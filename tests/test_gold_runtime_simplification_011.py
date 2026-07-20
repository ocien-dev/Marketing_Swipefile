from __future__ import annotations

import copy
from pathlib import Path

from scripts.complete_gold_episode import _session_performance
from scripts.gold_audit_lifecycle import (
    build_audit_request,
    materialize_audit_envelope,
    resume_audit_request,
    write_audit_request,
)
from scripts.gold_authoring_manifest import (
    ADVERSARIAL_REVIEW_CATEGORIES,
    authoring_decisions_sha256,
    calibration_decision_issues,
    manifest_to_compact_payload,
    normalize_authoring_input,
    validate_authoring_manifest,
)
from scripts.gold_extraction_common import candidate_numeric_coverage, sha256_semantic_json, write_json
from scripts.gold_review_compiler import hydrate_episode_payload
from scripts.gold_terminal_identity import register_terminal_completion
from scripts.run_gold_episode_fast import _fit_cli_output, select_next_episode


def _seed_source(root: Path, video_id: str, *, text: str = "Receita cresceu 40 por cento.") -> None:
    raw = root / "raw" / "youtube" / video_id
    processed = root / "processed" / video_id
    segments = [{
        "segment_id": f"{video_id}-transcript-0001",
        "clean_index": 0,
        "start_seconds": 0.0,
        "end_seconds": 3.0,
        "text": text,
    }]
    write_json(raw / "metadata.json", {
        "youtube_video_id": video_id,
        "title": video_id,
        "transcript_status": "available",
    })
    write_json(raw / "transcript_original.json", {
        "youtube_video_id": video_id,
        "transcript_status": "available",
        "segments": segments,
    })
    write_json(processed / "content_segments.json", {"segments": segments})


def _terminal_receipt(video_id: str) -> dict:
    core = {
        "schema_version": "1.1.0",
        "kind": "gold_episode_completion",
        "episode_video_id": video_id,
        "status": "complete",
        "audit_status": "passed",
        "open_audit_findings": 0,
    }
    return {**core, "receipt_semantic_sha256": sha256_semantic_json(core)}


def _queue(path: Path, video_ids: list[str]) -> None:
    entries = [
        {"rank": index + 1, "video_id": video_id, "title": video_id}
        for index, video_id in enumerate(video_ids)
    ]
    core = {"schema_version": "1.0.0", "kind": "gold_episode_priority_queue", "entries": entries}
    write_json(path, {**core, "semantic_sha256": sha256_semantic_json(entries)})


def _manifest(video_id: str) -> dict:
    manifest = {
        "schema_version": "1.0.0",
        "kind": "gold_authoring_manifest",
        "manifest_format": "gold_authoring_manifest_v1",
        "episode_video_id": video_id,
        "extraction_architecture": "chronological_hybrid_v1",
        "candidate_defaults": {},
        "type_defaults": {},
        "candidates": [],
        "zero_insight_chunks": [1],
        "source_dispositions": [{
            "segment_id": f"{video_id}-transcript-0001",
            "chunk_number": 1,
            "disposition": "excluded",
            "reason_code": "low_signal",
            "candidate_ids": [],
        }],
        "risk_recall_acknowledgements": [],
        "audit_warning_dispositions": [],
        "calibration_decisions": [{"calibration_id": "cal-1", "candidate_id": None}],
    }
    normalized, _ = normalize_authoring_input(video_id, manifest)
    return normalized


def test_hi01_stale_queue_terminal_is_skipped_by_active_registry(tmp_path):
    first, second = "terminal-first", "ready-second"
    _seed_source(tmp_path, first)
    _seed_source(tmp_path, second)
    receipt_path = tmp_path / "receipt.json"
    receipt = _terminal_receipt(first)
    write_json(receipt_path, receipt)
    register_terminal_completion(tmp_path, first, receipt, completion_receipt_path=receipt_path)
    # Prove that the central registry, not the episode directory, is sufficient.
    (tmp_path / "processed" / first / "gold_extraction" / "terminal_identity.json").unlink()
    (tmp_path / "processed" / first / "gold_extraction").rmdir()
    queue = tmp_path / "queue.json"
    _queue(queue, [first, second])

    result = select_next_episode(
        tmp_path, minimum_segments=1, maximum_segments=10, priority_queue=queue
    )

    assert result["status"] == "selected"
    assert result["selected"]["video_id"] == second
    assert result["terminal_reconciled_count"] == 1
    assert result["terminal_reconciled"][0]["video_id"] == first


