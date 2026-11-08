'use strict';
/* building.js — White House exterior (axonometric-ish elevation) + dollhouse cutaway interior */

const U = require('./util');
const A = require('./art');
const T = require('./textures');
const P = require('./props');
const R = require('./rooms');

// ---- mini room anchors (dollhouse floor plan) ----
const MINI = {
  oval:   { cx: -255, yTop: 30 },
  cabinet:{ cx: -255, yTop: -170 },
  dining: { cx: 255,  yTop: -170 },
  east:   { cx: 255,  yTop: 30 },
};
const MINI_R = 0.3;
const mkMiniRoom = (id) => ({
  id, cx: MINI[id].cx, yTop: MINI[id].yTop,
  wallH: 300, Hf: 240, Wb: 760, Wf: 950, skew: 40,
});

// ---- ground plane, walkway, landscaping ----
function ground(ctx, o = {}) {
  const alpha = o.alpha !== undefined ? o.alpha : 1;
  ctx.save();
  ctx.globalAlpha = alpha;
  // grass field
  const pat = ctx.createPattern(T.T.grass(), 'repeat');
  ctx.fillStyle = pat;
  ctx.fillRect(-1400, -320, 2800, 420);
  ctx.globalAlpha = 0.25;
  ctx.fillStyle = '#5f6e45';
  ctx.fillRect(-1400, -320, 2800, 420);
  ctx.globalAlpha = 1;
  // walkway to portico
  A.inkRect(ctx, -150, 30, 300, 130, {
    fill: '#ded4c1', tex: T.T.stone(), hatch: true, strokeW: 2.4, strokeA: 0.8, jitter: 1.2, inner: false,
  });
  // hedges
  for (const hx of [-560, -480, 480, 560]) {
    ctx.fillStyle = '#5e7a4a';
    ctx.beginPath(); ctx.ellipse(hx, 4, 70, 22, 0, 0, U.TAU); ctx.fill();
    ctx.strokeStyle = '#3d5526'; ctx.lineWidth = 1.6; ctx.stroke();
  }
  // trees behind
  A.tree(ctx, -760, -120, 1.5, { seed: 21, season: 'green' });
  A.tree(ctx, 760, -130, 1.6, { seed: 22, season: 'green' });
  A.tree(ctx, -620, -170, 1.1, { seed: 23, season: 'green' });
  A.tree(ctx, 640, -180, 1.2, { seed: 24, season: 'autumn' });
  ctx.restore();
}

// ---- main block walls (ivory, textured) ----
function blockWalls(ctx, o = {}) {
  const alpha = o.alpha !== undefined ? o.alpha : 1;
  ctx.save();
  ctx.globalAlpha = alpha;
  // main block
  A.inkRect(ctx, -420, -188, 840, 188, {
    fill: '#f0e7d3', tex: T.T.plaster(), tint: '#e8ddc4', tintA: 0.5,
    strokeW: 3, strokeA: 0.9, jitter: 1.4,
  });
  // corner pilasters
  for (const px of [-420, 420]) {
    A.inkRect(ctx, px - 16, -188, 32, 188, {
      fill: '#e8dcc2', strokeW: 2.4, strokeA: 0.8, jitter: 1.1,
    });
  }
  // cornice + parapet
  A.inkRect(ctx, -436, -208, 872, 22, {
    fill: '#e2d6ba', strokeW: 2.8, strokeA: 0.85, jitter: 1.2,
  });
  A.inkRect(ctx, -440, -214, 880, 8, { fill: '#d8caa8', strokeW: 2, strokeA: 0.7, jitter: 1 });
  // wings
  for (const [wx, ww] of [[-650, 230], [420, 230]]) {
    A.inkRect(ctx, wx, -140, ww, 140, {
      fill: '#ede4ce', tex: T.T.plaster(), tint: '#e2d6ba', tintA: 0.45,
      strokeW: 2.8, strokeA: 0.85, jitter: 1.2,
    });
    A.inkRect(ctx, wx - 8, -152, ww + 16, 14, { fill: '#e2d6ba', strokeW: 2.2, strokeA: 0.8, jitter: 1 });
  }
  ctx.restore();
}

