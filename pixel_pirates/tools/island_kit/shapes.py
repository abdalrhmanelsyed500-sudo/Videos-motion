"""Shape operators for island templates (Module A6). Each op returns a potential P (>0 = land, about 1 at the heart) and aux data.

All coordinates are normalised to [-1, 1] across the island grid. Every parameter has a default; a template overrides some.
`var` randomises the main size parameters by +-var (so one template gives different islands per seed); `rot_deg` (absent =
random) rotates the whole shape; `warp` bends the domain; `rough` roughens the coastline.
"""
from __future__ import annotations

import math

import numpy as np

import prng

COMMON = {"warp": 0.16, "rough": 0.10, "var": 0.12, "rot_deg": None}
PARAMS: dict[str, dict[str, float]] = {
    "blob": {"radius": 0.62, "aspect": 0.85, "lobes": 2, "lobe_amp": 0.12},
    "ring": {"radius": 0.58, "width": 0.17, "passes": 2, "pass_width": 0.35},
    "crescent": {"radius": 0.66, "bite_radius": 0.42, "bite_offset": 0.50, "aspect": 1.0, "lobes": 2, "lobe_amp": 0.08},
    "ridge": {"length": 0.88, "width": 0.22, "bend": 0.25},
    "twin_lobes": {"r1": 0.40, "r2": 0.32, "sep": 0.52, "neck": 0.10},
    "cone": {"radius": 0.56, "crater": 0.22, "aspect": 1.0, "lobes": 2, "lobe_amp": 0.08},
    "mesa": {"radius": 0.56, "ramp_width": 0.9, "aspect": 1.0, "lobes": 2, "lobe_amp": 0.08},
    "stack_field": {"count": 14, "rmin": 0.05, "rmax": 0.16, "spread": 0.62},
    "flats": {"length": 0.90, "width": 0.14, "bend": 0.15},
    "fjord": {"radius": 0.64, "cut_width": 0.11, "cut_length": 0.62, "aspect": 1.0, "lobes": 2, "lobe_amp": 0.08},
}


def allowed_params(op: str) -> set[str]:
    return set(PARAMS.get(op, {})) | set(COMMON)


def _wrap(a: np.ndarray) -> np.ndarray:
    return (a + math.pi) % (2 * math.pi) - math.pi


def potential(op: str, params: dict, rng: prng.SplitMix64, n: int, seed: int):
    """returns (P, aux). rng call order is fixed per op => deterministic."""
    p = {**COMMON, **PARAMS[op], **params}
    lin = (np.arange(n) + 0.5) / n * 2 - 1
    U, V = np.meshgrid(lin, lin)
    rot = (p["rot_deg"] if p["rot_deg"] is not None else rng.uniform(0, 360)) * math.pi / 180
    c, s = math.cos(rot), math.sin(rot)
    X, Y = c * U + s * V, -s * U + c * V
    wa = prng.fbm(n, n / 3.2, 3, seed + 11)
    wb = prng.fbm(n, n / 3.2, 3, seed + 23)
    X = X + p["warp"] * (wa - 0.5) * 2
    Y = Y + p["warp"] * (wb - 0.5) * 2
    var = p["var"]

    def vr(name: str) -> float:
        return p[name] * (1 + rng.uniform(-var, var))

    aux: dict = {"X": X, "Y": Y, "U": U, "V": V}
    if op in ("blob", "cone", "mesa", "fjord", "crescent"):
        R = vr("radius")
        asp = min(vr("aspect"), 1.1)
        ax, ay = R, R * asp
        r = np.sqrt((X / ax) ** 2 + (Y / ay) ** 2)
        th = np.arctan2(Y / ay, X / ax)
        lobes = int(p["lobes"])
        amp = p["lobe_amp"]
        ph = rng.uniform(0, 6.283)
        P = 1 - r / (1 + amp * np.sin(lobes * th + ph))
        aux.update(R=R, r=r, th=th)
        if op == "crescent":
            br, bo = vr("bite_radius"), vr("bite_offset")
            phi = rng.uniform(0, 6.283)
            d = np.sqrt((X - bo * math.cos(phi)) ** 2 + (Y - bo * math.sin(phi)) ** 2)
            P = np.minimum(P, -(br - d) / br)
        elif op == "mesa":
            aux["ramp_th"] = rng.uniform(-math.pi, math.pi)
            aux["ramp_w"] = p["ramp_width"]
        elif op == "cone":
            aux["crater"] = p["crater"]
        elif op == "fjord":
            L, w = vr("cut_length"), vr("cut_width")
            x0 = R - L
            t = np.clip((X - x0) / max(L, 1e-6), 0, 1.4)
            wt = w * (0.45 + 0.55 * np.clip(t, 0, 1))
            pc = np.where((X > x0) & (X < R + 0.4), (wt - np.abs(Y)) / wt, -1.0)
            P = np.minimum(P, -pc)
    elif op == "ring":
        R0, w = vr("radius"), vr("width")
        r = np.sqrt(X ** 2 + Y ** 2)
        th = np.arctan2(Y, X)
        P = (w - np.abs(r - R0)) / w
        npass, pw = int(p["passes"]), p["pass_width"]
        ph = rng.uniform(0, 6.283)
        for k in range(npass):
            a = ph + k * 2 * math.pi / max(npass, 1) + rng.uniform(-0.25, 0.25)
            dth = np.abs(_wrap(th - a))
            P = P - 1.6 * np.clip(1 - dth / (pw / 2), 0, 1)
    elif op == "ridge" or op == "flats":
        Ln, w = vr("length"), vr("width")
        bend = p["bend"]
        Yb = Y - bend * (X / (Ln / 2)) ** 2 * 0.5
        P = 1 - np.sqrt((X / (Ln / 2)) ** 2 + (Yb / (w / 2)) ** 2)
    elif op == "twin_lobes":
        r1, r2, sep, neck = vr("r1"), vr("r2"), vr("sep"), vr("neck")
        P1 = 1 - np.sqrt((X + sep / 2) ** 2 + Y ** 2) / r1
        P2 = 1 - np.sqrt((X - sep / 2) ** 2 + Y ** 2) / r2
        Pb = np.where(np.abs(X) < sep / 2, (neck - np.abs(Y)) / neck * 0.8, -1.0)
        P = np.maximum(np.maximum(P1, P2), Pb)
    elif op == "stack_field":
        P = np.full((n, n), -1.0)
        for _ in range(int(p["count"])):
            rr = p["rmin"] + (p["rmax"] - p["rmin"]) * rng.random() ** 2
            ang, dist = rng.uniform(0, 6.283), p["spread"] * math.sqrt(rng.random())
            cx, cy = dist * math.cos(ang), dist * math.sin(ang)
            P = np.maximum(P, 1 - np.sqrt((X - cx) ** 2 + (Y - cy) ** 2) / rr)
    else:
        raise ValueError(f"unknown shape op {op}")
    aux["p"] = p
    return P, aux
