"""GDScript LOGIC parity check (Module E1). Godot cannot run in the build sandbox, so this tool mechanically translates the
small GDScript subset used by game/core/ocean.gd and game/core/wildlife.gd into Python, runs the result against the golden
fixtures, and reports any difference.

WHAT THIS PROVES: the formulas, operator order, hash arithmetic and data access written in GDScript give the same numbers
as the Python reference.
WHAT THIS DOES NOT PROVE: that Godot accepts the code or that engine calls (DirAccess, FileAccess, sort_custom, String
methods) behave as assumed. Those are checked only by running tests/run_all.gd in Godot (docs/E1_WORLD_SPEC.md).

    python tools/data_tools/gd_logic_check.py
"""
from __future__ import annotations

import copy
import json
import math
import re
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ocean as PO  # noqa: E402

ROOT = HERE.parents[1]
GAME = ROOT / "game"

SHIM = {
    "floorf": lambda x: float(math.floor(x)), "minf": min, "maxf": max, "mini": min, "maxi": max, "absf": abs,
    "clampf": lambda x, lo, hi: lo if x < lo else hi if x > hi else x, "lerpf": lambda a, b, t: a + (b - a) * t,
    "fmod": math.fmod, "fposmod": lambda a, b: a - b * math.floor(a / b), "pow": math.pow, "exp": math.exp, "sin": math.sin,
    "cos": math.cos, "atan2": math.atan2, "sqrt": math.sqrt, "deg_to_rad": math.radians, "rad_to_deg": math.degrees,
    "PI": math.pi, "str": str, "float": float, "int": int, "range": range, "len": len,
}


def translate(src: str, skip_funcs: set[str]) -> str:
    lines = src.split("\n")
    # pass 1: collect function names
    static_names, inst_names = set(), set()
    for ln in lines:
        m = re.match(r"^(static )?func (\w+)\(", ln)
        if m:
            (static_names if m.group(1) else inst_names).add(m.group(2))
    members = [m.group(1) for m in (re.match(r"^var (\w+)", ln) for ln in lines) if m]
    out: list[str] = []
    skipping = False
    for ln in lines:
        if ln.startswith("extends") or ln.startswith("class_name"):
            continue
        m = re.match(r"^(static )?func (\w+)\((.*?)\)\s*(->\s*[\w\[\]]+)?\s*:\s*$", ln)
        if m:
            skipping = m.group(2) in skip_funcs
            if skipping:
                continue
            args = [re.sub(r":\s*[\w\[\]]+(\s*=\s*.*)?$", lambda mm: mm.group(1) or "", a.strip()) if ":" in a else a.strip() for a in m.group(3).split(",") if a.strip()]
            args = [re.sub(r"\s*=\s*", "=", a) for a in args]
            if not m.group(1):
                args = ["self"] + args
            if m.group(2) == "_init":
                out.append(f"def __init__({', '.join(args)}):")
            else:
                out.append(f"def {m.group(2)}({', '.join(args)}):")
            continue
        if skipping:
            if ln and not ln.startswith(("\t", " ", "#")):
                skipping = False
            else:
                continue
        if re.match(r"^const \w+ := preload", ln):
            continue
        ln = re.sub(r"^const (\w+) := ", r"\1 = ", ln)
        ln = re.sub(r"\bvar (\w+)(?::\s*[\w\[\]]+)?\s*:?=\s*", r"\1 = ", ln)
        ln = re.sub(r"\bvar (\w+)(?::\s*[\w\[\]]+)?\s*$", r"\1 = None", ln)
        ln = ln.replace("true", "True").replace("false", "False").replace("null", "None")
        ln = re.sub(r"\bPackedFloat64Array\(\)", "[]", ln)
        ln = re.sub(r"(\w+) is Array", r"isinstance(\1, list)", ln)
        ln = re.sub(r"\(window as Array\)", "window", ln)
        ln = re.sub(r"\b(\w+)\.has\(([^)]*)\)", r"(\2 in \1)", ln)
        ln = re.sub(r"(\b[\w\.]+)\.size\(\)", r"len(\1)", ln)
        ln = ln.replace(".is_empty()", " == {}")
        ln = re.sub(r"for (\w+) in (\w+):$", lambda mm: f"for {mm.group(1)} in range({mm.group(2)}):" if mm.group(2) in ("n",) else mm.group(0), ln)
        ln = re.sub(r"for (\w+) in len\((.+)\):", r"for \1 in range(len(\2)):", ln)
        ln = re.sub(r" as (Dictionary|Array|float|int|String)\b", "", ln)
        ln = re.sub(r"for (\w+) in (\d+):", r"for \1 in range(\2):", ln)
        ln = ln.replace(".append_array(", ".extend(")
        ln = re.sub(r"\bdoc\.get\(", "doc.get(", ln)
        for mname in members:
            ln = re.sub(rf"(?<![\w.\"]){mname}(?![\w\"])", f"self.{mname}", ln) if ("def " not in ln and ln[:1] in ("\t", " ")) else ln
        for nm in inst_names:
            if not ln.lstrip().startswith("def "):
                ln = re.sub(rf"(?<![\w.]){nm}\(", f"self.{nm}(", ln)
        out.append(ln)
    code = "\n".join(out)
    code = code.replace("self.self.", "self.")
    return code


