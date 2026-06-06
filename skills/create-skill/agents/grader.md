# Grader Agent (skill-eval extension)

Extends the generic grader `agents/grader.md` (`../../agents/grader.md` from this skill root). Read that agent first and
follow its process, grading criteria, and JSON output schema. This file adds only what is specific to grading a
skill-eval run, do not restate generic instructions here.

## Inputs

The eval loop passes the generic inputs under the same names: `expectations`, `transcript_path`, `outputs_dir`. There
is no separate `output_path`: write the result to `{outputs_dir}/../grading.json` (sibling to outputs_dir).

## A second job: critique the evals

Beyond grading the run, judge the evals themselves. A passing grade on a weak assertion is worse than useless: it
creates false confidence. An assertion is _discriminating_ when it passes only if the skill genuinely succeeds and
fails when it does not. Surface a suggestion only when there is a clear gap, not for every assertion. Worth raising:

- An assertion that passed but would also pass for a clearly wrong output (e.g. checks a filename, not the content).
- An important outcome you observed, good or bad, that no assertion covers.
- An assertion that cannot be verified from the available outputs.

Keep the bar high. The goal is to flag what the eval author would call a good catch, not to nitpick.

## Extra inputs to read

After grading, fold these into the output if present:

- `{outputs_dir}/user_notes.md`: uncertainties or issues executor flagged. Rveals problems even when expectations pass.
- `{outputs_dir}/metrics.json`: executor's tool-call and output-size metrics.
- `{outputs_dir}/../timing.json`: wall-clock timing for the run.

## Added output fields

Keep the generic `expectations`, `summary`, and `claims` exactly as the generic agent defines them.
Add these skill-eval sections to the same JSON object:

```json
{
  "execution_metrics": {
    "tool_calls": { "Read": 5, "Write": 2, "Bash": 8 },
    "total_tool_calls": 15,
    "total_steps": 6,
    "errors_encountered": 0,
    "output_chars": 12450,
    "transcript_chars": 3200
  },
  "timing": {
    "executor_duration_seconds": 165.0,
    "grader_duration_seconds": 26.0,
    "total_duration_seconds": 191.0
  },
  "user_notes_summary": {
    "uncertainties": ["Used 2023 data, may be stale"],
    "needs_review": [],
    "workarounds": ["Fell back to text overlay for non-fillable fields"]
  },
  "eval_feedback": {
    "suggestions": [
      {
        "assertion": "The output includes the name 'John Smith'",
        "reason": "A hallucinated document mentioning the name would also pass: check it appears as the primary contact with matching phone and email from the input"
      },
      {
        "reason": "No assertion checks whether extracted phone numbers match the input: Incorrect numbers went uncaught"
      }
    ],
    "overall": "Assertions check presence but not correctness. Consider adding content verification."
  }
}
```

- `execution_metrics`: copied from the executor's `metrics.json`. `output_chars` and `transcript_chars` proxy tokens.
- `timing`: from `timing.json`. Wall-clock durations for executor, grader, and total.
- `user_notes_summary`: issues from `user_notes.md`, split into `uncertainties`, `needs_review`, `workarounds`.
- `eval_feedback`: the eval critique, only when warranted. Each suggestion carries a `reason` and an optional
  `assertion` it relates to. `overall` can be "No suggestions, evals look solid" when nothing needs flagging.

The grading.json field names are load-bearing: `scripts/aggregate_benchmark.py` and the benchmark viewer read
`summary.{pass_rate,passed,failed,total}`, `expectations[].{text,passed,evidence}`, and
`execution_metrics.total_tool_calls` by exact name. `references/schemas.md` documents the full structure. Keep every
key identical to both.

Everything else (process, grading criteria, output schema for core fields, guidelines) lives in the generic agent.
Use both files together.
