from __future__ import annotations

import copy
from pathlib import Path

import pytest

from scripts.gold_audit_lifecycle import (
    build_consolidated_audit_request,
    validate_consolidated_audit_request,
    write_consolidated_audit_request,
)
from scripts.gold_authoring_manifest import normalize_authoring_input
from scripts.gold_extraction_common import load_json, sha256_semantic_json, write_json
from scripts.gold_final_audit_bundle import _compact_warning_references
from scripts.gold_review_autocheck import review_audit_warnings, source_complete_invariant_issues
from scripts.gold_terminal_identity import open_terminal_revision, register_terminal_completion
from scripts.run_gold_episode_fast import _bind_local_warning_identities, run_authoring_manifest_remediation


def _manifest(video_id: str) -> dict:
    raw = {
        "schema_version": "1.0.0",
        "kind": "gold_authoring_manifest",
        "manifest_format": "gold_authoring_manifest_v1",
        "episode_video_id": video_id,
        "extraction_architecture": "chronological_hybrid_v1",
        "candidate_defaults": {},
        "type_defaults": {},
        "candidates": [],
        "zero_insight_chunks": [1],
        "source_dispositions": [],
        "risk_recall_acknowledgements": [],
        "audit_warning_dispositions": [],
        "calibration_decisions": [],
    }
    return normalize_authoring_input(video_id, raw)[0]


def test_source_complete_invariant_rejects_unreviewed_segments():
    report = {
        "transcript_segments": 427,
        "semantic_workbench": {"summary": {
            "transcript_segments": 427,
            "covered_segments": 0,
            "excluded_segments": 0,
            "unreviewed_segments": 427,
        }},
        "numeric_coverage": [],
        "calibration": {"status": "pass"},
        "audit_warnings": [],
    }

    issues = source_complete_invariant_issues(report)

    assert any(item.get("unreviewed_segments") == 427 for item in issues)


def test_warning_identity_is_local_to_source_candidate_and_proposition():
    warning = [{"category": "semantic_workbench", "items": [{
        "issue": "claim needs confirmation",
        "closure_kind": "candidate_binding",
        "candidate_ids": ["G012"],
        "segment_ids": ["seg-12"],
        "clean_index_range": [12, 14],
        "review_requirement": "audit_only",
    }]}]
    first = review_audit_warnings(warning)[1][0]
    unrelated = copy.deepcopy(warning)
    unrelated.append({"category": "semantic_workbench", "items": [{
        "issue": "another claim",
        "closure_kind": "candidate_binding",
        "candidate_ids": ["G044"],
        "segment_ids": ["seg-44"],
        "clean_index_range": [44, 45],
        "review_requirement": "audit_only",
    }]})
    second = review_audit_warnings(unrelated)[1][0]

    assert first["warning_id"] == second["warning_id"]
    assert first["input_semantic_sha256"] == second["input_semantic_sha256"]


def test_must_close_retained_support_without_candidate_binding_stays_open():
    warning = [{"category": "semantic_workbench", "items": [{
        "issue": "material source block is not bound",
        "closure_kind": "uncovered_material",
        "segment_ids": ["seg-1"],
        "clean_index_range": [1, 1],
        "review_requirement": "must_close",
    }]}]
    warning_id = review_audit_warnings(warning)[1][0]["warning_id"]

    _reviewed, _inventory, unresolved = review_audit_warnings(
        warning,
        [{
            "warning_id": warning_id,
            "disposition": "retained_support",
            "justification": "The segment supports an existing claim.",
        }],
        required_categories={"semantic_workbench"},
    )

    assert unresolved


def test_local_warning_input_hash_is_persisted_in_rebound_manifest():
    video_id = "local-warning"
    manifest = _manifest(video_id)
    manifest["audit_warning_dispositions"] = [{
        "warning_id": "warning-legacy",
        "disposition": "incidental",
        "source_segment_ids": ["seg-1"],
        "justification": "The scoped source is incidental promotion.",
    }]
    preview = {"prelint_inventory": {"audit_warning_inventory": [{
        "warning_id": "warning-local",
        "matched_disposition_warning_id": "warning-legacy",
        "input_semantic_sha256": "a" * 64,
    }]}}

    rebound = _bind_local_warning_identities(video_id, manifest, preview)

    decision = rebound["audit_warning_dispositions"][0]
    assert decision["warning_id"] == "warning-local"
    assert decision["input_semantic_sha256"] == "a" * 64


def test_compact_warning_surface_deduplicates_only_exact_identity_rows():
    item = {
        "warning_id": "warning-exact",
        "issue": "same local proposition",
        "segment_ids": ["seg-1"],
        "review": {"disposition": "incidental", "justification": "Scoped promotion."},
    }
    surface, _justifications = _compact_warning_references([
        {"category": "semantic_workbench", "kind": "audit_warning", "items": [item]},
        {"category": "semantic_workbench", "kind": "audit_warning", "items": [copy.deepcopy(item)]},
    ])

    assert surface["item_count"] == 1
    assert surface["identity_collisions"] == []


