#!/usr/bin/env bash
# Starts the E1 ocean slice (Linux/macOS dev machines). GODOT=/path/to/godot ./tools/run_slice.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
exec "${GODOT:-godot}" --path "$HERE/../game" res://ui/ocean_slice.tscn
