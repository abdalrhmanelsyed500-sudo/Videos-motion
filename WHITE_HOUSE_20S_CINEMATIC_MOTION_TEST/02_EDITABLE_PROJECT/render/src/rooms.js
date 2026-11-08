'use strict';
/* rooms.js — 2.5D interior engine: perspective projector, room shells,
   and the four White House rooms (Oval Office, Cabinet Room, State Dining Room, East Room)
   rendered at full scale (R=1) or miniature dollhouse scale (R≈0.32). */

const U = require('./util');
const A = require('./art');
const T = require('./textures');
const P = require('./props');
const F = require('./figures');

// ---------- projectors ----------
function floorProjector(room, R) {
  const { cx, yTop, wallH, Hf, Wb, Wf, skew } = room;
  return (u, v) => {
    const half = U.lerp(Wb / 2, Wf / 2, v) * R;
    return {
      x: cx + half * u + skew * v * R,
      y: yTop + wallH * R + Hf * v * R,
      s: U.lerp(0.72, 1.05, v) * R,
    };
  };
}
function wallProjector(room, R) {
  const { cx, yTop, wallH, Wb, Wf, skew } = room;
  return (u, v) => {
    const half = U.lerp(Wb / 2, Wf / 2, v) * R;
    return {
      x: cx + half * u + skew * v * R,
      y: yTop + wallH * v * R,
    };
  };
}

