#!/usr/bin/env python3
"""H2D-1.2.2: reproduces the 'invisible pirate' bug as a frustum-culling model (NOT a Godot run).

Godot culls a MultiMeshInstance3D by its AABB. When `multimesh.custom_aabb` is set the engine returns it as is and never
adds the instance transforms (drivers/gles3/storage/mesh_storage.cpp `_multimesh_get_aabb`). The old hero code kept the
AABB at the origin and moved only the instance, so the pirate was drawn only while that origin box was on screen.
This model builds the camera exactly as sea_view_3d.gd::_update_camera does and tests the box against the 6 frustum planes.

Usage: check_hero_cull.py            -> prints the table, exits 1 if the fixed layout still culls the hero
"""
import math, sys
import numpy as np

FOV, PITCH, PXM, ART_H, ZOOM = 22.0, 48.0, 3.6, 360.0, 4.0
POINTS = {  # name: (x, z)   from docs / anvil_cay.json
    "landing (16,4)": (16, 4), "pier mid (16,21)": (16, 21), "plaza (16,-2)": (16, -2),
    "lookout (119,-577)": (119, -577), "pearl cove (483,-357)": (483, -357), "wreck beach (-443,-275)": (-443, -275),
    "20 m east of origin": (20, 0), "30 m south": (0, 30), "45 m east": (45, 0), "100 m north": (0, -100),
}

def frustum_planes(cam, target, aspect):
    f = (target - cam); f /= np.linalg.norm(f)
    r = np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    t = math.tan(math.radians(FOV) / 2.0)
    ht, wt = t, t * aspect
    near, far = 8.0, 1800.0
    # planes as (normal pointing inwards, point)
    def plane(a, b):
        n = np.cross(a, b); n /= np.linalg.norm(n); return n
    top = plane(r, f + u * ht);  top = top if np.dot(top, -u) > 0 else -top
    bot = plane(r, f - u * ht);  bot = bot if np.dot(bot, u) > 0 else -bot
    rig = plane(u, f + r * wt);  rig = rig if np.dot(rig, -r) > 0 else -rig
    lef = plane(u, f - r * wt);  lef = lef if np.dot(lef, r) > 0 else -lef
    return [(top, cam), (bot, cam), (rig, cam), (lef, cam), (f, cam + f * near), (-f, cam + f * far)]

def box_visible(planes, lo, hi):
    c = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    for n, p in planes:
        if np.all((c - p) @ n < 0):
            return False
    return True

def visible(hero, box_center, half, aspect=16 / 9):
    dist = ART_H / (2.0 * math.tan(math.radians(FOV) / 2.0) * PXM * ZOOM)
    p = math.radians(PITCH)
    target = np.array([hero[0], 0.0, hero[1] - 1.6])
    cam = target + np.array([0.0, dist * math.sin(p), dist * math.cos(p)])
    pl = frustum_planes(cam, target, aspect)
    lo = np.array(box_center) - half; hi = np.array(box_center) + half
    return box_visible(pl, lo, hi)

def source_guard():
    """Static rule: every MultiMesh with a custom_aabb must either hold fixed instances inside that box, or be moved as a node.
    The hero is the single moving sprite; its set_hero() must move the NODE and must not move the instance."""
    import re, pathlib
    src = (pathlib.Path(__file__).resolve().parents[2] / "game/h2d/cay_world.gd").read_text()
    m = re.search(r"func set_hero\(.*?(?=\n\n\n|\Z)", src, re.S)
    body = m.group(0) if m else ""
    ok = "_hero.position" in body and "set_instance_transform" not in body
    print("source guard (set_hero moves the node, not the instance):", "OK" if ok else "FAIL")
    return 0 if ok else 1


def main():
    bad = source_guard()
    print(f"{'hero position':26s} {'OLD box @origin':>16s} {'NEW box @hero':>14s}")
    for name, (x, z) in POINTS.items():
        old = visible((x, z), (0, 2, 0), np.array([4, 6, 4]))          # AABB(-4,-4,-4)+(8,12,8): centre (0,2,0), half (4,6,4)
        new = visible((x, z), (x, 2, z), np.array([4, 6, 4]))          # box follows the node
        print(f"{name:26s} {'visible' if old else 'CULLED':>16s} {'visible' if new else 'CULLED':>14s}")
        bad += 0 if new else 1
    for label, ang in (("east", 0.0), ("south", 90.0), ("north", 270.0), ("west", 180.0)):
        d = 0.0
        while d < 400 and visible((d * math.cos(math.radians(ang)), d * math.sin(math.radians(ang))), (0, 2, 0), np.array([4, 6, 4])):
            d += 0.5
        print(f"old box: first culled {label} of the origin at {d:.1f} m (16:9, zoom 4)")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
