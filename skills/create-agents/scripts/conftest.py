"""Module fixtures for the create-agents scripts under test."""

from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS_DIR = Path(__file__).parent
ScriptLoader = Callable[[Path, str], ModuleType]


@pytest.fixture(scope="session")
def init_agent(load_script: ScriptLoader) -> ModuleType:
    """The init_agent module."""
    return load_script(SCRIPTS_DIR / "init_agent.py", "create_agents_init_agent")


@pytest.fixture(scope="session")
def quick_validate(load_script: ScriptLoader) -> ModuleType:
    """The create-agents quick_validate module."""
    return load_script(
        SCRIPTS_DIR / "quick_validate.py", "create_agents_quick_validate"
    )
