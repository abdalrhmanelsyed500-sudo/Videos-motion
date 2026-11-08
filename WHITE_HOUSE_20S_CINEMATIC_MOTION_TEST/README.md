# WHITE HOUSE 20S — CINEMATIC MOTION TEST

**A 20-second, 16:9 (1920×1080, 30 fps) cinematic cutaway explainer of the White House,
fully procedural: every frame is drawn from code — no stock footage, no photos, no 3D renderer.**
Arabic typography (real Amiri / Noto Sans Arabic fonts, proper RTL), synthesized sound design,
H.264 delivery.

> ماذا يوجد داخل البيت الأبيض؟ — "What's inside the White House?"

## Contents

| Path | What's inside |
|---|---|
| `01_FINAL_VIDEO/` | The final MP4 (video + 16-bit audio) and the silent video track |
| `02_EDITABLE_PROJECT/` | The full Node.js editable source: every layer, texture, prop, character, camera move and timeline in plain JS |
| `03_SEPARATED_ASSETS/` | Every layer exported as its own PNG/JSON (furniture, architecture, characters, text, textures, FX) + `layers_manifest.json` |
| `04_audio_out/` | Synthesized 20 s stereo mix (float32 + 16-bit WAV) |
| `05_PREVIEWS_AND_QC/` | QC report, preview GIFs, ASCII composition checks |

## The timeline

| # | Time (s) | Shot | Layer system |
|---|---|---|---|
| 1 | 0.0–2.0 | Paper sky + title reveal, the House materializes from flat folds | intro |
| 2 | 2.0–3.6 | Facade dolly-in, windows clear, walkway lead | intro |
| 3 | 3.0–5.2 | Roof lifts away → cutaway to dollhouse plan → Oval Office reveal + route line + **المكتب البيضاوي** | lift + ovalScene |
| 4 | 5.2–7.3 | Annotation leader line to the Resolute desk; staff figure idle; camera drifts | oval |
| 5 | 7.3–8.5 | Corridor pass-through with walking figure, then **غرفة مجلس الوزراء** (Cabinet Room) plan | corridor + cabinetScene |
| 6 | 8.5–11.2 | Dining Room match-cut via circle wipe → **قاعة الطعام الرسمية** with flickering chandelier | dining + diningScene |
| 7 | 11.2–13.4 | **القاعة الشرقية** (East Room) with sun-shafted windows, piano, sofas | east + eastScene |
| 8 | 13.4–15.2 | Roof returns, camera descends to monumental hero | hero |
| 9 | 15.2–17.4 | Hero shot with sequential room markers + connector lines | hero |
| 10 | 17.4–20.0 | Close on the portico + main title return + resolve chord | resolve |

## Editing the project

Everything lives in `02_EDITABLE_PROJECT/render/src/`:

| File | Role |
|---|---|
| `util.js` | Math (easing, projection, shadows), deterministic RNG |
| `textures.js` | Procedural paper, plaster, wood, marble, velvet, grass, stone, sky tiles + film-grain frames |
| `art.js` | Pen-drawn line-art component painters (block walls, windows, facade, columns, portico, roofs, chimneys, doors, outline, miniature dollhouse dioramas) |
| `props.js` | Furniture: chairs, desks, sofas, tables, sideboards, bookshelves, piano, fireplace, chandelier, drapes, rugs, paintings, busts, plants |
| `figures.js` | Stylized human figures: idle (separate head/torso/arms/legs) and 8-frame walk cycle |
| `rooms.js` | The four full-scale interiors: ovalScene, cabinetScene, diningScene, eastScene |
| `building.js` | whiteHouse() — the exterior cutaway assembly |
| `labels.js` | Arabic text engine: RTL draw, 5 reveal types, annotation lines, Latin labels |
| `fx.js` | Paper/vignette/grain/light-sweep/grade/circle-wipe compositing |
| `timeline.js` | Camera keyframes per phase, buildingParams, expansionG, LABELS windows |
| `scene.js` | Frame assembler: all phase dispatch, match-cut, overlays |

### Render

```bash
cd 02_EDITABLE_PROJECT/render
npm install          # @napi-rs/canvas, @fontsource/amiri, @fontsource/noto-sans-arabic
node tools/render.js --frames 0,300,599          # QC frames + stats
node tools/render.js --pngs frames/ --start 0 --end 600   # all 600 frames as PNG
node tools/ascii_qc.js <t> out.txt                # 150×42 ASCII density composition check
node tools/export_assets.js                       # re-export 03_SEPARATED_ASSETS
python tools/make_audio.py                        # synthesize 04_audio_out/mix.wav (needs numpy+scipy)
python tools/mux.py <silent.mp4> 04_audio_out/mix.wav <final.mp4>
python tools/qc.py <final.mp4>                    # writes QC_REPORT.md
```

**Operational note (this machine, 4 GB RAM):** render in `--pngs` chunks
(`--start/--end`), then encode with ffmpeg separately. The single-process rawvideo pipe
is OOM-prone here; the two-step flow is stable. `fx.js` caches the 8 film-grain frames
module-level (regenerating them per frame leaks ~140 MB/frame natively).

### Audio

`tools/make_audio.py` synthesizes the entire 20 s soundtrack in numpy/scipy —
paper crackles, roof creak, whooshes, footsteps, room chimes, marker pings,
a resolve chord, and a low room-tone bed. No samples are used; every event is
generated from filters and noise. The event list is in the file header.

### QC

`tools/qc.py` checks: container/streams, sampled-frame luminance & black-frame
ratio, frame-diff motion continuity, audio RMS windows + peak, and Arabic-text
ink presence on title/label frames. The honest report lives in
`05_PREVIEWS_AND_QC/QC_REPORT.md` — this agent has no vision, so all visual
checks are numeric/ASCII density, not eyeballing.

## Honest limitations

- **No vision QC**: composition was verified through ASCII density maps and
  luminance stats, not visual inspection.
- Audio is procedural ambience/design — no music.
- The walk cycle and idle figures are simplified pen-figure rigs, not clip-library motion.
