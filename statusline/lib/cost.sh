# shellcheck shell=bash
# ── Session-aware monthly cost tracking ───────────────────────────────────────
# Delta-based accounting so simultaneous sessions never conflict or double-count.
# Each month has one file (sessions/YYYY-MM.dat); each session owns one row keyed
# by its session id (falling back to PPID). Concurrent sessions serialize writes
# via flock; each only writes its own row.
#
# Requires globals: SESSION_DIR, MONTHLY_CACHE, MODEL_ID, SESSION_ID,
#   TOK_IN, TOK_CACHE_W, TOK_CACHE_R, TOK_OUT, RATE_IN, RATE_OUT, RATE_CACHE_R, RATE_CACHE_W
# Sets globals: MONTHLY_TOTAL (raw 6dp sum), COST (display "%.2f")
# All float-producing awk/printf calls force LC_ALL=C so the decimal separator is
# always "." regardless of the user's locale (a comma would corrupt the ledger).
track_cost() {
  # Without these path globals the atomic-write lines below would expand to a
  # bare ".tmp" / ".dat" in the cwd (e.g. `> "${MONTHLY_CACHE}.tmp"` → `> .tmp`).
  if [ -z "${SESSION_DIR:-}" ] || [ -z "${MONTHLY_CACHE:-}" ]; then
    echo "track_cost: SESSION_DIR and MONTHLY_CACHE must be set" >&2
    return 1
  fi

  local MONTH SESSION_FILE NOW
  MONTH=$(TZ=America/Los_Angeles date +%Y-%m)
  SESSION_FILE="$SESSION_DIR/${MONTH}.dat"
  NOW=$(date +%s)

  mkdir -p "$SESSION_DIR"

  # Rows are keyed by session id (stable), not PPID (the OS recycles PPIDs within
  # a month, so two unrelated sessions would otherwise collide on one row).
  local KEY
  KEY="${SESSION_ID:-$PPID}"

  # Read own row from the current month's file. If there's no session-keyed row
  # yet, fall back to a legacy PPID-keyed row in the same month (one-time
  # migration for sessions already running when this keying changed); that stale
  # row is dropped from the write below so its cost isn't counted twice.
  local OWN_ROW IS_CURRENT_MONTH MIGRATE_PPID
  OWN_ROW=$(grep "^${KEY}|" "$SESSION_FILE" 2>/dev/null || true)
  IS_CURRENT_MONTH=true
  MIGRATE_PPID=false
  if [ -z "$OWN_ROW" ] && [ "$KEY" != "$PPID" ]; then
    OWN_ROW=$(grep "^${PPID}|" "$SESSION_FILE" 2>/dev/null || true)
    [ -n "$OWN_ROW" ] && MIGRATE_PPID=true
  fi

  # Cross-month: carry token counts forward (for correct delta) from the most
  # recent past month. Match only the session key, never PPID, to avoid the reuse
  # collision the keying change fixes.
  if [ -z "$OWN_ROW" ]; then
    IS_CURRENT_MONTH=false
    while IFS= read -r past_file; do
      OWN_ROW=$(grep "^${KEY}|" "$past_file" 2>/dev/null || true)
      [ -n "$OWN_ROW" ] && break
    done < <(find "$SESSION_DIR" -name "????-??.dat" ! -name "${MONTH}.dat" | sort -r)
  fi

  local LAST_MODEL LAST_IN LAST_CW LAST_CR LAST_OUT PREV_COST
  LAST_MODEL=""; LAST_IN=0; LAST_CW=0; LAST_CR=0; LAST_OUT=0; PREV_COST=0
  if [ -n "$OWN_ROW" ]; then
    IFS='|' read -r _ LAST_MODEL LAST_IN LAST_CW LAST_CR LAST_OUT PREV_COST <<< "$OWN_ROW"
    # Row from a past month: keep token counts for correct delta, but start cost at 0
    [ "$IS_CURRENT_MONTH" = false ] && PREV_COST=0
  fi

  # Token delta — clamped to 0 on drops (compaction or model switch)
  local DELTA_IN DELTA_CW DELTA_CR DELTA_OUT
  if [ "$LAST_MODEL" = "$MODEL_ID" ]; then
    DELTA_IN=$(( TOK_IN      > LAST_IN  ? TOK_IN      - LAST_IN  : 0 ))
    DELTA_CW=$(( TOK_CACHE_W > LAST_CW  ? TOK_CACHE_W - LAST_CW  : 0 ))
    DELTA_CR=$(( TOK_CACHE_R > LAST_CR  ? TOK_CACHE_R - LAST_CR  : 0 ))
    DELTA_OUT=$(( TOK_OUT    > LAST_OUT ? TOK_OUT     - LAST_OUT : 0 ))
  else
    DELTA_IN=$TOK_IN; DELTA_CW=$TOK_CACHE_W; DELTA_CR=$TOK_CACHE_R; DELTA_OUT=$TOK_OUT
  fi

  local NEW_COST
  NEW_COST=$(LC_ALL=C awk \
    -v prev="$PREV_COST" \
    -v i="$DELTA_IN" -v cw="$DELTA_CW" -v cr="$DELTA_CR" -v o="$DELTA_OUT" \
    -v ri="$RATE_IN" -v ro="$RATE_OUT" -v rcr="$RATE_CACHE_R" -v rcw="$RATE_CACHE_W" '
    BEGIN {
      delta = (i/1000000)*ri + (cw/1000000)*rcw + (cr/1000000)*rcr + (o/1000000)*ro
      printf "%.6f", prev + delta
    }')

  # flock serializes concurrent sessions; each only rewrites its own row. When
  # migrating off a legacy PPID row, drop that row too so the cost isn't doubled.
  {
    flock 9
    {
      if [ "$MIGRATE_PPID" = true ]; then
        grep -v "^${PPID}|" "$SESSION_FILE" 2>/dev/null | grep -v "^${KEY}|" || true
      else
        grep -v "^${KEY}|" "$SESSION_FILE" 2>/dev/null || true
      fi
      printf '%s\n' "${KEY}|${MODEL_ID}|${TOK_IN}|${TOK_CACHE_W}|${TOK_CACHE_R}|${TOK_OUT}|${NEW_COST}"
    } > "${SESSION_FILE}.tmp" && mv "${SESSION_FILE}.tmp" "$SESSION_FILE"
  } 9>"${SESSION_FILE}.lock"

  # Monthly total: use cache if fresh (<60s), otherwise re-sum the monthly file
  local CACHE_STALE=true CACHE_LINE CACHE_TIME
  if [ -f "$MONTHLY_CACHE" ]; then
    CACHE_LINE=$(grep "^${MONTH}|" "$MONTHLY_CACHE")
    if [ -n "$CACHE_LINE" ]; then
      CACHE_TIME=$(echo "$CACHE_LINE" | cut -d'|' -f2)
      if [ $(( NOW - CACHE_TIME )) -lt 60 ]; then
        MONTHLY_TOTAL=$(echo "$CACHE_LINE" | cut -d'|' -f3)
        CACHE_STALE=false
      fi
    fi
  fi

  if [ "$CACHE_STALE" = true ]; then
    MONTHLY_TOTAL=$(LC_ALL=C awk -F'|' 'NF==7{sum += $7} END {printf "%.6f", sum+0}' "$SESSION_FILE" 2>/dev/null || echo "0.000000")
    # flock so concurrent sessions don't clobber each other's month line
    {
      flock 9
      {
        [ -f "$MONTHLY_CACHE" ] && grep -v "^${MONTH}|" "$MONTHLY_CACHE"
        printf '%s\n' "${MONTH}|${NOW}|${MONTHLY_TOTAL}"
      } > "${MONTHLY_CACHE}.tmp" && mv "${MONTHLY_CACHE}.tmp" "$MONTHLY_CACHE"
    } 9>"${MONTHLY_CACHE}.lock"
  fi

  # Format via awk, not the printf builtin: a `LC_ALL=C` prefix reliably forces a
  # dot decimal for an external command, but not for a shell builtin (which would
  # choke on a dot-formatted value in a comma-decimal locale).
  COST=$(LC_ALL=C awk -v total="$MONTHLY_TOTAL" 'BEGIN { printf "%.2f", total }')
}
