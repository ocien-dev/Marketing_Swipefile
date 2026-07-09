---
name: msf-process-quiz
description: Use this Marketing Swipe File process skill to create, critique, or improve quiz funnels, diagnostic quizzes, segmentation quizzes, readiness quizzes, product-match quizzes, result pages, quiz-to-offer bridges, and quiz completion design from the v2 master retrieval pool. Trigger when the task asks for quiz questions, personalized results, mechanism belief, proof control, offer bridge, completion flow, or an audit of whether a quiz funnel is ready for a blind baseline test.
---

# Quiz

Status: approved on 2026-07-08. MSF-S09 quiz passed after external
reconfirmation: with-skill won 4/4 pairs, 32/32 criteria, and 12/12
commercial-core cells. The encoding CONCERNS was resolved by the hardened
guard and localized encoding-fixed sample.

## Workflow

1. Read `retrieval.md` and retrieve pool insights matching `process-quiz`,
   plus imported transversal module tags when they support the briefing.
2. Import `transversal:mecanismo-big-idea` and
   `transversal:prova-depoimentos` by reference from
   `skills/_modules/msf-transversal-copy/`; do not copy those modules into
   this playbook.
3. Build the quiz funnel from evidence-backed decisions: entry promise,
   diagnostic sequence, segmentation logic, personalized result, mechanism,
   proof or claim control, offer bridge, completion design, and test plan.
4. Cite every non-obvious internal claim as `[insight:<insight_id>]`; mark
   unsupported but standard quiz craft as `[generic-practice]`.
5. Draft the final quiz plan using `templates/output-template.md`.
6. Evaluate major revisions with `rubric.md` and the MSF-R09/S09 protocol
   before treating changed playbook behavior as approved.

## Imported Modules

- Import `transversal:mecanismo-big-idea` when the quiz needs one belief,
  named mechanism, causal bridge, or a reason the diagnosis naturally points
  to the offer.
- Import `transversal:prova-depoimentos` when the quiz result or offer bridge
  needs proof, credibility, testimonial logic, expert authority, or
  claim-risk control.
- Deduplicate evidence by unique `insight_id` when both modules are imported.
  Known overlap ids `zoChfFHnlOQ-v2-0008` and `mCaFyZpXJdE-v2-0011` count once.
- Keep quiz-specific logic here: diagnostic questions, segmentation branches,
  result personalization, page sequence, mini VSL placement, offer bridge,
  completion design, and quiz analytics. Transversal claims stay at principle
  level.

## Quiz Funnel Playbook

Use this sequence unless the briefing gives a stronger constraint:

1. Sell the consumption of the quiz before selling the offer. The first
   promise should make the lead want the diagnosis, score, type, or plan they
   will receive by answering. [insight:TOW0sWhPaZw-v2-0001]
2. Treat the first question as the 80/20 of the quiz. It must pull the lead
   into the process and make the implicit diagnostic promise feel relevant.
   [insight:TOW0sWhPaZw-v2-0010]
3. Make questions create self-recognition, not just data capture. The sequence
   should help the lead reach a conclusion about their own pain, constraint,
   desire, or readiness. [insight:TOW0sWhPaZw-v2-0009]
4. Earn attention before explaining mechanism. The opening screens should
   justify continuation and reduce friction before the quiz asks for belief in
   the solution. [insight:mCaFyZpXJdE-v2-0016]
5. Align the creative promise, quiz mechanism, question logic, and result
   page. If the mechanism does not match the idea that brought the lead in,
   the quiz becomes meaningless friction. [insight:TOW0sWhPaZw-v2-0002]
6. Define one belief for the whole funnel before writing questions. Ad,
   quiz, result, VSL, checkout, and follow-up should all reinforce the same
   central belief instead of opening competing theses.
   [insight:mCaFyZpXJdE-v2-0004]
7. Use a longer quiz only when each screen earns a microdecision. Multi-step
   funnels can convert well when every page maintains engagement instead of
   repeating the same argument. [insight:mCaFyZpXJdE-v2-0015]
8. Use the result page to interpret answers and anchor belief. A mini VSL or
   short explanation after the diagnostic should organize the belief work the
   questions prepared. [insight:TOW0sWhPaZw-v2-0003]
9. After the quiz raises awareness, the mini VSL can focus on proving the
   "how" instead of rebuilding the whole problem from zero.
   [insight:TOW0sWhPaZw-v2-0012]
10. If the offer needs more belief or a higher ticket, split diagnostic and
    direct-sale jobs: one mini VSL can diagnose before the sale and a final,
    tighter VSL can convert. [insight:mCaFyZpXJdE-v2-0018]
11. Treat the mini VSL as a likely abandonment point. The quiz plan should
    state what makes the video worth watching and how to measure drop-off.
    [insight:TOW0sWhPaZw-v2-0015]
12. Make the result feel personal by reflecting back the answer pattern, then
    bridge to the offer as the logical next step for that pattern.
    [insight:TOW0sWhPaZw-v2-0009] [generic-practice]
13. Use mechanism as the bridge from promise to purchase. The result should
    explain why the desired outcome is possible and why the offer is the next
    step, not merely display a score. [insight:zoChfFHnlOQ-v2-0009]
14. Use proof carefully in the result and bridge. Review proof from the
    customer's point of view: does it make the promised next step credible, or
    is it only impressive internally? [insight:yyoGeQp5yzM-v2-0002]
15. For ascension or backend quizzes, combine several stimuli and a perceived
    result before asking for the next level. A single pitch rarely carries the
    whole upgrade. [insight:JF2oC44lBG8-v2-0013]
16. Diagnose the quiz by stage. Separate marketing, quiz engagement, VSL,
    checkout, and upsell before deciding what to rewrite.
    [insight:aSFAve1klsc-v2-0004] [insight:qj04cUeaRAw-v2-0008]
17. Measure drop-off by quiz page. If page three loses half the leads, rewrite
    that screen, question, or promise before blaming the whole funnel.
    [insight:TOW0sWhPaZw-v2-0014]

## Output Requirements

Every quiz output should include:

- Briefing summary: market, avatar, awareness level, offer, traffic source,
  destination, constraints, and risk.
- Quiz promise: what the lead gets by completing the quiz before they see an
  offer.
- Diagnostic thesis: the one belief, mechanism, and answer pattern the quiz is
  meant to surface.
- Question map: opening question, diagnostic questions, segmentation
  questions, friction reducers, branch logic, and what each question proves or
  qualifies.
- Result personalization: result types, personalized mirror copy, result
  interpretation, and what not to overclaim.
- Mechanism and proof: why the diagnosis points to the solution and what proof
  can be used without overstating.
- Offer bridge: how the result naturally leads to the offer, mini VSL, checkout,
  application, or backend step.
- Completion design: progress, final screen, lead capture, CTA, fallback path,
  and analytics for completion and drop-off.
- Test plan: first traffic or list test, minimum decision signal, page-level
  metrics, and next iteration if the quiz underperforms.
- Citation map: each non-obvious rule or strategic choice mapped to
  `insight_id`.

## No Invention

- Use only `v2_master_pool` as source material unless the owner explicitly
  reopens curation.
- Do not count the same `insight_id` twice when it appears in both imported
  modules.
- Do not let a transversal module decide quiz-specific questions, result
  types, branch logic, mini VSL placement, offer bridge, completion design, or
  page-level metrics.
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
