import json
from pathlib import Path

from scripts.backfill_vturb_transcripts import atomic_write_json, read_json
from scripts.codex_translate_transcripts import assemble, prepare, promote


def test_codex_translation_round_trip_preserves_original(tmp_path: Path):
    video_id = "abcdefghijk"
    raw = tmp_path / "data" / "raw" / "youtube" / video_id
    raw.mkdir(parents=True)
    original = {
        "youtube_video_id": video_id,
        "language": "en",
        "transcript_status": "available",
        "segments": [
            {"start_seconds": 0, "duration_seconds": 30, "text": "Hello world."},
            {"start_seconds": 65, "duration_seconds": 30, "text": "Keep the source."},
        ],
    }
    atomic_write_json(raw / "transcript_original.json", original)
    original_bytes = (raw / "transcript_original.json").read_bytes()
    atomic_write_json(raw / "metadata.json", {"youtube_video_id": video_id, "duration_seconds": 100})
    manifest = prepare(video_id, tmp_path / "data", tmp_path / "jobs", 60, 1_000)
    batch = manifest["batches"][0]
    source = read_json(Path(batch["source"]))
    atomic_write_json(Path(batch["translation"]), {
        "translations": {unit["unit_id"]: (f"Traducao {unit['unit_id']} " * 50).strip() for unit in source["units"]}
    })

    assembled = assemble(video_id, tmp_path / "data", tmp_path / "jobs", tmp_path / "assembled")
    promoted = promote(video_id, tmp_path / "data", Path(assembled["path"]))

    assert assembled["segments"] == 2
    assert promoted["status"] == "promoted"
    assert (raw / "transcript_original.json").read_bytes() == original_bytes
    translation = json.loads((raw / "transcript_pt_br.json").read_text(encoding="utf-8"))
    assert translation["language"] == "pt-BR"
    assert translation["source_language"] == "en"
    content = read_json(tmp_path / "data" / "processed" / video_id / "content_segments.json")
    assert content["segments"][0]["text_original"].startswith("Traducao U0001")
    assert content["segments"][0]["language"] == "pt-BR"
