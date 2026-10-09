The Datalib app runs on the current app model, which removed the app instances layer.

- `launch_datalib_http.py`, a standard-library launcher, replaces the `datalib-app` Python package and its instances API. It registers the app through `forward_port.py` and then becomes `datalib-http`.

- The window still opens at `/?token=<token>`: the launcher registers a copy of `app.toml` whose one launch path, `ui`, carries the token as a preset.

- The app is no longer a uv workspace member (`system/apps/datalib` is excluded in the root `pyproject.toml`), so `uv.lock` is the base template's own.

- `app.toml` declares `stop_when_no_windows = false`, because a sync started from the Manage screen must finish after the window closes.
