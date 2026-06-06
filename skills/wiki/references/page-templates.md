# Page Templates

Starter formats for page types a wiki uses. Use on `init` and when creating a page of a type we haven't written before.
Adapt freely. The templates are scaffolds, not contracts.

All pages are plain markdown with optional YAML frontmatter. Cross-page links use `[[Page Name]]`. Source citations are
numbered footnotes (`[^N]`) defined at the bottom of each page that point at external references
(URL, file path, conversation date), not at other wiki pages.

---

## `index.md`

The routing layer. The LLM reads this first on every `query` to decide which pages to drill into.
Keep entries short: one link plus one line. Group by category. Update on every ingest.

```markdown
# Index

_Updated YYYY-MM-DD. <N> pages total._

## Entities

- [[Acme Corp]]: affiliate vendor; quarterly remittance, NET-30.
- [[Jane Smith]]: Acme account contact since 2024.

## Concepts

- [[Affiliate Reconciliation]]: process of matching vendor statements to internal records.
- [[Remittance Cycle]]: when and how vendors pay out commissions.

## Synthesis

- [[Vendor Comparison]]: payment terms across Acme, Globex, Initech.
```

---

## `log.md`

Newest-first: prepend each new entry. Each entry starts with `## [YYYY-MM-DD] <op> | <title>` so
`grep "^## \[" wiki/log.md | head -N` returns the N most recent. Operations: `ingest`, `init`, `lint`, `query`.

```markdown
# Log

## [2026-05-27] query | how does Acme remit vs EF?

- Pages read: [[Acme Corp]], [[EF]], [[Remittance Cycle]]
- Filed answer at: [[Vendor Comparison]]

## [2026-05-26] ingest | Acme Q1 Statement

- Source: ~/Downloads/acme-q1-2026.pdf
- New: [[Acme Corp]]
- Updated: [[Remittance Cycle]], [[index]]
- Notes: First vendor on the wiki. Established the `Entities/Vendors` section.

## [2026-05-25] init | wiki scaffolded

- Created `wiki/`, `wiki/index.md`, `wiki/log.md`.
```

---

## Entity page

One per durable thing: a company, person, product, dataset, system component.
Entities accumulate facts over time as more sources mention them.

```markdown
---
type: entity
first_seen: 2026-05-01
---

# Acme Corp

Affiliate network vendor. Pays monthly commissions on a NET-30 cycle.

## Profile

- Type: affiliate vendor
- Contact: [[Jane Smith]]
- Contract: MSA signed 2024-03, auto-renews annually
- Remittance: NET-30 from statement date

## Facts

- 2.3% transaction fee deducted before remittance [^1].
- Statement format is CSV with trailing summary block [^1].
- Reconciliation mismatches in Q4 2025 traced to currency conversion timing [^2].

## Open questions

- Are mid-month adjustments reported on the following statement or back-dated?

[^1]: ~/Downloads/acme-q1-2026.pdf, ingested 2026-05-26.

[^2]: internal/reconciliation-postmortem.md, ingested 2026-05-30.
```

---

## Concept page

One per recurring idea, process, or abstraction. Concepts synthesize across many sources and entities.

```markdown
---
type: concept
---

# Remittance Cycle

When and how an affiliate vendor pays out earned commissions.

## Variants observed

- **NET-30**: payment 30 days after statement close. Seen for [[Acme Corp]] [^1].
- **NET-60**: payment 60 days after statement close. Seen for [[Globex]] [^2].
- **Mid-month + month-end**: two payments per cycle. Seen for [[Initech]] [^3].

## Implications

- NET-60 vendors create a forecast lag relevant to [[Cash Flow Forecast]].
- Cycle-end timing determines when statements land for [[Affiliate Reconciliation]].

[^1]: ~/Downloads/acme-q1-2026.pdf, ingested 2026-05-26.

[^2]: https://example.com/onboarding, ingested 2026-05-28.

[^3]: initech-api-spec.json from vendor portal, ingested 2026-05-29.
```

---

## Synthesis page

A page filed back from a `query` answer or a deliberate cross-cutting analysis.
Optional but high-value: synthesis pages are where the wiki's compounding value shows up.

```markdown
---
type: synthesis
created: 2026-05-27
---

# Vendor Comparison

Cross-cut of remittance terms and statement shapes across active vendors.

| Vendor        | Cycle   | Fee  | Statement format    |
| ------------- | ------- | ---- | ------------------- |
| [[Acme Corp]] | NET-30  | 2.3% | CSV + summary block |
| [[Globex]]    | NET-60  | 3.0% | XLSX, multi-sheet   |
| [[Initech]]   | mid+end | 1.8% | JSON via API        |

## Notes

- NET-60 with Globex is the binding constraint on the [[Cash Flow Forecast]] [^2].
- Initech's JSON feed is the only programmatic source; others require parsing [^3].

[^1]: ~/Downloads/acme-q1-2026.pdf, ingested 2026-05-26.

[^2]: https://example.com/onboarding, ingested 2026-05-28.

[^3]: initech-api-spec.json from vendor portal, ingested 2026-05-29.
```
