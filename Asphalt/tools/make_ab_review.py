#!/usr/bin/env python3
"""Create three-panel A/B review images: reference, full 3D, hybrid 2.5D."""
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
PANEL_W, PANEL_H = 960, 540
HEADER = 46
FOOTER = 118
GAP = 8

def f(size):
    return ImageFont.truetype(FONT, size)

def fit(path: Path) -> Image.Image:
    return ImageOps.fit(Image.open(path).convert("RGB"), (PANEL_W, PANEL_H), method=Image.Resampling.LANCZOS)

def metric_line(report_path: Path) -> str:
    d = json.loads(report_path.read_text())
    g = d["global"]
    return (f"Global RGB dist {g['mean_rgb_distance']:.2f} | "
            f"mean region {d['mean_region_rgb_distance']:.2f} | "
            f"structure {g['structure_score']:.4f}")

def compose(out_name: str, title: str, panels: list[tuple[str, Path]], notes: list[str]) -> None:
    width = PANEL_W * len(panels) + GAP * (len(panels) - 1)
    height = HEADER + PANEL_H + FOOTER
    canvas = Image.new("RGB", (width, height), (18, 18, 22))
    d = ImageDraw.Draw(canvas)
    d.text((18, 12), title, font=f(26), fill=(238, 205, 92))
    x = 0
    for label, path in panels:
        img = fit(path)
        canvas.paste(img, (x, HEADER))
        d.rectangle([x, HEADER, x + PANEL_W - 1, HEADER + 34], fill=(16, 16, 20))
        d.text((x + 14, HEADER + 7), label, font=f(21), fill=(238, 238, 228))
        x += PANEL_W + GAP
    d.rectangle([0, HEADER + PANEL_H, width, height], fill=(24, 24, 28))
    y = HEADER + PANEL_H + 12
    for line in notes:
        d.text((18, y), line, font=f(17), fill=(220, 220, 214))
        y += 23
    out = ROOT / "screenshots" / out_name
    canvas.save(out, optimize=True)
    print(out.name, canvas.size)

def main() -> None:
    compose("ab_cockpit_reference_3d_hybrid.png",
        "COCKPIT A/B — Reference 1 / Existing Full 3D / Hybrid 2.5D",
        [
            ("REFERENCE 1", ROOT / "docs/reference/reference_01.png"),
            ("APPROACH A — FULL 3D", ROOT / "screenshots/benchmark_cockpit.png"),
            ("APPROACH C — HYBRID 2.5D", ROOT / "screenshots/hybrid_benchmark_static.png"),
        ],
        [
            "3D metrics: " + metric_line(ROOT / "docs/metrics_final_cockpit.json"),
            "Hybrid metrics: " + metric_line(ROOT / "docs/metrics_hybrid_cockpit.json"),
            "Review: hybrid has closer dashboard mass, sprite-scaled riders, layered buildings and classic scanline road perspective.",
            "Numeric similarity is a guide only; artwork, silhouettes and composition were inspected directly.",
        ])
    compose("ab_movement_reference_3d_hybrid.png",
        "MOVEMENT A/B — Reference 3 / Full 3D Chase / Hybrid 2.5D Moving",
        [
            ("REFERENCE 3", ROOT / "docs/reference/reference_03.jpeg"),
            ("APPROACH A — FULL 3D CHASE", ROOT / "screenshots/benchmark_chase.png"),
            ("APPROACH C — HYBRID MOVING", ROOT / "screenshots/hybrid_benchmark_moving.png"),
        ],
        [
            "3D bridge metrics: " + metric_line(ROOT / "docs/metrics_final_bridge.json"),
            "Hybrid moving metrics: " + metric_line(ROOT / "docs/metrics_hybrid_moving.json"),
            "Review: hybrid sprites scale by road-relative z; markings and speed state remain readable while distance changes.",
            "Full 3D has flexible geometry, but its rider/bike and environment read as modern low-poly primitives.",
        ])
    compose("ab_crash_reference_3d_hybrid.png",
        "CRASH A/B — Reference 2 / Full 3D Fall / Hybrid 2.5D Fall",
        [
            ("REFERENCE 2", ROOT / "docs/reference/reference_02.png"),
            ("APPROACH A — FULL 3D FALL", ROOT / "screenshots/benchmark_3d_crash.png"),
            ("APPROACH C — HYBRID FALL", ROOT / "screenshots/hybrid_benchmark_crash.png"),
        ],
        [
            "3D crash metrics: " + metric_line(ROOT / "docs/metrics_3d_crash.json"),
            "Hybrid crash metrics: " + metric_line(ROOT / "docs/metrics_hybrid_crash.json"),
            "Review: hybrid uses dedicated fallen-rider/sliding-bike frames; 3D uses real geometry but a sparser scene.",
            "Both remain non-graphic; hybrid better matches the supplied image's layered cockpit/crash presentation.",
        ])
    summary = {
        "pairs": {
            "cockpit": {
                "3d": json.loads((ROOT / "docs/metrics_final_cockpit.json").read_text()),
                "hybrid": json.loads((ROOT / "docs/metrics_hybrid_cockpit.json").read_text()),
            },
            "movement": {
                "3d": json.loads((ROOT / "docs/metrics_final_bridge.json").read_text()),
                "hybrid": json.loads((ROOT / "docs/metrics_hybrid_moving.json").read_text()),
            },
            "crash": {
                "3d": json.loads((ROOT / "docs/metrics_3d_crash.json").read_text()),
                "hybrid": json.loads((ROOT / "docs/metrics_hybrid_crash.json").read_text()),
            },
        },
        "review_images": [
            "screenshots/ab_cockpit_reference_3d_hybrid.png",
            "screenshots/ab_movement_reference_3d_hybrid.png",
            "screenshots/ab_crash_reference_3d_hybrid.png",
        ],
        "note": "Metrics supplement, but do not replace, visual inspection of the actual screenshots.",
    }
    (ROOT / "docs/ab_comparison_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
