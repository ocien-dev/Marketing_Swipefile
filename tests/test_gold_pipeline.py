import json
from pathlib import Path

from scripts.build_gold_semantic_extraction import build_from_reviews, readiness_check
from scripts.gold_extraction_common import external_audit_gate, load_json, validate_document, validate_external_audit_report, write_json
from scripts.reprocess_gold_episode import prepare_episode, raw_preflight


def seed_episode(root: Path, video_id: str) -> None:
    raw = root / "raw" / "youtube" / video_id
    processed = root / "processed" / video_id
    exports = root / "exports"
    raw.mkdir(parents=True)
    processed.mkdir(parents=True)
    exports.mkdir(parents=True)
    write_json(raw / "metadata.json", {"youtube_video_id": video_id, "duration_seconds": 40})
    write_json(raw / "transcript_original.json", {"youtube_video_id": video_id, "transcript_status": "available", "segments": [
        {"start_seconds": 0, "duration_seconds": 5, "text": "Testamos 20% de desconto."},
        {"start_seconds": 5, "duration_seconds": 5, "text": "Antes era 10% e depois foi 20%."},
        {"start_seconds": 10, "duration_seconds": 5, "text": "Primeiro faz o teste e depois mede."},
    ]})
    write_json(processed / "insights_v2.json", {"frozen": True})
    write_json(exports / "curated_insights.json", {"frozen": True})
    write_json(exports / "insights_v2_master.json", {"frozen": True})


def write_valid_review(root: Path, video_id: str, *, steps: list[str] | None = None) -> Path:
    out = root / "processed" / video_id / "gold_extraction"
    status = load_json(out / "gold_extraction_status.json")
    chunk = status["chunks"][0]
    transcript = load_json(out / "transcript_clean.json")["segments"]
    citations = [{"segment_id": item["segment_id"]} for item in transcript]
    review = {
        "schema_version": "1.0.0", "episode_video_id": video_id, "chunk_id": chunk["chunk_id"],
        "input_hash": chunk["input_hash"], "full_chunk_reviewed": True,
        "candidates": [{
            "candidate_id": f"{video_id}-G001", "chunk_id": chunk["chunk_id"], "title": "Teste de desconto de vinte por cento",
            "type": "playbook_step", "themes": ["copy_vsl"], "subthemes": [], "process_tags": [],
            "source_claim": "O entrevistado relatou testar desconto de 20% apos comparar uma taxa de 10%.",
            "takeaway_applicavel": "Teste o desconto isoladamente e compare com o baseline antes de aumentar o investimento.",
            "reported_case": True, "causal_certainty": "reported_attribution", "claim_risk": "medium",
            "numbers": [], "steps": list(steps) if steps is not None else ["Testar a variante de desconto."], "conditions": [], "caveats": [],
            "evidence": {"minimal_quote": citations[:2], "context_range": {}, "support_segments": citations[2:]},
            "relations": {"parent_candidate_id": None, "child_candidate_ids": []},
        }], "ledger_decisions": [],
    }
    path = out / "manual_reviews" / "chunk_001_review.json"
    write_json(path, review)
    return path


def test_raw_preflight_is_read_only_and_reports_missing_inputs(tmp_path):
    video_id = "episode"
    seed_episode(tmp_path, video_id)
    result = raw_preflight(video_id, tmp_path)
    assert result["status"] == "pass"
    assert not (tmp_path / "processed" / video_id / "gold_extraction").exists()

    (tmp_path / "raw" / "youtube" / video_id / "transcript_original.json").unlink()
    result = raw_preflight(video_id, tmp_path)
    assert result["status"] == "error"
    assert any("missing raw transcript" in error for error in result["errors"])
    assert not (tmp_path / "processed" / video_id / "gold_extraction").exists()


def test_raw_preflight_rejects_unavailable_metadata_status_without_writing(tmp_path):
    video_id = "episode"
    seed_episode(tmp_path, video_id)
    metadata_path = tmp_path / "raw" / "youtube" / video_id / "metadata.json"
    write_json(metadata_path, {"youtube_video_id": video_id, "duration_seconds": 40, "transcript_status": "unavailable"})

    result = raw_preflight(video_id, tmp_path)

    assert result["status"] == "error"
    assert "raw metadata transcript unavailable: unavailable" in result["errors"]
    assert not (tmp_path / "processed" / video_id / "gold_extraction").exists()


