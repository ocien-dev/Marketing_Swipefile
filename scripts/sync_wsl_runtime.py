#!/usr/bin/env python3
"""Synchronize the allowlisted gold runtime into a Linux-native WSL mirror."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _semantic_hash(value: Any) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def _manifest_files(manifest_path: Path, source_root: Path | None = None) -> list[str]:
    payload = _read_json(manifest_path)
    files = payload.get("files")
    if payload.get("sync_scope") == "full_worktree":
        if source_root is None:
            raise ValueError("full_worktree runtime sync requires source_root")
        try:
            result = subprocess.run(
                ["git", "-C", str(source_root), "ls-files", "--cached", "--others", "--exclude-standard"],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise ValueError(f"cannot inventory the complete Git worktree: {exc}") from exc
        excluded = tuple(str(item).rstrip("/") + "/" for item in payload.get("exclude_prefixes", []))
        discovered = [
            line.replace("\\", "/")
            for line in result.stdout.splitlines()
            if line.strip()
            and not line.replace("\\", "/").startswith(excluded)
            and "/__pycache__/" not in f"/{line.replace(chr(92), '/')}"
            and not line.endswith((".pyc", ".pyo"))
        ]
        files = [*discovered, *(files or [])]
    if not isinstance(files, list) or not files:
        raise ValueError("runtime sync manifest must contain a non-empty files array")
    normalized: list[str] = []
    full_worktree = payload.get("sync_scope") == "full_worktree"
    for raw in files:
        path = PurePosixPath(str(raw).replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts or str(path) in {"", "."}:
            raise ValueError(f"unsafe runtime sync path: {raw}")
        value = str(path)
        if value in normalized:
            if full_worktree:
                continue
            raise ValueError(f"duplicate runtime sync path: {value}")
        normalized.append(value)
    return normalized


def _manifest_execution_files(manifest_path: Path, all_paths: list[str]) -> list[str]:
    payload = _read_json(manifest_path)
    raw_files = payload.get("execution_files")
    if raw_files is None:
        return list(all_paths)
    if not isinstance(raw_files, list) or not raw_files:
        raise ValueError("runtime sync manifest execution_files must be a non-empty list")
    execution: list[str] = []
    for raw in raw_files:
        path = PurePosixPath(str(raw).replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts or str(path) in {"", "."}:
            raise ValueError(f"unsafe runtime execution path: {raw}")
        value = str(path)
        if value in execution:
            raise ValueError(f"duplicate runtime execution path: {value}")
        execution.append(value)
    missing = sorted(set(execution) - set(all_paths))
    if missing:
        raise ValueError(f"execution_files missing from synchronized inventory: {missing}")
    return execution


def _scoped_signature(files: list[dict[str, Any]], scope: str) -> str:
    return _semantic_hash([
        {"path": item.get("path"), "sha256": item.get("sha256")}
        for item in sorted(files, key=lambda value: str(value.get("path")))
        if item.get("signature_scope") == scope
    ])


def _git_value(source_root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(source_root), *args],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() or None


def _dirty_allowlist(source_root: Path, paths: list[str]) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(source_root), "status", "--porcelain=v1", "--", *paths],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    return sorted({line[3:].replace("\\", "/") for line in result.stdout.splitlines() if len(line) > 3})


def _runtime_python(destination_root: Path) -> dict[str, Any]:
    executable = destination_root / ".venv" / "bin" / "python"
    if not executable.is_file():
        return {"executable": str(executable), "available": False, "version": None}
    try:
        result = subprocess.run(
            [str(executable), "--version"], check=True, capture_output=True, text=True, timeout=10
        )
        version = (result.stdout or result.stderr).strip()
    except (OSError, subprocess.SubprocessError):
        return {"executable": str(executable), "available": False, "version": None}
    return {"executable": str(executable), "available": True, "version": version}


def _copy_atomic(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
    os.close(fd)
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, destination)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def build_sync_plan(
    source_root: Path,
    destination_root: Path,
    manifest_path: Path,
    receipt_path: Path,
    *,
    initialize: bool = False,
) -> dict[str, Any]:
    source_root = source_root.resolve()
    destination_root = destination_root.resolve()
    if source_root == destination_root:
        raise ValueError("source and destination runtime roots must differ")
    if str(destination_root).replace("\\", "/").startswith("/mnt/"):
        raise ValueError("destination runtime must be Linux-native, not /mnt")
    manifest_payload = _read_json(manifest_path)
    paths = _manifest_files(manifest_path, source_root)
    execution_paths = set(_manifest_execution_files(manifest_path, paths))
    prior = _read_json(receipt_path) if receipt_path.exists() else {}
    prior_files = {item.get("path"): item for item in prior.get("files", [])}
    records: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    if manifest_payload.get("require_git_clone"):
        source_origin = _git_value(source_root, "remote", "get-url", "origin")
        destination_origin = _git_value(destination_root, "remote", "get-url", "origin")
        if not (destination_root / ".git").exists():
            conflicts.append({"path": ".git", "reason": "linux_native_clone_missing"})
        elif source_origin and destination_origin != source_origin:
            conflicts.append({
                "path": ".git/config",
                "reason": "clone_origin_mismatch",
                "source_origin": source_origin,
                "destination_origin": destination_origin,
            })
    copies: list[str] = []
    for relative in paths:
        source = source_root / relative
        destination = destination_root / relative
        if not source.is_file():
            conflicts.append({"path": relative, "reason": "source_missing"})
            continue
        source_hash = _sha256(source)
        destination_hash = _sha256(destination) if destination.is_file() else None
        previous_hash = prior_files.get(relative, {}).get("sha256")
        if source_hash != destination_hash:
            destination_drifted = previous_hash is not None and destination_hash != previous_hash
            unknown_existing = previous_hash is None and destination_hash is not None
            if destination_drifted or (unknown_existing and not initialize):
                conflicts.append({
                    "path": relative,
                    "reason": "destination_drift" if destination_drifted else "uninitialized_destination",
                    "source_sha256": source_hash,
                    "destination_sha256": destination_hash,
                    "previous_sha256": previous_hash,
                })
            else:
                copies.append(relative)
        records.append({
            "path": relative,
            "signature_scope": "execution" if relative in execution_paths else "documentation",
            "sha256": source_hash,
            "source_size": source.stat().st_size,
            "destination_sha256": destination_hash,
            "destination_size": destination.stat().st_size if destination.is_file() else None,
        })
    return {
        "source_root": str(source_root),
        "destination_root": str(destination_root),
        "manifest": str(manifest_path.resolve()),
        "manifest_sha256": _sha256(manifest_path),
        "sync_scope": manifest_payload.get("sync_scope", "allowlist"),
        "require_git_clone": bool(manifest_payload.get("require_git_clone")),
        "receipt": str(receipt_path.resolve()),
        "files": records,
        "copies": copies,
        "conflicts": conflicts,
    }


def synchronize_runtime(
    source_root: Path,
    destination_root: Path,
    manifest_path: Path,
    receipt_path: Path,
    *,
    check: bool = False,
    initialize: bool = False,
    reuse_valid: bool = False,
) -> dict[str, Any]:
    if reuse_valid and receipt_path.exists():
        errors = validate_runtime_parity_receipt(receipt_path, destination_root, manifest_path)
        if not errors:
            return {
                "status": "pass",
                "read_only": True,
                "reused": True,
                "copied": [],
                "receipt": _read_json(receipt_path),
            }
    plan = build_sync_plan(source_root, destination_root, manifest_path, receipt_path, initialize=initialize)
    if plan["conflicts"]:
        return {"status": "blocked", "read_only": check, **plan}
    if check:
        return {"status": "pass" if not plan["copies"] else "stale", "read_only": True, **plan}
    for relative in plan["copies"]:
        _copy_atomic(Path(plan["source_root"]) / relative, Path(plan["destination_root"]) / relative)
    verified = build_sync_plan(
        Path(plan["source_root"]), Path(plan["destination_root"]), manifest_path, receipt_path, initialize=True
    )
    if verified["conflicts"] or verified["copies"]:
        raise RuntimeError("runtime mirror verification failed after sync")
    files = []
    for item in verified["files"]:
        files.append({
            "path": item["path"],
            "signature_scope": item["signature_scope"],
            "sha256": item["sha256"],
            "source_size": item["source_size"],
            "destination_size": item["destination_size"],
        })
    core = {
        "schema_version": "1.1.0",
        "kind": "gold_runtime_parity",
        "status": "pass",
        "source_root": verified["source_root"],
        "destination_root": verified["destination_root"],
        "manifest": str(manifest_path.resolve()),
        "manifest_sha256": verified["manifest_sha256"],
        "sync_scope": verified["sync_scope"],
        "require_git_clone": verified["require_git_clone"],
        "git_branch": _git_value(Path(plan["source_root"]), "branch", "--show-current"),
        "git_head": _git_value(Path(plan["source_root"]), "rev-parse", "HEAD"),
        "destination_git_head": _git_value(Path(plan["destination_root"]), "rev-parse", "HEAD"),
        "destination_git_origin": _git_value(Path(plan["destination_root"]), "remote", "get-url", "origin"),
        "dirty_allowlist": _dirty_allowlist(Path(plan["source_root"]), [item["path"] for item in files]),
        "python_executable": os.path.realpath(os.sys.executable),
        "python_version": os.sys.version.split()[0],
        "runtime_python": _runtime_python(Path(verified["destination_root"])),
        "files": files,
        "execution_signature": _scoped_signature(files, "execution"),
        "documentation_signature": _scoped_signature(files, "documentation"),
        "synced_at": _utc_now(),
    }
    receipt = {**core, "receipt_semantic_sha256": _semantic_hash(core)}
    _atomic_json(receipt_path, receipt)
    return {"status": "pass", "read_only": False, "copied": plan["copies"], "receipt": receipt}


def validate_runtime_parity_receipt(
    receipt_path: Path,
    destination_root: Path,
    manifest_path: Path,
    *,
    check_source: bool = True,
    expected_execution_signature: str | None = None,
) -> list[str]:
    if not receipt_path.is_file():
        return ["runtime parity receipt is missing"]
    try:
        receipt = _read_json(receipt_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"runtime parity receipt is unreadable: {exc}"]
    core = {key: value for key, value in receipt.items() if key != "receipt_semantic_sha256"}
    errors: list[str] = []
    if receipt.get("receipt_semantic_sha256") != _semantic_hash(core):
        errors.append("runtime parity receipt semantic hash is invalid")
    if receipt.get("status") != "pass":
        errors.append("runtime parity receipt is not passing")
    if Path(receipt.get("destination_root", "")).resolve() != destination_root.resolve():
        errors.append("runtime parity receipt destination does not match runtime root")
    if check_source and (not manifest_path.is_file() or receipt.get("manifest_sha256") != _sha256(manifest_path)):
        errors.append("runtime parity manifest is stale or missing")
    source_root = Path(receipt.get("source_root", ""))
    receipt_files = {item.get("path"): item for item in receipt.get("files", [])}
    receipt_execution_paths = {
        path for path, item in receipt_files.items()
        if item.get("signature_scope", "execution") == "execution"
    }
    if check_source:
        expected_paths_list = _manifest_files(manifest_path, source_root) if manifest_path.is_file() else []
        expected_execution_paths = set(_manifest_execution_files(manifest_path, expected_paths_list)) if manifest_path.is_file() else set()
        if receipt_execution_paths != expected_execution_paths:
            errors.append("runtime parity receipt execution allowlist does not match manifest")
    else:
        expected_execution_paths = receipt_execution_paths
    computed_execution_signature = _scoped_signature(list(receipt_files.values()), "execution")
    if receipt.get("schema_version") == "1.1.0" and receipt.get("execution_signature") != computed_execution_signature:
        errors.append("runtime parity execution signature is invalid")
    if expected_execution_signature is not None and receipt.get("execution_signature") != expected_execution_signature:
        errors.append("runtime parity execution signature differs from the run snapshot")
    for relative in sorted(expected_execution_paths):
        expected = receipt_files.get(relative, {}).get("sha256")
        source = source_root / relative
        destination = destination_root / relative
        if check_source and (not source.is_file() or _sha256(source) != expected):
            errors.append(f"runtime source changed after parity receipt: {relative}")
        if not destination.is_file() or _sha256(destination) != expected:
            errors.append(f"runtime mirror is stale or changed: {relative}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--destination-root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--initialize", action="store_true")
    parser.add_argument("--reuse-valid", action="store_true", help="Reuse an unchanged passing parity receipt without rewriting it.")
    parser.add_argument("--full-output", action="store_true", help="Print the complete receipt instead of the compact CLI summary.")
    parser.add_argument(
        "--exec-after",
        nargs=argparse.REMAINDER,
        help="After a passing sync, replace this process with the explicit command array.",
    )
    args = parser.parse_args()
    result = synchronize_runtime(
        args.source_root,
        args.destination_root,
        args.manifest,
        args.receipt,
        check=args.check,
        initialize=args.initialize,
        reuse_valid=args.reuse_valid,
    )
    if result["status"] == "pass" and args.exec_after:
        executable = args.exec_after[0]
        if not os.path.isabs(executable):
            parser.error("--exec-after requires an absolute executable path")
        # The sync process may have been launched from the mounted Windows
        # checkout. Ensure module discovery and parity validation use the
        # Linux-native runtime clone before replacing this process.
        os.chdir(args.destination_root)
        os.execv(executable, args.exec_after)
    output = result
    if not args.full_output:
        receipt_value = result.get("receipt", {})
        if isinstance(receipt_value, dict):
            receipt = receipt_value
        elif args.receipt.is_file():
            receipt = _read_json(args.receipt)
        else:
            receipt = {}
        output = {
            "status": result.get("status"),
            "read_only": result.get("read_only"),
            "reused": result.get("reused", False),
            "copied_count": len(result.get("copied", [])),
            "conflicts": result.get("conflicts", []),
            "receipt": {
                "path": str(args.receipt),
                "semantic_sha256": receipt.get("receipt_semantic_sha256"),
                "file_count": len(receipt.get("files", [])),
                "execution_file_count": sum(1 for item in receipt.get("files", []) if item.get("signature_scope", "execution") == "execution"),
                "execution_signature": receipt.get("execution_signature"),
                "documentation_signature": receipt.get("documentation_signature"),
                "sync_scope": receipt.get("sync_scope"),
            },
        }
    print(json.dumps(output, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
