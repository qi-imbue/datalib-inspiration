The datalib template moves to the v2 template format: `inspiration-datalib.md` / `.svg` become `template.md` / `template.svg`, with the recipe, requirements, and environment in a new `template.toml` (validated by `validate_template.py`). The template base is merged up to current default-workspace-template main.

- `system/scripts/env.d/2000-datalib-binaries.sh`: installs the datalib v0.31.1 musl release into `~/.local/share/datalib/<version>/` and links every binary into `~/.local/bin`; the versioned directory is its satisfied-check.

- `system/supervisord.conf.d/datalib.conf`: the `datalib` program that runs the Datalib tab (see `system/apps/datalib/`).

- `uv.lock`: the `datalib-app` workspace member.

- `README.md` describes the Datalib tab, the env.d install, and the v2 manifest files.
