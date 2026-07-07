#!/usr/bin/env python
"""Capture a YouTube transcript through the Playwright CLI transcript panel."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from collect_youtube_transcript_from_playwright_snapshot import extract_segments
from youtube_common import canonical_watch_url, extract_video_id, write_json


BUTTON_REF_RE = re.compile(r'- button "(?P<label>[^"]+)" \[ref=(?P<ref>[^\]]+)\]')

DOM_TRANSCRIPT_CODE = r"""
async (page) => {
  await page.waitForLoadState('domcontentloaded', { timeout: 45000 }).catch(() => {});
  await page.waitForTimeout(5500);
  await page.keyboard.press('Escape').catch(() => {});

  return await page.evaluate(async () => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const normalize = (value) => (value || '').trim().replace(/\s+/g, ' ');
    const buttonSelector = 'button,[role=button],yt-button-shape,ytd-button-renderer,tp-yt-paper-button';
    const labelFor = (element) => normalize(
      element.innerText || element.textContent || element.getAttribute('aria-label') || ''
    );
    const clickButton = async (patterns) => {
      const regexes = patterns.map((pattern) => new RegExp(pattern, 'i'));
      const elements = Array.from(document.querySelectorAll(buttonSelector));
      const target = elements.find((element) => regexes.some((pattern) => pattern.test(labelFor(element))));
      if (!target) return null;
      target.scrollIntoView({ block: 'center', inline: 'nearest' });
      await sleep(350);
      (target.querySelector('button') || target).click();
      await sleep(1500);
      return labelFor(target);
    };
    const readSegments = () => {
      const nodes = Array.from(document.querySelectorAll('transcript-segment-view-model,ytd-transcript-segment-renderer'));
      return nodes.map((element, index) => {
        const timestamp = normalize(
          element.querySelector('.ytwTranscriptSegmentViewModelTimestamp,#timestamp,.segment-timestamp')?.textContent
        );
        const textCandidates = Array.from(
          element.querySelectorAll('span.ytAttributedStringHost,.segment-text,#content-text,.segment-text')
        ).map((node) => normalize(node.textContent)).filter(Boolean);
        let text = textCandidates.join(' ');
        if (!text) {
          const lines = normalize(element.innerText || element.textContent)
            .split(/\s*(?:\n|\r)+\s*/)
            .map((line) => normalize(line))
            .filter(Boolean);
          text = lines.filter((line) => line !== timestamp && !/^\d+\s+(segundo|minuto|hora)/i.test(line)).join(' ');
        }
        return { index, timestamp, text: normalize(text) };
      }).filter((segment) => segment.timestamp && segment.text);
    };

    await clickButton(['^\\.\\.\\.mais$', '^mostrar\\s+mais$', '^show\\s+more$']);

    let segments = readSegments();
    let transcriptButton = null;
    if (!segments.length) {
      transcriptButton = await clickButton(['mostrar\\s+transcri', 'show\\s+transcript']);
      await sleep(3500);
      segments = readSegments();
    }

    const transcriptButtons = Array.from(document.querySelectorAll(buttonSelector))
      .map(labelFor)
      .filter((label) => /transcri|transcript/i.test(label))
      .slice(0, 20);
    return { segments, transcriptButton, transcriptButtons };
  });
}
""".strip()


def utc_now_slug() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_cli(session: str, command: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    npx = shutil.which("npx.cmd") or shutil.which("npx")
    if not npx:
        raise FileNotFoundError("Could not find npx or npx.cmd on PATH")
    completed = subprocess.run(
        [npx, "--yes", "--package", "@playwright/cli", "playwright-cli", "--session", session, *command],
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Playwright CLI command failed: "
            + " ".join(command)
            + "\nSTDOUT:\n"
            + completed.stdout[-4000:]
            + "\nSTDERR:\n"
            + completed.stderr[-4000:]
        )
    return completed


def run_code_json(session: str, code: str, timeout: int) -> dict[str, Any]:
    code_path = Path(".tmp") / "playwright_dom_transcript_code.js"
    code_path.parent.mkdir(parents=True, exist_ok=True)
    code_path.write_text(f"({code})", encoding="utf-8", newline="\n")
    completed = run_cli(session, ["--raw", "run-code", "--filename", str(code_path)], timeout=timeout)
    text = completed.stdout.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Playwright run-code returned non-JSON output: {text[:2000]}") from error


def timestamp_seconds(value: str | None) -> float | None:
    if not value:
        return None
    parts = [part for part in value.strip().split(":") if part]
    if not parts or not all(part.isdigit() for part in parts):
        return None
    numbers = [int(part) for part in parts]
    seconds = 0
    for number in numbers:
        seconds = seconds * 60 + number
    return float(seconds)


def normalize_dom_segments(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        start_seconds = timestamp_seconds(str(item.get("timestamp") or ""))
        text = " ".join(str(item.get("text") or "").split())
        if start_seconds is None or not text:
            continue
        normalized.append(
            {
                "index": index,
                "start_seconds": start_seconds,
                "duration_seconds": None,
                "text": text,
            }
        )

    for index, item in enumerate(normalized[:-1]):
        next_start = normalized[index + 1]["start_seconds"]
        duration = max(0.0, round(float(next_start) - float(item["start_seconds"]), 3))
        item["duration_seconds"] = duration
    return normalized


def capture_dom_segments(session: str, timeout: int) -> list[dict[str, Any]]:
    payload = run_code_json(session, DOM_TRANSCRIPT_CODE, timeout=timeout)
    segments = payload.get("segments") if isinstance(payload, dict) else None
    if not isinstance(segments, list):
        return []
    return normalize_dom_segments([item for item in segments if isinstance(item, dict)])


def latest_snapshot(root: Path, previous: set[Path]) -> Path:
    candidates = [path for path in root.glob("page-*.yml") if path not in previous and path.stat().st_size > 0]
    if not candidates:
        candidates = [path for path in root.glob("page-*.yml") if path.stat().st_size > 0]
    if not candidates:
        raise FileNotFoundError(f"No Playwright snapshot found under {root}")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def find_button_ref(snapshot_text: str, patterns: list[str]) -> str | None:
    compiled = [re.compile(pattern, flags=re.IGNORECASE) for pattern in patterns]
    for line in snapshot_text.splitlines():
        match = BUTTON_REF_RE.search(line)
        if not match:
            continue
        label = match.group("label")
        if any(pattern.search(label) for pattern in compiled):
            return match.group("ref")
    return None


def click_description_more(session: str, timeout: int) -> None:
    js = """
