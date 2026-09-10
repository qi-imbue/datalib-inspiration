---
title: datalib -- your personal data, searchable
description: Mirror your own data (Slack, email, GitHub, Notion, chat history) into a private local store, and let the mind search and answer questions from it.
thumbnail: inspiration-datalib.svg
---

# datalib -- your personal data, searchable

This file is the manifest for the **datalib** inspiration (slug: `datalib`). It
is the one document a future agent reads to understand, present, and adapt this
inspiration. If you are an agent in a mind that was created from this
inspiration, this file is your script: read all of it, then follow "How to adapt
it" below.

## What it is

datalib gives a mind a private, always-local copy of the user's own data --
their Slack messages, email, GitHub activity, Notion pages, and chat history --
mirrored out of those services into a single store on the mind's disk. Once
mirrored, the mind can search it and answer questions from it ("what did I tell
Sam about the launch?", "find the invoice email from March") without going back
out to each service. Nothing leaves the mind: the data is fetched with the
user's own credentials (via latchkey) and stored locally. It is opt-in on
purpose -- concentrating this much personal data is powerful and sensitive, so a
mind only gets it when the user chooses this inspiration.

## How it works

The snapshot includes these paths (each is a repo-root-relative path copied from
the original mind onto a clean default-workspace-template base):

- `.agents/skills/datalib/SKILL.md` (the datalib skill -- the capability itself)
- `system/apps/data/run_datalib_http.sh` (the web UI's service wrapper)
- the `[program:data]` stanza at the end of `system/supervisord.conf` -- copy
  the stanza onto the base template's own file, don't copy the file wholesale:
  the rest of it belongs to the base and drifts with it.

The `datalib` skill is self-contained: on first use it installs the
`datalib-*` binaries (a fully-static musl build, pinned to datalib v0.31.1)
into `~/.local/bin`; the web-UI service is the only thing the base template
gains. A pipeline config at
`$DATALIB_CONFIG` (default `data/.skills/datalib/config.toml`) lists which
sources to mirror; each source is fetched through `latchkey` (so the user's
credentials are injected by the Minds gateway, never stored in the config) and
written to a local store under the data root (`data/.skills/datalib`, the
workspace's own gitignored data tree on the persistent volume), where the skill
searches it. The agent queries that store directly, as a local tool, when
answering a question -- no service is involved in the answering.

datalib also ships a web UI (a searchable grid over everything mirrored), and
the snapshot runs it as the supervised `data` service on port 8731, registered
through `forward_port.py` so it appears in the workspace's app picker and is
proxied at `/service/data/`. It is the user's own way into the store, separate
from the agent's. Two things to know about it: the service installs the datalib
binaries itself if the skill hasn't yet, so a fresh mind's UI works before any
sync has run (it just shows an empty index); and every route sits behind
datalib's per-process API token, so the first visit needs
`?token=<contents of data/.skills/datalib/system/api-token>`. That sets a
session cookie and then bounces once to the workspace root -- datalib strips
the token from the URL by redirecting, and it doesn't know it is being served
under a path prefix. Reopening `data` from the picker works from then on. The
skill tells the adopting agent how to hand the user that link.

The concrete commands, config format, and query surfaces are datalib's own and
change between versions, so they are deliberately not restated here or in the
skill. They live in datalib's agent guide, pinned to the version above:
https://github.com/imbue-ai/datalib/blob/v0.31.1/docs/agent_user.md

## Prerequisites

Activation requirements: what the adopting agent must SET UP -- and must INITIATE
ITSELF during setup, before asking how to adapt -- for this inspiration to run
against the new user's own accounts/data. One line per requirement, in this
machine-readable form (greppable by `requires_`):

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
JMAP mailbox through the service for that host.)

## How to adapt it

Instructions for the NEXT agent -- the one adapting this inspiration into a new
mind. This is the `use-inspiration` skill's template path; in short:

1. Read this entire file first, especially "Prerequisites" and "Holes" below --
   Prerequisites are your SETUP agenda, Holes are your ADAPTATION agenda.
2. Present the inspiration to the user in plain, non-technical language: what it
   is, what it does, and what it needs from them (name the Prerequisites).
3. Ask whether they want to use their own accounts (e.g. their own Slack). If
   YES: ACTIVATE FIRST -- initiate every `requires_permission` line NOW via a
   latchkey permission request (see the `latchkey` skill; the request opens the
   approval/login flow in the minds app), write a `$DATALIB_CONFIG` with the
   chosen sources, run the sync, and get the store showing THE USER'S OWN DATA. Done for a data-backed app means the user can search and see their
   own data -- NOT that a service starts or an endpoint returns 200. Then tell
   them it is live and to try a search.
4. Only AFTER that (or immediately, if they chose different sources -- the swap
   is then the first adaptation) ask: "How do you want to adapt it?"
5. Work through each hole interactively, one at a time. Translate each into plain
   language, ask for a decision only when you genuinely need one, and resolve the
   obvious ones yourself.
6. When done, append a dated entry to "Adaptation history" below (never rewrite
   earlier entries) and commit.

## Holes

- **Which sources, and how much.** The skill ships an example config only. The
  adapter must set the user's real sources: which Slack channels (or
  `all_channels = true`), which of the three email modes to use -- a Google
  Takeout `.mbox` on disk, a Gmail account over Google's API, or a JMAP
  server -- and which GitHub/Notion scopes. Nothing is mirrored until the
  config names a source and the sync runs.
- **Cloudflare-walled sources need a recent Minds.** `claude` (claude.ai)
  and `chatgpt` work inside Minds as of datalib v0.24.0: the latchkey
  gateway routes marked requests through datalib's Chrome-impersonating curl,
  clearing the TLS fingerprint check that used to challenge them. As of v0.27.0
  a remotely-hosted mind additionally sends those requests back out through the
  gateway on the user's own computer (`MINDS_VIA_DESKTOP_URL_PREFIX`, published
  by Minds), so they carry a residential IP instead of the VPS's -- these sites
  block datacenter ranges outright. On an older Minds app one or both halves
  are missing and these sources still get challenged -- if a sync returns
  challenge pages instead of data, point the same `claude` source at an
  unpacked on-disk export instead. Not something the adapter wires up either
  way.
- **The store is rebuildable, and big enough to think about.** The data root
  (`data/.skills/datalib`) persists across restarts on the mind's own volume and
  is covered by the encrypted host backup like the rest of `data/`. It is also
  large (doltlite stores plus a qmd index) and fully reconstructible by
  re-syncing, so an adapting mind may prefer to exclude it from backups -- the
  skill says how. Treat it as rebuildable-by-resync, not as precious storage.

## Adaptation history

Each mind that adapts this inspiration appends one dated entry below. Earlier
entries are never rewritten.
