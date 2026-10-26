#!/usr/bin/env python3
"""EGYPTIAN TUKTUK MAYHEM - authored geometry generator (deterministic, seeded).
Writes Wavefront .obj (+.mtl) into game/assets/models/. Metres, +Y up, origin at ground contact.
These are REAL authored meshes (Phase-1 final bar per ART_BIBLE); regenerate = same bytes (fixed seed, no randomness
except seeded). Tri budgets: tuktuk <=1200, building shell <=200, person <=350.
"""
import math, os, random

OUT = os.path.join(os.path.dirname(__file__), "..", "game", "assets", "models")
os.makedirs(OUT, exist_ok=True)
R = random.Random(7)


class Mesh:
    def __init__(self):
        self.v, self.f, self.groups = [], [], []  # groups: (name, [face idx])

    def add_box(self, cx, cy, cz, sx, sy, sz, group="body", ry=0.0):
        """axis box, ry = yaw radians about own centre"""
        i0 = len(self.v)
        c, s = math.cos(ry), math.sin(ry)
        pts = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
        for px, py, pz in pts:
            x, z = px * sx / 2, pz * sz / 2
            xr, zr = x * c - z * s, x * s + z * c
            self.v.append((cx + xr, cy + py * sy / 2, cz + zr))
        faces = [(0, 1, 2, 3), (5, 4, 7, 6), (4, 0, 3, 7), (1, 5, 6, 2), (3, 2, 6, 7), (4, 5, 1, 0)]
        gi = len(self.groups)
        self.groups.append([group, []])
        for f in faces:
            self.f.append(tuple(i0 + k for k in f))
            self.groups[gi][1].append(len(self.f) - 1)

    def add_cyl(self, cx, cy, cz, r, h, seg, group="wheel", axis="y"):
        i0 = len(self.v)
        gi = len(self.groups)
        self.groups.append([group, []])
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            if axis == "y":
                ring.append((cx + r * math.cos(a), cy, cz + r * math.sin(a)))
            else:  # x axis (wheels roll about x)
                ring.append((cx, cy + r * math.cos(a), cz + r * math.sin(a)))
        for p in ring:
            self.v.append(p)
        for p in ring:
            self.v.append((p[0] + (h if axis == "x" else 0), p[1] + (h if axis == "y" else 0), p[2]))
        for k in range(seg):
            k2 = (k + 1) % seg
            self.f.append((i0 + k, i0 + k2, i0 + seg + k2, i0 + seg + k))
            self.groups[gi][1].append(len(self.f) - 1)
        self.f.append(tuple(i0 + k for k in range(seg)))
        self.groups[gi][1].append(len(self.f) - 1)
        self.f.append(tuple(i0 + seg + k for k in range(seg - 1, -1, -1)))
        self.groups[gi][1].append(len(self.f) - 1)

    def write(self, name, mtl_groups):
        """mtl_groups: {group: material name}. Writes .obj+.mtl (DCC source) AND a runtime mesh spec
        game/data/meshes/<name>.mesh.json (the wasm/desktop RUNTIME cannot import .obj without the editor,
        so gameplay builds ArrayMeshes from this spec via core/mesh_builder.gd - same numbers, deterministic)."""
        p = os.path.join(OUT, name + ".obj")
        with open(p, "w") as f:
            f.write("# EGYPTIAN TUKTUK MAYHEM authored mesh %s (tools/make_models.py)\n" % name)
            f.write("mtllib %s.mtl\n" % name)
            for v in self.v:
                f.write("v %.4f %.4f %.4f\n" % v)
            for g, (gname, fidx) in enumerate(self.groups):
                f.write("usemtl %s\n" % mtl_groups.get(gname, "M_default"))
                for i in fidx:
                    face = tuple(reversed(self.f[i]))
                    f.write("f " + " ".join("%d/%d" % (k + 1, k + 1) for k in face) + "\n")
        with open(os.path.join(OUT, name + ".mtl"), "w") as f:
            seen = set()
            for g in mtl_groups.values():
                if g in seen:
                    continue
                seen.add(g)
                f.write("newmtl %s\nKd 0.8 0.8 0.8\n" % g)
        self._write_spec(name, mtl_groups)
        return p

    def _write_spec(self, name, mtl_groups):
        import json
        spec = {"source": "tools/make_models.py", "groups": {}}
        for gname, fidx in self.groups:
            verts, norms, uvs, idx = [], [], [], []
            vmap = {}
            for i in fidx:
                face = self.f[i]
                # planar face: normal from first three corners
                a, b, c = (self.v[face[0]], self.v[face[1]], self.v[face[2]])
                ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
                wx, wy, wz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
                nx, ny, nz = uy * wz - uz * wy, uz * wx - ux * wz, ux * wy - uy * wx
                ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
                n = (round(nx / ln, 4), round(ny / ln, 4), round(nz / ln, 4))
                quad_uvs = [(0, 0), (1, 0), (1, 1), (0, 1)] if len(face) == 4 else [(0, 0), (1, 0), (0.5, 1)] + [(0, 0)] * (len(face) - 3)
                corners = []
                for k, vi in enumerate(face):
                    key = (vi, n, quad_uvs[k])
                    if key not in vmap:
                        vmap[key] = len(verts)
                        verts.append([round(x, 4) for x in self.v[vi]])
                        norms.append(list(n))
                        uvs.append(list(quad_uvs[k]))
                    corners.append(vmap[key])
                for k in range(1, len(corners) - 1):  # fan triangulation (quads and n-gon caps)
                    idx.extend([corners[0], corners[k], corners[k + 1]])
            spec["groups"][gname] = {"material": mtl_groups.get(gname, "M_default"), "verts": verts,
                                     "normals": norms, "uvs": uvs, "indices": idx}
        d = os.path.join(OUT, "..", "..", "data", "meshes")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, name + ".mesh.json"), "w") as f:
            json.dump(spec, f, separators=(",", ":"))


