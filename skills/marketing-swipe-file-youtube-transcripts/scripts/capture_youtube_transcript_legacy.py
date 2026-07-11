#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LEGACY_CAPTURE_JS = r"""
async (page) => {
  await page.waitForLoadState('domcontentloaded', { timeout: 45000 }).catch(() => {});
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {});
  return await page.evaluate(async () => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const normalize = (value) => (value || '').trim().replace(/\s+/g, ' ');
    const visible = (element) => {
      const rect = element.getBoundingClientRect();
      const style = window.getComputedStyle(element);
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
    };
    const labelFor = (element) => normalize(
      element.innerText || element.textContent || element.getAttribute('aria-label') || element.getAttribute('title') || ''
    );
    const clickElement = async (element) => {
      element.scrollIntoView({ block: 'center', inline: 'nearest' });
      await sleep(450);
      (element.querySelector('button') || element).click();
      await sleep(1200);
    };
    const buttonSelector = 'button,[role=button],yt-button-shape,ytd-button-renderer,tp-yt-paper-button,a';
    const events = [];
    const description =
      document.querySelector('ytd-watch-metadata #description') ||
      document.querySelector('#description-inline-expander') ||
      document.querySelector('ytd-text-inline-expander') ||
      document.querySelector('#above-the-fold');
    if (description) {
      description.scrollIntoView({ block: 'center', inline: 'nearest' });
      events.push('scrolled_description');
      await sleep(900);
    }
    for (let attempt = 0; attempt < 4; attempt += 1) {
      const moreButtons = Array.from(document.querySelectorAll(buttonSelector))
        .filter((element) => /^\.{3}\s*mais$|^mostrar\s+mais$|^mais$|^show\s+more$|^more$/i.test(labelFor(element)));
      const target = moreButtons.find(visible) || moreButtons[0];
      if (!target) break;
      await clickElement(target);
      events.push(`clicked_more_${attempt + 1}:${labelFor(target).slice(0, 40)}`);
      if (/Mostrar transcri|Show transcript|Transcri[cç][aã]o/.test(document.body.innerText || '')) break;
    }
    const transcriptSection = document.querySelector('ytd-video-description-transcript-section-renderer');
    if (transcriptSection) {
      transcriptSection.scrollIntoView({ block: 'center', inline: 'nearest' });
      events.push('scrolled_transcript_section');
      await sleep(700);
    }
    const transcriptButtons = Array.from(document.querySelectorAll(buttonSelector))
      .filter((element) => /mostrar\s+transcri|show\s+transcript/i.test(labelFor(element)));
    const transcriptButton =
      transcriptButtons.find((element) => element.closest('ytd-video-description-transcript-section-renderer') && visible(element)) ||
      transcriptButtons.find((element) => element.closest('ytd-video-description-transcript-section-renderer')) ||
      transcriptButtons.find(visible) ||
      transcriptButtons[0];
    if (!transcriptButton) {
      return { ok: false, reason: 'missing_description_transcript_button', events };
    }
    await clickElement(transcriptButton);
    events.push(`clicked_transcript:${labelFor(transcriptButton).slice(0, 60)}`);
    const segmentSelector = 'transcript-segment-view-model,ytd-transcript-segment-renderer';
    for (let attempt = 0; attempt < 3; attempt += 1) {
      const tab = Array.from(document.querySelectorAll('button,[role=tab],[role=button],yt-chip-cloud-chip-renderer'))
        .find((element) => /^Transcri[cç][aã]o$|^Transcript$/i.test(labelFor(element)) && visible(element));
      if (tab) {
        await clickElement(tab);
        events.push(`clicked_transcript_tab_${attempt + 1}`);
      }
      const deadline = Date.now() + 15000;
      while (Date.now() < deadline) {
        if (document.querySelectorAll(segmentSelector).length > 0) break;
        await sleep(750);
      }
      if (document.querySelectorAll(segmentSelector).length > 0) break;
    }
    const nodes = Array.from(document.querySelectorAll(segmentSelector));
    const segments = nodes.map((element, index) => {
      const rawText = normalize(element.innerText || element.textContent || '');
      let timestamp = normalize(
        element.querySelector('.ytwTranscriptSegmentViewModelTimestamp,#timestamp,.segment-timestamp')?.textContent || ''
      );
      if (!timestamp) {
        const match = rawText.match(/\b\d{1,2}:\d{2}(?::\d{2})?\b/);
        timestamp = match ? match[0] : '';
      }
      let text = normalize(
        Array.from(element.querySelectorAll('span.ytAttributedStringHost,.segment-text,#content-text,.segment-text'))
          .map((node) => node.textContent || '')
          .join(' ')
      );
      if (!text || text === timestamp) {
        text = rawText
          .replace(new RegExp(`^${timestamp.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*`), '')
          .replace(/^\d+\s+(segundo|segundos|minuto|minutos|hora|horas)\s*/i, '');
      }
      return { index, timestamp, text: normalize(text), rawText };
    }).filter((segment) => segment.timestamp && segment.text);
    return {
      ok: segments.length > 0,
      reason: segments.length ? 'segments_found' : 'description_button_present_segments_not_loaded',
      events,
      playerError: normalize(document.body.innerText).includes('Algo deu errado. Atualize ou tente de novo depois.'),
      segmentCount: segments.length,
      segments,
    };
  });
}
""".strip()


def data_root() -> Path:
    return Path(os.environ.get("MSF_DATA_DIR", "data"))


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def video_id_from_url(value: str) -> str:
    return value.split("v=")[-1].split("&")[0].strip()


def timestamp_seconds(value: str) -> float | None:
    parts = [part for part in value.strip().split(":") if part]
    if not parts or not all(part.isdigit() for part in parts):
        return None
    total = 0
    for part in parts:
        total = total * 60 + int(part)
    return float(total)


def clean_text(text: str, timestamp: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if timestamp:
        text = re.sub(rf"^{re.escape(timestamp)}\s*", "", text)
    return re.sub(r"^\d+\s+(segundo|segundos|minuto|minutos|hora|horas)\s*", "", text, flags=re.I).strip()


def normalize_segments(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[float, str]] = set()
    for item in items:
        timestamp = str(item.get("timestamp") or "").strip()
        start = timestamp_seconds(timestamp)
        text = clean_text(str(item.get("text") or item.get("rawText") or ""), timestamp)
        if start is None or not text:
            continue
        key = (start, text)
        if key in seen:
            continue
        seen.add(key)
        normalized.append({"index": len(normalized), "start_seconds": start, "duration_seconds": None, "text": text})
    normalized.sort(key=lambda segment: (segment["start_seconds"], segment["index"]))
    for index, segment in enumerate(normalized):
        segment["index"] = index
    for index, segment in enumerate(normalized[:-1]):
        segment["duration_seconds"] = round(
            max(0.0, float(normalized[index + 1]["start_seconds"]) - float(segment["start_seconds"])),
            3,
        )
    return normalized


def run_cli(session: str, command: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    npx = shutil.which("npx.cmd") or shutil.which("npx")
    if not npx:
        raise FileNotFoundError("npx not found on PATH")
    return subprocess.run(
        [npx, "--yes", "--package", "@playwright/cli", "playwright-cli", "--session", session, *command],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture a YouTube transcript via the MSF legacy UI fallback.")
    parser.add_argument("--url")
    parser.add_argument("--video-id")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--session", default="msf-youtube-transcript")
    parser.add_argument("--timeout", type=int, default=150)
    args = parser.parse_args()

    if not args.url and not args.video_id:
        parser.error("pass --url or --video-id")
    video_id = args.video_id or video_id_from_url(args.url or "")
    url = args.url or f"https://www.youtube.com/watch?v={video_id}"
    output = args.output or data_root() / "raw" / "youtube" / video_id / "transcript_original.json"

    tmp_dir = Path(".tmp")
    tmp_dir.mkdir(exist_ok=True)
    js_path = tmp_dir / "youtube_transcript_legacy_capture_skill.js"
    js_path.write_text(LEGACY_CAPTURE_JS, encoding="utf-8")

    start = time.time()
    opened = run_cli(args.session, ["open", url], timeout=args.timeout)
    if opened.returncode:
        raise RuntimeError(opened.stderr[-1500:] or opened.stdout[-1500:])
    captured = run_cli(args.session, ["--raw", "run-code", "--filename", str(js_path)], timeout=args.timeout + 90)
    if captured.returncode:
        raise RuntimeError(captured.stderr[-1500:] or captured.stdout[-1500:])

    result = json.loads(captured.stdout)
    segments = normalize_segments(result.get("segments", []))
    payload = {
        "schema_version": "1.0",
        "youtube_video_id": video_id,
        "source_kind": "transcript",
        "language": "pt",
        "provider": "youtube_ui_playwright_legacy_description",
        "collected_at": utc_now(),
        "segments": segments,
    }
    tmp_output = output.with_suffix(".json.tmp")
    tmp_output.parent.mkdir(parents=True, exist_ok=True)
    tmp_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if len(segments) == 0 or tmp_output.stat().st_size <= 50 * 1024:
        tmp_output.unlink(missing_ok=True)
        print(json.dumps({
            "status": "failed",
            "reason": result.get("reason", "no_usable_segments"),
            "video_id": video_id,
            "segments": len(segments),
            "elapsed_s": round(time.time() - start, 1),
            "player_error_seen": result.get("playerError"),
            "events": result.get("events", []),
        }, ensure_ascii=False))
        return 2

    tmp_output.replace(output)
    print(json.dumps({
        "status": "success",
        "video_id": video_id,
        "segments": len(segments),
        "bytes": output.stat().st_size,
        "output": str(output),
        "elapsed_s": round(time.time() - start, 1),
        "events": result.get("events", []),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
