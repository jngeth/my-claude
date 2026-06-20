"""Tests for frontmatter_rules.py."""

from __future__ import annotations

from types import ModuleType


def test_parse_valid(frontmatter_rules: ModuleType) -> None:
    frontmatter, error = frontmatter_rules.parse_frontmatter(
        "---\nname: x\ndescription: y\n---\nbody"
    )
    assert error is None
    assert frontmatter == {"name": "x", "description": "y"}


def test_parse_no_frontmatter(frontmatter_rules: ModuleType) -> None:
    frontmatter, error = frontmatter_rules.parse_frontmatter("# Just a heading\n")
    assert frontmatter is None
    assert "No YAML frontmatter" in error


def test_parse_unterminated(frontmatter_rules: ModuleType) -> None:
    frontmatter, error = frontmatter_rules.parse_frontmatter("---\nname: open\n")
    assert frontmatter is None
    assert "Invalid frontmatter format" in error


def test_parse_invalid_yaml(frontmatter_rules: ModuleType) -> None:
    frontmatter, error = frontmatter_rules.parse_frontmatter(
        '---\nname: "unterminated\n---\n'
    )
    assert frontmatter is None
    assert "Invalid YAML" in error


def test_parse_not_a_dict(frontmatter_rules: ModuleType) -> None:
    frontmatter, error = frontmatter_rules.parse_frontmatter(
        "---\njust a bare string\n---\n"
    )
    assert frontmatter is None
    assert "must be a YAML dictionary" in error


def test_name_valid(frontmatter_rules: ModuleType) -> None:
    assert frontmatter_rules.validate_name("code-reviewer") is None


def test_name_not_a_string(frontmatter_rules: ModuleType) -> None:
    assert "Name must be a string" in frontmatter_rules.validate_name(42)


def test_name_not_kebab(frontmatter_rules: ModuleType) -> None:
    assert "kebab-case" in frontmatter_rules.validate_name("Bad_Name")


def test_name_double_hyphen(frontmatter_rules: ModuleType) -> None:
    assert "cannot start/end with hyphen" in frontmatter_rules.validate_name(
        "bad--name"
    )


def test_name_too_long_default(frontmatter_rules: ModuleType) -> None:
    assert "max 64" in frontmatter_rules.validate_name("a" * 65)


def test_name_custom_max_length(frontmatter_rules: ModuleType) -> None:
    assert "max 10" in frontmatter_rules.validate_name("a" * 11, max_length=10)


def test_description_valid(frontmatter_rules: ModuleType) -> None:
    assert frontmatter_rules.validate_description("Does a thing when asked.") is None


def test_description_not_a_string(frontmatter_rules: ModuleType) -> None:
    assert "Description must be a string" in frontmatter_rules.validate_description(5)


def test_description_empty(frontmatter_rules: ModuleType) -> None:
    assert "Description is empty" in frontmatter_rules.validate_description("   ")


def test_description_angle_brackets(frontmatter_rules: ModuleType) -> None:
    assert "angle brackets" in frontmatter_rules.validate_description("Use <tool> here")


def test_description_too_long_default(frontmatter_rules: ModuleType) -> None:
    assert "max 107" in frontmatter_rules.validate_description("x" * 108)


def test_description_multiline(frontmatter_rules: ModuleType) -> None:
    assert "single line" in frontmatter_rules.validate_description("line one\nline two")


def test_description_custom_max_length(frontmatter_rules: ModuleType) -> None:
    assert "max 50" in frontmatter_rules.validate_description("x" * 51, max_length=50)
