#!/usr/bin/env python3
"""
Quick validation for a skill directory — checks SKILL.md frontmatter and naming.

Usage:
    quick_validate.py <skill-directory>
"""

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip3 install pyyaml")
    sys.exit(2)


ALLOWED_PROPERTIES = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}


def validate_skill(skill_path):
    skill_path = Path(skill_path).expanduser().resolve()

    if not skill_path.is_dir():
        return False, f"Not a directory: {skill_path}"

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, f"SKILL.md not found in {skill_path}"

    content = skill_md.read_text()
    if not content.startswith("---"):
        return False, "No YAML frontmatter at top of SKILL.md"

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format (must be --- ... ---)"

    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        return False, f"Invalid YAML in frontmatter: {e}"

    if not isinstance(frontmatter, dict):
        return False, "Frontmatter must be a YAML dictionary"

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

    name = frontmatter["name"]
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if not re.match(r"^[a-z0-9-]+$", name):
        return False, f"Name '{name}' must be kebab-case (lowercase letters, digits, hyphens)"
    if name.startswith("-") or name.endswith("-") or "--" in name:
        return False, f"Name '{name}' cannot start/end with hyphen or contain '--'"
    if len(name) > 64:
        return False, f"Name is {len(name)} chars; max 64"

    if name != skill_path.name:
        return False, f"Frontmatter name '{name}' must match directory name '{skill_path.name}'"

    description = frontmatter["description"]
    if not isinstance(description, str):
        return False, f"Description must be a string, got {type(description).__name__}"
    description = description.strip()
    if not description:
        return False, "Description is empty"
    if "<" in description or ">" in description:
        return False, "Description cannot contain angle brackets"
    if len(description) > 107:
        return False, f"Description is {len(description)} chars; max 107 (120 including 'description: ' prefix)"
    if "\n" in description:
        return False, "Description must be a single line"

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
