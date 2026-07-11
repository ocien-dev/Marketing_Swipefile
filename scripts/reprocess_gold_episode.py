#!/usr/bin/env python
"""Prepare one podcast for human semantic gold extraction.

The command performs deterministic cleanup, chunking, recall-oriented signal
inventory and work-order checkpointing.  It intentionally does not call an
LLM or create editorial insights.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from scripts.gold_extraction_common import (
    GoldPauseError,
    clean_segments,
    chunks_for_segments,
    discover_calibrations,
    fingerprint_paths,
    load_json,
    make_signal_inventory,
    now,
    protected_paths,
    sha256_json,
    write_json,
)


def validate(
    segments: list[dict[str, Any]],
    chunks: list[list[dict[str, Any]]],
    removed: list[dict[str, Any]],
    duration_seconds: float,
) -> list[str]:
    errors: list[str] = []
    starts = [float(item["start_seconds"]) for item in segments]
    if starts != sorted(starts):
        errors.append("clean transcript is not chronological")
    if any(start > duration_seconds for start in starts):
        errors.append("clean transcript exceeds video duration")
    clean_ids = [item["segment_id"] for item in segments]
    chunk_ids = [item["segment_id"] for chunk in chunks for item in chunk]
    if clean_ids != chunk_ids or len(chunk_ids) != len(set(chunk_ids)):
        errors.append("chunks do not cover clean segments exactly once")
    if any(not item.get("reason") for item in removed):
        errors.append("removed segment lacks reason")
    return errors


def audit_omissions(segments: list[dict[str, Any]], represented_segment_ids: set[str]) -> list[dict[str, Any]]:
    """Compatibility helper: return signals not represented by a review yet."""
    inventory = make_signal_inventory(segments)
    return [
        {"segment_id": item["segment_id"], "text": next(segment["text"] for segment in segments if segment["segment_id"] == item["segment_id"])}
        for item in inventory if item["segment_id"] not in represented_segment_ids
    ]


def chunk_work_order(video_id: str, chunk: dict[str, Any], signals: list[dict[str, Any]], calibrations: list[dict[str, Any]]) -> dict[str, Any]:
    chunk_segments = chunk["segments"]
    segment_ids = {item["segment_id"] for item in chunk_segments}
    return {
        "schema_version": "1.0.0",
        "episode_video_id": video_id,
        "chunk_id": chunk["chunk_id"],
        "input_hash": sha256_json(chunk_segments),
        "route": "codex_manual_no_paid_api",
        "required_passes": [
            "numbers", "experiments", "procedures", "copy_vsl", "funnel", "traffic_creatives", "caveats", "gap_reread",
        ],
        "completion_contract": {
            "write_review_file": "manual_reviews/chunk_###_review.json",
            "candidate_fields": "gold_insights.schema.json",
            "zero_insight_allowed_only_after_full_read": True,
            "evidence": "minimal_quote + context_range + support_segments; quotes must remain verbatim UTF-8",
            "ledger": "every listed signal must be captured, merged, or excluded with a reason",
        },
        "calibration_targets": [item for item in calibrations if set(item["segment_ids"]) & segment_ids],
        "signals": [item for item in signals if item["segment_id"] in segment_ids],
        "segments": chunk_segments,
    }


def prior_chunk_state(status_path: Path) -> dict[str, dict[str, Any]]:
    if not status_path.exists():
        return {}
    try:
        return {item["chunk_id"]: item for item in load_json(status_path).get("chunks", [])}
    except (json.JSONDecodeError, KeyError, TypeError):
        return {}


def reusable_signal_inventory(out: Path, input_transcript_hash: str, prior_status: dict[str, Any], clean: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    """Reuse a reviewed inventory on an identical input instead of narrowing coverage on rerun."""
    if prior_status.get("input_transcript_hash") != input_transcript_hash:
        return None
    path = out / "signal_inventory.json"
    if not path.exists():
        return None
    try:
        signals = load_json(path).get("signals", [])
    except (json.JSONDecodeError, AttributeError):
        return None
    indexes = {item["segment_id"]: item["clean_index"] for item in clean}
    if not isinstance(signals, list) or any(
        item.get("segment_id") not in indexes or item.get("clean_index") != indexes[item.get("segment_id")]
        or not item.get("signal_types")
        for item in signals
    ):
        return None
    return signals


def archive_legacy_gold_once(out: Path) -> None:
    """Protect an older gold package before a new preparation rewrites it."""
    status_path = out / "gold_extraction_status.json"
    snapshot = out / "legacy_snapshot_before_r20"
    if not status_path.exists() or snapshot.exists():
        return
    existing = load_json(status_path)
    if existing.get("schema_version") == "1.0.0":
        return
    snapshot.mkdir(parents=True, exist_ok=True)
    for name in (
        "insights_exhaustive.json", "candidate_claims_master.json", "high_signal_coverage_ledger.json",
        "calibration_tests.json", "coverage_report.md", "validation_report.md", "editorial_audit_report.json",
        "gold_extraction_status.json",
    ):
        source = out / name
        if source.exists():
            try:
                shutil.copy2(source, snapshot / name)
            except PermissionError as exc:
                raise GoldPauseError(f"filesystem permission/lock while snapshotting {source}") from exc
def prepare_episode(video_id: str, data_root: Path) -> dict[str, Any]:
    raw_dir = data_root / "raw" / "youtube" / video_id
    out = data_root / "processed" / video_id / "gold_extraction"
    archive_legacy_gold_once(out)
    metadata = load_json(raw_dir / "metadata.json")
    original = load_json(raw_dir / "transcript_original.json")
    duration = float(metadata["duration_seconds"])
    raw_segments = original.get("segments") or []
    clean, removed = clean_segments(raw_segments, duration, video_id)
    chunks_raw = chunks_for_segments(clean)
    errors = validate(clean, chunks_raw, removed, duration)
    status_path = out / "gold_extraction_status.json"
    previous = prior_chunk_state(status_path)
    previous_status = load_json(status_path) if status_path.exists() else {}
    input_transcript_hash = sha256_json(clean)
    signals = reusable_signal_inventory(out, input_transcript_hash, previous_status, clean) or make_signal_inventory(clean)
    calibrations = discover_calibrations(clean, duration)
    chunk_index: list[dict[str, Any]] = []
    chunk_states: list[dict[str, Any]] = []
    for number, segments in enumerate(chunks_raw, 1):
        chunk_id = f"{video_id}-gold-chunk-{number:03d}"
        chunk_file = out / "chunks" / f"chunk_{number:03d}.json"
        payload = {"episode_video_id": video_id, "chunk_id": chunk_id, "chunk_number": number, "segments": segments}
        input_hash = sha256_json(segments)
        write_json(chunk_file, payload)
        work_order = chunk_work_order(video_id, payload, signals, calibrations["tests"])
        work_path = out / "work_orders" / f"chunk_{number:03d}_work_order.json"
        write_json(work_path, work_order)
        existing = previous.get(chunk_id, {})
        unchanged_completed = existing.get("input_hash") == input_hash and existing.get("status") == "completed"
        chunk_states.append({
            "chunk_id": chunk_id, "chunk_number": number, "input_hash": input_hash,
            "status": "completed" if unchanged_completed else "pending",
            "attempts": int(existing.get("attempts", 0)),
            "review_hash": existing.get("review_hash") if unchanged_completed else None,
            "candidate_count": int(existing.get("candidate_count", 0)) if unchanged_completed else 0,
            "work_order_file": str(work_path),
        })
        chunk_index.append({
            "chunk_id": chunk_id, "chunk_number": number,
            "start_seconds": segments[0]["start_seconds"],
            "end_seconds": segments[-1]["start_seconds"] + segments[-1]["duration_seconds"],
            "segment_count": len(segments), "char_count": sum(len(str(item["text"])) for item in segments),
            "first_segment_id": segments[0]["segment_id"], "last_segment_id": segments[-1]["segment_id"],
            "file": str(chunk_file), "input_hash": input_hash,
        })
    before = fingerprint_paths(protected_paths(data_root, video_id))
    write_json(out / "transcript_clean.json", {
        "episode_video_id": video_id, "source": str(raw_dir / "transcript_original.json"),
        "duration_seconds": duration, "segments": clean,
    })
    write_json(out / "removed_segments.json", {"episode_video_id": video_id, "removed_count": len(removed), "segments": removed})
    write_json(out / "chunks" / "chunk_index.json", {
        "episode_video_id": video_id, "strategy": "chronological_no_overlap_max_12000_chars_target_10_minutes",
        "chunks": chunk_index,
    })
    write_json(out / "signal_inventory.json", {
        "episode_video_id": video_id, "purpose": "recall-oriented lexical inventory; not editorial insights", "signals": signals,
    })
    write_json(out / "calibration_tests.json", {"episode_video_id": video_id, **calibrations})
    write_json(out / "high_signal_coverage_ledger.json", {
        "episode_video_id": video_id, "status": "awaiting_semantic_review",
        "entries": [{
            "segment_id": signal["segment_id"], "segment_range": [signal["clean_index"], signal["clean_index"]],
            "signal_types": signal["signal_types"], "disposition": "pending", "candidate_ids": [], "reason": None,
        } for signal in signals],
    })
    write_json(out / "protected_fingerprints.json", {"before": before, "after": before, "verified_at": now()})
    preserved_audit = previous_status.get("audit_status", "not_started") if previous_status.get("input_transcript_hash") == input_transcript_hash else "not_started"
    status = {
        "schema_version": "1.0.0", "episode_video_id": video_id,
        "route": "codex_manual_no_paid_api", "status": "validation_failed" if errors else "awaiting_semantic_review",
        "checkpoint_every_chunks": 1, "input_transcript_hash": input_transcript_hash,
        "chunks": chunk_states, "signal_count": len(signals), "calibration_target_count": len(calibrations["tests"]),
        "audit_status": preserved_audit, "updated_at": now(), "errors": errors,
    }
    write_json(status_path, status)
    return {"clean_segments": len(clean), "removed_segments": len(removed), "chunks": len(chunk_states), "signals": len(signals), "calibrations": len(calibrations["tests"]), "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--data-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = prepare_episode(args.video_id, args.data_root)
    except GoldPauseError as exc:
        print(json.dumps({"status": "paused_filesystem", "error": str(exc)}))
        return 75
    print(json.dumps(result, ensure_ascii=False))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
