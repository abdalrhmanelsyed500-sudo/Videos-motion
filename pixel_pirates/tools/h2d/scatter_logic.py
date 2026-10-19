"""Python twin of game/h2d/cay_scatter.gd (H2D-1.2 vegetation scatter) and the fixture writer for the GDScript test.

  python tools/h2d/scatter_logic.py            # rewrites game/tests/fixtures/scatter_cases.json
  python tools/h2d/scatter_logic.py --check    # recomputes and compares with the stored fixture (exit 1 on a difference)

The scatter is a pure function of (chunk, baked maps): one candidate per 8 m cell, kept or dropped by biome class, forest
density and ground height. tests/test_scatter.gd replays the fixture in Godot (NOT YET RUN IN GODOT).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "game/h2d/art"
FIXTURE = ROOT / "game/tests/fixtures/scatter_cases.json"
FOREST = 4


def hash01(ix: int, iz: int, salt: int) -> float:
    v = (ix * 374761393 + iz * 668265263 + salt * 1442695041) & 0xFFFFFFFF
    v = ((v ^ (v >> 13)) * 1274126177) & 0xFFFFFFFF
    v ^= v >> 16
    return (v & 0xFFFF) / 65535.0


def decode_height(b: int, top: float) -> float:
    v = b / 255.0
    if v < 0.1:
        return v / 0.1 * 8.0 - 8.0
    u = (v - 0.1) / 0.9
    return u * u * top


class Scatter:
    def __init__(self) -> None:
        self.meta = json.loads((ART / "anvil_cay.json").read_text())
        g = self.meta["grid"]
        self.n, self.cell, self.ox, self.oz = int(g["cells"]), float(g["cell_m"]), float(g["origin_x"]), float(g["origin_z"])
        self.hgt = np.array(Image.open(ART / "anvil_cay_height.png").convert("RGBA"))
        self.bio = np.array(Image.open(ART / "anvil_cay_biome.png").convert("RGBA"))
        top = float(self.meta["height_enc"]["top"])
        self.lut = [decode_height(i, top) for i in range(256)]
        sc = self.meta["scatter"]
        self.sc = sc
        self.rules: list[list] = [[] for _ in range(16)]
        for k, v in sc["classes"].items():
            self.rules[int(k)] = v
        self.trunk = {int(k): float(v) for k, v in sc["trunk_r"].items()}

    def chunk(self, cx: int, cz: int) -> dict:
        sp = float(self.sc["spacing_m"])
        per = int(round(float(self.sc["chunk_m"]) / sp))
        inst: list[tuple[float, float, int, float, float]] = []
        trunks: list[tuple[float, float, float]] = []
        for gj in range(cz * per, cz * per + per):
            for gi in range(cx * per, cx * per + per):
                x = (gi + 0.15 + 0.7 * hash01(gi, gj, 1)) * sp
                z = (gj + 0.15 + 0.7 * hash01(gi, gj, 2)) * sp
                ix, iz = int(np.floor((x - self.ox) / self.cell)), int(np.floor((z - self.oz) / self.cell))
                if ix < 0 or iz < 0 or ix >= self.n or iz >= self.n:
                    continue
                cls = int(self.bio[iz, ix, 0]) >> 4
                if cls == 0 or cls >= len(self.rules) or not self.rules[cls]:
                    continue
                b = int(self.bio[iz, ix, 2])
                if b == 255:
                    continue
                dens = 1.0
                if cls == FOREST:
                    dens = float(self.sc["forest_density_min"]) + float(self.sc["forest_density_gain"]) * b / 250.0
                h = self.lut[int(self.hgt[iz, ix, 0])]
                if h < float(self.sc["min_height_m"]):
                    continue
                r = hash01(gi, gj, 3)
                cum, pick = 0.0, None
                for e in self.rules[cls]:
                    cum += float(e[1]) * dens
                    if r < cum:
                        pick = e
                        break
                if pick is None:
                    continue
                typ = int(pick[0])
                s = float(pick[2]) + (float(pick[3]) - float(pick[2])) * hash01(gi, gj, 4)
                inst.append((x, z, typ, s, h))
                if typ in self.trunk:
                    trunks.append((x, z, self.trunk[typ] * s))
        return {"count": len(inst), "trunks": trunks, "inst": inst}


def build_fixture() -> dict:
    s = Scatter()
    hashes = []
    for ix, iz, salt in [(0, 0, 1), (1, 0, 1), (0, 1, 2), (-1, -1, 3), (17, -33, 4), (-250, 80, 2), (499, -499, 3), (123, 456, 1)]:
        hashes.append({"ix": ix, "iz": iz, "salt": salt, "v": round(hash01(ix, iz, salt), 6)})
    chunks = []
    # a spread of chunks: the village (0, -1), forest, the lookout, Wreck Beach, Pearl Cove, an empty sea chunk
    for cx, cz in [(0, -1), (0, -2), (0, -3), (-2, -2), (2, -2), (0, -4), (-5, -10), (10, 5)]:
        c = s.chunk(cx, cz)
        sx = sum(i[0] for i in c["inst"])
        sz = sum(i[1] for i in c["inst"])
        st = sum(i[2] for i in c["inst"])
        chunks.append({"cx": cx, "cz": cz, "count": c["count"], "trunks": len(c["trunks"]), "sum_x": round(sx, 3),
                       "sum_z": round(sz, 3), "sum_type": st})
    return {"schema": 1, "hashes": hashes, "chunks": chunks}


def main() -> int:
    fx = build_fixture()
    text = json.dumps(fx, indent=1) + "\n"
    if "--check" in sys.argv:
        same = FIXTURE.exists() and json.loads(FIXTURE.read_text()) == fx
        print("scatter fixture", "matches" if same else "DIFFERS from the stored file")
        return 0 if same else 1
    FIXTURE.write_text(text)
    print("wrote", FIXTURE.relative_to(ROOT), [(c["cx"], c["cz"], c["count"]) for c in fx["chunks"]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
