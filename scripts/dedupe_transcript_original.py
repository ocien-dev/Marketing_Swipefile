#!/usr/bin/env python3
"""Deduplicate exact Chrome DOM transcript pairs while retaining raw provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.backfill_vturb_transcripts import (
    atomic_write_json,
    metadata_path,
    read_json,
    validate_transcript_payload,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dedupe_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered: list[dict[str, Any]] = []
    positions: dict[tuple[float, str], int] = {}
    for segment in segments:
        text = str(segment.get("text") or "").strip()
        start = round(float(segment.get("start_seconds") or 0), 3)
        key = (start, text)
        duration = max(float(segment.get("duration_seconds") or 0), 0.0)
        if key not in positions:
            positions[key] = len(ordered)
            ordered.append({**segment, "start_seconds": start, "duration_seconds": round(duration, 3), "text": text})
            continue
        existing = ordered[positions[key]]
        if duration > float(existing.get("duration_seconds") or 0):
            existing["duration_seconds"] = round(duration, 3)
    return ordered


def dedupe_episode(data_root: Path, video_id: str) -> dict[str, Any]:
    raw = data_root / "raw" / "youtube" / video_id
    original_path = raw / "transcript_original.json"
    capture_path = raw / "transcript_original_browser_capture.json"
    original = read_json(original_path)
    before_segments = list(original.get("segments") or [])
    before_sha = sha256(original_path)
    if not capture_path.is_file():
        atomic_write_json(capture_path, original)
    deduped = dedupe_segments(before_segments)
    payload = dict(original)
    payload["segments"] = deduped
    payload["normalization"] = {
        "kind": "exact_start_text_pair_deduplication",
        "raw_capture_path": str(capture_path),
        "raw_capture_sha256": sha256(capture_path),
        "input_segments": len(before_segments),
        "output_segments": len(deduped),
        "removed_segments": len(before_segments) - len(deduped),
    }
    atomic_write_json(original_path, payload)
    meta_path = metadata_path(data_root, video_id)
    metadata = read_json(meta_path)
    validation = validate_transcript_payload(
        payload,
        video_id=video_id,
        duration_seconds=float(metadata.get("duration_seconds") or 0),
        minimum_bytes=1_000,
        minimum_coverage=0.60,
    )
    if validation["errors"]:
        raise ValueError(f"deduplicated transcript is invalid: {validation['errors']}")
    after_sha = sha256(original_path)
    metadata.update({
        "transcript_sha256": validation["sha256"],
        "transcript_segments": validation["segment_count"],
        "transcript_last_timestamp": validation["last_timestamp"],
        "transcript_coverage": validation["coverage"],
        "transcript_deduplicated": True,
        "transcript_raw_capture_sha256": sha256(capture_path),
    })
    translated_path = raw / "transcript_pt_br.json"
    if translated_path.is_file():
        translated = read_json(translated_path)
        translated["source_transcript_sha256"] = after_sha
        atomic_write_json(translated_path, translated)
        translated_validation = validate_transcript_payload(
            translated,
            video_id=video_id,
            duration_seconds=float(metadata.get("duration_seconds") or 0),
            minimum_bytes=1_000,
            minimum_coverage=0.60,
        )
        if translated_validation["errors"]:
            raise ValueError(
                f"translation became invalid after source fingerprint update: "
                f"{translated_validation['errors']}"
            )
        metadata.update({
            "translation_sha256": translated_validation["sha256"],
            "translation_segments": translated_validation["segment_count"],
            "translation_last_timestamp": translated_validation["last_timestamp"],
            "translation_coverage": translated_validation["coverage"],
        })
    atomic_write_json(meta_path, metadata)
    return {
        "status": "deduplicated",
        "video_id": video_id,
        "before_sha256": before_sha,
        "after_sha256": after_sha,
        "input_segments": len(before_segments),
        "output_segments": len(deduped),
        "removed_segments": len(before_segments) - len(deduped),
        "coverage": validation["coverage"],
        "raw_capture": str(capture_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--video-id", action="append", required=True)
    args = parser.parse_args()
    results = [dedupe_episode(args.data_root, video_id) for video_id in args.video_id]
    print(json.dumps({"status": "complete", "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
