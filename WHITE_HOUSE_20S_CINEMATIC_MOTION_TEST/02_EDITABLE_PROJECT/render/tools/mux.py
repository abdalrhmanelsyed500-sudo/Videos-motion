#!/usr/bin/env python3
"""mux.py — combine silent video + synthesized audio into the final MP4.
Usage: python3 tools/mux.py <silent.mp4> <mix.wav> <out.mp4>"""
import subprocess, sys, os

FFMPEG = '/home/user/.venv-wh20s/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v9.0.2'

silent, mix, out = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(os.path.dirname(out), exist_ok=True)
cmd = [
    FFMPEG, '-y',
    '-i', silent, '-i', mix,
    '-map', '0:v:0', '-map', '1:a:0',
    '-c:v', 'copy',
    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
    '-movflags', '+faststart',
    '-t', '20',
    out,
]
print(' '.join(cmd))
r = subprocess.run(cmd, capture_output=True, text=True)
print(r.stdout[-800:])
print(r.stderr[-800:])
print('exit', r.returncode)
