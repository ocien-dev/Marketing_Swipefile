#!/usr/bin/env python
"""Compile, validate, persist, and finalize one complete gold episode draft."""

from __future__ import annotations

import argparse
import copy
import json
import time
from pathlib import Path
from typing import Any

from scripts.finalize_gold_episode import finalize_episode
from scripts.gold_extraction_common import load_json, record_operation_event
from scripts.gold_review_autocheck import autocheck_state
from scripts.gold_review_compiler import compile_payload
from scripts.record_gold_manual_reviews import load_payload, record


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)


def _episode_state(video_id: str, data_root: Path) -> dict[str, Any]:
    out = data_root / "processed" / video_id / "gold_extraction"
    status = load_json(out / "gold_extraction_status.json")
    transcript = load_json(out / "transcript_clean.json")["segments"]
    chunks = load_json(out / "chunks" / "chunk_index.json")["chunks"]
    signals = load_json(out / "signal_inventory.json").get("signals", [])
    calibration = load_json(out / "calibration_tests.json")
    review_dir = out / "manual_reviews"
    reviews = {
        path.name: load_json(path)
        for path in sorted(review_dir.glob("chunk_*_review.json"))
    }
    return {
        "out": out,
        "status": status,
        "transcript": transcript,
        "chunks": chunks,
        "signals": signals,
        "calibration": calibration,
        "reviews": reviews,
    }


def inspect_episode_draft(video_id: str, data_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Return the complete pre-write inventory for an episode payload."""
    total_started = time.perf_counter()
    state = _episode_state(video_id, data_root)
    if state["status"].get("status") == "complete" and state["status"].get("audit_status") == "passed":
        return {
            "status": "protected",
            "mode": "check",
            "episode_video_id": video_id,
            "issues": [],
            "hard_blockers": [],
            "audit_warnings": [],
            "metrics": {"total_ms": _elapsed_ms(total_started)},
        }

    compile_started = time.perf_counter()
    compiled = compile_payload(
        video_id,
        payload,
        state["status"],
        state["transcript"],
        copy.deepcopy(state["reviews"]),
    )
    compile_ms = _elapsed_ms(compile_started)
    if compiled["issues"]:
        return {
            "status": "blocked",
            "mode": "check",
            "stopped_at": "compiler",
            "episode_video_id": video_id,
            "issues": compiled["issues"],
            "hard_blockers": [],
            "audit_warnings": [],
            "semantic_sha256": compiled["semantic_sha256"],
            "metrics": {
                "compile_ms": compile_ms,
                "autocheck_ms": 0.0,
                "total_ms": _elapsed_ms(total_started),
                "review_count": len(compiled["reviews"]),
                "candidate_count": compiled["candidate_count"],
            },
        }

    autocheck_started = time.perf_counter()
    report = autocheck_state(
        video_id,
        status=state["status"],
        transcript=state["transcript"],
        chunks=state["chunks"],
        signals=state["signals"],
        calibration=state["calibration"],
        reviews=compiled["composed_reviews"],
        stored_ledger=[],
        prefer_stored_ledger=False,
    )
    autocheck_ms = _elapsed_ms(autocheck_started)
    return {
        "status": "ready_to_apply" if not report["hard_blockers"] else "blocked",
        "mode": "check",
        "stopped_at": None if not report["hard_blockers"] else "autocheck",
        "episode_video_id": video_id,
        "issues": [],
        "hard_blockers": report["hard_blockers"],
        "audit_warnings": report.get("audit_warnings", []),
        "autocheck": report,
        "semantic_sha256": compiled["semantic_sha256"],
        "metrics": {
            "compile_ms": compile_ms,
            "autocheck_ms": autocheck_ms,
            "total_ms": _elapsed_ms(total_started),
            "review_count": len(compiled["reviews"]),
            "final_review_count": len(compiled["composed_reviews"]),
            "candidate_count": sum(
                len(review.get("candidates", []))
                for review in compiled["composed_reviews"].values()
            ),
        },
    }


def run_episode(
    video_id: str,
    data_root: Path,
    payload: dict[str, Any],
    *,
    apply: bool = False,
    revision_id: str = "initial-finalization",
    export_suffix: str | None = None,
    executor_thread_id: str | None = None,
) -> dict[str, Any]:
    """Run the fast lane; no episode write occurs before a clean preview."""
    total_started = time.perf_counter()
    preview = inspect_episode_draft(video_id, data_root, payload)
    if not apply or preview["status"] != "ready_to_apply":
        return preview

    persist_started = time.perf_counter()
    persisted = record(video_id, data_root, payload)
    persist_ms = _elapsed_ms(persist_started)

    finalize_started = time.perf_counter()
    finalized = finalize_episode(
        video_id,
        data_root,
        executor_thread_id=executor_thread_id,
        export_suffix=export_suffix,
        revision_id=revision_id,
    )
    finalize_ms = _elapsed_ms(finalize_started)
    metrics = {
        **preview["metrics"],
        "persist_ms": persist_ms,
        "finalize_ms": finalize_ms,
        "total_ms": _elapsed_ms(total_started),
        "review_write_operations": 0 if persisted.get("idempotent") else 1,
        "finalizer_calls": 1,
    }
    result = {
        "status": finalized.get("status"),
        "mode": "apply",
        "episode_video_id": video_id,
        "revision_id": revision_id,
        "semantic_sha256": preview["semantic_sha256"],
        "persist": persisted,
        "finalization": finalized,
        "hard_blockers": finalized.get("hard_blockers", []),
        "audit_warnings": finalized.get("audit_warnings", preview.get("audit_warnings", [])),
        "metrics": metrics,
    }
    if finalized.get("status") in {"ready", "protected"}:
        record_operation_event(
            _episode_state(video_id, data_root)["out"],
            "episode_one_shot",
            preview["semantic_sha256"],
            metrics,
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--input", required=True, help="Complete episode review payload JSON.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Compile and run the final autocheck without episode or export writes.")
    mode.add_argument("--apply", action="store_true", help="Persist once and invoke the finalizer once after a clean preview.")
    parser.add_argument("--revision-id", default="initial-finalization")
    parser.add_argument("--export-suffix")
    parser.add_argument("--executor-thread-id")
    args = parser.parse_args()
    result = run_episode(
        args.video_id,
        args.data_root,
        load_payload(args.input),
        apply=args.apply,
        revision_id=args.revision_id,
        export_suffix=args.export_suffix,
        executor_thread_id=args.executor_thread_id,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] in {"ready_to_apply", "ready", "protected"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
