"""Generate ALL placeholder art + manifest + QA report (Module A4).

    /home/user/.venv/bin/python tools/placeholder/gen_placeholders.py

Outputs (all deterministic):
  game/art/placeholder/<category>/<asset_id>.png   category = characters | tiles | props | ships | icons
  game/art/manifest/sprites.json                   one entry per asset (sizes, pivots, frames, timings, status)
  art_bible/placeholder_contact_sheet.png          overview image
  docs/ART_STATUS.md                               which assets are still placeholders vs final
The user's PC needs NO Python: the generated PNGs are committed to git.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import characters as CH  # noqa: E402
import props as PR  # noqa: E402
from pxdraw import PALETTE_SET, ROOT, used_colours  # noqa: E402

GAME = ROOT / "game"
OUT = GAME / "art" / "placeholder"
MANIFEST = GAME / "art" / "manifest" / "sprites.json"
LIMITS = {"characters": 48, "tiles": 20, "props": 32, "ships": 40, "icons": 14}  # max distinct colours per sheet (QA)
ID_RE = __import__("re").compile(r"^(spr|til|prp|shp|ico|fx|ui|bg)(_[a-z0-9]+)+$")


def save(cat: str, aid: str, im: Image.Image) -> Path:
    assert ID_RE.match(aid), aid
    p = OUT / cat / f"{aid}.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    im.save(p, optimize=True)
    return p


def hstrip(frames: list[Image.Image]) -> Image.Image:
    w, h = frames[0].size
    s = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        s.paste(f, (i * w, 0))
    return s


def main() -> None:
    man: dict[str, dict] = {}
    previews: list[tuple[str, Image.Image]] = []

    for v in CH.VARIANTS:
        aid = f"spr_crew_mannequin_{v}" if v != "villager" else "spr_npc_mannequin_villager"
        sheet, meta = CH.make_sheet(v)
        save("characters", aid, sheet)
        man[aid] = {"kind": "character_sheet", "category": "characters", "cell": [CH.CELL_W, CH.CELL_H], "pivot": list(CH.PIVOT),
                    "px_per_m": 24, "dirs": CH.DIRS, "anims": meta, "layout": "rows=dirs (s,n,e,w); columns=frames of all anims in order"}
        previews.append((aid, sheet.crop((0, 0, CH.CELL_W * 4, CH.CELL_H))))

    tiles = {"til_sand_a": PR.tile_sand(), "til_grass_a": PR.tile_grass(), "til_dirt_a": PR.tile_dirt(),
             "til_cobble_a": PR.tile_cobble(), "til_deck_planks_a": PR.tile_planks(), "til_snow_a": PR.tile_snow()}
    for aid, im in tiles.items():
        save("tiles", aid, im)
        man[aid] = {"kind": "tile", "category": "tiles", "size": [48, 48], "px_per_m": 24, "frames": 1, "seamless": True}
        previews.append((aid, im))
    wf = PR.tile_water_frames()
    save("tiles", "til_water_deep_a", hstrip(wf))
    man["til_water_deep_a"] = {"kind": "tile", "category": "tiles", "size": [48, 48], "px_per_m": 24, "frames": 4, "ms": 220, "seamless": True, "layout": "columns=frames"}
    previews.append(("til_water_deep_a", hstrip(wf)))

    props = {"prp_barrel": (PR.prop_barrel(), False), "prp_crate": (PR.prop_crate(), False), "prp_chest_closed": (PR.prop_chest(), False),
             "prp_rock_a": (PR.prop_rock(), False), "prp_palm_a": (PR.prop_palm(), False), "prp_palm_b": (PR.prop_palm(1.8), False), "prp_hut_a": (PR.prop_hut(), False),
             "prp_lantern": (PR.prop_lantern(), True), "prp_cannon": (PR.prop_cannon(), False)}
    for aid, (cv, emis) in props.items():
        im = cv.to_image()
        save("props", aid, im)
        man[aid] = {"kind": "prop", "category": "props", "size": [cv.w, cv.h], "pivot": [cv.w // 2, cv.h - 2], "px_per_m": 24, "frames": 1, "emissive": emis}
        previews.append((aid, im))
    fire = [c.to_image() for c in PR.prop_campfire_frames()]
    save("props", "prp_campfire", hstrip(fire))
    man["prp_campfire"] = {"kind": "prop", "category": "props", "size": [28, 28], "pivot": [14, 26], "px_per_m": 24, "frames": 4, "ms": 110, "emissive": True, "layout": "columns=frames"}
    previews.append(("prp_campfire", hstrip(fire)))

    sh = PR.ship_sloop()
    save("ships", "shp_sloop_e", sh.to_image())
    man["shp_sloop_e"] = {"kind": "ship_billboard", "category": "ships", "size": [sh.w, sh.h], "pivot": [sh.w // 2, 150], "px_per_m": 12,
                          "note": "placeholder sea-scale billboard; the real ship is a 3D model (A3 decision)"}
    previews.append(("shp_sloop_e", sh.to_image()))

    specs = json.loads((Path(__file__).parent / "placeholder_specs.json").read_text())
    for aid, code, cat in specs["icons"]:
        im = PR.make_icon(code, cat)
        save("icons", aid, im)
        man[aid] = {"kind": "icon", "category": "icons", "size": [24, 24], "px_per_m": 0, "frames": 1, "group": cat}
        previews.append((aid, im))

    # ---- QA: palette lock + colour budget + size
    problems = []
    for aid, e in man.items():
        p = OUT / e["category"] / f"{aid}.png"
        im = Image.open(p).convert("RGBA")
        cols = used_colours(im)
        bad = [c for c in cols if c not in PALETTE_SET]
        if bad:
            problems.append(f"{aid}: {len(bad)} off-palette colours e.g. {bad[:2]}")
        if len(cols) > LIMITS[e["category"]]:
            problems.append(f"{aid}: {len(cols)} colours > budget {LIMITS[e['category']]}")
        if e["kind"] == "character_sheet":  # no frame may touch its cell border (clipping)
            import numpy as np
            a = np.asarray(im)[..., 3] > 0
            cw, ch = e["cell"]
            bad_cells = 0
            for r in range(a.shape[0] // ch):
                for c in range(a.shape[1] // cw):
                    cell = a[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw]
                    if cell[0].any() or cell[-1].any() or cell[:, 0].any() or cell[:, -1].any() or not cell.any():
                        bad_cells += 1
            if bad_cells:
                problems.append(f"{aid}: {bad_cells} frames touch the cell border or are empty")
        e["colours"] = len(cols)
        e["status"] = "placeholder"
    for e in man.values():
        pass
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps({"version": 1, "assets": man}, indent=1, sort_keys=True) + "\n")

    # ---- contact sheet
    pad = 6
    rows, x, y, rowh, W = [], pad, pad, 0, 1500
    canvas = Image.new("RGBA", (W, 900), (58, 66, 74, 255))
    for aid, im in previews:
        s = 2 if im.width <= 300 else 1
        im2 = im.resize((im.width * s, im.height * s), Image.NEAREST)
        if im2.width > W - 2 * pad:
            im2 = im2.crop((0, 0, W - 2 * pad, im2.height))
        if x + im2.width + pad > W:
            x, y, rowh = pad, y + rowh + pad, 0
        if y + im2.height > canvas.height:
            canvas = canvas.crop((0, 0, W, y + im2.height + 2 * pad))
        canvas.alpha_composite(im2, (x, y)) if y + im2.height <= canvas.height else None
        x += im2.width + pad
        rowh = max(rowh, im2.height)
    canvas = canvas.crop((0, 0, W, min(canvas.height, y + rowh + pad)))
    canvas.convert("RGB").save(ROOT / "art_bible" / "placeholder_contact_sheet.png")

    # ---- status doc
    final = {p.stem for p in (GAME / "art" / "final").rglob("*.png")}
    lines = ["# ART STATUS (generated by tools/placeholder/gen_placeholders.py)", "",
             f"{len(man)} assets, {len(final & set(man))} replaced by final art.", "", "| asset | category | size | colours | status |", "|---|---|---|---|---|"]
    for aid, e in sorted(man.items()):
        size = e.get("size") or e.get("cell")
        lines.append(f"| {aid} | {e['category']} | {size[0]}x{size[1]} | {e['colours']} | {'FINAL' if aid in final else 'placeholder'} |")
    (ROOT / "docs" / "ART_STATUS.md").write_text("\n".join(lines) + "\n")

    print(f"{len(man)} assets written; QA problems: {len(problems)}")
    for pr in problems:
        print("  ", pr)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
