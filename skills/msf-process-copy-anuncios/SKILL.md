---
name: msf-process-copy-anuncios
description: Use this Marketing Swipe File process skill to create, critique, or improve paid-ad copy, hooks, angles, short scripts, platform-specific creative briefs, and test matrices from curated insights. Trigger when the task asks for Meta ads, Reels or short-video ads, Google search ads, Google display ads, hook testing, creative direction, paid-traffic angles, or an audit of whether ads are ready for a blind baseline test.
---

# Copy Anuncios

Status: approved on 2026-07-08. MSF-S09 ads passed: with-skill won 4/4
pairs, 30/32 criteria, and 12/12 commercial-core cells with no pending
encoding defect.

## Workflow

1. Read `retrieval.md` and retrieve curated insights matching
   `process-copy-anuncios`, plus imported transversal module tags when they
   support the briefing.
2. Import `transversal:mecanismo-big-idea` and
   `transversal:prova-depoimentos` by reference from
   `skills/_modules/msf-transversal-copy/`; do not copy those modules into
   this playbook.
3. Build the ad system from evidence-backed decisions: platform, format, hook,
   angle, promise, proof or plausibility, script, creative direction, CTA, and
   test plan.
4. Cite every non-obvious internal claim as `[insight:<insight_id>]`; mark
   unsupported but standard craft guidance as `[generic-practice]`.
5. Draft the final ad set using `templates/output-template.md`.
6. Evaluate major revisions with `rubric.md` and the MSF-R09/S09 protocol
   before treating changed playbook behavior as approved.

## Imported Modules

- Import `transversal:mecanismo-big-idea` when the ad needs a causal bridge,
  differentiated angle, one belief, named mechanism, or a reason the promise
  can work now.
- Import `transversal:prova-depoimentos` when the ad needs proof, expert
  authority, testimonial logic, credibility, or claim-risk control.
- Deduplicate evidence by unique `insight_id` when both modules are imported.
  Known overlap ids `zoChfFHnlOQ-v2-0008` and `mCaFyZpXJdE-v2-0011` count once.
- Keep ad-specific logic here: hook, angle, short script, variation logic,
  platform fit, creative direction, edit notes, CTA, and testing order.
  Transversal claims stay at principle level.

## Ads Playbook

Use this sequence unless the briefing gives a stronger constraint:

1. Define the job of the ad before writing: Meta feed image, Reels or short
   video, Google search, Google display, retargeting, or traffic into VSL,
   quiz, lead magnet, or checkout. The first VSL or offer should be treated as
   part of the ad, offer, and monetization architecture, not as an isolated
   asset. [insight:v6luZ9KvmOI-v2-0004]
2. Start angle selection from benefit and persona before writing the promise.
   The promise should be born from who wants the benefit and why that persona
   cares, not from a generic market slogan. [insight:BbhJn8NXRso-v2-0004]
3. The hook must sell attention before it sells the offer. In low-ticket or
   cold-feed creative, headline and image can break pattern first while the
   explanation moves to the caption, script, or next funnel step.
   [insight:TOW0sWhPaZw-v2-0013]
4. When a visual hook is already working, lateralize it by changing footage,
   framing, object, gesture, or angle while preserving the validated attention
   mechanism. [insight:YcqJ_vrjf-g-v2-0005]
5. Even hooks written from zero should start from observed signals in organic
   content, old copy, customer language, or market patterns, so the writer is
   not inventing attention from taste alone. [insight:wHdyTM-nVqg-v2-0009]
6. Separate hook, visual, promise, and CTA before testing. This lets the team
   vary one surface at a time without losing the learning from a winning
   creative. [insight:YcqJ_vrjf-g-v2-0001]
   [insight:YcqJ_vrjf-g-v2-0004] [insight:YcqJ_vrjf-g-v2-0006]
7. If a name, headline, or short angle wins, use it as a signal for the next
   mechanism or product angle to build, not only as a cosmetic naming win.
   [insight:mCaFyZpXJdE-v2-0002]
8. Keep proven winners live while testing new creative with more budget. Do
   not replace current ROI with an unproven hypothesis just because the new
   idea is more interesting to the team. [insight:L7u7r6rOl68-v2-0012]
9. In low-ticket acquisition, treat creative volume and renewal as a dominant
   scale variable after the account has a minimum viable campaign structure.
   [insight:mCaFyZpXJdE-v2-0022]
10. When an offer already shows sales signal, changing creative format can have
    more leverage than small checkout, banner, or page tweaks.
    [insight:mCaFyZpXJdE-v2-0019]
11. Diagnose ad failure before discarding the angle. Hook rate, play rate, and
    retention help separate an attention problem from a mismatch between
    audience, promise, and offer. [insight:BbhJn8NXRso-v2-0006]
12. Turn validated angles into reusable lead blocks when speed matters. A
    generic lead can refresh several working creatives if the underlying angle
    stays intact. [insight:mCaFyZpXJdE-v2-0020]
13. Brief editing and production with the strategic intent of the hook, rhythm,
    proof, and CTA, so the visual cut reinforces the sale instead of merely
    looking polished. [insight:wHdyTM-nVqg-v2-0011]
14. Judge ad copy by commercial effect in the funnel, not by writer preference
    or text elegance alone. [insight:YcqJ_vrjf-g-v2-0007]
15. Build a disciplined production rhythm for copy and creative. The ad system
    should not depend on whether the team felt inspired to study or edit on a
    given day. [insight:BbhJn8NXRso-v2-0002]
16. After validating an initial offer, reuse its learning about copy, angle,
    and objections to guide the next tests. [insight:wHdyTM-nVqg-v2-0002]

## Output Requirements

Every ads output should include:

- Briefing summary: product, avatar, awareness level, platform, format,
  traffic temperature, offer or destination, and constraints.
- Strategic hypothesis: angle, hook mechanism, belief or proof gap, and the
  main commercial risk.
- Ad set: 3+ variants when the briefing allows, each with hook, primary text or
  script, CTA, proof/plausibility cue, and creative direction.
- Platform fit: why the copy and format fit the selected channel.
- Test matrix: what variable changes across variants and what metric decides
  whether the angle survives.
- Production notes: visual, footage, edit, image, layout, or search-intent
  details that a creator or traffic buyer can execute.
- Citation map: each non-obvious rule or strategic choice mapped to
  `insight_id`.

## No Invention

- Use only `curated_insights` as source material unless the owner explicitly
  reopens curation.
- Do not count the same `insight_id` twice when it appears in both imported
  modules.
- Do not let a transversal module decide ad-specific hook, angle, platform
  fit, script shape, creative direction, CTA, or variation plan.
- If retrieved evidence does not support a claim, mark it `[generic-practice]`,
  narrow it, or remove it.

## Writing Policy

- Internal playbook, retrieval notes, contract fields, and editorial summaries
  use ASCII via NFKD transliteration when representing Portuguese without
  accents.
- Evidence quotes stay verbatim UTF-8. Never normalize or strip accents from
  quotes.
- Final outputs, examples, and templates use full pt-BR accents and correct
  spelling.
