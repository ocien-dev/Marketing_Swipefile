#!/usr/bin/env python
"""Compile, validate, persist, and finalize one complete gold episode draft."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import platform
import re
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scripts.finalize_gold_episode import finalize_episode
from scripts.gold_extraction_common import calibration_coverage, json_hashes, ledger_for_signals, load_json, numeric_mentions, preferred_transcript_path, record_operation_event, sha256_json, sha256_semantic_json, transcript_source_paths, write_json
from scripts.gold_final_audit_bundle import (
    audit_impact_set,
    build_audit_bundle,
    build_audit_dossier,
    build_reaudit_delta,
    validate_reaudit_delta,
    validate_audit_dossier,
    write_audit_bundle,
    write_audit_dossier,
)
from scripts.gold_audit_lifecycle import (
    build_audit_request,
    materialize_audit_envelope,
    resume_audit_request,
    validate_audit_envelope,
    validate_audit_request,
    write_audit_request,
)
from scripts.gold_authoring_manifest import (
    adversarial_authoring_view,
    calibration_decision_issues,
    is_authoring_manifest,
    manifest_to_compact_payload,
    normalize_authoring_input,
    validate_authoring_manifest,
)
from scripts import gold_review_autocheck as review_autocheck
from scripts.gold_review_autocheck import (
    SEMANTIC_CLOSURE_CATEGORY,
    SEMANTIC_WORKBENCH_CATEGORY,
    autocheck_state,
    review_audit_warnings,
    source_complete_invariant_issues,
    sparse_recall_view,
)
from scripts.gold_review_compiler import (
    COMPACT_EPISODE_PAYLOAD_FORMAT,
    COMPACT_EPISODE_PAYLOAD_FORMATS,
    COMPACT_EPISODE_PAYLOAD_FORMAT_V3,
    compile_payload,
)
from scripts.gold_review_patch import apply_patch as apply_gold_patch, generate_audit_remediation_scaffold, prepare_patch
from scripts.gold_episode_priority import load_queue_state, queue_state_path
from scripts.gold_terminal_identity import resolve_terminal_identity
from scripts.record_gold_manual_reviews import load_payload, record
from scripts.reprocess_gold_episode import prepare_episode, raw_preflight
from scripts.sync_wsl_runtime import validate_runtime_parity_receipt
from scripts.transcript_semantic_index import semantic_navigation_summary
from scripts.verify_gold_runtime import default_temp_root, verify_environment


LEGACY_CONTEXT_KEYS = {
    "insights_v2", "insights_v2_json", "legacy_insights", "old_insights",
    "legacy_comparison", "legacy_index",
}
CANONICAL_EXTRACTION_ARCHITECTURE = "chronological_hybrid_v1"
PROCEDURAL_TYPES = {"framework", "playbook_step", "script"}
MATERIAL_NUMBER_RE = re.compile(r"(?:R\$\s*)?\d+(?:[.,]\d+)?(?:\s*%)?")
CLI_OUTPUT_MAX_BYTES = 8 * 1024
SESSION_IDLE_THRESHOLD_MS = 60_000.0
SEMANTIC_PHASES = {
    "semantic_reading_and_authoring", "prelint_repair", "final_sol_audit",
    "remediation_authoring", "final_sol_reaudit", "closeout",
}


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _wall_elapsed_ms(started_at: str, ended_at: str | None = None) -> float:
    try:
        started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        ended = datetime.fromisoformat((ended_at or _utc_now()).replace("Z", "+00:00"))
        return round(max(0.0, (ended - started).total_seconds() * 1000), 2)
    except (TypeError, ValueError):
        return 0.0


def _is_wsl() -> bool:
    release = platform.release().lower()
    return "microsoft" in release or "wsl" in release


def _validate_job_dir(job_dir: Path | None) -> None:
    if job_dir is None:
        return
    supplied = str(job_dir).replace("\\", "/")
    if _is_wsl() and supplied.startswith("/mnt/"):
        raise ValueError("fast episode job-dir must be Linux-native under WSL, not /mnt")


def _mirror_final_artifact(source: Path, mirror_job_dir: Path | None) -> dict[str, Any] | None:
    if mirror_job_dir is None:
        return None
    destination = mirror_job_dir / source.name
    if destination.resolve(strict=False) == source.resolve(strict=False):
        return {"path": str(destination), **_final_artifact_hashes(destination)}
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_bytes(source.read_bytes())
    temporary.replace(destination)
    return {"path": str(destination), **_final_artifact_hashes(destination)}


def _final_artifact_hashes(path: Path) -> dict[str, Any]:
    if path.suffix.lower() != ".jsonl":
        return json_hashes(path)
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    semantic_sha256 = (
        records[-1].get("content_semantic_sha256")
        if records and records[-1].get("record_type") == "footer"
        else sha256_semantic_json(records)
    )
    return {
        "bytes": path.stat().st_size,
        "physical_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "semantic_sha256": semantic_sha256,
    }


def _session_path(job_dir: Path) -> Path:
    return job_dir / "episode_fast_session.json"


def _runtime_snapshot_paths(job_dir: Path) -> tuple[Path, Path]:
    return job_dir / "runtime_snapshot_receipt.json", job_dir / "runtime_snapshot_binding.json"


def _validate_or_pin_runtime_snapshot(
    job_dir: Path | None,
    receipt_path: Path,
    manifest_path: Path,
    destination_root: Path,
) -> tuple[Path, list[str]]:
    """Bind one certified Linux runtime to the job until its terminal receipt."""
    if job_dir is None:
        return receipt_path, validate_runtime_parity_receipt(receipt_path, destination_root, manifest_path)
    job_dir.mkdir(parents=True, exist_ok=True)
    pinned_path, binding_path = _runtime_snapshot_paths(job_dir)
    if pinned_path.exists() or binding_path.exists():
        if not pinned_path.exists() or not binding_path.exists():
            return pinned_path, ["runtime snapshot receipt or binding is missing"]
        binding = load_json(binding_path)
        binding_core = {key: value for key, value in binding.items() if key != "semantic_sha256"}
        errors = []
        if binding.get("semantic_sha256") != sha256_semantic_json(binding_core):
            errors.append("runtime snapshot binding semantic hash is invalid")
        pinned = load_json(pinned_path)
        if binding.get("receipt_semantic_sha256") != pinned.get("receipt_semantic_sha256"):
            errors.append("runtime snapshot receipt differs from its run binding")
        errors.extend(validate_runtime_parity_receipt(
            pinned_path,
            destination_root,
            manifest_path,
            check_source=False,
            expected_execution_signature=binding.get("execution_signature"),
        ))
        return pinned_path, errors
    errors = validate_runtime_parity_receipt(receipt_path, destination_root, manifest_path)
    if errors:
        return receipt_path, errors
    pinned = load_json(receipt_path)
    write_json(pinned_path, pinned)
    binding_core = {
        "schema_version": "1.0.0",
        "kind": "gold_runtime_run_binding",
        "receipt_semantic_sha256": pinned.get("receipt_semantic_sha256"),
        "execution_signature": pinned.get("execution_signature"),
        "destination_root": str(destination_root.resolve()),
        "pinned_at": _utc_now(),
    }
    write_json(binding_path, {**binding_core, "semantic_sha256": sha256_semantic_json(binding_core)})
    return pinned_path, []


def _load_or_start_session(
    job_dir: Path | None,
    video_id: str,
    *,
    epic_started_at: str | None = None,
) -> dict[str, Any] | None:
    if job_dir is None:
        return None
    _validate_job_dir(job_dir)
    job_dir.mkdir(parents=True, exist_ok=True)
    path = _session_path(job_dir)
    if path.exists():
        session = load_json(path)
        if session.get("episode_video_id") != video_id:
            raise ValueError("job-dir already belongs to a different episode")
        session.setdefault("operation_counts", {})
        session.setdefault("semantic_spans", [])
        return session
    started_at = epic_started_at or _utc_now()
    session = {
        "schema_version": "1.4.0",
        "episode_video_id": video_id,
        "started_at": started_at,
        "epic_started_at": started_at,
        "events": [],
        "operation_counts": {},
        "semantic_spans": [],
    }
    write_json(path, session)
    return session


def mark_semantic_phase(job_dir: Path, video_id: str, phase: str, action: str) -> dict[str, Any]:
    """Persist an explicit model-work span without inferring hidden model time."""
    if phase not in SEMANTIC_PHASES:
        raise ValueError(f"unknown semantic phase: {phase}")
    if action not in {"start", "end", "interrupt"}:
        raise ValueError("semantic phase action must be start, end, or interrupt")
    session = _load_or_start_session(job_dir, video_id)
    assert session is not None
    spans = session.setdefault("semantic_spans", [])
    open_spans = [item for item in spans if item.get("phase") == phase and not item.get("ended_at")]
    if action == "start":
        if open_spans:
            raise ValueError(f"semantic phase is already open: {phase}")
        started_at = _utc_now()
        for item in spans:
            if item.get("phase") == phase or item.get("ended_at"):
                continue
            item["ended_at"] = started_at
            item["elapsed_ms"] = _wall_elapsed_ms(item["started_at"], started_at)
            item["state"] = "completed"
        span = {
            "phase": phase,
            "state": "running",
            "started_at": started_at,
            "ended_at": None,
            "elapsed_ms": None,
        }
        spans.append(span)
    else:
        if len(open_spans) != 1:
            raise ValueError(f"semantic phase does not have exactly one open span: {phase}")
        span = open_spans[0]
        span["ended_at"] = _utc_now()
        span["elapsed_ms"] = _wall_elapsed_ms(span["started_at"], span["ended_at"])
        span["state"] = "completed" if action == "end" else "interrupted"
    write_json(_session_path(job_dir), session)
    return copy.deepcopy(span)


def start_semantic_phase_if_absent(job_dir: Path | None, video_id: str, phase: str) -> dict[str, Any] | None:
    if job_dir is None:
        return None
    session = _load_or_start_session(job_dir, video_id)
    assert session is not None
    open_phase = [
        item for item in session.get("semantic_spans", [])
        if item.get("phase") == phase and not item.get("ended_at")
    ]
    if open_phase:
        if len(open_phase) != 1:
            raise ValueError(f"semantic phase has multiple open spans: {phase}")
        boundary = open_phase[0]["started_at"]
        changed = False
        for item in session.get("semantic_spans", []):
            if item is open_phase[0] or item.get("ended_at"):
                continue
            item["ended_at"] = boundary
            item["elapsed_ms"] = _wall_elapsed_ms(item["started_at"], boundary)
            item["state"] = "completed"
            changed = True
        if changed:
            write_json(_session_path(job_dir), session)
        return copy.deepcopy(open_phase[0])
    return mark_semantic_phase(job_dir, video_id, phase, "start")


def end_semantic_phase_if_open(job_dir: Path | None, video_id: str, phase: str) -> dict[str, Any] | None:
    if job_dir is None:
        return None
    session = _load_or_start_session(job_dir, video_id)
    assert session is not None
    if not any(item.get("phase") == phase and not item.get("ended_at") for item in session.get("semantic_spans", [])):
        return None
    return mark_semantic_phase(job_dir, video_id, phase, "end")


def interrupt_semantic_phase_if_open(job_dir: Path | None, video_id: str, phase: str) -> dict[str, Any] | None:
    if job_dir is None:
        return None
    session = _load_or_start_session(job_dir, video_id)
    assert session is not None
    if not any(item.get("phase") == phase and not item.get("ended_at") for item in session.get("semantic_spans", [])):
        return None
    return mark_semantic_phase(job_dir, video_id, phase, "interrupt")


def _runtime_command_ms(metrics: dict[str, Any]) -> float:
    for key in ("total_ms", "context_ms", "check_ms", "selection_ms"):
        if metrics.get(key) is not None:
            return round(max(0.0, float(metrics[key])), 2)
    return 0.0


def _started_before(completed_at: str, elapsed_ms: float) -> str:
    completed = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
    return (completed - timedelta(milliseconds=max(0.0, elapsed_ms))).isoformat()


def _record_session_event(
    job_dir: Path | None,
    video_id: str,
    phase: str,
    metrics: dict[str, Any],
    *,
    started_at: str | None = None,
    completed_at: str | None = None,
) -> None:
    if job_dir is None:
        return
    session = _load_or_start_session(job_dir, video_id)
    assert session is not None
    recorded_at = completed_at or _utc_now()
    runtime_command_ms = _runtime_command_ms(metrics)
    started_at = started_at or _started_before(recorded_at, runtime_command_ms)
    prior_event = session.get("events", [])[-1] if session.get("events") else None
    prior_recorded_at = (
        prior_event.get("completed_at") or prior_event.get("recorded_at")
        if prior_event
        else session["started_at"]
    )
    active_wall_ms = _wall_elapsed_ms(started_at, recorded_at)
    gap_ms = _wall_elapsed_ms(prior_recorded_at, started_at)
    unattributed_gap_ms = gap_ms if gap_ms >= SESSION_IDLE_THRESHOLD_MS else 0.0
    inter_turn_idle_ms = 0.0
    phase_transition_ms = gap_ms if gap_ms < SESSION_IDLE_THRESHOLD_MS else 0.0
    measured_model_ms = metrics.get("model_judgment_ms")
    model_judgment_ms = (
        max(0.0, float(measured_model_ms))
        if measured_model_ms is not None
        else max(0.0, active_wall_ms - runtime_command_ms)
    )
    elapsed_since_preflight_ms = max(
        _wall_elapsed_ms(session["started_at"], recorded_at),
        runtime_command_ms,
        float(prior_event.get("elapsed_since_preflight_ms", 0.0)) if prior_event else 0.0,
    )
    event = {
        "phase": phase,
        "recorded_at": recorded_at,
        "started_at": started_at,
        "completed_at": recorded_at,
        "active_wall_ms": round(active_wall_ms, 2),
        "runtime_command_ms": runtime_command_ms,
        "model_judgment_ms": round(model_judgment_ms, 2),
        "inter_turn_idle_ms": round(inter_turn_idle_ms, 2),
        "unattributed_gap_ms": round(unattributed_gap_ms, 2),
        "phase_transition_ms": round(phase_transition_ms, 2),
        "elapsed_since_preflight_ms": round(elapsed_since_preflight_ms, 2),
        "elapsed_since_epic_start_ms": round(elapsed_since_preflight_ms, 2),
        "elapsed_since_previous_event_ms": _wall_elapsed_ms(prior_recorded_at, recorded_at),
        "metrics": metrics,
    }
    session["events"] = [*session.get("events", []), event]
    session["schema_version"] = "1.4.0"
    increments = {
        "selection": {"selections": 1},
        "preflight_and_context": {"context_generations": 1},
        "prelint": {"prelints": 1},
        "preview": {"checks": 1},
        "final_audit": {"audits": int(metrics.get("audits", 1))},
        "apply_and_finalize": {
            "applies": 1,
            "review_write_operations": int(metrics.get("review_write_operations", 0)),
            "finalizers": int(metrics.get("finalizer_calls", 0)),
            "builds": int(metrics.get("builds", 0)),
            "audit_bundles": int(metrics.get("audit_bundles", 0)),
            "audit_requests": int(metrics.get("audit_requests", 0)),
        },
        "post_audit_completion": {
            "audits": int(metrics.get("audits", 0)),
            "audit_registrations": int(metrics.get("audit_registrations", 0)),
            "builds": int(metrics.get("builds", 0)),
            "required_audit_validations": int(metrics.get("required_audit_validations", 0)),
        },
        "post_audit_remediation": {
            "remediations": int(metrics.get("remediations", metrics.get("patches", 0))),
            "patches": int(metrics.get("patches", 0)),
            "finalizers": int(metrics.get("finalizer_calls", 0)),
            "builds": int(metrics.get("builds", 0)),
            "audit_bundles": int(metrics.get("audit_bundles", 0)),
            "audit_requests": int(metrics.get("audit_requests", 0)),
        },
    }.get(phase, {})
    counts = session.setdefault("operation_counts", {})
    for name, amount in increments.items():
        counts[name] = int(counts.get(name, 0)) + amount
    session["elapsed_ms"] = event["elapsed_since_preflight_ms"]
    session["last_recorded_at"] = recorded_at
    write_json(_session_path(job_dir), session)


def _safe_slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._-")


def _episode_source_candidate(video_id: str, data_root: Path) -> dict[str, Any] | None:
    processed = data_root / "processed" / video_id
    content_path = processed / "content_segments.json"
    metadata_path = data_root / "raw" / "youtube" / video_id / "metadata.json"
    transcript_path = preferred_transcript_path(data_root, video_id)
    if (processed / "gold_extraction").exists() or not all(path.exists() for path in (content_path, metadata_path, transcript_path)):
        return None
    try:
        content = load_json(content_path)
        metadata = load_json(metadata_path)
        transcript = load_json(transcript_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    clean_segments = content.get("segments", []) if isinstance(content, dict) else []
    raw_segments = transcript.get("segments", []) if isinstance(transcript, dict) else []
    transcript_status = metadata.get("transcript_status") or transcript.get("transcript_status")
    metadata_video_id = metadata.get("youtube_video_id") or metadata.get("video_id") or video_id
    transcript_video_id = transcript.get("youtube_video_id") or transcript.get("video_id") or video_id
    if metadata_video_id != video_id or transcript_video_id != video_id:
        return None
    if transcript_status not in {None, "available"} or not clean_segments or not raw_segments:
        return None
    return {
        "video_id": video_id,
        "title": metadata.get("title"),
        "duration_seconds": metadata.get("duration_seconds") or metadata.get("duration"),
        "clean_segments": len(clean_segments),
        "raw_segments": len(raw_segments),
        "source_files": [
            {"path": str(path), **json_hashes(path)}
            for path in (metadata_path, *transcript_source_paths(data_root, video_id), content_path)
        ],
    }


def _episode_source_readiness(video_id: str, data_root: Path) -> dict[str, Any]:
    """Explain the active-root prerequisite without treating the queue as proof."""
    processed = data_root / "processed" / video_id
    required = {
        "metadata": data_root / "raw" / "youtube" / video_id / "metadata.json",
        "transcript": preferred_transcript_path(data_root, video_id),
        "content_segments": processed / "content_segments.json",
    }
    missing = [name for name, path in required.items() if not path.is_file()]
    invalid: list[str] = []
    metadata: dict[str, Any] | None = None
    transcript: dict[str, Any] | None = None
    if "metadata" not in missing:
        try:
            loaded = load_json(required["metadata"])
            metadata = loaded if isinstance(loaded, dict) else None
        except (OSError, ValueError, json.JSONDecodeError):
            invalid.append("metadata_invalid")
    if "transcript" not in missing:
        try:
            loaded = load_json(required["transcript"])
            transcript = loaded if isinstance(loaded, dict) else None
        except (OSError, ValueError, json.JSONDecodeError):
            invalid.append("transcript_invalid")
    if metadata is not None:
        metadata_video_id = metadata.get("youtube_video_id") or metadata.get("video_id") or video_id
        if metadata_video_id != video_id:
            invalid.append("metadata_video_id_mismatch")
    if transcript is not None:
        transcript_video_id = transcript.get("youtube_video_id") or transcript.get("video_id") or video_id
        transcript_status = (metadata or {}).get("transcript_status") or transcript.get("transcript_status")
        if transcript_video_id != video_id:
            invalid.append("transcript_video_id_mismatch")
        if transcript_status not in {None, "available"}:
            invalid.append(f"transcript_status_{transcript_status}")
        if not transcript.get("segments"):
            invalid.append("transcript_segments_empty")
    if "content_segments" not in missing:
        try:
            content = load_json(required["content_segments"])
            if not isinstance(content, dict) or not content.get("segments"):
                invalid.append("content_segments_empty")
        except (OSError, ValueError, json.JSONDecodeError):
            invalid.append("content_segments_invalid")
    if missing or invalid:
        return {
            "status": "not_ready_in_active_data_root",
            "missing_artifacts": missing,
            "invalid_artifacts": invalid,
            "paths": {name: str(path) for name, path in required.items()},
        }
    if (processed / "gold_extraction").exists():
        return {"status": "already_gold", "missing_artifacts": [], "invalid_artifacts": [], "paths": {name: str(path) for name, path in required.items()}}
    return {"status": "ready", "missing_artifacts": [], "invalid_artifacts": [], "paths": {name: str(path) for name, path in required.items()}}


def _source_required_item(item: dict[str, Any], data_root: Path) -> dict[str, Any] | None:
    """Return the runtime acquisition requirement for one queued item."""
    video_id = str(item["video_id"])
    readiness = _episode_source_readiness(video_id, data_root)
    if readiness["status"] == "already_gold":
        return None
    return {
        "video_id": video_id,
        "youtube_url": item.get("youtube_url"),
        "title": item.get("title"),
        "queue_rank": item.get("rank"),
        "category": item.get("category"),
        "category_label": item.get("category_label"),
        "source_status": "not_ready_in_active_data_root",
        "runtime_readiness": readiness,
    }


def _select_runtime_ready_queue_item(
    items: list[dict[str, Any]],
    data_root: Path,
    *,
    minimum_segments: int,
    maximum_segments: int,
    explicit_reprocess: bool = False,
) -> tuple[
    dict[str, Any] | None,
    dict[str, Any] | None,
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Pick from the queue after reconciling active source and terminal identity."""
    skipped: list[dict[str, Any]] = []
    terminal_skips: list[dict[str, Any]] = []
    reprocess_conflicts: list[dict[str, Any]] = []
    for item in items:
        video_id = str(item["video_id"])
        terminal = resolve_terminal_identity(data_root, video_id)
        if terminal.get("terminal"):
            terminal_skips.append({
                "video_id": video_id,
                "status": terminal.get("status"),
                "authority": terminal.get("authority"),
                "terminal_identity_semantic_sha256": (terminal.get("identity") or {}).get("semantic_sha256"),
            })
            continue
        if terminal.get("explicit_reprocess_required") and not explicit_reprocess:
            reprocess_conflicts.append({
                "video_id": video_id,
                "status": terminal.get("status"),
                "prior_source_semantic_sha256": (terminal.get("identity") or {}).get("source_semantic_sha256"),
                "active_source_semantic_sha256": terminal.get("source", {}).get("source_semantic_sha256"),
            })
            continue
        candidate = _episode_source_candidate(video_id, data_root)
        if candidate is not None:
            segment_count = int(candidate["clean_segments"])
            if minimum_segments <= segment_count <= maximum_segments:
                return item, candidate, skipped, terminal_skips, reprocess_conflicts
            continue
        required = _source_required_item(item, data_root)
        if required is not None:
            skipped.append(required)
    return None, None, skipped, terminal_skips, reprocess_conflicts


