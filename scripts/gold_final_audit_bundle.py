#!/usr/bin/env python
"""Build the compact, read-only evidence bundle used by the final gold audit."""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.export_gold_audit_packet import PACKET_OUTPUT_FILES
from scripts.gold_extraction_common import json_hashes, load_json, sha256_semantic_json, write_json
from scripts.gold_review_autocheck import (
    SEMANTIC_CLOSURE_CATEGORY,
    SEMANTIC_WORKBENCH_CATEGORY,
    autocheck,
    review_audit_warnings,
    source_complete_invariant_issues,
)


DOSSIER_NAVIGATION_TARGET_BYTES = 500_000
DOSSIER_TRANSCRIPT_BLOCK_SIZE = 200
DOSSIER_TRANSCRIPT_COLUMNS_V3 = [
    "clean_index", "start_seconds", "duration_seconds", "text",
    "ledger_disposition", "ledger_candidate_ids", "ledger_reason_code", "ledger_reason_reference",
]
DOSSIER_CANDIDATE_COLUMNS = [
    "candidate_id", "chunk_id", "title", "type", "themes", "subthemes", "process_tags",
    "source_claim", "takeaway_applicavel", "context", "reported_case", "causal_certainty",
    "claim_risk", "numbers", "steps", "conditions", "caveats", "relations",
    "minimal_clean_indexes", "support_clean_indexes",
]
DOSSIER_LEDGER_GROUP_COLUMNS = [
    "disposition", "candidate_ids", "reason_code", "reason_reference", "clean_indexes",
]


def _ledger_candidate_ids(item: dict[str, Any]) -> list[str]:
    candidate_ids = item.get("candidate_ids")
    if isinstance(candidate_ids, list):
        return sorted(str(value) for value in candidate_ids if value)
    candidate_id = item.get("candidate_id")
    return [str(candidate_id)] if candidate_id else []


def _compact_warning_references(
    warnings: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, str]]:
    justifications: dict[str, str] = {}
    columns = [
        "category", "kind", "warning_id", "closure_id", "lineage_id", "closure_kind",
        "issue", "candidate_ids", "segment_ids", "clean_index_range", "review_requirement",
        "disposition", "destination_candidate_ids", "justification_ref",
    ]
    rows: list[list[Any]] = []
    seen_rows_by_warning_id: dict[str, str] = {}
    identity_collisions: list[str] = []
    for group in warnings:
        for item in group.get("items", []):
            if not isinstance(item, dict):
                continue
            review = item.get("review", {}) if isinstance(item.get("review"), dict) else {}
            justification = str(review.get("justification", "")).strip()
            justification_ref = None
            if justification:
                justification_ref = "J" + sha256_semantic_json(justification)[:12]
                justifications[justification_ref] = justification
            row = [
                group.get("category"), group.get("kind"), item.get("warning_id"),
                item.get("closure_id"), item.get("lineage_id"), item.get("closure_kind"),
                item.get("issue"),
                item.get("candidate_ids") or ([item.get("candidate_id")] if item.get("candidate_id") else []),
                item.get("segment_ids") or ([item.get("segment_id")] if item.get("segment_id") else []),
                item.get("clean_index_range"), item.get("review_requirement"),
                review.get("disposition"),
                review.get("candidate_ids") or review.get("destination_candidate_ids") or [],
                justification_ref,
            ]
            warning_id = str(item.get("warning_id", ""))
            row_hash = sha256_semantic_json(row)
            prior_hash = seen_rows_by_warning_id.get(warning_id)
            if warning_id and prior_hash == row_hash:
                continue
            if warning_id and prior_hash is not None:
                identity_collisions.append(warning_id)
            if warning_id:
                seen_rows_by_warning_id[warning_id] = row_hash
            rows.append(row)
    return {
        "columns": columns,
        "rows": rows,
        "item_count": len(rows),
        "identity_collisions": sorted(set(identity_collisions)),
    }, dict(sorted(justifications.items()))


def _compact_risk_recall_clusters(clusters: list[dict[str, Any]]) -> dict[str, Any]:
    columns = [
        "cluster_id", "source_cluster_id", "clean_index_range", "segment_ids",
        "signal_types", "score", "prominence_cues", "exclusion_reasons",
    ]
    return {
        "columns": columns,
        "rows": [[item.get(key) for key in columns] for item in clusters],
        "cluster_count": len(clusters),
    }


