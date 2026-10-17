#!/bin/sh
# Optional: run the project checker before every commit that touches pixel_pirates/ (needs Python on PATH).
# Uses a local hook file; does not change global git config.
ROOT="$(git rev-parse --show-toplevel)"
cp "$ROOT/pixel_pirates/tools/hooks/pre-commit" "$ROOT/.git/hooks/pre-commit"
chmod +x "$ROOT/.git/hooks/pre-commit"
echo "pre-commit hook installed."