// ---------- room shell: ceiling, walls, floor, moldings ----------
function roomShell(ctx, room, R, o = {}) {
  const { cx, yTop, wallH, Hf, Wb, Wf, skew } = room;
  const ceilDrop = 30 * R;
  const fx = (v) => cx + U.lerp(Wb / 2, Wf / 2, v) * R + skew * v * R;
  // ceiling
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(cx - Wb / 2 * R, yTop);
  ctx.lineTo(cx + Wb / 2 * R, yTop);
  ctx.lineTo(fx(1) + 0, yTop + ceilDrop);
  ctx.lineTo(fx(0) + 0, yTop + ceilDrop);
  ctx.closePath();
  const cg = ctx.createLinearGradient(0, yTop, 0, yTop + ceilDrop + wallH * R);
  cg.addColorStop(0, 'rgba(244,235,218,0.0)');
  cg.addColorStop(1, o.ceilTint || 'rgba(233,221,196,0.5)');
  ctx.fillStyle = cg;
  ctx.fill();
  ctx.restore();

  // back wall
  A.inkRect(ctx, cx - Wb / 2 * R, yTop, Wb * R, wallH * R, {
    fill: o.wallFill || '#f0e7d3', tex: T.T.plaster(), tint: o.wallTint || '#e8ddc4', tintA: 0.5,
    strokeW: 2.6 * R, strokeA: o.wallStrokeA !== undefined ? o.wallStrokeA : 0.85, jitter: 1.2 * R, inner: o.wallInner !== false,
  });
  // crown molding
  A.inkRect(ctx, cx - Wb / 2 * R - 4 * R, yTop - 6 * R, Wb * R + 8 * R, 9 * R, {
    fill: '#e6dcc4', strokeW: 2.2 * R, strokeA: 0.8, jitter: 1 * R,
  });
  // wainscot (wood paneling lower half)
  const wcTop = yTop + wallH * R * 0.52;
  A.inkRect(ctx, cx - Wb / 2 * R, wcTop, Wb * R, wallH * R - (wcTop - yTop), {
    fill: '#9a7446', tex: T.T.woodDark(), tint: '#8a6238', tintA: 0.5,
    strokeW: 2.4 * R, strokeA: 0.8, jitter: 1.1 * R,
  });
  // panel lines
  ctx.save();
  ctx.strokeStyle = 'rgba(60,40,20,0.35)';
  ctx.lineWidth = 1.4 * R;
  const pcount = Math.max(4, Math.round(Wb * R / 90));
  for (let i = 1; i < pcount; i++) {
    const px = cx - Wb / 2 * R + (Wb * R / pcount) * i;
    ctx.beginPath(); ctx.moveTo(px, wcTop + 6 * R); ctx.lineTo(px, yTop + wallH * R - 4 * R); ctx.stroke();
  }
  // rail
  ctx.strokeStyle = '#c9a227'; ctx.lineWidth = 2.6 * R;
  ctx.beginPath(); ctx.moveTo(cx - Wb / 2 * R - 4 * R, wcTop + 2 * R); ctx.lineTo(cx + Wb / 2 * R + 4 * R, wcTop + 2 * R); ctx.stroke();
  ctx.restore();
  // baseboard
  A.inkRect(ctx, cx - Wb / 2 * R - 4 * R, yTop + wallH * R - 8 * R, Wb * R + 8 * R, 10 * R, {
    fill: '#d8caa8', strokeW: 2 * R, strokeA: 0.75, jitter: 1 * R,
  });

  // side walls (left + right trapezoids)
  for (const sgn of [-1, 1]) {
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(cx + sgn * Wb / 2 * R, yTop);
    ctx.lineTo(cx + sgn * Wb / 2 * R, yTop + wallH * R);
    ctx.lineTo(fx(1) * 0 + cx + sgn * U.lerp(Wb / 2, Wf / 2, 1) * R + skew * R, yTop + wallH * R + Hf * R);
    ctx.lineTo(cx + sgn * U.lerp(Wb / 2, Wf / 2, 1) * R + skew * R, yTop + ceilDrop);
    ctx.closePath();
    const shade = sgn < 0 ? 0.0 : -0.06;
    ctx.fillStyle = o.sideFill || `rgb(${236 - shade * 40},${228 - shade * 36},${208 - shade * 30})`;
    ctx.fill();
    ctx.strokeStyle = '#2f2a24';
    ctx.lineWidth = 2.4 * R;
    ctx.globalAlpha = 0.7;
    ctx.stroke();
    ctx.globalAlpha = 1;
    // side wall wainscot strip
    ctx.save();
    ctx.clip();
    ctx.fillStyle = 'rgba(138,98,56,0.85)';
    ctx.fillRect(cx + sgn * Wb / 2 * R, wcTop, 200 * R, wallH * R - (wcTop - yTop));
    ctx.restore();
    ctx.restore();
  }

  // floor
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(cx - Wb / 2 * R, yTop + wallH * R);
  ctx.lineTo(cx + Wb / 2 * R, yTop + wallH * R);
  ctx.lineTo(fx(1), yTop + wallH * R + Hf * R);
  ctx.lineTo(fx(0), yTop + wallH * R + Hf * R);
  ctx.closePath();
  const pat = ctx.createPattern(T.T.woodLight(), 'repeat');
  ctx.fillStyle = pat;
  ctx.fill();
  ctx.globalAlpha = 0.18;
  ctx.fillStyle = '#7a5230';
  ctx.fill();
  ctx.globalAlpha = 1;
  ctx.strokeStyle = '#2f2a24';
  ctx.lineWidth = 2.6 * R;
  ctx.globalAlpha = 0.8;
  ctx.stroke();
  ctx.globalAlpha = 1;
  // floor plank seams (perspective fan)
  ctx.save();
  ctx.clip();
  ctx.strokeStyle = 'rgba(90,60,30,0.35)';
  ctx.lineWidth = 1.2 * R;
  const n = 9;
  for (let i = 0; i <= n; i++) {
    const t = i / n;
    const bx = U.lerp(cx - Wb / 2 * R, cx + Wb / 2 * R, t);
    const fxv = U.lerp(cx - Wf / 2 * R, cx + Wf / 2 * R, t) + skew * R;
    ctx.beginPath();
    ctx.moveTo(bx, yTop + wallH * R);
    ctx.lineTo(fxv, yTop + wallH * R + Hf * R);
    ctx.stroke();
  }
  // depth lines
  for (let i = 1; i <= 4; i++) {
    const v = i / 4;
    const y = yTop + wallH * R + Hf * R * v;
    const hw = U.lerp(Wb / 2, Wf / 2, v) * R;
    ctx.beginPath();
    ctx.moveTo(cx - hw, y);
    ctx.lineTo(cx + hw + skew * v * R, y);
    ctx.stroke();
  }
  ctx.restore();
  ctx.restore();
}

// ---------- wall-attached items helper ----------
function wallItem(ctx, room, R, u, vTop, fn, o = {}) {
  const w = wallProjector(room, R);
  const p = w(u, vTop);
  fn(ctx, p.x, p.y, R * (o.s || 1), o);
}