() => {
  const labels = [/^\\.\\.\\.mais$/i, /mostrar mais/i, /^show more$/i];
  const buttons = Array.from(document.querySelectorAll('button,[role=button],yt-button-shape,ytd-button-renderer'));
  const target = buttons.find((button) => {
    const text = (button.innerText || button.textContent || '').trim();
    return labels.some((pattern) => pattern.test(text));
  });
  if (!target) return false;
  target.scrollIntoView({ block: 'center' });
  (target.querySelector('button') || target).click();
  return true;
}
""".strip()
    run_cli(session, ["eval", js], timeout=timeout)


def wait_for_any_button_text(session: str, patterns: list[str], timeout: int, milliseconds: int) -> bool:
    pattern_json = json.dumps(patterns)
    js = f"""
() => new Promise((resolve) => {{
  const patterns = {pattern_json}.map((pattern) => new RegExp(pattern, 'i'));
  const selector = 'button,[role=button],yt-button-shape,ytd-button-renderer';
  const deadline = Date.now() + {milliseconds};
  const tick = () => {{
    const found = Array.from(document.querySelectorAll(selector)).some((button) => {{
      const text = `${{button.innerText || ''}} ${{button.textContent || ''}} ${{button.getAttribute('aria-label') || ''}}`;
      return patterns.some((pattern) => pattern.test(text.trim()));
    }});
    if (found) return resolve(true);
    if (Date.now() >= deadline) return resolve(false);
    setTimeout(tick, 500);
  }};
  tick();
}})
""".strip()
    result = run_cli(session, ["eval", js], timeout=timeout)
    return "true" in result.stdout


def click_show_transcript(session: str, timeout: int) -> bool:
    js = """
