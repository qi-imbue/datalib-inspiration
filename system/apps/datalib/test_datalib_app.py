"""Integration: ``datalib-app`` as a real process around a fake datalib-http."""

import os
import signal
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Final
from uuid import uuid4

import httpx
import pytest
from app_instances.testing import (
    LOOPBACK_HOST,
    SidecarEnvironment,
    free_port,
    is_port_accepting,
    wait_until,
)
from app_manifest.primitives import AppName, InstancesUrl
from app_manifest.registry import read_registry
from datalib_app.testing import (
    ENV_FAKE_DATALIB_HTTP_DIR,
    install_fake_datalib_http,
    read_fake_datalib_http_argv,
    read_fake_datalib_http_environment,
)
from imbue.imbue_common.frozen_model import FrozenModel
from pydantic import Field

_STARTUP_TIMEOUT_SECONDS: Final[float] = 20.0
_EXIT_TIMEOUT_SECONDS: Final[float] = 10.0
_REQUEST_TIMEOUT_SECONDS: Final[float] = 5.0

_MINIMAL_ICON: Final[str] = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M3 3h18v18H3z"/></svg>'
)


class _DatalibAppUnderTest(FrozenModel):
    """One datalib-app process's command line, its ports and files, and where its stderr lands."""

    app_name: AppName = Field(description="The unique name the app registers")
    http_port: int = Field(description="The port the fake datalib-http is told to bind")
    instances_port: int = Field(description="The port the instances API is served on")
    instances_url: InstancesUrl = Field(description="Where the instances API is served")
    data_root: Path = Field(description="The data root the app is told to serve")
    record_dir: Path = Field(
        description="Where the fake datalib-http records its argv and environment"
    )
    log_path: Path = Field(description="Where the app's stderr is captured")
    command: tuple[str, ...] = Field(description="The full command line")
    environment: Mapping[str, str] = Field(
        description="The environment the process runs with"
    )


def _write_manifest(
    directory: Path, app_name: AppName, instances_url: InstancesUrl
) -> Path:
    """The real manifest's shape under a unique name, so parallel tests never share a registry row."""
    (directory / "icon.svg").write_text(_MINIMAL_ICON)
    manifest_path = directory / "app.toml"
    manifest_path.write_text(
        f'name = "{app_name}"\n'
        'display_name = "Datalib"\n'
        'icon = "icon.svg"\n'
        "instances = true\n"
        f'instances_url = "{instances_url}"\n'
        "\n"
        "[default_shortcut]\n"
        'action = "open"\n'
        'mode = "focus"\n'
        "\n"
        "[[actions]]\n"
        'id = "open"\n'
        'label = "Open Datalib"\n'
    )
    return manifest_path


def _prepare(
    environment: SidecarEnvironment,
    published_token: str | None,
    is_binary_installed: bool = True,
) -> _DatalibAppUnderTest:
    app_name = AppName(f"datalib-{uuid4().hex[:8]}")
    http_port = free_port()
    instances_port = free_port()
    instances_url = InstancesUrl(f"http://{LOOPBACK_HOST}:{instances_port}")
    manifest_path = _write_manifest(environment.scratch_dir, app_name, instances_url)
    executable, record_dir = install_fake_datalib_http(
        environment.scratch_dir / "fake-datalib-http"
    )
    if not is_binary_installed:
        executable = environment.scratch_dir / "not-installed" / "datalib-http"
    data_root = environment.scratch_dir / "data-root"
    if published_token is not None:
        (data_root / "system").mkdir(parents=True)
        (data_root / "system" / "api-token").write_text(published_token)
    return _DatalibAppUnderTest(
        app_name=app_name,
        http_port=http_port,
        instances_port=instances_port,
        instances_url=instances_url,
        data_root=data_root,
        record_dir=record_dir,
        log_path=environment.scratch_dir / "datalib-app.log",
        command=(
            sys.executable,
            "-m",
            "datalib_app.main",
            "--manifest",
            str(manifest_path),
            "--app-url",
            f"http://localhost:{http_port}",
            "--instances-url",
            instances_url,
            "--data-root",
            str(data_root),
            "--datalib-http",
            str(executable),
        ),
        environment={**os.environ, ENV_FAKE_DATALIB_HTTP_DIR: str(record_dir)},
    )


def _read_log(app: _DatalibAppUnderTest) -> str:
    return app.log_path.read_text() if app.log_path.exists() else ""


def _spawn(app: _DatalibAppUnderTest) -> subprocess.Popen[bytes]:
    # A session of its own puts the app and the fake server in one process group, so a failed
    # test can kill both rather than orphan the fake.
    with app.log_path.open("wb") as log_file:
        return subprocess.Popen(
            app.command,
            stdout=subprocess.DEVNULL,
            stderr=log_file,
            env=app.environment,
            start_new_session=True,
        )


