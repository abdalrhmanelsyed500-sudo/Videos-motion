'use strict';
/* export_assets.js — export separated production assets:
   textures, furniture sprites, architectural components, characters, text layers,
   plus a layer manifest JSON describing every animated layer. */
const { createCanvas, GlobalFonts } = require('@napi-rs/canvas');
const fs = require('fs');
const path = require('path');
const U = require('../src/util');
const A = require('../src/art');
const T = require('../src/textures');
const P = require('../src/props');
const F = require('../src/figures');
const L = require('../src/labels');

L.registerFonts();

const OUT = path.join(__dirname, '..', '..', '..', '03_SEPARATED_ASSETS');
const dirs = {
  textures: path.join(OUT, 'textures'),
  furniture: path.join(OUT, 'furniture'),
  architecture: path.join(OUT, 'architecture'),
  characters: path.join(OUT, 'characters'),
  text: path.join(OUT, 'text'),
  fx: path.join(OUT, 'fx'),
};
for (const d of Object.values(dirs)) fs.mkdirSync(d, { recursive: true });

function saveCanvas(cv, name, dir) {
  fs.writeFileSync(path.join(dir, name), cv.toBuffer('image/png'));
  console.log('✓', name);
}

// ---- textures ----
const texMap = {
  paper: T.T.paper(), plaster: T.T.plaster(), wood_light: T.T.woodLight(),
  wood_dark: T.T.woodDark(), wood_walnut: T.T.woodWalnut(), marble: T.T.marble(),
  velvet_red: T.T.velvetRed(), velvet_blue: T.T.velvetBlue(), velvet_gold: T.T.velvetGold(),
  grass: T.T.grass(), stone: T.T.stone(), sky: T.T.sky(),
};
for (const [k, cv] of Object.entries(texMap)) saveCanvas(cv, `${k}.png`, dirs.textures);

// ---- furniture sprites (transparent bg) ----
function sprite(drawFn, size, opts = {}) {
  const cv = createCanvas(size.w, size.h);
  const ctx = cv.getContext('2d');
  drawFn(ctx, size.w / 2, size.h - 12, opts.scale || 1, opts);
  return cv;
}
const furniture = {
  'chair_executive': (c, x, y, s) => P.chair(c, x, y, s),
  'desk_presidential': (c, x, y, s) => P.desk(c, x, y, s),
  'sofa': (c, x, y, s) => P.sofa(c, x, y, s),
  'table_conference': (c, x, y, s) => P.table(c, x, y, s, { w: 300, d: 90 }),
  'table_dining': (c, x, y, s) => P.diningTable(c, x, y, s, { w: 320 }),
  'sideboard': (c, x, y, s) => P.sideboard(c, x, y, s),
  'bookshelf': (c, x, y, s) => P.bookshelf(c, x, y, s, { seed: 5 }),
  'lamp_table': (c, x, y, s) => P.lamp(c, x, y, s),
  'chandelier': (c, x, y, s) => P.chandelier(c, x, y, s),
  'rug_oval_blue': (c, x, y, s) => P.rug(c, x, y, s, { rx: 110, ry: 62 }),
  'painting_framed': (c, x, y, s) => P.painting(c, x, y, s),
  'portrait': (c, x, y, s) => P.portrait(c, x, y, s),
  'drapes_red': (c, x, y, s) => P.drapes(c, x, y, s, { w: 90, h: 200 }),
  'fireplace': (c, x, y, s) => P.fireplace(c, x, y, s),
  'piano_grand': (c, x, y, s) => P.piano(c, x, y, s),
  'bust_pedestal': (c, x, y, s) => P.bust(c, x, y, s),
  'plant': (c, x, y, s) => P.plant(c, x, y, s, { seed: 9 }),
  'globe': (c, x, y, s) => P.globe(c, x, y, s),
  'telephone': (c, x, y, s) => P.telephone(c, x, y, s),
  'mug': (c, x, y, s) => P.mug(c, x, y, s),
  'vase_flowers': (c, x, y, s) => P.vase(c, x, y, s),
  'stack_books': (c, x, y, s) => P.stackBooks(c, x, y, s),
  'eagle_table': (c, x, y, s) => P.eagleTable(c, x, y, s),
};
for (const [name, fn] of Object.entries(furniture)) {
  saveCanvas(sprite(fn, { w: 360, h: 300 }, { scale: 1.2 }), `${name}.png`, dirs.furniture);
}

