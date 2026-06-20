#!/usr/bin/env python3
"""
Aggregate per-eval grading.json files into a single benchmark.json and benchmark.md.

Expected layout (produced by the eval loop in references/eval-loop.md):

    <iteration-dir>/
        <eval-name>/
            with_skill/
                grading.json
                timing.json (optional)
            without_skill/    (or old_skill/)
                grading.json
                timing.json (optional)

Each grading.json must follow the schema in references/schemas.md — at minimum a
`summary` with `pass_rate`, `passed`, `total`, and `expectations` list.

Usage:
    aggregate_benchmark.py <iteration-dir> --skill-name <name>
                           [--baseline without_skill|old_skill]
                           [--output-dir <dir>] [--verbose]
"""

from __future__ import annotations

import argparse
import json
import logging
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def read_json(path: Path) -> dict | None:
    """Read and parse a JSON file, returning None when it is missing or invalid.

    Parameters
    ----------
    path : Path
        File to read.

    Returns
    -------
    dict | None
        The parsed object, or ``None`` if the file is absent or unparseable.
    """
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as error:
        logger.warning("could not parse %s: %s", path, error)
        return None


def collect_runs(iteration_dir: Path, baseline_name: str) -> list[dict]:
    """Collect per-eval run records from an iteration directory.

    Parameters
    ----------
    iteration_dir : Path
        Directory holding one subdirectory per eval.
    baseline_name : str
        Name of the baseline config subdir (``without_skill`` or ``old_skill``).

    Returns
    -------
    list[dict]
        One record per (eval, configuration) pair that has a grading.json.
    """
    runs = []
    eval_id = 0
    for eval_dir in sorted(
        entry for entry in iteration_dir.iterdir() if entry.is_dir()
    ):
        for config_name in ("with_skill", baseline_name):
            config_dir = eval_dir / config_name
            if not config_dir.is_dir():
                continue
            grading = read_json(config_dir / "grading.json")
            if grading is None:
                continue
            timing = read_json(config_dir / "timing.json") or {}
            summary = grading.get("summary", {})
            result = {
                "pass_rate": summary.get("pass_rate", 0.0),
                "passed": summary.get("passed", 0),
                "failed": summary.get("failed", 0),
                "total": summary.get("total", 0),
                "time_seconds": timing.get("total_duration_seconds")
                or (
                    timing.get("duration_ms", 0) / 1000.0
                    if timing.get("duration_ms")
                    else 0.0
                ),
                "tokens": timing.get("total_tokens", 0),
                "tool_calls": grading.get("execution_metrics", {}).get(
                    "total_tool_calls", 0
                ),
                "errors": grading.get("execution_metrics", {}).get(
                    "errors_encountered", 0
                ),
            }
            runs.append(
                {
                    "eval_id": eval_id,
                    "eval_name": eval_dir.name,
                    # An old_skill baseline is recorded as "without_skill" so downstream grouping stays uniform.
                    "configuration": "with_skill"
                    if config_name == "with_skill"
                    else "without_skill",
                    "run_number": 1,
                    "result": result,
                    "expectations": grading.get("expectations", []),
                    "notes": [],
                }
            )
        eval_id += 1
    return runs


def stat_summary(values: list[float | None]) -> dict:
    """Summarize a list of numbers as mean, stddev, min, and max.

    Parameters
    ----------
    values : list[float | None]
        Values to summarize; ``None`` entries are ignored.

    Returns
    -------
    dict
        Keys ``mean``, ``stddev``, ``min``, ``max``. All zero when empty.
    """
    present = [value for value in values if value is not None]
    if not present:
        return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}
    return {
        "mean": statistics.fmean(present),
        "stddev": statistics.pstdev(present) if len(present) > 1 else 0.0,
        "min": min(present),
        "max": max(present),
    }


def summarize(runs: list[dict], configuration: str) -> dict | None:
    """Aggregate pass rate, time, and tokens across runs of one configuration.

    Parameters
    ----------
    runs : list[dict]
        Run records from :func:`collect_runs`.
    configuration : str
        ``with_skill`` or ``without_skill``.

    Returns
    -------
    dict | None
        Per-metric :func:`stat_summary` blocks, or ``None`` when no run matches.
    """
    subset = [run["result"] for run in runs if run["configuration"] == configuration]
    if not subset:
        return None
    return {
        "pass_rate": stat_summary([run["pass_rate"] for run in subset]),
        "time_seconds": stat_summary([run["time_seconds"] for run in subset]),
        "tokens": stat_summary([run["tokens"] for run in subset]),
    }


def fmt_delta(
    with_value: float | None, without_value: float | None, fmt: str = "+.2f"
) -> str:
    """Format the signed difference between a with-skill and baseline value.

    Parameters
    ----------
    with_value : float | None
        The with-skill metric.
    without_value : float | None
        The baseline metric.
    fmt : str, optional
        Format spec for the difference, by default ``"+.2f"``.

    Returns
    -------
    str
        The formatted delta, or ``"n/a"`` when either input is ``None``.
    """
    if without_value is None or with_value is None:
        return "n/a"
    return format(with_value - without_value, fmt)


