#!/bin/bash
# IRON ATLAS headless suite through the shared wasm harness (Godot 4.7.2, no rendering).
# Usage: bash iron_atlas/tools/run_suite.sh [logfile]  -> prints "SUITE: n passed, m failed"
LOG=${1:-/tmp/iron_atlas_suite.log}
HERE="$(cd "$(dirname "$0")" && pwd)"
GAME="$HERE/../game"
RUN="$HERE/../../pixel_pirates/tools/godot_node/run.mjs"
: > "$LOG"
pass=0; fail=0
run() {
  local name=$1; shift
  local out
  out=$(GODOT_REGEX_SHIM=1 GODOT_RAW=1 GODOT_SECONDS=240 timeout 280 node "$RUN" "$GAME" "$@" 2>&1 | grep -v "^   at:")
  local line
  line=$(echo "$out" | grep -E "TESTS:|SELFPLAY" | tail -1 | cut -c1-200)
  if echo "$line" | grep -qE "PASS" && ! echo "$line" | grep -qE ": 0 checks"; then
    pass=$((pass+1))
  else
    fail=$((fail+1)); echo "$out" | grep -E "FAIL|SCRIPT ERROR" | head -8 | cut -c1-240 >> "$LOG"
  fi
  echo "$name: $line" >> "$LOG"
}
run test_logic --script res://tests/run_all.gd
run test_ui_flow --fixed-fps 60 --script res://tests/test_ui_flow.gd
run test_tactical --fixed-fps 60 --script res://tests/test_tactical.gd
run selfplay --fixed-fps 60 --script res://tests/selfplay.gd
echo "SUITE: $pass passed, $fail failed" | tee -a "$LOG"
