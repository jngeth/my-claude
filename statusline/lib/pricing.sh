# shellcheck shell=bash
# ── Pricing ───────────────────────────────────────────────────────────────────
# Per-model token rates (USD per million tokens).

# load_pricing <model_id>
#   Sets RATE_IN, RATE_OUT, RATE_CACHE_R, RATE_CACHE_W based on the model family.
#   Cache reads bill at 10% of the input rate (90% discount);
#   5-minute cache writes bill at 1.25x the input rate.
load_pricing() {
  local model_id=$1
  if echo "$model_id" | grep -qiE "fable|mythos"; then
    RATE_IN=10.00; RATE_OUT=50.00
  elif echo "$model_id" | grep -qi "opus"; then
    RATE_IN=5.00; RATE_OUT=25.00
  elif echo "$model_id" | grep -qi "haiku"; then
    RATE_IN=1.00; RATE_OUT=5.00
  else
    RATE_IN=3.00; RATE_OUT=15.00
  fi
  # Cache reads bill at 0.1x input; 5-minute cache writes at 1.25x input.
  RATE_CACHE_R=$(echo "$RATE_IN" | LC_ALL=C awk '{printf "%.4f", $1 * 0.1}')
  RATE_CACHE_W=$(echo "$RATE_IN" | LC_ALL=C awk '{printf "%.4f", $1 * 1.25}')
}
