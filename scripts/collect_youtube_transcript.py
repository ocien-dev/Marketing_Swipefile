#!/usr/bin/env python
"""Collect YouTube automatic transcript when caption tracks are available."""

from __future__ import annotations

import argparse
import json
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from youtube_common import (
    canonical_watch_url,
    extract_initial_player_response,
    extract_video_id,
    read_text_url,
    utc_now,
    write_json,
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def find_caption_tracks(player_response: dict[str, Any]) -> list[dict[str, Any]]:
    captions = player_response.get("captions", {}) or {}
    renderer = captions.get("playerCaptionsTracklistRenderer", {}) or {}
    return renderer.get("captionTracks", []) or []


def choose_caption_track(tracks: list[dict[str, Any]], preferred_languages: list[str]) -> dict[str, Any] | None:
    if not tracks:
        return None

    for preferred in preferred_languages:
        preferred_lower = preferred.lower()
        for track in tracks:
            language_code = str(track.get("languageCode", "")).lower()
            if language_code == preferred_lower or language_code.startswith(preferred_lower.split("-")[0]):
                return track

    return tracks[0]


def fetch_transcript_text(base_url: str, fmt: str) -> str:
    separator = "&" if "?" in base_url else "?"
    url = base_url
    if "fmt=" not in base_url:
        url = f"{base_url}{separator}fmt={fmt}"
    return read_text_url(url)


def parse_transcript_json3(json_text: str) -> list[dict[str, Any]]:
    payload = json.loads(json_text)
    segments: list[dict[str, Any]] = []
    for index, event in enumerate(payload.get("events", [])):
        text_parts = event.get("segs") or []
        text = "".join(part.get("utf8", "") for part in text_parts).strip()
        if not text:
            continue
        start_ms = event.get("tStartMs", 0)
        duration_ms = event.get("dDurationMs")
        segments.append(
            {
                "index": index,
                "start_seconds": round(float(start_ms) / 1000, 3),
                "duration_seconds": round(float(duration_ms) / 1000, 3) if duration_ms is not None else None,
                "text": text,
            }
        )
    return segments


def parse_transcript_xml(xml_text: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    segments: list[dict[str, Any]] = []
    for index, text_element in enumerate(root.iter("text")):
        start = float(text_element.attrib.get("start", 0))
        duration = float(text_element.attrib.get("dur", 0)) if "dur" in text_element.attrib else None
        text = "".join(text_element.itertext()).strip()
        if not text:
            continue
        segments.append(
            {
                "index": index,
                "start_seconds": start,
                "duration_seconds": duration,
                "text": text,
            }
        )
    return segments


def collect_transcript(video_id: str, preferred_languages: list[str]) -> dict[str, Any]:
    watch_url = canonical_watch_url(video_id)
    html_text = read_text_url(watch_url)
    player_response = extract_initial_player_response(html_text)
    if not player_response:
        return empty_transcript(video_id, "player_response_missing")

    tracks = find_caption_tracks(player_response)
    track = choose_caption_track(tracks, preferred_languages)
    if not track:
        return empty_transcript(video_id, "caption_tracks_missing")

    try:
        json_text = fetch_transcript_text(track["baseUrl"], "json3")
        segments = parse_transcript_json3(json_text)
        if not segments:
            xml_text = fetch_transcript_text(track["baseUrl"], "srv3")
            segments = parse_transcript_xml(xml_text)
    except Exception as error:
        payload = empty_transcript(video_id, f"caption_fetch_error={error}")
        payload["language"] = track.get("languageCode")
        return payload

    return {
        "schema_version": "1.0",
        "youtube_video_id": video_id,
        "source_kind": "transcript",
        "language": track.get("languageCode"),
        "provider": "youtube_caption_track",
        "collected_at": utc_now(),
        "segments": segments,
    }


def empty_transcript(video_id: str, reason: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "youtube_video_id": video_id,
        "source_kind": "transcript",
        "language": None,
        "provider": f"missing:{reason}",
        "collected_at": utc_now(),
        "segments": [],
    }


def video_id_from_args(url: str | None, metadata: Path | None) -> str:
    if metadata:
        payload = load_json(metadata)
        return payload["youtube_video_id"]
    if not url:
        raise ValueError("Provide --url or --metadata")
    return extract_video_id(url)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="YouTube URL or video id")
    parser.add_argument("--metadata", type=Path, help="Path to metadata.json")
    parser.add_argument("--output", type=Path, help="Path to transcript_original.json")
    parser.add_argument("--output-root", default=Path("data/raw/youtube"), type=Path)
    parser.add_argument("--languages", default="pt-BR,pt,en,es", help="Comma-separated preferred language order")
    args = parser.parse_args()

    video_id = video_id_from_args(args.url, args.metadata)
    languages = [language.strip() for language in args.languages.split(",") if language.strip()]
    payload = collect_transcript(video_id, languages)
    output_path = args.output or args.output_root / video_id / "transcript_original.json"
    write_json(output_path, payload)

    print(f"Wrote {len(payload['segments'])} transcript segment(s) to {output_path}")
    if not payload["segments"]:
        print(f"Transcript unavailable or empty. Provider status: {payload['provider']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
