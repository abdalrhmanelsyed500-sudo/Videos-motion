'use strict';
/* render.js — render frames of the 20s sequence.
   Usage:
     node tools/render.js --frames 0,75,150,240,330,420,510,599 [--out dir]   → PNG frames
     node tools/render.js --video out.mp4                                    → pipe rawvideo → H.264
     node tools/render.js --stats 0,150,300,450,599                          → per-frame numeric stats
*/
const { createCanvas } = require('@napi-rs/canvas');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const scene = require('../src/scene');
const U = require('../src/util');

const FFMPEG = process.env.FFMPEG_PATH || '/home/user/.venv-wh20s/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v9.0.2';
const W = 1920, H = 1080, FPS = 30, NFRAMES = 600;

function parseArgs() {
  const args = process.argv.slice(2);
  const o = { frames: null, video: null, pngs: null, stats: null, out: 'qc_frames', start: 0, end: 600 };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--frames') o.frames = args[++i];
    if (args[i] === '--video') o.video = args[++i];
    if (args[i] === '--pngs') o.pngs = args[++i];
    if (args[i] === '--stats') o.stats = args[++i];
    if (args[i] === '--out') o.out = args[++i];
    if (args[i] === '--start') o.start = parseInt(args[++i]);
    if (args[i] === '--end') o.end = parseInt(args[++i]);
  }
  return o;
}

function makeCanvas() {
  const cv = createCanvas(W, H);
  return { cv, ctx: cv.getContext('2d') };
}

function frameStats(ctx) {
  const d = ctx.getImageData(0, 0, W, H).data;
  let sum = 0, sum2 = 0, n = 0;
  let warm = 0, gold = 0, blue = 0;
  for (let i = 0; i < d.length; i += 4 * 13) { // sample
    const r = d[i], g = d[i + 1], b = d[i + 2];
    const lum = 0.299 * r + 0.587 * g + 0.114 * b;
    sum += lum; sum2 += lum * lum; n++;
    if (r > 180 && g > 150 && b < g - 25) warm++;
    if (r > 150 && g > 110 && b < 90) gold++;
    if (b > r + 25 && b > 90) blue++;
  }
  const mean = sum / n;
  return {
    mean: +mean.toFixed(1),
    std: +Math.sqrt(sum2 / n - mean * mean).toFixed(1),
    warmPct: +(warm / n * 100).toFixed(1),
    goldPct: +(gold / n * 100).toFixed(1),
    bluePct: +(blue / n * 100).toFixed(1),
  };
}

async function main() {
  const o = parseArgs();
  const { cv, ctx } = makeCanvas();

  if (o.frames) {
    const idxs = o.frames.split(',').map(s => parseInt(s.trim(), 10)).filter(v => v >= 0 && v < NFRAMES);
    fs.mkdirSync(o.out, { recursive: true });
    for (const i of idxs) {
      const t = i / FPS;
      scene.renderFrame(ctx, t);
      const buf = cv.toBuffer('image/png');
      fs.writeFileSync(path.join(o.out, `frame_${String(i).padStart(3, '0')}_t${t.toFixed(2)}s.png`), buf);
      const s = frameStats(ctx);
      console.log(`frame ${i} t=${t.toFixed(2)}s  mean=${s.mean} std=${s.std} warm=${s.warmPct}% gold=${s.goldPct}% blue=${s.bluePct}%`);
    }
    console.log('PNG frames written to', o.out);
  } else if (o.stats) {
    const idxs = o.stats.split(',').map(s => parseInt(s.trim(), 10));
    for (const i of idxs) {
      const t = i / FPS;
      scene.renderFrame(ctx, t);
      const s = frameStats(ctx);
      console.log(`frame ${i} t=${t.toFixed(2)}s  mean=${s.mean} std=${s.std} warm=${s.warmPct}% gold=${s.goldPct}% blue=${s.bluePct}%`);
    }
  } else if (o.pngs) {
    fs.mkdirSync(o.pngs, { recursive: true });
    let t0 = Date.now();
    for (let i = o.start; i < o.end; i++) {
      scene.renderFrame(ctx, i / FPS);
      fs.writeFileSync(path.join(o.pngs, `f${String(i).padStart(4, '0')}.png`), cv.toBuffer('image/png'));
      if ((i - o.start) % 60 === 0) {
        const el = (Date.now() - t0) / 1000;
        console.log(`frame ${i}/${o.end}  ${el.toFixed(1)}s elapsed  ${((i - o.start) / Math.max(el, 0.001)).toFixed(1)} fps`);
      }
    }
    console.log('PNG frames →', o.pngs, 'range', o.start, '-', o.end, 'elapsed', ((Date.now() - t0) / 1000).toFixed(1), 's');
  } else if (o.video) {
    const ff = spawn(FFMPEG, [
      '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-r', String(FPS), '-i', '-',
      '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
      '-profile:v', 'high', '-movflags', '+faststart', o.video,
    ], { stdio: ['pipe', 'inherit', 'inherit'] });
    const buf = Buffer.alloc(W * H * 4);
    let t0 = Date.now();
    for (let i = 0; i < NFRAMES; i++) {
      scene.renderFrame(ctx, i / FPS);
      const img = ctx.getImageData(0, 0, W, H);
      ff.stdin.write(Buffer.from(img.data.buffer, img.data.byteOffset, img.data.byteLength));
      if (i % 60 === 0) {
        const el = (Date.now() - t0) / 1000;
        console.log(`frame ${i}/${NFRAMES}  ${el.toFixed(1)}s elapsed  ${(i / Math.max(el, 0.001)).toFixed(1)} fps`);
      }
    }
    ff.stdin.end();
    ff.on('close', (code) => {
      console.log('ffmpeg exit', code, '→', o.video);
      if (code === 0 && fs.existsSync(o.video)) {
        console.log('size:', (fs.statSync(o.video).size / 1e6).toFixed(1), 'MB');
      }
    });
  } else {
    console.log('usage: --frames i,j,k | --video out.mp4 | --stats i,j,k');
  }
}

main().catch(e => { console.error(e); process.exit(1); });
