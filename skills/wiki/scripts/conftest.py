"""Module fixtures for the wiki scripts under test."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS_DIR = Path(__file__).parent
ScriptLoader = Callable[[Path, str], ModuleType]


@pytest.fixture(scope="session")
def lint(load_script: ScriptLoader) -> ModuleType:
    """The wiki lint module."""
    return load_script(SCRIPTS_DIR / "lint.py", "wiki_lint")
