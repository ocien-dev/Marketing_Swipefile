#!/usr/bin/env python
"""Register one accepted final audit and complete the episode in one process."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.build_gold_semantic_extraction import build_from_reviews
from scripts.export_gold_audit_packet import PACKET_OUTPUT_FILES
from scripts.gold_extraction_common import (
    external_audit_gate,
    ledger_errors,
    load_json,
    json_hashes,
    record_operation_event,
    sha256_semantic_json,
    transcript_source_paths,
    validate_document,
    write_json,
)
from scripts.record_gold_external_audit import record_audit
from scripts.gold_audit_lifecycle import materialize_audit_envelope
from scripts.gold_episode_priority import advance_queue_state
from scripts.gold_terminal_identity import register_terminal_completion
from scripts.run_gold_episode_fast import (
    SESSION_IDLE_THRESHOLD_MS,
    _record_session_event,
    _validate_or_pin_runtime_snapshot,
    end_semantic_phase_if_open,
    start_semantic_phase_if_absent,
)


def _is_wsl() -> bool:
    release = platform.release().lower()
    return "microsoft" in release or "wsl" in release


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _elapsed_between(started_at: str | None, ended_at: str | None = None) -> float | None:
    if not started_at:
        return None
    try:
        started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        ended = datetime.fromisoformat((ended_at or _utc_now()).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return round(max(0.0, (ended - started).total_seconds() * 1000), 2)


def _session_performance(session: dict[str, Any], elapsed_ms: float | None) -> dict[str, Any]:
    phase_wall_ms: dict[str, float] = {}
    deterministic_command_ms = 0.0
    active_wall_ms = 0.0
    model_judgment_ms = 0.0
    inter_turn_idle_ms = 0.0
    recorded_unattributed_gap_ms = 0.0
    phase_transition_ms = 0.0
    semantic_phase_wall_ms: dict[str, float] = {}
    interrupted_semantic_span_count = 0
    interrupted_semantic_wall_ms = 0.0
    artifact_bytes = {
        "context": 0,
        "payload": 0,
        "prelint_report": 0,
        "audit_dossier": 0,
    }
    for event in session.get("events", []):
        if not isinstance(event, dict):
            continue
        phase = str(event.get("phase", "unknown"))
        metrics = event.get("metrics", {}) if isinstance(event.get("metrics"), dict) else {}
        command_ms = event.get("runtime_command_ms")
        if command_ms is None:
            command_ms = metrics.get("total_ms")
        if command_ms is None:
            command_ms = metrics.get("context_ms") or metrics.get("check_ms") or metrics.get("selection_ms") or 0.0
        command_ms = float(command_ms or 0.0)
        if event.get("active_wall_ms") is not None:
            active = float(event.get("active_wall_ms") or 0.0)
            idle = float(event.get("inter_turn_idle_ms") or 0.0)
            unattributed = float(event.get("unattributed_gap_ms") or 0.0)
            transition = float(event.get("phase_transition_ms") or 0.0)
            judgment = float(event.get("model_judgment_ms") or max(0.0, active - command_ms))
        else:
            legacy_delta = float(event.get("elapsed_since_previous_event_ms") or 0.0)
            active = command_ms
            gap = max(0.0, legacy_delta - active)
            idle = 0.0
            unattributed = gap if gap >= SESSION_IDLE_THRESHOLD_MS else 0.0
            transition = gap if gap < SESSION_IDLE_THRESHOLD_MS else 0.0
            judgment = 0.0
        phase_wall_ms[phase] = round(phase_wall_ms.get(phase, 0.0) + active, 2)
        active_wall_ms += active
        model_judgment_ms += judgment
        inter_turn_idle_ms += idle
        recorded_unattributed_gap_ms += unattributed
        phase_transition_ms += transition
        deterministic_command_ms += float(command_ms or 0.0)
        artifact_bytes["context"] = max(artifact_bytes["context"], int(metrics.get("context_bytes") or 0))
        artifact_bytes["payload"] = max(artifact_bytes["payload"], int(metrics.get("payload_bytes") or 0))
        artifact_bytes["prelint_report"] = max(artifact_bytes["prelint_report"], int(metrics.get("full_result_bytes") or 0))
        artifact_bytes["audit_dossier"] = max(artifact_bytes["audit_dossier"], int(metrics.get("audit_dossier_bytes") or 0))
    deterministic_command_ms = round(deterministic_command_ms, 2)
    measured_elapsed = float(elapsed_ms or 0.0)
    active_wall_ms = round(active_wall_ms, 2)
    model_judgment_ms = round(model_judgment_ms, 2)
    inter_turn_idle_ms = round(inter_turn_idle_ms, 2)
    recorded_unattributed_gap_ms = round(recorded_unattributed_gap_ms, 2)
    phase_transition_ms = round(phase_transition_ms, 2)
    for span in session.get("semantic_spans", []):
        if not isinstance(span, dict) or span.get("elapsed_ms") is None:
            continue
        if span.get("state") == "interrupted":
            interrupted_semantic_span_count += 1
            interrupted_semantic_wall_ms += float(span.get("elapsed_ms") or 0.0)
            continue
        phase = str(span.get("phase", "unknown"))
        semantic_phase_wall_ms[phase] = round(
            semantic_phase_wall_ms.get(phase, 0.0) + float(span.get("elapsed_ms") or 0.0), 2
        )
    semantic_wall_ms = round(sum(semantic_phase_wall_ms.values()), 2)
    classified_gap_ms = recorded_unattributed_gap_ms + phase_transition_ms
    total_gap_ms = max(0.0, measured_elapsed - active_wall_ms)
    semantic_in_gap_ms = min(semantic_wall_ms, total_gap_ms)
    semantic_overlap_ms = round(max(0.0, semantic_wall_ms - semantic_in_gap_ms), 2)
    unclassified_gap_ms = round(max(0.0, total_gap_ms - semantic_in_gap_ms), 2)
    unattributed_wall_ms = round(
        recorded_unattributed_gap_ms
        + max(0.0, unclassified_gap_ms - classified_gap_ms),
        2,
    )
    reconciled_wall_ms = round(active_wall_ms + semantic_in_gap_ms + unclassified_gap_ms, 2)
    return {
        "phase_wall_ms": dict(sorted(phase_wall_ms.items())),
        "active_wall_ms": active_wall_ms,
        "deterministic_command_ms": deterministic_command_ms,
        "runtime_command_ms": deterministic_command_ms,
        "model_judgment_ms": model_judgment_ms,
        "judgment_and_orchestration_ms": model_judgment_ms,
        "inter_turn_idle_ms": inter_turn_idle_ms,
        "unattributed_gap_ms": unattributed_wall_ms,
        "phase_transition_ms": phase_transition_ms,
        "semantic_phase_wall_ms": dict(sorted(semantic_phase_wall_ms.items())),
        "semantic_wall_ms": semantic_wall_ms,
        "semantic_in_gap_ms": semantic_in_gap_ms,
        "semantic_overlap_ms": semantic_overlap_ms,
        "interrupted_semantic_span_count": interrupted_semantic_span_count,
        "interrupted_semantic_wall_ms": round(interrupted_semantic_wall_ms, 2),
        "unclassified_gap_ms": unclassified_gap_ms,
        "unattributed_wall_ms": unattributed_wall_ms,
        "reconciled_wall_ms": reconciled_wall_ms,
        "wall_reconciliation_delta_ms": round(measured_elapsed - reconciled_wall_ms, 2),
        "artifact_bytes": artifact_bytes,
        "event_count": len(session.get("events", [])),
    }


def _epic_timing(job_dir: Path | None) -> dict[str, Any]:
    if job_dir is None or not (job_dir / "episode_fast_session.json").exists():
        return {}
    session = load_json(job_dir / "episode_fast_session.json")
    started_at = session.get("epic_started_at") or session.get("started_at")
    completed_at = _utc_now()
    elapsed_ms = _elapsed_between(started_at, completed_at)
    return {
        "run_id": session.get("run_id"),
        "started_at": started_at,
        "completed_at": completed_at,
        "elapsed_ms": elapsed_ms,
        "start_boundary": "outer_launcher_before_runtime_sync" if any(item.get("phase") == "selection" for item in session.get("events", [])) else "first_certified_episode_process",
        "end_boundary": "completion_artifacts_generated",
        "events": session.get("events", []),
        "operation_counts": session.get("operation_counts", {}),
        "performance": _session_performance(session, elapsed_ms),
    }


def performance_budget(segment_count: int) -> dict[str, Any]:
    """Return the operational SLA band used for episode-level retrospectives."""
    if segment_count <= 700:
        return {"band": "small", "segment_count": segment_count, "target_minutes": [6, 10]}
    if segment_count <= 1300:
        return {"band": "standard", "segment_count": segment_count, "target_minutes": [11, 15]}
    return {"band": "long", "segment_count": segment_count, "target_minutes": [18, 30]}


def _required_audit_validation(video_id: str, data_root: Path) -> dict[str, Any]:
    out = data_root / "processed" / video_id / "gold_extraction"
    document = load_json(out / "insights_exhaustive.json")
    transcript = load_json(out / "transcript_clean.json")["segments"]
    chunks = load_json(out / "chunks" / "chunk_index.json")["chunks"]
    ledger = load_json(out / "high_signal_coverage_ledger.json")["entries"]
    errors = validate_document(document, transcript, chunks, require_external_audit=True)
    errors.extend(
        ledger_errors(
            ledger,
            {item["candidate_id"] for item in document["insights"]},
            {item["segment_id"] for item in ledger},
        )
    )
    gate = external_audit_gate(out, load_json(out / "gold_extraction_status.json").get("executor_thread_id"))
    if not gate["eligible_for_complete"]:
        errors.extend(gate["errors"] or ["external audit has not passed"])
    errors = sorted(set(errors))
    return {"status": "pass" if not errors else "fail", "errors": errors}


def build_completion_receipt(
    video_id: str,
    data_root: Path,
    *,
    export_suffix: str,
    metrics: dict[str, Any] | None = None,
    job_dir: Path | None = None,
) -> dict[str, Any]:
    out = data_root / "processed" / video_id / "gold_extraction"
    packet = data_root / "exports" / export_suffix
    status = load_json(out / "gold_extraction_status.json")
    audit = load_json(out / "editorial_audit_report.json")
    document = load_json(out / "insights_exhaustive.json")
    calibration = load_json(out / "calibration_tests.json")
    fingerprints = load_json(out / "protected_fingerprints.json")
    packet_paths = sorted(path for path in packet.iterdir() if path.is_file()) if packet.is_dir() else []
    packet_files = [{"name": path.name, **json_hashes(path)} for path in packet_paths]
    source_paths = [
        data_root / "raw" / "youtube" / video_id / "metadata.json",
        *transcript_source_paths(data_root, video_id),
        data_root / "processed" / video_id / "content_segments.json",
    ]
    candidate_ids = [item.get("candidate_id") for item in document.get("insights", [])]
    packet_manifest = load_json(packet / "packet_manifest.json") if (packet / "packet_manifest.json").exists() else {}
    transcript_segments = load_json(out / "transcript_clean.json").get("segments", [])
    core = {
        "schema_version": "1.1.0",
        "kind": "gold_episode_completion",
        "episode_video_id": video_id,
        "status": status.get("status"),
        "audit_status": status.get("audit_status"),
        "open_audit_findings": status.get("open_audit_findings"),
        "audit": {
            "status": audit.get("status"),
            "open_findings": audit.get("open_findings"),
            "reviewer_model": audit.get("reviewer_model"),
            "reasoning_effort": audit.get("reasoning_effort"),
            "audit_route": audit.get("audit_route"),
            "semantic_sha256": sha256_semantic_json(audit),
        },
        "candidates": {
            "count": len(candidate_ids),
            "unique": len(candidate_ids) == len(set(candidate_ids)),
            "semantic_sha256": sha256_semantic_json(document),
        },
        "calibration": {
            "status": calibration.get("status"),
            "covered_count": calibration.get("covered_count"),
            "minimum_required": calibration.get("minimum_required"),
            "duplicate_target_segments": calibration.get("duplicate_target_segments", []),
            "semantic_sha256": sha256_semantic_json(calibration),
        },
        "packet": {
            "path": str(packet),
            "names": [item["name"] for item in packet_files],
            "files": packet_files,
            "manifest_episode_video_id": packet_manifest.get("episode_video_id"),
        },
        "protected_fingerprints": fingerprints,
        "source_files": [{"path": str(path), **json_hashes(path)} for path in source_paths if path.exists()],
        "validation": _required_audit_validation(video_id, data_root),
        "metrics": metrics or {},
        "epic_timing": _epic_timing(job_dir),
        "performance_budget": performance_budget(len(transcript_segments)),
        "terminal_authority": {
            "terminal": True,
            "additional_verify_required": False,
            "next_action": "stop",
        },
    }
    return {**core, "receipt_semantic_sha256": sha256_semantic_json(core)}


def validate_completion_receipt(receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    core = {key: value for key, value in receipt.items() if key != "receipt_semantic_sha256"}
    if receipt.get("receipt_semantic_sha256") != sha256_semantic_json(core):
        errors.append("completion receipt semantic hash is invalid")
    if receipt.get("status") != "complete" or receipt.get("audit_status") != "passed" or receipt.get("open_audit_findings") not in {0, None}:
        errors.append("completion lifecycle is not complete/passed/zero")
    if receipt.get("audit", {}).get("status") != "passed" or receipt.get("audit", {}).get("open_findings") != 0:
        errors.append("accepted audit is not passed with zero findings")
    if not receipt.get("candidates", {}).get("unique"):
        errors.append("candidate ids are not unique")
    calibration = receipt.get("calibration", {})
    if calibration.get("status") != "pass" or calibration.get("duplicate_target_segments"):
        errors.append("calibration is not passing and distinct")
    packet = receipt.get("packet", {})
    if set(packet.get("names", [])) != PACKET_OUTPUT_FILES or len(packet.get("files", [])) != 5:
        errors.append("completion packet does not contain exactly five files")
    if packet.get("manifest_episode_video_id") != receipt.get("episode_video_id"):
        errors.append("completion packet episode identity mismatch")
    fingerprints = receipt.get("protected_fingerprints", {})
    if fingerprints.get("before") != fingerprints.get("after"):
        errors.append("protected fingerprints changed")
    if receipt.get("validation", {}).get("errors"):
        errors.append("required external-audit validation failed")
    terminal = receipt.get("terminal_authority", {})
    if receipt.get("schema_version") == "1.1.0" and terminal != {"terminal": True, "additional_verify_required": False, "next_action": "stop"}:
        errors.append("completion receipt is not terminal authority")
    return errors


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)


def _atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_bytes(source.read_bytes())
    temporary.replace(destination)


def write_nonterminal_audit_state(
    job_dir: Path,
    video_id: str,
    checked_audit: dict[str, Any],
    *,
    audit_envelope: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist an internal audit transition without producing closeout files."""
    findings = checked_audit.get("findings", [])
    core = {
        "schema_version": "1.0.0",
        "kind": "gold_episode_audit_state",
        "episode_video_id": video_id,
        "state": "remediation_required",
        "terminal": False,
        "audit_status": checked_audit.get("status"),
        "open_findings": checked_audit.get("open_findings"),
        "finding_ids": [item.get("finding_id") for item in findings],
        "audit_request_semantic_sha256": (audit_envelope or {}).get("request_semantic_sha256"),
        "audit_envelope_semantic_sha256": (audit_envelope or {}).get("semantic_sha256"),
        "next_action": "apply source-backed remediation, rebuild dossier, and reaudit",
        "recorded_at": _utc_now(),
    }
    state = {**core, "semantic_sha256": sha256_semantic_json(core)}
    write_json(job_dir / "episode_audit_state.json", state)
    return state


