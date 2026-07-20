#!/usr/bin/env python
"""Persist the dedicated final audit result without exposing it in packets."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from scripts.gold_extraction_common import GoldPauseError, now, record_operation_event, sha256_json, sha256_semantic_json, validate_external_audit_report, write_json
from scripts.gold_audit_lifecycle import materialize_audit_envelope


def record_audit(video_id: str, data_root: Path, payload: dict[str, Any], *, persist: bool = True) -> dict[str, Any]:
    if payload.get("episode_video_id") not in {None, video_id}:
        raise ValueError("episode_video_id mismatch")
    validation_errors = validate_external_audit_report(payload, payload.get("executor_thread_id"), require_executor_provenance=False)
    if validation_errors:
        raise ValueError("; ".join(validation_errors))
    findings = payload["findings"]
    open_findings = sum(item["status"] == "open" for item in findings)
    if payload["status"] == "passed" and open_findings:
        raise ValueError("passed external audit report has open findings")
    result = {
        "episode_video_id": video_id, "audit_route": payload["audit_route"],
        "reviewer": payload["reviewer"], "reviewer_thread_id": payload["reviewer_thread_id"],
        "reviewer_model": payload["reviewer_model"], "reasoning_effort": payload["reasoning_effort"],
        "reviewed_at": payload.get("reviewed_at") or now(),
        "status": payload["status"], "summary": payload["summary"],
        "findings": findings, "open_findings": open_findings,
    }
    out = data_root / "processed" / video_id / "gold_extraction"
    if persist:
        write_json(out / "editorial_audit_report.json", result)
        record_operation_event(out, "audit", sha256_json(payload), {"open_findings": open_findings})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--data-root", required=True, type=Path)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--input", type=Path, help="Audit JSON. Omit to read JSON from stdin.")
    source.add_argument("--input-base64", help="UTF-8 audit JSON encoded as base64 for direct WSL argv transport.")
    parser.add_argument("--check", action="store_true", help="Validate the audit envelope without writing episode artifacts.")
    parser.add_argument("--envelope-output", type=Path, help="Validate and atomically materialize the source envelope at this job-local path without writing episode artifacts.")
    parser.add_argument("--audit-request", type=Path, help="Sealed audit request receipt that the envelope must match.")
    args = parser.parse_args()
    if args.check and args.envelope_output is not None:
        parser.error("--check and --envelope-output are mutually exclusive")
    try:
        if args.input_base64:
            source_text = base64.b64decode(args.input_base64, validate=True).decode("utf-8")
        else:
            source_text = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
        payload: dict[str, Any] = json.loads(source_text)
        persist = not args.check and args.envelope_output is None
        result = record_audit(args.video_id, args.data_root, payload, persist=persist)
        envelope = None
        if args.envelope_output is not None:
            if args.audit_request is not None:
                envelope_document = materialize_audit_envelope(
                    args.envelope_output.parent,
                    args.video_id,
                    payload,
                    request_path=args.audit_request,
                )
                if args.envelope_output.name != "audit_envelope.json":
                    write_json(args.envelope_output, envelope_document)
            else:
                # Historical compatibility.  The canonical runtime always
                # supplies --audit-request and writes a bound envelope.
                write_json(args.envelope_output, payload)
                envelope_document = payload
            envelope = {
                "path": str(args.envelope_output),
                "bytes": args.envelope_output.stat().st_size,
                "physical_sha256": hashlib.sha256(args.envelope_output.read_bytes()).hexdigest(),
                "semantic_sha256": sha256_semantic_json(envelope_document),
                "request_semantic_sha256": envelope_document.get("request_semantic_sha256"),
            }
    except (GoldPauseError, KeyError, ValueError, UnicodeDecodeError, binascii.Error, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1
    print(json.dumps({
        "status": result["status"],
        "open_findings": result["open_findings"],
        "read_only": args.check,
        "episode_artifacts_written": persist,
        "envelope": envelope,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
