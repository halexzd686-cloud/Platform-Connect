# Visual prompt handoff

Use this after reading the source and building the shared brief. This Skill delivers
image-generation prompts only. Never call an image-generation or image-editing tool, inspect
generated images, or embed image files.

## Prompt-first sequence

1. Summarize the visual problem: audience, communication job, emotional register, abstract concepts, and platform context.
2. Classify the source's primary industry and communication job, then use the routed industry constraints.
3. Create one recommended prompt package per selected platform by default.
4. Limit the default delivery to three prompt packages total. Add alternatives only when the user explicitly asks for them.
5. Choose the platform-appropriate asset type and aspect ratio.
6. Ground each prompt in one source anchor and one communication job.
7. Preserve names, numbers, products, people, locations, quotations, and other factual invariants.
8. Keep on-image text short and exact. Recommend leaving text blank when image models are likely to render it poorly.
9. Include an editable main prompt, negative constraints, and practical tool notes.
10. In `compact`, include prompt packages in the combined review. In `strict`, expose a separate visual-prompt gate. In `autopilot`, deliver them directly.

If the user supplies a custom prompt, keep it as a first-class input. Reconcile it with source
facts and platform constraints instead of replacing its creative direction.

## Prompt package fields

```yaml
id: stable-prompt-id
platform: xiaohongshu
asset_type: cover | opening-keyframe | explainer | chapter-card | carousel-page
purpose: the single communication job
source_anchor: content brief unit or protected claim
core_idea: one idea only
aspect_ratio: platform-appropriate ratio
visual_direction: composition, medium, palette, texture, and typography
on_image_text: exact short text or empty
prompt: production-ready positive prompt grounded in the article
negative_prompt: factual, safety, stereotype, typography, and quality constraints
factual_invariants: facts that must remain accurate
tool_notes: optional model-agnostic guidance such as crop-safe placement
status: proposed | edited | approved
```

## Prompt assembly

Normalize each package into this order:

```text
Use case and asset type
Source anchor and communication job
Subject and action
Scene or backdrop
Style and medium
Composition and crop-safe placement
Lighting and mood
Palette, materials, and texture
Exact on-image text or no-text instruction
Factual invariants
Brand and safety constraints
Negative constraints
```

Write self-contained prompts that can be copied into different image tools. Do not mention a
specific provider unless the user asks for provider-specific syntax.

## Efficiency boundaries

- Do not generate preview images.
- Do not use `view_image`.
- Do not create placeholder raster or SVG assets.
- Do not simulate visual QA for an image that does not exist.
- Do not expand one article into a multi-image campaign unless explicitly requested.
- Prefer one strong prompt per platform over several generic style alternatives.

## Xiaohei preset

Xiaohei can be offered when hand-drawn explanatory diagrams fit the article. Keep it optional
and apply the attribution requirements routed through `SKILL.md` before reusing derived rules or
examples.
