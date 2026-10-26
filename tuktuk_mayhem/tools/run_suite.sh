#!/bin/bash
# EGYPTIAN TUKTUK MAYHEM logic suite through the shared wasm harness
# (pixel_pirates/tools/godot_node/run.mjs = real Godot 4.7.2 engine, headless, no rendering).
# Pure-logic tests run via tests/run_one.gd; scene-based tests run as fixed-fps main-loop
# scripts (SceneTree.iterate() never flushes READY, so scene tests need the real loop).
# Usage: bash tuktuk_mayhem/tools/run_suite.sh [logfile]   -> prints "SUITE: n passed, m failed"
LOG=${1:-/tmp/tkm_suite.log}
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
  # PASS with a nonzero check count only: a suite that ran zero checks is a failure, not a pass.
  if echo "$line" | grep -qE "PASS" && ! echo "$line" | grep -qE ": 0 checks"; then
    pass=$((pass+1))
  else
    fail=$((fail+1)); echo "$out" | grep -E "FAIL|SCRIPT ERROR" | head -8 | cut -c1-240 >> "$LOG"
  fi
  echo "$name: $line" >> "$LOG"
}
run test_reward --script res://tests/run_one.gd -- test_reward
run test_mission --script res://tests/run_one.gd -- test_mission
run test_save --fixed-fps 60 --script res://tests/test_save.gd
run test_vehicle --fixed-fps 60 --script res://tests/test_vehicle.gd
run test_camera --fixed-fps 60 --script res://tests/test_camera.gd
run test_district --fixed-fps 60 --script res://tests/test_district.gd
run selfplay --fixed-fps 60 --script res://tests/selfplay.gd
echo "SUITE: $pass passed, $fail failed" | tee -a "$LOG"
