# Delivery schema

Use one output directory per source article:

```text
outputs/<article-slug>/
├── source-brief.md
├── manifest.json
├── index.md
└── <platform>/
    ├── copy.md
    └── images/
```

The manifest is the source of truth:

```json
{
  "schema_version": "1.0",
  "article_slug": "example",
  "mode": "full",
  "platforms": ["douyin", "bilibili"],
  "copy_approval": "pending",
  "visual_approval": "pending",
  "global_style_id": null,
  "platform_overrides": {},
  "copy_files": {},
  "assets": [],
  "review_flags": []
}
```

Each asset must contain:

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

Allowed approval values are `pending` and `approved`. Never set either approval to `approved` without an explicit user decision.