def tuktuk():
    m = Mesh()
    # floor pan + front cowl + cabin + canopy + fenders + bench + handlebar + mirrors
    m.add_box(0, 0.42, 0.15, 1.45, 0.16, 2.55, "trim")            # floor pan
    m.add_box(0, 0.78, -1.02, 1.05, 0.72, 0.85, "paint")          # front cowl
    m.add_box(0, 0.62, -1.42, 0.34, 0.5, 0.22, "trim")            # front fork shield
    m.add_box(0, 0.66, 0.62, 1.4, 0.55, 1.25, "paint")            # cabin sides/rear shell
    m.add_box(0, 0.98, 0.62, 1.28, 0.42, 1.1, "cabin")            # cabin void (dark interior)
    m.add_box(0, 1.62, 0.1, 1.5, 0.08, 2.2, "canopy")             # roof canopy
    for sx in (-0.72, 0.72):                                      # canopy posts
        m.add_box(sx, 1.25, -0.62, 0.06, 0.75, 0.06, "trim")
        m.add_box(sx, 1.25, 1.15, 0.06, 0.75, 0.06, "trim")
    m.add_box(0, 1.05, -0.75, 1.0, 0.42, 0.06, "glass")           # windshield
    m.add_box(0, 0.95, 0.95, 1.25, 0.35, 0.35, "seat")            # rear bench
    m.add_box(0, 1.02, -1.15, 0.5, 0.06, 0.3, "trim")             # handlebar
    m.add_box(0, 0.55, -1.52, 0.16, 0.22, 0.05, "lamp")           # headlamp block
    m.add_box(0, 0.85, 1.28, 1.3, 0.25, 0.06, "trim")             # rear panel + plate holder
    for sx in (-0.62, 0.62):                                      # rear fenders
        m.add_box(sx, 0.5, 0.95, 0.22, 0.3, 0.9, "paint")
    m.add_box(0, 0.5, -1.4, 0.2, 0.26, 0.7, "paint")              # front fender
    m.add_cyl(0, 0.3, -1.35, 0.3, 0.12, 12, "wheel", axis="x")    # front wheel
    m.add_cyl(-0.68, 0.3, 0.95, 0.3, 0.14, 12, "wheel", axis="x")
    m.add_cyl(0.54, 0.3, 0.95, 0.3, 0.14, 12, "wheel", axis="x")
    m.add_box(0, 1.78, 0.1, 0.7, 0.16, 0.28, "sign")              # roof sign plate
    return m.write("tuktuk", {"paint": "M_paint", "trim": "M_trim", "canopy": "M_canopy", "glass": "M_glass",
                              "cabin": "M_cabin", "seat": "M_seat", "wheel": "M_wheel", "lamp": "M_lamp",
                              "sign": "M_sign"})


