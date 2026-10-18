"""DIAGNOSTIC ONLY (H2D-0.3): draws the REAL sail art through a numpy copy of ship.gdshader's sail maths (whole-pixel bands,
per-frame sail box, anchored mast edge, fold shading) driven by the Python twin of sail_model.gd, for calm / breezy / rough /
gale. Also prints how many whole-pixel changes per second a mid-sail pixel shows with the OLD H2D-0.2 model and the new one.
It is not a Godot render and says nothing about how it LOOKS in motion. Output: build/sail_preview.png, sail_preview.txt.
  python tools/h2d/sail_preview.py [out_dir]"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import env_logic as E  # noqa: E402
import sail_logic as S  # noqa: E402

ROOT = E.ROOT
ART = ROOT / "game" / "h2d" / "art"
FW = FH = 112


def frame(sheet: np.ndarray, col: int, row: int) -> np.ndarray:
    return sheet[row * FH:(row + 1) * FH, col * FW:(col + 1) * FW]


def shade(hull, sails, box, belly, flap_amp, flap_phase, folds, lee=(1.0, 0.0), pivot_x=56.0):
    out = hull.copy()
    ys, xs = np.mgrid[0:FH, 0:FW]
    pcx, pcy = xs + 0.5, ys + 0.5
    bh = max(box[3] - box[1], 8.0)
    band = np.floor((pcy - box[1]) / 3.0)
    prof = np.sin(math.pi * np.clip((band * 3.0 + 1.5) / bh, 0, 1))
    anchor = np.clip(np.abs(pcx - pivot_x) / max(0.5 * (box[2] - box[0]), 4.0), 0, 1)
    off = belly * prof * (0.3 + 0.7 * anchor) + flap_amp * np.sin(flap_phase + band * 0.9) * prof * (0.4 + 0.6 * anchor)
    ox = np.floor(lee[0] * off + 0.5).astype(int)
    oy = np.floor(lee[1] * off + 0.5).astype(int)
    sx = np.clip(xs - ox, 0, FW - 1)
    sy = np.clip(ys - oy, 0, FH - 1)
    sa = sails[sy, sx]
    m = sa[..., 3] > 127
    col = sa.copy()
    if folds > 0.02:
        fx = (pcx - box[0]) * 0.55 + (pcy - box[1]) * 0.30 + belly * 0.6
        dark = 1.0 - 0.16 * folds * (np.mod(fx * 0.2, 1.0) >= 0.62)
        col[..., :3] = (col[..., :3] * dark[..., None]).astype(np.uint8)
    out[m] = col[m]
    return out


def old_steps(wind_kn: float, gustiness: float, off: float, secs: float = 60.0) -> float:
    """H2D-0.2: belly 0.8*(1+2ss(4,16,w))*(1-0.3ss(26,40,w))*(1-luff) plus 1.6*flutter*sin(p.y*0.55 + t*13) on a mid-sail row."""
    dt = 1 / 60
    prev, steps = None, 0
    luff = 1 - E.smoothstep(36.0, 52.0, off)
    for i in range(int(secs / dt)):
        t = 30 + i * dt
        g = E.smoothstep(0.60, 0.92, E.gust_noise(t)) * gustiness
        w = wind_kn * (1 + 0.45 * g)
        billow = (1 - luff) * (1 + 2 * E.smoothstep(4, 16, w)) * (1 - 0.3 * E.smoothstep(26, 40, w))
        slack = 1 - E.smoothstep(3, 8, w)
        flutter = E.clamp(luff + 0.5 * slack + 0.35 * g, 0, 1)
        d = math.floor(0.8 * billow * 0.9 + flutter * 1.6 * math.sin(30 * 0.55 + t * 13) * 0.7 + 0.5)
        if prev is not None and d != prev:
            steps += 1
        prev = d
    return steps / secs


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "build"
    out.mkdir(parents=True, exist_ok=True)
    meta = json.loads((ART / "ship_sloop.json").read_text())
    boxes = json.loads((ART / "ship_sloop_sailbox.json").read_text())["boxes"]
    hull = np.array(Image.open(ART / meta["hull_sheet"]).convert("RGBA"))
    sails = np.array(Image.open(ART / meta["sail_sheet"]).convert("RGBA"))
    P = E.load_params()
    col_f, row_t = 4, 3   # heading 90 deg, wind on the port beam (boom to starboard side drawing)
    weathers = [("calm", 4.0, 0.0, 90.0), ("breezy", 14.0, E.gustiness(14.0, 0.0), 90.0),
                ("rough", 24.0, E.gustiness(24.0, 0.25), 90.0), ("gale", 36.0, E.gustiness(36.0, 0.7), 90.0)]
    times = [0, 2, 4, 6, 8]
    scale = 3
    sheet = Image.new("RGBA", (FW * scale * len(times), FH * scale * len(weathers)), (70, 110, 130, 255))
    lines = ["DIAGNOSTIC ONLY: numpy copy of the shader's sail maths on the real art; not a Godot render.",
             "whole-pixel displacement changes per second on a mid-sail pixel, beam reach, 60 s (OLD H2D-0.2 vs NEW H2D-0.3):"]
    for r, (name, wk, gk, off) in enumerate(weathers):
        s = S.Sail(P)
        dt = 1 / 60
        for i in range(60 * 20):
            t = 20 + (i + 1) * dt
            g = E.smoothstep(0.60, 0.92, E.gust_noise(t)) * gk
            s.step(dt, wk * (1 + 0.45 * g), g, off, 40.0, t)
            sec = (i + 1) / 60
            if abs(sec - round(sec)) < 1e-9 and int(round(sec)) - 12 in times:
                o = s.out()
                fo = min(1.0, max(o["slack"], o["luff"]) * (1 - 0.5 * min(1.0, o["fill"])))
                img = shade(frame(hull, col_f, 0), frame(sails, col_f, row_t), boxes[row_t][col_f], o["belly_px"], o["flap_px"], o["flap_phase"], fo)
                im = Image.fromarray(img).resize((FW * scale, FH * scale), Image.NEAREST)
                sheet.alpha_composite(im, (times.index(int(round(sec)) - 12) * FW * scale, r * FH * scale))
        new_rows = S.run(S.Sail(P), 60, wk, lambda t, gk=gk: E.smoothstep(0.60, 0.92, E.gust_noise(t)) * gk, off, 40.0, 30.0)
        disp = [math.floor(x[1] + x[2] + 0.5) for x in new_rows]
        new = sum(1 for a, b in zip(disp, disp[1:]) if a != b) / 60.0
        lines.append(f"  {name:7s} old {old_steps(wk, gk, off):5.2f}/s   new {new:5.2f}/s   belly now {s.out()['belly_px']:.2f} px")
    sheet.convert("RGB").save(out / "sail_preview.png")
    (out / "sail_preview.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
