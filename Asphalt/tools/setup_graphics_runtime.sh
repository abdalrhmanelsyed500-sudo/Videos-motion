#!/usr/bin/env bash
# Reassemble and normalize the CI-staged Xvfb/Mesa runtime for local capture.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PART_DIR="$ROOT/tools/runtime"
OUT_DIR="$ROOT/.cache/graphics-runtime"
PKG="$OUT_DIR/package"
TARBALL="$OUT_DIR/godot-graphics-runtime.tar.gz"
mkdir -p "$OUT_DIR"

if [ ! -f "$PKG/env.sh" ]; then
  parts=("$PART_DIR"/godot-graphics-runtime.tar.gz.part*)
  if [ ! -f "${parts[0]}" ]; then
    echo "Graphics runtime parts are missing. Run the fetch-graphics-runtime workflow first." >&2
    exit 1
  fi
  cat "${parts[@]}" > "$TARBALL"
  if [ -f "$PART_DIR/godot-graphics-runtime.parts.sha256" ]; then
    # CI wrote absolute runner paths; rewrite them to local basenames.
    sed -E 's#  .*/#  #' "$PART_DIR/godot-graphics-runtime.parts.sha256" > "$OUT_DIR/parts.sha256"
    (cd "$PART_DIR" && sha256sum -c "$OUT_DIR/parts.sha256")
  fi
  tar -xzf "$TARBALL" -C "$OUT_DIR"
  chmod +x "$PKG/bin/Xvfb" "$PKG/env.sh"
fi

# Optional small XKB fix: xkbcomp binary + xkeyboard-config data.
if [ -f "$PART_DIR/xkb-fix.tar.gz" ] && [ ! -f "$PKG/bin/xkbcomp" ]; then
  tar -xzf "$PART_DIR/xkb-fix.tar.gz" -C "$OUT_DIR"
  if [ -f "$PKG/xkb-env.sh" ] && ! grep -q 'XKB_BIN_DIRECTORY' "$PKG/env.sh"; then
    cat "$PKG/xkb-env.sh" >> "$PKG/env.sh"
  fi
  chmod +x "$PKG/bin/xkbcomp" 2>/dev/null || true
fi

python3 "$ROOT/tools/create_soname_links.py" "$PKG"
echo "Graphics runtime ready: $PKG"
