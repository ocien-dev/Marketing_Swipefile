#!/usr/bin/env python
"""Synchronize the public VTurb podcast catalog with the extraction queue."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.gold_episode_priority import CATEGORY_ORDER, classify_episode
from scripts.msf_common import data_path
from scripts.youtube_common import canonical_watch_url, extract_balanced_json, extract_video_id


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

DEFAULT_CHANNEL_ID = "UCe83vpSONtz8Ex9viQH6nNg"
PODCAST_TITLE_PATTERN = re.compile(r"(?:segredos\s+da\s+escala|(?<![a-z0-9])sde\s*#?\s*\d+)", re.IGNORECASE)
QUEUE_FIELDS = [
    "source_priority",
    "channel_name",
    "youtube_url",
    "episode_priority",
    "notes",
    "video_id",
    "title",
    "duration_seconds",
    "category",
    "category_label",
    "discovered_order",
    "published_time_text",
    "last_seen_at",
]


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


def _text(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    simple = value.get("simpleText")
    if isinstance(simple, str):
        return simple.strip()
    runs = value.get("runs")
    if isinstance(runs, list):
        return "".join(str(item.get("text") or "") for item in runs if isinstance(item, dict)).strip()
    return ""


def duration_seconds(value: str | None) -> int:
    parts = str(value or "").strip().split(":")
    if not parts or any(not part.isdigit() for part in parts):
        return 0
    total = 0
    for part in parts:
        total = (total * 60) + int(part)
    return total


def _nested(value: Any, *keys: Any) -> Any:
    current = value
    for key in keys:
        if isinstance(key, int) and isinstance(current, list) and len(current) > key:
            current = current[key]
        elif isinstance(key, str) and isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current


def _lockup_record(value: dict[str, Any]) -> dict[str, Any] | None:
    video_id = value.get("contentId")
    if (
        value.get("contentType") != "LOCKUP_CONTENT_TYPE_VIDEO"
        or not isinstance(video_id, str)
        or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id)
    ):
        return None
    title = _nested(value, "metadata", "lockupMetadataViewModel", "title", "content")
    duration_text = _nested(
        value,
        "contentImage",
        "thumbnailViewModel",
        "overlays",
        0,
        "thumbnailBottomOverlayViewModel",
        "badges",
        0,
        "thumbnailBadgeViewModel",
        "text",
    )
    metadata_parts = _nested(
        value,
        "metadata",
        "lockupMetadataViewModel",
        "metadata",
        "contentMetadataViewModel",
        "metadataRows",
        0,
        "metadataParts",
    )
    published = ""
    if isinstance(metadata_parts, list):
        for part in reversed(metadata_parts):
            candidate = _nested(part, "text", "content")
            if isinstance(candidate, str) and candidate:
                published = candidate
                break
    return {
        "video_id": video_id,
        "youtube_url": canonical_watch_url(video_id),
        "title": str(title or "").strip(),
        "duration_text": str(duration_text or "").strip(),
        "duration_seconds": duration_seconds(str(duration_text or "")),
        "published_time_text": published,
    }


def collect_records_and_tokens(payload: Any) -> tuple[list[dict[str, Any]], list[str]]:
    """Collect public video IDs plus any renderer metadata in payload order."""
    records: list[dict[str, Any]] = []
    continuation_tokens: list[str] = []
    record_by_id: dict[str, dict[str, Any]] = {}

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            lockup = _lockup_record(value)
            video_id = lockup.get("video_id") if lockup else value.get("videoId")
            title = str(lockup.get("title") or "") if lockup else _text(value.get("title"))
            if isinstance(video_id, str) and re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
                duration_text = str(lockup.get("duration_text") or "") if lockup else _text(value.get("lengthText"))
                candidate = lockup or {
                    "video_id": video_id,
                    "youtube_url": canonical_watch_url(video_id),
                    "title": title,
                    "duration_text": duration_text,
                    "duration_seconds": duration_seconds(duration_text),
                    "published_time_text": _text(value.get("publishedTimeText")),
                }
                previous = record_by_id.get(video_id)
                if previous is None:
                    records.append(candidate)
                    record_by_id[video_id] = candidate
                else:
                    for key in ("title", "duration_text", "duration_seconds", "published_time_text"):
                        if not previous.get(key) and candidate.get(key):
                            previous[key] = candidate[key]
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
    return records, continuation_tokens


def extract_player_details(html_text: str, video_id: str) -> dict[str, Any]:
    player = None
    for marker in ("var ytInitialPlayerResponse =", "ytInitialPlayerResponse ="):
        index = html_text.find(marker)
        if index != -1:
            player = extract_balanced_json(html_text, index + len(marker))
            break
    if not isinstance(player, dict):
        raise ValueError(f"Could not find player details for {video_id}")
    details = player.get("videoDetails") if isinstance(player.get("videoDetails"), dict) else {}
    microformat = player.get("microformat") if isinstance(player.get("microformat"), dict) else {}
    renderer = microformat.get("playerMicroformatRenderer") if isinstance(microformat.get("playerMicroformatRenderer"), dict) else {}
    seconds = int(details.get("lengthSeconds") or 0)
    return {
        "video_id": video_id,
        "youtube_url": canonical_watch_url(video_id),
        "title": str(details.get("title") or "").strip(),
        "duration_text": "",
        "duration_seconds": seconds,
        "published_time_text": str(renderer.get("publishDate") or renderer.get("uploadDate") or "").strip(),
    }


def fetch_player_details(video_id: str) -> dict[str, Any]:
    return extract_player_details(read_url(canonical_watch_url(video_id)), video_id)


def hydrate_catalog_details(records: list[dict[str, Any]], workers: int = 8) -> int:
    pending = [item for item in records if not item.get("title") or not item.get("duration_seconds")]
    if not pending:
        return 0
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        details = list(executor.map(fetch_player_details, [str(item["video_id"]) for item in pending]))
    by_id = {str(item["video_id"]): item for item in details}
    for record in pending:
        detail = by_id[str(record["video_id"])]
        for key in ("title", "duration_text", "duration_seconds", "published_time_text"):
            if not record.get(key) and detail.get(key):
                record[key] = detail[key]
    missing = [str(item["video_id"]) for item in records if not item.get("title") or not item.get("duration_seconds")]
    if missing:
        raise ValueError(f"Catalog metadata incomplete for {len(missing)} video(s): {', '.join(missing[:5])}")
    return len(pending)


def discover_channel_catalog(channel_id: str, max_videos: int, max_pages: int, detail_workers: int = 8) -> dict[str, Any]:
    page_url = f"https://www.youtube.com/channel/{channel_id}/videos"
    html_text = read_url(page_url)
    config = extract_config(html_text)
    initial_data = extract_initial_data(html_text)
    records, tokens = collect_records_and_tokens(initial_data)

    api_url = f"https://www.youtube.com/youtubei/v1/browse?key={config['INNERTUBE_API_KEY']}"
    context = config["INNERTUBE_CONTEXT"]
    client_version = str(config["INNERTUBE_CLIENT_VERSION"])
    seen_tokens: set[str] = set()
    queued_tokens = list(tokens)
    seen_video_ids = {item["video_id"] for item in records}

    while queued_tokens and len(records) < max_videos and len(seen_tokens) < max_pages:
        token = queued_tokens.pop(0)
        if token in seen_tokens:
            continue
        seen_tokens.add(token)
        response = post_json(api_url, {"context": context, "continuation": token}, client_version=client_version)
        page_records, page_tokens = collect_records_and_tokens(response)
        for record in page_records:
            if record["video_id"] not in seen_video_ids:
                records.append(record)
                seen_video_ids.add(record["video_id"])
                if len(records) >= max_videos:
                    break
        for page_token in page_tokens:
            if page_token not in seen_tokens and page_token not in queued_tokens:
                queued_tokens.append(page_token)

    for index, record in enumerate(records[:max_videos], start=1):
        record["discovered_order"] = index
    selected = records[:max_videos]
    hydrated = hydrate_catalog_details(selected, workers=detail_workers)
    return {
        "records": selected,
        "pages_fetched": len(seen_tokens),
        "continuations_seen": len(seen_tokens),
        "pagination_complete": not queued_tokens and len(records) < max_videos,
        "hydrated_records": hydrated,
    }


def is_podcast_episode(record: dict[str, Any]) -> bool:
    return bool(PODCAST_TITLE_PATTERN.search(str(record.get("title") or "")))


def classify_catalog(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classified = []
    for record in records:
        item = {**record, **classify_episode(str(record.get("title") or ""))}
        classified.append(item)
    return classified


def priority_key(record: dict[str, Any]) -> tuple[int, float, int, str]:
    category = str(record.get("category") or "other")
    duration = int(record.get("duration_seconds") or 0)
    discovered_order = int(record.get("discovered_order") or 0)
    return (
        CATEGORY_ORDER.index(category) if category in CATEGORY_ORDER else len(CATEGORY_ORDER),
        float(duration) if duration > 0 else float("inf"),
        discovered_order if discovered_order > 0 else 10**9,
        str(record.get("video_id") or ""),
    )


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
        writer.writerows(rows)


def _row_video_id(row: dict[str, Any]) -> str:
    explicit = str(row.get("video_id") or "").strip()
    if explicit:
        return explicit
    try:
        return extract_video_id(str(row.get("youtube_url") or ""))
    except ValueError:
        return ""


def synchronize_queue(
    queue_path: Path,
    catalog: list[dict[str, Any]],
    *,
    source_priority: str,
    channel_name: str,
    full_catalog: bool = True,
) -> dict[str, int]:
    """Merge catalog rows and make classification order authoritative."""
    existing_rows = read_queue(queue_path)
    existing_by_id = {_row_video_id(row): row for row in existing_rows if _row_video_id(row)}
    catalog_ids = {str(item["video_id"]) for item in catalog}
    if not full_catalog:
        merged_catalog: dict[str, dict[str, Any]] = {}
        for row in existing_rows:
            video_id = _row_video_id(row)
            if not video_id:
                continue
            merged_catalog[video_id] = {
                "video_id": video_id,
                "youtube_url": row.get("youtube_url") or canonical_watch_url(video_id),
                "title": row.get("title") or video_id,
                "duration_seconds": row.get("duration_seconds") or 0,
                "category": row.get("category") or "other",
                "category_label": row.get("category_label") or "Outros",
                "discovered_order": row.get("discovered_order") or 0,
                "published_time_text": row.get("published_time_text") or "",
            }
        for item in catalog:
            merged_catalog[str(item["video_id"])] = item
        catalog = list(merged_catalog.values())
    today = utc_date()
    ordered_rows: list[dict[str, Any]] = []
    added = 0
    updated = 0

    for item in sorted(catalog, key=priority_key):
        video_id = str(item["video_id"])
        previous = existing_by_id.get(video_id, {})
        if previous:
            updated += 1
        else:
            added += 1
        ordered_rows.append(
            {
                **previous,
                "source_priority": previous.get("source_priority") or source_priority,
                "channel_name": previous.get("channel_name") or channel_name,
                "youtube_url": canonical_watch_url(video_id),
                "notes": previous.get("notes") or f"VTurb public podcast catalog sync {today}",
                "video_id": video_id,
                "title": item.get("title") or previous.get("title") or "",
                "duration_seconds": item.get("duration_seconds") or previous.get("duration_seconds") or "",
                "category": item.get("category") or "other",
                "category_label": item.get("category_label") or "Outros",
                "discovered_order": item.get("discovered_order") or "",
                "published_time_text": item.get("published_time_text") or "",
                "last_seen_at": today,
            }
        )

    effective_catalog_ids = {str(item["video_id"]) for item in catalog}
    preserved = [row for row in existing_rows if _row_video_id(row) not in effective_catalog_ids]
    ordered_rows.extend(preserved)
    for rank, row in enumerate(ordered_rows, start=1):
        row["episode_priority"] = str(rank)
    write_queue(queue_path, ordered_rows)
    return {
        "added": len([video_id for video_id in catalog_ids if video_id not in existing_by_id]),
        "updated": len([video_id for video_id in catalog_ids if video_id in existing_by_id]),
        "preserved": len(preserved),
        "queue_total": len(ordered_rows),
    }


def write_discovery_export(path: Path, catalog: list[dict[str, Any]], existing_ids: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "priority_rank",
        "discovered_order",
        "video_id",
        "youtube_url",
        "title",
        "duration_seconds",
        "duration_text",
        "published_time_text",
        "category",
        "category_label",
        "already_in_queue",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for rank, item in enumerate(sorted(catalog, key=priority_key), start=1):
            writer.writerow({**item, "priority_rank": rank, "already_in_queue": "yes" if item["video_id"] in existing_ids else "no"})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel-id", default=DEFAULT_CHANNEL_ID)
    parser.add_argument("--max-videos", default=500, type=int)
    parser.add_argument("--max-pages", default=80, type=int)
    parser.add_argument("--detail-workers", default=8, type=int)
    parser.add_argument("--recent-limit", type=int, help="Incremental scan of only the newest N public videos")
    parser.add_argument("--catalog-input", type=Path, help="Use a previously verified full catalog without fetching channel pages")
    parser.add_argument("--podcast-only", action="store_true", help="Legacy filter; default is every public channel video")
    parser.add_argument("--queue", default=data_path("input", "youtube_urls.csv"), type=Path)
    parser.add_argument("--output", default=data_path("exports", "vturb_podcast_catalog.csv"), type=Path)
    parser.add_argument("--sync-queue", action="store_true", help="Merge and reprioritize the extraction queue")
    parser.add_argument("--source-priority", default="1")
    parser.add_argument("--channel-name", default="VTurb")
    args = parser.parse_args()

    if args.recent_limit is not None and args.recent_limit < 1:
        parser.error("--recent-limit must be at least 1")
    if args.recent_limit is not None and args.catalog_input is not None:
        parser.error("--recent-limit and --catalog-input are mutually exclusive")
    if args.catalog_input is not None:
        with args.catalog_input.open("r", encoding="utf-8-sig", newline="") as file:
            input_records = list(csv.DictReader(file))
        discovery = {
            "records": input_records,
            "pages_fetched": 0,
            "continuations_seen": 0,
            "pagination_complete": True,
            "hydrated_records": 0,
        }
    else:
        discovery = discover_channel_catalog(
            args.channel_id,
            max_videos=args.recent_limit or args.max_videos,
            max_pages=args.max_pages,
            detail_workers=args.detail_workers,
        )
    discovered = discovery["records"]
    selected = [item for item in discovered if is_podcast_episode(item)] if args.podcast_only else discovered
    catalog = classify_catalog(selected)
    existing_ids = {_row_video_id(row) for row in read_queue(args.queue)}
    incremental_complete = args.recent_limit is not None and len(discovered) == args.recent_limit
    if not discovery["pagination_complete"] and not incremental_complete:
        print(json.dumps({
            "status": "incomplete_pagination",
            "discovered_channel_videos": len(discovered),
            "pages_fetched": discovery["pages_fetched"],
            "queue_updated": False,
        }, ensure_ascii=False))
        return 2
    write_discovery_export(args.output, catalog, existing_ids)

    sync_result: dict[str, int] | None = None
    if args.sync_queue:
        sync_result = synchronize_queue(
            args.queue,
            catalog,
            source_priority=args.source_priority,
            channel_name=args.channel_name,
            full_catalog=args.recent_limit is None,
        )

    print(json.dumps({
        "status": "ok",
        "discovered_channel_videos": len(discovered),
        "catalog_videos": len(catalog),
        "numbered_or_named_podcast_videos": sum(1 for item in discovered if is_podcast_episode(item)),
        "pages_fetched": discovery["pages_fetched"],
        "pagination_complete": discovery["pagination_complete"],
        "scan_mode": "catalog_input" if args.catalog_input is not None else "recent" if args.recent_limit is not None else "full",
        "recent_limit": args.recent_limit,
        "hydrated_records": discovery["hydrated_records"],
        "output": str(args.output),
        "queue_updated": bool(args.sync_queue),
        "queue": str(args.queue),
        "sync": sync_result,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
