# shellcheck shell=bash
# ── Pricing ───────────────────────────────────────────────────────────────────
# Per-model token rates (USD per million tokens).

# load_pricing <model_id>
#   Sets RATE_IN, RATE_OUT, RATE_CACHE_R based on the model family.
#   Cache reads are billed at 10% of the input rate (90% discount);
#   cache writes are billed at the input rate.
load_pricing() {
  local model_id=$1
  if echo "$model_id" | grep -qi "opus"; then
    RATE_IN=5.00; RATE_OUT=25.00
  elif echo "$model_id" | grep -qi "haiku"; then
    RATE_IN=1.00; RATE_OUT=5.00
  else
    RATE_IN=3.00; RATE_OUT=15.00
  fi
  RATE_CACHE_R=$(echo "$RATE_IN" | LC_ALL=C awk '{printf "%.4f", $1 * 0.1}')
}
