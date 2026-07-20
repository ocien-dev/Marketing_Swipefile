import json
import unittest
from pathlib import Path

from scripts.backfill_vturb_transcripts import acquisition_processing_status
from scripts.reconcile_transcript_roots import artifact_paths, validate_source_set


class ReconcileTranscriptRootsTests(unittest.TestCase):
    def test_validate_source_set_requires_available_nonempty_and_matching_ids(self):
        video_id = "abc123def45"
        payloads = {
            "metadata": {"youtube_video_id": video_id, "transcript_status": "available"},
            "transcript_original": {"youtube_video_id": video_id, "segments": [{"text": "ok"}]},
            "content_segments": {"episode_video_id": video_id, "segments": [{"text": "ok"}]},
        }
        raw = {name: json.dumps(value).encode("utf-8") for name, value in payloads.items()}
        hashes = validate_source_set(video_id, raw)
        self.assertEqual(set(hashes), set(payloads))

    def test_artifact_paths_keep_optional_translation_separate(self):
        paths = artifact_paths(Path("C:/tmp"), "abc123def45")
        self.assertEqual(paths["transcript_original"].name, "transcript_original.json")
        self.assertEqual(paths["transcript_pt_br"].name, "transcript_pt_br.json")
        self.assertEqual(paths["content_segments"].parts[-3:], ("processed", "abc123def45", "content_segments.json"))

    def test_unsynced_acquisition_is_mirror_pending(self):
        self.assertEqual(acquisition_processing_status("abc123def45", set()), "mirror_pending")
        self.assertEqual(acquisition_processing_status("abc123def45", {"abc123def45"}), "source_complete")
