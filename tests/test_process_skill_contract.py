#!/usr/bin/env python
"""Fixture checks for MSF process-skill contracts."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from create_process_skill import DEFAULT_TEMPLATE_DIR, instantiate_process_skill  # noqa: E402
from validate_process_skill import DEFAULT_SCHEMA, DEFAULT_TAXONOMY, validate_skill_dir  # noqa: E402


def workspace_case_dir() -> Path:
    root = ROOT / ".tmp" / "process-skill-tests"
    root.mkdir(parents=True, exist_ok=True)
    case_dir = root / f"case-{uuid.uuid4().hex}"
    case_dir.mkdir()
    return case_dir


def test_process_skill_template_instantiates_and_validates() -> None:
    target = instantiate_process_skill(
        slug="copy-vsl",
        display_name="Copy VSL",
        process_tags=["process-copy-vsl"],
        output_root=workspace_case_dir(),
        template_dir=DEFAULT_TEMPLATE_DIR,
    )
    errors = validate_skill_dir(target, DEFAULT_SCHEMA, DEFAULT_TAXONOMY)
    assert errors == []


def test_process_skill_require_done_blocks_pending_checklist() -> None:
    target = instantiate_process_skill(
        slug="copy-vsl",
        display_name="Copy VSL",
        process_tags=["process-copy-vsl"],
        output_root=workspace_case_dir(),
        template_dir=DEFAULT_TEMPLATE_DIR,
    )
    errors = validate_skill_dir(target, DEFAULT_SCHEMA, DEFAULT_TAXONOMY, require_done=True)
    assert any(error.startswith("checklist_not_pass=") for error in errors)


def test_process_skill_validator_rejects_unresolved_placeholders() -> None:
    target = instantiate_process_skill(
        slug="copy-vsl",
        display_name="Copy VSL",
        process_tags=["process-copy-vsl"],
        output_root=workspace_case_dir(),
        template_dir=DEFAULT_TEMPLATE_DIR,
    )
    retrieval_path = target / "retrieval.md"
    retrieval_path.write_text(
        retrieval_path.read_text(encoding="utf-8") + "\n__UNRESOLVED_PLACEHOLDER__\n",
        encoding="utf-8",
        newline="\n",
    )
    errors = validate_skill_dir(target, DEFAULT_SCHEMA, DEFAULT_TAXONOMY)
    assert any(error.startswith("unresolved_placeholders=") for error in errors)


if __name__ == "__main__":
    test_process_skill_template_instantiates_and_validates()
    test_process_skill_require_done_blocks_pending_checklist()
    test_process_skill_validator_rejects_unresolved_placeholders()
    print("VALID process_skill_contract")
