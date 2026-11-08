'use strict';
/* scene.js — frame assembler: base → camera → world → UI layers → FX. renderFrame(ctx, t). */

const U = require('./util');
const T = require('./textures');
const A = require('./art');
const B = require('./building');
const Rm = require('./rooms');
const L = require('./labels');
const FX = require('./fx');
const TL = require('./timeline');

L.registerFonts();

const W = 1920, H = 1080;
const FULL_ROOM = { cx: 0, yTop: -290, wallH: 300, Hf: 240, Wb: 760, Wf: 950, skew: 40 };
// room-local origin → world offsets
const FULL_ANCHOR = { x: 0, y: -20 };
const MINI_ANCHORS = {
  oval: { x: -255, y: 320 },
  cabinet: { x: -255, y: -150 },
  dining: { x: 255, y: -150 },
  east: { x: 255, y: 320 },
};
const ROOM_TEXT = {
  oval: 'المكتب البيضاوي',
  cabinet: 'غرفة مجلس الوزراء',
  dining: 'قاعة الطعام الرسمية',
  east: 'القاعة الشرقية',
};

function worldToScreen(cam, x, y) {
  const dx = (x - cam.x) * cam.scale;
  const dy = (y - cam.y) * cam.scale;
  const cos = Math.cos(cam.rot), sin = Math.sin(cam.rot);
  return { x: W / 2 + dx * cos - dy * sin, y: H / 2 + dx * sin + dy * cos };
}

function applyCamera(ctx, cam) {
  ctx.translate(W / 2, H / 2);
  ctx.rotate(cam.rot);
  ctx.scale(cam.scale, cam.scale);
  ctx.translate(-cam.x, -cam.y);
}

function drawFullRoom(ctx, fn, room, g, off, o = {}) {
  ctx.save();
  ctx.translate(off.x, off.y);
  if (g !== 1) ctx.scale(g, g);
  fn(ctx, room, 1, o);
  ctx.restore();
}

// ---------------- UI layers ----------------
function drawTitle(ctx, t) {
  const r = TL.labelReveal('title', t);
  if (r > 0) {
    L.labelReveal(ctx, {
      text: 'ماذا يوجد داخل البيت الأبيض؟', x: W / 2 + 330, y: 208,
      size: 64, weight: '700', family: 'Amiri', color: '#2f2a24',
      reveal: r, type: 'mask', shadow: { blur: 10, dy: 3, color: 'rgba(40,28,12,0.3)' },
    });
  }
  const rs = TL.labelReveal('subtitle', t);
  if (rs > 0) {
    const sub = 'AN ARCHITECTURAL CUTAWAY JOURNEY — WASHINGTON, D.C.';
    ctx.save();
    ctx.font = '500 17px "DejaVu Sans"';
    let total = 0;
    for (const c of sub) total += ctx.measureText(c).width + 5;
    L.latinLabel(ctx, sub, W / 2 - total / 2, 296, 17, '#6b5f4f', 5, rs);
    ctx.restore();
  }
}
function drawTitleEnd(ctx, t) {
  const r = TL.labelReveal('titleEnd', t);
  if (r > 0) {
    L.labelReveal(ctx, {
      text: 'ماذا يوجد داخل البيت الأبيض؟', x: W / 2 + 330, y: 208,
      size: 58, weight: '700', family: 'Amiri', color: '#2f2a24',
      reveal: r, type: 'scale', shadow: { blur: 10, dy: 3, color: 'rgba(40,28,12,0.3)' },
    });
  }
  const rs = TL.labelReveal('subtitleEnd', t);
  if (rs > 0) {
    const sub = 'AN ARCHITECTURAL CUTAWAY JOURNEY — WASHINGTON, D.C.';
    ctx.save();
    ctx.font = '500 16px "DejaVu Sans"';
    let total = 0;
    for (const c of sub) total += ctx.measureText(c).width + 5;
    L.latinLabel(ctx, sub, W / 2 - total / 2, 290, 16, '#6b5f4f', 5, rs);
    ctx.restore();
  }
}

