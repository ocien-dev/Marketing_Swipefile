#!/usr/bin/env python
"""Instantiate a Marketing Swipe File process-skill template."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from msf_common import load_json, normalize_process_tags, slugify


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE_DIR = ROOT / "skills" / "_templates" / "msf-process-skill"
DEFAULT_OUTPUT_ROOT = ROOT / "skills"
DEFAULT_TAXONOMY = ROOT / "data" / "processed" / "taxonomy_seed.json"


def valid_process_ids(taxonomy_path: Path) -> set[str]:
    taxonomy = load_json(taxonomy_path)
    return {
        str(item.get("id"))
        for item in taxonomy.get("terms", [])
        if item.get("term_type") == "process" and item.get("status") == "active"
    }


def display_name_from_slug(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.split("-"))


def replacement_map(slug: str, display_name: str, process_tags: list[str]) -> dict[str, str]:
    skill_name = f"msf-process-{slug}"
    process_tags_inline = ", ".join(f"`{tag}`" for tag in process_tags)
    return {
        "__DATE__": date.today().isoformat(),
        "__SLUG__": slug,
        "__SKILL_NAME__": skill_name,
        "__DISPLAY_NAME__": display_name,
        "__DESCRIPTION__": f"Process skill for {display_name}",
        "__PRIMARY_PROCESS_TAG__": process_tags[0],
        "__PROCESS_TAGS_CSV__": ",".join(process_tags),
        "__PROCESS_TAGS_INLINE__": process_tags_inline,
    }


def render_template_file(source: Path, target: Path, replacements: dict[str, str]) -> None:
    text = source.read_text(encoding="utf-8")
    for old, new in replacements.items():
        text = text.replace(old, new)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def instantiate_process_skill(
    slug: str,
    process_tags: list[str],
    output_root: Path,
    template_dir: Path,
    display_name: str | None = None,
) -> Path:
    slug = slugify(slug, max_length=48)
    if not slug:
        raise ValueError("slug is required")
    if not process_tags:
        raise ValueError("at least one process tag is required")
    display_name = display_name or display_name_from_slug(slug)
    target_dir = output_root / f"msf-process-{slug}"
    if target_dir.exists():
        raise FileExistsError(f"target skill already exists: {target_dir}")
    replacements = replacement_map(slug, display_name, process_tags)
    for source in template_dir.rglob("*"):
        if source.is_dir():
            continue
        relative = source.relative_to(template_dir)
        render_template_file(source, target_dir / relative, replacements)
    contract_path = target_dir / "skill.contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["process_tags"] = process_tags
    contract_path.write_text(json.dumps(contract, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return target_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", required=True, help="Process skill slug, without the msf-process- prefix.")
    parser.add_argument("--display-name", help="Human-readable skill name.")
    parser.add_argument("--process-tags", nargs="+", required=True, help="Active process-* tags. Comma-separated values are accepted.")
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT, type=Path)
    parser.add_argument("--template-dir", default=DEFAULT_TEMPLATE_DIR, type=Path)
    parser.add_argument("--taxonomy", default=DEFAULT_TAXONOMY, type=Path)
    args = parser.parse_args()

    process_tags = normalize_process_tags(args.process_tags)
    invalid = sorted(set(process_tags) - valid_process_ids(args.taxonomy))
    if invalid:
        raise SystemExit(f"Invalid process_tags: {', '.join(invalid)}")

    target_dir = instantiate_process_skill(
        slug=args.slug,
        process_tags=process_tags,
        output_root=args.output_root,
        template_dir=args.template_dir,
        display_name=args.display_name,
    )
    print(f"Created {target_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
