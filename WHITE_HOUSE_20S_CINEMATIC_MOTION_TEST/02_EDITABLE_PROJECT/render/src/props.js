'use strict';
/* props.js — furniture & object library.
   Each draw(ctx, x, y, s, opts): (x,y) = ground contact point, s = scale (px at s=1 defined per prop),
   draws upward from (x,y). opts: {rot, alpha, phase, glowT, woodTex, seatTex...} */

const U = require('./util');
const A = require('./art');
const T = require('./textures');

const INK = '#2f2a24';

// ============ CHAIR (3/4 front, executive) ============
function chair(ctx, x, y, s, o = {}) {
  const w = 46 * s, h = 84 * s; // footprint, height
  ctx.save();
  ctx.translate(x, y);
  if (o.rot) ctx.rotate(o.rot * U.D2R);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  A.drawShadow(ctx, 0, 3 * s, w * 0.62, w * 0.22, 0, 0.34 * (o.shadowA ?? 1), 'soft');
  const woodT = o.woodTex !== false ? T.T.woodDark() : null;
  // legs
  ctx.strokeStyle = '#5b3c22';
  ctx.lineWidth = 3 * s; ctx.lineCap = 'round';
  for (const [lx, ly] of [[-w * 0.34, -6], [w * 0.34, -6]]) {
    ctx.beginPath(); ctx.moveTo(lx, -6 * s); ctx.lineTo(lx * 0.96, -34 * s); ctx.stroke();
  }
  ctx.beginPath(); ctx.moveTo(-w * 0.34, -30 * s); ctx.lineTo(w * 0.34, -30 * s); ctx.stroke();
  // seat
  A.inkRect(ctx, -w / 2, -40 * s, w, 16 * s, {
    fill: o.seatColor || '#9a7b4a', tex: T.T.velvetGold(), tint: o.seatColor || null, tintA: 0.4,
    strokeW: 2.4 * s, strokeA: 0.8, jitter: 0.5 * s, round: 3 * s,
  });
  // back
  A.inkRect(ctx, -w / 2, -h, w, 30 * s, {
    fill: o.seatColor || '#9a7b4a', tex: T.T.velvetGold(), tint: o.seatColor || null, tintA: 0.4,
    strokeW: 2.4 * s, strokeA: 0.8, jitter: 0.5 * s, round: 6 * s,
  });
  // back splat
  A.inkRect(ctx, -w * 0.26, -h + 4 * s, w * 0.52, 22 * s, {
    fill: '#7d5f33', strokeW: 1.8 * s, strokeA: 0.6, round: 4 * s, inner: false,
  });
  // arms
  ctx.strokeStyle = '#6b4a2e';
  ctx.lineWidth = 4 * s;
  ctx.beginPath(); ctx.moveTo(-w / 2, -36 * s); ctx.quadraticCurveTo(-w / 2 - 5 * s, -30 * s, -w / 2 - 3 * s, -20 * s); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(w / 2, -36 * s); ctx.quadraticCurveTo(w / 2 + 5 * s, -30 * s, w / 2 + 3 * s, -20 * s); ctx.stroke();
  ctx.restore();
}

// ============ DESK (presidential / Resolute style) ============
function desk(ctx, x, y, s, o = {}) {
  const w = 150 * s, h = 78 * s;
  ctx.save();
  ctx.translate(x, y);
  if (o.rot) ctx.rotate(o.rot * U.D2R);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  A.drawShadow(ctx, 0, 4 * s, w * 0.58, w * 0.2, 0, 0.36, 'soft');
  const wt = T.T.woodLight();
  // body with drawers
  A.inkRect(ctx, -w / 2, -h, w, h - 14 * s, {
    fill: '#b07f4d', tex: wt, tint: '#a06a3e', tintA: 0.5, hatch: true,
    strokeW: 2.6 * s, strokeA: 0.85, jitter: 0.7 * s,
  });
  // drawer fronts
  for (let i = 0; i < 3; i++) {
    A.inkRect(ctx, -w * 0.42 + i * (w * 0.31), -h + 8 * s, w * 0.26, 18 * s, {
      fill: '#c08a52', tex: wt, strokeW: 1.8 * s, strokeA: 0.7, jitter: 0.5 * s, round: 2 * s,
    });
    ctx.fillStyle = '#e8c98a';
    ctx.beginPath(); ctx.arc(-w * 0.29 + i * (w * 0.31) + w * 0.13, -h + 17 * s, 2.4 * s, 0, U.TAU); ctx.fill();
  }
  // legs (bun feet)
  ctx.strokeStyle = '#6e4a2a';
  ctx.lineWidth = 3.4 * s;
  for (const lx of [-w * 0.44, w * 0.44]) {
    ctx.beginPath(); ctx.moveTo(lx, -16 * s); ctx.quadraticCurveTo(lx * 1.12, -20 * s, lx * 1.14, -30 * s); ctx.stroke();
  }
  // top slab
  A.inkRect(ctx, -w * 0.52, -h - 10 * s, w * 1.04, 12 * s, {
    fill: '#c9955e', tex: wt, strokeW: 2.6 * s, strokeA: 0.85, jitter: 0.7 * s,
  });
  // items on top: papers, phone, book, pen holder
  A.inkRect(ctx, -w * 0.3, -h - 9 * s, 30 * s, 7 * s, { fill: '#f2ecdc', strokeW: 1.4 * s, strokeA: 0.7, jitter: 0.4 * s });
  A.inkRect(ctx, -w * 0.3 + 33 * s, -h - 9 * s, 26 * s, 7 * s, { fill: '#ece2c8', strokeW: 1.4 * s, strokeA: 0.7, jitter: 0.4 * s });
  A.inkRect(ctx, w * 0.2, -h - 11 * s, 16 * s, 12 * s, { fill: '#26323e', strokeW: 1.3 * s, strokeA: 0.6, jitter: 0.4 * s, round: 2 * s });
  ctx.fillStyle = '#9fd0f5';
  ctx.fillRect(w * 0.22, -h - 9.5 * s, 12 * s, 5 * s);
  // book standing
  ctx.save();
  ctx.translate(w * 0.34, -h - 2 * s);
  ctx.fillStyle = '#7a3b2e';
  A.inkRect(ctx, -8 * s, -22 * s, 16 * s, 22 * s, { fill: '#7a3b2e', strokeW: 1.4 * s, strokeA: 0.7, jitter: 0.4 * s });
  ctx.fillStyle = '#f0e3c4';
  ctx.fillRect(-8 * s, -19 * s, 16 * s, 2 * s);
  ctx.restore();
  // flag on right (simple striped)
  if (o.flag !== false) {
    ctx.save();
    ctx.translate(w * 0.52, -h - 8 * s);
    ctx.strokeStyle = '#5b3c22'; ctx.lineWidth = 2.2 * s;
    ctx.beginPath(); ctx.moveTo(0, -30 * s); ctx.lineTo(0, 6 * s); ctx.stroke();
    const fw = 24 * s, fh = 16 * s;
    ctx.fillStyle = '#2f4a7a';
    A.inkRect(ctx, 0, -28 * s, fw, fh, { fill: '#2f4a7a', strokeW: 1.2 * s, strokeA: 0.6, jitter: 0.4 * s, inner: false });
    ctx.fillStyle = '#e8e8e8';
    for (let i = 0; i < 5; i++) ctx.fillRect(0, -28 * s + i * (fh / 5), fw, fh / 10);
    ctx.restore();
  }
  ctx.restore();
}

