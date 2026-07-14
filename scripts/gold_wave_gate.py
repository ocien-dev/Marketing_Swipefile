#!/usr/bin/env python
"""Consolidate per-episode finalization evidence into one wave audit gate."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.finalize_gold_episode import _packet_snapshot
from scripts.gold_extraction_common import load_json, resolve_data_path, sha256_semantic_json, validate_external_audit_report, write_json


def _gold_dir(data_root: Path, video_id: str) -> Path:
    return data_root / "processed" / video_id / "gold_extraction"


def _fingerprints_match(out: Path) -> bool:
    path = out / "protected_fingerprints.json"
    if not path.exists():
        return False
    fingerprints = load_json(path)
    return bool(fingerprints.get("before")) and fingerprints.get("before") == fingerprints.get("after")


def _packet_evidence(video_id: str, data_root: Path, entry: dict[str, Any], receipt: dict[str, Any] | None) -> dict[str, Any]:
    """Bind a receipt to the manifest destination and its exact blind packet."""
    export_suffix = entry.get("export_suffix")
    if not isinstance(export_suffix, str) or not export_suffix.strip():
        return {
            "packet": None, "packet_valid": False, "packet_identity": False,
            "packet_snapshot_valid": False, "reason": "manifest export_suffix is missing",
        }
    packet = data_root / "exports" / export_suffix.strip()
    packet_files = _packet_snapshot(packet)
    if packet_files is None:
        return {
            "packet": str(packet), "packet_valid": False, "packet_identity": False,
            "packet_snapshot_valid": False, "reason": "expected packet is absent or does not contain exactly five files",
        }
    receipt_packet_matches = False
    if isinstance(receipt, dict) and isinstance(receipt.get("packet"), str) and receipt["packet"].strip():
        try:
            receipt_packet_matches = resolve_data_path(receipt["packet"], data_root) == packet.resolve()
        except (OSError, ValueError):
            receipt_packet_matches = False
    if not receipt_packet_matches:
        return {
            "packet": str(packet), "packet_valid": True, "packet_identity": False,
            "packet_snapshot_valid": False, "reason": "finalization receipt packet does not match manifest export destination",
        }
    manifest_identity = False
    try:
        manifest_identity = load_json(packet / "packet_manifest.json").get("episode_video_id") == video_id
    except (OSError, ValueError):
        manifest_identity = False
    if not manifest_identity:
        return {
            "packet": str(packet), "packet_valid": True, "packet_identity": False,
            "packet_snapshot_valid": False, "reason": "packet_manifest episode_video_id does not match manifest episode",
        }
    snapshot_valid = isinstance(receipt, dict) and receipt.get("packet_files") == packet_files
    if not snapshot_valid:
        return {
            "packet": str(packet), "packet_valid": True, "packet_identity": True,
            "packet_snapshot_valid": False, "reason": "packet snapshot does not match finalization receipt",
        }
    return {
        "packet": str(packet), "packet_valid": True, "packet_identity": True,
        "packet_snapshot_valid": True, "reason": None,
    }


def _protected_packet_state(video_id: str, data_root: Path, entry: dict[str, Any], out: Path, status: dict[str, Any]) -> dict[str, Any]:
    """Validate all immutable evidence before a complete/passed episode is ready."""
    receipt_path = out / "gold_finalization_receipt.json"
    receipt: dict[str, Any] | None = None
    if receipt_path.exists():
        try:
            loaded = load_json(receipt_path)
            receipt = loaded if isinstance(loaded, dict) else None
        except (OSError, ValueError):
            receipt = None
    packet_state = _packet_evidence(video_id, data_root, entry, receipt)
    audit_path = out / "editorial_audit_report.json"
    audit_valid = False
    if audit_path.exists():
        try:
            audit = load_json(audit_path)
            executor = entry.get("executor_thread_id") or status.get("executor_thread_id")
            audit_valid = (
                audit.get("episode_video_id") == video_id
                and audit.get("status") == "passed"
                and audit.get("open_findings") == 0
                and not validate_external_audit_report(
                    audit,
                    str(executor) if executor else None,
                    require_executor_provenance=bool(executor),
                )
            )
        except (OSError, ValueError):
            audit_valid = False
    fingerprints_match = _fingerprints_match(out)
    ready = packet_state["packet_snapshot_valid"] and audit_valid and fingerprints_match
    return {
        "video_id": video_id,
        "state": "ready" if ready else "in_progress",
        "route": "protected_complete_read_only",
        **packet_state,
        "audit_valid": audit_valid,
        "fingerprints_match": fingerprints_match,
        "reason": None if ready else packet_state["reason"] or "protected audit or fingerprints are invalid",
    }


def _episode_state(video_id: str, data_root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    out = _gold_dir(data_root, video_id)
    status_path = out / "gold_extraction_status.json"
    if not status_path.exists():
        return {"video_id": video_id, "state": "in_progress", "reason": "gold status is absent"}
    status = load_json(status_path)
    if status.get("status") == "complete" and status.get("audit_status") == "passed":
        return _protected_packet_state(video_id, data_root, entry, out, status)
    receipt_path = out / "gold_finalization_receipt.json"
    if not receipt_path.exists():
        return {"video_id": video_id, "state": "in_progress", "reason": "finalization receipt is absent"}
    try:
        receipt = load_json(receipt_path)
    except (OSError, ValueError):
        return {"video_id": video_id, "state": "in_progress", "reason": "finalization receipt is unreadable"}
    if not isinstance(receipt, dict):
        return {"video_id": video_id, "state": "in_progress", "reason": "finalization receipt must be an object"}
    packet_state = _packet_evidence(video_id, data_root, entry, receipt)
    ready = (
        receipt.get("status") == "ready"
        and receipt.get("next_gate") == "awaiting_external_audit"
        and status.get("status") == "awaiting_external_audit"
        and status.get("audit_status") == "pending_external"
        and not receipt.get("autocheck", {}).get("hard_blockers")
        and packet_state["packet_snapshot_valid"]
        and _fingerprints_match(out)
    )
    return {
        "video_id": video_id,
        "state": "ready" if ready else "in_progress",
        "revision_id": receipt.get("revision_id"),
        **packet_state,
        "fingerprints_match": _fingerprints_match(out),
        "reason": None if ready else packet_state["reason"] or "finalization evidence is incomplete or invalid",
    }


def evaluate_wave(manifest: dict[str, Any], data_root: Path, routes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Classify a wave without writing; only explicit terminal routes block it."""
    entries = manifest.get("episodes")
    if not isinstance(entries, list) or not entries:
        raise ValueError("manifest needs a non-empty episodes list")
    expected = int(manifest.get("required_episode_count", manifest.get("expected_episode_count", len(entries))))
    route_by_id = {str(item.get("video_id")): item for item in (routes or [])}
    episodes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries:
        video_id = str(entry.get("video_id", ""))
        if not video_id or video_id in seen:
            episodes.append({"video_id": video_id, "state": "terminally_blocked", "reason": "missing or duplicate video_id"})
            continue
        seen.add(video_id)
        route = route_by_id.get(video_id, {})
        if route.get("status") == "blocked" and str(route.get("next_gate", "")).startswith("blocked_"):
            episodes.append({"video_id": video_id, "state": "terminally_blocked", "reason": route.get("budget_error") or route.get("error") or route["next_gate"]})
        else:
            episodes.append(_episode_state(video_id, data_root, entry))
    states = [item["state"] for item in episodes]
    if "terminally_blocked" in states:
        wave_status = "terminally_blocked"
    elif len(entries) != expected or len(episodes) != expected or any(state != "ready" for state in states):
        wave_status = "in_progress"
    else:
        wave_status = "ready_for_audit"
    signature_source = {
        "required_episode_count": expected,
        "episodes": [{key: value for key, value in item.items() if key != "reason"} for item in episodes],
    }
    return {
        "schema_version": "1.0.0",
        "wave_status": wave_status,
        "required_episode_count": expected,
        "episode_results": episodes,
        "semantic_sha256": sha256_semantic_json(signature_source),
    }


def write_wave_receipt(path: Path, result: dict[str, Any]) -> dict[str, Any]:
    """Persist a deterministic consolidation receipt after evaluation."""
    write_json(path, result)
    return result
