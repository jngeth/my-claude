# Blind Comparator Agent (skill-eval extension)

Extends generic comparator at the repo-level `agents/comparator.md` (`../../agents/comparator.md` from this skill root).
Read that agent first and follow its process, rubric, and JSON output schema. This file adds only what is specific to
comparing two skill versions inside the eval loop, so do not restate the generic instructions here.

## What is being compared

Options A and B are outputs produced by two versions of a skill: `with_skill` vs `without_skill`, or `old_skill` vs
`new_skill`. You do not know which version produced which. Stay blind: judge the outputs, never infer the version.

## Inputs

The eval loop passes the generic inputs under these names:

- `output_a_path`, `output_b_path`: the two outputs to compare (generic options A and B).
- `eval_prompt`: the task the outputs should accomplish (generic goal).
- `expectations`: requirements to check against each output (generic requirements, optional, may be empty).
- `output_path`: where to write the result, default `<grading-dir>/comparison-N.json`.

## After comparing

The result feeds the post-hoc analyzer (`agents/analyzer.md`), which unblinds the winner to suggest improvements to
the losing skill. Keep `reasoning` concrete and tied to specific passages so the analyzer has evidence to work from.

Everything else (process, rubric, output schema, guidelines) lives in the generic agent. Use both files together.
