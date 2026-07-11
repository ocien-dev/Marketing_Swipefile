from scripts.reprocess_gold_episode import audit_omissions, reusable_signal_inventory, validate
from scripts.gold_extraction_common import clean_segments, chunks_for_segments, deduplicate_calibrations, discover_calibrations, sha256_json, write_json


def test_clean_segments_removes_regressive_recommendation_and_preserves_episode():
    raw = [
        {"start_seconds": 0.0, "duration_seconds": 5.0, "text": "Conteudo do episodio."},
        {"start_seconds": 5.0, "duration_seconds": 5.0, "text": "Mais conteudo do episodio."},
        {"start_seconds": 1.0, "duration_seconds": 300.0, "text": "Como Fazer R$ 5 MIL POR DIA | Podcast #12"},
    ]
    kept, removed = clean_segments(raw, 30.0, "video")
    assert len(kept) == 2
    assert len(removed) == 1
    assert removed[0]["reason"] == "implausible_segment_duration"
    assert [item["start_seconds"] for item in kept] == [0.0, 5.0]


def test_chunks_cover_each_clean_segment_once():
    segments = [{"segment_id": f"s{i}", "clean_index": i, "start_seconds": float(i * 3), "duration_seconds": 3.0, "text": "texto"} for i in range(12)]
    chunks = chunks_for_segments(segments, max_chars=130, target_seconds=10)
    assert [item["segment_id"] for chunk in chunks for item in chunk] == [item["segment_id"] for item in segments]
    assert validate(segments, chunks, [], 60.0) == []


def test_omission_inventory_reports_high_signal_without_review_destination():
    segments = [{"segment_id": "s1", "clean_index": 0, "start_seconds": 0.0, "duration_seconds": 2.0, "text": "A conversao subiu 10%."}]
    assert audit_omissions(segments, set()) == [{"segment_id": "s1", "text": "A conversao subiu 10%."}]


def test_calibration_discovery_is_episode_specific_and_proportional():
    segments = [
        {"segment_id": "s1", "clean_index": 0, "start_seconds": 0.0, "duration_seconds": 2.0, "text": "Testamos 20% de desconto."},
        {"segment_id": "s2", "clean_index": 1, "start_seconds": 2.0, "duration_seconds": 2.0, "text": "Antes era 10% e depois foi 20%."},
        {"segment_id": "s3", "clean_index": 2, "start_seconds": 4.0, "duration_seconds": 2.0, "text": "Primeiro faz o teste e depois mede."},
    ]
    calibration = discover_calibrations(segments, 7200.0)
    assert calibration["minimum_required"] == 3
    assert calibration["generated_count"] >= 3


def test_calibration_dedup_merges_overlapping_signal_and_repeated_targets():
    candidates = [
        {"calibration_id": "signal-a", "kind": "quantitative_claim", "segment_ids": ["s1"], "segment_range": [1, 1], "trigger_types": ["number"], "quote_verbatim": "A"},
        {"calibration_id": "repeated-a", "kind": "repeated_numeric_claim", "segment_ids": ["s1", "s2"], "segment_range": [1, 2], "trigger_types": ["number"], "quote_verbatim": "A"},
    ]
    result = deduplicate_calibrations(candidates)
    assert len(result) == 1
    assert result[0]["segment_ids"] == ["s1"]
    assert result[0]["deduplicated_segment_ids"] == ["s2"]
    assert result[0]["deduplicated_count"] == 2


def test_calibration_dedup_keeps_same_number_in_distinct_claims_separate():
    candidates = [
        {"calibration_id": "price", "kind": "quantitative_claim", "segment_ids": ["s1"], "segment_range": [1, 1], "trigger_types": ["number"], "semantic_key": "quantitative_claim|price 10", "quote_verbatim": "Price is 10."},
        {"calibration_id": "experts", "kind": "quantitative_claim", "segment_ids": ["s2"], "segment_range": [2, 2], "trigger_types": ["number"], "semantic_key": "quantitative_claim|10 experts", "quote_verbatim": "We have 10 experts."},
    ]
    result = deduplicate_calibrations(candidates)
    assert [item["segment_ids"] for item in result] == [["s1"], ["s2"]]


def test_rerun_reuses_compatible_signal_inventory(tmp_path):
    clean = [{"segment_id": "s1", "clean_index": 0, "text": "Teste", "start_seconds": 0.0, "duration_seconds": 2.0}]
    transcript_hash = sha256_json(clean)
    write_json(tmp_path / "signal_inventory.json", {"signals": [{"segment_id": "s1", "clean_index": 0, "signal_types": ["experiment"], "evidence": []}]})
    assert reusable_signal_inventory(tmp_path, transcript_hash, {"input_transcript_hash": transcript_hash}, clean)[0]["segment_id"] == "s1"
