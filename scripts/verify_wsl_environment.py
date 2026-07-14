#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from pathlib import Path


REQUIRED_COMMANDS = ("git", "ffmpeg", "node", "npm", "rsync")


def inside_wsl() -> bool:
    release = platform.release().lower()
    return "microsoft" in release or "wsl" in release


def path_check(name: str, value: Path) -> dict[str, object]:
    resolved = value.expanduser().resolve(strict=False)
    linux_native = not str(resolved).startswith("/mnt/")
    return {
        "name": name,
        "path": str(resolved),
        "exists": resolved.exists(),
        "linux_native": linux_native,
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    data_root = Path(
        os.environ.get("MSF_DATA_DIR", "~/msf-data/Marketing_Swipe_File")
    )
    temp_root = Path(os.environ.get("TMPDIR", "~/.cache/msf/tmp"))
    commands = {name: shutil.which(name) for name in REQUIRED_COMMANDS}
    paths = [
        path_check("repository", repo_root),
        path_check("data_root", data_root),
        path_check("temp_root", temp_root),
        path_check("virtualenv", repo_root / ".venv"),
    ]
    errors: list[str] = []
    if sys.platform != "linux" or not inside_wsl():
        errors.append("runtime is not WSL Linux")
    if sys.version_info[:2] != (3, 12):
        errors.append(f"expected Python 3.12, found {platform.python_version()}")
    for item in paths:
        if not item["linux_native"]:
            errors.append(f"{item['name']} is under /mnt and is not Linux-native")
    for name, executable in commands.items():
        if executable is None:
            errors.append(f"missing command: {name}")

    result = {
        "status": "pass" if not errors else "fail",
        "platform": platform.platform(),
        "python": platform.python_version(),
        "paths": paths,
        "commands": commands,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
