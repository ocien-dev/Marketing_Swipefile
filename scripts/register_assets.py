#!/usr/bin/env python
"""Register obtained complementary files as Marketing Swipe File assets."""

from __future__ import annotations

import argparse
import hashlib
import mimetypes
import shutil
from pathlib import Path
from typing import Any

from youtube_common import utc_now, write_json


ASSET_TYPE_BY_SUFFIX = {
    ".pdf": "pdf",
    ".doc": "doc",
    ".docx": "doc",
    ".txt": "text",
    ".md": "text",
    ".html": "html",
    ".htm": "html",
    ".csv": "spreadsheet",
    ".xlsx": "spreadsheet",
    ".xls": "spreadsheet",
    ".ppt": "slides",
    ".pptx": "slides",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def guess_asset_type(path: Path) -> str:
    return ASSET_TYPE_BY_SUFFIX.get(path.suffix.lower(), "other")


def asset_id_for(episode_video_id: str, checksum: str) -> str:
    return f"{episode_video_id}-asset-{checksum[:12]}"


def register_file(
    file_path: Path,
    episode_video_id: str,
    output_root: Path,
    referenced_asset_id: str | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    checksum = sha256_file(file_path)
    asset_id = asset_id_for(episode_video_id, checksum)
    asset_dir = output_root / asset_id
    asset_dir.mkdir(parents=True, exist_ok=True)

    original_path = asset_dir / f"original{file_path.suffix.lower()}"
    if not original_path.exists():
        shutil.copy2(file_path, original_path)

    mime_type, _ = mimetypes.guess_type(str(file_path))
    metadata = {
        "schema_version": "1.0",
        "asset_id": asset_id,
        "referenced_asset_id": referenced_asset_id,
        "episode_video_id": episode_video_id,
        "source": source,
        "original_filename": file_path.name,
        "storage_path": str(original_path).replace("\\", "/"),
        "mime_type": mime_type,
        "asset_type": guess_asset_type(file_path),
        "language_original": None,
        "checksum": checksum,
        "processing_status": "pending",
        "created_at": utc_now(),
        "processed_at": None,
    }
    write_json(asset_dir / "metadata.json", metadata)
    return metadata


def iter_input_files(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        return []
    return [path for path in sorted(input_dir.iterdir()) if path.is_file() and not path.name.startswith(".")]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode-video-id", required=True, help="Episode/video id that owns the assets")
    parser.add_argument("--input-dir", type=Path, help="Directory containing obtained files")
    parser.add_argument("--file", type=Path, help="Single obtained file to register")
    parser.add_argument("--referenced-asset-id", default=None, help="Optional referenced asset id")
    parser.add_argument("--source", default=None, help="Optional source name")
    parser.add_argument("--output-root", default=Path("data/raw/assets"), type=Path)
    args = parser.parse_args()

    files: list[Path]
    if args.file:
        files = [args.file]
    elif args.input_dir:
        files = iter_input_files(args.input_dir)
    else:
        parser.error("Provide --file or --input-dir")

    if not files:
        print("No asset files found.")
        return 0

    registered = []
    for file_path in files:
        metadata = register_file(
            file_path=file_path,
            episode_video_id=args.episode_video_id,
            output_root=args.output_root,
            referenced_asset_id=args.referenced_asset_id,
            source=args.source,
        )
        registered.append(metadata)
        print(f"Registered {file_path} as {metadata['asset_id']}")

    print(f"Registered {len(registered)} asset file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

