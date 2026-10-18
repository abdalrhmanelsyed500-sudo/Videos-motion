#!/usr/bin/env bash
# H2D-0 benchmark (Linux/macOS), about 80 s. GODOT=/path/to/godot ./tools/run_h2d0_bench.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HERE/../build"
"${GODOT:-godot}" --path "$HERE/../game" res://h2d/h2d0.tscn -- --bench 2>&1 | tee "$HERE/../build/h2d0_console.txt" | grep -E "H2D0|ERROR|SCRIPT"
exit "${PIPESTATUS[0]}"
