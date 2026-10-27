#!/usr/bin/env python3
"""Static project audit: resource paths, data files and generated asset hashes."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES_RE = re.compile(r'res://[A-Za-z0-9_./-]+')
GENERATED_PREFIXES = (
    "res://tests/reports/", "res://screenshots/", "res://logs/", "res://.godot/",
)
REQUIRED_FILES = [
    "project.godot", "icon.svg", "README.md",
    "scenes/main.tscn", "scenes/race_world.tscn",
    "docs/00-production-plan.md", "docs/01-visual-analysis.md",
    "docs/02-visual-benchmark.md", "docs/03-architecture.md", "docs/04-test-report.md",
    "assets/ASSET_MANIFEST.json", "assets/LICENSE-ASSETS.txt",
    "assets/data/riders.json", "assets/data/bikes.json", "assets/data/traffic.json",
]


def resolve(res_path: str) -> Path:
    return ROOT / res_path[len("res://"):]


def check_paths() -> list[str]:
    errors: list[str] = []
    for source in list(ROOT.rglob("*.gd")) + list(ROOT.rglob("*.tscn")) + [ROOT / "project.godot"]:
        text = source.read_text(encoding="utf-8", errors="ignore")
        for match in RES_RE.findall(text):
            # Format strings and dynamically concatenated paths are verified
            # separately through generated data below.
            clean = match.rstrip(".")
            if "%" in clean or "+" in clean:
                continue
            # Dynamic format-string prefixes (rider_%02d_..., brick_%d.png, ...)
            # are checked against the generated JSON data separately.
            if clean.endswith("_"):
                continue
            # Reports and screenshots are written at runtime, not shipped as
            # static input resources.
            if any(clean.startswith(prefix) for prefix in GENERATED_PREFIXES):
                continue
            target = resolve(clean)
            if not target.exists():
                errors.append(f"{source.relative_to(ROOT)} references missing {clean}")
    return sorted(set(errors))


def check_data() -> tuple[list[str], dict]:
    errors: list[str] = []
    summary: dict = {}
    riders = json.loads((ROOT / "assets/data/riders.json").read_text(encoding="utf-8"))
    bikes = json.loads((ROOT / "assets/data/bikes.json").read_text(encoding="utf-8"))
    traffic = json.loads((ROOT / "assets/data/traffic.json").read_text(encoding="utf-8"))
    summary["riders"] = len(riders["riders"])
    summary["bikes"] = len(bikes["bikes"])
    summary["traffic_types"] = len(traffic["types"])
    if len(riders["riders"]) != 8:
        errors.append("Expected eight riders")
    if len(bikes["bikes"]) != 6:
        errors.append("Expected six motorcycles")
    if len(traffic["types"]) != 7:
        errors.append("Expected seven traffic types")
    rider_ids = [str(r.get("id", "")) for r in riders["riders"]]
    bike_ids = [str(b.get("id", "")) for b in bikes["bikes"]]
    hair_styles = [str(r.get("hair_style", "")) for r in riders["riders"]]
    accessories = [str(r.get("accessory", "")) for r in riders["riders"]]
    if len(set(rider_ids)) != len(rider_ids):
        errors.append("Duplicate rider ids")
    if len(set(bike_ids)) != len(bike_ids):
        errors.append("Duplicate bike ids")
    if len(set(hair_styles)) < 7:
        errors.append("Rider hair silhouettes are not sufficiently distinct")
    if len(set(accessories)) < 7:
        errors.append("Rider accessories are not sufficiently distinct")
    for i, rider in enumerate(riders["riders"]):
        path = ROOT / f"assets/ui/portraits/rider_{i:02d}_{rider['id']}.png"
        if not path.exists():
            errors.append(f"Missing rider portrait: {path.relative_to(ROOT)}")
    for i, bike in enumerate(bikes["bikes"]):
        path = ROOT / f"assets/ui/portraits/bike_{i:02d}_{bike['id']}.png"
        if not path.exists():
            errors.append(f"Missing bike portrait: {path.relative_to(ROOT)}")
    for type_def in traffic["types"]:
        if float(type_def.get("speed_min", 0)) >= float(type_def.get("speed_max", 0)):
            errors.append(f"Invalid speed range for {type_def.get('id')}")
    return errors, summary


def check_manifest() -> tuple[list[str], dict]:
    errors: list[str] = []
    manifest_path = ROOT / "assets/ASSET_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checked = 0
    for entry in manifest.get("files", []):
        path = ROOT / entry["path"]
        if not path.exists():
            errors.append(f"Manifest file missing: {entry['path']}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != entry.get("sha256"):
            errors.append(f"Manifest checksum mismatch: {entry['path']}")
        checked += 1
    return errors, {"manifest_entries": checked, "declared_total_bytes": manifest.get("total_bytes", 0)}


def check_sources() -> list[str]:
    errors: list[str] = []
    markers = ("TODO", "FIXME", "XXX")
    for source in ROOT.rglob("*.gd"):
        text = source.read_text(encoding="utf-8", errors="ignore")
        for marker in markers:
            if marker in text:
                errors.append(f"Unfinished marker {marker} in {source.relative_to(ROOT)}")
    project = (ROOT / "project.godot").read_text(encoding="utf-8")
    match = re.search(r'run/main_scene="([^"]+)"', project)
    if not match or not resolve(match.group(1)).exists():
        errors.append("Main scene path in project.godot is invalid")
    return errors


def main() -> int:
    errors: list[str] = []
    summary: dict = {}
    for path in REQUIRED_FILES:
        if not (ROOT / path).exists():
            errors.append(f"Missing required file: {path}")
    errors.extend(check_paths())
    data_errors, data_summary = check_data()
    errors.extend(data_errors)
    summary.update(data_summary)
    manifest_errors, manifest_summary = check_manifest()
    errors.extend(manifest_errors)
    summary.update(manifest_summary)
    errors.extend(check_sources())
    summary["gdscript_files"] = len(list(ROOT.rglob("*.gd")))
    summary["scene_files"] = len(list(ROOT.rglob("*.tscn")))
    summary["generated_asset_files"] = len([p for p in (ROOT / "assets").rglob("*") if p.is_file()])
    report = {"passed": not errors, "error_count": len(errors), "errors": errors, "summary": summary}
    output = ROOT / "tests/reports/static_audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "errors": errors[:20], "summary": summary}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
