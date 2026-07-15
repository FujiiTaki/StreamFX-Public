#!/usr/bin/env python3
"""Verify that an OBS plugin's bundled runtime imports exist in an OBS ZIP."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path


RUNTIME_IMPORT = re.compile(
    r"^(?:avcodec-|avutil-|swscale-|swresample-|Qt6|libcurl|obs(?:-|\.dll))",
    re.IGNORECASE,
)


def imported_dlls(plugin: Path) -> set[str]:
    result = subprocess.run(
        ["objdump", "-p", str(plugin)],
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        match.group(1).casefold()
        for match in re.finditer(r"^\s*DLL Name:\s*(\S+)\s*$", result.stdout, re.MULTILINE)
    }


def archived_dlls(obs_zip: Path) -> set[str]:
    with zipfile.ZipFile(obs_zip) as archive:
        return {
            Path(name).name.casefold()
            for name in archive.namelist()
            if name.casefold().endswith(".dll")
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plugin", type=Path)
    parser.add_argument("obs_zip", type=Path)
    args = parser.parse_args()

    required = {name for name in imported_dlls(args.plugin) if RUNTIME_IMPORT.match(name)}
    missing = sorted(required - archived_dlls(args.obs_zip))
    if missing:
        print("OBS runtime is missing plugin dependencies:", file=sys.stderr)
        for name in missing:
            print(f"  - {name}", file=sys.stderr)
        return 1

    print(f"All {len(required)} OBS runtime dependencies are available.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
