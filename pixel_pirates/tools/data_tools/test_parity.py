"""Runs game/tests/fixtures/validator_cases.json through the Python validator.

The GDScript twin (game/tests/test_schema.gd) runs the SAME file, so the two validators are proven equal on every case.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import minischema as M  # noqa: E402

FIXTURE = Path(__file__).resolve().parents[2] / "game" / "tests" / "fixtures" / "validator_cases.json"


def run_all(verbose: bool = True) -> int:
    fx = json.loads(FIXTURE.read_text())
    known = fx["ref_known"]

    def lookup(kind, i):
        return i in known.get(kind, [])

    bad = 0
    for c in fx["cases"]:
        got = M.error_paths(M.validate(c["value"], c["schema"], lookup))
        if got != c["error_paths"]:
            bad += 1
            print("MISMATCH", c["name"], "expected", c["error_paths"], "got", got)
    if verbose:
        print(f"validator cases: {len(fx['cases'])}, mismatches: {bad}")
    import validate_data as V  # noqa: PLC0415
    wf = json.loads((FIXTURE.parent / "world_cases.json").read_text())
    wbad = 0
    for c in wf["cases"]:
        got = V.world_codes({i["id"]: i for i in c["islands"]})
        if got != c["codes"]:
            wbad += 1
            print("WORLD MISMATCH", c["name"], "expected", c["codes"], "got", got)
    if verbose:
        print(f"world-rule cases: {len(wf['cases'])}, mismatches: {wbad}")
    return 1 if (bad or wbad) else 0


if __name__ == "__main__":
    sys.exit(run_all())