// ============ SOFA ============
function sofa(ctx, x, y, s, o = {}) {
  const w = 130 * s, h = 52 * s;
  ctx.save();
  ctx.translate(x, y);
  if (o.rot) ctx.rotate(o.rot * U.D2R);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  A.drawShadow(ctx, 0, 3 * s, w * 0.55, w * 0.18, 0, 0.34, 'soft');
  const col = o.color || '#7c3b32';
  A.inkRect(ctx, -w / 2, -h, w, h - 10 * s, {
    fill: col, tex: T.T.velvetRed(), tint: col, tintA: 0.45, strokeW: 2.6 * s, strokeA: 0.8, jitter: 0.6 * s, round: 8 * s,
  });
  // back + arms
  A.inkRect(ctx, -w / 2, -h - 18 * s, w, 20 * s, {
    fill: col, tex: T.T.velvetRed(), tint: col, tintA: 0.4, strokeW: 2.6 * s, strokeA: 0.8, jitter: 0.6 * s, round: 8 * s,
  });
  A.inkRect(ctx, -w / 2, -h - 4 * s, 14 * s, h * 0.7, { fill: col, strokeW: 2.2 * s, strokeA: 0.7, round: 6 * s, jitter: 0.5 * s });
  A.inkRect(ctx, w / 2 - 14 * s, -h - 4 * s, 14 * s, h * 0.7, { fill: col, strokeW: 2.2 * s, strokeA: 0.7, round: 6 * s, jitter: 0.5 * s });
  // cushions seams
  ctx.strokeStyle = 'rgba(0,0,0,0.18)';
  ctx.lineWidth = 1.2 * s;
  for (const sx of [-w * 0.18, w * 0.18]) {
    ctx.beginPath(); ctx.moveTo(sx, -h + 8 * s); ctx.lineTo(sx, -10 * s); ctx.stroke();
  }
  // legs
  ctx.strokeStyle = '#6b4a2e'; ctx.lineWidth = 3 * s;
  for (const lx of [-w * 0.42, -w * 0.16, w * 0.16, w * 0.42]) {
    ctx.beginPath(); ctx.moveTo(lx, -8 * s); ctx.lineTo(lx, -2 * s); ctx.stroke();
  }
  // pillows
  if (o.pillows !== false) {
    A.inkRect(ctx, -w * 0.34, -h - 26 * s, 30 * s, 22 * s, { fill: '#e9dcc2', strokeW: 1.8 * s, strokeA: 0.7, round: 8 * s, jitter: 0.5 * s });
    A.inkRect(ctx, w * 0.04, -h - 26 * s, 30 * s, 22 * s, { fill: '#3e5f7e', strokeW: 1.8 * s, strokeA: 0.7, round: 8 * s, jitter: 0.5 * s });
  }
  ctx.restore();
}

// ============ TABLE (conference / dining, drawn 3/4) ============
function table(ctx, x, y, s, o = {}) {
  const w = o.w || 190 * s, d = o.d || 90 * s; // width, depth-extent
  ctx.save();
  ctx.translate(x, y);
  if (o.rot) ctx.rotate(o.rot * U.D2R);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  A.drawShadow(ctx, 0, 5 * s, w * 0.55, d * 0.42, 0, 0.36, 'soft');
  const wt = T.T.woodLight();
  // tabletop (3/4: front edge + top surface)
  const topY = -62 * s;
  A.inkRect(ctx, -w / 2, topY - 12 * s, w, 14 * s, {
    fill: '#c9955e', tex: wt, strokeW: 2.6 * s, strokeA: 0.85, jitter: 0.7 * s,
  });
  // front apron
  A.inkRect(ctx, -w / 2, topY, w, 10 * s, {
    fill: '#a06a3e', tex: T.T.woodDark(), strokeW: 2.2 * s, strokeA: 0.75, jitter: 0.6 * s,
  });
  // top surface (lighter slab, receding up-left toward far edge)
  ctx.fillStyle = '#d9a868';
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(-w / 2, topY - 12 * s);
  ctx.lineTo(w / 2, topY - 12 * s);
  ctx.lineTo(w / 2 - d * 0.16, topY - 20 * s);
  ctx.lineTo(-w / 2 - d * 0.16, topY - 20 * s);
  ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = INK; ctx.lineWidth = 2.6 * s; ctx.globalAlpha = 0.85;
  ctx.stroke();
  ctx.restore();
  // legs
  ctx.strokeStyle = '#6e4a2a';
  ctx.lineWidth = 3.4 * s;
  for (const lx of [-w * 0.42, w * 0.42]) {
    ctx.beginPath(); ctx.moveTo(lx, topY + 6 * s); ctx.lineTo(lx * 0.98, -4 * s); ctx.stroke();
  }
  ctx.restore();
}

// ============ DINING TABLE with settings ============
function diningTable(ctx, x, y, s, o = {}) {
  table(ctx, x, y, s, { w: (o.w || 220) * s, d: 80 * s, rot: o.rot });
  ctx.save();
  ctx.translate(x, y);
  if (o.rot) ctx.rotate(o.rot * U.D2R);
  // centerpiece: flowers
  const cx = 0, cy = -58 * s;
  A.inkRect(ctx, cx - 12 * s, cy - 14 * s, 24 * s, 16 * s, { fill: '#b8c9a8', strokeW: 1.6 * s, strokeA: 0.7, round: 3 * s, jitter: 0.4 * s });
  for (let i = 0; i < 5; i++) {
    const a = i * (U.TAU / 5) + 0.4;
    ctx.fillStyle = i % 2 ? '#c0683c' : '#e0b44c';
    ctx.beginPath();
    ctx.ellipse(cx + Math.cos(a) * 9 * s, cy - 18 * s + Math.sin(a) * 5 * s, 5 * s, 7 * s, a, 0, U.TAU);
    ctx.fill();
    ctx.strokeStyle = '#8a5a2a'; ctx.lineWidth = 1.4 * s; ctx.stroke();
  }
  // plates along the table
  for (let i = -2; i <= 2; i++) {
    const px = i * 40 * s;
    ctx.fillStyle = '#f4efe4';
    ctx.beginPath(); ctx.ellipse(px, -56 * s, 9 * s, 5 * s, 0, 0, U.TAU); ctx.fill();
    ctx.strokeStyle = '#cbb98e'; ctx.lineWidth = 1.1 * s; ctx.stroke();
    ctx.fillStyle = '#e6d9b8';
    ctx.beginPath(); ctx.ellipse(px, -56 * s, 3.4 * s, 2 * s, 0, 0, U.TAU); ctx.fill();
  }
  // candle holders at ends
  for (const ex of [-96 * s, 96 * s]) {
    ctx.strokeStyle = '#9a7b3a'; ctx.lineWidth = 2.4 * s;
    ctx.beginPath(); ctx.moveTo(ex, -54 * s); ctx.lineTo(ex, -70 * s); ctx.stroke();
    A.drawGlow(ctx, ex, -74 * s, 10 * s, 0.85 + 0.15 * Math.sin((o.t || 0) * 3), 'gold');
    ctx.fillStyle = '#ffd98a';
    ctx.beginPath(); ctx.ellipse(ex, -72 * s, 2.6 * s, 4 * s, 0, 0, U.TAU); ctx.fill();
  }
  ctx.restore();
}

