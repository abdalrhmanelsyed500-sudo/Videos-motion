const { createCanvas, GlobalFonts } = require('@napi-rs/canvas');
const fs = require('fs');
const path = require('path');

const base = path.join(__dirname, '..');
const amiri = path.join(base, 'node_modules/@fontsource/amiri/files/amiri-arabic-400-normal.woff2');
const amiri700 = path.join(base, 'node_modules/@fontsource/amiri/files/amiri-arabic-700-normal.woff2');
const noto = path.join(base, 'node_modules/@fontsource/noto-sans-arabic/files/noto-sans-arabic-arabic-400-normal.woff2');

console.log('amiri exists:', fs.existsSync(amiri), fs.existsSync(amiri700), fs.existsSync(noto));

let ok1 = GlobalFonts.registerFromPath(amiri, 'Amiri');
let ok2 = GlobalFonts.registerFromPath(amiri700, 'Amiri');
let ok3 = GlobalFonts.registerFromPath(noto, 'Noto Sans Arabic');
console.log('registered:', ok1, ok2, ok3);
console.log('families:', GlobalFonts.families.map(f => f.family).slice(-6));

const cv = createCanvas(900, 300);
const ctx = cv.getContext('2d');
ctx.fillStyle = '#f6efe2';
ctx.fillRect(0, 0, 900, 300);
ctx.fillStyle = '#2f2a24';
ctx.textAlign = 'right';
ctx.textBaseline = 'alphabetic';

// Test 1: Amiri 700, title, RTL visual order
const title = 'ماذا يوجد داخل البيت الأبيض؟';
// split words, reverse word order, reverse chars in each word
const visual = title.split(' ').reverse().map(w => Array.from(w).reverse().join('')).join(' ');
ctx.font = '700 54px "Amiri"';
ctx.fillText(visual, 880, 90);
const m = ctx.measureText(visual);
console.log('title width:', m.width);

// Test 2: Noto Sans Arabic label
const label = 'المكتب البيضاوي';
const vis2 = label.split(' ').reverse().map(w => Array.from(w).reverse().join('')).join(' ');
ctx.font = '400 40px "Noto Sans Arabic"';
ctx.fillText(vis2, 880, 170);
console.log('label width:', ctx.measureText(vis2).width);

// Test 3: Arabic+Latin mixed: "البيت الأبيض — White House"
const mixed = 'البيت الأبيض — White House';
// crude: split into RTL runs and LTR runs: RTL parts reversed, LTR kept
// simple approach: handle per-word: arabic words reversed, latin words kept, word order: RTL runs first (right side)
const parts = mixed.split(' ');
const arabic = [], latin = [];
for (const p of parts) {
  if (/[\u0600-\u06FF]/.test(p)) arabic.push(p); else latin.push(p);
}
const visMixed = Array.from(latin).reverse().concat([Array.from(arabic).reverse().map(w => Array.from(w).reverse().join('')).join(' ')]).join(' ');
ctx.font = '400 34px "Noto Sans Arabic"';
ctx.fillText(visMixed, 880, 240);
console.log('mixed width:', ctx.measureText(visMixed).width);

// Glyph coverage check for title
const t2 = cv.getContext('2d'); // reuse
const cv2 = createCanvas(900, 120);
const c2 = cv2.getContext('2d');
c2.font = '700 54px "Amiri"';
c2.fillText(visual, 880, 90);
const data = c2.getImageData(0, 0, 900, 120).data;
let dark = 0;
for (let i = 3; i < data.length; i += 4) if (data[i] > 100) dark++;
console.log('title glyph coverage pixels:', dark, '(expect > 2000)');

// Shape check: visual reversal produces connected RTL word; check Amiri glyphs render (non-tofu).
// Tofu boxes would render as rectangles; count distinct column runs > 10 indicates real glyphs
const cols = new Set();
for (let x = 0; x < 900; x++) {
  let hit = false;
  for (let y = 20; y < 100; y++) if (data[(y * 900 + x) * 4 + 3] > 100) { hit = true; break; }
  if (hit) cols.add(x);
}
console.log('title ink columns:', cols.size, '(expect > 60 for real glyphs)');

fs.writeFileSync(path.join(base, 'tools', 'font_test.png'), cv.toBuffer('image/png'));
fs.writeFileSync(path.join(base, 'tools', 'font_test2.png'), cv2.toBuffer('image/png'));
console.log('OK');
