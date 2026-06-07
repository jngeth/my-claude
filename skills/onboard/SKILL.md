---
name: onboard
description: Orient at session start. Identify handoff and plan docs, read wiki. Use when opening or resuming a project.
---

# Onboard

## Overview

Get up to speed in a project without reading everything up front. Identify the handoff and plan docs for this project,
read a targeted slice of the wiki, then report so work can start. Open a handoff or plan doc only when the user asks.

Pairs with three existing skills:

- `handoff` writes a session-summary doc to the OS temp dir. `onboard` surfaces it, but reads it only on request.
- `plan` writes an implementation plan to the OS temp dir. `onboard` surfaces it, but reads it only on request.
- `wiki` owns the project knowledge base at `wiki/`. `onboard` reads only what's needed; it never edits.

## When to use

Trigger phrases:

- "onboard me", "catch me up", "where were we", "resume", "what's the state of this project"
- The user opens a project and asks what's going on, or invokes this skill explicitly at the start of a session.

Skip when the user already has clear context for the task at hand, or when they've asked a specific narrow
question that doesn't need broad orientation.

## How to use

### 1. Find handoff and plan docs

The `handoff` and `plan` skills write working docs to the OS temp dir:

- `handoff_<project>_<YYYY-MM-DDTHH:MM>.md`
- `plan_<project>_<feature>_<YYYY-MM-DDTHH:MM>.md`

Resolve the project name and list both, newest last (the ISO-8601 timestamp sorts lexically):

```bash
project=$(basename "$PWD")
ls "$TMPDIR"/handoff_"$project"_*.md /tmp/handoff_"$project"_*.md 2>/dev/null | sort
ls "$TMPDIR"/plan_"$project"_*.md /tmp/plan_"$project"_*.md 2>/dev/null | sort
```

(`$TMPDIR` is set on macOS; `/tmp` is the Linux default. Including both covers either OS without branching.)

If both globs return nothing, skip to step 3.

### 2. Identify, don't open

List the docs found by filename: handoff timestamp, and each plan's feature and date. Do not read their contents.
They can be long, and the user may want a specific one. Treat them as leads, not required reading.

Open a doc only when the user names it or asks ("read the latest handoff", "open the auth plan"). Then read it in full.

### 3. Check for a wiki

Look for `wiki/index.md` in the current working directory. If it's absent:

- Stop here.
- Tell the user there's no wiki, and list the handoff and plan docs you found (unread).
- If no docs and no wiki exist, say so and ask what the user wants to work on.

### 4. Read the index and recent log activity

The index is the routing layer; the log head shows what's been touched recently (the log is newest-first).
Together they reveal what exists and what's active without reading any entity pages.

```bash
cat wiki/index.md
grep "^## \[" wiki/log.md | head -20
```

### 5. Pick a small set of pages to read

Read in full **only** pages that:

- The log shows as updated in the last few entries, OR
- Match the topic the user said they want to work on (if they said).

Cap at roughly 5 pages. Skip anything tangential. The point is targeted orientation; reading the whole wiki defeats it.

### 6. Report

One short paragraph covering:

- The handoff and plan docs available (filename)
- What the wiki shows as recently changed
- A one-line suggestion for where to start

End with: **Ready. Open a handoff or plan doc, or tell me what to work on?**

## Notes

- **Identify, don't open.** Surface the handoff and plan docs by name, but read one only when the user asks for it.
- **Read-only.** Do not ingest, lint, or edit the wiki. Mutations go through the `wiki` skill.
- **No CLAUDE.md duplication.** Don't re-read or re-summarize it, the harness has already loaded it.