def test_prepare_prefers_pt_br_translation_and_preserves_original(tmp_path):
    video_id = "episode"
    seed_episode(tmp_path, video_id)
    raw = tmp_path / "raw" / "youtube" / video_id
    original_path = raw / "transcript_original.json"
    original_before = original_path.read_bytes()
    translated_path = raw / "transcript_pt_br.json"
    write_json(translated_path, {
        "youtube_video_id": video_id,
        "transcript_status": "available",
        "language": "pt-BR",
        "source_language": "en",
        "segments": [
            {"start_seconds": 0, "duration_seconds": 5, "text": "Este e o texto traduzido."},
            {"start_seconds": 5, "duration_seconds": 5, "text": "A fonte original permanece preservada."},
        ],
    })

    preflight = raw_preflight(video_id, tmp_path)
    prepared = prepare_episode(video_id, tmp_path)
    clean = load_json(tmp_path / "processed" / video_id / "gold_extraction" / "transcript_clean.json")

    assert preflight["status"] == "pass"
    assert preflight["transcript_path"] == str(translated_path)
    assert prepared["errors"] == []
    assert clean["source"] == str(translated_path)
    assert clean["segments"][0]["text"] == "Este e o texto traduzido."
    assert original_path.read_bytes() == original_before


def test_readiness_reports_missing_procedural_steps_without_writing(tmp_path):
    video_id = "episode"
    seed_episode(tmp_path, video_id)
    prepare_episode(video_id, tmp_path)
    review_path = write_valid_review(tmp_path, video_id, steps=[])
    before = {path: path.read_bytes() for path in (tmp_path / "processed" / video_id / "gold_extraction").rglob("*") if path.is_file()}

    result = readiness_check(video_id, tmp_path, review_path.parent)

    after = {path: path.read_bytes() for path in (tmp_path / "processed" / video_id / "gold_extraction").rglob("*") if path.is_file()}
    assert result["status"] == "not_ready"
    assert f"{video_id}-G001: procedural type needs steps" in result["errors"]
    assert before == after


def test_explicit_export_suffix_does_not_write_legacy_packet(tmp_path):
    video_id = "episode"
    seed_episode(tmp_path, video_id)
    prepare_episode(video_id, tmp_path)
    review_path = write_valid_review(tmp_path, video_id)

    result = build_from_reviews(video_id, tmp_path, review_path.parent, export_suffix="wave_packet")

    assert result["status"] == "awaiting_external_audit"
    assert (tmp_path / "exports" / "wave_packet" / "packet_manifest.json").exists()
    assert not (tmp_path / "exports" / f"msf_r20_piloto_{video_id}").exists()


def test_legacy_export_suffix_remains_default(tmp_path):
    video_id = "episode"
    seed_episode(tmp_path, video_id)
    prepare_episode(video_id, tmp_path)
    review_path = write_valid_review(tmp_path, video_id)

    result = build_from_reviews(video_id, tmp_path, review_path.parent)

    assert result["status"] == "awaiting_external_audit"
    assert (tmp_path / "exports" / f"msf_r20_piloto_{video_id}" / "packet_manifest.json").exists()


def test_new_finalization_snapshot_does_not_reuse_prior_passed_audit(tmp_path):
    video_id = "episode"
    seed_episode(tmp_path, video_id)
    prepare_episode(video_id, tmp_path)
    review_path = write_valid_review(tmp_path, video_id)
    out = tmp_path / "processed" / video_id / "gold_extraction"
    write_json(out / "editorial_audit_report.json", audit_payload())

    result = build_from_reviews(
        video_id,
        tmp_path,
        review_path.parent,
        executor_thread_id="executor",
        defer_packet=True,
        force_pending_external=True,
    )

    assert result["status"] == "awaiting_external_audit"
    assert load_json(out / "gold_extraction_status.json")["audit_status"] == "pending_external"
    assert load_json(out / "insights_exhaustive.json")["audit"]["status"] == "pending_external"