def test_hi01_source_change_requires_explicit_reprocess_reason(tmp_path):
    video_id = "changed-source"
    _seed_source(tmp_path, video_id)
    receipt = _terminal_receipt(video_id)
    receipt_path = tmp_path / "receipt.json"
    write_json(receipt_path, receipt)
    register_terminal_completion(tmp_path, video_id, receipt, completion_receipt_path=receipt_path)
    (tmp_path / "processed" / video_id / "gold_extraction" / "terminal_identity.json").unlink()
    (tmp_path / "processed" / video_id / "gold_extraction").rmdir()
    _seed_source(tmp_path, video_id, text="Fonte corrigida para 45 por cento.")
    queue = tmp_path / "queue.json"
    _queue(queue, [video_id])

    blocked = select_next_episode(
        tmp_path, minimum_segments=1, maximum_segments=10, priority_queue=queue
    )
    allowed = select_next_episode(
        tmp_path,
        minimum_segments=1,
        maximum_segments=10,
        priority_queue=queue,
        explicit_reprocess=True,
        explicit_reprocess_reason="source transcript changed",
    )

    assert blocked["status"] == "blocked"
    assert blocked["explicit_reprocess_conflicts"][0]["video_id"] == video_id
    assert allowed["status"] == "selected"
    assert allowed["selected"]["video_id"] == video_id


def test_hi02_manifest_replaces_complete_reviews_without_parallel_patch_fields():
    video_id = "manifest-replace"
    manifest = _manifest(video_id)
    manifest["adversarial_review"] = {
        "status": "completed",
        "input_semantic_sha256": authoring_decisions_sha256(manifest),
        "reviewed_categories": list(ADVERSARIAL_REVIEW_CATEGORIES),
    }
    normalized, _ = normalize_authoring_input(video_id, manifest)
    assert validate_authoring_manifest(video_id, normalized, require_adversarial_review=True) == []
    payload = manifest_to_compact_payload(normalized, replace_existing_reviews=True)
    status = {"chunks": [{"chunk_number": 1, "chunk_id": "chunk-1", "input_hash": "hash-1"}]}
    existing = {"chunk_001_review.json": {"chunk_id": "chunk-1", "candidates": [{"candidate_id": "old"}]}}

    hydrated, issues = hydrate_episode_payload(video_id, payload, status, existing)

    assert issues == []
    assert hydrated["reviews"] == [{
        "chunk_number": 1,
        "candidates": [],
        "ledger_decisions": [{
            "segment_id": f"{video_id}-transcript-0001",
            "disposition": "excluded",
            "reason_code": "low_signal",
            "candidate_ids": [],
        }],
    }]


def test_hi02_rejects_ledger_and_calibration_parallel_authorities():
    video_id = "parallel-authority"
    manifest = _manifest(video_id)
    manifest["ledger_updates"] = [{"segment_id": "x"}]
    manifest["calibration_redirects"] = [{"calibration_id": "cal-1"}]
    normalized, _ = normalize_authoring_input(video_id, manifest)

    issues = validate_authoring_manifest(video_id, normalized, require_adversarial_review=False)

    assert {item["field"] for item in issues} >= {"ledger_updates", "calibration_redirects"}


def test_hi02_rejects_empty_or_partial_source_coverage():
    video_id = "source-complete"
    manifest = _manifest(video_id)
    manifest["source_dispositions"] = []
    empty_issues = validate_authoring_manifest(
        video_id,
        manifest,
        require_adversarial_review=False,
        expected_segment_ids={
            f"{video_id}-transcript-0001",
            f"{video_id}-transcript-0002",
        },
    )
    assert any(item["category"] == "source_coverage" for item in empty_issues)

    manifest["source_dispositions"] = [{
        "segment_id": f"{video_id}-transcript-0001",
        "chunk_number": 1,
        "disposition": "excluded",
        "reason_code": "low_signal",
        "candidate_ids": [],
    }]
    partial_issues = validate_authoring_manifest(
        video_id,
        manifest,
        require_adversarial_review=False,
        expected_segment_ids={
            f"{video_id}-transcript-0001",
            f"{video_id}-transcript-0002",
        },
    )
    coverage = next(item for item in partial_issues if item["category"] == "source_coverage")
    assert coverage["evidence"]["missing_segment_ids"] == [f"{video_id}-transcript-0002"]


def test_cli_fallback_counts_singleton_review_gates():
    compact = {
        "status": "blocked",
        "review_gate": [
            {"warning_id": "warning-one", "expected": "x" * 1000},
            {"warning_id": "warning-two", "expected": "y" * 1000},
        ],
        "hard_blockers": [],
        "audit_warnings": [{"category": "semantic", "item_count": 3}],
    }
    fitted = _fit_cli_output(compact, 128)
    assert fitted["review_gate_count"] == 2
    assert fitted["audit_warning_count"] == 3


