"""Syntax and type check for game/h2d/shaders/*.gdshader WITHOUT Godot (Module H2D-0).

Each shader is turned into plain GLSL (includes inlined, Godot hints and render_mode stripped, built-ins such as VERTEX or
ALBEDO declared as globals, vertex()/fragment() renamed) and run through glslangValidator. That catches typos, undeclared
names, wrong argument types and int/float mix-ups. It does NOT prove the shader works in Godot: Godot-only rules (render
modes, which built-ins exist in which stage, global-uniform registration) are not checked. Only a Godot run proves those.

  python tools/h2d/check_shaders.py        # exit 0 when all pass or when no validator is installed (prints SKIP)
Validator lookup: env GLSLANG, then PATH (glslangValidator), then ~/tools_cache/node_modules/glslang-validator-prebuilt-predownloaded.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHADERS = ROOT / "game/h2d/shaders"

PRELUDE = {
    "spatial": """
vec3 VERTEX; vec3 NORMAL; vec2 UV; vec3 ALBEDO; float ALPHA; vec4 INSTANCE_CUSTOM;
mat4 MODEL_MATRIX; mat4 VIEW_MATRIX; mat4 INV_VIEW_MATRIX; mat4 PROJECTION_MATRIX; mat4 MODELVIEW_MATRIX;
vec3 CAMERA_POSITION_WORLD; vec4 FRAGCOORD; int INSTANCE_ID; float TIME;
""",
    "canvas_item": """
vec2 UV; vec2 TEXTURE_PIXEL_SIZE; vec4 COLOR; uniform sampler2D TEXTURE; float TIME;
""",
}


def find_validator() -> str | None:
    cands = [os.environ.get("GLSLANG", ""), shutil.which("glslangValidator") or ""]
    cands.append(str(Path.home() / "tools_cache/node_modules/glslang-validator-prebuilt-predownloaded/bin/glslangValidator.linux"))
    cands.append("/home/user/tools_cache/node_modules/glslang-validator-prebuilt-predownloaded/bin/glslangValidator.linux")
    for c in cands:
        if c and Path(c).exists():
            if not os.access(c, os.X_OK):
                try:
                    os.chmod(c, 0o755)  # npm leaves the prebuilt binary non-executable in some sandboxes
                except OSError:
                    continue
            return c
    return None


def inline_includes(text: str) -> str:
    def repl(m: re.Match) -> str:
        p = ROOT / "game" / m.group(1).replace("res://", "")
        return p.read_text()
    return re.sub(r'#include\s+"([^"]+)"', repl, text)


def to_glsl(src: str) -> tuple[str, str]:
    src = inline_includes(src)
    kind = re.search(r"shader_type\s+(\w+)\s*;", src).group(1)
    src = re.sub(r"shader_type\s+\w+\s*;", "", src)
    src = re.sub(r"render_mode\s+[^;]+;", "", src)
    src = re.sub(r"//[^\n]*", "", src)
    src = src.replace("global uniform", "uniform")

    src = re.sub(r"uniform\s+\w+\s+\w+\s*(?::\s*[^=;]+)?(?:=\s*[^;]+)?;", _uniform_line, src)
    src = re.sub(r"\bvarying\s+", "", src)
    src = re.sub(r"\bvoid\s+vertex\s*\(\s*\)", "void vertex_fn()", src)
    src = re.sub(r"\bvoid\s+fragment\s*\(\s*\)", "void fragment_fn()", src)
    has_v = "vertex_fn" in src
    body = "#version 330\n" + PRELUDE[kind] + src + "\nout vec4 _o;\nvoid main() {" + ("vertex_fn();" if has_v else "") + "fragment_fn(); _o = vec4(0.0);}\n"
    return kind, body


def _uniform_line(m: re.Match) -> str:
    text = m.group(0)
    mm = re.match(r"uniform\s+(\w+)\s+(\w+)\s*(?::\s*[^=;]+)?(?:=\s*([^;]+))?;", text)
    typ, name, default = mm.group(1), mm.group(2), mm.group(3)
    if typ.startswith("sampler"):
        default = None
    return f"uniform {typ} {name}" + (f" = {default.strip()}" if default else "") + ";"


def main() -> int:
    exe = find_validator()
    if exe is None:
        print("SKIP: glslangValidator not found (set GLSLANG or npm install glslang-validator-prebuilt-predownloaded)")
        return 0
    bad = 0
    shaders = sorted(SHADERS.glob("*.gdshader"))
    for sh in shaders:
        kind, glsl = to_glsl(sh.read_text())
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / (sh.stem + ".frag")
            f.write_text(glsl)
            p = subprocess.run([exe, "-S", "frag", str(f)], capture_output=True, text=True)
            out = (p.stdout + p.stderr).strip()
        if p.returncode == 0:
            print(f"PASS  {sh.name} ({kind})")
        else:
            bad += 1
            print(f"FAIL  {sh.name} ({kind})")
            lines = glsl.split("\n")
            for ln in out.split("\n")[:12]:
                print("      " + ln)
                m = re.search(r":(\d+):", ln)
                if m and 0 < int(m.group(1)) <= len(lines):
                    print("        > " + lines[int(m.group(1)) - 1].strip())
    print(f"{len(shaders) - bad}/{len(shaders)} shaders pass the GLSL syntax check (not a Godot run)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
