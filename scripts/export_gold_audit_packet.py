#!/usr/bin/env python
"""Create a blind external-review packet without internal audit notes."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path

from scripts.gold_extraction_common import GoldPauseError, load_json, now, write_json


PACKET_FILES = (
    "transcript_clean.json", "insights_exhaustive.json", "high_signal_coverage_ledger.json", "calibration_tests.json",
)
PACKET_OUTPUT_FILES = frozenset((*PACKET_FILES, "packet_manifest.json"))


def export_packet(
    video_id: str,
    data_root: Path,
    suffix: str,
    *,
    audit_warnings: list[dict] | None = None,
    revision_id: str | None = None,
) -> dict[str, str]:
    source = data_root / "processed" / video_id / "gold_extraction"
    destination = data_root / "exports" / suffix
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{suffix}.staging-", dir=destination.parent))
    backup: Path | None = None
    published = False
    try:
        for filename in PACKET_FILES:
            shutil.copy2(source / filename, stage / filename)
        write_json(stage / "packet_manifest.json", {
            "episode_video_id": video_id, "created_at": now(), "packet_kind": "blind_external_audit",
            "included_files": list(PACKET_FILES), "excluded": ["editorial_audit_report.json", "validation_report.md", "manual_reviews", "dedupe_decision_queue.json"],
            "audit_warnings": audit_warnings or [], "revision_id": revision_id,
        })
        if {path.name for path in stage.iterdir() if path.is_file()} != PACKET_OUTPUT_FILES:
            raise ValueError("staged audit packet does not contain exactly five files")
        if destination.exists():
            backup = destination.with_name(f".{destination.name}.backup-{stage.name.rsplit('-', 1)[-1]}")
            os.replace(destination, backup)
        try:
            os.replace(stage, destination)
            published = True
        except OSError:
            if backup is not None and backup.exists() and not destination.exists():
                os.replace(backup, destination)
            raise
        status_path = source / "gold_extraction_status.json"
        if status_path.exists():
            status = load_json(status_path)
            status["audit_packet"] = str(destination)
            status["audit_packet_exported_at"] = now()
            write_json(status_path, status)
    except PermissionError as exc:
        raise GoldPauseError(f"filesystem permission/lock while writing audit packet {destination}") from exc
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        if published and backup is not None and backup.exists():
            shutil.rmtree(backup, ignore_errors=True)
    return {"packet": str(destination)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--suffix", required=True)
    args = parser.parse_args()
    try:
        result = export_packet(args.video_id, args.data_root, args.suffix)
    except GoldPauseError as exc:
        print(json.dumps({"status": "paused_filesystem", "error": str(exc)}))
        return 75
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