def test_f019_calibration_topic_match_is_blocked_before_apply():
    manifest = _manifest("f019")
    manifest["calibration_decisions"] = [{"calibration_id": "cal-1", "candidate_id": "f019-G001"}]
    workbench = {
        "calibration_bindings": [{
            "calibration_id": "cal-1",
            "semantic_candidate_ids": ["f019-G001"],
            "linked_candidates": [{
                "candidate_id": "f019-G001",
                "status": "needs_semantic_confirmation",
                "evidence_intersection": [],
                "shared_proposition_terms": ["produto"],
                "numeric_anchor_match": False,
            }],
        }],
    }

    issues = calibration_decision_issues(manifest, workbench)

    assert issues[0]["category"] == "calibration_proposition_mismatch"


def test_f019_explicit_cross_language_equivalence_requires_exact_evidence_and_number():
    manifest = _manifest("f019-bilingual")
    manifest["calibration_decisions"] = [{
        "calibration_id": "cal-1",
        "candidate_id": "f019-bilingual-G001",
        "proposition_equivalent": True,
        "justification": "The Portuguese source span states the same proposition as the English editorial claim.",
    }]
    workbench = {
        "calibration_bindings": [{
            "calibration_id": "cal-1",
            "semantic_candidate_ids": ["f019-bilingual-G001"],
            "linked_candidates": [{
                "candidate_id": "f019-bilingual-G001",
                "status": "needs_semantic_confirmation",
                "evidence_intersection": ["f019-bilingual-transcript-0001"],
                "shared_proposition_terms": [],
                "numeric_anchor_match": True,
            }],
        }],
    }

    assert calibration_decision_issues(manifest, workbench) == []

    workbench["calibration_bindings"][0]["linked_candidates"][0]["evidence_intersection"] = []
    issues = calibration_decision_issues(manifest, workbench)
    assert issues[0]["category"] == "calibration_proposition_mismatch"


def test_f019_explicit_equivalence_can_bind_an_unlinked_calibration_by_exact_range():
    manifest = _manifest("f019-unlinked")
    manifest["calibration_decisions"] = [{
        "calibration_id": "cal-1",
        "candidate_id": "f019-unlinked-G001",
        "proposition_equivalent": True,
        "numeric_anchor_match": True,
        "justification": "The reviewed source span and candidate express the same proposition and numeric anchors.",
    }]
    workbench = {
        "candidate_bindings": [{
            "candidate_id": "f019-unlinked-G001",
            "evidence_clean_index_ranges": [[10, 12]],
        }],
        "calibration_bindings": [{
            "calibration_id": "cal-1",
            "target_clean_index_ranges": [[11, 11]],
            "semantic_candidate_ids": [],
            "linked_candidates": [],
        }],
    }

    assert calibration_decision_issues(manifest, workbench) == []

    workbench["calibration_bindings"][0]["target_clean_index_ranges"] = [[20, 20]]
    issues = calibration_decision_issues(manifest, workbench)
    assert issues[0]["category"] == "calibration_proposition_mismatch"


def test_f019_explicit_duplicate_source_equivalence_uses_one_canonical_numeric_record():
    manifest = _manifest("f019-duplicate")
    manifest["calibration_decisions"] = [{
        "calibration_id": "cal-1",
        "candidate_id": "f019-duplicate-G001",
        "source_equivalent_duplicate": True,
        "proposition_equivalent": True,
        "numeric_anchor_match": True,
        "duplicate_source_segment_ids": ["f019-duplicate-transcript-0001"],
        "canonical_source_segment_ids": ["f019-duplicate-transcript-0010"],
        "justification": "The cold open repeats the same numeric proposition retained at its canonical body occurrence.",
    }]
    workbench = {
        "candidate_bindings": [{
            "candidate_id": "f019-duplicate-G001",
            "evidence_clean_index_ranges": [[9, 9]],
        }],
        "calibration_bindings": [{
            "calibration_id": "cal-1",
            "target_clean_index_ranges": [[0, 0]],
            "target_segment_ids": ["f019-duplicate-transcript-0001"],
            "semantic_candidate_ids": [],
            "linked_candidates": [],
        }],
    }

    assert calibration_decision_issues(manifest, workbench) == []

    manifest["calibration_decisions"][0]["canonical_source_segment_ids"] = []
    issues = calibration_decision_issues(manifest, workbench)
    assert issues[0]["category"] == "calibration_proposition_mismatch"


def test_f037_candidate_edit_invalidates_adversarial_review_receipt():
    video_id = "f037"
    manifest = _manifest(video_id)
    manifest["adversarial_review"] = {
        "status": "completed",
        "input_semantic_sha256": authoring_decisions_sha256(manifest),
        "reviewed_categories": list(ADVERSARIAL_REVIEW_CATEGORIES),
    }
    manifest["candidates"].append({"id": f"{video_id}-G001", "k": 1, "cl": "Novo claim"})
    normalized, _ = normalize_authoring_input(video_id, manifest)

    issues = validate_authoring_manifest(video_id, normalized, require_adversarial_review=True)

    assert any(item["category"] == "adversarial_review_stale" for item in issues)


