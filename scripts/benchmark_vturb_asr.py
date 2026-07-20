#!/usr/bin/env python3
"""Benchmark approved local ASR models on a cached VTurb audio clip."""

from __future__ import annotations

import argparse
import json
import re
import resource
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from faster_whisper import WhisperModel


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.casefold())


def extract_terms(text: str) -> dict[str, set[str]]:
    return {
        "numbers": set(re.findall(r"\b\d+(?:[.,]\d+)?%?\b", text)),
        "marketing": {
            term for term in (
                "vsl", "funil", "copy", "oferta", "checkout", "criativo", "conversão",
                "upsell", "downsell", "advertorial", "tráfego", "pixel", "tracking",
            ) if term in text.casefold()
        },
    }


def retention(reference: set[str], candidate: set[str]) -> float:
    if not reference:
        return 1.0
    return len(reference & candidate) / len(reference)


def transcribe(model: WhisperModel, media: Path, clip_seconds: int) -> tuple[str, dict[str, Any]]:
    started = time.perf_counter()
    segments_iter, info = model.transcribe(
        str(media), beam_size=1, vad_filter=True, clip_timestamps=f"0,{clip_seconds}"
    )
    segments = [str(segment.text or "").strip() for segment in segments_iter if str(segment.text or "").strip()]
    elapsed = time.perf_counter() - started
    text = " ".join(segments)
    return text, {
        "inference_seconds": round(elapsed, 3),
        "media_seconds": clip_seconds,
        "rtf": round(elapsed / clip_seconds, 4),
        "language": getattr(info, "language", None),
        "segments": len(segments),
        "words": len(tokens(text)),
    }


def benchmark_model(name: str, media: Path, cache: Path, clip_seconds: int) -> dict[str, Any]:
    cache.mkdir(parents=True, exist_ok=True)
    cold_started = time.perf_counter()
    cold = WhisperModel(name, device="cpu", compute_type="int8", download_root=str(cache))
    cold_load = time.perf_counter() - cold_started
    del cold
    warm_started = time.perf_counter()
    model = WhisperModel(name, device="cpu", compute_type="int8", download_root=str(cache))
    warm_load = time.perf_counter() - warm_started
    text, inference = transcribe(model, media, clip_seconds)
    return {
        "model": name,
        "device": "cpu",
        "compute_type": "int8",
        "cold_load_seconds": round(cold_load, 3),
        "warm_load_seconds": round(warm_load, 3),
        **inference,
        "peak_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
        "text": text,
        "terms": {key: sorted(value) for key, value in extract_terms(text).items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--media", required=True, type=Path)
    parser.add_argument("--model-cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", action="append", default=[])
    parser.add_argument("--clip-seconds", default=600, type=int)
    parser.add_argument("--backlog-media-seconds", default=0.0, type=float)
    args = parser.parse_args()
    models = args.model or ["large-v3-turbo", "small"]
    if "large-v3-turbo" not in models or len(set(models)) < 2:
        parser.error("benchmark requires large-v3-turbo and at least one alternative")
    report: dict[str, Any] = {
        "schema_version": "1.0.0",
        "kind": "vturb_asr_benchmark",
        "started_at": now(),
        "media": str(args.media),
        "clip_seconds": args.clip_seconds,
        "results": [],
    }
    for model_name in models:
        report["results"].append(benchmark_model(model_name, args.media, args.model_cache, args.clip_seconds))
        atomic_json(args.output, report)
    baseline = next(item for item in report["results"] if item["model"] == "large-v3-turbo")
    baseline_tokens = set(tokens(baseline["text"]))
    baseline_terms = {key: set(value) for key, value in baseline["terms"].items()}
    for item in report["results"]:
        candidate_tokens = set(tokens(item["text"]))
        candidate_terms = {key: set(value) for key, value in item["terms"].items()}
        item["quality_vs_large"] = {
            "token_recall": round(retention(baseline_tokens, candidate_tokens), 4),
            "number_retention": round(retention(baseline_terms["numbers"], candidate_terms["numbers"]), 4),
            "marketing_term_retention": round(retention(baseline_terms["marketing"], candidate_terms["marketing"]), 4),
        }
        item["eta_backlog_seconds"] = round(item["rtf"] * args.backlog_media_seconds, 1)
    approved = [
        item for item in report["results"]
        if item["quality_vs_large"]["token_recall"] >= 0.90
        and item["quality_vs_large"]["number_retention"] == 1.0
        and item["quality_vs_large"]["marketing_term_retention"] >= 0.90
    ]
    chosen = min(approved or [baseline], key=lambda item: item["rtf"])
    rtfs = [item["rtf"] for item in approved or [baseline]]
    report["decision"] = {
        "model": chosen["model"],
        "reason": "fastest configuration that passed the literal quality gate",
        "estimated_backlog_seconds": chosen["eta_backlog_seconds"],
        "rtf_interval_observed": [min(rtfs), max(rtfs)],
        "quality_gate": {
            "token_recall_min": 0.90,
            "number_retention": 1.0,
            "marketing_term_retention_min": 0.90,
        },
    }
    report["finished_at"] = now()
    atomic_json(args.output, report)
    print(json.dumps({key: report[key] for key in ("kind", "decision", "finished_at")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
