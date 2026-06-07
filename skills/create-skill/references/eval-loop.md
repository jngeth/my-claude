# Eval Loop

Full subagent workflow for testing a skill: spawn runs in parallel, grade outputs, aggregate into a benchmark,
review with the user. Read this before running tests in Step 5 of SKILL.md.

This entire section is one continuous sequence: don't stop partway through. Do NOT use
`/skill-test` or any other testing skill: this **is** the testing flow.

---

## Workspace layout

Put results in `<skill-name>-workspace/` as a sibling to the skill directory:

```
my-skill-workspace/
├── skill-snapshot/        (only when improving an existing skill: `cp -r` before editing)
├── iteration-1/
│   ├── <eval-name-1>/
│   │   ├── with_skill/
│   │   │   ├── outputs/
│   │   │   ├── grading.json
│   │   │   └── timing.json
│   │   └── without_skill/   (or old_skill/ when improving)
│   │       ├── outputs/
│   │       ├── grading.json
│   │       └── timing.json
│   ├── <eval-name-2>/
│   │   └── ...
│   ├── benchmark.json
│   └── benchmark.md
└── iteration-2/
    └── ...
```

Create directories as you go; don't pre-create everything.

---

## Step 1: Spawn all runs in one turn

For each eval, spawn **two** subagents in the same turn: one with the skill, one without. Don't spawn the with-skill
runs first and come back for baselines later. Launch everything at once.

**With-skill subagent prompt:**

```
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input files: <eval files, or "none">
- Save outputs to: <workspace>/iteration-<N>/<eval-name>/with_skill/outputs/
- Outputs to save: <what the user cares about e.g. "the final .docx file">
- Also write to that outputs dir: `metrics.json` (tool-call counts, total steps, files created, errors, output and
  transcript char counts; schema in `references/schemas.md`) and `user_notes.md` (uncertainties, anything needing
  review, workarounds you used).
```

**Baseline subagent prompt:**

- **New skill**: same prompt, no skill path. Save to `without_skill/outputs/`.
- **Improving an existing skill**: snapshot the skill first (`cp -r <skill-path> <workspace>/skill-snapshot/`).
  Point the baseline at the snapshot, save to `old_skill/outputs/`.

Write `eval_metadata.json` per eval (expectations can be empty).
Give each eval a descriptive name based on what it's testing not "eval-0":

```json
{
  "eval_id": 0,
  "eval_name": "rotates-portrait-pdf",
  "prompt": "Rotate this PDF 90 degrees clockwise.",
  "expectations": []
}
```

If this iteration uses new or modified eval prompts, write a fresh metadata file per eval, don't assume they carry over.

## Step 2: Draft expectations while runs are in progress

Don't idle. Use the time:

- Draft quantitative expectations per eval. Good expectations are **objectively verifiable** with **descriptive names**.
- Subjective skills (writing style, design) don't need expectations: qualitative review is fine.
- Update `eval_metadata.json` and `evals/evals.json` once drafted.
- Brief the user on what they'll see: qualitative outputs _plus_ the quantitative benchmark.

## Step 3: Capture timing as runs complete

When each subagent finishes, the task notification includes `total_tokens` and `duration_ms`.
**Save them immediately.** This data isn't persisted anywhere else:

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

Write to `<run-dir>/timing.json`. Process notifications as they arrive, not in batch.

## Step 4: Grade, aggregate, review

Each agent in this step has two layers: the repo-level `agents/<name>.md` (process, rubric, schema) and this skill's
`agents/<name>.md` (eval-loop specifics). Always spawn with both; the skill-eval file says what to read and write.

### 4a. Grade each run

Spawn a grader subagent (both layers, per the note above). It evaluates each expectation against the outputs and writes
`grading.json` per run.

**The grading.json schema is load-bearing**: `aggregate_benchmark.py` reads exact field names. Each expectation
must have `text`, `passed`, and `evidence` (not `name`/`met`/`details`). See `schemas.md` for the full structure.

For programmatically-checkable expectations, write and run a script rather than eyeballing across iterations.

### 4b. Aggregate into a benchmark

```bash
python3 ~/.claude/skills/create-skill/scripts/aggregate_benchmark.py \
    <workspace>/iteration-N --skill-name <name>
```

Produces `benchmark.json` and `benchmark.md` with pass rate, time, tokens per configuration mean ± stddev plus delta.
Use `--baseline old_skill` when improving an existing skill.

### 4c. Do an analyst pass

Read the benchmark and surface patterns the aggregate hides. Spawn the run-pattern analyzer (both layers; use the
"Run-pattern Analyzer" section of the repo-level file). Look for:

- Expectations that always pass regardless of skill (non-discriminating)
- High-variance evals (possibly flaky)
- Time/token tradeoffs (skill is slower but more accurate?)

### 4d. Review with the user

Show the user `benchmark.md` plus the per-eval output files directly in the conversation. For the full HTML viewer
(with `generate_review.py`), see the anthropics skill-creator repo that viewer isn't bundled here. The markdown report
covers most of what reviewers actually need.

When showing results, tell the user something like: "Here are per-eval outputs and the benchmark summary. Look through
each one and tell me what's off, even one-word feedback is fine. I'll iterate on the skill based on what you flag."

## Step 5: Read the feedback and iterate

Note what the user flagged. Focus improvements on the evals where they had specific complaints.

**How to think about improvements:**

1. **Generalize.** These few examples are a window into thousands of future invocations.
   Resist the urge to add fiddly fixes that only handle the case in front of you.
2. **Keep the prompt lean.** Read the transcripts, not just the outputs. If the skill is making
   the model waste time on unproductive steps, remove the parts causing that.
3. **Explain the why.** If you're writing ALWAYS/NEVER, reframe and give the reasoning.
   Smart models with theory of mind do better with rationale than with rigid rules.
4. **Look for repeated work across runs.** If all 3 baseline runs independently wrote similar
   helper scripts, bundle that script in the skill. Write it once.

Apply improvements, then rerun all evals into `iteration-<N+1>/` (including baselines).
Pass `--previous-workspace` patterns or just point users at both `benchmark.md` files for comparison.

Keep iterating until: the user says they're happy, feedback is all empty, or you're not making meaningful progress.

---

## Advanced: blind comparison

For a more rigorous A/B between two skill versions ("is the new version actually better?"), give both outputs to an
independent subagent that doesn't know which is which. Optional: most users don't need it; human review suffices.

1. **Compare blind.** Spawn the comparator (both layers) on the two outputs. It writes `comparison-N.json`.
2. **Unblind.** Spawn the post-hoc analyzer (both layers; the "Post-hoc Analyzer" section of the repo-level file)
   on that result to name the winner and suggest improvements to the losing skill.
