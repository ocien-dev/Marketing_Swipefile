#!/usr/bin/env python
"""Validate Marketing Swipe File transversal module folders."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from msf_common import load_json


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "schemas" / "msf_transversal_module_contract.schema.json"
DEFAULT_TAXONOMY = ROOT / "data" / "processed" / "taxonomy_seed.json"
PLACEHOLDER_RE = re.compile(r"__[A-Z0-9_]+__")
INSIGHT_CITATION_RE = re.compile(r"\[insight:[A-Za-z0-9_-]+-v2-\d{4}\]")


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


def non_ascii_positions(text: str) -> list[str]:
    return [f"{index}:{char}" for index, char in enumerate(text) if ord(char) > 127]


def validate_module_dir(module_dir: Path, schema_path: Path, taxonomy_path: Path) -> list[str]:
    errors: list[str] = []
    contract_path = module_dir / "module.contract.json"
    if not contract_path.exists():
        return [f"missing_file={contract_path}"]

    contract = load_json(contract_path)
    validator = schema_validator(schema_path)
    for error in sorted(validator.iter_errors(contract), key=lambda item: list(item.path)):
        path = ".".join(str(part) for part in error.path) or "<root>"
        errors.append(f"schema_error={path}:{error.message}")

    required_files = set(contract.get("required_files") or [])
    for relative in sorted(required_files):
        if not (module_dir / relative).exists():
            errors.append(f"missing_file={relative}")

    valid_process_ids = active_process_ids(taxonomy_path)
    retrieval_text = (module_dir / "retrieval.md").read_text(encoding="utf-8") if (module_dir / "retrieval.md").exists() else ""

    for module in contract.get("modules") or []:
        module_id = str(module.get("module_id") or "")
        process_tag = str(module.get("process_tag") or "")
        file_path = module_dir / str(module.get("file") or "")
        consumed_by = module.get("consumed_by") or []
        if process_tag not in valid_process_ids:
            errors.append(f"invalid_process_tag={module_id}:{process_tag}")
        if len(consumed_by) < 2:
            errors.append(f"module_consumed_by_lt_2={module_id}")
        if process_tag and process_tag not in retrieval_text:
            errors.append(f"process_tag_missing_from_retrieval={module_id}:{process_tag}")
        if not file_path.exists():
            errors.append(f"missing_module_file={module_id}:{file_path}")
            continue
        text = file_path.read_text(encoding="utf-8")
        if module_id not in text:
            errors.append(f"module_id_missing_from_file={module_id}")
        if process_tag not in text:
            errors.append(f"process_tag_missing_from_file={module_id}:{process_tag}")
        citations = sorted(set(INSIGHT_CITATION_RE.findall(text)))
        if len(citations) < 3:
            errors.append(f"too_few_insight_citations={module_id}:{len(citations)}")

    for path in sorted(module_dir.rglob("*")):
        if path.is_dir():
            continue
        text = path.read_text(encoding="utf-8")
        placeholders = sorted(set(PLACEHOLDER_RE.findall(text)))
        if placeholders:
            errors.append(f"unresolved_placeholders={path.relative_to(module_dir)}:{','.join(placeholders)}")
        hits = non_ascii_positions(text)
        if hits:
            errors.append(f"non_ascii_internal_file={path.relative_to(module_dir)}:{';'.join(hits[:5])}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module_dirs", nargs="+", type=Path)
    parser.add_argument("--schema", default=DEFAULT_SCHEMA, type=Path)
    parser.add_argument("--taxonomy", default=DEFAULT_TAXONOMY, type=Path)
    args = parser.parse_args()

    all_errors: list[str] = []
    for module_dir in args.module_dirs:
        errors = validate_module_dir(module_dir, args.schema, args.taxonomy)
        if errors:
            all_errors.extend(f"{module_dir}: {error}" for error in errors)
        else:
            print(f"VALID transversal_modules {module_dir}")
    if all_errors:
        for error in all_errors:
            print(error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
