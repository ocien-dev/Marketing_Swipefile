#!/usr/bin/env python
"""Discover public videos from the VTurb YouTube channel and optionally append them to the queue."""

from __future__ import annotations

import argparse
import csv
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from msf_common import data_path
from youtube_common import canonical_watch_url, extract_balanced_json


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

DEFAULT_CHANNEL_ID = "UCe83vpSONtz8Ex9viQH6nNg"
QUEUE_FIELDS = ["source_priority", "channel_name", "youtube_url", "episode_priority", "notes"]


def utc_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def read_url(url: str, timeout: int = 20) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def post_json(url: str, payload: dict[str, Any], client_version: str, timeout: int = 20) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "X-YouTube-Client-Name": "1",
            "X-YouTube-Client-Version": client_version,
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def extract_config(html_text: str) -> dict[str, Any]:
    marker = "ytcfg.set({"
    index = html_text.find(marker)
    if index == -1:
        raise ValueError("Could not find ytcfg config in YouTube channel page")
    return extract_balanced_json(html_text, index + len("ytcfg.set("))


def extract_initial_data(html_text: str) -> dict[str, Any]:
    for marker in ("var ytInitialData =", "ytInitialData ="):
        index = html_text.find(marker)
        if index != -1:
            return extract_balanced_json(html_text, index + len(marker))
    raise ValueError("Could not find ytInitialData in YouTube channel page")


def collect_ids_and_tokens(payload: Any) -> tuple[list[str], list[str]]:
    video_ids: list[str] = []
    continuation_tokens: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            video_id = value.get("videoId")
            if isinstance(video_id, str) and re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
                if video_id not in video_ids:
                    video_ids.append(video_id)
            command = value.get("continuationCommand")
            if isinstance(command, dict):
                token = command.get("token")
                if isinstance(token, str) and token and token not in continuation_tokens:
                    continuation_tokens.append(token)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    return video_ids, continuation_tokens


def discover_channel_videos(channel_id: str, max_videos: int, max_pages: int) -> list[str]:
    page_url = f"https://www.youtube.com/channel/{channel_id}/videos"
    html_text = read_url(page_url)
    config = extract_config(html_text)
    initial_data = extract_initial_data(html_text)
    video_ids, tokens = collect_ids_and_tokens(initial_data)

    api_url = f"https://www.youtube.com/youtubei/v1/browse?key={config['INNERTUBE_API_KEY']}"
    context = config["INNERTUBE_CONTEXT"]
    client_version = str(config["INNERTUBE_CLIENT_VERSION"])
    seen_tokens: set[str] = set()
    queue = list(tokens)

    while queue and len(video_ids) < max_videos and len(seen_tokens) < max_pages:
        token = queue.pop(0)
        if token in seen_tokens:
            continue
        seen_tokens.add(token)
        try:
            response = post_json(api_url, {"context": context, "continuation": token}, client_version=client_version)
        except Exception:
            continue
        page_video_ids, page_tokens = collect_ids_and_tokens(response)
        for video_id in page_video_ids:
            if video_id not in video_ids:
                video_ids.append(video_id)
                if len(video_ids) >= max_videos:
                    break
        for page_token in page_tokens:
            if page_token not in seen_tokens and page_token not in queue:
                queue.append(page_token)

    return video_ids[:max_videos]


def read_queue(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_queue(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=QUEUE_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_discovery_export(path: Path, video_ids: list[str], existing_urls: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["discovered_order", "video_id", "youtube_url", "already_in_queue"]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for index, video_id in enumerate(video_ids, start=1):
            url = canonical_watch_url(video_id)
            writer.writerow(
                {
                    "discovered_order": index,
                    "video_id": video_id,
                    "youtube_url": url,
                    "already_in_queue": "yes" if url in existing_urls else "no",
                }
            )


def append_to_queue(queue_path: Path, video_ids: list[str], limit: int | None, source_priority: str, channel_name: str) -> int:
    rows = read_queue(queue_path)
    existing_urls = {row.get("youtube_url", "").strip() for row in rows}
    priorities = []
    for row in rows:
        try:
            priorities.append(int(row.get("episode_priority") or 0))
        except ValueError:
            continue
    next_priority = max(priorities or [0]) + 1
    appended = 0
    note = f"Channel discovery {utc_date()} from VTurb channel {DEFAULT_CHANNEL_ID}"

    for video_id in video_ids:
        url = canonical_watch_url(video_id)
        if url in existing_urls:
            continue
        if limit is not None and appended >= limit:
            break
        rows.append(
            {
                "source_priority": source_priority,
                "channel_name": channel_name,
                "youtube_url": url,
                "episode_priority": str(next_priority),
                "notes": note,
            }
        )
        existing_urls.add(url)
        next_priority += 1
        appended += 1

    if appended:
        write_queue(queue_path, rows)
    return appended


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel-id", default=DEFAULT_CHANNEL_ID)
    parser.add_argument("--max-videos", default=160, type=int)
    parser.add_argument("--max-pages", default=40, type=int)
    parser.add_argument("--queue", default=data_path("input", "youtube_urls.csv"), type=Path)
    parser.add_argument("--output", default=data_path("exports", "vturb_channel_discovered_videos.csv"), type=Path)
    parser.add_argument("--append", action="store_true", help="Append discovered videos not already present in the queue")
    parser.add_argument("--append-limit", type=int, help="Maximum number of new queue rows to append")
    parser.add_argument("--source-priority", default="1")
    parser.add_argument("--channel-name", default="VTurb")
    args = parser.parse_args()

    discovered = discover_channel_videos(args.channel_id, max_videos=args.max_videos, max_pages=args.max_pages)
    existing_urls = {row.get("youtube_url", "").strip() for row in read_queue(args.queue)}
    write_discovery_export(args.output, discovered, existing_urls)

    appended = 0
    if args.append:
        appended = append_to_queue(
            args.queue,
            discovered,
            limit=args.append_limit,
            source_priority=args.source_priority,
            channel_name=args.channel_name,
        )

    print(f"Discovered {len(discovered)} channel video(s).")
    print(f"Wrote discovery export to {args.output}.")
    if args.append:
        print(f"Appended {appended} new video(s) to {args.queue}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
