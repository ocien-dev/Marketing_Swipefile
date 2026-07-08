#!/usr/bin/env python
"""Validate a Marketing Swipe File process skill folder."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from msf_common import load_json, repo_data_path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "schemas" / "msf_process_skill_contract.schema.json"
DEFAULT_TAXONOMY = repo_data_path("processed", "taxonomy_seed.json")
REQUIRED_FILES = {
    "SKILL.md",
    "skill.contract.json",
    "retrieval.md",
    "rubric.md",
    "templates/output-template.md",
    "examples/briefing.md",
    "examples/output-approved.md",
}
INTERNAL_ASCII_FILES = {
    "SKILL.md",
    "skill.contract.json",
    "retrieval.md",
    "rubric.md",
}
CHECKLIST_KEYS = {
    "output_from_test_briefing",
    "r09_rubric_evaluation",
    "blind_baseline_test",
    "playbook_claims_cited_or_generic",
}
PLACEHOLDER_RE = re.compile(r"__[A-Z0-9_]+__")


def schema_validator(schema_path: Path) -> Any:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: jsonschema. Run `.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt`."
        ) from exc
    return Draft202012Validator(load_json(schema_path))


def active_process_ids(taxonomy_path: Path) -> set[str]:
    taxonomy = load_json(taxonomy_path)
    return {
        str(item.get("id"))
        for item in taxonomy.get("terms", [])
        if item.get("term_type") == "process" and item.get("status") == "active"
    }


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        return {}
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"')
    return values


def non_ascii_positions(text: str) -> list[str]:
    hits = []
    for index, char in enumerate(text):
        if ord(char) > 127:
            hits.append(f"{index}:{char}")
    return hits


def validate_skill_dir(skill_dir: Path, schema_path: Path, taxonomy_path: Path, require_done: bool = False) -> list[str]:
    errors: list[str] = []
    contract_path = skill_dir / "skill.contract.json"
    if not contract_path.exists():
        return [f"missing_file={contract_path}"]

    contract = load_json(contract_path)
    validator = schema_validator(schema_path)
    for error in sorted(validator.iter_errors(contract), key=lambda item: list(item.path)):
        path = ".".join(str(part) for part in error.path) or "<root>"
        errors.append(f"schema_error={path}:{error.message}")

    required_files = set(contract.get("required_files") or []) | REQUIRED_FILES
    for relative in sorted(required_files):
        if not (skill_dir / relative).exists():
            errors.append(f"missing_file={relative}")

    frontmatter = parse_frontmatter(skill_dir / "SKILL.md")
    if frontmatter.get("name") != contract.get("skill_name"):
        errors.append("skill_name_mismatch=SKILL.md frontmatter vs skill.contract.json")
    if not frontmatter.get("description"):
        errors.append("missing_description=SKILL.md")

    valid_ids = active_process_ids(taxonomy_path)
    process_tags = [str(tag) for tag in contract.get("process_tags") or []]
    invalid_tags = sorted(set(process_tags) - valid_ids)
    if invalid_tags:
        errors.append(f"invalid_process_tags={','.join(invalid_tags)}")

    retrieval_text = (skill_dir / "retrieval.md").read_text(encoding="utf-8") if (skill_dir / "retrieval.md").exists() else ""
    for tag in process_tags:
        if tag not in retrieval_text:
            errors.append(f"process_tag_missing_from_retrieval={tag}")

    skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8") if (skill_dir / "SKILL.md").exists() else ""
    if "[insight:<insight_id>]" not in skill_text or "[generic-practice]" not in skill_text:
        errors.append("citation_markers_missing=SKILL.md")

    checklist = contract.get("validation_checklist") or {}
    missing_checklist = sorted(CHECKLIST_KEYS - set(checklist))
    if missing_checklist:
        errors.append(f"missing_checklist_keys={','.join(missing_checklist)}")
    if require_done:
        incomplete = sorted(key for key in CHECKLIST_KEYS if checklist.get(key) != "pass")
        if incomplete:
            errors.append(f"checklist_not_pass={','.join(incomplete)}")

    for relative in sorted(INTERNAL_ASCII_FILES):
        path = skill_dir / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        placeholders = sorted(set(PLACEHOLDER_RE.findall(text)))
        if placeholders:
            errors.append(f"unresolved_placeholders={relative}:{','.join(placeholders)}")
        hits = non_ascii_positions(text)
        if hits:
            errors.append(f"non_ascii_internal_file={relative}:{';'.join(hits[:5])}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dirs", nargs="+", type=Path)
    parser.add_argument("--schema", default=DEFAULT_SCHEMA, type=Path)
    parser.add_argument("--taxonomy", default=DEFAULT_TAXONOMY, type=Path)
    parser.add_argument("--require-done", action="store_true", help="Require all Definition of Done checklist items to be pass.")
    args = parser.parse_args()

    all_errors: list[str] = []
    for skill_dir in args.skill_dirs:
        errors = validate_skill_dir(skill_dir, args.schema, args.taxonomy, require_done=args.require_done)
        if errors:
            all_errors.extend(f"{skill_dir}: {error}" for error in errors)
        else:
            print(f"VALID process_skill {skill_dir}")
    if all_errors:
        for error in all_errors:
            print(error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
