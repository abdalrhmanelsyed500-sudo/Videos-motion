"""VP-0: bake every prototype sprite. Usage: python tools/vp0/bake_all.py [group ...]   (groups: ship, island, ground)
Writes game/art/vp0/<group>/<name>[_f<k>].png and game/art/vp0/<group>/<group>_manifest.json (pivot, size, facings, colours per sprite)."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voxel as V  # noqa: E402

OUT = V.ROOT / "game" / "art" / "vp0"


def bake_group(group: str, models: dict, only=None) -> dict:
    man = {}
    for name, (fn, nf) in models.items():
        if only and name not in only:
            continue
        t = time.time()
        vox = fn()
        frames = []
        for k in range(nf):
            m = vox if nf == 1 else vox.rotate(k * 360.0 / nf)
            res = V.crop(V.render(m))
            fname = f"{name}.png" if nf == 1 else f"{name}_f{k}.png"
            V.save(res, OUT / group / fname)
            frames.append({"file": fname, "w": int(res["img"].shape[1]), "h": int(res["img"].shape[0]),
                           "pivot": [round(float(res["pivot"][0]), 1), round(float(res["pivot"][1]), 1)],
                           "colours": V.count_colours(res["img"])})
        man[name] = {"facings": nf, "frames": frames}
        print(f"{group}/{name}: {nf} frame(s) {frames[0]['w']}x{frames[0]['h']} colours {max(f['colours'] for f in frames)} ({time.time() - t:.1f}s)", flush=True)
    (OUT / group).mkdir(parents=True, exist_ok=True)
    (OUT / group / f"{group}_manifest.json").write_text(json.dumps(man, indent=1))
    return man


def sheet(group: str, man: dict, path: Path, scale=3, bg=(86, 132, 140)) -> None:
    items = []
    for name, m in man.items():
        row = [Image.open(OUT / group / f["file"]) for f in m["frames"]]
        items.append((name, row))
    W = 8 + max(sum(i.width + 6 for i in row) for _, row in items)
    Hh = 8 + sum(max(i.height for i in row) + 8 for _, row in items)
    im = Image.new("RGBA", (W, Hh), bg + (255,))
    y = 4
    for name, row in items:
        x = 4
        hmax = max(i.height for i in row)
        for i in row:
            im.alpha_composite(i, (x, y + hmax - i.height))
            x += i.width + 6
        y += hmax + 8
    im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)


if __name__ == "__main__":
    groups = sys.argv[1:] or ["ship", "island"]
    for g in groups:
        if g == "ship":
            import models_ship as M
            man = bake_group("ship", M.MODELS)
            sheet("ship", man, Path("/tmp/sheet_ship.png"))
        if g == "island":
            import models_island as I
            man = bake_group("island", I.MODELS)
            sheet("island", man, Path("/tmp/sheet_island.png"), scale=2)
