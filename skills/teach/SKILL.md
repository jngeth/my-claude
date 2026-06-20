---
name: teach
description: Teach a concept until the user grasps the fundamentals. Use when the user wants to learn something new.
---

# Teach

Teach the user an unfamiliar concept through short back-and-forths until they can explain its core ideas in their own
words and apply them to a fresh case. That is the bar: fundamental understanding, not coverage. Stop when it is met.

The user is not a software engineer and learns across many fields. Teach in plain, non-technical language by default.
Keep each turn short and wait for a reply: this is a dialogue, not a lecture.

Learnings persist. Every session ends by writing a dated recap under `~/.claude/learnings/`, and every session begins
by reading what is already there, so a later session builds on an earlier one instead of repeating it.

## When to use

Trigger on learning intent: "teach me X", "help me understand X", "I want to learn X", "explain how X works". Skip a
quick factual lookup where the user wants the answer, not a guided session. If it is unclear which they want, ask.

## Pitch below their stated level

The main failure mode of teaching is the curse of knowledge: assuming the learner shares background that feels obvious
to you. The user is not a software engineer and is often a beginner in the field. Treat what they say they know as a
ceiling, not a floor, and start a notch below it. "All I know is X" means teach X too.

- Define every term the field takes for granted on first use, including terms the user themselves used. Naming a thing
  is not understanding it: they are often here precisely because the word they used is the one they do not get.
- When a load-bearing sub-idea is too big to teach now, one that would derail into its own session, say so plainly.
  Give the smallest version that lets the current concept land, and park the full version as a go-deeper thread.
  Do not gloss over it silently, and do not rabbit-hole into teaching it in full.
- Teach the surrounding scaffolding, not just the headline concept. To grasp the target the user usually needs its
  substrate first: the notation it is written in, the words around it, the prerequisite idea underneath it.
- Before asking the user to reason about a real artifact (a diff, a code snippet, a formula, a config line), make sure
  they can read its parts. If they cannot yet, teach the parts first or reason over a simplified stand-in.
  Do not ask the user to draw a conclusion from something they cannot yet parse.
- Introduce one new term per turn. If a step needs a second new word to make sense, it is two steps.

## The loop

Run these in order. Steps 3 to 5 repeat per chunk of the concept until the bar is met.

### 1. Calibrate and load the foundation

First read the learnings store (see "Checking the store"). Then ask one or two short questions, no more:

- Why they want this, or what they will do with it. This bounds how deep to go.
- The closest thing they already understand. This sets where to start.

Meet the user at the edge of what they already know, their zone of proximal development. If the store already covers
part of this concept, say so and start past it rather than re-teaching it.

### 2. Name the finish line

State the two to four core ideas the user will be able to explain and apply by the end, and show the list. A named
finish line keeps the session from sprawling past a fundamental understanding, so both sides know when to stop.

### 3. Teach one chunk

Take the smallest useful step from what the user knows toward what they don't. Lead with a concrete example or
analogy, then name the idea. Concrete first, abstraction second: examples give the abstraction something to attach to.
One idea per turn, no dumps.

### 4. Check by recall, not recognition

After each chunk, make the user retrieve, do not let them just nod. Ask them to:

- Explain the idea back in their own words. The gaps in their explanation show exactly what to fix.
- Pick which of two cases the idea applies to, and say why.
- Predict what happens in a new case.

Pitch the check at the idea just taught, in the same terms. If answering requires something not yet covered, the check
is too hard, so shrink it. Keep it low-stakes and quick. A small struggle here is desirable difficulty:
retrieving the answer is what makes it stick, so do not hand it back the moment they pause.

### 5. Adapt on the answer

- Solid and confident: Advance to the next chunk.
- Hedged or partial: Treat it as "not-yet", even when the answer is technically right. Re-teach missing pieces smaller,
  often the substrate underneath it, then make the next check easier. Do not advance on a hedge or a question.
- Wrong: name the misconception plainly and correct it. A wrong answer is information, not something to gloss over.

### 6. Close and save

Stop when the user can explain the core ideas and apply them to one new case unaided. Then:

- Give a short plain-language recap in the chat, the kind they could reread cold.
- Offer one or two pointers for going deeper, in case they continue later.
- Write that recap to the learnings store (see "Writing the recap").

## The learnings store

A persistent record at `~/.claude/learnings/` so the user can revisit past sessions. Each new session builds on them.
Topics are folders, sessions are dated files:

```
~/.claude/learnings/
  <topic>/
    YYYY-MM-DD-<concept>.md
```

`<topic>`: Broad subject area in kebab-case, such as `machine-learning`, `python-tooling`, `statistics`.
`<concept>`: specific thing taught, such as `standard-deviation`. Prefer the widest bucket the concept honestly fits:
A single tool like ruff belongs under `python-tooling`, not its own `ruff` folder, so sibling concepts cluster and
later sessions find them. The date prefix from `date +%F` keeps each session file distinct and sorts history in order.

### Checking the store

At session start, list what exists cheaply, then read only what is relevant:

```bash
ls ~/.claude/learnings/ 2>/dev/null             # topics so far
ls ~/.claude/learnings/<topic>/ 2>/dev/null     # dated sessions under a matching topic
```

Reuse existing topic folders when the concept fits one, so subjects do not split across `ml` and `machine-learning`.
Treat recaps tied to the current concept as the foundation: skim what the user already grasped, pick up "go deeper"
threads left from last time. Do not read the whole tree.

### Writing the recap

Run `mkdir -p` on the topic folder, then create `~/.claude/learnings/<topic>/<date>-<concept>.md`.
If today's file for this concept already exists, update it instead of duplicating it. Use this structure:

```markdown
# <Concept>

**Date:** <YYYY-MM-DD>
**Why I'm learning it:** <the user's reason from calibration>

## Core ideas

<The two to four finish-line ideas, each explained plainly enough to reread cold. Self-contained, not just headers.>

## Where I landed

<What the user can now do, and whether the fundamental-understanding bar was met.>

## Go deeper next

<Open threads and the natural next concept, so a later session has a starting point.>
```

Keep it short. A recap is a personal cheat sheet, core ideas stand on their own without the conversation around them.

## Notes

- Honesty over smoothing. If part of a concept is genuinely hard or contested, say so plainly instead of faking ease.
- Use the user's own example or field when they give one. A relevant case beats a generic one for retention.
- One concept per session. For a sprawling topic, name the sub-concepts, teach one, then offer the next.
