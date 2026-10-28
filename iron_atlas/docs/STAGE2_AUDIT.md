# Stage 2 starting-state audit

Inspected 2026-10-28 before edits. Branch `arena/7464ca7a-videos-motion`, clean
working tree, HEAD `7ff6e08` (Stage 1); the preceding commit was `531a7ff`.
Stage 1 was rerun before changes: **4/4 suites passed, 119 checks**
(`59 + 12 + 5 + 43`). The result was reproducible, but not sufficient proof
of all claims in the earlier report.

## Verified discrepancies in the starting code

- `world/world_generator.gd` always made 24 regions; the stated configurable
  200-region path and connected-graph validation did not exist.
- `ai/faction_ai.gd` generated a random treasury proxy and directly created
  troops; it did not pay for recruitment or equipment through player rules.
- Recruits accumulated in a reserve that did not form staffed units or incur
  wages; issued equipment could create combat power without personnel.
- Market previews re-rolled prices; assignment did not reject negative counts
  or check formation ownership. Some inventory items had no effect.
- Tactical Retreat/End called `_finish(true)`, producing a victory; enemy losses
  and territorial consequences did not faithfully follow the tactical result.
- The RNG persisted `rng.seed`, not its stream state. The claimed v1 migration
  and automatic saves were absent; the earlier report overstated both.
- Diplomatic relations and ceasefire status existed, but the reported treaty
  catalogue, espionage layer and full intelligence coverage did not.
- The existing UI tests had tautological assertions. Item lists used
  `set_metadata` rather than `set_item_metadata`, preventing real selection;
  campaign setup had a float/integer `%` parse error. Browser rendering also
  exposed a scene-transition error in `boot.gd`.
- The old suite could report PASS despite engine errors or a nonzero test
  outcome, because it grepped a line and ignored the process/error stream.
- Committed pixels were inspected against the supplied CHAR tank and Rogue
  North images; the in-game tactical scene originally drew colored rectangles
  instead of using the sprite files.

Stage 2 addresses these specific issues, retains and strengthens the existing
Stage 1 test files, and adds independent tests. See `STATUS.md` for remaining
simplifications; passing tests do not imply the entire original grand-strategy
brief or professional art polish is finished.
