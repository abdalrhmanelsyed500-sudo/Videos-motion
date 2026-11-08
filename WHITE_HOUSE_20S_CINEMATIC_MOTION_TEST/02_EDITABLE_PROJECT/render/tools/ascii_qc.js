'use strict';
/* ascii_qc.js — render a frame to ASCII density map for composition QC (no vision needed) */
const { createCanvas } = require('@napi-rs/canvas');
const fs = require('fs');
const path = require('path');
const scene = require('../src/scene');

const W = 1920, H = 1080;
const COLS = 150, ROWS = 42;
const CHARS = ' .:-=+*#%@';

function asciiOf(t, out) {
  const cv = createCanvas(W, H);
  const ctx = cv.getContext('2d');
  scene.renderFrame(ctx, t);
  const d = ctx.getImageData(0, 0, W, H).data;
  let s = '';
  for (let r = 0; r < ROWS; r++) {
    let line = '';
    for (let c = 0; c < COLS; c++) {
      const x0 = Math.floor(c * W / COLS), x1 = Math.floor((c + 1) * W / COLS);
      const y0 = Math.floor(r * H / ROWS), y1 = Math.floor((r + 1) * H / ROWS);
      let sum = 0, n = 0;
      for (let y = y0; y < y1; y += 3) for (let x = x0; x < x1; x += 3) {
        const i = (y * W + x) * 4;
        sum += (d[i] + d[i + 1] + d[i + 2]) / 3; n++;
      }
      const lum = sum / n;
      // invert: dark = dense char
      const idx = Math.min(CHARS.length - 1, Math.floor((255 - lum) / 256 * CHARS.length));
      line += CHARS[idx];
    }
    s += line + '\n';
  }
  fs.writeFileSync(out, s);
  console.log(s);
}

const t = parseFloat(process.argv[2] || '6.5');
const out = process.argv[3] || `qc_ascii_t${t}.txt`;
asciiOf(t, out);
