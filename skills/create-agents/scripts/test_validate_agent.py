"""Tests for quick_validate.py (create-agents)."""

import subprocess
import sys
import textwrap
from pathlib import Path
from types import ModuleType


def write_agent(
    parent: Path, file_name: str, frontmatter: str, body: str = "\nYou are an agent.\n"
) -> Path:
    """Create ``<parent>/<file_name>`` with the given raw frontmatter block."""
    path = parent / file_name
    content = "---\n" + textwrap.dedent(frontmatter).strip("\n") + "\n---\n" + body
    path.write_text(content)
    return path


def run_validate(module: ModuleType, agent_path: Path) -> subprocess.CompletedProcess[str]:
    """Invoke quick_validate.py as a subprocess against ``agent_path``."""
    script = module.__file__
    assert script is not None
    return subprocess.run(
        [sys.executable, script, str(agent_path)], capture_output=True, text=True
    )


def test_minimal_valid_agent(quick_validate: ModuleType, tmp_path: Path) -> None:
    agent = write_agent(
        tmp_path,
        "reviewer.md",
        'name: reviewer\ndescription: "Reviews code when the user asks for a review."',
    )
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert valid, message
    assert "reviewer" in message


def test_optional_keys_allowed(quick_validate: ModuleType, tmp_path: Path) -> None:
    agent = write_agent(
        tmp_path,
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
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert valid, message


def test_not_a_file(quick_validate: ModuleType, tmp_path: Path) -> None:
    valid, message = quick_validate.validate_agent(
        tmp_path / "missing.md", search_dirs=[str(tmp_path)]
    )
    assert not valid
    assert "Not a file" in message


def test_no_frontmatter(quick_validate: ModuleType, tmp_path: Path) -> None:
    path = tmp_path / "no-fm.md"
    path.write_text("# Just a heading\n")
    valid, message = quick_validate.validate_agent(path, search_dirs=[str(tmp_path)])
    assert not valid
    assert "No YAML frontmatter" in message


def test_unterminated_frontmatter(quick_validate: ModuleType, tmp_path: Path) -> None:
    path = tmp_path / "open.md"
    path.write_text("---\nname: open\n")
    valid, message = quick_validate.validate_agent(path, search_dirs=[str(tmp_path)])
    assert not valid
    assert "Invalid frontmatter format" in message


def test_invalid_yaml(quick_validate: ModuleType, tmp_path: Path) -> None:
    agent = write_agent(tmp_path, "bad.md", 'name: bad\ndescription: "unterminated')
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert not valid
    assert "Invalid YAML" in message


def test_unexpected_key(quick_validate: ModuleType, tmp_path: Path) -> None:
    agent = write_agent(
        tmp_path, "extra.md", 'name: extra\ndescription: "ok"\nbogus: true'
    )
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert not valid
    assert "Unexpected frontmatter key" in message
    assert "bogus" in message


def test_missing_name(quick_validate: ModuleType, tmp_path: Path) -> None:
    agent = write_agent(tmp_path, "no-name.md", 'description: "ok"')
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert not valid
    assert "Missing 'name'" in message


def test_missing_description(quick_validate: ModuleType, tmp_path: Path) -> None:
    agent = write_agent(tmp_path, "no-desc.md", "name: no-desc")
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert not valid
    assert "Missing 'description'" in message


def test_name_not_kebab(quick_validate: ModuleType, tmp_path: Path) -> None:
    agent = write_agent(tmp_path, "bad.md", 'name: Bad_Name\ndescription: "ok"')
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert not valid
    assert "kebab-case" in message


def test_description_too_long(quick_validate: ModuleType, tmp_path: Path) -> None:
    long_desc = "x" * 108
    agent = write_agent(tmp_path, "long.md", f'name: long\ndescription: "{long_desc}"')
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert not valid
    assert "max 107" in message


def test_description_angle_brackets(quick_validate: ModuleType, tmp_path: Path) -> None:
    agent = write_agent(
        tmp_path, "angle.md", 'name: angle\ndescription: "Use <tool> here"'
    )
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert not valid
    assert "angle brackets" in message


def test_model_alias_ok(quick_validate: ModuleType, tmp_path: Path) -> None:
    agent = write_agent(tmp_path, "ok.md", 'name: ok\ndescription: "ok"\nmodel: haiku')
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert valid, message


def test_model_full_id_ok(quick_validate: ModuleType, tmp_path: Path) -> None:
    agent = write_agent(
        tmp_path, "ok.md", 'name: ok\ndescription: "ok"\nmodel: claude-opus-4-8'
    )
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert valid, message


def test_model_invalid_alias(quick_validate: ModuleType, tmp_path: Path) -> None:
    agent = write_agent(
        tmp_path, "bad.md", 'name: bad\ndescription: "ok"\nmodel: gpt-4'
    )
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert not valid
    assert "inherit/sonnet/opus/haiku" in message


def test_model_not_a_string(quick_validate: ModuleType, tmp_path: Path) -> None:
    agent = write_agent(tmp_path, "bad.md", 'name: bad\ndescription: "ok"\nmodel: 5')
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert not valid
    assert "model must be a string" in message


def test_tools_string_ok(quick_validate: ModuleType, tmp_path: Path) -> None:
    agent = write_agent(
        tmp_path, "ok.md", 'name: ok\ndescription: "ok"\ntools: "Read, Grep"'
    )
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert valid, message


def test_tools_bad_type(quick_validate: ModuleType, tmp_path: Path) -> None:
    agent = write_agent(tmp_path, "bad.md", 'name: bad\ndescription: "ok"\ntools: 5')
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert not valid
    assert "tools must be" in message


def test_disallowed_tools_bad_type(quick_validate: ModuleType, tmp_path: Path) -> None:
    agent = write_agent(
        tmp_path, "bad.md", 'name: bad\ndescription: "ok"\ndisallowedTools: 5'
    )
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert not valid
    assert "disallowedTools must be" in message


def test_body_too_long(quick_validate: ModuleType, tmp_path: Path) -> None:
    big_body = "\n".join(f"line {index}" for index in range(260))
    agent = write_agent(
        tmp_path, "big.md", 'name: big\ndescription: "ok"', body=big_body
    )
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert not valid
    assert "max 250" in message


def test_collision_detected(quick_validate: ModuleType, tmp_path: Path) -> None:
    write_agent(tmp_path, "first.md", 'name: dup\ndescription: "first"')
    second = write_agent(tmp_path, "second.md", 'name: dup\ndescription: "second"')
    valid, message = quick_validate.validate_agent(second, search_dirs=[str(tmp_path)])
    assert not valid
    assert "already used by another agent" in message


def test_unique_name_ok(quick_validate: ModuleType, tmp_path: Path) -> None:
    write_agent(tmp_path, "first.md", 'name: alpha\ndescription: "first"')
    second = write_agent(tmp_path, "second.md", 'name: beta\ndescription: "second"')
    valid, message = quick_validate.validate_agent(second, search_dirs=[str(tmp_path)])
    assert valid, message


def test_unparseable_neighbor_ignored(
    quick_validate: ModuleType, tmp_path: Path
) -> None:
    (tmp_path / "harness.md").write_text("# Harness worker, no frontmatter\n")
    agent = write_agent(tmp_path, "agent.md", 'name: solo\ndescription: "ok"')
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert valid, message


def test_e2e_valid_exits_zero(quick_validate: ModuleType, tmp_path: Path) -> None:
    agent = write_agent(
        tmp_path,
        "zzz-e2e-unique-agent.md",
        'name: zzz-e2e-unique-agent\ndescription: "A focused agent for the e2e test."',
    )
    result = run_validate(quick_validate, agent)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK:" in result.stdout


def test_e2e_invalid_exits_one(quick_validate: ModuleType, tmp_path: Path) -> None:
    agent = write_agent(tmp_path, "bad.md", 'description: "no name"')
    result = run_validate(quick_validate, agent)
    assert result.returncode == 1
    assert "FAIL:" in result.stdout


def test_e2e_wrong_arg_count_exits_one(quick_validate: ModuleType) -> None:
    script = quick_validate.__file__
    assert script is not None
    result = subprocess.run([sys.executable, script], capture_output=True, text=True)
    assert result.returncode == 1
    assert "Usage:" in result.stdout