def _compact_semantic_workbench(workbench: dict[str, Any]) -> dict[str, Any]:
    """Retain one auditable reference map while dropping duplicated source prose."""
    coverage_columns = (
        "block_id", "clean_index_range", "segment_count", "state", "candidate_ids",
        "signal_types", "reason_codes", "risk_score", "risk_tier", "risk_reasons",
        "review_requirement",
    )
    candidate_columns = (
        "candidate_id", "evidence_clean_index_ranges", "evidence_segment_count",
        "claim_term_count", "proposition_overlap_ratio", "number_record_count",
        "caveat_count", "calibration_ids", "requires_review", "structural_missing_evidence",
    )
    calibration_columns = (
        "calibration_id", "target_clean_index_ranges", "target_segment_ids",
        "semantic_candidate_ids", "requires_review",
    )
    review_columns = (
        "closure_kind", "closure_id", "lineage_id", "issue", "block_id",
        "candidate_ids", "segment_ids", "clean_index_range", "state",
        "risk_score", "risk_tier", "risk_reasons", "review_requirement",
    )
    core = {
        "schema_version": "1.1.0-compact",
        "coverage_columns": list(coverage_columns),
        "coverage_rows": [
            [item.get(key) for key in coverage_columns]
            for item in workbench.get("coverage_blocks", [])
        ],
        "candidate_binding_columns": list(candidate_columns),
        "candidate_binding_rows": [
            [item.get(key) for key in candidate_columns]
            for item in workbench.get("candidate_bindings", [])
        ],
        "calibration_binding_columns": list(calibration_columns),
        "calibration_binding_rows": [
            [item.get(key) for key in calibration_columns]
            for item in workbench.get("calibration_bindings", [])
        ],
        "review_columns": list(review_columns),
        "review_order_rows": [
            [item.get(key) for key in review_columns]
            for item in workbench.get("review_order", [])
        ],
        "review_overflow_rows": [
            [item.get(key) for key in review_columns]
            for item in workbench.get("review_overflow", [])
        ],
        "summary": workbench.get("summary", {}),
        "source_workbench_semantic_sha256": workbench.get("semantic_sha256"),
    }
    return {**core, "semantic_sha256": sha256_semantic_json(core)}


def _ledger_groups(ledger: list[dict[str, Any]], index_by_id: dict[str, int]) -> list[list[Any]]:
    grouped: dict[tuple[Any, ...], list[int]] = {}
    for item in ledger:
        segment_id = item.get("segment_id")
        if segment_id not in index_by_id:
            continue
        key = (
            str(item.get("disposition", "missing")),
            tuple(_ledger_candidate_ids(item)),
            item.get("reason_code"),
            item.get("reason_reference"),
        )
        grouped.setdefault(key, []).append(index_by_id[segment_id])
    return [
        [disposition, list(candidate_ids), reason_code, reason_reference, sorted(clean_indexes)]
        for (disposition, candidate_ids, reason_code, reason_reference), clean_indexes in sorted(
            grouped.items(), key=lambda value: (value[0][0], value[0][1], str(value[0][2]), str(value[0][3]))
        )
    ]


def _packet_snapshot(packet: Path) -> dict[str, Any]:
    files = sorted(path for path in packet.iterdir() if path.is_file()) if packet.is_dir() else []
    return {
        "valid_five_file_packet": {path.name for path in files} == PACKET_OUTPUT_FILES,
        "names": [path.name for path in files],
        "files": [{"name": path.name, **json_hashes(path)} for path in files],
    }


def build_audit_bundle(
    video_id: str,
    data_root: Path,
    *,
    packet: Path,
    audit_warnings: list[dict[str, Any]] | None = None,
    revision_id: str | None = None,
) -> dict[str, Any]:
    out = data_root / "processed" / video_id / "gold_extraction"
    document = load_json(out / "insights_exhaustive.json")
    ledger = load_json(out / "high_signal_coverage_ledger.json").get("entries", [])
    calibration = load_json(out / "calibration_tests.json")
    fingerprints = load_json(out / "protected_fingerprints.json")
    candidates = []
    for item in document.get("insights", []):
        evidence = item.get("evidence", {})
        candidates.append({
            "candidate_id": item.get("candidate_id"),
            "title": item.get("title"),
            "type": item.get("type"),
            "themes": item.get("themes", []),
            "source_claim": item.get("source_claim"),
            "takeaway_applicavel": item.get("takeaway_applicavel"),
            "numbers": item.get("numbers", []),
            "caveats": item.get("caveats", []),
            "relations": item.get("relations", {}),
            "minimal_evidence": [
                {"segment_id": quote.get("segment_id"), "quote_verbatim": quote.get("quote_verbatim")}
                for quote in evidence.get("minimal_quote", [])
            ],
        })
    disposition_counts = Counter(str(item.get("disposition", "missing")) for item in ledger)
    calibration_tests = [{
        "calibration_id": item.get("calibration_id"),
        "segment_ids": item.get("segment_ids", []),
        "semantic_candidate_ids": item.get("semantic_candidate_ids", []),
        "semantic_coverage": item.get("semantic_coverage"),
    } for item in calibration.get("tests", [])]
    packet_snapshot = _packet_snapshot(packet)
    bundle = {
        "schema_version": "1.0.0",
        "episode_video_id": video_id,
        "revision_id": revision_id,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "audit_warnings": audit_warnings or [],
        "ledger": {
            "entry_count": len(ledger),
            "disposition_counts": dict(sorted(disposition_counts.items())),
            "unresolved_segment_ids": [
                item.get("segment_id") for item in ledger
                if item.get("disposition") not in {"captured", "merged", "excluded"}
            ],
        },
        "calibration": {
            "status": calibration.get("status"),
            "covered_count": calibration.get("covered_count"),
            "minimum_required": calibration.get("minimum_required"),
            "duplicate_target_segments": calibration.get("duplicate_target_segments", []),
            "tests": calibration_tests,
        },
        "protected_fingerprints": fingerprints,
        "packet": packet_snapshot,
    }
    bundle["semantic_sha256"] = sha256_semantic_json(bundle)
    return bundle


