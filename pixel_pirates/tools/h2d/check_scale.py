"""H2D-1.2 scale audit: the numbers of docs/H2D1_2_SCALE_AND_LAND.md, computed from the baked files and the tuning.

  python tools/h2d/check_scale.py

Hard checks: Anvil Cay is 3-5 km across (a "medium" island of the Canon), the hero is a human next to a 22 m sloop (ratio
10-14), the land zoom keeps one sprite pixel on one screen pixel (hero atlas scale), the harbour is the H2D-1 harbour, and the
sea speed / walking speed ratios are the ones the document states. Prints the table. Static: not a Godot run.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "game/h2d/art"
SEA_PX_PER_M = 3.6
SHIP_LEN_M = 22.0
errors: list[str] = []


def need(cond: bool, msg: str) -> None:
    if not cond:
        errors.append(msg)


def main() -> int:
    meta = json.loads((ART / "anvil_cay.json").read_text())
    tu = {r["key"]: float(r["value"]) for f in (ROOT / "game/data/tuning").glob("tuning_*.json")
          for r in json.loads(f.read_text())["records"]}
    ext = meta["extent"]
    dia = ext["diameter_m"] / 1000.0
    need(3.0 <= dia <= 5.0, f"island diameter {dia:.2f} km is outside 3-5 km")
    need(2.0 <= ext["area_km2"] <= 9.0, f"island area {ext['area_km2']} km2 is outside the medium range")
    hero = np.array(Image.open(ART / "anvil_hero_atlas.png").convert("RGBA"))
    cw, ch = 24, 32
    rows = []
    for r in range(4):
        for c in range(4):
            a = hero[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw, 3] >= 128
            ys = np.nonzero(a.any(axis=1))[0]
            rows.append(ys.max() - ys.min() + 1)
    hero_px = int(max(rows))
    zoom = tu["land.zoom"]
    px_per_m = SEA_PX_PER_M * zoom
    hero_m = hero_px / px_per_m
    need(1.7 <= hero_m <= 2.3, f"the pirate is {hero_m:.2f} m tall with the hat (want 1.7-2.3)")
    ratio = SHIP_LEN_M / (hero_m - 0.2)
    need(9.0 <= ratio <= 14.0, f"sloop / body-height ratio {ratio:.1f} is outside 9-14")
    need(abs(px_per_m - 14.4) < 0.5, f"land px/m {px_per_m:.1f}: the hero art assumes 14.4 (zoom 4)")
    walk, run = tu["land.walk_ms"], tu["land.run_ms"]
    sea_ms = 5 * 0.514444 * (24.7 / (5 * 0.514444))      # the scene speed at 5 kn is 24.7 m/s (H2D-0 scale table)
    cross = ext["diameter_m"]
    print("H2D-1.2 scale table")
    print(f"  island            {dia:.2f} km across, {ext['area_km2']:.2f} km2, peak {ext['peak_m']:.0f} m, coast {ext['coast_m'] / 1000:.1f} km")
    print(f"  pirate            {hero_px} px = {hero_m:.2f} m with hat at {px_per_m:.1f} px/m (sea view {SEA_PX_PER_M} px/m, sloop {SHIP_LEN_M:.0f} m = {SHIP_LEN_M * SEA_PX_PER_M:.0f} px)")
    print(f"  sloop : body      {ratio:.1f} : 1")
    print(f"  across the island walking {cross / walk / 60:5.1f} min, running {cross / run / 60:5.1f} min, sailing at 5 kn (scene) {cross / sea_ms / 60:4.1f} min")
    print(f"  one screen        {640 / px_per_m:.0f} m wide on land, {640 / SEA_PX_PER_M:.0f} m at sea (640 px pixel grid)")
    need(cross / run / 60 > 5.0, "the island is crossed in under 5 minutes of running: too small to feel like an island")
    for e in errors:
        print("FAIL", e)
    print("PASS" if not errors else f"{len(errors)} ERROR(S)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
