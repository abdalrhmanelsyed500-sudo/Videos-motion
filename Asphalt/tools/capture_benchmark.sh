#!/usr/bin/env bash
# Capture actual Godot gameplay-camera screenshots with software rendering.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GODOT="${GODOT:-/home/user/Videos-motion/.cache/godot-runtime/Godot_v4.2.2-stable_linux.x86_64}"
CAPTURE_SCRIPT="${CAPTURE_SCRIPT:-res://tools/capture_benchmark.gd}"
GRAPHICS="$ROOT/.cache/graphics-runtime/package"
if [ -x "$ROOT/tools/setup_graphics_runtime.sh" ]; then
  "$ROOT/tools/setup_graphics_runtime.sh"
fi
if [ ! -f "$GRAPHICS/env.sh" ]; then
  echo "Missing portable Xvfb/Mesa runtime at $GRAPHICS" >&2
  exit 2
fi
# shellcheck disable=SC1091
source "$GRAPHICS/env.sh"
export DISPLAY=:99
mkdir -p "$ROOT/logs" "$ROOT/screenshots"
# This Xvfb build has compiled-in /usr/bin/xkbcomp and /usr/share/X11/xkb
# paths. On a normal desktop those already exist; in the sandbox, bridge them
# to the portable bundle when passwordless sudo is available.
if [ ! -e /usr/bin/xkbcomp ] && [ -x "$GRAPHICS/bin/xkbcomp" ] && command -v sudo >/dev/null 2>&1; then
  sudo -n ln -sfn "$GRAPHICS/bin/xkbcomp" /usr/bin/xkbcomp 2>/dev/null || true
  sudo -n ln -sfn "$GRAPHICS/share/X11/xkb" /usr/share/X11/xkb 2>/dev/null || true
fi
if [ -S /tmp/.X11-unix/X99 ]; then
  echo "Warning: X display :99 already has a socket; reusing it." >&2
  XVFB_PID=""
else
  Xvfb :99 -screen 0 1280x720x24 +extension GLX +render -noreset -ac +iglx \
    -xkbdir "$GRAPHICS/share/X11/xkb" > "$ROOT/logs/xvfb.log" 2>&1 &
  XVFB_PID=$!
  trap 'if [ -n "${XVFB_PID:-}" ]; then kill "$XVFB_PID" 2>/dev/null || true; fi' EXIT
  for i in $(seq 1 30); do
    [ -S /tmp/.X11-unix/X99 ] && break
    sleep 0.2
  done
fi
"$GODOT" --headless --path "$ROOT" --editor --quit > "$ROOT/logs/import.log" 2>&1 || true
set +e
"$GODOT" --path "$ROOT" \
  --display-driver x11 --rendering-method gl_compatibility --rendering-driver opengl3 \
  --audio-driver Dummy --disable-vsync --fixed-fps 30 \
  --script "$CAPTURE_SCRIPT" 2>&1 | tee "$ROOT/logs/capture.log"
code=${PIPESTATUS[0]}
set -e
echo "Capture exit code: $code"
exit "$code"
