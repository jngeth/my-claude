---
name: writing-voice
description: User's writing voice. Plain, declarative, no em-dashes, no flavor. Use for prose, docs, markdown.
---

# Writing Voice

The user prefers writing that is plain, declarative, and direct. Apply this voice to any user-facing prose: README
files, SKILL.md, doc edits, PR descriptions, summaries, anything the user will read or publish.

## Core principles

Five principles cover most of the editing:

1. **Punctuation: colon or period, never em-dash.** Em-dashes hide structure; colons reveal it. Em-dashes are banned.
2. **Cut flavor, keep instruction.** Anecdotes, jokes, voicy framing, rhetorical flourishes go first. The rule stays.
3. **Plain over voicy.** Prefer direct assertion to performative phrasing.
4. **Alphabetize lists.** Sort every list alphabetically. The exception is a list whose order is itself meaningful.
5. **Pack lines toward 120 characters.** Combine short consecutive lines.
   If a wrap leaves one or two orphan words on the next line, trim the previous line so they fit.

For the full set with concrete before/after examples, load `subskills/markdown.md`.

## When writing skill instructions

Four additional principles apply when the content is a SKILL.md or skill reference file:

1. **Imperative voice.** "To do X, do Y" not "you should do X" or "if you need to do X."
2. **Explain the why.** Justify instructions instead of stacking ALWAYS/NEVER. Rules with rationale survives edge cases.
3. **Theory of mind.** Lead with what's non-obvious: quirks, gotchas, hidden constraints. Skills are reas cold.
4. **Generalize.** Skills run across many contexts. Resist hard-coding rules that only fix examples in front of you.

## When writing markdown

Load `subskills/markdown.md` whenever drafting or editing markdown: SKILL.md, README, documentation, technical
writing, PR descriptions formatted in markdown. It has the full principle list with worked examples.

## Markdown tables

Whenever you create or edit a markdown table, run `scripts/align_tables.py` on the file so the columns line up.
It measures display width, so emoji, CJK text, and combining marks stay aligned where a `len()`-based pass drifts.
It rewrites only table blocks and leaves the rest of the file untouched.

- Print the aligned result: `python3 scripts/align_tables.py <file>`
- Rewrite in place: `python3 scripts/align_tables.py -w <file>`

It preserves each column's alignment: plain `| --- |` stays plain, and `:--`, `:-:`, `--:` keep their colons.

## Out of scope

- Code comments. System rules govern those (default: no comments).
- Internal tool descriptions and JSON config. Keep functional, not stylized.
- Apply the voice only to text you produce or text the user has asked you to edit, not what the user writes.

## Quick check before shipping any prose

- Is any sentence mostly flavor?
- Could any example be half as long?
- Any em-dashes? Replace with a colon or period.
- Could any short consecutive lines pack into one near 120 chars?
- Is any list out of alphabetical order? Sort it unless the order is meaningful.
- Any orphan one-or-two-word lines that could be absorbed by trimming the line above?
- Are any bullets or sentences removable without breaking the surrounding instruction?