def build_benchmark(iteration_dir: Path, skill_name: str, baseline_name: str) -> dict:
    """Build the full benchmark object from an iteration directory.

    Parameters
    ----------
    iteration_dir : Path
        Directory holding one subdirectory per eval.
    skill_name : str
        Skill name embedded in the metadata.
    baseline_name : str
        Name of the baseline config subdir.

    Returns
    -------
    dict
        Benchmark with ``metadata``, ``runs``, ``run_summary``, and ``notes``.
    """
    runs = collect_runs(iteration_dir, baseline_name)
    with_summary = summarize(runs, "with_skill")
    without_summary = summarize(runs, "without_skill")

    summary_block = {}
    if with_summary:
        summary_block["with_skill"] = with_summary
    if without_summary:
        summary_block["without_skill"] = without_summary
    if with_summary and without_summary:
        summary_block["delta"] = {
            "pass_rate": fmt_delta(
                with_summary["pass_rate"]["mean"], without_summary["pass_rate"]["mean"]
            ),
            "time_seconds": fmt_delta(
                with_summary["time_seconds"]["mean"],
                without_summary["time_seconds"]["mean"],
                "+.1f",
            ),
            "tokens": fmt_delta(
                with_summary["tokens"]["mean"],
                without_summary["tokens"]["mean"],
                "+.0f",
            ),
        }

    eval_names = sorted({run["eval_name"] for run in runs})

    return {
        "metadata": {
            "skill_name": skill_name,
            "iteration_dir": str(iteration_dir),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "evals_run": eval_names,
            "runs_per_configuration": 1,
        },
        "runs": runs,
        "run_summary": summary_block,
        "notes": [],
    }


def render_markdown(benchmark: dict) -> str:
    """Render a benchmark object as a human-readable markdown report.

    Parameters
    ----------
    benchmark : dict
        Benchmark object from :func:`build_benchmark`.

    Returns
    -------
    str
        Markdown with a summary table and a per-eval results table.
    """
    lines = []
    metadata = benchmark["metadata"]
    lines.append(f"# Benchmark: {metadata['skill_name']}")
    lines.append("")
    lines.append(f"- Iteration: `{metadata['iteration_dir']}`")
    lines.append(f"- Timestamp: {metadata['timestamp']}")
    lines.append(f"- Evals: {', '.join(metadata['evals_run']) or 'none'}")
    lines.append("")

    summary = benchmark["run_summary"]
    if summary:
        lines.append("## Summary")
        lines.append("")
        lines.append("| Configuration | Pass rate | Time (s) | Tokens |")
        lines.append("|---|---|---|---|")
        for config in ("with_skill", "without_skill"):
            if config not in summary:
                continue
            config_summary = summary[config]
            lines.append(
                f"| {config} | "
                f"{config_summary['pass_rate']['mean']:.2f} ± {config_summary['pass_rate']['stddev']:.2f} | "
                f"{config_summary['time_seconds']['mean']:.1f} ± {config_summary['time_seconds']['stddev']:.1f} | "
                f"{config_summary['tokens']['mean']:.0f} ± {config_summary['tokens']['stddev']:.0f} |"
            )
        if "delta" in summary:
            delta = summary["delta"]
            lines.append(
                f"| **delta** | **{delta['pass_rate']}** | **{delta['time_seconds']}** | **{delta['tokens']}** |"
            )
        lines.append("")

    lines.append("## Per-eval results")
    lines.append("")
    lines.append("| Eval | Config | Pass rate | Passed/Total | Time (s) | Tokens |")
    lines.append("|---|---|---|---|---|---|")
    for run in benchmark["runs"]:
        result = run["result"]
        lines.append(
            f"| {run['eval_name']} | {run['configuration']} | "
            f"{result['pass_rate']:.2f} | {result['passed']}/{result['total']} | "
            f"{result['time_seconds']:.1f} | {result['tokens']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    """Parse arguments, build the benchmark, and write benchmark.json + .md."""
    parser = argparse.ArgumentParser(
        description="Aggregate eval grading.json files into a benchmark"
    )
    parser.add_argument(
        "iteration_dir", help="Path to iteration directory containing eval subdirs"
    )
    parser.add_argument(
        "--skill-name", required=True, help="Skill name to embed in metadata"
    )
    parser.add_argument(
        "--baseline",
        default="without_skill",
        choices=["without_skill", "old_skill"],
        help="Name of the baseline subdir (default: without_skill)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Where to write benchmark.json + .md (default: iteration-dir)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    iteration_dir = Path(args.iteration_dir).expanduser().resolve()
    if not iteration_dir.is_dir():
        logger.error("not a directory: %s", iteration_dir)
        sys.exit(1)

    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else iteration_dir
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    benchmark = build_benchmark(iteration_dir, args.skill_name, args.baseline)

    json_path = output_dir / "benchmark.json"
    md_path = output_dir / "benchmark.md"
    json_path.write_text(json.dumps(benchmark, indent=2))
    md_path.write_text(render_markdown(benchmark))

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(
        f"Aggregated {len(benchmark['runs'])} runs across {len(benchmark['metadata']['evals_run'])} evals"
    )


if __name__ == "__main__":
    main()
