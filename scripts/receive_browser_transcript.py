#!/usr/bin/env python3
"""Receive validated Chrome transcript segments into Linux-native staging."""

from __future__ import annotations

import argparse
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from scripts.backfill_vturb_transcripts import atomic_write_json
from scripts.prepare_baoyu_transcript_import import canonical_payload


VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


class CaptureHandler(BaseHTTPRequestHandler):
    server: "CaptureServer"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/capture":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length < 2 or length > self.server.maximum_bytes:
                raise ValueError("invalid payload length")
            request = json.loads(self.rfile.read(length).decode("utf-8"))
            if request.get("token") != self.server.token:
                raise PermissionError("invalid capture token")
            video_id = str(request.get("video_id") or "")
            language = str(request.get("language") or "").strip()
            segments = request.get("segments")
            if not VIDEO_ID_RE.fullmatch(video_id):
                raise ValueError("invalid video id")
            if not language or not isinstance(segments, list) or not segments:
                raise ValueError("language and segments are required")
            payload = canonical_payload(video_id, language, "chrome_transcript_panel", segments)
            if not payload["segments"]:
                raise ValueError("no valid transcript segments")
            target = self.server.output_dir / f"{video_id}.json"
            atomic_write_json(target, payload)
            response = {
                "status": "captured",
                "video_id": video_id,
                "language": language,
                "segments": len(payload["segments"]),
                "path": str(target),
            }
            self.server.captured += 1
            body = json.dumps(response, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except PermissionError as exc:
            self.send_error(403, str(exc))
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self.send_error(400, str(exc))


class CaptureServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], *, output_dir: Path, token: str, maximum_bytes: int):
        super().__init__(address, CaptureHandler)
        self.output_dir = output_dir
        self.token = token
        self.maximum_bytes = maximum_bytes
        self.captured = 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--token", required=True)
    parser.add_argument("--max-captures", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=float, default=600)
    parser.add_argument("--maximum-bytes", type=int, default=5_000_000)
    args = parser.parse_args()
    if args.max_captures < 1 or args.timeout_seconds <= 0:
        parser.error("max captures and timeout must be positive")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    server = CaptureServer(
        (args.host, args.port),
        output_dir=args.output_dir,
        token=args.token,
        maximum_bytes=args.maximum_bytes,
    )
    server.timeout = args.timeout_seconds
    while server.captured < args.max_captures:
        server.handle_request()
        if server.captured < args.max_captures and server.timeout <= 0:
            break
    print(json.dumps({"status": "complete", "captured": server.captured}, ensure_ascii=False))
    return 0 if server.captured == args.max_captures else 1


if __name__ == "__main__":
    raise SystemExit(main())