// room label + annotation for full-room shots
function drawRoomLabel(ctx, t, cam, name, text, labelXRight, labelY, annFrom, annTo, annT0, annT1, size = 34) {
  const r = TL.labelReveal(name, t);
  if (r > 0) {
    L.labelReveal(ctx, {
      text, x: labelXRight, y: labelY, size, weight: '500', family: 'Noto Sans Arabic',
      color: '#2f2a24', reveal: r, type: LABELTYPE(name), shadow: { blur: 8, dy: 2, color: 'rgba(40,28,12,0.28)' },
    });
    // gold underline accent
    ctx.save();
    ctx.globalAlpha = r * 0.9;
    ctx.strokeStyle = '#c9a227';
    ctx.lineWidth = 2.4;
    ctx.beginPath();
    ctx.moveTo(labelXRight - 84, labelY + 16);
    ctx.lineTo(labelXRight - 20, labelY + 16);
    ctx.stroke();
    ctx.restore();
  }
  const ap = U.kf([{ t: annT0, v: 0 }, { t: annT1, v: 1 }], t, U.ease.outCubic);
  if (ap > 0) {
    const a = worldToScreen(cam, annFrom.x, annFrom.y);
    const b = worldToScreen(cam, annTo.x, annTo.y);
    L.annotationLine(ctx, { x1: a.x, y1: a.y, x2: b.x, y2: b.y, progress: ap, t, color: '#b8862c' });
  }
}
function LABELTYPE(name) {
  const m = { oval: 'slide', cabinet: 'mask', dining: 'slide', east: 'mask' };
  return m[name] || 'fade';
}

// mini room labels (dollhouse)
function drawMiniLabels(ctx, t, cam, hero = false) {
  const map = hero
    ? { oval: 'heroOval', cabinet: 'heroCabinet', dining: 'heroDining', east: 'heroEast' }
    : { oval: 'miniOval', cabinet: 'miniCabinet', dining: 'miniDining', east: 'miniEast' };
  for (const id of ['oval', 'cabinet', 'dining', 'east']) {
    const name = map[id];
    const r = TL.labelReveal(name, t);
    if (r <= 0) continue;
    const a = B.MINI[id];
    const p = worldToScreen(cam, a.cx, a.yTop - (hero ? 52 : 40));
    L.labelReveal(ctx, {
      text: ROOM_TEXT[id], x: p.x + 20, y: p.y,
      size: hero ? 17 : 15, weight: '500', family: 'Noto Sans Arabic',
      color: '#2f2a24', reveal: r, type: 'fade',
      shadow: { blur: 5, dy: 1.5, color: 'rgba(40,28,12,0.3)' },
    });
  }
}

// arch frame overlay for shot 4 transition (screen space, 2 parallax layers)
function drawArchPass(ctx, t) {
  const f = U.ease.inOutCubic((t - 8.0) / 0.5);
  const alpha = U.windowed(t, 8.0, 8.5);
  if (alpha <= 0) return;
  ctx.save();
  ctx.globalAlpha = alpha;
  // outer arch (slower)
  const ox = U.lerp(1250, -1350, f);
  ctx.strokeStyle = '#2f2a24';
  ctx.lineWidth = 5;
  archPath(ctx, W / 2 + ox, 540, 460, 640);
  ctx.stroke();
  // inner glow arch (faster)
  const ix = U.lerp(1500, -1050, f);
  A.drawGlow(ctx, W / 2 + ix, 540 - 240, 240, 0.25, 'warm');
  ctx.restore();
}
function archPath(ctx, cx, cy, w, h) {
  const r = w / 2;
  ctx.beginPath();
  ctx.moveTo(cx - w / 2, cy + h / 2);
  ctx.lineTo(cx - w / 2, cy - h / 2 + r);
  ctx.arc(cx, cy - h / 2 + r, r, Math.PI, 0);
  ctx.lineTo(cx + w / 2, cy + h / 2);
  ctx.stroke();
}

