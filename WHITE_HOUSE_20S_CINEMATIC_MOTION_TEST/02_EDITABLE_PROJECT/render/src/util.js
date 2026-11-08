'use strict';
/* util.js — math, easing, RNG, noise, curves for the WHITE HOUSE 20s cinematic */

const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
const lerp = (a, b, t) => a + (b - a) * t;
const TAU = Math.PI * 2;
const D2R = Math.PI / 180;

// deterministic seeded RNG (mulberry32)
function makeRng(seed) {
  let s = seed >>> 0;
  return function () {
    s |= 0; s = (s + 0x6D2B79F5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---- easing library ----
const ease = {
  linear: t => t,
  inOutCubic: t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  outCubic: t => 1 - Math.pow(1 - t, 3),
  inCubic: t => t * t * t,
  outQuad: t => 1 - (1 - t) * (1 - t),
  inOutQuad: t => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2),
  outBack: (t, s = 1.70158) => 1 + (s + 1) * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2),
  inOutBack: (t, s = 1.2) => (t < 0.5 ? -0.5 * Math.pow(2 * t, 2) * Math.sin((2 * t - 0.75) * ((2 * s) + 1) * Math.PI / 2)
    : 0.5 * Math.pow(2 * 2 - 2 * t, 2) * Math.sin((2 - 2 * t - 0.75) * ((2 * s) + 1) * Math.PI / 2) + 1),
  outElastic: t => t === 0 ? 0 : t === 1 ? 1 : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * (TAU / 3)) + 1,
  outBounce: t => { const n = 7.5625, d = 2.75; if (t < 1 / d) return n * t * t; if (t < 2 / d) return n * (t -= 1.5 / d) * t + 0.75; if (t < 2.5 / d) return n * (t -= 2.25 / d) * t + 0.9375; return n * (t -= 2.625 / d) * t + 0.984375; },
  smoothstep: t => t * t * (3 - 2 * t),
  softclip: t => t >= 1 ? 1 : t <= 0 ? 0 : t * t * (3 - 2 * t),
};

// cubic bezier evaluator (CSS-style cubic-bezier(x1,y1,x2,y2)) — solve x(t) via Newton, evaluate y
function cubicBezier(x1, y1, x2, y2) {
  const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
  const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
  const fx = t => ((ax * t + bx) * t + cx) * t;
  const fy = t => ((ay * t + by) * t + cy) * t;
  return (x) => {
    if (x <= 0) return 0; if (x >= 1) return 1;
    let t = x;
    for (let i = 0; i < 8; i++) {
      const err = fx(t) - x;
      if (Math.abs(err) < 1e-5) break;
      const d = (3 * ax * t + 2 * bx) * t + cx;
      if (Math.abs(d) < 1e-6) break;
      t -= err / d;
    }
    return fy(t);
  };
}

// ---- keyframe track: array of {t, v} with easing between ----
function kf(track, t, easeFn = ease.inOutCubic) {
  if (!track || !track.length) return 0;
  if (t <= track[0].t) return track[0].v;
  for (let i = 0; i < track.length - 1; i++) {
    const a = track[i], b = track[i + 1];
    if (t <= b.t) {
      const f = clamp((t - a.t) / (b.t - a.t), 0, 1);
      return lerp(a.v, b.v, (a.ease || easeFn)(f));
    }
  }
  return track[track.length - 1].v;
}

// windowed value: 0 outside [a,b], smooth ramps inside
function windowed(t, a, b, easeIn = ease.inOutCubic, easeOut = ease.inOutCubic) {
  if (t <= a || t >= b) return 0;
  if (b <= a) return 1;
  const f1 = clamp((t - a) / 0.12, 0, 1);
  const f2 = clamp((b - t) / 0.12, 0, 1);
  return clamp(Math.min(easeIn(f1), easeOut(f2)), 0, 1);
}

// rise over run with smoothstep edges — for reveal wipes
function wipe(t, a, b) {
  return clamp((t - a) / (b - a), 0, 1);
}

