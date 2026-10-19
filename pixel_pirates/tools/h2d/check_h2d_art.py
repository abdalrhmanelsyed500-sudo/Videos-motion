"""Checks the baked art (ship sheets, Anvil Cay maps, vegetation and structure atlases). Fails on hard errors, only WARNS on readability.

  python tools/h2d/check_h2d_art.py            # run the checks
  python tools/h2d/check_h2d_art.py --sheet    # also write art_bible/h2d0/ship_adjacent_xor.png

Hard checks: sheet sizes, nothing touches a frame border, the pivot is inside the silhouette's box, colour counts within
the A3 palette limits (ships 40 colours, 6 ramps), every ship colour comes from palette.json, no #000000 / #ffffff.
Readability metric: silhouette IoU between neighbouring headings (22.5 deg apart). Too high (> 0.93) means the turn is
hard to read at that heading; too low (< 0.45) means a visible pop. These are WARNINGS: they quantify, not judge.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "game" / "h2d" / "art"
IOU_HIGH = 0.93
IOU_LOW = 0.45
errors: list[str] = []
warnings: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def load(name: str) -> np.ndarray:
    return np.array(Image.open(ART / name).convert("RGBA"))


def colours(a: np.ndarray, alpha_min: int = 128) -> set[str]:
    m = a[..., 3] >= alpha_min
    return {"#%02x%02x%02x" % tuple(px) for px in a[m][:, :3]}


def palette() -> tuple[dict[str, str], dict]:
    doc = json.loads((ROOT / "game" / "data" / "look" / "palette.json").read_text())
    owner: dict[str, str] = {}
    for rid, ramp in doc["ramps"].items():
        for c in ramp:
            owner[c.lower()] = rid
    return owner, doc["limits"]


def check_ship(sheet: bool) -> None:
    meta = json.loads((ART / "ship_sloop.json").read_text())
    fw, fh = meta["frame_px"]
    n = meta["headings"]
    hull = load(meta["hull_sheet"])
    sails = load(meta["sail_sheet"])
    rows = len(meta["trims_deg"])
    if hull.shape[:2] != (fh, fw * n):
        fail(f"hull sheet size {hull.shape[:2]} != {(fh, fw * n)}")
        return
    if sails.shape[:2] != (fh * rows, fw * n):
        fail(f"sail sheet size {sails.shape[:2]} != {(fh * rows, fw * n)}")
        return
    owner, limits = palette()
    cols = colours(hull) | colours(sails)
    used = {owner[c] for c in cols if c in owner}
    outside = sorted(c for c in cols if c not in owner)
    if outside:
        fail(f"ship colours not in palette.json: {outside[:6]}")
    if len(cols) > limits["max_colours_per_sheet"]["ships"]:
        fail(f"ship colours {len(cols)} > limit {limits['max_colours_per_sheet']['ships']}")
    if len(used) > limits["max_ramps_per_asset"]["ships"]:
        fail(f"ship ramps {len(used)} > limit {limits['max_ramps_per_asset']['ships']}")
    for bad in limits["forbidden"]:
        if bad in cols:
            fail(f"forbidden colour {bad} in ship art")
    px, py = meta["pivot_px"]
    sil: list[np.ndarray] = []
    for k in range(n):
        h = hull[:, k * fw:(k + 1) * fw]
        for r in range(rows):
            s = sails[r * fh:(r + 1) * fh, k * fw:(k + 1) * fw]
            comp = np.where(s[..., 3:4] >= 128, s, h)
            a = comp[..., 3] >= 128
            if not a.any():
                fail(f"empty frame heading {k} trim {r}")
                continue
            if a[0].any() or a[-1].any() or a[:, 0].any() or a[:, -1].any():
                fail(f"frame touches its border: heading {k} trim {r}")
            ys, xs = np.nonzero(a)
            if not (xs.min() <= px <= xs.max() and ys.min() <= py <= ys.max()):
                fail(f"pivot outside the silhouette box: heading {k} trim {r}")
            if r == 2:
                sil.append(a)
    ious = []
    for k in range(n):
        a, b = sil[k], sil[(k + 1) % n]
        ious.append(float((a & b).sum()) / float((a | b).sum()))
    print("adjacent-heading silhouette IoU (trim 0 deg), heading k -> k+1:")
    for k, v in enumerate(ious):
        flag = ""
        if v > IOU_HIGH:
            flag = "  WEAK (hard to read the turn)"
            warnings.append(f"heading {k * 22.5:g}->{((k + 1) % n) * 22.5:g}: IoU {v:.2f} > {IOU_HIGH}")
        elif v < IOU_LOW:
            flag = "  POP"
            warnings.append(f"heading {k * 22.5:g}->{((k + 1) % n) * 22.5:g}: IoU {v:.2f} < {IOU_LOW}")
        print(f"  {k * 22.5:6.1f} -> {((k + 1) % n) * 22.5:6.1f}  {v:.3f}{flag}")
    print(f"  min {min(ious):.3f}  mean {sum(ious) / n:.3f}  max {max(ious):.3f}")
    print(f"ship: {len(cols)} colours, {len(used)} ramps ({', '.join(sorted(used))})")
    if sheet:
        out = np.zeros((fh, fw * n, 3), np.uint8)
        for k in range(n):
            a, b = sil[k], sil[(k + 1) % n]
            f = out[:, k * fw:(k + 1) * fw]
            f[a & b] = (150, 150, 150)
            f[a & ~b] = (230, 90, 60)
            f[~a & b] = (60, 150, 230)
        dst = ROOT / "art_bible" / "h2d0" / "ship_adjacent_xor.png"
        Image.fromarray(out).resize((fw * n * 2, fh * 2), Image.NEAREST).save(dst)
        print("wrote", dst)


def check_atlas(name: str, cw: int, ch: int, cap: int, owner: dict[str, str], label: str,
                top_ok: bool | set = False) -> None:
    atlas = load(name)
    tc = colours(atlas)
    out_t = sorted(c for c in tc if c not in owner)
    if out_t:
        fail(f"{label} colours not in palette.json: {out_t[:6]}")
    if len(tc) > cap:
        fail(f"{label} colours {len(tc)} > {cap}")
    if atlas.shape[1] % cw or atlas.shape[0] % ch:
        fail(f"{label} size is not a multiple of {cw} x {ch}")
    else:
        for r in range(atlas.shape[0] // ch):
            for c in range(atlas.shape[1] // cw):
                cell = atlas[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw, 3] >= 128
                if cell.any() and ((cell[0].any() and not (top_ok is True or (c, r) in (top_ok or ()))) or cell[-1].any() or cell[:, 0].any() or cell[:, -1].any()):
                    fail(f"{label} cell ({c},{r}) touches its border")
    print(f"{label}: {len(tc)} colours, atlas {atlas.shape[1]}x{atlas.shape[0]}")


def check_island() -> None:
    """H2D-1.2 Anvil Cay: the data maps, the 8 x 16 ground palette image and the three atlases."""
    owner, limits = palette()
    meta = json.loads((ART / "anvil_cay.json").read_text())
    n = int(meta["grid"]["cells"])
    for name in ("anvil_cay_height.png", "anvil_cay_biome.png"):
        if load(name).shape[:2] != (n, n):
            fail(f"{name} is not {n} x {n} like the json grid")
    pal = load("anvil_cay_palette.png")
    cols = colours(np.delete(pal, 5, axis=1))     # column 5 holds numbers (base, spread, pattern), not a colour
    outside = sorted(c for c in cols if c not in owner)
    if outside:
        fail(f"ground palette colours not in palette.json: {outside[:6]}")
    biome = load("anvil_cay_biome.png")
    classes = np.unique(biome[..., 0] // 16)
    if int(classes.max()) >= pal.shape[0]:
        fail("a biome class has no row in the ground palette image")
    print(f"island: grid {n} x {n} at {meta['grid']['cell_m']} m, ground palette {len(cols)} colours, {len(classes)} biome classes, "
          f"extent {meta['extent']}")
    props = limits["max_colours_per_sheet"]["props"]
    check_atlas("anvil_veg_atlas.png", 48, 56, props, owner, "vegetation atlas")
    check_atlas("anvil_struct_atlas.png", 80, 72, props, owner, "structure atlas",
                top_ok={(2, 3)})   # the lighthouse finial is a one-pixel spike on row 0
    check_atlas("anvil_hero_atlas.png", 24, 32, props, owner, "hero atlas", top_ok=True)   # the 30 px pirate has a closed outline on row 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", action="store_true")
    a = ap.parse_args()
    check_ship(a.sheet)
    check_island()
    for w in warnings:
        print("WARN", w)
    for e in errors:
        print("FAIL", e)
    print("PASS" if not errors else f"{len(errors)} ERROR(S)", f"({len(warnings)} readability warning(s))")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
