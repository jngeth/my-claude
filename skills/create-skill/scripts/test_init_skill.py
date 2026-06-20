"""Tests for init_skill.py."""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest


def run_init(module: ModuleType, args: list[str]) -> subprocess.CompletedProcess[str]:
    """Invoke init_skill.py as a subprocess."""
    script = module.__file__
    assert script is not None
    return subprocess.run(
        [sys.executable, script, *args],
        capture_output=True,
        text=True,
    )


def test_title_case_single_word(init_skill: ModuleType) -> None:
    assert init_skill.title_case("pdf") == "Pdf"


def test_title_case_hyphenated(init_skill: ModuleType) -> None:
    assert init_skill.title_case("my-new-skill") == "My New Skill"


def test_no_dirs_has_no_resources_section(init_skill: ModuleType) -> None:
    body = init_skill.build_skill_md("solo", "Solo", set())
    assert "name: solo" in body
    assert "# Solo" in body
    assert "## Resources" not in body
    assert "## Routing" not in body


def test_resources_section_lists_created_dirs(init_skill: ModuleType) -> None:
    body = init_skill.build_skill_md("res", "Res", {"scripts", "references"})
    assert "## Resources" in body
    assert "`scripts/`" in body
    assert "`references/`" in body
    assert "`assets/`" not in body


def test_subskills_adds_routing_section(init_skill: ModuleType) -> None:
    body = init_skill.build_skill_md("router", "Router", {"subskills"})
    assert "## Routing" in body
    assert "subskills/example-route.md" in body
    assert "`subskills/`" in body


def test_no_routing_without_subskills(init_skill: ModuleType) -> None:
    body = init_skill.build_skill_md("plain", "Plain", {"scripts"})
    assert "## Routing" not in body


def test_skill_md_only_by_default(init_skill: ModuleType, tmp_path: Path) -> None:
    skill_dir = init_skill.init_skill("bare", str(tmp_path), set())
    assert skill_dir is not None
    assert (skill_dir / "SKILL.md").is_file()
    children = {child.name for child in skill_dir.iterdir()}
    assert children == {"SKILL.md"}


def test_scripts_dir_created_and_executable(
    init_skill: ModuleType, tmp_path: Path
) -> None:
    skill_dir = init_skill.init_skill("with-scripts", str(tmp_path), {"scripts"})
    example = skill_dir / "scripts" / "example.py"
    assert example.is_file()
    assert example.stat().st_mode & 0o111, "script should be executable"
    assert "with-scripts" in example.read_text()


def test_all_optional_dirs(init_skill: ModuleType, tmp_path: Path) -> None:
    skill_dir = init_skill.init_skill(
        "kitchen-sink", str(tmp_path), {"scripts", "references", "assets", "subskills"}
    )
    assert (skill_dir / "scripts" / "example.py").is_file()
    assert (skill_dir / "references" / "reference.md").is_file()
    assert (skill_dir / "assets" / "example_asset.txt").is_file()
    assert (skill_dir / "subskills" / "example-route.md").is_file()


def test_skill_md_matches_builder(init_skill: ModuleType, tmp_path: Path) -> None:
    skill_dir = init_skill.init_skill("matchy", str(tmp_path), {"references"})
    expected = init_skill.build_skill_md("matchy", "Matchy", {"references"})
    assert (skill_dir / "SKILL.md").read_text() == expected


def test_reference_doc_uses_title(init_skill: ModuleType, tmp_path: Path) -> None:
    skill_dir = init_skill.init_skill("doc-skill", str(tmp_path), {"references"})
    text = (skill_dir / "references" / "reference.md").read_text()
    assert "Doc Skill" in text


def test_existing_directory_returns_none(
    init_skill: ModuleType, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    (tmp_path / "taken").mkdir()
    with caplog.at_level(logging.ERROR):
        result = init_skill.init_skill("taken", str(tmp_path), set())
    assert result is None
    assert "already exists" in caplog.text


def test_creates_skill_exit_zero(init_skill: ModuleType, tmp_path: Path) -> None:
    result = run_init(init_skill, ["cli-skill", "--path", str(tmp_path), "--scripts"])
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "cli-skill" / "SKILL.md").is_file()
    assert (tmp_path / "cli-skill" / "scripts" / "example.py").is_file()


def test_existing_dir_exit_one(init_skill: ModuleType, tmp_path: Path) -> None:
    (tmp_path / "dup").mkdir()
    result = run_init(init_skill, ["dup", "--path", str(tmp_path)])
    assert result.returncode == 1
    assert "already exists" in result.stderr


def test_missing_required_path_exit_two(init_skill: ModuleType) -> None:
    result = run_init(init_skill, ["orphan"])
    assert result.returncode == 2  # argparse usage error