// ============ SIDEBOARD (dining room) ============
function sideboard(ctx, x, y, s, o = {}) {
  const w = 120 * s, h = 76 * s;
  ctx.save();
  ctx.translate(x, y);
  if (o.rot) ctx.rotate(o.rot * U.D2R);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  A.drawShadow(ctx, 0, 4 * s, w * 0.5, w * 0.18, 0, 0.34, 'soft');
  const wt = T.T.woodWalnut();
  A.inkRect(ctx, -w / 2, -h, w, h - 16 * s, {
    fill: '#7d5430', tex: wt, tint: '#6b4622', tintA: 0.5, hatch: true,
    strokeW: 2.6 * s, strokeA: 0.85, jitter: 0.6 * s,
  });
  for (let i = 0; i < 2; i++) {
    A.inkRect(ctx, -w * 0.42 + i * (w * 0.5), -h + 10 * s, w * 0.36, 16 * s, {
      fill: '#8a5a33', strokeW: 1.7 * s, strokeA: 0.65, jitter: 0.4 * s, round: 2 * s,
    });
    ctx.strokeStyle = '#c9a227'; ctx.lineWidth = 1.8 * s;
    ctx.beginPath(); ctx.moveTo(-w * 0.24 + i * (w * 0.5), -h + 18 * s); ctx.lineTo(w * 0.24 - i * (w * 0.5), -h + 18 * s); ctx.stroke();
  }
  // legs
  ctx.strokeStyle = '#5b3c22'; ctx.lineWidth = 3 * s;
  for (const lx of [-w * 0.42, w * 0.42]) {
    ctx.beginPath(); ctx.moveTo(lx, -14 * s); ctx.lineTo(lx * 0.98, -2 * s); ctx.stroke();
  }
  // top with candelabra + plates
  A.inkRect(ctx, -w * 0.52, -h - 10 * s, w * 1.04, 11 * s, { fill: '#96663a', strokeW: 2.4 * s, strokeA: 0.8, jitter: 0.6 * s });
  for (let i = 0; i < 3; i++) {
    const ex = -26 * s + i * 26 * s;
    ctx.strokeStyle = '#c9a227'; ctx.lineWidth = 2.2 * s;
    ctx.beginPath(); ctx.moveTo(ex, -h - 9 * s); ctx.lineTo(ex, -h - 34 * s); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(ex - 6 * s, -h - 20 * s); ctx.quadraticCurveTo(ex, -h - 24 * s, ex + 6 * s, -h - 20 * s); ctx.stroke();
    A.drawGlow(ctx, ex, -h - 38 * s, 9 * s, 0.8 + 0.2 * Math.sin((o.t || 0) * 3 + i), 'gold');
    ctx.fillStyle = '#ffd98a';
    ctx.beginPath(); ctx.ellipse(ex, -h - 36 * s, 2.4 * s, 3.6 * s, 0, 0, U.TAU); ctx.fill();
  }
  ctx.restore();
}

// ============ BOOKSHELF ============
function bookshelf(ctx, x, y, s, o = {}) {
  const w = 92 * s, h = 150 * s;
  ctx.save();
  ctx.translate(x, y);
  if (o.rot) ctx.rotate(o.rot * U.D2R);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  A.drawShadow(ctx, 0, 4 * s, w * 0.55, w * 0.2, 0, 0.32, 'soft');
  A.inkRect(ctx, -w / 2, -h, w, h, {
    fill: '#8a5a33', tex: T.T.woodDark(), strokeW: 3 * s, strokeA: 0.85, jitter: 0.7 * s,
  });
  const rng = U.makeRng(o.seed || 5);
  const bookCols = ['#7a3b2e', '#2f4a7a', '#4a6b4f', '#8f3a30', '#9a7b3a', '#3e5f7e', '#5c3a6e', '#6b4a2e'];
  const shelves = 4;
  for (let sh = 0; sh < shelves; sh++) {
    const sy = -h + 12 * s + sh * ((h - 20 * s) / shelves);
    A.inkRect(ctx, -w * 0.46, sy, w * 0.92, 5 * s, { fill: '#6b4622', strokeW: 1.6 * s, strokeA: 0.6, jitter: 0.4 * s });
    let bx = -w * 0.44;
    while (bx < w * 0.42) {
      const bw = (6 + rng() * 9) * s, bh = (16 + rng() * 12) * s;
      const col = bookCols[Math.floor(rng() * bookCols.length)];
      A.inkRect(ctx, bx, sy - bh, bw, bh, { fill: col, strokeW: 1.3 * s, strokeA: 0.6, jitter: 0.35 * s });
      ctx.fillStyle = 'rgba(255,240,200,0.5)';
      ctx.fillRect(bx + 1.5 * s, sy - bh + 3 * s, bw - 3 * s, 2 * s);
      bx += bw + 1.5 * s;
    }
  }
  ctx.restore();
}

// ============ TABLE LAMP ============
function lamp(ctx, x, y, s, o = {}) {
  ctx.save();
  ctx.translate(x, y);
  if (o.rot) ctx.rotate(o.rot * U.D2R);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  A.drawGlow(ctx, 0, -64 * s, 42 * s, 0.35 + 0.08 * Math.sin((o.t || 0) * 2), 'warm');
  A.drawShadow(ctx, 0, 2 * s, 16 * s, 7 * s, 0, 0.3, 'soft');
  // base
  ctx.fillStyle = '#5b3c22';
  A.inkRect(ctx, -12 * s, -10 * s, 24 * s, 10 * s, { fill: '#5b3c22', strokeW: 2 * s, strokeA: 0.8, jitter: 0.4 * s, round: 3 * s });
  // stem
  ctx.strokeStyle = '#8a6a3a'; ctx.lineWidth = 3.4 * s;
  ctx.beginPath(); ctx.moveTo(0, -10 * s); ctx.lineTo(0, -56 * s); ctx.stroke();
  // shade (trapezoid)
  ctx.beginPath();
  ctx.moveTo(-20 * s, -56 * s);
  ctx.lineTo(20 * s, -56 * s);
  ctx.lineTo(14 * s, -76 * s);
  ctx.lineTo(-14 * s, -76 * s);
  ctx.closePath();
  ctx.fillStyle = '#d9c08a';
  ctx.fill();
  ctx.strokeStyle = INK; ctx.lineWidth = 2.2 * s; ctx.globalAlpha = 0.85; ctx.stroke();
  ctx.globalAlpha = 0.35;
  ctx.strokeStyle = '#fff6dd'; ctx.lineWidth = 1.4 * s; ctx.stroke();
  ctx.globalAlpha = o.alpha !== undefined ? o.alpha : 1;
  // bulb glow
  A.drawGlow(ctx, 0, -66 * s, 12 * s, 0.9, 'warm');
  ctx.restore();
}

