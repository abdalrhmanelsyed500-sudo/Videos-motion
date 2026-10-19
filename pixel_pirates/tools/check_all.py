"""One command for every automatic check (Module A7).

  python tools/check_all.py                 # everything that runs without Godot
  python tools/check_all.py --quick         # skip the slow island-kit tests
  python tools/check_all.py --godot PATH    # also run the in-engine tests (or set env GODOT_EXE)

Writes build/check_report.md. Exit code 0 only if every step passed.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
ERROR_MARKERS = ("SCRIPT ERROR", "Parse Error", "Compile Error", "ERROR: Failed to load script", "Invalid call", "Identifier not found")


def run(cmd: list[str], cwd: Path = ROOT, timeout: int = 900) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as e:
        return 124, f"timeout after {timeout}s\n{e.stdout or ''}"
    except FileNotFoundError as e:
        return 127, str(e)


def tool(name: str) -> list[str] | None:
    exe = shutil.which(name) or str(Path(sys.executable).parent / name)
    return [exe] if Path(exe).exists() else None


def godot_tests(exe: str) -> tuple[int, str]:
    """Imports the project, then runs res://tests/run_all.gd. Fails on a script error even if Godot exits 0."""
    proj = str(ROOT / "game")
    rc1, out1 = run([exe, "--headless", "--path", proj, "--import"], timeout=600)
    rc, out = run([exe, "--headless", "--path", proj, "--script", "res://tests/run_all.gd"], timeout=600)
    text = out1[-1500:] + "\n----\n" + out
    m = re.search(r"TESTS:\s*(\d+)\s+checks,\s*(\d+)\s+failed", out)
    errs = [ln for ln in out.splitlines() if any(k in ln for k in ERROR_MARKERS)]
    if not m:
        return 1, text + "\nNO 'TESTS: N checks, M failed' LINE FOUND: the test runner did not finish."
    if errs:
        return 1, text + "\nENGINE ERRORS:\n" + "\n".join(errs[:20])
    return (0 if int(m.group(2)) == 0 and rc == 0 else 1), text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--godot", default=os.environ.get("GODOT_EXE", ""))
    a = ap.parse_args()
    steps: list[tuple[str, list[str] | None, Path]] = [
        ("project check (data, parity, island kit, refs, content rules)", [PY, "tools/check_project.py"], ROOT),
        ("data tools tests", [PY, "tools/data_tools/test_data_tools.py"], ROOT),
        ("design checks tests (pillar invariants, content lint)", [PY, "tools/data_tools/test_design_checks.py"], ROOT),
        ("economy tests (market maths fixtures, invariants, mutations)", [PY, "tools/data_tools/test_economy.py"], ROOT),
        ("ocean tests (world invariants, wildlife seed, slice route, golden fixtures)", [PY, "tools/data_tools/test_ocean.py"], ROOT),
        ("GDScript logic parity (ocean.gd, wildlife.gd and sea_state.gd translated and replayed; NOT a Godot run)", [PY, "tools/data_tools/gd_logic_check.py"], ROOT),
    ]
    steps.append(("H2D-0 art checks (borders, palette, heading silhouettes)", [PY, "tools/h2d/check_h2d_art.py"], ROOT))
    steps.append(("H2D-0 shader checks (transpile to GLSL + glslang; lenient, NOT Godot)", [PY, "tools/h2d/check_shaders.py"], ROOT))
    steps.append(("H2D-0.1 helm: Python twin, fixture, tuning JSON in sync", [PY, "tools/h2d/helm_logic.py", "--check"], ROOT))
    steps.append(("H2D-0.2 environment: Python twin, fixture, tuning JSON and GDScript defaults in sync", [PY, "tools/h2d/env_logic.py", "--check"], ROOT))
    steps.append(("H2D-0.3 sail model: Python twin and fixture in sync", [PY, "tools/h2d/sail_logic.py", "--check"], ROOT))
    steps.append(("H2D-1 harbor: Python twin, fixture, tuning JSON and GDScript defaults in sync", [PY, "tools/h2d/harbor_logic.py", "--check"], ROOT))
    steps.append(("H2D-1 harbor geometry (berth, lane, pier, props, start reachable)", [PY, "tools/h2d/check_harbor.py"], ROOT))
    steps.append(("H2D-1.2 scatter: Python twin and fixture in sync", [PY, "tools/h2d/scatter_logic.py", "--check"], ROOT))
    steps.append(("H2D-1.2 on-foot reachability (pier to all four stops, trunks and blockers)", [PY, "tools/h2d/check_land.py"], ROOT))
    steps.append(("H2D-1.2 scale audit (island size, pirate vs sloop, walking and sailing times)", [PY, "tools/h2d/check_scale.py"], ROOT))
    steps.append(("H2D-1.2.1 GDScript static type scan (argument and member types across project classes; heuristic, NOT Godot)", [PY, "tools/h2d/check_gd_types.py", "--all"], ROOT))
    steps.append(("CP-1 economy: Python twin, fixture, tuning JSON, GDScript defaults and balance targets in sync", [PY, "tools/h2d/economy_logic.py", "--check"], ROOT))
    steps.append(("CP-1 Fish Row layout (people, recruits, market, bridges, decks, moored hulls, fishing grounds; NOT Godot)", [PY, "tools/h2d/check_port.py"], ROOT))
    steps.append(("CP-1 docs vs data (purse, prices, recruit costs, grounds, hold, spoilage must match the manual; NOT Godot)", [PY, "tools/h2d/check_docs.py"], ROOT))
    steps.append(("H2D-1.2.2 hero frustum-cull model + source guard (reproduces the invisible-pirate bug; NOT Godot)", [PY, "tools/h2d/check_hero_cull.py"], ROOT))
    steps.append(("H2D-0.1 GDScript warning scan (heuristic, NOT Godot)", [PY, "tools/h2d/check_gd_warnings.py"], ROOT))
    if not a.quick:
        steps.append(("island kit tests", [PY, "tools/island_kit/test_island_kit.py"], ROOT))
    gdlint, gdparse = tool("gdlint"), tool("gdparse")
    steps.append(("gdlint (style)", gdlint + ["."] if gdlint else None, ROOT / "game"))
    gd_files = sorted(str(p) for p in (ROOT / "game").rglob("*.gd"))
    steps.append(("gdparse (syntax)", gdparse + gd_files if gdparse else None, ROOT / "game"))
    results = []
    for name, cmd, cwd in steps:
        t0 = time.time()
        if cmd is None:
            results.append((name, "SKIP", 0.0, "tool not installed: pip install gdtoolkit"))
            continue
        rc, out = run(cmd, cwd)
        results.append((name, "PASS" if rc == 0 else "FAIL", time.time() - t0, out.strip()))
    t0 = time.time()
    if a.godot:
        rc, out = godot_tests(a.godot)
        results.append(("Godot in-engine tests", "PASS" if rc == 0 else "FAIL", time.time() - t0, out.strip()))
    else:
        results.append(("Godot in-engine tests", "SKIP", 0.0, "no Godot given: use --godot PATH or set GODOT_EXE (see tools/run_godot_tests.bat)"))
    lines = ["# check_all report", ""]
    print()
    for name, st, dt, out in results:
        print(f"{st:5} {name} ({dt:.1f}s)")
        lines.append(f"- **{st}** {name} ({dt:.1f}s)")
    failed = [r for r in results if r[1] == "FAIL"]
    for name, st, _, out in failed:
        print(f"\n--- {name} ---\n{out[-3000:]}")
    lines += ["", "## Output of failed steps"] + [f"### {n}\n```\n{o[-4000:]}\n```" for n, s, _, o in failed]
    (ROOT / "build").mkdir(exist_ok=True)
    (ROOT / "build" / "check_report.md").write_text("\n".join(lines) + "\n")
    print("\nALL PASSED" if not failed else f"\n{len(failed)} STEP(S) FAILED  (see build/check_report.md)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
