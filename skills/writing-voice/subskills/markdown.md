# Markdown Voice

The user's voice principles applied to markdown writing. Load this subskill when drafting or editing markdown:
SKILL.md, README, docs, technical writing, anything formatted with markdown.

The principles below were extracted from the user's own copy edits on a freshly written SKILL.md.
They reflect what the user actually does when they cut, not abstract style advice.

---

## The ten principles

### 1. Punctuation: colon or period, never em-dash

Em-dashes hide subordinate clauses. Colons and periods make the structure visible. Em-dashes are banned entirely.

- Before: "Mine it first - what tools they used, the sequence, corrections they made."
- After: "Mine it first: what tools they used, the sequence, corrections they made."

### 2. Cut flavor, keep instruction

The joke, anecdote, or colorful illustration is the first thing to go. The rule stays.

- Before: "Skill-creator users range from grandparents who just installed npm to senior engineers. Read the cues."
- After: "Read the cues to determine how technical the user is."

If a sentence is mostly color, cut the sentence.

### 3. Shorten examples to a stub

Leave enough to convey the shape. Let the reader fill in the rest.

- Before: "Use whenever the user mentions dashboards, metrics, or company data even without the word 'dashboard'."
- After: "Use whenever the user mentions metrics or data."

The pattern is what matters, not the exhaustive enumeration.

### 4. Drop items that aren't load-bearing

If a list item could be removed without breaking surrounding instruction, remove it.
Test: does the next step still work if this bullet is gone? If yes, it's gone.

### 5. Reduce repetition of names

Once names are established, refer to them collectively.

- Before: "example `scripts/`, `references/`, `assets/` files"
- After: "example subdirectory files"

### 6. Alphabetize lists

Alphabetize every list. Predictable ordering scans faster. The only exception is lists whose order is itself meaningful.

- Before: scripts, references, assets
- After: assets, references, scripts

### 7. Align internal constraints

If the document gives a constraint elsewhere ("keep under 250 lines"), make sure inline guidance matches.
Don't say "under 500" in one section and "under 250" in another.

### 8. Plain over voicy

Direct assertion over performative phrasing. Cut "Cool? Cool." and "billions a year in economic value here" energy.

- Before: "Be slightly pushy, Claude tends to under-trigger."
- After: "Claude tends to under-trigger."

State the rule. Trust the reader.

### 9. Pack lines toward 120 characters

Combine short consecutive lines into denser ones so each line fills toward the 120-char budget.
Narrow wraps fragment the eye and pad the line count without adding signal.

- Before (hard-wrapped at ~55, leaves a short second line):
  Em-dashes hide subordinate clauses. Colons and periods
  make the structure visible.
- After (packed toward 120, one line):
  Em-dashes hide subordinate clauses. Colons and periods make the structure visible.

**Orphan rule:** when a wrap leaves only one or two words on the next line, tighten the line above so they fit.
Drop a word, swap "and" for a comma, rephrase. No continuation line should hold fewer than three or four words.

- Before (orphan):
  "Anecdotes, jokes, voicy framing, and rhetorical flourishes go first. The rule / stays."
- After (no orphan):
  "Anecdotes, jokes, voicy framing, rhetorical flourishes go first. The rule stays."

**Sentence breaks:** when a bullet or paragraph runs several sentences, break at a sentence boundary so each line holds
whole sentences, not a stray clause leading the next line. Fill the line but break between sentences, not within one.

- Before (mid-sentence wrap):
  "reason over a stand-in. Do not ask / the user to draw a conclusion."
- After (break at the period):
  "reason over a stand-in. / Do not ask the user to draw a conclusion."

Apply when editing: if a paragraph is wrapped at 70-90 chars and the budget is 120, repack.
Apply when writing: don't break to a new line unless the next word would push past 120.
Never leave an orphan when a 1-3 char trim upstream would absorb it.

---

## Anti-patterns

- **Em-dashes.** Never use them. Replace with a colon, period, or comma.
- **The 'why this matters' kicker.** "...which means we ship faster." If the why is real, give it a sentence or cut it.
- **Adverb-led sentences.** "Importantly, ..." "Notably, ..." Drop the adverb.
- **Hedging language.** "It might be worth considering" becomes "Consider". "Generally speaking" gets deleted.
- **Echoing the heading.** A section called "Validation" that opens with "To validate...". Start with the substance.

---

## What to keep

- **Imperative voice** for instructions ("To do X, do Y").
- **The why behind a rule** when the why is non-obvious. Cut filler, not rationale.
- **Concrete file paths, command examples, code blocks.** Anchors beat abstractions.
- **No em-dashes.** Use a colon, period, or comma instead.

---

## Quick edit pass

Before shipping any markdown, read it once with these questions:

1. Any em-dashes? Replace with a colon, period, or comma.
2. Is any sentence mostly flavor?
3. Could any example be half as long?
4. Could any bullet be removed?
5. Are names repeated where "them" or "they" would do?
6. Is any list out of alphabetical order? Alphabetize unless the order is meaningful.
7. Could any short consecutive lines pack into one near 120 chars?
8. Any orphan one-or-two-word continuation lines that could be absorbed upstream?

If you answer yes to any, make the edit before sending.
