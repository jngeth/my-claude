---
name: onboard
description: Orient at session start by reading handoff docs and project wiki. Use when opening or resuming a project.
---

# Onboard

## Overview

Get up to speed in a project without reading every wiki page. Read the latest handoff doc (if any) and a small,
targeted slice of the project wiki, then report the current state so work can start.

Pairs with two existing skills:

- `handoff` writes a session-summary doc to the OS temp dir. `onboard` reads it.
- `wiki` owns the project knowledge base at `wiki/`. `onboard` reads only what's needed; it never edits.

## When to use

Trigger phrases:

- "onboard me", "catch me up", "where were we", "resume", "what's the state of this project"
- The user opens a project and asks what's going on, or invokes this skill explicitly at the start of a session.

Skip when the user already has clear context for the task at hand, or when they've asked a specific narrow
question that doesn't need broad orientation.

## How to use

### 1. Find the latest handoff doc

The `handoff` skill writes files named `handoff_<project>_<YYYY-MM-DDTHH:MM>.md` to the OS temp dir. The ISO-8601
timestamp sorts lexically, so the latest is the last entry after a plain sort.

Resolve the project name and glob:

```bash
project=$(basename "$PWD")
ls "$TMPDIR"/handoff_"$project"_*.md /tmp/handoff_"$project"_*.md 2>/dev/null | sort | tail -1
```

(`$TMPDIR` is set on macOS; `/tmp` is the Linux default. Including both covers either OS without branching.)

If the glob returns nothing, skip to step 3. If the user wants an older handoff, list all matches and ask.

### 2. Read the latest handoff in full

Handoff docs are short by design: read the whole thing. Note especially:

- The "suggested skills" section (these may need to be invoked next)
- Any referenced file paths or URLs (don't open them yet; they're leads for later)
- Stated open questions or in-progress work

### 3. Check for a wiki

Look for `wiki/index.md` in the current working directory. If it's absent:

- Stop here.
- Tell the user there's no wiki to load and summarize what the handoff said (if anything).
- If neither handoff nor wiki exist, say so and ask what the user wants to work on.

### 4. Read the index and recent log activity

The index is the routing layer; the log head shows what's been touched recently (the log is newest-first).
Together they reveal what exists and what's active without reading any entity pages.

```bash
cat wiki/index.md
grep "^## \[" wiki/log.md | head -20
```

### 5. Pick a small set of pages to read

Cross-reference what the handoff covers with index categories and recent log entries. Read in full **only** pages that:

- The handoff references directly, OR
- The log shows as updated in the last few entries, OR
- Match the topic the user said they want to work on (if they said).

Cap at roughly 5 pages. Skip anything tangential. The point is targeted orientation; reading the whole wiki defeats it.

### 6. Report

One short paragraph covering:

- What the last session was doing
- What's open or in progress
- What was recently changed in the wiki
- A one-line suggestion for where to start

End with: **Ready. What do you want to work on?**

## Notes

- **Read-only.** Do not ingest, lint, or edit the wiki. Mutations go through the `wiki` skill.
- **Surface conflicts.** If the handoff and wiki disagree, call it out rather than guessing which is current.
- **No CLAUDE.md duplication.** Don't re-read or re-summarize it, the harness has already loaded it.
