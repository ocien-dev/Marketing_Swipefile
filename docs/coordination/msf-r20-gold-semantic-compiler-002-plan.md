# MSF-R20 Gold Semantic Compiler 002

Status: archived_research_not_for_production
Production status: read_only_benchmark
Date: 2026-07-17

Canonical production route: `chronological_hybrid_v1`; see
`msf-r20-gold-canonical-hybrid-001-plan.md`.

## Objective

Validate the semantic compiler with independent model outputs rather than an
approved-gold replay.  Three completed episodes form a short, medium, and long
benchmark band.  Approved candidates are hidden during extraction and become
visible only to the scoring phase.

## Episodes

- `AqzF_M2mM04`: 395 segments, 17 approved candidates, relation-heavy.
- `eCaODMtU5GY`: 1,079 segments, 48 approved candidates, procedural.
- `NiT0-ABoVnk`: 1,087 segments, 59 approved candidates, numeric/caveated.

## Architecture under test

1. WSL prepares chronological, oracle-free shard requests.
2. Ephemeral `gpt-5.6-terra/high` calls compile shards concurrently.  The
   transport working directory contains no approved candidates, calls run with
   a read-only sandbox, and any tool-use event invalidates the result.
3. A deterministic reducer hydrates evidence text from selected source segment
   IDs, validates core ownership and literal evidence, and produces a compact
   comparison bundle.
4. One `gpt-5.6-sol/high` judge per episode compares the independent atoms with
   the frozen approved gold and source evidence.  This is evaluation, not
   extraction.
5. The adoption report combines deterministic and Sol judgments without
   changing any approved gold, packet, audit, status, or fingerprint.

## Acceptance

- all shard requests contain no approved candidate IDs;
- every accepted atom references an existing segment and at least one core
  segment from its owning shard;
- all model calls are ephemeral and contain zero tool-use events;
- three episodes complete with measured wall time and token usage;
- material recall, unsupported claims, numbers, procedures, caveats, relations,
  calibration coverage, and judge findings are reported separately;
- production adoption requires non-inferior material recall, zero unsupported
  claims, no increase in final-audit findings, and under ten minutes per
  episode in the standard band;
- approved data and packet hashes remain unchanged.

## Safety

The benchmark writes only job-local artifacts.  The Windows Codex executable is
used solely as the authenticated model transport because no API key or Linux
Codex binary is present.  Source preparation and deterministic scoring remain
on the approved Linux runtime.  A model response is rejected if its event log
shows command, file, browser, MCP, or other tool use.

## Pilot result

The owner authorized the short episode only.  `AqzF_M2mM04` completed seven
blind `gpt-5.6-terra/high` shard calls in 88.821 seconds and one
`gpt-5.6-sol/high` evaluation in 221.010 seconds.  All calls were ephemeral,
schema-valid, and had zero tool-use events.

The speed target passed, but the quality gate failed: material recall was
0.8529, one unsupported claim remained, and the Sol judge opened six findings.
The main losses were one omitted material candidate, incomplete quantitative
and procedural capture, and failure to reconstruct the parent/child framework.
The architecture is therefore not production-ready and the two long prepared
episodes were not sent to models.
