#!/usr/bin/env python
"""Normalize a raw transcript into Marketing Swipe File content segments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(payload, file, ensure_ascii=True, indent=2)
        file.write("\n")


def normalize_segment(video_id: str, source: dict[str, Any], index: int) -> dict[str, Any]:
    start_seconds = source.get("start_seconds")
    duration_seconds = source.get("duration_seconds")
    end_seconds = None
    if isinstance(start_seconds, (int, float)) and isinstance(duration_seconds, (int, float)):
        end_seconds = round(float(start_seconds) + float(duration_seconds), 3)

    return {
        "segment_id": f"{video_id}-transcript-{index + 1:04d}",
        "segment_index": index,
        "source_kind": "transcript",
        "start_seconds": start_seconds,
        "end_seconds": end_seconds,
        "page_number": None,
        "sheet_name": None,
        "cell_range": None,
        "slide_number": None,
        "section_title": None,
        "text_original": str(source.get("text", "")).strip(),
        "text_ptbr": None,
        "language": None,
    }


def normalize_transcript(payload: dict[str, Any]) -> dict[str, Any]:
    video_id = payload["youtube_video_id"]
    language = payload.get("language")
    segments = [
        normalize_segment(video_id, segment, index)
        for index, segment in enumerate(payload.get("segments", []))
        if str(segment.get("text", "")).strip()
    ]

    for segment in segments:
        segment["language"] = language

    return {
        "schema_version": "1.0",
        "episode_video_id": video_id,
        "asset_id": None,
        "source_kind": "transcript",
        "language_original": language,
        "segments": segments,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Path to transcript_original.json")
    parser.add_argument("--output", required=True, type=Path, help="Path to content_segments.json")
    args = parser.parse_args()

    payload = load_json(args.input)
    normalized = normalize_transcript(payload)
    write_json(args.output, normalized)
    print(f"Wrote {len(normalized['segments'])} segments to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
