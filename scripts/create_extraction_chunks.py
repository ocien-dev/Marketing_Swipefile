#!/usr/bin/env python
"""Split normalized content segments into extraction-sized chunks."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from youtube_common import utc_now, write_json


CHAPTER_RE = re.compile(r"^\s*(?P<time>\d{1,2}:\d{2}(?::\d{2})?)\s+(?P<title>.+?)\s*$")


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


def parse_chapters(description: str | None, duration_seconds: float | None) -> list[dict[str, Any]]:
    if not description:
        return []

    chapters: list[dict[str, Any]] = []
    seen_starts: set[float] = set()
    for line in description.splitlines():
        match = CHAPTER_RE.match(line)
        if not match:
            continue
        start_seconds = parse_timestamp(match.group("time"))
        if start_seconds in seen_starts:
            continue
        seen_starts.add(start_seconds)
        chapters.append(
            {
                "title": match.group("title").strip(),
                "start_seconds": start_seconds,
                "end_seconds": None,
            }
        )

    chapters.sort(key=lambda item: item["start_seconds"])
    for index, chapter in enumerate(chapters):
        if index + 1 < len(chapters):
            chapter["end_seconds"] = chapters[index + 1]["start_seconds"]
        else:
            chapter["end_seconds"] = duration_seconds
    return chapters


def segment_char_count(segment: dict[str, Any]) -> int:
    return len(str(segment.get("text_original", ""))) + 64


def segments_for_chapter(segments: list[dict[str, Any]], chapter: dict[str, Any]) -> list[dict[str, Any]]:
    start = chapter["start_seconds"]
    end = chapter.get("end_seconds")
    selected: list[dict[str, Any]] = []
    for segment in segments:
        segment_start = segment.get("start_seconds")
        if not isinstance(segment_start, (int, float)):
            continue
        if float(segment_start) < float(start):
            continue
        if isinstance(end, (int, float)) and float(segment_start) >= float(end):
            continue
        selected.append(segment)
    return selected


def split_segment_group(
    group_segments: list[dict[str, Any]],
    chapter_title: str,
    max_chars: int,
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    current_chars = 0
    part_index = 1

    def flush() -> None:
        nonlocal current, current_chars, part_index
        if not current:
            return
        start_seconds = current[0].get("start_seconds")
        end_seconds = current[-1].get("end_seconds") or current[-1].get("start_seconds")
        chunks.append(
            {
                "title": chapter_title if part_index == 1 else f"{chapter_title} - part {part_index}",
                "chapter_title": chapter_title,
                "part_index": part_index,
                "start_seconds": start_seconds,
                "end_seconds": end_seconds,
                "char_count": current_chars,
                "segments": current,
            }
        )
        current = []
        current_chars = 0
        part_index += 1

    for segment in group_segments:
        cost = segment_char_count(segment)
        if current and current_chars + cost > max_chars:
            flush()
        current.append(segment)
        current_chars += cost

    flush()
    return chunks


def build_chunks(segments_payload: dict[str, Any], metadata: dict[str, Any] | None, max_chars: int) -> list[dict[str, Any]]:
    segments = segments_payload.get("segments", [])
    duration_seconds = metadata.get("duration_seconds") if metadata else None
    chapters = parse_chapters(metadata.get("description") if metadata else None, duration_seconds)

    if not chapters:
        chapters = [
            {
                "title": "Episode transcript",
                "start_seconds": segments[0].get("start_seconds") if segments else None,
                "end_seconds": segments[-1].get("end_seconds") if segments else None,
            }
        ]
        chapter_segments = [(chapters[0], segments)]
    else:
        chapter_segments = [(chapter, segments_for_chapter(segments, chapter)) for chapter in chapters]

    chunks: list[dict[str, Any]] = []
    for chapter, selected_segments in chapter_segments:
        if not selected_segments:
            continue
        chunks.extend(split_segment_group(selected_segments, chapter["title"], max_chars))
    return chunks


def relative_to_cwd(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--segments", required=True, type=Path, help="Path to content_segments.json")
    parser.add_argument("--metadata", type=Path, help="Optional metadata.json with description chapters")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory for chunk files")
    parser.add_argument("--max-chars", default=50000, type=int, help="Approximate max characters per chunk")
    args = parser.parse_args()

    segments_payload = load_json(args.segments)
    metadata = load_json(args.metadata) if args.metadata else None
    video_id = segments_payload.get("episode_video_id") or (metadata or {}).get("youtube_video_id")
    if not video_id:
        raise ValueError("Could not determine episode video id")

    chunks = build_chunks(segments_payload, metadata, args.max_chars)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    index_chunks: list[dict[str, Any]] = []
    for chunk_index, chunk in enumerate(chunks):
        chunk_id = f"{video_id}-chunk-{chunk_index + 1:04d}"
        chunk_path = args.output_dir / f"chunk_{chunk_index + 1:03d}.json"
        chunk_payload = {
            "schema_version": segments_payload.get("schema_version", "1.0"),
            "episode_video_id": segments_payload.get("episode_video_id"),
            "asset_id": segments_payload.get("asset_id"),
            "source_kind": segments_payload.get("source_kind"),
            "language_original": segments_payload.get("language_original"),
            "segments": chunk["segments"],
        }
        write_json(chunk_path, chunk_payload)
        index_chunks.append(
            {
                "chunk_id": chunk_id,
                "chunk_index": chunk_index,
                "title": chunk["title"],
                "chapter_title": chunk["chapter_title"],
                "part_index": chunk["part_index"],
                "start_seconds": chunk["start_seconds"],
                "end_seconds": chunk["end_seconds"],
                "segment_count": len(chunk["segments"]),
                "char_count": chunk["char_count"],
                "file": relative_to_cwd(chunk_path),
            }
        )

    index_payload = {
        "schema_version": "1.0",
        "episode_video_id": video_id,
        "chunking_strategy": "metadata_chapters_then_max_chars",
        "max_chars": args.max_chars,
        "created_at": utc_now(),
        "chunks": index_chunks,
    }
    write_json(args.output_dir / "chunk_index.json", index_payload)
    print(f"Wrote {len(index_chunks)} chunk(s) to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
