#!/usr/bin/env python
"""Create a human decision queue for conservative gold semantic duplicates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.gold_extraction_common import build_dedupe_queue, load_json, now, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--data-root", required=True, type=Path)
    args = parser.parse_args()
    out = args.data_root / "processed" / args.video_id / "gold_extraction"
    candidates = load_json(out / "insights_exhaustive.json").get("insights", [])
    queue = build_dedupe_queue(candidates)
    payload = {
        "episode_video_id": args.video_id, "generated_at": now(),
        "policy": "Human reviewer must choose merge, keep_separate, or parent_child for every queued pair before an episode can be externally audited.",
        "queue": queue,
    }
    write_json(out / "dedupe_decision_queue.json", payload)
    print(json.dumps({"queue_items": len(queue)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
