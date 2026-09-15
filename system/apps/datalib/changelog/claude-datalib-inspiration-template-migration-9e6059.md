New: the Datalib tab. `datalib-app` runs datalib's web UI (`datalib-http`, the Manage screen and the Add/Edit source wizard) as the supervised `datalib` app over the store the datalib skill writes (`data/.skills/datalib`), replacing the old-format `data` app (`system/apps/data/run_datalib_http.sh` plus a `[program:data]` stanza in `system/supervisord.conf`).

- The app is multi-instance with one action, `open`, and one page, so that it -- not the shell -- chooses the tab's URL: `/?token=<token>`, which datalib-http trades for its session cookie before redirecting to `/`. No link to paste any more.

- The token is the one datalib-http publishes at `data/.skills/datalib/system/api-token`, re-read at start and pinned through `DATALIB_TOKEN`, so it survives restarts and the skill can use it as a bearer token.

- The binary is `~/.local/bin/datalib-http` from the env.d unit; until that has installed it, the app exits without registering and supervisord retries.