// ---- architecture components ----
const arch = {
  'column_fluted': (c, x, y, s) => P.column(c, x, y, s, { w: 34, h: 300 }),
  'roof_slate_slab': (c, x, y, s) => P.roofSection(c, x, y, s, { w: 420, h: 60 }),
  'doors_double': (c, x, y, s) => P.doors(c, x, y, s, { w: 88, h: 160 }),
  'window_unit': (c, x, y, s) => P.window(c, x, y, s, { w: 120, h: 170 }),
  'window_tall': (c, x, y, s) => P.window(c, x, y, s, { w: 84, h: 210 }),
};
for (const [name, fn] of Object.entries(arch)) {
  saveCanvas(sprite(fn, { w: 420, h: 360 }, { scale: 1 }), `${name}.png`, dirs.architecture);
}

// ---- characters: walk cycle frames + seated ----
const WALK_FRAMES = 8;
for (let i = 0; i < WALK_FRAMES; i++) {
  const cv = createCanvas(200, 240);
  const ctx = cv.getContext('2d');
  F.figure(ctx, 100, 228, 2.4, { pose: 'walk', phase: i / WALK_FRAMES, facing: 1, suit: '#2c3e55' });
  saveCanvas(cv, `figure_walk_${i}.png`, dirs.characters);
}
{
  const cv = createCanvas(200, 200);
  const ctx = cv.getContext('2d');
  F.seatedFigure(ctx, 100, 190, 2.4, { facing: 1, suit: '#3a3a3f' });
  saveCanvas(cv, 'figure_seated.png', dirs.characters);
}
{
  const cv = createCanvas(200, 240);
  const ctx = cv.getContext('2d');
  F.figure(ctx, 100, 228, 2.4, { pose: 'stand', phase: 0.4, facing: 1, suit: '#3a3a3f' });
  saveCanvas(cv, 'figure_stand.png', dirs.characters);
}

// ---- text layers (transparent) ----
function textSprite(text, font, color, pad = 40) {
  const probe = createCanvas(10, 10).getContext('2d');
  probe.font = font;
  const w = Math.ceil(probe.measureText(text).width) + pad * 2;
  const h = Math.ceil(parseInt(font.match(/(\d+)px/)[1])) * 2 + pad;
  const cv = createCanvas(w, h);
  const ctx = cv.getContext('2d');
  ctx.font = font;
  ctx.textAlign = 'right';
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = color;
  ctx.fillText(text, w - pad, h - pad * 0.6);
  return cv;
}
saveCanvas(textSprite('ماذا يوجد داخل البيت الأبيض؟', '700 64px "Amiri"', '#2f2a24'), 'title_ar_amiri700.png', dirs.text);
saveCanvas(textSprite('المكتب البيضاوي', '500 34px "Noto Sans Arabic"', '#2f2a24'), 'label_oval_office.png', dirs.text);
saveCanvas(textSprite('غرفة مجلس الوزراء', '500 34px "Noto Sans Arabic"', '#2f2a24'), 'label_cabinet_room.png', dirs.text);
saveCanvas(textSprite('قاعة الطعام الرسمية', '500 34px "Noto Sans Arabic"', '#2f2a24'), 'label_state_dining.png', dirs.text);
saveCanvas(textSprite('القاعة الشرقية', '500 34px "Noto Sans Arabic"', '#2f2a24'), 'label_east_room.png', dirs.text);
saveCanvas(textSprite('ماذا يوجد داخل البيت الأبيض؟', '500 17px "Noto Sans Arabic"', '#2f2a24'), 'label_mini_oval.png', dirs.text);
saveCanvas(textSprite('ماذا يوجد داخل البيت الأبيض؟', '500 17px "Noto Sans Arabic"', '#2f2a24'), 'label_mini_generic.png', dirs.text);

