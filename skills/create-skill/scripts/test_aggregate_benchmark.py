#!/usr/bin/env python3
"""Tests for aggregate_benchmark.py. Run with: python3 -m unittest test_aggregate_benchmark"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "aggregate_benchmark.py"

spec = importlib.util.spec_from_file_location("aggregate_benchmark", SCRIPT)
agg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agg)


def write_config(eval_dir: Path, config_name: str, *, pass_rate, passed, total,
                 failed=0, time_seconds=None, tokens=0, tool_calls=0, errors=0):
    """Create <eval_dir>/<config_name>/{grading.json,timing.json} fixtures."""
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
    write_config(alpha, "with_skill", pass_rate=1.0, passed=2, total=2, time_seconds=10.0, tokens=100)
    write_config(alpha, "without_skill", pass_rate=0.5, passed=1, total=2, failed=1, time_seconds=20.0, tokens=200)
    beta = iteration / "beta"
    beta.mkdir()
    write_config(beta, "with_skill", pass_rate=0.0, passed=0, total=1, failed=1, time_seconds=5.0, tokens=50)
    write_config(beta, "without_skill", pass_rate=0.0, passed=0, total=1, failed=1, time_seconds=8.0, tokens=80)
    return iteration


class ReadJsonTest(unittest.TestCase):
    def test_missing_file_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(agg.read_json(Path(tmp) / "nope.json"))

    def test_valid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ok.json"
            path.write_text('{"a": 1}')
            self.assertEqual(agg.read_json(path), {"a": 1})

    def test_invalid_json_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("{not json")
            self.assertIsNone(agg.read_json(path))


class StatSummaryTest(unittest.TestCase):
    def test_empty_is_zeros(self):
        self.assertEqual(
            agg.stat_summary([]),
            {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
        )

    def test_single_value_has_zero_stddev(self):
        summary = agg.stat_summary([4.0])
        self.assertEqual(summary["mean"], 4.0)
        self.assertEqual(summary["stddev"], 0.0)
        self.assertEqual(summary["min"], 4.0)
        self.assertEqual(summary["max"], 4.0)

    def test_multiple_values(self):
        summary = agg.stat_summary([2.0, 4.0])
        self.assertEqual(summary["mean"], 3.0)
        self.assertEqual(summary["min"], 2.0)
        self.assertEqual(summary["max"], 4.0)
        self.assertGreater(summary["stddev"], 0.0)

    def test_filters_none(self):
        self.assertEqual(agg.stat_summary([None, 5.0, None])["mean"], 5.0)


class FmtDeltaTest(unittest.TestCase):
    def test_none_is_na(self):
        self.assertEqual(agg.fmt_delta(None, 1.0), "n/a")
        self.assertEqual(agg.fmt_delta(1.0, None), "n/a")

    def test_positive_delta_has_sign(self):
        self.assertEqual(agg.fmt_delta(1.0, 0.5), "+0.50")

    def test_negative_delta(self):
        self.assertEqual(agg.fmt_delta(0.5, 1.0), "-0.50")

    def test_custom_format(self):
        self.assertEqual(agg.fmt_delta(100.0, 80.0, "+.0f"), "+20")


class CollectRunsTest(unittest.TestCase):
    def test_collects_both_configs(self):
        with tempfile.TemporaryDirectory() as tmp:
            iteration = build_iteration(Path(tmp))
            runs = agg.collect_runs(iteration, "without_skill")
            self.assertEqual(len(runs), 4)
            configs = sorted(run["configuration"] for run in runs)
            self.assertEqual(configs, ["with_skill", "with_skill", "without_skill", "without_skill"])

    def test_eval_id_shared_within_eval(self):
        with tempfile.TemporaryDirectory() as tmp:
            iteration = build_iteration(Path(tmp))
            runs = agg.collect_runs(iteration, "without_skill")
            by_eval = {}
            for run in runs:
                by_eval.setdefault(run["eval_name"], set()).add(run["eval_id"])
            # Each eval's two configs share one id; the two evals get distinct ids.
            self.assertEqual(by_eval["alpha"], {0})
            self.assertEqual(by_eval["beta"], {1})

    def test_result_fields_pulled_through(self):
        with tempfile.TemporaryDirectory() as tmp:
            iteration = build_iteration(Path(tmp))
            runs = agg.collect_runs(iteration, "without_skill")
            alpha_with = next(
                run for run in runs
                if run["eval_name"] == "alpha" and run["configuration"] == "with_skill"
            )
            self.assertEqual(alpha_with["result"]["pass_rate"], 1.0)
            self.assertEqual(alpha_with["result"]["passed"], 2)
            self.assertEqual(alpha_with["result"]["time_seconds"], 10.0)
            self.assertEqual(alpha_with["result"]["tokens"], 100)

    def test_old_skill_baseline_recorded_as_without_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            iteration = Path(tmp) / "iter"
            iteration.mkdir()
            eval_dir = iteration / "solo"
            eval_dir.mkdir()
            write_config(eval_dir, "with_skill", pass_rate=1.0, passed=1, total=1)
            write_config(eval_dir, "old_skill", pass_rate=0.0, passed=0, total=1, failed=1)
            runs = agg.collect_runs(iteration, "old_skill")
            configs = sorted(run["configuration"] for run in runs)
            self.assertEqual(configs, ["with_skill", "without_skill"])

    def test_missing_grading_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            iteration = Path(tmp) / "iter"
            iteration.mkdir()
            eval_dir = iteration / "partial"
            eval_dir.mkdir()
            write_config(eval_dir, "with_skill", pass_rate=1.0, passed=1, total=1)
            (eval_dir / "without_skill").mkdir()  # no grading.json
            runs = agg.collect_runs(iteration, "without_skill")
            self.assertEqual(len(runs), 1)
            self.assertEqual(runs[0]["configuration"], "with_skill")

    def test_duration_ms_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            iteration = Path(tmp) / "iter"
            iteration.mkdir()
            eval_dir = iteration / "ms"
            eval_dir.mkdir()
            config_dir = eval_dir / "with_skill"
            config_dir.mkdir(parents=True)
            (config_dir / "grading.json").write_text(
                json.dumps({"summary": {"pass_rate": 1.0, "passed": 1, "total": 1}})
            )
            (config_dir / "timing.json").write_text(json.dumps({"duration_ms": 2500}))
            runs = agg.collect_runs(iteration, "without_skill")
            self.assertEqual(runs[0]["result"]["time_seconds"], 2.5)


class SummarizeTest(unittest.TestCase):
    def test_returns_none_for_absent_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            iteration = build_iteration(Path(tmp))
            runs = agg.collect_runs(iteration, "without_skill")
            self.assertIsNone(agg.summarize(runs, "nonexistent"))

    def test_mean_pass_rate(self):
        with tempfile.TemporaryDirectory() as tmp:
            iteration = build_iteration(Path(tmp))
            runs = agg.collect_runs(iteration, "without_skill")
            with_summary = agg.summarize(runs, "with_skill")
            self.assertEqual(with_summary["pass_rate"]["mean"], 0.5)  # mean of 1.0 and 0.0


class BuildBenchmarkTest(unittest.TestCase):
    def test_structure_and_delta(self):
        with tempfile.TemporaryDirectory() as tmp:
            iteration = build_iteration(Path(tmp))
            benchmark = agg.build_benchmark(iteration, "my-skill", "without_skill")
            self.assertEqual(benchmark["metadata"]["skill_name"], "my-skill")
            self.assertEqual(benchmark["metadata"]["evals_run"], ["alpha", "beta"])
            self.assertEqual(len(benchmark["runs"]), 4)
            self.assertIn("with_skill", benchmark["run_summary"])
            self.assertIn("without_skill", benchmark["run_summary"])
            self.assertIn("delta", benchmark["run_summary"])

    def test_no_delta_when_one_config_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            iteration = Path(tmp) / "iter"
            iteration.mkdir()
            eval_dir = iteration / "solo"
            eval_dir.mkdir()
            write_config(eval_dir, "with_skill", pass_rate=1.0, passed=1, total=1)
            benchmark = agg.build_benchmark(iteration, "solo-skill", "without_skill")
            self.assertIn("with_skill", benchmark["run_summary"])
            self.assertNotIn("without_skill", benchmark["run_summary"])
            self.assertNotIn("delta", benchmark["run_summary"])


class RenderMarkdownTest(unittest.TestCase):
    def test_contains_headers_and_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            iteration = build_iteration(Path(tmp))
            benchmark = agg.build_benchmark(iteration, "my-skill", "without_skill")
            md = agg.render_markdown(benchmark)
            self.assertIn("# Benchmark: my-skill", md)
            self.assertIn("## Summary", md)
            self.assertIn("## Per-eval results", md)
            self.assertIn("alpha", md)
            self.assertIn("beta", md)
            self.assertIn("**delta**", md)


class EndToEndTest(unittest.TestCase):
    def test_writes_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            iteration = build_iteration(Path(tmp))
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(iteration), "--skill-name", "my-skill"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            benchmark_json = iteration / "benchmark.json"
            benchmark_md = iteration / "benchmark.md"
            self.assertTrue(benchmark_json.is_file())
            self.assertTrue(benchmark_md.is_file())
            data = json.loads(benchmark_json.read_text())
            self.assertEqual(data["metadata"]["skill_name"], "my-skill")
            self.assertEqual(len(data["runs"]), 4)

    def test_output_dir_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            iteration = build_iteration(Path(tmp))
            out_dir = Path(tmp) / "out"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(iteration),
                 "--skill-name", "my-skill", "--output-dir", str(out_dir)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((out_dir / "benchmark.json").is_file())

    def test_bad_dir_exits_one(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "/no/such/dir", "--skill-name", "x"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("not a directory", result.stderr)


if __name__ == "__main__":
    unittest.main()
