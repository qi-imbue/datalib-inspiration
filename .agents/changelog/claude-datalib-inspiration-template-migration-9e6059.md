The datalib skill no longer installs the datalib binaries itself: they arrive at boot through `system/scripts/env.d/2000-datalib-binaries.sh` (pinned to datalib v0.31.1, linked into `~/.local/bin`), and the skill runs that unit by hand only when they are not there yet. It now points the agent at the Datalib tab (`python3 system/scripts/layout.py open datalib`) as the user's way into the store, and at the HTTP API on `127.0.0.1:8731` with the bearer token from `data/.skills/datalib/system/api-token`, which stays stable across restarts. The pinned agent-guide link moves to v0.31.1 with the binaries.

The welcome skill is reworded for the v2 templates flow (`template.md` + `template.toml`, the `use-template` skill).

The update-self apply test that lists every app tool a shared-file change refreshes now includes `datalib-app`, and gains two cases for a change under `system/apps/datalib/`.
