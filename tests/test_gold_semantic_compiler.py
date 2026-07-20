from __future__ import annotations

import json
from pathlib import Path

from scripts.gold_semantic_compiler import (
    benchmark_replay,
    build_audit_plan,
    build_shard_requests,
    compile_shards_cached,
    plan_shards,
    replay_adapter,
    semantic_hash,
    validate_calibration_bindings,
    validate_and_reduce,
    validate_ledger_groups,
    validate_shard_plan,
)


def _transcript(video_id: str = "episode", count: int = 12) -> list[dict]:
    return [
        {
            "segment_id": f"{video_id}-transcript-{index + 1:04d}",
            "clean_index": index,
            "start_seconds": float(index * 60),
            "duration_seconds": 60.0,
            "text": f"Segmento {index} com evidencia literal.",
        }
        for index in range(count)
    ]


def _candidate(video_id: str, number: int, index: int, **overrides: object) -> dict:
    value = {
        "candidate_id": f"{video_id}-G{number:03d}",
        "chunk_id": f"{video_id}-gold-chunk-001",
        "title": "Titulo de teste source backed",
        "type": "principle",
        "themes": ["copywriting"],
        "subthemes": [],
        "process_tags": ["process-copy"],
        "source_claim": "Claim source backed para o teste.",
        "takeaway_applicavel": "Takeaway source backed suficientemente detalhado para o teste.",
        "context": {"episode_video_id": video_id, "source_kind": "transcript"},
        "reported_case": False,
        "causal_certainty": "not_applicable",
        "claim_risk": "low",
        "numbers": [],
        "steps": [],
        "conditions": [],
        "caveats": [],
        "relations": {"parent_candidate_id": None, "child_candidate_ids": []},
        "minimal_clean_indexes": [index],
        "support_clean_indexes": [],
    }
    value.update(overrides)
    return value


def test_shard_plan_owns_every_segment_once_and_overlap_is_context_only():
    transcript = _transcript(count=12)
    shards = plan_shards(
        "episode", transcript, target_seconds=180, max_segments=4, overlap_segments=2
    )
    assert validate_shard_plan(transcript, shards) == []
    owned = [segment_id for shard in shards for segment_id in shard.core_segment_ids]
    assert owned == [item["segment_id"] for item in transcript]
    assert len(owned) == len(set(owned))
    assert sum(len(shard.context_segment_ids) for shard in shards) > len(transcript)
    requests = build_shard_requests("episode", transcript, shards)
    serialized = json.dumps(requests)
    assert "episode-G001" not in serialized
    assert "approved_gold_replay" not in serialized


def test_replay_reducer_preserves_candidates_and_verbatim_proofs():
    video_id = "episode"
    transcript = _transcript(video_id, 6)
    candidates = [_candidate(video_id, 1, 0), _candidate(video_id, 2, 4)]
    shards = plan_shards(video_id, transcript, target_seconds=180, max_segments=3)
    results = [replay_adapter(shard, transcript, candidates) for shard in shards]
    reduced = validate_and_reduce(transcript, results)
    assert reduced["errors"] == []
    assert reduced["candidate_projection"] == candidates
    assert len(reduced["proof_graph"]["evidence_edges"]) == 2
    assert all(
        atom["evidence"][0]["quote_verbatim"]
        == transcript[atom["evidence"][0]["clean_index"]]["text"]
        for atom in reduced["atoms"]
    )


def test_cache_second_pass_is_hit_only_and_does_not_rewrite(tmp_path):
    video_id = "episode"
    transcript = _transcript(video_id, 4)
    candidates = [_candidate(video_id, 1, 0)]
    shards = plan_shards(video_id, transcript, target_seconds=120, max_segments=2)
    cache = tmp_path / "cache"
    compile_one = lambda shard: replay_adapter(shard, transcript, candidates)
    first, first_stats = compile_shards_cached(
        shards,
        cache_dir=cache,
        adapter_name="replay",
        prompt_version="v1",
        model_version="none",
        workers=2,
        compile_one=compile_one,
    )
    mtimes = {path.name: path.stat().st_mtime_ns for path in cache.glob("*.json")}
    second, second_stats = compile_shards_cached(
        shards,
        cache_dir=cache,
        adapter_name="replay",
        prompt_version="v1",
        model_version="none",
        workers=2,
        compile_one=compile_one,
    )
    assert first_stats == {"hits": 0, "misses": len(shards)}
    assert second_stats == {"hits": len(shards), "misses": 0}
    assert semantic_hash(first) == semantic_hash(second)
    assert mtimes == {path.name: path.stat().st_mtime_ns for path in cache.glob("*.json")}


