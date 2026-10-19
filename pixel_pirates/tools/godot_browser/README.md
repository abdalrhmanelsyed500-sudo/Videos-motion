# godot_browser: the game in a REAL renderer (software WebGL2), with real key events and screenshots

`render.mjs` serves the project to headless Chromium, starts the Godot 4.7.2 web template inside it (Compatibility renderer, OpenGL ES 3
through SwiftShader), sends DOM keyboard events and saves screenshots.

    cd tools/godot_browser && npm install
    # one-time (Linux): unpack the shared libs bundled with @sparticuz/chromium to /tmp/al:
    #   node -e "const z=require('zlib'),f=require('fs');f.writeFileSync('/tmp/al.tar',z.brotliDecompressSync(f.readFileSync('node_modules/@sparticuz/chromium/bin/al2023.tar.br')))" && mkdir -p /tmp/al && tar -xf /tmp/al.tar -C /tmp/al
    # (chromium itself is unpacked to /tmp/chromium by the package on first launch)
    LD_LIBRARY_PATH=/tmp/al/lib:/tmp AWS_EXECUTION_ENV=AWS_Lambda_nodejs20.x \
      VIEW_W=1366 VIEW_H=876 SHOT_DIR=shots node render.mjs ../../game scenarios/map_ashore.mjs

**What it proves:** the real scenes, scripts and GL drawing, real key events through the engine's web input layer (a `rawKey` helper
sends an Arabic-layout M: physical `KeyM`, character `ة`).
**What it does not prove:** the Windows build on the Intel HD 3000 (no ANGLE/D3D11, no GPU, ~8 fps, so nothing about speed), audio, the
editor's import step (files are served raw; PNGs go through the raw-image fallback; `sea_view_3d.gd` and `h2d0.gd` are patched IN MEMORY only:
the texture loader, and an F9 "step ashore at the pier" hook).
The project's own RegEx-based scripts (registry, schema, console) cannot compile in this template; the game does not need them to run.