def wheel_loose():
    m = Mesh()
    m.add_cyl(0, 0.3, 0, 0.3, 0.14, 12, "wheel", axis="x")
    return m.write("wheel", {"wheel": "M_wheel"})


def building_a():
    """sandstone apartment: shell + balcony slabs + cornice + roof hut (silhouette detail)."""
    m = Mesh()
    m.add_box(0, 6.0, 0, 9.0, 12.0, 11.0, "facade_a")
    m.add_box(0, 12.2, 0, 9.5, 0.5, 11.5, "trim_w")               # cornice
    for fy in (3.4, 6.6, 9.8):                                    # balcony slabs, street side (+z)
        m.add_box(0, fy, 5.75, 6.5, 0.22, 0.9, "trim_w")
        m.add_box(0, fy + 0.5, 6.12, 6.5, 0.8, 0.08, "rail")
    m.add_box(2.0, 13.3, -2.0, 2.6, 2.2, 2.6, "facade_a")         # roof stair hut
    m.add_box(-2.4, 12.9, 2.5, 1.4, 1.2, 1.4, "trim_w")           # water tank base
    m.add_cyl(-2.4, 13.8, 2.5, 0.8, 1.4, 8, "tank")
    return m.write("building_a", {"facade_a": "M_facade_a", "trim_w": "M_trim_w", "rail": "M_rail", "tank": "M_tank"})


def building_b():
    """shopfront row: low block + awning rail + signage band + rooftop pergola."""
    m = Mesh()
    m.add_box(0, 2.6, 0, 10.0, 5.2, 8.0, "facade_b")
    m.add_box(0, 3.4, 4.2, 9.4, 0.5, 0.9, "awning")
    m.add_box(0, 4.6, 4.05, 9.6, 1.1, 0.15, "sign")
    m.add_box(0, 5.45, 0, 10.4, 0.4, 8.4, "trim_w")
    for px in (-3.5, 0.0, 3.5):                                   # pergola posts
        m.add_box(px, 6.3, -2.0, 0.12, 1.4, 0.12, "trim_w")
    m.add_box(0, 7.05, -2.0, 8.0, 0.1, 2.2, "trim_w")
    return m.write("building_b", {"facade_b": "M_facade_b", "awning": "M_awning", "sign": "M_sign_b",
                                  "trim_w": "M_trim_w"})


def building_c():
    """rural brick house: small shell + flat roof parapet + palm-side porch slab."""
    m = Mesh()
    m.add_box(0, 1.9, 0, 6.0, 3.8, 5.5, "facade_c")
    m.add_box(0, 3.95, 0, 6.4, 0.35, 5.9, "trim_w")
    m.add_box(0, 1.5, 3.2, 4.0, 0.18, 1.2, "trim_w")
    m.add_box(-1.4, 0.8, 3.2, 0.14, 1.6, 0.14, "trim_w")
    m.add_box(1.4, 0.8, 3.2, 0.14, 1.6, 0.14, "trim_w")
    return m.write("building_c", {"facade_c": "M_facade_c", "trim_w": "M_trim_w"})


def person(hijab=False):
    """stylised low-poly person ~1.7 m; hijab variant replaces hair with headscarf + loose dress silhouette."""
    m = Mesh()
    m.add_box(0, 0.42, 0, 0.34, 0.84, 0.22, "legs")
    m.add_box(0, 1.12, 0, 0.42, 0.6, 0.26, "cloth")
    if hijab:
        m.add_box(0, 0.95, 0, 0.5, 0.95, 0.34, "cloth")          # long loose garment over hips
        m.add_box(0, 1.52, 0, 0.3, 0.34, 0.3, "hijab")           # headscarf (covers hair+neck)
        m.add_box(0, 1.32, 0.02, 0.34, 0.22, 0.34, "hijab")      # neck/drape wrap
        m.add_box(0, 1.55, 0.16, 0.2, 0.22, 0.06, "skin")        # face plane only
    else:
        m.add_box(0, 1.55, 0, 0.24, 0.28, 0.24, "skin")
        m.add_box(0, 1.7, -0.02, 0.25, 0.1, 0.25, "hair")
    for sx in (-0.26, 0.26):
        m.add_box(sx, 1.15, 0, 0.1, 0.55, 0.12, "cloth")
    m.add_box(-0.26, 0.86, 0, 0.1, 0.1, 0.12, "skin")
    m.add_box(0.26, 0.86, 0, 0.1, 0.1, 0.12, "skin")
    mats = {"legs": "M_legs", "cloth": "M_cloth", "skin": "M_skin", "hair": "M_hair", "hijab": "M_hijab"}
    return m.write("person_hijab" if hijab else "person", mats)


