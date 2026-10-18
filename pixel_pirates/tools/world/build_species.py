"""Authoring helper for the E1 species SEED (about 66 records). It writes game/data/wildlife/species_<group>.json once;
the JSON files are the source of truth afterwards (edit them directly, or extend this table and re-run to regenerate).

Region codes: K kettle, S shattered, B sunward, G glass, D dead, V verge, F fogbound, M marches, T storm, W white hollow.
value = reales per kg of fresh catch (observe-only creatures: reales paid for a verified sighting report, B4 scale).
    python tools/world/build_species.py
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "game" / "data" / "wildlife"
REG = {"K": "reg_kettle_seas", "S": "reg_shattered_reaches", "B": "reg_sunward_banks", "G": "reg_glass_sea", "D": "reg_dead_ocean",
       "V": "reg_green_verge", "F": "reg_fogbound_expanse", "M": "reg_grey_marches", "T": "reg_storm_belt", "W": "reg_white_hollow"}
TROP = "K.9 S.9 B.7 G.3"


def regs(s: str) -> list[dict]:
    out = []
    for tok in s.split():
        out.append({"region": REG[tok[0]], "abundance": float("0" + tok[1:])})
    return out


# slug, name, scientific, group, habitat, regions, temp, depth, group_size, activity, speed, diet, rarity, methods, lod, value, extra
S = [
 # ---- pelagic fish
 ("yellowfin_tuna", "Yellowfin Tuna", "Thunnus albacares", "pelagic_fish", "open_water", "K.9 S.7 B.8 G.4 D.3", (18, 31), (0, 250), (4, 40), "diurnal", 20, ["small_fish", "squid"], "common", ["line", "net", "observe"], "school", 9, {"season": [0.0, 1.0]}),
 ("skipjack_tuna", "Skipjack Tuna", "Katsuwonus pelamis", "pelagic_fish", "open_water", "K.8 S.8 B.8 G.4 D.3", (15, 30), (0, 260), (20, 200), "diurnal", 18, ["small_fish", "krill"], "common", ["line", "net", "observe"], "school", 6, {}),
 ("mahi_mahi", "Mahi-mahi", "Coryphaena hippurus", "pelagic_fish", "surface", "K.8 S.6 B.7 G.4 D.2", (21, 31), (0, 85), (2, 12), "diurnal", 25, ["small_fish", "flying_fish"], "common", ["line", "observe"], "instance", 8, {"note": "Follows drifting wreckage and floating weed; a school under the bow means flotsam ahead."}),
 ("flying_fish", "Flying Fish", "Cheilopogon melanurus", "pelagic_fish", "surface", "K.9 S.7 B.8 G.5", (22, 31), (0, 30), (10, 60), "diurnal", 30, ["plankton"], "common", ["net", "observe"], "ambient", 3, {"note": "Glides 200 m to escape mahi-mahi. Lands on deck at night: free breakfast."}),
 ("wahoo", "Wahoo", "Acanthocybium solandri", "pelagic_fish", "open_water", "K.6 S.5 B.6", (21, 30), (0, 100), (1, 4), "diurnal", 35, ["small_fish", "squid"], "uncommon", ["line"], "instance", 11, {"danger": 0.1}),
 ("sailfish", "Sailfish", "Istiophorus platypterus", "pelagic_fish", "surface", "K.5 B.5 S.3", (21, 30), (0, 200), (1, 6), "diurnal", 37, ["small_fish", "squid"], "uncommon", ["line", "harpoon", "observe"], "instance", 12, {"danger": 0.15}),
 ("blue_marlin", "Blue Marlin", "Makaira nigricans", "pelagic_fish", "open_water", "K.4 B.4 S.2", (22, 30), (0, 200), (1, 2), "diurnal", 40, ["tuna", "squid"], "rare", ["line", "harpoon", "observe"], "instance", 16, {"danger": 0.3, "note": "A hooked marlin can tow a sloop. Cut the line or fight it for a day."}),
 ("swordfish", "Swordfish", "Xiphias gladius", "pelagic_fish", "open_water", "K.4 B.5 D.3 V.3 F.2 T.2", (5, 27), (0, 800), (1, 1), "nocturnal", 35, ["squid", "small_fish"], "uncommon", ["line", "harpoon", "observe"], "instance", 13, {"danger": 0.25}),
 ("atlantic_bluefin", "Bluefin Tuna", "Thunnus thynnus", "pelagic_fish", "open_water", "V.7 F.6 B.4 M.3 T.3", (6, 24), (0, 500), (3, 30), "diurnal", 40, ["herring", "mackerel"], "uncommon", ["line", "harpoon", "net"], "school", 15, {}),
 ("sunfish", "Ocean Sunfish", "Mola mola", "pelagic_fish", "surface", "B.4 D.4 V.3 F.3 T.2", (10, 26), (0, 600), (1, 1), "always", 2, ["jellyfish"], "uncommon", ["observe", "harpoon"], "instance", 3, {"note": "Lies on its side at the surface. Harmless. Sailors report them as drifting wreckage."}),
 ("sardine", "Sardine", "Sardina pilchardus", "pelagic_fish", "open_water", "B.6 V.6 F.4", (10, 24), (0, 100), (5000, 100000), "diurnal", 5, ["plankton"], "common", ["net", "observe"], "school", 2, {"needs_productivity": 0.4, "note": "The bait ball: birds above, tuna beneath, one net."}),
 ("mackerel", "Atlantic Mackerel", "Scomber scombrus", "pelagic_fish", "open_water", "V.8 F.6 M.5 T.3", (5, 20), (0, 200), (100, 5000), "diurnal", 12, ["krill", "copepods"], "common", ["line", "net"], "school", 4, {"needs_productivity": 0.4}),
 # ---- reef and coastal
 ("barracuda", "Great Barracuda", "Sphyraena barracuda", "reef_fish", "reef", "K.7 S.8 B.5", (22, 31), (0, 100), (1, 3), "diurnal", 25, ["small_fish"], "common", ["line", "observe"], "instance", 6, {"danger": 0.3}),
 ("goliath_grouper", "Goliath Grouper", "Epinephelus itajara", "reef_fish", "reef", "K.5 S.7", (22, 31), (5, 50), (1, 2), "diurnal", 4, ["crab", "fish"], "uncommon", ["line", "harpoon", "dive"], "instance", 10, {"note": "300 kg of fish for a wise crew; hard to hook, harder to land."}),
 ("red_snapper", "Red Snapper", "Lutjanus campechanus", "reef_fish", "reef", "K.8 S.9 B.5", (18, 30), (10, 120), (5, 40), "crepuscular", 8, ["small_fish", "shrimp"], "common", ["line", "trap"], "school", 10, {}),
 ("parrotfish", "Blue Parrotfish", "Scarus coeruleus", "reef_fish", "reef", "K.8 S.9", (24, 31), (1, 30), (4, 20), "diurnal", 5, ["algae"], "common", ["trap", "dive", "observe"], "school", 5, {"note": "The grinding sound at a reef at night is parrotfish; the sand beneath it is their work."}),
 ("sargassum_fish", "Weedfish", "Histrio histrio", "reef_fish", "surface", "G.8 K.3 D.3 S.2", (18, 31), (0, 20), (1, 12), "always", 1, ["small_crab", "shrimp"], "common", ["net", "observe"], "ambient", 4, {"note": "Lives inside floating weed rafts, coloured exactly like the weed. A raft on the Glass Sea is a whole village; scoop it up and look."}),
 ("moray_eel", "Green Moray", "Gymnothorax funebris", "reef_fish", "reef", "K.6 S.8", (22, 30), (1, 40), (1, 1), "nocturnal", 3, ["fish", "octopus"], "common", ["trap", "dive"], "ambient", 7, {"danger": 0.35}),
 ("porcupinefish", "Porcupinefish", "Diodon hystrix", "reef_fish", "reef", "K.6 S.7 B.4", (22, 30), (2, 50), (1, 2), "nocturnal", 2, ["crab", "urchin"], "common", ["trap", "dive"], "ambient", 1, {"note": "Poisonous to eat. The cook will tell you; the new hand will not listen."}),
 ("spiny_lobster", "Spiny Lobster", "Panulirus argus", "crustacean", "reef", "K.7 S.9 B.4", (20, 30), (1, 90), (1, 30), "nocturnal", 1, ["snail", "clam"], "common", ["trap", "dive"], "ambient", 20, {"note": "Best-value food in the game: nearly 20 reales a kilo, no preservation needed if eaten the same day."}),
 ("mud_crab", "Mud Crab", "Scylla serrata", "crustacean", "coastal", "S.9 B.5 K.4", (22, 32), (0, 30), (1, 10), "nocturnal", 1, ["mussel", "carrion"], "common", ["trap"], "ambient", 9, {}),
 ("sea_cucumber", "Sea Cucumber", "Holothuria scabra", "invertebrate", "coastal", "S.7 K.5 B.3", (22, 32), (0, 40), (5, 200), "always", 0, ["detritus"], "uncommon", ["dredge", "dive"], "ambient", 14, {"note": "Dried, it keeps for years and trades in every port."}),
 ("oystercatcher", "Oystercatcher", "Haematopus ostralegus", "seabird", "coastal", "S.8 V.7 F.3", (3, 28), (0, 0), (3, 40), "always", 20, ["shellfish"], "common", ["observe"], "ambient", 0, {"note": "Feeds along tidelines: a flock on a bare reef means the reef is a tide-flat at low water."}),
 # ---- sharks and rays
 ("tiger_shark", "Tiger Shark", "Galeocerdo cuvier", "shark_ray", "open_water", "K.7 S.6 B.6 G.1", (20, 30), (0, 350), (1, 1), "nocturnal", 18, ["turtle", "fish", "carrion"], "uncommon", ["observe", "harpoon"], "instance", 6, {"danger": 0.7}),
 ("hammerhead", "Great Hammerhead", "Sphyrna mokarran", "shark_ray", "open_water", "K.5 S.6 B.4", (22, 30), (1, 300), (1, 3), "crepuscular", 15, ["ray", "fish"], "uncommon", ["observe", "harpoon"], "instance", 6, {"danger": 0.6}),
 ("caribbean_reef_shark", "Reef Shark", "Carcharhinus perezi", "shark_ray", "reef", "K.7 S.9", (22, 31), (1, 60), (1, 8), "always", 14, ["fish"], "common", ["observe", "line"], "instance", 5, {"danger": 0.35}),
 ("whale_shark", "Whale Shark", "Rhincodon typus", "shark_ray", "surface", "K.3 B.5 G.3", (21, 30), (0, 700), (1, 1), "diurnal", 3, ["plankton"], "rare", ["observe", "report"], "instance", 400, {"needs_productivity": 0.6, "sensitivity": 0.3, "note": "Follows the Sunward bloom. Harmless. A sighting report pays; harming one costs the crew's goodwill in every port."}),
 ("manta_ray", "Giant Manta", "Mobula birostris", "shark_ray", "open_water", "K.5 S.5 B.6", (21, 30), (0, 120), (1, 5), "diurnal", 9, ["plankton"], "uncommon", ["observe"], "instance", 120, {"needs_productivity": 0.5}),
 ("great_white", "Great White Shark", "Carcharodon carcharias", "shark_ray", "open_water", "V.4 F.3 T.4 D.2", (8, 22), (0, 1000), (1, 1), "diurnal", 22, ["seal", "tuna"], "rare", ["observe", "harpoon"], "instance", 7, {"danger": 0.9}),
 ("basking_shark", "Basking Shark", "Cetorhinus maximus", "shark_ray", "surface", "V.6 F.5 M.4", (6, 18), (0, 900), (1, 12), "diurnal", 3, ["copepods"], "uncommon", ["observe", "harpoon"], "instance", 5, {"needs_productivity": 0.7, "note": "Looks like a fin the length of a longboat. Takes no notice of ships."}),
 ("greenland_shark", "Greenland Shark", "Somniosus microcephalus", "shark_ray", "deep", "M.6 W.3 F.2", (-1, 8), (200, 2000), (1, 1), "always", 1, ["fish", "carrion"], "rare", ["observe", "line"], "instance", 4, {"danger": 0.1, "note": "Slowest shark; its flesh is poisonous raw. Lives for centuries."}),
 # ---- turtles, snakes
 ("green_turtle", "Green Turtle", "Chelonia mydas", "reptile", "coastal", "K.7 S.8 B.4", (22, 31), (0, 80), (1, 6), "diurnal", 4, ["seagrass"], "common", ["observe", "harpoon", "dive"], "instance", 8, {"note": "Keeps alive in the hold for weeks: the sailor's fresh meat. Catching too many lowers the next visit's catch."}),
 ("hawksbill_turtle", "Hawksbill Turtle", "Eretmochelys imbricata", "reptile", "reef", "K.5 S.8", (22, 31), (0, 70), (1, 2), "diurnal", 4, ["sponge"], "uncommon", ["observe", "dive"], "instance", 10, {"sensitivity": 0.5}),
 ("leatherback_turtle", "Leatherback", "Dermochelys coriacea", "reptile", "open_water", "K.4 B.5 V.3 F.3", (4, 30), (0, 1200), (1, 1), "always", 5, ["jellyfish"], "rare", ["observe"], "instance", 90, {"sensitivity": 0.6}),
 ("yellow_bellied_sea_snake", "Pelagic Sea Snake", "Hydrophis platurus", "reptile", "surface", "K.6 S.4 B.5 G.4", (20, 31), (0, 50), (5, 5000), "always", 2, ["small_fish"], "uncommon", ["observe"], "ambient", 0, {"danger": 0.5, "note": "Drifting slicks of thousands on the Glass Sea. Do not bring one aboard in a net."}),
 # ---- cetaceans
 ("bottlenose_dolphin", "Bottlenose Dolphin", "Tursiops truncatus", "cetacean", "coastal", "K.9 S.8 B.6 V.4 F.3", (8, 30), (0, 300), (4, 30), "diurnal", 20, ["fish", "squid"], "common", ["observe"], "instance", 0, {"sensitivity": 0.5, "note": "Rides the bow wave. Crews log it; the morale lift is real."}),
 ("spinner_dolphin", "Spinner Dolphin", "Stenella longirostris", "cetacean", "open_water", "K.7 B.8 G.4", (22, 31), (0, 300), (20, 200), "nocturnal", 18, ["small_fish", "squid"], "uncommon", ["observe"], "school", 0, {"sensitivity": 0.4}),
 ("humpback_whale", "Humpback Whale", "Megaptera novaeangliae", "cetacean", "open_water", "B.7 K.4 V.5 F.3 T.4 M.3", (2, 28), (0, 400), (1, 6), "always", 9, ["krill", "herring"], "uncommon", ["observe", "harpoon", "report"], "instance", 150, {"season": [0.0, 0.6], "sensitivity": 0.8, "needs_productivity": 0.5, "note": "Breaches in the Sunward bloom. Its song carries through the hull; the hull-watch hears it before the lookout sees it."}),
 ("blue_whale", "Blue Whale", "Balaenoptera musculus", "cetacean", "open_water", "T.4 M.3 V.2 B.2", (2, 24), (0, 500), (1, 2), "always", 12, ["krill"], "rare", ["observe", "report"], "instance", 300, {"sensitivity": 0.9, "needs_productivity": 0.7, "note": "The largest living thing. A sloop is a third of its length."}),
 ("fin_whale", "Fin Whale", "Balaenoptera physalus", "cetacean", "open_water", "T.5 M.4 V.4 F.3 W.2", (0, 22), (0, 500), (1, 4), "always", 20, ["krill", "herring"], "uncommon", ["observe", "report", "harpoon"], "instance", 120, {"sensitivity": 0.7}),
 ("sperm_whale", "Sperm Whale", "Physeter macrocephalus", "cetacean", "deep", "K.3 B.3 D.4 V.3 T.3", (4, 28), (200, 3000), (1, 12), "always", 8, ["squid"], "rare", ["observe", "harpoon", "report"], "instance", 220, {"danger": 0.6, "sensitivity": 0.8, "note": "Dives an hour, surfaces breathing for ten minutes. A ramming whale is a famous way for a ship to end."}),
 ("orca", "Orca", "Orcinus orca", "cetacean", "open_water", "M.5 T.4 W.4 F.4 V.4", (-1, 20), (0, 500), (3, 12), "always", 27, ["seal", "fish", "whale"], "uncommon", ["observe"], "instance", 0, {"danger": 0.2, "sensitivity": 0.9, "note": "Never attacks ships in this world; will clear a seal colony from a rock in 4 minutes if you watch."}),
 ("narwhal", "Narwhal", "Monodon monoceros", "cetacean", "ice_edge", "M.7", (-2, 6), (0, 1500), (3, 20), "always", 8, ["cod", "squid"], "rare", ["observe", "report"], "instance", 250, {"sensitivity": 0.8, "note": "The 'unicorn of the sea' of old charts."}),
 ("beluga", "Beluga", "Delphinapterus leucas", "cetacean", "ice_edge", "M.7 F.2", (-2, 8), (0, 600), (5, 40), "always", 8, ["cod", "capelin"], "uncommon", ["observe"], "school", 0, {"sensitivity": 0.7, "note": "Chatters through the hull. Crews call them canaries of the ice."}),
 ("bowhead_whale", "Bowhead Whale", "Balaena mysticetus", "cetacean", "ice_edge", "M.5 W.1", (-2, 6), (0, 300), (1, 4), "always", 6, ["copepods", "krill"], "rare", ["observe", "report", "harpoon"], "instance", 200, {"sensitivity": 0.9, "note": "Breaks 20 cm of ice with its back."}),
 ("southern_right_whale", "Southern Right Whale", "Eubalaena australis", "cetacean", "coastal", "T.6 W.2 D.2", (1, 18), (0, 200), (1, 6), "always", 5, ["copepods", "krill"], "uncommon", ["observe", "report"], "instance", 150, {"season": [0.4, 1.0], "sensitivity": 0.9}),
 # ---- pinnipeds
 ("harbour_seal", "Harbour Seal", "Phoca vitulina", "pinniped", "coastal", "V.8 F.4 M.4", (2, 18), (0, 200), (1, 30), "diurnal", 12, ["fish"], "common", ["observe", "harpoon"], "ambient", 5, {}),
 ("walrus", "Walrus", "Odobenus rosmarus", "pinniped", "ice_edge", "M.7", (-2, 8), (0, 90), (5, 200), "always", 5, ["clam"], "uncommon", ["observe", "harpoon"], "instance", 12, {"danger": 0.5, "note": "Colonies on floes stink for 4 km downwind. Useful as a smell-compass in fog."}),
 ("leopard_seal", "Leopard Seal", "Hydrurga leptonyx", "pinniped", "ice_edge", "W.7 T.2", (-2, 5), (0, 300), (1, 2), "always", 18, ["penguin", "krill"], "uncommon", ["observe"], "instance", 3, {"danger": 0.6}),
 ("elephant_seal", "Elephant Seal", "Mirounga leonina", "pinniped", "coastal", "T.5 W.5", (-1, 10), (0, 1500), (1, 40), "always", 9, ["squid", "fish"], "uncommon", ["observe", "harpoon"], "instance", 8, {"danger": 0.3}),
 ("sea_otter", "Sea Otter", "Enhydra lutris", "pinniped", "kelp", "V.7", (4, 16), (0, 40), (1, 12), "diurnal", 4, ["urchin", "crab"], "uncommon", ["observe"], "ambient", 0, {"sensitivity": 0.9, "note": "Holds paws while asleep, tied into the kelp. Hunting them is the one act on any island that the Verge towns will never forgive."}),
 # ---- cold and deep fish
 ("atlantic_cod", "Atlantic Cod", "Gadus morhua", "cold_fish", "coastal", "V.8 F.7 M.7", (0, 14), (10, 600), (10, 400), "always", 5, ["herring", "crab"], "common", ["line", "net", "trap"], "school", 4, {"needs_productivity": 0.4, "note": "Salt-cod: the best long-keeping fish. 1 kg dried holds 3x the days of fresh."}),
 ("atlantic_herring", "Atlantic Herring", "Clupea harengus", "cold_fish", "open_water", "V.7 F.7 M.7 T.3", (2, 16), (0, 200), (10000, 100000), "diurnal", 5, ["copepods"], "common", ["net", "observe"], "school", 2, {"needs_productivity": 0.5}),
 ("haddock", "Haddock", "Melanogrammus aeglefinus", "cold_fish", "coastal", "V.6 F.5 M.4", (1, 12), (30, 300), (5, 100), "always", 5, ["worm", "crab"], "common", ["line", "net"], "school", 5, {}),
 ("halibut", "Atlantic Halibut", "Hippoglossus hippoglossus", "cold_fish", "deep", "V.4 M.5 F.3", (0, 10), (50, 1500), (1, 1), "always", 4, ["cod", "crab"], "uncommon", ["line"], "ambient", 9, {"note": "A single fish can feed a watch for three days."}),
 ("atlantic_salmon", "Atlantic Salmon", "Salmo salar", "cold_fish", "coastal", "V.6 F.2", (2, 16), (0, 200), (3, 40), "diurnal", 12, ["small_fish", "shrimp"], "uncommon", ["net", "line"], "school", 8, {"season": [0.3, 0.7]}),
 ("capelin", "Capelin", "Mallotus villosus", "cold_fish", "ice_edge", "M.8 W.3 F.2", (-1, 8), (0, 300), (1000, 50000), "diurnal", 4, ["copepods"], "common", ["net", "observe"], "school", 1, {"needs_productivity": 0.5}),
 ("antarctic_toothfish", "Antarctic Toothfish", "Dissostichus mawsoni", "cold_fish", "deep", "W.7", (-2, 3), (100, 2000), (1, 20), "always", 3, ["fish", "squid"], "uncommon", ["line"], "ambient", 12, {"note": "Has its own antifreeze. Cooks to a buttery white fish."}),
 # ---- cephalopods, invertebrates
 ("common_octopus", "Common Octopus", "Octopus vulgaris", "cephalopod", "reef", "K.6 S.7 V.4", (8, 28), (1, 200), (1, 1), "nocturnal", 3, ["crab", "clam"], "common", ["trap", "dive"], "ambient", 10, {}),
 ("giant_squid", "Giant Squid", "Architeuthis dux", "cephalopod", "deep", "D.3 T.3 V.2 F.2", (3, 14), (300, 1500), (1, 1), "always", 8, ["fish", "squid"], "legendary", ["observe", "report"], "bespoke", 800, {"sensitivity": 0.5, "danger": 0.5, "note": "Washes up dead in the Verge; never seen alive. A carcass sighting is a report worth 800 reales."}),
 ("humboldt_squid", "Jumbo Flying Squid", "Dosidicus gigas", "cephalopod", "open_water", "K.3 B.4 D.4", (10, 26), (0, 700), (50, 1000), "nocturnal", 12, ["small_fish"], "uncommon", ["line", "net", "observe"], "school", 5, {"danger": 0.45, "note": "Red, fast, and aggressive. Jig them at night; keep hands off the hook."}),
 ("chambered_nautilus", "Chambered Nautilus", "Nautilus pompilius", "cephalopod", "deep", "S.3 K.2 G.1", (10, 25), (100, 700), (1, 6), "nocturnal", 1, ["crab"], "rare", ["trap", "observe"], "ambient", 180, {"note": "Shell trades as a curio. Slow to breed; trapping wipes a reef."}),
 ("portuguese_man_o_war", "Man-o'-war", "Physalia physalis", "cnidarian", "surface", "K.6 S.4 B.5 G.5 D.3", (18, 31), (0, 1), (1, 800), "always", 1, ["small_fish"], "common", ["observe"], "ambient", 0, {"danger": 0.6, "note": "Blue floats down the wind in fleets. Spot them and keep the swimmers aboard."}),
 ("moon_jelly", "Moon Jelly", "Aurelia aurita", "cnidarian", "surface", "V.7 F.6 M.5 B.3", (3, 25), (0, 100), (5, 5000), "always", 1, ["plankton"], "common", ["observe"], "ambient", 0, {}),
 ("blue_mussel", "Blue Mussel", "Mytilus edulis", "invertebrate", "coastal", "V.9 F.4 M.4 T.2", (-1, 20), (0, 30), (20, 2000), "always", 0, ["plankton"], "common", ["dredge", "dive"], "ambient", 3, {"note": "Never gather from red tide water; the surgeon's book lists it."}),
 ("king_crab", "King Crab", "Paralithodes camtschaticus", "crustacean", "deep", "M.5 V.3 W.2", (0, 8), (10, 400), (1, 40), "always", 1, ["urchin", "clam"], "uncommon", ["trap"], "ambient", 22, {}),
 # ---- plankton
 ("krill", "Krill", "Euphausia superba", "plankton", "open_water", "T.9 W.8 M.5 V.4", (-2, 10), (0, 300), (100000, 100000), "always", 1, ["algae"], "common", ["observe"], "ambient", 0, {"needs_productivity": 0.8, "note": "Pink water at dawn: the whales are coming."}),
 ("copepod", "Copepod", "Calanus finmarchicus", "plankton", "open_water", "V.9 F.8 M.8 T.6", (0, 14), (0, 200), (100000, 100000), "always", 1, ["algae"], "common", ["observe"], "ambient", 0, {"needs_productivity": 0.7}),
 ("noctiluca", "Sea Sparkle", "Noctiluca scintillans", "plankton", "surface", "B.8 K.5 S.5 V.3", (10, 28), (0, 10), (100000, 100000), "nocturnal", 0, ["algae"], "common", ["observe"], "ambient", 0, {"needs_productivity": 0.6, "note": "Glowing wake at night. Also reveals the ship to anyone watching; lights-out routines matter near hostile coasts."}),
 # ---- seabirds
 ("magnificent_frigatebird", "Frigatebird", "Fregata magnificens", "seabird", "surface", "K.9 S.8 B.8 G.5 D.2", (22, 31), (0, 0), (1, 20), "diurnal", 25, ["flying_fish", "squid"], "common", ["observe"], "instance", 0, {"note": "Never lands on water. A frigatebird at sunset means land is within 150 km."}),
 ("brown_booby", "Brown Booby", "Sula leucogaster", "seabird", "coastal", "K.8 S.8 B.7", (22, 31), (0, 0), (1, 30), "diurnal", 20, ["flying_fish", "squid"], "common", ["observe"], "instance", 0, {"note": "Plunge-dives; roosts on land at night: seen at dusk, land is within 80 km."}),
 ("red_billed_tropicbird", "Tropicbird", "Phaethon aethereus", "seabird", "open_water", "K.7 B.8 D.3 G.4", (20, 31), (0, 0), (1, 4), "diurnal", 25, ["flying_fish", "squid"], "uncommon", ["observe"], "instance", 0, {"note": "Ranges over 400 km from land; a rare messenger of open water."}),
 ("northern_gannet", "Northern Gannet", "Morus bassanus", "seabird", "open_water", "V.7 F.6 M.4", (4, 20), (0, 0), (5, 200), "diurnal", 30, ["herring", "mackerel"], "common", ["observe"], "school", 0, {"note": "Plunging gannets mark the bait ball. The white column from 40 m is visible 8 km away."}),
 ("wandering_albatross", "Wandering Albatross", "Diomedea exulans", "seabird", "open_water", "T.9 D.3 W.4 V.2", (-1, 20), (0, 0), (1, 3), "diurnal", 40, ["squid", "carrion"], "uncommon", ["observe"], "instance", 0, {"note": "Rides the westerlies for 1,000 km without a wingbeat. Follows ships for days: a companion on empty water."}),
 ("european_storm_petrel", "Storm Petrel", "Hydrobates pelagicus", "seabird", "open_water", "V.5 F.5 T.7 M.5", (3, 20), (0, 0), (1, 60), "crepuscular", 20, ["plankton", "small_fish"], "common", ["observe"], "ambient", 0, {"note": "Gathers in the lee of the ship before a gale. Sailors have called them 'storm chickens' for centuries; they are an early warning, not an omen."}),
 ("arctic_tern", "Arctic Tern", "Sterna paradisaea", "seabird", "open_water", "M.8 F.5 V.4 W.5 T.4 D.2 K.1", (-2, 25), (0, 0), (5, 200), "diurnal", 22, ["small_fish", "krill"], "common", ["observe"], "ambient", 0, {"season": [0.0, 1.0], "note": "Migrates pole to pole every year, so its position in a given month is a hint about where you are on the compass."}),
 ("great_skua", "Great Skua", "Stercorarius skua", "seabird", "open_water", "M.6 V.4 F.4 T.4", (0, 14), (0, 0), (1, 6), "diurnal", 28, ["fish", "carrion", "seabird"], "uncommon", ["observe"], "instance", 0, {"danger": 0.1, "note": "Robs gulls of catches. A crew that leaves fish drying on the rail will notice."}),
 ("black_legged_kittiwake", "Kittiwake", "Rissa tridactyla", "seabird", "open_water", "M.7 F.5 V.5 T.3", (-1, 16), (0, 0), (5, 300), "diurnal", 22, ["capelin", "krill"], "common", ["observe"], "ambient", 0, {}),
 ("atlantic_puffin", "Puffin", "Fratercula arctica", "seabird", "coastal", "M.5 V.6 F.3", (0, 14), (0, 60), (2, 60), "diurnal", 20, ["capelin", "herring"], "uncommon", ["observe"], "ambient", 0, {"season": [0.1, 0.6]}),
 ("emperor_penguin", "Emperor Penguin", "Aptenodytes forsteri", "seabird", "ice_edge", "W.7", (-2, 4), (0, 500), (5, 400), "always", 5, ["fish", "krill", "squid"], "uncommon", ["observe"], "school", 0, {"sensitivity": 0.7, "note": "The only real birds of the White Hollow. A colony on a floe is a landmark you can sail toward."}),
 # ---- strange (fictional; all follow the content rules: lore and nature only)
 ("looking_glass_ray", "Looking-glass Ray", None, "strange", "surface", "G.9", (26, 32), (0, 20), (1, 6), "diurnal", 2, ["plankton"], "uncommon", ["observe", "net"], "instance", 60, {"real": False, "note": "A flat silver ray that holds still enough to double the sky. Seen only on the Glass Sea: the surface above one looks like a second sea overhead, and a net hauled over one finds nothing."}),
 ("ghost_lantern", "Ghost Lantern", None, "strange", "open_water", "D.8 G.2", (14, 26), (0, 200), (1, 400), "nocturnal", 1, ["plankton"], "uncommon", ["observe", "net"], "school", 40, {"real": False, "note": "A colony-jelly that pulses once an hour, in step with every other lantern in the ocean. Dead Ocean navigators time their watch-bells by it. Dried, it burns without smoke."}),
 ("stormglass_medusa", "Stormglass Medusa", None, "strange", "surface", "K.8 B.5 S.4", (24, 31), (0, 5), (1, 40), "always", 1, ["plankton"], "uncommon", ["observe", "net"], "ambient", 25, {"real": False, "note": "Rises to the surface 6 game hours (about 4 real minutes) before a squall. Carried in a jar, its colour is the cheapest barometer on a ship."}),
 ("bellsinger", "Bellsinger", None, "strange", "open_water", "F.7 M.2", (2, 14), (0, 500), (1, 3), "always", 7, ["krill", "herring"], "rare", ["observe", "report"], "bespoke", 350, {"real": False, "sensitivity": 0.9, "note": "A grey whale whose call carries three kilometres through fog. Fog pilots navigate by hearing it, and a pod answering the ship's bell is the sign of open water ahead."}),
 ("hollow_whale", "The Hollow Whale", None, "strange", "ice_edge", "W.3", (-2, 3), (0, 800), (1, 1), "always", 6, ["krill"], "legendary", ["observe", "report"], "bespoke", 3000, {"real": False, "sensitivity": 1.0, "note": "One white whale, older than the maps. It leads a ship through ice leads if the ship does not hunt. Appears at most once per voyage."}),
 ("trench_angler", "Trench Angler", None, "strange", "vent", "T.5", (1, 5), (1500, 6000), (1, 1), "always", 2, ["fish"], "rare", ["observe", "dredge"], "bespoke", 150, {"real": False, "danger": 0.4, "note": "Rises on the Storm Belt trench in gales, its lure visible on the troughs like a lamp. Three crews have steered to it; none returned the second time."}),
 ("grandfather_squid", "Grandfather Squid", None, "strange", "deep", "D.2 T.2", (3, 12), (400, 2500), (1, 1), "nocturnal", 12, ["whale", "fish"], "legendary", ["observe", "report"], "bespoke", 2500, {"real": False, "danger": 0.9, "sensitivity": 1.0, "note": "The oldest sailor's tale: arms the length of a mast. It does not hunt ships; it hunts whales, and a ship near the fight may lose a day or more to the churn."}),
]


def rec(s: tuple) -> dict:
    slug, name, sci, grp, hab, rg, temp, depth, gs, act, spd, diet, rar, meth, lod, val, ex = s
    r: dict = {"id": "spc_" + slug, "name": name}
    real = ex.get("real", True)
    if sci:
        r["scientific"] = sci
    r["real"] = real
    r.update({"group": grp, "habitat": hab, "regions": regs(rg), "temp_c": list(temp), "depth_m": list(depth), "group_size": list(gs),
              "activity": act, "speed_kn": spd, "diet": diet, "rarity": rar, "methods": meth, "lod": lod, "value": val})
    for k in ("season", "needs_productivity", "danger", "sensitivity", "note"):
        if k in ex:
            r[k] = ex[k]
    r.update({"provisional": True, "owner": "E1", "source": "E1 wildlife seed; real species from standard natural history, numbers provisional"})
    return r


def main() -> None:
    by: dict[str, list] = {}
    for s in S:
        by.setdefault(s[3], []).append(rec(s))
    groups = {"fish": ["pelagic_fish", "reef_fish", "cold_fish", "deep_fish"], "sharks_rays": ["shark_ray"], "marine_mammals": ["cetacean", "pinniped"],
              "reptiles": ["reptile"], "invertebrates": ["cephalopod", "crustacean", "cnidarian", "invertebrate", "plankton"], "seabirds": ["seabird"], "strange": ["strange"]}
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    for fname, gl in groups.items():
        recs = [r for g in gl for r in by.get(g, [])]
        total += len(recs)
        (OUT / f"species_{fname}.json").write_text(json.dumps({"schema": 1, "kind": "species", "records": recs}, indent=1, ensure_ascii=False) + "\n")
        print(fname, len(recs))
    print("total", total)


if __name__ == "__main__":
    main()
