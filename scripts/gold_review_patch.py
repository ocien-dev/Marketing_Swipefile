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
    json_hashes,
    load_json,
    normalize_relations,
    numeric_mentions,
    record_operation_event,
    sha256_json,
    validate_candidate,
    write_json,
    write_json_batch,
)


def canonical_source_assert_value(value: Any) -> Any:
    """Remove builder-only compatibility fields from a source assertion."""
    if isinstance(value, dict):
        return {
            key: canonical_source_assert_value(item)
            for key, item in value.items()
            if not str(key).startswith("legacy_")
        }
    if isinstance(value, list):
        return [canonical_source_assert_value(item) for item in value]
    return copy.deepcopy(value)


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


def generate_source_assert_manifest(
    video_id: str,
    data_root: Path,
    intent: dict[str, Any],
) -> dict[str, Any]:
    """Hydrate assert_paths from current manual-review source without gold writes."""
    if intent.get("episode_video_id") != video_id:
        raise ValueError("patch episode_video_id mismatch")
    out = data_root / "processed" / video_id / "gold_extraction"
    _reviews, candidates = _load_reviews(out)
    manifest = copy.deepcopy(intent)
    manifest["assertion_mode"] = "source_canonical"
    for update in manifest.get("updates", []):
        candidate_id = update.get("candidate_id")
        if candidate_id not in candidates:
            raise ValueError(f"unknown update candidate {candidate_id}")
        if "assert" in update:
            raise ValueError(f"{candidate_id}: source-assert intent must use assert_paths, not assert")
        paths = update.pop("assert_paths", None)
        if paths is None:
            paths = list(update.get("set", {}))
        if not isinstance(paths, list) or not paths or any(not isinstance(path, str) or not path for path in paths):
            raise ValueError(f"{candidate_id}: assert_paths must be a non-empty string list")
        candidate = candidates[candidate_id][1]
        update["assert"] = {
            path: canonical_source_assert_value(_path_value(candidate, path))
            for path in paths
        }
        update["set"] = {
            path: canonical_source_assert_value(value)
            for path, value in update.get("set", {}).items()
        }
    return manifest


