"""Module fixtures for the writing-voice scripts under test."""

from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS_DIR = Path(__file__).parent
ScriptLoader = Callable[[Path, str], ModuleType]


@pytest.fixture(scope="session")
def align_tables(load_script: ScriptLoader) -> ModuleType:
    """The align_tables module."""
    return load_script(SCRIPTS_DIR / "align_tables.py", "writing_voice_align_tables")
