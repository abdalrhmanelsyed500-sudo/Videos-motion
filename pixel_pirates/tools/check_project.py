"""Project checker (Module A2). Enforces conventions + the three HARD CONTENT RULES automatically.

    python tools/check_project.py            # needs only Python 3.9+ (gdparse optional, used if installed)
Exit code 0 = clean, 1 = problems. Wired to the optional git pre-commit hook (tools/install_hooks.sh).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"
problems: list[str] = []
warnings: list[str] = []

DATA_KINDS = {"isl", "reg", "crew", "npc", "item", "rcp", "ship", "evt", "loc", "fac", "qst", "dlg", "clue", "mode", "kit", "tpl"}
ASSET_PREFIXES = {"spr", "til", "prp", "shp", "ico", "fx", "ui", "bg"}
RE_DATA = re.compile(r"^[a-z]+(_[a-z0-9]+)+$")
RE_ISLAND = re.compile(r"^isl_[0-9]{3}$")
RE_FILE = re.compile(r"^[a-z0-9_]+(\.[a-z0-9]+)+$")
FILE_ALLOW = {"project.godot", "README.md", ".gdlintrc", ".gdignore", "export_presets.cfg", ".gitkeep"}


def valid_data_id(i: str) -> bool:
    if not RE_DATA.match(i) or i.split("_")[0] not in DATA_KINDS:
        return False
    return bool(RE_ISLAND.match(i)) if i.startswith("isl_") else True


def valid_asset_id(i: str) -> bool:
    return bool(RE_DATA.match(i)) and i.split("_")[0] in ASSET_PREFIXES


def self_test() -> None:
    """mirror of game/tests/test_ids.gd so the regex logic is verified even without Godot."""
    cases = [("isl_001", 1), ("isl_1", 0), ("isl_sunken_bay", 0), ("item_hardtack", 1), ("crew_old_tomas", 1), ("mode_normal", 1),
             ("Item_Hardtack", 0), ("item-hardtack", 0), ("banana_split", 0), ("item", 0)]
    for s, want in cases:
        if valid_data_id(s) != bool(want):
            problems.append(f"self-test: valid_data_id({s!r}) != {bool(want)}")
    for s, want in (("spr_crew_mannequin_captain", 1), ("til_water_deep_a", 1), ("crew_x", 0)):
        if valid_asset_id(s) != bool(want):
            problems.append(f"self-test: valid_asset_id({s!r}) != {bool(want)}")


def check_names() -> None:
    for p in GAME.rglob("*"):
        if any(part in (".godot", ".import") for part in p.parts):
            continue
        if p.name in FILE_ALLOW or p.name.endswith(".import") or p.name.endswith(".uid"):
            continue
        if not RE_FILE.match(p.name) and not (p.is_dir() and re.match(r"^[a-z0-9_]+$", p.name)):
            problems.append(f"naming: {p.relative_to(ROOT)} (use lower_snake_case)")


FAIL_TERMS = ["god", "gods", "goddess", "church", "prayer", "pray", "prays", "bible", "quran", "koran", "allah", "jesus", "christ",
              "atheist", "atheism", "religion", "religious", "worship", "sex", "sexy", "sexual", "nude", "naked", "erotic", "brothel"]
WARN_TERMS = ["temple", "shrine", "priest", "holy", "sacred", "heaven", "angel", "demon", "devil"]


def allowed(rel: str, term: str) -> bool:
    f = ROOT / "tools" / "content_allow.txt"
    return f.exists() and f"{rel}:{term}" in f.read_text().split()


def walk_json(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk_json(v, f"{path}/{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk_json(v, f"{path}[{i}]")
    else:
        yield path, o


def check_data() -> None:
    for f in sorted((GAME / "data").rglob("*.json")):
        rel = str(f.relative_to(ROOT))
        try:
            d = json.loads(f.read_text())
        except Exception as ex:  # noqa: BLE001
            problems.append(f"json: {rel}: {ex}")
            continue
        for path, v in walk_json(d):
            if isinstance(v, str):
                words = set(re.findall(r"[a-z]+", v.lower()))
                if "look" not in rel and not path.split("/")[-1].startswith("_"):
                    for t in FAIL_TERMS:
                        if t in words and not allowed(rel, t):
                            problems.append(f"CONTENT RULE: {rel}{path} contains '{t}'")
                    for t in WARN_TERMS:
                        if t in words and not allowed(rel, t):
                            warnings.append(f"content review: {rel}{path} contains '{t}'")
            if re.search(r"^(/records\[\d+\])?/id$", path) and isinstance(v, str) and not valid_data_id(v):
                problems.append(f"id grammar: {rel}{path} = {v!r}")
        # crew records: HARD RULE 1 (no female characters in the crew)
        if "/crew/" in str(f).replace("\\", "/"):
            recs = d if isinstance(d, list) else d.get("records", d.get("crew", [d])) if isinstance(d, dict) else []
            for r in recs:
                if isinstance(r, dict) and str(r.get("gender", "male")).lower() not in ("male", "m"):
                    problems.append(f"CONTENT RULE 1: crew record {r.get('id')} in {rel} is not male")


def check_manifest() -> None:
    mf = GAME / "art" / "manifest" / "sprites.json"
    if not mf.exists():
        warnings.append("no art manifest yet")
        return
    assets = json.loads(mf.read_text())["assets"]
    listed = set()
    for aid, e in assets.items():
        if not valid_asset_id(aid):
            problems.append(f"asset id grammar: {aid}")
        p = GAME / "art" / "placeholder" / e["category"] / f"{aid}.png"
        listed.add(p.resolve())
        if not p.exists():
            problems.append(f"manifest lists missing file: {p.relative_to(ROOT)}")
    for p in (GAME / "art" / "placeholder").rglob("*.png"):
        if p.resolve() not in listed:
            problems.append(f"placeholder file not in manifest: {p.relative_to(ROOT)}")
    for p in (GAME / "art" / "final").rglob("*.png"):
        if p.stem not in assets:
            warnings.append(f"final art without manifest entry (add it): {p.relative_to(ROOT)}")


def check_data_model() -> None:
    """A5: schema + reference + world-rule validation of every data file, and Python/GDScript validator parity."""
    sys.path.insert(0, str(ROOT / "tools" / "data_tools"))
    import validate_data  # noqa: PLC0415
    import test_parity  # noqa: PLC0415
    probs, info, res = validate_data.run()
    problems.extend(f"data model: {p}" for p in probs)
    warnings.extend(f"data info: {i}" for i in info if i.startswith("world target"))
    if test_parity.run_all() != 0:
        problems.append("data model: validator parity fixtures failed (tools/data_tools/test_parity.py)")
    print("data model:", ", ".join(f"{k}={v}" for k, v in sorted(res["counts"].items())))


def check_island_kit() -> None:
    """A6: templates, baked maps (stale / hand-edited / rule violations) and the sameness catalog."""
    try:
        sys.path.insert(0, str(ROOT / "tools" / "island_kit"))
        import bake  # noqa: PLC0415
        import island_checks  # noqa: PLC0415
        import sameness  # noqa: PLC0415
        import shapes  # noqa: PLC0415
    except ImportError as ex:
        warnings.append(f"island kit checks skipped ({ex}); pip install numpy scipy pillow")
        return
    sys.path.insert(0, str(ROOT / "tools" / "data_tools"))
    import validate_data  # noqa: PLC0415
    ctx = bake.load_context()
    for t in ctx["templates"].values():
        for k in t["shape"].get("params", {}):
            if k not in shapes.allowed_params(t["shape"]["op"]):
                problems.append(f"island kit: template {t['id']} has unknown shape parameter '{k}'")
    schemas = validate_data.load_schemas(GAME / "data")
    _, _, res = validate_data.run()
    base = validate_data.make_lookup(res["tables"], schemas, set(json.loads((GAME / "art" / "manifest" / "sprites.json").read_text())["assets"]))
    sets = [("data", list(res["tables"].get("island", {}).values()), GAME / "data" / "islands" / "maps", False),
            ("fixtures", bake.read_island_file(GAME / "tests" / "fixtures" / "islands" / "islands.json"), GAME / "tests" / "fixtures" / "islands" / "maps", True)]
    for label, recs, mapdir, is_fixture in sets:
        ids = {r["id"] for r in recs}

        def look(kind, i, _ids=ids):
            return (kind == "region" and i == "reg_fixture") or (kind == "island" and i in _ids) or base(kind, i)
        entries = []
        for rec in recs:
            if is_fixture:
                for e in validate_data.M.validate(rec, schemas["island"]["record"], look):
                    problems.append(f"island kit: fixture {rec['id']} {e[0]}: {e[1]}")
            mp = mapdir / f"{rec['id']}.map.json"
            if not mp.exists():
                if is_fixture or rec.get("status") in ("built", "tested"):
                    problems.append(f"island kit: {rec['id']} has no baked map ({mp.name})")
                continue
            if "template" not in rec:
                problems.append(f"island kit: {rec['id']} has a map but no template")
                continue
            m = island_checks.load_map(mp)
            if island_checks.is_stale(m, rec, ctx):
                problems.append(f"island kit: {rec['id']} map is STALE (template/kit/seed changed): run tools/island_kit/bake.py")
            for p in island_checks.check_map(m, rec, ctx):
                problems.append(f"island kit: {rec['id']}: {p}")
            entries.append((rec, m))
        if len(entries) > 1:
            probs, warns, _ = sameness.check_catalog(entries, ctx)
            problems.extend(f"island kit ({label}): {p}" for p in probs)
            warnings.extend(f"island kit ({label}): {w}" for w in warns)
    print(f"island kit: {len(ctx['templates'])} templates, {len(ctx['kits'])} kits, {len(sets[1][1])} fixture islands checked")


def check_design() -> None:
    """Pillar invariants (B1) and the content-word lint (HARD CONTENT RULES)."""
    sys.path.insert(0, str(ROOT / "tools" / "data_tools"))
    import design_checks  # noqa: PLC0415

    problems.extend(design_checks.invariants(design_checks.load_tuning()))
    problems.extend(design_checks.scan_data())


def check_registry_doc() -> None:
    sys.path.insert(0, str(ROOT / "tools" / "data_tools"))
    import registry_doc  # noqa: PLC0415

    if not registry_doc.DOC.exists() or registry_doc.DOC.read_text() != registry_doc.build():
        problems.append("docs/ISLAND_REGISTRY.md is out of date: run python tools/data_tools/registry_doc.py")


def check_godot_static() -> None:
    """Godot cannot run in CI here, so catch what gdparse cannot: duplicate member names (var vs func) and dead res:// paths."""
    member = re.compile(r"^(?:static\s+)?(var|const|signal|func|enum)\s+([A-Za-z_][A-Za-z0-9_]*)")
    for f in sorted(GAME.rglob("*.gd")):
        seen: dict[str, str] = {}
        for ln, line in enumerate(f.read_text().splitlines(), 1):
            m = member.match(line)
            if not m:
                continue
            kind, name = m.groups()
            if name in seen and not (kind == "enum" and name == ""):
                problems.append(f"gdscript: {f.relative_to(ROOT)}:{ln} member '{name}' already defined as {seen[name]} (name collision)")
            seen[name] = kind
    for f in sorted(list(GAME.rglob("*.gd")) + list(GAME.rglob("*.tscn")) + [GAME / "project.godot"]):
        for ln, line in enumerate(f.read_text().splitlines(), 1):
            if line.lstrip().startswith(("#", "##")):
                continue
            for m in re.finditer(r"res://([^\"'\s)]+)", line):
                rel = m.group(1)
                if rel.endswith("/") or "*" in rel or "%" in rel:
                    continue
                if not (GAME / rel).exists():
                    problems.append(f"godot path: {f.relative_to(ROOT)}:{ln} res://{rel} does not exist")


def check_gdscript() -> None:
    exe = shutil.which("gdparse") or str(Path(sys.executable).parent / "gdparse")
    if not Path(exe).exists() and not shutil.which("gdparse"):
        warnings.append("gdparse not installed: GDScript syntax not checked (pip install gdtoolkit)")
        return
    for f in GAME.rglob("*.gd"):
        r = subprocess.run([exe, str(f)], capture_output=True, text=True)
        if r.returncode != 0:
            problems.append(f"gdscript syntax: {f.relative_to(ROOT)}: {r.stderr.strip().splitlines()[-1] if r.stderr else 'error'}")


def main() -> int:
    self_test()
    check_names()
    check_data()
    check_manifest()
    check_data_model()
    check_island_kit()
    check_design()
    check_registry_doc()
    check_godot_static()
    check_gdscript()
    for w in warnings:
        print("WARN ", w)
    for p in problems:
        print("FAIL ", p)
    print(f"check_project: {len(problems)} problems, {len(warnings)} warnings")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
