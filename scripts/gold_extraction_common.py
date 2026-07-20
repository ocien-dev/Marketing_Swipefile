#!/usr/bin/env python
"""Shared deterministic primitives for the parallel gold extraction layer.

This module deliberately contains no model client.  Semantic review is carried
out by Codex from resumable work orders; this module protects the source,
validates the resulting editorial records, and makes a rerun deterministic.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import re
import tempfile
import unicodedata
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Iterable


SCHEMA_VERSION = "1.0.0"
GOLD_TYPES = {
    "principle", "tactic", "playbook_step", "framework", "quantitative_case",
    "test_result", "copy_pattern", "script", "warning", "example",
}
CAUSAL_CERTAINTY = {
    "direct_test", "reported_attribution", "correlation", "uncertain", "not_applicable",
}
CLAIM_RISK = {"low", "medium", "high"}
UNIT_KINDS = {"currency", "percent", "count", "duration", "ratio"}
NUMBER_ROLES = {"baseline", "result", "delta", "target", "price", "budget", "capacity", "cadence", "other"}
VALUE_STATUS = {"reported", "calculated", "corrected", "inferred"}
EXCLUSION_REASON_CODES = {"interviewer_restate", "duplicate_of", "anecdote", "promo", "low_signal"}
AUDIT_FINDING_SEVERITIES = {"critical", "major", "minor"}
AUDIT_FINDING_STATUSES = {"open", "resolved"}
AUDIT_STATUSES = {"passed", "changes_requested", "failed"}

# This is intentionally small and closed.  Specific language remains available
# in subthemes and process_tags, where it is safer for retrieval evolution.
CANONICAL_THEMES = (
    "audience_market", "business_model", "copywriting", "copy_vsl", "creative_strategy",
    "conversion_optimization", "delivery_support", "funnel_architecture", "launch_campaign",
    "offer_pricing", "operations_management", "paid_traffic", "product_strategy",
    "retention_ascension", "sales_relationship", "testing_measurement", "unit_economics",
)

THEME_ALIASES = {
    "copy_vsl": "copy_vsl", "vsl": "copy_vsl", "copy": "copywriting", "lead": "copywriting",
    "hook": "copywriting", "headline": "copywriting", "mechanism": "copywriting",
    "proof": "copywriting", "objection_handling": "copywriting", "story": "copywriting",
    "traffic_creatives": "creative_strategy", "creative_fatigue": "creative_strategy",
    "angles": "creative_strategy", "video_editing": "creative_strategy", "production": "creative_strategy",
    "funnel_offer": "funnel_architecture", "frontend": "funnel_architecture", "backend": "funnel_architecture",
    "checkout": "funnel_architecture", "order_bump": "funnel_architecture", "downsell": "funnel_architecture",
    "launch": "launch_campaign", "paid_launch": "launch_campaign", "workshop": "launch_campaign",
    "offer": "offer_pricing", "pricing": "offer_pricing", "price_anchoring": "offer_pricing",
    "discount": "offer_pricing", "bonus": "offer_pricing", "guarantee": "offer_pricing",
    "business_model": "business_model", "cash_flow": "business_model", "profit": "business_model",
    "operations": "operations_management", "team": "operations_management", "workflow": "operations_management",
    "media_buying": "paid_traffic", "organic_content": "paid_traffic", "video_platform": "paid_traffic",
    "product": "product_strategy", "delivery": "product_strategy", "positioning": "product_strategy",
    "ascension": "retention_ascension", "upsell": "retention_ascension", "retention": "retention_ascension",
    "onboarding": "retention_ascension", "high_end": "retention_ascension",
    "sales": "sales_relationship", "support": "sales_relationship", "qualification": "sales_relationship",
    "testing_optimization": "testing_measurement", "ab_testing": "testing_measurement",
    "analytics": "testing_measurement", "conversion": "testing_measurement", "validation": "testing_measurement",
    "metrics_benchmarks": "testing_measurement", "reported_performance": "testing_measurement",
    "unit_economics": "unit_economics", "ltv": "unit_economics", "average_order_value": "unit_economics",
    "market_adaptation": "audience_market", "market_research": "audience_market",
    "customer_research": "audience_market", "audience": "audience_market", "belief": "audience_market",
}

DEFAULT_PROCESS_TAG_BY_THEME = {
    "audience_market": "process-pesquisa-avatar",
    "business_model": "process-estrategia-negocio",
    "copywriting": "process-copy-vsl",
    "copy_vsl": "process-copy-vsl",
    "creative_strategy": "process-teste-variacao-criativos",
    "conversion_optimization": "process-cro-testes",
    "delivery_support": "process-atendimento-suporte",
    "funnel_architecture": "process-arquitetura-funil",
    "launch_campaign": "process-lancamento",
    "offer_pricing": "process-construcao-oferta",
    "operations_management": "process-processos-operacao",
    "paid_traffic": "process-trafego-meta",
    "product_strategy": "process-validacao-oferta",
    "retention_ascension": "process-upsell-downsell",
    "sales_relationship": "process-time-vendas",
    "testing_measurement": "process-metricas-analise",
    "unit_economics": "process-financas-margem",
}

NUMBER_RE = re.compile(
    r"(?:r\$\s*)?\d{1,3}(?:[.\s]\d{3})*(?:[,\.]\d+)?\s*(?:%|x\b|k\b|milh(?:ao|oes)?\b|mil\b|dias?\b|mes(?:es)?\b|min(?:uto)?s?\b|horas?\b|leads?\b|compradores?\b|vendas?\b|alunos?\b)?",
    re.IGNORECASE,
)

MATERIAL_NUMERIC_TOKEN_RE = re.compile(
    r"(?P<currency>r\$\s*(?:\d{1,3}(?:[.\s]\d{3})+|\d+)(?:[,]\d+)?(?:\s*(?:k\b|milh(?:ao|oes)?\b|mil\b))?)"
    r"|(?P<percent>\d+(?:[,\.]\d+)?(?:\s+\d+)?\s*%)"
    r"|(?P<ratio>(?:\d+(?:[,\.]\d+)?\s*x\b|(?:um|uma|dois|duas|tr[eê]s|quatro|cinco|seis|sete|oito|nove|dez)\s+vezes\b))"
    r"|(?P<unit>\d+(?:[,\.]\d+)?\s*(?:k\b|milh(?:ao|oes)?\b|mil\b|dias?\b|semanas?\b|mes(?:es)?\b|min(?:uto)?s?\b|horas?\b|leads?\b|compradores?\b|vendas?\b|alunos?\b))"
    r"|(?P<bare>\d+(?:[,\.]\d+)?)",
    re.IGNORECASE,
)

NUMERIC_CLAIM_TYPES = {"quantitative_case", "test_result"}
NUMERIC_SEQUENCE_RE = re.compile(
    r"\b(?:sucessiv|etapa|depois|seguinte|aplica|aplicou|vira|chega|composto|base atualizada)\w*\b",
    re.IGNORECASE,
)

SIGNAL_PATTERNS = {
    "number": NUMBER_RE,
    "comparison": re.compile(r"\b(?:antes|depois|aumentou|diminuiu|caiu|dobrou|triplicou|metade|de\s+.+\s+para\s+)\b", re.I),
    "procedure": re.compile(r"\b(?:primeiro|segundo|terceiro|passo|etapa|faca|coloca|precisa|tem que|regra|checklist)\b", re.I),
    "copy": re.compile(r"\b(?:vsl|copy|lead|headline|mecanismo|prova|oferta|bonus|garantia|cta|pitch|desconto|cronometro|botao)\b", re.I),
    "funnel": re.compile(r"\b(?:funil|front.?end|upsell|downsell|backend|checkout|workshop|lancamento|reembolso|high.?end)\b", re.I),
    "traffic_creative": re.compile(r"\b(?:trafego|criativo|anuncio|campanha|orcamento|escala|publico|cpl|roas)\b", re.I),
    "experiment": re.compile(r"\b(?:teste|testamos|testei|validou|mudamos|converteu|conversao|resultado)\b", re.I),
    "warning": re.compile(r"\b(?:risco|erro|falha|cuidado|nao funciona|nao pode|depende|problema)\b", re.I),
    "sequence": re.compile(r"\b(?:depois|em seguida|por fim|ai|entao)\b", re.I),
}

RECOMMENDATION_TITLE_RE = re.compile(
    r"(?:\|.*(?:podcast|cast|episodio)|\bcomo\s+(?:fazer|lucrar|vender)\b|#\d+\s*$)", re.I
)


class GoldPauseError(RuntimeError):
    """Filesystem state makes a resumable execution unsafe to continue."""


def now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def normalize_ascii(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(char for char in text if not unicodedata.combining(char)).lower()


def comparison_texts(value: Any) -> set[str]:
    """Return normalized forms, including a reversible UTF-8-as-Latin-1 glitch."""
    raw = str(value or "")
    values = {normalize_ascii(raw)}
    if "\u00c3" in raw or "\u00c2" in raw:
        for encoding in ("latin-1", "cp1252"):
            try:
                values.add(normalize_ascii(raw.encode(encoding).decode("utf-8")))
            except (UnicodeDecodeError, UnicodeEncodeError):
                continue
    return values


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_data_path(value: str | Path, data_root: Path) -> Path:
    """Resolve persisted data paths after moving a data root across platforms."""
    direct = Path(value)
    if direct.exists():
        return direct.resolve()

    raw = str(value)
    pure = PureWindowsPath(raw) if "\\" in raw or PureWindowsPath(raw).drive else PurePosixPath(raw)
    parts = list(pure.parts)
    if "Marketing_Swipe_File" in parts:
        relative = parts[parts.index("Marketing_Swipe_File") + 1 :]
    else:
        anchors = {"input", "raw", "processed", "exports", "logs", "cache"}
        anchor_index = next((index for index, part in enumerate(parts) if part in anchors), None)
        if anchor_index is None:
            raise ValueError(f"cannot rebase data path without a known anchor: {value}")
        relative = parts[anchor_index:]
    if not relative:
        raise ValueError(f"cannot rebase empty data path: {value}")

    root = data_root.resolve()
    rebased = root.joinpath(*relative).resolve()
    if not rebased.is_relative_to(root):
        raise ValueError(f"rebased data path escapes the configured root: {value}")
    return rebased


def sha256_semantic_json(value: Any) -> str:
    """Hash JSON by parsed value, deliberately ignoring CRLF/LF serialization."""
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def json_hashes(path: Path) -> dict[str, str]:
    """Expose both physical and semantic hashes for a JSON artifact."""
    raw = path.read_bytes()
    return {
        "physical_sha256": hashlib.sha256(raw).hexdigest(),
        "semantic_sha256": sha256_semantic_json(json.loads(raw.decode("utf-8"))),
    }


def record_operation_event(out: Path, operation: str, event_key: str, metadata: dict[str, Any] | None = None) -> None:
    """Persist an idempotent measured operation receipt for Fast Path metrics."""
    path = out / "fastpath_operation_receipt.json"
    receipt = load_json(path) if path.exists() else {"events": []}
    if any(event.get("operation") == operation and event.get("event_key") == event_key for event in receipt["events"]):
        return
    receipt["events"].append({"operation": operation, "event_key": event_key, "metadata": metadata or {}})
    write_json(path, receipt)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    except PermissionError as exc:
        raise GoldPauseError(f"filesystem permission/lock while writing {path}") from exc


def write_json_batch(values: dict[Path, Any]) -> None:
    """Stage JSON files beside their destinations before replacing any target.

    Validation callers use this after building every payload in memory.  It
    prevents malformed later reviews from leaving an earlier review persisted.
    The small restore path handles an interruption during the replace phase.
    """
    staged: list[tuple[Path, Path, bytes | None]] = []
    replaced: list[tuple[Path, bytes | None]] = []
    try:
        for path, value in values.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
            temporary = Path(temporary_name)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(value, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            staged.append((path, temporary, path.read_bytes() if path.exists() else None))
        for path, temporary, previous in staged:
            os.replace(temporary, path)
            replaced.append((path, previous))
    except Exception as exc:
        for path, previous in reversed(replaced):
            if previous is not None:
                path.write_bytes(previous)
            elif path.exists():
                path.unlink()
        for path, temporary, _previous in staged:
            if temporary.exists():
                temporary.unlink()
        if isinstance(exc, PermissionError):
            raise GoldPauseError(f"filesystem permission/lock while writing batch") from exc
        raise


def editorial_ascii_errors(candidate: dict[str, Any]) -> list[str]:
    """Enforce ASCII only for internal editorial fields, never verbatim quotes."""
    fields = ("title", "source_claim", "takeaway_applicavel")
    errors: list[str] = []
    for field in fields:
        value = str(candidate.get(field, ""))
        if any(ord(char) > 127 for char in value) or re.search(r"\w\?\w", value):
            errors.append(f"{candidate.get('candidate_id', '<unknown>')}: editorial encoding issue in {field}")
    return errors


def validate_external_audit_report(report: Any, executor_thread_id: str | None = None, allow_legacy: bool = False, require_executor_provenance: bool = True) -> list[str]:
    """Validate the provenance and findings contract of a new external audit."""
    if not isinstance(report, dict):
        return ["external audit report must be an object"]
    required = {
        "episode_video_id", "audit_route", "reviewer", "reviewer_thread_id", "reviewer_model",
        "reasoning_effort", "reviewed_at", "status", "summary", "findings", "open_findings",
    }
    missing = sorted(required - set(report))
    if missing:
        return [] if allow_legacy else [f"external audit report missing {missing}"]
    errors: list[str] = []
    if not str(report.get("audit_route", "")).strip():
        errors.append("external audit report missing audit_route")
    for field in ("reviewer", "reviewer_thread_id", "reviewer_model", "reasoning_effort", "summary"):
        if not str(report.get(field, "")).strip():
            errors.append(f"external audit report missing {field}")
    if report.get("status") not in AUDIT_STATUSES:
        errors.append("external audit report has invalid status")
    findings = report.get("findings")
    if not isinstance(findings, list):
        return errors + ["external audit report findings must be a list"]
    open_count = 0
    for index, finding in enumerate(findings):
        prefix = f"external audit finding {index}"
        if not isinstance(finding, dict):
            errors.append(f"{prefix} must be an object")
            continue
        finding_required = {"finding_id", "severity", "status", "category", "segment_range", "candidate_ids", "summary", "evidence", "required_action"}
        finding_missing = sorted(finding_required - set(finding))
        if finding_missing:
            errors.append(f"{prefix} missing {finding_missing}")
            continue
        if not str(finding["finding_id"]).strip():
            errors.append(f"{prefix} missing finding_id")
        if finding["severity"] not in AUDIT_FINDING_SEVERITIES:
            errors.append(f"{prefix} has invalid severity")
        if finding["status"] not in AUDIT_FINDING_STATUSES:
            errors.append(f"{prefix} has invalid status")
        if not str(finding["category"]).strip() or not str(finding["summary"]).strip() or not str(finding["evidence"]).strip() or not str(finding["required_action"]).strip():
            errors.append(f"{prefix} has incomplete narrative fields")
        segment_range = finding["segment_range"]
        if not isinstance(segment_range, list) or len(segment_range) != 2 or not all(isinstance(item, int) and item >= 0 for item in segment_range) or segment_range[0] > segment_range[1]:
            errors.append(f"{prefix} has invalid segment_range")
        if not isinstance(finding["candidate_ids"], list) or any(not isinstance(item, str) or not item for item in finding["candidate_ids"]):
            errors.append(f"{prefix} has invalid candidate_ids")
        if finding["status"] == "open":
            open_count += 1
    if report.get("open_findings") != open_count:
        errors.append("external audit report open_findings mismatch")
    if report.get("status") == "passed" and open_count:
        errors.append("passed external audit report has open findings")
    if report.get("status") == "passed" and require_executor_provenance and not executor_thread_id:
        errors.append("passed external audit requires executor provenance")
    if report.get("status") == "passed" and executor_thread_id and report.get("reviewer_thread_id") == executor_thread_id:
        same_thread_final_phase = (
            report.get("audit_route") == "final_model_review"
            and report.get("reviewer_model") == "gpt-5.6-sol"
            and report.get("reasoning_effort") in {"high", "xhigh", "max", "ultra"}
        )
        if not same_thread_final_phase:
            errors.append("same-thread final audit requires final_model_review with gpt-5.6-sol/high or above")
    return errors


def external_audit_gate(out: Path, executor_thread_id: str | None = None) -> dict[str, Any]:
    """Read a report without rewriting it and return the only valid completion gate."""
    path = out / "editorial_audit_report.json"
    if not path.exists():
        return {"status": "pending_external", "eligible_for_complete": False, "errors": [], "report": None}
    report = load_json(path)
    errors = validate_external_audit_report(report, executor_thread_id)
    if errors:
        return {"status": "pending_external", "eligible_for_complete": False, "errors": errors, "report": report}
    passed = report["status"] == "passed" and report["open_findings"] == 0
    return {"status": "passed" if passed else "pending_external", "eligible_for_complete": passed, "errors": [], "report": report}


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def preferred_transcript_path(data_root: Path, video_id: str) -> Path:
    """Use the pt-BR translation for gold when it exists, preserving the source transcript."""
    raw_dir = data_root / "raw" / "youtube" / video_id
    translated = raw_dir / "transcript_pt_br.json"
    return translated if translated.is_file() else raw_dir / "transcript_original.json"


def transcript_source_paths(data_root: Path, video_id: str) -> list[Path]:
    raw_dir = data_root / "raw" / "youtube" / video_id
    paths = [raw_dir / "transcript_original.json"]
    translated = raw_dir / "transcript_pt_br.json"
    if translated.is_file():
        paths.append(translated)
    return paths


def protected_paths(data_root: Path, video_id: str) -> list[Path]:
    raw_capture = data_root / "raw" / "youtube" / video_id / "transcript_original_browser_capture.json"
    return [
        *transcript_source_paths(data_root, video_id),
        *([raw_capture] if raw_capture.is_file() else []),
        data_root / "processed" / video_id / "insights_v2.json",
        data_root / "exports" / "curated_insights.json",
        data_root / "exports" / "insights_v2_master.json",
    ]


def fingerprint_paths(paths: Iterable[Path]) -> dict[str, str]:
    return {str(path): sha256_path(path) for path in paths if path.exists()}


def canonical_themes(themes: Iterable[Any]) -> tuple[list[str], list[str]]:
    canonical: list[str] = []
    subthemes: list[str] = []
    for raw in themes:
        raw_text = str(raw).strip()
        key = normalize_ascii(raw_text).replace(" ", "_").replace("-", "_")
        mapped = THEME_ALIASES.get(key)
        if mapped is None and key in CANONICAL_THEMES:
            mapped = key
        if mapped and mapped not in canonical:
            canonical.append(mapped)
        if raw_text and raw_text not in subthemes and (not mapped or raw_text != mapped):
            subthemes.append(raw_text)
    return canonical or ["business_model"], subthemes


def default_process_tags(themes: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(DEFAULT_PROCESS_TAG_BY_THEME[item] for item in themes if item in DEFAULT_PROCESS_TAG_BY_THEME))[:4]


def signal_types(text: str) -> list[str]:
    normalized_forms = comparison_texts(text)
    return [name for name, pattern in SIGNAL_PATTERNS.items() if any(pattern.search(form) for form in normalized_forms)]


def looks_like_recommendation_title(text: str) -> bool:
    compact = normalize_ascii(text).strip()
    return bool(RECOMMENDATION_TITLE_RE.search(compact))


def clean_segments(raw_segments: list[dict[str, Any]], duration_seconds: float, video_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Remove deterministic transcript pollution and preserve every decision."""
    kept: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    previous_start: float | None = None
    plausible_segment_seconds = max(180.0, min(900.0, duration_seconds * 0.05))
    for raw_index, raw in enumerate(raw_segments):
        segment = dict(raw)
        text = str(segment.get("text", "")).strip()
        start = segment.get("start_seconds")
        reported_duration = segment.get("duration_seconds")
        reason: str | None = None
        if not isinstance(start, (int, float)):
            reason = "missing_timestamp"
        elif start < 0:
            reason = "negative_timestamp"
        elif start > duration_seconds:
            reason = "timestamp_outside_video_duration"
        elif isinstance(reported_duration, (int, float)) and (reported_duration < 0 or reported_duration > plausible_segment_seconds):
            reason = "implausible_segment_duration"
        elif previous_start is not None and float(start) < previous_start:
            reason = "regressive_timestamp_recommendation" if looks_like_recommendation_title(text) else "unexpected_regressive_timestamp"
        if reason:
            removed.append({"raw_index": raw_index, "segment": raw, "text": text, "reason": reason})
            continue
        segment["youtube_video_id"] = video_id
        segment["text"] = text
        kept.append(segment)
        previous_start = float(start)
    for index, segment in enumerate(kept):
        next_start = float(kept[index + 1]["start_seconds"]) if index + 1 < len(kept) else duration_seconds
        segment["duration_seconds"] = round(max(0.0, next_start - float(segment["start_seconds"])), 3)
        segment["segment_id"] = f"{video_id}-transcript-{index + 1:04d}"
        segment["clean_index"] = index
    return kept, removed