// ============ CHANDELIER ============
function chandelier(ctx, x, y, s, o = {}) {
  // y = ceiling attachment point
  ctx.save();
  ctx.translate(x, y);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  // chain
  ctx.strokeStyle = '#8a6a3a'; ctx.lineWidth = 2 * s;
  ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 18 * s); ctx.stroke();
  // body
  ctx.strokeStyle = '#c9a227'; ctx.lineWidth = 3 * s;
  ctx.beginPath(); ctx.ellipse(0, 26 * s, 46 * s, 12 * s, 0, 0, Math.PI); ctx.stroke();
  ctx.beginPath(); ctx.ellipse(0, 26 * s, 46 * s, 12 * s, 0, Math.PI, U.TAU); ctx.stroke();
  // arms + candles
  const arms = 6;
  for (let i = 0; i < arms; i++) {
    const a = (i / arms) * U.TAU;
    const ax = Math.cos(a) * 40 * s, ay = 26 * s + Math.sin(a) * 10 * s;
    ctx.beginPath(); ctx.moveTo(0, 26 * s); ctx.quadraticCurveTo(ax * 0.5, 20 * s, ax, ay); ctx.stroke();
    ctx.strokeStyle = '#b8912a'; ctx.lineWidth = 2 * s;
    ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(ax, ay + 12 * s); ctx.stroke();
    A.drawGlow(ctx, ax, ay + 16 * s, 11 * s, 0.85 + 0.15 * Math.sin((o.t || 0) * 4 + i), 'gold');
    ctx.fillStyle = '#ffd98a';
    ctx.beginPath(); ctx.ellipse(ax, ay + 14 * s, 2.6 * s, 4 * s, 0, 0, U.TAU); ctx.fill();
  }
  // central crystals
  A.drawGlow(ctx, 0, 34 * s, 14 * s, 0.6, 'gold');
  ctx.restore();
}

// ============ RUG (oval, blue with medallion) ============
function rug(ctx, x, y, s, o = {}) {
  const rx = (o.rx || 110) * s, ry = (o.ry || 62) * s;
  ctx.save();
  ctx.translate(x, y);
  if (o.rot) ctx.rotate(o.rot * U.D2R);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  // shadow under rug edge
  A.drawShadow(ctx, 0, 2 * s, rx * 1.05, ry * 1.05, 0, 0.22, 'contact');
  ctx.beginPath();
  ctx.ellipse(0, 0, rx, ry, 0, 0, U.TAU);
  const g = ctx.createRadialGradient(0, 0, ry * 0.2, 0, 0, rx);
  g.addColorStop(0, '#41618c');
  g.addColorStop(0.75, '#2f4a72');
  g.addColorStop(1, '#27405c');
  ctx.fillStyle = g;
  ctx.fill();
  ctx.strokeStyle = '#c9a227'; ctx.lineWidth = 3 * s;
  ctx.stroke();
  // gold border ring
  ctx.beginPath(); ctx.ellipse(0, 0, rx * 0.86, ry * 0.86, 0, 0, U.TAU);
  ctx.strokeStyle = '#d8b64a'; ctx.lineWidth = 2.4 * s; ctx.stroke();
  // medallion
  ctx.beginPath(); ctx.ellipse(0, -ry * 0.12, rx * 0.34, ry * 0.4, 0, 0, U.TAU);
  ctx.fillStyle = '#e8d9b0'; ctx.fill();
  ctx.strokeStyle = '#b8862c'; ctx.lineWidth = 2.2 * s; ctx.stroke();
  ctx.beginPath(); ctx.ellipse(0, -ry * 0.12, rx * 0.18, ry * 0.22, 0, 0, U.TAU);
  ctx.fillStyle = '#2f4a72'; ctx.fill();
  ctx.strokeStyle = '#d8b64a'; ctx.lineWidth = 1.8 * s; ctx.stroke();
  // star points at ends
  for (const sx of [-rx * 0.62, rx * 0.62]) {
    ctx.fillStyle = '#e8d9b0';
    ctx.beginPath();
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * U.TAU;
      const rr = i % 2 ? rx * 0.06 : rx * 0.11;
      ctx.lineTo(sx + Math.cos(a) * rr, -ry * 0.12 + Math.sin(a) * rr * 0.7);
    }
    ctx.closePath(); ctx.fill();
  }
  ctx.restore();
}

// ============ PAINTING (framed abstract landscape) ============
function painting(ctx, x, y, s, o = {}) {
  const w = (o.w || 70) * s, h = (o.h || 54) * s;
  ctx.save();
  ctx.translate(x, y);
  if (o.rot) ctx.rotate(o.rot * U.D2R);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  const fy = -h * 0.55;
  // frame
  A.inkRect(ctx, -w / 2, fy, w, h, {
    fill: '#c9a227', strokeW: 3 * s, strokeA: 0.9, jitter: 0.6 * s, inner: false,
  });
  A.inkRect(ctx, -w * 0.44, fy + h * 0.1, w * 0.88, h * 0.8, { fill: '#f0e6cf', strokeW: 1.6 * s, strokeA: 0.6, jitter: 0.4 * s, inner: false });
  // mini landscape
  const sky = ['#cfe0ec', '#e6d8c0', '#8fa8c4'];
  ctx.fillStyle = sky[o.skyIdx || 0];
  ctx.fillRect(-w * 0.42, fy + h * 0.12, w * 0.84, h * 0.42);
  ctx.fillStyle = o.landColor || '#6e8a5a';
  ctx.beginPath();
  ctx.moveTo(-w * 0.42, fy + h * 0.55);
  ctx.quadraticCurveTo(-w * 0.2, fy + h * 0.38, 0, fy + h * 0.48);
  ctx.quadraticCurveTo(w * 0.22, fy + h * 0.4, w * 0.42, fy + h * 0.55);
  ctx.lineTo(w * 0.42, fy + h * 0.9);
  ctx.lineTo(-w * 0.42, fy + h * 0.9);
  ctx.closePath();
  ctx.fill();
  // sun/moon
  ctx.fillStyle = o.skyIdx === 1 ? '#e8b94c' : '#f4e8c8';
  ctx.beginPath(); ctx.arc(w * 0.2, fy + h * 0.26, w * 0.07, 0, U.TAU); ctx.fill();
  ctx.restore();
}

// ============ PORTRAIT (dark framed bust) ============
function portrait(ctx, x, y, s, o = {}) {
  const w = (o.w || 56) * s, h = (o.h || 74) * s;
  ctx.save();
  ctx.translate(x, y);
  if (o.rot) ctx.rotate(o.rot * U.D2R);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  const fy = -h;
  A.inkRect(ctx, -w / 2, fy, w, h, { fill: '#3a2f22', strokeW: 3 * s, strokeA: 0.9, jitter: 0.6 * s, inner: false });
  A.inkRect(ctx, -w * 0.42, fy + h * 0.12, w * 0.84, h * 0.76, { fill: '#e8dec8', strokeW: 1.6 * s, strokeA: 0.5, jitter: 0.4 * s, inner: false });
  // bust silhouette
  ctx.fillStyle = '#4a5560';
  ctx.beginPath(); ctx.ellipse(0, fy + h * 0.42, w * 0.2, h * 0.24, 0, 0, U.TAU); ctx.fill();
  ctx.beginPath();
  ctx.moveTo(-w * 0.3, fy + h * 0.62);
  ctx.quadraticCurveTo(-w * 0.2, fy + h * 0.5, 0, fy + h * 0.52);
  ctx.quadraticCurveTo(w * 0.2, fy + h * 0.5, w * 0.3, fy + h * 0.62);
  ctx.closePath(); ctx.fill();
  ctx.restore();
}

