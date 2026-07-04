# Asset Extractor

Use `prompts/extraction/base_insight_extraction.md` as the output contract.

Focus on extracting intelligence from complementary files:

- PDFs;
- docs;
- spreadsheets;
- slides;
- templates;
- prompts;
- swipe files;
- checklists;
- VSL models;
- ad examples;
- offer calculators;
- complete or partial copies;
- frameworks.

Prioritize insights that are richer than the episode transcript:

- reusable frameworks;
- finished copy;
- spreadsheet logic;
- step-by-step checklists;
- examples that can be adapted;
- templates that can be turned into agent instructions.

Special rules:

- If the source is a spreadsheet, preserve `sheet_name` and `cell_range`.
- If the source is a PDF or doc, preserve page/section when available.
- If the source is a slide deck, preserve `slide_number`.
- Classify complete scripts, ads, emails, or VSL blocks as `complete_copy` or `partial_copy`.
- Classify reusable tables or calculators as `spreadsheet_model`.

