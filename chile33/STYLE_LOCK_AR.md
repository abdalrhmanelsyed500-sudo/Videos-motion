# STYLE LOCK — Arabic oil-painted layered-puppet series
Approved by the user on the 12.5 s test (`Test_Oil_Layered_Style.mp4`, commit 597c306).
**Rule: this look and motion must NOT change for the whole video / series. Only content (story, characters, props, plates) changes.**

## 1. Painting
- Thick impasto OIL painting, warm palette, visible brush strokes. Every new asset is generated with the same prompt language as `ar_parts.jpg` / `ar_bg.jpg`
  (oil painting, thick brush strokes, warm light, no text, no borders). Never photo / flat vector / cartoon.
- Characters = DISASSEMBLED PARTS SHEET on flat grey -> cut into RGBA layers (head, lids, mouth, torso, arms, forearms, legs). Plates = depth layers.
- Post (identical every shot): canvas-weave multiply, warm tone, vignette, film grain, fade in 0.6 s / out 1 s. 1280x720, 30 fps, 16:9.

## 2. Motion (layer rig, `scenes_ar.py::character`)
- Bones: root -> hips/legs, torso (breathing), head (nods), arm -> forearm (elbow). Walk cycle, talking gestures, mouth driven by the voice.
- Nothing is a still image: every character part and every prop moves on its own layer; backgrounds are split (base / walls / swinging lantern).
- Camera: slow dolly, parallax (walls 1.22x vs base 1.08x around VP (700,420)); same easing (`sstep`, `ease_out`). No whole-frame shake/zoom tricks on a flat picture.

## 3. Signature face mark — EVERY character, EVERY shot
- Circle around the whole face: B&W high-contrast filter inside, black outer ring + white inner ring, radius = 128 x character scale.
- Solid black bar over the eyes (head-local x 12-132, y 72-108). Both follow the head matrix. (`scenes_ar.py::face_mark`)

## 4. NO on-screen subtitles / captions (user decision)
- Do NOT show any translated/spoken-text captions in the video. `scenes_ar.py` has `CAPTIONS = False`; keep it False.
- The story is carried by the voice + animation only. (Caption code is kept dormant only for reference.)

## 5. Process rules
- New character: generate a parts sheet with the SAME layout/part order and rig it with the same constants; add the face mark.
- Compare a preview frame against `style_ref/` before rendering the full video.
- Keep audio: voice + subtle ambience (wind, pad, footsteps); mouth timing from the real voice.

## 6. Project notes (Part 1 "hook", Chile 33 in Arabic)
- Code: `prepare_hook.py` (cuts parts sheets m/w + sprites + plate layers), `hook_scenes.py` (rig, shots, timeline), `render_hook.py` (`--preview t1,t2` / `--range f0 f1 out.mp4`; two halves rendered in parallel then concatenated), `audio_hook.py` (voice + SFX mix), `align_hook.py` (phrase timing from silences).
- Characters: `m` miner (hard hat), `w` woman, `ar` civilian; all share the same part layout/rig, variations via shirt/pants tint, flip, scale. Every one gets the face mark.
- Shots: exterior dawn -> tunnel crew -> collapse (rocks, dust, shake) -> 700 m cutaway pan -> dark refuge + food -> surface vigil (time-lapse day/night) -> cutaway pan -> refuge, men gather. No captions.
