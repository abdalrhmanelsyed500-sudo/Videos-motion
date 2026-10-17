"""Deterministic randomness for island baking (Module A6).

Own SplitMix64 + integer-hash value noise: results do not depend on Python/numpy versions, so a seed always means the same island.
(Only +, -, *, comparisons and smoothstep are used on floats; no transcendental function feeds a threshold except sin/cos/atan2
in shapes, whose last-bit differences cannot move a cell unless a value sits within 1e-12 of the land threshold. The staleness
check therefore hashes the SOURCE (seed, template, kit, tuning) and not the output.)
"""
from __future__ import annotations

import numpy as np

MASK = (1 << 64) - 1


class SplitMix64:
    def __init__(self, seed: int) -> None:
        self.s = seed & MASK

    def next_u64(self) -> int:
        self.s = (self.s + 0x9E3779B97F4A7C15) & MASK
        z = self.s
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return z ^ (z >> 31)

    def random(self) -> float:
        return (self.next_u64() >> 11) / float(1 << 53)

    def uniform(self, a: float, b: float) -> float:
        return a + (b - a) * self.random()

    def randint(self, a: int, b: int) -> int:
        """inclusive both ends"""
        return a + int(self.random() * (b - a + 1))

    def choice(self, seq):
        return seq[int(self.random() * len(seq))]

    def fork(self, label: str) -> "SplitMix64":
        h = 1469598103934665603
        for ch in label.encode():
            h = ((h ^ ch) * 1099511628211) & MASK
        return SplitMix64(self.next_u64() ^ h)


def _hash(ix: np.ndarray, iy: np.ndarray, seed: int) -> np.ndarray:
    with np.errstate(over="ignore"):
        h = ix.astype(np.uint64) * np.uint64(0x9E3779B97F4A7C15)
        h ^= iy.astype(np.uint64) * np.uint64(0xC2B2AE3D27D4EB4F)
        h ^= np.uint64(seed & MASK)
        h ^= h >> np.uint64(33)
        h *= np.uint64(0xFF51AFD7ED558CCD)
        h ^= h >> np.uint64(33)
        h *= np.uint64(0xC4CEB9FE1A85EC53)
        h ^= h >> np.uint64(33)
    return (h >> np.uint64(11)).astype(np.float64) / float(1 << 53)


def value_noise(n: int, period: float, seed: int) -> np.ndarray:
    """n x n value noise in [0,1), lattice spacing `period` pixels, smoothstep interpolation."""
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float64)
    gx, gy = xx / period, yy / period
    x0, y0 = np.floor(gx).astype(np.int64), np.floor(gy).astype(np.int64)
    fx, fy = gx - x0, gy - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = _hash(x0, y0, seed), _hash(x0 + 1, y0, seed)
    c, d = _hash(x0, y0 + 1, seed), _hash(x0 + 1, y0 + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(n: int, base_period: float, octaves: int, seed: int) -> np.ndarray:
    """fractal noise normalised to [0,1]."""
    total = np.zeros((n, n))
    amp, norm, per = 1.0, 0.0, base_period
    for o in range(octaves):
        total += amp * value_noise(n, max(per, 1.5), seed + 1013 * o)
        norm += amp
        amp *= 0.5
        per *= 0.5
    return total / norm
