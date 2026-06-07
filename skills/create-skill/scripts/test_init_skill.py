#!/usr/bin/env python3
"""Tests for init_skill.py. Run with: python3 -m unittest test_init_skill"""

import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "init_skill.py"

spec = importlib.util.spec_from_file_location("init_skill", SCRIPT)
init_skill_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(init_skill_mod)

title_case = init_skill_mod.title_case
build_skill_md = init_skill_mod.build_skill_md
init_skill = init_skill_mod.init_skill


def make_skill(parent: Path, name: str, dirs: set):
    """Call init_skill, swallowing its stdout chatter, and return the result path."""
    with redirect_stdout(io.StringIO()):
        return init_skill(name, str(parent), dirs)


class TitleCaseTest(unittest.TestCase):
    def test_single_word(self):
        self.assertEqual(title_case("pdf"), "Pdf")

    def test_hyphenated(self):
        self.assertEqual(title_case("my-new-skill"), "My New Skill")


class BuildSkillMdTest(unittest.TestCase):
    def test_no_dirs_has_no_resources_section(self):
        body = build_skill_md("solo", "Solo", set())
        self.assertIn("name: solo", body)
        self.assertIn("# Solo", body)
        self.assertNotIn("## Resources", body)
        self.assertNotIn("## Routing", body)

    def test_resources_section_lists_created_dirs(self):
        body = build_skill_md("res", "Res", {"scripts", "references"})
        self.assertIn("## Resources", body)
        self.assertIn("`scripts/`", body)
        self.assertIn("`references/`", body)
        self.assertNotIn("`assets/`", body)

    def test_subskills_adds_routing_section(self):
        body = build_skill_md("router", "Router", {"subskills"})
        self.assertIn("## Routing", body)
        self.assertIn("subskills/example-route.md", body)
        self.assertIn("`subskills/`", body)

    def test_no_routing_without_subskills(self):
        body = build_skill_md("plain", "Plain", {"scripts"})
        self.assertNotIn("## Routing", body)


class InitSkillTest(unittest.TestCase):
    def test_skill_md_only_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = make_skill(Path(tmp), "bare", set())
            self.assertIsNotNone(skill_dir)
            self.assertTrue((skill_dir / "SKILL.md").is_file())
            children = {child.name for child in skill_dir.iterdir()}
            self.assertEqual(children, {"SKILL.md"})

    def test_scripts_dir_created_and_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = make_skill(Path(tmp), "with-scripts", {"scripts"})
            example = skill_dir / "scripts" / "example.py"
            self.assertTrue(example.is_file())
            self.assertTrue(example.stat().st_mode & 0o111, "script should be executable")
            self.assertIn("with-scripts", example.read_text())

    def test_all_optional_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = make_skill(
                Path(tmp), "kitchen-sink", {"scripts", "references", "assets", "subskills"}
            )
            self.assertTrue((skill_dir / "scripts" / "example.py").is_file())
            self.assertTrue((skill_dir / "references" / "reference.md").is_file())
            self.assertTrue((skill_dir / "assets" / "example_asset.txt").is_file())
            self.assertTrue((skill_dir / "subskills" / "example-route.md").is_file())

    def test_skill_md_matches_builder(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = make_skill(Path(tmp), "matchy", {"references"})
            expected = build_skill_md("matchy", "Matchy", {"references"})
            self.assertEqual((skill_dir / "SKILL.md").read_text(), expected)

    def test_reference_doc_uses_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = make_skill(Path(tmp), "doc-skill", {"references"})
            text = (skill_dir / "references" / "reference.md").read_text()
            self.assertIn("Doc Skill", text)

    def test_existing_directory_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "taken").mkdir()
            with redirect_stdout(io.StringIO()) as out:
                result = init_skill("taken", tmp, set())
            self.assertIsNone(result)
            self.assertIn("already exists", out.getvalue())


class EndToEndTest(unittest.TestCase):
    def run_init(self, args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
        )

    def test_creates_skill_exit_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_init(["cli-skill", "--path", tmp, "--scripts"])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(tmp) / "cli-skill" / "SKILL.md").is_file())
            self.assertTrue((Path(tmp) / "cli-skill" / "scripts" / "example.py").is_file())

    def test_existing_dir_exit_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "dup").mkdir()
            result = self.run_init(["dup", "--path", tmp])
            self.assertEqual(result.returncode, 1)
            self.assertIn("already exists", result.stdout)

    def test_missing_required_path_exit_two(self):
        result = self.run_init(["orphan"])
        self.assertEqual(result.returncode, 2)  # argparse usage error


if __name__ == "__main__":
    unittest.main()