// ============ CURTAINS / DRAPES (pleated, floor to ceiling) ============
function drapes(ctx, x, y, s, o = {}) {
  const w = (o.w || 90) * s, h = (o.h || 200) * s;
  ctx.save();
  ctx.translate(x, y);
  if (o.rot) ctx.rotate(o.rot * U.D2R);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  const col = o.color || '#8f3a30';
  A.inkRect(ctx, -w / 2, -h, w, h, {
    fill: col, tex: T.T.velvetRed(), tint: col, tintA: 0.5, strokeW: 2.4 * s, strokeA: 0.7, jitter: 0.6 * s, inner: false,
  });
  // pleats
  ctx.save();
  ctx.clip();
  ctx.globalAlpha = 0.5;
  for (let i = 0; i <= 6; i++) {
    const px = -w / 2 + (w / 6) * i + w / 12;
    ctx.fillStyle = 'rgba(255,240,220,0.10)';
    ctx.fillRect(px - w * 0.03, -h, w * 0.06, h);
    ctx.fillStyle = 'rgba(0,0,0,0.14)';
    ctx.fillRect(px + w * 0.03, -h, w * 0.06, h);
  }
  ctx.restore();
  // bottom swag
  ctx.fillStyle = col;
  ctx.beginPath();
  ctx.moveTo(-w / 2, -4 * s);
  ctx.quadraticCurveTo(-w * 0.25, 18 * s, 0, 4 * s);
  ctx.quadraticCurveTo(w * 0.25, 18 * s, w / 2, -4 * s);
  ctx.quadraticCurveTo(w * 0.25, 8 * s, 0, -2 * s);
  ctx.quadraticCurveTo(-w * 0.25, 8 * s, -w / 2, -4 * s);
  ctx.fill();
  ctx.strokeStyle = '#5c241c'; ctx.lineWidth = 1.8 * s; ctx.stroke();
  ctx.restore();
}

// ============ FIREPLACE (with fire glow) ============
function fireplace(ctx, x, y, s, o = {}) {
  const w = (o.w || 130) * s, h = (o.h || 150) * s;
  ctx.save();
  ctx.translate(x, y);
  if (o.rot) ctx.rotate(o.rot * U.D2R);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  A.drawShadow(ctx, 0, 3 * s, w * 0.55, w * 0.2, 0, 0.3, 'soft');
  const ft = T.T.woodWalnut();
  A.inkRect(ctx, -w / 2, -h, w, h - 40 * s, {
    fill: '#7d5430', tex: ft, tint: '#6b4622', tintA: 0.5, strokeW: 2.8 * s, strokeA: 0.85, jitter: 0.7 * s,
  });
  // mantel
  A.inkRect(ctx, -w * 0.62, -h - 14 * s, w * 1.24, 16 * s, {
    fill: '#8a5a33', tex: ft, strokeW: 2.8 * s, strokeA: 0.85, jitter: 0.7 * s,
  });
  // firebox opening
  ctx.fillStyle = '#2b2018';
  A.inkRect(ctx, -w * 0.3, -h + 40 * s, w * 0.6, h * 0.4, { fill: '#2b2018', strokeW: 2.4 * s, strokeA: 0.8, jitter: 0.5 * s, round: 6 * s, inner: false });
  // fire glow + flames
  const pulse = 0.85 + 0.15 * Math.sin((o.t || 0) * 5);
  A.drawGlow(ctx, 0, -h + 60 * s, 40 * s, 0.5 * pulse, 'warm');
  ctx.fillStyle = '#e8622c';
  for (let i = 0; i < 4; i++) {
    const fx = -w * 0.14 + i * (w * 0.09);
    const fh = (18 + 10 * Math.sin((o.t || 0) * 6 + i * 1.7)) * s;
    ctx.beginPath();
    ctx.moveTo(fx - 8 * s, -h + 78 * s);
    ctx.quadraticCurveTo(fx, -h + 78 * s - fh, fx + 8 * s, -h + 78 * s);
    ctx.closePath();
    ctx.fill();
  }
  ctx.fillStyle = '#f0a63c';
  ctx.beginPath();
  ctx.moveTo(-6 * s, -h + 78 * s);
  ctx.quadraticCurveTo(0, -h + 78 * s - 14 * s, 6 * s, -h + 78 * s);
  ctx.closePath();
  ctx.fill();
  // logs
  ctx.strokeStyle = '#4c2f18'; ctx.lineWidth = 4 * s;
  ctx.beginPath(); ctx.moveTo(-w * 0.18, -h + 82 * s); ctx.lineTo(w * 0.12, -h + 80 * s); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-w * 0.1, -h + 86 * s); ctx.lineTo(w * 0.2, -h + 84 * s); ctx.stroke();
  // brick inner lining
  ctx.strokeStyle = 'rgba(120,70,40,0.5)'; ctx.lineWidth = 1.4 * s;
  for (let bx = -w * 0.26; bx < w * 0.26; bx += 14 * s) {
    ctx.beginPath(); ctx.moveTo(bx, -h + 42 * s); ctx.lineTo(bx, -h + 76 * s); ctx.stroke();
  }
  ctx.restore();
}

// ============ PIANO (grand-ish) ============
function piano(ctx, x, y, s, o = {}) {
  const w = 140 * s, h = 78 * s;
  ctx.save();
  ctx.translate(x, y);
  if (o.rot) ctx.rotate(o.rot * U.D2R);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  A.drawShadow(ctx, 0, 4 * s, w * 0.55, w * 0.22, 0, 0.36, 'soft');
  const pt = T.T.woodDark();
  // body
  ctx.beginPath();
  ctx.moveTo(-w / 2, 0);
  ctx.lineTo(-w * 0.42, -h);
  ctx.quadraticCurveTo(0, -h - 10 * s, w * 0.42, -h);
  ctx.lineTo(w / 2, 0);
  ctx.quadraticCurveTo(0, 8 * s, -w / 2, 0);
  ctx.closePath();
  ctx.fillStyle = '#3a2a1c'; ctx.fill();
  ctx.strokeStyle = INK; ctx.lineWidth = 2.6 * s; ctx.globalAlpha = 0.85; ctx.stroke();
  ctx.globalAlpha = o.alpha !== undefined ? o.alpha : 1;
  // lid open (3/4)
  ctx.beginPath();
  ctx.moveTo(-w * 0.42, -h);
  ctx.quadraticCurveTo(-w * 0.1, -h - 26 * s, w * 0.34, -h - 16 * s);
  ctx.lineTo(w * 0.34, -h);
  ctx.quadraticCurveTo(-w * 0.1, -h - 6 * s, -w * 0.42, -h);
  ctx.fillStyle = '#4c3520';
  ctx.fill();
  ctx.strokeStyle = INK; ctx.lineWidth = 2.2 * s; ctx.stroke();
  // keys (lid closed front view)
  const ky = -h * 0.3;
  ctx.fillStyle = '#f2ecdc';
  A.inkRect(ctx, -w * 0.44, ky - 12 * s, w * 0.88, 14 * s, { fill: '#f2ecdc', strokeW: 1.6 * s, strokeA: 0.7, jitter: 0.4 * s, inner: false });
  ctx.fillStyle = '#1e1a16';
  const nKeys = 26;
  for (let i = 0; i < nKeys; i++) {
    const kx = -w * 0.44 + i * (w * 0.88 / nKeys);
    ctx.fillRect(kx + 1 * s, ky - 4 * s, (w * 0.88 / nKeys) - 2.2 * s, 8 * s);
  }
  ctx.restore();
}

