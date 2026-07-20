import { createHash } from "node:crypto";
import { appendFile, mkdir, readFile, rename, stat, writeFile } from "node:fs/promises";
import path from "node:path";

const SCHEMA_VERSION = "1.0.0";

function now() {
  return new Date().toISOString();
}

function monotonicMs(started) {
  return Math.round((globalThis.performance.now() - started) * 1000) / 1000;
}

async function atomicWriteJson(target, payload) {
  await mkdir(path.dirname(target), { recursive: true });
  const temporary = `${target}.${globalThis.process?.pid || "node"}.tmp`;
  await writeFile(temporary, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  await rename(temporary, target);
}

async function appendJsonl(target, payload) {
  await mkdir(path.dirname(target), { recursive: true });
  await appendFile(target, `${JSON.stringify(payload)}\n`, "utf8");
}

export function timestampSeconds(value) {
  if (typeof value !== "string" || !/^\d+(?::\d+){1,2}$/.test(value.trim())) return null;
  return value.trim().split(":").reduce((total, part) => total * 60 + Number(part), 0);
}

export function manifestHash(items) {
  const body = JSON.stringify(items.map((item) => ({
    video_id: item.video_id,
    youtube_url: item.youtube_url,
    episode_priority: Number(item.episode_priority || 0),
    duration_seconds: Number(item.duration_seconds || 0),
  })));
  return createHash("sha256").update(body).digest("hex");
}

export function normalizeSegments(raw) {
  const normalized = [];
  for (const item of raw || []) {
    const start = timestampSeconds(String(item.timestamp || ""));
    const text = String(item.text || "").trim().replace(/\s+/g, " ");
    if (start === null || !text) continue;
    if (normalized.length && start < normalized.at(-1).start_seconds) return [];
    normalized.push({ index: normalized.length, start_seconds: start, duration_seconds: null, text });
  }
  for (let index = 0; index < normalized.length - 1; index += 1) {
    normalized[index].duration_seconds = Math.max(
      0,
      normalized[index + 1].start_seconds - normalized[index].start_seconds,
    );
  }
  return normalized;
}

export function validateSegments(segments, expectedVideoId, currentUrl) {
  const errors = [];
  const current = new URL(currentUrl);
  if (current.searchParams.get("v") !== expectedVideoId) errors.push("video_id_mismatch");
  if (!Array.isArray(segments) || segments.length === 0) errors.push("segments_missing_or_empty");
  let previous = -1;
  for (const [index, segment] of (segments || []).entries()) {
    if (!segment.text) errors.push(`segment_${index}_text_empty`);
    if (!Number.isFinite(segment.start_seconds) || segment.start_seconds < previous) {
      errors.push(`segment_${index}_order_invalid`);
    }
    previous = segment.start_seconds;
  }
  return { valid: errors.length === 0, errors };
}

async function readJsonIfPresent(target) {
  try {
    return JSON.parse(await readFile(target, "utf8"));
  } catch (error) {
    if (error?.code === "ENOENT") return null;
    throw error;
  }
}

export async function pendingItems(items, checkpointDir) {
  const hash = manifestHash(items);
  const pending = [];
  for (const item of items) {
    const result = await readJsonIfPresent(path.join(checkpointDir, "results", `${item.video_id}.json`));
    if (!result || result.manifest_sha256 !== hash || !["captured", "no_ui", "failed"].includes(result.status)) {
      pending.push(item);
    }
  }
  return pending;
}

async function waitForDescription(tab, videoId, timeoutMs) {
  const started = globalThis.performance.now();
  while (monotonicMs(started) < timeoutMs) {
    const state = await tab.playwright.evaluate((expected) => ({
      videoId: new URL(location.href).searchParams.get("v"),
      heading: Boolean(document.querySelector("h1")),
      description: Boolean(document.querySelector("ytd-watch-metadata #description, ytd-text-inline-expander")),
      expected,
    }), videoId, { timeoutMs: Math.min(timeoutMs, 3000) });
    if (state.videoId === videoId && state.heading && state.description) return true;
    await tab.playwright.waitForTimeout(250);
  }
  return false;
}

async function readTranscriptDom(tab) {
  return await tab.playwright.evaluate(() => {
    const clean = (value) => String(value || "").trim().replace(/\s+/g, " ");
    const nodes = Array.from(document.querySelectorAll(
      "transcript-segment-view-model,ytd-transcript-segment-renderer",
    )).filter((element) => !element.closest("[hidden]"));
    return {
      url: location.href,
      title: document.title,
      segments: nodes.map((element, index) => ({
        index,
        timestamp: clean(element.querySelector(
          ".ytwTranscriptSegmentViewModelTimestamp,#timestamp,.segment-timestamp",
        )?.textContent),
        text: clean(Array.from(element.querySelectorAll(
          "span.ytAttributedStringHost,.segment-text,#content-text",
        )).map((node) => clean(node.textContent)).filter(Boolean).join(" ")),
      })).filter((segment) => segment.timestamp && segment.text),
    };
  });
}

async function waitForTranscript(tab, timeoutMs) {
  const started = globalThis.performance.now();
  let capture = await readTranscriptDom(tab);
  while (!capture.segments.length && monotonicMs(started) < timeoutMs) {
    await tab.playwright.waitForTimeout(250);
    capture = await readTranscriptDom(tab);
  }
  return capture;
}

async function waitForTranscriptControl(tab, timeoutMs) {
  const started = globalThis.performance.now();
  while (monotonicMs(started) < timeoutMs) {
    const control = tab.playwright.locator('[aria-label="Mostrar transcrição"]').filter({ visible: true });
    const count = await control.count();
    if (count === 1) return control;
    if (count > 1) throw new Error(`ambiguous_transcript_button:${count}`);
    await tab.playwright.waitForTimeout(250);
  }
  return null;
}

async function clickAfterStateRefresh(tab, selector) {
  let locator = tab.playwright.locator(selector).filter({ visible: true });
  let count = await locator.count();
  if (count !== 1) throw new Error(`ambiguous_or_missing_click_target:${selector}:${count}`);
  try {
    await locator.click({ timeoutMs: 20000 });
  } catch (error) {
    if (!String(error?.message || error).includes("Timed out")) throw error;
    await tab.playwright.domSnapshot();
    locator = tab.playwright.locator(selector).filter({ visible: true });
    count = await locator.count();
    if (count !== 1) throw new Error(`retryable_loading:click_target_changed:${selector}:${count}`);
    await locator.click({ timeoutMs: 20000 });
  }
}

async function captureOne({ tab, item, checkpointDir, manifestSha256, timeoutMs, panelTimeoutMs }) {
  const videoId = item.video_id;
  const resultPath = path.join(checkpointDir, "results", `${videoId}.json`);
  const ledgerPath = path.join(checkpointDir, "browser-ledger.jsonl");
  const capturePath = path.join(checkpointDir, "captures", `${videoId}.json`);
  const priorResult = await readJsonIfPresent(resultPath);
  const attempt = Number(priorResult?.attempt || 0) + 1;
  const totalStarted = globalThis.performance.now();
  const phases = {};
  let result;
  try {
    let started = globalThis.performance.now();
    const targetUrl = item.youtube_url || `https://www.youtube.com/watch?v=${videoId}`;
    const currentUrl = await tab.url();
    if (new URL(currentUrl || "about:blank").searchParams.get("v") !== videoId) {
      await tab.goto(targetUrl);
      await tab.playwright.waitForLoadState({ state: "domcontentloaded", timeoutMs }).catch(() => {});
    }
    if (!(await waitForDescription(tab, videoId, timeoutMs))) {
      throw new Error("retryable_loading:description_not_ready");
    }
    phases.browser_navigation_ms = monotonicMs(started);

    started = globalThis.performance.now();
    await tab.playwright.domSnapshot();
    const more = tab.playwright.locator("tp-yt-paper-button#expand").filter({ visible: true });
    const moreCount = await more.count();
    if (moreCount > 1) throw new Error("ambiguous_description_button");
    if (moreCount === 1) {
      await clickAfterStateRefresh(tab, "tp-yt-paper-button#expand");
      await tab.playwright.domSnapshot();
    }
    phases.description_expand_ms = monotonicMs(started);

    started = globalThis.performance.now();
    const transcript = await waitForTranscriptControl(tab, panelTimeoutMs);
    if (!transcript) {
      result = {
        schema_version: SCHEMA_VERSION,
        kind: "vturb_browser_checkpoint",
        video_id: videoId,
        episode_priority: Number(item.episode_priority || 0),
        status: "no_ui",
        attempt,
        reason: "description_transcript_button_absent",
        manifest_sha256: manifestSha256,
        phases,
        duration_ms: monotonicMs(totalStarted),
        finished_at: now(),
      };
    } else {
      await clickAfterStateRefresh(tab, '[aria-label="Mostrar transcrição"]');
      const capture = await waitForTranscript(tab, panelTimeoutMs);
      phases.transcript_panel_ms = monotonicMs(started);

      started = globalThis.performance.now();
      const segments = normalizeSegments(capture.segments);
      const validation = validateSegments(segments, videoId, capture.url);
      if (!validation.valid) throw new Error(validation.errors.join(";"));
      const payload = {
        schema_version: "1.0",
        youtube_video_id: videoId,
        source_kind: "transcript",
        language: "pt",
        provider: "youtube_ui_chrome_dom",
        collected_at: now(),
        segments,
      };
      await atomicWriteJson(capturePath, payload);
      phases.browser_serialize_ms = monotonicMs(started);
      result = {
        schema_version: SCHEMA_VERSION,
        kind: "vturb_browser_checkpoint",
        video_id: videoId,
        episode_priority: Number(item.episode_priority || 0),
        status: "captured",
        attempt,
        capture_path: capturePath,
        segment_count: segments.length,
        last_timestamp: segments.at(-1).start_seconds,
        bytes: (await stat(capturePath)).size,
        manifest_sha256: manifestSha256,
        phases,
        duration_ms: monotonicMs(totalStarted),
        finished_at: now(),
      };
    }
  } catch (error) {
    const reason = String(error?.message || error);
    const retryable = reason.startsWith("retryable_loading:") || reason.includes("Timed out") || reason === "segments_missing_or_empty";
    result = {
      schema_version: SCHEMA_VERSION,
      kind: "vturb_browser_checkpoint",
      video_id: videoId,
      episode_priority: Number(item.episode_priority || 0),
      status: retryable && attempt < 2 ? "retryable" : "failed",
      attempt,
      reason,
      manifest_sha256: manifestSha256,
      phases,
      duration_ms: monotonicMs(totalStarted),
      finished_at: now(),
    };
  }
  await atomicWriteJson(resultPath, result);
  await appendJsonl(ledgerPath, { logged_at: now(), ...result });
  return result;
}

export async function captureCatalogBatch({
  tab,
  items,
  checkpointDir,
  maxItems = null,
  timeoutMs = 8000,
  panelTimeoutMs = 4000,
}) {
  const ordered = [...items].sort((a, b) => Number(a.episode_priority || 0) - Number(b.episode_priority || 0));
  const manifestSha256 = manifestHash(ordered);
  await atomicWriteJson(path.join(checkpointDir, "manifest.json"), {
    schema_version: SCHEMA_VERSION,
    kind: "vturb_browser_manifest",
    manifest_sha256: manifestSha256,
    generated_at: now(),
    item_count: ordered.length,
    items: ordered,
  });
  let work = await pendingItems(ordered, checkpointDir);
  if (maxItems !== null) work = work.slice(0, maxItems);
  const results = [];
  for (const item of work) {
    results.push(await captureOne({ tab, item, checkpointDir, manifestSha256, timeoutMs, panelTimeoutMs }));
  }
  const completed = await pendingItems(ordered, checkpointDir);
  const durations = results.map((item) => item.duration_ms).sort((a, b) => a - b);
  return {
    schema_version: SCHEMA_VERSION,
    kind: "vturb_browser_batch_summary",
    manifest_sha256: manifestSha256,
    attempted: results.length,
    captured: results.filter((item) => item.status === "captured").length,
    no_ui: results.filter((item) => item.status === "no_ui").length,
    retryable: results.filter((item) => item.status === "retryable").length,
    failed: results.filter((item) => item.status === "failed").length,
    p50_duration_ms: durations.length ? durations[Math.floor((durations.length - 1) / 2)] : null,
    remaining: completed.length,
    results,
  };
}
