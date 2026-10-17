"""Full pipeline: rigs -> audio -> video -> mux -> QA -> sheets."""
import os, subprocess, sys
ROOT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, ROOT)
from rigkit import build, render, audio, validate, sheets
FF = render.FFMPEG; od = os.path.join(ROOT, 'out', 'demo'); os.makedirs(od, exist_ok=True)
build.build_all(os.path.join(ROOT, 'out', 'rigs'))
ep = render.make_episode(); audio.mix(ep, os.path.join(ROOT, 'audio'), os.path.join(od, 'mix.wav'))
subprocess.check_call([sys.executable, '-m', 'rigkit.render', 'video', os.path.join(od, 'video_silent.mp4')], cwd=ROOT)
subprocess.check_call([FF, '-y', '-loglevel', 'error', '-i', os.path.join(od, 'video_silent.mp4'), '-i', os.path.join(od, 'mix.wav'), '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', os.path.join(od, 'Cartoon_RigKit_Demo.mp4')])
subprocess.check_call([sys.executable, '-m', 'rigkit.validate', os.path.join(od, 'Cartoon_RigKit_Demo.mp4')], cwd=ROOT)
subprocess.check_call([sys.executable, '-m', 'rigkit.sheets'], cwd=ROOT)
