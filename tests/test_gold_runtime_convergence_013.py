from __future__ import annotations

from pathlib import Path

from scripts.gold_audit_lifecycle import (
    build_audit_request,
    materialize_audit_envelope,
    write_audit_request,
)
from scripts.gold_authoring_manifest import manifest_to_compact_payload
from scripts.gold_final_audit_bundle import numeric_coverage_source_projection
from scripts.gold_review_autocheck import semantic_coverage_workbench
from scripts.gold_extraction_common import (
    calibration_coverage,
    candidate_numeric_coverage,
    load_json,
    write_json,
)
from scripts.run_gold_episode_fast import (
    mark_semantic_phase,
    remediation_impact_closure,
    start_semantic_phase_if_absent,
)


def _candidate(*, raw: str, number: dict, caveats: list[str] | None = None) -> dict:
    return {
        "candidate_id": "episode-G001",
        "type": "quantitative_case",
        "source_claim": f"O caso reporta {raw} como resultado material.",
        "takeaway_applicavel": f"Preservar {raw} com unidade, papel e atribuicao source-backed.",
        "steps": [],
        "caveats": caveats or [],
        "numbers": [number],
        "evidence": {
            "minimal_quote": [{
                "segment_id": "episode-transcript-1",
                "quote_verbatim": f"O caso reporta {raw} como resultado material.",
            }],
            "support_segments": [],
        },
    }


def _number(
    raw: str,
    *,
    value: float | None,
    unit_kind: str,
    unit: str,
    role: str,
) -> dict:
    return {
        "raw": raw,
        "value": value,
        "min_value": None,
        "max_value": None,
        "unit_kind": unit_kind,
        "unit": unit,
        "period": None,
        "role": role,
        "value_status": "inferred" if value is None else "reported",
        "denominator": None,
        "attribution_window": None,
    }


def test_p0_numeric_closure_rejects_material_opaque_count_fallback():
    candidate = _candidate(
        raw="R$ 100",
        number=_number("R$ 100", value=None, unit_kind="count", unit="count", role="other"),
    )
    coverage = candidate_numeric_coverage(candidate)
    assert coverage["status"] == "blocked"
    assert any("opaque" in item["issue"] for item in coverage["missing_material"])


def test_p0_numeric_closure_accepts_explicit_unknown_asr_scale_with_null_value():
    raw = "r$ 2"
    candidate = _candidate(
        raw=raw,
        number=_number(
            raw,
            value=None,
            unit_kind="currency",
            unit="BRL unknown ASR scale",
            role="other",
        ),
        caveats=["Raw r$ 2 is retained verbatim; ASR scale and unit are unknown."],
    )
    coverage = candidate_numeric_coverage(candidate)
    assert coverage["status"] == "pass"
    assert coverage["mentions"][0]["disposition"] == "covered_unknown_asr"


def test_p0_numeric_closure_accepts_bare_unknown_asr_scale_only_when_explicit():
    raw = "10000"
    candidate = _candidate(
        raw=raw,
        number=_number(
            raw,
            value=None,
            unit_kind="currency",
            unit="unknown ASR currency scale",
            role="other",
        ),
        caveats=["Raw 10000 is retained verbatim; ASR currency scale is unknown."],
    )
    coverage = candidate_numeric_coverage(candidate)
    assert coverage["status"] == "pass"
    assert coverage["mentions"][0]["disposition"] == "covered_unknown_asr"


def test_p0_numeric_closure_requires_inferred_status_and_caveat_for_asr_decimal():
    candidate = _candidate(
        raw="030%",
        number=_number("030%", value=0.30, unit_kind="percent", unit="percent", role="result"),
    )
    blocked = candidate_numeric_coverage(candidate)
    assert blocked["status"] == "blocked"
    candidate["numbers"][0]["value_status"] = "inferred"
    candidate["caveats"] = ["ASR raw 030% is retained verbatim and interpreted as 0.30%."]
    covered = candidate_numeric_coverage(candidate)
    assert covered["status"] == "pass"
    assert covered["mentions"][0]["disposition"] == "covered_asr_ambiguous"


def test_p0_numeric_closure_rejects_typed_record_plus_opaque_shadow():
    candidate = _candidate(
        raw="R$ 100",
        number=_number("R$ 100", value=100, unit_kind="currency", unit="BRL", role="result"),
    )
    candidate["numbers"].append(
        _number("R$ 100", value=None, unit_kind="count", unit="count", role="other")
    )
    coverage = candidate_numeric_coverage(candidate)
    assert coverage["status"] == "blocked"
    assert any(item["disposition"] == "duplicate_opaque_record" for item in coverage["missing_material"])


def test_p0_numeric_closure_allows_context_typed_k_suffix_as_currency():
    candidate = _candidate(
        raw="700k",
        number=_number("700k", value=700, unit_kind="currency", unit="mil BRL", role="result"),
    )
    coverage = candidate_numeric_coverage(candidate)
    assert coverage["status"] == "pass"


