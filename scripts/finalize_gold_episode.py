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
from scripts.gold_review_autocheck import autocheck


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


def _calibration_source(payload: dict[str, Any]) -> dict[str, Any]:
    derived = {"semantic_candidate_ids", "semantic_coverage", "covered_count", "status", "duplicate_target_segments"}
    return {
        key: value for key, value in payload.items() if key not in derived
    } | {
        "tests": [{key: value for key, value in test.items() if key not in derived} for test in payload.get("tests", [])]
    }


def _finalization_inputs(out: Path) -> dict[str, Any]:
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
        "semantic_sha256": sha256_semantic_json({"files": [{"path": item["path"], "semantic_sha256": item["semantic_sha256"]} for item in records], "calibration_source": calibration}),
        "files": records,
        "calibration_source_semantic_sha256": calibration_hash,
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


def finalize_episode(
    video_id: str,
    data_root: Path,
    *,
    executor_thread_id: str | None = None,
    export_suffix: str | None = None,
    revision_id: str = "initial-finalization",
) -> dict[str, Any]:
    out = _out(data_root, video_id)
    status = load_json(out / "gold_extraction_status.json")
    if status.get("status") == "complete" and status.get("audit_status") == "passed":
        return {"status": "protected", "next_gate": "none", "revision_id": revision_id}
    receipt_path = _receipt_path(out)
    if receipt_path.exists():
        receipt = load_json(receipt_path)
        if receipt.get("revision_id") == revision_id and receipt.get("status") == "ready":
            packet = Path(receipt.get("packet", ""))
            inputs = _finalization_inputs(out)
            if receipt.get("input_signature", {}).get("semantic_sha256") != inputs["semantic_sha256"]:
                return {
                    "status": "conflict", "stopped_at": "receipt",
                    "error": "same revision_id has different finalization inputs",
                    "revision_id": revision_id,
                }
            if _same_packet(receipt, packet):
                return {**receipt, "idempotent": True}
            return {
                "status": "conflict", "stopped_at": "receipt",
                "error": "receipt packet files are missing, extra, corrupted, or changed",
                "revision_id": revision_id,
            }
    report = autocheck(video_id, data_root)
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
    inputs = _finalization_inputs(out)
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
    result = {
        "status": "ready",
        "next_gate": "awaiting_external_audit",
        "revision_id": revision_id,
        "packet": packet,
        "audit_warnings": report.get("audit_warnings", []),
        "autocheck": report,
        "readiness": readiness,
        "build": build,
        "validation": validation,
        "input_signature": inputs,
        "packet_files": packet_files,
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
