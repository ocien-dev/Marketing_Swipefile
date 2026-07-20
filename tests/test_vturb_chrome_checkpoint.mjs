import assert from "node:assert/strict";
import { mkdtemp } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  manifestHash,
  normalizeSegments,
  pendingItems,
  timestampSeconds,
  validateSegments,
} from "../scripts/vturb_chrome_checkpoint.mjs";

test("timestamp parsing and stale-tail rejection", () => {
  assert.equal(timestampSeconds("1:02:03"), 3723);
  assert.equal(timestampSeconds("bad"), null);
  assert.deepEqual(normalizeSegments([
    { timestamp: "0:00", text: "start" },
    { timestamp: "1:00", text: "end" },
    { timestamp: "0:30", text: "stale" },
  ]), []);
});

test("normalized capture validates the exact current video", () => {
  const segments = normalizeSegments([
    { timestamp: "0:00", text: "start" },
    { timestamp: "0:10", text: "end" },
  ]);
  assert.equal(validateSegments(segments, "video000001", "https://www.youtube.com/watch?v=video000001").valid, true);
  assert.deepEqual(
    validateSegments(segments, "video000001", "https://www.youtube.com/watch?v=other000001").errors,
    ["video_id_mismatch"],
  );
});

test("manifest hash is stable and unfinished items remain pending", async () => {
  const items = [
    { video_id: "video000001", youtube_url: "https://youtu.be/video000001", episode_priority: 1, duration_seconds: 10 },
    { video_id: "video000002", youtube_url: "https://youtu.be/video000002", episode_priority: 2, duration_seconds: 20 },
  ];
  assert.equal(manifestHash(items), manifestHash(items));
  const root = await mkdtemp(path.join(os.tmpdir(), "vturb-browser-test-"));
  assert.deepEqual((await pendingItems(items, root)).map((item) => item.video_id), ["video000001", "video000002"]);
});

