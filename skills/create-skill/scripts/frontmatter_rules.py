#!/usr/bin/env python3
"""Shared frontmatter validation rules for skill and agent files.

Both ``create-skill`` and ``create-agents`` validate the same ``name`` and
``description`` rules. Keep that logic here so the two validators cannot drift.
The functions are pure: each validator layers its own structural checks on top.
"""

from __future__ import annotations

import re

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    raise SystemExit("Error: PyYAML is required. Install with: pip3 install pyyaml")


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def parse_frontmatter(content: str) -> tuple[dict, None] | tuple[None, str]:
    """Parse the leading YAML frontmatter block from markdown content.

    Parameters
    ----------
    content : str
        Full text of a ``SKILL.md`` or agent ``.md`` file.

    Returns
    -------
    tuple[dict | None, str | None]
        ``(frontmatter, None)`` on success, or ``(None, error)`` on failure.

    Examples
    --------
    >>> frontmatter, error = parse_frontmatter("---\\nname: x\\n---\\nbody")
    >>> error is None
    True
    >>> frontmatter["name"]
    'x'
    >>> parse_frontmatter("# no frontmatter")
    (None, 'No YAML frontmatter at top of file')
    """
    if not content.startswith("---"):
        return None, "No YAML frontmatter at top of file"

    match = FRONTMATTER_RE.match(content)
    if not match:
        return None, "Invalid frontmatter format (must be --- ... ---)"

    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError as error:
        return None, f"Invalid YAML in frontmatter: {error}"

    if not isinstance(frontmatter, dict):
        return None, "Frontmatter must be a YAML dictionary"

    return frontmatter, None


def validate_name(name: object, max_length: int = 64) -> str | None:
    """Validate a kebab-case identifier shared by skills and agents.

    Parameters
    ----------
    name : object
        The ``name`` frontmatter value.
    max_length : int, optional
        Maximum allowed length, by default 64.

    Returns
    -------
    str | None
        An error message, or ``None`` when the name is valid.

    Examples
    --------
    >>> validate_name("code-reviewer") is None
    True
    >>> validate_name("Bad_Name")
    "Name 'Bad_Name' must be kebab-case (lowercase letters, digits, hyphens)"
    """
    if not isinstance(name, str):
        return f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if not re.match(r"^[a-z0-9-]+$", name):
        return f"Name '{name}' must be kebab-case (lowercase letters, digits, hyphens)"
    if name.startswith("-") or name.endswith("-") or "--" in name:
        return f"Name '{name}' cannot start/end with hyphen or contain '--'"
    if len(name) > max_length:
        return f"Name is {len(name)} chars; max {max_length}"
    return None


def validate_description(description: object, max_length: int = 107) -> str | None:
    """Validate a skill or agent ``description`` field.

    The cap is intentionally identical for skills and agents: the description
    is the only signal that drives triggering and delegation, and it stays in
    context for every installed skill and agent, so it must stay terse.

    Parameters
    ----------
    description : object
        The ``description`` frontmatter value.
    max_length : int, optional
        Maximum length of the value, by default 107 (120 including the
        ``description: `` prefix).

    Returns
    -------
    str | None
        An error message, or ``None`` when the description is valid.

    Examples
    --------
    >>> validate_description("Reviews code when asked.") is None
    True
    >>> validate_description("   ")
    'Description is empty'
    >>> validate_description("Use the <tool> here")
    'Description cannot contain angle brackets'
    """
    if not isinstance(description, str):
        return f"Description must be a string, got {type(description).__name__}"
    description = description.strip()
    if not description:
        return "Description is empty"
    if "<" in description or ">" in description:
        return "Description cannot contain angle brackets"
    if len(description) > max_length:
        return f"Description is {len(description)} chars; max {max_length} (120 including 'description: ' prefix)"
    if "\n" in description:
        return "Description must be a single line"
    return None