// ---------------- main render ----------------
function renderFrame(ctx, t) {
  t = U.clamp(t, 0, 19.9667);
  const cam = TL.cameraAt(t);
  const ph = TL.phase(t);

  // ---- base: sky + paper ----
  ctx.drawImage(T.T.sky(), 0, 0, W, H);
  FX.paperOverlay(ctx, W, H, 0.5);

  // ---- world ----
  ctx.save();
  applyCamera(ctx, cam);

  const bp = TL.buildingParams(t);
  const showAll = { oval: true, cabinet: true, dining: true, east: true };

  if (ph === 'corridor') {
    // corridor is a full-screen screen-space layer (drawn later)
  } else if (ph === 'expand') {
    const g = TL.expansionG(t);
    ctx.save();
    ctx.globalAlpha = 1 - g;
    B.whiteHouse(ctx, { drawOn: 1, ...bp, showRooms: { ...showAll, oval: false }, highlight: 'oval', t });
    ctx.restore();
    drawFullRoom(ctx, Rm.ovalScene, FULL_ROOM, g, MINI_ANCHORS.oval, { t, lightShaft: true });
  } else if (ph === 'oval') {
    drawFullRoom(ctx, Rm.ovalScene, FULL_ROOM, 1, FULL_ANCHOR, {
      t, lightShaft: true, accentGlow: U.windowed(t, 6.6, 7.3),
    });
  } else if (ph === 'trans4') {
    const f = U.ease.inOutCubic((t - 8.0) / 0.5);
    ctx.save();
    ctx.globalAlpha = 1 - f;
    drawFullRoom(ctx, Rm.ovalScene, FULL_ROOM, 1, FULL_ANCHOR, { t, lightShaft: true });
    ctx.restore();
    ctx.save();
    ctx.globalAlpha = f;
    drawFullRoom(ctx, Rm.cabinetScene, FULL_ROOM, U.lerp(0.92, 1, f), FULL_ANCHOR, { t });
    ctx.restore();
  } else if (ph === 'cabinet') {
    drawFullRoom(ctx, Rm.cabinetScene, FULL_ROOM, 1, FULL_ANCHOR, {
      t, accentGlow: U.windowed(t, 10.3, 10.9),
    });
  } else if (ph === 'dive') {
    drawFullRoom(ctx, Rm.cabinetScene, FULL_ROOM, 1, FULL_ANCHOR, { t });
  } else if (ph === 'wipe') {
    const f = U.clamp((t - 11.5) / 0.4, 0, 1);
    // dining room underneath
    drawFullRoom(ctx, Rm.diningScene, FULL_ROOM, 1, FULL_ANCHOR, { t, lightShaft: true });
    // cabinet room on top, clipped by shrinking circle centered on the tabletop
    // surface point (world (0, 4.8) under dive camera (0,106,2.4) → screen (960, 291))
    ctx.save();
    ctx.beginPath();
    ctx.arc(960, 291, 1500 * (1 - f) + 10, 0, U.TAU);
    ctx.clip();
    drawFullRoom(ctx, Rm.cabinetScene, FULL_ROOM, 2.4, FULL_ANCHOR, { t });
    ctx.restore();
  } else if (ph === 'dining') {
    drawFullRoom(ctx, Rm.diningScene, FULL_ROOM, 1, FULL_ANCHOR, {
      t, lightShaft: true, accentGlow: U.windowed(t, 13.4, 13.9),
    });
  } else if (ph === 'east') {
    drawFullRoom(ctx, Rm.eastScene, FULL_ROOM, 1, FULL_ANCHOR, { t });
  } else if (ph === 'reverse') {
    const g = TL.expansionG(t);
    B.whiteHouse(ctx, { drawOn: 1, ...bp, showRooms: showAll, t });
    drawFullRoom(ctx, Rm.eastScene, FULL_ROOM, g, MINI_ANCHORS.east, { t });
  } else if (ph === 'hero') {
    B.whiteHouse(ctx, { drawOn: 1, ...bp, showRooms: showAll, t });
    B.drawMarkers(ctx, { progress: U.kf([{ t: 18.2, v: 0 }, { t: 19.6, v: 1 }], t, U.ease.outCubic) });
  } else {
    // building / approach
    B.whiteHouse(ctx, { drawOn: bp.drawOn, ...bp, showRooms: showAll, highlight: 'oval', t });
  }
  ctx.restore();

  // ---- screen-space UI layers ----
  if (ph === 'corridor') {
    const a = U.clamp((t - 14.0) / 0.22, 0, 1) * (1 - U.clamp((t - 14.45) / 0.25, 0, 1));
    ctx.save();
    ctx.globalAlpha = a;
    Rm.corridor(ctx, { progress: (t - 14.0) / 0.7, t });
    ctx.restore();
  }

  // light sweeps (screen space)
  FX.lightSweep(ctx, W, H, U.windowed(t, 5.2, 5.6), 0.3);
  FX.lightSweep(ctx, W, H, U.windowed(t, 8.15, 8.45), 0.35);
  FX.lightSweep(ctx, W, H, U.windowed(t, 11.55, 11.9), 0.35);
  FX.lightSweep(ctx, W, H, U.windowed(t, 13.4, 13.9), 0.28);
  FX.lightSweep(ctx, W, H, U.windowed(t, 14.0, 14.3), 0.25);
  FX.lightSweep(ctx, W, H, U.windowed(t, 17.1, 17.5), 0.22);

  if (ph === 'trans4') drawArchPass(ctx, t);

  // titles
  if (ph === 'building' || ph === 'approach') drawTitle(ctx, t);
  if (ph === 'hero') drawTitleEnd(ctx, t);

  // room labels + annotations (full-room shots)
  if (ph === 'oval' || ph === 'expand') {
    drawRoomLabel(ctx, t, cam, 'oval', ROOM_TEXT.oval, 250, 168,
      { x: 250, y: 206 }, { x: 0 + FULL_ANCHOR.x, y: 86.8 + FULL_ANCHOR.y }, 6.3, 6.95);
  }
  if (ph === 'cabinet' || ph === 'trans4') {
    drawRoomLabel(ctx, t, cam, 'cabinet', ROOM_TEXT.cabinet, W - 250, 168,
      { x: W - 250, y: 206 }, { x: 0 + FULL_ANCHOR.x, y: 106 + FULL_ANCHOR.y }, 9.6, 10.25);
  }
  if (ph === 'dining') {
    drawRoomLabel(ctx, t, cam, 'dining', ROOM_TEXT.dining, W - 250, 150,
      { x: W - 250, y: 188 }, { x: 0 + FULL_ANCHOR.x, y: 110.8 + FULL_ANCHOR.y }, 13.35, 14.0);
  }
  if (ph === 'east') {
    drawRoomLabel(ctx, t, cam, 'east', ROOM_TEXT.east, 300, 140,
      { x: 300, y: 178 }, { x: 0 + FULL_ANCHOR.x, y: -206 + FULL_ANCHOR.y }, 16.15, 16.8);
  }

  // dollhouse mini labels + route annotation
  if (ph === 'approach') {
    drawMiniLabels(ctx, t, cam, false);
    const rp = U.kf([{ t: 4.5, v: 0 }, { t: 5.0, v: 1 }], t, U.ease.outCubic);
    if (rp > 0) {
      const a = worldToScreen(cam, 0, 20);
      const b = worldToScreen(cam, -255, 30);
      L.annotationLine(ctx, { x1: a.x, y1: a.y, x2: b.x, y2: b.y, progress: rp, t, color: '#c9a227', width: 2.4 });
    }
  }
  if (ph === 'hero') {
    drawMiniLabels(ctx, t, cam, true);
  }

  // ---- final FX pass ----
  FX.grade(ctx, W, H, 0.12);
  FX.vignette(ctx, W, H, 0.5);
  FX.grain(ctx, Math.floor(t * 30), W, H, 0.045);
}

module.exports = { renderFrame, worldToScreen, FULL_ROOM, FULL_ANCHOR, ROOM_TEXT, MINI_ANCHORS };
