"""CP-1 docs vs data: every number the manual (docs/CP1_CAPITAL_PORT.md) states about the starting economy must equal the data the game
loads (game/data/tuning/tuning_port.json, game/data/port/*.json). A drifting doc is a bug: the player and the tester read it.
Pure Python, no Godot. Exit 0 = consistent."""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = (ROOT / "docs/CP1_CAPITAL_PORT.md").read_text(encoding="utf-8")
DATA = ROOT / "game/data"
fails = []


def fail(msg):
    fails.append(msg)
    print("FAIL:", msg)


def need(cond, msg):
    if not cond:
        fail(msg)


def num(v):
    return ("%g" % v)


tun = {r["key"]: r["value"] for r in json.loads((DATA / "tuning/tuning_port.json").read_text())["records"]}
fish = json.loads((DATA / "port/fish_market.json").read_text())["species"]
rec = json.loads((DATA / "port/recruits_port.json").read_text())
grounds = json.loads((DATA / "port/fishing_grounds.json").read_text())["grounds"]

# the starting purse, the hold, the nets
m = re.search(r"\*\*purse of (\d+) reales\*\*", DOC)
need(m and int(m.group(1)) == int(tun["port.start_reales"]), f"doc purse {m and m.group(1)} != tuning port.start_reales {tun['port.start_reales']}")
need(f"{int(tun['port.hold_kg'])} kg" in DOC, "doc does not state the %d kg hold" % tun["port.hold_kg"])
need(f"**{int(tun['fish.haul_interval_s'])} s**" in DOC, "doc does not state the haul interval %s s" % tun["fish.haul_interval_s"])
need(f"**{num(tun['fish.spoil_per_day'])} of its value per game day**" in DOC, "doc spoilage per day differs from %s" % tun["fish.spoil_per_day"])
need(f"floor **{num(tun['fish.spoil_floor'])}**" in DOC, "doc spoilage floor differs from %s" % tun["fish.spoil_floor"])
need(f"**{num(tun['fish.max_sea'])}**" in DOC, "doc sea limit differs from %s" % tun["fish.max_sea"])
need(f"depth {int(tun['market.fish_depth_reales'])} reales" in DOC.replace("**depth ", "depth ").replace(" reales per species**", " reales per species"),
     "doc market depth differs from %s" % tun["market.fish_depth_reales"])

# prices
for sid, f in fish.items():
    row = re.search(r"\|\s*%s\s*\|\s*([\d.]+)\s*\|" % re.escape(f["name"].replace("Atlantic ", "Atlantic ")), DOC)
    need(row and abs(float(row.group(1)) - f["base_reales_per_kg"]) < 1e-9, f"doc price of {f['name']} ({row and row.group(1)}) != data {f['base_reales_per_kg']}")

# recruits
total = 0
for cid in rec["order"]:
    r = rec["recruits"][cid]
    total += r["cost"]
    short = r["name"]
    # the table writes either "Name, age" or the full name with the nickname quoted
    row = re.search(r"\|\s*%s(?:,\s*%d)?\s*\|\s*%s\s*\|\s*(\d+)\s*\|" % (re.escape(short), r["age"], re.escape(r["role"])), DOC)
    need(row and int(row.group(1)) == r["cost"], f"doc cost of {short} ({row and row.group(1)}) != data {r['cost']}")
need(f"{total}" in DOC, f"doc does not state the total recruit cost {total}")

# grounds: position, radius, richness, distance from the berth (21.4, 21)
for gid, g in grounds.items():
    dist = math.hypot(g["x"] - 21.4, g["z"] - 21.0)
    row = re.search(r"\|\s*%s\s*\|\s*\((-?\d+), (-?\d+)\), r (\d+), (\d+) m\s*\|\s*([\d.]+)\s*\|" % re.escape(g["name"]), DOC)
    if not row:
        fail(f"doc has no table row for {g['name']}")
        continue
    need(int(row.group(1)) == g["x"] and int(row.group(2)) == g["z"] and int(row.group(3)) == g["r"], f"doc position/radius of {g['name']} differs")
    need(abs(int(row.group(4)) - dist) <= 3, f"doc distance of {g['name']} is {row.group(4)} m, the data gives {dist:.0f} m")
    need(abs(float(row.group(5)) - g["richness"]) < 1e-9, f"doc richness of {g['name']} differs")
    if g["min_crew"] >= 1:
        line = [ln for ln in DOC.splitlines() if ln.startswith("| " + g["name"] + " |")]
        need(line and "needs at least %d hand" % g["min_crew"] in line[0], f"doc does not say {g['name']} needs a hand")

# the people count the docs state must be the baked count
cay = json.loads((ROOT / "game/h2d/art/anvil_cay.json").read_text())
npeople = len(cay["port"]["npcs"])
for fn in ("docs/CP1_CAPITAL_PORT.md", "docs/CP1_REVISION_R3.md", "docs/CP1R_CITY_DISTRICT_PLAN.md", "docs/CANON_BIBLE.md"):
    txt = (ROOT / fn).read_text(encoding="utf-8")
    need(f"{npeople} people" in txt, f"{fn} does not state the baked people count ({npeople} people)")
need(not re.search(r"\b184 people\b", DOC), "CP1_CAPITAL_PORT.md still says 184 people")

print("docs vs data:", "ALL CONSISTENT" if not fails else f"{len(fails)} problem(s)")
sys.exit(1 if fails else 0)