def test_numeric_coverage_projection_ignores_classifier_evolution_not_source_binding():
    old = [{
        "candidate_id": "episode-G001",
        "record_count": 1,
        "mentions": [{
            "segment_id": "episode-transcript-1",
            "layer": "minimal",
            "raw": "R$ 100",
            "canonical": "100",
            "kind": "currency",
            "record_index": 0,
            "record": {"raw": "R$ 100", "value": None},
            "disposition": "covered",
            "severity": None,
        }],
    }]
    current = load_json_copy(old)
    current[0]["mentions"][0].update({
        "disposition": "missing_material",
        "severity": "hard_blocker",
    })
    assert numeric_coverage_source_projection(old) == numeric_coverage_source_projection(current)
    current[0]["mentions"][0]["record"]["raw"] = "R$ 200"
    assert numeric_coverage_source_projection(old) != numeric_coverage_source_projection(current)


def test_calibration_decision_compiles_to_merged_ledger_without_evidence_pollution():
    manifest = {
        "episode_video_id": "episode",
        "candidates": [{"candidate_id": "episode-G001"}],
        "source_dispositions": [{
            "segment_id": "episode-transcript-1",
            "chunk_number": 1,
            "disposition": "excluded",
            "candidate_ids": [],
            "reason_code": "low_signal",
            "reason_reference": None,
            "reason": "Initial authoring disposition.",
        }],
        "calibration_decisions": [{
            "calibration_id": "cal-1",
            "candidate_id": "episode-G001",
            "source_equivalent_duplicate": True,
            "proposition_equivalent": True,
            "numeric_anchor_match": True,
            "duplicate_source_segment_ids": ["episode-transcript-1"],
            "canonical_source_segment_ids": ["episode-transcript-2"],
            "justification": "Same proposition and numeric anchor.",
        }],
    }
    payload = manifest_to_compact_payload(manifest)
    decision = payload["ledger_decisions"][0]
    assert payload["calibration_decisions"] == manifest["calibration_decisions"]
    assert decision["disposition"] == "merged"
    assert decision["candidate_ids"] == ["episode-G001"]
    assert decision["reason_reference"] == "episode-G001"
    assert decision["reason"].startswith("source_equivalent_duplicate:cal-1:")


def test_calibration_coverage_accepts_validated_merged_duplicate_without_candidate_evidence():
    candidate = _candidate(
        raw="R$ 100",
        number=_number("R$ 100", value=100, unit_kind="currency", unit="BRL", role="result"),
    )
    candidate["evidence"]["minimal_quote"][0]["segment_id"] = "episode-transcript-2"
    calibration = {
        "minimum_required": 1,
        "tests": [{
            "calibration_id": "cal-1",
            "segment_ids": ["episode-transcript-1"],
            "quote_verbatim": "R$ 100",
        }],
    }
    ledger = [{
        "segment_id": "episode-transcript-1",
        "disposition": "merged",
        "candidate_ids": ["episode-G001"],
        "reason_code": "duplicate_of",
        "reason_reference": "episode-G001",
        "reason": "source_equivalent_duplicate:cal-1: validated.",
    }]
    result = calibration_coverage(calibration, [candidate], ledger)
    assert result["status"] == "pass"
    assert result["tests"][0]["semantic_candidate_ids"] == ["episode-G001"]


def _impact_candidate(candidate_id: str, segment_id: str, claim: str) -> dict:
    return {
        "candidate_id": candidate_id,
        "source_claim": claim,
        "takeaway_applicavel": claim,
        "numbers": [],
        "caveats": [],
        "evidence": {
            "minimal_quote": [{"segment_id": segment_id, "quote_verbatim": claim}],
            "support_segments": [],
            "context_range": {"segment_start": 0, "segment_end": 0},
        },
    }


def _impact_state() -> dict:
    candidate = _impact_candidate("episode-G001", "episode-transcript-1", "Before claim")
    return {
        "transcript": [
            {"segment_id": "episode-transcript-1", "clean_index": 0},
            {"segment_id": "episode-transcript-2", "clean_index": 1},
        ],
        "signals": [
            {"segment_id": "episode-transcript-1", "clean_index": 0, "signal_types": ["number"]},
            {"segment_id": "episode-transcript-2", "clean_index": 1, "signal_types": ["number"]},
        ],
        "calibration": {"minimum_required": 0, "tests": []},
        "reviews": {"chunk_001_review.json": {
            "candidates": [candidate],
            "ledger_decisions": [
                {"segment_id": "episode-transcript-1", "disposition": "captured", "candidate_ids": ["episode-G001"], "reason": "Evidence."},
                {"segment_id": "episode-transcript-2", "disposition": "excluded", "candidate_ids": [], "reason_code": "low_signal", "reason": "Reviewed."},
            ],
        }},
    }


def _audit_for_g1() -> dict:
    return {
        "episode_video_id": "episode",
        "findings": [{
            "finding_id": "F001",
            "category": "numeric_coverage_and_semantics",
            "candidate_ids": ["episode-G001"],
            "segment_range": [0, 0],
            "required_action": "Correct the numeric candidate.",
        }],
    }