// ---------- OVAL OFFICE ----------
function ovalScene(ctx, room, R, o = {}) {
  const fp = floorProjector(room, R);
  const t = o.t || 0;
  roomShell(ctx, room, R, o.shell || {});
  // windows on back wall
  wallItem(ctx, room, R, -0.52, 0.3, (ctx2, x, y, s) => P.window(ctx2, x, y, s, { w: 100, h: 150 }));
  wallItem(ctx, room, R, 0.52, 0.3, (ctx2, x, y, s) => P.window(ctx2, x, y, s, { w: 100, h: 150 }));
  // painting between windows
  wallItem(ctx, room, R, 0, 0.14, (ctx2, x, y, s) => P.portrait(ctx2, x, y, s, { w: 54, h: 70 }));
  // rug
  const rug = fp(0, 0.5);
  P.rug(ctx, rug.x, rug.y, R * 1.05, { rx: 105, ry: 58 });
  // chair behind desk (drawn before desk — behind it)
  const chairP = fp(0, 0.14);
  P.chair(ctx, chairP.x, chairP.y, R * 0.92, { seatColor: '#7c3b32' });
  // desk
  const deskP = fp(0, 0.32);
  P.desk(ctx, deskP.x, deskP.y, R, { t });
  // fireplace on left wall (floor-standing, hugging wall plane)
  const fl = fp(-0.85, 0.02);
  P.fireplace(ctx, fl.x + 8 * R, fl.y, R, { t });
  // side chairs
  for (const su of [-0.52, 0.52]) {
    const cp = fp(su, 0.42);
    P.chair(ctx, cp.x, cp.y, R * 0.85, { rot: su < 0 ? 0.22 : -0.22 });
  }
  // bookshelf right
  const bs = fp(0.62, 0.62);
  P.bookshelf(ctx, bs.x, bs.y, R * 0.8, { seed: 3 });
  // lamp on desk side — place on floor left of desk
  const lampP = fp(-0.42, 0.4);
  P.lamp(ctx, lampP.x, lampP.y, R * 0.7, { t });
  // globe on shelf area
  const globeP = fp(0.62, 0.7);
  P.globe(ctx, globeP.x, globeP.y, R * 0.6);
  // standing staff figure beside desk
  if (o.figure !== false) {
    const figP = fp(0.5, 0.55);
    F.figure(ctx, figP.x, figP.y, R * 0.9, { pose: 'idle', phase: t * 0.9, facing: -0.6, suit: '#3a3a3f', hair: '#2f2418' });
  }
  // window light shafts
  const lightA = o.lightShaft !== false ? 0.1 : 0;
  if (lightA > 0) {
    const lw = wallProjector(room, R);
    const l1 = lw(-0.52, 0.3);
    A.lightShaft(ctx, l1.x, l1.y + 30 * R, 90 * R, 220 * R, 0.12, lightA * 0.7);
    const l2 = lw(0.52, 0.3);
    A.lightShaft(ctx, l2.x, l2.y + 30 * R, 90 * R, 220 * R, -0.12, lightA * 0.5);
  }
  // accent glow on rug
  if (o.accentGlow) {
    A.drawGlow(ctx, rug.x, rug.y - 20 * R, 120 * R, 0.25, 'warm');
  }
}

