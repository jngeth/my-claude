#!/usr/bin/env python3
"""Tests for quick_validate.py. Run with: python3 -m unittest test_quick_validate"""

import importlib.util
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "quick_validate.py"

spec = importlib.util.spec_from_file_location("quick_validate", SCRIPT)
quick_validate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quick_validate)

validate_skill = quick_validate.validate_skill


def write_skill(parent: Path, dir_name: str, frontmatter: str, body: str = "\n# Body\n") -> Path:
    """Create <parent>/<dir_name>/SKILL.md with the given raw frontmatter block."""
    skill_dir = parent / dir_name
    skill_dir.mkdir()
    content = "---\n" + textwrap.dedent(frontmatter).strip("\n") + "\n---\n" + body
    (skill_dir / "SKILL.md").write_text(content)
    return skill_dir


class ValidSkillTest(unittest.TestCase):
    def test_minimal_valid_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(
                Path(tmp),
                "my-skill",
                'name: my-skill\ndescription: "Does a thing AND triggers when the user asks."',
            )
            valid, message = validate_skill(skill_dir)
            self.assertTrue(valid, message)
            self.assertIn("my-skill", message)

    def test_optional_keys_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(
                Path(tmp),
                "full-skill",
                """
                name: full-skill
                description: "Does a thing when asked."
                license: MIT
                allowed-tools: ["Bash"]
                metadata:
                  author: someone
                compatibility: "Works everywhere."
                """,
            )
            valid, message = validate_skill(skill_dir)
            self.assertTrue(valid, message)


class StructuralFailureTest(unittest.TestCase):
    def test_not_a_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            valid, message = validate_skill(Path(tmp) / "does-not-exist")
            self.assertFalse(valid)
            self.assertIn("Not a directory", message)

    def test_missing_skill_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "empty"
            skill_dir.mkdir()
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("SKILL.md not found", message)

    def test_no_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "no-fm"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# Just a heading\n")
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("No YAML frontmatter", message)

    def test_unterminated_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "open-fm"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("---\nname: open-fm\n")
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("Invalid frontmatter format", message)

    def test_invalid_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(
                Path(tmp), "bad-yaml", 'name: bad-yaml\ndescription: "unterminated'
            )
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("Invalid YAML", message)

    def test_frontmatter_not_a_dict(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(Path(tmp), "scalar-fm", "just a bare string")
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("must be a YAML dictionary", message)


class FrontmatterKeyTest(unittest.TestCase):
    def test_unexpected_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(
                Path(tmp),
                "extra-key",
                'name: extra-key\ndescription: "ok"\nbogus: true',
            )
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("Unexpected frontmatter key", message)
            self.assertIn("bogus", message)

    def test_missing_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(Path(tmp), "no-name", 'description: "ok"')
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("Missing 'name'", message)

    def test_missing_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(Path(tmp), "no-desc", "name: no-desc")
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("Missing 'description'", message)


class NameValidationTest(unittest.TestCase):
    def test_name_not_a_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(Path(tmp), "42", 'name: 42\ndescription: "ok"')
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("Name must be a string", message)

    def test_name_not_kebab_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(
                Path(tmp), "Bad_Name", 'name: Bad_Name\ndescription: "ok"'
            )
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("kebab-case", message)

    def test_name_double_hyphen(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(
                Path(tmp), "bad--name", 'name: bad--name\ndescription: "ok"'
            )
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("cannot start/end with hyphen", message)

    def test_name_too_long(self):
        long_name = "a" * 65
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(
                Path(tmp), long_name, f'name: {long_name}\ndescription: "ok"'
            )
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("max 64", message)

    def test_name_must_match_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(
                Path(tmp), "dir-name", 'name: other-name\ndescription: "ok"'
            )
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("must match directory name", message)


class DescriptionValidationTest(unittest.TestCase):
    def test_description_not_a_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(
                Path(tmp), "desc-int", "name: desc-int\ndescription: 5"
            )
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("Description must be a string", message)

    def test_description_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(
                Path(tmp), "desc-empty", 'name: desc-empty\ndescription: "   "'
            )
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("Description is empty", message)

    def test_description_angle_brackets(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(
                Path(tmp),
                "desc-angle",
                'name: desc-angle\ndescription: "Use <tool> here"',
            )
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("angle brackets", message)

    def test_description_too_long(self):
        long_desc = "x" * 108
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(
                Path(tmp),
                "desc-long",
                f'name: desc-long\ndescription: "{long_desc}"',
            )
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("max 107", message)

    def test_description_multiline(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(
                Path(tmp),
                "desc-nl",
                'name: desc-nl\ndescription: "line one\\nline two"',
            )
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("single line", message)


class CompatibilityValidationTest(unittest.TestCase):
    def test_compatibility_not_a_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(
                Path(tmp),
                "compat-int",
                'name: compat-int\ndescription: "ok"\ncompatibility: 5',
            )
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("compatibility must be a string", message)

    def test_compatibility_too_long(self):
        long_compat = "z" * 501
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(
                Path(tmp),
                "compat-long",
                f'name: compat-long\ndescription: "ok"\ncompatibility: "{long_compat}"',
            )
            valid, message = validate_skill(skill_dir)
            self.assertFalse(valid)
            self.assertIn("max 500", message)


class EndToEndTest(unittest.TestCase):
    def run_validate(self, skill_dir: Path):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(skill_dir)],
            capture_output=True,
            text=True,
        )

    def test_valid_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(
                Path(tmp), "good", 'name: good\ndescription: "Does a thing when asked."'
            )
            result = self.run_validate(skill_dir)
            self.assertEqual(result.returncode, 0)
            self.assertIn("OK:", result.stdout)

    def test_invalid_exits_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = write_skill(Path(tmp), "bad", 'description: "no name"')
            result = self.run_validate(skill_dir)
            self.assertEqual(result.returncode, 1)
            self.assertIn("FAIL:", result.stdout)

    def test_wrong_arg_count_exits_one(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("Usage:", result.stdout)


if __name__ == "__main__":
    unittest.main()
