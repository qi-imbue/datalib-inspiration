---
name: welcome
description: Greet the user when a new project starts. This mind was created from the "datalib -- your personal data, searchable" inspiration, so the welcome introduces that inspiration and immediately starts the adaptation conversation.
---

# Welcome the user (inspiration: datalib -- your personal data, searchable)

This mind was created from an inspiration -- a published snapshot of a capability
another mind built:

- Title: datalib -- your personal data, searchable
- Slug: `datalib`
- Description: Mirror your own data (Slack, email, GitHub, Notion, chat history) into a private local store, and let the mind search and answer questions from it.
- Manifest: `inspiration-datalib.md` (at the repo root)

Do ALL of the following in your FIRST response, in the same turn, without waiting
to be asked:

1. Open with a short CUSTOM welcome that names **datalib -- your personal data,
   searchable** and gives the one-line description above. Do NOT use a generic
   "Welcome to Minds" greeting and do NOT offer a generic suggestions list.
2. Immediately read `inspiration-datalib.md` at the repo root (reading the
   manifest in the first turn is required).
3. In plain, non-technical language, present what the inspiration is and what it
   needs from the user -- name the manifest's "Prerequisites" (which of their
   accounts it can mirror: Slack, email, GitHub, Notion). Then ask whether they
   want to hook it up to their own data now, and to which source(s) (e.g. "Want
   me to start by mirroring your Slack, or your email?"). End your first response
   on THAT question. This is the `use-inspiration` skill's template path; the
   manifest's "How to adapt it" section is the full script: if they say yes,
   ACTIVATE FIRST -- initiate the relevant `requires_permission` via a latchkey
   permission request, run the first sync, get the store showing THEIR OWN DATA
   (that is the definition of working; a running service is not), invite them to
   try a search -- and only then ask how they want to adapt it.

If this repo has accumulated several `inspiration-*.md` manifests, the one named
above is the latest; treat the others as reference (they were likely already
adapted upstream).