// ---- fx layers ----
{
  const cv = createCanvas(1920, 1080);
  const ctx = cv.getContext('2d');
  const g = ctx.createRadialGradient(960, 540, 380, 960, 540, 1030);
  g.addColorStop(0, 'rgba(30,22,12,0)');
  g.addColorStop(1, 'rgba(30,22,12,0.42)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 1920, 1080);
  saveCanvas(cv, 'vignette.png', dirs.fx);
}
{
  const cv = createCanvas(1920, 1080);
  const ctx = cv.getContext('2d');
  ctx.fillStyle = 'rgba(255,246,220,0.35)';
  ctx.fillRect(640, 0, 640, 1080);
  saveCanvas(cv, 'light_sweep_band.png', dirs.fx);
}
{
  const cv = createCanvas(1920, 1080);
  const ctx = cv.getContext('2d');
  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, 1920, 1080);
  ctx.globalAlpha = 0.05;
  ctx.fillStyle = '#fff';
  for (let i = 0; i < 4000; i++) {
    ctx.fillRect(Math.random() * 1920, Math.random() * 1080, 1, 1);
  }
  saveCanvas(cv, 'grain_sample.png', dirs.fx);
}

// ---- layer manifest ----
const manifest = {
  project: 'WHITE_HOUSE_20S_CINEMATIC_MOTION_TEST',
  pipeline: 'Node @napi-rs/canvas deterministic frame renderer + ffmpeg H.264 + Python synthesized audio',
  render: { resolution: '1920x1080', fps: 30, frames: 600, duration: '20s', aspect: '16:9' },
  layers: [
    { name: 'SKY_BASE', group: 'Environment', role: 'paper-sky gradient base', z: 0 },
    { name: 'PAPER_TEXTURE', group: 'Environment', role: 'multiply paper grain overlay', z: 1, animation: 'static' },
    { name: 'WHITE_HOUSE/GROUND', group: 'Architecture', role: 'grass, walkway, hedges, trees', z: 2 },
    { name: 'WHITE_HOUSE/BLOCK_WALLS', group: 'Architecture', role: 'main block + wings, ivory plaster', z: 3, animation: 'drawOn reveal 0.1-2.1s' },
    { name: 'WHITE_HOUSE/FACADE_OPENINGS', group: 'Architecture', role: 'window grid + side doors (slides away 3.4-4.45s)', z: 4 },
    { name: 'WHITE_HOUSE/PORTICO', group: 'Architecture', role: 'north portico columns, pediment, steps', z: 5 },
    { name: 'WHITE_HOUSE/ROOF_MAIN', group: 'Architecture', role: 'main slate roof slab (lifts 3.0-4.15s, descends 17.4-18.4s)', z: 6 },
    { name: 'WHITE_HOUSE/ROOF_WING_E', group: 'Architecture', role: 'east wing roof slab', z: 6 },
    { name: 'WHITE_HOUSE/ROOF_WING_W', group: 'Architecture', role: 'west wing roof slab', z: 6 },
    { name: 'WHITE_HOUSE/CHIMNEYS', group: 'Architecture', role: 'roof chimneys', z: 6 },
    { name: 'WHITE_HOUSE/OUTLINE', group: 'Architecture', role: 'silhouette stroke keeps cutaway coherent', z: 7 },
    { name: 'CUTAWAY/BACK_WALL', group: 'Architecture', role: 'interior paneled back wall', z: 8, animation: 'fade in 3.6-4.65s' },
    { name: 'CUTAWAY/FLOOR_SLAB', group: 'Architecture', role: 'interior floor slice', z: 8 },
    { name: 'CUTAWAY/PARTITIONS', group: 'Architecture', role: 'plan-view partition walls + door arcs', z: 8 },
    { name: 'CUTAWAY/STAIRCASE', group: 'Architecture', role: 'zigzag staircase plan', z: 8 },
    { name: 'DOLLHOUSE/MINI_OVAL', group: 'Architecture', role: 'miniature Oval Office diorama', z: 9 },
    { name: 'DOLLHOUSE/MINI_CABINET', group: 'Architecture', role: 'miniature Cabinet Room diorama', z: 9 },
    { name: 'DOLLHOUSE/MINI_DINING', group: 'Architecture', role: 'miniature State Dining Room diorama', z: 9 },
    { name: 'DOLLHOUSE/MINI_EAST', group: 'Architecture', role: 'miniature East Room diorama', z: 9 },
    { name: 'ROOM_SHELL/BACK_WALL', group: 'Rooms', role: 'plaster wall + wainscot + crown + baseboard', z: 10 },
    { name: 'ROOM_SHELL/SIDE_WALLS', group: 'Rooms', role: 'left/right wall trapezoids', z: 10 },
    { name: 'ROOM_SHELL/FLOOR', group: 'Rooms', role: 'wood floor + plank seams', z: 10 },
    { name: 'ROOM_SHELL/CEILING', group: 'Rooms', role: 'ceiling light quad', z: 10 },
    { name: 'OVAL_OFFICE/RUG', group: 'Furniture', role: 'oval blue rug w/ gold medallion', z: 11 },
    { name: 'OVAL_OFFICE/CHAIR_PRES', group: 'Furniture', role: 'chair behind Resolute desk', z: 11 },
    { name: 'OVAL_OFFICE/DESK', group: 'Furniture', role: 'presidential desk + items + flag', z: 12 },
    { name: 'OVAL_OFFICE/CHAIRS_SIDE', group: 'Furniture', role: 'two side chairs', z: 12 },
    { name: 'OVAL_OFFICE/BOOKSHELF', group: 'Furniture', role: 'bookshelf + globe', z: 12 },
    { name: 'OVAL_OFFICE/LAMP', group: 'Furniture', role: 'warm table lamp + glow', z: 12 },
    { name: 'OVAL_OFFICE/FIREPLACE', group: 'Furniture', role: 'fireplace with fire glow', z: 11 },
    { name: 'OVAL_OFFICE/WINDOWS', group: 'Furniture', role: 'two windows + light shafts', z: 10 },
    { name: 'OVAL_OFFICE/PORTRAIT', group: 'Furniture', role: 'framed portrait', z: 10 },
    { name: 'OVAL_OFFICE/FIGURE_STAFF', group: 'Characters', role: 'idle staff figure (separate head/torso/arms/legs)', z: 13, animation: 'breathing idle' },
    { name: 'CABINET_ROOM/RUG', group: 'Furniture', role: 'conference rug', z: 11 },
    { name: 'CABINET_ROOM/FIGURES_SEATED', group: 'Characters', role: 'two seated figures behind table', z: 11, animation: 'subtle head turns' },
    { name: 'CABINET_ROOM/CHAIRS_FAR', group: 'Furniture', role: 'far-side chairs + president chair', z: 11 },
    { name: 'CABINET_ROOM/TABLE', group: 'Furniture', role: 'long conference table', z: 12 },
    { name: 'CABINET_ROOM/CHAIRS_NEAR', group: 'Furniture', role: 'near-side chairs', z: 13 },
    { name: 'CABINET_ROOM/SIDEBOARD', group: 'Furniture', role: 'sideboard + candelabra', z: 13 },
    { name: 'CABINET_ROOM/BOOKSHELF', group: 'Furniture', role: 'bookshelf', z: 13 },
    { name: 'CABINET_ROOM/FIGURE_STAND', group: 'Characters', role: 'standing figure at table end', z: 14 },
    { name: 'CABINET_ROOM/WINDOWS', group: 'Furniture', role: 'windows + portrait', z: 10 },
    { name: 'DINING_ROOM/FIREPLACE', group: 'Furniture', role: 'center fireplace + portrait', z: 11 },
    { name: 'DINING_ROOM/DRAPES', group: 'Furniture', role: 'side drapery', z: 11 },
    { name: 'DINING_ROOM/RUG', group: 'Furniture', role: 'dining rug', z: 11 },
    { name: 'DINING_ROOM/CHAIRS_FAR', group: 'Furniture', role: 'far-side chairs', z: 11 },
    { name: 'DINING_ROOM/TABLE', group: 'Furniture', role: 'dining table + settings + centerpiece', z: 12 },
    { name: 'DINING_ROOM/CHAIRS_NEAR_ENDS', group: 'Furniture', role: 'near-side + end chairs', z: 13 },
    { name: 'DINING_ROOM/SIDEBOARD', group: 'Furniture', role: 'sideboard', z: 13 },
    { name: 'DINING_ROOM/EAGLE_TABLE', group: 'Furniture', role: 'eagle pedestal table', z: 13 },
    { name: 'DINING_ROOM/CHANDELIER', group: 'Furniture', role: 'chandelier + rod + light pool', z: 12, animation: 'candle flicker' },
    { name: 'EAST_ROOM/WINDOWS_TALL', group: 'Furniture', role: 'three tall windows + sun shafts', z: 10, animation: 'sun shimmer' },
    { name: 'EAST_ROOM/RUG', group: 'Furniture', role: 'grand rug', z: 11 },
    { name: 'EAST_ROOM/PIANO', group: 'Furniture', role: 'grand piano', z: 11 },
    { name: 'EAST_ROOM/SOFAS', group: 'Furniture', role: 'two sofas + side chairs', z: 12 },
    { name: 'EAST_ROOM/PLANTS', group: 'Furniture', role: 'plants + bust', z: 13 },
    { name: 'EAST_ROOM/CHANDELIER', group: 'Furniture', role: 'chandelier', z: 12 },
    { name: 'EAST_ROOM/FIGURE_PIANO', group: 'Characters', role: 'figure at piano', z: 14 },
    { name: 'EAST_ROOM/FIREPLACE', group: 'Furniture', role: 'side fireplace', z: 11 },
    { name: 'CORRIDOR/WALLS', group: 'Transition', role: 'corridor tunnel walls + sliding panels', z: 20, animation: 'parallax slide' },
    { name: 'CORRIDOR/CEILING_LIGHTS', group: 'Transition', role: 'passing ceiling glows', z: 20 },
    { name: 'CORRIDOR/FIGURE_WALKER', group: 'Characters', role: 'walking figure (8-frame walk cycle)', z: 21 },
    { name: 'UI/TITLE_MAIN', group: 'Typography', role: 'Arabic main title (Amiri 700, mask reveal)', z: 30, animation: 'mask wipe 1.0-1.7s' },
    { name: 'UI/SUBTITLE_EN', group: 'Typography', role: 'English subtitle (letterspaced caps)', z: 30 },
    { name: 'UI/LABEL_OVAL', group: 'Typography', role: 'المكتب البيضاوي (slide reveal)', z: 30 },
    { name: 'UI/LABEL_CABINET', group: 'Typography', role: 'غرفة مجلس الوزراء (mask reveal)', z: 30 },
    { name: 'UI/LABEL_DINING', group: 'Typography', role: 'قاعة الطعام الرسمية (slide reveal)', z: 30 },
    { name: 'UI/LABEL_EAST', group: 'Typography', role: 'القاعة الشرقية (mask reveal)', z: 30 },
    { name: 'UI/LABEL_MINI_*', group: 'Typography', role: 'dollhouse room labels (fade)', z: 30 },
    { name: 'UI/ANNOTATION_OVAL', group: 'Graphics', role: 'animated leader line → desk', z: 31, animation: 'draw 6.3-6.95s' },
    { name: 'UI/ANNOTATION_CABINET', group: 'Graphics', role: 'animated leader line → table', z: 31 },
    { name: 'UI/ANNOTATION_DINING', group: 'Graphics', role: 'animated leader line → chandelier', z: 31 },
    { name: 'UI/ANNOTATION_EAST', group: 'Graphics', role: 'animated leader line → windows', z: 31 },
    { name: 'UI/ANNOTATION_ROUTE', group: 'Graphics', role: 'route line portico→Oval (4.5-5.0s)', z: 31 },
    { name: 'UI/MARKERS_HERO', group: 'Graphics', role: 'sequential room markers + connector lines (18.2-19.6s)', z: 31 },
    { name: 'UI/ARCH_PASS', group: 'Transition', role: 'arch frame pass-through overlay (8.0-8.5s)', z: 29 },
    { name: 'FX/LIGHT_SWEEP', group: 'FX', role: 'diagonal light sweeps on transitions', z: 32 },
    { name: 'FX/GRADE', group: 'FX', role: 'warm cinematic grade', z: 33 },
    { name: 'FX/VIGNETTE', group: 'FX', role: 'edge vignette', z: 33 },
    { name: 'FX/GRAIN', group: 'FX', role: 'film grain (8-frame cycle)', z: 34 },
  ],
};
fs.writeFileSync(path.join(OUT, 'layers_manifest.json'), JSON.stringify(manifest, null, 2));
console.log('✓ layers_manifest.json');
console.log('assets exported to', OUT);
