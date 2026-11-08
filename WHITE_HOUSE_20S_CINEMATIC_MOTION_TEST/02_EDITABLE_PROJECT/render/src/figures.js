'use strict';
/* figures.js — articulated miniature characters (separate head/torso/arms/legs layers) */

const U = require('./util');
const A = require('./art');

// capsule limb with ink outline
function limb(ctx, x1, y1, x2, y2, w, color, outline = '#2f2a24') {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = w;
  ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
  ctx.strokeStyle = outline;
  ctx.lineWidth = w * 0.34;
  ctx.globalAlpha = 0.75;
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
  ctx.restore();
}

// o = {pose:'walk'|'stand'|'sit'|'idle', phase, facing, suit, skin, scale, alpha, behindTable}
function figure(ctx, x, y, s, o = {}) {
  const f = o.facing || 1;
  const suit = o.suit || '#2c3e55';
  const skin = o.skin || '#e3b98c';
  const suitDark = '#1d2b3d';
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(s * f, s); // mirror via negative scale
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;

  const T = o.phase || 0;
  let thighL = 0, thighR = 0, shinL = 0, shinR = 0, armL = 0, armR = 0, bob = 0, lean = 0, headTilt = 0;
  if (o.pose === 'walk') {
    const sw = Math.sin(T * U.TAU);
    thighL = sw * 0.42; thighR = -sw * 0.42;
    shinL = Math.max(0, Math.sin(T * U.TAU + 0.8)) * 0.55;
    shinR = Math.max(0, Math.sin(T * U.TAU - 0.8)) * 0.55;
    armL = -sw * 0.35; armR = sw * 0.35;
    bob = Math.abs(Math.sin(T * U.TAU * 2)) * 1.6;
    lean = 0.04;
  } else if (o.pose === 'idle' || o.pose === 'stand') {
    const breath = Math.sin(T * 1.7);
    armL = 0.05 + breath * 0.03; armR = -0.05 - breath * 0.03;
    bob = breath * 0.8;
    headTilt = Math.sin(T * 1.1) * 0.03;
  } else if (o.pose === 'sit') {
    thighL = thighR = -1.15; shinL = shinR = 1.35;
    armL = 0.1; armR = -0.1;
    bob = Math.sin(T * 1.6) * 0.6;
  }
  const H = 58; // total height units at s=1
  const hipY = -26;
  const shoulderY = -46;
  const headY = -55;

  // ---- back leg ----
  const hipX = 0;
  const legLen = 26;
  const footL = { x: Math.sin(thighL) * legLen, y: hipY + Math.cos(thighL) * legLen };
  const knee = { x: Math.sin(thighL) * legLen * 0.55, y: hipY + Math.cos(thighL) * legLen * 0.55 };
  const footPos = { x: footL.x + Math.sin(shinL) * legLen * 0.5, y: footL.y + Math.cos(shinL) * legLen * 0.5 };
  limb(ctx, hipX, hipY + bob, knee.x, knee.y + bob, 6.5, suitDark);
  limb(ctx, knee.x, knee.y + bob, footPos.x, Math.max(footPos.y, hipY - 1), 5.5, suitDark);
  // back foot
  ctx.fillStyle = '#241f1a';
  ctx.beginPath();
  ctx.ellipse(footPos.x + 3, Math.max(footPos.y, hipY - 1), 5, 2.6, 0, 0, U.TAU);
  ctx.fill();

  // ---- back arm ----
  const shX = 0, shY = shoulderY + bob;
  const armLen = 17;
  const elbowB = { x: shX + Math.sin(armL) * armLen * 0.55, y: shY + Math.cos(armL) * armLen * 0.55 + 6 };
  const handB = { x: elbowB.x + Math.sin(armL + 0.25) * armLen * 0.5, y: elbowB.y + Math.cos(armL + 0.25) * armLen * 0.5 + 5 };
  limb(ctx, shX, shY, elbowB.x, elbowB.y, 5, suitDark);
  limb(ctx, elbowB.x, elbowB.y, handB.x, handB.y, 4.2, skin);
  // hand
  ctx.fillStyle = skin;
  ctx.beginPath(); ctx.arc(handB.x, handB.y, 2.6, 0, U.TAU); ctx.fill();

  // ---- torso ----
  ctx.save();
  ctx.translate(0, bob);
  ctx.rotate(lean);
  ctx.fillStyle = suit;
  A.roundRect(ctx, -8, shoulderY, 16, shoulderY * -1 + hipY - shoulderY + 2, 6);
  // wait: draw torso capsule from shoulderY to hipY
  ctx.beginPath();
  A.rrPath(ctx, -8, shoulderY, 16, hipY - shoulderY + 3, 6);
  ctx.fill();
  ctx.strokeStyle = '#2f2a24'; ctx.lineWidth = 1.8; ctx.globalAlpha = 0.8; ctx.stroke();
  ctx.globalAlpha = 1;
  // jacket shading
  ctx.fillStyle = 'rgba(0,0,0,0.14)';
  ctx.fillRect(-8, shoulderY + 2, 4, hipY - shoulderY);
  // tie
  if (o.tie !== false) {
    ctx.fillStyle = '#8f3a30';
    ctx.beginPath();
    ctx.moveTo(-2.4, shoulderY + 4);
    ctx.lineTo(2.4, shoulderY + 4);
    ctx.lineTo(1.4, shoulderY + 13);
    ctx.lineTo(0, shoulderY + 17);
    ctx.lineTo(-1.4, shoulderY + 13);
    ctx.closePath();
    ctx.fill();
  }
  ctx.restore();

  // ---- front leg ----
  const footR = { x: Math.sin(thighR) * legLen, y: hipY + Math.cos(thighR) * legLen };
  const kneeR = { x: Math.sin(thighR) * legLen * 0.55, y: hipY + Math.cos(thighR) * legLen * 0.55 };
  const footPosR = { x: footR.x + Math.sin(shinR) * legLen * 0.5, y: footR.y + Math.cos(shinR) * legLen * 0.5 };
  limb(ctx, hipX, hipY + bob, kneeR.x, kneeR.y + bob, 7, suit);
  limb(ctx, kneeR.x, kneeR.y + bob, footPosR.x, Math.max(footPosR.y, hipY - 1), 6, suit);
  ctx.fillStyle = '#171410';
  ctx.beginPath();
  ctx.ellipse(footPosR.x + 3, Math.max(footPosR.y, hipY - 1), 5.5, 2.8, 0, 0, U.TAU);
  ctx.fill();

  // ---- front arm ----
  const elbowF = { x: shX + Math.sin(armR) * armLen * 0.55, y: shY + Math.cos(armR) * armLen * 0.55 + 6 };
  const handF = { x: elbowF.x + Math.sin(armR + 0.3) * armLen * 0.5, y: elbowF.y + Math.cos(armR + 0.3) * armLen * 0.5 + 5 };
  limb(ctx, shX, shY, elbowF.x, elbowF.y, 5.4, suit);
  limb(ctx, elbowF.x, elbowF.y, handF.x, handF.y, 4.4, skin);
  ctx.fillStyle = skin;
  ctx.beginPath(); ctx.arc(handF.x, handF.y, 2.8, 0, U.TAU); ctx.fill();

  // ---- head ----
  ctx.save();
  ctx.translate(0, headY + bob);
  ctx.rotate(headTilt);
  // neck
  limb(ctx, 0, 4, 0, -2, 4.4, skin);
  // head
  ctx.fillStyle = skin;
  ctx.beginPath(); ctx.ellipse(0, -6, 7.2, 8, 0, 0, U.TAU); ctx.fill();
  ctx.strokeStyle = '#2f2a24'; ctx.lineWidth = 1.7; ctx.globalAlpha = 0.8; ctx.stroke();
  ctx.globalAlpha = 1;
  // hair
  ctx.fillStyle = o.hair || '#3a2f24';
  ctx.beginPath();
  ctx.ellipse(0, -10, 7.4, 5.2, 0, Math.PI, U.TAU);
  ctx.fill();
  ctx.beginPath();
  ctx.ellipse(-5.6, -8, 2.4, 5, 0.3, 0, U.TAU);
  ctx.fill();
  // eye
  ctx.fillStyle = '#2f2a24';
  ctx.beginPath(); ctx.arc(2.6, -6.5, 1.1, 0, U.TAU); ctx.fill();
  // slight mouth
  ctx.strokeStyle = '#a07858'; ctx.lineWidth = 0.9;
  ctx.beginPath(); ctx.moveTo(0.5, -2.4); ctx.quadraticCurveTo(2.4, -2.9, 4.2, -2.5); ctx.stroke();
  ctx.restore();

  ctx.restore();
}