def ramp():
    """Jump ramp wedge: 4 m run, 2.6 m wide, 0.9 m rise (visual; launch is the district trigger)."""
    m = Mesh()
    gi = len(m.groups)
    m.groups.append(["ramp", []])
    verts = [(-1.3, 0.0, -2.0), (1.3, 0.0, -2.0), (1.3, 0.0, 2.0), (-1.3, 0.0, 2.0),
             (-1.3, 0.9, 1.6), (1.3, 0.9, 1.6)]
    m.v.extend(verts)
    faces = [(0, 1, 5, 4), (0, 4, 5, 1), (2, 3, 4, 5), (0, 2, 5), (3, 1, 0), (4, 3, 0), (5, 2, 1)]
    keep = [(0, 1, 5, 4), (2, 3, 4, 5), (0, 2, 5), (3, 1, 0)]
    for f in keep:
        m.f.append(f)
        m.groups[gi][1].append(len(m.f) - 1)
    return m.write("ramp", {"ramp": "M_ramp"})


def props():
    m = Mesh()  # crate stack
    m.add_box(0, 0.35, 0, 0.7, 0.7, 0.7, "crate")
    m.add_box(0.15, 1.0, 0.1, 0.55, 0.6, 0.55, "crate")
    m.write("crate_stack", {"crate": "M_crate"})
    m = Mesh()  # market stall: table + awning poles + striped top
    m.add_box(0, 0.45, 0, 1.8, 0.1, 1.0, "crate")
    for sx in (-0.85, 0.85):
        for sz in (-0.45, 0.45):
            m.add_box(sx, 0.9, sz, 0.06, 1.8, 0.06, "trim")
    m.add_box(0, 1.85, 0, 2.1, 0.08, 1.3, "awning")
    m.write("market_stall", {"crate": "M_crate", "trim": "M_trim", "awning": "M_awning"})
    m = Mesh()  # lamp post
    m.add_cyl(0, 2.5, 0, 0.07, 5.0, 8, "trim")
    m.add_box(0.35, 5.0, 0, 0.8, 0.1, 0.16, "trim")
    m.add_box(0.7, 4.9, 0, 0.3, 0.12, 0.2, "lamp")
    m.write("lamp_post", {"trim": "M_trim", "lamp": "M_lamp"})
    m = Mesh()  # speed bump (segment)
    m.add_box(0, 0.06, 0, 3.4, 0.12, 0.5, "bump")
    m.write("speed_bump", {"bump": "M_bump"})
    m = Mesh()  # destination chevron arrow (points down), ~2 m
    m.add_box(0, 0.9, 0, 0.5, 1.2, 0.22, "arrow")
    m.add_box(-0.42, 0.55, 0, 0.5, 0.5, 0.22, "arrow", ry=math.radians(45))
    m.add_box(0.42, 0.55, 0, 0.5, 0.5, 0.22, "arrow", ry=math.radians(-45))
    m.write("arrow_chevron", {"arrow": "M_arrow"})
    m = Mesh()  # parked car silhouette (4-box, props only in P1)
    m.add_box(0, 0.55, 0, 1.8, 0.7, 4.2, "carpaint")
    m.add_box(0, 1.15, -0.2, 1.6, 0.6, 2.2, "carpaint")
    m.add_box(0, 1.12, -1.35, 1.5, 0.4, 0.1, "glass")
    for sx in (-0.85, 0.85):
        m.add_cyl(sx, 0.32, -1.4, 0.32, 0.16, 10, "wheel", axis="x")
        m.add_cyl(sx, 0.32, 1.4, 0.32, 0.16, 10, "wheel", axis="x")
    m.write("parked_car", {"carpaint": "M_carpaint", "glass": "M_glass", "wheel": "M_wheel"})


if __name__ == "__main__":
    tuktuk(); wheel_loose(); building_a(); building_b(); building_c()
    person(False); person(True); props(); ramp()
    print("models written:", sorted(os.listdir(OUT)))