def select_next_episode(
    data_root: Path,
    *,
    minimum_segments: int = 600,
    maximum_segments: int = 1200,
    target_segments: int = 950,
    excluded_video_ids: set[str] | None = None,
    priority_queue: Path | None = None,
    explicit_reprocess: bool = False,
    explicit_reprocess_reason: str | None = None,
) -> dict[str, Any]:
    """Select one unprepared source-complete episode without writing gold data."""
    started = time.perf_counter()
    processed_root = data_root / "processed"
    if not processed_root.is_dir():
        return {"status": "blocked", "errors": ["processed data root does not exist"], "candidates": []}
    excluded = excluded_video_ids or set()
    if explicit_reprocess and not str(explicit_reprocess_reason or "").strip():
        return {
            "status": "blocked",
            "errors": ["explicit reprocess requires a non-empty reason"],
            "candidates": [],
        }
    if priority_queue is not None:
        if not priority_queue.is_file():
            return {"status": "blocked", "errors": [f"priority queue does not exist: {priority_queue}"], "candidates": []}
        try:
            queue = load_json(priority_queue)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            return {"status": "blocked", "errors": [f"priority queue is invalid: {error}"], "candidates": []}
        entries = queue.get("entries", []) if isinstance(queue, dict) else []
        if not isinstance(entries, list):
            return {"status": "blocked", "errors": ["priority queue entries must be a list"], "candidates": []}
        state_path = queue_state_path(priority_queue)
        state, state_errors = load_queue_state(priority_queue, state_path)
        if state_errors:
            return {
                "status": "blocked",
                "errors": state_errors,
                "candidates": [],
                "selection_policy": {"mode": "priority_queue_state", "priority_queue": str(priority_queue), "state_path": str(state_path)},
            }
        if state is not None:
            queue_next = state.get("next_episode")
            if not isinstance(queue_next, dict) or not isinstance(queue_next.get("video_id"), str):
                queue_next = None
            # Cursor history is not terminal authority.  Reconcile every queue
            # entry against the active source and terminal receipt registry.
            pending = [
                item for item in entries
                if isinstance(item, dict)
                and isinstance(item.get("video_id"), str)
                and item["video_id"] not in excluded
            ]
            item, candidate, skipped, terminal_skips, reprocess_conflicts = _select_runtime_ready_queue_item(
                pending,
                data_root,
                minimum_segments=minimum_segments,
                maximum_segments=maximum_segments,
                explicit_reprocess=explicit_reprocess,
            )
            selected = ({
                **candidate,
                "queue_rank": item.get("rank"),
                "category": item.get("category"),
                "category_label": item.get("category_label"),
            } if item is not None and candidate is not None else None)
            source_required = skipped[0] if selected is None and skipped else None
            selection_status = (
                "selected" if selected
                else "blocked" if reprocess_conflicts
                else "source_required" if source_required
                else "blocked"
            )
            return {
                "status": selection_status,
                "next_episode": item or queue_next,
                "queue_next_episode": queue_next,
                "selected": selected,
                "source_required": source_required,
                "skipped_source_required_count": len(skipped),
                "skipped_source_required": skipped[:10],
                "terminal_reconciled_count": len(terminal_skips),
                "terminal_reconciled": terminal_skips[:10],
                "explicit_reprocess_conflicts": reprocess_conflicts[:10],
                "eligible_count": len(pending),
                "remaining_count": max(0, len(pending) - len(terminal_skips)),
                "selection_policy": {
                    "mode": "priority_queue_state",
                    "priority_queue": str(priority_queue),
                    "state_path": str(state_path),
                    "priority_queue_semantic_sha256": queue.get("semantic_sha256"),
                    "state_semantic_sha256": state.get("semantic_sha256"),
                    "excluded_video_ids": sorted(excluded),
                    "minimum_segments": minimum_segments,
                    "maximum_segments": maximum_segments,
                    "target_segments": target_segments,
                    "explicit_reprocess": explicit_reprocess,
                    "explicit_reprocess_reason": explicit_reprocess_reason,
                },
                "elapsed_ms": _elapsed_ms(started),
                "errors": [] if selected else [
                    "source identity changed after a terminal receipt; rerun with explicit reprocess and a reason"
                    if reprocess_conflicts
                    else "no pending priority episode has a source ready in the active data root"
                ],
            }
        remaining = [
            item for item in entries
            if isinstance(item, dict)
            and isinstance(item.get("video_id"), str)
            and item["video_id"] not in excluded
            and not (processed_root / item["video_id"] / "gold_extraction").exists()
        ]
        item, candidate, skipped, terminal_skips, reprocess_conflicts = _select_runtime_ready_queue_item(
            remaining,
            data_root,
            minimum_segments=minimum_segments,
            maximum_segments=maximum_segments,
            explicit_reprocess=explicit_reprocess,
        )
        selected = ({
            **candidate,
            "queue_rank": item.get("rank"),
            "category": item.get("category"),
            "category_label": item.get("category_label"),
        } if item is not None and candidate is not None else None)
        source_required = skipped[0] if selected is None and skipped else None
        status = "selected" if selected else "source_required" if source_required else "blocked"
        return {
            "status": status,
            "selected": selected,
            "source_required": source_required,
            "skipped_source_required_count": len(skipped),
            "skipped_source_required": skipped[:10],
            "terminal_reconciled_count": len(terminal_skips),
            "terminal_reconciled": terminal_skips[:10],
            "explicit_reprocess_conflicts": reprocess_conflicts[:10],
            "eligible_count": len(remaining),
            "selection_policy": {
                "mode": "priority_queue",
                "priority_queue": str(priority_queue),
                "priority_queue_semantic_sha256": queue.get("semantic_sha256"),
                "excluded_video_ids": sorted(excluded),
                "minimum_segments": minimum_segments,
                "maximum_segments": maximum_segments,
                "target_segments": target_segments,
                "explicit_reprocess": explicit_reprocess,
                "explicit_reprocess_reason": explicit_reprocess_reason,
            },
            "elapsed_ms": _elapsed_ms(started),
            "errors": [] if selected else [
                "source identity changed after a terminal receipt; rerun with explicit reprocess and a reason"
                if reprocess_conflicts
                else "no unprepared priority episode has a source ready in the active data root"
                if source_required
                else "priority queue has no unprepared episode"
            ],
        }
    candidates: list[dict[str, Any]] = []
    for episode_dir in sorted(processed_root.iterdir()):
        if not episode_dir.is_dir() or episode_dir.name in excluded:
            continue
        terminal = resolve_terminal_identity(data_root, episode_dir.name)
        if terminal.get("terminal"):
            continue
        if terminal.get("explicit_reprocess_required") and not explicit_reprocess:
            continue
        candidate = _episode_source_candidate(episode_dir.name, data_root)
        if candidate is None:
            continue
        count = int(candidate["clean_segments"])
        if minimum_segments <= count <= maximum_segments:
            candidate["distance_from_target"] = abs(count - target_segments)
            candidates.append(candidate)
    candidates.sort(key=lambda item: (item["distance_from_target"], item["video_id"]))
    selected = copy.deepcopy(candidates[0]) if candidates else None
    return {
        "status": "selected" if selected else "blocked",
        "selected": selected,
        "eligible_count": len(candidates),
        "selection_policy": {
            "minimum_segments": minimum_segments,
            "maximum_segments": maximum_segments,
            "target_segments": target_segments,
            "excluded_video_ids": sorted(excluded),
            "explicit_reprocess": explicit_reprocess,
            "explicit_reprocess_reason": explicit_reprocess_reason,
        },
        "elapsed_ms": _elapsed_ms(started),
        "errors": [] if selected else ["no source-complete unprepared episode matches the selection policy"],
    }


