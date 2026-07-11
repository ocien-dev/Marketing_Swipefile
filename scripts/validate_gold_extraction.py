#!/usr/bin/env python
"""CLI validator for a gold extraction package and its source transcript."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.gold_extraction_common import external_audit_gate, ledger_errors, load_json, validate_document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--require-external-audit", action="store_true")
    args = parser.parse_args()
    out = args.data_root / "processed" / args.video_id / "gold_extraction"
    document = load_json(out / "insights_exhaustive.json")
    transcript = load_json(out / "transcript_clean.json")["segments"]
    chunks = load_json(out / "chunks" / "chunk_index.json")["chunks"]
    signals = load_json(out / "signal_inventory.json")["signals"]
    ledger = load_json(out / "high_signal_coverage_ledger.json")["entries"]
    errors = validate_document(document, transcript, chunks, args.require_external_audit)
    errors.extend(ledger_errors(ledger, {item["candidate_id"] for item in document["insights"]}, {item["segment_id"] for item in ledger}))
    if args.require_external_audit:
        gate = external_audit_gate(out, load_json(out / "gold_extraction_status.json").get("executor_thread_id"))
        if not gate["eligible_for_complete"]:
            errors.extend(gate["errors"] or ["external audit has not passed"])
    result = {"status": "pass" if not errors else "fail", "errors": sorted(set(errors))}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
