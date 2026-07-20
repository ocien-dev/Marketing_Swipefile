import csv
from pathlib import Path

from scripts.gold_episode_priority import CATEGORY_ORDER, build_priority_queue
from scripts.discover_vturb_youtube_videos import (
    classify_catalog,
    collect_records_and_tokens,
    duration_seconds,
    is_podcast_episode,
    read_queue,
    synchronize_queue,
)


def test_empty_categories_are_omitted_from_active_queue_order():
    queue = build_priority_queue(base_entries=[{
        "video_id": "copyonly001",
        "title": "Copy que vende",
        "duration_seconds": 100,
        "category": "copy",
        "category_label": "Copy",
        "clean_segments": 1,
    }])
    assert "quiz" in CATEGORY_ORDER
    assert queue["category_order"] == ["copy"]
    assert queue["category_labels"] == {"copy": "Copy"}


def test_collects_renderer_metadata_and_continuation():
    payload = {
        "items": [
            {
                "videoId": "abcdefghijk",
                "title": {"runs": [{"text": "VSL na prática - Segredos da Escala #164"}]},
                "lengthText": {"simpleText": "2:03:04"},
                "publishedTimeText": {"simpleText": "1 day ago"},
            },
            {"continuationCommand": {"token": "next-page"}},
        ]
    }
    records, tokens = collect_records_and_tokens(payload)
    assert records == [
        {
            "video_id": "abcdefghijk",
            "youtube_url": "https://www.youtube.com/watch?v=abcdefghijk",
            "title": "VSL na prática - Segredos da Escala #164",
            "duration_text": "2:03:04",
            "duration_seconds": 7384,
            "published_time_text": "1 day ago",
        }
    ]
    assert tokens == ["next-page"]
    assert duration_seconds("58:02") == 3482


def test_keeps_unnumbered_public_video_for_default_catalog():
    record = {"video_id": "ccccccccccc", "title": "Conversa especial da VTurb", "duration_seconds": 20}
    assert not is_podcast_episode(record)
    assert classify_catalog([record])[0]["category"] == "other"


def test_collects_current_youtube_lockup_view_model():
    payload = {
        "lockupViewModel": {
            "contentId": "lockupvid01",
            "contentType": "LOCKUP_CONTENT_TYPE_VIDEO",
            "contentImage": {"thumbnailViewModel": {"overlays": [{"thumbnailBottomOverlayViewModel": {"badges": [{"thumbnailBadgeViewModel": {"text": "2:50:58"}}]}}]}},
            "metadata": {"lockupMetadataViewModel": {
                "title": {"content": "Episódio extra sem número"},
                "metadata": {"contentMetadataViewModel": {"metadataRows": [{"metadataParts": [{"text": {"content": "1 mil visualizações"}}, {"text": {"content": "há 1 dia"}}]}]}},
            }},
        }
    }
    records, _ = collect_records_and_tokens(payload)
    assert records[0]["video_id"] == "lockupvid01"
    assert records[0]["title"] == "Episódio extra sem número"
    assert records[0]["duration_seconds"] == 10258
    assert records[0]["published_time_text"] == "há 1 dia"


def test_filters_podcast_and_applies_owner_category_order():
    records = [
        {"video_id": "aaaaaaaaaaa", "title": "Copy que vende | SDE #10", "duration_seconds": 100, "discovered_order": 2},
        {"video_id": "bbbbbbbbbbb", "title": "VSL que vende | Segredos da Escala #11", "duration_seconds": 200, "discovered_order": 1},
        {"video_id": "ccccccccccc", "title": "Tutorial avulso da VTurb", "duration_seconds": 20, "discovered_order": 3},
    ]
    assert [is_podcast_episode(item) for item in records] == [True, True, False]
    classified = classify_catalog(records[:2])
    assert [item["category"] for item in classified] == ["copy", "vsl"]


def test_sync_queue_reorders_existing_and_new_rows_by_classification(tmp_path: Path):
    queue = tmp_path / "youtube_urls.csv"
    with queue.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["source_priority", "channel_name", "youtube_url", "episode_priority", "notes"])
        writer.writeheader()
        writer.writerow({
            "source_priority": "1",
            "channel_name": "VTurb",
            "youtube_url": "https://www.youtube.com/watch?v=aaaaaaaaaaa",
            "episode_priority": "1",
            "notes": "keep me",
        })
    catalog = classify_catalog([
        {"video_id": "aaaaaaaaaaa", "youtube_url": "https://www.youtube.com/watch?v=aaaaaaaaaaa", "title": "Copy no SDE #10", "duration_seconds": 100, "discovered_order": 2, "published_time_text": ""},
        {"video_id": "bbbbbbbbbbb", "youtube_url": "https://www.youtube.com/watch?v=bbbbbbbbbbb", "title": "VSL no SDE #11", "duration_seconds": 200, "discovered_order": 1, "published_time_text": ""},
    ])
    result = synchronize_queue(queue, catalog, source_priority="1", channel_name="VTurb")
    rows = read_queue(queue)
    assert result == {"added": 1, "updated": 1, "preserved": 0, "queue_total": 2}
    assert [row["video_id"] for row in rows] == ["bbbbbbbbbbb", "aaaaaaaaaaa"]
    assert [row["episode_priority"] for row in rows] == ["1", "2"]
    assert rows[1]["notes"] == "keep me"


def test_incremental_sync_keeps_older_rows_and_adds_only_recent_novelty(tmp_path: Path):
    queue = tmp_path / "youtube_urls.csv"
    with queue.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["source_priority", "channel_name", "youtube_url", "episode_priority", "notes", "video_id", "title", "duration_seconds", "category", "category_label"])
        writer.writeheader()
        writer.writerow({"source_priority": "1", "channel_name": "VTurb", "youtube_url": "https://www.youtube.com/watch?v=oldoldold01", "episode_priority": "1", "notes": "", "video_id": "oldoldold01", "title": "Copy antiga", "duration_seconds": "100", "category": "copy", "category_label": "Copy"})
    recent = classify_catalog([
        {"video_id": "newnewnew01", "youtube_url": "https://www.youtube.com/watch?v=newnewnew01", "title": "VSL recente", "duration_seconds": 300, "discovered_order": 1, "published_time_text": ""},
    ])
    result = synchronize_queue(queue, recent, source_priority="1", channel_name="VTurb", full_catalog=False)
    rows = read_queue(queue)
    assert result["added"] == 1
    assert result["updated"] == 0
    assert {row["video_id"] for row in rows} == {"oldoldold01", "newnewnew01"}
    assert [row["video_id"] for row in rows] == ["newnewnew01", "oldoldold01"]
