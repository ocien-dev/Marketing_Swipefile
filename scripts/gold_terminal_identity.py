#!/usr/bin/env python
"""Reconcile terminal gold receipts with the active source identity.

The priority queue is ordering only.  This module is the read-through terminal
authority used by selection and the write-through registry used by completion.
It never copies or mutates raw, transcript, packet, or gold editorial data.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from scripts.gold_extraction_common import (
    SCHEMA_VERSION,
    json_hashes,
    load_json,
    now,
    preferred_transcript_path,
    sha256_semantic_json,
    transcript_source_paths,
    write_json,
)


TERMINAL_IDENTITY_KIND = "gold_terminal_identity"
TERMINAL_REGISTRY_KIND = "gold_terminal_registry"
TERMINAL_IDENTITY_SCHEMA = "1.0.0"
CANONICAL_EXTRACTION_ARCHITECTURE = "chronological_hybrid_v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def terminal_registry_path(data_root: Path) -> Path:
    return data_root / "processed" / ".gold_terminal_registry.json"


def terminal_identity_path(data_root: Path, video_id: str) -> Path:
    return data_root / "processed" / video_id / "gold_extraction" / "terminal_identity.json"


def _source_paths(data_root: Path, video_id: str) -> list[tuple[str, Path]]:
    paths: list[tuple[str, Path]] = [
        ("metadata", data_root / "raw" / "youtube" / video_id / "metadata.json"),
    ]
    for index, path in enumerate(transcript_source_paths(data_root, video_id)):
        role = "transcript_preferred" if path == preferred_transcript_path(data_root, video_id) else f"transcript_source_{index}"
        paths.append((role, path))
    paths.append(("content_segments", data_root / "processed" / video_id / "content_segments.json"))
    unique: list[tuple[str, Path]] = []
    seen: set[Path] = set()
    for role, path in paths:
        resolved = path.resolve(strict=False)
        if resolved not in seen:
            unique.append((role, path))
            seen.add(resolved)
    return unique


def source_identity(data_root: Path, video_id: str) -> dict[str, Any]:
    """Hash the semantic source independently from filesystem paths."""
    files: list[dict[str, Any]] = []
    missing: list[str] = []
    for role, path in _source_paths(data_root, video_id):
        if not path.is_file():
            missing.append(role)
            continue
        try:
            value = load_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            return {
                "status": "invalid",
                "episode_video_id": video_id,
                "errors": [f"{role}: {error}"],
                "missing": missing,
            }
        files.append({
            "role": role,
            "semantic_sha256": sha256_semantic_json(value),
        })
    if missing:
        return {
            "status": "missing",
            "episode_video_id": video_id,
            "errors": [],
            "missing": missing,
        }
    core = {
        "episode_video_id": video_id,
        "files": files,
    }
    return {
        "status": "ready",
        **core,
        "source_semantic_sha256": sha256_semantic_json(core),
        "errors": [],
        "missing": [],
    }


def _identity_core(
    data_root: Path,
    video_id: str,
    *,
    completion_receipt: dict[str, Any],
    completion_receipt_path: Path | None,
) -> dict[str, Any]:
    source = source_identity(data_root, video_id)
    if source.get("status") != "ready":
        raise ValueError("terminal identity requires a complete active source")
    return {
        "schema_version": TERMINAL_IDENTITY_SCHEMA,
        "kind": TERMINAL_IDENTITY_KIND,
        "episode_video_id": video_id,
        "source_semantic_sha256": source["source_semantic_sha256"],
        "source_files": source["files"],
        "extraction_architecture": CANONICAL_EXTRACTION_ARCHITECTURE,
        "gold_schema_version": SCHEMA_VERSION,
        "lifecycle": completion_receipt.get("status"),
        "audit_status": completion_receipt.get("audit_status"),
        "open_audit_findings": completion_receipt.get("open_audit_findings"),
        "completion_receipt_semantic_sha256": completion_receipt.get("receipt_semantic_sha256"),
        "completion_receipt_path": str(completion_receipt_path) if completion_receipt_path else None,
        "registered_at": _utc_now(),
    }


def validate_terminal_identity(identity: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    core = {key: value for key, value in identity.items() if key != "semantic_sha256"}
    if identity.get("semantic_sha256") != sha256_semantic_json(core):
        errors.append("terminal identity semantic hash is invalid")
    if identity.get("kind") != TERMINAL_IDENTITY_KIND:
        errors.append("terminal identity kind is invalid")
    if identity.get("extraction_architecture") != CANONICAL_EXTRACTION_ARCHITECTURE:
        errors.append("terminal identity architecture is incompatible")
    if identity.get("gold_schema_version") != SCHEMA_VERSION:
        errors.append("terminal identity gold schema is incompatible")
    if identity.get("lifecycle") != "complete" or identity.get("audit_status") != "passed":
        errors.append("terminal identity is not complete/passed")
    if identity.get("open_audit_findings") not in {0, None}:
        errors.append("terminal identity has open audit findings")
    if not identity.get("completion_receipt_semantic_sha256"):
        errors.append("terminal identity has no completion receipt")
    return errors


def load_terminal_registry(data_root: Path) -> dict[str, Any]:
    path = terminal_registry_path(data_root)
    if not path.is_file():
        return {
            "schema_version": TERMINAL_IDENTITY_SCHEMA,
            "kind": TERMINAL_REGISTRY_KIND,
            "entries": [],
        }
    registry = load_json(path)
    core = {key: value for key, value in registry.items() if key != "semantic_sha256"}
    if registry.get("kind") != TERMINAL_REGISTRY_KIND:
        raise ValueError("terminal registry kind is invalid")
    if registry.get("semantic_sha256") != sha256_semantic_json(core):
        raise ValueError("terminal registry semantic hash is invalid")
    if not isinstance(registry.get("entries"), list):
        raise ValueError("terminal registry entries must be a list")
    return registry


def register_terminal_completion(
    data_root: Path,
    video_id: str,
    completion_receipt: dict[str, Any],
    *,
    completion_receipt_path: Path | None = None,
) -> dict[str, Any]:
    """Write only terminal identity metadata after a validated completion."""
    receipt_core = {
        key: value for key, value in completion_receipt.items()
        if key != "receipt_semantic_sha256"
    }
    if completion_receipt.get("receipt_semantic_sha256") != sha256_semantic_json(receipt_core):
        raise ValueError("completion receipt semantic hash is invalid")
    existing_path = terminal_identity_path(data_root, video_id)
    if existing_path.is_file():
        existing = load_json(existing_path)
        current_source = source_identity(data_root, video_id)
        status_path = existing_path.parent / "gold_extraction_status.json"
        current_status = load_json(status_path) if status_path.is_file() else {}
        terminal_revision = current_status.get("terminal_revision", {})
        revision_replaces_existing = (
            isinstance(terminal_revision, dict)
            and terminal_revision.get("prior_terminal_identity_semantic_sha256")
            == existing.get("semantic_sha256")
        )
        if (
            not validate_terminal_identity(existing)
            and current_source.get("status") == "ready"
            and existing.get("source_semantic_sha256") == current_source.get("source_semantic_sha256")
        ):
            if existing.get("completion_receipt_semantic_sha256") == completion_receipt.get("receipt_semantic_sha256"):
                return existing
            # A protected idempotent replay may regenerate a completion receipt
            # with fresh telemetry timestamps.  It must not replace the sealed
            # identity.  Replacement is legal only after an explicitly opened
            # terminal revision that binds the prior identity hash.
            if not revision_replaces_existing:
                return existing
            history_path = (
                existing_path.parent
                / "terminal_identity_history"
                / f"{existing['semantic_sha256'][:20]}.json"
            )
            if not history_path.is_file():
                write_json(history_path, existing)
    core = _identity_core(
        data_root,
        video_id,
        completion_receipt=completion_receipt,
        completion_receipt_path=completion_receipt_path,
    )
    identity = {**core, "semantic_sha256": sha256_semantic_json(core)}
    errors = validate_terminal_identity(identity)
    if errors:
        raise ValueError("; ".join(errors))
    write_json(terminal_identity_path(data_root, video_id), identity)

    registry = load_terminal_registry(data_root)
    entries = {
        str(item.get("episode_video_id")): item
        for item in registry.get("entries", [])
        if isinstance(item, dict) and item.get("episode_video_id")
    }
    entries[video_id] = identity
    registry_core = {
        "schema_version": TERMINAL_IDENTITY_SCHEMA,
        "kind": TERMINAL_REGISTRY_KIND,
        "entries": [entries[key] for key in sorted(entries)],
        "updated_at": _utc_now(),
    }
    write_json(
        terminal_registry_path(data_root),
        {**registry_core, "semantic_sha256": sha256_semantic_json(registry_core)},
    )
    return identity


def open_terminal_revision(
    data_root: Path,
    video_id: str,
    *,
    revision_id: str,
    reason: str,
    audit_payload: dict[str, Any],
    job_dir: Path,
) -> dict[str, Any]:
    """Open an owner-authorized semantic revision without mutating sealed provenance."""
    if not revision_id.strip() or not reason.strip():
        raise ValueError("terminal revision requires revision_id and reason")
    findings = [
        item for item in audit_payload.get("findings", [])
        if isinstance(item, dict) and item.get("status", "open") == "open"
    ]
    if audit_payload.get("status") != "changes_requested" or not findings:
        raise ValueError("terminal revision requires a changes_requested audit with open findings")
    if audit_payload.get("episode_video_id") not in {None, video_id}:
        raise ValueError("terminal revision audit episode identity mismatch")
    terminal = resolve_terminal_identity(data_root, video_id)
    if not terminal.get("terminal"):
        raise ValueError("episode is not protected by a compatible terminal identity")
    out = data_root / "processed" / video_id / "gold_extraction"
    status_path = out / "gold_extraction_status.json"
    identity_path = terminal_identity_path(data_root, video_id)
    finalization_path = out / "gold_finalization_receipt.json"
    audit_path = out / "editorial_audit_report.json"
    required = [status_path, identity_path, finalization_path]
    if any(not path.is_file() for path in required):
        raise ValueError("terminal revision provenance is incomplete")
    prior_status = load_json(status_path)
    if prior_status.get("status") != "complete" or prior_status.get("audit_status") != "passed":
        raise ValueError("terminal revision requires local complete/passed status")
    prior_provenance = {
        "status": json_hashes(status_path),
        "terminal_identity": json_hashes(identity_path),
        "finalization_receipt": json_hashes(finalization_path),
    }
    audit_history_path: Path | None = None
    if audit_path.is_file():
        audit_hashes = json_hashes(audit_path)
        audit_history_path = out / "audit_history" / f"{audit_hashes['semantic_sha256']}.json"
        audit_history_path.parent.mkdir(parents=True, exist_ok=True)
        source_bytes = audit_path.read_bytes()
        if audit_history_path.is_file():
            if audit_history_path.read_bytes() != source_bytes:
                raise ValueError("sealed audit history hash collision")
        else:
            temporary = audit_history_path.with_suffix(".json.tmp")
            temporary.write_bytes(source_bytes)
            temporary.replace(audit_history_path)
        if audit_history_path.read_bytes() != source_bytes:
            raise ValueError("sealed audit history copy verification failed")
        prior_provenance["editorial_audit_report"] = {
            **audit_hashes,
            "history_path": str(audit_history_path),
        }
    core = {
        "schema_version": "1.0.0",
        "kind": "gold_terminal_revision_authorization",
        "episode_video_id": video_id,
        "revision_id": revision_id,
        "reason": reason.strip(),
        "audit_payload_semantic_sha256": sha256_semantic_json(audit_payload),
        "finding_ids": sorted(str(item.get("finding_id") or item.get("id")) for item in findings),
        "prior_provenance": prior_provenance,
        "authorized_at": now(),
    }
    receipt = {**core, "semantic_sha256": sha256_semantic_json(core)}
    receipt_path = job_dir / "terminal_revision_authorization.json"
    if receipt_path.is_file():
        existing = load_json(receipt_path)
        comparable_existing = {
            key: value for key, value in existing.items()
            if key not in {"authorized_at", "semantic_sha256"}
        }
        comparable_current = {
            key: value for key, value in receipt.items()
            if key not in {"authorized_at", "semantic_sha256"}
        }
        if comparable_existing != comparable_current:
            raise ValueError("job-dir already contains a different terminal revision authorization")
        receipt = existing
    else:
        write_json(receipt_path, receipt)
    if audit_history_path is not None:
        audit_path.unlink()
    reopened = {
        **prior_status,
        "status": "awaiting_semantic_review",
        "audit_status": "changes_requested",
        "open_audit_findings": len(findings),
        "terminal_revision": {
            "revision_id": revision_id,
            "reason": reason.strip(),
            "prior_terminal_identity_semantic_sha256": terminal.get("identity", {}).get("semantic_sha256"),
            "authorization_semantic_sha256": receipt["semantic_sha256"],
        },
        "updated_at": now(),
    }
    write_json(status_path, reopened)
    return {
        "status": "opened",
        "episode_video_id": video_id,
        "revision_id": revision_id,
        "finding_count": len(findings),
        "authorization": {"path": str(receipt_path), **receipt},
        "prior_terminal_identity_preserved": True,
        "archived_prior_audit": str(audit_history_path) if audit_history_path else None,
    }


def resolve_terminal_identity(data_root: Path, video_id: str) -> dict[str, Any]:
    """Resolve current terminal state without trusting queue cursor history."""
    source = source_identity(data_root, video_id)
    out = data_root / "processed" / video_id / "gold_extraction"
    status_path = out / "gold_extraction_status.json"
    local_status = load_json(status_path) if status_path.is_file() else {}
    local_protected = (
        local_status.get("status") == "complete"
        and local_status.get("audit_status") == "passed"
        and local_status.get("open_audit_findings") in {0, None}
    )

    candidates: list[tuple[str, dict[str, Any]]] = []
    local_identity = terminal_identity_path(data_root, video_id)
    if local_identity.is_file():
        candidates.append(("episode", load_json(local_identity)))
    try:
        registry = load_terminal_registry(data_root)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return {
            "status": "registry_invalid",
            "terminal": local_protected,
            "episode_video_id": video_id,
            "source": source,
            "errors": [str(error)],
        }
    for entry in registry.get("entries", []):
        if isinstance(entry, dict) and entry.get("episode_video_id") == video_id:
            candidates.append(("registry", entry))

    for authority, identity in candidates:
        errors = validate_terminal_identity(identity)
        if errors:
            continue
        if source.get("status") != "ready":
            continue
        if identity.get("source_semantic_sha256") == source.get("source_semantic_sha256"):
            return {
                "status": "terminal_compatible",
                "terminal": True,
                "episode_video_id": video_id,
                "authority": authority,
                "identity": identity,
                "source": source,
                "errors": [],
            }
        return {
            "status": "terminal_source_changed",
            "terminal": False,
            "explicit_reprocess_required": True,
            "episode_video_id": video_id,
            "authority": authority,
            "identity": identity,
            "source": source,
            "errors": [],
        }
    if local_protected:
        return {
            "status": "terminal_local_legacy",
            "terminal": True,
            "episode_video_id": video_id,
            "authority": "gold_status",
            "identity": None,
            "source": source,
            "errors": ["local complete/passed gold has no compatible terminal receipt identity"],
        }
    if out.is_dir():
        return {
            "status": "gold_in_progress",
            "terminal": False,
            "episode_video_id": video_id,
            "source": source,
            "errors": [],
        }
    return {
        "status": "not_terminal",
        "terminal": False,
        "episode_video_id": video_id,
        "source": source,
        "errors": [],
    }


def _receipt_is_terminal(receipt: dict[str, Any]) -> bool:
    core = {key: value for key, value in receipt.items() if key != "receipt_semantic_sha256"}
    return bool(
        receipt.get("receipt_semantic_sha256") == sha256_semantic_json(core)
        and receipt.get("kind") == "gold_episode_completion"
        and receipt.get("status") == "complete"
        and receipt.get("audit_status") == "passed"
        and receipt.get("open_audit_findings") in {0, None}
    )


def reconcile_completion_receipts(
    data_root: Path,
    receipt_roots: Iterable[Path],
) -> dict[str, Any]:
    """Import compatible receipt identities only; never copy episode data."""
    imported: list[str] = []
    incompatible: list[dict[str, str]] = []
    invalid: list[dict[str, str]] = []
    seen: set[Path] = set()
    for root in receipt_roots:
        paths = [root] if root.is_file() else sorted(root.rglob("episode_completion_receipt.json"))
        for path in paths:
            resolved = path.resolve(strict=False)
            if resolved in seen:
                continue
            seen.add(resolved)
            try:
                receipt = load_json(path)
            except (OSError, ValueError, json.JSONDecodeError) as error:
                invalid.append({"path": str(path), "error": str(error)})
                continue
            if not _receipt_is_terminal(receipt):
                invalid.append({"path": str(path), "error": "receipt is not valid complete/passed terminal authority"})
                continue
            video_id = str(receipt.get("episode_video_id") or "")
            source = source_identity(data_root, video_id)
            # New receipts carry a direct identity.  Historical receipts are
            # accepted only when every semantic file hash is present in the
            # active source; path names and data-root locations are ignored.
            active_hashes = {item.get("semantic_sha256") for item in source.get("files", [])}
            receipt_hashes = {item.get("semantic_sha256") for item in receipt.get("source_files", [])}
            compatible = (
                source.get("status") == "ready"
                and receipt_hashes
                and receipt_hashes <= active_hashes
            )
            if not compatible:
                incompatible.append({"path": str(path), "episode_video_id": video_id})
                continue
            register_terminal_completion(
                data_root,
                video_id,
                receipt,
                completion_receipt_path=path,
            )
            imported.append(video_id)
    return {
        "status": "ok",
        "imported": sorted(set(imported)),
        "incompatible": incompatible,
        "invalid": invalid,
        "data_migrated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--video-id")
    parser.add_argument("--resolve", action="store_true")
    parser.add_argument("--receipt-root", action="append", type=Path, default=[])
    args = parser.parse_args()
    if args.resolve:
        if not args.video_id:
            parser.error("--resolve requires --video-id")
        result = resolve_terminal_identity(args.data_root, args.video_id)
    else:
        if not args.receipt_root:
            parser.error("receipt reconciliation requires --receipt-root")
        result = reconcile_completion_receipts(args.data_root, args.receipt_root)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("status") in {"ok", "not_terminal", "terminal_compatible", "terminal_local_legacy"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