def select_and_bootstrap_episode(
    data_root: Path,
    job_dir: Path,
    *,
    selection_id: str = "gold-runtime",
    export_prefix: str = "msf_r20_gold_runtime",
    minimum_segments: int = 600,
    maximum_segments: int = 1200,
    target_segments: int = 950,
    excluded_video_ids: set[str] | None = None,
    epic_started_at: str | None = None,
    priority_queue: Path | None = None,
    explicit_reprocess: bool = False,
    explicit_reprocess_reason: str | None = None,
) -> dict[str, Any]:
    """Select, identify, and bootstrap the next episode in one certified call."""
    epic_started_at = epic_started_at or _utc_now()
    selection_started_at = _utc_now()
    selection = select_next_episode(
        data_root,
        minimum_segments=minimum_segments,
        maximum_segments=maximum_segments,
        target_segments=target_segments,
        excluded_video_ids=excluded_video_ids,
        priority_queue=priority_queue,
        explicit_reprocess=explicit_reprocess,
        explicit_reprocess_reason=explicit_reprocess_reason,
    )
    if selection["status"] != "selected":
        return selection
    selected = selection["selected"]
    video_id = str(selected["video_id"])
    safe_selection = _safe_slug(selection_id) or "gold-runtime"
    safe_video = _safe_slug(video_id)
    revision_id = f"{safe_selection}-{safe_video}-final-001"
    export_suffix = f"{_safe_slug(export_prefix) or 'msf_r20_gold_runtime'}_{safe_video}"
    _validate_job_dir(job_dir)
    job_dir.mkdir(parents=True, exist_ok=True)
    session = _load_or_start_session(job_dir, video_id, epic_started_at=epic_started_at)
    assert session is not None
    run_id = f"{safe_selection}-{safe_video}-{sha256_semantic_json({'started_at': epic_started_at})[:10]}"
    session["run_id"] = run_id
    write_json(_session_path(job_dir), session)
    selection_core = {
        "schema_version": "1.0.0",
        "kind": "gold_episode_selection",
        "status": "selected",
        "epic_started_at": epic_started_at,
        "episode_video_id": video_id,
        "selected": selected,
        "eligible_count": selection["eligible_count"],
        "selection_policy": selection["selection_policy"],
        "revision_id": revision_id,
        "export_suffix": export_suffix,
        "run_id": run_id,
    }
    selection_receipt = {**selection_core, "semantic_sha256": sha256_semantic_json(selection_core)}
    selection_path = job_dir / "selection_receipt.json"
    write_json(selection_path, selection_receipt)
    _record_session_event(job_dir, video_id, "selection", {
        "selection_ms": selection["elapsed_ms"],
        "eligible_count": selection["eligible_count"],
        "selected_clean_segments": selected["clean_segments"],
    }, started_at=selection_started_at)
    bootstrap_request = {
        "video_id": video_id,
        "data_root": str(data_root),
        "job_dir": str(job_dir),
        "context_path": str(job_dir / "episode_context.jsonl"),
        "prepare_if_missing": True,
        "epic_started_at": epic_started_at,
        "selection_receipt": str(selection_path),
        "revision_id": revision_id,
        "export_suffix": export_suffix,
    }
    request_path = job_dir / "bootstrap_request.json"
    write_json(request_path, bootstrap_request)
    bootstrap = bootstrap_episode(bootstrap_request)
    return {
        "status": bootstrap.get("status"),
        "episode_video_id": video_id,
        "revision_id": revision_id,
        "export_suffix": export_suffix,
        "selection_receipt": str(selection_path),
        "bootstrap_request": str(request_path),
        "selection": selection_receipt,
        "bootstrap": bootstrap,
        "run_id": run_id,
    }


def start_episode(
    data_root: Path,
    job_dir: Path,
    **selection_options: Any,
) -> dict[str, Any]:
    """Certify the configured native runtime and bootstrap the next episode."""
    started = time.perf_counter()
    certification_started = time.perf_counter()
    verification = verify_environment(
        repo_root=Path(__file__).resolve().parents[1],
        data_root=data_root,
        temp_root=default_temp_root(data_root),
    )
    certification_ms = _elapsed_ms(certification_started)
    if verification.get("status") != "pass":
        return {
            "status": "blocked",
            "stopped_at": "runtime_certification",
            "runtime_verification": verification,
            "startup_metrics": {
                "certification_ms": certification_ms,
                "total_ms": _elapsed_ms(started),
            },
        }
    bootstrap_started = time.perf_counter()
    result = select_and_bootstrap_episode(data_root, job_dir, **selection_options)
    if result.get("status") not in {"blocked", "error"} and result.get("episode_video_id"):
        start_semantic_phase_if_absent(
            job_dir, str(result["episode_video_id"]), "semantic_reading_and_authoring"
        )
    return {
        **result,
        "runtime_verification": verification,
        "startup_metrics": {
            "certification_ms": certification_ms,
            "selection_bootstrap_ms": _elapsed_ms(bootstrap_started),
            "total_ms": _elapsed_ms(started),
        },
    }


def _legacy_context_issues(payload: Any, path: str = "payload") -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            normalized = str(key).lower().replace("-", "_").removesuffix(".json")
            if normalized in LEGACY_CONTEXT_KEYS:
                issues.append({
                    "candidate_id": None,
                    "field": f"{path}.{key}",
                    "category": "legacy_context_forbidden",
                    "evidence": {"key": key},
                    "expected": "raw transcript, prepared work orders, and current gold state only",
                })
            issues.extend(_legacy_context_issues(value, f"{path}.{key}"))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            issues.extend(_legacy_context_issues(value, f"{path}[{index}]"))
    return issues


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
    result = {
        "out": out,
        "status": status,
        "transcript": transcript,
        "chunks": chunks,
        "signals": signals,
        "calibration": calibration,
        "reviews": reviews,
    }
    return result


def _prepared_input_signature(state: dict[str, Any]) -> str:
    derived_calibration_fields = {
        "semantic_candidate_ids", "semantic_coverage", "covered_count",
        "status", "duplicate_target_segments",
    }
    calibration = {
        key: value for key, value in state["calibration"].items()
        if key not in derived_calibration_fields
    }
    calibration["tests"] = [
        {
            key: value for key, value in item.items()
            if key not in derived_calibration_fields
        }
        for item in state["calibration"].get("tests", [])
    ]
    status_source = {
        "episode_video_id": state["status"].get("episode_video_id"),
        "input_transcript_hash": state["status"].get("input_transcript_hash"),
        "protected_fingerprints": state["status"].get("protected_fingerprints"),
        "chunks": [
            {
                "chunk_id": item.get("chunk_id"),
                "chunk_number": item.get("chunk_number"),
                "input_hash": item.get("input_hash"),
            }
            for item in state["status"].get("chunks", [])
        ],
    }
    return sha256_semantic_json({
        "status": status_source,
        "transcript": state["transcript"],
        "chunks": state["chunks"],
        "signals": state["signals"],
        "calibration": calibration,
    })


def _composed_reviews_signature(reviews: dict[str, dict[str, Any]]) -> str:
    return sha256_semantic_json({"reviews": [{"name": name, "review": reviews[name]} for name in sorted(reviews)]})


def _preview_receipt_core(
    preview: dict[str, Any],
    *,
    revision_id: str,
    export_suffix: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "kind": "gold_episode_clean_preview",
        "status": "ready_to_apply",
        "episode_video_id": preview["episode_video_id"],
        "revision_id": revision_id,
        "export_suffix": export_suffix,
        "payload_semantic_sha256": preview["semantic_sha256"],
        "authoring_manifest_semantic_sha256": preview.get("authoring_manifest_semantic_sha256"),
        "prepared_input_semantic_sha256": preview["prepared_input_semantic_sha256"],
        "composed_reviews_semantic_sha256": preview["composed_reviews_semantic_sha256"],
        "autocheck_semantic_sha256": preview["autocheck_semantic_sha256"],
    }


def make_preview_receipt(
    preview: dict[str, Any],
    *,
    revision_id: str,
    export_suffix: str | None,
) -> dict[str, Any]:
    if preview.get("status") != "ready_to_apply":
        raise ValueError("only a clean ready_to_apply preview can produce a receipt")
    core = _preview_receipt_core(preview, revision_id=revision_id, export_suffix=export_suffix)
    return {**core, "receipt_semantic_sha256": sha256_semantic_json(core)}


def _preview_receipt_matches(
    preview: dict[str, Any],
    receipt: dict[str, Any],
    *,
    revision_id: str,
    export_suffix: str | None,
) -> bool:
    expected = make_preview_receipt(preview, revision_id=revision_id, export_suffix=export_suffix)
    core = {key: value for key, value in receipt.items() if key != "receipt_semantic_sha256"}
    if receipt.get("receipt_semantic_sha256") != sha256_semantic_json(core):
        return False
    stable_fields = {
        "schema_version", "kind", "status", "episode_video_id", "revision_id",
        "export_suffix", "payload_semantic_sha256",
        "authoring_manifest_semantic_sha256",
        "prepared_input_semantic_sha256", "composed_reviews_semantic_sha256",
    }
    return all(receipt.get(key) == expected.get(key) for key in stable_fields)


