// Runs the game in a REAL renderer: the Godot 4.7.2 web template inside headless Chromium (software WebGL2 via SwiftShader), with
// real keyboard events and real screenshots.
//   node render.mjs <project dir> <scenario.mjs>         scenario: export default async (s) => { await s.wait(5); await s.key('KeyM'); await s.shot('a.png') }
// What this is: the real engine, the real scenes and scripts, real Compatibility (OpenGL ES 3) drawing, real DOM key events turned into
// InputEventKey by the engine's web layer. What it is NOT: the Windows build on the Intel HD 3000 (no ANGLE/D3D11 path, no real GPU,
// software speed, so framerates mean nothing). Files are served raw, with no editor import: PNGs are loaded through the raw-image fallback.
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import chromium from '@sparticuz/chromium';
import puppeteer from 'puppeteer-core';

const here = path.dirname(fileURLToPath(import.meta.url));
const gen = path.join(here, 'node_modules/@ringozz/godot-web-wasm32/gen');
const base = 'godot.web.template_release.wasm32.nothreads';
const projectDir = path.resolve(process.argv[2] ?? '../../game');
const scenarioFile = path.resolve(process.argv[3]);
const VW = Number(process.env.VIEW_W ?? 1280), VH = Number(process.env.VIEW_H ?? 720);
const outDir = path.resolve(process.env.SHOT_DIR ?? 'shots');
fs.mkdirSync(outDir, { recursive: true });

// ---- file list of the project (no .godot, .git, *.import: the raw-file fallbacks load the PNGs) --------------------------------------
const files = [];
(function walk(d, rel) {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    if (e.name === '.godot' || e.name === '.git' || e.name.endsWith('.import') || e.name === 'node_modules') continue;
    const r = rel ? rel + '/' + e.name : e.name;
    if (e.isDirectory()) walk(path.join(d, e.name), r); else files.push(r);
  }
})(projectDir, '');

// RENDER_REGEX_SHIM=1: the web template has no RegEx module, so the Data/DebugConsole autoloads cannot compile; inject the harness-only
// polyfill (tools/godot_node/regex_shim.gd) exactly as tools/godot_node/run.mjs does
const SHIM = process.env.RENDER_REGEX_SHIM === '1';
if (SHIM) files.push('core/regex_shim.gd');
const shimSrc = () => fs.readFileSync(path.join(here, '../godot_node/regex_shim.gd'), 'utf8');

// the one change the raw (never imported) project needs: the view's texture loader returns the raw PNG as a texture
// harness-only CP-2 hooks (in memory): Q sleeping deck, U hold, I crow's nest, O captain's cabin, J winch, K fish barrels,
// L half way up the rope ladder, H hold racks, V test fish + provisions (letters that the game never binds in these scenarios). They only PLACE the pirate; the transitions are real keys.
const deckHooks = (s) => s.replace('\tvar kc: int = KeyUtil.code(k)', '\tvar dh: int = [KEY_Q, KEY_U, KEY_I, KEY_O, KEY_J, KEY_K, KEY_L, KEY_H, KEY_V, KEY_BACKSLASH].find(int(k.keycode)) + 1\n\tif dh > 0:\n\t\t_deck_hook(dh)\n\t\treturn\n\tvar kc: int = KeyUtil.code(k)') + `
func _deck_hook(n: int) -> void:
	if not _ship_mode.is_deck():
		_ship_mode.leave_helm(_ship_ctx())
	var w: RefCounted = _ship_mode.walker
	var lay: RefCounted = _ship_mode.layout
	match n:
		1:
			w.call("place", 1, Vector2(-4.0, 0.0))
		2:
			w.call("place", 2, Vector2(-1.0, 0.0))
		3:
			w.call("place", 3, ShipLayout.NEST_ARRIVE)
		4:
			w.call("place", 0, Vector2(-7.7, 0.9))
		5:
			w.call("place", 0, (lay.call("interaction", 0, "winch") as Dictionary)["c"])
		6:
			w.call("place", 0, (lay.call("interaction", 0, "fish_barrels") as Dictionary)["c"])
		7:
			w.call("place", 0, ShipLayout.LADDER_BASE)
			w.call("start_climb", 1)
			w.set("climb_t", 0.5)
		8:
			w.call("place", 2, Vector2(-0.4, 0.0))
		10:
			w.call(\"place\", 0, Vector2(-0.3, 0.9))
		9:
			(_port as PortGame).state.add_catch("spc_mackerel", 28.0, 0.0)
			_give_test_provisions()
`;


