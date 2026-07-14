#!/usr/bin/env python
"""Record human-authored gold review decisions from JSON stdin or a file.

This command is intentionally a data recorder, not an extractor.  It converts
reviewer-selected segment IDs into transcript citations and writes one durable
review file per chunk, which the semantic builder can resume safely.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.gold_extraction_common import (
    EXCLUSION_REASON_CODES,
    GoldPauseError,
    SCHEMA_VERSION,
    citation,
    default_process_tags,
    editorial_ascii_errors,
    load_json,
    normalize_relations,
    record_operation_event,
    sha256_json,
    validate_candidate,
    write_json_batch,
)
from scripts.gold_review_compiler import compile_payload


def load_payload(path: str | None) -> dict[str, Any]:
    raw = Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()
    return json.loads(raw)


def _resolved_ids(
    raw_ids: list[Any],
    index_mode: str | None,
    segments: dict[str, dict[str, Any]],
    segments_by_index: dict[int, dict[str, Any]],
) -> list[str]:
    resolved: list[str] = []
    for raw_id in raw_ids:
        segment_id = str(raw_id)
        suffix = segment_id.rsplit("-", 1)[-1]
        if index_mode == "zero_based" and suffix.isdigit() and int(suffix) in segments_by_index:
            resolved.append(segments_by_index[int(suffix)]["segment_id"])
        elif segment_id in segments:
            resolved.append(segment_id)
        elif suffix.isdigit() and int(suffix) in segments_by_index:
            resolved.append(segments_by_index[int(suffix)]["segment_id"])
        else:
            resolved.append(segment_id)
    return resolved


def _review_draft(
    video_id: str,
    raw_review: dict[str, Any],
    chunk: dict[str, Any],
    segments: dict[str, dict[str, Any]],
    segments_by_index: dict[int, dict[str, Any]],
    index_mode: str | None,
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for raw_candidate in raw_review.get("candidates", []):
        candidate = dict(raw_candidate)
        minimal_ids = _resolved_ids(list(candidate.pop("minimal_segment_ids", [])), index_mode, segments, segments_by_index)
        support_ids = _resolved_ids(list(candidate.pop("support_segment_ids", [])), index_mode, segments, segments_by_index)
        all_ids = minimal_ids + support_ids
        if not minimal_ids:
            raise ValueError(f"{candidate.get('candidate_id', '<unknown>')}: minimal_segment_ids is required")
        missing = [segment_id for segment_id in all_ids if segment_id not in segments]
        if missing:
            raise ValueError(f"{candidate.get('candidate_id', '<unknown>')}: unknown segments {missing}")
        citations = [citation(segments[segment_id]) for segment_id in all_ids]
        candidate["chunk_id"] = chunk["chunk_id"]
        candidate.setdefault("subthemes", [])
        candidate.setdefault("process_tags", default_process_tags(candidate.get("themes") or []))
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
    ledger_decisions = list(raw_review.get("ledger_decisions", []))
    for decision in ledger_decisions:
        if decision.get("disposition") == "excluded" and decision.get("reason_code") not in EXCLUSION_REASON_CODES:
            raise ValueError(f"{chunk['chunk_id']}: excluded ledger decision needs a valid reason_code")
        if decision.get("reason_code") == "duplicate_of" and not decision.get("reason_reference"):
            raise ValueError(f"{chunk['chunk_id']}: duplicate_of needs reason_reference")
    return {
        "schema_version": SCHEMA_VERSION, "episode_video_id": video_id,
        "chunk_id": chunk["chunk_id"], "input_hash": chunk["input_hash"],
        "review_route": "codex_manual_no_paid_api", "full_chunk_reviewed": True,
        "reviewer_effort_minutes": raw_review.get("reviewer_effort_minutes"),
        "candidates": candidates, "ledger_decisions": ledger_decisions,
    }


def _batch_receipt_path(out: Path) -> Path:
    return out / "manual_review_batch_receipts.json"


def _receipt_matches(receipt: dict[str, Any], review_dir: Path) -> bool:
    hashes = receipt.get("review_hashes")
    if not isinstance(hashes, dict) or not hashes:
        return False
    for name, expected in hashes.items():
        path = review_dir / name
        if not path.exists() or sha256_json(load_json(path)) != expected:
            return False
    return True


def record(video_id: str, data_root: Path, payload: dict[str, Any], *, check: bool = False) -> dict[str, Any]:
    """Compile and atomically persist a review batch, with receipt recovery.

    The legacy draft helpers remain importable for job-local parity checks.  All
    recorder writes now flow through ``compile_payload`` so check and apply use
    the same normalization and complete validation inventory.
    """
    out = data_root / "processed" / video_id / "gold_extraction"
    status = load_json(out / "gold_extraction_status.json")
    transcript = load_json(out / "transcript_clean.json")["segments"]
    review_dir = out / "manual_reviews"
    existing = {path.name: load_json(path) for path in sorted(review_dir.glob("chunk_*_review.json"))}
    compiled = compile_payload(video_id, payload, status, transcript, copy.deepcopy(existing))
    if compiled["issues"]:
        if check:
            return {
                "status": "error",
                "mode": "check",
                "issues": compiled["issues"],
                "recorded_reviews": len(compiled["reviews"]),
                "candidate_count": compiled["candidate_count"],
                "semantic_sha256": compiled["semantic_sha256"],
            }
        details = "; ".join(
            f"{item['candidate_id']}:{item['field']}:{item['evidence']}"
            for item in compiled["issues"]
        )
        raise ValueError(f"review validation failed: {details}")
    if check:
        return {
            "status": "ok",
            "mode": "check",
            "recorded_reviews": len(compiled["reviews"]),
            "candidate_count": compiled["candidate_count"],
            "semantic_sha256": compiled["semantic_sha256"],
        }

    receipt_path = _batch_receipt_path(out)
    receipt_document = load_json(receipt_path) if receipt_path.exists() else {"batches": []}
    batches = receipt_document.get("batches", [])
    if not isinstance(batches, list):
        raise ValueError("manual review batch receipt has invalid batches")
    for prior in batches:
        if prior.get("semantic_sha256") == compiled["semantic_sha256"]:
            if _receipt_matches(prior, review_dir):
                return {
                    "status": "ok", "idempotent": True,
                    "recorded_reviews": len(compiled["reviews"]),
                    "candidate_count": compiled["candidate_count"],
                    "semantic_sha256": compiled["semantic_sha256"],
                }
            raise GoldPauseError("manual review receipt exists but review hashes do not match")

    drafts = compiled["review_paths"]
    normalized_existing = compiled["normalized_existing_reviews"]
    normalized_existing_writes = {
        name: review for name, review in normalized_existing.items()
        if name not in drafts and existing.get(name) != review
    }
    receipt_reviews = {**normalized_existing_writes, **drafts}
    review_hashes = {name: sha256_json(review) for name, review in receipt_reviews.items()}
    receipt_document["batches"] = [*batches, {
        "semantic_sha256": compiled["semantic_sha256"],
        "review_hashes": review_hashes,
        "review_count": len(drafts),
        "candidate_count": compiled["candidate_count"],
    }]
    writes = {
        review_dir / name: review
        for name, review in drafts.items()
        if existing.get(name) != review
    }
    writes.update({review_dir / name: review for name, review in normalized_existing_writes.items()})
    writes[receipt_path] = receipt_document
    write_json_batch(writes)
    record_operation_event(out, "review_batch", compiled["semantic_sha256"], {
        "recorded_reviews": len(drafts), "candidate_count": compiled["candidate_count"],
    })
    return {
        "status": "ok", "idempotent": False,
        "recorded_reviews": len(drafts), "written_reviews": len(writes) - 1,
        "candidate_count": compiled["candidate_count"], "semantic_sha256": compiled["semantic_sha256"],
        "normalized_existing_reviews": len(normalized_existing_writes),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--input", help="JSON file. Omit to read JSON from stdin.")
    parser.add_argument("--check", action="store_true", help="Compile and validate without writing.")
    args = parser.parse_args()
    try:
        result = record(args.video_id, args.data_root, load_payload(args.input), check=args.check)
    except (GoldPauseError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
