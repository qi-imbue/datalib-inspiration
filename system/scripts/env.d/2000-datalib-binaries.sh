#!/usr/bin/env bash
# env.d unit: the datalib binaries (datalib-http for the Datalib tab, datalib-dag
# and the rest for the datalib skill), one pinned release for both so the UI
# and the agent's tools never disagree about the store format. This is the
# template's one URL-fetched install, so it ships as an env.d unit rather than
# an [environment] package entry (see template.toml).
#
# The release lands in a directory named after the pin, under the persistent
# home, and ~/.local/bin gets one symlink per binary. The versioned directory
# is the satisfied-check (env.d contract: idempotent, fast, no marker files):
# a pin bump changes the directory and so re-installs. datalib-http finds its
# sibling binaries through the resolved executable path, which is why the
# binaries themselves stay together in that directory.
set -euo pipefail

# Keep this pin in step with the datalib skill (.agents/skills/datalib/SKILL.md),
# README.md and template.md.
readonly PINNED_VERSION="v0.36.1"

readonly INSTALL_ROOT="${DATALIB_INSTALL_ROOT:-$HOME/.local/share/datalib}"
readonly BIN_DIR="${DATALIB_BIN_DIR:-$HOME/.local/bin}"
readonly RELEASE_DIR="$INSTALL_ROOT/$PINNED_VERSION"

_log() {
    printf '[env.d/datalib-binaries] %s\n' "$*"
}

_link_binaries() {
    local binary name
    mkdir -p "$BIN_DIR"
    for binary in "$RELEASE_DIR"/*; do
        [ -f "$binary" ] || continue
        name="$(basename "$binary")"
        ln -sfn "$binary" "$BIN_DIR/$name"
    done
}

if [ -x "$RELEASE_DIR/datalib-http" ] && [ "$(readlink "$BIN_DIR/datalib-http" 2>/dev/null || true)" = "$RELEASE_DIR/datalib-http" ]; then
    _log "datalib $PINNED_VERSION already installed at $RELEASE_DIR, satisfied"
    exit 0
fi

if [ -x "$RELEASE_DIR/datalib-http" ]; then
    _log "datalib $PINNED_VERSION present at $RELEASE_DIR; relinking into $BIN_DIR"
    _link_binaries
    _log "unit satisfied"
    exit 0
fi

# datalib's own installer (the fully-static musl build runs as-is on any Linux). It
# downloads the release tarball for this architecture, verifies the published
# sha256, and drops the binaries into DATALIB_INSTALL_DIR.
_log "installing datalib $PINNED_VERSION into $RELEASE_DIR"
mkdir -p "$RELEASE_DIR"
if ! curl -LsSf "https://raw.githubusercontent.com/imbue-ai/datalib/$PINNED_VERSION/scripts/install.sh" \
    | DATALIB_VERSION="$PINNED_VERSION" DATALIB_LIBC=musl DATALIB_INSTALL_DIR="$RELEASE_DIR" sh; then
    _log "install FAILED; the next converge retries"
    exit 1
fi
[ -x "$RELEASE_DIR/datalib-http" ] || {
    _log "install did not produce $RELEASE_DIR/datalib-http; the next converge retries"
    exit 1
}
_link_binaries
_log "installed datalib $PINNED_VERSION; binaries linked into $BIN_DIR"

# The tarball carries the binaries only. The Node runtime a sync shells out
# to (latchkey and qmd, at the versions datalib was built with) is a separate
# asset of the same release, fetched sha256-checked into ~/.cache/datalib/runtime
# on the first sync. Pull it now so that sync doesn't start with a ~100 MB
# download; a miss here is not fatal because the first sync fetches it too.
if "$RELEASE_DIR/datalib-step" pull-runtime >/dev/null 2>&1; then
    _log "runtime fetched into ~/.cache/datalib/runtime"
else
    _log "runtime pre-fetch failed; the first sync fetches it instead"
fi
_log "unit satisfied"
