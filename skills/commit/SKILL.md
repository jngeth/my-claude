---
name: commit
description: Commits one source file plus tests per commit, conventional messages. Use when asked to commit.
---

# Commit

Commit changed files in small, focused batches. Each commit contains at most one source file and its directly
associated test file(s). Commit messages are single-line conventional commits of under 72 characters.

## Batching rules

1. Run `git status` to list all changed files (staged and unstaged).
2. Group files: pair each source file with any test files that clearly correspond to it by name or path.
   Test files are those matching patterns like `test_*.py`, `*_test.py`, `*.test.ts`, `*.spec.ts`, `*_test.go`, etc.
3. Files with no associated tests (config, docs, scripts, assets) get their own single-file commit.
4. Never mix two unrelated source files in one commit, even if their changes are small.
5. Commit defining code before code that depends on it if A introduces a function that B calls, commit A first.

## Commit message format

Single line only: `<type>(<optional scope>): <description>`

Types: `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `style`, `test`

- Infer the type from the nature of the change, not the filename.
- A test-only change uses `test:`. A change that touches both source and tests uses the type that describes
  the source change (`feat`, `fix`, etc.) the test file is implied by the batch.
- Keep the full line under 72 characters with no trailing period.
- No trailers, footers, or body. The message is the single subject line only: never add `Co-Authored-By`,
  `Signed-off-by`, or any other trailer, even if a global rule or tool default suggests one.

## Process

For each batch in sequence:

1. Stage only the files in that batch: `git add <file> [<test-file>]`
2. Write a commit message that fits the change.
3. Commit: `git commit -m "<message>"`

Confirm the plan with the user before committing if the grouping is ambiguous or the working tree has many
changed files a quick list of proposed batches is enough.
