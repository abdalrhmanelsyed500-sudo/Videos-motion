#!/bin/bash
# Runs every game/tests/test_*.gd one at a time (a full run_all.gd dies in the WASM runtime), then the standalone scene scripts.
# RegEx polyfill on (the WASM template has no RegEx module). Usage: tools/godot_node/run_suite.sh [logfile]   (default /tmp/suite.log)
# Prints "SUITE: n passed, m failed". The WASM template is NOT the desktop engine: see docs/CP1_FIX_R6.md for what it proves.
LOG=${1:-/tmp/suite.log}
cd "$(dirname "$0")/../../game" || exit 2
: > "$LOG"
pass=0; fail=0
run() {  # name, godot args..., marker regex
  local name=$1; shift
  local out
  out=$(GODOT_REGEX_SHIM=1 GODOT_RAW=1 GODOT_SECONDS=240 timeout 280 node ../tools/godot_node/run.mjs . "$@" 2>&1 | grep -v "^   at:")
  local line
  line=$(echo "$out" | grep -E "TESTS:|SELFPLAY|MAPSCREEN|MAPFLOW|MAPSANDBOX|AUDIT6|LOADALL|load_all" | tail -1 | cut -c1-200)
  if echo "$line" | grep -qE "PASS|LOADALL: [0-9]+ scripts, 0 failed"; then pass=$((pass+1)); else fail=$((fail+1)); echo "$out" | grep -E "FAIL|SCRIPT ERROR" | head -6 | cut -c1-240 >> "$LOG"; fi
  echo "$name: $line" >> "$LOG"
}
for f in tests/test_*.gd; do
  n=$(basename "$f" .gd)
  run "$n" --script res://tests/run_one.gd -- "$n"
done
run selfplay --fixed-fps 60 --script res://tests/selfplay.gd
run map_screen --fixed-fps 60 --script res://tests/map_screen_test.gd
run map_flow --fixed-fps 60 --script res://tests/map_flow.gd
run map_sandbox --fixed-fps 60 --script res://tests/map_sandbox_test.gd
run load_all --script res://tests/load_all.gd
run audit_r6 --fixed-fps 60 --script res://tests/audit_r6.gd
echo "SUITE: $pass passed, $fail failed" | tee -a "$LOG"