def test_owner_authorized_terminal_revision_preserves_prior_identity(tmp_path):
    video_id = "terminal-revision"
    raw = tmp_path / "raw" / "youtube" / video_id
    processed = tmp_path / "processed" / video_id
    segments = [{
        "segment_id": f"{video_id}-transcript-0001",
        "clean_index": 0,
        "start_seconds": 0.0,
        "duration_seconds": 1.0,
        "text": "Source proposition.",
    }]
    write_json(raw / "metadata.json", {"youtube_video_id": video_id, "transcript_status": "available"})
    write_json(raw / "transcript_original.json", {"youtube_video_id": video_id, "transcript_status": "available", "segments": segments})
    write_json(processed / "content_segments.json", {"segments": segments})
    out = processed / "gold_extraction"
    write_json(out / "gold_extraction_status.json", {
        "episode_video_id": video_id, "status": "complete", "audit_status": "passed", "open_audit_findings": 0,
    })
    write_json(out / "gold_finalization_receipt.json", {"status": "ready"})
    receipt_core = {
        "schema_version": "1.1.0", "kind": "gold_episode_completion",
        "episode_video_id": video_id, "status": "complete", "audit_status": "passed",
        "open_audit_findings": 0,
    }
    first_receipt = {**receipt_core, "receipt_semantic_sha256": sha256_semantic_json(receipt_core)}
    first_identity = register_terminal_completion(tmp_path, video_id, first_receipt)
    prior_audit = {
        "episode_video_id": video_id,
        "status": "passed",
        "findings": [],
        "open_findings": 0,
    }
    write_json(out / "editorial_audit_report.json", prior_audit)
    audit = {
        "episode_video_id": video_id, "status": "changes_requested",
        "findings": [{"finding_id": "F-1", "status": "open"}],
    }

    opened = open_terminal_revision(
        tmp_path, video_id,
        revision_id="revision-002", reason="Owner authorized semantic correction.",
        audit_payload=audit, job_dir=tmp_path / "job",
    )

    assert opened["status"] == "opened"
    assert opened["prior_terminal_identity_preserved"] is True
    assert opened["archived_prior_audit"]
    assert not (out / "editorial_audit_report.json").exists()
    assert load_json(Path(opened["archived_prior_audit"])) == prior_audit
    assert load_json(out / "gold_extraction_status.json")["audit_status"] == "changes_requested"
    assert load_json(out / "terminal_identity.json") == first_identity

    second_core = {**receipt_core, "revision_id": "revision-002"}
    second_receipt = {**second_core, "receipt_semantic_sha256": sha256_semantic_json(second_core)}
    second_identity = register_terminal_completion(tmp_path, video_id, second_receipt)
    history = out / "terminal_identity_history" / f"{first_identity['semantic_sha256'][:20]}.json"
    assert history.is_file()
    assert second_identity["completion_receipt_semantic_sha256"] == second_receipt["receipt_semantic_sha256"]


def test_envelope_absence_blocks_authoring_remediation_before_gold_write(tmp_path):
    video_id = "envelope-first"
    job_dir = tmp_path / "job"
    prior = _manifest(video_id)
    write_json(job_dir / "gold_authoring_manifest.json", prior)
    remediation = copy.deepcopy(prior)
    remediation["base_manifest_semantic_sha256"] = prior["semantic_sha256"]
    remediation = normalize_authoring_input(video_id, remediation)[0]

    result = run_authoring_manifest_remediation(
        video_id,
        tmp_path,
        remediation,
        revision_id="remediation-001",
        export_suffix=None,
        job_dir=job_dir,
    )

    assert result["stopped_at"] == "audit_envelope_precondition"
    assert result["writes_gold"] is False
    assert result["metrics"]["review_write_operations"] == 0
    assert not (tmp_path / "processed").exists()


def test_consolidated_request_refuses_partial_scope_without_writing(tmp_path):
    artifact = tmp_path / "episode-a.jsonl"
    artifact.write_text('{"record_type":"footer","content_semantic_sha256":"abc"}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="not ready"):
        build_consolidated_audit_request("wave-012", [{
            "episode_video_id": "episode-a",
            "status": "pending",
            "artifact_path": str(artifact),
        }])

    assert not (tmp_path / "consolidated_audit_request_receipt.json").exists()


def test_consolidated_request_seals_all_ready_dossiers(tmp_path):
    episodes = []
    for video_id in ("episode-a", "episode-b"):
        artifact = tmp_path / f"{video_id}.jsonl"
        artifact.write_text('{"record_type":"footer","content_semantic_sha256":"abc"}\n', encoding="utf-8")
        episodes.append({
            "episode_video_id": video_id,
            "status": "ready",
            "unreviewed_segments": 0,
            "artifact_path": str(artifact),
        })

    request = build_consolidated_audit_request("wave-012", episodes)
    receipt = write_consolidated_audit_request(tmp_path, request)

    assert validate_consolidated_audit_request(request) == []
    assert receipt["episode_count"] == 2
    assert Path(receipt["path"]).is_file()
