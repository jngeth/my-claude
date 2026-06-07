# Claude Code Status Line

Custom status line for Claude Code. Shows model info, context window usage, rate limits, running monthly cost estimate.

Requires `jq` and `flock` (`brew install jq flock` on macOS).

Configured in `~/.claude/settings.json`:

```json
"statusLine": {
  "type": "command",
  "command": "~/.claude/statusline/statusline.sh"
}
```

---

## Display

The status line renders two lines after each response.

### Line 1 Model · Effort · Context

```
🤖 Claude Sonnet 4.6  🎯 effort:high  💭 ███░░░░░░░ 32% (51% until auto-compact)
```

| Segment                  | Description                                                                           |
| ------------------------ | ------------------------------------------------------------------------------------- |
| Model name               | Active Claude model                                                                   |
| Effort                   | Current effort level (low / medium / high / xhigh / max)                              |
| Bar                      | 10-block context bar. Green blcoks = normal usage. Yellow = auto-compact buffer zone. |
| XX%                      | Context window used                                                                   |
| (XX% until auto-compact) | Headroom remains before auto-compact triggers                                         |

**Color thresholds** (applied to context % and rate limit bars):

- Green: < 50% used
- Orange: 50–74% used
- Red: ≥ 75% used

### Line 2 Rate Limits · Cost

```
⏱️ ██░░░░░░░░ 17% (4h 12m left)  📅 █████░░░░░ 51% (2d 6h left)  💸 $0.24
```

| Segment      | Description                                                              |
| ------------ | ------------------------------------------------------------------------ |
| 5h bar       | 5-hour rolling usage window. Bar fills as quota is consumed.             |
| 7d bar       | 7-day rolling usage window.                                              |
| XX%          | Percent of quota **used**                                                |
| (Xh Xm left) | Time until the window resets. Format: `Xm` / `Xh Xm` / `Xd Xh`           |
| $X.XX        | Estimated cumulative spend for the current calendar month (Pacific Time) |

Rate limits are only available after the first message in a session.
The last known values are cached in `
s.cache` and shown at session open so the display is never blank.

---

## Directory Layout

```
~/.claude/statusline/
├── statusline.sh        # Orchestrator (registered in settings.json)
├── lib/                 # Sourced modules see Architecture
│   ├── colors.sh        # ANSI color constants + pct_color()
│   ├── pricing.sh       # load_pricing per-model token rates
│   ├── cost.sh          # track_cost session-aware monthly cost
│   ├── ratelimits.sh    # load_rate_limits fresh-or-cached limits
│   └── render.sh        # build_context_bar, rate_bar, rate_label
├── README.md            # This file
├── monthly.cache        # Persistent per-month cost totals (60s TTL)
├── monthly.cache.lock   # flock target guarding monthly.cache writes
├── ratelimits.cache     # Last known rate limit values (survives session open)
└── sessions/
    ├── <YYYY-MM>.dat      # One file per calendar month; one row per session
    └── <YYYY-MM>.dat.lock # flock target guarding that month's writes (one per month)
```

The `.lock` files are zero-byte flock targets; they persist (one per month, plus
`monthly.cache.lock`) and are safe to leave in place.

All data is self-contained in this directory. Nothing is written to `/tmp` or elsewhere.

---

## Architecture

`statusline.sh` is a thin orchestrator: it reads the harness JSON on stdin, extracts the fields it needs, sources the
modules in `lib/`, calls them in order, and prints the two lines. Each module is a **sourced fragment** (not a
standalone script) and communicates through shared shell variables, documented in each file's header.

| Module          | Entry point(s)                                | Reads                       | Sets                                  |
| --------------- | --------------------------------------------- | --------------------------- | ------------------------------------- |
| `colors.sh`     | `pct_color()`                                 |                             | color constants                       |
| `pricing.sh`    | `load_pricing <model_id>`                     |                             | `RATE_IN`, `RATE_OUT`, `RATE_CACHE_R` |
| `cost.sh`       | `track_cost`                                  | `TOK_*`, `RATE_*`, dir path | `MONTHLY_TOTAL`, `COST`               |
| `ratelimits.sh` | `load_rate_limits <json>`                     | `RATE_CACHE`                | `FIVE_H_*`, `WEEK_*`                  |
| `render.sh`     | `build_context_bar`, `rate_bar`, `rate_label` | `CTX_*`, colors             | bars / labels                         |

Load order matters: `pricing` sourced before `cost` (cost uses rates) and `colors` before `render` (render uses colors).

### Linting

Lint via the entry point so ShellCheck follows the `# shellcheck source=` directives and analyzes every module together:

```bash
shellcheck -x statusline.sh   # clean (exit 0)
```

