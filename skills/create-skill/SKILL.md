---
name: create-skill
description: Build, edit, evaluate, and tune Claude skills. Use whenever the user wants to create or improve a skill.
---

# Create Skill

Help a user create and iterate on Claude skills. A skill is a self-contained directory with a `SKILL.md`
(YAML frontmatter + markdown instructions) plus optional `assets/`, `scripts/` and `references/` subdirectories.

Figure out which step below the user is on and jump in. They might arrive with nothing ("I want a skill for X"),
a half-built draft, or feedback after running an existing skill. Meet them where they are.

---

## Step 1: Capture intent

If the conversation already contains the workflow the user wants to bottle, mine it first: What tools they used,
the sequence, corrections they made, input/output formats. Fill gaps with these questions (don't dump all at once):

1. What should this skill enable Claude to do?
2. When should it trigger? (what user phrases or contexts)
3. What's the expected output format?

## Step 2: Baseline the gap

Before writing, find out what Claude gets wrong without the skill. Skip when the gap is obvious from the conversation.

Run the task cold (no skill) with a throwaway subagent and watch two things:

- **Where it fails or guesses:** wrong defaults, missing domain knowledge, skipped steps. These become instructions.
- **What it rewrites from scratch:** helper scripts, boilerplate, the same lookup. These become `scripts/` or `assets/`.

Close the gaps you observed, not the ones you imagine: a skill fixing a problem Claude doesn't have is wasted context.
The rigorous with-skill/without-skill measurement comes later at test time (Step 6, `references/eval-loop.md`).

## Step 3: Plan reusable contents

For each concrete example, ask: how would Claude execute this from scratch? What would be rewritten every time?
That's the candidate list for `assets/`, `references/`, or `scripts/`.

- **assets/** files used in the skill's output (templates, fonts, boilerplate)
- **references/** docs loaded on demand (schemas, API specs, policies)
- **scripts/** deterministic code reused per task (e.g. `rotate_pdf.py`)
- **subskills/** focused instruction files for a dispatcher skill that routes to several unrelated sub-tasks

See `references/writing-guide.md` for the full anatomy, when to use each directory, and the dispatcher pattern.

## Step 4: Initialize

```bash
python3 ~/.claude/skills/create-skill/scripts/init_skill.py <skill-name> --path ~/.claude/skills \
    [--scripts] [--references] [--assets] [--subskills]
```

This creates the directory and a `SKILL.md` with TODO placeholders. Subdirectories are **opt-in**: pass a flag only for
each one the skill in Step 3 actually needs. With no flags, only `SKILL.md` is created. `--subskills` also adds a
routing-table stub to `SKILL.md` for the dispatcher pattern. You can always add a directory by hand later.
`~/.claude/skills` is symlinked to `my-claude/skills/`, so new skills land in the repo automatically.

## Step 5: Edit the skill

Write the skill for **another instance of Claude** that will read it cold. Lead with what's not-obvious:
procedural knowledge, domain quirks, gotchas.

**Start with the bundled resources** identified in Step 3, then write `SKILL.md` to reference them.
Often the user needs to provide assets (brand files, templates) or knowledge (schemas, policies) at this point, ask.

**Frontmatter:**

- `name` kebab-case, ≤64 chars; must match the directory name. Name it for what it does (verb-first), not a catch-all
- `description` single line, third person, **max 120 chars including the `description:` field name itself**.
  Convey both **what** the skill does AND **when** to trigger. Claude tends to under-trigger. Name concrete
  contexts and keywords. No angle brackets (`<`/`>`); the validator rejects them.

Pre-tuning examples (rough drafts to start from; refine in Step 7):

- Bad: `description: How to build a dashboard`
- Good: `description: Build dashboards. Use whenever the user mentions metrics, KPIs, or charts.`
- Bad: `description: Helps with PDFs`
- Good: `description: Extract text/tables from PDFs. Use when user mentions PDFs or document extraction.`

**Body:** imperative voice ("To do X, do Y"), not second person. Explain the **why** behind instructions instead of
stacking ALWAYS/NEVER. Modern models reason well when they understand intent. Avoid time-sensitive content
(model versions, "currently", dated feature lists): it rots fast. See `references/writing-guide.md`.

**Validate as you go:**

```bash
python3 ~/.claude/skills/create-skill/scripts/quick_validate.py <skill-dir>
```

## Step 6: Test on real prompts

Draft 2-3 prompts a real user would actually type. Run them and review outputs with the user. The full loop with
subagents, grading, benchmarking, and the HTML viewer lives in `references/eval-loop.md`. Read it before running tests.

Quick version (lightweight iteration): execute each test prompt yourself using the skill, show the output to the user.

## Step 7: Tune the description (optional but high-leverage)

The `description` field is the **only** thing Claude sees when deciding to invoke a skill, so it's worth optimizing
once the skill works. Workflow: generate trigger eval queries, review them with the user, run an optimization loop.
The workflow lives in `references/description-tuning.md`.

---

## Anatomy of a skill

A skill is `SKILL.md` plus optional `agents/`, `assets/`, `references/`, `scripts/`, and `subskills/` subdirectories,
each opt-in. `init_skill.py` scaffolds only the ones you pass flags for (see Step 4); add others by hand later. For the
full tree, when to use each directory, and progressive-disclosure guidance (keep `SKILL.md` under ~250 lines), see
`references/writing-guide.md`.

## Iteration

After testing, the user gives feedback. Generalize from it; don't add fiddly overfit MUSTs that only fix the example.
Keep the skill lean; explain the **why**. If you notice all test runs reinventing the same helper script, bundle it.
Repeat until the user is satisfied or feedback dries up.

For full iteration mechanics (iteration directories, snapshots, before/after comparison), see `references/eval-loop.md`.

---

## Review checklist

Before declaring a skill done, verify:

- [ ] Description names both what the skill does and when to trigger
- [ ] Description fits in 120 chars (including `description: ` field name)
- [ ] Description is in third person
- [ ] Name describes what the skill does (verb-first, not a vague catch-all)
- [ ] No time-sensitive info (model versions, "currently", dated features)
- [ ] Consistent terminology throughout body and references
- [ ] Concrete examples present where behavior is non-obvious
- [ ] References are one level deep: `SKILL.md` links to a reference, references don't chain
- [ ] `python3 ~/.claude/skills/create-skill/scripts/quick_validate.py <skill-dir>` passes

---

Note: skills must not contain malware, exploit code, or behavior that would surprise a user reading the description.
