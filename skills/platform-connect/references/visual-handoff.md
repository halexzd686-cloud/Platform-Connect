# Visual handoff

Use this only after reading the full source and producing platform copy.

## Interaction sequence

1. Enter this sequence only after the user has selected `是，生成配图` at the copy-approved image-intent gate.
2. Summarize the visual problem: audience, emotional register, abstract concepts, and platform contexts.
3. Classify the source's primary industry and communication job, then read the matching entry in [industry-visual-routing.md](industry-visual-routing.md).
4. Recommend three to five distinct visual directions. Explain why each direction fits this particular article and include one concise editable sample prompt per direction.
5. Let the user choose one global main style or choose `自定义提示词`.
6. Allow per-platform overrides for style, aspect ratio, or asset type.
7. Always include:
   - refresh recommendations;
   - custom prompt input;
   - no-images option.
8. Build an editable asset manifest. Recommend the number of images dynamically; do not force a fixed count.
9. Ask the user to confirm the manifest.
10. Only then call an image-generation tool, one asset at a time.

## Style recommendation fields

```yaml
id: stable-style-id
name: user-facing name
fit_reason: why it matches the actual article
visual_language: composition, medium, palette, texture, and typography
best_for: relevant platforms and asset types
risk: likely mismatch or trade-off
sample_prompt: concise, editable prompt grounded in the source article
```

## Asset manifest fields

```yaml
platform: youtube-shorts
asset_type: cover | opening-keyframe | explainer | chapter-card | carousel-page
purpose: the single communication job of this image
source_anchor: content brief unit or protected claim
core_idea: one idea only
aspect_ratio: platform-appropriate ratio
style_id: global style or platform override
visual_metaphor: optional physical or spatial metaphor
on_image_text: short, editable labels
custom_prompt: optional user instruction
factual_invariants: people, products, anatomy, numbers, locations, or evidence that must remain accurate
brand_constraints: exact logo, product geometry, packaging, type, and brand colors when applicable
avoid: industry-specific safety, compliance, stereotype, and visual-quality constraints
planning_status: proposed | edited | approved
generation_status: not-requested | generating | ready | needs-review
```

## Prompt assembly

Normalize each confirmed asset into this order:

```text
Use case and asset type
Source anchor and communication job
Subject and action
Scene or backdrop
Style and medium
Composition and crop-safe placement
Lighting and mood
Palette, materials, and texture
Exact on-image text
Factual invariants
Brand constraints
Constraints and avoid list
```

Keep one prompt per distinct asset. For revisions, change one variable at a time and repeat all invariants.

## Xiaohei preset

Xiaohei can be offered when hand-drawn explanatory diagrams suit the source. It should remain optional. Before adapting its style rules, prompts, or examples, read [third-party-notices.md](third-party-notices.md).
