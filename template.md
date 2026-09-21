---
title: datalib -- your personal data, searchable
description: Mirror your own data (Slack, email, GitHub, Notion, chat history) into a private local store, and let the mind search and answer questions from it.
thumbnail: template.svg
version: v2
format: v2
---

# datalib -- your personal data, searchable

This file is the manifest for the **datalib -- your personal data,
searchable** template (slug: `datalib`). It is the one document a future agent
reads to understand, present, and adapt this template. If you are an agent in a
mind that was created from this template, this file is your script: read all
of it, then follow "How to adapt it" below.

## What it is

datalib gives a mind a private, always-local copy of the user's own data --
their Slack messages, email, GitHub activity, Notion pages, and chat history --
mirrored out of those services into a single store on the mind's disk. Once
mirrored, the mind can search it and answer questions from it ("what did I tell
Sam about the launch?", "find the invoice email from March") without going back
out to each service, and the user can browse and manage the same store
themselves in the Datalib tab. Nothing leaves the mind: the data is fetched
with the user's own credentials (via latchkey) and stored locally. It is opt-in
on purpose -- concentrating this much personal data is powerful and sensitive,
so a mind only gets it when the user chooses this template.

## How it works

The snapshot includes these paths (each is a repo-root-relative path copied from
the original mind onto a clean default-workspace-template base):

- `.agents/skills/datalib/` (the datalib skill -- the agent's side of the
  capability)
- `system/apps/datalib/` (the Datalib tab: the app manifest, its icon, and the
  `datalib-app` launcher that runs datalib's web UI)
- `system/supervisord.conf.d/datalib.conf` (the `datalib` program that
  supervises it)
- `system/scripts/env.d/2000-datalib-binaries.sh` (the env.d unit that
  installs the datalib binaries)
- `uv.lock` (the workspace lockfile, which now lists the `datalib-app`
  package; the base template's own lock is otherwise unchanged)

The **skill** is how the agent uses datalib. A pipeline config at
`data/.skills/datalib/config.toml` lists which sources to mirror; each source is
fetched through `latchkey` (so the user's credentials are injected by the Minds
gateway, never stored in the config) and written to a local store under that
data root (`data/.skills/datalib`, the workspace's own gitignored data tree on
the persistent volume), where the skill searches it. The agent queries that
store directly, as a local tool, when answering a question. The concrete
commands, config format, and query surfaces are datalib's own and change
between versions, so they are deliberately not restated here or in the skill.
They live in datalib's agent guide, pinned to the release the binaries come
from (datalib v0.35.2):
https://github.com/imbue-ai/datalib/blob/v0.35.2/docs/agent_user.md

The **Datalib tab** is how the user uses it. datalib's own web UI -- the
Manage screen, which shows every configured source and its sync state, and
the Add/Edit source wizard -- is served by `datalib-http` over the same data
root, so a source the user adds in the wizard is what the agent searches and a
sync the agent runs is what the user sees. It runs as the supervised `datalib`
program: `datalib-app` (system/apps/datalib) registers the app through
`forward_port.py` and runs `~/.local/bin/datalib-http --no-open
data/.skills/datalib` as its child, bound to `127.0.0.1:8731`, and the
workspace shows it as the `datalib` app at its own origin. datalib-http
requires its API token on every route, and a tab has no way to type one, so
the app's instances API lists the one page at `/?token=<token>`: the tab opens
there, datalib-http sets its session cookie and redirects to `/`. The token is
`data/.skills/datalib/system/api-token`, kept stable across restarts, and it
is also what the agent sends as a bearer token to reach the API.

The **binaries** (a fully-static musl build of datalib v0.35.2: `datalib-http`
for the tab, `datalib-dag` and the rest for the skill) are installed by the
env.d unit on the env-converge one-shot, into `~/.local/share/datalib/<version>/`
with links in `~/.local/bin`. On a first boot that takes a few minutes; the
`datalib` program waits for it by exiting and letting supervisord retry, so the
tab only appears once there is a server behind it. The tarball holds the
binaries alone: the Node runtime a sync shells out to (`latchkey` for
credentials, `qmd` for the semantic index, at the versions datalib was built
with) is a second asset of the same release, which the unit pulls into
`~/.cache/datalib/runtime` (about 100 MB, once per release) right after the
install and which the first sync fetches itself if that pull missed. datalib
does not use the mind's own `node`.

## Recipe

This template is version `v2`. It is not a fork of the workspace it came
from -- it is DERIVED from it by a recipe: include these paths, leave these
out, apply these published-version rules. An update re-runs the recipe against
the current workspace and publishes the result as the next version, so anything
excluded stays excluded even though it still exists in the source workspace.

The recipe is machine-read, so it lives in the sibling
[`template.toml`](template.toml) -- its `[recipe]` table -- along with the
structured requirements and the environment this template needs installed.
That file is authoritative for all of it; this one holds the prose.

## Requirements

Everything the adopting mind must deal with before this template is really
theirs. Two kinds of entry, handled at different times:

- **Activation** -- what must be SET UP before anything runs, in the
  machine-readable `requires_` forms below. The adopting agent acts on these
  ITSELF, first, before asking anything.
- **Adaptation** -- what must be DECIDED or REWIRED, in prose. Worked through
  interactively with the user, after activation.

Activation, one line per requirement:

- requires_permission: slack-api / slack-read-all (user-approved; the adopting
  agent initiates this via a latchkey permission request during setup -- only if
  the user wants their Slack mirrored)
- requires_permission: github-api / github-read-all (user-approved; same, for
  GitHub)
- requires_permission: notion-api / notion-read-all (user-approved; same, for
  Notion)

Only request the permission(s) for the source(s) the user actually wants. The
exact permission-schema names come from latchkey itself -- run `latchkey curl
http://latchkey-self.invalid/permissions/available/<service>` and use the
`*-read-all` variant; the `latchkey` skill drives the request/approval flow. No
`requires_secret`: credentials are handled entirely by latchkey. (Email from a
Google Takeout `.mbox` needs no permission at all -- it is a file on disk; the
user just points the config at it. The two live email modes do need one: Gmail /
Google Workspace goes through latchkey's built-in `google-gmail` service, and a
JMAP mailbox through the service for that host.) No `requires_llm`: nothing
here calls a model; the agent answers from the store with its own tools.

Adaptation:

- **Which sources, and how much.** The store ships with no config, so nothing
  is mirrored until a source is named and the sync runs. The adapter must set
  the user's real sources: which Slack channels (or `all_channels = true`),
  which of the three email modes to use -- a Google Takeout `.mbox` on disk, a
  Gmail account over Google's API, or a JMAP server -- and which GitHub/Notion
  scopes. The Datalib tab's wizard is the user's way to do this; the agent can
  also write the config directly.
- **Cloudflare-walled sources need a recent Minds.** The `claude` source over
  claude.ai's API (its `api` method) and the `chatgpt` source work inside
  Minds as of datalib v0.24.0: the latchkey
  gateway routes marked requests through datalib's Chrome-impersonating curl,
  clearing the TLS fingerprint check that used to challenge them. As of v0.27.0
  a remotely-hosted mind additionally sends those requests back out through the
  gateway on the user's own computer (`MINDS_VIA_DESKTOP_URL_PREFIX`, published
  by Minds), so they carry a residential IP instead of the VPS's -- these sites
  block datacenter ranges outright. On an older Minds app one or both halves
  are missing and these sources still get challenged -- if a sync returns
  challenge pages instead of data, point the source at an on-disk export
  instead (the `claude` source's `export` method). Not something the adapter
  wires up either way.
- **The store is rebuildable, and big enough to think about.** The data root
  (`data/.skills/datalib`) persists across restarts on the mind's own volume and
  is covered by the encrypted host backup like the rest of `data/`. It is also
  large (doltlite stores plus a qmd index) and fully reconstructible by
  re-syncing, so an adapting mind may prefer to exclude it from backups -- the
  skill says how. Treat it as rebuildable-by-resync, not as precious storage.

## Environment

What this template needs INSTALLED, beyond what the template already has.
Declared in `template.toml`'s `[environment]` table; an adopting mind
converges it at ITS OWN pinned apt snapshot timestamp, so package versions come
out consistent with the rest of that mind's environment rather than frozen to
whatever this publisher happened to have.

- `system/scripts/env.d/2000-datalib-binaries.sh`: the datalib binaries,
  pinned to v0.35.2 (a fully-static musl build fetched from datalib's GitHub
  release, with its published checksum verified). Both the Datalib tab and the
  skill run them. No apt packages, npm globals, uv tools, or cargo crates
  beyond the stock workspace: `datalib-app` is a workspace member installed
  the way every built-in app is.

## How to adapt it

Instructions for the NEXT agent -- the one adapting this template into a
new mind. This is the `use-template` skill's template path; in short:

1. Read this entire file first, especially "Requirements" above. It holds two
   kinds of entry and they are handled at different times: the machine-readable
   `requires_` lines are ACTIVATION (set them up before anything runs), and
   the prose bullets are ADAPTATION (decide or rewire them afterwards).
2. Present the template to the user in plain, non-technical language: what
   it is, what it does, and what it needs from them (name the activation
   requirements).
3. Ask whether they want to use their own accounts (e.g. their own Slack). If
   YES: ACTIVATE FIRST -- initiate every `requires_permission` line NOW via a
   latchkey permission request (see the `latchkey` skill; the request opens the
   approval/login flow in the minds app), write the config with the chosen
   sources (or walk the user through the wizard in the Datalib tab), run the
   sync, and get the store showing THE USER'S OWN DATA. Done for a data-backed
   app means the user can search and see their own data -- NOT that a service
   starts or an endpoint returns 200. Then tell them it is live, open the
   Datalib tab for them (`python3 system/scripts/layout.py open datalib`), and
   invite them to try a search.
4. Only AFTER that (or immediately, if they chose different sources -- the swap
   is then the first adaptation) ask: "How do you want to adapt it?"
5. Work through each adaptation entry interactively, one at a time. Translate
   each into plain language, ask for a decision only when you genuinely need
   one, and resolve the obvious ones yourself.
6. When done, append a dated entry to "Adaptation history" below (never rewrite
   earlier entries) and commit.

## Publication history

This template's changelog: what each published version changed. The PUBLISHER
appends one entry per version (newest last); earlier entries are never rewritten.
This is distinct from "Adaptation history" below, which is the ADOPTERS' log.

### v1 (2026-07-15) -- the datalib skill as an opt-in inspiration

The datalib skill, self-installing the datalib binaries on first use, with the
store at `data/.skills/datalib` and every pin bumped in step with datalib's
releases (v0.17.0 through v0.29.0). A late v1 also ran datalib's web UI as the
`data` service, reachable only by pasting a token link.

### v2 (2026-09-15) -- the Datalib tab, and the v2 template format

Migrated from the v1 `inspiration-datalib.md` manifest to `template.md` +
`template.toml` + `template.svg` on the current default-workspace-template
base. datalib's new web UI (the Manage screen and the Add/Edit source wizard)
runs as the `datalib` app tab, opened at its own origin with the token handed
over by the app's instances API, so it needs no pasted link. The binaries are
pinned to datalib v0.31.1 and installed by an env.d unit at boot rather than
by the skill on first use.

## Adaptation history

Each mind that adapts this template appends one dated entry below. Earlier
entries are never rewritten.