// ---------- CABINET ROOM ----------
function cabinetScene(ctx, room, R, o = {}) {
  const fp = floorProjector(room, R);
  const t = o.t || 0;
  roomShell(ctx, room, R, o.shell || {});
  // windows back wall
  wallItem(ctx, room, R, -0.42, 0.32, (c2, x, y, s) => P.window(c2, x, y, s, { w: 90, h: 140 }));
  wallItem(ctx, room, R, 0.42, 0.32, (c2, x, y, s) => P.window(c2, x, y, s, { w: 90, h: 140 }));
  // portrait above table
  wallItem(ctx, room, R, 0, 0.12, (c2, x, y, s) => P.portrait(c2, x, y, s, { w: 52, h: 66 }));
  // rug under table
  const rug = fp(0, 0.5);
  P.rug(ctx, rug.x, rug.y, R * 1.1, { rx: 120, ry: 62, alpha: o.rugAlpha });
  // seated figures behind table (drawn before table — hidden by table body)
  if (o.figures !== false) {
    const sf1 = fp(-0.24, 0.2);
    F.seatedFigure(ctx, sf1.x, sf1.y - 2 * R, R * 0.85, { phase: t * 0.8, facing: 1, suit: '#3a3a3f' });
    const sf2 = fp(0.24, 0.2);
    F.seatedFigure(ctx, sf2.x, sf2.y - 2 * R, R * 0.85, { phase: t * 0.8 + 1.3, facing: -1, suit: '#4a4a52' });
  }
  // chairs behind table (far side — before table)
  for (let i = -2; i <= 2; i++) {
    const cp = fp(i * 0.26, 0.24);
    P.chair(ctx, cp.x, cp.y, R * 0.8, { rot: 0.1 });
  }
  // president chair center behind table
  const pres = fp(0, 0.2);
  P.chair(ctx, pres.x, pres.y, R * 0.9, { seatColor: '#8f3a30' });
  // long conference table
  const tp = fp(0, 0.4);
  P.table(ctx, tp.x, tp.y, R, { w: 300 * R, d: 90 * R });
  // near-side chairs
  for (let i = -1; i <= 1; i += 2) {
    const cp = fp(i * 0.42, 0.68);
    P.chair(ctx, cp.x, cp.y, R * 0.75, { rot: -i * 0.16 });
  }
  // sideboard right
  const sb = fp(0.68, 0.55);
  P.sideboard(ctx, sb.x, sb.y, R * 0.75, { t });
  // bookshelf left
  const bs = fp(-0.7, 0.6);
  P.bookshelf(ctx, bs.x, bs.y, R * 0.75, { seed: 7 });
  // standing figure at table end (approaching)
  if (o.figure !== false) {
    const figP = fp(0.55, 0.75);
    F.figure(ctx, figP.x, figP.y, R * 0.9, { pose: 'idle', phase: t, facing: -0.8, suit: '#2c3e55', hair: '#3a2f24' });
  }
  // accent
  if (o.accentGlow) A.drawGlow(ctx, tp.x, tp.y - 30 * R, 150 * R, 0.2, 'warm');
}

// ---------- STATE DINING ROOM ----------
function diningScene(ctx, room, R, o = {}) {
  const fp = floorProjector(room, R);
  const t = o.t || 0;
  roomShell(ctx, room, R, o.shell || {});
  // fireplace center back wall (floor-standing)
  const fbase = fp(0, 0.02);
  P.fireplace(ctx, fbase.x, fbase.y, R, { t, w: 140 });
  // portrait above fireplace mantel
  wallItem(ctx, room, R, 0, 0.43, (c2, x, y, s) => P.portrait(c2, x, y, s, { w: 48, h: 60 }));
  // drapes on side walls (floor to ceiling)
  const dp1 = fp(-1, 0.02);
  P.drapes(ctx, dp1.x + 20 * R, dp1.y, R, { w: 70, h: 230, color: '#8f3a30' });
  const dp2 = fp(1, 0.02);
  P.drapes(ctx, dp2.x - 20 * R, dp2.y, R, { w: 70, h: 230, color: '#8f3a30' });
  // rug
  const rug = fp(0, 0.5);
  P.rug(ctx, rug.x, rug.y, R * 1.2, { rx: 140, ry: 66, alpha: o.rugAlpha });
  // chairs behind table (far side — before table)
  for (let i = -3; i <= 3; i++) {
    if (i === 0) continue;
    const cp = fp(i * 0.19, 0.3);
    P.chair(ctx, cp.x, cp.y, R * 0.78, { rot: 0.08 });
  }
  // dining table
  const tp = fp(0, 0.42);
  P.diningTable(ctx, tp.x, tp.y, R, { w: 320, t });
  // chairs near side + ends (after table)
  for (let i = -3; i <= 3; i++) {
    if (i === 0) continue;
    const cn = fp(i * 0.19, 0.62);
    P.chair(ctx, cn.x, cn.y, R * 0.72, { rot: -0.08 });
  }
  for (const eu of [-0.66, 0.66]) {
    const cp = fp(eu, 0.42);
    P.chair(ctx, cp.x, cp.y, R * 0.78, { rot: eu < 0 ? 1.2 : -1.2 });
  }
  // sideboard + eagle tables (floor pieces, front)
  const sb = fp(-0.66, 0.55);
  P.sideboard(ctx, sb.x, sb.y, R * 0.8, { t });
  const ea = fp(0.62, 0.55);
  P.eagleTable(ctx, ea.x, ea.y, R * 0.8, {});
  // chandelier above table center
  const ch = fp(0, 0.42);
  P.chandelier(ctx, ch.x, ch.y - 300 * R, R * 0.9, { t });
  // chandelier rod to ceiling
  ctx.save();
  ctx.strokeStyle = '#8a6a3a';
  ctx.lineWidth = 2 * R;
  ctx.beginPath();
  ctx.moveTo(ch.x, room.yTop + 30 * R * 0.42);
  ctx.lineTo(ch.x, ch.y - 300 * R + 18 * R * 0.9);
  ctx.stroke();
  ctx.restore();
  // chandelier light pool
  A.drawGlow(ctx, ch.x, ch.y, 90 * R, 0.3, 'gold');
  // window light shafts from sides
  if (o.lightShaft) {
    const lw = wallProjector(room, R);
    const l1 = lw(-0.78, 0.45);
    A.lightShaft(ctx, l1.x, l1.y + 20 * R, 70 * R, 200 * R, 0.1, 0.5);
    const l2 = lw(0.78, 0.45);
    A.lightShaft(ctx, l2.x, l2.y + 20 * R, 70 * R, 200 * R, -0.1, 0.4);
  }
  if (o.accentGlow) A.drawGlow(ctx, tp.x, tp.y - 20 * R, 160 * R, 0.22, 'warm');
}

