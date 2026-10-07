# Videos-motion

## Current deliverable

`renders/time-origin-sample.mp4` is a 31.5-second, 1280×720 style test built from the opening of the supplied narration. It contains the original narration audio, animated captions, a hand-drawn puppet in the requested thick-ink style, comic props, and camera movement over realistic Cairo / Egypt plates.

The sample is intentionally a motion test rather than a slideshow:

- The puppet has independent body, face, eyes, mouth, bobbing and reaction animation.
- The mouth opens from the measured audio envelope so the character reacts to the narration.
- Realistic plates use slow parallax drift and crossfades.
- Red crosses, question marks, paper cards, a sun dial and a clock are animated as comic accents.
- Arabic captions were cleaned from the noisy ASR WebVTT and timed against the supplied timestamps.

## Source and renderer

- `tools/render_sample.py` renders the sample from an MP3/WAV input.
- `assets/` contains the realistic background plates used by the sample.
- `docs/time-history-shot-plan.md` contains the audio analysis and the planned visual language for the full narration.

To render locally after installing the Python dependencies in `requirements.txt`:

```bash
python tools/render_sample.py --audio path/to/merged-audio.mp3 \
  --output renders/time-origin-sample.mp4
```
