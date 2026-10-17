# RANGER – top-down sci-fi pixel-art character (32×32)
Procedural pixel rig (`pxlib.py` + `ranger.py`), regenerate everything with `python3 build.py`.
- 4 directions (down / up / right / left, left is re-drawn with the light kept top-left), idle (4f), walk (6f), shoot (4f)
- 14-colour-ramp palette: 6 materials × 5 tones (outline / shadow / base / light / highlight), selective coloured outlines, no anti-aliasing
- `out/ranger_sheet_32.png` (6 cols × 12 rows, 192×384, with soft ground shadow), `_noshadow` variant, `ranger_atlas.json` (frames + frameTags + durations, pivot = feet), GIF previews, palette (.png/.hex/.gpl), `QA_REPORT.txt`
Known limits: single character/colour scheme, no diagonal directions, no hurt/death/run animations yet.
