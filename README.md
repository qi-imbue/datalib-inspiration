# datalib -- your personal data, searchable

This repo is a published **inspiration**: a bootable snapshot of a Minds agent
("mind") that mirrors your own data into a private local store and answers
questions from it. You can create a new mind directly from this repo, or hand
the repo URL to a mind you already have.

## What it does

datalib gives a mind a local copy of the data you already have scattered across
the services you use -- Slack messages, email, GitHub activity, Notion pages,
and chat exports -- mirrored into a single store on the mind's own disk. Once
it's mirrored, you can ask the mind about your own history in plain language:

> what did I tell Sam about the launch?
> find the invoice email from March

The mind answers from the local store instead of going back out to each service.
Nothing leaves the mind: data is fetched with your own credentials (through the
`latchkey` gateway, which injects them at request time -- they're never written
into any config) and stored locally.

This is opt-in on purpose. Concentrating this much personal data in one place is
useful precisely because it's comprehensive, which is also why a mind only gets
it when you choose it.

## Getting started

Everything happens in the Minds app -- there's nothing to clone or install by
hand. You need this repo's URL:

```
https://github.com/qi-imbue/datalib-inspiration.git
```

**In a new workspace.** When you create a workspace, give that URL as the
template it's built from. The workspace boots already holding the snapshot, and
its agent opens by introducing datalib and asking which of your accounts to
start with -- you don't have to ask it for anything.

**In a workspace you already have.** Paste the URL into the chat and ask the
agent to adopt the inspiration. It brings the snapshot in and picks up the same
setup conversation.

Either way the agent drives the rest interactively: it asks which sources you
want, requests your approval for each service it needs, writes the config, runs
the first sync, and tells you when your data is searchable. You are done when
you can search your own data -- not when a service starts.

## Using it

**You don't have to say "datalib".** Once the inspiration is adopted, the skill
is part of the agent's working knowledge, and it's matched by *purpose* rather
than by name. Just ask about your own history in whatever words are natural:

> did anyone reply to my PR last week?
> what was the address in that email from the landlord?
> pull up the thread where we picked the launch date

The agent recognizes these as questions about your own mirrored data, searches
the local store, and answers from it -- without being told which tool to use.
Naming the skill explicitly is only useful for forcing the issue (say, "check
datalib" when you think it should have looked and didn't).

The same goes for growing the mirror: "also pull in my Notion" or "refresh my
Slack" routes to the skill on its own, and it will ask for any approval it still
needs.

**One thing that is *not* automatic: this is a mirror, not a filing cabinet.**
"Storing" here means importing more of an external service, not saving arbitrary
content you hand the agent. "Save this note for me" or "remember that I prefer X"
does *not* go into datalib -- those are the agent's own memory, which is a
separate thing. datalib only ever holds copies of data that already exists in
Slack, email, GitHub, Notion, or an export.

Two caveats worth knowing, since both look like the skill failing when it isn't:

- **It only knows what's been mirrored.** A source you never synced is simply
  absent, and an empty result means "not mirrored yet", not "doesn't exist". If
  an answer looks thin, ask what's actually synced.
- **It goes stale between syncs.** The store is a point-in-time copy, so recent
  activity won't be there until you ask for a refresh.

## What it needs from you

Only for the sources you actually want mirrored:

- **Slack, GitHub, Notion** -- your approval of a permission request that the
  mind initiates during setup. The approval flow opens in the Minds app; no
  tokens or API keys to find or paste.
- **Email** -- a Google Takeout `.mbox` file, which needs no permission at all.
  You just tell the agent where the file is.

## Good to know

- **Claude.ai and ChatGPT history can't be mirrored over the web API here.**
  Those sources sit behind Cloudflare, and inside Minds the credential gateway
  bypasses the browser-impersonating shim they'd need, so they get challenged.
  Use an on-disk export instead.
- **The store is rebuildable, not durable.** It lives on the mind's persistent
  volume and survives restarts, but it's too large to be part of the backup
  branch. If it's lost, you re-sync rather than restore.
- **The first sync is slow.** It downloads everything and builds a search index.
  Later runs only pull what changed, and are stoppable and resumable.

## How it's put together

The whole capability is one self-contained skill, `.agents/skills/datalib/`. On
first use it installs the `frankweiler` binaries (a static musl build, pinned to
datalib v0.21.0) into `~/.local/bin`, so the base template needs no changes. A
pipeline config lists the sources to mirror, and the store is written under
`/mngr/datalib`, where the agent searches it on demand. There's no background
service and no forwarded port -- it's a local tool the agent runs when answering
a question. The skill deliberately doesn't restate datalib's commands or config
format; it points the agent at
[datalib's own agent guide](https://github.com/imbue-ai/datalib/blob/v0.21.0/docs/agent_user.md),
pinned to the same version, so the two can't drift.

`inspiration-datalib.md` is the manifest: the authoritative document an agent
reads to understand, present, and adapt this inspiration, including the parts
deliberately left open for the adopting mind to fill in. Read that one if you're
an agent; this README is the human-facing tour.

## The base template

Underneath the datalib skill, this repo is an ordinary
[default-workspace-template](https://github.com/imbue-ai/default-workspace-template)
tree -- a persistent Claude agent that delegates work to sub-agents and manages
its own background services. The pieces most worth knowing:

- `CLAUDE.md` -- agent instructions
- `parent.toml` -- upstream repo, for pulling template updates
- `.agents/skills/` -- the agent's skills, including `datalib` itself
- `supervisord.conf` -- background service definitions
- `vendor/mngr/` -- a vendored, mutable copy of `mngr`; changes here do affect
  the `mngr` command
- `vendor/tk/` -- the vendored [tk](https://github.com/wedow/ticket) ticket
  tracker, backing the agent's task management

The template's own docs cover the rest (sub-agent create templates, the artifact
harden lifecycle that promotes ad-hoc work into tested skills, and the update
flow).
