'use strict';
/* art.js — drawing primitives: textured fills, hatching, ink outlines, cached shadows/glow */

const { createCanvas } = require('@napi-rs/canvas');
const U = require('./util');
const T = require('./textures');

// ---------- ink rectangle with wobbly outline ----------
function inkRect(ctx, x, y, w, h, opts = {}) {
  const {
    fill = null, tex = null, tint = null, tintA = 0.35, hatch = false, hatchColor = '#2f2a24',
    stroke = true, strokeColor = '#2f2a24', strokeW = 2.2, strokeA = 0.85,
    jitter = 0.8, round = 0, inner = true,
  } = opts;
  const j = jitter;
  const p = [
    { x: x - j, y: y - j }, { x: x + w + j, y: y - j },
    { x: x + w + j, y: y + h + j }, { x: x - j, y: y + h + j },
  ];
  ctx.beginPath();
  if (round > 0) {
    const r = Math.min(round, w / 2, h / 2);
    ctx.moveTo(p[0].x + r, p[0].y);
    ctx.lineTo(p[1].x - r, p[1].y); ctx.quadraticCurveTo(p[1].x, p[1].y, p[1].x, p[1].y + r);
    ctx.lineTo(p[1].x, p[2].y - r); ctx.quadraticCurveTo(p[1].x, p[2].y, p[1].x - r, p[2].y);
    ctx.lineTo(p[2].x - r, p[2].y); ctx.quadraticCurveTo(p[2].x, p[2].y, p[2].x, p[2].y - r);
    ctx.lineTo(p[3].x, p[3].y + r); ctx.quadraticCurveTo(p[3].x, p[3].y, p[3].x + r, p[3].y);
    ctx.lineTo(p[0].x, p[0].y + r); ctx.quadraticCurveTo(p[0].x, p[0].y, p[0].x + r, p[0].y);
    ctx.closePath();
  } else {
    ctx.moveTo(p[0].x, p[0].y);
    ctx.lineTo(p[1].x, p[1].y); ctx.lineTo(p[2].x, p[2].y); ctx.lineTo(p[3].x, p[3].y);
    ctx.closePath();
  }
  if (fill || tex) {
    ctx.save();
    if (tex) {
      const pat = ctx.createPattern(tex, 'repeat');
      if (fill) { ctx.fillStyle = fill; ctx.fill(); }
      ctx.globalAlpha = tintA;
      ctx.fillStyle = pat;
      ctx.fill();
      if (tint) {
        ctx.globalAlpha = tintA;
        ctx.fillStyle = tint;
        ctx.globalCompositeOperation = 'multiply';
        ctx.fill();
        ctx.globalCompositeOperation = 'source-over';
      }
    } else if (tint) {
      ctx.fillStyle = fill || tint;
      ctx.fill();
      ctx.globalAlpha = tintA;
      ctx.fillStyle = tint;
      ctx.fill();
    } else {
      ctx.fillStyle = fill; ctx.fill();
    }
    ctx.restore();
  }
  if (hatch) {
    ctx.save();
    ctx.clip();
    ctx.globalAlpha = 0.1;
    ctx.strokeStyle = hatchColor;
    ctx.lineWidth = 1;
    for (let d = -h; d < w + h; d += 7) {
      ctx.beginPath();
      ctx.moveTo(x + d, y);
      ctx.lineTo(x + d - h, y + h);
      ctx.stroke();
    }
    ctx.restore();
  }
  if (stroke) {
    ctx.save();
    ctx.globalAlpha = strokeA;
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = strokeW;
    ctx.lineJoin = 'round';
    ctx.stroke();
    if (inner) {
      ctx.globalAlpha = strokeA * 0.55;
      ctx.strokeStyle = '#fbf6ea';
      ctx.lineWidth = strokeW * 0.42;
      ctx.stroke();
    }
    ctx.restore();
  }
}

// ---------- rounded filled rect helper ----------
function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r); ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

// ---------- cached soft shadow sprites ----------
const shadowCache = {};
function shadow(kind, size = 128) {
  if (shadowCache[kind + size]) return shadowCache[kind + size];
  const cv = createCanvas(size, size);
  const ctx = cv.getContext('2d');
  const grad = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  if (kind === 'contact') {
    grad.addColorStop(0, 'rgba(43,32,20,0.55)');
    grad.addColorStop(0.55, 'rgba(43,32,20,0.3)');
    grad.addColorStop(1, 'rgba(43,32,20,0)');
  } else if (kind === 'soft') {
    grad.addColorStop(0, 'rgba(45,35,24,0.4)');
    grad.addColorStop(0.6, 'rgba(45,35,24,0.16)');
    grad.addColorStop(1, 'rgba(45,35,24,0)');
  } else { // light pool on floor
    grad.addColorStop(0, 'rgba(255,242,205,0.5)');
    grad.addColorStop(0.6, 'rgba(255,242,205,0.18)');
    grad.addColorStop(1, 'rgba(255,242,205,0)');
  }
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, size, size);
  shadowCache[kind + size] = cv;
  return cv;
}

