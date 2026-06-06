# Analyzer Agent (skill-eval extension)

Extends the generic analyzer at the repo-level `agents/analyzer.md` (`../../agents/analyzer.md` from this skill root).
Read that agent first and follow its process, output schema, and guidelines for whichever job you were spawned for.
This file adds only what is specific to skill evaluation, so do not restate the generic instructions here.

Both jobs apply to skills: the source artifact is a skill, the comparison is between two skill versions
(with_skill vs without_skill, or old_skill vs new_skill), and the runs are eval runs of those versions.

---

## Post-hoc Analyzer

The generic `winner_source_path` and `loser_source_path` are skill directories. Read each skill's SKILL.md and its key
referenced files (scripts, references, examples), not just the prompt, when comparing the two.

The blind comparator at `agents/comparator.md` produces the `comparison_result_path` you read. Its labels are blind:
this step is where the winner is unblinded back to a concrete skill version.

Use these `improvement_suggestions[].category` values, since the loser is a skill:

| Category         | What it covers                                    |
| ---------------- | ------------------------------------------------- |
| `instructions`   | Changes to the skill's prose instructions         |
| `tools`          | Scripts, templates, or utilities to add or modify |
| `examples`       | Example inputs or outputs to include              |
| `error_handling` | Guidance for handling failures                    |
| `structure`      | Reorganization of skill content                   |
| `references`     | External docs or resources to add                 |

Default `output_path` is `<grading-dir>/analysis.json`. The schema matches `references/schemas.md` (analysis.json):
keep `comparison_summary`, `winner_strengths`, `loser_weaknesses`, `instruction_following`, `improvement_suggestions`,
and `transcript_insights` identical to what that file documents.

---

## Run-pattern Analyzer

The generic `runs_data_path` is the in-progress `benchmark.json` (see `references/schemas.md`). The spawning prompt
also passes `skill_path`, the skill being benchmarked.

The configurations are named `with_skill` and `without_skill`. Read per-check patterns through that lens: a check that
passes with_skill but fails without_skill is where the skill adds value; the reverse is where the skill may be hurting.

The notes you emit become the `notes` array in `benchmark.json`, so keep them as a flat JSON array of strings.

Everything else (process, output schema, guidelines) lives in the generic agent. Use both files together.
