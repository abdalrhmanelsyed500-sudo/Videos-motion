#!/usr/bin/env bash
# Full reproducible static + parse + headless gameplay test suite.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GODOT="${GODOT:-/home/user/Videos-motion/.cache/godot-runtime/Godot_v4.2.2-stable_linux.x86_64}"
PYTHON="${PYTHON:-python3}"
mkdir -p "$ROOT/logs" "$ROOT/tests/reports"
echo "[1/4] Static resource audit"
"$PYTHON" "$ROOT/tests/static_audit.py" | tee "$ROOT/logs/static_audit.log"
echo "[2/4] Godot import and global class refresh"
"$GODOT" --headless --path "$ROOT" --editor --quit > "$ROOT/logs/import.log" 2>&1 || true
if grep -qE 'SCRIPT ERROR|Parse Error|Compile Error' "$ROOT/logs/import.log"; then
  echo "Import/parse errors detected:" >&2
  grep -E 'SCRIPT ERROR|Parse Error|Compile Error' "$ROOT/logs/import.log" >&2
  exit 1
fi
echo "[3/4] GDScript parse check"
: > "$ROOT/logs/parse.log"
for f in $(find "$ROOT" -name '*.gd' | sort); do
  rel="res://${f#$ROOT/}"
  "$GODOT" --headless --path "$ROOT" --check-only --script "$rel" >> "$ROOT/logs/parse.log" 2>&1 || {
    echo "Parse failed for $rel" >&2; tail -40 "$ROOT/logs/parse.log" >&2; exit 1;
  }
done
echo "[4/4] Headless gameplay smoke test"
set +e
"$GODOT" --headless --disable-render-loop --path "$ROOT" --audio-driver Dummy \
  --script res://tests/headless_smoke.gd > "$ROOT/logs/smoke.log" 2>&1
code=$?
set -e
grep -E 'SMOKE_TESTS|SCRIPT ERROR|Parse Error|Compile Error' "$ROOT/logs/smoke.log" | tail -20 || true
if [ "$code" -ne 0 ]; then
  echo "Smoke test failed with exit code $code" >&2
  exit "$code"
fi
echo "All tests passed. Reports: $ROOT/tests/reports/"
