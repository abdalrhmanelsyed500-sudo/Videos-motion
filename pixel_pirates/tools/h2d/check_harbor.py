"""H2D-1 harbour geometry checks on the baked Anvil Cay (H2D-1.2 data: anvil_cay.json and anvil_cay_height.png).

  python tools/h2d/check_harbor.py

Checks: the berth footprint and the approach lane are open water; the pier deck is solid at deck height and joins the beach;
the dock zone is water and contains the approach point; every vegetation / structure prop stands on the surface it should
(land, or water for buoys); no tree stands on the pier or the lane; the ship can reach the approach point from the
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
    data = np.array(Image.open(ART / "anvil_cay_height.png").convert("RGBA"))
    g = meta["grid"]
    px, cell, gx0, gz0 = int(g["cells"]), float(g["cell_m"]), float(g["origin_x"]), float(g["origin_z"])
    if data.shape[0] != px or data.shape[1] != px:
        fail("height map size differs from the json")
    top = float(meta["height_enc"]["top"])
    lay = meta["harbor_layout"]
    pier = lay["pier"]

    def decode(b):
        v = b.astype(np.float32) / 255.0
        return np.where(v < 0.1, v / 0.1 * 8.0 - 8.0, ((v - 0.1) / 0.9) ** 2 * top)

    height = decode(data[..., 0])
    occ = decode(data[..., 1])

    def on_pier_xz(x: float, z: float) -> bool:
        hd = pier["head"]
        return ((pier["x0"] <= x <= pier["x1"] and pier["z0"] <= z <= pier["z1"])
                or (hd["x0"] <= x <= pier["x1"] and hd["z0"] <= z <= pier["z1"]))

    def raw_h(x: float, z: float) -> float:
        i, j = int(np.floor((x - gx0) / cell)), int(np.floor((z - gz0) / cell))
        if i < 0 or j < 0 or i >= px or j >= px:
            return -99.0
        return float(height[j, i])

    def h_at(x: float, z: float) -> float:
        """What the game's land_height_at returns: the pier counts as 1 m of land."""
        if on_pier_xz(x, z):
            return float(pier["height_m"])
        return raw_h(x, z)

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

    b, ap, zone = lay["berth"], lay["approach"], lay["dock_zone"]
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
    dmin = max(raw_h(b["x"] + dx, b["z"] + dz) for dx in (-3, 0, 3) for dz in (-10, 0, 10))
    if dmin > -0.6:
        fail(f"berth water is too shallow ({dmin:.2f} m)")
    # pier: the deck is stamped into the occluder channel only; the ground under it must stay below the water
    xs = np.linspace(pier["x0"] + 0.3, pier["x1"] - 0.3, 5)
    zs = np.linspace(pier["z0"] + 0.5, pier["z1"] - 0.5, 30)
    deck = []
    for x in xs:
        for z in zs:
            i, j = int(np.floor((x - gx0) / cell)), int(np.floor((z - gz0) / cell))
            deck.append(float(occ[j, i]))
            # the first 2 m cell of the pier (z0..z0+2) is the shore ramp the walker steps onto (r5: shore_ramp in city_layout.py); the
            # rest must be water
            if height[j, i] > 0.3 and z > pier["z0"] + 2.5:
                fail(f"ground under the pier at ({x:.1f}, {z:.1f}) rises to {height[j, i]:.2f} m")
    if min(deck) < pier["height_m"] - 0.15 or max(deck) > pier["height_m"] + 0.2:
        fail(f"pier occluder heights {min(deck):.2f}..{max(deck):.2f} are not near {pier['height_m']}")
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
    def on_pier(x: float, z: float) -> bool:
        return on_pier_xz(x, z) or on_pier_xz(x - 0.8, z) or on_pier_xz(x + 0.8, z) or on_pier_xz(x, z + 0.8)
    bad = 0
    for t in meta["props"]:
        hh = raw_h(t["x_m"], t["z_m"])
        if hh < 0.05:
            bad += 1
        if on_pier(t["x_m"], t["z_m"]):
            fail(f"prop on the pier at {t['x_m']},{t['z_m']}")
        if abs(t["x_m"] - b["x"]) < 8 and b["z"] - 12 < t["z_m"] < ap["z"]:
            fail(f"prop in the berth lane at {t['x_m']},{t['z_m']}")
    if bad:
        fail(f"{bad} stack props stand in water")
    for s in meta["structures"]:
        hh = raw_h(s["x_m"], s["z_m"] - 0.5 * s["d_m"])
        if s["name"].startswith("buoy"):
            if hh > 0.0:
                fail(f"buoy {s['name']} is on land")
        elif on_pier(s["x_m"], s["z_m"]):
            continue
        elif hh < 0.5:
            fail(f"structure {s['name']} is not on solid ground (h={hh:.2f})")
    for lp in meta["lamps"]:
        if not on_pier(lp["x_m"], lp["z_m"]) and raw_h(lp["x_m"], lp["z_m"]) < 0.5:
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
          f"{len(meta['props'])} stack props, {len(meta['structures'])} structures, {len(meta['lamps'])} lamps, "
          f"start reaches the approach: {bool(seen[gj, gi])}")
    for e in errors:
        print("FAIL", e)
    print("PASS" if not errors else f"{len(errors)} ERROR(S)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
