import hashlib
from pathlib import Path

from scripts.backfill_vturb_transcripts import atomic_write_json, read_json
from scripts.dedupe_transcript_original import dedupe_episode


def test_dedupe_keeps_longest_exact_pair_and_raw_capture(tmp_path: Path):
    video_id = "abcdefghijk"
    raw = tmp_path / "raw" / "youtube" / video_id
    raw.mkdir(parents=True)
    atomic_write_json(raw / "metadata.json", {"youtube_video_id": video_id, "duration_seconds": 20})
    atomic_write_json(raw / "transcript_original.json", {
        "youtube_video_id": video_id,
        "language": "en",
        "segments": [
            {"start_seconds": 0, "duration_seconds": 0, "text": "Repeated text " * 100},
            {"start_seconds": 0, "duration_seconds": 10, "text": "Repeated text " * 100},
            {"start_seconds": 10, "duration_seconds": 10, "text": "Unique text " * 100},
        ],
    })
    atomic_write_json(raw / "transcript_pt_br.json", {
        "youtube_video_id": video_id,
        "language": "pt-BR",
        "source_transcript_sha256": "stale",
        "segments": [
            {"start_seconds": 0, "duration_seconds": 10, "text": "Texto traduzido " * 100},
            {"start_seconds": 10, "duration_seconds": 10, "text": "Texto final " * 100},
        ],
    })

    result = dedupe_episode(tmp_path, video_id)

    assert result["removed_segments"] == 1
    assert result["output_segments"] == 2
    assert (raw / "transcript_original_browser_capture.json").is_file()
    transcript = read_json(raw / "transcript_original.json")
    assert transcript["segments"][0]["duration_seconds"] == 10
    assert len(read_json(raw / "transcript_original_browser_capture.json")["segments"]) == 3
    translated = read_json(raw / "transcript_pt_br.json")
    assert translated["source_transcript_sha256"] == hashlib.sha256(
        (raw / "transcript_original.json").read_bytes()
    ).hexdigest()
    metadata = read_json(raw / "metadata.json")
    assert metadata["translation_sha256"]
    assert metadata["translation_segments"] == 2
