"""Shared YouTube helpers for Marketing Swipe File scripts."""

from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(payload, file, ensure_ascii=True, indent=2)
        file.write("\n")


def read_text_url(url: str, timeout: int = 20) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def read_json_url(url: str, timeout: int = 20) -> dict[str, Any]:
    text = read_text_url(url, timeout=timeout)
    return json.loads(text)


def extract_video_id(url_or_id: str) -> str:
    value = url_or_id.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value

    parsed = urllib.parse.urlparse(value)
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")

    if "youtu.be" in host and path:
        return path.split("/")[0]
    if "youtube.com" in host:
        query = urllib.parse.parse_qs(parsed.query)
        if query.get("v"):
            return query["v"][0]
        if path.startswith("shorts/"):
            return path.split("/")[1]
        if path.startswith("live/"):
            return path.split("/")[1]
        if path.startswith("embed/"):
            return path.split("/")[1]

    raise ValueError(f"Could not extract YouTube video id from: {url_or_id}")


def canonical_watch_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def extract_balanced_json(text: str, start_index: int) -> dict[str, Any]:
    brace_start = text.find("{", start_index)
    if brace_start == -1:
        raise ValueError("Could not find JSON object start")

    depth = 0
    in_string = False
    escape = False
    for index in range(brace_start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[brace_start : index + 1])

    raise ValueError("Could not parse balanced JSON object")


def extract_initial_player_response(html_text: str) -> dict[str, Any] | None:
    for marker in ("ytInitialPlayerResponse =", "var ytInitialPlayerResponse ="):
        marker_index = html_text.find(marker)
        if marker_index != -1:
            try:
                return extract_balanced_json(html_text, marker_index + len(marker))
            except Exception:
                continue

    match = re.search(r"ytInitialPlayerResponse\"\s*:\s*({.+?})\s*,\s*\"html5player", html_text)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            return None
    return None


def oembed_metadata(video_id: str) -> dict[str, Any]:
    query = urllib.parse.urlencode({"url": canonical_watch_url(video_id), "format": "json"})
    return read_json_url(f"https://www.youtube.com/oembed?{query}")


def clean_html_text(value: str | None) -> str | None:
    if value is None:
        return None
    return html.unescape(value).strip()

