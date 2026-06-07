#!/usr/bin/env python3
"""Tests for frontmatter_rules.py. Run with: python3 -m unittest test_frontmatter_rules"""

import doctest
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "frontmatter_rules.py"

spec = importlib.util.spec_from_file_location("frontmatter_rules", SCRIPT)
frontmatter_rules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frontmatter_rules)

parse_frontmatter = frontmatter_rules.parse_frontmatter
validate_name = frontmatter_rules.validate_name
validate_description = frontmatter_rules.validate_description


def load_tests(loader, tests, ignore):
    """Run the module's doctests as part of the suite."""
    tests.addTests(doctest.DocTestSuite(frontmatter_rules))
    return tests


class ParseFrontmatterTest(unittest.TestCase):
    def test_valid(self):
        frontmatter, error = parse_frontmatter("---\nname: x\ndescription: y\n---\nbody")
        self.assertIsNone(error)
        self.assertEqual(frontmatter, {"name": "x", "description": "y"})

    def test_no_frontmatter(self):
        frontmatter, error = parse_frontmatter("# Just a heading\n")
        self.assertIsNone(frontmatter)
        self.assertIn("No YAML frontmatter", error)

    def test_unterminated(self):
        frontmatter, error = parse_frontmatter("---\nname: open\n")
        self.assertIsNone(frontmatter)
        self.assertIn("Invalid frontmatter format", error)

    def test_invalid_yaml(self):
        frontmatter, error = parse_frontmatter('---\nname: "unterminated\n---\n')
        self.assertIsNone(frontmatter)
        self.assertIn("Invalid YAML", error)

    def test_not_a_dict(self):
        frontmatter, error = parse_frontmatter("---\njust a bare string\n---\n")
        self.assertIsNone(frontmatter)
        self.assertIn("must be a YAML dictionary", error)


class ValidateNameTest(unittest.TestCase):
    def test_valid(self):
        self.assertIsNone(validate_name("code-reviewer"))

    def test_not_a_string(self):
        self.assertIn("Name must be a string", validate_name(42))

    def test_not_kebab(self):
        self.assertIn("kebab-case", validate_name("Bad_Name"))

    def test_double_hyphen(self):
        self.assertIn("cannot start/end with hyphen", validate_name("bad--name"))

    def test_too_long_default(self):
        self.assertIn("max 64", validate_name("a" * 65))

    def test_custom_max_length(self):
        self.assertIn("max 10", validate_name("a" * 11, max_length=10))


class ValidateDescriptionTest(unittest.TestCase):
    def test_valid(self):
        self.assertIsNone(validate_description("Does a thing when asked."))

    def test_not_a_string(self):
        self.assertIn("Description must be a string", validate_description(5))

    def test_empty(self):
        self.assertIn("Description is empty", validate_description("   "))

    def test_angle_brackets(self):
        self.assertIn("angle brackets", validate_description("Use <tool> here"))

    def test_too_long_default(self):
        self.assertIn("max 107", validate_description("x" * 108))

    def test_multiline(self):
        self.assertIn("single line", validate_description("line one\nline two"))

    def test_custom_max_length(self):
        self.assertIn("max 50", validate_description("x" * 51, max_length=50))


if __name__ == "__main__":
    unittest.main()
