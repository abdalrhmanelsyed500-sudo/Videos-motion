"""Island workbench (Module A7): create a new island record, find a working seed, bake, check and preview it - in one command.

  python tools/island_kit/new_island.py --id isl_012 --name "Saltglass" --tier 2 --template tpl_mesa_cliffs --kit kit_arid \\
      --offers fresh_water,game --hook-kind beacon_tower --region reg_sunfall --x-km 410 --y-km -220 [--dry-run]

The seed search skips seeds that fail a bake rule AND seeds whose silhouette looks like an island already in the file
(Silhouette Quota), so every island created this way is distinct from the ones before it.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bake as B  # noqa: E402
import island_checks as IC  # noqa: E402
import sameness as S  # noqa: E402

DEFAULT_FILE = B.GAME_DATA / "islands" / "islands.json"
SCHEMA = json.loads((B.GAME_DATA / "schemas" / "island.schema.json").read_text())["record"]["props"]
OFFERS = set(SCHEMA["survival_offers"]["items"]["enum"])
HOOKS = set(SCHEMA["hook_kind"]["enum"])


class SpecError(Exception):
    pass


def validate_spec(spec: dict, ctx: dict, existing: list[dict]) -> None:
    if not re.fullmatch(r"isl_[0-9]{3}", spec["id"]):
        raise SpecError("id must look like isl_012")
    if any(r["id"] == spec["id"] for r in existing):
        raise SpecError(f"{spec['id']} already exists")
    if spec["tier"] not in (1, 2, 3):
        raise SpecError("tier must be 1, 2 or 3")
    tpl = ctx["templates"].get(spec["template"])
    if tpl is None:
        raise SpecError(f"unknown template {spec['template']}; known: {', '.join(sorted(ctx['templates']))}")
    if spec["tier"] not in tpl["tiers"]:
        raise SpecError(f"{spec['template']} is not allowed for tier {spec['tier']} (allowed {tpl['tiers']})")
    for k in spec["kits"]:
        if k not in ctx["kits"]:
            raise SpecError(f"unknown kit {k}; known: {', '.join(sorted(ctx['kits']))}")
    bad = [o for o in spec["offers"] if o not in OFFERS]
    if bad or not spec["offers"]:
        raise SpecError(f"offers must be a non-empty subset of {sorted(OFFERS)} (bad: {bad})")
    if spec["hook_kind"] not in HOOKS:
        raise SpecError(f"unknown hook kind; known: {sorted(HOOKS)}")
    t = ctx["tuning"]
    if sum(1 for r in existing if r.get("hook_kind") == spec["hook_kind"]) >= t["island.max_per_hook_kind"]:
        raise SpecError(f"hook kind '{spec['hook_kind']}' is already used {int(t['island.max_per_hook_kind'])} times (the quota); pick another")
    if sum(1 for r in existing if r.get("template") == spec["template"] and r["kits"][0] == spec["kits"][0]) >= t["island.max_per_template_kit"]:
        raise SpecError(f"template+kit {spec['template']}+{spec['kits'][0]} is already used {int(t['island.max_per_template_kit'])} times; vary one of them")
    if not 2 <= len(spec["name"]) <= 40:
        raise SpecError("name must be 2-40 characters")


def make_record(spec: dict, seed: int, ctx: dict) -> dict:
    rec = {"id": spec["id"], "name": spec["name"], "tier": spec["tier"], "biome": ctx["kits"][spec["kits"][0]]["biome"],
           "region": spec["region"], "position": {"x_km": spec["x_km"], "y_km": spec["y_km"]}, "survival_offers": spec["offers"],
           "landmark": False, "kits": spec["kits"], "template": spec["template"], "seed": str(seed), "hook_kind": spec["hook_kind"],
           "status": "planned", "provisional": True, "owner": "E3", "source": "new_island.py; position and name pending E3/F modules"}
    if spec.get("hook"):
        rec["hook"] = spec["hook"]
    return rec


def create(spec: dict, ctx: dict, existing: list[dict], existing_maps: dict[str, dict], tries: int = 400):
    """returns (record, map, info). Raises SpecError / RuntimeError."""
    validate_spec(spec, ctx, existing)
    start = spec.get("seed") or int(hashlib.sha256(spec["id"].encode()).hexdigest()[:12], 16)
    limit = ctx["tuning"]["island.sameness_max_iou"]
    others = [(r, existing_maps[r["id"]]) for r in existing if r["id"] in existing_maps]
    rejected = {"bake": 0, "checks": 0, "alike": 0}
    for i in range(tries):
        seed = int(start) + i
        rec = make_record(spec, seed, ctx)
        try:
            m = B.bake(rec, ctx)
        except B.BakeError:
            rejected["bake"] += 1
            continue
        if IC.check_map(m, rec, ctx):
            rejected["checks"] += 1
            continue
        sil = S.silhouette(m)
        worst = max(((S.iou(sil, S.silhouette(om)), o["id"]) for o, om in others), default=(0.0, ""))
        if worst[0] >= limit:
            rejected["alike"] += 1
            continue
        info = {"seed": seed, "tries": i + 1, "rejected": rejected, "closest": worst}
        return rec, m, info
    raise RuntimeError(f"no seed worked in {tries} tries (rejected {rejected}); relax the spec or change the template")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--id", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--tier", type=int, required=True)
    ap.add_argument("--template", required=True)
    ap.add_argument("--kit", action="append", required=True, help="repeat for several kits; the first gives the tiles")
    ap.add_argument("--offers", required=True, help="comma separated survival offers")
    ap.add_argument("--hook-kind", required=True)
    ap.add_argument("--hook", help="one sentence describing the hook (optional now, required by F)")
    ap.add_argument("--region", required=True)
    ap.add_argument("--x-km", type=float, required=True)
    ap.add_argument("--y-km", type=float, required=True)
    ap.add_argument("--seed", type=int, help="first seed to try (default: derived from the id)")
    ap.add_argument("--islands-file", default=str(DEFAULT_FILE))
    ap.add_argument("--maps-dir", help="default: <islands-file folder>/maps")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    ctx = B.load_context()
    path = Path(a.islands_file)
    mdir = Path(a.maps_dir) if a.maps_dir else path.parent / "maps"
    doc = json.loads(path.read_text()) if path.exists() else {"schema": 1, "kind": "island", "records": []}
    existing = doc["records"]
    maps = {r["id"]: IC.load_map(mdir / f"{r['id']}.map.json") for r in existing if (mdir / f"{r['id']}.map.json").exists()}
    spec = {"id": a.id, "name": a.name, "tier": a.tier, "template": a.template, "kits": a.kit, "offers": [o for o in a.offers.split(",") if o],
            "hook_kind": a.hook_kind, "hook": a.hook, "region": a.region, "x_km": a.x_km, "y_km": a.y_km, "seed": a.seed}
    try:
        rec, m, info = create(spec, ctx, existing, maps)
    except (SpecError, RuntimeError) as e:
        print(f"ERROR: {e}")
        return 2
    s = m["stats"]
    print(f"{rec['id']} '{rec['name']}': seed {info['seed']} after {info['tries']} tries (rejected {info['rejected']})")
    print(f"  grid {m['size'][0]}x{m['size'][0]} tiles, land {s['land_fraction'] * 100:.0f}%, {s['pois']} POIs, {s['landings']} landings, {s['props']} props")
    print(f"  explore time {s['explore_minutes']} min (tier budget {B.explore_budget(ctx, rec['tier']):.0f} min)")
    if info["closest"][1]:
        print(f"  closest silhouette: {info['closest'][1]} at {info['closest'][0]:.2f} (limit {ctx['tuning']['island.sameness_max_iou']})")
    if a.dry_run:
        print("  dry run: nothing written")
        return 0
    existing.append(rec)
    existing.sort(key=lambda r: r["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    B.write_map(m, mdir / f"{rec['id']}.map.json")
    try:
        import preview  # noqa: PLC0415
        out = B.ROOT / "build" / "island_previews"
        out.mkdir(parents=True, exist_ok=True)
        preview.render(m, 3).save(out / f"{rec['id']}.png")
        print(f"  preview: {out / (rec['id'] + '.png')}")
    except Exception as ex:  # noqa: BLE001
        print(f"  (no preview: {ex})")
    print(f"  wrote {path} and {mdir / (rec['id'] + '.map.json')}; now run: python tools/check_project.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
