# Delivery schema

## Contents

- [Run directory](#run-directory)
- [Manifest](#manifest)
- [Asset](#asset)
- [Optional showcase data](#optional-showcase-data)

## Run directory

Use one immutable run directory per execution:

```text
outputs/<article-slug>/<run-id>/
├── source-brief.md
├── manifest.json
├── index.md
├── showcase/
│   ├── index.html
│   ├── app.js
│   └── styles.css
└── <platform>/
    ├── copy.md
    └── images/
```

Never overwrite an earlier run. A revision creates a new `run_id` and records the previous run in `parent_run_id`.

## Manifest

The manifest is the machine-readable source of truth:

```json
{
  "schema_version": "1.2",
  "skill_version": "1.1.0",
  "article_slug": "example",
  "run_id": "20260726-143500",
  "parent_run_id": null,
  "mode": "full",
  "review_policy": "compact",
  "platforms": ["douyin", "linkedin"],
  "locale_assumptions": {
    "source_language": "zh-CN",
    "target_language": "en",
    "market": "global"
  },
  "copy_approval": "pending",
  "image_intent": "pending",
  "visual_direction_approval": "pending",
  "visual_manifest_approval": "pending",
  "decision_provenance": {
    "brief": "pending",
    "platforms": "explicit",
    "copy_approval": "pending",
    "image_intent": "pending",
    "visual_direction_approval": "pending",
    "visual_manifest_approval": "pending"
  },
  "global_style_id": null,
  "platform_overrides": {},
  "copy_files": {
    "douyin": "douyin/copy.md",
    "linkedin": "linkedin/copy.md"
  },
  "showcase_file": "showcase/index.html",
  "assets": [],
  "review_flags": []
}
```

Allowed decision values:

- approval fields: `pending`, `approved`, or `needs-revision`;
- `image_intent`: `pending`, `yes`, or `no`;
- `mode`: `plan`, `copy`, or `full`.
- `review_policy`: `strict`, `compact`, or `autopilot`.

Keep these as separate audit records even when one bundled reply or preauthorization resolves several decisions:

1. `copy_approval`;
2. `image_intent`;
3. `visual_direction_approval`;
4. `visual_manifest_approval`.

Each decision records provenance as `pending`, `explicit`, `inferred`, `profile`, `bundled`, or `preauthorized`. Never use `inferred` for `image_intent=yes`. Under `autopilot`, approved or affirmative decisions must be `explicit`, `profile`, or `preauthorized`.

## Asset

Each distinct asset must contain:

```json
{
  "id": "douyin-cover-01",
  "platform": "douyin",
  "asset_type": "cover",
  "purpose": "one communication job",
  "source_anchor": "brief fact or content-unit id",
  "core_idea": "one idea only",
  "aspect_ratio": "9:16",
  "style_id": "selected-style",
  "on_image_text": "exact short text",
  "custom_prompt": "",
  "planning_status": "proposed",
  "generation_status": "not-requested",
  "file": null,
  "qa": {
    "facts": "pending",
    "text": "pending",
    "composition": "pending",
    "style": "pending"
  }
}
```

Allowed asset states:

- `planning_status`: `proposed`, `edited`, or `approved`;
- `generation_status`: `not-requested`, `generating`, `ready`, or `needs-review`;
- each QA field: `pending`, `passed`, or `failed`.

An asset cannot be `generating` or `ready` unless:

- `mode` is `full`;
- `copy_approval` is `approved`;
- `image_intent` is `yes`;
- `visual_direction_approval` is `approved`;
- `visual_manifest_approval` is `approved`;
- the asset `planning_status` is `approved`.

When `image_intent` is `no`, keep `assets` empty and offer only non-visual follow-up actions.

## Optional showcase data

`render_showcase.py` can derive a minimal report from the manifest, brief, and copy files. For a richer interview-ready report, provide `--data showcase-data.json` with any of these optional fields:

```json
{
  "source": {
    "file_name": "article.md",
    "title": "source title",
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
  "visual_directions": [],
  "decisions": {},
  "trace": {},
  "deliverables": []
}
```

Showcase data is a presentation projection. It must not override decision states, asset states, run metadata, or review flags stored in `manifest.json`.
