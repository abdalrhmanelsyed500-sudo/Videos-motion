"""H2D-1 geometry checks on the baked Anvil Cay (reads game/h2d/art/anvil_cay.json and anvil_cay_data.png only).

  python tools/h2d/check_harbor.py

Checks: the berth footprint and the approach lane are open water; the pier deck is solid at deck height and joins the beach;
the dock zone is water and contains the approach point; every vegetation / structure prop stands on the surface it should
(land, deck, or water for buoys); no tree stands on the pier or the lane; the ship can reach the approach point from the
start position through water only (breadth-first search with a conservative disc). Same rules the game uses for the
grounding test: the ship is aground where land height > 0.3 m under its hull footprint.
"""
from __future__ import annotations

import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "game/h2d/art"
START = (-100.0, 140.0)    # keep in step with START_POS in h2d0.gd
GROUND_LIMIT = 0.3
errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def main() -> int:
    meta = json.loads((ART / "anvil_cay.json").read_text())
    data = np.array(Image.open(ART / "anvil_cay_data.png").convert("RGBA"))
    size, px = float(meta["size_m"]), int(meta["px"])
    if data.shape[0] != px:
        fail("data map size differs from the json")
    hmin, hmax = float(meta["height_min_m"]), float(meta["height_max_m"])
    height = data[..., 0].astype(float) / 255.0 * (hmax - hmin) + hmin
    lay = meta["harbor_layout"]

    def h_at(x: float, z: float) -> float:
        i, j = int(np.floor(x / size * px + px * 0.5)), int(np.floor(z / size * px + px * 0.5))
        if i < 0 or j < 0 or i >= px or j >= px:
            return -99.0
        return float(height[j, i])

    def footprint_clear(x: float, z: float, heading_deg: float, half_len=11.0, half_beam=3.1) -> bool:
        import math
        a = math.radians(heading_deg)
        f = (math.sin(a), -math.cos(a))
        s = (-f[1], f[0])
        for ul in (-1.0, -0.5, 0.0, 0.5, 1.0):
            for ub in (-1.0, 0.0, 1.0):
                if h_at(x + f[0] * ul * half_len + s[0] * ub * half_beam, z + f[1] * ul * half_len + s[1] * ub * half_beam) > GROUND_LIMIT:
                    return False
        return True

    b, ap, zone, pier = lay["berth"], lay["approach"], lay["dock_zone"], lay["pier"]
    # berth and lane
    if not footprint_clear(b["x"], b["z"], b["heading_deg"]):
        fail("berth footprint touches land")
    z = ap["z"]
    while z >= b["z"]:
        if not footprint_clear(b["x"], z, 0.0):
            fail(f"approach lane blocked at z={z:.1f}")
            break
        z -= 1.0
    # depth under the berth (the ship needs at least ~1.5 m of water to look right)
    dmin = min(h_at(b["x"] + dx, b["z"] + dz) for dx in (-3, 0, 3) for dz in (-10, 0, 10))
    if dmin > -0.6:
        fail(f"berth water is too shallow ({dmin:.2f} m)")
    # pier
    xs = np.linspace(pier["x0"] + 0.3, pier["x1"] - 0.3, 5)
    zs = np.linspace(pier["z0"] + 0.5, pier["z1"] - 0.5, 30)
    deck = [h_at(x, z) for x in xs for z in zs]
    if min(deck) < pier["height_m"] - 0.15 or max(deck) > pier["height_m"] + 0.2:
        fail(f"pier deck heights {min(deck):.2f}..{max(deck):.2f} are not near {pier['height_m']}")
    if h_at(lay["landing"]["x"], lay["landing"]["z"]) < 0.5:
        fail("the landing point is not on solid ground")
    # the ship's side must clear the pier edge
    gap = b["x"] - lay["ship_half_beam_m"] - pier["x1"]
    if not 0.2 <= gap <= 2.0:
        fail(f"gap between hull and pier is {gap:.2f} m (want 0.2..2.0)")
    # dock zone
    sub = [h_at(x, z) for x in np.arange(zone["x0"], zone["x1"], 2.0) for z in np.arange(zone["z0"], zone["z1"], 2.0)]
    water_share = float(np.mean(np.array(sub) <= GROUND_LIMIT))
    if water_share < 0.9:
        fail(f"dock zone is only {water_share:.0%} water")
    if not (zone["x0"] <= ap["x"] <= zone["x1"] and zone["z0"] <= ap["z"] <= zone["z1"]):
        fail("the approach point is outside the dock zone")
    # props
    on_pier = lambda x, z: pier["x0"] - 0.2 <= x <= pier["x1"] + 0.2 and pier["z0"] - 0.2 <= z <= pier["z1"] + 0.2  # noqa: E731
    types = meta["veg_atlas"]["types"]
    bad = 0
    for t in meta["trees"]:
        hh = h_at(t["x_m"], t["z_m"])
        if hh < 0.05:
            bad += 1
        if on_pier(t["x_m"], t["z_m"]):
            fail(f"vegetation on the pier at {t['x_m']},{t['z_m']}")
        if abs(t["x_m"] - b["x"]) < 8 and b["z"] - 12 < t["z_m"] < ap["z"] and hh > -0.2 and types[t["type"]] not in ("reef_rock",):
            fail(f"prop in the berth lane at {t['x_m']},{t['z_m']}")
    if bad:
        fail(f"{bad} vegetation props stand in water")
    for s in meta["structures"]:
        hh = h_at(s["x_m"], s["z_m"])
        if s["name"].startswith("buoy"):
            if hh > 0.0:
                fail(f"buoy {s['name']} is on land")
        elif hh < 0.5:
            fail(f"structure {s['name']} is not on solid ground (h={hh:.2f})")
    for lp in meta["lamps"]:
        if h_at(lp["x_m"], lp["z_m"]) < 0.5:
            fail(f"lamp {lp['name']} is not on solid ground")
    # reachability: from the start to the approach point through water, with a conservative disc
    step, r = 2.0, 6.0
    x0, x1, z0, z1 = -160.0, 160.0, -160.0, 200.0
    nx, nz = int((x1 - x0) / step), int((z1 - z0) / step)
    rr = int(r / step)
    solid = np.zeros((nz, nx), bool)
    for j in range(nz):
        for i in range(nx):
            solid[j, i] = h_at(x0 + i * step, z0 + j * step) > GROUND_LIMIT
    pad = np.pad(solid, rr, constant_values=False)
    blocked = np.zeros_like(solid)
    for dj in range(-rr, rr + 1):
        for di in range(-rr, rr + 1):
            if di * di + dj * dj <= rr * rr:
                blocked |= pad[rr + dj:rr + dj + nz, rr + di:rr + di + nx]
    si, sj = int((START[0] - x0) / step), int((START[1] - z0) / step)
    gi, gj = int((ap["x"] - x0) / step), int((ap["z"] - z0) / step)
    if blocked[sj, si]:
        fail("the start position is blocked")
    seen = np.zeros_like(solid)
    seen[sj, si] = True
    q = deque([(si, sj)])
    while q:
        i, j = q.popleft()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, c = i + di, j + dj
            if 0 <= a < nx and 0 <= c < nz and not seen[c, a] and not blocked[c, a]:
                seen[c, a] = True
                q.append((a, c))
    if not seen[gj, gi]:
        fail("the approach point cannot be reached from the start through open water")
    print(f"harbor: berth ({b['x']}, {b['z']}) depth {dmin:.1f} m, lane ok, pier {len(deck)} samples, zone {water_share:.0%} water, "
          f"{len(meta['trees'])} vegetation props, {len(meta['structures'])} structures, {len(meta['lamps'])} lamps, "
          f"start reaches the approach: {bool(seen[gj, gi])}")
    for e in errors:
        print("FAIL", e)
    print("PASS" if not errors else f"{len(errors)} ERROR(S)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
