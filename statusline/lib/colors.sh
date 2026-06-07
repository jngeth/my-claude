# shellcheck shell=bash
# ── Colors ────────────────────────────────────────────────────────────────────
# ANSI color constants and the shared percentage→color helper used by every bar.
# Constants hold real ESC bytes ($'\033...') so callers print with `printf '%s'`
# rather than `printf '%b'` — the latter would also interpret backslash escapes
# inside interpolated data (e.g. a model name containing "\t").

GREEN=$'\033[32m'
YELLOW=$'\033[33m'
ORANGE=$'\033[38;5;214m'
RED=$'\033[31m'
CYAN=$'\033[36m'
MAGENTA=$'\033[35m'
DIM=$'\033[2m'
BOLD=$'\033[1m'
RESET=$'\033[0m'

# pct_color <percent> — green < 50, orange 50–74, red ≥ 75.
# Self-defends: strips a decimal tail and treats empty/non-numeric input as 0,
# so a float or missing value never aborts the integer comparison.
pct_color() {
  local pct=${1%.*}
  case ${pct:-0} in ''|*[!0-9]*) pct=0 ;; esac
  if   [ "$pct" -ge 75 ]; then echo "$RED"
  elif [ "$pct" -ge 50 ]; then echo "$ORANGE"
  else                         echo "$GREEN"
  fi
}
