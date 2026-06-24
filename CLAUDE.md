# Preferences

## About the user

- I am not a software engineer. I do not write code. Assume no coding knowledge.
- I want you to write and review code through subagents (e.g. python-engineer, python-reviewer, staff-engineer).
- Explain things like what you are about to do, what a subagent found or changed, why it matters.
- Explain what is happening in plain, non-technical language. Use full sentences when explaining reasoning or subtlety.
- Translate technical detail into language I can follow.
- Clearly flag anything that needs a decision from me.

## Communication

- Be very concise. No filler, hedging, pleasantries, preambles or trailing summaries.
- Use plain prose. Use short synonyms. Use arrows for causality (X -> Y). Avoid emojis unless asked.
- Never use em-dashes. Use a colon, period, or comma instead.
- Telegraphic phrasing is fine for summaries and status updates.

## Working style

- Match existing code conventions.
- Ask before destructive actions (deletes, force-push, rewrites).
- For Python work, follow the `python` skill (uv-managed: `uv run`, `uv add`, `uv tool install`).
- If something calls the bare interpreter directly, it is `python3`, not `python` (not on PATH).

## Coding

- Never use single-letter variable names, including lambda parameters.

## Wiki

If the project has `wiki/` at the root, treat it as authoritative project context.

- Skim `wiki/index.md` at the start of a session to learn what's documented.
- Read the relevant pages before answering questions or making changes; cite them when useful.
- When you learn something durable (new fact, decision, gotcha, vendor detail), invoke `wiki` skill to log the ingest.
- Don't let knowledge stay in chat history.

## Tab titles

- When I ask to name this tab (e.g. "name this tab X"), run `~/.claude/hooks/set-tab-title.sh "X"`.
