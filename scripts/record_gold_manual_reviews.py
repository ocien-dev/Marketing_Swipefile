#!/usr/bin/env python
"""Record human-authored gold review decisions from JSON stdin or a file.

This command is intentionally a data recorder, not an extractor.  It converts
reviewer-selected segment IDs into transcript citations and writes one durable
review file per chunk, which the semantic builder can resume safely.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from scripts.gold_extraction_common import EXCLUSION_REASON_CODES, GoldPauseError, SCHEMA_VERSION, citation, load_json, write_json


def load_payload(path: str | None) -> dict[str, Any]:
    raw = Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()
    return json.loads(raw)


def record(video_id: str, data_root: Path, payload: dict[str, Any]) -> dict[str, int]:
    if payload.get("episode_video_id") not in {None, video_id}:
        raise ValueError("payload episode_video_id mismatch")
    out = data_root / "processed" / video_id / "gold_extraction"
    status = load_json(out / "gold_extraction_status.json")
    transcript = load_json(out / "transcript_clean.json")["segments"]
    segments = {item["segment_id"]: item for item in transcript}
    segments_by_index = {int(item["clean_index"]): item for item in transcript}
    chunks = {item["chunk_number"]: item for item in status["chunks"]}
    index_mode = payload.get("segment_index_mode")
    recorded = 0
    for raw_review in payload.get("reviews", []):
        number = int(raw_review["chunk_number"])
        chunk = chunks[number]
        candidates: list[dict[str, Any]] = []
        for raw_candidate in raw_review.get("candidates", []):
            candidate = dict(raw_candidate)
            minimal_ids = candidate.pop("minimal_segment_ids", [])
            support_ids = candidate.pop("support_segment_ids", [])
            all_ids = minimal_ids + support_ids
            if not minimal_ids:
                raise ValueError(f"{candidate.get('candidate_id', '<unknown>')}: minimal_segment_ids is required")
            resolved_ids: list[str] = []
            for segment_id in all_ids:
                suffix = str(segment_id).rsplit("-", 1)[-1]
                if index_mode == "zero_based" and suffix.isdigit() and int(suffix) in segments_by_index:
                    resolved_ids.append(segments_by_index[int(suffix)]["segment_id"])
                elif segment_id in segments:
                    resolved_ids.append(segment_id)
                elif suffix.isdigit() and int(suffix) in segments_by_index:
                    resolved_ids.append(segments_by_index[int(suffix)]["segment_id"])
                else:
                    resolved_ids.append(segment_id)
            minimal_ids = resolved_ids[:len(minimal_ids)]
            support_ids = resolved_ids[len(minimal_ids):]
            all_ids = minimal_ids + support_ids
            missing = [segment_id for segment_id in all_ids if segment_id not in segments]
            if missing:
                raise ValueError(f"{candidate.get('candidate_id', '<unknown>')}: unknown segments {missing}")
            citations = [citation(segments[segment_id]) for segment_id in all_ids]
            candidate["chunk_id"] = chunk["chunk_id"]
            candidate.setdefault("subthemes", [])
            candidate.setdefault("process_tags", [])
            candidate.setdefault("context", {"episode_video_id": video_id, "source_kind": "transcript"})
            candidate.setdefault("reported_case", False)
            candidate.setdefault("causal_certainty", "not_applicable")
            candidate.setdefault("claim_risk", "low")
            candidate.setdefault("numbers", [])
            candidate.setdefault("steps", [])
            candidate.setdefault("conditions", [])
            candidate.setdefault("caveats", [])
            candidate["evidence"] = {
                "minimal_quote": [citation(segments[segment_id]) for segment_id in minimal_ids],
                "context_range": {
                    "segment_start": min(segments[segment_id]["clean_index"] for segment_id in all_ids),
                    "segment_end": max(segments[segment_id]["clean_index"] for segment_id in all_ids),
                    "start_seconds": min(item["start_seconds"] for item in citations),
                    "end_seconds": max(item["end_seconds"] for item in citations),
                },
                "support_segments": [citation(segments[segment_id]) for segment_id in support_ids],
            }
            candidate.setdefault("relations", {"parent_candidate_id": None, "child_candidate_ids": []})
            candidates.append(candidate)
        ledger_decisions = raw_review.get("ledger_decisions", [])
        for decision in ledger_decisions:
            if decision.get("disposition") == "excluded" and decision.get("reason_code") not in EXCLUSION_REASON_CODES:
                raise ValueError(f"{chunk['chunk_id']}: excluded ledger decision needs a valid reason_code")
            if decision.get("reason_code") == "duplicate_of" and not decision.get("reason_reference"):
                raise ValueError(f"{chunk['chunk_id']}: duplicate_of needs reason_reference")
        review = {
            "schema_version": SCHEMA_VERSION, "episode_video_id": video_id,
            "chunk_id": chunk["chunk_id"], "input_hash": chunk["input_hash"],
            "review_route": "codex_manual_no_paid_api", "full_chunk_reviewed": True,
            "reviewer_effort_minutes": raw_review.get("reviewer_effort_minutes"),
            "candidates": candidates, "ledger_decisions": ledger_decisions,
        }
        write_json(out / "manual_reviews" / f"chunk_{number:03d}_review.json", review)
        recorded += 1
    return {"recorded_reviews": recorded}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--input", help="JSON file. Omit to read JSON from stdin.")
    args = parser.parse_args()
    try:
        result = record(args.video_id, args.data_root, load_payload(args.input))
    except (GoldPauseError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
