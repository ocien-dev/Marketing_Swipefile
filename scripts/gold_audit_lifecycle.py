#!/usr/bin/env python
"""Durable request/envelope boundary for final gold audits."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.gold_extraction_common import load_json, sha256_semantic_json, write_json


AUDIT_REQUEST_KIND = "gold_final_audit_request"
CONSOLIDATED_AUDIT_REQUEST_KIND = "gold_final_consolidated_audit_request"
AUDIT_ENVELOPE_KIND = "gold_final_audit_envelope"
AUDIT_REQUEST_SCHEMA = "1.0.0"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _close_materialized_audit_span(
    job_dir: Path,
    video_id: str,
    request: dict[str, Any],
    ended_at: str,
) -> None:
    """Close the matching Sol span at the verdict boundary.

    Session telemetry is internal and optional.  Materializing an envelope is
    the first durable proof that the model verdict exists, so leaving the span
    open beyond this point would charge remediation time to the audit.
    """
    session_path = job_dir / "episode_fast_session.json"
    if not session_path.is_file():
        return
    session = load_json(session_path)
    if session.get("episode_video_id") != video_id:
        raise ValueError("audit envelope session episode identity mismatch")
    phase = "final_sol_reaudit" if request.get("phase") == "reaudit" else "final_sol_audit"
    open_spans = [
        item
        for item in session.get("semantic_spans", [])
        if item.get("phase") == phase and not item.get("ended_at")
    ]
    if not open_spans:
        return
    if len(open_spans) != 1:
        raise ValueError(f"audit phase has multiple open spans: {phase}")
    span = open_spans[0]
    started = datetime.fromisoformat(str(span["started_at"]).replace("Z", "+00:00"))
    ended = datetime.fromisoformat(ended_at.replace("Z", "+00:00"))
    span["ended_at"] = ended_at
    span["elapsed_ms"] = round(max(0.0, (ended - started).total_seconds() * 1000.0), 2)
    span["state"] = "completed"
    write_json(session_path, session)


def _jsonl_semantic_sha256(path: Path) -> str:
    records = [
        __import__("json").loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    if records and records[-1].get("record_type") == "footer":
        return str(records[-1].get("content_semantic_sha256"))
    return sha256_semantic_json(records)


def audit_artifact_identity(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"audit artifact does not exist: {path}")
    if path.suffix.lower() == ".jsonl":
        semantic = _jsonl_semantic_sha256(path)
    else:
        payload = load_json(path)
        declared = payload.get("semantic_sha256") if isinstance(payload, dict) else None
        unhashed = (
            {key: value for key, value in payload.items() if key != "semantic_sha256"}
            if isinstance(payload, dict)
            else payload
        )
        computed = sha256_semantic_json(unhashed)
        semantic = declared if declared == computed else sha256_semantic_json(payload)
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "physical_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "semantic_sha256": semantic,
        "kind": "dossier" if path.suffix.lower() == ".jsonl" else "reaudit_delta",
    }


def build_audit_request(
    video_id: str,
    artifact_path: Path,
    *,
    audit_route: str = "final_model_review",
    reviewer_model: str = "gpt-5.6-sol",
    reasoning_effort: str = "high",
    phase: str = "final",
) -> dict[str, Any]:
    artifact = audit_artifact_identity(artifact_path)
    core = {
        "schema_version": AUDIT_REQUEST_SCHEMA,
        "kind": AUDIT_REQUEST_KIND,
        "episode_video_id": video_id,
        "phase": phase,
        "audit_route": audit_route,
        "reviewer_model": reviewer_model,
        "reasoning_effort": reasoning_effort,
        "artifact": artifact,
        "state": "running",
        "requested_at": _utc_now(),
    }
    return {**core, "semantic_sha256": sha256_semantic_json(core)}


def validate_audit_request(request: dict[str, Any]) -> list[str]:
    core = {key: value for key, value in request.items() if key != "semantic_sha256"}
    errors: list[str] = []
    if request.get("semantic_sha256") != sha256_semantic_json(core):
        errors.append("audit request semantic hash is invalid")
    if request.get("kind") != AUDIT_REQUEST_KIND:
        errors.append("audit request kind is invalid")
    if request.get("audit_route") != "final_model_review":
        errors.append("audit request route must be final_model_review")
    if request.get("reviewer_model") != "gpt-5.6-sol":
        errors.append("audit request model must be gpt-5.6-sol")
    if request.get("reasoning_effort") not in {"high", "xhigh", "max", "ultra"}:
        errors.append("audit request reasoning effort is below high")
    artifact = request.get("artifact", {})
    if not isinstance(artifact, dict) or not artifact.get("path"):
        errors.append("audit request artifact is missing")
    else:
        try:
            current = audit_artifact_identity(Path(artifact["path"]))
            for field in ("physical_sha256", "semantic_sha256", "bytes", "kind"):
                if current.get(field) != artifact.get(field):
                    errors.append(f"audit request artifact {field} is stale")
        except (OSError, ValueError) as error:
            errors.append(str(error))
    return errors


def write_audit_request(job_dir: Path, request: dict[str, Any]) -> dict[str, Any]:
    errors = validate_audit_request(request)
    if errors:
        raise ValueError("; ".join(errors))
    job_dir.mkdir(parents=True, exist_ok=True)
    history = job_dir / "audit_requests" / f"{request['semantic_sha256'][:20]}.json"
    history.parent.mkdir(parents=True, exist_ok=True)
    write_json(history, request)
    write_json(job_dir / "audit_request_receipt.json", request)
    return {"path": str(job_dir / "audit_request_receipt.json"), **request}


def build_consolidated_audit_request(
    scope_id: str,
    episodes: list[dict[str, Any]],
    *,
    reviewer_model: str = "gpt-5.6-sol",
    reasoning_effort: str = "high",
) -> dict[str, Any]:
    """Seal one final audit request only after every episode is dossier-ready."""
    if not scope_id or not episodes:
        raise ValueError("consolidated audit request requires a scope and episodes")
    seen: set[str] = set()
    sealed: list[dict[str, Any]] = []
    for episode in episodes:
        video_id = str(episode.get("episode_video_id", ""))
        if not video_id or video_id in seen:
            raise ValueError("consolidated audit request has a missing or duplicate episode")
        seen.add(video_id)
        if episode.get("status") != "ready":
            raise ValueError(f"episode {video_id} is not ready for final audit")
        if int(episode.get("unreviewed_segments", 0) or 0) != 0:
            raise ValueError(f"episode {video_id} is not source-complete")
        artifact_path = Path(str(episode.get("artifact_path", "")))
        identity = audit_artifact_identity(artifact_path)
        if identity.get("kind") != "dossier":
            raise ValueError(f"episode {video_id} final audit artifact is not a dossier")
        sealed.append({"episode_video_id": video_id, "artifact": identity})
    core = {
        "schema_version": AUDIT_REQUEST_SCHEMA,
        "kind": CONSOLIDATED_AUDIT_REQUEST_KIND,
        "scope_id": scope_id,
        "episode_count": len(sealed),
        "episodes": sealed,
        "audit_route": "final_model_review",
        "reviewer_model": reviewer_model,
        "reasoning_effort": reasoning_effort,
        "state": "running",
        "requested_at": _utc_now(),
    }
    return {**core, "semantic_sha256": sha256_semantic_json(core)}


def validate_consolidated_audit_request(request: dict[str, Any]) -> list[str]:
    core = {key: value for key, value in request.items() if key != "semantic_sha256"}
    errors: list[str] = []
    if request.get("semantic_sha256") != sha256_semantic_json(core):
        errors.append("consolidated audit request semantic hash is invalid")
    if request.get("kind") != CONSOLIDATED_AUDIT_REQUEST_KIND:
        errors.append("consolidated audit request kind is invalid")
    episodes = request.get("episodes", [])
    if not isinstance(episodes, list) or request.get("episode_count") != len(episodes) or not episodes:
        errors.append("consolidated audit request episode inventory is invalid")
    if request.get("reviewer_model") != "gpt-5.6-sol":
        errors.append("consolidated audit request model must be gpt-5.6-sol")
    if request.get("reasoning_effort") not in {"high", "xhigh", "max", "ultra"}:
        errors.append("consolidated audit request reasoning effort is below high")
    for episode in episodes if isinstance(episodes, list) else []:
        artifact = episode.get("artifact", {}) if isinstance(episode, dict) else {}
        try:
            current = audit_artifact_identity(Path(str(artifact.get("path", ""))))
            for field in ("physical_sha256", "semantic_sha256", "bytes", "kind"):
                if current.get(field) != artifact.get(field):
                    errors.append(f"consolidated audit artifact {field} is stale")
        except (OSError, ValueError) as error:
            errors.append(str(error))
    return errors


def write_consolidated_audit_request(job_dir: Path, request: dict[str, Any]) -> dict[str, Any]:
    errors = validate_consolidated_audit_request(request)
    if errors:
        raise ValueError("; ".join(errors))
    job_dir.mkdir(parents=True, exist_ok=True)
    path = job_dir / "consolidated_audit_request_receipt.json"
    write_json(path, request)
    return {"path": str(path), **request}


def materialize_audit_envelope(
    job_dir: Path,
    video_id: str,
    audit_payload: dict[str, Any],
    *,
    request_path: Path | None = None,
) -> dict[str, Any]:
    """Atomically bind the first post-model artifact to the sealed request."""
    request_path = request_path or (job_dir / "audit_request_receipt.json")
    if not request_path.is_file():
        raise ValueError("audit request receipt is missing")
    request = load_json(request_path)
    errors = validate_audit_request(request)
    if errors:
        raise ValueError("; ".join(errors))
    if request.get("episode_video_id") != video_id:
        raise ValueError("audit request episode identity mismatch")
    if audit_payload.get("episode_video_id") not in {None, video_id}:
        raise ValueError("audit payload episode identity mismatch")
    for field in ("audit_route", "reviewer_model", "reasoning_effort"):
        if audit_payload.get(field) != request.get(field):
            raise ValueError(f"audit payload {field} differs from sealed request")
    materialized_at = _utc_now()
    core = {
        "schema_version": AUDIT_REQUEST_SCHEMA,
        "kind": AUDIT_ENVELOPE_KIND,
        "episode_video_id": video_id,
        "request_semantic_sha256": request["semantic_sha256"],
        "artifact_semantic_sha256": request["artifact"]["semantic_sha256"],
        "audit_payload": audit_payload,
        "audit_payload_semantic_sha256": sha256_semantic_json(audit_payload),
        "materialized_at": materialized_at,
    }
    envelope = {**core, "semantic_sha256": sha256_semantic_json(core)}
    history = job_dir / "audit_envelopes" / f"{request['semantic_sha256'][:20]}.json"
    history.parent.mkdir(parents=True, exist_ok=True)
    if history.is_file():
        existing = load_json(history)
        existing_core = {
            key: value for key, value in existing.items()
            if key not in {"materialized_at", "semantic_sha256"}
        }
        current_core = {
            key: value for key, value in envelope.items()
            if key not in {"materialized_at", "semantic_sha256"}
        }
        if existing_core != current_core:
            raise ValueError("sealed audit request already has a different envelope")
        envelope = existing
    else:
        write_json(history, envelope)
    write_json(job_dir / "audit_envelope.json", envelope)
    _close_materialized_audit_span(
        job_dir,
        video_id,
        request,
        materialized_at,
    )
    return envelope


def validate_audit_envelope(
    envelope: dict[str, Any],
    request: dict[str, Any],
) -> list[str]:
    core = {key: value for key, value in envelope.items() if key != "semantic_sha256"}
    errors: list[str] = []
    if envelope.get("semantic_sha256") != sha256_semantic_json(core):
        errors.append("audit envelope semantic hash is invalid")
    if envelope.get("kind") != AUDIT_ENVELOPE_KIND:
        errors.append("audit envelope kind is invalid")
    if envelope.get("request_semantic_sha256") != request.get("semantic_sha256"):
        errors.append("audit envelope belongs to another request")
    if envelope.get("artifact_semantic_sha256") != request.get("artifact", {}).get("semantic_sha256"):
        errors.append("audit envelope artifact hash mismatch")
    if envelope.get("audit_payload_semantic_sha256") != sha256_semantic_json(envelope.get("audit_payload")):
        errors.append("audit envelope payload hash is invalid")
    return errors


def resume_audit_request(job_dir: Path, video_id: str) -> dict[str, Any]:
    request_path = job_dir / "audit_request_receipt.json"
    if not request_path.is_file():
        raise ValueError("audit request receipt is missing")
    request = load_json(request_path)
    errors = validate_audit_request(request)
    if request.get("episode_video_id") != video_id:
        errors.append("audit request episode identity mismatch")
    envelope_path = job_dir / "audit_envelopes" / f"{str(request.get('semantic_sha256'))[:20]}.json"
    if envelope_path.is_file():
        envelope = load_json(envelope_path)
        errors.extend(validate_audit_envelope(envelope, request))
        state = "completed"
    else:
        envelope = None
        state = "restart_final_model_only"
    if errors:
        return {"status": "blocked", "errors": errors, "request": request}
    return {
        "status": "ready",
        "state": state,
        "request": request,
        "envelope": envelope,
        "repeat_extraction": False,
        "repeat_build": False,
        "repeat_dossier": False,
    }