def test_prepare_and_build_are_resumable_and_idempotent(tmp_path):
    video_id = "episode"
    seed_episode(tmp_path, video_id)
    prepared = prepare_episode(video_id, tmp_path)
    assert prepared["errors"] == []
    out = tmp_path / "processed" / video_id / "gold_extraction"
    status = load_json(out / "gold_extraction_status.json")
    chunk = status["chunks"][0]
    transcript = load_json(out / "transcript_clean.json")["segments"]
    citations = [{"segment_id": item["segment_id"]} for item in transcript]
    review = {
        "schema_version": "1.0.0", "episode_video_id": video_id, "chunk_id": chunk["chunk_id"],
        "input_hash": chunk["input_hash"], "full_chunk_reviewed": True,
        "candidates": [{
            "candidate_id": "episode-G001", "chunk_id": chunk["chunk_id"], "title": "Teste de desconto de vinte por cento",
            "type": "test_result", "themes": ["copy_vsl", "testing_optimization"], "subthemes": [], "process_tags": ["process-copy-vsl", "process-cro-testes"],
            "source_claim": "O entrevistado relatou testar desconto de 20% apos comparar uma taxa de 10%.",
            "takeaway_applicavel": "Teste o desconto isoladamente, compare com o baseline e meca a conversao antes de escalar a variante.",
            "reported_case": True, "causal_certainty": "reported_attribution", "claim_risk": "medium",
            "numbers": [
                {"raw": "20%", "value": 20, "unit_kind": "percent", "unit": "percent", "period": None, "role": "result", "value_status": "reported", "denominator": None, "attribution_window": None},
                {"raw": "10%", "value": 10, "unit_kind": "percent", "unit": "percent", "period": None, "role": "baseline", "value_status": "reported", "denominator": None, "attribution_window": None},
            ],
            "steps": ["Testar uma variante.", "Comparar com o baseline."], "conditions": [], "caveats": ["O caso e relatado, nao uma garantia."],
            "evidence": {"minimal_quote": citations[:2], "context_range": {}, "support_segments": citations[2:]},
            "relations": {"parent_candidate_id": None, "child_candidate_ids": []},
        }], "ledger_decisions": [],
    }
    write_json(out / "manual_reviews" / "chunk_001_review.json", review)
    first = build_from_reviews(video_id, tmp_path, out / "manual_reviews", "pending_external")
    assert first["status"] == "awaiting_external_audit"
    assert first["errors"] == []
    first_status = load_json(out / "gold_extraction_status.json")
    second = build_from_reviews(video_id, tmp_path, out / "manual_reviews", "pending_external")
    second_status = load_json(out / "gold_extraction_status.json")
    assert second["errors"] == []
    assert first_status["chunks"][0]["attempts"] == second_status["chunks"][0]["attempts"]
    assert len(load_json(out / "insights_exhaustive.json")["insights"]) == 1
    rejected = build_from_reviews(video_id, tmp_path, out / "manual_reviews", "passed")
    assert rejected["status"] == "validation_failed"
    assert "passed audit must be derived from editorial_audit_report.json" in rejected["errors"]


def test_number_raw_accepts_ascii_nfkd_against_verbatim_quote():
    from scripts.gold_extraction_common import validate_numbers

    numbers = [{
        "raw": "tres conteudos por semana", "value": 3, "min_value": None, "max_value": None,
        "unit_kind": "count", "period": "per_week", "role": "cadence", "value_status": "reported",
    }]
    assert validate_numbers("candidate", numbers, ["ele postava tr\u00eas conte\u00fados por semana"]) == []


def test_number_raw_accepts_ascii_nfkd_against_mojibake_quote():
    from scripts.gold_extraction_common import validate_numbers

    numbers = [{
        "raw": "1 milhao e meio por dia", "value": 1500000, "min_value": None, "max_value": None,
        "unit_kind": "currency", "period": "per_day", "role": "budget", "value_status": "reported",
    }]
    assert validate_numbers("candidate", numbers, ["ele colocou 1 milh\u00c3\u00a3o e meio por dia"]) == []


def test_signal_inventory_recovers_mojibake_sequence_and_warning_words():
    from scripts.gold_extraction_common import signal_types

    types = signal_types("a\u00c3\u00ad depois, isso n\u00c3\u00a3o funciona")
    assert "sequence" in types
    assert "warning" in types


def audit_payload(status="passed", finding_status="resolved", reviewer_thread_id="reviewer"):
    findings = [{
        "finding_id": "F1", "severity": "minor", "status": finding_status, "category": "editorial",
        "segment_range": [0, 1], "candidate_ids": ["episode-G001"], "summary": "Clear finding.",
        "evidence": "Transcript support.", "required_action": "Apply a deterministic correction.",
    }]
    return {
        "episode_video_id": "episode", "audit_route": "external_blind_reviewer", "reviewer": "Codex reviewer",
        "reviewer_thread_id": reviewer_thread_id, "reviewer_model": "gpt-5.6-sol", "reasoning_effort": "high",
        "reviewed_at": "2026-07-11T00:00:00Z", "status": status, "summary": "Complete audit.",
        "findings": findings, "open_findings": 1 if finding_status == "open" else 0,
    }


def test_passed_audit_with_open_finding_is_rejected():
    errors = validate_external_audit_report(audit_payload(finding_status="open"), "executor")
    assert "passed external audit report has open findings" in errors


def test_recorder_rejects_passed_audit_with_open_finding(tmp_path):
    from scripts.record_gold_external_audit import record_audit

    try:
        record_audit("episode", tmp_path, audit_payload(finding_status="open"))
    except ValueError as exc:
        assert "open findings" in str(exc)
    else:
        raise AssertionError("passed audit with open finding was accepted")


