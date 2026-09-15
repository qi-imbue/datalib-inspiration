import os
import sys
from pathlib import Path
from typing import Final

import click
from app_instances.sidecar import app_url_port, run_sidecar
from app_manifest.primitives import AppName, AppUrl, InstancesUrl
from imbue.imbue_common.frozen_model import FrozenModel
from imbue.imbue_common.pure import pure
from pydantic import Field

from datalib_app.errors import DatalibBinaryMissingError
from datalib_app.source import DatalibInstanceSource
from datalib_app.token import ApiToken, read_or_mint_token

# The Datalib tab's fixed wiring, all relative to the repo root every supervised program runs from.
MANIFEST_PATH: Final[Path] = Path("system/apps/datalib/app.toml")
APP_NAME: Final[AppName] = AppName("datalib")
APP_URL: Final[AppUrl] = AppUrl("http://localhost:8731")
INSTANCES_URL: Final[InstancesUrl] = InstancesUrl("http://127.0.0.1:8732")

# The store the datalib skill's CLI writes and searches; the UI serves the same one, so a
# source added through the wizard is what the agent queries and vice versa.
DATA_ROOT: Final[Path] = Path("data/.skills/datalib")

# datalib-http reads both from its environment: where to listen, and the token to require
# (auth.rs, TOKEN_ENV) instead of minting one per process.
ENV_BIND: Final[str] = "DATALIB_BIND"
ENV_TOKEN: Final[str] = "DATALIB_TOKEN"
BIND_HOST: Final[str] = "127.0.0.1"

# Where system/scripts/env.d/2000-datalib-binaries.sh links the pinned binaries. An absolute path:
# supervisord's children do not have ~/.local/bin on PATH.
DATALIB_HTTP_RELATIVE_TO_HOME: Final[Path] = Path(".local") / "bin" / "datalib-http"


def default_datalib_http_path() -> Path:
    return Path.home() / DATALIB_HTTP_RELATIVE_TO_HOME


class DatalibAppArguments(FrozenModel):
    """Everything the Datalib app is told on its command line."""

    manifest_path: Path = Field(description="The app.toml to register")
    app_url: AppUrl = Field(description="Where datalib-http serves the UI")
    instances_url: InstancesUrl = Field(description="Where the instances API is served")
    data_root: Path = Field(description="The datalib data root the UI serves")
    datalib_http_path: Path = Field(description="The datalib-http binary to run")


@pure
def build_datalib_http_argv(datalib_http_path: Path, data_root: Path) -> list[str]:
    """The datalib-http command line: the data root, and no browser to open (the tab is the browser)."""
    return [str(datalib_http_path), "--no-open", str(data_root)]


@pure
def child_environment(port: int, token: ApiToken) -> dict[str, str]:
    """What datalib-http reads from its environment: the loopback bind and the token to require."""
    return {ENV_BIND: f"{BIND_HOST}:{port}", ENV_TOKEN: str(token)}


def run_datalib_app(arguments: DatalibAppArguments) -> int:
    """Serve the instances API over the token and run datalib-http under the sidecar, returning its exit status.

    Refuses to start (so supervisord retries with its backoff, and the app is never registered without a
    server behind it) until the env.d unit has installed the binary.
    """
    if not arguments.datalib_http_path.is_file():
        raise DatalibBinaryMissingError(
            f"{arguments.datalib_http_path} is not installed yet; "
            "system/scripts/env.d/2000-datalib-binaries.sh installs it on the next env-converge run"
        )
    token = read_or_mint_token(arguments.data_root)
    # The sidecar spawns the child with this process's environment, and the token must not appear on
    # the command line (the sidecar logs the argv it starts), so the two variables go in here.
    os.environ.update(child_environment(app_url_port(arguments.app_url), token))
    return run_sidecar(
        manifest_path=arguments.manifest_path,
        app_url=arguments.app_url,
        instances_url=arguments.instances_url,
        child_argv=build_datalib_http_argv(
            datalib_http_path=arguments.datalib_http_path,
            data_root=arguments.data_root,
        ),
        source=DatalibInstanceSource(token=token),
    )


@click.command()
@click.option(
    "--manifest",
    "manifest_path",
    type=click.Path(path_type=Path),
    default=MANIFEST_PATH,
    show_default=True,
    help="The app.toml to register",
)
@click.option(
    "--app-url",
    default=APP_URL,
    show_default=True,
    help="Where datalib-http serves the UI",
)
@click.option(
    "--instances-url",
    default=INSTANCES_URL,
    show_default=True,
    help="Where the instances API is served",
)
@click.option(
    "--data-root",
    "data_root",
    type=click.Path(path_type=Path),
    default=DATA_ROOT,
    show_default=True,
    help="The datalib data root the UI serves",
)
@click.option(
    "--datalib-http",
    "datalib_http_path",
    type=click.Path(path_type=Path),
    default=None,
    help="The datalib-http binary [default: ~/.local/bin/datalib-http]",
)
def main(
    manifest_path: Path,
    app_url: str,
    instances_url: str,
    data_root: Path,
    datalib_http_path: Path | None,
) -> None:
    """Run the Datalib tab: datalib-http plus the instances API that hands the browser its token."""
    arguments = DatalibAppArguments(
        manifest_path=manifest_path,
        app_url=AppUrl(app_url),
        instances_url=InstancesUrl(instances_url),
        data_root=data_root,
        datalib_http_path=(
            datalib_http_path
            if datalib_http_path is not None
            else default_datalib_http_path()
        ),
    )
    try:
        exit_code = run_datalib_app(arguments)
    except DatalibBinaryMissingError as e:
        raise click.ClickException(str(e)) from e
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
