#!/usr/bin/env python
"""Persist the dedicated final audit result without exposing it in packets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from scripts.gold_extraction_common import GoldPauseError, now, record_operation_event, sha256_json, validate_external_audit_report, write_json


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
    parser.add_argument("--input", type=Path, help="Audit JSON. Omit to read JSON from stdin.")
    parser.add_argument("--check", action="store_true", help="Validate the audit envelope without writing episode artifacts.")
    args = parser.parse_args()
    try:
        payload: dict[str, Any] = json.loads(args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read())
        result = record_audit(args.video_id, args.data_root, payload, persist=not args.check)
    except (GoldPauseError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1
    print(json.dumps({"status": result["status"], "open_findings": result["open_findings"], "read_only": args.check}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
