#!/usr/bin/env python3
"""
Skill Initializer — creates a new skill directory from a template.

Subdirectories are opt-in: pass a flag for each one the skill actually needs. With no flags,
only SKILL.md is created.

Usage:
    init_skill.py <skill-name> --path <output-directory>
                  [--scripts] [--references] [--assets] [--subskills]

Examples:
    init_skill.py my-new-skill --path ~/.claude/skills
    init_skill.py pdf --path ~/.claude/skills --scripts --references
    init_skill.py router --path ./skills --subskills
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


SKILL_TEMPLATE = """---
name: {skill_name}
description: "TODO replace this single line with what the skill does AND when to trigger. Be slightly pushy."
---

# {skill_title}

## Overview

TODO: 1-2 sentences explaining what this skill enables.

## When to use

TODO: Concrete user phrases or contexts that should trigger this skill.

## How to use

TODO: Step-by-step procedural instructions. Imperative voice ("To do X, do Y"), not second
person. Explain the WHY behind each step.
"""

ROUTING_SECTION = """
## Routing

This skill is a dispatcher. The table below loads when the skill triggers, so route with no
extra file read. Map an observable condition to one subskill file; keep conditions mutually
exclusive. After routing, read only the chosen subskill.

| When the user... | Load |
|---|---|
| TODO: describes condition A | `subskills/example-route.md` |
| TODO: describes condition B | `subskills/another-route.md` |
"""

RESOURCE_DESCRIPTIONS = {
    "assets": "files used in the skill's output (templates, images, fonts)",
    "references": "documentation Claude loads on demand",
    "scripts": "executable code; can be run without loading into context",
    "subskills": "focused instruction files a dispatcher SKILL.md routes to (not full skills)",
}

EXAMPLE_SCRIPT = '''#!/usr/bin/env python3
"""Example helper script for {skill_name}. Replace or delete."""


def main():
    print("Example script for {skill_name}")


if __name__ == "__main__":
    main()
'''

EXAMPLE_REFERENCE = """# Reference Documentation for {skill_title}

Placeholder reference doc. Reference files are good for:

- API documentation
- Database schemas
- Detailed workflow guides
- Domain knowledge too long for SKILL.md

Reference files are loaded by Claude on demand, not always in context. Link to them from
SKILL.md with a clear pointer about when to read them.
"""

EXAMPLE_ASSET = """Placeholder asset file. Assets are files used in the skill's output (templates,
images, fonts, boilerplate). They are NOT loaded into Claude's context.
"""

EXAMPLE_SUBSKILL = """# Example Route

Placeholder subskill. A subskill is a focused instruction file for ONE branch of a dispatcher
skill. It is NOT a full skill: no frontmatter, no `description`, never triggered on its own.
The parent SKILL.md routes here via its routing table, then this file takes over.

Use subskills when one SKILL.md would otherwise stack several unrelated workflows that don't
share context. Each route loads only the instructions it needs, keeping the dispatcher lean.

## Steps

