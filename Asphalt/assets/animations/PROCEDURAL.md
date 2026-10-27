# Procedural animation

Animations are intentionally procedural and compatible with the generated rigs:

- `bike_view.gd`: wheel rotation, steering-head yaw, lean roll, suspension bob, crash slide.
- `rider_view.gd`: riding lean, head look, arm steering, leg/brake posture, non-graphic fall.
- `vehicle_view.gd`: traffic wheel rotation and alternating police beacons.
- `camera_rig.gd`: cockpit/chase damping, restrained speed FOV, shake and crash replay orbit.
- `motorcycle_controller.gd`: wobble after minor impacts, one-shot severe crash sequence.

These are deterministic per-frame transforms rather than imported skeletal clips, so no external
animation license is required and every motion remains tied to live gameplay state.
