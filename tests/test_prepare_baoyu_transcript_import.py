import json

from scripts.prepare_baoyu_transcript_import import (
    baoyu_payload,
    browser_payload,
    timestamp_seconds,
)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_timestamp_seconds_supports_long_form():
    assert timestamp_seconds("1:02:03") == 3723


def test_baoyu_payload_preserves_source_language(tmp_path):
    directory = tmp_path / "vturb" / "episode"
    write_json(directory / "meta.json", {"videoId": "abcdefghijk", "language": {"code": "pt"}})
    write_json(directory / "transcript-raw.json", [
        {"start": 0.1, "duration": 2.3, "text": "Olá"},
    ])
    payload = baoyu_payload(tmp_path, "abcdefghijk", "vturb/episode")
    assert payload["language"] == "pt"
    assert payload["segments"][0]["duration_seconds"] == 2.3


def test_browser_payload_derives_missing_durations(tmp_path):
    source = tmp_path / "capture.json"
    write_json(source, {
        "video_id": "abcdefghijk", "language": "en", "source": "youtube_transcript_panel",
        "segments": [
            {"timestamp": "0:00", "text": "First"},
            {"timestamp": "0:07", "text": "Second"},
        ],
    })
    payload = browser_payload("abcdefghijk", source)
    assert payload["segments"][0]["duration_seconds"] == 7.0
    assert payload["provider"] == "youtube_transcript_panel"