def write_audit_bundle(path: Path, bundle: dict[str, Any]) -> None:
    write_json(path, bundle)


def build_audit_dossier(
    video_id: str,
    data_root: Path,
    *,
    packet: Path,
    audit_warnings: list[dict[str, Any]] | None = None,
    revision_id: str | None = None,
) -> dict[str, Any]:
    """Return one source-complete, de-duplicated audit surface."""
    out = data_root / "processed" / video_id / "gold_extraction"
    transcript = load_json(out / "transcript_clean.json").get("segments", [])
    document = load_json(out / "insights_exhaustive.json")
    ledger = load_json(out / "high_signal_coverage_ledger.json").get("entries", [])
    calibration = load_json(out / "calibration_tests.json")
    fingerprints = load_json(out / "protected_fingerprints.json")
    index_by_id = {item["segment_id"]: int(item["clean_index"]) for item in transcript}
    ledger_by_segment = {str(item.get("segment_id")): item for item in ledger if item.get("segment_id")}
    transcript_rows = []
    for item in transcript:
        decision = ledger_by_segment.get(str(item["segment_id"]), {})
        transcript_rows.append([
            int(item["clean_index"]), float(item["start_seconds"]),
            float(item.get("duration_seconds", 0.0)), item["text"],
            decision.get("disposition"), _ledger_candidate_ids(decision),
            decision.get("reason_code"), decision.get("reason_reference"),
        ])
    candidate_rows: list[list[Any]] = []
    for candidate in document.get("insights", []):
        evidence = candidate.get("evidence", {})
        minimal = [index_by_id[item["segment_id"]] for item in evidence.get("minimal_quote", []) if item.get("segment_id") in index_by_id]
        support = [index_by_id[item["segment_id"]] for item in evidence.get("support_segments", []) if item.get("segment_id") in index_by_id]
        row_values = {**candidate, "minimal_clean_indexes": minimal, "support_clean_indexes": support}
        candidate_rows.append([row_values.get(column) for column in DOSSIER_CANDIDATE_COLUMNS])
    minimal_index_position = DOSSIER_CANDIDATE_COLUMNS.index("minimal_clean_indexes")
    candidate_id_position = DOSSIER_CANDIDATE_COLUMNS.index("candidate_id")
    candidate_rows.sort(key=lambda row: (
        min(row[minimal_index_position]) if row[minimal_index_position] else 10**12,
        str(row[candidate_id_position]),
    ))
    calibration_rows = [{
        "calibration_id": item.get("calibration_id"),
        "clean_indexes": [index_by_id[segment_id] for segment_id in item.get("segment_ids", []) if segment_id in index_by_id],
        "quote_verbatim": item.get("quote_verbatim"),
        "semantic_candidate_ids": item.get("semantic_candidate_ids", []),
        "semantic_coverage": item.get("semantic_coverage"),
    } for item in calibration.get("tests", [])]
    ledger_groups = _ledger_groups(ledger, index_by_id)
    report = autocheck(video_id, data_root)
    if audit_warnings is None:
        receipt_path = out / "gold_finalization_receipt.json"
        dispositions = (
            load_json(receipt_path).get("input_signature", {}).get("audit_warning_dispositions", [])
            if receipt_path.is_file() else []
        )
        warnings, _warning_inventory, warning_gate = review_audit_warnings(
            report.get("audit_warnings", []),
            dispositions,
            required_categories={
                "claim_evidence_alignment", SEMANTIC_CLOSURE_CATEGORY, SEMANTIC_WORKBENCH_CATEGORY,
            },
        )
    else:
        warnings = audit_warnings
        warning_gate = []
    source_complete_issues = source_complete_invariant_issues(
        report,
        reviewed_warnings=warnings,
        review_gate=warning_gate,
    )
    if source_complete_issues:
        raise ValueError(
            "audit dossier requires a source-complete final state: "
            + "; ".join(str(item.get("issue")) for item in source_complete_issues)
        )
    dossier_warnings, warning_justifications = _compact_warning_references(warnings)
    compact_workbench = _compact_semantic_workbench(report.get("semantic_workbench", {}))
    header = {
        "kind": "gold_final_audit_dossier",
        "schema_version": "3.2.0",
        "episode_video_id": video_id,
        "revision_id": revision_id,
        "transcript_columns": DOSSIER_TRANSCRIPT_COLUMNS_V3,
        "transcript_block_size": DOSSIER_TRANSCRIPT_BLOCK_SIZE,
        "candidate_columns": DOSSIER_CANDIDATE_COLUMNS,
        "ledger_group_columns": DOSSIER_LEDGER_GROUP_COLUMNS,
        "segment_count": len(transcript_rows),
        "candidate_count": len(candidate_rows),
        "calibration_count": len(calibration_rows),
        "ledger_entry_count": len(ledger),
        "ledger_group_count": len(ledger_groups),
        "ledger_disposition_counts": dict(sorted(Counter(str(item.get("disposition", "missing")) for item in ledger).items())),
        "calibration": {
            "status": calibration.get("status"),
            "covered_count": calibration.get("covered_count"),
            "minimum_required": calibration.get("minimum_required"),
            "duplicate_target_segments": calibration.get("duplicate_target_segments", []),
        },
        "hard_blockers": report.get("hard_blockers", []),
        "audit_warnings": dossier_warnings,
        "audit_warning_justifications": warning_justifications,
        "numeric_coverage": {
            "candidate_count": len(report.get("numeric_coverage", [])),
            "missing_material_count": sum(
                len(item.get("missing_material", []))
                for item in report.get("numeric_coverage", [])
            ),
            "warning_count": sum(
                len(item.get("audit_warnings", []))
                for item in report.get("numeric_coverage", [])
            ),
        },
        "semantic_workbench": {
            "semantic_sha256": compact_workbench.get("semantic_sha256"),
            "source_workbench_semantic_sha256": compact_workbench.get("source_workbench_semantic_sha256"),
            "summary": compact_workbench.get("summary", {}),
        },
        "risk_recall_clusters": _compact_risk_recall_clusters(report.get("risk_recall_clusters", [])),
        "protected_fingerprints": fingerprints,
        "packet": _packet_snapshot(packet),
    }
    records = [
        {"record_type": "header", **header},
        {"record_type": "semantic_workbench", "value": compact_workbench},
        *({"record_type": "candidate", "value": row} for row in candidate_rows),
        *(
            {"record_type": "numeric_coverage", "value": item}
            for item in report.get("numeric_coverage", [])
        ),
        *({"record_type": "calibration", "value": row} for row in calibration_rows),
        *(
            {"record_type": "transcript_block", "value": transcript_rows[start:start + DOSSIER_TRANSCRIPT_BLOCK_SIZE]}
            for start in range(0, len(transcript_rows), DOSSIER_TRANSCRIPT_BLOCK_SIZE)
        ),
        *({"record_type": "ledger_group", "value": row} for row in ledger_groups),
    ]
    content_hash = sha256_semantic_json(records)
    footer = {
        "record_type": "footer",
        "record_count": len(records) + 1,
        "content_semantic_sha256": content_hash,
    }
    return {"records": [*records, footer], "semantic_sha256": content_hash}