// harness-only CP-2B hooks (in memory): Z steps through the winch story WITHOUT waiting for the real timers (the software renderer runs
// far slower than real time): 1 = ship on a fishing ground + pirate at the winch (then the real F key enters), 2 = needle centred,
// 3 = mid-haul, 4 = a surge warning, 5 = net coming up with the real catch, 6 = catch card, 7 = unloading, 8 = a lost haul, 9 = barrels panel.
// The drawing, the layout, the keys and the hold are the real ones; only the clock of the stage machine is nudged.
const fishHooks = (s) => s.replace('\t_key_raw += 1\n', '\tif k.keycode == KEY_Z:\n\t\t_fish_hook()\n\t\treturn\n\t_key_raw += 1\n') + `
var _fh := 0
func _fish_hook() -> void:
	_fh += 1
	var m = _fish.manual if _fish != null else null
	match _fh:
		1:
			if not _ship_mode.is_deck():
				_ship_mode.leave_helm(_ship_ctx())
			var g: Dictionary = (_port as PortGame).fishing.grounds["gnd_gannet_bank"]
			_pos = Vector2(float(g["x"]), float(g["z"]))
			_helm.speed_kn = 0.3
			_ship_mode.walker.call("place", 0, (_ship_mode.layout.call("interaction", 0, "winch") as Dictionary)["c"])
		2:
			m.stage_t = 0.40
		3:
			m.press("cast")
			m.stage = 5
			m.depth = 0.75
			m.progress = 0.55
			m.integrity = 0.82
			m.tension = 0.58
			m.strain = 0.25
			m.streak = 9
			m.best_streak = 9
			m.pulls = 14
			m.haul_t = 6.1
			m.lever = 1.0
			m.last_side = "right"
			m.message = "Good rhythm: keep it up!"
			m.message_kind = "ok"
			m.winch_angle = 3.0
		4:
			m.message = "THE FISH IS ABOUT TO RUN! Ease off!"
			m.message_kind = "warn"
			m.tension = 0.78
			m.strain = 0.55
			m.lever = -1.0
			_fish.view.call("on_events", [{"type": "surge_warn", "kind": 1}])
		5:
			m.progress = 1.0
			m.haul_t = 9.4
			m._finish_haul()
			m.stage_t = 1.6
		6:
			m._set_stage(7)
			m.depth = 0.0
		7:
			m.unload()
			m.stage_t = 0.7
		8:
			m._fail("snap", "The rope snapped under the strain and the catch fell back into the sea. Ease off when the rope groans or the fish runs, and pull at a steady beat.")
		9:
			_fish.abort("harness")
			(_port as PortGame).state.add_catch("spc_sardine", 3.0, 0.0)
			(_port as PortGame).state.add_catch("spc_parrotfish", 4.2, 0.0)
			(_port as PortGame).state.add_catch("spc_yellowfin_tuna", 12.0, 0.0)
			_ship_mode.walker.call("place", 0, (_ship_mode.layout.call("interaction", 0, "fish_barrels") as Dictionary)["c"])
`;

const PATCHES = {
  // harness-only hook: F9 steps ashore at the pier without the docking manoeuvre (steering into the berth by script is not the point)
  'h2d/h2d0.gd': (s) => fishHooks(deckHooks(s.replace('\tvar kc: int = KeyUtil.code(k)', '\tif k.keycode == KEY_F9:\n\t\t_walker.disembark((_v3 as View3D).land_world().meta["land"])\n\t\t(_v3 as View3D).land_world().prime(Vector2(_walker.x, _walker.z))\n\t\treturn\n\tif k.keycode == KEY_F10 or k.keycode == KEY_F11:\n\t\t_walker.x = 27.5 if k.keycode == KEY_F10 else -75.0\n\t\t_walker.z = -0.5 if k.keycode == KEY_F10 else -10.6\n\t\t(_v3 as View3D).land_world().prime(Vector2(_walker.x, _walker.z))\n\t\treturn\n\tvar kc: int = KeyUtil.code(k)'))),
  'h2d/sea_view_3d.gd': (s) => s.replace('\tif not ResourceLoader.exists(path):\n', '\tif false:\n').replace('\treturn load(path) as Texture2D\n',
    '\tvar raw := Image.load_from_file(path)\n\tif raw == null or raw.is_empty():\n\t\treturn null\n\treturn ImageTexture.create_from_image(raw)\n'),
};

