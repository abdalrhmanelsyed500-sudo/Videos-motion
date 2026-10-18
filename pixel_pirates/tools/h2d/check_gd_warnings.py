"""Heuristic approximation of three Godot GDScript warnings, for the scripts under game/h2d (and anything given).

  python tools/h2d/check_gd_warnings.py [files...]

It is NOT the Godot analyser (nothing here can run Godot). It looks for the textual patterns that trigger:
  SHADOWED_VARIABLE            a local or parameter with the name of a member of the same script or of Node/RefCounted
  SHADOWED_GLOBAL_IDENTIFIER   a local/parameter named like a GDScript utility function or global constant
  UNUSED_VARIABLE / UNUSED_PARAMETER   a local or parameter never read in its function (leading underscore = deliberate)
  INTEGER_DIVISION             `/` whose operands look like ints (int literals, .size(), get_width(), int(...))
A clean result here is a necessary, not a sufficient, condition.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UTILITY = set("""abs absf absi acos asin atan atan2 bezier_derivative bezier_interpolate bytes_to_var bytes_to_var_with_objects
ceil ceilf ceili clamp clampf clampi cos cosh cubic_interpolate cubic_interpolate_angle deg_to_rad ease error_string exp
floor floorf floori fmod fposmod hash instance_from_id inverse_lerp is_equal_approx is_finite is_inf is_instance_id_valid
is_instance_valid is_nan is_same is_zero_approx lerp lerp_angle lerpf linear_to_db log max maxf maxi min minf mini
move_toward nearest_po2 pingpong posmod pow print print_rich print_verbose printerr printraw prints printt push_error
push_warning rad_to_deg rand_from_seed randf randf_range randfn randi randi_range randomize remap rid_allocate_id
rid_from_int64 round roundf roundi seed shuffle sign signf signi sin sinh smoothstep snapped snappedf snappedi sqrt step
str str_to_var tan tanh type_convert type_string typeof var_to_bytes var_to_bytes_with_objects var_to_str weakref wrap
wrapf wrapi load preload len range char ord assert""".split())
GLOBALS = set("PI TAU INF NAN Time OS Engine Input Image Color Basis Plane Rect2 Vector2 Vector3 Quaternion AABB RID Signal Callable".split())
NODE_MEMBERS = set("""name owner process_mode process_priority process_physics_priority process_thread_group
process_thread_group_order process_thread_messages physics_interpolation_mode auto_translate_mode editor_description
unique_name_in_owner scene_file_path multiplayer""".split())
DECL = re.compile(r"^(\s*)(var|const)\s+(\w+)")
FUNC = re.compile(r"^(static\s+)?func\s+(\w+)\s*\((.*?)\)")


def scan(path: Path) -> list[str]:
    lines = path.read_text().split("\n")
    out: list[str] = []
    members = {m.group(3) for ln in lines if (m := DECL.match(ln)) and not m.group(1)}
    members |= {m.group(2) for ln in lines if (m := FUNC.match(ln))}
    funcs: list[tuple[int, int, str, list[str]]] = []
    start = None
    for i, ln in enumerate(lines):
        m = FUNC.match(ln)
        if m:
            if start is not None:
                funcs[-1] = (funcs[-1][0], i, funcs[-1][2], funcs[-1][3])
            params = [p.strip().split(":")[0].split("=")[0].strip() for p in m.group(3).split(",") if p.strip()]
            funcs.append((i, len(lines), m.group(2), params))
            start = i
    for a, b, fname, params in funcs:
        body = "\n".join(lines[a + 1:b])
        code_only = "\n".join(re.sub(r"#.*", "", re.sub(r'"[^"\n]*"', '""', x)) for x in body.split("\n"))
        decls = [(a + 2 + j, m.group(3)) for j, ln in enumerate(lines[a + 1:b]) if (m := DECL.match(ln)) and m.group(1)]
        decls += [(a + 1, p) for p in params]
        for ln_no, name in decls:
            if name in members or name in NODE_MEMBERS:
                out.append(f"{path.name}:{ln_no}: SHADOWED_VARIABLE '{name}' in {fname}()")
            if name in UTILITY or name in GLOBALS:
                out.append(f"{path.name}:{ln_no}: SHADOWED_GLOBAL_IDENTIFIER '{name}' in {fname}()")
            if not name.startswith("_"):
                uses = len(re.findall(rf"\b{re.escape(name)}\b", code_only))
                is_param = (ln_no == a + 1)
                if uses <= (0 if is_param else 1):
                    out.append(f"{path.name}:{ln_no}: UNUSED_{'PARAMETER' if is_param else 'VARIABLE'} '{name}' in {fname}()")
    intish = re.compile(r"(?:\b\d+|\.size\(\)|get_width\(\)|get_height\(\)|\bint\([^()]*\)|\))\s*/\s*(?:\d+\b(?!\.)|\w+\.size\(\)|get_width\(\)|get_height\(\))")
    for i, ln in enumerate(lines):
        code = re.sub(r"#.*", "", re.sub(r'"[^"]*"', '""', ln))
        for m in intish.finditer(code):
            seg = m.group(0)
            if re.search(r"\d\.\d|\.\d|\d\.", seg):
                continue
            left = code[:m.start()].rstrip()
            if seg.startswith(")") and not re.search(r"(get_width|get_height|size|int)\(\)?$", left + ")"):
                if "float(" in code or "/ float" in code:
                    continue
            out.append(f"{path.name}:{i + 1}: INTEGER_DIVISION? {code.strip()[:90]}")
    return out


def main() -> int:
    files = [Path(a) for a in sys.argv[1:]] or sorted((ROOT / "game" / "h2d").glob("*.gd"))
    problems: list[str] = []
    for f in files:
        problems += scan(f)
    for p in problems:
        print(p)
    print(f"{len(problems)} possible warning(s) in {len(files)} file(s) (heuristic, not Godot)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
