#!/usr/bin/env bash
# Runs the actual Godot wasm engine. The harness can exit 0 on test failure,
# so a nonzero process exit, missing/zero PASS line, or any runtime error fails.
# Usage: bash iron_atlas/tools/run_suite.sh [/path/to/log]
set -u
LOG=${1:-/tmp/iron_atlas_suite.log}
HERE="$(cd "$(dirname "$0")" && pwd)"
GAME="$HERE/../game"
RUN="$HERE/../../pixel_pirates/tools/godot_node/run.mjs"
DEPS="$HERE/../../pixel_pirates/tools/godot_node/node_modules/@ringozz/godot-web-wasm32/package.json"
if [ ! -f "$DEPS" ]; then
  echo "Missing Godot wasm dependency. Run: cd pixel_pirates/tools/godot_node && npm ci" >&2
  exit 1
fi
: > "$LOG"
pass=0; fail=0
run() {
  local name=$1; shift
  local out rc line bad
  out=$(GODOT_REGEX_SHIM=1 GODOT_RAW=1 GODOT_SECONDS=120 timeout 150 node "$RUN" "$GAME" "$@" 2>&1)
  rc=$?
  line=$(printf '%s\n' "$out" | grep -E '^(TESTS:|SELFPLAY )' | tail -1 || true)
  bad=$(printf '%s\n' "$out" | grep -E 'SCRIPT ERROR|Parse Error|^ERROR:|JS EXCEPTION|time limit reached' | head -12 || true)
  if [ "$rc" -eq 0 ] && [ -z "$bad" ] && \
      printf '%s\n' "$line" | grep -qE '^(TESTS: PASS:|SELFPLAY PASS:) [1-9][0-9]* checks$'; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
    printf '%s\n' "$name: runtime exit $rc; $line" | tee -a "$LOG"
    if [ -n "$bad" ]; then printf '%s\n' "$bad" | tee -a "$LOG"; fi
    if [ -z "$line" ]; then printf '%s\n' "$out" | tail -20 | tee -a "$LOG"; fi
    return
  fi
  printf '%s\n' "$name: $line" | tee -a "$LOG"
}
run test_logic --script res://tests/run_all.gd
run test_ui_flow --fixed-fps 60 --script res://tests/test_ui_flow.gd
run test_tactical --fixed-fps 60 --script res://tests/test_tactical.gd
run selfplay --fixed-fps 60 --script res://tests/selfplay.gd
run stage2_logic --script res://tests/test_stage2.gd
run stage2_ui --fixed-fps 60 --script res://tests/test_stage2_ui.gd
run stage2_tactical --fixed-fps 60 --script res://tests/test_stage2_tactical.gd
run stage2_campaign --fixed-fps 60 --script res://tests/test_stage2_campaign.gd
run stage2_long --fixed-fps 60 --script res://tests/test_stage2_long.gd
printf 'SUITE: %d passed, %d failed\n' "$pass" "$fail" | tee -a "$LOG"
[ "$fail" -eq 0 ]
