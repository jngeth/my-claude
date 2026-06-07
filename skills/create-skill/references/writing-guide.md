# Skill Writing Guide

Detailed guidance on writing a SKILL.md and organizing bundled resources. Read this when drafting or revising a skill.

---

## Anatomy of a skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── agents/     Subagent prompts (advanced)
    ├── assets/     Files used in the skill's output
    ├── references/ Docs loaded into context as needed
    ├── scripts/    Executable code (Python/Bash/etc.)
    └── subskills/  Focused instruction files a dispatcher routes to
```

### agents/

Markdown prompts for subagents the skill spawns. This skill's own `agents/*.md` are examples.

### assets/

Files used **in the skill's output** not loaded into Claude's context.

- **Include when**: Skills produces output that incorporates a template, image, font, or other binary/text artifact.
- **Examples**: `assets/tracker.csv` CSV. `assets/slides.pptx` template, `assets/logo.png` brand asset.

### references/

Documentation Claude loads on demand to inform its work.

- **Include when**: Documentation is useful but only applies in a subset of invocations (e.g. one schema per database).
- **Examples**: `references/api_docs.md` for an API spec, `references/policies.md` for company policy.
- **Best practice**: If a reference is >250 lines, break it up. If it's >10k words, suggest grep patterns in SKILL.md.
- **Avoid duplication**: Information lives in either SKILL.md or references, not both. Default to references for detail.
  Keep SKILL.md to procedural instructions and pointers.

### scripts/

Executable code for tasks that need determinism or are repeatedly rewritten.

- **Include when**: The same code would be re-written every invocation, or determinism matters
  (numerical accuracy, file format manipulation, deterministic side effects).
- **Example**: `scripts/align_tables.py` for table alignment tasks.
- **Benefit**: Token-efficient scripts can execute without being loaded into context.

### subskills/

Focused instruction files for a **dispatcher** type skill: a SKILL.md that routes to distinct sub-tasks rather than
running one workflow. Each subskill is a plain markdown file (`subskills/<name>.md`) with no frontmatter. Subskills are
never triggered on their own; the parent SKILL.md selects one via its routing table, then that file takes over.

- **Include when**: one SKILL.md would stack several unrelated workflows that don't share context (e.g. a `pdf` skill
  that rotates, merges, and OCRs). Each route only needs its own slice of instructions.
- **Don't include when**: variants share most logic or a variant is substantial and reusable enough to be its own skill.
  For share-most-logic case, keep one SKILL.md with a decision tree; for fully-fledged case, ship a separate skill.
- **Subskill vs reference**: a `reference/` doc is passive knowledge (an API spec, a schema) dispatcher reads to inform
  its own work. A subskill is an active set of instructions that _replaces_ dispatcher's workflow for that branch.

#### The routing table

Put the routing table in **SKILL.md**, not a separate file. It loads when the skill triggers, so the dispatcher routes
with no extra read. Map an observable condition to one file:

```markdown
## Routing

| When the user...                          | Load                  |
| ----------------------------------------- | --------------------- |
| wants to rotate or reorient a PDF         | `subskills/rotate.md` |
| wants to merge or split PDFs              | `subskills/merge.md`  |
| has a scanned PDF needing text extraction | `subskills/ocr.md`    |
```

Keep conditions mutually exclusive and phrased as what the user wants, not internal jargon, so the match is unambiguous.
After routing, the dispatcher reads only the chosen subskill.

---

## Progressive disclosure

Skills use a three-level loading system to manage context efficiently:

1. **Metadata (name + description)** always in context (~100 words across all installed skills)
2. **SKILL.md body** loaded when the skill triggers (target <250 lines)
3. **Bundled resources** loaded as Claude needs them (effectively unlimited)

**Patterns:**

- Keep SKILL.md under ~250 lines. Approaching the limit? Add a layer of hierarchy and link out.
- Reference each bundled file from SKILL.md with a one-liner about **when** to read it.
- For multi-variant skills (e.g. cloud-deploy across AWS/GCP/Azure), structure as:

```
cloud-deploy/
├── SKILL.md       (workflow + variant selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

Claude reads only the relevant variant.

---

## Writing style

Always use the `writing-voice` skill. It covers surface prose style and skill-specific principles.
Load it when drafting or editing any SKILL.md content.

---

## Naming the skill

`name` is kebab-case, ≤64 chars, matching the directory. Beyond the mechanics, name it for what it _does_:

- **Verb-first or gerund:** `analyze-logs` , `create-invoices`, `rotate-pdf` beat noun blobs like `invoice-tool`.
- **Name the action or core insight, not the implementation:** `condition-based-waiting` over `async-helpers`.
- **Avoid vague catch-alls:** `docs`, `helper`, `tools` `utils` say nothing about when to reach for the skill.

The name is a second triggering signal after description: it shows in the skills list and shapes the relevance guess.

---

## Description: the triggering mechanism

The `description` field is the **only** signal Claude uses to decide whether to invoke a skill. Write it to cover both:

- **What** the skill does
- **When** to use it concrete user phrases, file types, or contexts

Claude tends to **under-trigger** skills. Be a little pushy. Compare:

- Weak: `"How to build a simple fast dashboard."`
- Better: `"How to build a simple fast dashboard. Use whenever the user mentions dashboards or data visualization."`

Don't make it so pushy it triggers on adjacent-but-different tasks.
The optimization loop in `description-tuning.md` measures this directly.

**Use words Claude would search for.** Beyond the description, seed the body with literal error strings, symptoms
(`flaky`, `hanging`, `timeout`), file types and synonyms. `description-tuning.md` covers description keyword workflows.

---

## Degrees of freedom

Match how prescriptive the instructions are to how fragile the task is.

- **High (prose guidance):** many valid approaches, context decides. Give direction and trust Claude to route.
  Example: "Review the code for bugs, readability, and convention violations."
- **Medium (template or parameterized script):** a preferred pattern exists, some variation is fine.
  Example: a report skeleton Claude fills in, or `generate_report(data, format="md")`.
- **Low (exact command, no improvisation):** the task is fragile or order-dependent. Pin it:
  "Run exactly `python scripts/migrate.py --verify --backup`. Don't add flags."

Over-specifying an open task wastes context and boxes Claude in; under-specifying a fragile one invites the error.

---

## Writing patterns

### Defining an output format

```markdown
## Report structure

ALWAYS use this exact template:

# [Title]

## Executive summary

## Key findings

## Recommendations
```

### Examples block

```markdown
## Commit message format

**Example 1:**
Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication
```

### Decision tree

```markdown
## Choosing an approach

- If the input is a single PDF → use `scripts/single_pdf.py`
- If the input is a directory → use `scripts/batch_pdf.py`
- If the input includes scanned images → see `references/ocr.md` first
```

---

## Anti-patterns

These are structural. For prose-level anti-patterns (walls of MUST/NEVER, missing the why, examples that don't
generalize), the `writing-voice` skill is the home: see the "Writing style" section above.

- **Information duplicated between SKILL.md and a reference.** Pick one home.
- **Skipping `assets/`.** If the skill produces a templated output, ship the template, don't ask to recreate every time.
