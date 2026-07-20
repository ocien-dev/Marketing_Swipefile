#!/usr/bin/env python3
"""Benchmark batched large-v3-turbo against an existing standard reference."""

from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path

from faster_whisper import BatchedInferencePipeline, WhisperModel
from faster_whisper.audio import decode_audio

from scripts.benchmark_vturb_asr import atomic_json, extract_terms, retention, tokens


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--media", required=True, type=Path)
    parser.add_argument("--model-cache", required=True, type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--clip-seconds", default=600, type=int)
    parser.add_argument("--batch-size", default=8, type=int)
    parser.add_argument("--backlog-media-seconds", default=0.0, type=float)
    args = parser.parse_args()
    reference_report = json.loads(args.reference.read_text(encoding="utf-8"))
    reference = next(item for item in reference_report["results"] if item["model"] == "large-v3-turbo")
    started = time.perf_counter()
    model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8", download_root=str(args.model_cache))
    load_seconds = time.perf_counter() - started
    decode_started = time.perf_counter()
    audio = decode_audio(str(args.media), sampling_rate=16_000)[:args.clip_seconds * 16_000]
    decode_seconds = time.perf_counter() - decode_started
    pipeline = BatchedInferencePipeline(model)
    inference_started = time.perf_counter()
    segments_iter, info = pipeline.transcribe(
        audio, beam_size=1, vad_filter=True, without_timestamps=False, batch_size=args.batch_size
    )
    segments = [str(segment.text or "").strip() for segment in segments_iter if str(segment.text or "").strip()]
    inference_seconds = time.perf_counter() - inference_started
    text = " ".join(segments)
    reference_terms = {key: set(value) for key, value in reference["terms"].items()}
    candidate_terms = extract_terms(text)
    quality = {
        "token_recall": round(retention(set(tokens(reference["text"])), set(tokens(text))), 4),
        "number_retention": round(retention(reference_terms["numbers"], candidate_terms["numbers"]), 4),
        "marketing_term_retention": round(retention(reference_terms["marketing"], candidate_terms["marketing"]), 4),
    }
    passed = quality["token_recall"] >= 0.90 and quality["number_retention"] == 1.0 and quality["marketing_term_retention"] >= 0.90
    report = {
        "schema_version": "1.0.0",
        "kind": "vturb_asr_batched_benchmark",
        "model": "large-v3-turbo",
        "batch_size": args.batch_size,
        "clip_seconds": args.clip_seconds,
        "load_seconds": round(load_seconds, 3),
        "decode_seconds": round(decode_seconds, 3),
        "inference_seconds": round(inference_seconds, 3),
        "rtf": round(inference_seconds / args.clip_seconds, 4),
        "peak_rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
        "language": getattr(info, "language", None),
        "segments": len(segments),
        "quality_vs_standard_large": quality,
        "quality_gate_passed": passed,
        "estimated_backlog_seconds": round(inference_seconds / args.clip_seconds * args.backlog_media_seconds, 1),
    }
    atomic_json(args.output, report)
    print(json.dumps(report, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