const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]);
  if (u === '/' || u === '/index.html') {
    res.setHeader('content-type', 'text/html');
    return res.end(`<!doctype html><meta charset=utf-8><body style="margin:0;background:#000"><canvas id="canvas" width="${VW}" height="${VH}" style="width:${VW}px;height:${VH}px;display:block" tabindex="0"></canvas></body>`);
  }
  if (u === '/manifest.json') { res.setHeader('content-type', 'application/json'); return res.end(JSON.stringify(files)); }
  if (u.startsWith('/gen/')) {
    let name = u.slice(5).replace(/^godot\./, '');
    let f = path.join(gen, u.slice(5));
    if (!fs.existsSync(f)) f = path.join(gen, name);
    if (!fs.existsSync(f)) { res.statusCode = 404; return res.end(); }
    res.setHeader('content-type', f.endsWith('.js') ? 'text/javascript' : f.endsWith('.wasm') ? 'application/wasm' : 'application/octet-stream');
    return res.end(fs.readFileSync(f));
  }
  if (u.startsWith('/proj/')) {
    const rel = u.slice(6);
    if (!files.includes(rel)) { res.statusCode = 404; return res.end(); }
    let buf = rel === 'core/regex_shim.gd' ? Buffer.from(shimSrc()) : fs.readFileSync(path.join(projectDir, rel));
    if (SHIM && rel.endsWith('.gd') && rel !== 'core/regex_shim.gd' && buf.includes('RegEx')) {
      let txt = buf.toString('utf8').replace(/\bRegEx\b/g, 'RegExShim');
      txt = txt.replace(/^(extends [^\n]*\n)/m, '$1const RegExShim := preload("res://core/regex_shim.gd")\n');
      buf = Buffer.from(txt);
    }
    if (PATCHES[rel]) buf = Buffer.from(PATCHES[rel](buf.toString('utf8')));
    return res.end(buf);
  }
  res.statusCode = 404; res.end();
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const port = server.address().port;

const browser = await puppeteer.launch({
  executablePath: await chromium.executablePath(), headless: 'shell',
  args: [...chromium.args, '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--no-sandbox', `--window-size=${VW},${VH}`],
});
const page = await browser.newPage();
await page.setViewport({ width: VW, height: VH });
const log = [];
page.on('console', (m) => { const t = m.text(); log.push(t); if (process.env.RENDER_QUIET !== '1') console.log('[page]', t.slice(0, 300)); });
page.on('pageerror', (e) => { log.push('PAGEERROR ' + e.message); console.log('[pageerror]', String(e.message).slice(0, 300)); });
await page.goto(`http://127.0.0.1:${port}/`);

const t0 = Date.now();
await page.evaluate(async (port, base, extraArgs, W, H) => {
  const mod = await import(`/gen/${base}.js`);
  const wasm = await (await fetch(`/gen/${base}.wasm`)).arrayBuffer();
  const canvas = document.getElementById('canvas');
  const M = await mod.default({
    wasmBinary: wasm, noInitialRun: true, canvas,
    print: (s) => console.log(s), printErr: (s) => console.log('ERR ' + s),
    locateFile: (p) => `/gen/${p}`,
  });
  const list = await (await fetch('/manifest.json')).json();
  for (const f of list) {
    const b = new Uint8Array(await (await fetch('/proj/' + encodeURI(f))).arrayBuffer());
    M.copyToFS('/proj/' + f, b);
  }
  M.initConfig({ canvas, canvasResizePolicy: 2, focusCanvas: true });
  window.__M = M;
  M.callMain(['--path', '/proj', '--rendering-driver', 'opengl3', '--resolution', `${W}x${H}`, ...extraArgs]);
}, port, base, process.argv.slice(4), VW, VH);
console.log(`[render] engine started after ${((Date.now() - t0) / 1000).toFixed(1)} s, ${files.length} project files`);

const s = {
  page, log, outDir,
  wait: (sec) => new Promise((r) => setTimeout(r, sec * 1000)),
  // a real key press on the canvas: code is a DOM code like 'KeyM', 'Space', 'Tab', 'F8'; key is the character the layout would give
  key: async (code, opts = {}) => { await page.keyboard.down(code); await new Promise((r) => setTimeout(r, opts.hold ?? 90)); await page.keyboard.up(code); },
  // a key event as an Arabic keyboard layout produces it: physical key KeyM, but the character is the Arabic letter
  rawKey: async (code, key, vk, opts = {}) => {
    const c = await page.createCDPSession();
    const base = { code, key, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk, text: opts.text ?? '' };
    await c.send('Input.dispatchKeyEvent', { type: opts.text ? 'keyDown' : 'rawKeyDown', ...base });
    await new Promise((r) => setTimeout(r, opts.hold ?? 90));
    await c.send('Input.dispatchKeyEvent', { type: 'keyUp', ...base });
  },
  hold: async (code, sec) => { await page.keyboard.down(code); await new Promise((r) => setTimeout(r, sec * 1000)); await page.keyboard.up(code); },
  shot: async (name) => { await page.screenshot({ path: path.join(outDir, name) }); console.log('[render] shot', name); },
  logSince: (n) => log.slice(n),
  mark: () => log.length,
};
try {
  const sc = await import(pathToFileURL(scenarioFile).href);
  await sc.default(s);
} catch (e) {
  console.log('[render] scenario error:', String(e && e.stack).slice(0, 500));
}
fs.writeFileSync(path.join(outDir, 'page.log'), log.join('\n'));
await browser.close();
server.close();
process.exit(0);