// ---- facade openings: windows grid + doors (on sliding wall) ----
function facade(ctx, o = {}) {
  const alpha = o.alpha !== undefined ? o.alpha : 1;
  const dx = o.dx || 0;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.translate(dx, 0);
  // window grid on main block (3 rows x 6)
  const cols = [-320, -192, -64, 64, 192, 320];
  const rows = [-42, -90, -138];
  for (const cy of rows) for (const cx of cols) {
    const wx = cx - 23, wy = cy - 29;
    A.inkRect(ctx, wx, wy, 46, 58, {
      fill: '#bcd4e4', strokeW: 2.2, strokeA: 0.8, jitter: 0.8, inner: false,
    });
    // glass sheen: partial white gradient at bottom only
    const sheen = ctx.createLinearGradient(0, wy, 0, wy + 58);
    sheen.addColorStop(0, 'rgba(255,255,255,0)');
    sheen.addColorStop(0.7, 'rgba(240,235,220,0.25)');
    sheen.addColorStop(1, 'rgba(240,235,220,0.55)');
    ctx.fillStyle = sheen;
    ctx.fillRect(wx + 1, wy + 1, 44, 56);
    ctx.strokeStyle = '#e8ddc4';
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(cx, wy + 3); ctx.lineTo(cx, wy + 55); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(wx + 3, cy); ctx.lineTo(wx + 43, cy); ctx.stroke();
    // arch top
    ctx.beginPath();
    ctx.moveTo(wx, wy);
    ctx.quadraticCurveTo(cx, wy - 14, wx + 46, wy);
    ctx.stroke();
  }
  // side entrance doors
  for (const dx2 of [-340, 340]) {
    A.inkRect(ctx, dx2 - 20, -108, 40, 108, {
      fill: '#b98c52', tex: T.T.woodLight(), strokeW: 2.6, strokeA: 0.85, jitter: 1, inner: false,
    });
    ctx.strokeStyle = '#8a6a3a'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(dx2, -108); ctx.lineTo(dx2, 0); ctx.stroke();
    ctx.fillStyle = '#e8c98a';
    ctx.beginPath(); ctx.arc(dx2 + 12, -54, 2.6, 0, U.TAU); ctx.fill();
  }
  ctx.restore();
}

