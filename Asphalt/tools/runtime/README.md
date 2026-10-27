# Optional screenshot runtime staging

This directory is used only during development/CI to stage a portable Godot editor,
Xvfb, Mesa llvmpipe and XKB data for headless screenshot capture inside the sandbox.
Those archives are build/test tooling, not game assets, and are intentionally excluded
from the final project ZIP and Git history state.

On a normal desktop, install Godot 4.2.2 and use a GPU-capable X11/Wayland display.
`tools/capture_benchmark.sh` and `tools/setup_graphics_runtime.sh` document the
software-rendering workflow used for this project's verified screenshots.