def generate_audit_remediation_scaffold(
    video_id: str,
    data_root: Path,
    audit: dict[str, Any],
) -> dict[str, Any]:
    """Resolve one audit into source-canonical remediation inputs without writes."""
    if audit.get("episode_video_id") != video_id:
        raise ValueError("audit episode_video_id mismatch")
    out = data_root / "processed" / video_id / "gold_extraction"
    transcript = load_json(out / "transcript_clean.json").get("segments", [])
    chunks = load_json(out / "chunks" / "chunk_index.json").get("chunks", [])
    calibration = load_json(out / "calibration_tests.json")
    reviews, candidates = _load_reviews(out)
    by_index = {int(item["clean_index"]): item for item in transcript}
    segment_by_id = {str(item["segment_id"]): item for item in transcript}
    next_number = max([
        int(str(candidate_id).rsplit("-G", 1)[1])
        for candidate_id in candidates if "-G" in str(candidate_id)
        and str(candidate_id).rsplit("-G", 1)[1].isdigit()
    ] or [0]) + 1
    findings = []
    for position, finding in enumerate(audit.get("findings", [])):
        if not isinstance(finding, dict):
            raise ValueError(f"audit finding {position} is not an object")
        raw_range = finding.get("segment_range") or finding.get("clean_index_range") or []
        try:
            start, end = int(raw_range[0]), int(raw_range[1])
        except (IndexError, TypeError, ValueError):
            raise ValueError(f"audit finding {position} has invalid segment_range")
        source_segments = [by_index[index] for index in range(start, end + 1) if index in by_index]
        if not source_segments:
            raise ValueError(f"audit finding {position} does not resolve to transcript segments")
        candidate_ids = sorted({
            str(value) for key in ("candidate_ids", "target_candidate_ids")
            for value in (finding.get(key) or []) if value
        })
        unknown = [candidate_id for candidate_id in candidate_ids if candidate_id not in candidates]
        if unknown:
            raise ValueError(f"audit finding {position} references unknown candidates: {unknown}")
        candidate_asserts = []
        for candidate_id in candidate_ids:
            review_path, candidate = candidates[candidate_id]
            evidence = candidate.get("evidence", {}) if isinstance(candidate.get("evidence"), dict) else {}
            evidence_ids = [
                str(item.get("segment_id"))
                for layer in ("minimal_quote", "support_segments")
                for item in evidence.get(layer, [])
                if isinstance(item, dict) and item.get("segment_id")
            ]
            evidence_indexes = sorted(
                int(segment_by_id[segment_id]["clean_index"])
                for segment_id in set(evidence_ids) if segment_id in segment_by_id
            )
            candidate_asserts.append({
                "candidate_id": candidate_id,
                "review_file": review_path.name,
                "assert_candidate": canonical_source_assert_value(candidate),
                "current_relations": canonical_source_assert_value(candidate.get("relations", {})),
                "current_evidence_segment_ids": sorted(set(evidence_ids)),
                "current_evidence_clean_index_range": (
                    [evidence_indexes[0], evidence_indexes[-1]] if evidence_indexes else []
                ),
            })
        owning_chunks = []
        source_ids = {item["segment_id"] for item in source_segments}
        for chunk in chunks:
            chunk_indices = set(range(
                int(segment_by_id[chunk["first_segment_id"]]["clean_index"]),
                int(segment_by_id[chunk["last_segment_id"]]["clean_index"]) + 1,
            )) if chunk.get("first_segment_id") in segment_by_id and chunk.get("last_segment_id") in segment_by_id else set()
            if chunk_indices & set(range(start, end + 1)):
                owning_chunks.append({
                    "chunk_number": chunk.get("chunk_number"),
                    "chunk_id": chunk.get("chunk_id"),
                    "input_hash": chunk.get("input_hash"),
                    "candidate_ids": [
                        candidate.get("candidate_id")
                        for review in reviews.values()
                        if review.get("chunk_id") == chunk.get("chunk_id")
                        for candidate in review.get("candidates", [])
                    ],
                })
        source_numeric_occurrences = [
            {
                "clean_index": int(item["clean_index"]),
                "segment_id": item["segment_id"],
                **mention,
            }
            for item in source_segments
            for mention in numeric_mentions(str(item.get("text", "")))
        ]
        calibration_asserts = []
        for test in calibration.get("tests", []):
            test_ids = {str(value) for value in test.get("segment_ids", []) if value}
            if not (test_ids & source_ids):
                continue
            calibration_asserts.append({
                "calibration_id": test.get("calibration_id"),
                "assert": canonical_source_assert_value(test),
                "source_intersection": sorted(test_ids & source_ids),
                "current_semantic_candidate_ids": list(test.get("semantic_candidate_ids", [])),
            })
        findings.append({
            "finding_id": finding.get("finding_id") or finding.get("id") or f"finding-{position + 1:03d}",
            "required_action": finding.get("required_action"),
            "segment_range": [start, end],
            "source_segments": [
                {"clean_index": item["clean_index"], "segment_id": item["segment_id"], "quote_verbatim": item["text"]}
                for item in source_segments
            ],
            "source_segment_ids": sorted(source_ids),
            "source_numeric_occurrences": source_numeric_occurrences,
            "owning_chunks": owning_chunks,
            "review_assertions": owning_chunks,
            "candidate_asserts": candidate_asserts,
            "calibration_asserts": calibration_asserts,
            "suggested_insert_candidate_id": f"{video_id}-G{next_number:03d}",
            "semantic_fields_for_model": [
                "merge_or_insert", "source_claim", "takeaway_applicavel", "type",
                "themes", "caveats", "relations",
            ],
        })
        next_number += 1
    core = {
        "schema_version": "1.1.0",
        "kind": "gold_audit_remediation_scaffold",
        "episode_video_id": video_id,
        "audit_status": audit.get("status"),
        "open_findings": audit.get("open_findings"),
        "findings": findings,
        "patch_manifest_template": {
            "episode_video_id": video_id,
            "revision_id": None,
            "revision_kind": "audit_remediation",
            "reason": "resolve " + ", ".join(item["finding_id"] for item in findings),
            "review_assertions": [
                assertion
                for item in findings
                for assertion in item.get("review_assertions", [])
            ],
            "updates": [],
            "inserts": [],
            "removals": [],
            "relations": [],
            "calibration_redirects": [],
        },
        "model_contract": {
            "semantic_decisions_required": True,
            "allowed_inputs": [
                "source_segments", "source_numeric_occurrences", "candidate_asserts",
                "calibration_asserts", "review_assertions",
            ],
            "must_not_infer": [
                "numbers absent from source", "calibration equivalence from shared topic only",
                "relations used only to suppress overlap warnings",
            ],
        },
        "writes_gold": False,
    }
    return {**core, "semantic_sha256": sha256_json(core)}


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

    source_canonical_asserts = manifest.get("assertion_mode") == "source_canonical"
    for update in manifest.get("updates", []):
        candidate_id = update["candidate_id"]
        if candidate_id not in candidates:
            raise ValueError(f"unknown update candidate {candidate_id}")
        candidate = candidates[candidate_id][1]
        for path, expected in update.get("assert", {}).items():
            actual = _path_value(candidate, path)
            if source_canonical_asserts:
                actual = canonical_source_assert_value(actual)
                expected = canonical_source_assert_value(expected)
            if actual != expected:
                raise ValueError(
                    f"{candidate_id}: assertion failed for {path}; "
                    f"current_source={json.dumps(actual, ensure_ascii=False, sort_keys=True)}"
                )
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


