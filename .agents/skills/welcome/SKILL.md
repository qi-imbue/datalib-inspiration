---
name: welcome
description: Greet the user when a new project starts. This mind was created from the datalib -- your personal data, searchable template, so the welcome introduces that template and immediately starts the adaptation conversation.
---

# Welcome the user (template: datalib -- your personal data, searchable)

This mind was created from a template -- a published snapshot of apps
another mind built:

- Title: datalib -- your personal data, searchable
- Slug: `datalib`
- Description: Mirror your own data (Slack, email, GitHub, Notion, chat history) into a private local store, and let the mind search and answer questions from it.
- Manifest: `template.md` (at the repo root, with `template.toml` beside it)

Do ALL of the following in your FIRST response, in the same turn, without
waiting to be asked:

1. Open with a short CUSTOM welcome that names **datalib -- your personal data,
   searchable** and gives the one-line description above. Do NOT use a generic
   "Welcome to Minds" greeting and do NOT offer a generic suggestions list.
2. Immediately read `template.md` at the repo root (reading the
   manifest in the first turn is required).
3. In plain, non-technical language, present what the template is and
   what it needs from the user -- name the manifest's activation requirements
   (which of their accounts it can mirror: Slack, email, GitHub, Notion). Then
   ask whether they want to hook it up to their own data now, and to which
   source(s) (e.g. "Want me to start by mirroring your Slack, or your email?").
   End your first response on THAT question. This is the `use-template`
   skill's template path; the manifest's "How to adapt it" section is the full
   script: if they say yes, ACTIVATE FIRST -- initiate the relevant
   `requires_permission` via a latchkey permission request, run the first
   sync, get the store showing THEIR OWN DATA (that is the definition of
   working; a running service is not), invite them to try a search or open the
   Datalib tab -- and only then ask how they want to adapt it.

This repo holds exactly one template. If `template.toml` lists
`[[lineage]]` entries, those are the templates this one was built on --
each with the repo URL and commit it was taken at, so you can go read any of
them at the exact state that was used. They are provenance, not something to
adapt here.