def test_dependency_closed_remediation_keeps_local_change_on_delta_route():
    state = _impact_state()
    after = load_json_copy(state["reviews"])
    after["chunk_001_review.json"]["candidates"][0]["source_claim"] = "After claim"
    closure = remediation_impact_closure(state, after, _audit_for_g1())
    assert closure["artifact_mode"] == "delta"
    assert closure["candidate_ids"] == ["episode-G001"]
    assert closure["full_dossier_reasons"] == []


def test_dependency_closed_remediation_preselects_full_dossier_for_unrelated_change():
    state = _impact_state()
    after = load_json_copy(state["reviews"])
    after["chunk_001_review.json"]["candidates"].append(
        _impact_candidate("episode-G002", "episode-transcript-2", "Unrelated claim")
    )
    closure = remediation_impact_closure(state, after, _audit_for_g1())
    assert closure["artifact_mode"] == "full_dossier"
    assert "changed_candidate_outside_findings:episode-G002" in closure["full_dossier_reasons"]


def load_json_copy(value: dict) -> dict:
    import copy

    return copy.deepcopy(value)


def test_materialized_verdict_closes_matching_sol_span(tmp_path: Path):
    video_id = "episode"
    artifact = tmp_path / "dossier.json"
    write_json(artifact, {"kind": "fixture"})
    request = build_audit_request(video_id, artifact, phase="reaudit")
    write_audit_request(tmp_path, request)
    write_json(tmp_path / "episode_fast_session.json", {
        "schema_version": "1.4.0",
        "episode_video_id": video_id,
        "started_at": "2026-07-18T10:00:00+00:00",
        "events": [],
        "operation_counts": {},
        "semantic_spans": [{
            "phase": "final_sol_reaudit",
            "state": "running",
            "started_at": "2026-07-18T10:01:00+00:00",
            "ended_at": None,
            "elapsed_ms": None,
        }],
    })
    materialize_audit_envelope(tmp_path, video_id, {
        "episode_video_id": video_id,
        "audit_route": "final_model_review",
        "reviewer_model": "gpt-5.6-sol",
        "reasoning_effort": "high",
        "status": "passed",
        "findings": [],
    })
    span = load_json(tmp_path / "episode_fast_session.json")["semantic_spans"][0]
    assert span["state"] == "completed"
    assert span["ended_at"] is not None
    assert span["elapsed_ms"] >= 0


def test_starting_new_semantic_phase_closes_prior_phase_without_overlap(tmp_path: Path):
    video_id = "episode"
    write_json(tmp_path / "episode_fast_session.json", {
        "schema_version": "1.4.0",
        "episode_video_id": video_id,
        "started_at": "2026-07-18T10:00:00+00:00",
        "events": [],
        "operation_counts": {},
        "semantic_spans": [{
            "phase": "semantic_reading_and_authoring",
            "state": "running",
            "started_at": "2026-07-18T10:00:00+00:00",
            "ended_at": None,
            "elapsed_ms": None,
        }],
    })
    final_span = mark_semantic_phase(tmp_path, video_id, "final_sol_audit", "start")
    spans = load_json(tmp_path / "episode_fast_session.json")["semantic_spans"]
    assert spans[0]["state"] == "completed"
    assert spans[0]["ended_at"] == final_span["started_at"]
    assert spans[1]["state"] == "running"


def test_existing_final_phase_reconciles_prior_open_span_to_its_start(tmp_path: Path):
    video_id = "episode"
    write_json(tmp_path / "episode_fast_session.json", {
        "schema_version": "1.4.0",
        "episode_video_id": video_id,
        "started_at": "2026-07-18T10:00:00+00:00",
        "events": [],
        "operation_counts": {},
        "semantic_spans": [
            {
                "phase": "semantic_reading_and_authoring",
                "state": "running",
                "started_at": "2026-07-18T10:00:00+00:00",
                "ended_at": None,
                "elapsed_ms": None,
            },
            {
                "phase": "final_sol_audit",
                "state": "running",
                "started_at": "2026-07-18T10:05:00+00:00",
                "ended_at": None,
                "elapsed_ms": None,
            },
        ],
    })
    start_semantic_phase_if_absent(tmp_path, video_id, "final_sol_audit")
    spans = load_json(tmp_path / "episode_fast_session.json")["semantic_spans"]
    assert spans[0]["state"] == "completed"
    assert spans[0]["ended_at"] == spans[1]["started_at"]
    assert spans[0]["elapsed_ms"] == 300000.0
    assert spans[1]["state"] == "running"


def test_semantic_workbench_honors_merged_calibration_candidate_ids():
    workbench = semantic_coverage_workbench(
        [{"clean_index": 0, "segment_id": "episode-transcript-1", "text": "Cold open duplicate."}],
        [],
        [],
        {"tests": []},
        [{
            "segment_id": "episode-transcript-1",
            "disposition": "merged",
            "candidate_ids": ["episode-G001"],
            "reason_code": "duplicate_of",
            "reason_reference": "episode-G001",
        }],
    )
    assert workbench["coverage_blocks"][0]["state"] == "merged"
    assert workbench["coverage_blocks"][0]["candidate_ids"] == ["episode-G001"]
    assert workbench["summary"]["unreviewed_segments"] == 0