def _audit_payload(video_id: str) -> dict:
    return {
        "episode_video_id": video_id,
        "audit_route": "final_model_review",
        "reviewer": "sol",
        "reviewer_thread_id": "thread-1",
        "reviewer_model": "gpt-5.6-sol",
        "reasoning_effort": "high",
        "status": "passed",
        "summary": "source-complete audit passed",
        "findings": [],
    }


def test_hi04_request_envelope_is_durable_and_resume_does_not_rebuild(tmp_path):
    video_id = "audit-durable"
    artifact = tmp_path / "final_reaudit_delta.json"
    write_json(artifact, {"kind": "gold_final_reaudit_delta", "episode_video_id": video_id})
    request = build_audit_request(video_id, artifact, phase="reaudit")
    write_audit_request(tmp_path, request)

    before = resume_audit_request(tmp_path, video_id)
    envelope = materialize_audit_envelope(tmp_path, video_id, _audit_payload(video_id))
    after = resume_audit_request(tmp_path, video_id)

    assert before["state"] == "restart_final_model_only"
    assert before["repeat_extraction"] is False
    assert before["repeat_build"] is False
    assert envelope["request_semantic_sha256"] == request["semantic_sha256"]
    assert after["state"] == "completed"


def test_hi04_interrupted_span_is_not_counted_as_active_semantic_time():
    session = {
        "events": [],
        "semantic_spans": [
            {"phase": "final_sol_reaudit", "state": "interrupted", "elapsed_ms": 8 * 60 * 60 * 1000},
            {"phase": "final_sol_reaudit", "state": "completed", "elapsed_ms": 4 * 60 * 1000},
        ],
    }

    performance = _session_performance(session, 8 * 60 * 60 * 1000 + 4 * 60 * 1000)

    assert performance["semantic_phase_wall_ms"]["final_sol_reaudit"] == 4 * 60 * 1000
    assert performance["interrupted_semantic_span_count"] == 1
    assert performance["interrupted_semantic_wall_ms"] == 8 * 60 * 60 * 1000


def test_explicit_oral_numeric_duplicate_reuses_capacity_without_consuming_sales_records():
    candidate = {
        "candidate_id": "duplicate-capacity-G001",
        "type": "test_result",
        "source_claim": "The host announced 20 slots, forecast 10 sales, depois reported 20 sales.",
        "takeaway_applicavel": "Compare the forecast with the reported outcome.",
        "steps": [],
        "caveats": [
            "Source duplicate: 20 slots is repeated orally as the same capacity, not a second observation."
        ],
        "evidence": {
            "minimal_quote": [
                {"segment_id": "seg-1", "quote_verbatim": "Eu anunciei 20 vagas."},
                {
                    "segment_id": "seg-2",
                    "quote_verbatim": "Eu estimei 10% de 100 pessoas, 10 vendas, e repeti 20.",
                },
            ],
            "support_segments": [
                {
                    "segment_id": "seg-3",
                    "quote_verbatim": "Eu não sabia se faria 20 vendas e terminei com 20 vendas.",
                }
            ],
        },
        "numbers": [
            {"raw": "20", "value": 20, "unit_kind": "count", "unit": "slots"},
            {"raw": "10%", "value": 10, "unit_kind": "percent", "unit": "expected conversion rate"},
            {"raw": "100", "value": 100, "unit_kind": "count", "unit": "live attendees"},
            {"raw": "10 vendas", "value": 10, "unit_kind": "count", "unit": "expected sales"},
            {"raw": "20 vendas", "value": 20, "unit_kind": "count", "unit": "sales", "role": "target"},
            {"raw": "20 vendas", "value": 20, "unit_kind": "count", "unit": "sales", "role": "result"},
        ],
    }
    signals = {
        "seg-1": {"number"},
        "seg-2": {"number", "sequence"},
        "seg-3": {"number", "sequence", "test_result"},
    }

    coverage = candidate_numeric_coverage(candidate, signals)

    assert coverage["status"] == "pass"
    assert coverage["missing_material"] == []
    assert coverage["record_count"] == 6
    assert coverage["sequence"]["ordered_values"] == ["20", "10", "100", "10", "20", "20"]
    duplicate = [item for item in coverage["mentions"] if item["disposition"] == "covered_explicit_duplicate"]
    assert len(duplicate) == 1
    assert duplicate[0]["record_index"] == 0
    assert coverage["covered_record_indexes"] == [0, 1, 2, 3, 4, 5]