def write_audit_dossier(path: Path, dossier: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for record in dossier["records"]:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    temporary.replace(path)
    size = path.stat().st_size
    return {
        "path": str(path),
        "bytes": size,
        "navigation_target_bytes": DOSSIER_NAVIGATION_TARGET_BYTES,
        "within_navigation_target": size <= DOSSIER_NAVIGATION_TARGET_BYTES,
        **json_hashes_jsonl(path, dossier["semantic_sha256"]),
    }


def json_hashes_jsonl(path: Path, semantic_sha256: str) -> dict[str, str]:
    import hashlib
    return {"physical_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "semantic_sha256": semantic_sha256}


def numeric_coverage_source_projection(coverage: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Project the immutable source binding out of versioned classifications.

    A sealed dossier must remain verifiable after the numeric classifier is
    strengthened. Candidate content already proves the complete number matrix;
    this projection proves that every evidence occurrence in the dossier still
    binds to the same source and record without treating a later disposition,
    severity or diagnostic message as protected historical content.
    """
    projected: list[dict[str, Any]] = []
    for candidate in coverage:
        mentions = []
        for mention in candidate.get("mentions") or []:
            if mention.get("layer") == "record":
                # Synthetic diagnostics for unused records are derived from the
                # candidate matrix, which is compared independently above.
                continue
            mentions.append({
                key: copy.deepcopy(mention.get(key))
                for key in (
                    "segment_id", "layer", "raw", "canonical", "kind",
                    "record_index", "record",
                )
            })
        projected.append({
            "candidate_id": candidate.get("candidate_id"),
            "record_count": candidate.get("record_count"),
            "mentions": mentions,
        })
    return projected


def validate_audit_dossier(path: Path, video_id: str, data_root: Path, packet: Path) -> list[str]:
    errors: list[str] = []
    try:
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"audit dossier is unreadable: {exc}"]
    if len(records) < 2 or records[0].get("record_type") != "header" or records[-1].get("record_type") != "footer":
        return ["audit dossier header or footer is missing"]
    header, footer = records[0], records[-1]
    if header.get("episode_video_id") != video_id:
        errors.append("audit dossier episode identity mismatch")
    if footer.get("record_count") != len(records) or footer.get("content_semantic_sha256") != sha256_semantic_json(records[:-1]):
        errors.append("audit dossier semantic receipt is invalid")
    out = data_root / "processed" / video_id / "gold_extraction"
    transcript = load_json(out / "transcript_clean.json").get("segments", [])
    index_by_id = {item["segment_id"]: int(item["clean_index"]) for item in transcript}
    expected_source_rows = [[int(item["clean_index"]), float(item["start_seconds"]), float(item.get("duration_seconds", 0.0)), item["text"]] for item in transcript]
    actual_rows = [item.get("value") for item in records if item.get("record_type") == "transcript"]
    for item in records:
        if item.get("record_type") == "transcript_block":
            actual_rows.extend(item.get("value") or [])
    actual_source_rows = [row[:4] for row in actual_rows if isinstance(row, list)]
    if actual_source_rows != expected_source_rows or len(actual_source_rows) != len(actual_rows):
        errors.append("audit dossier transcript is not source-complete and verbatim")
    document_candidates = load_json(out / "insights_exhaustive.json").get("insights", [])
    expected_ids = sorted(item.get("candidate_id") for item in document_candidates)
    candidate_columns = header.get("candidate_columns", [])
    candidate_id_index = candidate_columns.index("candidate_id") if "candidate_id" in candidate_columns else None
    actual_ids = []
    for item in records:
        if item.get("record_type") != "candidate":
            continue
        value = item.get("value")
        if isinstance(value, list) and candidate_id_index is not None and len(value) > candidate_id_index:
            actual_ids.append(value[candidate_id_index])
        elif isinstance(value, dict):
            actual_ids.append(value.get("candidate_id"))
    actual_ids.sort()
    if actual_ids != expected_ids:
        errors.append("audit dossier candidate inventory differs from final gold")
    expected_candidate_rows = []
    for candidate in document_candidates:
        evidence = candidate.get("evidence", {})
        row_values = {
            **candidate,
            "minimal_clean_indexes": [
                index_by_id[item["segment_id"]] for item in evidence.get("minimal_quote", [])
                if item.get("segment_id") in index_by_id
            ],
            "support_clean_indexes": [
                index_by_id[item["segment_id"]] for item in evidence.get("support_segments", [])
                if item.get("segment_id") in index_by_id
            ],
        }
        expected_candidate_rows.append([row_values.get(column) for column in DOSSIER_CANDIDATE_COLUMNS])
    expected_candidate_rows.sort(key=lambda row: (
        min(row[DOSSIER_CANDIDATE_COLUMNS.index("minimal_clean_indexes")])
        if row[DOSSIER_CANDIDATE_COLUMNS.index("minimal_clean_indexes")] else 10**12,
        str(row[DOSSIER_CANDIDATE_COLUMNS.index("candidate_id")]),
    ))
    actual_candidate_rows = [item.get("value") for item in records if item.get("record_type") == "candidate"]
    if actual_candidate_rows != expected_candidate_rows:
        errors.append("audit dossier candidate content differs from final gold")
    actual_numeric_coverage = [
        item.get("value")
        for item in records
        if item.get("record_type") == "numeric_coverage"
    ]
    expected_numeric_coverage = autocheck(video_id, data_root).get("numeric_coverage", [])
    if numeric_coverage_source_projection(actual_numeric_coverage) != numeric_coverage_source_projection(expected_numeric_coverage):
        errors.append("audit dossier numeric coverage differs from final gold")
    if header.get("numeric_coverage", {}).get("missing_material_count") != 0:
        errors.append("audit dossier contains unresolved material numeric evidence")
    warning_surface = header.get("audit_warnings", {})
    if isinstance(warning_surface, dict) and warning_surface.get("identity_collisions"):
        errors.append("audit dossier warning identities collide with different local inputs")
    expected_ledger = load_json(out / "high_signal_coverage_ledger.json").get("entries", [])
    expected_ledger_by_index = {
        index_by_id[item["segment_id"]]: (
            str(item.get("disposition", "missing")),
            tuple(_ledger_candidate_ids(item)),
            item.get("reason_code"),
            item.get("reason_reference"),
        )
        for item in expected_ledger
        if item.get("segment_id") in index_by_id
    }
    actual_ledger_by_index: dict[int, tuple[Any, ...]] = {}
    for item in records:
        if item.get("record_type") != "ledger_group":
            continue
        value = item.get("value") or []
        if not isinstance(value, list) or len(value) != len(DOSSIER_LEDGER_GROUP_COLUMNS):
            errors.append("audit dossier ledger group is malformed")
            continue
        disposition, candidate_ids, reason_code, reason_reference, clean_indexes = value
        identity = (str(disposition), tuple(sorted(candidate_ids or [])), reason_code, reason_reference)
        for clean_index in clean_indexes or []:
            if clean_index in actual_ledger_by_index:
                errors.append("audit dossier ledger contains duplicate clean indexes")
            actual_ledger_by_index[int(clean_index)] = identity
    if actual_ledger_by_index != expected_ledger_by_index:
        errors.append("audit dossier ledger inventory differs from final gold")
    if header.get("schema_version") in {"3.0.0", "3.1.0", "3.2.0"}:
        inline_ledger_by_index = {
            int(row[0]): (str(row[4]), tuple(sorted(row[5] or [])), row[6], row[7])
            for row in actual_rows
            if isinstance(row, list) and len(row) == len(DOSSIER_TRANSCRIPT_COLUMNS_V3) and row[4] is not None
        }
        if inline_ledger_by_index != expected_ledger_by_index:
            errors.append("audit dossier inline transcript ledger differs from final gold")
    expected_calibration_rows = [{
        "calibration_id": item.get("calibration_id"),
        "clean_indexes": [index_by_id[segment_id] for segment_id in item.get("segment_ids", []) if segment_id in index_by_id],
        "quote_verbatim": item.get("quote_verbatim"),
        "semantic_candidate_ids": item.get("semantic_candidate_ids", []),
        "semantic_coverage": item.get("semantic_coverage"),
    } for item in load_json(out / "calibration_tests.json").get("tests", [])]
    actual_calibration_rows = [item.get("value") for item in records if item.get("record_type") == "calibration"]
    if actual_calibration_rows != expected_calibration_rows:
        errors.append("audit dossier calibration differs from final gold")
    if header.get("schema_version") in {"3.1.0", "3.2.0"}:
        workbench_records = [
            item.get("value") for item in records if item.get("record_type") == "semantic_workbench"
        ]
        source_workbench = autocheck(video_id, data_root).get("semantic_workbench", {})
        expected_workbench = (
            _compact_semantic_workbench(source_workbench)
            if header.get("schema_version") == "3.2.0"
            else source_workbench
        )
        if workbench_records != [expected_workbench]:
            errors.append("audit dossier semantic workbench differs from final gold")
        elif header.get("semantic_workbench", {}).get("semantic_sha256") != expected_workbench.get("semantic_sha256"):
            errors.append("audit dossier semantic workbench receipt is stale")
    if header.get("packet") != _packet_snapshot(packet) or not header.get("packet", {}).get("valid_five_file_packet"):
        errors.append("audit dossier packet identity is stale or invalid")
    return errors


def _read_dossier(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if len(records) < 2 or records[0].get("record_type") != "header" or records[-1].get("record_type") != "footer":
        raise ValueError("audit dossier header or footer is missing")
    if records[-1].get("content_semantic_sha256") != sha256_semantic_json(records[:-1]):
        raise ValueError("audit dossier semantic receipt is invalid")
    return records[0], records


def audit_impact_set(audit: dict[str, Any]) -> dict[str, Any]:
    """Derive the closed local revalidation scope from sealed audit findings."""
    candidate_ids: set[str] = set()
    clean_index_ranges: set[tuple[int, int]] = set()
    warning_ids: set[str] = set()
    calibration_ids: set[str] = set()
    categories: set[str] = set()
    numeric = False
    relations = False
    for finding in audit.get("findings", []):
        if not isinstance(finding, dict):
            continue
        category = str(finding.get("category", ""))
        required = str(finding.get("required_action", ""))
        categories.add(category)
        candidate_ids.update(
            str(value)
            for key in ("candidate_ids", "target_candidate_ids")
            for value in (finding.get(key) or [])
            if value
        )
        raw_range = finding.get("segment_range") or finding.get("clean_index_range") or []
        if isinstance(raw_range, list) and len(raw_range) == 2:
            clean_index_ranges.add((int(raw_range[0]), int(raw_range[1])))
        warning_ids.update(str(value) for value in finding.get("warning_ids", []) if value)
        calibration_ids.update(str(value) for value in finding.get("calibration_ids", []) if value)
        combined = f"{category} {required}".lower()
        numeric = numeric or any(token in combined for token in ("numeric", "number", "percent", "price", "valor"))
        relations = relations or any(token in combined for token in ("relation", "parent", "child", "duplicate"))
    core = {
        "candidate_ids": sorted(candidate_ids),
        "clean_index_ranges": [list(value) for value in sorted(clean_index_ranges)],
        "warning_ids": sorted(warning_ids),
        "calibration_ids": sorted(calibration_ids),
        "categories": sorted(categories),
        "numeric_revalidation": numeric,
        "relation_revalidation": relations,
    }
    return {**core, "semantic_sha256": sha256_semantic_json(core)}


def build_reaudit_delta(
    before_path: Path,
    after_path: Path,
    audit: dict[str, Any],
    *,
    impact_closure: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a focal reaudit surface with full-episode invariant proofs."""
    before_header, before_records = _read_dossier(before_path)
    after_header, after_records = _read_dossier(after_path)
    video_id = str(audit.get("episode_video_id", ""))
    if before_header.get("episode_video_id") != video_id or after_header.get("episode_video_id") != video_id:
        raise ValueError("reaudit delta episode identity mismatch")
    impact_set = audit_impact_set(audit)
    if impact_closure:
        merged_core = {
            "candidate_ids": sorted(set(impact_set["candidate_ids"]) | {
                str(value) for value in impact_closure.get("candidate_ids", []) if value
            }),
            "clean_index_ranges": [
                list(value) for value in sorted({
                    tuple(int(item) for item in value)
                    for source in (impact_set.get("clean_index_ranges", []), impact_closure.get("clean_index_ranges", []))
                    for value in source
                    if isinstance(value, list) and len(value) == 2
                })
            ],
            "warning_ids": sorted(set(impact_set["warning_ids"]) | {
                str(value) for value in impact_closure.get("warning_ids", []) if value
            }),
            "calibration_ids": sorted(set(impact_set["calibration_ids"]) | {
                str(value) for value in impact_closure.get("calibration_ids", []) if value
            }),
            "categories": sorted(set(impact_set["categories"]) | {
                str(value) for value in impact_closure.get("categories", []) if value
            }),
            "numeric_revalidation": bool(
                impact_set.get("numeric_revalidation")
                or impact_closure.get("numeric_revalidation")
            ),
            "relation_revalidation": bool(
                impact_set.get("relation_revalidation")
                or impact_closure.get("relation_revalidation")
            ),
        }
        impact_set = {**merged_core, "semantic_sha256": sha256_semantic_json(merged_core)}
    affected_ids: set[str] = set(impact_set["candidate_ids"])
    affected_indexes: set[int] = {
        index
        for value in impact_set.get("clean_index_ranges", [])
        if isinstance(value, list) and len(value) == 2
        for index in range(int(value[0]), int(value[1]) + 1)
    }
    calibration_may_change = bool(impact_set.get("calibration_ids"))
    finding_rows = []
    for finding in audit.get("findings", []):
        if not isinstance(finding, dict):
            continue
        candidate_ids = {
            str(value) for key in ("candidate_ids", "target_candidate_ids")
            for value in (finding.get(key) or []) if value
        }
        affected_ids.update(candidate_ids)
        raw_range = finding.get("segment_range") or finding.get("clean_index_range") or []
        if isinstance(raw_range, list) and len(raw_range) == 2:
            affected_indexes.update(range(int(raw_range[0]), int(raw_range[1]) + 1))
        required = f"{finding.get('category', '')} {finding.get('required_action', '')}".lower()
        calibration_may_change = calibration_may_change or "calibr" in required
        finding_rows.append({
            "finding_id": finding.get("finding_id") or finding.get("id"),
            "required_action": finding.get("required_action"),
            "candidate_ids": sorted(candidate_ids),
            "segment_range": raw_range,
        })

    def candidate_map(header: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
        columns = header.get("candidate_columns", DOSSIER_CANDIDATE_COLUMNS)
        position = columns.index("candidate_id")
        return {
            str(item["value"][position]): item["value"]
            for item in records
            if item.get("record_type") == "candidate" and isinstance(item.get("value"), list)
        }

    def transcript_hash(records: list[dict[str, Any]]) -> str:
        rows = [row[:4] for item in records if item.get("record_type") == "transcript_block" for row in item.get("value", [])]
        return sha256_semantic_json(rows)

    def ledger_outside_hash(records: list[dict[str, Any]]) -> str:
        rows = []
        for item in records:
            if item.get("record_type") != "ledger_group" or not isinstance(item.get("value"), list):
                continue
            row = list(item["value"])
            row[-1] = [index for index in row[-1] if int(index) not in affected_indexes]
            if row[-1]:
                rows.append(row)
        return sha256_semantic_json(rows)

    before_candidates = candidate_map(before_header, before_records)
    after_candidates = candidate_map(after_header, after_records)
    candidate_columns = after_header.get("candidate_columns", DOSSIER_CANDIDATE_COLUMNS)
    minimal_position = candidate_columns.index("minimal_clean_indexes")
    support_position = candidate_columns.index("support_clean_indexes")
    changed_ids = {
        candidate_id
        for candidate_id in set(before_candidates) | set(after_candidates)
        if before_candidates.get(candidate_id) != after_candidates.get(candidate_id)
    }
    range_scoped_ids: set[str] = set()
    for candidate_id in changed_ids:
        row = after_candidates.get(candidate_id) or before_candidates.get(candidate_id)
        if not isinstance(row, list):
            continue
        evidence_indexes = {
            int(value)
            for position in (minimal_position, support_position)
            for value in (row[position] or [])
        }
        if evidence_indexes & affected_indexes:
            range_scoped_ids.add(candidate_id)
    explicit_ids = set(affected_ids)
    affected_ids.update(changed_ids)
    unscoped_changed_ids = sorted(changed_ids - explicit_ids - range_scoped_ids)
    unaffected_before = {key: value for key, value in before_candidates.items() if key not in affected_ids}
    unaffected_after = {key: value for key, value in after_candidates.items() if key not in affected_ids}

    def protected_content(header: dict[str, Any], endpoint: str) -> dict[str, Any]:
        fingerprints = header.get("protected_fingerprints", {})
        if not isinstance(fingerprints, dict):
            return {}
        selected = fingerprints.get(endpoint)
        if isinstance(selected, dict):
            return selected
        return {
            key: value for key, value in fingerprints.items()
            if key not in {"verified_at", "generated_at", "checked_at"}
        }

    invariants = {
        "transcript": [transcript_hash(before_records), transcript_hash(after_records)],
        "unaffected_candidates": [sha256_semantic_json(unaffected_before), sha256_semantic_json(unaffected_after)],
        "ledger_outside_findings": [ledger_outside_hash(before_records), ledger_outside_hash(after_records)],
        "protected_fingerprints": [
            sha256_semantic_json(protected_content(before_header, "before")),
            sha256_semantic_json(protected_content(after_header, "after")),
        ],
    }
    if not calibration_may_change:
        invariants["calibration"] = [
            sha256_semantic_json([item.get("value") for item in before_records if item.get("record_type") == "calibration"]),
            sha256_semantic_json([item.get("value") for item in after_records if item.get("record_type") == "calibration"]),
        ]
    invariant_errors = [name for name, pair in invariants.items() if pair[0] != pair[1]]
    if unscoped_changed_ids:
        invariant_errors.append("changed_candidates_outside_findings")
    core = {
        "schema_version": "1.0.0",
        "kind": "gold_final_reaudit_delta",
        "episode_video_id": video_id,
        "findings": finding_rows,
        "impact_set": impact_set,
        "affected_candidate_ids": sorted(affected_ids),
        "changed_candidate_ids": sorted(changed_ids),
        "range_scoped_candidate_ids": sorted(range_scoped_ids),
        "unscoped_changed_candidate_ids": unscoped_changed_ids,
        "affected_clean_indexes": sorted(affected_indexes),
        "before_affected_candidates": {key: before_candidates.get(key) for key in sorted(affected_ids)},
        "after_affected_candidates": {key: after_candidates.get(key) for key in sorted(affected_ids)},
        "invariants": invariants,
        "invariant_errors": invariant_errors,
        "packet_snapshots": {
            "before": before_header.get("packet"),
            "after": after_header.get("packet"),
        },
        "before_dossier_semantic_sha256": before_records[-1].get("content_semantic_sha256"),
        "after_dossier_semantic_sha256": after_records[-1].get("content_semantic_sha256"),
    }
    return {**core, "semantic_sha256": sha256_semantic_json(core)}


def validate_reaudit_delta(delta: dict[str, Any]) -> list[str]:
    core = {key: value for key, value in delta.items() if key != "semantic_sha256"}
    errors = []
    if delta.get("semantic_sha256") != sha256_semantic_json(core):
        errors.append("reaudit delta semantic hash is invalid")
    errors.extend(f"reaudit invariant changed: {name}" for name in delta.get("invariant_errors", []))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id")
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--revision-id")
    parser.add_argument("--dossier", action="store_true", help="Write the complete compact JSONL audit dossier.")
    parser.add_argument("--reaudit-delta", action="store_true", help="Write a focal reaudit delta with full invariant proofs.")
    parser.add_argument("--before-dossier", type=Path)
    parser.add_argument("--after-dossier", type=Path)
    parser.add_argument("--audit-input", type=Path)
    args = parser.parse_args()
    if args.reaudit_delta:
        if not args.before_dossier or not args.after_dossier or not args.audit_input:
            parser.error("--reaudit-delta requires --before-dossier, --after-dossier, and --audit-input")
        artifact = build_reaudit_delta(args.before_dossier, args.after_dossier, load_json(args.audit_input))
        write_json(args.output, artifact)
        errors = validate_reaudit_delta(artifact)
        identity = {"path": str(args.output), "semantic_sha256": artifact["semantic_sha256"]}
    elif args.dossier:
        if not args.video_id or args.data_root is None or args.packet is None:
            parser.error("--dossier requires --video-id, --data-root, and --packet")
        artifact = build_audit_dossier(args.video_id, args.data_root, packet=args.packet, revision_id=args.revision_id)
        identity = write_audit_dossier(args.output, artifact)
        errors = validate_audit_dossier(args.output, args.video_id, args.data_root, args.packet)
    else:
        if not args.video_id or args.data_root is None or args.packet is None:
            parser.error("audit bundle requires --video-id, --data-root, and --packet")
        artifact = build_audit_bundle(args.video_id, args.data_root, packet=args.packet, revision_id=args.revision_id)
        write_audit_bundle(args.output, artifact)
        identity = {"path": str(args.output), "semantic_sha256": artifact["semantic_sha256"]}
        errors = []
    print(json.dumps({"status": "ok" if not errors else "blocked", "output": str(args.output), **identity, "errors": errors}))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
