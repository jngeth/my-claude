---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
---

Write a handoff document summarising the current conversation so a fresh agent can continue the work.
Save to the temporary directory of the user's OS, not the current workspace.

Name the file `handoff_<project>_<timestamp>.md` where:

- `<project>`: basename of the current working directory (`basename "$PWD"`).
- `<timestamp>`: current local time in ISO-8601 to the minute: `YYYY-MM-DDTHH:MM`, generate with `date +%Y-%m-%dT%H:%M`.

Example: `handoff_my_project_2026-05-31T14:32.md`.

## Mine the conversation first

Before writing, read back through the conversation and extract each of these.
The next session pays to rediscover anything you skip, so be thorough:

- Goal: what the user is trying to achieve and why.
- Work completed: every file, function, and config changed, with specifics.
- Approaches tried: chronological, both successful and abandoned.
- User feedback: corrections, preferences, frustrations, requests.
- Failed approaches: the most expensive thing to rediscover.
- Decisions made and alternatives rejected.
- Discoveries and gotchas.
- Open questions and dependencies on other work.

## Structure

Use these section headings so the next session knows where to look. Omit a section only when it has no content.

```markdown
# <one-line summary of the work>

**Date:** <YYYY-MM-DD>
**Status:** <COMPLETED | IN PROGRESS | BLOCKED>

## The Goal

<3-5 sentences: the objective, why it matters, the end state.>

## Where We Are

<Current state: files and functions changed, what works, what does not.>

## What We Tried

<Every approach in order: hypothesis, change, result with numbers, why kept or abandoned.>

## Key Decisions

<Each non-obvious decision and why, including alternatives rejected.>

## User Feedback

<Corrections, preferences, and direction the user gave. This calibrates the next session.>

## Where We're Going

<Ordered next steps.>

## Quick Start

<Exact files to read first and single most important next action, so next session starts without re-deriving context.>

## Suggested Skills

<Skills the next agent should invoke.>
```

## Rules

- Redact sensitive information: API keys, passwords, personally identifiable information.
- Do not duplicate content already captured in other artifacts. Reference them by path or URL instead.
- If a section reads thin, mine the conversation again before settling. Thin usually means missed, not absent.
- If the user passed arguments, treat them as the focus for the next session and frame the doc around it.
