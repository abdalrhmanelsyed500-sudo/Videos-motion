"""Writes game/h2d/art/ship_sloop_sailbox.json (H2D-0.3): the bounding box of the sail pixels in every frame of the sail
sheet (16 headings x 5 trims), so the shader can fix the head and foot of the sail and bend only the middle.
H2D-0.2 used one fixed band (rows 11..62) for every frame, but the sail is 12..57 in one frame and 19..77 in another.
  python tools/h2d/make_sail_boxes.py"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "game" / "h2d" / "art"


def main() -> None:
    meta = json.loads((ART / "ship_sloop.json").read_text())
    fw, fh = meta["frame_px"]
    n_head = int(meta["headings"])
    n_trim = len(meta["trims_deg"])
    a = np.array(Image.open(ART / meta["sail_sheet"]).convert("RGBA"))[..., 3]
    boxes = []
    for r in range(n_trim):
        row = []
        for c in range(n_head):
            fr = a[r * fh:(r + 1) * fh, c * fw:(c + 1) * fw]
            ys, xs = np.nonzero(fr > 127)
            row.append([int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if len(xs) else [0, 0, 1, 1])
        boxes.append(row)
    out = {"doc": "Sail pixel bounding boxes [x0, y0, x1, y1] per frame: boxes[trim_row][heading_frame]. Made by tools/h2d/make_sail_boxes.py.",
           "frame_px": [fw, fh], "boxes": boxes}
    dst = ART / "ship_sloop_sailbox.json"
    dst.write_text(json.dumps(out) + "\n")
    print("wrote", dst, n_trim, "x", n_head)


if __name__ == "__main__":
    main()
