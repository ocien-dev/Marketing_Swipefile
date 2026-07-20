# Gold Episode Work Order — L7u7r6rOl68 (historical provenance)

Preserved verbatim from the original seed prompt. This is the concrete
episode work order that seeded the gold pilot; the reusable rules were moved
to `docs/gold-extraction-contract.md` and the episode-agnostic task prompt.

## Episode binding

- YouTube video ID: `L7u7r6rOl68`
- Live data root: `C:\MSF-data\Marketing_Swipe_File`
- Episode title: `Lucrando Multiplos 7D/Mes Com Perpetuo White (Aos 21 Anos!) | Lucas Ramos - Segredos da Escala #140`

## Known problems to verify

Do not assume these statements are correct without checking the files, but use
them as a focused starting point:

- The source transcript contains 1,980 segments.
- The first 1,941 segments appear to be the real episode.
- The final 39 segments appear to be unrelated recommended-video titles
  captured by the YouTube UI snapshot collector.
- Those contaminated segments entered several chunks and produced malformed or
  misleading time ranges.
- The current v2 extraction produced one insight in 14 chunks and zero in two
  chunks, despite allowing up to five.
- Existing validation measured schema validity, exact quotes, title uniqueness,
  and promo noise, but did not measure insight recall.

## Mandatory calibration checks

The final inventory must capture these source claims separately if the clean
transcript confirms them. Treat them as calibration checks, not as the complete
answer:

- approximately 15,000 front-end buyers per month;
- approximately 10 VSL lead variants tested per month;
- one winning lead out of five in the cited scaled VSL case;
- a post-price bonus with a 60-second timer and its reported conversion effect;
- extending a VSL from approximately 18 to 25 minutes with about seven extra
  minutes of closing content;
- a delayed button with a reported 15-20 percent discount;
- the price movement from approximately BRL 200 to BRL 160;
- the report that about half of sales occurred at the discounted price;
- approximately 500 buyers entering per day;
- weekly workshop attendance and conversion figures;
- the business effect of 5, 10, or 15 percent conversion improvements at high
  volume.

Do not force these into the output if the transcript does not support them
verbatim. If any are not found, document the search and evidence result.
