"""Species quota report (Module E1): where the seed list of wildlife stands against the 200-species target.
    python tools/world/species_quota.py
The targets are PROVISIONAL (owner E1): they say how many species of each group the finished catalogue should have,
so that H (ocean life) can be planned in batches. Exit code is always 0: this is a plan, not a gate.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WILD = ROOT / "game" / "data" / "wildlife"
REG = ROOT / "game" / "data" / "world" / "regions.json"
TARGET = {"pelagic_fish": 24, "reef_fish": 20, "cold_fish": 18, "shark_ray": 16, "cetacean": 20, "pinniped": 9, "reptile": 9,
          "cephalopod": 12, "crustacean": 10, "cnidarian": 8, "plankton": 5, "invertebrate": 7, "seabird": 24, "strange": 18}
PER_REGION_MIN = 25  # every region should end with at least this many species at abundance >= 0.3 after the expansion


def main() -> int:
    species = [r for f in sorted(WILD.glob("*.json")) for r in json.loads(f.read_text())["records"]]
    regions = [r["id"] for r in json.loads(REG.read_text())["records"]]
    have = collections.Counter(s["group"] for s in species)
    total_target = sum(TARGET.values())
    print(f"seed {len(species)} / target {total_target}\n")
    print(f"{'group':14} {'have':>4} {'target':>6} {'to add':>6}")
    for g, t in TARGET.items():
        print(f"{g:14} {have.get(g, 0):4d} {t:6d} {max(0, t - have.get(g, 0)):6d}")
    unknown = sorted(set(have) - set(TARGET))
    if unknown:
        print("groups with no target:", unknown)
    print(f"\n{'region':24} {'species >=0.3':>13} {'to add (for ' + str(PER_REGION_MIN) + ')':>18}")
    by_region = {r: 0 for r in regions}
    for s in species:
        for e in s["regions"]:
            if e["abundance"] >= 0.3 and e["region"] in by_region:
                by_region[e["region"]] += 1
    for r in regions:
        print(f"{r:24} {by_region[r]:13d} {max(0, PER_REGION_MIN - by_region[r]):18d}")
    real = sum(1 for s in species if s["real"])
    print(f"\nreal {real}, fictional {len(species) - real} ({100 * (len(species) - real) / len(species):.0f}%; rule 5..25%)")
    batches = (total_target - len(species) + 24) // 25
    print(f"expansion: {total_target - len(species)} species = {batches} batches of about 25 (one batch per region cluster, in H)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
