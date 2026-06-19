"""Tests for quick_validate.py."""

import subprocess
import sys
import textwrap
from pathlib import Path
from types import ModuleType


def write_skill(
    parent: Path, dir_name: str, frontmatter: str, body: str = "\n# Body\n"
) -> Path:
    """Create ``<parent>/<dir_name>/SKILL.md`` with the given raw frontmatter block."""
    skill_dir = parent / dir_name
    skill_dir.mkdir()
    content = "---\n" + textwrap.dedent(frontmatter).strip("\n") + "\n---\n" + body
    (skill_dir / "SKILL.md").write_text(content)
    return skill_dir


def run_validate(module: ModuleType, skill_dir: Path) -> subprocess.CompletedProcess[str]:
    """Invoke quick_validate.py as a subprocess against ``skill_dir``."""
    script = module.__file__
    assert script is not None
    return subprocess.run(
        [sys.executable, script, str(skill_dir)],
        capture_output=True,
        text=True,
    )


def test_minimal_valid_skill(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = write_skill(
        tmp_path,
        "my-skill",
        'name: my-skill\ndescription: "Does a thing AND triggers when the user asks."',
    )
    valid, message = quick_validate.validate_skill(skill_dir)
    assert valid, message
    assert "my-skill" in message


def test_optional_keys_allowed(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = write_skill(
        tmp_path,
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
    valid, message = quick_validate.validate_skill(skill_dir)
    assert valid, message


def test_not_a_directory(quick_validate: ModuleType, tmp_path: Path) -> None:
    valid, message = quick_validate.validate_skill(tmp_path / "does-not-exist")
    assert not valid
    assert "Not a directory" in message


def test_missing_skill_md(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = tmp_path / "empty"
    skill_dir.mkdir()
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "SKILL.md not found" in message


def test_no_frontmatter(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = tmp_path / "no-fm"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Just a heading\n")
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "No YAML frontmatter" in message


def test_unterminated_frontmatter(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = tmp_path / "open-fm"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: open-fm\n")
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "Invalid frontmatter format" in message


def test_invalid_yaml(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = write_skill(
        tmp_path, "bad-yaml", 'name: bad-yaml\ndescription: "unterminated'
    )
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "Invalid YAML" in message


def test_frontmatter_not_a_dict(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = write_skill(tmp_path, "scalar-fm", "just a bare string")
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "must be a YAML dictionary" in message


def test_unexpected_key(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = write_skill(
        tmp_path, "extra-key", 'name: extra-key\ndescription: "ok"\nbogus: true'
    )
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "Unexpected frontmatter key" in message
    assert "bogus" in message


def test_missing_name(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = write_skill(tmp_path, "no-name", 'description: "ok"')
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "Missing 'name'" in message


def test_missing_description(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = write_skill(tmp_path, "no-desc", "name: no-desc")
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "Missing 'description'" in message


def test_name_not_a_string(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = write_skill(tmp_path, "42", 'name: 42\ndescription: "ok"')
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "Name must be a string" in message


def test_name_not_kebab_case(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = write_skill(tmp_path, "Bad_Name", 'name: Bad_Name\ndescription: "ok"')
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "kebab-case" in message


def test_name_double_hyphen(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = write_skill(tmp_path, "bad--name", 'name: bad--name\ndescription: "ok"')
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "cannot start/end with hyphen" in message


def test_name_too_long(quick_validate: ModuleType, tmp_path: Path) -> None:
    long_name = "a" * 65
    skill_dir = write_skill(
        tmp_path, long_name, f'name: {long_name}\ndescription: "ok"'
    )
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "max 64" in message


def test_name_must_match_directory(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = write_skill(tmp_path, "dir-name", 'name: other-name\ndescription: "ok"')
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "must match directory name" in message


def test_description_not_a_string(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = write_skill(tmp_path, "desc-int", "name: desc-int\ndescription: 5")
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "Description must be a string" in message


def test_description_empty(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = write_skill(
        tmp_path, "desc-empty", 'name: desc-empty\ndescription: "   "'
    )
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "Description is empty" in message


def test_description_angle_brackets(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = write_skill(
        tmp_path, "desc-angle", 'name: desc-angle\ndescription: "Use <tool> here"'
    )
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "angle brackets" in message


def test_description_too_long(quick_validate: ModuleType, tmp_path: Path) -> None:
    long_desc = "x" * 108
    skill_dir = write_skill(
        tmp_path, "desc-long", f'name: desc-long\ndescription: "{long_desc}"'
    )
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "max 107" in message


def test_description_multiline(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = write_skill(
        tmp_path, "desc-nl", 'name: desc-nl\ndescription: "line one\\nline two"'
    )
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "single line" in message


def test_compatibility_not_a_string(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = write_skill(
        tmp_path, "compat-int", 'name: compat-int\ndescription: "ok"\ncompatibility: 5'
    )
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "compatibility must be a string" in message


def test_compatibility_too_long(quick_validate: ModuleType, tmp_path: Path) -> None:
    long_compat = "z" * 501
    skill_dir = write_skill(
        tmp_path,
        "compat-long",
        f'name: compat-long\ndescription: "ok"\ncompatibility: "{long_compat}"',
    )
    valid, message = quick_validate.validate_skill(skill_dir)
    assert not valid
    assert "max 500" in message


def test_valid_exits_zero(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = write_skill(
        tmp_path, "good", 'name: good\ndescription: "Does a thing when asked."'
    )
    result = run_validate(quick_validate, skill_dir)
    assert result.returncode == 0
    assert "OK:" in result.stdout


def test_invalid_exits_one(quick_validate: ModuleType, tmp_path: Path) -> None:
    skill_dir = write_skill(tmp_path, "bad", 'description: "no name"')
    result = run_validate(quick_validate, skill_dir)
    assert result.returncode == 1
    assert "FAIL:" in result.stdout


def test_wrong_arg_count_exits_one(quick_validate: ModuleType) -> None:
    script = quick_validate.__file__
    assert script is not None
    result = subprocess.run([sys.executable, script], capture_output=True, text=True)
    assert result.returncode == 1
    assert "Usage:" in result.stdout
