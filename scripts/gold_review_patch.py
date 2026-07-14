#!/usr/bin/env python
"""Apply a declared gold-review correction transactionally.

The manifest is intentionally narrow: assertions protect the prior state,
inserts happen before relations, and an applied manifest hash cannot run twice.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from scripts.gold_extraction_common import (
    EXCLUSION_REASON_CODES,
    GoldPauseError,
    calibration_coverage,
    editorial_ascii_errors,
    load_json,
    normalize_relations,
    record_operation_event,
    sha256_json,
    validate_candidate,
    write_json_batch,
)


def _path_value(value: dict[str, Any], path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise ValueError(f"missing asserted path {path}")
        current = current[part]
    return current


def _set_path(value: dict[str, Any], path: str, replacement: Any) -> None:
    parts = path.split(".")
    current: dict[str, Any] = value
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            raise ValueError(f"cannot set missing path {path}")
        current = current[part]
    current[parts[-1]] = replacement


def _load_reviews(out: Path) -> tuple[dict[Path, dict[str, Any]], dict[str, tuple[Path, dict[str, Any]]]]:
    reviews: dict[Path, dict[str, Any]] = {}
    candidates: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in sorted((out / "manual_reviews").glob("chunk_*_review.json")):
        review = load_json(path)
        for candidate in review.get("candidates", []):
            candidate_id = candidate.get("candidate_id")
            if not candidate_id or candidate_id in candidates:
                raise ValueError(f"duplicate or missing candidate_id in reviews: {candidate_id}")
            candidates[candidate_id] = (path, candidate)
        reviews[path] = review
    return reviews, candidates


def _assert_reviews(manifest: dict[str, Any], reviews: dict[Path, dict[str, Any]]) -> None:
    by_number = {int(path.name.split("_")[1]): review for path, review in reviews.items()}
    for assertion in manifest.get("review_assertions", []):
        review = by_number.get(int(assertion["chunk_number"]))
        if review is None:
            raise ValueError(f"missing asserted chunk {assertion['chunk_number']}")
        for key in ("chunk_id", "input_hash"):
            if key in assertion and review.get(key) != assertion[key]:
                raise ValueError(f"review assertion failed for chunk {assertion['chunk_number']}: {key}")
        if "candidate_ids" in assertion:
            actual = [item.get("candidate_id") for item in review.get("candidates", [])]
            if actual != assertion["candidate_ids"]:
                raise ValueError(f"review assertion failed for chunk {assertion['chunk_number']}: candidate_ids")


def _validate_ledger_decisions(review: dict[str, Any]) -> None:
    for decision in review.get("ledger_decisions", []):
        if decision.get("disposition") == "excluded" and decision.get("reason_code") not in EXCLUSION_REASON_CODES:
            raise ValueError(f"{review.get('chunk_id')}: excluded ledger decision needs a valid reason_code")
        if decision.get("reason_code") == "duplicate_of" and not decision.get("reason_reference"):
            raise ValueError(f"{review.get('chunk_id')}: duplicate_of needs reason_reference")


def _has_review_guard(manifest: dict[str, Any], chunk_number: int) -> bool:
    for assertion in manifest.get("review_assertions", []):
        if int(assertion.get("chunk_number", -1)) == chunk_number and {"chunk_id", "input_hash", "candidate_ids"} <= set(assertion):
            return True
    return False


def _validate_final_ledger(
    reviews: dict[Path, dict[str, Any]],
    segments_by_id: dict[str, dict[str, Any]],
    candidate_ids: set[str],
) -> None:
    seen_segments: set[str] = set()
    valid_dispositions = {"captured", "merged", "excluded"}
    for review in reviews.values():
        for decision in review.get("ledger_decisions", []):
            disposition = decision.get("disposition")
            segment_id = decision.get("segment_id")
            if disposition not in valid_dispositions:
                raise ValueError(f"{review.get('chunk_id')}: invalid ledger disposition")
            if not segment_id or segment_id not in segments_by_id:
                raise ValueError(f"{review.get('chunk_id')}: ledger segment_id is missing or unknown")
            if segment_id in seen_segments:
                raise ValueError(f"duplicate ledger decision segment_id: {segment_id}")
            seen_segments.add(segment_id)
            destinations = decision.get("candidate_ids") or []
            if not isinstance(destinations, list):
                raise ValueError(f"{review.get('chunk_id')}: ledger candidate_ids must be a list")
            if disposition in {"captured", "merged"}:
                if not destinations:
                    raise ValueError(f"{review.get('chunk_id')}: {disposition} ledger decision needs candidate_ids")
                missing = sorted(set(destinations) - candidate_ids)
                if missing:
                    raise ValueError(f"{review.get('chunk_id')}: ledger references missing candidate_ids {missing}")
            else:
                if destinations:
                    raise ValueError(f"{review.get('chunk_id')}: excluded ledger decision cannot keep candidate_ids")
                if decision.get("reason_code") not in EXCLUSION_REASON_CODES:
                    raise ValueError(f"{review.get('chunk_id')}: excluded ledger decision needs a valid reason_code")
                if decision.get("reason_code") == "duplicate_of":
                    reference = decision.get("reason_reference")
                    if not reference or reference not in candidate_ids:
                        raise ValueError(f"{review.get('chunk_id')}: duplicate_of reference is not a final candidate")


def _revision_provenance(manifest: dict[str, Any], history: dict[str, Any], manifest_hash: str) -> dict[str, Any]:
    """Accept revision provenance while retaining readable legacy manifests."""
    revision_id = manifest.get("revision_id")
    if revision_id is not None:
        revision_kind = manifest.get("revision_kind")
        reason = manifest.get("reason")
        if not all(isinstance(value, str) and value.strip() for value in (revision_id, revision_kind, reason)):
            raise ValueError("revision manifests need non-empty revision_id, revision_kind and reason")
        for entry in history.get("applied", []):
            if entry.get("revision_id") == revision_id and entry.get("manifest_hash") != manifest_hash:
                raise ValueError(f"revision_id already belongs to a different manifest: {revision_id}")
        return {"revision_id": revision_id, "revision_kind": revision_kind, "reason": reason}
    patch_window = manifest.get("patch_window")
    if patch_window is None:
        patch_window = "pre_packet"
    if patch_window not in {"pre_packet", "post_packet"}:
        raise ValueError("legacy patch_window must be pre_packet or post_packet")
    return {"legacy_patch_window": patch_window}


def prepare_patch(video_id: str, data_root: Path, manifest: dict[str, Any]) -> tuple[dict[Path, dict[str, Any]], list[str], str]:
    if manifest.get("episode_video_id") != video_id:
        raise ValueError("patch episode_video_id mismatch")
    out = data_root / "processed" / video_id / "gold_extraction"
    history_path = out / "fastpath_patch_history.json"
    manifest_hash = sha256_json(manifest)
    history = load_json(history_path) if history_path.exists() else {"applied": []}
    if manifest_hash in {entry.get("manifest_hash") for entry in history.get("applied", [])}:
        raise ValueError("patch manifest was already applied")
    _revision_provenance(manifest, history, manifest_hash)
    reviews, candidates = _load_reviews(out)
    _assert_reviews(manifest, reviews)
    original = copy.deepcopy(reviews)
    status = load_json(out / "gold_extraction_status.json")
    calibration_path = out / "calibration_tests.json"
    calibration = load_json(calibration_path) if calibration_path.exists() else None
    transcript = load_json(out / "transcript_clean.json")["segments"]
    segments_by_id = {item["segment_id"]: item for item in transcript}
    chunk_ids = {item["chunk_id"] for item in status.get("chunks", [])}
    by_number = {int(path.name.split("_")[1]): (path, review) for path, review in reviews.items()}

    # Candidate insertion happens as a complete phase, before any relation reads.
    for insertion in manifest.get("inserts", []):
        number = int(insertion["chunk_number"])
        if number not in by_number:
            raise ValueError(f"unknown insertion chunk {number}")
        path, review = by_number[number]
        candidate = copy.deepcopy(insertion["candidate"])
        candidate_id = candidate.get("candidate_id")
        if not candidate_id or candidate_id in candidates:
            raise ValueError(f"insert candidate_id already exists or missing: {candidate_id}")
        if candidate.get("chunk_id") != review.get("chunk_id"):
            raise ValueError(f"{candidate_id}: insertion chunk_id mismatch")
        review.setdefault("candidates", []).append(candidate)
        candidates[candidate_id] = (path, candidate)

    for update in manifest.get("updates", []):
        candidate_id = update["candidate_id"]
        if candidate_id not in candidates:
            raise ValueError(f"unknown update candidate {candidate_id}")
        candidate = candidates[candidate_id][1]
        for path, expected in update.get("assert", {}).items():
            if _path_value(candidate, path) != expected:
                raise ValueError(f"{candidate_id}: assertion failed for {path}")
        for path, replacement in update.get("set", {}).items():
            _set_path(candidate, path, replacement)

    for removal in manifest.get("removals", []):
        candidate_id = removal["candidate_id"]
        if candidate_id not in candidates:
            raise ValueError(f"unknown removal candidate {candidate_id}")
        path, candidate = candidates[candidate_id]
        chunk_number = int(path.name.split("_")[1])
        if not removal.get("assert") and not _has_review_guard(manifest, chunk_number):
            raise ValueError(f"{candidate_id}: removal needs a candidate assert or a full review_assertion")
        for field, expected in removal.get("assert", {}).items():
            if _path_value(candidate, field) != expected:
                raise ValueError(f"{candidate_id}: removal assertion failed for {field}")
        reviews[path]["candidates"] = [item for item in reviews[path].get("candidates", []) if item.get("candidate_id") != candidate_id]
        del candidates[candidate_id]

    for ledger_update in manifest.get("ledger_updates", []):
        number = int(ledger_update["chunk_number"])
        if number not in by_number:
            raise ValueError(f"unknown ledger chunk {number}")
        _path, review = by_number[number]
        if "assert" not in ledger_update:
            raise ValueError(f"ledger_update for chunk {number} needs assert")
        expected = ledger_update["assert"]
        if review.get("ledger_decisions") != expected:
            raise ValueError(f"ledger assertion failed for chunk {number}")
        review["ledger_decisions"] = list(ledger_update.get("set", []))
        _validate_ledger_decisions(review)

    for relation in manifest.get("relations", []):
        candidate_id = relation["candidate_id"]
        if candidate_id not in candidates:
            raise ValueError(f"unknown relation candidate {candidate_id}")
        candidate = candidates[candidate_id][1]
        expected = relation.get("assert")
        if expected is not None and candidate.get("relations") != expected:
            raise ValueError(f"{candidate_id}: relation assertion failed")
        candidate["relations"] = {
            "parent_candidate_id": relation.get("parent_candidate_id"),
            "child_candidate_ids": list(relation.get("child_candidate_ids", [])),
        }

    calibration_changed = False
    allowed_redirect_fields = {"segment_ids", "segment_range", "quote_verbatim", "semantic_key", "semantic_candidate_ids", "deduplicated_segment_ids", "provenance"}
    for redirect in manifest.get("calibration_redirects", []):
        if calibration is None:
            raise ValueError("calibration redirect requires calibration_tests.json")
        calibration_id = redirect.get("calibration_id")
        target = next((item for item in calibration.get("tests", []) if item.get("calibration_id") == calibration_id), None)
        if target is None:
            raise ValueError(f"unknown calibration_id {calibration_id}")
        if "assert" not in redirect:
            raise ValueError(f"calibration redirect {calibration_id} needs assert")
        unknown_fields = set(redirect.get("set", {})) - allowed_redirect_fields
        if unknown_fields:
            raise ValueError(f"calibration redirect has unsupported fields: {sorted(unknown_fields)}")
        for field, expected in redirect["assert"].items():
            if target.get(field) != expected:
                raise ValueError(f"calibration redirect assertion failed for {calibration_id}: {field}")
        for field, replacement in redirect.get("set", {}).items():
            target[field] = copy.deepcopy(replacement)
        calibration_changed = True

    all_candidates = [candidate for review in reviews.values() for candidate in review.get("candidates", [])]
    errors: list[str] = []
    for candidate in all_candidates:
        errors.extend(validate_candidate(candidate, segments_by_id, chunk_ids))
        errors.extend(editorial_ascii_errors(candidate))
    errors.extend(normalize_relations(all_candidates))
    if errors:
        raise ValueError("patch validation failed: " + "; ".join(sorted(set(errors))))
    _validate_final_ledger(reviews, segments_by_id, {candidate["candidate_id"] for candidate in all_candidates})
    if calibration_changed and calibration is not None:
        final_ids = {candidate["candidate_id"] for candidate in all_candidates}
        seen_targets: set[str] = set()
        for test in calibration.get("tests", []):
            test_ids = test.get("segment_ids", [])
            if not isinstance(test_ids, list) or not test_ids or any(segment_id not in segments_by_id for segment_id in test_ids):
                raise ValueError("calibration redirect references missing segment_ids")
            if seen_targets & set(test_ids):
                raise ValueError("calibration redirect creates duplicate target segments")
            seen_targets.update(test_ids)
            semantic_ids = test.get("semantic_candidate_ids", [])
            if any(candidate_id not in final_ids for candidate_id in semantic_ids):
                raise ValueError("calibration redirect references missing semantic_candidate_ids")
        coverage = calibration_coverage(calibration, all_candidates)
        if coverage.get("duplicate_target_segments"):
            raise ValueError("calibration redirect leaves duplicate target segments")
    changed = [str(path) for path, review in reviews.items() if review != original[path]]
    if calibration_changed:
        reviews[calibration_path] = calibration
        original[calibration_path] = None
        changed.append(str(calibration_path))
    return reviews, changed, manifest_hash


def apply_patch(video_id: str, data_root: Path, manifest: dict[str, Any], apply: bool) -> dict[str, Any]:
    out = data_root / "processed" / video_id / "gold_extraction"
    manifest_hash = sha256_json(manifest)
    history_path = out / "fastpath_patch_history.json"
    history = load_json(history_path) if history_path.exists() else {"applied": []}
    if manifest_hash in {entry.get("manifest_hash") for entry in history.get("applied", [])}:
        if apply:
            return {"status": "ok", "mode": "already_applied", "changed_reviews": [], "manifest_hash": manifest_hash}
        raise ValueError("patch manifest was already applied")
    reviews, changed, manifest_hash = prepare_patch(video_id, data_root, manifest)
    if apply:
        provenance = _revision_provenance(manifest, history, manifest_hash)
        history["applied"].append({
            "manifest_hash": manifest_hash,
            "changed_reviews": changed,
            **provenance,
        })
        writes = {Path(path): reviews[Path(path)] for path in changed}
        writes[history_path] = history
        write_json_batch(writes)
        record_operation_event(out, "patch", manifest_hash, {"changed_reviews": changed})
    return {"status": "ok", "mode": "apply" if apply else "check", "changed_reviews": changed, "manifest_hash": manifest_hash}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--patch", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        result = apply_patch(args.video_id, args.data_root, load_json(args.patch), args.apply)
    except (GoldPauseError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