// ---------- EAST ROOM ----------
function eastScene(ctx, room, R, o = {}) {
  const fp = floorProjector(room, R);
  const t = o.t || 0;
  roomShell(ctx, room, R, o.shell || {});
  // three tall windows on back wall
  for (let i = -1; i <= 1; i++) {
    wallItem(ctx, room, R, i * 0.46, 0.28, (c2, x, y, s) => P.window(c2, x, y, s, { w: 84, h: 210, skyTop: '#b8d2e6', skyBot: '#e8dcbe' }));
  }
  // drapery above windows (swags)
  // fireplace on side wall (floor-standing)
  const fl = fp(-0.85, 0.02);
  P.fireplace(ctx, fl.x + 8 * R, fl.y, R * 0.95, { t, w: 120 });
  // rug
  const rug = fp(0, 0.55);
  P.rug(ctx, rug.x, rug.y, R * 1.3, { rx: 155, ry: 72, alpha: o.rugAlpha });
  // piano (grand, against left-back)
  const piano = fp(-0.42, 0.3);
  P.piano(ctx, piano.x, piano.y, R, { rot: 0.1 });
  // sofas
  const sf1 = fp(-0.5, 0.6);
  P.sofa(ctx, sf1.x, sf1.y, R * 0.9, { rot: 0.14, color: '#8f3a30' });
  const sf2 = fp(0.5, 0.6);
  P.sofa(ctx, sf2.x, sf2.y, R * 0.9, { rot: -0.14, color: '#2f4460' });
  // side chairs
  const ch1 = fp(-0.12, 0.42);
  P.chair(ctx, ch1.x, ch1.y, R * 0.8, { rot: 0.3 });
  const ch2 = fp(0.12, 0.42);
  P.chair(ctx, ch2.x, ch2.y, R * 0.8, { rot: -0.3 });
  // plants
  const pl1 = fp(0.72, 0.5);
  P.plant(ctx, pl1.x, pl1.y, R * 0.85, { seed: 11 });
  const pl2 = fp(-0.72, 0.7);
  P.plant(ctx, pl2.x, pl2.y, R * 0.7, { seed: 13 });
  // bust
  const bs = fp(0.62, 0.42);
  P.bust(ctx, bs.x, bs.y, R * 0.8);
  // chandelier
  const ch = fp(0, 0.42);
  P.chandelier(ctx, ch.x, ch.y - 340 * R, R * 1.0, { t });
  ctx.save();
  ctx.strokeStyle = '#8a6a3a';
  ctx.lineWidth = 2 * R;
  ctx.beginPath();
  ctx.moveTo(ch.x, room.yTop + 30 * R * 0.42);
  ctx.lineTo(ch.x, ch.y - 340 * R + 18 * R);
  ctx.stroke();
  ctx.restore();
  A.drawGlow(ctx, ch.x, ch.y, 100 * R, 0.28, 'gold');
  // figure at piano
  if (o.figure !== false) {
    const figP = fp(-0.42, 0.55);
    F.figure(ctx, figP.x, figP.y, R * 0.9, { pose: 'stand', phase: t * 0.7, facing: -0.9, suit: '#3a3a3f', hair: '#2f2418' });
  }
  // sun light shafts through tall windows (animated shimmer)
  const shimmer = 0.9 + 0.1 * Math.sin(t * 1.3);
  const lw = wallProjector(room, R);
  for (let i = -1; i <= 1; i++) {
    const l = lw(i * 0.46, 0.28);
    A.lightShaft(ctx, l.x, l.y + 24 * R, 80 * R, 300 * R, i * 0.12, 0.1 * shimmer);
  }
  if (o.accentGlow) A.drawGlow(ctx, rug.x, rug.y - 24 * R, 170 * R, 0.2, 'warm');
}

