"""Tests for init_agent.py."""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest


def make_agent(init_agent: ModuleType, parent: Path, name: str, **kwargs: str) -> Path:
    """Call init_agent with sensible defaults and return the created file path."""
    params: dict[str, str] = {
        "description": init_agent.DEFAULT_DESCRIPTION,
        "tools": "",
        "model": "",
        "extends": "",
    }
    params.update(kwargs)
    return init_agent.init_agent(name, str(parent), **params)


def run_init(module: ModuleType, args: list[str]) -> subprocess.CompletedProcess[str]:
    """Invoke init_agent.py as a subprocess."""
    script = module.__file__
    assert script is not None
    return subprocess.run(
        [sys.executable, script, *args], capture_output=True, text=True
    )


def test_title_case_hyphenated(init_agent: ModuleType) -> None:
    assert init_agent.title_case("python-engineer") == "Python Engineer"


def test_minimal_frontmatter(init_agent: ModuleType) -> None:
    text = init_agent.build_agent_md("solo", "Does a thing.", "", "", "")
    assert "name: solo" in text
    assert 'description: "Does a thing."' in text
    assert "# Solo" in text
    assert "tools:" not in text
    assert "model:" not in text
    assert "Load the" not in text


def test_tools_and_model_included(init_agent: ModuleType) -> None:
    text = init_agent.build_agent_md("rev", "Reviews.", "Read, Grep", "sonnet", "")
    assert "tools: Read, Grep" in text
    assert "model: sonnet" in text


def test_extends_adds_load_section(init_agent: ModuleType) -> None:
    text = init_agent.build_agent_md("py", "Builds.", "", "", "python")
    assert "Load the python conventions first" in text
    assert "`python` skill" in text


def test_creates_named_file(init_agent: ModuleType, tmp_path: Path) -> None:
    agent = make_agent(init_agent, tmp_path, "code-reviewer")
    assert agent is not None
    assert agent.name == "code-reviewer.md"
    assert agent.is_file()


def test_creates_missing_parent_dir(init_agent: ModuleType, tmp_path: Path) -> None:
    nested = tmp_path / "deep" / "agents"
    agent = make_agent(init_agent, nested, "fresh")
    assert agent.is_file()


def test_existing_file_returns_none(
    init_agent: ModuleType, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    make_agent(init_agent, tmp_path, "dup")
    with caplog.at_level(logging.ERROR):
        result = init_agent.init_agent(
            "dup", str(tmp_path), init_agent.DEFAULT_DESCRIPTION, "", "", ""
        )
    assert result is None
    assert "already exists" in caplog.text


def test_generated_default_agent_passes_validation(
    init_agent: ModuleType, quick_validate: ModuleType, tmp_path: Path
) -> None:
    agent = make_agent(init_agent, tmp_path, "scaffold-demo")
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert valid, message


def test_generated_full_agent_passes_validation(
    init_agent: ModuleType, quick_validate: ModuleType, tmp_path: Path
) -> None:
    agent = make_agent(
        init_agent,
        tmp_path,
        "full-demo",
        description="Reviews Python diffs when the user asks for review.",
        tools="Read, Grep, Glob, Bash",
        model="inherit",
        extends="python",
    )
    valid, message = quick_validate.validate_agent(agent, search_dirs=[str(tmp_path)])
    assert valid, message


def test_creates_agent_exit_zero(init_agent: ModuleType, tmp_path: Path) -> None:
    result = run_init(
        init_agent,
        ["cli-agent", "--path", str(tmp_path), "--tools", "Read, Grep"],
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "cli-agent.md").is_file()


def test_existing_file_exit_one(init_agent: ModuleType, tmp_path: Path) -> None:
    (tmp_path / "dup.md").write_text("x")
    result = run_init(init_agent, ["dup", "--path", str(tmp_path)])
    assert result.returncode == 1
    assert "already exists" in result.stderr


def test_missing_required_path_exit_two(init_agent: ModuleType) -> None:
    result = run_init(init_agent, ["orphan"])
    assert result.returncode == 2  # argparse usage error