def test_reducer_rejects_non_verbatim_proof_and_asymmetric_relation():
    video_id = "episode"
    transcript = _transcript(video_id, 3)
    parent = _candidate(
        video_id, 1, 0,
        relations={"parent_candidate_id": None, "child_candidate_ids": [f"{video_id}-G002"]},
    )
    child = _candidate(video_id, 2, 1)
    shards = plan_shards(video_id, transcript, target_seconds=500)
    result = replay_adapter(shards[0], transcript, [parent, child])
    result["atoms"][0]["evidence"][0]["quote_verbatim"] = "fabricado"
    reduced = validate_and_reduce(transcript, [result])
    assert any("non-verbatim" in error for error in reduced["errors"])
    assert any("asymmetric relation" in error for error in reduced["errors"])


def test_audit_plan_includes_all_risk_and_samples_low_risk_deterministically():
    video_id = "episode"
    transcript = _transcript(video_id, 6)
    candidates = [
        _candidate(video_id, 1, 0, numbers=[{"raw": "1"}]),
        _candidate(video_id, 2, 1, type="framework", steps=["Passo"]),
        _candidate(video_id, 3, 2),
        _candidate(video_id, 4, 3),
    ]
    shard = plan_shards(video_id, transcript, target_seconds=1000)[0]
    reduced = validate_and_reduce(transcript, [replay_adapter(shard, transcript, candidates)])
    plan = build_audit_plan(
        reduced,
        [{"semantic_candidate_ids": [f"{video_id}-G003"]}],
        [{"items": [{"candidate_id": f"{video_id}-G004"}]}],
    )
    selected = {
        item["candidate_id"]
        for item in plan["high_risk_candidates"] + plan["sampled_low_risk_candidates"]
    }
    assert selected == {candidate["candidate_id"] for candidate in candidates}
    assert plan["limitations"]


def test_calibration_and_ledger_bindings_are_structural_gates():
    video_id = "episode"
    transcript = _transcript(video_id, 3)
    candidate = _candidate(video_id, 1, 0)
    shard = plan_shards(video_id, transcript, target_seconds=1000)[0]
    reduced = validate_and_reduce(
        transcript, [replay_adapter(shard, transcript, [candidate])]
    )
    calibration_errors = validate_calibration_bindings(
        [
            {
                "calibration_id": "c1", "clean_indexes": [0],
                "semantic_candidate_ids": [candidate["candidate_id"]],
            },
            {
                "calibration_id": "c2", "clean_indexes": [0],
                "semantic_candidate_ids": [f"{video_id}-G999"],
            },
        ],
        transcript,
        {candidate["candidate_id"]},
    )
    assert any("duplicates target" in error for error in calibration_errors)
    assert any("missing semantic candidate" in error for error in calibration_errors)
    ledger_errors = validate_ledger_groups(
        [["captured", [candidate["candidate_id"]], None, None, [2]]],
        transcript,
        reduced,
    )
    assert any("does not prove" in error for error in ledger_errors)


def _write_dossier(path: Path) -> None:
    video_id = "fixture"
    transcript = _transcript(video_id, 4)
    candidate = _candidate(video_id, 1, 0)
    columns = list(candidate)
    records = [
        {
            "record_type": "header",
            "episode_video_id": video_id,
            "segment_count": len(transcript),
            "candidate_count": 1,
            "transcript_columns": [
                "clean_index", "start_seconds", "duration_seconds", "text",
                "ledger_disposition", "ledger_candidate_ids", "ledger_reason_code",
                "ledger_reason_reference",
            ],
            "candidate_columns": columns,
            "audit_warnings": [],
        },
        {"record_type": "candidate", "value": [candidate[key] for key in columns]},
        {
            "record_type": "calibration",
            "value": {
                "calibration_id": "c1", "clean_indexes": [0],
                "semantic_candidate_ids": [candidate["candidate_id"]],
            },
        },
        {
            "record_type": "transcript_block",
            "value": [
                [item["clean_index"], item["start_seconds"], item["duration_seconds"], item["text"], "captured", [candidate["candidate_id"]], None, None]
                for item in transcript
            ],
        },
    ]
    records.append({"record_type": "footer", "content_semantic_sha256": semantic_hash(records)})
    path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in records) + "\n",
        encoding="utf-8",
    )


def test_replay_benchmark_labels_semantics_pending_and_is_lossless(tmp_path):
    dossier = tmp_path / "dossier.jsonl"
    _write_dossier(dossier)
    report = benchmark_replay(dossier, tmp_path / "out", workers=2, target_seconds=120)
    assert report["quality_claim"] == "mechanics_validated_semantics_pending"
    assert report["semantic_independence"] is False
    assert report["quality"]["candidate_ids_equal"] is True
    assert report["quality"]["exact_candidate_count"] == 1
    assert report["cache"]["warm"]["misses"] == 0
    assert report["adoption_gate"]["production_ready"] is False
