from pathlib import Path
from typing import Final

import pytest
from app_instances.sidecar import app_url_port
from app_manifest.manifest import load_manifest
from inline_snapshot import snapshot

from datalib_app.errors import DatalibBinaryMissingError
from datalib_app.main import (
    APP_NAME,
    APP_URL,
    DATA_ROOT,
    INSTANCES_URL,
    MANIFEST_PATH,
    DatalibAppArguments,
    build_datalib_http_argv,
    child_environment,
    default_datalib_http_path,
    run_datalib_app,
)
from datalib_app.source import OPEN_ACTION
from datalib_app.token import ApiToken

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[5]


def test_the_fixed_wiring_agrees_with_the_manifest() -> None:
    manifest = load_manifest(_REPO_ROOT / MANIFEST_PATH)

    assert manifest.instances_url == INSTANCES_URL
    assert manifest.name == APP_NAME
    assert manifest.instances is True
    assert [action.id for action in manifest.actions] == [OPEN_ACTION]
    assert manifest.default_shortcut is not None
    assert manifest.default_shortcut.action == OPEN_ACTION
    assert app_url_port(APP_URL) == 8731
    assert DATA_ROOT == Path("data/.skills/datalib")


def test_the_binary_is_looked_up_under_the_home_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    assert default_datalib_http_path() == tmp_path / ".local" / "bin" / "datalib-http"


def test_the_datalib_http_command_line_serves_the_data_root_without_opening_a_browser() -> (
    None
):
    assert build_datalib_http_argv(
        datalib_http_path=Path("/home/user/.local/bin/datalib-http"),
        data_root=DATA_ROOT,
    ) == snapshot(
        ["/home/user/.local/bin/datalib-http", "--no-open", "data/.skills/datalib"]
    )


def test_the_child_environment_binds_loopback_and_pins_the_token() -> None:
    assert child_environment(8731, ApiToken("abc")) == snapshot(
        {"DATALIB_BIND": "127.0.0.1:8731", "DATALIB_TOKEN": "abc"}
    )


def test_a_missing_binary_refuses_to_start_before_registering_anything(
    tmp_path: Path,
) -> None:
    arguments = DatalibAppArguments(
        manifest_path=MANIFEST_PATH,
        app_url=APP_URL,
        instances_url=INSTANCES_URL,
        data_root=tmp_path / "root",
        datalib_http_path=tmp_path / "missing" / "datalib-http",
    )

    with pytest.raises(DatalibBinaryMissingError, match="is not installed yet"):
        run_datalib_app(arguments)
