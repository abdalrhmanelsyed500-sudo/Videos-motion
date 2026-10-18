#!/usr/bin/env bash
# Runs the in-engine tests (Module A7). Linux/macOS/Git-Bash. Set GODOT_EXE or write the path into tools/godot_path.txt
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
GAME="$HERE/../game"
GODOT_EXE="${GODOT_EXE:-}"
[ -z "$GODOT_EXE" ] && [ -f "$HERE/godot_path.txt" ] && GODOT_EXE="$(head -n1 "$HERE/godot_path.txt" | tr -d '\r')"
[ -z "$GODOT_EXE" ] && { echo "Godot not found. Set GODOT_EXE or write its path into tools/godot_path.txt"; exit 2; }
mkdir -p "$HERE/../build"
OUT="$HERE/../build/godot_tests.txt"
echo "Importing project..."
"$GODOT_EXE" --headless --path "$GAME" --import >"$OUT" 2>&1
echo "Running tests..."
"$GODOT_EXE" --headless --path "$GAME" --script res://tests/run_all.gd >>"$OUT" 2>&1
cat "$OUT"
if grep -qE "SCRIPT ERROR|Parse Error" "$OUT"; then echo; echo "ENGINE ERRORS FOUND - see build/godot_tests.txt"; exit 1; fi
if grep -qE "TESTS: [0-9]+ checks, 0 failed" "$OUT"; then echo; echo "ALL TESTS PASSED"; exit 0; fi
echo; echo "TESTS FAILED OR DID NOT FINISH - see build/godot_tests.txt"; exit 1