() => {
  const buttons = Array.from(document.querySelectorAll('button,[role=button],yt-button-shape,ytd-button-renderer'));
  const target = buttons.find((button) => {
    const text = `${button.innerText || ''} ${button.textContent || ''} ${button.getAttribute('aria-label') || ''}`;
    return /mostrar\\s+transcri|show\\s+transcript/i.test(text);
  });
  if (!target) return false;
  target.scrollIntoView({ block: 'center' });
  (target.querySelector('button') || target).click();
  return true;
}
""".strip()
    result = run_cli(session, ["eval", js], timeout=timeout)
    return '"true"' in result.stdout or "true" in result.stdout


def wait_for_panel(session: str, timeout: int, milliseconds: int = 2500) -> None:
    js = f"() => new Promise((resolve) => setTimeout(() => resolve(true), {milliseconds}))"
    run_cli(session, ["eval", js], timeout=timeout)


def capture_snapshot(session: str, snapshot_root: Path, timeout: int) -> Path:
    previous = set(snapshot_root.glob("page-*.yml")) if snapshot_root.exists() else set()
    run_cli(session, ["snapshot"], timeout=timeout)
    return latest_snapshot(snapshot_root, previous)


def snapshot_until_button(
    session: str,
    snapshot_root: Path,
    timeout: int,
    patterns: list[str],
    max_wait_seconds: int,
) -> tuple[Path, str, str | None]:
    deadline = time.time() + max_wait_seconds
    last_path: Path | None = None
    last_text = ""
    while True:
        snapshot_path = capture_snapshot(session, snapshot_root=snapshot_root, timeout=timeout)
        snapshot_text = snapshot_path.read_text(encoding="utf-8")
        button_ref = find_button_ref(snapshot_text, patterns)
        if button_ref or time.time() >= deadline:
            return snapshot_path, snapshot_text, button_ref
        last_path = snapshot_path
        last_text = snapshot_text
        time.sleep(5)


def snapshot_until_button_with_reload(
    session: str,
    snapshot_root: Path,
    timeout: int,
    patterns: list[str],
    max_wait_seconds: int,
) -> tuple[Path, str, str | None]:
    snapshot_path, snapshot_text, button_ref = snapshot_until_button(
        session,
        snapshot_root=snapshot_root,
        timeout=timeout,
        patterns=patterns,
        max_wait_seconds=max_wait_seconds,
    )
    if button_ref:
        return snapshot_path, snapshot_text, button_ref

    run_cli(session, ["reload"], timeout=timeout)
    time.sleep(12)
    return snapshot_until_button(
        session,
        snapshot_root=snapshot_root,
        timeout=timeout,
        patterns=patterns,
        max_wait_seconds=max_wait_seconds,
    )


def capture_transcript(url: str, output: Path, session: str, snapshot_root: Path, timeout: int) -> tuple[Path, int]:
    video_id = extract_video_id(url)
    run_cli(session, ["open", canonical_watch_url(video_id)], timeout=timeout)
    segments = capture_dom_segments(session, timeout=timeout)
    if segments:
        payload: dict[str, Any] = {
            "schema_version": "1.0",
            "youtube_video_id": video_id,
            "source_kind": "transcript",
            "language": "pt",
            "provider": "youtube_ui_playwright_cli_dom",
            "collected_at": utc_now_slug(),
            "segments": segments,
        }
        write_json(output, payload)
        return Path("(playwright-dom)"), len(segments)

    snapshot_path, snapshot_text, initial_ref = snapshot_until_button_with_reload(
        session,
        snapshot_root=snapshot_root,
        timeout=timeout,
        patterns=[r"^\.\.\.mais$", r"^mostrar\s+mais$", r"^show\s+more$", r"mostrar\s+transcri", r"show\s+transcript"],
        max_wait_seconds=45,
    )
    transcript_ref = find_button_ref(snapshot_text, [r"mostrar\s+transcri", r"show\s+transcript"])
    if not transcript_ref:
        more_ref = initial_ref or find_button_ref(snapshot_text, [r"^\.\.\.mais$", r"^mostrar\s+mais$", r"^show\s+more$"])
        if more_ref:
            run_cli(session, ["click", more_ref], timeout=timeout)
            snapshot_path, snapshot_text, transcript_ref = snapshot_until_button(
                session,
                snapshot_root=snapshot_root,
                timeout=timeout,
                patterns=[r"mostrar\s+transcri", r"show\s+transcript"],
                max_wait_seconds=20,
            )

    if not transcript_ref:
        raise RuntimeError(f"Could not find a 'Mostrar transcricao' button. Snapshot: {snapshot_path}")

    run_cli(session, ["click", transcript_ref], timeout=timeout)
    time.sleep(4)
    snapshot_path = capture_snapshot(session, snapshot_root=snapshot_root, timeout=timeout)
    snapshot_text = snapshot_path.read_text(encoding="utf-8")
    segments = extract_segments(snapshot_text)
    if not segments:
        raise RuntimeError(f"Transcript panel produced zero segments. Snapshot: {snapshot_path}")

    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "youtube_video_id": video_id,
        "source_kind": "transcript",
        "language": "pt",
        "provider": "youtube_ui_playwright_cli",
        "collected_at": utc_now_slug(),
        "segments": segments,
    }
    write_json(output, payload)
    return snapshot_path, len(segments)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="YouTube URL. Use this for ids beginning with '-' too.")
    parser.add_argument("--output", type=Path, help="Path to transcript_original.json")
    parser.add_argument("--output-root", default=Path("data/raw/youtube"), type=Path)
    parser.add_argument("--session", default="msf-transcript")
    parser.add_argument("--snapshot-root", default=Path(".playwright-cli"), type=Path)
    parser.add_argument("--timeout", default=90, type=int)
    args = parser.parse_args()

    video_id = extract_video_id(args.url)
    output_path = args.output or args.output_root / video_id / "transcript_original.json"
    snapshot_path, segment_count = capture_transcript(
        args.url,
        output=output_path,
        session=args.session,
        snapshot_root=args.snapshot_root,
        timeout=args.timeout,
    )
    print(f"Wrote {segment_count} transcript segment(s) to {output_path}")
    print(f"Snapshot: {snapshot_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
