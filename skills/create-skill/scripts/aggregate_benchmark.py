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
                           [--output-dir <dir>]
"""

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path


def read_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"Warning: could not parse {path}: {e}", file=sys.stderr)
        return None


def collect_runs(iteration_dir: Path, baseline_name: str):
    runs = []
    eval_id = 0
    for eval_dir in sorted(p for p in iteration_dir.iterdir() if p.is_dir()):
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
                or (timing.get("duration_ms", 0) / 1000.0 if timing.get("duration_ms") else 0.0),
                "tokens": timing.get("total_tokens", 0),
                "tool_calls": grading.get("execution_metrics", {}).get("total_tool_calls", 0),
                "errors": grading.get("execution_metrics", {}).get("errors_encountered", 0),
            }
            runs.append({
                "eval_id": eval_id,
                "eval_name": eval_dir.name,
                # An old_skill baseline is recorded as "without_skill" so downstream grouping stays uniform.
                "configuration": "with_skill" if config_name == "with_skill" else "without_skill",
                "run_number": 1,
                "result": result,
                "expectations": grading.get("expectations", []),
                "notes": [],
            })
        eval_id += 1
    return runs


def stat_summary(values):
    values = [v for v in values if v is not None]
    if not values:
        return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}
    return {
        "mean": statistics.fmean(values),
        "stddev": statistics.pstdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
    }


def summarize(runs, configuration):
    subset = [r["result"] for r in runs if r["configuration"] == configuration]
    if not subset:
        return None
    return {
        "pass_rate": stat_summary([r["pass_rate"] for r in subset]),
        "time_seconds": stat_summary([r["time_seconds"] for r in subset]),
        "tokens": stat_summary([r["tokens"] for r in subset]),
    }


def fmt_delta(with_v, without_v, fmt="+.2f"):
    if without_v is None or with_v is None:
        return "n/a"
    return format(with_v - without_v, fmt)


def build_benchmark(iteration_dir: Path, skill_name: str, baseline_name: str):
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
            "pass_rate": fmt_delta(with_summary["pass_rate"]["mean"],
                                   without_summary["pass_rate"]["mean"]),
            "time_seconds": fmt_delta(with_summary["time_seconds"]["mean"],
                                      without_summary["time_seconds"]["mean"], "+.1f"),
            "tokens": fmt_delta(with_summary["tokens"]["mean"],
                                without_summary["tokens"]["mean"], "+.0f"),
        }

    eval_names = sorted({r["eval_name"] for r in runs})

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
    lines = []
    md = benchmark["metadata"]
    lines.append(f"# Benchmark: {md['skill_name']}")
    lines.append("")
    lines.append(f"- Iteration: `{md['iteration_dir']}`")
    lines.append(f"- Timestamp: {md['timestamp']}")
    lines.append(f"- Evals: {', '.join(md['evals_run']) or 'none'}")
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
            s = summary[config]
            lines.append(
                f"| {config} | "
                f"{s['pass_rate']['mean']:.2f} ± {s['pass_rate']['stddev']:.2f} | "
                f"{s['time_seconds']['mean']:.1f} ± {s['time_seconds']['stddev']:.1f} | "
                f"{s['tokens']['mean']:.0f} ± {s['tokens']['stddev']:.0f} |"
            )
        if "delta" in summary:
            d = summary["delta"]
            lines.append(
                f"| **delta** | **{d['pass_rate']}** | **{d['time_seconds']}** | **{d['tokens']}** |"
            )
        lines.append("")

    lines.append("## Per-eval results")
    lines.append("")
    lines.append("| Eval | Config | Pass rate | Passed/Total | Time (s) | Tokens |")
    lines.append("|---|---|---|---|---|---|")
    for run in benchmark["runs"]:
        r = run["result"]
        lines.append(
            f"| {run['eval_name']} | {run['configuration']} | "
            f"{r['pass_rate']:.2f} | {r['passed']}/{r['total']} | "
            f"{r['time_seconds']:.1f} | {r['tokens']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Aggregate eval grading.json files into a benchmark")
    parser.add_argument("iteration_dir", help="Path to iteration directory containing eval subdirs")
    parser.add_argument("--skill-name", required=True, help="Skill name to embed in metadata")
    parser.add_argument("--baseline", default="without_skill",
                        choices=["without_skill", "old_skill"],
                        help="Name of the baseline subdir (default: without_skill)")
    parser.add_argument("--output-dir", default=None,
                        help="Where to write benchmark.json + .md (default: iteration-dir)")
    args = parser.parse_args()

    iteration_dir = Path(args.iteration_dir).expanduser().resolve()
    if not iteration_dir.is_dir():
        print(f"Error: not a directory: {iteration_dir}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else iteration_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    benchmark = build_benchmark(iteration_dir, args.skill_name, args.baseline)

    json_path = output_dir / "benchmark.json"
    md_path = output_dir / "benchmark.md"
    json_path.write_text(json.dumps(benchmark, indent=2))
    md_path.write_text(render_markdown(benchmark))

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Aggregated {len(benchmark['runs'])} runs across {len(benchmark['metadata']['evals_run'])} evals")


if __name__ == "__main__":
    main()