def write_completion_artifacts(
    job_dir: Path,
    receipt: dict[str, Any],
    *,
    mirror_job_dir: Path | None = None,
) -> dict[str, Any]:
    generation_started = time.perf_counter()
    receipt = dict(receipt)
    timing = dict(receipt.get("epic_timing") or {})
    generated_at = _utc_now()
    timing["completed_at"] = generated_at
    timing["final_response_generated_at"] = generated_at
    timing["elapsed_ms"] = _elapsed_between(timing.get("started_at"), generated_at)
    receipt["epic_timing"] = timing
    receipt["metrics"] = {
        **dict(receipt.get("metrics") or {}),
        "closeout_artifact_generation_ms": round((time.perf_counter() - generation_started) * 1000, 2),
    }
    core = {key: value for key, value in receipt.items() if key != "receipt_semantic_sha256"}
    receipt["receipt_semantic_sha256"] = sha256_semantic_json(core)
    errors = validate_completion_receipt(receipt)
    if errors:
        raise ValueError("; ".join(errors))
    receipt_path = job_dir / "episode_completion_receipt.json"
    summary_path = job_dir / "completion_summary.md"
    performance_path = job_dir / "episode_performance_report.json"
    response_path = job_dir / "final_response.md"
    retrospective_path = job_dir / "runtime_retrospective.md"
    lines = [
        "# Gold episode completion",
        "",
        f"- episode: `{receipt['episode_video_id']}`",
        f"- lifecycle: `{receipt['status']}/{receipt['audit_status']}`",
        f"- candidates: {receipt['candidates']['count']} unique",
        f"- calibration: {receipt['calibration']['covered_count']}/{receipt['calibration']['minimum_required']} ({receipt['calibration']['status']})",
        f"- packet: 5 files at `{receipt['packet']['path']}`",
        f"- fingerprints: {'preserved' if receipt['protected_fingerprints'].get('before') == receipt['protected_fingerprints'].get('after') else 'changed'}",
        f"- receipt: `{receipt['receipt_semantic_sha256']}`",
        f"- epic elapsed: {receipt.get('epic_timing', {}).get('elapsed_ms')} ms",
        f"- performance budget: {receipt['performance_budget']['band']} {receipt['performance_budget']['target_minutes']} min",
        "- terminal receipt: no additional verify/sync step is required",
        "",
    ]
    final_response = [
        "# EPIC COMPLETED - PROJECT CONTINUES",
        "",
        f"Episode `{receipt['episode_video_id']}` completed with {receipt['candidates']['count']} unique candidates.",
        f"Calibration passed at {receipt['calibration']['covered_count']}/{receipt['calibration']['minimum_required']}.",
        "The final audit passed with zero open findings; the five-file packet and protected fingerprints were verified.",
        f"Measured epic time through generated closeout: {receipt.get('epic_timing', {}).get('elapsed_ms')} ms.",
        "This receipt is terminal; no additional verification or synchronization command is required.",
        "",
    ]
    performance = {
        "schema_version": "1.0.0",
        "kind": "gold_episode_performance",
        "episode_video_id": receipt["episode_video_id"],
        "epic_timing": receipt.get("epic_timing", {}),
        "command_metrics": receipt.get("metrics", {}),
        "operation_counts": receipt.get("epic_timing", {}).get("operation_counts", {}),
        "receipt_semantic_sha256": receipt["receipt_semantic_sha256"],
        "performance_budget": receipt.get("performance_budget", {}),
    }
    runtime_performance = receipt.get("epic_timing", {}).get("performance", {})
    retrospective = [
        "# Gold runtime retrospective",
        "",
        f"- episode: `{receipt['episode_video_id']}`",
        f"- run_id: `{receipt.get('epic_timing', {}).get('run_id')}`",
        f"- total wall: {receipt.get('epic_timing', {}).get('elapsed_ms')} ms",
        f"- active wall: {runtime_performance.get('active_wall_ms', 0)} ms",
        f"- deterministic commands: {runtime_performance.get('deterministic_command_ms', 0)} ms",
        f"- model judgment: {runtime_performance.get('model_judgment_ms', 0)} ms",
        f"- semantic wall: {runtime_performance.get('semantic_wall_ms', 0)} ms",
        f"- unattributed gaps: {runtime_performance.get('unattributed_wall_ms', 0)} ms",
        f"- phase transitions: {runtime_performance.get('phase_transition_ms', 0)} ms",
        "",
        "## Phase wall time",
        "",
        *[
            f"- {phase}: {elapsed} ms"
            for phase, elapsed in runtime_performance.get("phase_wall_ms", {}).items()
        ],
        "",
        "## Semantic spans",
        "",
        *[
            f"- {phase}: {elapsed} ms"
            for phase, elapsed in runtime_performance.get("semantic_phase_wall_ms", {}).items()
        ],
        "",
        "## Artifact bytes",
        "",
        *[
            f"- {name}: {size}"
            for name, size in runtime_performance.get("artifact_bytes", {}).items()
        ],
        "",
    ]
    write_json(receipt_path, receipt)
    write_json(performance_path, performance)
    _atomic_write_text(summary_path, "\n".join(lines))
    _atomic_write_text(response_path, "\n".join(final_response))
    _atomic_write_text(retrospective_path, "\n".join(retrospective))
    artifacts: dict[str, Any] = {
        "receipt": str(receipt_path),
        "summary": str(summary_path),
        "performance_report": str(performance_path),
        "final_response": str(response_path),
        "runtime_retrospective": str(retrospective_path),
    }
    if mirror_job_dir is not None and mirror_job_dir.resolve(strict=False) != job_dir.resolve(strict=False):
        mirrored: dict[str, str] = {}
        for source in (receipt_path, summary_path, performance_path, response_path, retrospective_path, job_dir / "episode_fast_session.json"):
            if not source.exists():
                continue
            destination = mirror_job_dir / source.name
            _atomic_copy(source, destination)
            mirrored[source.name] = str(destination)
        artifacts["mirror"] = mirrored
    return artifacts


