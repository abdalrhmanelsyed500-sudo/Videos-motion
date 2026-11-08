'use strict';
/* textures.js — procedural material textures (paper, plaster, wood, marble, velvet, grass, stone)
   Each generator returns an offscreen canvas usable as a fill pattern or drawImage source. */

const { createCanvas } = require('@napi-rs/canvas');
const U = require('./util');

const cache = {};
function get(name, w, h, fn) {
  if (!cache[name]) cache[name] = fn(w, h);
  return cache[name];
}

// ---- paper: warm base + fibers + stains (full-frame, non-tiling) ----
function paper(w, h) {
  const cv = createCanvas(w, h);
  const ctx = cv.getContext('2d');
  const fbm = U.makeFbm(4201);
  ctx.fillStyle = '#f4ecda';
  ctx.fillRect(0, 0, w, h);
  // base mottling
  const img = ctx.getImageData(0, 0, w, h);
  const d = img.data;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const n = fbm(x / 380, y / 380, 2, 0.55);
      const i = (y * w + x) * 4;
      const dark = n > 0.55 ? (n - 0.55) * 2 * 26 : 0;
      d[i] = Math.max(0, d[i] - dark * 0.9);
      d[i + 1] = Math.max(0, d[i + 1] - dark);
      d[i + 2] = Math.max(0, d[i + 2] - dark * 1.1);
    }
  }
  ctx.putImageData(img, 0, 0);
  // fibers: faint short strokes
  const rng = U.makeRng(77);
  ctx.globalAlpha = 0.05;
  for (let i = 0; i < 900; i++) {
    const x = rng() * w, y = rng() * h, a = rng() * U.TAU, len = 4 + rng() * 18;
    ctx.strokeStyle = rng() > 0.5 ? '#c9bfa6' : '#8a7c5e';
    ctx.lineWidth = 0.6 + rng() * 1.2;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + Math.cos(a) * len, y + Math.sin(a) * len);
    ctx.stroke();
  }
  // stains: soft radial blots
  ctx.globalAlpha = 0.05;
  for (let i = 0; i < 6; i++) {
    const x = rng() * w, y = rng() * h, r = 120 + rng() * 260;
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, 'rgba(180,160,120,0.5)');
    g.addColorStop(1, 'rgba(180,160,120,0)');
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(x, y, r, 0, U.TAU); ctx.fill();
  }
  ctx.globalAlpha = 1;
  return cv;
}

// ---- plaster (wall): tiled subtle mottle ----
function plaster(w, h) {
  const cv = createCanvas(w, h);
  const ctx = cv.getContext('2d');
  const fbm = U.makeFbm(3303, 128);
  ctx.fillStyle = '#efe6d2';
  ctx.fillRect(0, 0, w, h);
  const img = ctx.getImageData(0, 0, w, h);
  const d = img.data;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const n = fbm(x / 90, y / 90, 3, 0.5);
    const i = (y * w + x) * 4;
    const k = (n - 0.5) * 34;
    d[i] = U.clamp(d[i] - k, 0, 255);
    d[i + 1] = U.clamp(d[i + 1] - k * 0.95, 0, 255);
    d[i + 2] = U.clamp(d[i + 2] - k * 0.85, 0, 255);
  }
  ctx.putImageData(img, 0, 0);
  return cv;
}

// ---- wood: grain streaks (tiled) ----
function wood(w, h, base = '#b3814f', dark = '#6e4a29', spacing = 26) {
  const cv = createCanvas(w, h);
  const ctx = cv.getContext('2d');
  const fbm = U.makeFbm(9091, 64);
  ctx.fillStyle = base;
  ctx.fillRect(0, 0, w, h);
  ctx.save();
  ctx.globalAlpha = 0.55;
  for (let x = 0; x < w; x += spacing) {
    const off = (fbm(x / 60, 7, 3, 0.5) - 0.5) * spacing * 0.8;
    for (let y = -h; y < h * 2; y += 5 + fbm(x / 40, y / 30, 2, 0.5) * 9) {
      const wave = Math.sin((y / 90) + x * 0.01) * 4 + fbm(x / 30, y / 60, 3, 0.5) * 7;
      ctx.strokeStyle = fbm(x / 50, y / 40, 3, 0.5) > 0.62 ? dark : 'rgba(90,58,30,0.5)';
      ctx.lineWidth = 0.8 + fbm(x / 45, y / 50, 2, 0.5) * 1.6;
      ctx.beginPath();
      ctx.moveTo(x + off + wave, y);
      ctx.bezierCurveTo(x + off + wave + 3, y + 14, x + off + wave - 4, y + 28, x + off + wave * 1.2, y + 42);
      ctx.stroke();
    }
  }
  ctx.restore();
  return cv;
}

