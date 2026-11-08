'use strict';
/* fx.js — compositing: paper overlay, vignette, film grain, light sweeps, color grade */

const U = require('./util');
const T = require('./textures');

function paperOverlay(ctx, W, H, alpha = 0.5) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.globalCompositeOperation = 'multiply';
  ctx.drawImage(T.T.paper(), 0, 0, W, H);
  ctx.restore();
}

function vignette(ctx, W, H, intensity = 0.5) {
  const g = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.95);
  g.addColorStop(0, 'rgba(30,22,12,0)');
  g.addColorStop(1, `rgba(30,22,12,${0.42 * intensity})`);
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);
}

let _grain = null;
function grain(ctx, frameIdx, W, H, alpha = 0.05) {
  if (!_grain || _grain.w !== W || _grain.h !== H) {
    _grain = { w: W, h: H, frames: T.make.grainFrames(8, W, H) };
  }
  const f = _grain.frames[frameIdx % _grain.frames.length];
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.drawImage(f, 0, 0);
  ctx.restore();
}

// diagonal light sweep band — used on transitions
function lightSweep(ctx, W, H, progress, alpha = 0.35, angle = -0.5) {
  if (progress <= 0 || progress >= 1) return;
  ctx.save();
  ctx.translate(W / 2, H / 2);
  ctx.rotate(angle);
  const bandW = W * 0.34;
  const x = U.lerp(-W * 0.75, W * 0.75, progress);
  const g = ctx.createLinearGradient(x - bandW, 0, x + bandW, 0);
  g.addColorStop(0, 'rgba(255,246,220,0)');
  g.addColorStop(0.5, `rgba(255,246,220,${alpha})`);
  g.addColorStop(1, 'rgba(255,246,220,0)');
  ctx.fillStyle = g;
  ctx.fillRect(-W, -H, W * 2, H * 2);
  ctx.restore();
}

// warm cinematic grade overlay (edges + subtle warm wash)
function grade(ctx, W, H, warmth = 0.12) {
  ctx.save();
  ctx.globalCompositeOperation = 'overlay';
  const g = ctx.createRadialGradient(W * 0.5, H * 0.62, H * 0.1, W * 0.5, H * 0.6, H * 1.1);
  g.addColorStop(0, `rgba(255,236,190,${warmth})`);
  g.addColorStop(0.6, `rgba(255,230,180,${warmth * 0.5})`);
  g.addColorStop(1, 'rgba(90,60,30,0.14)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

// circular wipe mask helper — reveals `under` content through expanding/shrinking circle
function circleWipe(ctx, x, y, r, mode) {
  // mode: 'shrink' keeps content inside circle; 'expand' reveals inside circle
  ctx.beginPath();
  ctx.arc(x, y, Math.max(r, 0.5), 0, U.TAU);
  if (mode === 'shrink') ctx.clip();
}

module.exports = { paperOverlay, vignette, grain, lightSweep, grade, circleWipe };