// ---------- corridor (transition space shot 6) ----------
function corridor(ctx, o = {}) {
  // o: {progress, t, width} — tunnel with sliding parallax layers + walking figure
  const W = 1920, H = 1080;
  const cx = W / 2;
  const top = 180, bottom = 820;
  // ceiling
  ctx.save();
  ctx.fillStyle = '#e6dcc4';
  ctx.beginPath();
  ctx.moveTo(cx - 700, top - 40);
  ctx.lineTo(cx + 700, top - 40);
  ctx.lineTo(cx + 340, top + 40);
  ctx.lineTo(cx - 340, top + 40);
  ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = '#2f2a24'; ctx.lineWidth = 2.4; ctx.globalAlpha = 0.8; ctx.stroke();
  ctx.globalAlpha = 1;
  // floor
  ctx.fillStyle = '#c08a52';
  ctx.beginPath();
  ctx.moveTo(cx - 340, bottom);
  ctx.lineTo(cx + 340, bottom);
  ctx.lineTo(cx + 700, bottom + 90);
  ctx.lineTo(cx - 700, bottom + 90);
  ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = '#2f2a24'; ctx.lineWidth = 2.4; ctx.globalAlpha = 0.8; ctx.stroke();
  ctx.globalAlpha = 1;
  // side walls with sliding panel lines (parallax)
  for (const sgn of [-1, 1]) {
    ctx.save();
    ctx.fillStyle = '#efe6d2';
    ctx.beginPath();
    ctx.moveTo(cx + sgn * 340, top + 40);
    ctx.lineTo(cx + sgn * 700, top - 40);
    ctx.lineTo(cx + sgn * 700, bottom + 90);
    ctx.lineTo(cx + sgn * 340, bottom);
    ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = '#2f2a24'; ctx.lineWidth = 2.4; ctx.globalAlpha = 0.8; ctx.stroke();
    ctx.globalAlpha = 1;
    // panel lines sliding toward viewer
    ctx.save();
    ctx.clip();
    ctx.strokeStyle = 'rgba(120,90,50,0.4)';
    ctx.lineWidth = 1.6;
    const speed = 260;
    for (let i = -8; i < 20; i++) {
      const ph = (o.progress * speed + i * 120) % (bottom + 90 - (top + 40));
      const y = top + 40 + ph;
      ctx.beginPath();
      ctx.moveTo(cx + sgn * 340, y);
      ctx.lineTo(cx + sgn * 700, y - 30);
      ctx.stroke();
    }
    // baseboard
    ctx.fillStyle = '#d8caa8';
    ctx.fillRect(cx + sgn * 340, bottom - 14, 360, 14);
    ctx.restore();
    ctx.restore();
  }
  // ceiling light strips passing
  ctx.save();
  for (let i = -4; i < 10; i++) {
    const ph = (o.progress * 300 + i * 150) % 1500;
    const y = top - 6 + (ph % 120);
    const a = 0.25 + 0.25 * Math.sin((ph / 1500) * Math.PI);
    A.drawGlow(ctx, cx, y, 60, a, 'cool');
  }
  ctx.restore();
  // walking figure ahead
  const figX = cx + Math.sin(o.progress * 2) * 26;
  const figY = bottom - 6;
  F.figure(ctx, figX, figY, 1.1, { pose: 'walk', phase: o.progress * 2.2, facing: 1, suit: '#2c3e55', hair: '#3a2f24' });
  // end glow (reveal ahead)
  A.drawGlow(ctx, cx, bottom + 30, 260, 0.22 + 0.1 * Math.sin(o.t * 2), 'warm');
}

module.exports = {
  roomShell, floorProjector, wallProjector, wallItem,
  ovalScene, cabinetScene, diningScene, eastScene, corridor,
};
