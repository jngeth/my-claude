# Description Tuning

The `description` field in a skill's frontmatter is the **only** thing Claude reads when deciding whether to invoke
the skill. Tuning it produces outsized gains relative to the effort. Run this after the skill works.

---

## How triggering actually works

Skills appear in Claude's `available_skills` list as **name + description**. Claude consults a skill only when it judges
the description matches what the user is asking _and_ the task is substantive enough to benefit from the skill.

Key implication: **simple one-step queries don't reliably trigger skills.** "Read this PDF" won't trigger a PDF skill
even with a perfect description, because Claude can handle it with basic tools. Test queries must be substantive enough
that consulting a skill is actually worth Claude's time.

---

## Step 1: Generate trigger eval queries

Create ~20 queries: a mix of should-trigger and should-not-trigger. JSON format:

```json
[
  { "query": "the user prompt", "should_trigger": true },
  { "query": "another prompt", "should_trigger": false }
]
```

**Queries must be realistic**: what a Claude Code or human user would actually type. Not abstract requests, but concrete
ones with detail: file paths, personal context, column names, URLs. Some lowercase, some with typos. Vary length.

- **Bad**: `"Format this data"`, `"Extract text from PDF"`, `"Create a chart"`
- **Good**: `"ok so I have this xlsx file (its in my downloads, called something like 'Q4 sales final FINAL v2.xlsx') 
and I want to add a column that shows profit as a percentage. Revenue in column C and costs are in column D i think"`

### Should-trigger queries (8–10)

Aim for coverage. Different phrasings of the same intent: formal, casual, abbreviated. Include cases the skill or file
type is not named but clearly needed, uncommon use cases, and cases where the skill competes with others but should win.

### Should-not-trigger queries (8–10)

Valuable ones are **near-misses** queries that share keywords or concepts with the skill but actually need something
different. Adjacent domains, ambiguous phrasing where a naive keyword match would trigger but shouldn't, contexts where
another tool is more appropriate.

**Don't make negatives obviously irrelevant.** "Write a Fibonacci function" as a negative for a PDF skill is too easy.
Negatives should be genuinely tricky.

---

## Step 2: Review with the user

Present the eval set to the user. Have them edit queries, toggle should-trigger labels, add or remove entries.
This step matters: bad eval queries lead to bad descriptions.

A lightweight version: just paste the JSON into the conversation and ask "look these over, flip anything that's wrong,
add cases you think I'm missing."

---

## Step 3: Run the loop (manual version)

This skill doesn't bundle a full optimization loop. Do it manually instead:

For the current description, score it against the eval set:

1. For each query, ask Claude (in a fresh subagent) whether it would invoke the skill given the description.
   Run each query **3 times** triggering is non-deterministic, you need a rate not a single bit.
2. Compute the train/test pass rate.
3. Read the failures. What kind of query is the description missing? What kind of negative is it over-triggering on?
4. Propose 2-3 description variants that address the failures. Show the user.
5. Re-score the variants. Pick the best **test** score (not train) to avoid overfitting to queries you tuned against.

To help with step 1, the subagent prompt can be as simple as:

```
You are deciding whether to invoke a skill. The skill's description is:

  "<paste current description>"

User says: "<paste query>"

Answer ONLY "trigger" or "skip".
```

Run that prompt 3× per query, count the "trigger" responses.

---

## Step 4: Apply and validate

Update the `description` field in SKILL.md. Show the user the before/after and report the scores. Validate the skill:

```bash
python3 ~/.claude/skills/create-skill/scripts/quick_validate.py <skill-dir>
```

---

## Heuristics from past tuning

- **Spell out scenarios.** "Use when the user mentions X, Y, or Z" beats abstract definitions.
- **Name the file types and tools.** "Excel files, .xlsx, spreadsheets, pivot tables" catches more than "spreadsheets."
- **Cover indirect triggers.** "Use even if the user doesn't say 'dashboard'" rescues queries that describe the need.
- **Don't oversell.** Pushy is good; misleading is bad. Description must not claim capabilities skill doesn't deliver.
- **Watch for keyword collisions** with other installed skills. If two skills both mention "data," disambiguate.
