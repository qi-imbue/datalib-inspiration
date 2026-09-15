"""Test doubles for the Datalib app: a fake ``datalib-http`` installed as an executable."""

from pathlib import Path
from typing import Final

# Where the fake datalib-http records the argv and environment it was started with.
ENV_FAKE_DATALIB_HTTP_DIR: Final[str] = "FAKE_DATALIB_HTTP_DIR"

_EXECUTABLE_MODE: Final[int] = 0o755

# The fake records its argv and the two variables the real server reads, then waits to be signalled.
_FAKE_DATALIB_HTTP_SCRIPT: Final[str] = f"""#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$@" > "${ENV_FAKE_DATALIB_HTTP_DIR}/argv"
printf 'DATALIB_BIND=%s\\nDATALIB_TOKEN=%s\\n' "${{DATALIB_BIND:-}}" "${{DATALIB_TOKEN:-}}" > "${ENV_FAKE_DATALIB_HTTP_DIR}/environment"
exec sleep 100000
"""


def install_fake_datalib_http(directory: Path) -> tuple[Path, Path]:
    """Write the fake ``datalib-http`` into ``directory/bin``, returning its path and the directory it records into."""
    bin_dir = directory / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    executable = bin_dir / "datalib-http"
    executable.write_text(_FAKE_DATALIB_HTTP_SCRIPT)
    executable.chmod(_EXECUTABLE_MODE)
    record_dir = directory / "datalib-http-state"
    record_dir.mkdir(parents=True, exist_ok=True)
    return executable, record_dir


def read_fake_datalib_http_argv(record_dir: Path) -> list[str] | None:
    """The argv the fake datalib-http was started with, or None when it has not started."""
    argv_path = record_dir / "argv"
    if not argv_path.exists():
        return None
    return argv_path.read_text().splitlines()


def read_fake_datalib_http_environment(record_dir: Path) -> dict[str, str] | None:
    """The bind and token variables the fake datalib-http saw, or None when it has not started."""
    environment_path = record_dir / "environment"
    if not environment_path.exists():
        return None
    return dict(
        line.split("=", 1) for line in environment_path.read_text().splitlines()
    )
