'use strict';
/* labels.js — Arabic typography engine: proper RTL via engine bidi, animated reveals,
   annotations. All text drawn as independent layers (never baked into artwork). */

const path = require('path');
const { createCanvas, GlobalFonts } = require('@napi-rs/canvas');
const U = require('./util');

const BASE = path.join(__dirname, '..');
let fontsReady = false;
function registerFonts() {
  if (fontsReady) return;
  GlobalFonts.registerFromPath(path.join(BASE, 'node_modules/@fontsource/amiri/files/amiri-arabic-700-normal.woff2'), 'Amiri');
  GlobalFonts.registerFromPath(path.join(BASE, 'node_modules/@fontsource/amiri/files/amiri-arabic-400-normal.woff2'), 'Amiri');
  GlobalFonts.registerFromPath(path.join(BASE, 'node_modules/@fontsource/noto-sans-arabic/files/noto-sans-arabic-arabic-500-normal.woff2'), 'Noto Sans Arabic');
  GlobalFonts.registerFromPath(path.join(BASE, 'node_modules/@fontsource/noto-sans-arabic/files/noto-sans-arabic-arabic-400-normal.woff2'), 'Noto Sans Arabic');
  fontsReady = true;
}

// draw RTL Arabic: logical string, right-aligned at xRight
function drawArabic(ctx, text, xRight, y, font, color, alpha = 1) {
  ctx.save();
  ctx.font = font;
  ctx.textAlign = 'right';
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = color;
  ctx.globalAlpha = alpha;
  ctx.fillText(text, xRight, y);
  ctx.restore();
}
function measureArabic(ctx, text, font) {
  ctx.save();
  ctx.font = font;
  const m = ctx.measureText(text);
  ctx.restore();
  return m.width;
}

// word-level tracking animation for Arabic (bidi-safe: draw words RTL individually)
function drawArabicTracking(ctx, text, xRight, y, font, color, tracking, alpha = 1) {
  const words = text.split(' ');
  ctx.save();
  ctx.font = font;
  ctx.textAlign = 'right';
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = color;
  ctx.globalAlpha = alpha;
  let cx = xRight;
  // draw from rightmost word to left
  for (let i = words.length - 1; i >= 0; i--) {
    const w = measureArabic(ctx, words[i], font);
    ctx.fillText(words[i], cx, y);
    cx -= w + tracking;
  }
  ctx.restore();
}

// ---------- animated label ----------
// o = {text, x (right edge), y, size, weight:'400'|'700', family:'Amiri'|'Noto Sans Arabic',
//      color, reveal (0..1 progress), type:'mask'|'slide'|'scale'|'tracking'|'fade',
//      trackingPx (for tracking type), shadow:{dx,dy,blur,color}, maxTracking}
function labelReveal(ctx, o) {
  const {
    text, x, y, size = 40, weight = '400', family = 'Amiri', color = '#2f2a24',
    reveal = 1, type = 'fade', maxTracking = 22, shadow = null,
  } = o;
  const font = `${weight} ${size}px "${family}"`;
  if (reveal <= 0) return;
  ctx.save();
  // shadow
  if (shadow) {
    ctx.shadowColor = shadow.color || 'rgba(30,22,10,0.35)';
    ctx.shadowBlur = shadow.blur || 8;
    ctx.shadowOffsetX = shadow.dx || 0;
    ctx.shadowOffsetY = shadow.dy || 2;
  }
  let alpha = 1;
  let offX = 0, offY = 0, sc = 1, tracking = 0;
  if (type === 'fade') {
    alpha = reveal;
  } else if (type === 'slide') {
    alpha = U.clamp(reveal * 1.6, 0, 1);
    offX = (1 - U.ease.outCubic(reveal)) * -46;
    offY = (1 - U.ease.outCubic(reveal)) * 10;
  } else if (type === 'scale') {
    alpha = U.clamp(reveal * 1.5, 0, 1);
    sc = U.clamp(U.ease.outBack(reveal), 0.2, 1.08);
  } else if (type === 'tracking') {
    alpha = U.clamp(reveal * 1.4, 0, 1);
    const f = U.ease.outCubic(reveal);
    tracking = (1 - f) * maxTracking;
    offY = (1 - f) * 6;
  } else if (type === 'mask') {
    // wipe reveal from bottom
    const f = U.ease.outCubic(U.clamp(reveal * 1.15 - 0.1, 0, 1));
    alpha = 1;
    // clip bottom-up
    ctx.save();
    ctx.beginPath();
    ctx.rect(x - 900, y - size * 2.2, 1800, (size * 2.2) * f + size * 0.6);
    ctx.clip();
    drawArabic(ctx, text, x, y, font, color, 1);
    ctx.restore();
    ctx.restore();
    return;
  }
  if (sc !== 1) {
    ctx.translate(x, y);
    ctx.scale(sc, sc);
    ctx.translate(-x, -y);
  }
  ctx.translate(offX, offY);
  if (type === 'tracking') {
    drawArabicTracking(ctx, text, x - offX, y - offY, font, color, tracking, alpha);
  } else {
    drawArabic(ctx, text, x - offX, y - offY, font, color, alpha);
  }
  ctx.restore();
}

// ---------- annotation leader line (animated draw + pulse dot) ----------
function annotationLine(ctx, o) {
  const { x1, y1, x2, y2, progress = 1, color = '#c9a227', width = 2, t = 0, label } = o;
  if (progress <= 0) return;
  ctx.save();
  const f = U.ease.outCubic(U.clamp(progress, 0, 1));
  const x2p = U.lerp(x1, x2, f), y2p = U.lerp(y1, y2, f);
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.setLineDash([7, 5]);
  ctx.lineDashOffset = -t * 22 % 12;
  ctx.globalAlpha = 0.9;
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2p, y2p);
  ctx.stroke();
  ctx.setLineDash([]);
  // endpoint dot
  if (f > 0.2) {
    ctx.globalAlpha = 1;
    ctx.fillStyle = color;
    const pulse = 6 + 1.6 * Math.sin(t * 3);
    ctx.beginPath(); ctx.arc(x2p, y2p, pulse, 0, U.TAU); ctx.fill();
    ctx.strokeStyle = '#2f2a24'; ctx.lineWidth = 1.4; ctx.stroke();
  }
  ctx.restore();
}

// ---------- small English label (letterspaced caps) ----------
function latinLabel(ctx, text, x, y, size, color, tracking = 4, alpha = 1, align = 'left') {
  ctx.save();
  ctx.font = `500 ${size}px "DejaVu Sans"`;
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = color;
  ctx.globalAlpha = alpha;
  let cx = align === 'right' ? x : x;
  if (align === 'right') {
    // measure total width with tracking
    const chars = text.split('');
    let total = 0;
    for (const c of chars) total += ctx.measureText(c).width + tracking;
    cx = x - total + tracking;
    for (const c of chars) {
      ctx.fillText(c, cx, y);
      cx += ctx.measureText(c).width + tracking;
    }
  } else {
    for (const c of text.split('')) {
      ctx.fillText(c, cx, y);
      cx += ctx.measureText(c).width + tracking;
    }
  }
  ctx.restore();
}

module.exports = { registerFonts, drawArabic, measureArabic, drawArabicTracking, labelReveal, annotationLine, latinLabel };
