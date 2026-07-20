#!/usr/bin/env python
"""Finish one gold episode after reviews and internal remediation are complete."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.build_gold_semantic_extraction import build_from_reviews, readiness_check
from scripts.export_gold_audit_packet import PACKET_OUTPUT_FILES, export_packet
from scripts.gold_extraction_common import json_hashes, ledger_errors, load_json, record_operation_event, sha256_json, sha256_semantic_json, validate_document, write_json
from scripts.gold_review_autocheck import (
    SEMANTIC_CLOSURE_CATEGORY,
    SEMANTIC_WORKBENCH_CATEGORY,
    autocheck,
    review_audit_warnings,
    source_complete_invariant_issues,
)
from scripts.gold_episode_priority import advance_queue_state


def _out(data_root: Path, video_id: str) -> Path:
    return data_root / "processed" / video_id / "gold_extraction"


def _normal_validation(out: Path) -> dict[str, Any]:
    document = load_json(out / "insights_exhaustive.json")
    transcript = load_json(out / "transcript_clean.json")["segments"]
    chunks = load_json(out / "chunks" / "chunk_index.json")["chunks"]
    ledger = load_json(out / "high_signal_coverage_ledger.json")["entries"]
    errors = validate_document(document, transcript, chunks, require_external_audit=False)
    errors.extend(ledger_errors(ledger, {item["candidate_id"] for item in document["insights"]}, {item["segment_id"] for item in ledger}))
    return {"status": "pass" if not errors else "fail", "errors": sorted(set(errors))}


def _receipt_path(out: Path) -> Path:
    return out / "gold_finalization_receipt.json"


def _advance_project_priority_queue(video_id: str) -> dict[str, Any]:
    queue_path = Path(__file__).resolve().parents[1] / "docs" / "coordination" / "gold-episode-priority-queue.json"
    if not queue_path.is_file():
        return {"status": "not_configured"}
    try:
        state = advance_queue_state(queue_path, video_id, "finalized_pending_audit")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return {"status": "unavailable", "error": str(error)}
    return {
        "status": "advanced",
        "state_path": str(queue_path.with_name(f"{queue_path.stem}-state.json")),
        "remaining_count": state.get("remaining_count"),
        "next_episode": state.get("next_episode"),
    }


def _calibration_source(payload: dict[str, Any]) -> dict[str, Any]:
    derived = {"semantic_candidate_ids", "semantic_coverage", "covered_count", "status", "duplicate_target_segments"}
    return {
        key: value for key, value in payload.items() if key not in derived
    } | {
        "tests": [{key: value for key, value in test.items() if key not in derived} for test in payload.get("tests", [])]
    }


def _finalization_inputs(
    out: Path,
    audit_warning_dispositions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    files = [
        out / "transcript_clean.json",
        out / "chunks" / "chunk_index.json",
        out / "signal_inventory.json",
        out / "protected_fingerprints.json",
        *sorted((out / "manual_reviews").glob("chunk_*_review.json")),
    ]
    records = [{"path": str(path.relative_to(out)), **json_hashes(path)} for path in files]
    calibration = _calibration_source(load_json(out / "calibration_tests.json"))
    calibration_hash = sha256_semantic_json(calibration)
    return {
        "semantic_sha256": sha256_semantic_json({
            "files": [{"path": item["path"], "semantic_sha256": item["semantic_sha256"]} for item in records],
            "calibration_source": calibration,
            "audit_warning_dispositions": audit_warning_dispositions or [],
        }),
        "files": records,
        "calibration_source_semantic_sha256": calibration_hash,
        "audit_warning_dispositions": audit_warning_dispositions or [],
    }


def _packet_snapshot(packet: Path) -> dict[str, Any] | None:
    if not packet.is_dir():
        return None
    files = [path for path in packet.iterdir() if path.is_file()]
    if {path.name for path in files} != PACKET_OUTPUT_FILES:
        return None
    records = [{"name": path.name, **json_hashes(path)} for path in sorted(files)]
    return {"names": [item["name"] for item in records], "files": records}


def _same_packet(receipt: dict[str, Any], packet: Path) -> bool:
    return receipt.get("packet_files") == _packet_snapshot(packet)


def _current_reviews_signature(out: Path) -> str:
    review_dir = out / "manual_reviews"
    reviews = [
        {"name": path.name, "review": load_json(path)}
        for path in sorted(review_dir.glob("chunk_*_review.json"))
    ]
    return sha256_semantic_json({"reviews": reviews})


def _preview_receipt_error(
    out: Path,
    path: Path | None,
    *,
    video_id: str,
    revision_id: str,
    export_suffix: str | None,
    required_preview_sha256: str | None,
) -> str | None:
    if path is None or not path.exists():
        return "fast finalization requires an existing clean preview receipt"
    receipt = load_json(path)
    core = {key: value for key, value in receipt.items() if key != "receipt_semantic_sha256"}
    if receipt.get("receipt_semantic_sha256") != sha256_semantic_json(core):
        return "preview receipt semantic hash is invalid"
    expected = {
        "kind": "gold_episode_clean_preview",
        "status": "ready_to_apply",
        "episode_video_id": video_id,
        "revision_id": revision_id,
        "export_suffix": export_suffix,
        "payload_semantic_sha256": required_preview_sha256,
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            return f"preview receipt {key} does not match finalization"
    if receipt.get("composed_reviews_semantic_sha256") != _current_reviews_signature(out):
        return "persisted reviews do not match the clean preview"
    batch_path = out / "manual_review_batch_receipts.json"
    if not batch_path.exists():
        return "manual review batch receipt is missing"
    batches = load_json(batch_path).get("batches", [])
    if not any(item.get("semantic_sha256") == required_preview_sha256 for item in batches):
        return "manual review batch receipt does not contain the previewed payload"
    return None


def finalize_episode(
    video_id: str,
    data_root: Path,
    *,
    executor_thread_id: str | None = None,
    export_suffix: str | None = None,
    revision_id: str = "initial-finalization",
    preview_receipt_path: Path | None = None,
    required_preview_sha256: str | None = None,
    audit_warning_dispositions: list[dict[str, Any]] | None = None,
    require_warning_dispositions: bool = False,
) -> dict[str, Any]:
    out = _out(data_root, video_id)
    status = load_json(out / "gold_extraction_status.json")
    if status.get("status") == "complete" and status.get("audit_status") == "passed":
        return {"status": "protected", "next_gate": "none", "revision_id": revision_id}
    if required_preview_sha256 is not None:
        preview_error = _preview_receipt_error(
            out,
            preview_receipt_path,
            video_id=video_id,
            revision_id=revision_id,
            export_suffix=export_suffix,
            required_preview_sha256=required_preview_sha256,
        )
        if preview_error:
            return {
                "status": "blocked",
                "stopped_at": "preview_receipt",
                "error": preview_error,
                "revision_id": revision_id,
            }
    receipt_path = _receipt_path(out)
    if receipt_path.exists():
        receipt = load_json(receipt_path)
        if receipt.get("revision_id") == revision_id and receipt.get("status") == "ready":
            packet = Path(receipt.get("packet", ""))
            inputs = _finalization_inputs(out, audit_warning_dispositions)
            if receipt.get("input_signature", {}).get("semantic_sha256") != inputs["semantic_sha256"]:
                return {
                    "status": "conflict", "stopped_at": "receipt",
                    "error": "same revision_id has different finalization inputs",
                    "revision_id": revision_id,
                }
            if _same_packet(receipt, packet):
                return {**receipt, "idempotent": True, "queue_state": _advance_project_priority_queue(video_id)}
            return {
                "status": "conflict", "stopped_at": "receipt",
                "error": "receipt packet files are missing, extra, corrupted, or changed",
                "revision_id": revision_id,
            }
    # A prior packet ledger is derived output, not authority for a changed
    # review set. Finalization always previews the ledger the builder will
    # derive from the current candidates and explicit review decisions.
    report = autocheck(video_id, data_root, prefer_persisted_ledger=False)
    reviewed_warnings, warning_inventory, warning_review_required = review_audit_warnings(
        report.get("audit_warnings", []),
        audit_warning_dispositions,
        required_categories={
            "claim_evidence_alignment", SEMANTIC_CLOSURE_CATEGORY, SEMANTIC_WORKBENCH_CATEGORY,
        } if require_warning_dispositions else set(),
    )
    report["audit_warnings"] = reviewed_warnings
    report["audit_warning_inventory"] = warning_inventory
    if warning_review_required:
        return {
            "status": "blocked",
            "stopped_at": "warning_review",
            "review_gate": warning_review_required,
            "audit_warnings": reviewed_warnings,
            "audit_warning_inventory": warning_inventory,
            "autocheck": report,
        }
    source_complete_issues = source_complete_invariant_issues(
        report,
        reviewed_warnings=reviewed_warnings,
        review_gate=warning_review_required,
    )
    if source_complete_issues:
        report["hard_blockers"] = [
            *report.get("hard_blockers", []),
            {
                "category": "source_complete_invariant",
                "kind": "hard_blocker",
                "items": source_complete_issues,
            },
        ]
    if report.get("hard_blockers"):
        return {
            "status": "blocked",
            "stopped_at": "autocheck",
            "hard_blockers": report["hard_blockers"],
            "audit_warnings": report.get("audit_warnings", []),
            "autocheck": report,
        }
    reviews_dir = out / "manual_reviews"
    readiness = readiness_check(video_id, data_root, reviews_dir)
    if readiness["errors"]:
        return {
            "status": "blocked",
            "stopped_at": "readiness",
            "errors": readiness["errors"],
            "audit_warnings": report.get("audit_warnings", []),
            "autocheck": report,
            "readiness": readiness,
        }
    build = build_from_reviews(
        video_id,
        data_root,
        reviews_dir,
        executor_thread_id=executor_thread_id,
        export_suffix=export_suffix,
        audit_warnings=report.get("audit_warnings", []),
        revision_id=revision_id,
        defer_packet=True,
        # A finalization build is a new semantic snapshot. Any audit already
        # present belongs to an earlier snapshot and cannot certify this one.
        force_pending_external=True,
    )
    if build["errors"]:
        return {
            "status": "blocked",
            "stopped_at": "build",
            "errors": build["errors"],
            "audit_warnings": report.get("audit_warnings", []),
            "autocheck": report,
            "readiness": readiness,
            "build": build,
        }
    record_operation_event(
        out,
        "build",
        sha256_json({"revision_id": revision_id, "candidates": build.get("candidates")}),
        {"revision_id": revision_id},
    )
    validation = _normal_validation(out)
    if validation["errors"]:
        return {
            "status": "blocked",
            "stopped_at": "validator",
            "errors": validation["errors"],
            "audit_warnings": report.get("audit_warnings", []),
            "autocheck": report,
            "readiness": readiness,
            "build": build,
            "validation": validation,
        }
    inputs = _finalization_inputs(out, audit_warning_dispositions)
    packet = export_packet(
        video_id,
        data_root,
        export_suffix or f"msf_r20_piloto_{video_id}",
        audit_warnings=report.get("audit_warnings", []),
        revision_id=revision_id,
    )["packet"]
    packet_files = _packet_snapshot(Path(packet))
    if packet_files is None:
        raise ValueError("exported packet does not contain exactly the required five files")
    queue_state = _advance_project_priority_queue(video_id)
    result = {
        "status": "ready",
        "next_gate": "awaiting_external_audit",
        "revision_id": revision_id,
        "packet": packet,
        "audit_warnings": report.get("audit_warnings", []),
        "audit_warning_inventory": warning_inventory,
        "autocheck": report,
        "readiness": readiness,
        "build": build,
        "validation": validation,
        "input_signature": inputs,
        "packet_files": packet_files,
        "queue_state": queue_state,
    }
    write_json(receipt_path, result)
    record_operation_event(out, "finalize", sha256_json({"revision_id": revision_id, "packet": packet}), {"warning_count": len(result["audit_warnings"])})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--executor-thread-id")
    parser.add_argument("--export-suffix")
    parser.add_argument("--revision-id", default="initial-finalization")
    args = parser.parse_args()
    result = finalize_episode(
        args.video_id,
        args.data_root,
        executor_thread_id=args.executor_thread_id,
        export_suffix=args.export_suffix,
        revision_id=args.revision_id,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] in {"ready", "protected"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