// ---- marble: pale base + veins ----
function marble(w, h) {
  const cv = createCanvas(w, h);
  const ctx = cv.getContext('2d');
  ctx.fillStyle = '#f2ede1';
  ctx.fillRect(0, 0, w, h);
  const fbm = U.makeFbm(555, 128);
  ctx.save();
  ctx.globalAlpha = 0.5;
  for (let i = 0; i < 7; i++) {
    const y0 = h * (0.15 + 0.7 * U.makeRng(100 + i)());
    ctx.strokeStyle = `rgba(150,140,125,${0.25 + U.makeRng(200 + i)() * 0.25})`;
    ctx.lineWidth = 1 + U.makeRng(300 + i)() * 3.5;
    ctx.beginPath();
    const x = -20;
    ctx.moveTo(x, y0);
    for (let s = 0; s <= 10; s++) {
      const t = s / 10;
      const yy = y0 + Math.sin(t * 6 + i) * h * 0.09 + Math.sin(t * 2.3 + i * 2) * h * 0.05;
      ctx.lineTo(x + (w + 40) * t, yy);
    }
    ctx.stroke();
  }
  // mottle
  const img = ctx.getImageData(0, 0, w, h);
  const d = img.data;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const n = fbm(x / 70, y / 70, 4, 0.5);
    const i = (y * w + x) * 4;
    const k = (n - 0.5) * 22;
    d[i] = U.clamp(d[i] - k, 0, 255); d[i + 1] = U.clamp(d[i + 1] - k, 0, 255); d[i + 2] = U.clamp(d[i + 2] - k * 0.9, 0, 255);
  }
  ctx.putImageData(img, 0, 0);
  ctx.restore();
  return cv;
}

// ---- velvet (drapes): vertical streak sheen (tiled) ----
function velvet(w, h, base = '#8a2f28') {
  const cv = createCanvas(w, h);
  const ctx = cv.getContext('2d');
  const fbm = U.makeFbm(7777, 64);
  ctx.fillStyle = base;
  ctx.fillRect(0, 0, w, h);
  ctx.save();
  for (let x = 0; x < w; x += 12) {
    const sh = fbm(x / 40, 3.7, 3, 0.5);
    ctx.fillStyle = `rgba(255,255,255,${0.04 + sh * 0.07})`;
    ctx.fillRect(x, 0, 5, h);
    ctx.fillStyle = 'rgba(0,0,0,0.16)';
    ctx.fillRect(x + 6, 0, 6, h);
  }
  ctx.restore();
  return cv;
}

// ---- grass ----
function grass(w, h) {
  const cv = createCanvas(w, h);
  const ctx = cv.getContext('2d');
  const fbm = U.makeFbm(2048, 128);
  const rng = U.makeRng(2048);
  ctx.fillStyle = '#7d8f5e';
  ctx.fillRect(0, 0, w, h);
  const img = ctx.getImageData(0, 0, w, h);
  const d = img.data;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const n = fbm(x / 80, y / 80, 4, 0.5);
    const i = (y * w + x) * 4;
    const k = (n - 0.5) * 46;
    d[i] = U.clamp(d[i] - k * 0.7, 0, 255);
    d[i + 1] = U.clamp(d[i + 1] - k, 0, 255);
    d[i + 2] = U.clamp(d[i + 2] - k * 0.6, 0, 255);
  }
  ctx.putImageData(img, 0, 0);
  // blades
  ctx.save();
  ctx.globalAlpha = 0.35;
  for (let i = 0; i < 380; i++) {
    const x = rng() * w, y = rng() * h;
    ctx.strokeStyle = rng() > 0.5 ? '#9aa972' : '#5f6e45';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.quadraticCurveTo(x + (rng() - 0.5) * 6, y - 8, x + (rng() - 0.5) * 10, y - 12 - rng() * 10);
    ctx.stroke();
  }
  ctx.restore();
  return cv;
}

