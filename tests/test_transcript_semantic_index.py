import json
from pathlib import Path

from scripts.gold_extraction_common import load_json, write_json
from scripts.reprocess_gold_episode import prepare_episode
from scripts.run_gold_episode_fast import build_compact_reading_context, build_reading_context
from scripts.transcript_semantic_index import (
    INDEX_ALGORITHM_VERSION,
    build_semantic_index,
    ensure_semantic_index,
    semantic_index_paths,
    semantic_index_state,
    semantic_navigation_summary,
)


def seed_episode(root: Path, video_id: str = "semantic-index") -> list[dict]:
    raw = root / "raw" / "youtube" / video_id
    processed = root / "processed" / video_id
    exports = root / "exports"
    raw.mkdir(parents=True)
    processed.mkdir(parents=True)
    exports.mkdir(parents=True, exist_ok=True)
    source_segments = [
        {
            "start_seconds": 0,
            "duration_seconds": 4,
            "text": "Primeiro mostramos o mecanismo em cinco segundos, sem alterar a frustração original.",
        },
        {
            "start_seconds": 4,
            "duration_seconds": 4,
            "text": "Antes eram 30 mil e depois foram 50 mil em vendas.",
        },
        {
            "start_seconds": 8,
            "duration_seconds": 4,
            "text": "Segundo o entrevistado, esse foi um caso relatado e o resultado pode variar.",
        },
        {
            "start_seconds": 12,
            "duration_seconds": 4,
            "text": "Como que você mediu esse resultado?",
        },
        {
            "start_seconds": 16,
            "duration_seconds": 4,
            "text": "Clique no link da descrição para conhecer nosso curso.",
        },
    ]
    write_json(raw / "metadata.json", {
        "youtube_video_id": video_id,
        "duration_seconds": 20,
        "transcript_status": "available",
    })
    write_json(raw / "transcript_original.json", {
        "youtube_video_id": video_id,
        "transcript_status": "available",
        "segments": source_segments,
    })
    write_json(processed / "insights_v2.json", {"frozen": True})
    write_json(exports / "curated_insights.json", {"frozen": True})
    write_json(exports / "insights_v2_master.json", {"frozen": True})
    return source_segments


def test_preparation_builds_current_index_outside_gold_and_preserves_verbatim(tmp_path):
    video_id = "semantic-index"
    seed_episode(tmp_path, video_id)

    prepared = prepare_episode(video_id, tmp_path)
    clean = load_json(
        tmp_path / "processed" / video_id / "gold_extraction" / "transcript_clean.json"
    )["segments"]
    index_path, status_path = semantic_index_paths(tmp_path, video_id)
    state = semantic_index_state(video_id, tmp_path, clean)

    assert prepared["semantic_index"]["status"] == "ready"
    assert prepared["semantic_index"]["reused"] is False
    assert index_path.parent == tmp_path / "processed" / video_id
    assert index_path.parent != tmp_path / "processed" / video_id / "gold_extraction"
    assert index_path.exists() and status_path.exists()
    assert state["current"] is True
    assert load_json(status_path)["algorithm_version"] == INDEX_ALGORITHM_VERSION
    indexed_segments = [
        segment
        for unit in state["units"]
        for segment in unit["verbatim_segments"]
    ]
    assert [item["text"] for item in indexed_segments] == [item["text"] for item in clean]
    assert "frustração" in indexed_segments[0]["text"]


