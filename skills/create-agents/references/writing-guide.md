# Agent Writing Guide

Detailed guidance on writing a Claude subagent and its frontmatter. Read this when drafting or revising an agent.
For prose style, use the `writing-voice` skill (see "Writing style" below).

---

## Anatomy of an agent

An agent is a **single Markdown file** with YAML frontmatter plus a body. There are no bundled directories:
everything the agent knows that is specific to it lives in this one file.

```
~/.claude/agents/<name>.md   (user scope, all projects)
.claude/agents/<name>.md     (project scope, this repo)
```

- Identity is the `name` **field**, not filename or path. Nest files in subfolders (`agents/review/`) for organization;
  the path does not change how the agent is invoked.
- Duplicate names within one scope are resolved silently: Claude Code keeps one file and discards the other.
  Keep `name` unique across the whole tree. The validator enforces this across both agents directories.
- The body **is** the system prompt. The agent receives only the body plus basic environment details (working
  directory), not the full Claude Code system prompt.

---

## The body is the system prompt

The whole body loads on every invocation. There is no progressive disclosure inside an agent: an agent cannot read
`references/` on demand the way a skill can, because an agent has no bundled files. Two consequences:

- **Keep the body lean.** Target ~150 lines. A bloated body is paid on every call and crowds agent working context.
- **Offload reusable detail to a skill.** Domain knowledge that more than one agent needs (a testing stack, a house
  style, an API's quirks) belongs in a skill the agent loads, not copied into each agent body. See "Extension" below.

Write the body in imperative voice and explain the why behind instructions, the same as a SKILL.md. A typical body has
a one-line role, a numbered operating loop ("When invoked"), and a Boundaries section. `init_agent.py` scaffolds this.

---

## Frontmatter fields

Only `name` and `description` are required. Defaults make the rest optional. The full set Claude Code accepts:

| Field             | Required | Purpose                                                                               |
| ----------------- | -------- | ------------------------------------------------------------------------------------- |
| `name`            | Yes      | Unique kebab-case identifier. The agent's identity; the filename need not match.      |
| `description`     | Yes      | When Claude should delegate here. The only signal for automatic delegation.           |
| `background`      | No       | `true` to always run as a background task. Default `false`.                           |
| `color`           | No       | Display color in the task list and transcript.                                        |
| `disallowedTools` | No       | Denylist removed from the inherited or allowlisted set. Use for all-but-a-few.        |
| `effort`          | No       | Effort level while active: `low`, `medium`, `high`, `xhigh`, `max`. Model-dependent.  |
| `hooks`           | No       | Lifecycle hooks scoped to this agent.                                                 |
| `isolation`       | No       | `worktree` runs the agent in a temporary git worktree with an isolated repo copy.     |
| `model`           | No       | `inherit`, `sonnet`, `opus`, `haiku`, or a `claude-...` id. Defaults to `inherit`.    |
| `permissionMode`  | No       | Permission mode while agent runs: `default`, `acceptEdits`, `auto`, `dontAsk`, etc.   |
| `maxTurns`        | No       | Cap on agentic turns before the agent stops.                                          |
| `skills`          | No       | Skills preloaded in context at startup. Full content injected, not just description.  |
| `mcpServers`      | No       | MCP servers available to the agent, by name or inline definition.                     |
| `memory`          | No       | Persistent memory scope: `local`, `project`, or `user` for cross-session learning.    |
| `initialPrompt`   | No       | Auto-submitted first user turn when the agent runs as the main session via `--agent`. |
| `tools`           | No       | Allowlist of tools the agent may use. Inherits all tools if omitted.                  |

Most agents set only `name`, `description`. Reach for others when a specific need arises. Validator checks the key set,
name, description, `model` shape, and that `tools`/`disallowedTools` are a string or list; it does not police others.

---

## Description: the delegation signal

`description` is the **only** thing Claude reads when deciding whether to delegate to an agent, the same role it plays
for skill triggering. Write it to cover both what the agent does and when to hand off to it.

This repo caps the description at **107 characters, single line, no angle brackets**, the same as skills. The validator
enforces it. The cap is a deliberate house choice: it keeps always-loaded metadata small and forces a sharp, scannable
trigger. The tradeoff is less room to enumerate trigger contexts, so spend budget on the most distinctive ones.

- Weak: `Reviews code.`
- Better: `Senior Python reviewer. Use to review Python code or diffs read-only after writing Python or before a PR.`

When several agents have overlapping descriptions, Claude mis-delegates. Survey the existing agents first and make each
description carve out a distinct lane (see the SKILL.md workflow).

Tune the description with the same loop skills use: `create-skill/references/description-tuning.md`.

---

## Extension: share practice through a skill

There is **no native agent-to-agent inheritance**, and subagents cannot spawn subagents. Share base practices across
agents with **skills the agent loads first**. The agent body stays thin and points at the skill as the source of truth;
the skill holds the reusable conventions.

This repo already uses the pattern: `python-engineer` and `python-reviewer` both open by loading the `python` skill,
then describe only how they operate on top of it. `init_agent.py --extends <skill>` scaffolds the load-first section.

Worked example:

```markdown
## Load the conventions first

Before writing code, load project Python conventions: invoke the `python` skill. Stop and warn if skill is unavailable.
It is source of truth for docstrings, environment, logging, testing, tooling (prek/ruff/ty/wily) and typing.
You operate on top of those conventions, not a replacement for them. Do not restate or contradict the skill.
```

When to factor a new shared skill versus duplicate: if only one agent needs knowledge, inline a few lines in its body.
If two agents need it, move it into a skill and have each agent load it. To build that skill, use `create-skill`.

---

## Tools

Some tools are never available to a subagent because they depend on the main session state, even if you list them.
Do not put these in `tools`:

- `Agent`
- `AskUserQuestion`
- `EnterPlanMode`
- `ExitPlanMode` (unless `permissionMode: plan`)
- `ScheduleWakeup`
- `WaitForMcpServers`

An agent that needs to ask the user a question cannot: it runs headless and returns one result.
Design the agent to make a reasonable assumption and report it, rather than to prompt.

---

## Model: match cost to the task

`model` defaults to `inherit` (same model as main conversation). Override it if critical to control cost and latency:

- **`haiku`** for cheap, high-volume, mechanical work (scanning, extraction, simple lookups).
- **`inherit` or `sonnet`** for everyday engineering work.
- **`opus`** only when the task genuinely needs the strongest reasoning.

Routing a narrow, repetitive agent to `haiku` is one of the main reasons to define an agent.

---

## Anti-patterns

- **A fat body that restates a skill.** Say "load X skill first" and describe only the agent's own operating loop.
- **Description overlap with an existing agent.** Two agents with similar descriptions cause mis-delegation..
- **Inheriting all tools by default.** An agent that only reads should not hold `Edit`, `Write`, or MCP write tools.
- **Listing a session-only tool** (`Agent`, `AskUserQuestion`, ...) in `tools`. It is silently unavailable.
- **Time-sensitive content in the body** (model versions, "currently", dated lists). Loaded on every call and rots.