def _patch_preview(
    video_id: str,
    manifest_hash: str,
    reviews: dict[Path, dict[str, Any]],
    changed: list[str],
) -> dict[str, Any]:
    changes = []
    for raw_path in sorted(changed):
        path = Path(raw_path)
        changes.append({
            "path": raw_path,
            "before": json_hashes(path) if path.exists() else None,
            "after_semantic_sha256": sha256_json(reviews[path]),
        })
    core = {
        "schema_version": "1.0.0",
        "kind": "gold_review_patch_preview",
        "episode_video_id": video_id,
        "manifest_hash": manifest_hash,
        "changes": changes,
    }
    return {**core, "preview_semantic_sha256": sha256_json(core)}


def apply_patch(
    video_id: str,
    data_root: Path,
    manifest: dict[str, Any],
    apply: bool,
    *,
    preview_receipt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = data_root / "processed" / video_id / "gold_extraction"
    manifest_hash = sha256_json(manifest)
    history_path = out / "fastpath_patch_history.json"
    history = load_json(history_path) if history_path.exists() else {"applied": []}
    if manifest_hash in {entry.get("manifest_hash") for entry in history.get("applied", [])}:
        if apply:
            return {"status": "ok", "mode": "already_applied", "changed_reviews": [], "manifest_hash": manifest_hash}
        raise ValueError("patch manifest was already applied")
    reviews, changed, manifest_hash = prepare_patch(video_id, data_root, manifest)
    preview = _patch_preview(video_id, manifest_hash, reviews, changed)
    if apply and manifest.get("assertion_mode") == "source_canonical":
        if preview_receipt is None:
            raise ValueError("source-canonical apply requires its clean patch preview receipt")
        receipt_core = {
            key: value for key, value in preview_receipt.items()
            if key != "preview_semantic_sha256"
        }
        if (
            preview_receipt.get("preview_semantic_sha256") != sha256_json(receipt_core)
            or preview_receipt != preview
        ):
            raise ValueError("source-canonical patch preview receipt is stale or mismatched")
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
    return {
        "status": "ok",
        "mode": "apply" if apply else "check",
        "changed_reviews": changed,
        "manifest_hash": manifest_hash,
        "preview": preview,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--patch", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--generate-source-asserts", action="store_true")
    mode.add_argument("--generate-audit-scaffold", action="store_true")
    parser.add_argument("--output", type=Path, help="Job-local output for --generate-source-asserts.")
    parser.add_argument("--preview-receipt", type=Path, help="Receipt written by --check and required by source-canonical --apply.")
    args = parser.parse_args()
    try:
        payload = load_json(args.patch)
        if args.generate_audit_scaffold:
            scaffold = generate_audit_remediation_scaffold(args.video_id, args.data_root, payload)
            if args.output is not None:
                write_json(args.output, scaffold)
            result = {
                "status": "ok",
                "mode": "generate_audit_scaffold",
                "output": str(args.output) if args.output else None,
                "scaffold": scaffold if args.output is None else None,
                "semantic_sha256": scaffold["semantic_sha256"],
            }
        elif args.generate_source_asserts:
            manifest = generate_source_assert_manifest(args.video_id, args.data_root, payload)
            if args.output is not None:
                write_json(args.output, manifest)
            result = {
                "status": "ok",
                "mode": "generate_source_asserts",
                "output": str(args.output) if args.output else None,
                "manifest": manifest if args.output is None else None,
                "manifest_hash": sha256_json(manifest),
            }
        else:
            preview_receipt = load_json(args.preview_receipt) if args.apply and args.preview_receipt else None
            result = apply_patch(
                args.video_id, args.data_root, payload, args.apply,
                preview_receipt=preview_receipt,
            )
            if args.check and args.preview_receipt:
                write_json(args.preview_receipt, result["preview"])
    except (GoldPauseError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