// seated figure behind a table (only head+torso visible above table edge)
function seatedFigure(ctx, x, y, s, o = {}) {
  const f = o.facing || 1;
  const suit = o.suit || '#3a3a3f';
  const skin = o.skin || '#e3b98c';
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(s * f, s);
  if (o.alpha !== undefined) ctx.globalAlpha = o.alpha;
  const T = o.phase || 0;
  const breath = Math.sin(T * 1.6);
  // torso
  A.rrPath(ctx, -9, -34 - breath * 0.5, 18, 30, 7);
  ctx.fillStyle = suit;
  ctx.fill();
  ctx.strokeStyle = '#2f2a24'; ctx.lineWidth = 1.8; ctx.globalAlpha = 0.8; ctx.stroke();
  ctx.globalAlpha = 1;
  // arms on table (forearms)
  limb(ctx, -6, -32, -14, -24, 5, suit);
  limb(ctx, 6, -32, 14, -24, 5, suit);
  ctx.fillStyle = skin;
  ctx.beginPath(); ctx.arc(-15, -23, 2.6, 0, U.TAU); ctx.fill();
  ctx.beginPath(); ctx.arc(15, -23, 2.6, 0, U.TAU); ctx.fill();
  // head (slight turn)
  ctx.save();
  ctx.translate(breath * 1.2, -46);
  ctx.rotate(Math.sin(T * 0.9) * 0.06);
  ctx.fillStyle = skin;
  ctx.beginPath(); ctx.ellipse(0, 0, 7.4, 8.2, 0, 0, U.TAU); ctx.fill();
  ctx.strokeStyle = '#2f2a24'; ctx.lineWidth = 1.7; ctx.globalAlpha = 0.8; ctx.stroke();
  ctx.globalAlpha = 1;
  ctx.fillStyle = o.hair || '#3a2f24';
  ctx.beginPath(); ctx.ellipse(0, -4, 7.6, 5.4, 0, Math.PI, U.TAU); ctx.fill();
  ctx.fillStyle = '#2f2a24';
  ctx.beginPath(); ctx.arc(3 + Math.sin(T * 0.9) * 1.5, 0.5, 1.1, 0, U.TAU); ctx.fill();
  ctx.restore();
  ctx.restore();
}

module.exports = { figure, seatedFigure };