// ---- north portico: columns, pediment, steps, door ----
function portico(ctx, o = {}) {
  const alpha = o.alpha !== undefined ? o.alpha : 1;
  ctx.save();
  ctx.globalAlpha = alpha;
  // portico floor slab
  A.inkRect(ctx, -330, -6, 660, 30, {
    fill: '#ded4c1', tex: T.T.stone(), strokeW: 2.4, strokeA: 0.8, jitter: 1.1, inner: false,
  });
  // steps
  for (let i = 0; i < 3; i++) {
    A.inkRect(ctx, -120 + i * 6, 8 + i * 8, 240 - i * 12, 8, {
      fill: '#d8cfbc', strokeW: 2, strokeA: 0.75, jitter: 0.8, inner: false,
    });
  }
  // door behind columns
  P.doors(ctx, 0, -150, 1, { w: 90, h: 150 });
  // columns
  for (const cx of [-240, -80, 80, 240]) {
    P.column(ctx, cx, -6, 1, { w: 34, h: 148 });
  }
  // portico entablature
  A.inkRect(ctx, -300, -150, 600, 12, {
    fill: '#e2d6ba', strokeW: 2.6, strokeA: 0.85, jitter: 1.1,
  });
  // pediment
  ctx.beginPath();
  ctx.moveTo(-300, -162);
  ctx.lineTo(300, -162);
  ctx.lineTo(0, -214);
  ctx.closePath();
  ctx.fillStyle = '#e8dec8';
  ctx.fill();
  ctx.strokeStyle = '#2f2a24'; ctx.lineWidth = 2.8; ctx.globalAlpha = 0.85; ctx.stroke();
  ctx.globalAlpha = alpha;
  // pediment star decoration
  ctx.fillStyle = '#c9a227';
  ctx.beginPath();
  for (let i = 0; i < 10; i++) {
    const a = -Math.PI / 2 + (i / 10) * U.TAU;
    const rr = i % 2 ? 9 : 16;
    ctx.lineTo(Math.cos(a) * rr, -186 + Math.sin(a) * rr);
  }
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

// ---- roofs (liftable slabs) ----
function roofs(ctx, o = {}) {
  const alpha = o.alpha !== undefined ? o.alpha : 1;
  const lift = o.lift || 0;
  ctx.save();
  ctx.globalAlpha = alpha;
  P.roofSection(ctx, 0, -204 - lift, 1, { w: 880, h: 52 });
  P.roofSection(ctx, -535, -148 - lift * 0.8, 1, { w: 250, h: 44 });
  P.roofSection(ctx, 535, -148 - lift * 0.8, 1, { w: 250, h: 44 });
  // chimneys
  for (const cx of [-330, 330]) {
    A.inkRect(ctx, cx - 14, -258 - lift, 28, 54, {
      fill: '#8a5a33', tex: T.T.woodDark(), strokeW: 2.2, strokeA: 0.8, jitter: 0.8,
    });
  }
  // flagpole on main roof
  ctx.strokeStyle = '#5b3c22';
  ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(-380, -204 - lift); ctx.lineTo(-380, -300 - lift); ctx.stroke();
  ctx.fillStyle = '#2f4a7a';
  ctx.beginPath();
  ctx.moveTo(-380, -296 - lift);
  ctx.lineTo(-352, -290 - lift);
  ctx.lineTo(-380, -280 - lift);
  ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = '#2f2a24'; ctx.lineWidth = 1.4; ctx.globalAlpha = 0.7; ctx.stroke();
  ctx.globalAlpha = alpha;
  ctx.restore();
}

// ---- dollhouse cutaway interior ----
function cutaway(ctx, o = {}) {
  const alpha = o.alpha !== undefined ? o.alpha : 1;
  const highlight = o.highlight || null;
  const rooms = o.rooms || { oval: true, cabinet: true, dining: true, east: true };
  ctx.save();
  ctx.globalAlpha = alpha;
  // interior floor slab
  A.inkRect(ctx, -430, 4, 860, 120, {
    fill: '#c08a52', tex: T.T.woodLight(), hatch: true,
    strokeW: 2.8, strokeA: 0.85, jitter: 1.2, inner: false,
  });
  // interior back wall (paneled)
  A.inkRect(ctx, -420, -188, 840, 188, {
    fill: '#8a6238', tex: T.T.woodDark(), tint: '#7a5430', tintA: 0.5, hatch: true,
    strokeW: 2.8, strokeA: 0.85, jitter: 1.2, inner: false,
  });
  // partition walls (plan view)
  ctx.save();
  ctx.strokeStyle = '#2f2a24';
  ctx.lineWidth = 7;
  ctx.lineCap = 'square';
  // horizontal partition
  ctx.beginPath(); ctx.moveTo(-400, -12); ctx.lineTo(400, -12); ctx.stroke();
  // vertical partitions
  ctx.beginPath(); ctx.moveTo(-110, -170); ctx.lineTo(-110, 205); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(110, -170); ctx.lineTo(110, 205); ctx.stroke();
  // door openings (arcs) on partitions
  ctx.lineWidth = 2.2;
  ctx.strokeStyle = '#f0e7d3';
  ctx.beginPath(); ctx.arc(-110, -12, 20, -Math.PI / 2, Math.PI / 2, true); ctx.stroke();
  ctx.beginPath(); ctx.arc(110, -12, 20, Math.PI / 2, -Math.PI / 2, true); ctx.stroke();
  ctx.beginPath(); ctx.arc(0, -12, 22, 0, Math.PI); ctx.stroke();
  ctx.restore();
  // staircase (plan view zigzag) in the center hall
  ctx.save();
  ctx.strokeStyle = '#2f2a24';
  ctx.lineWidth = 3;
  let sy = 20, sx = 40, dir = -1;
  for (let i = 0; i < 10; i++) {
    A.inkRect(ctx, sx, sy, 44, 16, { fill: '#c9a227', strokeW: 1.6, strokeA: 0.7, inner: false });
    sy += dir * 18;
    sx += dir * 44;
    dir *= -1;
  }
  ctx.restore();
  ctx.restore();

  // mini rooms
  const drawMini = (id, roomFn, extra = {}) => {
    const room = mkMiniRoom(id);
    ctx.save();
    if (highlight === id) {
      A.drawGlow(ctx, room.cx, room.yTop + 60, 150, 0.18, 'warm');
    }
    roomFn(ctx, room, MINI_R, { t: o.t || 0, ...extra });
    ctx.restore();
  };
  if (rooms.oval) drawMini('oval', R.ovalScene, { figure: false });
  if (rooms.cabinet) drawMini('cabinet', R.cabinetScene, { figure: false, figures: false });
  if (rooms.dining) drawMini('dining', R.diningScene, {});
  if (rooms.east) drawMini('east', R.eastScene, { figure: false });
}

// ---- full exterior with all layers & animation params ----
function whiteHouse(ctx, o = {}) {
  const {
    drawOn = 1, roofLift = 0, wallSlide = 0, interiorReveal = 0,
    showRooms = { oval: true, cabinet: true, dining: true, east: true },
    highlight = null, t = 0,
  } = o;
  ground(ctx, { alpha: U.clamp((drawOn - 0) / 0.25) });
  // cutaway interior revealed behind facade
  if (interiorReveal > 0) {
    cutaway(ctx, { alpha: interiorReveal, highlight, t, rooms: showRooms });
  }
  // main walls
  blockWalls(ctx, { alpha: U.clamp((drawOn - 0.08) / 0.22) * (1 - wallSlide * 0.75) });
  // facade (slides away)
  facade(ctx, { alpha: U.clamp((drawOn - 0.22) / 0.25) * (1 - wallSlide), dx: wallSlide * 420 });
  // portico stays
  portico(ctx, { alpha: U.clamp((drawOn - 0.45) / 0.25) });
  // roofs lift away
  roofs(ctx, { alpha: U.clamp((drawOn - 0.55) / 0.25) * (1 - roofLift), lift: roofLift * 150 });
  // outline silhouette keeps structure coherent
  ctx.save();
  ctx.globalAlpha = 0.8;
  ctx.strokeStyle = '#2f2a24';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(-650, 0); ctx.lineTo(-650, -140); ctx.lineTo(-436, -140); ctx.lineTo(-436, -208);
  ctx.lineTo(436, -208); ctx.lineTo(436, -140); ctx.lineTo(650, -140); ctx.lineTo(650, 0);
  ctx.stroke();
  ctx.restore();
}

// ---- room markers for grand reveal (shot 7) ----
function drawMarkers(ctx, o = {}) {
  const { progress = 0, labels } = o;
  if (!labels) return;
  const order = ['oval', 'cabinet', 'dining', 'east'];
  const pts = order.map(id => ({ id, x: MINI[id].cx, y: MINI[id].yTop + 40 }));
  // connecting lines (drawn progressively)
  ctx.save();
  ctx.globalAlpha = 0.8;
  const total = order.length - 1;
  for (let i = 0; i < total; i++) {
    const a = pts[i], b = pts[i + 1];
    const segStart = i / total;
    const segEnd = (i + 1) / total;
    const f = U.clamp((progress - segStart) / (segEnd - segStart), 0, 1);
    if (f <= 0) continue;
    const x2 = U.lerp(a.x, b.x, f), y2 = U.lerp(a.y, b.y, f);
    ctx.strokeStyle = '#c9a227';
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 6]);
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    ctx.setLineDash([]);
  }
  // dots + labels sequentially
  for (let i = 0; i < pts.length; i++) {
    const f = U.clamp((progress - i / total) / (0.5 / total), 0, 1);
    if (f <= 0) continue;
    const p = pts[i];
    ctx.globalAlpha = f;
    ctx.fillStyle = '#c9a227';
    ctx.beginPath(); ctx.arc(p.x, p.y, 7, 0, U.TAU); ctx.fill();
    ctx.strokeStyle = '#2f2a24'; ctx.lineWidth = 1.6; ctx.stroke();
  }
  ctx.restore();
}

module.exports = { whiteHouse, ground, blockWalls, facade, portico, roofs, cutaway, drawMarkers, MINI, MINI_R, mkMiniRoom };
