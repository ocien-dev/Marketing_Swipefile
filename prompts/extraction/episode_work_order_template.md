# Gold Episode Work Order (per-episode)

This is the episode-specific input for a gold extraction. It carries only what
changes between episodes. The reusable extraction rules live once in
`docs/gold-extraction-contract.md` (the single normative source) and in
`prompts/extraction/episode_gold_standard_small_model.md` (the episode-agnostic
task prompt). Do not restate the rules here.

## Episode binding

- YouTube video ID: `<video_id>`
- Live data root: `<data_root>` (default `C:\MSF-data\Marketing_Swipe_File`)
- Episode title: `<title>`

## Known problems to verify (optional)

List any source defects already suspected for this episode, so the reader can
verify them against the files instead of assuming them. These are starting
points, never facts to trust. Example shape:

- The source transcript contains `<N>` segments.
- The first `<M>` segments appear to be the real episode.
- The final `<K>` segments appear to be unrelated recommended-video titles
  captured by the YouTube UI snapshot collector.
- Any chunk whose start time is greater than its end time.

Leave empty when no defect is suspected. Never invent a defect to fill this.

## Mandatory calibration checks (optional)

List source claims that must be captured separately if the clean transcript
confirms them verbatim. These are calibration probes, not the complete answer,
and must not be forced into the output when the transcript does not support
them. Example shape:

- approximately `<N>` front-end buyers per month;
- extending a VSL from approximately `<A>` to `<B>` minutes;
- the price movement from approximately `<X>` to `<Y>`;
- the business effect of a `<Z>` percent conversion improvement at high volume.

If any listed check is not found, document the search and the evidence result.
Leave empty when there are no pre-identified calibration probes.

## Historical example

The original L7u7r6rOl68 seed work order (video
`Lucrando Multiplos 7D/Mes Com Perpetuo White (Aos 21 Anos!) | Lucas Ramos -
Segredos da Escala #140`) is preserved verbatim for provenance in
`prompts/extraction/episode_work_order_L7u7r6rOl68.md`.
