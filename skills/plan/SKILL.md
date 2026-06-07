---
name: plan
description: "Writes an implementation plan for a multi-step coding task. Use before coding from a spec or feature."
---

# Plan

## Overview

Write an implementation plan an engineer could execute with zero context for this codebase. Spell out every task:
which files to touch, the actual code, the commands to run, how to verify. Break the work into small, ordered steps.
Favor DRY and YAGNI, and commit often. Assume a skilled engineer who does not know this toolset or problem domain.

## When to use

Reach for this when a spec, feature request, or bug fix needs more than a couple of steps and touches several files.
Trigger phrases: "write a plan", "plan this out", "how should we build X", or any multi-step task before writing code.

## Restate the requirements

Open by restating what you're building in your own words: the goal, the constraints, what's explicitly out of scope.
This surfaces a misread before it shapes the whole plan. If anything is ambiguous, ask the user now, not mid-execution.

## Scope check

If the spec spans several independent subsystems, split it into one plan per subsystem before writing any tasks.
Each plan should produce working, testable software on its own. A plan that only half-builds a system is hard to
execute and review. When in doubt, propose the split to the user and let them confirm.

## Ground in existing patterns

Before writing tasks, search the codebase for conventions the work should mirror. Plans that match existing patterns
gets reviewed and merged faster and avoids reinventing what's already there. Capture the top example for each
relevant category with a file reference:

- **Naming:** file, function, type, and command naming in the affected area
- **Data access:** repository, service, query, or filesystem patterns
- **Error handling:** how failures are raised, returned, logged, or recovered
- **Logging:** levels, format, and what gets logged
- **Tests:** location, framework, fixtures, and assertion style

If no similar code exists for a category, say so. Don't invent a pattern.
Record these as the "Patterns to mirror" table in the plan, each row pointing at `path:line`.

## Map the files first

Before defining tasks, list every file the work creates or modifies and what each is responsible for. Record this as
the "Files to change" table in the plan. Decomposition decisions get locked in here, so make them deliberately:

- Give each file one clear responsibility and a well-defined interface.
- Smaller, focused files are easier to reason about and edit reliably than large ones doing too much.
- Keep code that changes together in the same place. Split by responsibility, not by technical layer.
- Follow the patterns already in the codebase. Don't restructure unilaterally
- If a file you're touching has grown unwieldy, folding a split into the plan is reasonable.

This map drives the task breakdown: each task should produce self-contained changes that stand on their own.

## Plan document structure

Assemble the plan in this order: header, patterns, files, tasks, risks.

```markdown
# [Feature] Implementation Plan

**Goal:** [one sentence on what this builds]
**Architecture:** [2-3 sentences on the approach]
**Tech stack:** [key libraries and tools]

## Patterns to mirror

| Category | Source      | Pattern          |
| -------- | ----------- | ---------------- |
| Naming   | `path:line` | [what to follow] |
| Errors   | `path:line` | [what to follow] |
| Tests    | `path:line` | [what to follow] |

## Files to change

| File   | Action                   | Why      |
| ------ | ------------------------ | -------- |
| `path` | CREATE / UPDATE / DELETE | [reason] |

## Tasks

[see the task template below]

## Risks

| Risk                        | Likelihood       | Mitigation         |
| --------------------------- | ---------------- | ------------------ |
| [what could block or break] | High / Med / Low | [how to handle it] |
```

Steps use `- [ ]` checkboxes so whoever executes can track progress. Fill the Risks table with real blockers and
unknowns: migrations, external dependencies, performance cliffs. Skip filler. If nothing worth noting, drop the section.

### Bite-sized tasks

Each step is one action that takes a few minutes, not a paragraph of work. A task is a handful of these steps:

- Write the failing test
- Run it and confirm it fails
- Write the minimal code to pass
- Run the test and confirm it passes
- Commit

Default to this test-first shape: it catches bugs early and proves each step before the next moves. Not every task
fits it. Config, schema migrations, glue code, and docs often have no useful test. For those, keep the same precision:
the exact change, the exact command to verify, the expected result. Don't manufacture a test that adds no signal.

### Task template

````markdown
### Task N: [Component]

**Files:**

- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/path/test_file.py`

**Mirror:** `path:line` (the grounded pattern this task follows)

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    assert function(input) == expected
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `pytest tests/path/test_file.py::test_specific_behavior -v`
Expected: FAIL, "function not defined"

- [ ] **Step 3: Write the minimal implementation**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run it and confirm it passes**

Run: `pytest tests/path/test_file.py::test_specific_behavior -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test_file.py src/path/file.py
git commit -m "feat: add specific behavior"
```
````

## No placeholders

The point of a plan is that someone executes it without filling gaps. These patterns are plan failures. Don't ship them:

- "TBD", "TODO", "implement later", "fill in the details"
- "Add error handling", "add validation", "handle edge cases" without saying which cases and how
- "Similar to Task N": repeat the code, since tasks get read out of order
- A step that says what to do but not how. If a step changes code, show the code
- A reference to a type, function, or method that no task defines

## Self-review

After the plan is written, read it against the ask with fresh eyes. Run this checklist yourself, not via a subagent:

1. **Spec coverage:** walk each requirement in the spec. Point to the task that implements it. List any gaps.
2. **Placeholder scan:** search for the patterns above. Replace each with concrete content.
3. **Type consistency:** the names, signatures, and types used in later tasks match what earlier tasks defined.

Fix what you find inline and move on. If a requirement has no task, add the task.

## Save and finish

Save to the temporary directory of the user's OS, not the current workspace.

Name the file `plan_<project>_<feature>_<timestamp>.md` where:

- `<project>`: basename of the current working directory (`basename "$PWD"`).
- `<feature>`: short kebab-case slug for what the plan builds.
- `<timestamp>`: current local time in ISO-8601 to the minute, from `date +%Y-%m-%dT%H:%M`.

Example: `plan_my-project_market-notifications_2026-06-07T11:11.md`. Tell the user the full path where it landed.
