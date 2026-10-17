PIXEL PIRATES - A1 PROBE (revision R1)

STEP 1 - headless self-test (no GPU needed, runs even on very old PCs)
  Godot_v4.7.2-stable_win64_console.exe --headless --path <this folder> --script res://selftest.gd
  Expected last line:  SELFTEST PASS

STEP 2 - visual probe (needs OpenGL 3.3, or Direct3D 11 for the ANGLE fallback)
  Godot_v4.7.2-stable_win64.exe --path <this folder>
  (or open the folder in the Godot editor and press F5)
  Let it run ~10 s in each quality (key 1 = Dev-Lite, key 2 = Standard), press R, and send me
  the text of user://probe_result.txt (the console prints its path), or a screenshot.
  If a window never opens or Godot shows a graphics error, send me that error text: it is useful data.

Diagnostic switches (command line, after the exe):
  --rendering-driver opengl3_angle     force OpenGL ES 3.0 over Direct3D 11 (ANGLE)
  --rendering-driver opengl3           force native OpenGL 3.3