// ---- stone (portico steps / base) ----
function stone(w, h) {
  const cv = createCanvas(w, h);
  const ctx = cv.getContext('2d');
  const fbm = U.makeFbm(8080, 64);
  ctx.fillStyle = '#ded4c1';
  ctx.fillRect(0, 0, w, h);
  const img = ctx.getImageData(0, 0, w, h);
  const d = img.data;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const n = fbm(x / 60, y / 60, 3, 0.5);
    const i = (y * w + x) * 4;
    const k = (n - 0.5) * 30;
    d[i] = U.clamp(d[i] - k, 0, 255); d[i + 1] = U.clamp(d[i + 1] - k * 0.98, 0, 255); d[i + 2] = U.clamp(d[i + 2] - k * 0.9, 0, 255);
  }
  ctx.putImageData(img, 0, 0);
  // block lines
  ctx.save();
  ctx.globalAlpha = 0.25;
  ctx.strokeStyle = '#a99c83';
  ctx.lineWidth = 1.2;
  const bw = 90, bh = 42;
  for (let x = 0; x < w; x += bw) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
  }
  for (let y = 0; y < h; y += bh) {
    const off = (Math.floor(y / bh) % 2) * (bw / 2);
    ctx.beginPath(); ctx.moveTo(off, y); ctx.lineTo(w, y); ctx.stroke();
  }
  ctx.restore();
  return cv;
}

// ---- film grain frames (cycled per frame) ----
function grainFrames(n, w, h) {
  const frames = [];
  const fbm = U.makeFbm(1234, 128);
  for (let f = 0; f < n; f++) {
    const cv = createCanvas(w, h);
    const ctx = cv.getContext('2d');
    ctx.fillStyle = 'rgba(0,0,0,0)';
    ctx.fillRect(0, 0, w, h);
    const img = ctx.createImageData(w, h);
    const d = img.data;
    const rng = U.makeRng(9000 + f);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      if (rng() > 0.94) { // sparse grain
        const i = (y * w + x) * 4;
        const v = 200 + rng() * 55;
        d[i] = d[i + 1] = d[i + 2] = v; d[i + 3] = 26 + rng() * 30;
      }
    }
    ctx.putImageData(img, 0, 0);
    frames.push(cv);
  }
  return frames;
}

// ---- sky gradient (precomputed once per shot-lighting) ----
function skyGradient(w, h, top = '#bcd0de', bot = '#e8dcc6') {
  const cv = createCanvas(w, h);
  const ctx = cv.getContext('2d');
  const g = ctx.createLinearGradient(0, 0, 0, h);
  g.addColorStop(0, top);
  g.addColorStop(0.65, bot);
  g.addColorStop(1, '#f0e6d2');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, w, h);
  // clouds: soft horizontal blobs
  const rng = U.makeRng(5150);
  ctx.save();
  ctx.globalAlpha = 0.35;
  for (let i = 0; i < 5; i++) {
    const x = rng() * w, y = h * (0.1 + rng() * 0.3), rx = 140 + rng() * 220, ry = 26 + rng() * 40;
    const g2 = ctx.createRadialGradient(x, y, 0, x, y, rx);
    g2.addColorStop(0, 'rgba(255,252,244,0.8)');
    g2.addColorStop(1, 'rgba(255,252,244,0)');
    ctx.fillStyle = g2;
    ctx.beginPath(); ctx.ellipse(x, y, rx, ry, 0, 0, U.TAU); ctx.fill();
  }
  ctx.restore();
  return cv;
}

// expose with memoized defaults (512x512 tiles)
const T = {
  paper: () => get('paper', 1920, 1080, paper),
  plaster: () => get('plaster', 256, 256, plaster),
  woodLight: () => get('woodLight', 256, 256, (w, h) => wood(w, h, '#c08a52', '#6e4a29', 26)),
  woodDark: () => get('woodDark', 256, 256, (w, h) => wood(w, h, '#8a5a33', '#4c2f18', 20)),
  woodWalnut: () => get('woodWalnut', 256, 256, (w, h) => wood(w, h, '#7d5430', '#3f2512', 18)),
  marble: () => get('marble', 256, 256, marble),
  velvetRed: () => get('velvetRed', 256, 256, (w, h) => velvet(w, h, '#8f3a30')),
  velvetBlue: () => get('velvetBlue', 256, 256, (w, h) => velvet(w, h, '#2f4460')),
  velvetGold: () => get('velvetGold', 256, 256, (w, h) => velvet(w, h, '#9a7b3a')),
  grass: () => get('grass', 256, 256, grass),
  stone: () => get('stone', 256, 256, stone),
  sky: () => get('sky', 1920, 1080, skyGradient),
};

module.exports = { T, make: { paper, plaster, wood, marble, velvet, grass, stone, grainFrames, skyGradient } };
