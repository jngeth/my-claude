# shellcheck shell=bash
# ── Rate limits ───────────────────────────────────────────────────────────────
# Prefer fresh values from the harness input; fall back to the on-disk cache so
# the display is never blank at session open (rate limits arrive after msg 1).
#
# Requires globals: RATE_CACHE
# Sets globals: FIVE_H_USED, FIVE_H_RESET, WEEK_USED, WEEK_RESET

# load_rate_limits <input_json>
load_rate_limits() {
  local input=$1
  # One jq pass instead of four. Missing fields emit "" (not absent) so the four
  # values stay positionally aligned for the fixed-order reads below.
  local FRESH_5H_USED FRESH_5H_RESET FRESH_WK_USED FRESH_WK_RESET
  {
    read -r FRESH_5H_USED
    read -r FRESH_5H_RESET
    read -r FRESH_WK_USED
    read -r FRESH_WK_RESET
  } < <(jq -r '
    .rate_limits.five_hour.used_percentage // "",
    .rate_limits.five_hour.resets_at // "",
    .rate_limits.seven_day.used_percentage // "",
    .rate_limits.seven_day.resets_at // ""
  ' <<<"$input")

  # Last known values, so a half that's absent this turn keeps its prior value
  # instead of being wiped from the cache.
  local CACHED_5H_USED CACHED_5H_RESET CACHED_WK_USED CACHED_WK_RESET
  [ -f "$RATE_CACHE" ] && IFS='|' read -r CACHED_5H_USED CACHED_5H_RESET CACHED_WK_USED CACHED_WK_RESET < "$RATE_CACHE"

  # Fresh if EITHER window reported (not just five_hour); fill any empty half from
  # cache before persisting, so one present window can't erase the other.
  if [ -n "$FRESH_5H_USED" ] || [ -n "$FRESH_WK_USED" ]; then
    FIVE_H_USED=${FRESH_5H_USED:-$CACHED_5H_USED}; FIVE_H_RESET=${FRESH_5H_RESET:-$CACHED_5H_RESET}
    WEEK_USED=${FRESH_WK_USED:-$CACHED_WK_USED};   WEEK_RESET=${FRESH_WK_RESET:-$CACHED_WK_RESET}
    echo "${FIVE_H_USED}|${FIVE_H_RESET}|${WEEK_USED}|${WEEK_RESET}" > "$RATE_CACHE"
  elif [ -f "$RATE_CACHE" ]; then
    FIVE_H_USED=$CACHED_5H_USED; FIVE_H_RESET=$CACHED_5H_RESET
    WEEK_USED=$CACHED_WK_USED;   WEEK_RESET=$CACHED_WK_RESET
  fi
}
