#!/usr/bin/env python3
"""Verify the explicit runtime used by a gold episode execution."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any


RUNTIME_WINDOWS_NATIVE = "windows_native"
RUNTIME_WSL_LINUX = "wsl_linux"
RUNTIMES = (RUNTIME_WINDOWS_NATIVE, RUNTIME_WSL_LINUX)
OPTIONAL_COMMANDS = ("ffmpeg", "node", "npm", "rsync")


def inside_wsl() -> bool:
    release = platform.release().lower()
    return "microsoft" in release or "wsl" in release


def selected_runtime(runtime: str | None = None) -> str:
    value = (runtime or os.environ.get("MSF_GOLD_RUNTIME") or RUNTIME_WINDOWS_NATIVE).strip().lower()
    if value not in RUNTIMES:
        raise ValueError(f"unsupported MSF gold runtime: {value}")
    return value


def default_temp_root(data_root: Path, runtime: str | None = None) -> Path:
    active_runtime = selected_runtime(runtime)
    configured = os.environ.get("MSF_GOLD_TEMP_DIR") or os.environ.get("TMPDIR")
    if configured:
        return Path(configured).expanduser()
    if active_runtime == RUNTIME_WSL_LINUX:
        return Path("~/.cache/msf/tmp").expanduser()
    return data_root / ".tmp"


def _path_is_native(value: Path, runtime: str) -> bool:
    normalized = str(value).replace("\\", "/").lower()
    if runtime == RUNTIME_WSL_LINUX:
        return not normalized.startswith("/mnt/")
    return not normalized.startswith("/mnt/") and not normalized.startswith("//wsl$/")


def path_check(name: str, value: Path, runtime: str) -> dict[str, object]:
    resolved = value.expanduser().resolve(strict=False)
    return {
        "name": name,
        "path": str(resolved),
        "exists": resolved.exists(),
        "native": _path_is_native(resolved, runtime),
    }


def _inside_expected_venv(active_python: str, repo_root: Path, runtime: str) -> bool:
    venv_dir = repo_root / ".venv"
    expected = venv_dir / ("bin" if runtime == RUNTIME_WSL_LINUX else "Scripts")
    normalized_active = active_python.replace("\\", "/").casefold()
    normalized_expected = str(expected.expanduser().absolute()).replace("\\", "/").casefold().rstrip("/")
    return normalized_active.startswith(normalized_expected + "/")


def verify_environment(
    *,
    repo_root: Path | None = None,
    data_root: Path | None = None,
    temp_root: Path | None = None,
    runtime: str | None = None,
) -> dict[str, Any]:
    active_runtime = selected_runtime(runtime)
    repo_root = repo_root or Path(__file__).resolve().parents[1]
    data_root = data_root or Path(os.environ.get("MSF_DATA_DIR", "C:/MSF-data/Marketing_Swipe_File"))
    temp_root = temp_root or default_temp_root(data_root, active_runtime)
    # Gold review/finalization consumes prepared transcript JSON. Media recovery
    # and WSL synchronization are separate capabilities, not episode blockers.
    required_commands = ("git",)
    commands = {name: shutil.which(name) for name in required_commands}
    optional_commands = {name: shutil.which(name) for name in OPTIONAL_COMMANDS}
    paths = [
        path_check("repository", repo_root, active_runtime),
        path_check("data_root", data_root, active_runtime),
        path_check("temp_root", temp_root, active_runtime),
        path_check("virtualenv", repo_root / ".venv", active_runtime),
    ]
    errors: list[str] = []
    if active_runtime == RUNTIME_WSL_LINUX:
        if sys.platform != "linux" or not inside_wsl():
            errors.append("runtime is not WSL Linux")
    elif sys.platform != "win32":
        errors.append("runtime is not Windows native")
    if sys.version_info[:2] != (3, 12):
        errors.append(f"expected Python 3.12, found {platform.python_version()}")
    for item in paths:
        if not item["native"]:
            errors.append(f"{item['name']} is not native to {active_runtime}: {item['path']}")
        if item["name"] != "temp_root" and not item["exists"]:
            errors.append(f"missing path: {item['name']} ({item['path']})")
    active_python = str(Path(sys.executable).expanduser().absolute())
    if not _inside_expected_venv(active_python, repo_root, active_runtime):
        errors.append(f"Python is outside repository virtualenv: {active_python}")
    temp_writable = False
    try:
        resolved_temp = temp_root.expanduser().resolve(strict=False)
        resolved_temp.mkdir(parents=True, exist_ok=True)
        probe = resolved_temp / f".msf-write-probe-{os.getpid()}"
        probe.write_text("ok\n", encoding="ascii")
        probe.unlink()
        temp_writable = True
    except OSError as exc:
        errors.append(f"temp_root is not writable: {exc}")
    for name, executable in commands.items():
        if executable is None:
            errors.append(f"missing command: {name}")
    return {
        "status": "pass" if not errors else "fail",
        "runtime": active_runtime,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "paths": paths,
        "commands": commands,
        "optional_commands": optional_commands,
        "active_python": active_python,
        "temp_writable": temp_writable,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the configured Gold runtime without touching episode data.")
    parser.add_argument("--runtime", choices=RUNTIMES)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--temp-root", type=Path)
    args = parser.parse_args()
    result = verify_environment(data_root=args.data_root, temp_root=args.temp_root, runtime=args.runtime)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
