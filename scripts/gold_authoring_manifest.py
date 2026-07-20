#!/usr/bin/env python
"""Single source of model-authored decisions for the gold fast lane.

The manifest is internal and sparse.  It compiles deterministically to the
existing compact-v3 payload, so persisted reviews and the public gold schema do
not change.  Ledger and calibration remain derived outputs, never independent
post-build patches.
"""

from __future__ import annotations

import copy
import re
from typing import Any

from scripts.gold_extraction_common import sha256_semantic_json


AUTHORING_MANIFEST_FORMAT = "gold_authoring_manifest_v1"
AUTHORING_MANIFEST_KIND = "gold_authoring_manifest"
AUTHORING_MANIFEST_SCHEMA = "1.0.0"
CANONICAL_EXTRACTION_ARCHITECTURE = "chronological_hybrid_v1"

# Compact authoring v4: the model writes only the semantic minority.  The
# runtime expands it to the identical full v1 manifest *before* any hash,
# validation, or compact-payload derivation, so persisted schemas, ledger,
# calibration, workbench and dossier bytes are unchanged.  This is the same
# expand-before-validate precedent already used for compact v3 -> v2.
COMPACT_AUTHORING_MARKER = "compaction"
COMPACT_AUTHORING_V4 = "v4"
# Per-segment source dispositions are dominated by two boilerplate shapes:
# one `captured` template (its candidate_ids are exactly the candidates whose
# evidence covers the segment) and one default `excluded` template.  Both are
# declared once in the compact manifest, not hardcoded here, so the boilerplate
# text stays model-authored and episode-agnostic.  Only segments that deviate
# from those two shapes are listed explicitly as exceptions.
ADVERSARIAL_REVIEW_CATEGORIES = (
    "evidence_and_numeric_ownership",
    "excluded_material_blocks",
    "host_and_interviewer_attribution",
    "before_after_mechanisms_outcomes_caveats",
    "calibration_proposition_equivalence",
    "adjacent_boundaries_and_counterexamples",
)
FORBIDDEN_PARALLEL_FIELDS = {
    "ledger_updates",
    "calibration_redirects",
    "calibration_overrides",
    "review_updates",
    "review_replacements",
}


def _compiled_source_dispositions(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive duplicate calibration bindings from the authoring authority.

    The decision remains model-authored in ``calibration_decisions``.  This
    compiler only projects an already explicit, validated duplicate decision
    into the ledger input so final calibration can be rederived without
    polluting candidate evidence or patching calibration after the build.
    """
    dispositions = copy.deepcopy(manifest.get("source_dispositions", []))
    by_segment = {
        str(item.get("segment_id")): item
        for item in dispositions
        if isinstance(item, dict) and item.get("segment_id")
    }
    for decision in manifest.get("calibration_decisions", []):
        if not isinstance(decision, dict) or not (
            decision.get("source_equivalent_duplicate") is True
            and decision.get("proposition_equivalent") is True
            and decision.get("candidate_id")
        ):
            continue
        candidate_id = str(decision["candidate_id"])
        calibration_id = str(decision.get("calibration_id") or "unknown")
        for segment_id in decision.get("duplicate_source_segment_ids") or []:
            disposition = by_segment.get(str(segment_id))
            if disposition is None:
                continue
            disposition.update({
                "disposition": "merged",
                "candidate_ids": [candidate_id],
                "reason_code": "duplicate_of",
                "reason_reference": candidate_id,
                "reason": (
                    f"source_equivalent_duplicate:{calibration_id}: "
                    "authoring-manifest proposition and numeric anchors validated."
                ),
            })
    return dispositions


def is_compact_authoring_v4(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get(COMPACT_AUTHORING_MARKER) == COMPACT_AUTHORING_V4
    )


def _evidence_clean_indexes(candidate: dict[str, Any]) -> set[int]:
    """Every clean index covered by a candidate's minimal or support evidence."""
    covered: set[int] = set()
    for field in ("minimal_segment_ids", "support_segment_ids"):
        for evidence in candidate.get(field) or []:
            if not isinstance(evidence, dict):
                continue
            span = evidence.get("range")
            if isinstance(span, (list, tuple)) and len(span) == 2:
                start, end = int(span[0]), int(span[1])
                if end < start:
                    start, end = end, start
                covered.update(range(start, end + 1))
            elif evidence.get("clean_index") is not None:
                covered.add(int(evidence["clean_index"]))
    return covered


def _chunk_number_lookup(chunk_ranges: list[Any]) -> "callable":
    ordered = [
        (int(item[0]), int(item[1]), int(item[2]))
        for item in chunk_ranges
        if isinstance(item, (list, tuple)) and len(item) == 3
    ]

    def chunk_of(index: int) -> Any:
        for chunk_number, first_index, last_index in ordered:
            if first_index <= index <= last_index:
                return chunk_number
        return None

    return chunk_of


def _intern_justifications(items: list[Any]) -> dict[str, Any]:
    """Store each distinct justification once and reference it by id."""
    table: dict[str, str] = {}
    order: list[str] = []
    compact_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict) or "justification" not in item:
            compact_items.append(copy.deepcopy(item))
            continue
        text = item["justification"]
        ref = table.get(text)
        if ref is None:
            ref = f"j{len(order)}"
            table[text] = ref
            order.append(text)
        entry = {key: value for key, value in item.items() if key != "justification"}
        entry["justification_ref"] = ref
        compact_items.append(entry)
    return {
        "justification_table": {table[text]: text for text in order},
        "items": compact_items,
    }


