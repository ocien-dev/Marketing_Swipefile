#!/usr/bin/env python
"""Extract a YouTube transcript from a Playwright CLI snapshot."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from msf_common import data_path
from youtube_common import extract_video_id, utc_now, write_json


TIMESTAMP_RE = re.compile(r"^\s+- generic \[ref=[^\]]+\]: (?P<time>\d{1,2}:\d{2}(?::\d{2})?)\s*$")
TEXT_RE = re.compile(r"^\s+- text: (?P<text>.*)$")
TOP_LEVEL_GENERIC_RE = re.compile(r"^      - generic \[ref=[^\]]+\]:")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def parse_timestamp(value: str) -> float:
    parts = [int(part) for part in value.split(":")]
    if len(parts) == 2:
        minutes, seconds = parts
        return float(minutes * 60 + seconds)
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return float(hours * 3600 + minutes * 60 + seconds)
    raise ValueError(f"Unsupported timestamp: {value}")


def parse_snapshot_scalar(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        return ""

    if stripped.startswith('"') and stripped.endswith('"'):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return stripped[1:-1]

    if stripped.startswith("'") and stripped.endswith("'"):
        return stripped[1:-1].replace("''", "'")

    return stripped


def transcript_window(lines: list[str]) -> list[str]:
    start_index = None
    for index, line in enumerate(lines):
        if "Pesquisar transcrição" in line or "Pesquisar transcri" in line:
            start_index = index
            break

    if start_index is None:
        raise ValueError("Could not find transcript panel marker in snapshot")

    end_index = len(lines)
    for index in range(start_index + 1, len(lines)):
        if TOP_LEVEL_GENERIC_RE.match(lines[index]):
            end_index = index
            break

    return lines[start_index:end_index]


def extract_segments(snapshot_text: str) -> list[dict[str, Any]]:
    lines = transcript_window(snapshot_text.splitlines())
    raw_segments: list[dict[str, Any]] = []
    current_timestamp: str | None = None

    for line in lines:
        timestamp_match = TIMESTAMP_RE.match(line)
        if timestamp_match:
            current_timestamp = timestamp_match.group("time")
            continue

        if current_timestamp is None:
            continue

        text_match = TEXT_RE.match(line)
        if not text_match:
            continue

        text = parse_snapshot_scalar(text_match.group("text")).strip()
        if not text:
            continue

        raw_segments.append(
            {
                "index": len(raw_segments),
                "start_seconds": parse_timestamp(current_timestamp),
                "duration_seconds": None,
                "text": text,
            }
        )
        current_timestamp = None

    for index, segment in enumerate(raw_segments[:-1]):
        next_start = raw_segments[index + 1]["start_seconds"]
        duration = max(0.0, float(next_start) - float(segment["start_seconds"]))
        segment["duration_seconds"] = round(duration, 3)

    return raw_segments


def video_id_from_args(url: str | None, metadata: Path | None, video_id: str | None) -> str:
    if video_id:
        return video_id
    if metadata:
        payload = load_json(metadata)
        return payload["youtube_video_id"]
    if url:
        return extract_video_id(url)
    raise ValueError("Provide --video-id, --url, or --metadata")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, type=Path, help="Playwright CLI YAML snapshot path")
    parser.add_argument("--metadata", type=Path, help="Path to metadata.json")
    parser.add_argument("--url", help="YouTube URL or video id")
    parser.add_argument("--video-id", help="YouTube video id")
    parser.add_argument("--language", default="pt", help="Transcript language code")
    parser.add_argument("--output", type=Path, help="Path to transcript_original.json")
    parser.add_argument("--output-root", default=data_path("raw", "youtube"), type=Path)
    args = parser.parse_args()

    video_id = video_id_from_args(args.url, args.metadata, args.video_id)
    snapshot_text = args.snapshot.read_text(encoding="utf-8")
    segments = extract_segments(snapshot_text)

    payload = {
        "schema_version": "1.0",
        "youtube_video_id": video_id,
        "source_kind": "transcript",
        "language": args.language,
        "provider": "youtube_ui_playwright_snapshot",
        "collected_at": utc_now(),
        "segments": segments,
    }

    output_path = args.output or args.output_root / video_id / "transcript_original.json"
    write_json(output_path, payload)
    print(f"Wrote {len(segments)} transcript segment(s) to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