def _kill_if_running(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def _listed(app: _DatalibAppUnderTest) -> list[dict[str, object]]:
    listed = httpx.get(
        f"{app.instances_url}/_instances", timeout=_REQUEST_TIMEOUT_SECONDS
    )
    assert listed.status_code == 200, listed.text
    return listed.json()["instances"]


@pytest.mark.timeout(60)
def test_datalib_app_registers_runs_datalib_http_with_the_published_token_and_lists_its_page(
    datalib_environment: SidecarEnvironment,
) -> None:
    app = _prepare(datalib_environment, published_token="published-token-0001\n")
    process = _spawn(app)
    try:
        assert wait_until(
            lambda: datalib_environment.registry_path.exists(),
            _STARTUP_TIMEOUT_SECONDS,
        ), _read_log(app)
        assert is_port_accepting(app.instances_port), _read_log(app)

        rows = read_registry(datalib_environment.registry_path)
        assert [(row.name, row.url, row.instances_url) for row in rows] == [
            (app.app_name, f"http://localhost:{app.http_port}", app.instances_url)
        ]

        # datalib-http runs as the sidecar's child, told where to bind and which token to require.
        assert wait_until(
            lambda: read_fake_datalib_http_environment(app.record_dir) is not None,
            _STARTUP_TIMEOUT_SECONDS,
        ), _read_log(app)
        assert read_fake_datalib_http_argv(app.record_dir) == [
            "--no-open",
            str(app.data_root),
        ]
        assert read_fake_datalib_http_environment(app.record_dir) == {
            "DATALIB_BIND": f"127.0.0.1:{app.http_port}",
            "DATALIB_TOKEN": "published-token-0001",
        }

        # The one page carries that same token, and opening it again is the same page.
        assert _listed(app) == [
            {
                "key": "ui",
                "url": "/?token=published-token-0001",
                "title": "Datalib",
                "status": "idle",
                "lifetime": "explicit",
                "last_active": None,
                "renameable": False,
                "stoppable": False,
            }
        ]
        opened = httpx.post(
            f"{app.instances_url}/_instances",
            json={"action": "open", "params": {}},
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        assert opened.status_code == 201, opened.text
        assert opened.json()["instance"]["key"] == "ui"
        assert len(_listed(app)) == 1

        # Not renameable, no location, and a delete is accepted without removing the page.
        renamed = httpx.post(
            f"{app.instances_url}/_instances/ui/rename",
            json={"title": "Mine"},
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        assert renamed.status_code == 400
        relocated = httpx.post(
            f"{app.instances_url}/_instances/ui/location",
            json={"path": "/manage"},
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        assert relocated.status_code == 400
        deleted = httpx.delete(
            f"{app.instances_url}/_instances/ui", timeout=_REQUEST_TIMEOUT_SECONDS
        )
        assert deleted.status_code == 204
        assert len(_listed(app)) == 1

        process.send_signal(signal.SIGTERM)
        assert process.wait(timeout=_EXIT_TIMEOUT_SECONDS) == 143, _read_log(app)
        assert not is_port_accepting(app.instances_port)
    finally:
        _kill_if_running(process)


@pytest.mark.timeout(60)
def test_datalib_app_mints_a_token_when_none_is_published(
    datalib_environment: SidecarEnvironment,
) -> None:
    app = _prepare(datalib_environment, published_token=None)
    process = _spawn(app)
    try:
        assert wait_until(
            lambda: read_fake_datalib_http_environment(app.record_dir) is not None,
            _STARTUP_TIMEOUT_SECONDS,
        ), _read_log(app)
        environment = read_fake_datalib_http_environment(app.record_dir)
        assert environment is not None
        token = environment["DATALIB_TOKEN"]
        assert len(token) == 64
        [page] = _listed(app)
        assert page["url"] == f"/?token={token}"
    finally:
        _kill_if_running(process)


@pytest.mark.timeout(60)
def test_datalib_app_exits_without_registering_when_the_binary_is_missing(
    datalib_environment: SidecarEnvironment,
) -> None:
    app = _prepare(datalib_environment, published_token=None, is_binary_installed=False)
    process = _spawn(app)
    try:
        assert process.wait(timeout=_EXIT_TIMEOUT_SECONDS) == 1, _read_log(app)
        assert "is not installed yet" in _read_log(app)
        assert not datalib_environment.registry_path.exists()
        assert not is_port_accepting(app.instances_port)
    finally:
        _kill_if_running(process)
