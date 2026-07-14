from pathlib import Path

import pytest

from scripts.publish_shared_exports import (
    MANIFEST_NAME,
    PUBLISHED_EXPORTS_DIR,
    collect_exports,
    publication_plan,
    publish_exports,
    verify_published_snapshot,
)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def seed_exports(root: Path) -> Path:
    exports = root / "exports"
    write(exports / "curated_insights.json", '{"insights": []}\n')
    write(exports / "reports" / "summary.md", "# Summary\n")
    write(exports / "packets" / "episode" / "packet_manifest.json", '{"episode_video_id": "episode"}\n')
    write(exports / "_snapshots" / "ignored.json", '{"old": true}\n')
    write(exports / "ignored.bin", "binary")
    return exports


def test_collect_exports_excludes_snapshots_and_unsupported_files(tmp_path):
    exports = seed_exports(tmp_path)

    files, skipped = collect_exports(exports)

    assert [item["path"] for item in files] == [
        "curated_insights.json",
        "packets/episode/packet_manifest.json",
        "reports/summary.md",
    ]
    assert sorted(skipped) == ["_snapshots/ignored.json", "ignored.bin"]


def test_check_plan_is_read_only(tmp_path):
    exports = seed_exports(tmp_path)
    before = {path: path.read_bytes() for path in exports.rglob("*") if path.is_file()}

    plan = publication_plan(exports)

    after = {path: path.read_bytes() for path in exports.rglob("*") if path.is_file()}
    assert plan["status"] == "ready_to_publish"
    assert plan["file_count"] == 3
    assert before == after
    assert not (tmp_path / "published").exists()


def test_publish_creates_verified_snapshot_without_source_snapshots(tmp_path):
    exports = seed_exports(tmp_path)
    destination = tmp_path / "published"

    result = publish_exports(exports, destination)

    assert result["status"] == "published"
    assert result["valid"] is True
    assert (destination / MANIFEST_NAME).is_file()
    assert (destination / PUBLISHED_EXPORTS_DIR / "curated_insights.json").is_file()
    assert not (destination / PUBLISHED_EXPORTS_DIR / "_snapshots").exists()
    assert verify_published_snapshot(destination)["valid"] is True


def test_failed_swap_preserves_prior_snapshot(tmp_path):
    exports = seed_exports(tmp_path)
    destination = tmp_path / "published"
    publish_exports(exports, destination)
    before = {path.relative_to(destination): path.read_bytes() for path in destination.rglob("*") if path.is_file()}
    write(exports / "curated_insights.json", '{"insights": ["new"]}\n')

    with pytest.raises(RuntimeError, match="injected failure during swap"):
        publish_exports(exports, destination, inject_failure_at="during_swap")

    after = {path.relative_to(destination): path.read_bytes() for path in destination.rglob("*") if path.is_file()}
    assert after == before
    assert verify_published_snapshot(destination)["valid"] is True


def test_verifier_rejects_extra_or_modified_files(tmp_path):
    exports = seed_exports(tmp_path)
    destination = tmp_path / "published"
    publish_exports(exports, destination)
    write(destination / PUBLISHED_EXPORTS_DIR / "extra.json", "{}\n")

    invalid = verify_published_snapshot(destination)
    assert invalid["valid"] is False
    assert invalid["reason"] == "published file set differs from manifest"
