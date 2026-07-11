from scripts.gold_extraction_common import calibration_coverage, ledger_for_signals, normalize_relations, validate_candidate


def segment(index, text):
    return {"clean_index": index, "segment_id": f"s{index}", "text": text, "start_seconds": index * 2.0, "duration_seconds": 2.0}


def candidate(candidate_id="c1", parent=None):
    return {
        "candidate_id": candidate_id, "chunk_id": "chunk-1", "title": "Teste de desconto tardio", "type": "test_result",
        "themes": ["copy_vsl"], "subthemes": ["desconto"], "process_tags": ["process-copy-vsl"],
        "source_claim": "O desconto de 20% aumentou o ROI relatado.",
        "takeaway_applicavel": "Teste um desconto tardio separadamente e meca conversao incremental e possivel canibalizacao.",
        "context": {"episode_video_id": "v", "source_kind": "transcript"}, "reported_case": True,
        "causal_certainty": "reported_attribution", "claim_risk": "medium",
        "numbers": [{"raw": "20%", "value": 20, "min_value": None, "max_value": None, "unit_kind": "percent", "unit": "percent", "period": None, "role": "delta", "value_status": "reported", "denominator": None, "attribution_window": None}],
        "steps": [], "conditions": ["Botao exibido apos o pitch."], "caveats": ["Parte das vendas poderia ocorrer no preco cheio."],
        "evidence": {"minimal_quote": [{"segment_id": "s0", "start_seconds": 0.0, "end_seconds": 2.0, "quote_verbatim": "Desconto de 20%."}], "context_range": {"segment_start": 0, "segment_end": 1, "start_seconds": 0.0, "end_seconds": 4.0}, "support_segments": [{"segment_id": "s1", "start_seconds": 2.0, "end_seconds": 4.0, "quote_verbatim": "Aumentou o ROI."}]},
        "relations": {"parent_candidate_id": parent, "child_candidate_ids": []},
    }


def test_accepts_layered_evidence_and_normalized_number():
    assert validate_candidate(candidate(), {"s0": segment(0, "Desconto de 20%."), "s1": segment(1, "Aumentou o ROI.")}, {"chunk-1"}) == []


def test_rejects_number_not_present_in_evidence():
    item = candidate(); item["numbers"][0]["raw"] = "15%"
    assert any("raw absent" in error for error in validate_candidate(item, {"s0": segment(0, "Desconto de 20%."), "s1": segment(1, "Aumentou o ROI.")}, {"chunk-1"}))


def test_parent_relation_is_symmetrized():
    parent = candidate("parent")
    child = candidate("child", "parent")
    assert normalize_relations([parent, child]) == []
    assert parent["relations"]["child_candidate_ids"] == ["child"]


def test_relation_cycle_is_rejected():
    left = candidate("left", "right")
    right = candidate("right", "left")
    assert any("cycle" in error for error in normalize_relations([left, right]))


def test_calibration_uses_evidence_not_titles():
    item = candidate()
    calibration = {"minimum_required": 1, "tests": [{"calibration_id": "one", "segment_ids": ["s0"]}]}
    assert calibration_coverage(calibration, [item])["status"] == "pass"


def test_ledger_exclusions_receive_a_reason_category():
    signal = {"segment_id": "s1", "clean_index": 0, "signal_types": ["number"], "evidence": [{"quote_verbatim": "Visit the website to subscribe."}]}
    ledger = ledger_for_signals([signal], [])
    assert ledger[0]["reason_code"] == "promo"
