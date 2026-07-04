# Asset Acquisition Procedure

Use this procedure when Marketing Swipe File detects a complementary material in an episode.

## Where to See Pending Actions

For each processed episode, check:

```text
data/processed/{video_id}/manual_actions.md
data/processed/{video_id}/acquisition_tasks.json
```

The manual actions file tells you:

- what material was detected;
- where it was mentioned;
- the quote or timestamp that supports the detection;
- the action needed to obtain it;
- where to place the obtained file.

## How to Obtain Materials

### Comment Keyword

When the instruction says to comment a keyword:

1. Open the episode on YouTube or the relevant platform.
2. Comment the exact keyword shown in `manual_actions.md`.
3. Wait for the delivery path mentioned by the participant.
4. Save the received file.
5. Place it in:

```text
data/input/assets/{video_id}/
```

### Direct Message

When the instruction says to send a direct message:

1. Open the profile or channel mentioned in the episode.
2. Send the exact keyword or request.
3. Save the received material.
4. Place it in:

```text
data/input/assets/{video_id}/
```

### Description Link

When the instruction says to use a description link:

1. Open the episode description.
2. Find the referenced material.
3. Download or export the file.
4. Place it in:

```text
data/input/assets/{video_id}/
```

### Member Area

When the instruction says to use a member area:

1. Access the relevant member area manually.
2. Search for the file name, keyword, module, or participant mentioned.
3. Download or export the material if access is allowed.
4. Place it in:

```text
data/input/assets/{video_id}/
```

## File Naming

Use descriptive filenames:

```text
{referenced_asset_id}__short-description.pdf
{referenced_asset_id}__offer-calculator.xlsx
{referenced_asset_id}__vsl-model.docx
```

Example:

```text
fixture001-refasset-0001__vsl-framework.pdf
```

## Registering Files

After placing files in the folder, run:

```powershell
& 'C:\Users\luish\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\register_assets.py --episode-video-id {video_id} --input-dir data\input\assets\{video_id}
```

The script will:

- calculate checksum;
- create an `asset_id`;
- preserve the original file under `data/raw/assets/{asset_id}/`;
- write `metadata.json`;
- avoid duplicate registrations for the same file.

## Status Handling

Use these statuses:

- `pending`: action has not been attempted.
- `in_progress`: you started the procedure.
- `obtained`: file was received and inserted.
- `unavailable`: file cannot be obtained.
- `discarded`: material is irrelevant or not worth processing.

## Important

Do not commit private, paid, member-area, or copyrighted files. Raw assets are ignored by Git by default.

