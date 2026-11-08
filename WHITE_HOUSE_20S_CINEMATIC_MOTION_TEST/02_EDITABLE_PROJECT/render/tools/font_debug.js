const { createCanvas, GlobalFonts } = require('@napi-rs/canvas');
const path = require('path');
const base = path.join(__dirname, '..');
GlobalFonts.registerFromPath(path.join(base, 'node_modules/@fontsource/amiri/files/amiri-arabic-400-normal.woff2'), 'Amiri');

function coverage(text, font) {
  const cv = createCanvas(1200, 200);
  const ctx = cv.getContext('2d');
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, 1200, 200);
  ctx.fillStyle = '#000';
  ctx.font = font;
  ctx.textBaseline = 'alphabetic';
  ctx.fillText(text, 600, 140);
  const data = ctx.getImageData(0, 0, 1200, 200).data;
  let dark = 0;
  const xs = new Set();
  for (let y = 0; y < 200; y++) for (let x = 0; x < 1200; x++) {
    if (data[(y * 1200 + x) * 4] < 100) { dark++; xs.add(x); }
  }
  const m = ctx.measureText(text);
  return { dark, cols: xs.size, width: m.width };
}

console.log('Latin Amiri:', coverage('Hello World Test', '400 60px "Amiri"'));
console.log('Arabic logical:', coverage('ماذا يوجد', '400 60px "Amiri"'));
console.log('Arabic visual-reversed:', coverage('صو د م ا', '400 60px "Amiri"'));
const v = 'ماذا'.split('').reverse().join('');
console.log('Arabic visual ماذا->', JSON.stringify(v), coverage(v, '400 60px "Amiri"'));
// Check what DejaVu does (fallback check)
console.log('Arabic in DejaVu:', coverage('ماذا يوجد', '400 60px "DejaVu Sans"'));
