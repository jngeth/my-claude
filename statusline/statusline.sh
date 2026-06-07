#!/bin/bash
input=$(cat)

# All persistent data lives next to this script — self-contained directory
STATUSLINE_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB_DIR="$STATUSLINE_DIR/lib"
SESSION_DIR="$STATUSLINE_DIR/sessions"
MONTHLY_CACHE="$STATUSLINE_DIR/monthly.cache"
RATE_CACHE="$STATUSLINE_DIR/ratelimits.cache"

# ── Sourced modules ───────────────────────────────────────────────────────────
# shellcheck source=lib/colors.sh
source "$LIB_DIR/colors.sh"      # color constants + pct_color
# shellcheck source=lib/pricing.sh
source "$LIB_DIR/pricing.sh"     # load_pricing
# shellcheck source=lib/cost.sh
source "$LIB_DIR/cost.sh"        # track_cost
# shellcheck source=lib/ratelimits.sh
source "$LIB_DIR/ratelimits.sh"  # load_rate_limits
# shellcheck source=lib/render.sh
source "$LIB_DIR/render.sh"      # build_context_bar, rate_bar, rate_label

# ── Extract core fields (single jq pass) ─────────────────────────────────────
# One jq invocation instead of one per field — this runs on every refresh, so the
# saved process spawns add up. Values are newline-delimited in a fixed order; the
# brace group reads them in the current shell (no subshell) so they persist.
{
  read -r MODEL_ID
  read -r MODEL
  read -r EFFORT
  read -r SESSION_ID
  read -r TOK_IN
  read -r TOK_CACHE_W
  read -r TOK_CACHE_R
  read -r TOK_OUT
  read -r CTX_TOTAL
  read -r CTX_PCT_RAW
} < <(jq -r '
  .model.id // "",
  .model.display_name // "Unknown",
  .effort.level // "N/A",
  .session_id // "",
  .context_window.current_usage.input_tokens // 0,
  .context_window.current_usage.cache_creation_input_tokens // 0,
  .context_window.current_usage.cache_read_input_tokens // 0,
  .context_window.current_usage.output_tokens // 0,
  .context_window.context_window_size // 200000,
  (.context_window.used_percentage // 0)
' <<<"$input")
CTX_PCT=${CTX_PCT_RAW%%.*}   # floor to integer

# Auto-compact kicks in when within 33k tokens of the limit
AUTO_COMPACT_BUFFER=33000
AUTO_COMPACT_PCT=$(awk -v total="$CTX_TOTAL" -v buf="$AUTO_COMPACT_BUFFER" \
  'BEGIN { if (total <= 0) { print 0; exit } printf "%d", (total - buf) / total * 100 }')

# ── Compute ───────────────────────────────────────────────────────────────────
load_pricing "$MODEL_ID"      # → RATE_IN, RATE_OUT, RATE_CACHE_R
track_cost                    # → MONTHLY_TOTAL, COST
load_rate_limits "$input"     # → FIVE_H_USED/RESET, WEEK_USED/RESET
build_context_bar             # → CTX_COLOR, CTX_BAR, UNTIL_COMPACT

# ── Build rate limit line ─────────────────────────────────────────────────────
RATE_LINE=""
if [ -n "$FIVE_H_USED" ]; then
  BAR=$(rate_bar "$FIVE_H_USED")
  LBL=$(rate_label "$FIVE_H_USED" "$FIVE_H_RESET")
  RATE_LINE="⏱️ ${BAR} ${LBL}"
fi
if [ -n "$WEEK_USED" ]; then
  BAR=$(rate_bar "$WEEK_USED")
  LBL=$(rate_label "$WEEK_USED" "$WEEK_RESET")
  RATE_LINE="${RATE_LINE:+$RATE_LINE  }📅 ${BAR} ${LBL}"
fi

# ── Render ────────────────────────────────────────────────────────────────────

# Line 1 — Model · Effort · Context
# %s, not %b: color constants already hold real ESC bytes, and %s won't reinterpret
# backslash escapes that might appear in interpolated data (model/effort strings).
printf '%s\n' \
  "🤖 ${CYAN}${BOLD}${MODEL}${RESET}  🎯 effort:${MAGENTA}${EFFORT}${RESET}  💭 ${CTX_BAR} ${CTX_COLOR}${CTX_PCT}%${RESET} ${DIM}(${UNTIL_COMPACT}% until auto-compact)${RESET}"

# Line 2 — Rate limits · Cost
if [ -n "$RATE_LINE" ]; then
  printf '%s\n' "${RATE_LINE}  💸 ${YELLOW}\$${COST}${RESET}"
else
  printf '%s\n' "💸 ${YELLOW}\$${COST}${RESET}"
fi
