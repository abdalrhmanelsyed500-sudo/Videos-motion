# EGYPTIAN TUKTUK MAYHEM — Game Design Document (Phase 0)

Status: **Verified** as the working design baseline for Phase 1. Living document; every phase updates it.
Engine target: Godot **4.7.2**, Compatibility renderer. Platforms: Windows desktop first; web template used only as the
headless test/render harness in this sandbox (see TDD §6).

## 1. Concept

Arcade passenger-delivery driving game with an original contemporary Egyptian identity. The player drives a tuk-tuk
through dense, lively districts, picks up passengers, and delivers them before the timer dies. Fun comes from
momentum, risk, shortcuts and chaos — not from simulation. Tone: fast, warm, humorous, respectful.

Reference philosophy (Crazy Taxi, analysed in ART_BIBLE §2): continuous forward momentum, time pressure, one dominant
destination cue, rewards for skilled aggression, readable chase camera, instant feedback. **No protected asset, map,
model, logo, audio or code from Crazy Taxi or any other game is copied**; only abstract design principles are used.

## 2. Core loop (Phase 1 acceptance)

1. Player sees a waiting passenger marker (raised hand icon + name plate).
2. Drive into the pickup ring → offer card appears (passenger, destination, distance, base fare) → accept (E / pad A).
3. Passenger boards (animation), timer starts, destination arrow + distance + minimap cue activate.
4. Drive to the destination ring; stopping inside it with low speed = delivery.
5. Reward computed from data tuning (distance, time left, skill flags, collision penalties) → balance += reward,
   exactly once (unit-tested).
6. Result card (fare breakdown, time, tips) → next passenger spawns → loop repeats.
Failure: timer reaches 0 → passenger exits angry, small reputation cost, loop continues. No dead-ends: a new offer is
always available within the district.

## 3. Missions

Phase 1 ships ONE mission type (standard delivery) end-to-end. Designed types for later phases (data-driven, generated
by region/distance/progress): urgent, crowded-pickup, long-haul, narrow-alley, market, village, factory, station,
coastal, multi-stop, streak challenges. Mission generation reads `data/districts/*.json` (points, tags) and
`data/missions/reward_tuning.json`; no mission constants in code.

## 4. Rewards & economy

Reward = base_fare + per_m * metres + time_left_bonus(rate * seconds left) + skill bonuses (shortcut flag, clean-drive
flag) − collision penalties (clamped ≥ 0). All coefficients live in `data/missions/reward_tuning.json`. Currency:
Egyptian pounds, displayed "E£" (EN) / "ج.م" (AR). Reputation 0..100 gates district unlocks and fare multipliers
(Phase 5+). Persistent save via `user://save.json`, versioned from day one (SAVE_VERSION), upgraders mandatory.

## 5. World plan (honest staging)

Phase 1: **one** test district ("Mit Okba trial block", ~200×200 m: ring road + market street + alley shortcut).
Later phases add regions per master brief: Greater Cairo districts, Alexandria coast, tourist coastal city,
countryside, industrial, informal neighbourhoods, intercity roads — each playable before the next starts.
Region streaming: per-region PackedScene + load/unload manager (Phase 5); no false "open world" claims before then.

## 6. Characters

Diverse Egyptian passengers/pedestrians: varied builds, skin tones, men's hairstyles, clothing by role (students,
workers, shopkeepers, farmers, tourists...). **Mandatory rule: every female character wears a hijab fully covering her
hair plus respectful loose clothing** — enforced in the Art Bible, in generator constraints (geometry-level: hair mesh
replaced by hijab mesh), and in the asset review checklist; text prompts alone are not accepted as enforcement.
Phase 1 ships 4 authored characters (2 men, 2 women in hijab) with Idle/Walk/Board/Exit as scripted pose tweens
(labelled TEMP) replaced by AnimationPlayer clips in Phase 3.

## 7. Vehicles

Hero asset: the Egyptian tuk-tuk (three wheels, canopy roof, front cowl, rear cabin bench). Variants later: traditional,
modern, worn, performance, decorated, rural, mission-special — geometric variants, not recolours. Arcade handling:
CharacterBody3D with tuned accel/brake/steer/slip curves from `data/vehicles/*.json`; controlled drift above a speed
threshold; impact speed loss + recovery; flip protection (upright torque, documented as arcade convention).

## 8. Traffic & pedestrians (Phase 5 system, Phase 1 = parked props only)

Pooled vehicles with lane graphs per district, distance-tiered update rates (near: every frame, mid: 10 Hz, far:
paused), behaviours: stop/slow/lane-change/turn/merge + rare fair surprises. Pedestrians on sidewalk splines with
crossing gaps; market crowds as low-cost billboard tiers on low-end profile.

## 9. Camera & HUD

Chase camera: spring-arm behind/above, FOV widens with speed, damped yaw, collision-aware arm shortening, adjustable
distance/height/sensitivity in settings. HUD (ART_BIBLE §4): big stylised timer, fare LED panel, balance, speed,
world-space green destination arrow + on-screen edge arrow + distance, minimap inset (Phase 4), contextual toasts,
result card, pause/settings/vehicle/region menus. Arabic+English with correct RTL alignment (Phase 8 localization
pass; string table structure exists from Phase 1).

## 10. Audio

Original only. Engine loop pitched by RPM, horn, brakes, impacts, district ambiences, mission stings, original
arcade score with Egyptian maqam-flavoured motifs (composed/generated original material, licensed or self-made).
Separate music/SFX volumes. Nothing from Crazy Taxi or any commercial recording.

## 11. Progression

Balance, reputation, district unlocks, vehicle purchase/upgrades (speed/accel/brake/handling/cosmetics) — all tables in
`data/upgrades/*.json` (Phase 5+). Upgrades must keep missions non-trivial: tuning review per addition.

## 12. Content rules (house rules, binding)

- No sexual content; no female crew/character sexualisation; respectful representation of Egyptian society.
- Religion portrayed neutrally: real-world respect, no gameplay mockery, no sectarian content.
- Informal settlements designed with dignity: rich, clever level design — never caricature.
- No copyrighted assets of any third party; AI-generated material inspected and documented per ART_BIBLE §6.
