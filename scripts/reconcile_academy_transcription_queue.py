#!/usr/bin/env python3
"""Reconcile Academy queue statuses against canonical transcript files."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def transcript_state(data_root: Path, media_id: str) -> str:
    path = data_root / "raw" / "youtube" / media_id / "transcript_original.json"
    if not path.is_file():
        return "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "invalid"
    return "nonempty" if payload.get("segments") else "empty"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--queue", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with args.queue.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    updates = []
    for row in rows:
        media_id = row.get("transcription_media_id") or row.get("candidate_video_id") or ""
        state = transcript_state(args.data_root, media_id) if media_id else "missing"
        before = row.get("transcription_status") or ""
        after = before
        if before == "youtube_in_main_queue_pending_transcript" and state == "nonempty":
            after = "youtube_processed_existing"
        elif before == "transcribed_empty" and state == "nonempty":
            after = "transcribed"
        if after != before:
            row["transcription_status"] = after
            row["transcription_updated_at"] = utc_now()
            updates.append({"media_id": media_id, "from": before, "to": after})
    manifest = {
        "generated_at": utc_now(),
        "rows": len(rows),
        "updates": updates,
        "status_counts": {status: sum(row.get("transcription_status") == status for row in rows) for status in sorted({row.get("transcription_status") for row in rows})},
    }
    if not args.dry_run:
        args.queue.parent.mkdir(parents=True, exist_ok=True)
        with args.queue.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
