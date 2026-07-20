---
name: marketing-swipe-file-youtube-transcripts
description: Capture Marketing Swipe File YouTube podcast transcripts through the validated YouTube UI fallback. Use when direct timedtext/caption collection returns empty, `transcript_original.json` is tiny or missing, `transcript_fallback_needed.md` exists, or Codex needs to recover VTurb/Segredos da Escala YouTube transcripts without a paid API.
---

# Marketing Swipe File YouTube Transcripts

## Core Rule

Use the real Chrome UI path before declaring a YouTube episode transcript unavailable:

1. Use the Chrome-control skill and the user's connected Chrome profile. Do not start with a fresh headless browser when the real Chrome session is available.
2. Expand the video description with `...mais` / `Mostrar mais`.
3. Click `Mostrar transcricao` inside `ytd-video-description-transcript-section-renderer`, not only buttons near the player.
4. Verify the `Neste video` panel opens with the `Transcricao` tab selected. If a role-based click times out, use the visible DOM node for `Mostrar transcricao` and re-snapshot.
5. Read `transcript-segment-view-model` nodes. Each node exposes `.ytwTranscriptSegmentViewModelTimestamp` and `span.ytAttributedStringHost`.
6. Save `transcript_original.json` only when the generated JSON is usable: above 50KB, language `pt`, and containing timestamped segments.

If the button appears but no segments load, report that exact failure. Do not call it "sem legenda" unless the description transcript button is absent.

## Chrome Capture

Use a bounded read-only DOM projection after the panel is visible. Preserve the original text and convert the timestamp to seconds only when writing the MSF payload.

```javascript
Array.from(document.querySelectorAll('transcript-segment-view-model'))
  .map((element, index) => ({
    index,
    timestamp: element.querySelector('.ytwTranscriptSegmentViewModelTimestamp')?.textContent?.trim(),
    text: element.querySelector('span.ytAttributedStringHost')?.textContent?.replace(/\s+/g, ' ').trim(),
  }))
  .filter((segment) => segment.timestamp && segment.text)
```

The Chrome UI path was live-validated on `L7u7r6rOl68` (SDE #140): 1,941 segments from `0:00` through `3:51:27`.

## Legacy CLI Fallback

From `C:\Users\luish\OneDrive\Code\Marketing_Swipe_File`:

```powershell
$env:MSF_DATA_DIR = "C:\MSF-data\Marketing_Swipe_File"
.\.venv\Scripts\python.exe skills\marketing-swipe-file-youtube-transcripts\scripts\capture_youtube_transcript_legacy.py --video-id VIDEO_ID
```

For IDs beginning with `-`, pass the id with `--video-id=...` or use `--url`.

## Validation

After capture, verify:

```powershell
.\.venv\Scripts\python.exe scripts\normalize_transcript.py --input C:\MSF-data\Marketing_Swipe_File\raw\youtube\VIDEO_ID\transcript_original.json --output C:\MSF-data\Marketing_Swipe_File\processed\VIDEO_ID\content_segments.json
```

Then continue the normal MSF pipeline only if the transcript has enough timestamped segments.

## Resumable VTurb Backfill

Run the deterministic backfill in the certified WSL runtime. The script does
not call an LLM and never overwrites a valid transcript with an empty capture.

```powershell
wsl.exe --distribution Ubuntu-24.04 --user luish --cd /home/luish/src/Marketing_Swipe_File --exec /home/luish/src/Marketing_Swipe_File/.venv/bin/python -m scripts.backfill_vturb_transcripts --data-root /home/luish/msf-data/Marketing_Swipe_File --status-only
```

Use a bounded pilot before a full run:

```powershell
wsl.exe --distribution Ubuntu-24.04 --user luish --cd /home/luish/src/Marketing_Swipe_File --exec /home/luish/src/Marketing_Swipe_File/.venv/bin/python -m scripts.backfill_vturb_transcripts --data-root /home/luish/msf-data/Marketing_Swipe_File --routes metadata,direct,ui --max-items 5
```

The headless CLI route is not currently production-ready in the certified WSL
runtime. `@playwright/cli@0.0.60` accepts Node 18 but failed its command
protocol; the current CLI needs Node 20+ and the downloaded Chromium still
needs system libraries unavailable without sudo. Run one browser capability
preflight before any episode and open a circuit breaker on infrastructure
failure. Until that preflight passes, use connected real Chrome rather than
repeating headless attempts per video.

The durable state is `input/vturb_transcript_backfill_state.json`; compact
attempt evidence is appended to `logs/vturb_transcript_backfill.jsonl`. A
successful capture is staged and validated before promotion, then normalized
to `processed/<video_id>/content_segments.json` without running insight or
gold extraction.

`pending_chrome` is not a definitive absence. Verify that item in connected
Chrome. Only after the real description transcript surface is absent should
the operator mark it with `--mark-no-ui VIDEO_ID` and run the `asr` route with
`--allow-asr`. ASR uses local `faster-whisper`; no paid API is allowed.

For catalog waves, use `scripts/vturb_chrome_checkpoint.mjs`. It binds every
result to the manifest hash and writes `captures/<video_id>.json`,
`results/<video_id>.json` and `browser-ledger.jsonl` immediately after each
video. Expand the description and inspect the complete snapshot; visible-DOM
only is insufficient because `Mostrar transcricao` can be below the fold.
Use waves of at most eight items in the connected Chrome session.

The approved ASR configuration from the 2026-07-16 benchmark is
`large-v3-turbo`, CPU/int8, standard inference, chunks of 1,200 seconds and
two seconds of overlap. Do not substitute `small` or batch size 8: they kept
only 50% and 25% of reference numbers, respectively. Receipts under
`cache/vturb_transcript_backfill/asr-checkpoints` are authoritative for
resume; preserve them and promote only after full-file validation.

## Known Failure Pattern

In MSF-R19 lote 1 on 2026-07-10, headless Playwright could expose the `Mostrar transcricao` button yet leave the side panel in `loading`. Do not treat that as a definitive absence of transcript: retry the real Chrome UI path before escalating to local ASR.

When the real Chrome UI also has no `transcript-segment-view-model` nodes, report `description_button_present_segments_not_loaded`. The next fallback is local ASR, not paid API.
