"""Cinematic integration of a puppet into the painted plate: CAST SHADOW (silhouette sheared onto the ground, soft, tinted), RIM LIGHT (warm edge on the side facing the sun),
contact occlusion.  The puppet is drawn twice (black / white canvas) to recover its exact alpha; the black render is the premultiplied colour."""
import cv2, math, numpy as np
from engine import *


def hero_fx(cv, draw, gy, sun=1.0, sun_h=0.30, shadow_a=0.9, shadow_len=1.0, rim=0.6, rim_col=(120, 200, 255), rim_w=4, shade=None, sx_of=None, grade=1.0, haze=0.0, haze_col=(150, 190, 225), key=(0.90, 0.97, 1.07)):
    """draw(canvas) draws the puppet (must not draw its own shadow). sun=+1: sun on the right (shadow falls left), -1 left. sun_h: 0 low sun .. 1 high"""
    blk = np.zeros_like(cv); draw(blk)
    wht = np.full_like(cv, 255.0); draw(wht)
    a = np.clip(1.0 - (wht - blk).mean(2) / 255.0, 0.0, 1.0)
    # cast shadow: shear + flatten about the ground line
    f = 0.16 + 0.35 * sun_h; sh = -sun * (1.1 - 0.7 * sun_h) * shadow_len
    M = np.float32([[1, -sh, sh * gy], [0, -f, gy * (1 + f)]])
    sm = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR); sm = cv2.GaussianBlur(sm, (0, 0), 5)
    ys = np.arange(H, dtype=np.float32)[:, None]; fade = np.clip(1.0 - (ys - gy) / (260.0 * shadow_len + 1), 0.15, 1.0)
    sm = sm * fade * (ys >= gy - 2)
    tintc = np.array([0.38, 0.45, 0.62], np.float32) if shade is None else np.array(shade, np.float32)
    cv *= 1.0 - shadow_a * sm[..., None] * (1.0 - tintc)
    # colour-match the puppet to the plate: warm key light from the sun side falling off across the figure, cool/dark far side, slight desaturation, aerial haze with distance
    if grade > 0:
        cols = np.where(a.max(0) > 0.1)[0]
        if len(cols) > 4:
            x0, x1 = cols.min(), cols.max(); u = np.clip((np.arange(W, dtype=np.float32) - x0) / float(max(x1 - x0, 1)), 0, 1)
            u = u if sun < 0 else 1.0 - u
            L = (1.06 - 0.30 * u ** 1.3)[None, :, None]
            kk = np.array(key, np.float32)[None, None, :]
            g = L * (1.0 + (kk - 1.0) * (1.0 - 0.45 * u[None, :, None]))
            far = np.array([0.94, 0.97, 1.04], np.float32)[None, None, :]
            g = g * (1.0 + (far - 1.0) * u[None, :, None])
            gray = blk.mean(2, keepdims=True)
            blk2 = gray + (blk - gray) * 0.93
            blk = blk * (1 - grade) + blk2 * g * grade
    if haze > 0:
        blk = blk * (1.0 - haze) + np.array(haze_col, np.float32)[None, None, :] * haze * a[..., None]
    # composite the puppet
    cv *= (1.0 - a)[..., None]; cv += blk
    # rim light on the sun-facing edge
    if rim > 0:
        r = int(rim_w); shifted = np.roll(a, -int(sun) * r, axis=1)      # neighbour towards the sun
        edge = np.clip(a - shifted, 0, 1) * a
        edge = np.clip(cv2.GaussianBlur(edge, (0, 0), 1.0) * 1.8, 0, 1)
        col = np.array(rim_col, np.float32) * rim
        cv += edge[..., None] * col[None, None, :] * 0.9
    return a
