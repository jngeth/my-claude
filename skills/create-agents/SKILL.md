---
name: create-agents
description: Build, edit, evaluate, and tune Claude subagents. Use when the user wants to create or improve an agent.
---

# Create Agents

Help a user create and iterate on Claude subagents. An agent is a single Markdown file (YAML frontmatter plus a body
that becomes the system prompt) in an agents directory, usually `~/.claude/agents/` or a project's `.claude/agents/`.
There are no bundled subdirectories: the whole agent lives in one file and loads on every call.

This skill mirrors `create-skill` and shares its eval harness. Where a step reuses create-skill's machinery, this file
points at it rather than restating it. Figure out which step the user is on and jump in: they might arrive with nothing
("I want an agent for X"), a half-built draft, or feedback after running an existing agent.

For agent anatomy, frontmatter table, extension pattern and tool/model guidance, read `references/writing-guide.md`.

---

## Step 1: Capture intent

Pin down what the agent owns before writing. Fill gaps with these questions (don't dump all at once):

1. What single task should this agent own, and what does "done" look like for it?
2. When should Claude delegate to it? (the phrases or contexts that should trigger handoff)
3. What tools does it need, and should it be read-only?
4. How heavy is the work? (drives the model choice: `haiku` for cheap mechanical work, `opus` for hard reasoning)

An agent earns its keep when a side task would flood the main conversation, when a tool set should be constrained, or
when repetitive work can be routed to a cheaper model. If none of those hold, a skill or inline work may fit better.

## Step 2: Survey existing agents

Delegation keys on `description` alone, so overlapping descriptions cause mis-delegation. Before writing, scan agents
directories and read each agent's name and description:

```bash
ls ~/.claude/agents/**/*.md .claude/agents/**/*.md 2>/dev/null
grep -A2 '^name:' ~/.claude/agents/*.md .claude/agents/*.md 2>/dev/null
```

Flag two things: a **name collision** (same `name`) and **description overlap** (two agents both sound right for the
same task). Carve agents a distinct lane. Note any existing agent whose shared practice new ones could load as a skill.

## Step 3: Decide extension

There is no agent inheritance and subagents cannot spawn subagents. Shared practices lives in **skills agents load**.

Decide which applies:

- **Reuse a skill:** if a skill already holds the conventions (e.g. `python`), the agent loads it first and describes
  only how it operates on top. This repo's `python-engineer` and `python-reviewer` both do this.
- **Factor a new skill:** if two or more agents would need the same body of practice and no skill holds it yet, build
  that skill with `create-skill`, then have each agent load it. Do not copy the practice into each agent body.
- **Neither:** if only this one agent needs the knowledge, inline a few lines in its body.

See `references/writing-guide.md` ("Extension") for the worked example.

## Step 4: Initialize

```bash
python3 ~/.claude/skills/create-agents/scripts/init_agent.py <name> --path ~/.claude/agents \
    [--description "one line"] [--tools "Read, Grep, Glob, Bash"] [--model inherit] [--extends <skill-name>]
```

This writes `<name>.md` with TODO frontmatter and a lean body skeleton (role, "When invoked" loop, boundaries).
`--extends <skill>` injects a "load the skill first" section for the extension pattern.

## Step 5: Write the agent

The body **is** the system prompt and loads on every call, so keep it lean (target less than 150 lines, hard cap 250).
Write for another instance of Claude reading it cold:

- Lead with the role and the operating loop. Use imperative voice and explain the why, the same as a SKILL.md.
- If extending a skill, keep the load-first section and do not restate the skill's rules.
- Push reusable domain detail into a skill, not the body.

Use the `writing-voice` skill and see `references/writing-guide.md` for tool, model, and description specifics.

## Step 6: Validate

```bash
python3 ~/.claude/skills/create-agents/scripts/quick_validate.py ~/.claude/agents/<name>.md
```

Checks the frontmatter key set, name (kebab-case, unique across both agents directories), description (≤107 chars,
single line, no angle brackets), `model` shape, `tools`/`disallowedTools` well-formedness, and 250-line body cap.

## Step 7: Test on real prompts

Draft 2-3 prompts real users would type and run the harness in `create-skill/references/eval-loop.md` (read it first).
It is written for skills; map it to agents:

| Eval-loop term                        | Agent equivalent                                        |
| ------------------------------------- | ------------------------------------------------------- |
| skill path                            | the agent: invoke it by `@`-mention or `--agent <name>` |
| `with_skill/` run                     | `with_agent/` run (delegate to the agent)               |
| `without_skill/` run                  | baseline with no agent (the main model does the task)   |
| `aggregate_benchmark.py --skill-name` | pass the agent name to the same `--skill-name` flag     |

For a quick check instead, delegate each prompt to the agent yourself and show the output to the user.

## Step 8: Tune the description

Delegation works like skill triggering, same optimization loop applies: `create-skill/references/description-tuning.md`.
Generate trigger queries, review with the user, run the loop, re-validate to confirm the tuned description still fits.

---

## Anatomy of an agent

Single `.md` file: YAML frontmatter (only `name`, `description` required) plus a body that becomes the system prompt.
No bundled directories, no progressive disclosure inside the agent. For the full frontmatter field table, the
body-is-the-system-prompt consequences, and the extension pattern, see `references/writing-guide.md`.

## Iteration

After testing, the user gives feedback. Generalize from it; don't add fiddly overfit rules that only fix one example.
Keep the body lean and explain the why. If several agents keep needing the same practice, factor it into a skill rather
than growing each body. Repeat until the user is satisfied.

For full iteration mechanics (iteration directories, snapshot comparison), see `create-skill/references/eval-loop.md`.

---

## Review checklist

Before declaring an agent done, verify:

- [ ] Description names both what the agent does and when to delegate
- [ ] Description fits ≤107 chars, single line, no angle brackets
- [ ] Name is kebab-case and unique across both agents directories
- [ ] Body is lean (target ~150 lines, under the 250 cap) with no skill content copied in
- [ ] No time-sensitive info in the body (model versions, "currently", dated features)
- [ ] `python3 ~/.claude/skills/create-agents/scripts/quick_validate.py <agent-file>` passes

---

Note: agents must not contain malware, exploit code, or behavior that would surprise a user reading the description.