def build_module(path: Path, name: str, skip: set[str], extra: dict) -> types.ModuleType:
    code = translate(path.read_text(), skip)
    # a few GDScript idioms handled explicitly
    code = re.sub(r"self\.bands = band_records\.duplicate\(\)\n\s*self\.bands\.sort_custom\(.*\)\n", "self.bands = sorted(band_records, key=lambda b: float(b['lat_deg']))\n", code)
    mod = types.ModuleType(name)
    mod.__members__ = [m.group(1) for m in (re.match(r"^var (\w+)", ln) for ln in path.read_text().split("\n")) if m]
    mod.__dict__.update(SHIM)
    mod.__dict__.update(extra)
    try:
        exec(compile(code, name + ".py", "exec"), mod.__dict__)
    except SyntaxError as e:
        sys.stderr.write(code + "\n")
        raise SystemExit(f"translation of {path.name} produced invalid Python: {e}")
    return mod


def load_modules() -> tuple[types.ModuleType, types.ModuleType]:
    oc_mod = build_module(GAME / "core" / "ocean.gd", "gd_ocean", {"load_default", "load_tuning", "tuning_value_unused"}, {})
    oc_mod.hex_rgb = PO.hex_rgb      # String.substr/hex_to_int are engine calls: not testable here
    oc_mod.Ocean = oc_mod            # static calls written as Ocean.hash01(...)
    wl_mod = build_module(GAME / "core" / "wildlife.gd", "gd_wildlife", {"load_species"}, {"Ocean": oc_mod})
    return oc_mod, wl_mod


def instance_of(mod: types.ModuleType, *init_args):
    """A translated GDScript class lives as module-level functions taking `self`; bind them onto a throwaway class."""
    cls = type("GdObj", (), {})
    for k, v in list(mod.__dict__.items()):
        if callable(v) and not k.startswith("__") and k not in SHIM and isinstance(v, types.FunctionType):
            setattr(cls, k, v)
    inst = cls.__new__(cls)
    for m in getattr(mod, "__members__", []):
        if m in mod.__dict__:
            setattr(inst, m, copy.deepcopy(mod.__dict__[m]))
    mod.__dict__["__init__"](inst, *init_args)
    return inst


