const { createCanvas, GlobalFonts } = require('@napi-rs/canvas');
const path = require('path');
const base = path.join(__dirname, '..');
GlobalFonts.registerFromPath(path.join(base, 'node_modules/@fontsource/amiri/files/amiri-arabic-400-normal.woff2'), 'Amiri');

// 'بك' = beh+kaf. If shaping is correct, they connect (no whitespace gap in the middle).
function gapStats(text, font, size = 80, pad = 300) {
  const cv = createCanvas(pad * 2 + 600, 260);
  const ctx = cv.getContext('2d');
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, cv.width, cv.height);
  ctx.fillStyle = '#000';
  ctx.font = font;
  ctx.textBaseline = 'alphabetic';
  ctx.fillText(text, 300, 180);
  const d = ctx.getImageData(0, 0, cv.width, 260).data;
  // find ink columns
  const colHas = new Uint8Array(cv.width);
  for (let x = 0; x < cv.width; x++) {
    for (let y = 0; y < 260; y++) {
      if (d[(y * cv.width + x) * 4] < 128) { colHas[x] = 1; break; }
    }
  }
  let first = -1, last = -1;
  for (let x = 0; x < cv.width; x++) if (colHas[x]) { if (first < 0) first = x; last = x; }
  // count gap runs in the ink span
  let gaps = 0, maxGap = 0, run = 0;
  for (let x = first; x <= last; x++) {
    if (!colHas[x]) { run++; } else { if (run > 0) { gaps++; maxGap = Math.max(maxGap, run); } run = 0; }
  }
  return { span: last - first, gaps, maxGap, width: ctx.measureText(text).width };
}

// Connected pair 'بك'
const a = gapStats('بك', '400 80px "Amiri"');
console.log('بك connected-test:', a, '-> connected if gaps===0 (or gaps===1 with tiny maxGap)');
// With space 'ب ك' - expect a gap
const b = gapStats('ب ك', '400 80px "Amiri"');
console.log('ب ك spaced-test:', b);
// Single letters 'ب ا' reversed order test: 'اب' vs 'با'
const c = gapStats('اب', '400 80px "Amiri"');
console.log('اب (alif+beh):', c);

// RTL word placement test with textAlign right: does logical string place ink at right edge?
const cv = createCanvas(1000, 200);
const ctx = cv.getContext('2d');
ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, 1000, 200);
ctx.fillStyle = '#000';
ctx.font = '400 60px "Amiri"';
ctx.textAlign = 'right';
ctx.fillText('المكتب', 950, 130);
const d = ctx.getImageData(0, 0, 1000, 200).data;
let first = -1, last = -1;
for (let x = 0; x < 1000; x++) for (let y = 0; y < 200; y++) {
  if (d[(y * 1000 + x) * 4] < 128) { if (first < 0) first = x; last = x; break; }
}
console.log('RTL right-anchor test: ink span x =', first, '..', last, '(right edge 950; correct bidi => last near 950)');
console.log('measureText width:', ctx.measureText('المكتب').width);
