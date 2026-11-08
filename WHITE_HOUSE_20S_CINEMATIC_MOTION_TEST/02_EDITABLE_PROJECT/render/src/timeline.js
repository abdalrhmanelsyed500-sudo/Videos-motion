'use strict';
/* timeline.js — 20-second shot choreography: camera keyframes, element animation params.
   All times in seconds. 600 frames @30fps. */

const U = require('./util');

const W = 1920, H = 1080;
const T30 = (t) => Math.min(599, Math.max(0, Math.round(t * 30)));

// ---------- camera state ----------
function cameraAt(t) {
  const e = U.ease;
  // phase boundaries
  const phaseBuilding = t < 2.5;
  const phaseApproach = t < 5.0;
  const phaseExpand = t < 5.85;
  const phaseOval = t < 8.0;
  const phaseTrans4 = t < 8.5;
  const phaseCabinet = t < 11.0;
  const phaseDive = t < 11.5;
  const phaseWipe = t < 11.9;
  const phaseDining = t < 14.0;
  const phaseCorridor = t < 14.7;
  const phaseEast = t < 17.0;
  const phaseReverse = t < 17.9;

  if (phaseBuilding) {
    const f = e.inOutCubic(t / 2.5);
    return { x: 0, y: U.lerp(-270, -70, f), scale: U.lerp(0.58, 0.78, f), rot: U.lerp(0, 0.012, f) };
  }
  if (phaseApproach) {
    const f1 = e.inOutCubic(U.clamp((t - 2.5) / 1.7, 0, 1));
    const f2 = e.inOutCubic(U.clamp((t - 4.2) / 0.8, 0, 1));
    return {
      x: U.lerp(0, 0, f1) + U.lerp(0, -170, f2),
      y: U.lerp(-70, 10, f1) + U.lerp(0, 45, f2),
      scale: U.lerp(0.78, 1.02, f1) + U.lerp(0, 0.1, f2),
      rot: U.lerp(0.012, 0.018, U.clamp((t - 2.5) / 2.5, 0, 1)),
    };
  }
  if (phaseExpand) {
    const g = e.outCubic(U.clamp((t - 5.0) / 0.85, 0, 1));
    return {
      x: U.lerp(-170, 0, g),
      y: U.lerp(55, -20, g),
      scale: U.lerp(1.12, 1.15, g),
      rot: 0.015 * (1 - g * 0.5),
    };
  }
  if (phaseOval) {
    const tt = t - 5.85;
    const drift = U.kf([{ t: 7.5, v: 0 }, { t: 8.0, v: 150 }], t);
    return {
      x: 26 * Math.sin(tt * 0.75) + drift,
      y: -20 + 9 * Math.sin(tt * 0.55) - U.kf([{ t: 7.6, v: 0 }, { t: 8.0, v: 12 }], t),
      scale: 1.15,
      rot: 0.01 * Math.sin(tt * 0.4),
    };
  }
  if (phaseTrans4) {
    const f = e.inOutCubic((t - 8.0) / 0.5);
    return { x: U.lerp(150, 0, f), y: U.lerp(-25, -10, f), scale: U.lerp(1.15, 1.1, f), rot: 0.008 * (1 - f) };
  }
  if (phaseCabinet) {
    const tt = t - 8.5;
    return {
      x: 55 * Math.sin(tt * 0.55),
      y: -10 + 7 * Math.sin(tt * 0.4),
      scale: 1.1,
      rot: 0.008 * Math.sin(tt * 0.3),
    };
  }
  if (phaseDive) {
    const f = e.inOutCubic((t - 11.0) / 0.5);
    return { x: U.lerp(55 * Math.sin((11.0 - 8.5) * 0.55), 0, f), y: U.lerp(-10, 106, f), scale: U.lerp(1.1, 2.4, f), rot: 0 };
  }
  if (phaseWipe) {
    return { x: 0, y: 106, scale: 2.4, rot: 0 };
  }
  if (phaseDining) {
    return {
      x: U.kf([{ t: 11.9, v: 0 }, { t: 12.8, v: -70 }, { t: 14.0, v: 62 }], t, e.inOutCubic),
      y: U.kf([{ t: 11.9, v: 106 }, { t: 12.6, v: 18 }, { t: 14.0, v: -34 }], t, e.inOutCubic),
      scale: U.kf([{ t: 11.9, v: 2.4 }, { t: 12.6, v: 1.25 }, { t: 14.0, v: 1.12 }], t, e.inOutCubic),
      rot: 0,
    };
  }
  if (phaseEast) {
    return {
      x: U.kf([{ t: 14.7, v: 0 }, { t: 15.0, v: -60 }, { t: 16.2, v: -28 }, { t: 17.0, v: 18 }], t, e.inOutCubic),
      y: U.kf([{ t: 14.7, v: -20 }, { t: 15.9, v: -130 }, { t: 17.0, v: -52 }], t, e.inOutCubic),
      scale: U.kf([{ t: 14.7, v: 1.15 }, { t: 15.9, v: 1.1 }, { t: 17.0, v: 1.12 }], t, e.inOutCubic),
      rot: 0,
    };
  }
  if (phaseReverse) {
    const f = e.inOutCubic((t - 17.0) / 0.9);
    return { x: U.lerp(18, 0, f), y: U.lerp(-52, -90, f), scale: U.lerp(1.12, 0.85, f), rot: 0 };
  }
  // hero
  const tt = t - 17.9;
  return { x: 9 * Math.sin(tt * 0.7), y: -90 + 7 * Math.sin(tt * 0.5), scale: 0.85, rot: 0 };
}

