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

validate_agent = quick_validate.validate_agent


def write_agent(parent: Path, file_name: str, frontmatter: str, body: str = "\nYou are an agent.\n") -> Path:
    """Create <parent>/<file_name> with the given raw frontmatter block."""
    path = parent / file_name
    content = "---\n" + textwrap.dedent(frontmatter).strip("\n") + "\n---\n" + body
    path.write_text(content)
    return path


class ValidAgentTest(unittest.TestCase):
    def test_minimal_valid_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = write_agent(
                Path(tmp),
                "reviewer.md",
                'name: reviewer\ndescription: "Reviews code when the user asks for a review."',
            )
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertTrue(valid, message)
            self.assertIn("reviewer", message)

    def test_optional_keys_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = write_agent(
                Path(tmp),
                "full.md",
                """
                name: full
                description: "Does a focused thing when asked."
                tools: Read, Grep, Glob, Bash
                disallowedTools: Write
                model: sonnet
                permissionMode: plan
                skills:
                  - python
                memory: project
                color: blue
                effort: high
                """,
            )
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertTrue(valid, message)


class StructuralFailureTest(unittest.TestCase):
    def test_not_a_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            valid, message = validate_agent(Path(tmp) / "missing.md", search_dirs=[tmp])
            self.assertFalse(valid)
            self.assertIn("Not a file", message)

    def test_no_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "no-fm.md"
            path.write_text("# Just a heading\n")
            valid, message = validate_agent(path, search_dirs=[tmp])
            self.assertFalse(valid)
            self.assertIn("No YAML frontmatter", message)

    def test_unterminated_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "open.md"
            path.write_text("---\nname: open\n")
            valid, message = validate_agent(path, search_dirs=[tmp])
            self.assertFalse(valid)
            self.assertIn("Invalid frontmatter format", message)

    def test_invalid_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = write_agent(Path(tmp), "bad.md", 'name: bad\ndescription: "unterminated')
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertFalse(valid)
            self.assertIn("Invalid YAML", message)


class FrontmatterKeyTest(unittest.TestCase):
    def test_unexpected_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = write_agent(
                Path(tmp),
                "extra.md",
                'name: extra\ndescription: "ok"\nbogus: true',
            )
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertFalse(valid)
            self.assertIn("Unexpected frontmatter key", message)
            self.assertIn("bogus", message)

    def test_missing_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = write_agent(Path(tmp), "no-name.md", 'description: "ok"')
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertFalse(valid)
            self.assertIn("Missing 'name'", message)

    def test_missing_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = write_agent(Path(tmp), "no-desc.md", "name: no-desc")
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertFalse(valid)
            self.assertIn("Missing 'description'", message)


class NameAndDescriptionTest(unittest.TestCase):
    def test_name_not_kebab(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = write_agent(Path(tmp), "bad.md", 'name: Bad_Name\ndescription: "ok"')
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertFalse(valid)
            self.assertIn("kebab-case", message)

    def test_description_too_long(self):
        long_desc = "x" * 108
        with tempfile.TemporaryDirectory() as tmp:
            agent = write_agent(
                Path(tmp), "long.md", f'name: long\ndescription: "{long_desc}"'
            )
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertFalse(valid)
            self.assertIn("max 107", message)

    def test_description_angle_brackets(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = write_agent(
                Path(tmp), "angle.md", 'name: angle\ndescription: "Use <tool> here"'
            )
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertFalse(valid)
            self.assertIn("angle brackets", message)


class ModelTest(unittest.TestCase):
    def test_alias_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = write_agent(
                Path(tmp), "ok.md", 'name: ok\ndescription: "ok"\nmodel: haiku'
            )
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertTrue(valid, message)

    def test_full_id_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = write_agent(
                Path(tmp),
                "ok.md",
                'name: ok\ndescription: "ok"\nmodel: claude-opus-4-8',
            )
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertTrue(valid, message)

    def test_invalid_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = write_agent(
                Path(tmp), "bad.md", 'name: bad\ndescription: "ok"\nmodel: gpt-4'
            )
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertFalse(valid)
            self.assertIn("inherit/sonnet/opus/haiku", message)

    def test_not_a_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = write_agent(
                Path(tmp), "bad.md", 'name: bad\ndescription: "ok"\nmodel: 5'
            )
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertFalse(valid)
            self.assertIn("model must be a string", message)


class ToolsTest(unittest.TestCase):
    def test_string_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = write_agent(
                Path(tmp), "ok.md", 'name: ok\ndescription: "ok"\ntools: "Read, Grep"'
            )
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertTrue(valid, message)

    def test_bad_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = write_agent(
                Path(tmp), "bad.md", 'name: bad\ndescription: "ok"\ntools: 5'
            )
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertFalse(valid)
            self.assertIn("tools must be", message)

    def test_disallowed_bad_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = write_agent(
                Path(tmp), "bad.md", 'name: bad\ndescription: "ok"\ndisallowedTools: 5'
            )
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertFalse(valid)
            self.assertIn("disallowedTools must be", message)


class BodySizeTest(unittest.TestCase):
    def test_body_too_long(self):
        big_body = "\n".join(f"line {index}" for index in range(260))
        with tempfile.TemporaryDirectory() as tmp:
            agent = write_agent(
                Path(tmp), "big.md", 'name: big\ndescription: "ok"', body=big_body
            )
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertFalse(valid)
            self.assertIn("max 250", message)


class UniquenessTest(unittest.TestCase):
    def test_collision_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_agent(Path(tmp), "first.md", 'name: dup\ndescription: "first"')
            second = write_agent(Path(tmp), "second.md", 'name: dup\ndescription: "second"')
            valid, message = validate_agent(second, search_dirs=[tmp])
            self.assertFalse(valid)
            self.assertIn("already used by another agent", message)

    def test_unique_name_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_agent(Path(tmp), "first.md", 'name: alpha\ndescription: "first"')
            second = write_agent(Path(tmp), "second.md", 'name: beta\ndescription: "second"')
            valid, message = validate_agent(second, search_dirs=[tmp])
            self.assertTrue(valid, message)

    def test_unparseable_neighbor_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "harness.md").write_text("# Harness worker, no frontmatter\n")
            agent = write_agent(Path(tmp), "agent.md", 'name: solo\ndescription: "ok"')
            valid, message = validate_agent(agent, search_dirs=[tmp])
            self.assertTrue(valid, message)


class EndToEndTest(unittest.TestCase):
    def run_validate(self, agent_path: Path):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(agent_path)],
            capture_output=True,
            text=True,
        )

    def test_valid_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = write_agent(
                Path(tmp),
                "zzz-e2e-unique-agent.md",
                'name: zzz-e2e-unique-agent\ndescription: "A focused agent for the e2e test."',
            )
            result = self.run_validate(agent)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("OK:", result.stdout)

    def test_invalid_exits_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = write_agent(Path(tmp), "bad.md", 'description: "no name"')
            result = self.run_validate(agent)
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
