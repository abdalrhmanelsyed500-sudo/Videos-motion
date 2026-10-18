"""Writes game/data/tuning/tuning_env.json (H2D-0.2): the numbers of the shared environment model (env.*) and the ship's
response to the sea (motion.*). Edit the table, re-run, then re-run env_logic.py --fixture. Every value is PROVISIONAL (owner E1:
to be confirmed by hand on the dev PC)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = "H2D-0.2 weather, sea state and ship response; first values tuned by simulation, confirm by eye in Godot"
# key, value, unit, min, max, note
TABLE = [
    ("env.wind_tau_s", 5.0, "seconds", 0.5, 60, "How slowly the mean wind speed follows the weather target (a front arrives over this time)."),
    ("env.wind_dir_tau_s", 8.0, "seconds", 0.5, 90, "How slowly the wind direction swings to a new direction."),
    ("env.sea_build_s", 14.0, "seconds", 1, 120, "Time constant for the wave height to GROW towards a rougher target (about 3x this to reach 95 percent)."),
    ("env.sea_decay_s", 24.0, "seconds", 1, 180, "Time constant for the waves to SUBSIDE; larger than the build time because a sea dies away slowly."),
    ("env.wave_dir_tau_s", 20.0, "seconds", 1, 180, "How slowly the wave direction turns after the wind has turned (the old sea lingers)."),
    ("env.rain_build_s", 5.0, "seconds", 0.5, 60, "Time constant for rain to set in."),
    ("env.rain_decay_s", 9.0, "seconds", 0.5, 90, "Time constant for rain to ease off."),
    ("env.air_tau_s", 6.0, "seconds", 0.5, 60, "Time constant for storminess and fog."),
    ("env.gust_gain", 0.45, "ratio", 0, 1.5, "Extra wind speed at the peak of a gust, as a fraction of the mean wind, at full gustiness."),
    ("env.gust_veer_deg", 12.0, "degrees", 0, 40, "How far the wind direction veers during a gust (also tilts the rain)."),
    ("env.gust_manual_decay_s", 4.0, "seconds", 0.5, 20, "How long a gust fired by hand (key G) takes to die away."),
    ("env.gust_surge", 0.12, "ratio", 0, 0.4, "Extra boat speed at the peak of a gust (sails drawing harder). 0 turns the effect off."),
    ("env.wave_visual_gain", 1.3, "ratio", 0.5, 2.5, "Presentation gain on the wave height so storms read clearly at the camera distance."),
    ("env.crest_p_calm", 1.0, "exponent", 1.0, 4, "Crest sharpness in a calm sea (1 = plain sine)."),
    ("env.crest_p_gale", 2.6, "exponent", 1.0, 5, "Crest sharpness in a gale: peaked crests, flat troughs."),
    ("env.sea_wave_w", 0.5, "weight", 0, 1, "Weight of the wave height in the sea-state index."),
    ("env.sea_wind_w", 0.35, "weight", 0, 1, "Weight of the mean wind speed in the sea-state index."),
    ("env.sea_storm_w", 0.2, "weight", 0, 1, "Weight of storminess in the sea-state index."),
    ("env.sea_wave_ref_m", 6.5, "metres", 1, 14, "Wave height that counts as a full sea in the index."),
    ("env.sea_wind_ref_kn", 38.0, "knots", 10, 80, "Wind speed that counts as a full gale in the index."),
    ("env.sea_calm_max", 0.12, "index", 0, 1, "Sea-state index below which the sea is Calm."),
    ("env.sea_breezy_max", 0.35, "index", 0, 1, "Below this the sea is Breezy."),
    ("env.sea_rough_max", 0.65, "index", 0, 1, "Below this the sea is Rough; above it Gale."),
    ("env.sea_storm_min", 0.96, "index", 0, 1, "At or above this the Gale is called a Storm."),
    ("motion.gain", 1.0, "ratio", 0, 2, "Master strength of the ship's roll, pitch and heave on screen (key M cycles off / half / full)."),
    ("motion.roll_max_deg", 10.0, "degrees", 1, 30, "Roll limit (waves plus wind heel)."),
    ("motion.pitch_max_deg", 6.0, "degrees", 1, 20, "Pitch limit."),
    ("motion.heave_max_m", 1.8, "metres", 0.1, 5, "Heave limit."),
    ("motion.roll_period_s", 3.4, "seconds", 1, 10, "Natural roll period of the hull: how fast it answers a wave."),
    ("motion.pitch_period_s", 2.6, "seconds", 1, 10, "Natural pitch period."),
    ("motion.heave_period_s", 2.2, "seconds", 1, 10, "Natural heave period."),
    ("motion.damping", 0.6, "ratio", 0.1, 2, "Damping ratio of all three motions (0.6 = a couple of visible overshoots)."),
    ("motion.wave_follow", 0.8, "ratio", 0.2, 1.2, "How closely the hull follows the wave slope under it (1 = like a cork)."),
    ("motion.heel_deg_per_ms2", 0.04, "deg per (m/s)^2", 0, 0.2, "Wind heel on a beam reach: degrees per squared wind speed in m/s."),
    ("motion.slam_bow_ms", 11.0, "m/s", 1, 20, "Vertical speed of the water meeting the bow above which it throws spray."),
    ("motion.slam_side_ms", 12.0, "m/s", 1, 20, "Same for the rails (sides of the hull)."),
    ("motion.slam_cooldown_calm_s", 4.0, "seconds", 0.3, 10, "Shortest time between spray bursts from one point of the hull in a moderate sea."),
    ("motion.slam_cooldown_gale_s", 1.6, "seconds", 0.3, 10, "Same in a gale."),
    ("motion.slam_min_sea", 0.3, "index", 0, 1, "No spray bursts below this sea-state index."),
]


def main() -> None:
    recs = []
    for key, val, unit, lo, hi, note in TABLE:
        recs.append({"key": key, "value": val, "unit": unit, "min": lo, "max": hi, "provisional": True,
                     "owner": "E1", "source": SRC, "note": note})
    out = {"schema": 1, "kind": "tuning", "records": recs}
    lines = ["{", ' "schema": 1,', ' "kind": "tuning",', ' "records": [']
    for i, r in enumerate(recs):
        lines.append("  " + json.dumps(r) + ("," if i < len(recs) - 1 else ""))
    lines += [" ]", "}"]
    dst = ROOT / "game" / "data" / "tuning" / "tuning_env.json"
    dst.write_text("\n".join(lines) + "\n")
    json.loads(dst.read_text())
    print("wrote", dst, len(recs), "keys")


if __name__ == "__main__":
    main()
