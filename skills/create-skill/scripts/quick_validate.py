#!/usr/bin/env python3
"""
Quick validation for a skill directory — checks SKILL.md frontmatter and naming.

Shared name/description rules live in frontmatter_rules.py (also used by create-agents)
so the two validators cannot drift. This script adds the skill-specific checks.

Usage:
    quick_validate.py <skill-directory>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import frontmatter_rules  # noqa: E402


ALLOWED_PROPERTIES = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}


def validate_skill(skill_path):
    skill_path = Path(skill_path).expanduser().resolve()

    if not skill_path.is_dir():
        return False, f"Not a directory: {skill_path}"

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, f"SKILL.md not found in {skill_path}"

    frontmatter, error = frontmatter_rules.parse_frontmatter(skill_md.read_text())
    if error:
        return False, error

    unexpected = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected:
        return False, (
            f"Unexpected frontmatter key(s): {', '.join(sorted(unexpected))}. "
            f"Allowed: {', '.join(sorted(ALLOWED_PROPERTIES))}"
        )

    if "name" not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if "description" not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    name_error = frontmatter_rules.validate_name(frontmatter["name"])
    if name_error:
        return False, name_error
    name = frontmatter["name"].strip()

    if name != skill_path.name:
        return False, f"Frontmatter name '{name}' must match directory name '{skill_path.name}'"

    description_error = frontmatter_rules.validate_description(frontmatter["description"])
    if description_error:
        return False, description_error

    compatibility = frontmatter.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, str):
            return False, f"compatibility must be a string, got {type(compatibility).__name__}"
        if len(compatibility) > 500:
            return False, f"compatibility is {len(compatibility)} chars; max 500"

    return True, f"Skill '{name}' is valid"


def main():
    if len(sys.argv) != 2:
        print("Usage: quick_validate.py <skill-directory>")
        sys.exit(1)

    valid, message = validate_skill(sys.argv[1])
    print(("OK: " if valid else "FAIL: ") + message)
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
