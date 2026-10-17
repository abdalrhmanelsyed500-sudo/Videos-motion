# Penguin Commando (AKM) – 64×64 top-down pixel art

Character: penguin with red headband, olive tactical vest and an AKM rifle. View: top-down 3/4 (camera 44° above the ground), light from top-left.
Directions: **down (front), up (back), right, left**.  Canvas: 64×64 per frame.

| animation | frames | ms/frame | loop | notes |
|---|---|---|---|---|
| idle | 6 | 140 | yes | breathing, head sway, one blink frame |
| walk | 8 | 90 | yes | waddle: body roll, foot lift, rifle at low-ready |
| run | 8 | 65 | yes | forward lean, longer stride, headband streaming |
| shoot | 4 | 60 | yes | full-auto loop: muzzle flash, recoil, bolt, ejected brass |
| reload | 16 | 95 | no | drop mag, grab new mag from the vest, insert, charge, ready |
| hit | 7 | 70 | no | white-red hit flash, blood spray, flinch and recover |
| death | 16 | 100 | no | hit, rifle flung away, falls on its back, blood pool; last frame is the held pose |

## Files (`out/`)
* `sheets/penguin_<anim>_sheet.png` – one sprite sheet per animation. **Rows = down, up, right, left. Columns = frames.** Transparent PNG, soft ground shadow included.
* `sheets_noshadow/` – the same without the shadow (draw your own).
* `gifs/penguin_<anim>.gif` – one GIF per animation, 4 directions side by side (×4).
* `gifs_by_direction/` – 28 single-direction GIFs (×6).  `frames_png/` – every frame as its own PNG.
* `penguin_ALL_sheet.png` – every animation in one atlas (28 rows × 16 columns), rows listed in `penguin_atlas.json`.
* `penguin_atlas.json` – frame counts, durations, loop flag, row per direction, per-direction pivot offsets.
* `penguin_palette.png/.hex/.gpl` – the 12 colour ramps × 5 tones = 60 colours. `QA_REPORT.txt` – automated checks.

## Pivot
Feet contact point = **(32 + pivot_dx, 45)** in the 64×64 frame. `pivot_dx` is 0 everywhere except `right` (−3) and `left` (+3) for all non-death animations: the whole figure is shifted 3 px away from the gun so the muzzle flash never leaves the frame. Death frames: the body is shifted so the lying penguin stays inside the frame (no pivot offset).

## How it is made
`sdf3d.py` – tiny orthographic ray-marcher that renders a 3D-modelled character directly onto the 64×64 pixel grid, then turns it into real pixel art (per-material 5-tone ramps, banded toon light, 1 px selective outline, separation lines, no anti-aliasing).
`penguin.py` – model + palette. `anims.py` – pose tables / keyframes. `frames.py` – effects (muzzle flash, blood, pool). `build_all.py` – exports everything: `python build_all.py out` (~35 s).
Because the character is a 3D rig, new directions (diagonals), colour variants, new weapons or new animations are cheap to add.

## Honest limits
* It is 3D-derived pixel art, cleaned by rules, not hand-pixelled frame by frame. A human pixel artist would still polish some frames.
* Back view: the rifle is mostly hidden by the body (only the barrel/stock peek out) – that is what the geometry gives.
* The head is a dome from above, so the face is only clearly readable in the front view.
* Reload is clearest from the side; from the front the rifle points at the camera.
* Only 4 directions. One character, one palette.
