#!/usr/bin/env python
"""Fixture checks for MSF transversal copy modules."""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_transversal_modules import DEFAULT_SCHEMA, DEFAULT_TAXONOMY, validate_module_dir  # noqa: E402


MODULE_DIR = ROOT / "skills" / "_modules" / "msf-transversal-copy"


def workspace_case_dir() -> Path:
    root = ROOT / ".tmp" / "transversal-module-tests"
    root.mkdir(parents=True, exist_ok=True)
    case_dir = root / f"case-{uuid.uuid4().hex}"
    case_dir.mkdir()
    return case_dir


def copy_module_dir(target: Path) -> Path:
    destination = target / "msf-transversal-copy"
    for source in MODULE_DIR.rglob("*"):
        if source.is_dir():
            continue
        relative = source.relative_to(MODULE_DIR)
        output = destination / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(source.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    return destination


def test_transversal_modules_validate() -> None:
    errors = validate_module_dir(MODULE_DIR, DEFAULT_SCHEMA, DEFAULT_TAXONOMY)
    assert errors == []


def test_transversal_modules_require_two_consumers() -> None:
    copied = copy_module_dir(workspace_case_dir())
    contract_path = copied / "module.contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["modules"][0]["consumed_by"] = ["msf-process-copy-vsl"]
    contract_path.write_text(json.dumps(contract, ensure_ascii=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    errors = validate_module_dir(copied, DEFAULT_SCHEMA, DEFAULT_TAXONOMY)
    assert any(error.startswith("schema_error=modules.0.consumed_by") for error in errors)


if __name__ == "__main__":
    test_transversal_modules_validate()
    test_transversal_modules_require_two_consumers()
    print("VALID transversal_modules_contract")
