#!/usr/bin/env python
"""Publish a verified, read-only snapshot of MSF exports for Windows consumers.

The active pipeline stays on the Linux filesystem. This command copies only the
safe, derived ``exports`` surface into a OneDrive-visible directory using a
staged directory swap. It never reads from or writes to raw/processed data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from scripts.msf_common import data_path


MANIFEST_NAME = "published_manifest.json"
PUBLISHED_EXPORTS_DIR = "exports"
ALLOWED_SUFFIXES = frozenset({".csv", ".json", ".md", ".sha256"})
EXCLUDED_TOP_LEVEL_DIRECTORIES = frozenset({"_snapshots"})


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _is_publishable(relative_path: Path) -> bool:
    return (
        relative_path.suffix.lower() in ALLOWED_SUFFIXES
        and bool(relative_path.parts)
        and relative_path.parts[0] not in EXCLUDED_TOP_LEVEL_DIRECTORIES
        and not any(part.startswith(".") for part in relative_path.parts)
    )


def collect_exports(source: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Return the approved exports inventory without writing anything."""
    source = source.resolve()
    if not source.is_dir():
        raise ValueError(f"exports source does not exist: {source}")

    files: list[dict[str, Any]] = []
    skipped: list[str] = []
    for path in sorted(candidate for candidate in source.rglob("*") if candidate.is_file()):
        relative = path.relative_to(source)
        normalized = relative.as_posix()
        if not _is_publishable(relative):
            skipped.append(normalized)
            continue
        files.append({"path": normalized, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return files, skipped


def publication_plan(source: Path) -> dict[str, Any]:
    files, skipped = collect_exports(source)
    return {
        "status": "ready_to_publish",
        "source_content_hash": canonical_hash(files),
        "file_count": len(files),
        "total_bytes": sum(item["bytes"] for item in files),
        "files": files,
        "skipped": skipped,
    }


def build_manifest(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "kind": "marketing_swipe_file_shared_exports",
        "generated_at": datetime.now(UTC).isoformat(),
        "source_content_hash": plan["source_content_hash"],
        "file_count": plan["file_count"],
        "total_bytes": plan["total_bytes"],
        "files": plan["files"],
        "excluded_top_level_directories": sorted(EXCLUDED_TOP_LEVEL_DIRECTORIES),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _destination_entries(destination: Path) -> Iterable[Path]:
    return (path for path in destination.rglob("*") if path.is_file())


def verify_published_snapshot(destination: Path) -> dict[str, Any]:
    """Validate an existing published snapshot without writing to it."""
    destination = destination.resolve()
    manifest_path = destination / MANIFEST_NAME
    exports_root = destination / PUBLISHED_EXPORTS_DIR
    if not manifest_path.is_file() or not exports_root.is_dir():
        return {"valid": False, "reason": "missing manifest or exports directory"}

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"valid": False, "reason": f"invalid manifest: {exc}"}

    expected = manifest.get("files")
    if not isinstance(expected, list):
        return {"valid": False, "reason": "manifest files is not a list"}
    expected_by_path = {str(item.get("path")): item for item in expected if isinstance(item, dict)}
    if len(expected_by_path) != len(expected):
        return {"valid": False, "reason": "manifest contains duplicate or invalid file paths"}

    actual_by_path = {
        path.relative_to(exports_root).as_posix(): path
        for path in _destination_entries(exports_root)
    }
    if set(expected_by_path) != set(actual_by_path):
        return {
            "valid": False,
            "reason": "published file set differs from manifest",
            "missing": sorted(set(expected_by_path) - set(actual_by_path)),
            "extra": sorted(set(actual_by_path) - set(expected_by_path)),
        }

    for relative, entry in expected_by_path.items():
        actual = actual_by_path[relative]
        if actual.stat().st_size != entry.get("bytes") or sha256_file(actual) != entry.get("sha256"):
            return {"valid": False, "reason": f"hash or size mismatch: {relative}"}

    computed_content_hash = canonical_hash(expected)
    if computed_content_hash != manifest.get("source_content_hash"):
        return {"valid": False, "reason": "manifest source content hash mismatch"}
    return {
        "valid": True,
        "file_count": len(expected),
        "total_bytes": sum(int(item["bytes"]) for item in expected),
        "source_content_hash": computed_content_hash,
    }


def publish_exports(source: Path, destination: Path, *, inject_failure_at: str | None = None) -> dict[str, Any]:
    """Publish one complete snapshot or leave the prior snapshot untouched."""
    source = source.resolve()
    destination = destination.resolve()
    if destination == source or source in destination.parents:
        raise ValueError("published destination must not be inside the active exports source")

    plan = publication_plan(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{destination.name}.staging-", dir=destination.parent))
    backup: Path | None = None
    published = False
    try:
        staged_exports = stage / PUBLISHED_EXPORTS_DIR
        staged_exports.mkdir()
        for item in plan["files"]:
            source_file = source / item["path"]
            target_file = staged_exports / item["path"]
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target_file)
            if source_file.stat().st_size != item["bytes"] or sha256_file(source_file) != item["sha256"]:
                raise RuntimeError(f"source changed while publishing: {item['path']}")
            if target_file.stat().st_size != item["bytes"] or sha256_file(target_file) != item["sha256"]:
                raise RuntimeError(f"staged copy verification failed: {item['path']}")
        write_json(stage / MANIFEST_NAME, build_manifest(plan))
        validation = verify_published_snapshot(stage)
        if not validation["valid"]:
            raise RuntimeError(f"staged snapshot invalid: {validation['reason']}")
        if inject_failure_at == "before_swap":
            raise RuntimeError("injected failure before swap")

        if destination.exists():
            backup = destination.with_name(f".{destination.name}.backup-{stage.name.rsplit('-', 1)[-1]}")
            os.replace(destination, backup)
        try:
            if inject_failure_at == "during_swap":
                raise RuntimeError("injected failure during swap")
            os.replace(stage, destination)
            published = True
        except BaseException:
            if backup is not None and backup.exists() and not destination.exists():
                os.replace(backup, destination)
            raise
        if backup is not None and backup.exists():
            shutil.rmtree(backup)
        return {"status": "published", "destination": str(destination), **validation}
    except PermissionError as exc:
        raise RuntimeError(f"filesystem permission/lock while publishing {destination}") from exc
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        if published and backup is not None and backup.exists():
            shutil.rmtree(backup, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=data_path("exports"))
    parser.add_argument("--destination", type=Path, default=os.environ.get("MSF_PUBLISHED_DIR"))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="inspect the publish plan without writing")
    mode.add_argument("--publish", action="store_true", help="publish one verified snapshot")
    args = parser.parse_args()
    if args.destination is None:
        parser.error("--destination or MSF_PUBLISHED_DIR is required")

    try:
        result = publication_plan(args.source) if args.check else publish_exports(args.source, args.destination)
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
