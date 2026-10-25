#!/bin/bash
# Rebuilds the sandbox toolchain after a reset (happened 3x so far). /tmp and the venv are NOT persistent.
# Then: git fetch && git reset --hard origin/arena/7464ca7a-videos-motion
set -e
python3 -m venv /home/user/.venv
/home/user/.venv/bin/pip install -q numpy Pillow gdtoolkit brotli
cd /home/user/Videos-motion/pixel_pirates/tools/godot_node && npm install --no-audit --no-fund
cd /home/user/Videos-motion/pixel_pirates/tools/godot_browser && npm install --no-audit --no-fund
# chromium shared libs for the render harness:
cd /tmp && /home/user/.venv/bin/python - <<'PY'
import brotli, tarfile, os
src = "/home/user/Videos-motion/pixel_pirates/tools/godot_browser/node_modules/@sparticuz/chromium/bin/al2023.tar.br"
open('/tmp/al2023.tar', 'wb').write(brotli.decompress(open(src, 'rb').read()))
os.makedirs('/tmp/al', exist_ok=True)
with tarfile.open('/tmp/al2023.tar') as t:
    t.extractall('/tmp/al')
PY
echo "toolchain ready; render with: LD_LIBRARY_PATH=/tmp/al/lib:/tmp SHOT_DIR=<dir> VIEW_W=640 VIEW_H=360 \\"
echo "  node pixel_pirates/tools/godot_browser/render.mjs tuktuk_mayhem/game tuktuk_mayhem/tools/scenarios/mission_p1.mjs"
echo "suite with: bash tuktuk_mayhem/tools/run_suite.sh /tmp/tkm_suite.log"