// ============ BUST on pedestal ============
function bust(ctx, x, y, s, o = {}) {
  ctx.save();
  ctx.translate(x, y);
  if (o.rot) ctx.rotate(o.rot * U.D2R);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  A.drawShadow(ctx, 0, 3 * s, 18 * s, 8 * s, 0, 0.3, 'soft');
  A.inkRect(ctx, -14 * s, -34 * s, 28 * s, 34 * s, {
    fill: '#ded4c1', tex: T.T.stone(), strokeW: 2.4 * s, strokeA: 0.8, jitter: 0.5 * s,
  });
  ctx.fillStyle = '#e9e0cc';
  ctx.beginPath(); ctx.ellipse(0, -48 * s, 13 * s, 16 * s, 0, 0, U.TAU); ctx.fill();
  ctx.strokeStyle = INK; ctx.lineWidth = 2.2 * s; ctx.globalAlpha = 0.7; ctx.stroke();
  ctx.globalAlpha = o.alpha !== undefined ? o.alpha : 1;
  // shoulders
  ctx.fillStyle = '#e9e0cc';
  ctx.beginPath();
  ctx.moveTo(-18 * s, -36 * s);
  ctx.quadraticCurveTo(-12 * s, -44 * s, 0, -44 * s);
  ctx.quadraticCurveTo(12 * s, -44 * s, 18 * s, -36 * s);
  ctx.lineTo(18 * s, -34 * s);
  ctx.lineTo(-18 * s, -34 * s);
  ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = INK; ctx.lineWidth = 2 * s; ctx.globalAlpha = 0.7; ctx.stroke();
  ctx.restore();
}

// ============ PLANT ============
function plant(ctx, x, y, s, o = {}) {
  ctx.save();
  ctx.translate(x, y);
  if (o.rot) ctx.rotate(o.rot * U.D2R);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  A.drawShadow(ctx, 0, 3 * s, 16 * s, 7 * s, 0, 0.3, 'soft');
  A.inkRect(ctx, -13 * s, -26 * s, 26 * s, 26 * s, {
    fill: '#a8663c', tex: T.T.woodDark(), strokeW: 2.2 * s, strokeA: 0.8, jitter: 0.5 * s, round: 3 * s,
  });
  const rng = U.makeRng(o.seed || 9);
  ctx.strokeStyle = '#4d6b3d';
  ctx.lineWidth = 2.6 * s;
  for (let i = 0; i < 7; i++) {
    const a = -2.4 + i * 0.42;
    ctx.beginPath();
    ctx.moveTo(0, -26 * s);
    ctx.quadraticCurveTo(Math.sin(a) * 14 * s, -44 * s, Math.sin(a) * 20 * s + rng() * 6 * s, -64 * s - rng() * 10 * s);
    ctx.stroke();
    ctx.fillStyle = '#5e7a4a';
    ctx.beginPath();
    ctx.ellipse(Math.sin(a) * 18 * s, -58 * s - rng() * 8 * s, 6 * s, 12 * s, a, 0, U.TAU);
    ctx.fill();
    ctx.strokeStyle = '#3d5526'; ctx.lineWidth = 1.2 * s; ctx.stroke();
    ctx.strokeStyle = '#4d6b3d'; ctx.lineWidth = 2.6 * s;
  }
  ctx.restore();
}

// ============ DOUBLE DOORS ============
function doors(ctx, x, y, s, o = {}) {
  // y = top of door (architrave), x = center; doors hang below
  const w = (o.w || 88) * s, h = (o.h || 160) * s;
  ctx.save();
  ctx.translate(x, y);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  // frame
  A.inkRect(ctx, -w / 2 - 6 * s, 0, w + 12 * s, 8 * s, { fill: '#c9a227', strokeW: 2.4 * s, strokeA: 0.8, jitter: 0.5 * s });
  for (const sgn of [-1, 1]) {
    const dx = sgn * w * 0.25; // hinge offsets for sliding animation handled by caller via rot? keep simple
  }
  // left panel
  A.inkRect(ctx, -w / 2, 6 * s, w / 2 + 2 * s, h, {
    fill: '#b98c52', tex: T.T.woodLight(), strokeW: 2.6 * s, strokeA: 0.85, jitter: 0.6 * s, inner: false,
  });
  A.inkRect(ctx, -w * 0.38, h * 0.16, w * 0.34, h * 0.5, { fill: '#a06a3e', strokeW: 1.8 * s, strokeA: 0.6, jitter: 0.4 * s, round: 3 * s });
  // right panel
  A.inkRect(ctx, 2 * s, 6 * s, w / 2 - 2 * s, h, {
    fill: '#b98c52', tex: T.T.woodLight(), strokeW: 2.6 * s, strokeA: 0.85, jitter: 0.6 * s, inner: false,
  });
  A.inkRect(ctx, w * 0.04, h * 0.16, w * 0.34, h * 0.5, { fill: '#a06a3e', strokeW: 1.8 * s, strokeA: 0.6, jitter: 0.4 * s, round: 3 * s });
  // handles
  ctx.fillStyle = '#e8c98a';
  ctx.beginPath(); ctx.arc(-w * 0.02, h * 0.55, 3.2 * s, 0, U.TAU); ctx.fill();
  ctx.beginPath(); ctx.arc(w * 0.02, h * 0.55, 3.2 * s, 0, U.TAU); ctx.fill();
  ctx.restore();
}

// ============ WINDOW (with sky + mullions + sill) ============
function window(ctx, x, y, s, o = {}) {
  // y = top of window; draws downward
  const w = (o.w || 120) * s, h = (o.h || 170) * s;
  ctx.save();
  ctx.translate(x, y);
  if (o.rot) ctx.rotate(o.rot * U.D2R);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  // frame
  A.inkRect(ctx, -w / 2 - 7 * s, 0, w + 14 * s, 9 * s, { fill: '#e8ddc4', strokeW: 2.2 * s, strokeA: 0.8, jitter: 0.5 * s });
  // sky panel
  const sky = ctx.createLinearGradient(0, 0, 0, h);
  sky.addColorStop(0, o.skyTop || '#bcd4e4');
  sky.addColorStop(1, o.skyBot || '#e9dcc8');
  A.inkRect(ctx, -w / 2, 9 * s, w, h - 9 * s, { fill: null, strokeW: 0, inner: false });
  ctx.fillStyle = sky;
  roundRectFill(ctx, -w / 2, 9 * s, w, h - 9 * s, 2 * s);
  // distant landscape silhouette
  ctx.fillStyle = 'rgba(110,138,120,0.45)';
  ctx.beginPath();
  ctx.moveTo(-w / 2, h * 0.7);
  ctx.quadraticCurveTo(-w * 0.2, h * 0.55, 0, h * 0.64);
  ctx.quadraticCurveTo(w * 0.25, h * 0.56, w / 2, h * 0.68);
  ctx.lineTo(w / 2, h);
  ctx.lineTo(-w / 2, h);
  ctx.closePath();
  ctx.fill();
  // mullions
  ctx.strokeStyle = '#e8ddc4';
  ctx.lineWidth = 3.4 * s;
  ctx.beginPath(); ctx.moveTo(-w / 2, 9 * s); ctx.lineTo(-w / 2, h); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(w / 2, 9 * s); ctx.lineTo(w / 2, h); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(0, 9 * s); ctx.lineTo(0, h); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-w / 2, h * 0.5); ctx.lineTo(w / 2, h * 0.5); ctx.stroke();
  // sill
  A.inkRect(ctx, -w * 0.6, h - 4 * s, w * 1.2, 9 * s, { fill: '#e8ddc4', strokeW: 2.2 * s, strokeA: 0.8, jitter: 0.5 * s });
  ctx.restore();
}
function roundRectFill(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r); ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
  ctx.fill();
}