def _expand_interned_justifications(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return copy.deepcopy(value)
    if not isinstance(value, dict):
        return []
    table = value.get("justification_table", {}) or {}
    expanded: list[dict[str, Any]] = []
    for item in value.get("items", []):
        if not isinstance(item, dict) or "justification_ref" not in item:
            expanded.append(copy.deepcopy(item))
            continue
        entry = {key: val for key, val in item.items() if key != "justification_ref"}
        entry["justification"] = table.get(item["justification_ref"], "")
        expanded.append(entry)
    return expanded


def expand_compact_v4(compact: dict[str, Any]) -> dict[str, Any]:
    """Expand a compact-v4 authoring manifest into the full v1 manifest.

    Deterministic and lossless: every field a downstream stage reads is
    materialized identically to a hand-written full manifest, so hashes,
    ledger, calibration, workbench and dossier bytes are unchanged.
    """
    manifest = copy.deepcopy(compact)
    manifest.pop(COMPACT_AUTHORING_MARKER, None)

    segment_count = int(manifest.pop("segment_count", 0) or 0)
    chunk_ranges = manifest.pop("chunk_ranges", []) or []
    captured_template = manifest.pop("captured_disposition", {}) or {}
    default_disposition = manifest.pop("default_source_disposition", {}) or {}
    exceptions_list = manifest.pop("source_disposition_exceptions", []) or []
    video_id = str(manifest.get("episode_video_id") or "")

    chunk_of = _chunk_number_lookup(chunk_ranges)
    width = max(4, len(str(segment_count)))

    candidates = manifest.get("candidates", []) or []
    index_to_candidate_ids: dict[int, list[str]] = {}
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        candidate_id = str(candidate.get("candidate_id") or candidate.get("id") or "")
        if not candidate_id:
            continue
        for clean_index in _evidence_clean_indexes(candidate):
            index_to_candidate_ids.setdefault(clean_index, []).append(candidate_id)

    exceptions_by_index = {
        int(item["index"]): item
        for item in exceptions_list
        if isinstance(item, dict) and item.get("index") is not None
    }

    def default_segment_id(index: int) -> str:
        return f"{video_id}-transcript-{index + 1:0{width}d}"

    dispositions: list[dict[str, Any]] = []
    for index in range(segment_count):
        if index in exceptions_by_index:
            entry = copy.deepcopy(exceptions_by_index[index])
            entry.setdefault("segment_id", default_segment_id(index))
            entry.setdefault("index", index)
            entry.setdefault("chunk_number", chunk_of(index))
            entry.setdefault("candidate_ids", [])
            dispositions.append(entry)
            continue
        if index in index_to_candidate_ids:
            dispositions.append({
                "segment_id": default_segment_id(index),
                "index": index,
                "chunk_number": chunk_of(index),
                "disposition": "captured",
                "candidate_ids": sorted(index_to_candidate_ids[index]),
                "reason_code": captured_template.get("reason_code"),
                "reason": captured_template.get("reason"),
            })
            continue
        dispositions.append({
            "segment_id": default_segment_id(index),
            "index": index,
            "chunk_number": chunk_of(index),
            "disposition": default_disposition.get("disposition", "excluded"),
            "candidate_ids": [],
            "reason_code": default_disposition.get("reason_code", "low_signal"),
            "reason": default_disposition.get("reason"),
        })

    manifest["source_dispositions"] = dispositions
    manifest["audit_warning_dispositions"] = _expand_interned_justifications(
        manifest.get("audit_warning_dispositions", [])
    )
    manifest["risk_recall_acknowledgements"] = _expand_interned_justifications(
        manifest.get("risk_recall_acknowledgements", [])
    )
    return manifest


def compact_v4_from_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Encode a full v1 manifest as compact v4 (authoring helper / round-trip).

    Any segment whose full entry does not match the derived captured/default
    shape is emitted as an explicit exception, so the round trip is lossless
    for an arbitrary manifest by construction.
    """
    full = copy.deepcopy(manifest)
    dispositions = full.get("source_dispositions", []) or []
    segment_count = len(dispositions)

    chunk_bounds: dict[int, list[int]] = {}
    for entry in dispositions:
        if not isinstance(entry, dict) or entry.get("chunk_number") is None:
            continue
        chunk_number = int(entry["chunk_number"])
        index = int(entry.get("index", 0))
        bounds = chunk_bounds.setdefault(chunk_number, [index, index])
        bounds[0] = min(bounds[0], index)
        bounds[1] = max(bounds[1], index)
    chunk_ranges = [
        [chunk_number, bounds[0], bounds[1]]
        for chunk_number, bounds in sorted(chunk_bounds.items())
    ]

    captured = [e for e in dispositions if e.get("disposition") == "captured"]
    captured_template = {
        "reason_code": captured[0].get("reason_code") if captured else "candidate_capture",
        "reason": captured[0].get("reason") if captured else None,
    }
    excluded = [e for e in dispositions if e.get("disposition") == "excluded"]
    default_reason_counts: dict[tuple[str, str], int] = {}
    for entry in excluded:
        key = (entry.get("reason_code"), entry.get("reason"))
        default_reason_counts[key] = default_reason_counts.get(key, 0) + 1
    if default_reason_counts:
        (default_reason_code, default_reason), _ = max(
            default_reason_counts.items(), key=lambda kv: kv[1]
        )
    else:
        default_reason_code, default_reason = "low_signal", None
    default_disposition = {
        "disposition": "excluded",
        "reason_code": default_reason_code,
        "reason": default_reason,
    }

    compact = {key: value for key, value in full.items() if key not in {
        "source_dispositions", "audit_warning_dispositions",
        "risk_recall_acknowledgements", "authoring_decisions_sha256",
        "semantic_sha256",
    }}
    compact[COMPACT_AUTHORING_MARKER] = COMPACT_AUTHORING_V4
    compact["segment_count"] = segment_count
    compact["chunk_ranges"] = chunk_ranges
    compact["captured_disposition"] = captured_template
    compact["default_source_disposition"] = default_disposition

    stub = {
        COMPACT_AUTHORING_MARKER: COMPACT_AUTHORING_V4,
        "episode_video_id": full.get("episode_video_id"),
        "candidates": full.get("candidates", []),
        "segment_count": segment_count,
        "chunk_ranges": chunk_ranges,
        "captured_disposition": captured_template,
        "default_source_disposition": default_disposition,
        "source_disposition_exceptions": [],
        "audit_warning_dispositions": [],
        "risk_recall_acknowledgements": [],
    }
    derived = expand_compact_v4(copy.deepcopy(stub))["source_dispositions"]
    exceptions = [
        copy.deepcopy(actual)
        for actual, guess in zip(dispositions, derived)
        if sha256_semantic_json(actual) != sha256_semantic_json(guess)
    ]
    compact["source_disposition_exceptions"] = exceptions
    compact["audit_warning_dispositions"] = _intern_justifications(
        full.get("audit_warning_dispositions", []) or []
    )
    compact["risk_recall_acknowledgements"] = _intern_justifications(
        full.get("risk_recall_acknowledgements", []) or []
    )
    return compact


def is_authoring_manifest(value: Any) -> bool:
    return isinstance(value, dict) and (
        value.get("manifest_format") == AUTHORING_MANIFEST_FORMAT
        or value.get("kind") == AUTHORING_MANIFEST_KIND
        or is_compact_authoring_v4(value)
    )


def _decision_core(manifest: dict[str, Any]) -> dict[str, Any]:
    if isinstance(manifest.get("compatibility_payload"), dict):
        return {
            "episode_video_id": manifest.get("episode_video_id"),
            "compatibility_payload": copy.deepcopy(manifest["compatibility_payload"]),
        }
    return {
        "episode_video_id": manifest.get("episode_video_id"),
        "candidate_defaults": copy.deepcopy(manifest.get("candidate_defaults", {})),
        "type_defaults": copy.deepcopy(manifest.get("type_defaults", {})),
        "candidates": copy.deepcopy(manifest.get("candidates", [])),
        "zero_insight_chunks": copy.deepcopy(manifest.get("zero_insight_chunks", [])),
        "source_dispositions": copy.deepcopy(manifest.get("source_dispositions", [])),
        "risk_recall_acknowledgements": copy.deepcopy(manifest.get("risk_recall_acknowledgements", [])),
        "audit_warning_dispositions": copy.deepcopy(manifest.get("audit_warning_dispositions", [])),
        "calibration_decisions": copy.deepcopy(manifest.get("calibration_decisions", [])),
    }


def authoring_decisions_sha256(manifest: dict[str, Any]) -> str:
    return sha256_semantic_json(_decision_core(manifest))


def manifest_semantic_sha256(manifest: dict[str, Any]) -> str:
    core = {
        key: value for key, value in manifest.items()
        if key != "semantic_sha256"
    }
    return sha256_semantic_json(core)


def wrap_legacy_payload(video_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Compatibility adapter; new authoring should provide the manifest."""
    return {
        "schema_version": AUTHORING_MANIFEST_SCHEMA,
        "kind": AUTHORING_MANIFEST_KIND,
        "manifest_format": AUTHORING_MANIFEST_FORMAT,
        "episode_video_id": payload.get("episode_video_id", video_id),
        "extraction_architecture": CANONICAL_EXTRACTION_ARCHITECTURE,
        "candidate_defaults": copy.deepcopy(payload.get("candidate_defaults", payload.get("d", {}))),
        "type_defaults": copy.deepcopy(payload.get("type_defaults", payload.get("td", {}))),
        "candidates": copy.deepcopy(payload.get("candidates", payload.get("c", []))),
        "zero_insight_chunks": copy.deepcopy(payload.get("zero_insight_chunks", payload.get("z", []))),
        "source_dispositions": copy.deepcopy(payload.get("ledger_decisions", payload.get("l", []))),
        "risk_recall_acknowledgements": copy.deepcopy(payload.get("risk_recall_acknowledgements", payload.get("r", []))),
        "audit_warning_dispositions": copy.deepcopy(payload.get("audit_warning_dispositions", payload.get("w", []))),
        "calibration_decisions": copy.deepcopy(payload.get("calibration_decisions", [])),
        "compatibility_source_format": payload.get("payload_format", "legacy_review_payload"),
        "compatibility_payload": copy.deepcopy(payload),
        "adversarial_review": None,
    }


def normalize_authoring_input(video_id: str, value: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    if is_compact_authoring_v4(value):
        value = expand_compact_v4(value)
    explicit = is_authoring_manifest(value)
    manifest = copy.deepcopy(value) if explicit else wrap_legacy_payload(video_id, value)
    manifest.setdefault("schema_version", AUTHORING_MANIFEST_SCHEMA)
    manifest.setdefault("kind", AUTHORING_MANIFEST_KIND)
    manifest.setdefault("manifest_format", AUTHORING_MANIFEST_FORMAT)
    manifest.setdefault("episode_video_id", video_id)
    manifest.setdefault("extraction_architecture", CANONICAL_EXTRACTION_ARCHITECTURE)
    manifest.setdefault("candidate_defaults", {})
    manifest.setdefault("type_defaults", {})
    manifest.setdefault("candidates", [])
    manifest.setdefault("zero_insight_chunks", [])
    manifest.setdefault("source_dispositions", [])
    manifest.setdefault("risk_recall_acknowledgements", [])
    manifest.setdefault("audit_warning_dispositions", [])
    manifest.setdefault("calibration_decisions", [])
    manifest["authoring_decisions_sha256"] = authoring_decisions_sha256(manifest)
    core = {key: value for key, value in manifest.items() if key != "semantic_sha256"}
    manifest["semantic_sha256"] = sha256_semantic_json(core)
    return manifest, explicit


def validate_authoring_manifest(
    video_id: str,
    manifest: dict[str, Any],
    *,
    require_adversarial_review: bool,
    expected_segment_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    def issue(field: str, category: str, evidence: Any, expected: str) -> None:
        issues.append({
            "candidate_id": "<authoring_manifest>",
            "field": field,
            "category": category,
            "evidence": evidence,
            "expected": expected,
        })

    if manifest.get("manifest_format") != AUTHORING_MANIFEST_FORMAT:
        issue("manifest_format", "contract", manifest.get("manifest_format"), AUTHORING_MANIFEST_FORMAT)
    if manifest.get("episode_video_id") != video_id:
        issue("episode_video_id", "identity", manifest.get("episode_video_id"), video_id)
    if manifest.get("extraction_architecture") != CANONICAL_EXTRACTION_ARCHITECTURE:
        issue("extraction_architecture", "architecture", manifest.get("extraction_architecture"), CANONICAL_EXTRACTION_ARCHITECTURE)
    for field in sorted(FORBIDDEN_PARALLEL_FIELDS & set(manifest)):
        issue(field, "parallel_authority_forbidden", "present", "derive ledger and calibration from the authoring manifest")
    for field in (
        "candidate_defaults", "type_defaults", "adversarial_review",
    ):
        if field != "adversarial_review" and not isinstance(manifest.get(field), dict):
            issue(field, "contract", type(manifest.get(field)).__name__, "object")
    for field in (
        "candidates", "zero_insight_chunks", "source_dispositions",
        "risk_recall_acknowledgements", "audit_warning_dispositions",
        "calibration_decisions",
    ):
        if not isinstance(manifest.get(field), list):
            issue(field, "contract", type(manifest.get(field)).__name__, "list")

    dispositions = manifest.get("source_dispositions", [])
    if expected_segment_ids is not None and isinstance(dispositions, list) and not dispositions:
        issue(
            "source_dispositions",
            "source_coverage",
            "empty",
            "one explicit captured, merged, or excluded decision for every transcript segment",
        )
    disposition_segment_ids: list[str] = []
    for position, disposition in enumerate(dispositions if isinstance(dispositions, list) else []):
        if not isinstance(disposition, dict):
            issue(f"source_dispositions[{position}]", "contract", disposition, "object")
            continue
        if not disposition.get("segment_id") or disposition.get("chunk_number") is None:
            issue(
                f"source_dispositions[{position}]",
                "source_scope",
                disposition,
                "exact segment_id and owning chunk_number",
            )
        elif disposition.get("segment_id"):
            disposition_segment_ids.append(str(disposition["segment_id"]))
        if disposition.get("disposition") not in {"captured", "merged", "excluded"}:
            issue(
                f"source_dispositions[{position}].disposition",
                "ledger",
                disposition.get("disposition"),
                "captured, merged, or excluded",
            )
    duplicate_segment_ids = sorted({
        segment_id for segment_id in disposition_segment_ids
        if disposition_segment_ids.count(segment_id) > 1
    })
    if duplicate_segment_ids:
        issue(
            "source_dispositions",
            "duplicate_source_decision",
            duplicate_segment_ids,
            "exactly one decision per transcript segment",
        )
    if expected_segment_ids is not None:
        declared_segment_ids = set(disposition_segment_ids)
        missing_segment_ids = sorted(expected_segment_ids - declared_segment_ids)
        unknown_segment_ids = sorted(declared_segment_ids - expected_segment_ids)
        if missing_segment_ids or unknown_segment_ids:
            issue(
                "source_dispositions",
                "source_coverage",
                {
                    "missing_segment_ids": missing_segment_ids,
                    "unknown_segment_ids": unknown_segment_ids,
                },
                "one exact decision for every transcript segment and no foreign segment ids",
            )

    calibration_ids: set[str] = set()
    candidate_ids = {
        str(item.get("candidate_id") or item.get("id"))
        for item in manifest.get("candidates", [])
        if isinstance(item, dict) and (item.get("candidate_id") or item.get("id"))
    }
    for position, decision in enumerate(manifest.get("calibration_decisions", []) if isinstance(manifest.get("calibration_decisions"), list) else []):
        if not isinstance(decision, dict):
            issue(f"calibration_decisions[{position}]", "contract", decision, "object")
            continue
        calibration_id = str(decision.get("calibration_id") or "")
        if not calibration_id:
            issue(f"calibration_decisions[{position}].calibration_id", "calibration", "missing", "known calibration_id")
        elif calibration_id in calibration_ids:
            issue(f"calibration_decisions[{position}].calibration_id", "duplicate", calibration_id, "unique calibration decision")
        calibration_ids.add(calibration_id)
        if "candidate_id" not in decision:
            issue(f"calibration_decisions[{position}].candidate_id", "calibration", "missing", "candidate id or null")
        elif decision.get("candidate_id") is not None and str(decision.get("candidate_id")) not in candidate_ids:
            issue(
                f"calibration_decisions[{position}].candidate_id",
                "calibration",
                decision.get("candidate_id"),
                "candidate id authored in this manifest",
            )
        if decision.get("source_equivalent_duplicate") is True:
            duplicate_ids = decision.get("duplicate_source_segment_ids")
            canonical_ids = decision.get("canonical_source_segment_ids")
            if not isinstance(duplicate_ids, list) or not duplicate_ids:
                issue(
                    f"calibration_decisions[{position}].duplicate_source_segment_ids",
                    "calibration",
                    duplicate_ids,
                    "one or more exact calibration target segment ids",
                )
            if not isinstance(canonical_ids, list) or not canonical_ids:
                issue(
                    f"calibration_decisions[{position}].canonical_source_segment_ids",
                    "calibration",
                    canonical_ids,
                    "one or more canonical candidate evidence segment ids",
                )
            if expected_segment_ids is not None:
                foreign = sorted({
                    str(segment_id)
                    for segment_id in [*(duplicate_ids or []), *(canonical_ids or [])]
                    if str(segment_id) not in expected_segment_ids
                })
                if foreign:
                    issue(
                        f"calibration_decisions[{position}]",
                        "source_scope",
                        foreign,
                        "segment ids from the current transcript",
                    )

    if require_adversarial_review:
        review = manifest.get("adversarial_review")
        if not isinstance(review, dict):
            issue("adversarial_review", "adversarial_review_required", review, "completed source-backed executor pass")
        else:
            reviewed = set(review.get("reviewed_categories", []))
            missing = sorted(set(ADVERSARIAL_REVIEW_CATEGORIES) - reviewed)
            if missing:
                issue("adversarial_review.reviewed_categories", "adversarial_review_incomplete", missing, "all required categories")
            expected_hash = authoring_decisions_sha256(manifest)
            if review.get("input_semantic_sha256") != expected_hash:
                issue("adversarial_review.input_semantic_sha256", "adversarial_review_stale", review.get("input_semantic_sha256"), expected_hash)
            if review.get("status") != "completed":
                issue("adversarial_review.status", "adversarial_review_incomplete", review.get("status"), "completed")
    return issues


def manifest_to_compact_payload(
    manifest: dict[str, Any],
    *,
    replace_existing_reviews: bool = False,
) -> dict[str, Any]:
    """Compile decisions to the existing compact-v3 input contract."""
    if isinstance(manifest.get("compatibility_payload"), dict):
        payload = copy.deepcopy(manifest["compatibility_payload"])
        payload.setdefault("calibration_decisions", copy.deepcopy(manifest.get("calibration_decisions", [])))
        if replace_existing_reviews:
            payload["_replace_existing_reviews"] = True
        return payload
    payload = {
        "payload_format": "gold_episode_compact_v3",
        "episode_video_id": manifest.get("episode_video_id"),
        "candidate_defaults": copy.deepcopy(manifest.get("candidate_defaults", {})),
        "type_defaults": copy.deepcopy(manifest.get("type_defaults", {})),
        "candidates": copy.deepcopy(manifest.get("candidates", [])),
        "zero_insight_chunks": copy.deepcopy(manifest.get("zero_insight_chunks", [])),
        "ledger_decisions": _compiled_source_dispositions(manifest),
        "risk_recall_acknowledgements": copy.deepcopy(manifest.get("risk_recall_acknowledgements", [])),
        "audit_warning_dispositions": copy.deepcopy(manifest.get("audit_warning_dispositions", [])),
        "calibration_decisions": copy.deepcopy(manifest.get("calibration_decisions", [])),
        "_authoring_manifest_semantic_sha256": manifest.get("semantic_sha256"),
    }
    if replace_existing_reviews:
        payload["_replace_existing_reviews"] = True
    return payload


def calibration_decision_issues(
    manifest: dict[str, Any],
    semantic_workbench: dict[str, Any],
) -> list[dict[str, Any]]:
    """Reject topic-only calibration links before the first packet."""
    decisions = {
        str(item.get("calibration_id")): item.get("candidate_id")
        for item in manifest.get("calibration_decisions", [])
        if isinstance(item, dict) and item.get("calibration_id")
    }
    bindings = {
        str(item.get("calibration_id")): item
        for item in semantic_workbench.get("calibration_bindings", [])
        if isinstance(item, dict) and item.get("calibration_id")
    }
    candidate_ranges = {
        str(item.get("candidate_id")): item.get("evidence_clean_index_ranges", [])
        for item in semantic_workbench.get("candidate_bindings", [])
        if isinstance(item, dict) and item.get("candidate_id")
    }
    issues: list[dict[str, Any]] = []

    def segment_clean_index(segment_id: Any) -> int | None:
        match = re.search(r"-transcript-(\d+)$", str(segment_id or ""))
        return int(match.group(1)) - 1 if match else None

    for calibration_id, binding in bindings.items():
        if calibration_id not in decisions:
            issues.append({
                "category": "calibration_decision_missing",
                "calibration_id": calibration_id,
                "issue": "authoring manifest must decide candidate equivalence or none",
            })
            continue
        declared = decisions[calibration_id]
        linked = {
            str(item.get("candidate_id")): item
            for item in binding.get("linked_candidates", [])
            if isinstance(item, dict) and item.get("candidate_id")
        }
        if declared is None:
            if binding.get("semantic_candidate_ids"):
                issues.append({
                    "category": "calibration_decision_mismatch",
                    "calibration_id": calibration_id,
                    "candidate_ids": binding.get("semantic_candidate_ids", []),
                    "issue": "manifest declares none but derived coverage links candidates",
                })
            continue
        declared_id = str(declared)
        result = linked.get(declared_id)
        decision = next(
            (
                item
                for item in manifest.get("calibration_decisions", [])
                if isinstance(item, dict) and str(item.get("calibration_id")) == calibration_id
            ),
            {},
        )
        if result is None and decision.get("proposition_equivalent") is True:
            target_ranges = binding.get("target_clean_index_ranges", [])
            evidence_ranges = candidate_ranges.get(declared_id, [])
            overlaps = [
                [max(int(target[0]), int(evidence[0])), min(int(target[1]), int(evidence[1]))]
                for target in target_ranges
                for evidence in evidence_ranges
                if (
                    isinstance(target, list) and len(target) == 2
                    and isinstance(evidence, list) and len(evidence) == 2
                    and max(int(target[0]), int(evidence[0])) <= min(int(target[1]), int(evidence[1]))
                )
            ]
            if overlaps:
                result = {
                    "candidate_id": declared_id,
                    "status": "needs_semantic_confirmation",
                    "evidence_intersection": overlaps,
                    "numeric_anchor_match": decision.get("numeric_anchor_match") is True,
                    "derived_from_explicit_manifest_decision": True,
                }
        explicit_equivalence = (
            decision.get("proposition_equivalent") is True
            and bool(str(decision.get("justification") or "").strip())
            and isinstance(result, dict)
            and bool(result.get("evidence_intersection"))
            and result.get("numeric_anchor_match") is True
        )
        duplicate_targets = set(str(item) for item in decision.get("duplicate_source_segment_ids") or [])
        target_segments = set(str(item) for item in binding.get("target_segment_ids") or [])
        canonical_indexes = [
            segment_clean_index(item)
            for item in decision.get("canonical_source_segment_ids") or []
        ]
        canonical_source_is_candidate_evidence = bool(canonical_indexes) and all(
            index is not None and any(
                isinstance(evidence, list)
                and len(evidence) == 2
                and int(evidence[0]) <= index <= int(evidence[1])
                for evidence in candidate_ranges.get(declared_id, [])
            )
            for index in canonical_indexes
        )
        explicit_duplicate_equivalence = (
            decision.get("source_equivalent_duplicate") is True
            and decision.get("proposition_equivalent") is True
            and bool(str(decision.get("justification") or "").strip())
            and isinstance(decision.get("duplicate_source_segment_ids"), list)
            and bool(decision.get("duplicate_source_segment_ids"))
            and isinstance(decision.get("canonical_source_segment_ids"), list)
            and bool(decision.get("canonical_source_segment_ids"))
            and duplicate_targets.issubset(target_segments)
            and decision.get("numeric_anchor_match") is True
            and canonical_source_is_candidate_evidence
        )
        if (result is None and not explicit_duplicate_equivalence) or (
            result is not None
            and result.get("status") != "covered"
            and not explicit_equivalence
            and not explicit_duplicate_equivalence
        ):
            issues.append({
                "category": "calibration_proposition_mismatch",
                "calibration_id": calibration_id,
                "candidate_ids": [declared_id],
                "issue": "calibration target is only thematic or lacks source/number equivalence",
                "binding": result,
            })
    return issues


def adversarial_authoring_view(
    manifest: dict[str, Any],
    report: dict[str, Any],
) -> dict[str, Any]:
    """One compact executor surface; navigation only, never an auditor."""
    workbench = report.get("semantic_workbench", {})
    core = {
        "schema_version": "1.0.0",
        "kind": "gold_adversarial_authoring_view",
        "episode_video_id": manifest.get("episode_video_id"),
        "input_semantic_sha256": authoring_decisions_sha256(manifest),
        "required_categories": list(ADVERSARIAL_REVIEW_CATEGORIES),
        "source_blocks": [
            item for item in workbench.get("coverage_blocks", [])
            if item.get("review_requirement") in {"must_close", "audit_only"}
        ],
        "candidate_bindings": workbench.get("candidate_bindings", []),
        "numeric_occurrence_matrix": report.get("numeric_occurrence_matrix", []),
        "calibration_bindings": workbench.get("calibration_bindings", []),
        "adjacent_boundaries": report.get("chunk_boundaries_to_review", []),
        "counterexamples_and_closure": [
            item for item in report.get("semantic_closure_index", [])
            if item.get("review_requirement") == "must_close"
        ],
        "host_or_interviewer_candidate_ids": sorted(set(
            report.get("candidate_with_promo_or_interviewer_language", [])
            + report.get("candidate_supported_only_by_interviewer_or_promo", [])
        )),
    }
    return {**core, "semantic_sha256": sha256_semantic_json(core)}
