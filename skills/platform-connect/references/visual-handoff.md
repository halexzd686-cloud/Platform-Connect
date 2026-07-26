# Visual handoff

Use this after reading the full source. In `plan` mode, use it to propose directions and assets without generating copy or images. In `full` mode, enter it only after copy approval and explicit image intent.

## Interaction sequence

1. Enter the planning branch after the shared brief and platform strategy. Enter the generation branch only after the user selects `是，生成配图` at the copy-approved image-intent gate.
2. Summarize the visual problem: audience, emotional register, abstract concepts, and platform contexts.
3. Classify the source's primary industry and communication job, then apply the industry route already selected through `SKILL.md`.
4. Recommend three to five distinct visual directions. Explain why each direction fits this particular article and include one concise editable sample prompt per direction.
5. Let the user choose one global main style or choose `自定义提示词`.
6. Allow per-platform overrides for style, aspect ratio, or asset type.
7. Always include:
   - refresh recommendations;
   - custom prompt input;
   - no-images option.
8. Build an editable proposed asset list or manifest. Recommend the number of images dynamically; do not force a fixed count.
9. In `plan` mode, ask for plan review and stop. In `full` mode, ask the user to confirm the manifest.
10. Only after full-mode manifest approval, call an image-generation tool one asset at a time.

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

Xiaohei can be offered when hand-drawn explanatory diagrams suit the source. It should remain optional and may be used only after the attribution requirements routed through `SKILL.md` have been checked.
