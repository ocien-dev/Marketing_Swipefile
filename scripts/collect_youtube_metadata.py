#!/usr/bin/env python
"""Collect YouTube metadata for Marketing Swipe File."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from msf_common import data_path
from youtube_common import (
    canonical_watch_url,
    clean_html_text,
    extract_initial_player_response,
    extract_video_id,
    oembed_metadata,
    read_text_url,
    utc_now,
    write_json,
)


def metadata_from_player_response(player_response: dict[str, Any]) -> dict[str, Any]:
    details = player_response.get("videoDetails", {}) or {}
    microformat = (player_response.get("microformat", {}) or {}).get("playerMicroformatRenderer", {}) or {}

    duration = details.get("lengthSeconds")
    try:
        duration_seconds = int(duration) if duration is not None else None
    except ValueError:
        duration_seconds = None

    published_at = None
    publish_date = microformat.get("publishDate") or microformat.get("uploadDate")
    if publish_date:
        published_at = f"{publish_date}T00:00:00Z"

    description = details.get("shortDescription")
    if description is None:
        description = microformat.get("description", {}).get("simpleText")

    return {
        "title": clean_html_text(details.get("title")),
        "channel_name": clean_html_text(details.get("author")),
        "channel_id": details.get("channelId"),
        "description": clean_html_text(description),
        "published_at": published_at,
        "duration_seconds": duration_seconds,
    }


def collect_metadata(url: str, source: str, notes: str | None = None) -> dict[str, Any]:
    video_id = extract_video_id(url)
    watch_url = canonical_watch_url(video_id)
    collected_at = utc_now()

    metadata: dict[str, Any] = {
        "schema_version": "1.0",
        "source": source,
        "youtube_video_id": video_id,
        "url": watch_url,
        "title": "",
        "channel_name": source,
        "channel_id": None,
        "description": None,
        "published_at": None,
        "duration_seconds": None,
        "language_original": None,
        "collected_at": collected_at,
        "processing_status": "pending",
        "transcript_status": "pending",
        "asset_detection_status": "pending",
        "notes": notes,
    }

    try:
        html_text = read_text_url(watch_url)
        player_response = extract_initial_player_response(html_text)
        if player_response:
            metadata.update({k: v for k, v in metadata_from_player_response(player_response).items() if v is not None})
    except Exception as error:
        metadata["notes"] = f"{notes or ''} metadata_player_response_error={error}".strip()

    if not metadata["title"]:
        try:
            oembed = oembed_metadata(video_id)
            metadata["title"] = clean_html_text(oembed.get("title")) or ""
            metadata["channel_name"] = clean_html_text(oembed.get("author_name")) or source
        except Exception as error:
            metadata["notes"] = f"{metadata.get('notes') or ''} metadata_oembed_error={error}".strip()

    if not metadata["title"]:
        metadata["title"] = f"YouTube video {video_id}"

    return metadata


def iter_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Single YouTube URL or video id")
    parser.add_argument("--source", default="VTurb", help="Source/channel name")
    parser.add_argument("--notes", default=None, help="Optional notes for a single URL")
    parser.add_argument("--csv", type=Path, help="CSV with youtube_url and channel_name columns")
    parser.add_argument("--output-root", default=data_path("raw", "youtube"), type=Path)
    args = parser.parse_args()

    rows: list[dict[str, str]]
    if args.csv:
        rows = iter_csv_rows(args.csv)
    elif args.url:
        rows = [{"youtube_url": args.url, "channel_name": args.source, "notes": args.notes or ""}]
    else:
        parser.error("Provide --url or --csv")

    count = 0
    for row in rows:
        url = row.get("youtube_url", "").strip()
        if not url or "REPLACE_WITH_REAL" in url:
            continue
        source = row.get("channel_name") or args.source
        notes = row.get("notes") or None
        metadata = collect_metadata(url, source=source, notes=notes)
        output_path = args.output_root / metadata["youtube_video_id"] / "metadata.json"
        write_json(output_path, metadata)
        print(f"Wrote metadata for {metadata['youtube_video_id']} to {output_path}")
        count += 1

    print(f"Processed {count} video(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
