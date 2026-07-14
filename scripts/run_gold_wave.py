#!/usr/bin/env python
"""Manifest-driven Fast Path planner for new, resumable and protected gold episodes."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.finalize_gold_episode import finalize_episode
from scripts.gold_extraction_common import ledger_errors, load_json, sha256_json, validate_document
from scripts.gold_wave_gate import evaluate_wave, write_wave_receipt
from scripts.reprocess_gold_episode import prepare_episode, raw_preflight, work_order_metrics


DEFAULT_ACTIVE_BUDGET = {
    "max_raw_segments": 2500,
    "max_chunks": 40,
    "max_episodes": 3,
}


def _gold_dir(data_root: Path, video_id: str) -> Path:
    return data_root / "processed" / video_id / "gold_extraction"


def episode_metrics(video_id: str, data_root: Path) -> dict[str, Any]:
    out = _gold_dir(data_root, video_id)
    if not out.exists():
        return {"video_id": video_id, "available": False}
    required = [out / "gold_extraction_status.json", out / "chunks" / "chunk_index.json", out / "signal_inventory.json", out / "calibration_tests.json"]
    if any(not path.exists() for path in required):
        return {"video_id": video_id, "available": False, "reason": "gold preparation artifacts missing"}
    status = load_json(required[0])
    chunks = load_json(required[1]).get("chunks", [])
    signals = load_json(required[2]).get("signals", [])
    calibrations = load_json(required[3]).get("tests", [])
    hydrated = []
    for item in chunks:
        chunk_path = Path(item["file"])
        hydrated.append(load_json(chunk_path))
    metrics = work_order_metrics(video_id, hydrated, signals, calibrations)
    actual_bytes = sum(path.stat().st_size for path in (out / "work_orders").glob("chunk_*_work_order.json"))
    return {
        "video_id": video_id, "available": True, "actual_work_order_bytes": actual_bytes,
        "lifecycle_status": status.get("status"), "audit_status": status.get("audit_status"),
        "open_audit_findings": status.get("open_audit_findings"), "chunk_count": len(status.get("chunks", [])),
        "candidate_count": status.get("candidate_count"),
        "completed_chunks": sum(1 for chunk in status.get("chunks", []) if chunk.get("status") == "completed"),
        "operation_metrics": _operation_metrics(out),
        "timing_measurement": "not_available_for_historical_artifacts",
        **metrics,
    }


def _operation_metrics(out: Path) -> dict[str, Any]:
    path = out / "fastpath_operation_receipt.json"
    if not path.exists():
        return {"status": "not_available"}
    events = load_json(path).get("events", [])
    return {"status": "measured", **{operation: sum(item.get("operation") == operation for item in events) for operation in ("review_batch", "patch", "build", "audit", "finalize", "episode_one_shot")}}


def detect_route(video_id: str, data_root: Path) -> dict[str, Any]:
    out = _gold_dir(data_root, video_id)
    status_path = out / "gold_extraction_status.json"
    if out.exists() and not status_path.exists():
        return {
            "video_id": video_id, "mode": "inconsistent_checkpoint", "protected": False,
            "next_gate": "blocked_inconsistent_checkpoint", "error": "gold_extraction exists without gold_extraction_status.json",
        }
    if not status_path.exists():
        preflight = raw_preflight(video_id, data_root)
        return {
            "video_id": video_id, "mode": "new_raw_episode", "protected": False,
            "preflight": preflight, "next_gate": "prepare" if preflight["status"] == "pass" else "blocked_raw_preflight",
        }
    status = load_json(status_path)
    if status.get("status") == "complete" and status.get("audit_status") == "passed":
        return {"video_id": video_id, "mode": "protected_complete_read_only", "protected": True, "next_gate": "none"}
    reviews_dir = out / "manual_reviews"
    stale: list[str] = []
    pending: list[str] = []
    inconsistent: list[str] = []
    for chunk in status.get("chunks", []):
        review_path = reviews_dir / f"chunk_{int(chunk['chunk_number']):03d}_review.json"
        if not review_path.exists():
            (inconsistent if chunk.get("status") == "completed" else pending).append(chunk["chunk_id"])
            continue
        review = load_json(review_path)
        if review.get("input_hash") != chunk.get("input_hash"):
            stale.append(chunk["chunk_id"])
            continue
        review_hash = sha256_json(review)
        if chunk.get("status") == "completed" and chunk.get("review_hash") and review_hash != chunk["review_hash"]:
            stale.append(chunk["chunk_id"])
    return {
        "video_id": video_id, "mode": "resumable_incomplete_gold", "protected": False,
        "pending_chunks": pending, "stale_chunks": stale, "inconsistent_chunks": inconsistent,
        "next_gate": "blocked_inconsistent_checkpoint" if inconsistent else "reopen_changed_chunks" if stale else "semantic_review" if pending else "autocheck_readiness",
    }


def _raw_segment_count(video_id: str, data_root: Path) -> int:
    path = data_root / "raw" / "youtube" / video_id / "transcript_original.json"
    if not path.exists():
        return 0
    payload = load_json(path)
    return len(payload.get("segments", payload if isinstance(payload, list) else []))


def _review_ranges(chunk_ids: list[str], size: int) -> list[list[str]]:
    return [chunk_ids[index:index + size] for index in range(0, len(chunk_ids), size)]


def _budget_from_manifest(manifest: dict[str, Any]) -> tuple[dict[str, int], int]:
    configured = manifest.get("active_budget", {})
    if not isinstance(configured, dict):
        raise ValueError("active_budget must be an object")
    budget = {key: int(configured.get(key, value)) for key, value in DEFAULT_ACTIVE_BUDGET.items()}
    if any(value < 1 for value in budget.values()):
        raise ValueError("active_budget values must be positive")
    range_size = int(manifest.get("review_range_size", 10))
    if not 8 <= range_size <= 12:
        raise ValueError("review_range_size must be between 8 and 12")
    return budget, range_size


def _active_load(routes: list[dict[str, Any]], data_root: Path) -> dict[str, int]:
    active = [
        route for route in routes
        if not route.get("protected")
        and (
            route.get("mode") == "new_raw_episode"
            or (route.get("mode") == "resumable_incomplete_gold" and bool(route.get("pending_chunks") or route.get("stale_chunks")))
        )
    ]
    raw_segments = 0
    chunks = 0
    for route in active:
        if route.get("mode") == "new_raw_episode":
            count = _raw_segment_count(route["video_id"], data_root)
            raw_segments += count
            chunks += max(1, (count + 55) // 56)
            continue
        out = _gold_dir(data_root, route["video_id"])
        index = {item["chunk_id"]: item for item in load_json(out / "chunks" / "chunk_index.json").get("chunks", [])}
        ids = list(dict.fromkeys(route.get("pending_chunks", []) + route.get("stale_chunks", [])))
        chunks += len(ids)
        for chunk_id in ids:
            raw_segments += int(index[chunk_id].get("segment_count", 0))
    return {"active_episodes": len(active), "active_raw_segments": raw_segments, "active_chunks": chunks}


def normal_validation(video_id: str, data_root: Path) -> dict[str, Any]:
    """Mirror the normal validator without invoking an external-audit gate."""
    out = _gold_dir(data_root, video_id)
    document = load_json(out / "insights_exhaustive.json")
    transcript = load_json(out / "transcript_clean.json")["segments"]
    chunks = load_json(out / "chunks" / "chunk_index.json")["chunks"]
    ledger = load_json(out / "high_signal_coverage_ledger.json")["entries"]
    errors = validate_document(document, transcript, chunks, require_external_audit=False)
    errors.extend(ledger_errors(ledger, {item["candidate_id"] for item in document["insights"]}, {item["segment_id"] for item in ledger}))
    return {"status": "pass" if not errors else "fail", "errors": sorted(set(errors))}


def _strict_autocheck_errors(report: dict[str, Any]) -> list[str]:
    return [f"autocheck hard blocker: {item['category']}" for item in report.get("hard_blockers", [])]


def execute_resumable(video_id: str, data_root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    """Finalize one semantically complete episode without treating audit warnings as blockers."""
    return finalize_episode(
        video_id,
        data_root,
        executor_thread_id=entry.get("executor_thread_id"),
        export_suffix=entry.get("export_suffix"),
        revision_id=str(entry.get("revision_id") or "initial-finalization"),
    )


def run_manifest(
    manifest: dict[str, Any], data_root: Path, execute: bool = False, *, wave_receipt: Path | None = None,
) -> dict[str, Any]:
    episodes = manifest.get("episodes")
    if not isinstance(episodes, list) or not episodes:
        raise ValueError("manifest needs a non-empty episodes list")
    budget, range_size = _budget_from_manifest(manifest)
    seen: set[str] = set()
    planned: list[tuple[dict[str, Any], dict[str, Any]]] = []
    results: list[dict[str, Any]] = []
    for entry in episodes:
        video_id = str(entry.get("video_id", ""))
        if not video_id or video_id in seen:
            results.append({"video_id": video_id, "status": "blocked", "error": "missing or duplicate video_id"})
            continue
        seen.add(video_id)
        if entry.get("mode", "auto") != "auto":
            results.append({"video_id": video_id, "status": "blocked", "error": "only mode=auto is supported"})
            continue
        route = detect_route(video_id, data_root)
        planned.append((entry, route))
    load = _active_load([route for _entry, route in planned], data_root)
    over_budget = (
        load["active_episodes"] > budget["max_episodes"]
        or load["active_raw_segments"] > budget["max_raw_segments"]
        or load["active_chunks"] > budget["max_chunks"]
    )
    for entry, route in planned:
        started = time.perf_counter()
        video_id = route["video_id"]
        route["metrics"] = episode_metrics(video_id, data_root)
        route["active_load"] = load
        route["active_budget"] = budget
        chunk_ids = list(dict.fromkeys(route.get("pending_chunks", []) + route.get("stale_chunks", [])))
        if route.get("mode") == "new_raw_episode":
            estimated = max(1, (_raw_segment_count(video_id, data_root) + 55) // 56)
            chunk_ids = [f"{video_id}-planned-chunk-{index:03d}" for index in range(1, estimated + 1)]
        route["review_plan"] = {"range_size": range_size, "ranges": _review_ranges(chunk_ids, range_size)}
        contributes = route.get("mode") == "new_raw_episode" or bool(chunk_ids)
        if over_budget and contributes:
            route["next_gate"] = "blocked_active_budget"
            route["budget_error"] = "active load exceeds configured budget before any write"
        elif execute and route["mode"] == "new_raw_episode" and route["preflight"]["status"] == "pass":
            route["preparation"] = prepare_episode(video_id, data_root)
            route["next_gate"] = "semantic_review"
        elif execute and route["mode"] == "protected_complete_read_only":
            route["execution"] = "skipped_protected"
        elif execute and route["mode"] == "resumable_incomplete_gold":
            if route["next_gate"] != "autocheck_readiness":
                route["execution"] = "awaiting_semantic_review"
            else:
                route["execution"] = execute_resumable(video_id, data_root, entry)
                if route["execution"]["status"] == "blocked":
                    route["next_gate"] = f"blocked_{route['execution']['stopped_at']}"
                else:
                    route["next_gate"] = "awaiting_external_audit"
        route["stage_elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
        route["status"] = "protected" if route["protected"] else "blocked" if route.get("next_gate", "").startswith("blocked_") else "ready"
        results.append(route)
    result = {
        "schema_version": "1.0.0", "mode": "auto", "execute": execute,
        "metrics": {**load, "review_range_size": range_size, "batches_planned": sum(len(item.get("review_plan", {}).get("ranges", [])) for item in results)},
        "episodes": results,
    }
    result["wave_gate"] = evaluate_wave(manifest, data_root, results)
    if wave_receipt is not None:
        if result["wave_gate"]["wave_status"] in {"ready_for_audit", "terminally_blocked"}:
            result["wave_receipt"] = str(wave_receipt)
            write_wave_receipt(wave_receipt, result["wave_gate"])
        else:
            result["receipt_refused"] = "wave gate is in_progress; no delivery receipt was created or overwritten"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--execute", action="store_true", help="Prepare new episodes and finalize semantically complete resumable revisions; never writes protected gold.")
    parser.add_argument("--wave-receipt", type=Path, help="Write a terminal consolidated receipt only when the wave is ready_for_audit or terminally_blocked.")
    args = parser.parse_args()
    try:
        result = run_manifest(load_json(args.manifest), args.data_root, args.execute, wave_receipt=args.wave_receipt)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    if args.wave_receipt and result["wave_gate"]["wave_status"] == "in_progress":
        return 2
    return 0 if not any(item["status"] == "blocked" for item in result["episodes"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
