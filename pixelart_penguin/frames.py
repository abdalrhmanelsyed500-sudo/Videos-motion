"""Render one pose + facing into a 64x64 RGBA pixel-art frame (figure + shadow + muzzle flash + blood + pool)."""
import numpy as np
import sdf3d, penguin as P
from sdf3d import V, D
CX, CY = 32, 45

def proj(w, CX=CX):      # world point -> (col, row, depth)
    ph = sdf3d.CAM_PITCH; return CX + w[0], CY - (w[1] * np.cos(ph) + w[2] * np.sin(ph)), w[1] * -np.sin(ph) + w[2] * np.cos(ph) + 160.0

def draw_flash(rgb, alpha, depth, gfr, I, seed=0, cx=CX):
    if I <= 0: return
    ph = sdf3d.CAM_PITCH; mw = P.muzzle_world(gfr); fwd = gfr.R @ V(0, 0, 1)
    c0, r0, t0 = proj(mw, cx); du = fwd[0]; dv = fwd[1] * np.cos(ph) + fwd[2] * np.sin(ph); l = np.hypot(du, dv)
    ux, uy = (du / l, -dv / l) if l > 1e-6 else (1.0, 0.0)        # screen axis (col,row)
    Lf = 9.5 * I; Rb = 3.3 * I
    A = max(l * Lf * .55, Rb); B = Rb
    cx_, cy_ = c0 + ux * l * Lf * .42, r0 + uy * l * Lf * .42
    td = t0 + float(fwd @ sdf3d.V(0, -np.sin(ph), np.cos(ph))) * 3
    H, W = alpha.shape
    for y in range(H):
        for x in range(W):
            dx, dy = x + .5 - cx_, y + .5 - cy_; a = dx * ux + dy * uy; b = -dx * uy + dy * ux
            th = np.arctan2(b / B, a / A); mod = 1 + .30 * np.cos(5 * th + seed)
            rr = np.hypot(a / A, b / B) / mod
            if rr > 1: continue
            if alpha[y, x] and depth[y, x] < td - 1.5: continue    # flash hidden behind nearer geometry
            lv = 4 if rr < .30 else 3 if rr < .58 else 2 if rr < .82 else 1
            rgb[y, x] = P.RAMP_RGB[P.M('flash')][lv]; alpha[y, x] = 255

def draw_blood(rgb, alpha, root, body, age, seed, strength=1.0, cx=CX):
    rng = np.random.RandomState(seed); n = int(17 * strength)
    org = body.ap(V(0, 17, 9.5))
    for k in range(n):
        v = root.R @ V(rng.uniform(-2.4, 2.4), rng.uniform(.8, 3.2), -rng.uniform(.6, 3.4)) * 1.7
        pos = org + v * age + V(0, -.5 * age * age * 1.1, 0)
        c, r, _ = proj(pos, cx); x, y = int(round(c)), int(round(r))
        sz = 2 if (age < 2.2 and k % 2 == 0) else 1
        for yy in range(y, y + sz):
            for xx in range(x, x + sz):
                if 0 <= xx < 64 and 0 <= yy < 64 and age < 5: rgb[yy, xx] = P.RAMP_RGB[P.M('blood')][3 if k % 2 else 2]; alpha[yy, xx] = 255

def draw_pool(rgb, alpha, root, size, cen, cx=CX):
    if size <= 0: return None
    ph = sdf3d.CAM_PITCH; H, W = alpha.shape; yy, xx = np.mgrid[0:H, 0:W]
    u = xx + .5 - cx; v = CY - (yy + .5); gx = u; gz = v / np.sin(ph)
    c = root.R @ V(cen[0], 0, cen[1]) + root.t * 0
    ang = np.arctan2(gz - c[2], gx - c[0]); r = np.hypot(gx - c[0], (gz - c[2]) * 1.0)
    rad = (12.5 + 1.2 * np.cos(3 * ang + .7) + .8 * np.cos(5 * ang)) * size
    m = r < rad
    return m, (r < rad * .55)

def render_frame(pose, yaw, shadow=True, seed=0, cx=CX):
    sc, root, body, gfr = P.build(pose, yaw); r = sdf3d.render(sc, want_shadow=shadow, cx=cx, cy=CY)
    rgb, a = P.finish(r, hurt=pose['hurt'])
    im = np.zeros((64, 64, 4), np.uint8)
    if pose.get('pool', 0) > 0:
        res = draw_pool(rgb, a, root, pose['pool'], pose['pool_c'], cx)
        pm, pc = res; pm = pm & (a == 0); pr = pm & ~np.roll(np.roll(pm, 1, 0), 0, 1)
        im[pm, :3] = P.RAMP_RGB[P.M('blood')][2]; im[pm, 3] = 255
        im[pc & pm, :3] = P.RAMP_RGB[P.M('blood')][3]
        edge = pm & ~(np.roll(pm, 1, 0) & np.roll(pm, -1, 0) & np.roll(pm, 1, 1) & np.roll(pm, -1, 1)); im[edge, :3] = P.RAMP_RGB[P.M('blood')][1]
    if shadow:
        sh = r['shadow'] & (a == 0) & (im[..., 3] == 0); im[sh] = P.SHADOW_RGBA
    m = a > 0; im[m, :3] = rgb[m]; im[m, 3] = 255
    rgb2 = im[..., :3].copy(); a2 = im[..., 3].copy()
    if pose['blood']: draw_blood(rgb2, a2, root, body, pose['blood'][0], pose['blood'][1], pose['blood'][2] if len(pose['blood']) > 2 else 1.0, cx)
    draw_flash(rgb2, a2, r['depth'], gfr, pose['flash'], seed, cx)
    im[..., :3] = rgb2; im[..., 3] = a2
    return im
