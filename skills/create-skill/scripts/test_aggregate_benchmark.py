"""Tests for aggregate_benchmark.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType


def write_config(
    eval_dir: Path,
    config_name: str,
    *,
    pass_rate: float,
    passed: int,
    total: int,
    failed: int = 0,
    time_seconds: float | None = None,
    tokens: int = 0,
    tool_calls: int = 0,
    errors: int = 0,
) -> Path:
    """Create ``<eval_dir>/<config_name>/{grading.json,timing.json}`` fixtures."""
    config_dir = eval_dir / config_name
    config_dir.mkdir(parents=True)
    grading = {
        "summary": {
            "pass_rate": pass_rate,
            "passed": passed,
            "failed": failed,
            "total": total,
        },
        "expectations": [{"id": "e1", "passed": True}],
        "execution_metrics": {
            "total_tool_calls": tool_calls,
            "errors_encountered": errors,
        },
    }
    (config_dir / "grading.json").write_text(json.dumps(grading))
    if time_seconds is not None or tokens:
        timing = {"total_duration_seconds": time_seconds or 0.0, "total_tokens": tokens}
        (config_dir / "timing.json").write_text(json.dumps(timing))
    return config_dir


def build_iteration(tmp: Path) -> Path:
    """Two evals, each with a with_skill and without_skill config."""
    iteration = tmp / "iter-1"
    iteration.mkdir()
    alpha = iteration / "alpha"
    alpha.mkdir()
    write_config(
        alpha,
        "with_skill",
        pass_rate=1.0,
        passed=2,
        total=2,
        time_seconds=10.0,
        tokens=100,
    )
    write_config(
        alpha,
        "without_skill",
        pass_rate=0.5,
        passed=1,
        total=2,
        failed=1,
        time_seconds=20.0,
        tokens=200,
    )
    beta = iteration / "beta"
    beta.mkdir()
    write_config(
        beta,
        "with_skill",
        pass_rate=0.0,
        passed=0,
        total=1,
        failed=1,
        time_seconds=5.0,
        tokens=50,
    )
    write_config(
        beta,
        "without_skill",
        pass_rate=0.0,
        passed=0,
        total=1,
        failed=1,
        time_seconds=8.0,
        tokens=80,
    )
    return iteration


def run_agg(module: ModuleType, args: list[str]) -> subprocess.CompletedProcess[str]:
    """Invoke aggregate_benchmark.py as a subprocess."""
    script = module.__file__
    assert script is not None
    return subprocess.run(
        [sys.executable, script, *args], capture_output=True, text=True
    )


def test_read_json_missing_file_returns_none(
    aggregate_benchmark: ModuleType, tmp_path: Path
) -> None:
    assert aggregate_benchmark.read_json(tmp_path / "nope.json") is None


def test_read_json_valid(aggregate_benchmark: ModuleType, tmp_path: Path) -> None:
    path = tmp_path / "ok.json"
    path.write_text('{"a": 1}')
    assert aggregate_benchmark.read_json(path) == {"a": 1}


def test_read_json_invalid_returns_none(
    aggregate_benchmark: ModuleType, tmp_path: Path
) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json")
    assert aggregate_benchmark.read_json(path) is None


def test_stat_summary_empty_is_zeros(aggregate_benchmark: ModuleType) -> None:
    assert aggregate_benchmark.stat_summary([]) == {
        "mean": 0.0,
        "stddev": 0.0,
        "min": 0.0,
        "max": 0.0,
    }


def test_stat_summary_single_value_has_zero_stddev(
    aggregate_benchmark: ModuleType,
) -> None:
    summary = aggregate_benchmark.stat_summary([4.0])
    assert summary["mean"] == 4.0
    assert summary["stddev"] == 0.0
    assert summary["min"] == 4.0
    assert summary["max"] == 4.0


def test_stat_summary_multiple_values(aggregate_benchmark: ModuleType) -> None:
    summary = aggregate_benchmark.stat_summary([2.0, 4.0])
    assert summary["mean"] == 3.0
    assert summary["min"] == 2.0
    assert summary["max"] == 4.0
    assert summary["stddev"] > 0.0


def test_stat_summary_filters_none(aggregate_benchmark: ModuleType) -> None:
    assert aggregate_benchmark.stat_summary([None, 5.0, None])["mean"] == 5.0


def test_fmt_delta_none_is_na(aggregate_benchmark: ModuleType) -> None:
    assert aggregate_benchmark.fmt_delta(None, 1.0) == "n/a"
    assert aggregate_benchmark.fmt_delta(1.0, None) == "n/a"


def test_fmt_delta_positive_has_sign(aggregate_benchmark: ModuleType) -> None:
    assert aggregate_benchmark.fmt_delta(1.0, 0.5) == "+0.50"


def test_fmt_delta_negative(aggregate_benchmark: ModuleType) -> None:
    assert aggregate_benchmark.fmt_delta(0.5, 1.0) == "-0.50"


def test_fmt_delta_custom_format(aggregate_benchmark: ModuleType) -> None:
    assert aggregate_benchmark.fmt_delta(100.0, 80.0, "+.0f") == "+20"


def test_collect_runs_both_configs(
    aggregate_benchmark: ModuleType, tmp_path: Path
) -> None:
    iteration = build_iteration(tmp_path)
    runs = aggregate_benchmark.collect_runs(iteration, "without_skill")
    assert len(runs) == 4
    configs = sorted(run["configuration"] for run in runs)
    assert configs == ["with_skill", "with_skill", "without_skill", "without_skill"]


def test_collect_runs_eval_id_shared_within_eval(
    aggregate_benchmark: ModuleType, tmp_path: Path
) -> None:
    iteration = build_iteration(tmp_path)
    runs = aggregate_benchmark.collect_runs(iteration, "without_skill")
    by_eval: dict[str, set[int]] = {}
    for run in runs:
        by_eval.setdefault(run["eval_name"], set()).add(run["eval_id"])
    assert by_eval["alpha"] == {0}
    assert by_eval["beta"] == {1}


def test_collect_runs_result_fields_pulled_through(
    aggregate_benchmark: ModuleType, tmp_path: Path
) -> None:
    iteration = build_iteration(tmp_path)
    runs = aggregate_benchmark.collect_runs(iteration, "without_skill")
    alpha_with = next(
        run
        for run in runs
        if run["eval_name"] == "alpha" and run["configuration"] == "with_skill"
    )
    assert alpha_with["result"]["pass_rate"] == 1.0
    assert alpha_with["result"]["passed"] == 2
    assert alpha_with["result"]["time_seconds"] == 10.0
    assert alpha_with["result"]["tokens"] == 100


def test_collect_runs_old_skill_baseline_recorded_as_without_skill(
    aggregate_benchmark: ModuleType, tmp_path: Path
) -> None:
    iteration = tmp_path / "iter"
    iteration.mkdir()
    eval_dir = iteration / "solo"
    eval_dir.mkdir()
    write_config(eval_dir, "with_skill", pass_rate=1.0, passed=1, total=1)
    write_config(eval_dir, "old_skill", pass_rate=0.0, passed=0, total=1, failed=1)
    runs = aggregate_benchmark.collect_runs(iteration, "old_skill")
    configs = sorted(run["configuration"] for run in runs)
    assert configs == ["with_skill", "without_skill"]


def test_collect_runs_missing_grading_skipped(
    aggregate_benchmark: ModuleType, tmp_path: Path
) -> None:
    iteration = tmp_path / "iter"
    iteration.mkdir()
    eval_dir = iteration / "partial"
    eval_dir.mkdir()
    write_config(eval_dir, "with_skill", pass_rate=1.0, passed=1, total=1)
    (eval_dir / "without_skill").mkdir()  # no grading.json
    runs = aggregate_benchmark.collect_runs(iteration, "without_skill")
    assert len(runs) == 1
    assert runs[0]["configuration"] == "with_skill"


def test_collect_runs_duration_ms_fallback(
    aggregate_benchmark: ModuleType, tmp_path: Path
) -> None:
    iteration = tmp_path / "iter"
    iteration.mkdir()
    eval_dir = iteration / "ms"
    eval_dir.mkdir()
    config_dir = eval_dir / "with_skill"
    config_dir.mkdir(parents=True)
    (config_dir / "grading.json").write_text(
        json.dumps({"summary": {"pass_rate": 1.0, "passed": 1, "total": 1}})
    )
    (config_dir / "timing.json").write_text(json.dumps({"duration_ms": 2500}))
    runs = aggregate_benchmark.collect_runs(iteration, "without_skill")
    assert runs[0]["result"]["time_seconds"] == 2.5


def test_summarize_returns_none_for_absent_config(
    aggregate_benchmark: ModuleType, tmp_path: Path
) -> None:
    iteration = build_iteration(tmp_path)
    runs = aggregate_benchmark.collect_runs(iteration, "without_skill")
    assert aggregate_benchmark.summarize(runs, "nonexistent") is None


def test_summarize_mean_pass_rate(
    aggregate_benchmark: ModuleType, tmp_path: Path
) -> None:
    iteration = build_iteration(tmp_path)
    runs = aggregate_benchmark.collect_runs(iteration, "without_skill")
    with_summary = aggregate_benchmark.summarize(runs, "with_skill")
    assert with_summary["pass_rate"]["mean"] == 0.5  # mean of 1.0 and 0.0


def test_build_benchmark_structure_and_delta(
    aggregate_benchmark: ModuleType, tmp_path: Path
) -> None:
    iteration = build_iteration(tmp_path)
    benchmark = aggregate_benchmark.build_benchmark(
        iteration, "my-skill", "without_skill"
    )
    assert benchmark["metadata"]["skill_name"] == "my-skill"
    assert benchmark["metadata"]["evals_run"] == ["alpha", "beta"]
    assert len(benchmark["runs"]) == 4
    assert "with_skill" in benchmark["run_summary"]
    assert "without_skill" in benchmark["run_summary"]
    assert "delta" in benchmark["run_summary"]


def test_build_benchmark_no_delta_when_one_config_only(
    aggregate_benchmark: ModuleType, tmp_path: Path
) -> None:
    iteration = tmp_path / "iter"
    iteration.mkdir()
    eval_dir = iteration / "solo"
    eval_dir.mkdir()
    write_config(eval_dir, "with_skill", pass_rate=1.0, passed=1, total=1)
    benchmark = aggregate_benchmark.build_benchmark(
        iteration, "solo-skill", "without_skill"
    )
    assert "with_skill" in benchmark["run_summary"]
    assert "without_skill" not in benchmark["run_summary"]
    assert "delta" not in benchmark["run_summary"]


def test_render_markdown_contains_headers_and_rows(
    aggregate_benchmark: ModuleType, tmp_path: Path
) -> None:
    iteration = build_iteration(tmp_path)
    benchmark = aggregate_benchmark.build_benchmark(
        iteration, "my-skill", "without_skill"
    )
    markdown = aggregate_benchmark.render_markdown(benchmark)
    assert "# Benchmark: my-skill" in markdown
    assert "## Summary" in markdown
    assert "## Per-eval results" in markdown
    assert "alpha" in markdown
    assert "beta" in markdown
    assert "**delta**" in markdown


def test_e2e_writes_outputs(aggregate_benchmark: ModuleType, tmp_path: Path) -> None:
    iteration = build_iteration(tmp_path)
    result = run_agg(aggregate_benchmark, [str(iteration), "--skill-name", "my-skill"])
    assert result.returncode == 0, result.stderr
    benchmark_json = iteration / "benchmark.json"
    benchmark_md = iteration / "benchmark.md"
    assert benchmark_json.is_file()
    assert benchmark_md.is_file()
    data = json.loads(benchmark_json.read_text())
    assert data["metadata"]["skill_name"] == "my-skill"
    assert len(data["runs"]) == 4


def test_e2e_output_dir_override(
    aggregate_benchmark: ModuleType, tmp_path: Path
) -> None:
    iteration = build_iteration(tmp_path)
    out_dir = tmp_path / "out"
    result = run_agg(
        aggregate_benchmark,
        [str(iteration), "--skill-name", "my-skill", "--output-dir", str(out_dir)],
    )
    assert result.returncode == 0, result.stderr
    assert (out_dir / "benchmark.json").is_file()


def test_e2e_bad_dir_exits_one(aggregate_benchmark: ModuleType) -> None:
    result = run_agg(aggregate_benchmark, ["/no/such/dir", "--skill-name", "x"])
    assert result.returncode == 1
    assert "not a directory" in result.stderr
