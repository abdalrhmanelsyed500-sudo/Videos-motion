// Runs Godot 4.7.2 (the WebAssembly release template of the npm package @ringozz/godot-web-wasm32) headless under Node.
//   node run.mjs <project dir> [godot args...]      e.g.  node run.mjs ../../game --script res://tests/run_all.gd
// The project directory is copied into the engine's in-memory file system as /proj (skipping .godot and *.import caches).
// There is NO rendering (headless = dummy renderer) and no audio: this runs GDScript, scene trees, input events and logic.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const stubEl = () => ({ style: {}, getContext: () => null, addEventListener() {}, removeEventListener() {}, remove() {}, focus() {} });
globalThis.window = globalThis;
globalThis.document = { createElement: () => ({ getContext: () => null, style: {} }), addEventListener() {}, body: {},
  getElementById: () => stubEl(), querySelector: () => stubEl() };

const here = path.dirname(fileURLToPath(import.meta.url));
const gen = path.join(here, 'node_modules/@ringozz/godot-web-wasm32/gen');
const base = 'godot.web.template_release.wasm32.nothreads';
const projectDir = path.resolve(process.argv[2] ?? '../../game');
const args = process.argv.slice(3);
const quiet = process.env.GODOT_QUIET === '1';

const mod = await import(path.join(gen, base + '.js'));
const lines = [];
// Known harmless noise of THIS engine build: it has no RegEx module (core/ids.gd, schema.gd, console_commands.gd cannot
// compile) and the project was never imported by the editor (no .godot/imported/*.ctex), so textures fail to load.
const NOISE = [/RegEx/, /Cannot infer the type of "re" variable/, /Failed to compile depended scripts/, /\/registry\.gd/,
  /debug_console\.gd/, /console_commands\.gd/, /schema\.gd/, /\.godot\/imported/, /Failed loading resource: res:\/\/.*\.(png|ctex)/,
  /gdscript_resource_format\.cpp/, /resource_loader\.cpp/, /compressed_texture\.cpp/, /GDScript::reload/, /Failed to load script "res:\/\/(core|ui)\//];
let skipAt = false;
const emit = (tag, s) => {
  if (/^\s+at: /.test(s) && skipAt) return;
  skipAt = !process.env.GODOT_RAW && process.env.GODOT_REGEX_SHIM !== '1' && NOISE.some((r) => r.test(s));
  if (skipAt) return;
  lines.push(s); if (!quiet) console.log(s);
};
const M = await mod.default({
  wasmBinary: fs.readFileSync(path.join(gen, base + '.wasm')), noInitialRun: true, canvas: stubEl(),
  print: (s) => emit('out', s), printErr: (s) => emit('err', s), locateFile: (p) => path.join(gen, p),
});

let nfiles = 0;
function copyDir(src, dst) {
  for (const e of fs.readdirSync(src, { withFileTypes: true })) {
    if (e.name === '.godot' || e.name === '.git') continue;
    const s = path.join(src, e.name), d = dst + '/' + e.name;
    if (e.isDirectory()) copyDir(s, d);
    else {
      let buf = fs.readFileSync(s);
      if (process.env.GODOT_REGEX_SHIM === '1' && e.name.endsWith('.gd') && buf.includes('RegEx')) {
        let txt = buf.toString('utf8').replace(/\bRegEx\b/g, 'RegExShim');
        txt = txt.replace(/^(extends [^\n]*\n)/m, '$1const RegExShim := preload("res://core/regex_shim.gd")\n');
        buf = Buffer.from(txt);
      }
      M.copyToFS(d, new Uint8Array(buf)); nfiles++;
    }
  }
}
copyDir(projectDir, '/proj');
// GODOT_REGEX_SHIM=1: this engine build has no RegEx module; inject a harness-only polyfill (never part of the game) and its self-test
if (process.env.GODOT_REGEX_SHIM === '1') {
  M.copyToFS('/proj/core/regex_shim.gd', new Uint8Array(fs.readFileSync(path.join(here, 'regex_shim.gd'))));
  M.copyToFS('/proj/tests/_regex_shim_selftest.gd', new Uint8Array(fs.readFileSync(path.join(here, 'regex_shim_selftest.gd'))));
}
let status = 0;
let finished = false;
function finish() {
  if (finished) return; finished = true;
  if (process.env.GODOT_LOG) fs.writeFileSync(process.env.GODOT_LOG, lines.join('\n'));
  const failed = lines.some((l) => /^TESTS: .* FAIL$|^SELFPLAY: .*FAIL$|^LOADALL: .* [1-9]\d* failed/.test(l)) || status !== 0;
  console.log(`[godot-node] ${failed ? 'FAILED' : 'finished'} (status ${status}), ${nfiles} files, ${lines.length} output lines`);
  process.exit(failed ? 1 : 0);
}
process.on('uncaughtException', (e) => {
  // the engine's own shutdown touches a canvas that does not exist under Node: harmless, the script has already finished
  if (e && /reading 'style'/.test(String(e.message))) return finish();
  if (e && typeof e.status === 'number') { status = e.status; return finish(); }
  console.log('JS EXCEPTION:', String(e && e.message).slice(0, 200), String(e && e.stack).split('\n').slice(1,4).map((x)=>x.slice(0,140)).join(' | ')); status = 99; finish();
});
try {
  M.callMain(['--headless', '--path', '/proj', ...args]);
} catch (e) {
  if (e && typeof e.status === 'number') status = e.status;
  else { status = 99; console.log('JS EXCEPTION:', String(e && e.message).slice(0, 200), String(e && e.stack).split('\n').slice(1,4).map((x)=>x.slice(0,140)).join(' | ')); }
}
// the engine keeps running its main loop through Node's event loop until the script calls quit() (-> ExitStatus) or the timeout
const secs = Number(process.env.GODOT_SECONDS ?? 0);
if (secs > 0) setTimeout(() => { console.log('[godot-node] time limit reached'); finish(); }, secs * 1000);
else finish();