TODO: Imperative, step-by-step instructions for this specific route. Explain the WHY.
"""


def title_case(skill_name: str) -> str:
    """Convert a kebab-case skill name to a Title Case heading.

    Examples
    --------
    >>> title_case("pdf-tools")
    'Pdf Tools'
    """
    return " ".join(word.capitalize() for word in skill_name.split("-"))


def build_skill_md(skill_name: str, skill_title: str, created_dirs: set[str]) -> str:
    """Render the SKILL.md body, including routing and resource sections.

    Parameters
    ----------
    skill_name : str
        Kebab-case skill name for the frontmatter.
    skill_title : str
        Title Case heading derived from the name.
    created_dirs : set[str]
        Resource subdirectories being created; controls the optional sections.

    Returns
    -------
    str
        The full SKILL.md contents.
    """
    body = SKILL_TEMPLATE.format(skill_name=skill_name, skill_title=skill_title)
    if "subskills" in created_dirs:
        body += ROUTING_SECTION
    if created_dirs:
        lines = [
            "",
            "## Resources",
            "",
            "This skill includes these resource directories:",
            "",
        ]
        for name in sorted(created_dirs):
            lines.append(f"- `{name}/` — {RESOURCE_DESCRIPTIONS[name]}")
        body += "\n".join(lines) + "\n"
    return body


def init_skill(skill_name: str, path: str, dirs: set[str]) -> Path | None:
    """Create a skill directory and its opt-in resource subdirectories.

    Parameters
    ----------
    skill_name : str
        Kebab-case skill name; also the directory name.
    path : str
        Parent directory the skill is created inside.
    dirs : set[str]
        Resource subdirectories to create (``scripts``, ``references``,
        ``assets``, ``subskills``).

    Returns
    -------
    Path | None
        The created skill directory, or ``None`` if it already existed or
        could not be created.
    """
    skill_dir = Path(path).expanduser().resolve() / skill_name

    if skill_dir.exists():
        logger.error("directory already exists: %s", skill_dir)
        return None

    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
    except OSError as error:
        logger.error("creating directory: %s", error)
        return None
    print(f"Created {skill_dir}")

    skill_title = title_case(skill_name)
    (skill_dir / "SKILL.md").write_text(build_skill_md(skill_name, skill_title, dirs))
    print("  + SKILL.md")

    if "scripts" in dirs:
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir()
        example_script = scripts_dir / "example.py"
        example_script.write_text(EXAMPLE_SCRIPT.format(skill_name=skill_name))
        example_script.chmod(0o755)
        print("  + scripts/example.py")

    if "references" in dirs:
        references_dir = skill_dir / "references"
        references_dir.mkdir()
        (references_dir / "reference.md").write_text(
            EXAMPLE_REFERENCE.format(skill_title=skill_title)
        )
        print("  + references/reference.md")

    if "assets" in dirs:
        assets_dir = skill_dir / "assets"
        assets_dir.mkdir()
        (assets_dir / "example_asset.txt").write_text(EXAMPLE_ASSET)
        print("  + assets/example_asset.txt")

    if "subskills" in dirs:
        subskills_dir = skill_dir / "subskills"
        subskills_dir.mkdir()
        (subskills_dir / "example-route.md").write_text(EXAMPLE_SUBSKILL)
        print("  + subskills/example-route.md")

    print("\nNext steps:")
    step = 1
    print(f"  {step}. Edit {skill_dir}/SKILL.md — fill in description and instructions")
    step += 1
    if dirs:
        listed = ", ".join(f"{name}/" for name in sorted(dirs))
        print(f"  {step}. Customize the example files in {listed}")
        step += 1
    print(
        f"  {step}. Validate: python3 ~/.claude/skills/create-skill/scripts/quick_validate.py {skill_dir}"
    )

    return skill_dir


def main() -> None:
    """Parse arguments and create the skill directory, exiting non-zero on failure."""
    parser = argparse.ArgumentParser(
        description="Create a new skill directory from a template. Subdirectories are opt-in.",
    )
    parser.add_argument(
        "skill_name", help="Skill name: lowercase, hyphens, <=64 chars (kebab-case)"
    )
    parser.add_argument(
        "--path", required=True, help="Directory the skill is created inside"
    )
    parser.add_argument(
        "--scripts", action="store_true", help="Create scripts/ with an example script"
    )
    parser.add_argument(
        "--references",
        action="store_true",
        help="Create references/ with an example doc",
    )
    parser.add_argument(
        "--assets", action="store_true", help="Create assets/ with an example file"
    )
    parser.add_argument(
        "--subskills",
        action="store_true",
        help="Create subskills/ + a routing table in SKILL.md (dispatcher pattern)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    dirs = {
        name
        for name in ("scripts", "references", "assets", "subskills")
        if getattr(args, name)
    }

    result = init_skill(args.skill_name, args.path, dirs)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
