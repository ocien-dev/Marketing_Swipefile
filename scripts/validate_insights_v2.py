#!/usr/bin/env python
"""Validate Marketing Swipe File insights_v2 JSON files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_validator(schema_path: Path):
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:  # pragma: no cover - exercised only in missing envs
        raise SystemExit(
            "Missing dependency: jsonschema. Run `.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt`."
        ) from exc

    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_payload(payload: dict[str, Any], schema_path: Path | None = None) -> list[str]:
    schema = schema_path or Path("schemas/insights_v2.schema.json")
    validator = load_validator(schema)
    errors: list[str] = []
    for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "<root>"
        errors.append(f"{location}: {error.message}")
    return errors


def validate_file(path: Path, schema_path: Path) -> list[str]:
    return validate_payload(load_json(path), schema_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--schema", type=Path, default=Path("schemas/insights_v2.schema.json"))
    args = parser.parse_args()

    failed = False
    for path in args.paths:
        errors = validate_file(path, args.schema)
        if errors:
            failed = True
            print(f"INVALID {path}")
            for error in errors:
                print(f"- {error}")
        else:
            print(f"VALID {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
