#!/usr/bin/env python3
"""Measure the available headless WASM engine, not graphical FPS.

Usage from repository root: python3 iron_atlas/tools/benchmark_stage2.py
On Linux ru_maxrss is peak KiB for the Node/Godot child process (engine + game).
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
runner = ROOT / "pixel_pirates/tools/godot_node/run.mjs"
game = ROOT / "iron_atlas/game"
env = os.environ.copy()
env.update(GODOT_REGEX_SHIM="1", GODOT_RAW="1", GODOT_SECONDS="120")
cmd = ["node", str(runner), str(game), "--fixed-fps", "60", "--script", "res://tests/benchmark_stage2.gd"]
started = time.perf_counter()
try:
    result = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=150)
except (OSError, subprocess.TimeoutExpired) as exc:
    print(f"Benchmark failed: {exc}", file=sys.stderr)
    sys.exit(1)
elapsed = time.perf_counter() - started
output = result.stdout + result.stderr
lines = [line.removeprefix("PERF_JSON ") for line in output.splitlines() if line.startswith("PERF_JSON ")]
if result.returncode != 0 or len(lines) != 1 or any(s in output for s in ("SCRIPT ERROR", "ERROR:", "JS EXCEPTION", "time limit reached")):
    print(output, file=sys.stderr)
    sys.exit(1)
metrics = json.loads(lines[0])
usage = resource.getrusage(resource.RUSAGE_CHILDREN)
metrics.update(process_wall_seconds=round(elapsed, 3), process_peak_rss_kib=usage.ru_maxrss,
               process_user_cpu_seconds=round(usage.ru_utime, 3), process_system_cpu_seconds=round(usage.ru_stime, 3))
print(json.dumps(metrics, indent=2, sort_keys=True))
