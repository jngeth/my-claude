"""Shared pytest fixtures for loading standalone skill scripts as modules.

The scripts under ``skills/*/scripts`` are executable files, not an installed
package, and some share a basename (there are two ``quick_validate.py`` files).
Importing them by bare name would collide in ``sys.modules``. ``load_script``
loads each file under an explicit, unique module name so tests can import the
exact script they target.
"""

import importlib.util
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

ScriptLoader = Callable[[Path, str], ModuleType]


def _load_script(path: Path, name: str) -> ModuleType:
    """Import the Python file at ``path`` as a module registered under ``name``.

    Parameters
    ----------
    path : Path
        The script file to import.
    name : str
        Unique module name to register, avoiding basename collisions.

    Returns
    -------
    ModuleType
        The executed module.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot create import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def load_script() -> ScriptLoader:
    """Return the loader used by per-directory fixtures to import scripts."""
    return _load_script