// ============ COLUMN (fluted, with base+capital) ============
function column(ctx, x, y, s, o = {}) {
  // y = base ground; draws upward
  const w = (o.w || 34) * s, h = (o.h || 300) * s;
  ctx.save();
  ctx.translate(x, y);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  A.drawShadow(ctx, 0, 3 * s, w * 0.8, w * 0.26, 0, 0.3, 'soft');
  // base
  A.inkRect(ctx, -w * 0.68, -16 * s, w * 1.36, 16 * s, { fill: '#ded4c1', tex: T.T.stone(), strokeW: 2.4 * s, strokeA: 0.8, jitter: 0.5 * s });
  A.inkRect(ctx, -w * 0.58, -22 * s, w * 1.16, 7 * s, { fill: '#d8cfbc', strokeW: 2 * s, strokeA: 0.7, jitter: 0.4 * s });
  // shaft (fluted: alternating light/dark vertical bands)
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(-w / 2, -22 * s);
  ctx.lineTo(-w / 2, -h);
  ctx.lineTo(w / 2, -h);
  ctx.lineTo(w / 2, -22 * s);
  ctx.closePath();
  ctx.clip();
  const grad = ctx.createLinearGradient(-w / 2, 0, w / 2, 0);
  grad.addColorStop(0, '#cdc3ae');
  grad.addColorStop(0.35, '#f2ecdc');
  grad.addColorStop(0.6, '#e6ddca');
  grad.addColorStop(1, '#b9ad95');
  ctx.fillStyle = grad;
  ctx.fillRect(-w / 2, -h, w, h);
  ctx.strokeStyle = 'rgba(150,138,115,0.55)';
  ctx.lineWidth = 1.6 * s;
  for (let i = 0; i < 9; i++) {
    const fx = -w / 2 + (w / 9) * i + w / 18;
    ctx.beginPath(); ctx.moveTo(fx, -h); ctx.lineTo(fx, -22 * s); ctx.stroke();
  }
  ctx.restore();
  ctx.strokeStyle = INK; ctx.lineWidth = 2.4 * s; ctx.globalAlpha = 0.8;
  ctx.beginPath(); ctx.moveTo(-w / 2, -h); ctx.lineTo(-w / 2, -22 * s); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(w / 2, -h); ctx.lineTo(w / 2, -22 * s); ctx.stroke();
  // capital
  A.inkRect(ctx, -w * 0.62, -h - 14 * s, w * 1.24, 14 * s, { fill: '#e8dec8', tex: T.T.stone(), strokeW: 2.4 * s, strokeA: 0.8, jitter: 0.5 * s });
  ctx.strokeStyle = INK; ctx.lineWidth = 1.8 * s; ctx.globalAlpha = 0.6;
  for (let i = 0; i <= 6; i++) {
    ctx.beginPath(); ctx.moveTo(-w * 0.56 + i * (w * 1.12 / 6), -h - 14 * s); ctx.lineTo(-w * 0.56 + i * (w * 1.12 / 6), -h - 4 * s); ctx.stroke();
  }
  ctx.globalAlpha = o.alpha !== undefined ? o.alpha : 1;
  ctx.restore();
}

// ============ ROOF SECTION (slate slab) ============
function roofSection(ctx, x, y, s, o = {}) {
  const w = (o.w || 420) * s, h = (o.h || 60) * s;
  ctx.save();
  ctx.translate(x, y);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  if (o.rot) ctx.rotate(o.rot * U.D2R);
  // slab body
  ctx.beginPath();
  ctx.moveTo(-w / 2, 0);
  ctx.lineTo(w / 2, 0);
  ctx.lineTo(w * 0.44, -h);
  ctx.lineTo(-w * 0.44, -h);
  ctx.closePath();
  const g = ctx.createLinearGradient(0, -h, 0, 0);
  g.addColorStop(0, '#5a5f66');
  g.addColorStop(1, '#767d86');
  ctx.fillStyle = g;
  ctx.fill();
  ctx.strokeStyle = INK; ctx.lineWidth = 2.6 * s; ctx.globalAlpha = 0.85; ctx.stroke();
  // slate rows
  ctx.globalAlpha = 0.35;
  ctx.strokeStyle = '#454a51';
  ctx.lineWidth = 1.3 * s;
  const rows = 5;
  for (let r = 0; r < rows; r++) {
    const ry = -h * (0.15 + r * 0.19);
    const rw = w * (0.94 - r * 0.1);
    ctx.beginPath(); ctx.moveTo(-rw / 2, ry); ctx.lineTo(rw / 2, ry); ctx.stroke();
  }
  for (let r = 0; r < rows; r++) {
    const ry = -h * (0.15 + r * 0.19);
    const rw = w * (0.94 - r * 0.1);
    for (let c = 0; c < 6; c++) {
      const cx = -rw / 2 + 12 * s + c * (rw / 6);
      ctx.beginPath();
      ctx.arc(cx, ry - h * 0.075, 5 * s, Math.PI, 0);
      ctx.stroke();
    }
  }
  // fascia board
  A.inkRect(ctx, -w * 0.5, 0, w, 9 * s, { fill: '#c9bfa6', strokeW: 2 * s, strokeA: 0.7, jitter: 0.4 * s });
  ctx.restore();
}

// ============ SMALL OBJECTS: globe, telephone, mug, books, vase ============
function globe(ctx, x, y, s, o = {}) {
  ctx.save();
  ctx.translate(x, y);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  A.drawShadow(ctx, 0, 2 * s, 13 * s, 6 * s, 0, 0.3, 'soft');
  ctx.strokeStyle = '#8a6a3a'; ctx.lineWidth = 2.4 * s;
  ctx.beginPath(); ctx.moveTo(0, -34 * s); ctx.lineTo(-7 * s, -4 * s); ctx.lineTo(7 * s, -4 * s); ctx.closePath(); ctx.stroke();
  const g = ctx.createRadialGradient(-5 * s, -16 * s, 2 * s, 0, -16 * s, 15 * s);
  g.addColorStop(0, '#a8c8e0'); g.addColorStop(1, '#41618c');
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.arc(0, -16 * s, 14 * s, 0, U.TAU); ctx.fill();
  ctx.strokeStyle = INK; ctx.lineWidth = 2 * s; ctx.globalAlpha = 0.75; ctx.stroke();
  ctx.globalAlpha = 0.5;
  ctx.strokeStyle = '#2f4a72';
  ctx.beginPath(); ctx.ellipse(0, -16 * s, 14 * s, 5 * s, 0, 0, U.TAU); ctx.stroke();
  ctx.beginPath(); ctx.ellipse(0, -16 * s, 5 * s, 14 * s, 0, 0, U.TAU); ctx.stroke();
  ctx.globalAlpha = o.alpha !== undefined ? o.alpha : 1;
  ctx.restore();
}

