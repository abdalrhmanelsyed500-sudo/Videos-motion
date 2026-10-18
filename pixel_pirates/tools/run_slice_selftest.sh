#!/usr/bin/env bash
# Scripted self-test of the E1 slice (Linux/macOS). GODOT=/path/to/godot ./tools/run_slice_selftest.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HERE/../build"
"${GODOT:-godot}" --path "$HERE/../game" res://ui/ocean_slice.tscn -- --selftest 2>&1 | tee "$HERE/../build/slice_selftest_console.txt" | grep -E "SELFTEST|ERROR|SCRIPT"
exit "${PIPESTATUS[0]}"