def complete_episode(
    video_id: str,
    data_root: Path,
    audit_payload: dict[str, Any],
    *,
    executor_thread_id: str | None,
    export_suffix: str,
    job_dir: Path | None = None,
    mirror_job_dir: Path | None = None,
) -> dict[str, Any]:
    out = data_root / "processed" / video_id / "gold_extraction"
    status = load_json(out / "gold_extraction_status.json")
    audit_envelope = None
    if job_dir is not None and not (
        status.get("status") == "complete" and status.get("audit_status") == "passed"
    ):
        # Validate first, then make the model response durable before touching
        # lifecycle, telemetry, build, or episode audit state.
        record_audit(video_id, data_root, audit_payload, persist=False)
        audit_envelope = materialize_audit_envelope(
            job_dir,
            video_id,
            audit_payload,
        )
        audit_payload = audit_envelope["audit_payload"]
    end_semantic_phase_if_open(job_dir, video_id, "final_sol_audit")
    end_semantic_phase_if_open(job_dir, video_id, "final_sol_reaudit")
    phase_started_at = _utc_now()
    started = time.perf_counter()
    if status.get("status") == "complete" and status.get("audit_status") == "passed":
        result = {
            "status": "protected",
            "next_gate": "none",
            "episode_video_id": video_id,
            "terminal_receipt": True,
            "additional_verify_required": False,
        }
        if job_dir is not None:
            receipt = build_completion_receipt(video_id, data_root, export_suffix=export_suffix, metrics={"idempotent": True}, job_dir=job_dir)
            result["completion_artifacts"] = write_completion_artifacts(job_dir, receipt, mirror_job_dir=mirror_job_dir)
            terminal_receipt_path = Path(result["completion_artifacts"]["receipt"])
            result["terminal_identity"] = register_terminal_completion(
                data_root,
                video_id,
                load_json(terminal_receipt_path),
                completion_receipt_path=terminal_receipt_path,
            )
        return result
    checked = record_audit(video_id, data_root, audit_payload, persist=False)
    if checked.get("status") != "passed" or checked.get("open_findings") != 0:
        audit_state = None
        if checked.get("status") == "changes_requested" and int(checked.get("open_findings") or 0) > 0:
            if job_dir is not None:
                audit_state = write_nonterminal_audit_state(
                    job_dir,
                    video_id,
                    checked,
                    audit_envelope=audit_envelope,
                )
            _record_session_event(
                job_dir, video_id, "final_audit",
                {
                    "total_ms": round((time.perf_counter() - started) * 1000, 2),
                    "audits": 1,
                    "open_findings": int(checked.get("open_findings") or 0),
                },
                started_at=phase_started_at,
            )
            start_semantic_phase_if_absent(
                job_dir, video_id, "remediation_authoring"
            )
            return {
                "status": "remediation_required",
                "next_gate": "post_audit_remediation",
                "episode_video_id": video_id,
                "audit": {
                    "status": checked.get("status"),
                    "open_findings": checked.get("open_findings"),
                    "finding_ids": [item.get("finding_id") for item in checked.get("findings", [])],
                },
                "audit_state": audit_state,
                "audit_envelope": {
                    "semantic_sha256": audit_envelope.get("semantic_sha256"),
                    "request_semantic_sha256": audit_envelope.get("request_semantic_sha256"),
                } if audit_envelope else None,
                "terminal_receipt": False,
                "additional_verify_required": False,
            }
        _record_session_event(
            job_dir, video_id, "final_audit",
            {"total_ms": round((time.perf_counter() - started) * 1000, 2), "audits": 1},
            started_at=phase_started_at,
        )
        return {
            "status": "blocked",
            "stopped_at": "audit",
            "error": "post-audit completion requires a passed audit with zero open findings",
        }
    audit_path = out / "editorial_audit_report.json"
    audit_written = True
    if audit_path.exists() and sha256_semantic_json(load_json(audit_path)) == sha256_semantic_json(checked):
        audit_written = False
    else:
        record_audit(video_id, data_root, audit_payload, persist=True)
    build = build_from_reviews(
        video_id,
        data_root,
        out / "manual_reviews",
        executor_thread_id=executor_thread_id,
        export_suffix=export_suffix,
        revision_id=f"accepted-audit-{sha256_semantic_json(checked)[:12]}",
    )
    if build.get("errors") or build.get("status") != "complete":
        return {"status": "blocked", "stopped_at": "build", "build": build}
    validation = _required_audit_validation(video_id, data_root)
    if validation["errors"]:
        return {"status": "blocked", "stopped_at": "validator", "build": build, "validation": validation}
    metrics = {
        "total_ms": round((time.perf_counter() - started) * 1000, 2),
        "audits": 1,
        "audit_registrations": 1 if audit_written else 0,
        "builds": 1,
        "required_audit_validations": 1,
    }
    record_operation_event(
        out,
        "post_audit_completion",
        sha256_semantic_json({"audit": checked, "export_suffix": export_suffix}),
        metrics,
    )
    _record_session_event(
        job_dir, video_id, "post_audit_completion", metrics,
        started_at=phase_started_at,
    )
    completion_artifacts = None
    if job_dir is not None:
        start_semantic_phase_if_absent(job_dir, video_id, "closeout")
        end_semantic_phase_if_open(job_dir, video_id, "closeout")
        receipt = build_completion_receipt(video_id, data_root, export_suffix=export_suffix, metrics=metrics, job_dir=job_dir)
        completion_artifacts = write_completion_artifacts(job_dir, receipt, mirror_job_dir=mirror_job_dir)
        terminal_receipt_path = Path(completion_artifacts["receipt"])
        terminal_identity = register_terminal_completion(
            data_root,
            video_id,
            load_json(terminal_receipt_path),
            completion_receipt_path=terminal_receipt_path,
        )
    else:
        terminal_identity = None
    queue_path = Path(__file__).resolve().parents[1] / "docs" / "coordination" / "gold-episode-priority-queue.json"
    try:
        queue_state = (
            {"status": "not_configured"}
            if not queue_path.is_file()
            else {"status": "advanced", "state": advance_queue_state(queue_path, video_id, "complete_passed")}
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        queue_state = {"status": "unavailable", "error": str(error)}
    return {
        "status": "complete",
        "next_gate": "none",
        "episode_video_id": video_id,
        "audit": {"status": checked["status"], "open_findings": checked["open_findings"], "written": audit_written},
        "build": build,
        "validation": validation,
        "packet": str(data_root / "exports" / export_suffix),
        "metrics": metrics,
        "completion_artifacts": completion_artifacts,
        "audit_envelope": {
            "semantic_sha256": audit_envelope.get("semantic_sha256"),
            "request_semantic_sha256": audit_envelope.get("request_semantic_sha256"),
        } if audit_envelope else None,
        "terminal_identity": terminal_identity,
        "terminal_receipt": True,
        "additional_verify_required": False,
        "queue_state": queue_state,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", required=True)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--audit-input", required=True, type=Path)
    parser.add_argument("--executor-thread-id")
    parser.add_argument("--export-suffix", required=True)
    parser.add_argument("--job-dir", type=Path)
    parser.add_argument("--mirror-job-dir", type=Path, help="Optional final-only mirror for receipts and generated closeout artifacts.")
    parser.add_argument("--runtime-parity-receipt", type=Path)
    parser.add_argument("--runtime-manifest", type=Path)
    args = parser.parse_args()
    if args.runtime_parity_receipt or args.runtime_manifest:
        if not args.runtime_parity_receipt or not args.runtime_manifest:
            parser.error("runtime parity requires both receipt and manifest")
        _active_receipt, errors = _validate_or_pin_runtime_snapshot(
            args.job_dir,
            args.runtime_parity_receipt,
            args.runtime_manifest,
            Path(__file__).resolve().parents[1],
        )
        if errors:
            print(json.dumps({"status": "blocked", "stopped_at": "runtime_parity", "errors": errors}))
            return 1
    elif _is_wsl() and "/msf-data/Marketing_Swipe_File" in str(args.data_root.resolve()).replace("\\", "/"):
        print(json.dumps({"status": "blocked", "stopped_at": "runtime_parity", "errors": ["real WSL gold execution requires runtime parity"]}))
        return 1
    payload = load_json(args.audit_input)
    result = complete_episode(
        args.video_id,
        args.data_root,
        payload,
        executor_thread_id=args.executor_thread_id,
        export_suffix=args.export_suffix,
        job_dir=args.job_dir,
        mirror_job_dir=args.mirror_job_dir,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] in {"complete", "protected"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