function telephone(ctx, x, y, s, o = {}) {
  ctx.save();
  ctx.translate(x, y);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  A.inkRect(ctx, -16 * s, -14 * s, 32 * s, 14 * s, { fill: '#26323e', strokeW: 1.8 * s, strokeA: 0.7, round: 4 * s, jitter: 0.4 * s });
  ctx.strokeStyle = '#8a6a3a'; ctx.lineWidth = 2.2 * s;
  ctx.beginPath(); ctx.moveTo(-8 * s, -14 * s); ctx.quadraticCurveTo(-16 * s, -30 * s, -10 * s, -32 * s); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(8 * s, -14 * s); ctx.quadraticCurveTo(16 * s, -30 * s, 10 * s, -32 * s); ctx.stroke();
  ctx.fillStyle = '#9fd0f5';
  ctx.fillRect(-11 * s, -12.5 * s, 22 * s, 5 * s);
  ctx.restore();
}

function mug(ctx, x, y, s, o = {}) {
  ctx.save();
  ctx.translate(x, y);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  A.inkRect(ctx, -10 * s, -22 * s, 20 * s, 22 * s, { fill: '#f2ecdc', strokeW: 1.8 * s, strokeA: 0.7, round: 3 * s, jitter: 0.4 * s });
  ctx.beginPath(); ctx.arc(10 * s, -12 * s, 5 * s, -1.4, 1.4);
  ctx.strokeStyle = '#f2ecdc'; ctx.lineWidth = 3.4 * s; ctx.stroke();
  ctx.strokeStyle = INK; ctx.lineWidth = 1.6 * s; ctx.globalAlpha = 0.6; ctx.stroke();
  ctx.fillStyle = '#5a4632';
  ctx.beginPath(); ctx.ellipse(0, -22 * s, 10 * s, 3 * s, 0, 0, U.TAU); ctx.fill();
  ctx.restore();
}

function vase(ctx, x, y, s, o = {}) {
  ctx.save();
  ctx.translate(x, y);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  A.drawShadow(ctx, 0, 2 * s, 10 * s, 5 * s, 0, 0.3, 'soft');
  ctx.beginPath();
  ctx.moveTo(-9 * s, -34 * s);
  ctx.quadraticCurveTo(-14 * s, -18 * s, -11 * s, 0);
  ctx.lineTo(11 * s, 0);
  ctx.quadraticCurveTo(14 * s, -18 * s, 9 * s, -34 * s);
  ctx.closePath();
  ctx.fillStyle = '#2f4a72';
  ctx.fill();
  ctx.strokeStyle = INK; ctx.lineWidth = 2 * s; ctx.globalAlpha = 0.8; ctx.stroke();
  ctx.globalAlpha = 0.4;
  ctx.strokeStyle = '#e8dcc0';
  ctx.beginPath(); ctx.moveTo(-5 * s, -30 * s); ctx.quadraticCurveTo(-8 * s, -18 * s, -7 * s, -2 * s); ctx.stroke();
  ctx.globalAlpha = o.alpha !== undefined ? o.alpha : 1;
  // stems + blooms
  ctx.strokeStyle = '#4d6b3d'; ctx.lineWidth = 2 * s;
  for (let i = 0; i < 3; i++) {
    const a = -2.6 + i * 0.5;
    ctx.beginPath();
    ctx.moveTo(0, -34 * s);
    ctx.quadraticCurveTo(Math.sin(a) * 10 * s, -52 * s, Math.sin(a) * 16 * s, -64 * s);
    ctx.stroke();
    ctx.fillStyle = i % 2 ? '#e0b44c' : '#c0683c';
    ctx.beginPath();
    ctx.ellipse(Math.sin(a) * 15 * s, -62 * s, 6 * s, 9 * s, a, 0, U.TAU);
    ctx.fill();
  }
  ctx.restore();
}

function stackBooks(ctx, x, y, s, o = {}) {
  ctx.save();
  ctx.translate(x, y);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  const cols = ['#7a3b2e', '#2f4a7a', '#4a6b4f'];
  for (let i = 0; i < 3; i++) {
    const bw = (26 - i * 2) * s, bh = 7 * s;
    A.inkRect(ctx, -bw / 2, -bh * (3 - i), bw, bh, {
      fill: cols[i], strokeW: 1.4 * s, strokeA: 0.65, jitter: 0.35 * s,
    });
    ctx.fillStyle = 'rgba(255,240,200,0.5)';
    ctx.fillRect(-bw / 2 + 2 * s, -bh * (3 - i) + 1.6 * s, bw - 4 * s, 1.8 * s);
  }
  ctx.restore();
}

// ============ EAGLE PEDESTAL SIDE TABLE (State Dining Room) ============
function eagleTable(ctx, x, y, s, o = {}) {
  ctx.save();
  ctx.translate(x, y);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  A.drawShadow(ctx, 0, 3 * s, 18 * s, 8 * s, 0, 0.3, 'soft');
  // pedestal
  A.inkRect(ctx, -10 * s, -46 * s, 20 * s, 46 * s, {
    fill: '#b8912a', strokeW: 2.4 * s, strokeA: 0.85, jitter: 0.5 * s,
  });
  // eagle silhouette
  ctx.fillStyle = '#9a7b2a';
  ctx.beginPath();
  ctx.moveTo(0, -54 * s);
  ctx.quadraticCurveTo(-14 * s, -58 * s, -20 * s, -48 * s);
  ctx.quadraticCurveTo(-10 * s, -50 * s, 0, -44 * s);
  ctx.quadraticCurveTo(10 * s, -50 * s, 20 * s, -48 * s);
  ctx.quadraticCurveTo(14 * s, -58 * s, 0, -54 * s);
  ctx.fill();
  ctx.strokeStyle = INK; ctx.lineWidth = 1.6 * s; ctx.globalAlpha = 0.6; ctx.stroke();
  ctx.globalAlpha = o.alpha !== undefined ? o.alpha : 1;
  // top
  A.inkRect(ctx, -16 * s, -62 * s, 32 * s, 8 * s, { fill: '#c9a227', strokeW: 2.2 * s, strokeA: 0.8, jitter: 0.5 * s });
  // base
  A.inkRect(ctx, -15 * s, -4 * s, 30 * s, 6 * s, { fill: '#b8912a', strokeW: 2.2 * s, strokeA: 0.8, jitter: 0.5 * s });
  ctx.restore();
}

module.exports = {
  chair, desk, sofa, table, diningTable, sideboard, bookshelf, lamp, chandelier, rug,
  painting, portrait, drapes, fireplace, piano, bust, plant, doors, window, column,
  roofSection, globe, telephone, mug, vase, stackBooks, eagleTable,
};
