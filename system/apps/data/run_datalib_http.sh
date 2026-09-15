#!/usr/bin/env bash
# Wrapper for datalib's web UI (datalib-http) that:
# 1. Installs the datalib binaries if the skill hasn't already (no-op after)
# 2. Registers port 8731 via forward_port.py before starting the server
# 3. Execs datalib-http against the same data root the datalib skill uses
#
# Runs as the supervisord `data` program, so the UI is supervised and
# restarted alongside the other services. The skill installs the same
# binaries on first use; whichever runs first wins and the other is a no-op.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# The script lives at system/apps/data/, so the repo root is three levels up.
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Keep this pin in step with .agents/skills/datalib/SKILL.md -- the service and
# the skill must install the same datalib, or the UI and the agent's tools
# disagree about the store format.
DATALIB_VERSION=v0.32.0

# datalib-http binds this by default; set it explicitly so the port we register
# and the port it listens on cannot drift.
DATALIB_PORT=8731
export DATALIB_BIND="127.0.0.1:$DATALIB_PORT"

# The install target the skill uses. supervisord's environment does not
# necessarily carry it.
export PATH="$HOME/.local/bin:$PATH"

# The data root is the directory holding the config -- same convention as the
# skill, so both act on one store.
: "${DATALIB_CONFIG:=$REPO_ROOT/data/.skills/datalib/config.toml}"
DATA_ROOT="$(dirname "$DATALIB_CONFIG")"
mkdir -p "$DATA_ROOT"

# Install on first boot (fully-static musl build; runs as-is on any Linux).
if ! command -v datalib-http >/dev/null 2>&1; then
    curl -LsSf "https://raw.githubusercontent.com/imbue-ai/datalib/$DATALIB_VERSION/scripts/install.sh" \
        | DATALIB_VERSION="$DATALIB_VERSION" DATALIB_LIBC=musl DATALIB_INSTALL_DIR="$HOME/.local/bin" sh
fi

# Register the port before starting the server (the port is known ahead of
# time). The workspace UI proxies this service at /service/data/.
uv run python3 "$REPO_ROOT/system/scripts/forward_port.py" \
    --name data --url "http://localhost:$DATALIB_PORT"

# --no-open: there is no desktop browser to open here, and the UI is reached
# through the workspace's own proxy. An empty or absent data root is fine --
# datalib-http creates it and serves an empty index until a sync fills it.
exec datalib-http "$DATA_ROOT" --no-open
