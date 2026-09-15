# datalib

The Datalib tab: datalib's own web UI -- the Manage screen and the Add/Edit
source wizard served by `datalib-http` -- over the store the `datalib` skill
writes, so a source added through the wizard is what the agent searches and a
sync the agent runs is what the UI shows. Supervised as the `datalib` program,
declared in `system/supervisord.conf.d/datalib.conf`, which runs the
`datalib-app` entry point of this package (installed as its own uv tool by
`system/scripts/build_workspace.sh`, like every Python app with a manifest).

The server is `datalib-http` from the datalib release pinned in
`system/scripts/env.d/2000-datalib-binaries.sh` (the same pin as the skill,
`README.md`, and `template.md`), which that env.d unit installs into
`~/.local/share/datalib/<version>/` and links into `~/.local/bin` on the
env-converge one-shot. `datalib-app` (`src/datalib_app/main.py`) is the
`app_instances` sidecar launcher around it: it serves the instances API on
`127.0.0.1:8732` (the manifest's `instances_url`), registers `app.toml` and the
datalib-http port 8731 through `system/scripts/forward_port.py`, and runs
`~/.local/bin/datalib-http --no-open data/.skills/datalib` as its child with
`DATALIB_BIND=127.0.0.1:8731`, forwarding `SIGTERM` and `SIGINT` to it and
exiting with its status. Until the env.d unit has installed the binary (minutes
into a first boot), the app exits without registering anything and supervisord
retries it with its backoff, so the tab never appears with nothing behind it.

## The token

`datalib-http` requires its per-process API token on every route: loopback
does not keep a web page out, and `PUT /api/config` runs shell commands. A
browser gets in by loading `/?token=<token>` once, which sets a session cookie
and redirects to `/`. A tab in the workspace opens at whatever URL the app's
instances API lists, so that is where the token travels: the one instance this
app lists (`key = "ui"`, title `Datalib`, `explicit`, never renamed, no
location tracking) has the URL `/?token=<token>`. The shell fetches that list
over loopback; browsers never reach the instances API.

The token itself is `data/.skills/datalib/system/api-token`: the app reads it
at start and hands it to `datalib-http` through `DATALIB_TOKEN`, so it stays
the same across restarts (a browser already holding the cookie stays signed
in) and the skill can read the same file for its bearer token. When the file
is missing or unusable the app mints one, and `datalib-http` writes it there.

## Instances

`open` (the manifest's only action, also its `default_shortcut`) returns the
one record; a second open returns the same record and the shell focuses the
tab already showing it. Delete is accepted and changes nothing (closing the
tab needs no bookkeeping; stopping datalib is the app-level Stop). Rename and
location reports are refused.

## Tests

`uv run pytest system/apps/datalib` from the repo root. `main_test.py`,
`source_test.py`, and `token_test.py` pin the wiring; `test_datalib_app.py`
runs `datalib-app` as a process around a fake `datalib-http` (`testing.py`)
and drives the instances routes.