def build_reading_context(video_id: str, data_root: Path, *, slab_count: int = 3) -> dict[str, Any]:
    """Return all transcript text once, grouped into two or three large slabs."""
    state = _episode_state(video_id, data_root)
    chunks = state["chunks"]
    if not chunks:
        return {"episode_video_id": video_id, "slabs": [], "chunk_count": 0, "segment_count": 0}
    slab_count = max(1, min(3, slab_count, len(chunks)))
    width = math.ceil(len(chunks) / slab_count)
    transcript_by_id = {item["segment_id"]: item for item in state["transcript"]}
    index_by_id = {item["segment_id"]: index for index, item in enumerate(state["transcript"])}
    signals_by_id = {item["segment_id"]: item.get("signal_types", []) for item in state["signals"]}
    slabs = []
    for slab_index, offset in enumerate(range(0, len(chunks), width), 1):
        slab_chunks = chunks[offset:offset + width]
        start = index_by_id[slab_chunks[0]["first_segment_id"]]
        end = index_by_id[slab_chunks[-1]["last_segment_id"]]
        segments = []
        for segment in state["transcript"][start:end + 1]:
            segments.append({
                "segment_id": segment["segment_id"],
                "clean_index": segment["clean_index"],
                "start_seconds": segment["start_seconds"],
                "text": segment["text"],
                "signal_types": signals_by_id.get(segment["segment_id"], []),
            })
        boundary = None
        if offset > 0:
            prior = chunks[offset - 1]
            boundary = {
                "previous_chunk": prior["chunk_id"],
                "previous_last_segment": transcript_by_id[prior["last_segment_id"]],
                "current_chunk": slab_chunks[0]["chunk_id"],
                "current_first_segment": transcript_by_id[slab_chunks[0]["first_segment_id"]],
            }
        slabs.append({
            "slab_number": slab_index,
            "chunk_numbers": [item["chunk_number"] for item in slab_chunks],
            "boundary_from_previous_slab": boundary,
            "segments": segments,
        })
    result = {
        "episode_video_id": video_id,
        "mode": "read_only_semantic_context",
        "chunk_count": len(chunks),
        "segment_count": len(state["transcript"]),
        "transcript_semantic_index": semantic_navigation_summary(
            video_id, data_root, state["transcript"]
        ),
        "slabs": slabs,
    }
    result["model_context_bytes"] = len(json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    result["legacy_content_reads"] = 0
    return result


def build_compact_reading_context(video_id: str, data_root: Path) -> dict[str, Any]:
    """Build a source-complete JSONL-ready context without repeated IDs."""
    state = _episode_state(video_id, data_root)
    index_by_id = {item["segment_id"]: int(item["clean_index"]) for item in state["transcript"]}
    number_inventory: list[dict[str, Any]] = []
    for segment in state["transcript"]:
        mentions = numeric_mentions(segment.get("text", ""))
        if mentions:
            number_inventory.append({
                "clean_index": int(segment["clean_index"]),
                "segment_id": segment["segment_id"],
                "mentions": [
                    {**mention, "occurrence": occurrence}
                    for occurrence, mention in enumerate(mentions)
                ],
            })
    chunks = [
        [
            int(chunk["chunk_number"]),
            index_by_id[chunk["first_segment_id"]],
            index_by_id[chunk["last_segment_id"]],
        ]
        for chunk in state["chunks"]
    ]
    segments = [
        [
            int(segment["clean_index"]),
            float(segment["start_seconds"]),
            float(segment.get("duration_seconds", 0.0)),
            segment["text"],
        ]
        for segment in state["transcript"]
    ]
    calibration_targets: list[dict[str, Any]] = []
    for test in state["calibration"].get("tests", []):
        if not isinstance(test, dict):
            continue
        target = test.get("target") if isinstance(test.get("target"), dict) else test
        segment_ids = target.get("segment_ids", []) if isinstance(target, dict) else []
        calibration_targets.append({
            "calibration_id": test.get("calibration_id"),
            "clean_indices": [index_by_id[segment_id] for segment_id in segment_ids if segment_id in index_by_id],
        })
    route_map = []
    for chunk_number, start, end in chunks:
        chunk_signals = [
            signal for signal in state["signals"]
            if start <= int(signal.get("clean_index", -1)) <= end
        ]
        route_map.append({
            "chunk": chunk_number,
            "range": [start, end],
            "signal_counts": dict(sorted(Counter(
                signal_type
                for signal in chunk_signals
                for signal_type in signal.get("signal_types", [])
            ).items())),
            "numeric_indices": [
                item["clean_index"] for item in number_inventory
                if start <= item["clean_index"] <= end
            ],
            "calibration_ids": [
                item["calibration_id"] for item in calibration_targets
                if any(start <= index <= end for index in item["clean_indices"])
            ],
        })
    baseline_ledger = ledger_for_signals(state["signals"], [])
    baseline_risks = review_autocheck.excluded_risk_clusters(
        state["transcript"], state["signals"], baseline_ledger, covered_segment_ids=set()
    )
    header = {
        "kind": "gold_episode_context",
        "schema_version": "2.2.0",
        "extraction_architecture": CANONICAL_EXTRACTION_ARCHITECTURE,
        "episode_video_id": video_id,
        "payload_format": COMPACT_EPISODE_PAYLOAD_FORMAT_V3,
        "segment_index_mode": "zero_based",
        "segment_columns": ["clean_index", "start_seconds", "duration_seconds", "text"],
        "chunk_columns": ["chunk_number", "first_clean_index", "last_clean_index"],
        "segment_count": len(segments),
        "chunk_count": len(chunks),
        "chunks": chunks,
        "numeric_segment_count": len(number_inventory),
        "number_inventory": number_inventory,
        "calibration_targets": calibration_targets,
        "transcript_semantic_index": semantic_navigation_summary(
            video_id, data_root, state["transcript"]
        ),
        "semantic_route_map": route_map,
        "risk_recall_index": [{
            "cluster_id": item["cluster_id"],
            "source_cluster_id": item["source_cluster_id"],
            "source_semantic_sha256": item["source_semantic_sha256"],
            "range": item["clean_index_range"],
            "segment_ids": item["segment_ids"],
            "signal_types": item["signal_types"],
            "score": item["score"],
        } for item in baseline_risks],
        "draft_contract": {
            "semantic_authority": "complete_chronological_transcript",
            "deterministic_controls": {
                "numbers": "number_inventory and numeric_occurrence_matrix",
                "calibration": "calibration_targets and final candidate bindings",
                "boundaries": "risk_recall_index and semantic_closure_index",
                "dispositions": "captured, retained_support, or source-scoped incidental",
                "exact_duplicates": "hard blocker; never auto-merge candidate meaning",
            },
            "blind_semantic_compiler": "research_only_not_a_production_route",
            "procedural_types_requiring_steps": sorted(PROCEDURAL_TYPES),
            "numbers": "use source_segment_id/source_clean_index plus source_span or source_occurrence; compiler copies raw verbatim",
            "number_source_aliases": {
                "sid": "source_segment_id", "si": "source_clean_index",
                "sp": "source_span", "so": "source_occurrence",
            },
            "evidence": "keep minimal evidence atomic; use support only when it materially sustains the same proposition",
            "risk_recall_acknowledgements_required": True,
            "audit_warning_dispositions": {
                "top_level_key": "audit_warning_dispositions",
                "compact_key": "w",
                "shape": {"warning_id": "warning-...", "disposition": "incidental", "justification": "source-backed reason"},
                "allowed": ["captured", "retained_support", "incidental", "relation_not_useful", "confirmed_source_backed", "defer_to_final_audit"],
            },
            "claim_evidence_warning_dispositions_required": True,
            "semantic_closure_dispositions_required": True,
            "prelint_before_preview": True,
            "authoring_checklist": {
                "procedural": "framework, playbook_step, and script require non-empty steps",
                "quantitative": "material numbers require literal raw evidence plus attribution, risk, and caveat when reported",
                "relations": "parent and child links must be symmetric and acyclic",
                "evidence": "minimal ranges must be atomic; support must sustain the same proposition",
            },
        },
        "prepared_input_semantic_sha256": _prepared_input_signature(state),
        "legacy_content_reads": 0,
    }
    result = {"header": header, "segments": segments}
    result["semantic_sha256"] = sha256_semantic_json(result)
    return result


def write_compact_reading_context(path: Path, context: dict[str, Any]) -> dict[str, Any]:
    """Write the compact context as stable JSONL and return its identity."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(context["header"], ensure_ascii=False, separators=(",", ":")) + "\n")
        for segment in context["segments"]:
            handle.write(json.dumps(segment, ensure_ascii=False, separators=(",", ":")) + "\n")
    temporary.replace(path)
    return {
        "path": str(path),
        "physical_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "semantic_sha256": context["semantic_sha256"],
        "bytes": path.stat().st_size,
        "segment_count": len(context["segments"]),
    }


def validate_compact_reading_context(path: Path, transcript: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        header = json.loads(lines[0])
        records = [json.loads(line) for line in lines[1:]]
    except (OSError, ValueError, json.JSONDecodeError, IndexError) as exc:
        return [f"compact context is unreadable: {exc}"]
    if header.get("segment_count") != len(records) or len(records) != len(transcript):
        errors.append("compact context segment count differs from transcript")
    expected = [[int(item["clean_index"]), float(item["start_seconds"]), float(item.get("duration_seconds", 0.0)), item["text"]] for item in transcript]
    if records != expected:
        errors.append("compact context does not preserve transcript text and order exactly")
    return errors


def bootstrap_episode(request: dict[str, Any]) -> dict[str, Any]:
    """Perform the complete certified preflight from one file-based request."""
    phase_started_at = _utc_now()
    started = time.perf_counter()
    video_id = str(request.get("video_id", "")).strip()
    if not video_id:
        return {"status": "blocked", "stopped_at": "request", "errors": ["video_id is required"]}
    data_root = Path(request.get("data_root") or os.environ.get("MSF_DATA_DIR", ""))
    job_dir = Path(request.get("job_dir") or "")
    if not str(data_root) or not str(job_dir):
        return {"status": "blocked", "stopped_at": "request", "errors": ["data_root and job_dir are required"]}
    _validate_job_dir(job_dir)
    session = _load_or_start_session(job_dir, video_id, epic_started_at=request.get("epic_started_at"))
    preflight = raw_preflight(video_id, data_root)
    if preflight["errors"]:
        return {"status": "blocked", "stopped_at": "raw_preflight", "preflight": preflight}
    out = data_root / "processed" / video_id / "gold_extraction"
    prepared = None
    if not (out / "gold_extraction_status.json").exists():
        if request.get("prepare_if_missing", True) is not True:
            return {"status": "blocked", "stopped_at": "preparation", "errors": ["gold is not prepared"]}
        prepared = prepare_episode(video_id, data_root)
        if prepared.get("errors"):
            return {"status": "blocked", "stopped_at": "preparation", "preparation": prepared}
    state = _episode_state(video_id, data_root)
    context = build_compact_reading_context(video_id, data_root)
    context_path = Path(request.get("context_path") or job_dir / "episode_context.jsonl")
    context_identity = write_compact_reading_context(context_path, context)
    context_errors = validate_compact_reading_context(context_path, state["transcript"])
    if context_errors:
        return {"status": "blocked", "stopped_at": "context", "errors": context_errors}
    source_paths = [Path(preflight["metadata_path"]), Path(preflight["transcript_path"])]
    content_segments = data_root / "processed" / video_id / "content_segments.json"
    if content_segments.exists():
        source_paths.append(content_segments)
    run_manifest = {
        "schema_version": "1.0.0",
        "kind": "gold_episode_bootstrap",
        "status": "ready",
        "extraction_architecture": CANONICAL_EXTRACTION_ARCHITECTURE,
        "episode_video_id": video_id,
        "runtime": {"python": os.path.realpath(os.sys.executable), "version": os.sys.version.split()[0], "wsl": _is_wsl()},
        "data_root": str(data_root.resolve()),
        "job_dir": str(job_dir.resolve()),
        "source_files": [{"path": str(path), **json_hashes(path)} for path in source_paths],
        "prepared": prepared,
        "lifecycle": state["status"].get("status"),
        "pending_chunks": [item["chunk_number"] for item in state["status"].get("chunks", []) if item.get("status") != "completed"],
        "context": context_identity,
        "selection_receipt": request.get("selection_receipt"),
        "revision_id": request.get("revision_id"),
        "export_suffix": request.get("export_suffix"),
        "runtime_snapshot": (
            load_json(job_dir / "runtime_snapshot_binding.json")
            if (job_dir / "runtime_snapshot_binding.json").exists() else None
        ),
        "elapsed_ms": _elapsed_ms(started),
    }
    core = copy.deepcopy(run_manifest)
    run_manifest["semantic_sha256"] = sha256_semantic_json(core)
    manifest_path = job_dir / "episode_run_manifest.json"
    write_json(manifest_path, run_manifest)
    _record_session_event(job_dir, video_id, "preflight_and_context", {
        "context_ms": run_manifest["elapsed_ms"], "context_bytes": context_identity["bytes"],
        "segment_count": context_identity["segment_count"],
    }, started_at=phase_started_at)
    return {**run_manifest, "run_manifest": str(manifest_path)}


def _evidence_scope_warnings(
    reviews: dict[str, dict[str, Any]],
    transcript: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {item["segment_id"]: item for item in transcript}
    warnings: list[dict[str, Any]] = []
    for review in reviews.values():
        if not isinstance(review, dict):
            continue
        for candidate in review.get("candidates", []):
            if not isinstance(candidate, dict):
                continue
            evidence = candidate.get("evidence", {})
            minimal = evidence.get("minimal_quote", []) if isinstance(evidence, dict) else []
            support = evidence.get("support_segments", []) if isinstance(evidence, dict) else []
            all_citations = [item for item in [*minimal, *support] if isinstance(item, dict)]
            indices = [
                int(by_id[item["segment_id"]]["clean_index"])
                for item in all_citations
                if item.get("segment_id") in by_id
            ]
            candidate_id = str(candidate.get("candidate_id", "<unknown>"))
            if indices and max(indices) - min(indices) > 12:
                warnings.append({
                    "candidate_id": candidate_id,
                    "field": "evidence",
                    "category": "broad_evidence_scope",
                    "evidence": {"clean_index_range": [min(indices), max(indices)]},
                    "expected": "keep evidence atomic or justify why the full range supports one proposition",
                })
            minimal_text = " ".join(str(item.get("quote_verbatim", "")) for item in minimal if isinstance(item, dict))
            support_text = " ".join(str(item.get("quote_verbatim", "")) for item in support if isinstance(item, dict))
            if not candidate.get("numbers") and support_text and MATERIAL_NUMBER_RE.search(support_text) and not MATERIAL_NUMBER_RE.search(minimal_text):
                warnings.append({
                    "candidate_id": candidate_id,
                    "field": "evidence.support_segments",
                    "category": "support_only_numeric_evidence",
                    "evidence": {"numeric_tokens": MATERIAL_NUMBER_RE.findall(support_text)},
                    "expected": "remove incidental numeric support or structure the material number from literal evidence",
                })
    return warnings


def _fixed_point_risk_clusters(
    reviews: dict[str, dict[str, Any]],
    transcript: list[dict[str, Any]],
    signals: list[dict[str, Any]],
    source_clusters: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Predict risk clusters exposed if support evidence is narrowed later."""
    candidates: list[dict[str, Any]] = []
    decisions: dict[str, dict[str, Any]] = {}
    for review in reviews.values():
        if not isinstance(review, dict):
            continue
        for candidate in review.get("candidates", []):
            if not isinstance(candidate, dict):
                continue
            minimal_candidate = copy.deepcopy(candidate)
            evidence = minimal_candidate.get("evidence", {})
            if isinstance(evidence, dict):
                evidence["support_segments"] = []
            candidates.append(minimal_candidate)
        for decision in review.get("ledger_decisions", []):
            if isinstance(decision, dict) and decision.get("segment_id"):
                decisions[str(decision["segment_id"])] = decision
    ledger = ledger_for_signals(signals, candidates, decisions)
    covered = {
        item.get("segment_id")
        for candidate in candidates
        for item in candidate.get("evidence", {}).get("minimal_quote", [])
        if isinstance(item, dict) and item.get("segment_id")
    }
    return review_autocheck.excluded_risk_clusters(
        transcript,
        signals,
        ledger,
        covered_segment_ids=covered,
        source_clusters=source_clusters,
    )


def _risk_acknowledgement_for(
    cluster: dict[str, Any],
    acknowledgement_items: list[dict[str, Any]],
) -> dict[str, Any] | None:
    by_id = {item.get("cluster_id"): item for item in acknowledgement_items}
    acknowledgement = by_id.get(cluster.get("cluster_id"))
    if acknowledgement:
        return acknowledgement
    source_cluster_id = cluster.get("source_cluster_id")
    source_ids = set(cluster.get("source_segment_ids", []))
    residual_ids = set(cluster.get("residual_segment_ids", cluster.get("segment_ids", [])))
    scoped = []
    if source_cluster_id and residual_ids:
        for item in acknowledgement_items:
            item_ids = set(item.get("source_segment_ids", []))
            if item.get("source_cluster_id") == source_cluster_id and item_ids and residual_ids <= item_ids:
                scoped.append((len(item_ids), item))
    if scoped:
        scoped.sort(key=lambda pair: pair[0])
        return scoped[0][1]
    if source_cluster_id and residual_ids and residual_ids <= source_ids:
        return by_id.get(source_cluster_id)
    return None


def _risk_acknowledgement_is_valid(
    cluster: dict[str, Any],
    acknowledgement: dict[str, Any] | None,
    *,
    allowed: set[str],
) -> bool:
    if not acknowledgement or acknowledgement.get("disposition") not in allowed:
        return False
    if not str(acknowledgement.get("justification", "")).strip():
        return False
    if acknowledgement.get("disposition") != "incidental":
        return True
    residual_ids = set(cluster.get("residual_segment_ids", cluster.get("segment_ids", [])))
    reviewed_ids = set(acknowledgement.get("source_segment_ids", []))
    return bool(residual_ids) and residual_ids <= reviewed_ids


def _consolidated_repair_manifest(
    compiled: dict[str, Any],
    report: dict[str, Any],
    review_gate: list[dict[str, Any]],
    evidence_scope_warnings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Collapse the pure prelint into one sparse, source-addressable edit plan."""
    rows: list[dict[str, Any]] = []

    def add(source: str, item: dict[str, Any], requirement: str) -> None:
        candidate_ids = sorted(set(
            [str(value) for value in item.get("candidate_ids", []) if value]
            + ([str(item["candidate_id"])] if item.get("candidate_id") else [])
        ))
        segment_ids = sorted(set(
            [str(value) for value in item.get("segment_ids", []) if value]
            + ([str(item["segment_id"])] if item.get("segment_id") else [])
        ))
        core = {
            "source": source,
            "requirement": requirement,
            "category": item.get("category") or item.get("closure_kind") or item.get("field"),
            "candidate_ids": candidate_ids,
            "segment_ids": segment_ids,
            "field": item.get("field"),
            "issue": item.get("issue") or item.get("expected"),
        }
        core["repair_id"] = "repair-" + sha256_semantic_json(core)[:16]
        core["evidence"] = {
            key: copy.deepcopy(value)
            for key, value in item.items()
            if key not in {"review", "warning_id"}
        }
        rows.append(core)

    for item in compiled.get("issues", []):
        if isinstance(item, dict):
            add("compiler", item, "hard_blocker")
    for group in report.get("hard_blockers", []):
        if not isinstance(group, dict):
            continue
        for item in group.get("items", []):
            if isinstance(item, dict):
                add("autocheck", {**item, "category": group.get("category")}, "hard_blocker")
    for group in review_gate:
        if not isinstance(group, dict):
            continue
        items = group.get("items") if isinstance(group.get("items"), list) else [group]
        for item in items:
            if isinstance(item, dict):
                add("review_gate", {**item, "category": group.get("category")}, "must_close")
    for item in evidence_scope_warnings:
        if isinstance(item, dict):
            add("evidence_scope", item, "audit_only")
    unique = {row["repair_id"]: row for row in rows}
    ordered = sorted(
        unique.values(),
        key=lambda row: (
            {"hard_blocker": 0, "must_close": 1, "audit_only": 2}.get(row["requirement"], 3),
            row["candidate_ids"],
            row["segment_ids"],
            row["repair_id"],
        ),
    )
    return {
        "schema_version": "1.0.0",
        "kind": "gold_consolidated_repair_manifest",
        "counts": {
            requirement: sum(row["requirement"] == requirement for row in ordered)
            for requirement in ("hard_blocker", "must_close", "audit_only")
        },
        "items": ordered,
        "numeric_occurrence_matrix": copy.deepcopy(report.get("numeric_occurrence_matrix", [])),
        "semantic_sha256": sha256_semantic_json(ordered),
    }


def inspect_episode_draft(
    video_id: str,
    data_root: Path,
    payload: dict[str, Any],
    *,
    replace_existing_reviews: bool = False,
) -> dict[str, Any]:
    """Return the complete pre-write inventory for an episode payload."""
    total_started = time.perf_counter()
    payload_bytes = len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    preflight_started = time.perf_counter()
    state = _episode_state(video_id, data_root)
    preflight_ms = _elapsed_ms(preflight_started)
    authoring_manifest, explicit_authoring_manifest = normalize_authoring_input(video_id, payload)
    manifest_issues = validate_authoring_manifest(
        video_id,
        authoring_manifest,
        require_adversarial_review=False,
        expected_segment_ids=(
            {str(item["segment_id"]) for item in state["transcript"]}
            if explicit_authoring_manifest
            else None
        ),
    )
    compiled_payload = manifest_to_compact_payload(
        authoring_manifest,
        replace_existing_reviews=replace_existing_reviews,
    )
    legacy_issues = _legacy_context_issues(compiled_payload)
    source_policy_issues = [*manifest_issues, *legacy_issues]
    if source_policy_issues:
        return {
            "status": "blocked",
            "mode": "check",
            "stopped_at": "source_policy",
            "terminal": False,
            "continue_required": True,
            "workflow_disposition": "repair_payload_and_repeat_check",
            "next_action": "Remove the forbidden legacy context, then repeat the read-only check in the same epic.",
            "episode_video_id": video_id,
            "issues": source_policy_issues,
            "hard_blockers": source_policy_issues,
            "audit_warnings": [],
            "metrics": {"preflight_ms": preflight_ms, "total_ms": _elapsed_ms(total_started)},
            "authoring_manifest_semantic_sha256": authoring_manifest["semantic_sha256"],
        }
    if state["status"].get("status") == "complete" and state["status"].get("audit_status") == "passed":
        return {
            "status": "protected",
            "mode": "check",
            "episode_video_id": video_id,
            "issues": [],
            "hard_blockers": [],
            "audit_warnings": [],
            "metrics": {"preflight_ms": preflight_ms, "total_ms": _elapsed_ms(total_started)},
        }

    compile_started = time.perf_counter()
    compiled = compile_payload(
        video_id,
        compiled_payload,
        state["status"],
        state["transcript"],
        copy.deepcopy(state["reviews"]),
    )
    compile_ms = _elapsed_ms(compile_started)
    if compiled["issues"]:
        repair_manifest = _consolidated_repair_manifest(compiled, {}, [], [])
        return {
            "status": "blocked",
            "mode": "check",
            "stopped_at": "compiler",
            "terminal": False,
            "continue_required": True,
            "workflow_disposition": "repair_payload_and_repeat_check",
            "next_action": "Repair every compiler issue from the current source-backed payload, then repeat the read-only check in the same epic.",
            "episode_video_id": video_id,
            "issues": compiled["issues"],
            "hard_blockers": [],
            "audit_warnings": [],
            "prelint_inventory": {
                "compiler_issues": compiled["issues"],
                "hard_blockers": [],
                "evidence_scope_warnings": [],
                "repair_scaffold": compiled.get("repair_scaffold", {}),
                "repair_manifest": repair_manifest,
            },
            "semantic_sha256": compiled["semantic_sha256"],
            "authoring_manifest_semantic_sha256": authoring_manifest["semantic_sha256"],
            "metrics": {
                "compile_ms": compile_ms,
                "autocheck_ms": 0.0,
                "preflight_ms": preflight_ms,
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
    compact_episode = (
        explicit_authoring_manifest
        or compiled_payload.get("payload_format") in COMPACT_EPISODE_PAYLOAD_FORMATS
    )
    enforce_risk_recall = compact_episode or compiled_payload.get("enforce_risk_recall") is True
    baseline_risk_clusters = review_autocheck.excluded_risk_clusters(
        state["transcript"],
        state["signals"],
        ledger_for_signals(state["signals"], []),
        covered_segment_ids=set(),
    ) if enforce_risk_recall else []
    if enforce_risk_recall:
        report["risk_recall_clusters"] = review_autocheck.excluded_risk_clusters(
            state["transcript"],
            state["signals"],
            ledger_for_signals(
                state["signals"],
                [
                    candidate
                    for review in compiled["composed_reviews"].values()
                    for candidate in review.get("candidates", [])
                    if isinstance(candidate, dict)
                ],
                {
                    str(decision["segment_id"]): decision
                    for review in compiled["composed_reviews"].values()
                    for decision in review.get("ledger_decisions", [])
                    if isinstance(decision, dict) and decision.get("segment_id")
                },
            ),
            covered_segment_ids={
                item.get("segment_id")
                for review in compiled["composed_reviews"].values()
                for candidate in review.get("candidates", [])
                if isinstance(candidate, dict)
                for key in ("minimal_quote", "support_segments")
                for item in candidate.get("evidence", {}).get(key, [])
                if isinstance(item, dict) and item.get("segment_id")
            },
            source_clusters=baseline_risk_clusters,
        )
    fixed_point_risks = _fixed_point_risk_clusters(
        compiled["composed_reviews"], state["transcript"], state["signals"], baseline_risk_clusters
    ) if enforce_risk_recall else []
    fixed_point_review_required: list[dict[str, Any]] = []
    if enforce_risk_recall:
        raw_acknowledgements = authoring_manifest.get("risk_recall_acknowledgements", [])
        acknowledgement_items = [
            item for item in raw_acknowledgements
            if isinstance(item, dict) and item.get("cluster_id")
        ] if isinstance(raw_acknowledgements, list) else []
        acknowledgements = {
            item.get("cluster_id"): item
            for item in acknowledgement_items
        }
        unresolved = []
        current_lineage_ids = {
            item.get("source_cluster_id") or item.get("cluster_id")
            for item in report.get("risk_recall_clusters", [])
        }
        for cluster in report.get("risk_recall_clusters", []):
            acknowledgement = _risk_acknowledgement_for(cluster, acknowledgement_items)
            if not _risk_acknowledgement_is_valid(
                cluster, acknowledgement, allowed={"incidental"}
            ):
                unresolved.append({
                    "category": "risk_recall_unreviewed",
                    "kind": "hard_blocker",
                    "items": [cluster],
                })
        for cluster in fixed_point_risks:
            lineage_id = cluster.get("source_cluster_id") or cluster.get("cluster_id")
            if lineage_id in current_lineage_ids:
                continue
            acknowledgement = _risk_acknowledgement_for(cluster, acknowledgement_items)
            if not _risk_acknowledgement_is_valid(
                cluster, acknowledgement, allowed={"incidental", "retained_support"}
            ):
                fixed_point_review_required.append({
                    "category": "fixed_point_risk_review_required",
                    "kind": "review_gate",
                    "cluster_id": cluster["cluster_id"],
                    "items": [cluster],
                    "expected": "acknowledge as incidental or retained_support with a source-based justification",
                })
        report["risk_recall_acknowledgements"] = list(acknowledgements.values())
        report["fixed_point_risk_clusters"] = fixed_point_risks
        report["hard_blockers"] = [*report.get("hard_blockers", []), *unresolved]
    required_warning_categories = (
        {"claim_evidence_alignment", SEMANTIC_CLOSURE_CATEGORY, SEMANTIC_WORKBENCH_CATEGORY}
        if compact_episode else set()
    )
    if explicit_authoring_manifest:
        required_warning_categories.update({
            "numeric_support_ambiguity",
            "interviewer_or_promo_only",
            "promo_or_interviewer",
            "calibration_semantic_ambiguity",
            "reported_case_caveat",
        })
    reviewed_warnings, warning_inventory, warning_review_required = review_audit_warnings(
        report.get("audit_warnings", []),
        authoring_manifest.get("audit_warning_dispositions", []),
        required_categories=required_warning_categories,
    )
    report["audit_warnings"] = reviewed_warnings
    report["audit_warning_inventory"] = warning_inventory
    adversarial_view = adversarial_authoring_view(authoring_manifest, report)
    if explicit_authoring_manifest:
        final_manifest_issues = validate_authoring_manifest(
            video_id,
            authoring_manifest,
            require_adversarial_review=True,
            expected_segment_ids={str(item["segment_id"]) for item in state["transcript"]},
        )
        calibration_issues = calibration_decision_issues(
            authoring_manifest,
            report.get("semantic_workbench", {}),
        )
        if final_manifest_issues:
            report["hard_blockers"] = [
                *report.get("hard_blockers", []),
                {
                    "category": "authoring_manifest",
                    "kind": "hard_blocker",
                    "items": final_manifest_issues,
                },
            ]
        if calibration_issues:
            report["hard_blockers"] = [
                *report.get("hard_blockers", []),
                {
                    "category": "calibration_proposition_equivalence",
                    "kind": "hard_blocker",
                    "items": calibration_issues,
                },
            ]
    invariant_review_gate = [*fixed_point_review_required, *warning_review_required]
    source_complete_issues = source_complete_invariant_issues(
        report,
        reviewed_warnings=reviewed_warnings,
        review_gate=invariant_review_gate,
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
    report["semantic_report_hash"] = sha256_semantic_json({key: value for key, value in report.items() if key != "semantic_report_hash"})
    autocheck_ms = _elapsed_ms(autocheck_started)
    evidence_scope_warnings = _evidence_scope_warnings(compiled["composed_reviews"], state["transcript"])
    prepared_input_signature = _prepared_input_signature(state)
    composed_reviews_signature = _composed_reviews_signature(compiled["composed_reviews"])
    review_gate = invariant_review_gate
    repair_manifest = _consolidated_repair_manifest(
        compiled, report, review_gate, evidence_scope_warnings
    )
    needs_local_repair = bool(report["hard_blockers"] or review_gate)
    result = {
        "status": "blocked" if needs_local_repair else "ready_to_apply",
        "mode": "check",
        "extraction_architecture": CANONICAL_EXTRACTION_ARCHITECTURE,
        "stopped_at": ("autocheck" if report["hard_blockers"] else "review_gate") if needs_local_repair else None,
        "episode_video_id": video_id,
        "issues": [],
        "hard_blockers": report["hard_blockers"],
        "audit_warnings": report.get("audit_warnings", []),
        "prelint_inventory": {
            "compiler_issues": [],
            "hard_blockers": report["hard_blockers"],
            "evidence_scope_warnings": evidence_scope_warnings,
            "fixed_point_risk_clusters": fixed_point_risks,
            "review_gate": review_gate,
            "audit_warning_inventory": warning_inventory,
            "semantic_closure_index": report.get("semantic_closure_index", []),
            "repair_manifest": repair_manifest,
        },
        "autocheck": report,
        "recall_view": sparse_recall_view(report),
        "semantic_sha256": compiled["semantic_sha256"],
        "prepared_input_semantic_sha256": prepared_input_signature,
        "composed_reviews_semantic_sha256": composed_reviews_signature,
        "autocheck_semantic_sha256": report["semantic_report_hash"],
        "authoring_manifest_semantic_sha256": authoring_manifest["semantic_sha256"],
        "authoring_decisions_semantic_sha256": authoring_manifest["authoring_decisions_sha256"],
        "adversarial_authoring_view": adversarial_view,
        "authoring_manifest_explicit": explicit_authoring_manifest,
        "metrics": {
            "preflight_ms": preflight_ms,
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
    if needs_local_repair:
        result.update({
            "terminal": False,
            "continue_required": True,
            "workflow_disposition": "repair_payload_and_repeat_check",
            "next_action": "Resolve the consolidated source-backed repair inventory, then repeat the read-only check in the same epic.",
        })
    return result


def prelint_episode_draft(video_id: str, data_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Run the complete in-memory draft inventory without producing a preview receipt."""
    preview = inspect_episode_draft(video_id, data_root, payload)
    preview_status = preview.get("status")
    protected = preview_status == "protected"
    clean = preview_status == "ready_to_apply"
    return {
        **preview,
        "status": "protected" if protected else ("prelint_clean" if clean else "needs_revision"),
        "mode": "prelint",
        "preview_status": preview_status,
        "prelint_clean": clean,
        "diagnostic_stage": preview.get("stopped_at"),
        "stopped_at": None,
        "terminal": protected,
        "continue_required": not protected,
        "workflow_disposition": (
            "stop_protected_episode" if protected
            else ("run_one_shot" if clean else "repair_payload_and_repeat_prelint")
        ),
        "next_action": (
            "Do not modify the protected complete/passed episode." if protected
            else (
                "Run the official one-shot persistence and finalization route in the same epic."
                if clean
                else "Repair the consolidated source-backed inventory and repeat prelint in the same epic; do not emit a final response."
            )
        ),
    }


def _bind_local_warning_identities(
    video_id: str,
    manifest: dict[str, Any],
    preview: dict[str, Any],
) -> dict[str, Any]:
    """Persist the local warning input identity after the read-only preview."""
    inventory = preview.get("prelint_inventory", {}).get("audit_warning_inventory", [])
    by_matched_id = {
        str(item.get("matched_disposition_warning_id") or item.get("warning_id")): item
        for item in inventory
        if isinstance(item, dict) and item.get("warning_id")
    }
    changed = False
    decisions = []
    for decision in manifest.get("audit_warning_dispositions", []):
        if not isinstance(decision, dict):
            decisions.append(decision)
            continue
        row = by_matched_id.get(str(decision.get("warning_id")))
        if row is None:
            decisions.append(decision)
            continue
        enriched = {
            **decision,
            "warning_id": row["warning_id"],
            "input_semantic_sha256": row["input_semantic_sha256"],
        }
        changed = changed or enriched != decision
        decisions.append(enriched)
    if not changed:
        return manifest
    rebound, _explicit = normalize_authoring_input(
        video_id,
        {**manifest, "audit_warning_dispositions": decisions},
    )
    return rebound


def run_episode(
    video_id: str,
    data_root: Path,
    payload: dict[str, Any],
    *,
    apply: bool = False,
    revision_id: str = "initial-finalization",
    export_suffix: str | None = None,
    executor_thread_id: str | None = None,
    preview_receipt_path: Path | None = None,
    create_preview_receipt: bool = False,
    audit_bundle_path: Path | None = None,
    job_dir: Path | None = None,
    mirror_job_dir: Path | None = None,
) -> dict[str, Any]:
    """Run the fast lane; no episode write occurs before a clean preview."""
    _validate_job_dir(job_dir)
    _load_or_start_session(job_dir, video_id)
    phase_started_at = _utc_now()
    total_started = time.perf_counter()
    payload_bytes = len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    authoring_manifest, explicit_authoring_manifest = normalize_authoring_input(video_id, payload)
    compiled_payload = manifest_to_compact_payload(authoring_manifest)
    preview = inspect_episode_draft(video_id, data_root, payload)
    if not apply or preview["status"] != "ready_to_apply":
        _record_session_event(
            job_dir, video_id, "preview", preview.get("metrics", {}),
            started_at=phase_started_at,
        )
        return preview

    authoring_manifest = _bind_local_warning_identities(video_id, authoring_manifest, preview)
    compiled_payload = manifest_to_compact_payload(authoring_manifest)

    if preview_receipt_path is None:
        return {
            **preview,
            "status": "blocked",
            "stopped_at": "preview_receipt",
            "error": "apply requires a clean preview receipt bound to the same payload",
        }
    if create_preview_receipt:
        preview_receipt_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(
            preview_receipt_path,
            make_preview_receipt(preview, revision_id=revision_id, export_suffix=export_suffix),
        )
    if not preview_receipt_path.exists():
        return {
            **preview,
            "status": "blocked",
            "stopped_at": "preview_receipt",
            "error": "preview receipt does not exist",
        }
    preview_receipt = load_json(preview_receipt_path)
    if not _preview_receipt_matches(
        preview,
        preview_receipt,
        revision_id=revision_id,
        export_suffix=export_suffix,
    ):
        return {
            **preview,
            "status": "conflict",
            "stopped_at": "preview_receipt",
            "error": "preview receipt is stale or belongs to a different payload, revision, or export",
        }

    if job_dir is not None:
        write_json(job_dir / "gold_authoring_manifest.json", authoring_manifest)
    persist_started = time.perf_counter()
    persisted = record(video_id, data_root, compiled_payload)
    persist_ms = _elapsed_ms(persist_started)

    finalize_started = time.perf_counter()
    finalized = finalize_episode(
        video_id,
        data_root,
        executor_thread_id=executor_thread_id,
        export_suffix=export_suffix,
        revision_id=revision_id,
        preview_receipt_path=preview_receipt_path,
        required_preview_sha256=preview["semantic_sha256"],
        audit_warning_dispositions=authoring_manifest.get("audit_warning_dispositions", []),
        require_warning_dispositions=(
            explicit_authoring_manifest
            or compiled_payload.get("payload_format") in COMPACT_EPISODE_PAYLOAD_FORMATS
        ),
    )
    finalize_ms = _elapsed_ms(finalize_started)
    metrics = {
        **preview["metrics"],
        "persist_ms": persist_ms,
        "finalize_ms": finalize_ms,
        "total_ms": _elapsed_ms(total_started),
        "review_write_operations": 0 if persisted.get("idempotent") else 1,
        "finalizer_calls": 1,
        "builds": 1 if finalized.get("build") else 0,
        "payload_bytes": payload_bytes,
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
        "preview_receipt": str(preview_receipt_path),
    }
    if finalized.get("status") in {"ready", "protected"} and finalized.get("packet"):
        if audit_bundle_path is None and job_dir is not None:
            audit_bundle_path = job_dir / "final_audit_dossier.jsonl"
        if audit_bundle_path is not None:
            bundle_started = time.perf_counter()
            audit_bundle_path.parent.mkdir(parents=True, exist_ok=True)
            if audit_bundle_path.suffix.lower() == ".jsonl":
                bundle = build_audit_dossier(
                    video_id,
                    data_root,
                    packet=Path(finalized["packet"]),
                    audit_warnings=result["audit_warnings"],
                    revision_id=revision_id,
                )
                identity = write_audit_dossier(audit_bundle_path, bundle)
                dossier_errors = validate_audit_dossier(audit_bundle_path, video_id, data_root, Path(finalized["packet"]))
                if dossier_errors:
                    result["status"] = "blocked"
                    result["stopped_at"] = "audit_dossier"
                    result["errors"] = dossier_errors
                artifact_key = "audit_dossier"
            else:
                bundle = build_audit_bundle(
                    video_id,
                    data_root,
                    packet=Path(finalized["packet"]),
                    audit_warnings=result["audit_warnings"],
                    revision_id=revision_id,
                )
                write_audit_bundle(audit_bundle_path, bundle)
                identity = {"path": str(audit_bundle_path), "semantic_sha256": bundle["semantic_sha256"]}
                artifact_key = "audit_bundle"
            metrics["audit_bundle_ms"] = _elapsed_ms(bundle_started)
            metrics["audit_bundles"] = 1
            metrics["audit_dossier_bytes"] = audit_bundle_path.stat().st_size
            mirrored = _mirror_final_artifact(audit_bundle_path, mirror_job_dir)
            if mirrored is not None:
                identity["mirror"] = mirrored
            result[artifact_key] = identity
            if job_dir is not None and not result.get("errors"):
                audit_request = write_audit_request(
                    job_dir,
                    build_audit_request(video_id, audit_bundle_path, phase="final"),
                )
                result["audit_request"] = audit_request
                metrics["audit_requests"] = 1
    metrics["total_ms"] = _elapsed_ms(total_started)
    metrics["full_result_bytes"] = len(
        json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )
    _record_session_event(
        job_dir, video_id, "apply_and_finalize", metrics,
        started_at=phase_started_at,
    )
    if finalized.get("status") in {"ready", "protected"}:
        record_operation_event(
            _episode_state(video_id, data_root)["out"],
            "episode_one_shot",
            preview["semantic_sha256"],
            metrics,
        )
    return result


def inspect_post_audit_remediation(
    video_id: str,
    data_root: Path,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    """Validate a complete-review remediation against the composed final state."""
    started = time.perf_counter()
    state = _episode_state(video_id, data_root)
    documents, changed, manifest_hash = prepare_patch(video_id, data_root, manifest)
    review_documents = {
        path.name: document
        for path, document in documents.items()
        if path.parent.name == "manual_reviews"
    }
    calibration_path = state["out"] / "calibration_tests.json"
    calibration = documents.get(calibration_path, state["calibration"])
    report = autocheck_state(
        video_id,
        status=state["status"],
        transcript=state["transcript"],
        chunks=state["chunks"],
        signals=state["signals"],
        calibration=calibration,
        reviews=review_documents,
        stored_ledger=[],
        prefer_stored_ledger=False,
    )
    hard_blockers = report.get("hard_blockers", [])
    return {
        "status": "ready_to_apply" if not hard_blockers else "blocked",
        "mode": "post_audit_remediation_check",
        "episode_video_id": video_id,
        "manifest_hash": manifest_hash,
        "changed_documents": changed,
        "review_count": len(review_documents),
        "candidate_count": sum(len(review.get("candidates", [])) for review in review_documents.values()),
        "hard_blockers": hard_blockers,
        "audit_warnings": report.get("audit_warnings", []),
        "recall_view": sparse_recall_view(report),
        "metrics": {"check_ms": _elapsed_ms(started)},
    }


def _contiguous_ranges(indexes: set[int]) -> list[list[int]]:
    ordered = sorted(indexes)
    if not ordered:
        return []
    ranges: list[list[int]] = []
    start = previous = ordered[0]
    for index in ordered[1:]:
        if index != previous + 1:
            ranges.append([start, previous])
            start = index
        previous = index
    ranges.append([start, previous])
    return ranges


def remediation_impact_closure(
    state: dict[str, Any],
    composed_reviews: dict[str, dict[str, Any]],
    prior_audit: dict[str, Any],
) -> dict[str, Any]:
    """Choose delta or full dossier before the remediation commit.

    The closure expands sealed finding ranges only through deterministic
    candidate, ledger and calibration dependencies.  Any unrelated change
    selects the integral dossier before the write instead of discovering the
    invariant failure after persistence.
    """
    base = audit_impact_set(prior_audit)
    index_by_segment = {
        str(item["segment_id"]): int(item["clean_index"])
        for item in state["transcript"]
    }

    def candidate_map(reviews: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {
            str(candidate["candidate_id"]): candidate
            for review in reviews.values()
            if isinstance(review, dict)
            for candidate in review.get("candidates", [])
            if isinstance(candidate, dict) and candidate.get("candidate_id")
        }

    def manual_decisions(reviews: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {
            str(decision["segment_id"]): decision
            for review in reviews.values()
            if isinstance(review, dict)
            for decision in review.get("ledger_decisions", [])
            if isinstance(decision, dict) and decision.get("segment_id")
        }

    def evidence_indexes(candidate: dict[str, Any] | None) -> set[int]:
        if not isinstance(candidate, dict):
            return set()
        return {
            index_by_segment[segment_id]
            for segment_id in review_autocheck._candidate_evidence_segment_ids(candidate)
            if segment_id in index_by_segment
        }

    before_candidates = candidate_map(state["reviews"])
    after_candidates = candidate_map(composed_reviews)
    changed_candidates = {
        candidate_id
        for candidate_id in set(before_candidates) | set(after_candidates)
        if sha256_semantic_json(before_candidates.get(candidate_id))
        != sha256_semantic_json(after_candidates.get(candidate_id))
    }
    closure_candidates = set(str(value) for value in base.get("candidate_ids", []))
    closure_indexes = {
        index
        for value in base.get("clean_index_ranges", [])
        if isinstance(value, list) and len(value) == 2
        for index in range(int(value[0]), int(value[1]) + 1)
    }
    full_reasons: list[str] = []
    for candidate_id in sorted(changed_candidates):
        indexes = evidence_indexes(before_candidates.get(candidate_id)) | evidence_indexes(after_candidates.get(candidate_id))
        if candidate_id in closure_candidates or indexes & closure_indexes:
            closure_candidates.add(candidate_id)
            closure_indexes.update(indexes)
        else:
            full_reasons.append(f"changed_candidate_outside_findings:{candidate_id}")

    before_ledger = ledger_for_signals(
        state["signals"], list(before_candidates.values()), manual_decisions(state["reviews"])
    )
    after_ledger = ledger_for_signals(
        state["signals"], list(after_candidates.values()), manual_decisions(composed_reviews)
    )
    before_ledger_by_id = {str(item.get("segment_id")): item for item in before_ledger}
    after_ledger_by_id = {str(item.get("segment_id")): item for item in after_ledger}
    changed_ledger_segments = {
        segment_id
        for segment_id in set(before_ledger_by_id) | set(after_ledger_by_id)
        if sha256_semantic_json(before_ledger_by_id.get(segment_id))
        != sha256_semantic_json(after_ledger_by_id.get(segment_id))
    }
    for segment_id in sorted(changed_ledger_segments):
        index = index_by_segment.get(segment_id)
        rows = [before_ledger_by_id.get(segment_id), after_ledger_by_id.get(segment_id)]
        destinations = {
            str(candidate_id)
            for row in rows if isinstance(row, dict)
            for candidate_id in row.get("candidate_ids", [])
        }
        if index is not None and (index in closure_indexes or destinations & closure_candidates):
            closure_indexes.add(index)
            closure_candidates.update(destinations & changed_candidates)
        else:
            full_reasons.append(f"changed_ledger_outside_findings:{segment_id}")

    before_calibration = calibration_coverage(state["calibration"], list(before_candidates.values()), before_ledger)
    after_calibration = calibration_coverage(state["calibration"], list(after_candidates.values()), after_ledger)
    before_tests = {str(item.get("calibration_id")): item for item in before_calibration.get("tests", [])}
    after_tests = {str(item.get("calibration_id")): item for item in after_calibration.get("tests", [])}
    closure_calibrations = set(str(value) for value in base.get("calibration_ids", []))
    for calibration_id in sorted(set(before_tests) | set(after_tests)):
        before = before_tests.get(calibration_id)
        after = after_tests.get(calibration_id)
        if sha256_semantic_json(before) == sha256_semantic_json(after):
            continue
        target_segments = {
            str(value)
            for row in (before, after) if isinstance(row, dict)
            for value in row.get("segment_ids", [])
        }
        target_indexes = {index_by_segment[value] for value in target_segments if value in index_by_segment}
        linked_candidates = {
            str(value)
            for row in (before, after) if isinstance(row, dict)
            for value in row.get("semantic_candidate_ids", [])
        }
        if (
            calibration_id in closure_calibrations
            or target_indexes & closure_indexes
            or linked_candidates & closure_candidates
        ):
            closure_calibrations.add(calibration_id)
            closure_indexes.update(target_indexes)
            closure_candidates.update(linked_candidates & changed_candidates)
        else:
            full_reasons.append(f"changed_calibration_outside_findings:{calibration_id}")

    core = {
        "candidate_ids": sorted(closure_candidates),
        "clean_index_ranges": _contiguous_ranges(closure_indexes),
        "warning_ids": list(base.get("warning_ids", [])),
        "calibration_ids": sorted(closure_calibrations),
        "categories": sorted(set(base.get("categories", [])) | {"dependency_closed_remediation"}),
        "numeric_revalidation": bool(base.get("numeric_revalidation")),
        "relation_revalidation": bool(base.get("relation_revalidation")),
        "changed_candidate_ids": sorted(changed_candidates),
        "changed_ledger_segment_ids": sorted(changed_ledger_segments),
        "artifact_mode": "full_dossier" if full_reasons else "delta",
        "full_dossier_reasons": sorted(set(full_reasons)),
    }
    return {**core, "semantic_sha256": sha256_semantic_json(core)}


def run_authoring_manifest_remediation(
    video_id: str,
    data_root: Path,
    manifest: dict[str, Any],
    *,
    revision_id: str,
    export_suffix: str | None,
    executor_thread_id: str | None = None,
    audit_bundle_path: Path | None = None,
    job_dir: Path | None = None,
    mirror_job_dir: Path | None = None,
) -> dict[str, Any]:
    """Replace the complete semantic snapshot once and emit a focal delta."""
    _validate_job_dir(job_dir)
    _load_or_start_session(job_dir, video_id)
    phase_started_at = _utc_now()
    total_started = time.perf_counter()
    normalized, explicit = normalize_authoring_input(video_id, manifest)
    if not explicit:
        raise ValueError("post-audit authoring remediation requires gold_authoring_manifest_v1")
    prior_manifest_path = job_dir / "gold_authoring_manifest.json" if job_dir is not None else None
    if prior_manifest_path is None or not prior_manifest_path.is_file():
        return {
            "status": "blocked",
            "stopped_at": "authoring_manifest_lineage",
            "error": "prior gold_authoring_manifest.json is required for one-transaction remediation",
        }
    prior_manifest = load_json(prior_manifest_path)
    expected_base = prior_manifest.get("semantic_sha256")
    if normalized.get("base_manifest_semantic_sha256") != expected_base:
        return {
            "status": "conflict",
            "stopped_at": "authoring_manifest_lineage",
            "error": "remediation manifest does not reference the current authoring manifest",
            "expected_base_manifest_semantic_sha256": expected_base,
        }

    precondition_started = time.perf_counter()
    request_path = job_dir / "audit_request_receipt.json"
    envelope_path = job_dir / "audit_envelope.json"
    before_path = job_dir / "final_audit_dossier.jsonl"
    precondition_errors: list[str] = []
    if not request_path.is_file():
        precondition_errors.append("sealed audit request is required before remediation")
    if not envelope_path.is_file():
        precondition_errors.append("materialized findings envelope is required before remediation")
    if not before_path.is_file():
        precondition_errors.append("sealed pre-remediation dossier is required before remediation")
    if not precondition_errors:
        request = load_json(request_path)
        envelope = load_json(envelope_path)
        precondition_errors.extend(validate_audit_request(request))
        precondition_errors.extend(validate_audit_envelope(envelope, request))
        if request.get("episode_video_id") != video_id or envelope.get("episode_video_id") != video_id:
            precondition_errors.append("audit request or envelope episode identity mismatch")
    if precondition_errors:
        metrics = {
            "envelope_precondition_ms": _elapsed_ms(precondition_started),
            "patches": 0,
            "remediations": 0,
            "review_write_operations": 0,
            "finalizer_calls": 0,
            "builds": 0,
            "total_ms": _elapsed_ms(total_started),
        }
        _record_session_event(
            job_dir,
            video_id,
            "post_audit_remediation",
            metrics,
            started_at=phase_started_at,
        )
        return {
            "status": "blocked",
            "stopped_at": "audit_envelope_precondition",
            "errors": sorted(set(precondition_errors)),
            "metrics": metrics,
            "writes_gold": False,
        }
    prior_audit = envelope.get("audit_payload", {})

    check = inspect_episode_draft(
        video_id,
        data_root,
        normalized,
        replace_existing_reviews=True,
    )
    if check.get("status") != "ready_to_apply":
        _record_session_event(
            job_dir,
            video_id,
            "post_audit_remediation",
            check.get("metrics", {}),
            started_at=phase_started_at,
        )
        return {**check, "mode": "authoring_manifest_remediation_check"}

    normalized = _bind_local_warning_identities(video_id, normalized, check)

    compiled_payload = manifest_to_compact_payload(
        normalized,
        replace_existing_reviews=True,
    )
    closure_started = time.perf_counter()
    state = _episode_state(video_id, data_root)
    compiled_snapshot = compile_payload(
        video_id,
        compiled_payload,
        state["status"],
        state["transcript"],
        copy.deepcopy(state["reviews"]),
    )
    if compiled_snapshot.get("issues"):
        return {
            **check,
            "status": "blocked",
            "stopped_at": "impact_closure_compile",
            "issues": compiled_snapshot["issues"],
            "writes_gold": False,
        }
    impact_closure = remediation_impact_closure(
        state,
        compiled_snapshot["composed_reviews"],
        prior_audit,
    )
    impact_closure_ms = _elapsed_ms(closure_started)
    persist_started = time.perf_counter()
    persisted = record(video_id, data_root, compiled_payload)
    persist_ms = _elapsed_ms(persist_started)
    write_json(prior_manifest_path, normalized)

    finalized_started = time.perf_counter()
    finalized = finalize_episode(
        video_id,
        data_root,
        executor_thread_id=executor_thread_id,
        export_suffix=export_suffix,
        revision_id=revision_id,
        audit_warning_dispositions=normalized.get("audit_warning_dispositions", []),
        require_warning_dispositions=True,
    )
    finalize_ms = _elapsed_ms(finalized_started)
    metrics = {
        **check.get("metrics", {}),
        "persist_ms": persist_ms,
        "finalize_ms": finalize_ms,
        "patches": 1,
        "remediations": 1,
        "review_write_operations": 0 if persisted.get("idempotent") else 1,
        "finalizer_calls": 1,
        "builds": 1 if finalized.get("build") else 0,
        "impact_closure_ms": impact_closure_ms,
    }
    result: dict[str, Any] = {
        "status": finalized.get("status"),
        "mode": "authoring_manifest_remediation",
        "episode_video_id": video_id,
        "revision_id": revision_id,
        "base_manifest_semantic_sha256": expected_base,
        "authoring_manifest_semantic_sha256": normalized["semantic_sha256"],
        "persist": persisted,
        "finalization": finalized,
        "hard_blockers": finalized.get("hard_blockers", []),
        "audit_warnings": finalized.get("audit_warnings", []),
        "metrics": metrics,
        "impact_closure": impact_closure,
    }
    if finalized.get("status") in {"ready", "protected"} and finalized.get("packet"):
        after_path = audit_bundle_path or (job_dir / "final_audit_dossier_remediated.jsonl")
        dossier = build_audit_dossier(
            video_id,
            data_root,
            packet=Path(finalized["packet"]),
            audit_warnings=result["audit_warnings"],
            revision_id=revision_id,
        )
        result["audit_dossier"] = write_audit_dossier(after_path, dossier)
        dossier_errors = validate_audit_dossier(
            after_path,
            video_id,
            data_root,
            Path(finalized["packet"]),
        )
        if dossier_errors:
            metrics["audit_bundles"] = 1
            metrics["total_ms"] = _elapsed_ms(total_started)
            _record_session_event(
                job_dir,
                video_id,
                "post_audit_remediation",
                metrics,
                started_at=phase_started_at,
            )
            return {
                **result,
                "status": "blocked",
                "stopped_at": "audit_dossier",
                "errors": dossier_errors,
                "commit_state": "persisted_and_finalized",
                "next_action": "repair dossier generation without repeating the gold write",
            }
        delta = None
        delta_errors: list[str] = []
        if impact_closure.get("artifact_mode") == "delta":
            delta = build_reaudit_delta(
                before_path,
                after_path,
                prior_audit,
                impact_closure=impact_closure,
            )
            delta_errors = validate_reaudit_delta(delta)
        if impact_closure.get("artifact_mode") == "full_dossier" or delta_errors:
            result["reaudit_delta"] = {
                "status": "preselected_full_dossier" if not delta_errors else "unexpected_rejection",
                "errors": delta_errors or impact_closure.get("full_dossier_reasons", []),
                "full_dossier_fallback": str(after_path),
            }
            result["audit_request"] = write_audit_request(
                job_dir,
                build_audit_request(video_id, after_path, phase="reaudit"),
            )
        else:
            delta_path = job_dir / "final_reaudit_delta.json"
            assert delta is not None
            write_json(delta_path, delta)
            result["reaudit_delta"] = {
                "path": str(delta_path),
                "semantic_sha256": delta["semantic_sha256"],
            }
            result["audit_request"] = write_audit_request(
                job_dir,
                build_audit_request(video_id, delta_path, phase="reaudit"),
            )
            mirrored = _mirror_final_artifact(delta_path, mirror_job_dir)
            if mirrored is not None:
                result["reaudit_delta"]["mirror"] = mirrored
        metrics["audit_bundles"] = 1
        metrics["audit_requests"] = 1
    metrics["total_ms"] = _elapsed_ms(total_started)
    _record_session_event(
        job_dir,
        video_id,
        "post_audit_remediation",
        metrics,
        started_at=phase_started_at,
    )
    return result


def run_post_audit_remediation(
    video_id: str,
    data_root: Path,
    manifest: dict[str, Any],
    *,
    revision_id: str,
    export_suffix: str | None,
    executor_thread_id: str | None = None,
    audit_bundle_path: Path | None = None,
    job_dir: Path | None = None,
    mirror_job_dir: Path | None = None,
) -> dict[str, Any]:
    """Patch complete reviews once, re-finalize, and emit a fresh audit dossier.

    This lane deliberately bypasses the initial recorder: compact episode
    payloads contain only pending chunks, so a fully reviewed episode would
    otherwise compile as an empty batch and collide with an unrelated receipt.
    """
    if is_authoring_manifest(manifest):
        return run_authoring_manifest_remediation(
            video_id,
            data_root,
            manifest,
            revision_id=revision_id,
            export_suffix=export_suffix,
            executor_thread_id=executor_thread_id,
            audit_bundle_path=audit_bundle_path,
            job_dir=job_dir,
            mirror_job_dir=mirror_job_dir,
        )
    _validate_job_dir(job_dir)
    _load_or_start_session(job_dir, video_id)
    phase_started_at = _utc_now()
    total_started = time.perf_counter()
    state = _episode_state(video_id, data_root)
    manifest_hash = sha256_json(manifest)
    history_path = state["out"] / "fastpath_patch_history.json"
    history = load_json(history_path) if history_path.exists() else {"applied": []}
    already_applied = manifest_hash in {
        item.get("manifest_hash") for item in history.get("applied", [])
    }
    if already_applied:
        check = {
            "status": "ready_to_apply",
            "mode": "post_audit_remediation_recovery",
            "episode_video_id": video_id,
            "manifest_hash": manifest_hash,
            "hard_blockers": [],
            "metrics": {"check_ms": 0.0},
        }
    else:
        check = inspect_post_audit_remediation(video_id, data_root, manifest)
        if check["status"] != "ready_to_apply":
            _record_session_event(
                job_dir, video_id, "post_audit_remediation", check.get("metrics", {}),
                started_at=phase_started_at,
            )
            return check

    patch_preview_receipt = None
    if not already_applied and manifest.get("assertion_mode") == "source_canonical":
        patch_preview_receipt = apply_gold_patch(
            video_id, data_root, manifest, apply=False,
        )["preview"]
    patch_started = time.perf_counter()
    applied = apply_gold_patch(
        video_id, data_root, manifest, apply=True,
        preview_receipt=patch_preview_receipt,
    )
    patch_ms = _elapsed_ms(patch_started)
    finalized_started = time.perf_counter()
    finalized = finalize_episode(
        video_id,
        data_root,
        executor_thread_id=executor_thread_id,
        export_suffix=export_suffix,
        revision_id=revision_id,
        audit_warning_dispositions=manifest.get("audit_warning_dispositions", []),
        require_warning_dispositions=bool(manifest.get("require_warning_dispositions", False)),
    )
    finalize_ms = _elapsed_ms(finalized_started)
    metrics = {
        **check.get("metrics", {}),
        "patch_ms": patch_ms,
        "finalize_ms": finalize_ms,
        "patches": 0 if applied.get("mode") == "already_applied" else 1,
        "remediations": 0 if applied.get("mode") == "already_applied" else 1,
        "finalizer_calls": 1,
        "builds": 1 if finalized.get("build") else 0,
    }
    result = {
        "status": finalized.get("status"),
        "mode": "post_audit_remediation",
        "episode_video_id": video_id,
        "revision_id": revision_id,
        "manifest_hash": manifest_hash,
        "check": check,
        "patch": applied,
        "finalization": finalized,
        "hard_blockers": finalized.get("hard_blockers", []),
        "audit_warnings": finalized.get("audit_warnings", []),
        "metrics": metrics,
    }
    if finalized.get("status") in {"ready", "protected"} and finalized.get("packet"):
        if audit_bundle_path is None and job_dir is not None:
            audit_bundle_path = job_dir / "final_audit_dossier.jsonl"
        if audit_bundle_path is not None:
            bundle_started = time.perf_counter()
            dossier = build_audit_dossier(
                video_id,
                data_root,
                packet=Path(finalized["packet"]),
                audit_warnings=result["audit_warnings"],
                revision_id=revision_id,
            )
            identity = write_audit_dossier(audit_bundle_path, dossier)
            dossier_errors = validate_audit_dossier(
                audit_bundle_path, video_id, data_root, Path(finalized["packet"])
            )
            if dossier_errors:
                result.update(status="blocked", stopped_at="audit_dossier", errors=dossier_errors)
            result["audit_dossier"] = identity
            mirrored = _mirror_final_artifact(audit_bundle_path, mirror_job_dir)
            if mirrored is not None:
                identity["mirror"] = mirrored
            metrics["audit_bundle_ms"] = _elapsed_ms(bundle_started)
            metrics["audit_bundles"] = 1
    metrics["total_ms"] = _elapsed_ms(total_started)
    _record_session_event(
        job_dir, video_id, "post_audit_remediation", metrics,
        started_at=phase_started_at,
    )
    return result


def _compact_inventory_item(item: Any) -> Any:
    if not isinstance(item, dict):
        return item
    keys = (
        "candidate_id", "cluster_id", "source_cluster_id", "warning_id",
        "category", "kind", "clean_index_range", "segment_ids",
        "residual_segment_ids", "exclusion_reasons", "reason_code", "issue",
        "expected", "score", "signal_types", "disposition",
    )
    compact = {key: item.get(key) for key in keys if item.get(key) not in (None, [], {})}
    if not compact and "items" in item:
        compact["item_count"] = len(item.get("items", []))
    return compact


def _compact_inventory_groups(groups: Any, *, item_limit: int = 24) -> list[dict[str, Any]]:
    if not isinstance(groups, list):
        return []
    result: list[dict[str, Any]] = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        raw_items = group.get("items", []) if isinstance(group.get("items", []), list) else []
        compact_items = [_compact_inventory_item(item) for item in raw_items[:item_limit]]
        record = {
            key: group.get(key)
            for key in ("category", "kind", "cluster_id", "warning_id", "expected")
            if group.get(key) not in (None, "")
        }
        record["item_count"] = len(raw_items)
        if compact_items:
            record["items"] = compact_items
        if len(raw_items) > item_limit:
            record["items_truncated"] = len(raw_items) - item_limit
        result.append(record)
    return result


def _pending_risk_acknowledgements(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pending: list[dict[str, Any]] = []
    seen: set[str] = set()
    for group in groups:
        if group.get("category") not in {"risk_recall_unreviewed", "fixed_point_risk_review_required"}:
            continue
        for item in group.get("items", []):
            if not isinstance(item, dict):
                continue
            acknowledgement_id = str(item.get("source_cluster_id") or item.get("cluster_id") or "")
            if not acknowledgement_id or acknowledgement_id in seen:
                continue
            seen.add(acknowledgement_id)
            pending.append({
                "cluster_id": item.get("cluster_id") or acknowledgement_id,
                "source_cluster_id": acknowledgement_id,
                "source_segment_ids": item.get("residual_segment_ids", item.get("segment_ids", [])),
                "residual_cluster_id": item.get("cluster_id"),
                "range": item.get("clean_index_range"),
                "exclusion_reasons": item.get("exclusion_reasons", []),
                "allowed_dispositions": ["incidental", "retained_support"],
                "justification_required": True,
            })
    return pending


def _compact_calibration(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    tests = value.get("tests", []) if isinstance(value.get("tests"), list) else []
    return {
        key: value.get(key)
        for key in (
            "minimum_required", "generated_count", "covered_count", "status",
            "duplicate_target_segments",
        )
        if value.get(key) is not None
    } | {"target_count": len(tests)}


def _fit_cli_output(compact: dict[str, Any], max_bytes: int) -> dict[str, Any]:
    def size(value: dict[str, Any]) -> int:
        return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))

    if size(compact) <= max_bytes:
        return compact
    reduced = copy.deepcopy(compact)
    for key in ("audit_warnings", "evidence_scope_warnings"):
        groups = reduced.get(key, [])
        if isinstance(groups, list):
            reduced[key] = [
                {"category": item.get("category"), "kind": item.get("kind"), "item_count": item.get("item_count", 0)}
                for item in groups
                if isinstance(item, dict)
            ]
    for key in ("hard_blockers", "review_gate", "compiler_issues"):
        groups = reduced.get(key, [])
        if isinstance(groups, list):
            for group in groups:
                if isinstance(group, dict) and isinstance(group.get("items"), list):
                    original = group["items"]
                    group["items"] = original[:8]
                    if len(original) > 8:
                        group["items_truncated"] = int(group.get("items_truncated", 0)) + len(original) - 8
    reduced["stdout_truncated"] = True
    reduced["stdout_limit_bytes"] = max_bytes
    if size(reduced) <= max_bytes:
        return reduced
    def inventory_count(groups: Any) -> int:
        if not isinstance(groups, list):
            return 0
        count = 0
        for group in groups:
            if not isinstance(group, dict):
                continue
            if isinstance(group.get("item_count"), int):
                count += int(group["item_count"])
            elif isinstance(group.get("items"), list):
                count += len(group["items"]) + int(group.get("items_truncated", 0))
            else:
                count += 1
        return count

    return {
        "status": reduced.get("status"),
        "mode": reduced.get("mode"),
        "stopped_at": reduced.get("stopped_at"),
        "diagnostic_stage": reduced.get("diagnostic_stage"),
        "terminal": reduced.get("terminal"),
        "continue_required": reduced.get("continue_required"),
        "workflow_disposition": reduced.get("workflow_disposition"),
        "next_action": reduced.get("next_action"),
        "episode_video_id": reduced.get("episode_video_id"),
        "hard_blocker_count": inventory_count(reduced.get("hard_blockers", [])),
        "review_gate_count": inventory_count(reduced.get("review_gate", [])),
        "audit_warning_count": inventory_count(reduced.get("audit_warnings", [])),
        "pending_acknowledgements": reduced.get("pending_acknowledgements", [])[:16],
        "calibration": _compact_calibration(reduced.get("calibration")),
        "metrics": reduced.get("metrics"),
        "full_report": reduced.get("full_report"),
        "stdout_truncated": True,
        "stdout_limit_bytes": max_bytes,
    }


def compact_cli_result(
    result: dict[str, Any],
    *,
    output_path: Path | None = None,
    max_bytes: int | None = None,
) -> dict[str, Any]:
    """Return a sparse CLI result while keeping full derivations in --output."""
    autocheck = result.get("autocheck") if isinstance(result.get("autocheck"), dict) else {}
    inventory = result.get("prelint_inventory") if isinstance(result.get("prelint_inventory"), dict) else {}
    hard_blockers = _compact_inventory_groups(result.get("hard_blockers", []))
    review_gate = _compact_inventory_groups(inventory.get("review_gate", []))
    compact = {
        key: result.get(key)
        for key in (
            "status", "mode", "stopped_at", "diagnostic_stage", "terminal",
            "continue_required", "workflow_disposition", "next_action",
            "episode_video_id", "preview_status",
            "prelint_clean", "semantic_sha256", "prepared_input_semantic_sha256",
            "composed_reviews_semantic_sha256", "autocheck_semantic_sha256", "metrics",
            "authoring_manifest_semantic_sha256", "authoring_decisions_semantic_sha256",
            "authoring_manifest_explicit",
            "preview_receipt", "packet", "next_gate", "idempotent",
        )
        if result.get(key) is not None
    }
    compact["candidate_count"] = result.get("metrics", {}).get("candidate_count", autocheck.get("candidate_count"))
    compact["review_count"] = result.get("metrics", {}).get("final_review_count", autocheck.get("reviewed_chunks"))
    compact["hard_blockers"] = hard_blockers
    compact["review_gate"] = review_gate
    compact["compiler_issues"] = _compact_inventory_groups([
        {"category": "compiler", "kind": "hard_blocker", "items": result.get("issues", [])}
    ]) if result.get("issues") else []
    compact["audit_warnings"] = _compact_inventory_groups(result.get("audit_warnings", []))
    compact["evidence_scope_warnings"] = _compact_inventory_groups([
        {"category": "evidence_scope", "kind": "audit_warning", "items": inventory.get("evidence_scope_warnings", [])}
    ]) if inventory.get("evidence_scope_warnings") else []
    compact["calibration"] = _compact_calibration(
        autocheck.get("calibration") or result.get("recall_view", {}).get("calibration")
    )
    compact["inventory_counts"] = {
        key: len(value)
        for key, value in (result.get("recall_view", {}).get("inventories", {}) or {}).items()
        if isinstance(value, list) and value
    }
    compact["pending_acknowledgements"] = _pending_risk_acknowledgements([
        *result.get("hard_blockers", []),
        *inventory.get("review_gate", []),
    ])
    adversarial_view = result.get("adversarial_authoring_view")
    if isinstance(adversarial_view, dict):
        compact["adversarial_authoring_view"] = {
            "semantic_sha256": adversarial_view.get("semantic_sha256"),
            "input_semantic_sha256": adversarial_view.get("input_semantic_sha256"),
            "required_categories": adversarial_view.get("required_categories", []),
            "source_block_count": len(adversarial_view.get("source_blocks", [])),
            "candidate_binding_count": len(adversarial_view.get("candidate_bindings", [])),
            "numeric_candidate_count": len(adversarial_view.get("numeric_occurrence_matrix", [])),
            "calibration_binding_count": len(adversarial_view.get("calibration_bindings", [])),
        }
    repair_manifest = inventory.get("repair_manifest")
    if isinstance(repair_manifest, dict):
        compact["repair_manifest"] = {
            "counts": repair_manifest.get("counts", {}),
            "semantic_sha256": repair_manifest.get("semantic_sha256"),
        }
    if output_path is not None:
        compact["full_report"] = str(output_path)
    finalization = result.get("finalization")
    if isinstance(finalization, dict):
        compact["finalization"] = {
            key: finalization.get(key)
            for key in ("status", "next_gate", "revision_id", "packet", "idempotent")
            if key in finalization
        } | {
            "audit_warning_count": len(finalization.get("audit_warnings", [])),
            "hard_blocker_count": len(finalization.get("hard_blockers", [])),
            "readiness_status": finalization.get("readiness", {}).get("status") if isinstance(finalization.get("readiness"), dict) else None,
            "build_status": finalization.get("build", {}).get("status") if isinstance(finalization.get("build"), dict) else None,
            "validation_status": finalization.get("validation", {}).get("status") if isinstance(finalization.get("validation"), dict) else None,
        }
    return _fit_cli_output(compact, max_bytes) if max_bytes else compact


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id")
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--input", help="Complete episode review payload JSON.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--start-episode", action="store_true", help="Certify WSL, select, prepare, and emit context in one runtime process.")
    mode.add_argument("--select-next", action="store_true", help="Select and bootstrap one source-complete unprepared episode in a single call.")
    mode.add_argument("--bootstrap-request", type=Path, help="Run the certified preflight from one JSON request file.")
    mode.add_argument("--context", action="store_true", help="Emit the complete transcript in two or three chronological reading slabs.")
    mode.add_argument("--prelint", action="store_true", help="Return the complete in-memory payload inventory without creating a preview receipt.")
    mode.add_argument("--dry-run", action="store_true", help="Alias for the consolidated pure prelint; never writes a preview receipt or gold state.")
    mode.add_argument("--check", action="store_true", help="Recovery/debug route: compile, autocheck, and write only a job-local clean-preview receipt.")
    mode.add_argument("--apply", action="store_true", help="Recovery/debug route: apply only the exact payload approved by the supplied preview receipt.")
    mode.add_argument("--one-shot", action="store_true", help="Default clean route: create the preview receipt, persist once, finalize, and emit the audit dossier in one process.")
    mode.add_argument("--remediate", action="store_true", help="Post-audit route: transactionally patch complete reviews, re-finalize, and emit a fresh dossier without the initial recorder.")
    mode.add_argument("--audit-scaffold", action="store_true", help="Resolve a final audit into a source-canonical, read-only remediation scaffold.")
    mode.add_argument("--resume-audit", action="store_true", help="Resume only the sealed Sol audit after an interruption; never rebuild extraction or dossier.")
    mode.add_argument("--phase-start", choices=sorted(SEMANTIC_PHASES), help="Open one explicit semantic-work span in the episode session.")
    mode.add_argument("--phase-end", choices=sorted(SEMANTIC_PHASES), help="Close one explicit semantic-work span in the episode session.")
    mode.add_argument("--phase-interrupt", choices=sorted(SEMANTIC_PHASES), help="Close an interrupted semantic span without counting it as active model work.")
    parser.add_argument("--patch", type=Path, help="Declarative post-audit remediation manifest for --remediate.")
    parser.add_argument("--authoring-manifest", type=Path, help="Authoritative gold_authoring_manifest_v1 for initial or post-audit processing.")
    parser.add_argument("--audit-input", type=Path, help="Final audit JSON used by --audit-scaffold or materialized before --remediate.")
    parser.add_argument("--revision-id", default="initial-finalization")
    parser.add_argument("--export-suffix")
    parser.add_argument("--executor-thread-id")
    parser.add_argument("--job-dir", type=Path, help="Transient job directory native to the selected runtime.")
    parser.add_argument("--mirror-job-dir", type=Path, help="Optional final-artifact mirror outside the runtime job directory.")
    parser.add_argument("--preview-receipt", type=Path)
    parser.add_argument("--audit-bundle", type=Path)
    parser.add_argument("--output", type=Path, help="Write the full structured result to a Linux-native JSON file.")
    parser.add_argument("--slabs", type=int, default=3)
    parser.add_argument("--full-output", action="store_true", help="Include the full autocheck report instead of the sparse recall view.")
    parser.add_argument("--runtime-parity-receipt", type=Path)
    parser.add_argument("--runtime-manifest", type=Path)
    parser.add_argument("--selection-id", default="gold-runtime")
    parser.add_argument("--export-prefix", default="msf_r20_gold_runtime")
    parser.add_argument("--minimum-segments", type=int, default=600)
    parser.add_argument("--maximum-segments", type=int, default=1200)
    parser.add_argument("--target-segments", type=int, default=950)
    parser.add_argument("--exclude-video-id", action="append", default=[])
    parser.add_argument("--priority-queue", type=Path, help="Use a durable pre-ranked episode queue instead of rescanning all episodes.")
    parser.add_argument("--explicit-reprocess", action="store_true", help="Allow a source-changed terminal ID to start a new run.")
    parser.add_argument("--reprocess-reason", help="Required source-backed reason for --explicit-reprocess.")
    parser.add_argument("--epic-started-at", help="UTC timestamp captured by the outer launcher before runtime sync.")
    args = parser.parse_args()
    _validate_job_dir(args.job_dir)
    if args.runtime_parity_receipt or args.runtime_manifest:
        if not args.runtime_parity_receipt or not args.runtime_manifest:
            parser.error("runtime parity requires both --runtime-parity-receipt and --runtime-manifest")
        _active_receipt, parity_errors = _validate_or_pin_runtime_snapshot(
            args.job_dir,
            args.runtime_parity_receipt,
            args.runtime_manifest,
            Path(__file__).resolve().parents[1],
        )
        if parity_errors:
            print(json.dumps({"status": "blocked", "stopped_at": "runtime_parity", "errors": parity_errors}))
            return 1
    if args.start_episode or args.select_next:
        if args.data_root is None or args.job_dir is None:
            parser.error("--start-episode/--select-next requires --data-root and --job-dir")
        if args.minimum_segments < 1 or args.maximum_segments < args.minimum_segments:
            parser.error("selection segment limits are invalid")
        selector = start_episode if args.start_episode else select_and_bootstrap_episode
        result = selector(
            args.data_root,
            args.job_dir,
            selection_id=args.selection_id,
            export_prefix=args.export_prefix,
            minimum_segments=args.minimum_segments,
            maximum_segments=args.maximum_segments,
            target_segments=args.target_segments,
            excluded_video_ids=set(args.exclude_video_id),
            epic_started_at=args.epic_started_at,
            priority_queue=args.priority_queue,
            explicit_reprocess=args.explicit_reprocess,
            explicit_reprocess_reason=args.reprocess_reason,
        )
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            write_json(args.output, result)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result.get("status") == "ready" else 1
    if args.phase_start or args.phase_end or args.phase_interrupt:
        if not args.video_id or args.job_dir is None:
            parser.error("semantic phase control requires --video-id and --job-dir")
        phase = args.phase_start or args.phase_end or args.phase_interrupt
        action = "start" if args.phase_start else "end" if args.phase_end else "interrupt"
        result = {"status": "ok", "action": action, "span": mark_semantic_phase(args.job_dir, args.video_id, phase, action)}
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.resume_audit:
        if not args.video_id or args.job_dir is None:
            parser.error("--resume-audit requires --video-id and --job-dir")
        result = resume_audit_request(args.job_dir, args.video_id)
        if result.get("state") == "restart_final_model_only":
            phase = "final_sol_reaudit" if result.get("request", {}).get("phase") == "reaudit" else "final_sol_audit"
            interrupt_semantic_phase_if_open(args.job_dir, args.video_id, phase)
            start_semantic_phase_if_absent(args.job_dir, args.video_id, phase)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result.get("status") == "ready" else 1
    if args.bootstrap_request:
        request = load_json(args.bootstrap_request)
        request_data_root = Path(request.get("data_root") or os.environ.get("MSF_DATA_DIR", ""))
        if _is_wsl() and "/msf-data/Marketing_Swipe_File" in str(request_data_root.resolve()).replace("\\", "/") and not args.runtime_parity_receipt:
            print(json.dumps({"status": "blocked", "stopped_at": "runtime_parity", "errors": ["real WSL gold execution requires a runtime parity receipt"]}))
            return 1
        result = bootstrap_episode(request)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result.get("status") == "ready" else 1
    if not args.video_id or args.data_root is None:
        parser.error("--video-id and --data-root are required outside --bootstrap-request")
    if not args.runtime_parity_receipt and _is_wsl() and "/msf-data/Marketing_Swipe_File" in str(args.data_root.resolve()).replace("\\", "/"):
        print(json.dumps({"status": "blocked", "stopped_at": "runtime_parity", "errors": ["real WSL gold execution requires a runtime parity receipt"]}))
        return 1
    if args.audit_scaffold:
        if args.audit_input is None:
            parser.error("--audit-scaffold requires --audit-input")
        end_semantic_phase_if_open(args.job_dir, args.video_id, "final_sol_audit")
        start_semantic_phase_if_absent(args.job_dir, args.video_id, "remediation_authoring")
        audit_payload = load_json(args.audit_input)
        if args.job_dir is not None:
            materialize_audit_envelope(args.job_dir, args.video_id, audit_payload)
        result = generate_audit_remediation_scaffold(args.video_id, args.data_root, audit_payload)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            write_json(args.output, result)
            print(json.dumps({"status": "ok", "mode": "audit_scaffold", "output": str(args.output), "semantic_sha256": result["semantic_sha256"]}, ensure_ascii=False))
        else:
            print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.context:
        _load_or_start_session(args.job_dir, args.video_id)
        phase_started_at = _utc_now()
        started = time.perf_counter()
        result = build_reading_context(args.video_id, args.data_root, slab_count=args.slabs)
        metrics = {"context_ms": _elapsed_ms(started), "slab_count": len(result["slabs"]), "segment_count": result["segment_count"]}
        result["metrics"] = metrics
        _record_session_event(
            args.job_dir, args.video_id, "preflight_and_context", metrics,
            started_at=phase_started_at,
        )
        start_semantic_phase_if_absent(
            args.job_dir, args.video_id, "semantic_reading_and_authoring"
        )
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            write_json(args.output, result)
            print(json.dumps({
                "status": "context_ready",
                "episode_video_id": args.video_id,
                "output": str(args.output),
                "chunk_count": result["chunk_count"],
                "segment_count": result["segment_count"],
                "model_context_bytes": result["model_context_bytes"],
                "metrics": metrics,
            }, ensure_ascii=False))
        else:
            print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.remediate:
        if bool(args.patch) == bool(args.authoring_manifest):
            parser.error("--remediate requires exactly one of --authoring-manifest or legacy --patch")
        manifest = load_json(args.authoring_manifest or args.patch)
        if args.audit_input is not None:
            if args.job_dir is None:
                parser.error("--remediate --audit-input requires --job-dir")
            materialize_audit_envelope(
                args.job_dir,
                args.video_id,
                load_json(args.audit_input),
            )
        end_semantic_phase_if_open(args.job_dir, args.video_id, "remediation_authoring")
        result = run_post_audit_remediation(
            args.video_id,
            args.data_root,
            manifest,
            revision_id=args.revision_id,
            export_suffix=args.export_suffix,
            executor_thread_id=args.executor_thread_id,
            audit_bundle_path=args.audit_bundle,
            job_dir=args.job_dir,
            mirror_job_dir=args.mirror_job_dir,
        )
        if result.get("status") == "ready":
            start_semantic_phase_if_absent(
                args.job_dir, args.video_id, "final_sol_reaudit"
            )
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            write_json(args.output, result)
        output = result if args.full_output else compact_cli_result(
            result,
            output_path=args.output,
            max_bytes=CLI_OUTPUT_MAX_BYTES if args.output else None,
        )
        print(json.dumps(output, ensure_ascii=False))
        return 0 if result["status"] in {"ready", "protected"} else 1
    if bool(args.input) and bool(args.authoring_manifest):
        parser.error("use either --input or --authoring-manifest")
    authoring_input_path = args.authoring_manifest or (Path(args.input) if args.input else None)
    if authoring_input_path is None:
        parser.error("--input or --authoring-manifest is required for --dry-run, --prelint, --check, --apply, and --one-shot")
    preview_receipt = args.preview_receipt or (args.job_dir / "clean_preview_receipt.json" if args.job_dir else None)
    if preview_receipt is None and not (args.prelint or args.dry_run):
        parser.error("--preview-receipt or --job-dir is required for the enforced fast route")
    payload = load_payload(str(authoring_input_path))
    payload_bytes = len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    if args.prelint or args.dry_run:
        if not args.dry_run:
            end_semantic_phase_if_open(
                args.job_dir, args.video_id, "semantic_reading_and_authoring"
            )
            end_semantic_phase_if_open(args.job_dir, args.video_id, "prelint_repair")
        phase_started_at = _utc_now()
        result = prelint_episode_draft(args.video_id, args.data_root, payload)
        result["mode"] = "dry_run" if args.dry_run else "prelint"
        result.setdefault("metrics", {})["payload_bytes"] = payload_bytes
        result["metrics"]["full_result_bytes"] = len(
            json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )
        if not args.dry_run:
            _record_session_event(
                args.job_dir, args.video_id, "prelint", result.get("metrics", {}),
                started_at=phase_started_at,
            )
        if not args.dry_run and not result.get("prelint_clean"):
            start_semantic_phase_if_absent(
                args.job_dir, args.video_id, "prelint_repair"
            )
    elif args.check:
        end_semantic_phase_if_open(args.job_dir, args.video_id, "prelint_repair")
        phase_started_at = _utc_now()
        result = inspect_episode_draft(args.video_id, args.data_root, payload)
        if result.get("status") == "ready_to_apply":
            preview_receipt.parent.mkdir(parents=True, exist_ok=True)
            write_json(
                preview_receipt,
                make_preview_receipt(result, revision_id=args.revision_id, export_suffix=args.export_suffix),
            )
            result["preview_receipt"] = str(preview_receipt)
        _record_session_event(
            args.job_dir, args.video_id, "preview", result.get("metrics", {}),
            started_at=phase_started_at,
        )
    else:
        end_semantic_phase_if_open(args.job_dir, args.video_id, "prelint_repair")
        result = run_episode(
            args.video_id,
            args.data_root,
            payload,
            apply=True,
            revision_id=args.revision_id,
            export_suffix=args.export_suffix,
            executor_thread_id=args.executor_thread_id,
            preview_receipt_path=preview_receipt,
            create_preview_receipt=args.one_shot,
            audit_bundle_path=args.audit_bundle,
            job_dir=args.job_dir,
            mirror_job_dir=args.mirror_job_dir,
        )
        if result.get("status") in {"ready", "protected"}:
            end_semantic_phase_if_open(
                args.job_dir, args.video_id, "semantic_reading_and_authoring"
            )
        # The final Sol span starts only when the dedicated auditor actually begins.
        # Starting it at packet readiness contaminates per-episode timing in waves.
    result.setdefault("metrics", {}).setdefault("payload_bytes", payload_bytes)
    result["metrics"]["full_result_bytes"] = len(
        json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )
    output = result if args.full_output else compact_cli_result(
        result,
        output_path=args.output,
        max_bytes=CLI_OUTPUT_MAX_BYTES if args.output else None,
    )
    result.setdefault("metrics", {})["cli_output_bytes"] = len(
        json.dumps(output, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_json(args.output, result)
    print(json.dumps(output, ensure_ascii=False))
    successful_statuses = {"prelint_clean", "ready_to_apply", "ready", "protected"}
    return 0 if result["status"] in successful_statuses or result.get("continue_required") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
