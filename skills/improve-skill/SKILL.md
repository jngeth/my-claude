---
name: improve-skill
description: Refine an existing skill. Audit it, fix the top flaw, avoid regressions. Use to improve or tune a skill.
---

# Improve Skill

Make an existing skill better without breaking what already works.

This skill shares a toolbox with `create-skill`. It points at `create-skill` references and scripts instead of copying
them, so each lives in one place. Read the target skill in full, SKILL.md and every reference, before touching anything.

## Step 1: Set the goal

The goal comes from one of three sources; each starts differently, so name which one you are in:

- **The session just used this skill**: Mine the transcript first: the step that failed, the corrections the user made,
  where the skill made the agent guess or do wasted work. That run is your strongest evidence and a ready-made test.
  If the context is long or biased toward the task just done, hand the edit to a fresh sub-agent.
  Treat the run as one data point: generalize the fix, do not overfit it to this run.
- **A specific problem you can name**: Locate where in the skill it originates, then fix the cause, not the symptom.
- **"Make it better" with nothing specific**: Run the audit in Step 2 first. You cannot improve what you cannot name.

## Step 2: Audit

Grade the skill against lenses that already exist; do not invent new ones.
Produce a short list of concrete weaknesses, worst first, and show the user before changing anything:

- **Triggering**: Does the description say what the skill does and when, in words a user would type? Does it collide?
  See `~/.claude/skills/create-skill/references/description-tuning.md`.
- **Failure modes**: Hunt for no-op lines, sediment, sprawl, duplication, and steps that invite premature completion.
  These are defined in `create-skill`'s Iteration section.
- **Prose**: Run the `writing-voice` skill over SKILL.md and every reference.
- **Structure**: Walk the `create-skill` review checklist.
  (one-level references, checkable step done-conditions, concrete examples, no time-sensitive content).

## Step 3: Snapshot before editing

Copy the skill so every change is reversible and measurable. This is the baseline Step 5 compares against:

```bash
cp -r <skill-path> <skill-path>-workspace/skill-snapshot
```

Never edit without a snapshot.

## Step 4: Change one lever

Fix the highest-leverage weakness first, and only that one. One change per pass keeps cause and effect clear and
stops a working skill from regressing under a wholesale rewrite.

- **Do no harm.** Preserve what works. Resist scope creep and "while I'm here" edits.
- **Generalize the fix.** Address the class of problem, not the single example that exposed it.
- Apply the `writing-voice` skill and `~/.claude/skills/create-skill/references/writing-guide.md` as you write.

## Step 5: Measure new against old

Confirm the change helped the target without harming the rest. If the goal came from a real session failure (Step 1),
replay that exact scenario first: it is the most direct check that the fix landed. Then match effort to risk:

- **Light change** (pruned no-op, fixed trigger word): run `quick_validate.py` and re-read the review checklist. Done.
- **Behavioral or risky change**: Run the "improving an existing skill" A/B in
  `~/.claude/skills/create-skill/references/eval-loop.md`. It benchmarks edits against the snapshot, not just against
  no-skill. Reuse `create-skill`'s grader and comparator agents.

A change that wins on the target but loses elsewhere is a regression: revert it or narrow it.

## Step 6: Keep, revert, or stop

Keep the version that measured better; restore the snapshot if it did not. Take the next audit item or stop.
Stop once the target is fixed and nothing regressed: do not keep polishing a skill that already does its job.

---

## Validate

```bash
python3 ~/.claude/skills/create-skill/scripts/quick_validate.py <skill-dir>
```
