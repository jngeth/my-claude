# my-claude

Claude Code configuration. Agents, skills, statusline, and anything else that lives in `~/.claude`.

## Installation

Symlink each directory into `~/.claude/`:

```bash
ln -s "$(pwd)/agents"     ~/.claude/agents
ln -s "$(pwd)/skills"     ~/.claude/skills
ln -s "$(pwd)/statusline" ~/.claude/statusline
```

Run from the repo root after cloning.

Then register in `~/.claude/settings.json`:

```json
{
  "skillsDirectories": ["~/.claude/skills"],
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline/statusline.sh"
  }
}
```

## Required Binaries

`awk`, `bash`, `flock`, and `jq`. Standard on macOS and most Linux distros.

---

## Skills

Skills are prompt modules that Claude Code loads on demand. Each lives in `skills/<name>/` with a file. Skills
directories have optional `agents/`, `references/`, and `scripts/` subdirectories. `SKILL.md` files include YAML
frontmatter and instructions.

| Skill           | What it does                                                                                      |
| --------------- | ------------------------------------------------------------------------------------------------- |
| `create-skill`  | Full workflow for building, testing, and tuning new skills                                        |
| `handoff`       | Compact the current conversation into a dated doc a fresh session can pick up                     |
| `onboard`       | Read the latest handoff doc and a targeted slice of the project wiki at session start             |
| `wiki`          | Per-project knowledge base: init, ingest, query, lint, and search operations on `wiki/` directory |
| `writing-voice` | Style guide for plain, declarative prose. Applied when writing or editing user-facing text        |

## Status line

`statusline/` is a custom Claude Code status line. Displays model, effort level, context window usage, rate limits, and
running monthly cost estimate after each response.

```
🤖 Claude Sonnet 4.6  🎯 effort:high  💭 ███░░░░░░░ 32% (51% until auto-compact)
⏱️ ██░░░░░░░░ 17% (4h 12m left)  📅 █████░░░░░ 51% (2d 6h left)  💸 $0.24
```

See [`statusline/README.md`](statusline/README.md) for full documentation, architecture, and how cost tracking works.
