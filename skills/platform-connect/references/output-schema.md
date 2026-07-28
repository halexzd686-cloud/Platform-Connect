# Delivery schema

## Contents

- [Run directory](#run-directory)
- [Manifest](#manifest)
- [Visual prompt package](#visual-prompt-package)
- [Optional showcase data](#optional-showcase-data)

## Run directory

Use one immutable run directory per execution:

```text
outputs/<article-slug>/<run-id>/
├── source-brief.md
├── manifest.json
├── index.md
├── downloads/
│   ├── Platform-Connect-成果包.zip
│   ├── <平台>-文案.md
│   ├── 配图提示词.md
│   └── 交付说明.md
├── showcase/
│   ├── index.html
│   ├── app.js
│   └── styles.css
└── <platform>/
    └── copy.md
```

Never overwrite an earlier run. A revision creates a new `run_id` and records the previous run in
`parent_run_id`.

Every completed `copy` or `full` run must execute `scripts/finalize_delivery.py`. The command
must return `"status": "completed"` before the Agent announces completion. This requirement
applies even when the user did not explicitly request files or an HTML board. A missing manifest,
index, showcase, or ZIP bundle blocks delivery.

## Manifest

The manifest is the machine-readable source of truth:

```json
{
  "schema_version": "1.4",
  "skill_version": "1.4.1",
  "article_slug": "example",
  "run_id": "20260727-143500",
  "parent_run_id": null,
  "mode": "full",
  "review_policy": "compact",
  "platforms": ["douyin", "linkedin"],
  "source": {
    "input_type": "file",
    "reference": "article.pdf",
    "supporting_references": [],
    "media_type": "application/pdf",
    "title": "Example article",
    "read_status": "complete"
  },
  "platform_recommendations": [
    {
      "platform": "douyin",
      "rationale": "The article has a clear conflict suitable for a short spoken script.",
      "visual_direction": "Task cards split between human judgment and automation.",
      "selection_status": "selected"
    },
    {
      "platform": "linkedin",
      "rationale": "The argument addresses professional role design.",
      "visual_direction": "Editorial diagram showing tasks unbundling from a role.",
      "selection_status": "selected"
    }
  ],
  "locale_assumptions": {
    "source_language": "zh-CN",
    "target_language": "en",
    "market": "global"
  },
  "copy_approval": "pending",
  "visual_prompt_intent": "yes",
  "visual_prompt_approval": "pending",
  "visual_prompt_limit": 3,
  "decision_provenance": {
    "brief": "pending",
    "platforms": "explicit",
    "copy_approval": "pending",
    "visual_prompt_intent": "explicit",
    "visual_prompt_approval": "pending"
  },
  "copy_files": {
    "douyin": "douyin/copy.md",
    "linkedin": "linkedin/copy.md"
  },
  "showcase_file": "showcase/index.html",
  "visual_prompts": [],
  "review_flags": []
}
```

Allowed values:

- approval fields: `pending`, `approved`, or `needs-revision`;
- `visual_prompt_intent`: `pending`, `yes`, or `no`;
- `mode`: `plan`, `copy`, or `full`;
- `review_policy`: `strict`, `compact`, or `autopilot`.

Keep copy approval and visual-prompt approval as separate audit records when review is required.
Each decision records provenance as `pending`, `explicit`, `inferred`, `profile`, `bundled`, or
`preauthorized`.

`source.input_type` is `pasted`, `file`, or `url`. Delivery requires
`source.read_status: complete`; use `blocked` when pages, OCR passages, or the article body could
not be retrieved. When pasted content is primary and a URL is only supporting context, keep
`input_type: pasted` and record the URL in `source.supporting_references`.

Keep `platform_recommendations` empty when platforms were explicit. Otherwise record two
recommendations by default and no more than three. Every item needs a platform, rationale,
preliminary article-specific visual direction, and `selection_status` of `selected` or
`not-selected`.

## Visual prompt package

Each prompt package must contain:

```json
{
  "id": "douyin-cover-01",
  "platform": "douyin",
  "asset_type": "cover",
  "purpose": "express the core contrast",
  "source_anchor": "brief fact or content-unit id",
  "core_idea": "tasks change before roles disappear",
  "aspect_ratio": "9:16",
  "visual_direction": "editorial task diagram with restrained typography",
  "on_image_text": "TASKS CHANGE",
  "prompt": "Production-ready positive prompt...",
  "negative_prompt": "No invented statistics, no illegible text...",
  "factual_invariants": [
    "Do not imply that every role disappears."
  ],
  "tool_notes": "Keep the main subject inside the vertical crop-safe area.",
  "status": "approved"
}
```

Allowed prompt states are `proposed`, `edited`, or `approved`.

Rules:

- `copy` mode keeps `visual_prompts` empty.
- `visual_prompt_intent: no` keeps `visual_prompts` empty.
- `full` mode with `visual_prompt_intent: yes` requires at least one prompt package.
- Default to one package per selected platform and no more than three total.
- Every prompt must be non-empty, self-contained, grounded in a source anchor, and associated with a selected platform.
- Prompt packages never contain generated file paths, generation states, image QA states, or image-tool output.

## Optional showcase data

`render_showcase.py` can derive a minimal report from the manifest, brief, and copy files. For a
richer interview-ready report, provide `--data showcase-data.json` with any of these optional
fields:

```json
{
  "source": {
    "file_name": "article.md",
    "title": "source title",
    "input_type": "file",
    "read_status": "complete",
    "unit_label": "12 pages",
    "summary_paragraphs": []
  },
  "brief": {
    "core_thesis": "",
    "author_stance": "",
    "audience": "",
    "audience_need": "",
    "tone": "",
    "protected_claims": []
  },
  "platforms": [],
  "copies": [],
  "platform_recommendations": [],
  "decisions": {},
  "trace": {}
}
```

Showcase data is a presentation projection. It must not override decision states, prompt states,
run metadata, or review flags stored in `manifest.json`.

The rendered board is outcome-first: final copy, ready-to-use visual prompt cards, and downloads
are primary; brief, recommendations, decisions, and trace are supporting audit information. Do
not add controls that imply platform selection, approval, or image generation.

`render_showcase.py` creates `downloads/` beside `showcase/`. It writes one friendly Markdown
copy file per selected platform, an aggregate `配图提示词.md` when prompt packages exist,
`交付说明.md`, and `Platform-Connect-成果包.zip`. These files are generated projections; the
manifest, source brief, and platform copy files remain the source of truth.
