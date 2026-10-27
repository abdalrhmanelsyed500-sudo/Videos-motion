#!/usr/bin/env python3
"""Structured visual comparison between a supplied reference and an in-engine frame.

This is a review aid, not a claim of exact visual fidelity. It compares
region-level colour, luminance, edge density, quantized palettes and a simple
SSIM-like grayscale structure score.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

REGIONS = {
    "sky": (0.00, 0.25),
    "horizon": (0.25, 0.45),
    "road": (0.45, 0.75),
    "dashboard": (0.75, 1.00),
}


def load_image(path: Path, size=(1280, 720)) -> Image.Image:
    return ImageOps.fit(Image.open(path).convert("RGB"), size, method=Image.Resampling.LANCZOS)


def array_stats(arr: np.ndarray) -> dict:
    gray = arr[..., :3].mean(axis=2)
    gx = np.abs(np.diff(gray, axis=1)).mean() if gray.shape[1] > 1 else 0.0
    gy = np.abs(np.diff(gray, axis=0)).mean() if gray.shape[0] > 1 else 0.0
    return {
        "mean_rgb": [round(float(x), 2) for x in arr.reshape(-1, 3).mean(axis=0)],
        "median_rgb": [float(x) for x in np.median(arr.reshape(-1, 3), axis=0)],
        "luminance_mean": round(float(gray.mean()), 2),
        "luminance_std": round(float(gray.std()), 2),
        "edge_density": round(float((gx + gy) / 2.0), 3),
    }


def quantized_palette(arr: np.ndarray, step=24, count=8) -> list:
    q = (arr // step * step).reshape(-1, 3)
    colors, counts = np.unique(q, axis=0, return_counts=True)
    order = np.argsort(counts)[::-1][:count]
    return [
        {"rgb": [int(v) for v in colors[i]], "share": round(float(counts[i] / len(q)), 4)}
        for i in order
    ]


def box_mean(arr: np.ndarray, radius=2) -> np.ndarray:
    # Float box filter via a sliding window; no 8-bit clipping of squared
    # luminance, which would corrupt the variance/covariance calculation.
    a = np.asarray(arr, dtype=np.float64)
    size = 2 * radius + 1
    padded = np.pad(a, ((radius, radius), (radius, radius)), mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(padded, (size, size))
    return windows.mean(axis=(2, 3))


def structure_score(a: np.ndarray, b: np.ndarray) -> float:
    # Downsample to a coarse 320x180 luminance grid, then compute a local
    # mean/variance/covariance SSIM-like score without external dependencies.
    ia = Image.fromarray(a).convert("L").resize((320, 180), Image.Resampling.BOX)
    ib = Image.fromarray(b).convert("L").resize((320, 180), Image.Resampling.BOX)
    x = np.asarray(ia, dtype=np.float64) / 255.0
    y = np.asarray(ib, dtype=np.float64) / 255.0
    c1, c2 = 0.01 ** 2, 0.03 ** 2
    mu_x, mu_y = box_mean(x), box_mean(y)
    sigma_x = box_mean(x * x) - mu_x * mu_x
    sigma_y = box_mean(y * y) - mu_y * mu_y
    sigma_xy = box_mean(x * y) - mu_x * mu_y
    numerator = (2 * mu_x * mu_y + c1) * (2 * sigma_xy + c2)
    denominator = (mu_x * mu_x + mu_y * mu_y + c1) * (sigma_x + sigma_y + c2)
    score = numerator / np.maximum(denominator, 1e-6)
    return round(float(np.clip(score.mean(), -1.0, 1.0)), 4)


def rgb_distance(a, b) -> float:
    return round(float(np.linalg.norm(np.asarray(a, dtype=float) - np.asarray(b, dtype=float))), 2)


def compare(reference: Image.Image, capture: Image.Image, label: str) -> dict:
    a = np.asarray(reference, dtype=np.uint8)
    b = np.asarray(capture, dtype=np.uint8)
    height = a.shape[0]
    regions = {}
    region_distances = []
    for name, (top, bottom) in REGIONS.items():
        y0, y1 = int(height * top), int(height * bottom)
        ra, rb = a[y0:y1], b[y0:y1]
        sa, sb = array_stats(ra), array_stats(rb)
        distance = rgb_distance(sa["mean_rgb"], sb["mean_rgb"])
        region_distances.append(distance)
        regions[name] = {
            "reference": sa,
            "capture": sb,
            "mean_rgb_distance": distance,
            "luminance_delta": round(sb["luminance_mean"] - sa["luminance_mean"], 2),
            "edge_density_delta": round(sb["edge_density"] - sa["edge_density"], 3),
        }
    return {
        "label": label,
        "resolution": [a.shape[1], a.shape[0]],
        "global": {
            "reference": array_stats(a),
            "capture": array_stats(b),
            "mean_rgb_distance": rgb_distance(a.reshape(-1, 3).mean(axis=0), b.reshape(-1, 3).mean(axis=0)),
            "structure_score": structure_score(a, b),
            "reference_palette": quantized_palette(a),
            "capture_palette": quantized_palette(b),
        },
        "regions": regions,
        "mean_region_rgb_distance": round(sum(region_distances) / len(region_distances), 2),
        "interpretation": "Lower colour distances and a higher structure score indicate closer measurable composition. Artistic fidelity still requires visual inspection.",
    }


def make_review(reference: Image.Image, capture: Image.Image, report: dict, output: Path) -> None:
    w, h = reference.size
    footer = 150
    canvas = Image.new("RGB", (w * 2, h + footer), (18, 18, 22))
    canvas.paste(reference, (0, 0))
    canvas.paste(capture, (w, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, h, w * 2, h + footer], fill=(24, 24, 28))
    draw.text((20, h + 10), "REFERENCE (USER IMAGE)", fill=(232, 205, 92))
    draw.text((w + 20, h + 10), "IN-ENGINE GODOT CAMERA", fill=(232, 205, 92))
    g = report["global"]
    lines = [
        f"Label: {report['label']}    Size: {report['resolution'][0]}x{report['resolution'][1]}",
        f"Global mean RGB distance: {g['mean_rgb_distance']}    Structure score: {g['structure_score']}",
        f"Mean region RGB distance: {report['mean_region_rgb_distance']}",
        "Region RGB distances: " + ", ".join(
            f"{name}={data['mean_rgb_distance']}" for name, data in report["regions"].items()),
        "Review: compare sky/building density, road markings, vehicle silhouettes, dashboard mass and coarse texture scale.",
        "Numeric similarity does NOT prove exact fidelity; this image is for structured human review.",
    ]
    y = h + 34
    for line in lines:
        draw.text((20, y), line, fill=(220, 220, 214))
        y += 19
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--capture", required=True, type=Path)
    parser.add_argument("--label", default="benchmark")
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--review", required=True, type=Path)
    args = parser.parse_args()
    reference = load_image(args.reference)
    capture = load_image(args.capture)
    report = compare(reference, capture, args.label)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    make_review(reference, capture, report, args.review)
    print(json.dumps({
        "label": args.label,
        "global_rgb_distance": report["global"]["mean_rgb_distance"],
        "mean_region_rgb_distance": report["mean_region_rgb_distance"],
        "structure_score": report["global"]["structure_score"],
        "report": str(args.report),
        "review": str(args.review),
    }, indent=2))


if __name__ == "__main__":
    main()
