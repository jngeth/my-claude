---
name: review-architecture
description: Find deepening refactors, written to a Markdown review. Use to improve architecture or testability.
---

# Review Architecture

Surface architectural friction and propose **deepening opportunities**: refactors turn shallow modules into deep ones.
The aim is testability and AI-navigability. The output is a Markdown review, not a change to the code.

## Glossary

Use these terms exactly in every suggestion. Consistent language is the point. Don't drift into "component," "service,"
"API," or "boundary." Full definitions in [references/language.md](references/language.md).

- **Module**: anything with an interface and an implementation (function, class, package, slice).
- **Interface**: everything a caller must know to use the module: types, invariants, error modes, ordering, config.
- **Implementation**: the code inside.
- **Depth**: leverage at the interface, a lot of behaviour behind a small interface. **Deep** = high leverage.
  **Shallow** = interface nearly as complex as the implementation.
- **Seam**: where an interface lives, where behavior can be altered without editing in place. Use this, not "boundary."
- **Adapter**: a concrete thing satisfying an interface at a seam.
- **Leverage**: what callers get from depth.
- **Locality**: what maintainers get from depth: change, bugs, and knowledge concentrated in one place.

Key principles (see [references/language.md](references/language.md) for the full list):

- **Deletion test**: imagine deleting the module. If complexity vanishes, it was a pass-through.
  If complexity reappears across N callers, it was earning its keep.
- **The interface is the test surface.**
- **One adapter is a hypothetical seam. Two adapters is a real seam.**

The skill is _informed_ by the project's domain model. The domain language gives names to good seams.

## Process

### 1. Explore

Read the project's domain language first. If the repo has `wiki/`, skim it and read the pages relevant to areas you're
touching, since that is the authoritative project context. If there is no `wiki/`, read what glossary or design notes
exist, and otherwise take domain nouns straight from the code. Degrade gracefully: a missing wiki is not an error.

Then use the Agent tool with `subagent_type=Explore` to walk the codebase. Don't follow rigid heuristics. Explore
organically and note where you experience friction:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow**, interface nearly as complex as the implementation?
- Where have pure functions been extracted for testability, but real bugs hide in how they're called (no **locality**)?
- Where do tightly-coupled modules leak across their seams?
- Which parts are untested, or hard to test through their current interface?

Apply the **deletion test** to anything you suspect is shallow: would deleting it concentrate complexity, or just move
it? A "yes, concentrates" is the signal you want.

For classifying each candidate's dependencies and how it would be tested across its seam, see
[references/deepening.md](references/deepening.md).

### 2. Write the Markdown review

Write a single Markdown file to the OS temp directory so nothing lands in the repo. Resolve the temp dir from `$TMPDIR`,
falling back to `/tmp`, and write to `<tmpdir>/review-architecture_<project>_<timestamp>.md` where:

- `<project>`: basename of the current working directory (`basename "$PWD"`).
- `<timestamp>`: current local time in ISO-8601 to the minute, from `date +%Y-%m-%dT%H:%M`.

Example: `review-architecture_my-project_2026-06-07T16:55.md`. Tell the user the full path where it landed.

Each candidate gets a section with a before/after Mermaid diagram. Use the domain vocabulary from the wiki for the
domain, and [references/language.md](references/language.md) vocabulary for the architecture. If the wiki defines
"Order," talk about "the Order intake module," not "the FooBarHandler" and not "the Order service."

See [references/report-format.md](references/report-format.md) for the section template, Mermaid patterns, and closing
Top recommendation.

Do NOT propose interfaces yet. After the file is written, ask the user: "Which of these would you like to explore?"

### 3. Grilling loop

Once the user picks a candidate, drop into a grilling conversation. Walk the design tree with them: constraints,
dependencies, the shape of the deepened module, what sits behind the seam, what tests survive.

Side effects happen inline as decisions crystallize:

- **Naming a deepened module after a concept not in the wiki?** Add the term: invoke the `wiki` skill to record it and
  log the ingest. Keep durable domain knowledge in the wiki, not in chat history.
- **Sharpening a fuzzy term during the conversation?** Update the wiki page through the `wiki` skill.
- **User rejects the candidate with a load-bearing reason?** Offer to record it: _"Want me to note this in the wiki so
  future reviews don't re-suggest it?"_ Only offer when a future explorer would need the reason to avoid re-suggesting
  the same thing. Skip ephemeral reasons ("not worth it right now") and self-evident ones.
- **Want to explore alternative interfaces for the deepened module?** See
  [references/interface-design.md](references/interface-design.md).
