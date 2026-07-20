#!/usr/bin/env python3
"""Audit canonical gold-source readiness for every episode in a priority queue."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.gold_extraction_common import load_json, preferred_transcript_path, write_json
from scripts.gold_episode_priority import load_queue_state, queue_state_path


def inspect_source(video_id: str, data_root: Path) -> dict[str, Any]:
    raw_dir = data_root / "raw" / "youtube" / video_id
    processed_dir = data_root / "processed" / video_id
    paths = {
        "metadata": raw_dir / "metadata.json",
        "transcript": preferred_transcript_path(data_root, video_id),
        "content_segments": processed_dir / "content_segments.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    invalid: list[str] = []
    metadata: dict[str, Any] | None = None
    transcript: dict[str, Any] | None = None
    if "metadata" not in missing:
        try:
            payload = load_json(paths["metadata"])
            metadata = payload if isinstance(payload, dict) else None
        except (OSError, ValueError, json.JSONDecodeError):
            invalid.append("metadata_invalid_json")
    if "transcript" not in missing:
        try:
            payload = load_json(paths["transcript"])
            transcript = payload if isinstance(payload, dict) else None
        except (OSError, ValueError, json.JSONDecodeError):
            invalid.append("transcript_invalid_json")
    if metadata is not None:
        metadata_id = metadata.get("youtube_video_id") or metadata.get("video_id") or video_id
        if metadata_id != video_id:
            invalid.append("metadata_video_id_mismatch")
    if transcript is not None:
        transcript_id = transcript.get("youtube_video_id") or transcript.get("video_id") or video_id
        transcript_status = (metadata or {}).get("transcript_status") or transcript.get("transcript_status")
        if transcript_id != video_id:
            invalid.append("transcript_video_id_mismatch")
        if transcript_status not in {None, "available"}:
            invalid.append(f"transcript_status_{transcript_status}")
        if not isinstance(transcript.get("segments"), list) or not transcript["segments"]:
            invalid.append("transcript_segments_empty")
    if "content_segments" not in missing:
        try:
            content = load_json(paths["content_segments"])
            if not isinstance(content, dict) or content.get("episode_video_id") != video_id:
                invalid.append("content_episode_video_id_mismatch")
            elif not isinstance(content.get("segments"), list) or not content["segments"]:
                invalid.append("content_segments_empty")
        except (OSError, ValueError, json.JSONDecodeError):
            invalid.append("content_invalid_json")
    if invalid:
        source_state = "invalid_source"
    elif missing == ["content_segments"]:
        source_state = "needs_materialization"
    elif missing:
        source_state = "missing_source_artifacts"
    else:
        source_state = "ready_for_gold"
    return {
        "source_state": source_state,
        "missing_artifacts": missing,
        "invalid_artifacts": invalid,
        "gold_extraction_exists": (processed_dir / "gold_extraction").is_dir(),
        "paths": {name: str(path) for name, path in paths.items()},
    }


def build_inventory(data_root: Path, queue_path: Path) -> dict[str, Any]:
    queue = load_json(queue_path)
    entries = queue.get("entries", []) if isinstance(queue, dict) else []
    if not isinstance(entries, list):
        raise ValueError("priority queue entries must be a list")
    state, state_errors = load_queue_state(queue_path, queue_state_path(queue_path))
    if state_errors:
        raise ValueError("; ".join(state_errors))
    terminal_states = {
        str(item.get("video_id")): item.get("state")
        for item in (state or {}).get("terminal_entries", [])
        if isinstance(item, dict)
    }
    items = []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("video_id"), str):
            continue
        source = inspect_source(entry["video_id"], data_root)
        items.append({
            "video_id": entry["video_id"],
            "rank": entry.get("rank"),
            "category": entry.get("category"),
            "title": entry.get("title"),
            "queue_terminal_state": terminal_states.get(entry["video_id"]),
            **source,
        })
    return {
        "schema_version": "1.0.0",
        "kind": "gold_source_inventory",
        "data_root": str(data_root),
        "priority_queue": str(queue_path),
        "total_episodes": len(items),
        "source_state_counts": dict(Counter(item["source_state"] for item in items)),
        "gold_extraction_count": sum(1 for item in items if item["gold_extraction_exists"]),
        "items": items,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--priority-queue", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    inventory = build_inventory(args.data_root, args.priority_queue)
    write_json(args.output, inventory)
    print(json.dumps({key: value for key, value in inventory.items() if key != "items"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
