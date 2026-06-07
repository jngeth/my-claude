#!/usr/bin/env python3
"""
Agent Initializer — creates a new Claude Code agent file from a template.

An agent is a single .md file (YAML frontmatter + body) in an agents directory
(usually ~/.claude/agents). The body becomes the agent's system prompt, so the
template starts lean: role, an operating loop, and boundaries.

Usage:
    init_agent.py <name> --path <agents-directory>
                  [--description "one line"] [--tools "Read, Grep"]
                  [--model inherit] [--extends <skill-name>]

Examples:
    init_agent.py code-reviewer --path ~/.claude/agents --tools "Read, Grep, Glob, Bash"
    init_agent.py python-engineer --path ~/.claude/agents --extends python
"""

import argparse
import sys
from pathlib import Path


DEFAULT_DESCRIPTION = (
    "TODO one line: what this agent does AND when to delegate (max 107 chars, single line)."
)

EXTENDS_SECTION = """
## Load the {skill} conventions first

Before doing the work, load the project's {skill} conventions: invoke the `{skill}` skill, or read
`skills/{skill}/SKILL.md` if the skill is unavailable. It is the source of truth. Everything below is
how you operate on top of those conventions, not a replacement. Do not restate or contradict the skill.
"""

BODY_TEMPLATE = """# {title}

You are a {role}. TODO: one or two sentences on the outcome you reliably deliver.
{extends}
## When invoked

1. TODO: restate the goal and acceptance criteria in your own words.
2. TODO: do the work in small, verifiable steps. Explain the why, not just the what.
3. TODO: report back. Summarize what you did and cite files as `path:line`.

## Boundaries

- Scope discipline: do what the task asks. List adjacent problems instead of fixing them.
- If you hit a blocker you cannot resolve, stop and report it rather than guessing or hacking around it.
"""


def title_case(name: str) -> str:
    return " ".join(word.capitalize() for word in name.split("-"))


def build_frontmatter(name, description, tools, model):
    lines = ["---", f"name: {name}", f'description: "{description}"']
    if tools:
        lines.append(f"tools: {tools}")
    if model:
        lines.append(f"model: {model}")
    lines.append("---")
    return "\n".join(lines)


def build_agent_md(name, description, tools, model, extends):
    frontmatter = build_frontmatter(name, description, tools, model)
    extends_block = EXTENDS_SECTION.format(skill=extends) if extends else "\n"
    body = BODY_TEMPLATE.format(
        title=title_case(name),
        role=f"{title_case(name).lower()}",
        extends=extends_block,
    )
    return frontmatter + "\n\n" + body


def init_agent(name, path, description, tools, model, extends):
    agents_dir = Path(path).expanduser().resolve()
    agents_dir.mkdir(parents=True, exist_ok=True)

    agent_file = agents_dir / f"{name}.md"
    if agent_file.exists():
        print(f"Error: file already exists: {agent_file}")
        return None

    agent_file.write_text(build_agent_md(name, description, tools, model, extends))
    print(f"Created {agent_file}")

    print("\nNext steps:")
    print(f"  1. Edit {agent_file} — fill in the description and the TODO sections")
    if extends:
        print(f"  2. Confirm the `{extends}` skill exists and holds the shared conventions")
    validate = Path("~/.claude/skills/create-agents/scripts/quick_validate.py").expanduser()
    print(f"  {'3' if extends else '2'}. Validate: python3 {validate} {agent_file}")

    return agent_file


def main():
    parser = argparse.ArgumentParser(
        description="Create a new Claude Code agent file from a template.",
    )
    parser.add_argument("name", help="Agent name: lowercase, hyphens, <=64 chars (kebab-case)")
    parser.add_argument("--path", required=True, help="Agents directory the file is created in")
    parser.add_argument("--description", default=DEFAULT_DESCRIPTION, help="One-line description")
    parser.add_argument("--tools", default="", help='Allowlist, e.g. "Read, Grep, Glob, Bash"')
    parser.add_argument("--model", default="", help="inherit, sonnet, opus, haiku, or a claude-... id")
    parser.add_argument("--extends", default="", help="Skill whose conventions this agent loads first")
    args = parser.parse_args()

    result = init_agent(
        args.name, args.path, args.description, args.tools, args.model, args.extends
    )
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
