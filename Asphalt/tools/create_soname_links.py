#!/usr/bin/env python3
"""Create SONAME symlinks for a portable shared-library bundle.

CI copies the real versioned library files (e.g. libXcursor.so.1.0.2), but
dynamic loaders often request the shorter SONAME (libXcursor.so.1). This
script uses readelf when available and falls back to version-prefix matching.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


def soname(path: Path) -> str | None:
    try:
        result = subprocess.run(["readelf", "-d", str(path)], capture_output=True, text=True, timeout=10)
        match = re.search(r"\(SONAME\)\s+Library soname:\s+\[([^\]]+)\]", result.stdout)
        if match:
            return match.group(1)
    except (OSError, subprocess.SubprocessError):
        pass
    # Fallback: libFoo.so.1.2.3 -> libFoo.so.1
    match = re.match(r"^(.+\.so\.\d+)", path.name)
    return match.group(1) if match else None


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: create_soname_links.py <package-dir>", file=sys.stderr)
        return 2
    package = Path(sys.argv[1]).resolve()
    directories = [package / "lib", package / "lib" / "dri"]
    created = 0
    for directory in directories:
        if not directory.is_dir():
            continue
        for path in sorted(directory.iterdir()):
            if not path.is_file() or ".so" not in path.name:
                continue
            alias = soname(path)
            if not alias or alias == path.name:
                continue
            target = directory / alias
            if not target.exists() and not target.is_symlink():
                target.symlink_to(path.name)
                created += 1
    print(f"Created {created} SONAME symlinks in {package / 'lib'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
