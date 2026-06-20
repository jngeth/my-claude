#!/usr/bin/env python3
"""
Quick validation for a Claude Code agent file — checks frontmatter, naming, and body size.

An agent is a single .md file (YAML frontmatter + body). The shared name/description rules
come from create-skill's frontmatter_rules.py so skills and agents stay consistent; this
script adds the agent-specific checks: the agent frontmatter key set, name uniqueness across
the agent directories, a body-size cap, and light model/tools sanity.

Usage:
    quick_validate.py <agent-file.md>
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_shared_rules() -> ModuleType:
    """Import frontmatter_rules.py, owned by the create-skill skill.

    Tries the installed location (~/.claude/skills) first, then a repo-relative path so
    the validator works before the skills directory is symlinked.
    """
    candidates = [
        Path("~/.claude/skills/create-skill/scripts").expanduser(),
        Path(__file__).resolve().parents[2] / "create-skill" / "scripts",
    ]
    for candidate in candidates:
        module_path = candidate / "frontmatter_rules.py"
        if module_path.exists():
            spec = importlib.util.spec_from_file_location(
                "frontmatter_rules", module_path
            )
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    raise SystemExit(
        "Error: could not locate create-skill/scripts/frontmatter_rules.py"
    )


frontmatter_rules = _load_shared_rules()


# Frontmatter keys Claude Code accepts on an agent. Mirrors the official subagent docs.
AGENT_PROPERTIES = {
    "name",
    "description",
    "tools",
    "disallowedTools",
    "model",
    "permissionMode",
    "maxTurns",
    "skills",
    "mcpServers",
    "hooks",
    "memory",
    "background",
    "effort",
    "isolation",
    "color",
    "initialPrompt",
}

VALID_MODEL_ALIASES = {"inherit", "sonnet", "opus", "haiku"}

# The body IS the system prompt and loads on every invocation; there is no progressive
# disclosure inside an agent. Keep it lean and push reusable detail into a skill.
MAX_BODY_LINES = 250


def default_search_dirs() -> list[Path]:
    """Directories scanned for name collisions: user agents, then project agents."""
    return [
        Path("~/.claude/agents").expanduser(),
        Path.cwd() / ".claude" / "agents",
    ]


def find_name_collision(
    name: str, agent_path: Path, search_dirs: list[Path]
) -> Path | None:
    """Return the path of another agent file declaring ``name``, or None.

    Files that fail to parse (e.g. harness prompts without frontmatter) are skipped.

    Parameters
    ----------
    name : str
        The agent name to look for.
    agent_path : Path
        The agent file being validated; excluded from the search.
    search_dirs : list[Path]
        Directories searched recursively for ``*.md`` agent files.

    Returns
    -------
    Path | None
        The conflicting file, or ``None`` when the name is unique.
    """
    agent_path = agent_path.resolve()
    for base in search_dirs:
        base = Path(base)
        if not base.is_dir():
            continue
        for other in sorted(base.rglob("*.md")):
            if other.resolve() == agent_path:
                continue
            frontmatter, error = frontmatter_rules.parse_frontmatter(other.read_text())
            if error:
                continue
            other_name = frontmatter.get("name")
            if isinstance(other_name, str) and other_name.strip() == name:
                return other.resolve()
    return None


def validate_agent(
    agent_path: str | Path, search_dirs: list[Path] | None = None
) -> tuple[bool, str]:
    """Validate a Claude Code agent file's frontmatter, naming, and body size.

    Parameters
    ----------
    agent_path : str | Path
        Path to the agent ``.md`` file.
    search_dirs : list[Path] | None, optional
        Directories scanned for name collisions; defaults to
        :func:`default_search_dirs` when ``None``.

    Returns
    -------
    tuple[bool, str]
        ``(True, message)`` when valid, otherwise ``(False, reason)``.
    """
    resolved = Path(agent_path).expanduser().resolve()
    if search_dirs is None:
        search_dirs = default_search_dirs()

    if not resolved.is_file():
        return False, f"Not a file: {resolved}"

    content = resolved.read_text()
    frontmatter, error = frontmatter_rules.parse_frontmatter(content)
    if error:
        return False, error

    unexpected = set(frontmatter.keys()) - AGENT_PROPERTIES
    if unexpected:
        return False, (
            f"Unexpected frontmatter key(s): {', '.join(sorted(unexpected))}. "
            f"Allowed: {', '.join(sorted(AGENT_PROPERTIES))}"
        )

    if "name" not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if "description" not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    name_error = frontmatter_rules.validate_name(frontmatter["name"])
    if name_error:
        return False, name_error
    name = frontmatter["name"].strip()

    description_error = frontmatter_rules.validate_description(
        frontmatter["description"]
    )
    if description_error:
        return False, description_error

    model = frontmatter.get("model")
    if model is not None:
        if not isinstance(model, str):
            return False, f"model must be a string, got {type(model).__name__}"
        if model not in VALID_MODEL_ALIASES and not model.startswith("claude-"):
            return (
                False,
                f"model '{model}' must be inherit/sonnet/opus/haiku or a 'claude-...' id",
            )

    for field in ("tools", "disallowedTools"):
        value = frontmatter.get(field)
        if value is not None and not isinstance(value, (str, list)):
            return False, f"{field} must be a comma-separated string or a list"

    frontmatter_match = frontmatter_rules.FRONTMATTER_RE.match(content)
    if frontmatter_match is None:
        return False, "Invalid frontmatter format (must be --- ... ---)"
    body = content[frontmatter_match.end() :]
    body_lines = len(body.splitlines())
    if body_lines > MAX_BODY_LINES:
        return False, (
            f"Agent body is {body_lines} lines; max {MAX_BODY_LINES} (target ~150). "
            f"The body is the system prompt and loads every call; move shared detail into a skill."
        )

    collision = find_name_collision(name, resolved, search_dirs)
    if collision:
        return False, f"Name '{name}' is already used by another agent: {collision}"

    return True, f"Agent '{name}' is valid"


def main() -> None:
    """Validate the agent file named on the command line."""
    if len(sys.argv) != 2:
        print("Usage: quick_validate.py <agent-file.md>")
        sys.exit(1)

    valid, message = validate_agent(sys.argv[1])
    print(("OK: " if valid else "FAIL: ") + message)
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
