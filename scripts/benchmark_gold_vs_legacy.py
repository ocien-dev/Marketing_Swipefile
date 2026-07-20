#!/usr/bin/env python
"""Read-only post-gold structural benchmark; never part of extraction or audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _item_count(value: Any) -> int | None:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        for key in ("insights", "items", "records"):
            if isinstance(value.get(key), list):
                return len(value[key])
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--legacy-file", required=True, type=Path)
    args = parser.parse_args()
    out = args.data_root / "processed" / args.video_id / "gold_extraction"
    status = json.loads((out / "gold_extraction_status.json").read_text(encoding="utf-8"))
    if status.get("status") not in {"awaiting_external_audit", "complete"}:
        raise SystemExit("gold packet must be frozen before a legacy benchmark")
    gold_path = out / "insights_exhaustive.json"
    if not gold_path.is_file() or not args.legacy_file.is_file():
        raise SystemExit("gold or legacy benchmark input is missing")
    gold = json.loads(gold_path.read_text(encoding="utf-8"))
    legacy = json.loads(args.legacy_file.read_text(encoding="utf-8"))
    result = {
        "mode": "read_only_post_gold_benchmark",
        "episode_video_id": args.video_id,
        "gold": {"path": str(gold_path), "sha256": _sha256(gold_path), "bytes": gold_path.stat().st_size, "items": _item_count(gold)},
        "legacy": {"path": str(args.legacy_file), "sha256": _sha256(args.legacy_file), "bytes": args.legacy_file.stat().st_size, "items": _item_count(legacy)},
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
