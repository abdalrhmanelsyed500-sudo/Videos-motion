#!/usr/bin/env bash
# H2D-0 prototype (Linux/macOS). GODOT=/path/to/godot ./tools/run_h2d0.sh [--bench]
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HERE/../build"
if [ "${1:-}" = "--bench" ]; then
  "${GODOT:-godot}" --path "$HERE/../game" res://h2d/h2d0.tscn -- --bench 2>&1 | tee "$HERE/../build/h2d0_console.txt" | grep -E "H2D0|ERROR|SCRIPT"
else
  "${GODOT:-godot}" --path "$HERE/../game" res://h2d/h2d0.tscn 2>&1 | tee "$HERE/../build/h2d0_console.txt"
fi
exit "${PIPESTATUS[0]}"
