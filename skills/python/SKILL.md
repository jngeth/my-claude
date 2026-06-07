---
name: python
description: Python conventions. Use for any Python code or tooling.
---

# Python

Conventions for writing Python. Apply them to any Python work: new modules, edits to existing files, tests, debugging,
or tooling. Reproducible environments (uv), tests written first (TDD), and code that clears a quality gate before done.

## Plan before coding

Before writing code, brainstorm multiple approaches, rank them by probable effectiveness, then implement the best one.
This surfaces a simpler design before you commit to the first idea that came to mind.

## Environment and dependencies (uv)

- Manage environments and dependencies with `uv`. Run project code and tests through `uv run`
  (e.g. `uv run python script.py`, `uv run pytest`) so they use the project's locked environment.
- Add dependencies with `uv add <pkg>`, dev/test dependencies `uv add --dev <pkg>`. Never hand-edit `pyproject.toml`.
  Let uv keep it and the lockfile in sync.

## Test-driven development

- Write the test before the implementation. Watch it fail, write the minimum code to pass, then refactor.
- Use `pytest`. Collect shared fixtures in `conftest.py` so they are not duplicated across test modules.
- Reach for `hypothesis` (property-based testing) when the input space is large or edge-case heavy. Let it generate
  cases instead of enumerating them by hand.
- Test real code. Avoid mocking: it couples tests to implementation details and hides integration bugs. When you must
  isolate, prefer pytest's `monkeypatch` over mock objects. Use test doubles only when there is no real alternative
  (network, clocks, external services).
- When tests fail, rerun failures with `uv run pytest --last-failed` to tighten the loop before running the full suite.

## Bugs and regressions

When you find a bug or regression, write a failing test to reproduces it then fix the code. Think about how to make the
whole class of bug impossible (better types, invariants, boundary alidation) rather than patching the single instance.

## Code quality gate

After changing code, run the tooling and fix what it reports. A green gate is the definition of done.
`ruff`, `ty`, and `prek` are standalone CLIs installed globally, so run them directly, not through `uv run`.

- Lint and format with ruff: `ruff check --fix .` then `ruff format .`
- Type-check with ty: `ty check` (it finds the project's `.venv` automatically to resolve imports).
- Run pre-commit hooks with prek: `prek run --all-files` (install the git hook once with `prek install`).
- Track complexity with wily: not bundled, so install it per project with `uv tool install wily`, then
  `wily build .` to snapshot and `wily diff .` to see how your change moved complexity.

## Types and casting

- Annotate every function parameter and return type. The hints are the contract the type checker enforces.
- Do not lean on casting. Frequent `cast(...)` or `# type: ignore` signals the types are wrong. Refactor to model the
  data correctly. Confine casting to boundary layers where you parse untyped input from external systems.

## Docstrings

- Write numpy-style docstrings for every function and class.
- Include doctests in docstring to show real usage. Run with `uv run pytest --doctest-modules` so examples stay correct.

## Logging and CLIs

- Use `logging`, not `print`, for diagnostics. Log enough to explain failures, and never catch-and-log in a way that
  swallows the stack trace: re-raise or let the exception propagate so the traceback survives.
- For command-line interfaces, add a `--verbose` flag that raises the log level to expose debugging detail.
