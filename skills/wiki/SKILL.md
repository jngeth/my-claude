---
name: wiki
description: Maintains a per-project markdown wiki. Use whenever user mentions ingesting, querying or linting notes.
---

# Wiki

## Overview

A wiki is a per-project knowledge base of LLM-written markdown pages built incrementally as sources are processed.
The pattern (adapted from Karpathy's "LLM Wiki"): read each source once, integrate it into the existing pages, never
re-derive on every query. The wiki compounds; the maintenance cost stays near zero because the LLM does the bookkeeping.

The wiki is the only artifact. Sources are read in place (local files, URLs, pasted text, prior conversations) and never
copied into the project. The wiki captures what's worth keeping; originals stay wherever they live. Citations point out
to those originals via footnotes, not into a duplicated `raw/` directory.

This skill performs five operations on a wiki in the current directory: `init`, `ingest`, `query`, `lint`, `search`.

## When to use

Trigger phrases:

- "add this to the wiki", "ingest <file>", "wikify this"
- "ask the wiki", "what does the wiki say about X", "query the wiki"
- "lint the wiki", "check the wiki for orphans / broken links"
- "init a wiki here", "set up a wiki for this project"
- "search the wiki for <term>"

Use when the user is accumulating knowledge over time: research, journals, project documentation, competitive analysis.
Skip for one-off summarization, code edits, or transient questions where nothing should persist.

## Wiki layout

A project with a wiki has:

```
<project-root>/
  wiki/
    index.md        # content catalog: links + one-line summaries by category
    log.md          # append-only operation log
    <pages>.md      # entity, concept, synthesis pages
```

Discover the layout by checking for `wiki/` in cwd. If absent, run `init` first or ask the user where the wiki lives.

## Operations

### init

Scaffold a new wiki in the cwd.

1. Create `wiki/`.
2. Write `wiki/index.md` and `wiki/log.md` using `references/page-templates.md`.
3. Write the first log entry: `## [<today>] init | wiki scaffolded`.
4. Tell the user where the wiki lives.

### ingest `<source>`

Integrate a source into the wiki. The source is read in place, never copied. Only content distilled into pages persists.
Single sources typically touches 5–15 pages. Cross-references and synthesis are what justify the wiki over plain RAG.

1. Read the source (local file, URL, pasted text, prior conversation).
2. Discuss takeaways briefly with the user: what's important, what entities and concepts appear, what contradicts or
   extends prior pages. Confirm direction before writing if the source is large or the wiki is mature.
3. For each entity and concept the source touches:
   - **Existing page**: add new facts with a footnote citation pointing at the source. If a fact contradicts existing
     claims, flag the contradiction inline rather than overwriting. The wiki should make tensions visible, not hidden.
   - **No page yet**: create one only if the entity/concept is significant enough to recur. Incidental mentions can
     stay as `[[Page Name]]` links that don't resolve yet. Use `lint` to surfaces unresolved links so they aren't lost.
4. Update `wiki/index.md`: add lines for any new pages in the right category.
5. Prepend a log entry to `wiki/log.md` (newest first):

   ```md
   ## [YYYY-MM-DD] ingest | <source title>

   - Source: <path | url | "conversation YYYY-MM-DD" | other identifier>
   - New: <list of new pages>
   - Updated: <list of updated pages>
   - Notes: <one line on what changed in the synthesis>
   ```

6. End with a one-paragraph summary of what changed and how many pages were touched, so the user can spot-check.

### query `"<question>"`

Answer a question against the wiki.

1. Read `wiki/index.md` first. It's the routing layer: at small/medium scale it does the job of an embedding index.
2. Identify relevant pages from the index and read them in full.
3. If the index doesn't cover the topic, run `scripts/search.sh "<term>"` for keyword matches across all wiki pages.
4. Synthesize an answer with citations to the `[[wiki pages]]` you used. Footnotes point at the original sources.
5. After answering, ask whether to file the answer back as a new page under `wiki/synthesis/`. Good answers compound
   the wiki the same way ingested sources do. Don't lose them to chat history.
6. Prepend a log entry: `## [YYYY-MM-DD] query | <short question>`.

### lint

Run a wiki health check.

1. Run `scripts/lint.py wiki` and read the markdown report it prints.
2. On top of the script's findings, scan for things only an LLM can catch:
   - **Contradictions**: pages making opposing claims about the same fact.
   - **Stale claims**: pages superseded by newer ingests; cross-reference with `log.md`.
   - **Missing concepts**: terms recurring across many pages without a page of their own.
   - **Suggested follow-ups**: gaps a web search or new source could fill.
3. Report findings as a markdown summary. Propose specific fixes. Do not auto-apply edits without confirmation.
   Small mechanical fixes (a broken link with an obvious target) are fine to apply directly with a one-line note.
4. Prepend a log entry: `## [YYYY-MM-DD] lint | <one-line summary>`.

### search `"<term>"`

Run `scripts/search.sh "<term>"` and return the matches. Used internally by `query` and `lint`; also exposed for
ad-hoc grepping.

## Conventions

- **Voice**: use the `writing-voice` skill when writing or editing any page. The wiki is user-facing prose, it
  should match their voice, not a default LLM one.
- **Links**: Obsidian-style `[[Page Name]]`. Optional alias: `[[Page Name|alias text]]`. Use these for every
  reference between wiki pages. They make the graph navigable in Obsidian and let `lint.py` detect orphans.
- **Citations**: each page carries numbered footnotes for the sources its facts came from. Use `[^1]`, `[^2]`, ...
  inline next to the claim; define them at the bottom of the page as `[^N]: <source identifier>, ingested YYYY-MM-DD`.
  Source identifiers are external references, not wiki pages. Footnotes accumulate as sources reinforce a claim.
- **Filenames**: page filename matches the link text. `[[Acme Corp]]` → `Acme Corp.md`. Spaces are fine; Obsidian
  handles them. Pick one style and stay consistent within a vault.
- **Log format**: entries are newest-first. Every entry starts with `## [YYYY-MM-DD] <op> | <title>` so
  `grep "^## \[" wiki/log.md | head -N` returns the N most recent. The prefix is load-bearing; don't improvise.
- **Date**: use the actual current date. Run `date +%Y-%m-%d` if unsure.
- **One source, many edits**: when an ingest touches 10+ pages, show the user a summary so they can audit.
- **Empty `[[links]]` are fine**: a link to a page that doesn't exist yet is a to-do-write-this marker, not an error.

## Resources

- `references/page-templates.md`: starter formats for `index.md`, `log.md`, entity, concept, and synthesis pages.
  Read when initializing a wiki or writing a page type for the first time.
- `scripts/lint.py`: wiki health check. Reports broken `[[links]]`, orphans, stubs, pages missing from `index.md`.
  Markdown output to stdout.
- `scripts/search.sh`: ripgrep wrapper for searching `wiki/` content. Used by `query` and `lint`.
