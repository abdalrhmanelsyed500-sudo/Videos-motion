#!/usr/bin/env bash
# Test the isolated Hybrid 2.5D experiment without touching production tests.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GODOT="${GODOT:-/home/user/Videos-motion/.cache/godot-runtime/Godot_v4.2.2-stable_linux.x86_64}"
mkdir -p "$ROOT/logs" "$ROOT/tests/reports"
echo "[1/3] Parse hybrid GDScript"
"$GODOT" --headless --path "$ROOT" --editor --quit > "$ROOT/logs/hybrid_import.log" 2>&1 || true
if grep -qE 'SCRIPT ERROR|Parse Error|Compile Error' "$ROOT/logs/hybrid_import.log"; then
  echo "Hybrid import/parse errors:" >&2
  grep -E 'SCRIPT ERROR|Parse Error|Compile Error' "$ROOT/logs/hybrid_import.log" >&2
  exit 1
fi
echo "[2/3] Hybrid 2.5D headless gameplay smoke test"
set +e
"$GODOT" --headless --disable-render-loop --path "$ROOT" --audio-driver Dummy \
  --script res://tests/hybrid_2p5d_smoke.gd > "$ROOT/logs/hybrid_smoke.log" 2>&1
code=$?
set -e
grep -E 'HYBRID_SMOKE|SCRIPT ERROR|Parse Error|Compile Error' "$ROOT/logs/hybrid_smoke.log" | tail -20 || true
if [ "$code" -ne 0 ]; then
  echo "Hybrid smoke test failed with exit code $code" >&2
  exit "$code"
fi
echo "[3/3] Reports"
python3 - "$ROOT/tests/reports/hybrid_smoke.json" <<'PY'
import json, sys
r=json.load(open(sys.argv[1]))
print('Hybrid smoke:', r['passed'], r['total_checks'], 'checks,', r['failed_checks'], 'failures')
PY