Linting a `lib/*.sh` file on its own reports SC2034 ("appears unused") false positives.
Variables are consumed by sibling modules that standalone analysis can't see. Always lint through `statusline.sh`.

---

## Cost Calculation

### Pricing (per million tokens)

| Model  | Input | Cache Write | Cache Read | Output |
| ------ | ----- | ----------- | ---------- | ------ |
| Opus   | $5.00 | $5.00       | $0.50      | $25.00 |
| Sonnet | $3.00 | $3.00       | $0.30      | $15.00 |
| Haiku  | $1.00 | $1.00       | $0.10      | $5.00  |

Cache read is 10% of the input rate (90% discount). Cache write is the same as input.

### Per-message cost formula

```
cost = (input_tokens / 1M × rate_in)
     + (cache_write_tokens / 1M × rate_in)
     + (cache_read_tokens / 1M × rate_cache_read)
     + (output_tokens / 1M × rate_out)
```

### How monthly cost is tracked

Cost is accumulated using a **delta-based, session-aware system**.
Multiple simultaneous sessions don't conflict and costs are never double-counted.

**Monthly files** (`sessions/<YYYY-MM>.dat`)

Each calendar month has one file. Each session owns one row, keyed by its **session id** (from the harness
JSON, falling back to `$PPID` if absent). Session ids are stable for the life of a session, whereas the OS
recycles `$PPID`s within a month — keying on the PPID would let two unrelated sessions collide on one row.
On every status line update the script:

1. Reads the session's own row from `sessions/YYYY-MM.dat`
2. Computes the delta (tokens added since the last update)
3. Multiplies the delta by the current model's rates
4. Writes the updated row back (other sessions' rows are preserved)
5. Sums all rows in the file to produce the monthly total

Token counts that drop between updates (due to auto-compaction or a new session starting) are clamped to zero.
Those tokens were already counted and won't be double-charged.

Row format (the first field is the session id, or a PPID for legacy rows):

```
<session_id>|model|last_input|last_cache_write|last_cache_read|last_output|cumulative_cost
```

Example:

```
3f2c…a91|claude-sonnet-4-6|5000|2000|15000|500|0.034512
b7e1…04d|claude-sonnet-4-6|8100|3400|22000|900|0.051203
```

**Legacy PPID rows**: a session already running when keying changed from PPID to session id has no
session-keyed row yet. On its next update the script finds the old `<PPID>|…` row in the current month,
carries its counts and cost forward into a session-keyed row, and drops the PPID row in the same write, so
nothing is double-counted.

**Cross-month sessions**: when a session's row isn't found in the current month's file, the script looks in
the most recent past monthly file (matching the session id only). It carries the token counts forward (for
correct delta computation) but resets the cost to zero for the new month.

**Concurrent writes**: multiple sessions writing to the same monthly file — and to `monthly.cache` — are
serialized via `flock`. Each session only rewrites its own row, so there is no data loss under concurrency.

Month boundaries use **Pacific Time** (`TZ=America/Los_Angeles`).

**Monthly cache** (`monthly.cache`)

Summing the monthly file on every update is fast but unnecessary. The script caches the result with a 60-second TTL:

```
2026-05|1748201234|13.162363
2026-06|1748291234|13.234521
```

Fields: `YYYY-MM|unix_timestamp|total_cost`

- If the current month's line is less than 60 seconds old, the cached value is used as-is.
- If stale, `sessions/YYYY-MM.dat` is summed and the cache is updated.
- Past months' lines are never rewritten — they represent final historical spend.

### Rebuilding monthly totals

The monthly total is derived from `sessions/YYYY-MM.dat`. To force a rebuild, delete the current month's
line from `monthly.cache` (or delete the file entirely). To inspect or manually sum:

```bash
awk -F'|' 'NF==7{sum += $7} END {printf "%.6f\n", sum}' sessions/2026-06.dat
```

For reconstruction from scratch (e.g. session files were lost), historical costs can be recomputed from
Claude Code's session JSONL files in `~/.claude/projects/`, where each assistant message records exact token
counts and model used. No helper script for this is bundled today.

---

## Modifying Thresholds

| Constant              | Location                               | Default     | Purpose                                             |
| --------------------- | -------------------------------------- | ----------- | --------------------------------------------------- |
| `AUTO_COMPACT_BUFFER` | `statusline.sh:36`                     | `33000`     | Tokens before the limit where auto-compact triggers |
| Color thresholds      | `pct_color()` in `lib/colors.sh:18-19` | 50 / 75     | Orange and red cutoffs (% used)                     |
| Model rates           | `load_pricing()` in `lib/pricing.sh`   | see Pricing | Per-million token prices                            |
