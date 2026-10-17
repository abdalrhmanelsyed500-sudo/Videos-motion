"""'Silhouette Quota' (Module A6): do two islands look alike from the sea?

The player first meets every island as a shape on the horizon, so uniqueness is measured on what they SEE: the dry-land
silhouette, cropped to its bounding box, resampled to 32x32, compared at all 8 rotations/flips (an island turned 90 degrees
is still the same island to the eye). Catalog rules (hook-kind quota, template+kit quota, no identical neighbours) sit on top.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

RES = 32


def silhouette(m: dict) -> np.ndarray:
    t = np.array([list(r) for r in m["terrain"]])
    land = np.isin(t, list(".gur#"))
    ys, xs = np.where(land)
    crop = land[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = crop.shape
    s = max(h, w)
    sq = np.zeros((s, s), np.uint8)
    sq[(s - h) // 2:(s - h) // 2 + h, (s - w) // 2:(s - w) // 2 + w] = crop * 255
    im = Image.fromarray(sq).resize((RES, RES), Image.BOX)
    return np.asarray(im) >= 128


def _variants(a: np.ndarray):
    for k in range(4):
        r = np.rot90(a, k)
        yield r
        yield np.fliplr(r)


def iou(a: np.ndarray, b: np.ndarray) -> float:
    best = 0.0
    for v in _variants(b):
        u = (a | v).sum()
        best = max(best, (a & v).sum() / u if u else 0.0)
    return float(best)


def check_catalog(entries: list[tuple[dict, dict]], ctx: dict) -> tuple[list[str], list[str], list[tuple[str, str, float]]]:
    """entries = [(island_record, baked_map)]. returns (problems, warnings, pair_table sorted by IoU desc)."""
    tun = ctx["tuning"]
    max_iou = tun["island.sameness_max_iou"]
    probs: list[str] = []
    warns: list[str] = []
    sil = {i["id"]: silhouette(m) for i, m in entries}
    pairs = []
    ids = [i["id"] for i, _ in entries]
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            pairs.append((ids[a], ids[b], iou(sil[ids[a]], sil[ids[b]])))
    pairs.sort(key=lambda p: -p[2])
    for x, y, v in pairs:
        if v >= max_iou:
            probs.append(f"islands {x} and {y} look alike from the sea (silhouette overlap {v:.2f} >= {max_iou})")
    hooks: dict[str, list[str]] = {}
    combos: dict[tuple, list[str]] = {}
    for isl, _ in entries:
        hooks.setdefault(isl.get("hook_kind", ""), []).append(isl["id"])
        combos.setdefault((isl["template"], isl["kits"][0]), []).append(isl["id"])
    for k, v in hooks.items():
        if k and len(v) > tun["island.max_per_hook_kind"]:
            probs.append(f"hook kind '{k}' used by {len(v)} islands (max {int(tun['island.max_per_hook_kind'])}): {v}")
    for k, v in combos.items():
        if len(v) > tun["island.max_per_template_kit"]:
            probs.append(f"template+kit {k} used by {len(v)} islands (max {int(tun['island.max_per_template_kit'])}): {v}")
    by_id = {i["id"]: i for i, _ in entries}
    for isl, _ in entries:
        for nb in isl.get("neighbors", []):
            o = by_id.get(nb["id"])
            if o and o["id"] > isl["id"]:
                if o["template"] == isl["template"] and o["kits"][0] == isl["kits"][0]:
                    warns.append(f"neighbours {isl['id']} and {o['id']} share template and kit")
                if o.get("hook_kind") and o.get("hook_kind") == isl.get("hook_kind"):
                    probs.append(f"neighbours {isl['id']} and {o['id']} share hook kind '{o['hook_kind']}'")
    return probs, warns, pairs