def test_recorder_preserves_reviewer_provenance_and_full_finding_contract(tmp_path):
    from scripts.record_gold_external_audit import record_audit

    result = record_audit("episode", tmp_path, audit_payload())
    assert result["audit_route"] == "external_blind_reviewer"
    assert result["reviewer_thread_id"] == "reviewer"
    assert result["reviewer_model"] == "gpt-5.6-sol"
    assert result["reasoning_effort"] == "high"
    assert result["findings"][0]["required_action"]


def test_incomplete_finding_contract_is_rejected():
    report = audit_payload()
    del report["findings"][0]["required_action"]
    assert any("missing" in error for error in validate_external_audit_report(report, "executor"))


def test_valid_external_audit_report_can_complete_with_separate_reviewer(tmp_path):
    report = audit_payload()
    write_json(tmp_path / "editorial_audit_report.json", report)
    gate = external_audit_gate(tmp_path, "executor")
    assert gate["eligible_for_complete"] is True


def test_valid_final_sol_audit_can_complete_in_same_thread(tmp_path):
    report = audit_payload(reviewer_thread_id="executor")
    report["audit_route"] = "final_model_review"
    write_json(tmp_path / "editorial_audit_report.json", report)
    gate = external_audit_gate(tmp_path, "executor")
    assert gate["eligible_for_complete"] is True


def test_same_thread_audit_without_final_sol_provenance_is_rejected():
    report = audit_payload(reviewer_thread_id="executor")
    errors = validate_external_audit_report(report, "executor")
    assert "same-thread final audit requires final_model_review with gpt-5.6-sol/high or above" in errors


def test_historical_audit_remains_readable_without_new_provenance_fields():
    assert validate_external_audit_report({"episode_video_id": "legacy", "status": "passed"}, allow_legacy=True) == []


def test_open_external_finding_waits_without_failing_deterministic_validation(tmp_path):
    video_id = "episode"
    seed_episode(tmp_path, video_id)
    prepared = prepare_episode(video_id, tmp_path)
    assert prepared["errors"] == []
    out = tmp_path / "processed" / video_id / "gold_extraction"
    status = load_json(out / "gold_extraction_status.json")
    chunk = status["chunks"][0]
    transcript = load_json(out / "transcript_clean.json")["segments"]
    citations = [{"segment_id": item["segment_id"]} for item in transcript]
    review = {
        "schema_version": "1.0.0", "episode_video_id": video_id, "chunk_id": chunk["chunk_id"],
        "input_hash": chunk["input_hash"], "full_chunk_reviewed": True,
        "candidates": [{
            "candidate_id": "episode-G001", "chunk_id": chunk["chunk_id"], "title": "Teste de desconto de vinte por cento",
            "type": "test_result", "themes": ["copy_vsl", "testing_optimization"], "subthemes": [], "process_tags": [],
            "source_claim": "O entrevistado relatou testar desconto de 20% apos comparar uma taxa de 10%.",
            "takeaway_applicavel": "Teste o desconto isoladamente e compare com o baseline.",
            "reported_case": True, "causal_certainty": "reported_attribution", "claim_risk": "medium",
            "numbers": [
                {"raw": "20%", "value": 20, "unit_kind": "percent", "unit": "percent", "period": None, "role": "result", "value_status": "reported", "denominator": None, "attribution_window": None},
                {"raw": "10%", "value": 10, "unit_kind": "percent", "unit": "percent", "period": None, "role": "baseline", "value_status": "reported", "denominator": None, "attribution_window": None},
            ],
            "steps": ["Testar uma variante.", "Comparar com o baseline."], "conditions": [], "caveats": [],
            "evidence": {"minimal_quote": citations[:2], "context_range": {}, "support_segments": citations[2:]},
            "relations": {"parent_candidate_id": None, "child_candidate_ids": []},
        }], "ledger_decisions": [],
    }
    write_json(out / "manual_reviews" / "chunk_001_review.json", review)
    write_json(out / "editorial_audit_report.json", audit_payload(status="changes_requested", finding_status="open"))

    result = build_from_reviews(video_id, tmp_path, out / "manual_reviews", executor_thread_id="executor")
    document = load_json(out / "insights_exhaustive.json")
    chunks = load_json(out / "chunks" / "chunk_index.json")["chunks"]

    assert result == {"status": "awaiting_external_audit", "candidates": 1, "errors": [], "calibration": "pass"}
    assert validate_document(document, transcript, chunks) == []
    required_errors = validate_document(document, transcript, chunks, require_external_audit=True)
    assert "external audit has not passed" in required_errors
    assert "external audit has 1 open finding(s)" in required_errors