def test_index_surfaces_numeric_trajectory_mechanism_caveat_roles_and_boundaries():
    video_id = "episode"
    segments = [
        {
            "segment_id": f"{video_id}-transcript-{index + 1:04d}",
            "clean_index": index,
            "start_seconds": index * 4,
            "duration_seconds": 4,
            "text": text,
        }
        for index, text in enumerate([
            "Primeiro explicamos o mecanismo e depois mostramos o teste de cinco segundos.",
            "Antes eram 30 mil e depois foram 50 mil em vendas.",
            "Segundo ele, foi um caso relatado e o resultado pode variar.",
            "Como que voce mediu esse resultado?",
            "Clique no link da descricao para conhecer nosso curso.",
        ])
    ]
    built = build_semantic_index(video_id, segments, chunks=[segments[:1], segments[1:]])

    cues = {cue for unit in built["units"] for cue in unit["cues"]}
    raws = [number["raw"] for unit in built["units"] for number in unit["numbers"]]
    written_raws = [
        number["raw"]
        for unit in built["units"]
        for number in unit["written_number_mentions"]
    ]
    roles = {unit["speaker_role"] for unit in built["units"]}

    assert {"mechanism", "sequence", "comparison", "outcome", "caveat"} <= cues
    assert "30 mil" in raws and "50 mil" in raws
    assert "cinco segundos" in written_raws
    assert {"interviewer", "promo"} <= roles
    assert any(unit["unit_type"] == "numeric_trajectory" for unit in built["units"])
    assert any(unit["crosses_chunk_boundary"] for unit in built["units"])
    assert built["footer"]["units_semantic_sha256"]


def test_ensure_reuses_identical_index_and_refreshes_stale_source(tmp_path):
    video_id = "reuse"
    segments = [{
        "segment_id": f"{video_id}-transcript-0001",
        "clean_index": 0,
        "start_seconds": 0,
        "duration_seconds": 5,
        "text": "Antes eram 10 vendas e depois 20 vendas.",
    }]

    first = ensure_semantic_index(video_id, tmp_path, segments, chunks=[segments])
    index_path, _status_path = semantic_index_paths(tmp_path, video_id)
    before_bytes = index_path.read_bytes()
    before_mtime = index_path.stat().st_mtime_ns
    second = ensure_semantic_index(video_id, tmp_path, segments, chunks=[segments])

    assert first["reused"] is False
    assert second["reused"] is True
    assert index_path.read_bytes() == before_bytes
    assert index_path.stat().st_mtime_ns == before_mtime

    changed = [{**segments[0], "text": "Antes eram 10 vendas e depois 25 vendas."}]
    refreshed = ensure_semantic_index(video_id, tmp_path, changed, chunks=[changed])
    assert refreshed["reused"] is False
    assert refreshed["source_semantic_sha256"] != first["source_semantic_sha256"]
    assert index_path.read_bytes() != before_bytes


def test_read_only_summary_never_backfills_missing_index_or_changes_gold(tmp_path):
    video_id = "protected"
    seed_episode(tmp_path, video_id)
    prepare_episode(video_id, tmp_path)
    out = tmp_path / "processed" / video_id / "gold_extraction"
    index_path, status_path = semantic_index_paths(tmp_path, video_id)
    index_path.unlink()
    status_path.unlink()
    before = {path.relative_to(out): path.read_bytes() for path in out.rglob("*") if path.is_file()}
    transcript = load_json(out / "transcript_clean.json")["segments"]

    summary = semantic_navigation_summary(video_id, tmp_path, transcript)

    after = {path.relative_to(out): path.read_bytes() for path in out.rglob("*") if path.is_file()}
    assert summary["status"] == "missing"
    assert not index_path.exists() and not status_path.exists()
    assert before == after


def test_fast_contexts_consume_navigation_summary_without_duplicate_verbatim(tmp_path):
    video_id = "contexts"
    seed_episode(tmp_path, video_id)
    prepare_episode(video_id, tmp_path)

    slab = build_reading_context(video_id, tmp_path)
    compact = build_compact_reading_context(video_id, tmp_path)
    navigation = compact["header"]["transcript_semantic_index"]

    assert slab["transcript_semantic_index"]["status"] == "ready"
    assert navigation["status"] == "ready"
    assert navigation["authority"] == "navigation_only"
    assert navigation["navigation_units"]
    serialized_navigation = json.dumps(navigation, ensure_ascii=False)
    assert "frustração original" not in serialized_navigation
    assert compact["header"]["legacy_content_reads"] == 0