def main() -> int:
    om, wm = load_modules()
    import design_checks as D
    import ocean_checks as C
    regions = PO.load_regions()
    bands = PO.load_bands()
    # the translated class is the module itself (methods are module-level functions taking self); build an instance shim
    inst = instance_of(om, D.load_tuning(), regions, bands)
    inst.tuning = lambda: inst._t
    fx = json.loads((GAME / "tests" / "fixtures" / "ocean_cases.json").read_text())
    fxw = json.loads((GAME / "tests" / "fixtures" / "wildlife_cases.json").read_text())
    fails: list[str] = []
    n = 0

    def near(a: float, b: float) -> bool:
        return abs(a - b) <= 1e-4 * max(1.0, abs(b))

    for c in fx["noise"]["hash"]:
        n += 1
        if not near(om.hash01(*c["a"]), c["v"]):
            fails.append(f"hash01{c['a']}")
    for c in fx["noise"]["vnoise"]:
        n += 1
        if not near(om.vnoise(*c["a"][:3], int(c["a"][3])), c["v"]):
            fails.append(f"vnoise{c['a']}")
    for c in fx["noise"]["fbm"]:
        n += 1
        if not near(om.fbm(*c["a"][:3], int(c["a"][3])), c["v"]):
            fails.append(f"fbm{c['a']}")
    for c in fx["light"]:
        n += 1
        g = inst.light_limits(*c["a"])
        if not (near(g[0], c["v"][0]) and near(g[1], c["v"][1])):
            fails.append(f"light{c['a']}")
    for c in fx["winds"]:
        n += 1
        g = inst.base_wind(c["a"][0])
        if not all(near(g[i], c["v"][i]) for i in range(3)):
            fails.append(f"wind{c['a']}")
    for c in fx["samples"]:
        n += 1
        s = inst.sample(c["x"], c["y"], c["t"])
        bad = [k for k, v in c["v"].items() if not near(s[k], v)]
        if s["region"] != c["region"] or bad or not all(near(a, b) for a, b in zip(s["weights"], c["w"])):
            fails.append(f"sample({c['x']:.0f},{c['y']:.0f},{c['t']:.2f}) {bad[:4]}")
    for c in fx["speeds"]:
        n += 1
        if not near(inst.speed_through_water_kmh(*c["a"]), c["v"]):
            fails.append(f"speed{c['a']}")
    for c in fx["bergs"]:
        n += 1
        g = inst.bergs_near(*c["a"])
        if len(g) != len(c["v"]) or not all(near(a[0], b[0]) and near(a[1], b[1]) and a[2] == b[2] for a, b in zip(g, c["v"])):
            fails.append(f"bergs{c['a']} {len(g)} vs {len(c['v'])}")
    for c in fx["looks"]:
        n += 1
        g = inst.look_at(*c["a"])
        for k, v in c["v"].items():
            ok = all(near(g[k][i], v[i]) for i in range(3)) if isinstance(v, list) else near(g[k], v)
            if not ok:
                fails.append(f"look{c['a']} {k}")
    ss_mod = build_module(GAME / "core" / "sea_state.gd", "gd_sea_state", set(), {})
    fxs = json.loads((GAME / "tests" / "fixtures" / "sea_cases.json").read_text())
    for c in fxs["cases"]:
        n += 1
        st = instance_of(ss_mod, inst)
        st.place(*c["start"])
        t = c["t0"]
        for gs in c["steps"]:
            st.advance(t, gs)
            t += gs / 86400.0
        e = c["expect"]
        if not (abs(st.x_km - e["x"]) < 1e-3 and abs(st.y_km - e["y"]) < 1e-3 and abs(st.distance_km - e["distance"]) < 1e-3 and abs(st.speed_kn() - e["speed_kn"]) < 1e-3):
            fails.append(f"voyage '{c['name']}': got ({st.x_km:.3f}, {st.y_km:.3f}, {st.distance_km:.3f}) want ({e['x']}, {e['y']}, {e['distance']})")
    species = C.load_species()
    for c in fxw["cases"]:
        n += 1
        got = wm.sighting(inst, species, c["x"], c["y"], c["t"])
        want = c["sighting"]
        if want is None:
            if got:
                fails.append(f"sighting({c['x']:.0f},{c['y']:.0f}) expected none")
        else:
            ok = bool(got) and got["species"] == want["species"] and got["count"] == want["count"] and got["slot"] == want["slot"] \
                and near(got["bearing_deg"], want["bearing_deg"]) and near(got["distance_km"], want["distance_km"])
            if not ok:
                fails.append(f"sighting({c['x']:.0f},{c['y']:.0f}) {got} vs {want}")
        tb = sorted(wm.table(inst, species, c["x"], c["y"], c["t"]), key=lambda r: -r[1])[: len(c["top"])]
        if not all(a[0] == b[0] and near(a[1], b[1]) for a, b in zip(tb, c["top"])):
            fails.append(f"table({c['x']:.0f},{c['y']:.0f})")
    print(f"gd_logic_check: {n} GDScript-logic cases replayed, {len(fails)} differences")
    for f in fails[:25]:
        print("DIFF", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