function drawShadow(ctx, x, y, rx, ry, rot = 0, alpha = 1, kind = 'soft') {
  const spr = shadow(kind);
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.translate(x, y);
  ctx.rotate(rot);
  ctx.drawImage(spr, -rx, -ry, rx * 2, ry * 2);
  ctx.restore();
}

// ---------- glow sprites ----------
const glowCache = {};
function glow(kind, size = 128) {
  if (glowCache[kind + size]) return glowCache[kind + size];
  const cv = createCanvas(size, size);
  const ctx = cv.getContext('2d');
  const colors = {
    warm: ['rgba(255,226,160,0.9)', 'rgba(255,210,130,0.35)', 'rgba(255,210,130,0)'],
    cool: ['rgba(190,220,255,0.9)', 'rgba(170,205,245,0.3)', 'rgba(170,205,245,0)'],
    gold: ['rgba(255,220,130,0.9)', 'rgba(230,180,90,0.35)', 'rgba(230,180,90,0)'],
  };
  const c = colors[kind] || colors.warm;
  const g = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  g.addColorStop(0, c[0]); g.addColorStop(0.5, c[1]); g.addColorStop(1, c[2]);
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, size, size);
  glowCache[kind + size] = cv;
  return cv;
}

function drawGlow(ctx, x, y, r, alpha = 1, kind = 'warm') {
  const spr = glow(kind);
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.drawImage(spr, x - r, y - r, r * 2, r * 2);
  ctx.restore();
}

// ---------- light shaft (volumetric window light) ----------
function lightShaft(ctx, x, y, w, h, rot, alpha = 0.14) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.translate(x, y);
  ctx.rotate(rot);
  const g = ctx.createLinearGradient(0, -h / 2, 0, h / 2);
  g.addColorStop(0, 'rgba(255,244,214,0)');
  g.addColorStop(0.35, 'rgba(255,244,214,0.55)');
  g.addColorStop(0.7, 'rgba(255,244,214,0.3)');
  g.addColorStop(1, 'rgba(255,244,214,0)');
  ctx.fillStyle = g;
  ctx.beginPath();
  ctx.moveTo(-w / 2, -h / 2);
  ctx.lineTo(w / 2, -h / 2);
  ctx.lineTo(w * 0.62, h / 2);
  ctx.lineTo(-w * 0.62, h / 2);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

// ---------- simple miniature tree ----------
function tree(ctx, x, y, s, opts = {}) {
  const { season = 'green', seed = 1 } = opts;
  const rng = U.makeRng(seed);
  const trunkC = season === 'autumn' ? '#7a5230' : '#6b4a2e';
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(s, s);
  ctx.strokeStyle = trunkC;
  ctx.lineWidth = 3.2;
  ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, -46); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(0, -26); ctx.lineTo(-13, -40); ctx.moveTo(0, -34); ctx.lineTo(12, -46); ctx.stroke();
  const leafColors = season === 'autumn'
    ? ['#c0683c', '#a85628', '#d17b3e', '#8f4a24'] : ['#5e7a4a', '#6e8a52', '#4d6b3d', '#7d9158'];
  for (let i = 0; i < 9; i++) {
    const a = rng() * U.TAU, r = 14 + rng() * 12, cy = -48 - rng() * 14;
    ctx.fillStyle = leafColors[Math.floor(rng() * leafColors.length)];
    ctx.globalAlpha = 0.92;
    ctx.beginPath();
    ctx.arc(Math.cos(a) * r, cy + Math.sin(a) * r * 0.7, 9 + rng() * 6, 0, U.TAU);
    ctx.fill();
    ctx.strokeStyle = '#3d4a2b'; ctx.lineWidth = 1; ctx.stroke();
  }
  ctx.globalAlpha = 1;
  ctx.restore();
}

// ---------- path helper: rounded rect path (no fill) ----------
function rrPath(ctx, x, y, w, h, r) {
  roundRect(ctx, x, y, w, h, r);
}

module.exports = { inkRect, roundRect, rrPath, drawShadow, drawGlow, lightShaft, tree, shadow, glow };
