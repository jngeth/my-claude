#!/usr/bin/env python3
"""Tests for init_agent.py. Run with: python3 -m unittest test_init_agent"""

import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
INIT_SCRIPT = SCRIPTS / "init_agent.py"
VALIDATE_SCRIPT = SCRIPTS / "quick_validate.py"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


init_agent_mod = _load("init_agent", INIT_SCRIPT)
quick_validate_mod = _load("quick_validate", VALIDATE_SCRIPT)

title_case = init_agent_mod.title_case
build_agent_md = init_agent_mod.build_agent_md
init_agent = init_agent_mod.init_agent
DEFAULT_DESCRIPTION = init_agent_mod.DEFAULT_DESCRIPTION
validate_agent = quick_validate_mod.validate_agent


def make_agent(parent: Path, name: str, **kwargs) -> Path:
    """Call init_agent with defaults, swallowing stdout, and return the file path."""
    params = {"description": DEFAULT_DESCRIPTION, "tools": "", "model": "", "extends": ""}
    params.update(kwargs)
    with redirect_stdout(io.StringIO()):
        return init_agent(name, str(parent), **params)


class TitleCaseTest(unittest.TestCase):
    def test_hyphenated(self):
        self.assertEqual(title_case("python-engineer"), "Python Engineer")


class BuildAgentMdTest(unittest.TestCase):
    def test_minimal_frontmatter(self):
        text = build_agent_md("solo", "Does a thing.", "", "", "")
        self.assertIn("name: solo", text)
        self.assertIn('description: "Does a thing."', text)
        self.assertIn("# Solo", text)
        self.assertNotIn("tools:", text)
        self.assertNotIn("model:", text)
        self.assertNotIn("Load the", text)

    def test_tools_and_model_included(self):
        text = build_agent_md("rev", "Reviews.", "Read, Grep", "sonnet", "")
        self.assertIn("tools: Read, Grep", text)
        self.assertIn("model: sonnet", text)

    def test_extends_adds_load_section(self):
        text = build_agent_md("py", "Builds.", "", "", "python")
        self.assertIn("Load the python conventions first", text)
        self.assertIn("`python` skill", text)


class InitAgentTest(unittest.TestCase):
    def test_creates_named_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = make_agent(Path(tmp), "code-reviewer")
            self.assertIsNotNone(agent)
            self.assertEqual(agent.name, "code-reviewer.md")
            self.assertTrue(agent.is_file())

    def test_creates_missing_parent_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            nested = Path(tmp) / "deep" / "agents"
            agent = make_agent(nested, "fresh")
            self.assertTrue(agent.is_file())

    def test_existing_file_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_agent(Path(tmp), "dup")
            with redirect_stdout(io.StringIO()) as out:
                result = init_agent("dup", tmp, DEFAULT_DESCRIPTION, "", "", "")
            self.assertIsNone(result)
            self.assertIn("already exists", out.getvalue())

    def test_generated_default_agent_passes_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = make_agent(Path(tmp), "scaffold-demo")
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertTrue(valid, message)

    def test_generated_full_agent_passes_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = make_agent(
                Path(tmp),
                "full-demo",
                description="Reviews Python diffs when the user asks for review.",
                tools="Read, Grep, Glob, Bash",
                model="inherit",
                extends="python",
            )
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertTrue(valid, message)


class EndToEndTest(unittest.TestCase):
    def run_init(self, args):
        return subprocess.run(
            [sys.executable, str(INIT_SCRIPT), *args], capture_output=True, text=True
        )

    def test_creates_agent_exit_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_init(["cli-agent", "--path", tmp, "--tools", "Read, Grep"])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(tmp) / "cli-agent.md").is_file())

    def test_existing_file_exit_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "dup.md").write_text("x")
            result = self.run_init(["dup", "--path", tmp])
            self.assertEqual(result.returncode, 1)
            self.assertIn("already exists", result.stdout)

    def test_missing_required_path_exit_two(self):
        result = self.run_init(["orphan"])
        self.assertEqual(result.returncode, 2)  # argparse usage error


if __name__ == "__main__":
    unittest.main()
