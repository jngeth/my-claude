"""Module fixtures for the create-skill scripts under test."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS_DIR = Path(__file__).parent
ScriptLoader = Callable[[Path, str], ModuleType]


@pytest.fixture(scope="session")
def frontmatter_rules(load_script: ScriptLoader) -> ModuleType:
    """The shared frontmatter validation module."""
    return load_script(
        SCRIPTS_DIR / "frontmatter_rules.py", "create_skill_frontmatter_rules"
    )


@pytest.fixture(scope="session")
def quick_validate(load_script: ScriptLoader) -> ModuleType:
    """The create-skill quick_validate module."""
    return load_script(SCRIPTS_DIR / "quick_validate.py", "create_skill_quick_validate")


@pytest.fixture(scope="session")
def init_skill(load_script: ScriptLoader) -> ModuleType:
    """The init_skill module."""
    return load_script(SCRIPTS_DIR / "init_skill.py", "create_skill_init_skill")


@pytest.fixture(scope="session")
def aggregate_benchmark(load_script: ScriptLoader) -> ModuleType:
    """The aggregate_benchmark module."""
    return load_script(
        SCRIPTS_DIR / "aggregate_benchmark.py", "create_skill_aggregate_benchmark"
    )
