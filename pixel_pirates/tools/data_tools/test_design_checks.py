"""Tests for design_checks.py (B1). Run: python tools/data_tools/test_design_checks.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import design_checks as D  # noqa: E402

fails = 0


def expect(name: str, cond: bool, detail: str = "") -> None:
    global fails
    print(("ok   " if cond else "FAIL ") + name + ("" if cond else f"  {detail}"))
    fails += 0 if cond else 1


T = D.load_tuning()
expect("real tuning satisfies every pillar invariant", D.invariants(T) == [], str(D.invariants(T)))


def broken(**kw):
    t = dict(T)
    t.update(kw)
    return D.invariants(t)


expect("ladder order is enforced", any("ladder" in p for p in broken(**{"warn.warning_days": 9})))
expect("ladder must stay above zero", any("ladder" in p for p in broken(**{"warn.critical_days": 0})))
expect("3 warning steps minimum", any("3 warning" in p for p in broken(**{"warn.min_steps_before_loss": 2})))
expect("2 recovery options minimum", any("recovery" in p for p in broken(**{"recovery.min_options": 1})))
expect("dead ocean band wider than sea band", any("forecast band" in p for p in broken(**{"plan.forecast_spread_dead": 0.2})))
expect("narrowest band is above zero and below the sea band", any("narrowest" in p for p in broken(**{"plan.forecast_spread_min": 0})) and any("narrowest" in p for p in broken(**{"plan.forecast_spread_min": 0.3})))
expect("voyage bands must increase", any("strictly" in p for p in broken(**{"voyage.passage_max_minutes": 8})))
expect("dead ocean about 2x longest crossing", any("twice" in p for p in broken(**{"voyage.dead_max_minutes": 50})))
expect("shares must add to 100", any("add to 100" in p for p in broken(**{"share.sea_pct": 45})))
expect("sea share not below island share", any("at least as much" in p for p in broken(**{"share.sea_pct": 30, "share.island_pct": 45})))
expect("combat capped at 12 percent", any("combat" in p for p in broken(**{"share.combat_pct_max": 20, "share.sea_pct": 28})))
expect("missing keys are reported", any("missing" in p for p in D.invariants({"warn.advisory_days": 7})))

hit = D.content_findings({"x.json": {"records": [{"name": "Temple of the Gods", "note": "x"}]}})
expect("lint: religion word", any("rule 3" in h for h in hit))
expect("lint: sexual word", any("rule 2" in h for h in D.content_findings({"x.json": {"name": "The Naked Cove"}})))
expect("lint: female word in a name", any("rule 1" in h for h in D.content_findings({"x.json": {"name": "The Queen's Rest"}})))
expect("lint: word boundary (no false hit on 'Godfrey-less' words like 'goddard' or 'shelf')",
       D.content_findings({"x.json": {"name": "Shelf of Goddard"}}) == [])
expect("lint: free-text note may mention the rule", D.content_findings({"x.json": {"note": "no female crew"}}) == [])
expect("lint: id and gender fields skipped", D.content_findings({"x.json": {"id": "crew_she", "gender": "male"}}) == [])
expect("real data has no banned words", D.scan_data() == [], str(D.scan_data()[:3]))

r = D.reckoning(T, 12, 14, 0.25, {"hardtack_kg": 90, "water_l": 480})
expect("reckoning band 10.5 / 14 / 17.5", r["band_days"] == (10.5, 14, 17.5))
expect("reckoning daily need 5.4 kg and 30 L", r["per_day"] == {"hardtack_kg": 5.4, "water_l": 30.0})
expect("reckoning flags the worst case as short", all(row["margin_days_worst"] < 0 for row in r["rows"]))
expect("reckoning expected need is stock-compatible", all(row["need_expected"] < row["have"] for row in r["rows"]))
expect("ladder rungs", [D.rung(x, T) for x in (20, 7, 3.1, 3, 1, 0.2)] == ["ok", "advisory", "advisory", "warning", "critical", "critical"])

print("design checks tests:", "PASS" if not fails else f"{fails} FAILED")
sys.exit(1 if fails else 0)