// ---- 2D value noise (seeded, periodic) for hand-drawn wobble + textures ----
function makeNoise2(seed, period = 256) {
  const rng = makeRng(seed);
  const grid = new Float32Array(period * period);
  for (let i = 0; i < grid.length; i++) grid[i] = rng();
  const at = (x, y) => grid[((y % period) + period) % period * period + ((x % period) + period) % period];
  const sm = t => t * t * (3 - 2 * t);
  return (x, y) => {
    const xi = Math.floor(x), yi = Math.floor(y);
    const fx = sm(x - xi), fy = sm(y - yi);
    const v00 = at(xi, yi), v10 = at(xi + 1, yi), v01 = at(xi, yi + 1), v11 = at(xi + 1, yi + 1);
    return lerp(lerp(v00, v10, fx), lerp(v01, v11, fx), fy);
  };
}

// fBm fractal noise
function makeFbm(seed, oct = 5) {
  const n = makeNoise2(seed);
  return (x, y, lacunarity = 2, gain = 0.5) => {
    let amp = 1, freq = 1, sum = 0, norm = 0;
    for (let i = 0; i < oct; i++) {
      sum += amp * n(x * freq, y * freq);
      norm += amp;
      amp *= gain; freq *= lacunarity;
    }
    return sum / norm;
  };
}

// jittered polyline: stable hand-drawn wobble (jitter cached per index)
function makeWobble(points, seed, amp) {
  const rng = makeRng(seed);
  return points.map(p => ({ x: p.x + (rng() - 0.5) * 2 * amp, y: p.y + (rng() - 0.5) * 2 * amp }));
}

// draw a wobbly polyline (ink pass)
function strokePath(ctx, pts, opts = {}) {
  const {
    color = '#2f2a24', width = 2.5, alpha = 0.9, jitterAmp = 0,
    inner = true, innerColor = null, innerAlpha = 0.5, innerWidth = 0.45, round = true,
  } = opts;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.lineJoin = round ? 'round' : 'miter';
  ctx.lineCap = round ? 'round' : 'butt';
  ctx.beginPath();
  const j = jitterAmp ? makeWobble(pts, 9173 + Math.floor(jitterAmp * 100), jitterAmp) : pts;
  ctx.moveTo(j[0].x, j[0].y);
  for (let i = 1; i < j.length; i++) ctx.lineTo(j[i].x, j[i].y);
  ctx.stroke();
  if (inner) {
    ctx.globalAlpha = alpha * innerAlpha;
    ctx.strokeStyle = innerColor || '#ffffff';
    ctx.lineWidth = width * innerWidth;
    ctx.beginPath();
    ctx.moveTo(j[0].x, j[0].y);
    for (let i = 1; i < j.length; i++) ctx.lineTo(j[i].x, j[i].y);
    ctx.stroke();
  }
  ctx.restore();
}

// smooth bezier stroke through points (Catmull-Rom -> bezier)
function strokeSmooth(ctx, pts, opts = {}) {
  const { color = '#2f2a24', width = 2.5, alpha = 0.9, inner = true, innerColor = null, innerAlpha = 0.5, innerWidth = 0.45 } = opts;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  ctx.beginPath();
  if (pts.length < 2) { ctx.restore(); return; }
  ctx.moveTo(pts[0].x, pts[0].y);
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(i - 1, 0)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(i + 2, pts.length - 1)];
    const c1x = p1.x + (p2.x - p0.x) / 6, c1y = p1.y + (p2.y - p0.y) / 6;
    const c2x = p2.x - (p3.x - p1.x) / 6, c2y = p2.y - (p3.y - p1.y) / 6;
    ctx.bezierCurveTo(c1x, c1y, c2x, c2y, p2.x, p2.y);
  }
  ctx.stroke();
  if (inner) {
    ctx.globalAlpha = alpha * innerAlpha;
    ctx.strokeStyle = innerColor || '#ffffff';
    ctx.lineWidth = width * innerWidth;
    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[Math.max(i - 1, 0)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(i + 2, pts.length - 1)];
      const c1x = p1.x + (p2.x - p0.x) / 6, c1y = p1.y + (p2.y - p0.y) / 6;
      const c2x = p2.x - (p3.x - p1.x) / 6, c2y = p2.y - (p3.y - p1.y) / 6;
      ctx.bezierCurveTo(c1x, c1y, c2x, c2y, p2.x, p2.y);
    }
    ctx.stroke();
  }
  ctx.restore();
}

module.exports = {
  clamp, lerp, TAU, D2R, makeRng, ease, cubicBezier, kf, windowed, wipe,
  makeNoise2, makeFbm, makeWobble, strokePath, strokeSmooth,
};