// ---------- building animation params ----------
function buildingParams(t) {
  const drawOn = U.clamp(U.kf([{ t: 0.1, v: 0 }, { t: 2.1, v: 1 }], t, U.ease.outCubic), 0, 1);
  const roofLift = U.kf([{ t: 2.5, v: 0 }, { t: 3.0, v: 0 }, { t: 4.15, v: 1 }], t, U.ease.outCubic);
  const wallSlide = U.kf([{ t: 2.5, v: 0 }, { t: 3.4, v: 0 }, { t: 4.45, v: 1 }], t, U.ease.inOutCubic);
  const interiorReveal = U.kf([{ t: 3.6, v: 0 }, { t: 4.65, v: 1 }], t, U.ease.inOutCubic);
  // hero: roof descends, wall stays open (cutaway remains)
  const roofLiftEnd = U.kf([{ t: 17.4, v: roofLift }, { t: 18.4, v: 0 }], t, U.ease.inOutCubic);
  return {
    drawOn,
    roofLift: t > 17.0 ? roofLiftEnd : roofLift,
    wallSlide: t > 17.0 ? 1 : wallSlide,
    interiorReveal: t > 17.0 ? 1 : interiorReveal,
  };
}

// ---------- room expansion / reverse params ----------
function expansionG(t) {
  if (t < 5.0) return 0;
  if (t < 5.85) return U.ease.outCubic(U.clamp((t - 5.0) / 0.85, 0, 1));
  if (t < 8.0) return 1;
  if (t < 11.5) return 1;
  if (t < 17.0) return 1;
  if (t < 17.9) return U.lerp(1, 0.3, U.ease.inOutCubic((t - 17.0) / 0.9));
  return 0.3;
}
function roomOffset(g, roomAnchorMini) {
  // full room anchor (world) = (0, -20); mini anchor for room = roomAnchorMini
  return { x: U.lerp(roomAnchorMini.x, 0, g), y: U.lerp(roomAnchorMini.y, -20, g) };
}

// ---------- shot-phase helper ----------
function phase(t) {
  if (t < 2.5) return 'building';
  if (t < 5.0) return 'approach';
  if (t < 5.85) return 'expand';
  if (t < 8.0) return 'oval';
  if (t < 8.5) return 'trans4';
  if (t < 11.0) return 'cabinet';
  if (t < 11.5) return 'dive';
  if (t < 11.9) return 'wipe';
  if (t < 14.0) return 'dining';
  if (t < 14.7) return 'corridor';
  if (t < 17.0) return 'east';
  if (t < 17.9) return 'reverse';
  return 'hero';
}

// ---------- label reveal windows ----------
const LABELS = {
  title: { t0: 1.0, t1: 1.7, type: 'mask', size: 64, weight: '700', family: 'Amiri' },
  subtitle: { t0: 1.3, t1: 1.95, type: 'fade' },
  oval: { t0: 6.0, t1: 6.7, type: 'slide' },
  cabinet: { t0: 9.2, t1: 9.9, type: 'mask' },
  dining: { t0: 12.9, t1: 13.6, type: 'slide' },
  east: { t0: 15.7, t1: 16.4, type: 'mask' },
  miniOval: { t0: 4.4, t1: 5.0, type: 'fade', size: 15 },
  miniCabinet: { t0: 4.4, t1: 5.0, type: 'fade', size: 15 },
  miniDining: { t0: 4.5, t1: 5.05, type: 'fade', size: 15 },
  miniEast: { t0: 4.5, t1: 5.05, type: 'fade', size: 15 },
  // hero sequential
  heroOval: { t0: 18.35, t1: 18.9, type: 'scale', size: 17 },
  heroCabinet: { t0: 18.85, t1: 19.4, type: 'scale', size: 17 },
  heroDining: { t0: 19.3, t1: 19.85, type: 'scale', size: 17 },
  heroEast: { t0: 19.75, t1: 20.0, type: 'scale', size: 17 },
  titleEnd: { t0: 19.2, t1: 19.85, type: 'scale', size: 58 },
  subtitleEnd: { t0: 19.5, t1: 20.0, type: 'fade' },
};
function labelReveal(name, t) {
  const L = LABELS[name];
  if (!L) return 0;
  if (t >= L.t1) return 1; // labels persist once revealed
  return U.windowed(t, L.t0, L.t1, U.ease.outCubic, U.ease.outCubic);
}

module.exports = { W, H, T30, cameraAt, buildingParams, expansionG, roomOffset, phase, LABELS, labelReveal };
