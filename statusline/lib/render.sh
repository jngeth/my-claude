# shellcheck shell=bash
# ── Rendering ─────────────────────────────────────────────────────────────────
# Bar/label builders. Depends on colors.sh (color constants + pct_color).

# build_context_bar — 10-block context bar with an auto-compact buffer zone.
#   Requires globals: CTX_PCT, AUTO_COMPACT_PCT
#   Sets globals: CTX_COLOR, CTX_BAR, UNTIL_COMPACT
build_context_bar() {
  CTX_COLOR=$(pct_color "$CTX_PCT")
  local FILLED=$(( CTX_PCT / 10 ))
  [ "$FILLED" -gt 10 ] && FILLED=10   # never overflow the 10-block bar past 100%
  local AUTO_COMPACT_SECTIONS=$(( AUTO_COMPACT_PCT / 10 ))
  local NORMAL_FILL BUFFER_FILL ACTUAL_EMPTY F B E

  if [ "$FILLED" -le "$AUTO_COMPACT_SECTIONS" ]; then
    NORMAL_FILL="$FILLED"
    BUFFER_FILL=0
  else
    NORMAL_FILL="$AUTO_COMPACT_SECTIONS"
    BUFFER_FILL=$(( FILLED - AUTO_COMPACT_SECTIONS ))
  fi
  ACTUAL_EMPTY=$(( 10 - FILLED ))

  CTX_BAR=""
  [ "$NORMAL_FILL"  -gt 0 ] && printf -v F "%${NORMAL_FILL}s"  && CTX_BAR="${CTX_COLOR}${F// /█}${RESET}"
  [ "$BUFFER_FILL"  -gt 0 ] && printf -v B "%${BUFFER_FILL}s"  && CTX_BAR="${CTX_BAR}${YELLOW}${B// /█}${RESET}"
  [ "$ACTUAL_EMPTY" -gt 0 ] && printf -v E "%${ACTUAL_EMPTY}s" && CTX_BAR="${CTX_BAR}${DIM}${E// /░}${RESET}"

  UNTIL_COMPACT=$(( AUTO_COMPACT_PCT - CTX_PCT ))
  [ "$UNTIL_COMPACT" -lt 0 ] && UNTIL_COMPACT=0
}

# rate_bar <pct_used> — 10-block usage bar, colored by percent used.
rate_bar() {
  local pct_used=$1
  local pct_int="${pct_used%.*}"
  local color; color=$(pct_color "$pct_int")
  local filled=$(( pct_int / 10 ))
  [ "$filled" -gt 10 ] && filled=10   # never overflow the 10-block bar past 100%
  local empty=$(( 10 - filled ))
  local bar="" F E
  [ "$filled" -gt 0 ] && printf -v F "%${filled}s" && bar="${color}${F// /█}${RESET}"
  [ "$empty"  -gt 0 ] && printf -v E "%${empty}s"  && bar="${bar}${DIM}${E// /░}${RESET}"
  printf '%s' "$bar"
}

# rate_label <pct_used> <reset_epoch> — "NN% (Xd Xh / Xh Xm / Xm left)"
rate_label() {
  local pct_used=$1 reset_epoch=$2
  local pct_int="${pct_used%.*}"
  local color; color=$(pct_color "$pct_int")
  local time_str="?"
  if [ -n "$reset_epoch" ]; then
    local now secs_left
    now=$(date +%s)
    secs_left=$(( reset_epoch - now ))
    [ "$secs_left" -lt 0 ] && secs_left=0   # stale/expired reset → "0m", not negative
    if [ "$secs_left" -ge 86400 ]; then
      time_str="$(( secs_left / 86400 ))d $(( (secs_left % 86400) / 3600 ))h left"
    elif [ "$secs_left" -ge 3600 ]; then
      time_str="$(( secs_left / 3600 ))h $(( (secs_left % 3600) / 60 ))m left"
    else
      time_str="$(( secs_left / 60 ))m left"
    fi
  fi
  printf '%s' "${color}${pct_int}% ${RESET}${DIM}(${time_str})${RESET}"
}