def chunks_for_segments(segments: list[dict[str, Any]], max_chars: int = 12000, target_seconds: int = 600) -> list[list[dict[str, Any]]]:
    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_chars = 0
    start_seconds: float | None = None
    for segment in segments:
        cost = len(str(segment.get("text", ""))) + 80
        current_start = float(segment["start_seconds"])
        exceeds = current and (current_chars + cost > max_chars or (start_seconds is not None and current_start - start_seconds >= target_seconds))
        if exceeds:
            chunks.append(current)
            current, current_chars, start_seconds = [], 0, None
        if start_seconds is None:
            start_seconds = current_start
        current.append(segment)
        current_chars += cost
    if current:
        chunks.append(current)
    return chunks


def citation(segment: dict[str, Any]) -> dict[str, Any]:
    start = float(segment["start_seconds"])
    return {
        "segment_id": segment["segment_id"],
        "start_seconds": start,
        "end_seconds": start + float(segment["duration_seconds"]),
        "quote_verbatim": segment["text"],
    }


def make_signal_inventory(segments: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for segment in segments:
        signals = signal_types(str(segment["text"]))
        if signals:
            inventory.append({
                "segment_id": segment["segment_id"], "clean_index": segment["clean_index"],
                "signal_types": signals, "evidence": [citation(segment)],
            })
    return inventory


def _calibration_kind(text: str, signals: list[str]) -> str:
    normalized = normalize_ascii(text)
    if "experiment" in signals or re.search(r"\b(?:mudamos|testamos|validou|converteu)\b", normalized):
        return "experiment_or_test"
    if "comparison" in signals:
        return "before_after_or_change"
    if "procedure" in signals or "sequence" in signals:
        return "procedure_or_list"
    return "quantitative_claim"


def discover_calibrations(segments: list[dict[str, Any]], duration_seconds: float) -> dict[str, Any]:
    """Build one coverage target per semantic transcript unit, never per shared number."""
    candidates: list[dict[str, Any]] = []
    for segment in segments:
        signals = signal_types(segment["text"])
        trigger = {"number", "comparison", "procedure", "experiment"} & set(signals)
        if not trigger:
            continue
        kind = _calibration_kind(segment["text"], signals)
        candidates.append({
            "calibration_id": f"signal-{segment['clean_index']:04d}",
            "kind": kind,
            "segment_ids": [segment["segment_id"]],
            "segment_range": [segment["clean_index"], segment["clean_index"]],
            "trigger_types": sorted(trigger),
            "semantic_key": f"{kind}|{normalize_ascii(segment['text'])}",
            "quote_verbatim": segment["text"],
        })
    raw_discovered_count = len(candidates)
    candidates = deduplicate_calibrations(candidates)
    # A deterministic sample makes the calibration set reviewable in long episodes.
    candidates.sort(key=lambda item: (item["segment_range"][0], item["calibration_id"]))
    minimum_required = max(3, math.ceil(duration_seconds / 2700.0))
    target_count = max(12, minimum_required * 4)
    discovered_count = len(candidates)
    if len(candidates) > target_count:
        selected: list[dict[str, Any]] = []
        # Preserve at least one target of each detection class, then sample
        # chronologically across the full episode.  This keeps the review set
        # small without hard-coding episode facts or privileging only the intro.
        for kind in sorted({item["kind"] for item in candidates}):
            selected.append(next(item for item in candidates if item["kind"] == kind))
        remaining = max(target_count - len(selected), 0)
        for index in range(remaining):
            selected.append(candidates[round(index * (len(candidates) - 1) / max(remaining - 1, 1))])
        unique = {item["calibration_id"]: item for item in selected}
        if len(unique) < target_count:
            for item in candidates:
                unique.setdefault(item["calibration_id"], item)
                if len(unique) == target_count:
                    break
        candidates = [unique[key] for key in sorted(unique, key=lambda key: (unique[key]["segment_range"][0], key))]
    return {
        "discovery_method": "episode_generic_signal_discovery_v1",
        "minimum_required": minimum_required,
        "raw_discovered_count": raw_discovered_count,
        "discovered_count": discovered_count,
        "generated_count": len(candidates),
        "tests": candidates,
    }


def deduplicate_calibrations(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse only truly identical semantic units; never union related numbers."""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in candidates:
        quote_key = normalize_ascii(item.get("quote_verbatim", "")).strip()
        key = f"quote:{quote_key}" if quote_key else str(item.get("semantic_key") or item.get("calibration_id"))
        groups[key].append(item)
    merged: list[dict[str, Any]] = []
    for group in groups.values():
        ordered = sorted(group, key=lambda item: (len(item["segment_ids"]), item["segment_range"][0], item["calibration_id"]))
        primary = ordered[0]
        semantic_key = str(primary.get("semantic_key") or f"{primary.get('kind')}|{normalize_ascii(primary.get('quote_verbatim', ''))}")
        merged.append({
            **primary,
            "semantic_key": semantic_key,
            "calibration_id": f"calibration-{sha256_json([primary['kind'], primary['segment_ids'], semantic_key])[:12]}",
            "segment_ids": list(primary["segment_ids"]),
            "segment_range": list(primary["segment_range"]),
            "trigger_types": list(primary["trigger_types"]),
            "source_calibration_ids": sorted(item["calibration_id"] for item in group),
            "deduplicated_count": len(group),
            "deduplicated_segment_ids": sorted({segment_id for item in group for segment_id in item["segment_ids"] if segment_id not in primary["segment_ids"]}),
        })
    return merged


def context_range(citations: list[dict[str, Any]], segments_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    indexes = [int(segments_by_id[item["segment_id"]]["clean_index"]) for item in citations]
    starts = [float(item["start_seconds"]) for item in citations]
    ends = [float(item["end_seconds"]) for item in citations]
    return {
        "segment_start": min(indexes), "segment_end": max(indexes),
        "start_seconds": min(starts), "end_seconds": max(ends),
    }


def evidence_quotes(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = candidate.get("evidence") or {}
    if isinstance(evidence, list):
        return evidence
    return list(evidence.get("minimal_quote") or []) + list(evidence.get("support_segments") or [])


def _numeric_core(raw: Any) -> str:
    normalized = normalize_ascii(raw)
    split_decimal = re.search(r"(\d+)[,.](\d+)\s+(\d+)\s*%", normalized)
    if split_decimal:
        return f"{split_decimal.group(1)}.{split_decimal.group(2)}{split_decimal.group(3)}"
    normalized = normalized.replace("r$", "").strip()
    magnitude = re.search(r"((?<=\d)k\b|\b(?:k|mil|milhao|milhoes)\b)", normalized)
    numeric = re.search(r"\d[\d.\s]*(?:,\d+)?|\d+(?:\.\d+)?", normalized)
    if not numeric:
        return normalized
    token = numeric.group(0).strip()
    if "," in token:
        token = token.replace(".", "").replace(" ", "").replace(",", ".")
    elif (
        re.fullmatch(r"\d{1,3}(?:\.\d{3})+", token)
        or (" " in token and re.fullmatch(r"\d{1,3}(?:[.\s]\d{3})+", token))
    ):
        token = token.replace(".", "").replace(" ", "")
    else:
        token = token.replace(" ", "")
    return f"{token}:{magnitude.group(1)}" if magnitude else token


def numeric_mentions(text: Any) -> list[dict[str, Any]]:
    """Extract literal numeric tokens without changing their source form."""
    source = str(text or "")
    mentions: list[dict[str, Any]] = []
    for match in MATERIAL_NUMERIC_TOKEN_RE.finditer(source):
        kind = str(match.lastgroup or "bare")
        raw = match.group(0)
        mentions.append({
            "raw": raw,
            "kind": kind,
            "canonical": _numeric_core(raw),
            "asr_separated_decimal": bool(re.fullmatch(
                r"(?:0\s+\d{1,2}|0\d{2}|\d+[,.]\d+\s+\d+)\s*%",
                raw.strip(),
            )),
            "start": match.start(),
            "end": match.end(),
        })
    return mentions


def _number_record_mentions(number: dict[str, Any], record_index: int) -> list[dict[str, Any]]:
    mentions = numeric_mentions(number.get("raw", ""))
    inferred_kind = {
        "currency": "currency",
        "percent": "percent",
        "ratio": "ratio",
        "duration": "unit",
        "count": "unit",
    }.get(str(number.get("unit_kind")), "bare")
    if not mentions and number.get("value") is not None:
        mentions = [{
            "raw": str(number["value"]),
            "kind": inferred_kind,
            "canonical": _numeric_core(number["value"]),
            "start": 0,
            "end": len(str(number["value"])),
        }]
    result: list[dict[str, Any]] = []
    for mention in mentions:
        item = dict(mention)
        if item["kind"] == "bare":
            item["kind"] = inferred_kind
        item["record_index"] = record_index
        result.append(item)
    return result


def _numeric_kinds_compatible(evidence_kind: str, record_kind: str) -> bool:
    if evidence_kind == "bare":
        return True
    if record_kind == "bare":
        return True
    return evidence_kind == record_kind


def _expected_unit_kind(mention: dict[str, Any]) -> str | None:
    kind = str(mention.get("kind") or "")
    if kind in {"currency", "percent", "ratio"}:
        return kind
    if kind != "unit":
        return None
    raw = normalize_ascii(mention.get("raw"))
    if re.search(r"\b(?:dia|dias|semana|semanas|mes|meses|min|minuto|minutos|hora|horas)\b", raw):
        return "duration"
    if re.fullmatch(r"\d+(?:[.,]\d+)?\s*k", raw.strip()):
        # ``K`` carries scale but not semantic ownership: in source speech it
        # can mean currency, audience, leads or another count.  The authored
        # unit/role and surrounding proposition must decide it.
        return None
    return "count"


def _number_has_structured_value(number: dict[str, Any]) -> bool:
    return any(number.get(field) is not None for field in ("value", "min_value", "max_value"))


def _explicit_unknown_asr_number(
    candidate: dict[str, Any],
    number: dict[str, Any],
    mention: dict[str, Any],
) -> bool:
    """Accept an unknown ASR scale only when the ambiguity is explicit.

    Null is not a shortcut for unfinished authoring.  It is valid only when the
    source raw is preserved, the candidate caveat names ASR and the unknown
    scale/unit, and the record is deliberately classified as inferred/other.
    """
    if _number_has_structured_value(number):
        return False
    if number.get("value_status") != "inferred" or number.get("role") != "other":
        return False
    raw = normalize_ascii(number.get("raw")).strip()
    if not raw or raw != normalize_ascii(mention.get("raw")).strip():
        return False
    caveat = normalize_ascii(" ".join(str(item) for item in candidate.get("caveats") or []))
    unit = normalize_ascii(number.get("unit")).strip()
    ambiguity_markers = (
        "unknown", "uncertain", "ambiguous", "unclear", "desconhecid",
        "incert", "ambigu", "sem escala", "escala", "unidade",
    )
    return (
        raw in caveat
        and "asr" in caveat
        and any(marker in caveat for marker in ambiguity_markers)
        and ("asr" in unit or any(marker in unit for marker in ambiguity_markers))
    )


def _material_numeric_occurrence(
    *,
    layer: str,
    candidate_type: str,
    signal_types: set[str],
    mention: dict[str, Any],
    editorial_cores: set[str],
) -> bool:
    explicit_kind = mention["kind"] != "bare"
    numeric_signal = "number" in signal_types
    proposition_signal = bool({"comparison", "experiment", "test_result"} & signal_types)
    claim_mentions_value = mention["canonical"] in editorial_cores
    material = layer == "minimal" and (explicit_kind or candidate_type in NUMERIC_CLAIM_TYPES)
    material = material or (
        layer == "support"
        and candidate_type in NUMERIC_CLAIM_TYPES
        and numeric_signal
        and proposition_signal
    )
    return material or claim_mentions_value


def _explicit_source_duplicate_record_position(
    candidate: dict[str, Any],
    mention: dict[str, Any],
    record_mentions: list[dict[str, Any]],
    used_records: set[int],
) -> int | None:
    """Return a previously bound record for an explicitly declared repetition.

    A bare number repeated orally can otherwise consume an unrelated record
    with the same value (for example, a repeated 20-slot capacity consuming a
    later 20-sales result). Reuse is deliberately narrow: the evidence token
    must be bare and a human-written caveat must identify it as a ``source
    duplicate`` and ``not a second observation``, including the reused unit.
    This keeps exact source repetitions visible without inventing a second
    public numeric observation or silently merging ambiguous values.
    """
    if mention.get("kind") != "bare":
        return None
    caveat_text = normalize_ascii(" ".join(str(item) for item in candidate.get("caveats") or []))
    if "source duplicate" not in caveat_text or "not a second observation" not in caveat_text:
        return None
    canonical = str(mention.get("canonical") or "")
    if not re.search(rf"(?<!\d){re.escape(canonical)}(?!\d)", caveat_text):
        return None
    numbers = candidate.get("numbers") or []
    for position in sorted(used_records):
        record_mention = record_mentions[position]
        if record_mention.get("canonical") != canonical:
            continue
        record_index = record_mention["record_index"]
        unit = normalize_ascii(str(numbers[record_index].get("unit") or "")).strip()
        if unit and unit in caveat_text:
            return position
    return None


def candidate_numeric_coverage(
    candidate: dict[str, Any],
    signal_types_by_segment: dict[str, set[str]] | None = None,
) -> dict[str, Any]:
    """Reconcile material evidence mentions with structured number records.

    Minimal evidence is authoritative. Support-only mentions become blockers
    only for explicitly quantitative/test candidates when the source signal is
    numeric and comparative/experimental; other unmatched support remains an
    audit warning instead of being silently promoted into a claim.
    """
    signal_types_by_segment = signal_types_by_segment or {}
    evidence = candidate.get("evidence") or {}
    if isinstance(evidence, list):
        layers = [("minimal", evidence)]
    else:
        layers = [
            ("minimal", list(evidence.get("minimal_quote") or [])),
            ("support", list(evidence.get("support_segments") or [])),
        ]
    record_mentions = [
        mention
        for index, number in enumerate(candidate.get("numbers") or [])
        if isinstance(number, dict)
        for mention in _number_record_mentions(number, index)
    ]
    used_records: set[int] = set()
    candidate_type = str(candidate.get("type", ""))
    editorial = " ".join(
        str(candidate.get(field, ""))
        for field in ("source_claim", "takeaway_applicavel")
    ) + " " + " ".join(str(step) for step in candidate.get("steps", []))
    editorial_cores = {item["canonical"] for item in numeric_mentions(editorial)}
    evidence_text = " ".join(
        str(citation.get("quote_verbatim", ""))
        for _layer, citations in layers
        for citation in citations
    )
    preserve_multiplicity = candidate_type in NUMERIC_CLAIM_TYPES and bool(
        NUMERIC_SEQUENCE_RE.search(normalize_ascii(f"{editorial} {evidence_text}"))
    )
    seen: set[tuple[Any, ...]] = set()
    matrix: list[dict[str, Any]] = []
    for layer, citations in layers:
        for citation in citations:
            segment_id = str(citation.get("segment_id") or "")
            signal_types = set(signal_types_by_segment.get(segment_id, set()))
            for occurrence, mention in enumerate(numeric_mentions(citation.get("quote_verbatim", ""))):
                identity = (
                    segment_id if preserve_multiplicity else "*",
                    mention["canonical"],
                    occurrence if preserve_multiplicity else 0,
                )
                if identity in seen:
                    continue
                seen.add(identity)
                material = _material_numeric_occurrence(
                    layer=layer,
                    candidate_type=candidate_type,
                    signal_types=signal_types,
                    mention=mention,
                    editorial_cores=editorial_cores,
                )
                duplicate_position = _explicit_source_duplicate_record_position(
                    candidate, mention, record_mentions, used_records
                )
                matched_position = duplicate_position
                if matched_position is None:
                    matched_position = next(
                        (
                            position for position, item in enumerate(record_mentions)
                            if position not in used_records
                            and item["canonical"] == mention["canonical"]
                            and _numeric_kinds_compatible(mention["kind"], item["kind"])
                        ),
                        None,
                    )
                if matched_position is not None:
                    matched = record_mentions[matched_position]
                    if duplicate_position is None:
                        used_records.add(matched_position)
                    record_index = matched["record_index"]
                    number = candidate.get("numbers", [])[record_index]
                    record = {
                        key: copy.deepcopy(number.get(key))
                        for key in (
                            "raw", "value", "min_value", "max_value", "unit_kind",
                            "unit", "period", "role", "value_status", "denominator",
                            "attribution_window",
                        )
                        if key in number
                    }
                    if duplicate_position is not None:
                        disposition = "covered_explicit_duplicate"
                        severity = None
                        issue = "source repetition reuses one explicitly identified numeric observation"
                    elif _explicit_unknown_asr_number(candidate, number, mention):
                        disposition = "covered_unknown_asr"
                        severity = None
                        issue = "unknown ASR scale is explicit and retains a null structured value"
                    elif material and not _number_has_structured_value(number):
                        disposition = "missing_material"
                        severity = "hard_blocker"
                        issue = "material numeric record is opaque; type its value/range or declare explicit unknown ASR scale"
                    elif (
                        material
                        and _expected_unit_kind(mention) is not None
                        and number.get("unit_kind") != _expected_unit_kind(mention)
                    ):
                        disposition = "missing_material"
                        severity = "hard_blocker"
                        issue = "material numeric record unit_kind does not match the source occurrence"
                    elif material and number.get("role") == "other":
                        disposition = "missing_material"
                        severity = "hard_blocker"
                        issue = "material numeric record needs a semantic role"
                    elif mention.get("asr_separated_decimal"):
                        raw_preserved = str(number.get("raw", "")) == mention["raw"]
                        inferred = number.get("value_status") == "inferred"
                        caveated = bool(candidate.get("caveats"))
                        if raw_preserved and inferred and caveated:
                            disposition = "covered_asr_ambiguous"
                            severity = "audit_warning"
                            issue = "ASR-separated decimal preserved with inferred value and caveat"
                        else:
                            disposition = "missing_material"
                            severity = "hard_blocker"
                            issue = "ASR-separated decimal requires literal raw, inferred value_status, and caveat"
                    else:
                        disposition = "covered"
                        severity = None
                        issue = None
                else:
                    disposition = "missing_material" if material else "unresolved_support"
                    severity = "hard_blocker" if material else "audit_warning"
                    record_index = None
                    record = None
                    issue = "material numeric mention has no matching number record" if material else "support-only numeric mention needs semantic confirmation"
                matrix.append({
                    "segment_id": segment_id,
                    "layer": layer,
                    "raw": mention["raw"],
                    "canonical": mention["canonical"],
                    "kind": mention["kind"],
                    "signal_types": sorted(signal_types),
                    "disposition": disposition,
                    "severity": severity,
                    "issue": issue,
                    "record_index": record_index,
                    "record": record,
                })
    used_record_indexes = {
        int(item["record_index"])
        for item in matrix
        if item.get("record_index") is not None
    }
    evidence_canonicals = {str(item.get("canonical")) for item in matrix}
    for record_index, number in enumerate(candidate.get("numbers") or []):
        if not isinstance(number, dict) or record_index in used_record_indexes:
            continue
        mentions = _number_record_mentions(number, record_index)
        shadows_source = any(str(item.get("canonical")) in evidence_canonicals for item in mentions)
        if shadows_source and not _number_has_structured_value(number):
            matrix.append({
                "segment_id": None,
                "layer": "record",
                "raw": number.get("raw"),
                "canonical": mentions[0].get("canonical") if mentions else _numeric_core(number.get("raw")),
                "kind": mentions[0].get("kind") if mentions else "bare",
                "signal_types": [],
                "disposition": "duplicate_opaque_record",
                "severity": "hard_blocker",
                "issue": "unused opaque number record duplicates a represented source occurrence",
                "record_index": record_index,
                "record": copy.deepcopy(number),
            })
    return {
        "candidate_id": candidate.get("candidate_id"),
        "attribution": {
            "reported_case": bool(candidate.get("reported_case")),
            "causal_certainty": candidate.get("causal_certainty"),
            "claim_risk": candidate.get("claim_risk"),
            "caveats": list(candidate.get("caveats") or []),
        },
        "status": "blocked" if any(item["severity"] == "hard_blocker" for item in matrix) else "pass",
        "mentions": matrix,
        "sequence": {
            "preserved_multiplicity": preserve_multiplicity,
            "ordered_values": [
                item["canonical"]
                for item in matrix
                if item["disposition"] != "covered_explicit_duplicate"
            ] if preserve_multiplicity else [],
        },
        "missing_material": [item for item in matrix if item["severity"] == "hard_blocker"],
        "audit_warnings": [item for item in matrix if item["severity"] == "audit_warning"],
        "record_count": len(candidate.get("numbers") or []),
        "covered_record_indexes": sorted({item["record_index"] for item in matrix if item["record_index"] is not None}),
    }


def normalize_relations(candidates: list[dict[str, Any]]) -> list[str]:
    """Canonicalize parent/child edges and reject ambiguous links and cycles."""
    errors: list[str] = []
    by_id = {item.get("candidate_id"): item for item in candidates}
    if len(by_id) != len(candidates):
        return ["duplicate candidate_id"]
    for item in candidates:
        relations = item.setdefault("relations", {})
        if "parent_candidate_id" not in relations:
            relations["parent_candidate_id"] = item.pop("parent_candidate_id", None)
        relations.setdefault("child_candidate_ids", item.pop("child_candidate_ids", []))
        relations["child_candidate_ids"] = list(dict.fromkeys(relations["child_candidate_ids"] or []))
        parent_id = relations["parent_candidate_id"]
        if parent_id and parent_id not in by_id:
            errors.append(f"{item['candidate_id']}: dangling parent {parent_id}")
        for child_id in relations["child_candidate_ids"]:
            if child_id not in by_id:
                errors.append(f"{item['candidate_id']}: dangling child {child_id}")
    if errors:
        return errors
    for item in candidates:
        item_id = item["candidate_id"]
        parent_id = item["relations"]["parent_candidate_id"]
        if parent_id:
            parent = by_id[parent_id]
            children = parent["relations"]["child_candidate_ids"]
            if item_id not in children:
                children.append(item_id)
        for child_id in list(item["relations"]["child_candidate_ids"]):
            child = by_id[child_id]
            child_parent = child["relations"]["parent_candidate_id"]
            if child_parent and child_parent != item_id:
                errors.append(f"{item_id}: child {child_id} already belongs to {child_parent}")
            else:
                child["relations"]["parent_candidate_id"] = item_id
    for item in candidates:
        seen: set[str] = set()
        current = item["candidate_id"]
        while current:
            if current in seen:
                errors.append(f"relation cycle through {current}")
                break
            seen.add(current)
            current = by_id[current]["relations"]["parent_candidate_id"]
    return sorted(set(errors))


def validate_numbers(candidate_id: str, numbers: Any, source_quotes: list[str]) -> list[str]:
    errors: list[str] = []
    if not isinstance(numbers, list):
        return [f"{candidate_id}: numbers is not a list"]
    source = " ".join(source_quotes)
    normalized_source_forms = comparison_texts(source)
    for index, number in enumerate(numbers):
        prefix = f"{candidate_id}: number {index}"
        if not isinstance(number, dict):
            errors.append(f"{prefix} is not an object")
            continue
        required = {"raw", "value", "min_value", "max_value", "unit_kind", "period", "role", "value_status"}
        missing = required - set(number)
        if missing:
            errors.append(f"{prefix} missing {sorted(missing)}")
            continue
        if number["unit_kind"] not in UNIT_KINDS:
            errors.append(f"{prefix} invalid unit_kind")
        if number["role"] not in NUMBER_ROLES:
            errors.append(f"{prefix} invalid role")
        if number["value_status"] not in VALUE_STATUS:
            errors.append(f"{prefix} invalid value_status")
        for field in ("value", "min_value", "max_value"):
            value = number[field]
            if value is not None and not isinstance(value, (int, float)):
                errors.append(f"{prefix} {field} must be numeric or null")
        if number["min_value"] is not None and number["max_value"] is not None and number["min_value"] > number["max_value"]:
            errors.append(f"{prefix} min_value exceeds max_value")
        # Structured fields use ASCII NFKD internally while the evidence quote
        # stays verbatim UTF-8.  Accept either representation of the same
        # source token, without relaxing the verbatim citation check above.
        raw = str(number["raw"]).strip()
        normalized_raw = normalize_ascii(raw).strip()
        if raw not in source and (not normalized_raw or not any(normalized_raw in source_form for source_form in normalized_source_forms)):
            errors.append(f"{prefix} raw absent from evidence")
    return errors


def validate_candidate(candidate: dict[str, Any], segments_by_id: dict[str, dict[str, Any]], chunk_ids: set[str]) -> list[str]:
    errors: list[str] = []
    candidate_id = str(candidate.get("candidate_id", "<unknown>"))
    required = {
        "candidate_id", "chunk_id", "title", "type", "themes", "subthemes", "process_tags",
        "source_claim", "takeaway_applicavel", "context", "reported_case", "causal_certainty",
        "claim_risk", "numbers", "steps", "conditions", "caveats", "evidence", "relations",
    }
    missing = sorted(required - set(candidate))
    if missing:
        return [f"{candidate_id}: missing {missing}"]
    if candidate["chunk_id"] not in chunk_ids:
        errors.append(f"{candidate_id}: unknown chunk_id")
    if candidate["type"] not in GOLD_TYPES:
        errors.append(f"{candidate_id}: invalid type")
    if candidate["causal_certainty"] not in CAUSAL_CERTAINTY:
        errors.append(f"{candidate_id}: invalid causal_certainty")
    if candidate["claim_risk"] not in CLAIM_RISK:
        errors.append(f"{candidate_id}: invalid claim_risk")
    if not candidate["themes"] or any(theme not in CANONICAL_THEMES for theme in candidate["themes"]):
        errors.append(f"{candidate_id}: invalid canonical themes")
    if not isinstance(candidate["process_tags"], list) or any(not re.fullmatch(r"process-[a-z0-9-]+", str(tag)) for tag in candidate["process_tags"]):
        errors.append(f"{candidate_id}: invalid process_tags")
    if len(str(candidate["title"]).strip()) < 12 or len(str(candidate["takeaway_applicavel"]).strip()) < 35:
        errors.append(f"{candidate_id}: weak title or takeaway")
    evidence = candidate["evidence"]
    if not isinstance(evidence, dict):
        return errors + [f"{candidate_id}: evidence must use layered object"]
    minimal = evidence.get("minimal_quote") or []
    support = evidence.get("support_segments") or []
    context = evidence.get("context_range") or {}
    if not minimal:
        errors.append(f"{candidate_id}: missing minimal_quote")
    all_citations = list(minimal) + list(support)
    if not context or not {"segment_start", "segment_end", "start_seconds", "end_seconds"} <= set(context):
        errors.append(f"{candidate_id}: missing context_range")
    for item in all_citations:
        source = segments_by_id.get(item.get("segment_id"))
        if source is None:
            errors.append(f"{candidate_id}: evidence references missing segment")
        elif item.get("quote_verbatim") != source["text"]:
            errors.append(f"{candidate_id}: non-verbatim quote")
    if all_citations and context:
        indexes = [segments_by_id[item["segment_id"]]["clean_index"] for item in all_citations if item.get("segment_id") in segments_by_id]
        if indexes and (min(indexes) < context["segment_start"] or max(indexes) > context["segment_end"]):
            errors.append(f"{candidate_id}: evidence outside context_range")
    ordered_citations = sorted(all_citations, key=lambda item: (item.get("start_seconds", 0), item.get("segment_id", "")))
    errors.extend(validate_numbers(candidate_id, candidate["numbers"], [item.get("quote_verbatim", "") for item in ordered_citations]))
    if candidate["type"] in {"playbook_step", "framework", "script"} and not candidate["steps"]:
        errors.append(f"{candidate_id}: procedural type needs steps")
    return errors


def validate_document(document: dict[str, Any], segments: list[dict[str, Any]], chunks: list[dict[str, Any]], require_external_audit: bool = False) -> list[str]:
    errors: list[str] = []
    if document.get("schema_version") != SCHEMA_VERSION:
        errors.append("invalid schema_version")
    if document.get("insight_layer") != "gold_extraction":
        errors.append("invalid insight_layer")
    candidates = document.get("insights")
    if not isinstance(candidates, list):
        return errors + ["insights is not a list"]
    segments_by_id = {item["segment_id"]: item for item in segments}
    chunk_ids = {item["chunk_id"] for item in chunks}
    for candidate in candidates:
        errors.extend(validate_candidate(candidate, segments_by_id, chunk_ids))
    errors.extend(normalize_relations(candidates))
    audit = document.get("audit", {})
    if require_external_audit and audit.get("status") != "passed":
        errors.append("external audit has not passed")
    if require_external_audit and audit.get("open_findings", 0):
        errors.append(f"external audit has {audit['open_findings']} open finding(s)")
    return sorted(set(errors))


def infer_exclusion_reason(signal: dict[str, Any], candidates: list[dict[str, Any]]) -> tuple[str, str | None, str]:
    """Assign a reviewable category when a full-read exclusion has no override."""
    text = normalize_ascii(signal.get("evidence", [{}])[0].get("quote_verbatim", ""))
    if any(term in text for term in ("link in the description", "website", "subscribe", "sign up", "free checklist", "podcast")):
        return "promo", None, "promo: source promotion or call to action, not an independent marketing claim."
    if any(term in text for term in ("i remember", "funny story", "when i was", "my friend")):
        return "anecdote", None, "anecdote: context anecdote without an independent applicable claim."
    if any(term in text for term in ("you said", "do you", "what do you think", "so you actually", "right?")):
        return "interviewer_restate", None, "interviewer_restate: interviewer prompt or restatement covered by the source answer."
    segment_id = signal["segment_id"]
    for candidate in candidates:
        if segment_id in {item["segment_id"] for item in evidence_quotes(candidate)}:
            return "duplicate_of", candidate["candidate_id"], f"duplicate_of:{candidate['candidate_id']}: represented by selected evidence."
    return "low_signal", None, "low_signal: reviewed signal has no independent applicable marketing claim."


def ledger_for_signals(signal_inventory: list[dict[str, Any]], candidates: list[dict[str, Any]], manual_decisions: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    manual_decisions = manual_decisions or {}
    candidate_evidence = {
        candidate["candidate_id"]: {item["segment_id"] for item in evidence_quotes(candidate)}
        for candidate in candidates
    }
    inventory_by_segment = {item["segment_id"]: item for item in signal_inventory}
    # A reviewer may explicitly disposition a clean transcript row that was not
    # promoted into the automatic signal inventory.  Those source-scoped
    # decisions are intentional coverage, not disposable metadata: preserve
    # them in the derived ledger so the semantic workbench cannot leave the
    # reviewed row as ``unreviewed``.  Gold transcript ids end in a one-based
    # ordinal; ignore non-canonical ids rather than inventing an index.
    for segment_id in manual_decisions:
        if segment_id in inventory_by_segment:
            continue
        suffix = str(segment_id).rsplit("-", 1)[-1]
        if not suffix.isdigit() or int(suffix) <= 0:
            continue
        inventory_by_segment[segment_id] = {
            "segment_id": segment_id,
            "clean_index": int(suffix) - 1,
            "signal_types": ["manual_review"],
            "evidence": [],
        }
    for candidate in candidates:
        for item in evidence_quotes(candidate):
            inventory_by_segment.setdefault(item["segment_id"], {
                "segment_id": item["segment_id"], "clean_index": candidate["evidence"]["context_range"]["segment_start"],
                "signal_types": ["candidate_evidence"], "evidence": [item],
            })
    entries: list[dict[str, Any]] = []
    for signal in sorted(inventory_by_segment.values(), key=lambda item: (item["clean_index"], item["segment_id"])):
        segment_id = signal["segment_id"]
        decision = manual_decisions.get(segment_id)
        matched = sorted(candidate_id for candidate_id, evidence in candidate_evidence.items() if segment_id in evidence)
        if decision:
            disposition = decision["disposition"]
            candidate_ids = decision.get("candidate_ids", [])
            reason_code = decision.get("reason_code")
            reason_reference = decision.get("reason_reference")
            reason = decision.get("reason") or f"{reason_code or 'low_signal'}: reviewer decision."
        elif matched:
            disposition, candidate_ids, reason_code, reason_reference, reason = "captured", matched, None, None, "Evidence selected by semantic reviewer."
        else:
            disposition, candidate_ids = "excluded", []
            reason_code, reason_reference, reason = infer_exclusion_reason(signal, candidates)
        entries.append({
            "segment_id": segment_id, "segment_range": [signal["clean_index"], signal["clean_index"]],
            "signal_types": signal["signal_types"], "disposition": disposition,
            "candidate_ids": candidate_ids, "reason_code": reason_code,
            "reason_reference": reason_reference, "reason": reason,
        })
    return entries


def ledger_errors(ledger: list[dict[str, Any]], candidate_ids: set[str], expected_signal_ids: set[str]) -> list[str]:
    errors: list[str] = []
    actual_ids = {item["segment_id"] for item in ledger}
    if actual_ids != expected_signal_ids:
        errors.append("ledger does not cover every signal exactly once")
    if len(actual_ids) != len(ledger):
        errors.append("ledger duplicates a signal")
    for item in ledger:
        if item["disposition"] not in {"captured", "merged", "excluded"}:
            errors.append(f"ledger invalid disposition for {item['segment_id']}")
        if item["disposition"] in {"captured", "merged"} and not item["candidate_ids"]:
            errors.append(f"ledger missing destination for {item['segment_id']}")
        if any(candidate_id not in candidate_ids for candidate_id in item["candidate_ids"]):
            errors.append(f"ledger dangling candidate for {item['segment_id']}")
        if not str(item.get("reason", "")).strip():
            errors.append(f"ledger missing reason for {item['segment_id']}")
        if item["disposition"] == "excluded" and item.get("reason_code") not in EXCLUSION_REASON_CODES:
            errors.append(f"ledger invalid exclusion category for {item['segment_id']}")
        if item.get("reason_code") == "duplicate_of" and item.get("reason_reference") not in candidate_ids:
            errors.append(f"ledger duplicate reference missing for {item['segment_id']}")
    return errors


def calibration_target_errors(calibration: dict[str, Any], segments_by_id: dict[str, dict[str, Any]] | set[str]) -> list[str]:
    """Return deterministic calibration-target errors before semantic matching."""
    errors: list[str] = []
    segment_map = segments_by_id if isinstance(segments_by_id, dict) else {segment_id: {} for segment_id in segments_by_id}
    seen: set[str] = set()
    tests = calibration.get("tests", [])
    if not isinstance(tests, list):
        return ["calibration tests must be a list"]
    for item in tests:
        calibration_id = item.get("calibration_id", "<unknown>")
        segment_ids = item.get("segment_ids")
        if not isinstance(segment_ids, list) or not segment_ids:
            errors.append(f"{calibration_id}: calibration target needs segment_ids")
            continue
        quote = item.get("quote_verbatim", item.get("quote"))
        if not isinstance(quote, str) or not quote.strip():
            errors.append(f"{calibration_id}: calibration target needs a non-empty quote_verbatim")
        for segment_id in segment_ids:
            if segment_id not in segment_map:
                errors.append(f"{calibration_id}: calibration target references unknown segment {segment_id}")
            if segment_id in seen:
                errors.append(f"{calibration_id}: calibration target duplicates segment {segment_id}")
            seen.add(segment_id)
        if isinstance(quote, str) and quote.strip() and not any(quote == str(segment_map.get(segment_id, {}).get("text", "")) for segment_id in segment_ids):
            errors.append(f"{calibration_id}: calibration quote_verbatim does not match a referenced segment")
    return errors


def calibration_coverage(
    calibration: dict[str, Any],
    candidates: list[dict[str, Any]],
    ledger: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    evidence = {
        candidate["candidate_id"]: {item["segment_id"] for item in evidence_quotes(candidate)}
        for candidate in candidates
    }
    candidate_ids = set(evidence)
    ledger = ledger or []
    ledger_candidates: dict[str, set[str]] = defaultdict(set)
    for entry in ledger:
        if not isinstance(entry, dict) or entry.get("disposition") not in {"captured", "merged"}:
            continue
        segment_id = str(entry.get("segment_id") or "")
        destinations = {
            str(candidate_id)
            for candidate_id in entry.get("candidate_ids") or []
            if str(candidate_id) in candidate_ids
        }
        ledger_candidates[segment_id].update(destinations)
    tests: list[dict[str, Any]] = []
    seen_segments: set[str] = set()
    duplicate_target_segments: list[str] = []
    for test in calibration.get("tests", []):
        target_ids = set(test["segment_ids"])
        duplicate_target_segments.extend(sorted(target_ids & seen_segments))
        seen_segments.update(target_ids)
        matched = sorted({
            candidate_id
            for candidate_id, ids in evidence.items()
            if target_ids & ids
        } | {
            candidate_id
            for segment_id in target_ids
            for candidate_id in ledger_candidates.get(str(segment_id), set())
        })
        tests.append({**test, "semantic_candidate_ids": matched, "semantic_coverage": "pass" if matched else "fail"})
    required = min(calibration.get("minimum_required", 0), len(tests))
    passed = sum(item["semantic_coverage"] == "pass" for item in tests)
    return {**calibration, "tests": tests, "covered_count": passed, "duplicate_target_segments": sorted(set(duplicate_target_segments)), "status": "pass" if passed >= required and not duplicate_target_segments else "fail"}


def build_dedupe_queue(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return conservative title/claim/number clusters for a human decision."""
    tokens: dict[str, set[str]] = {}
    numbers: dict[str, set[str]] = {}
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        words = re.findall(r"[a-z0-9]{3,}", normalize_ascii(candidate["title"] + " " + candidate["source_claim"]))
        tokens[candidate_id] = set(words)
        numbers[candidate_id] = {normalize_ascii(item["raw"]) for item in candidate.get("numbers", [])}
    queue: list[dict[str, Any]] = []
    ordered_ids = sorted(tokens)
    for index, left_id in enumerate(ordered_ids):
        for right_id in ordered_ids[index + 1:]:
            union = tokens[left_id] | tokens[right_id]
            jaccard = len(tokens[left_id] & tokens[right_id]) / len(union) if union else 0.0
            same_numbers = bool(numbers[left_id] & numbers[right_id])
            if jaccard >= 0.52 or (jaccard >= 0.36 and same_numbers):
                queue.append({
                    "queue_id": f"dq-{sha256_json([left_id, right_id])[:12]}",
                    "candidate_ids": [left_id, right_id], "token_jaccard": round(jaccard, 3),
                    "shared_numbers": sorted(numbers[left_id] & numbers[right_id]),
                    "decision": "pending", "rationale": None,
                })
    return queue


def count_by(candidates: list[dict[str, Any]], key: str) -> dict[str, int]:
    values: Counter[str] = Counter()
    for candidate in candidates:
        value = candidate.get(key)
        if isinstance(value, list):
            values.update(str(item) for item in value)
        elif value is not None:
            values[str(value)] += 1
    return dict(sorted(values.items()))
