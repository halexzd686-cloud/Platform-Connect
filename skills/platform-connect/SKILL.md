---
name: platform-connect
description: Adapts a user-provided article into a fact-preserving content brief, editable platform-native copy, approved visual directions, a validated asset manifest, generated assets, and an offline execution showcase. Use when the user asks to repurpose, localize, rewrite, script, illustrate, or package an article for Chinese or overseas social platforms including TikTok, YouTube, Instagram, Facebook, LinkedIn, X, Threads, Pinterest, and Snapchat.
---

# Platform Connect

Turn one source article into selected platform-native content packages without changing its factual claims or author stance.

## Modes

- `plan`: create the shared brief, platform strategy, visual-direction proposal, and proposed asset list. Stop at a plan-review gate; do not draft final copy or generate images.
- `copy`: create the shared brief and platform copy. After copy approval, ask the mandatory image-intent question. A `yes` changes the run to `full`; a `no` ends visual work.
- `full`: follow the complete copy and visual workflow. Preserve every approval gate even when the original request already asks for images.

Infer `full` only when the user explicitly asks for images or 配图. Otherwise use `copy`. A mode never overrides an approval gate.

## Required flow

1. Read the entire source before drafting.
2. Build one shared content brief using [content-brief-schema.md](references/content-brief-schema.md). Treat it as the factual baseline for every downstream output.
3. Ask which platforms the user wants only if they did not already specify them. Allow one platform, any combination, or an explicit all-platform choice. Start with none selected; never assume all platforms.
4. For overseas platforms, ask for target language and market. Keep the source language when the user does not request localization. When an unlisted platform is requested, ask for its content format and audience, then create a clearly labeled provisional adapter without claiming platform-specific rules.
5. Read only the selected platform entries in [platform-adapters.md](references/platform-adapters.md).
6. In `plan` mode, produce strategy, visual-direction proposals, and a proposed asset list from the brief. Request plan review and stop. Do not enter the copy-approval or image-generation flow.
7. In `copy` or `full` mode, generate visibly different platform versions from the shared brief. Present every version as an editable draft.
8. Stop at the copy-review gate. Do not include visual directions with the initial copy drafts. Wait for explicit copy approval.
9. Immediately after copy approval, ask: "文案已确认，是否要基于这篇内容生成配图？" Present exactly two choices: `是，生成配图` and `否，暂不生成`.
10. If the user chooses `否`, finish the copy workflow and offer only non-visual next actions. Do not present visual directions or call an image tool.
11. If the user chooses `是`, read [visual-handoff.md](references/visual-handoff.md) and the relevant industry entry in [industry-visual-routing.md](references/industry-visual-routing.md). Recommend 3–5 article-specific directions with editable prompts, plus `自定义提示词` as an equal option.
12. Stop at the visual-direction gate. Wait for a global direction, optional platform overrides, or a custom direction.
13. Create an editable asset manifest using [output-schema.md](references/output-schema.md). Preserve custom-prompt intent and ask only questions needed to resolve material factual, brand, or safety constraints.
14. Stop at the visual-manifest gate. Generate no images until the user explicitly approves the manifest.
15. After approval, use the available image-generation tool once per distinct asset. Inspect every output, apply the QA checklist in [visual-handoff.md](references/visual-handoff.md), and change one variable at a time when revising.
16. When filesystem output is requested, follow the deterministic delivery loop below. Create a new immutable run directory for every revision; never overwrite a prior approved run.
17. When the user needs a visible execution artifact, render the bundled offline showcase from the approved run data. The showcase visualizes the Skill execution; it is not a separate AI application.

## Non-negotiable boundaries

- Preserve names, numbers, dates, causal claims, quotations, examples, and the author's stated position.
- Do not invent evidence, success claims, credentials, product capabilities, or platform rules.
- Adapt the angle, opening, pacing, structure, duration, CTA, and packaging—not the underlying facts.
- Mark unclear source claims for human review instead of silently repairing them.
- Localize for language and market context; do not perform mechanical sentence-by-sentence translation.
- Never generate images before the user sees and confirms visual directions and an editable asset list.
- Treat copy approval, image intent, visual-direction selection, and visual-manifest approval as separate user decisions. Do not infer any of them from the original request.
- In `copy` and `full` modes, always ask the explicit yes/no image-intent question after copy approval. The user's `否` is the decision that ends visual work.
- Recommend visual directions from the actual article's subject, audience, industry, and communication job. Do not offer generic style labels without an article-specific rationale and editable prompt.
- A user-written custom prompt is a first-class visual direction. Keep it editable, record it in the manifest, and reconcile it with factual invariants instead of replacing it wholesale.
- Route the visual plan through the source article's industry and communication job; industry determines factual risks and visual vocabulary, not a fixed aesthetic.
- Treat Xiaohei as one optional visual preset, not the product's default identity or industry scope.

## Output order

For `copy` and `full`, return results in this order:

1. content brief;
2. selected platforms and locale assumptions;
3. one copy package per platform;
4. factual or editorial review flags;
5. one explicit next action: edit, approve, regenerate, or proceed to visual direction.

Keep platform labels explicit. Do not merge several platform scripts into one generic version.

For `plan`, replace the copy packages with platform strategy, visual-direction proposals, and the proposed asset list, then stop at plan review.

## Runtime and deterministic delivery

Require Python 3.10 or newer. The scripts use only the Python standard library. The offline showcase has no package, CDN, network, React, or FastAPI dependency. Use the image-generation capability available in the host environment; do not assume a named provider.

Execute these scripts for file operations; do not manually recreate their behavior:

- `scripts/prepare_workspace.py <slug> --platforms ...` creates an immutable versioned run directory and starter manifest.
- `scripts/validate_manifest.py <manifest.json>` validates required fields, platform selection, duplicate assets, ratios, and approval state.
- `scripts/build_delivery_index.py <manifest.json>` builds a Markdown delivery index after assets and copy paths are recorded.
- `scripts/render_showcase.py <manifest.json>` renders the bundled offline execution showcase.
- `scripts/validate_showcase.py <showcase-dir>` checks the rendered showcase contract and offline constraints.

Run scripts from the repository or skill consumer's working directory. Use `--root` to choose a different output root.

Follow this delivery loop:

1. Run `prepare_workspace.py` after platform selection.
2. Write the brief, copy packages, decisions, asset plan, and review flags into the run.
3. Run `validate_manifest.py`.
4. If validation fails, fix the manifest or source files and rerun validation. Do not continue from an invalid run.
5. After validation passes, run `render_showcase.py`, then `validate_showcase.py`.
6. If showcase validation fails, fix the manifest, display data, or source template and rerender. Do not patch generated HTML as the source of truth.
7. Run `build_delivery_index.py` only after the manifest and showcase pass.

Treat nonzero exit codes and JSON with `"status": "failed"` as blocking. Report the error and preserve the failed run for diagnosis; start a child run for any approved revision.

## Reference routing

- Always read [content-brief-schema.md](references/content-brief-schema.md) before creating the shared brief.
- Search [platform-adapters.md](references/platform-adapters.md) by its exact `##` heading and read only the selected platform sections plus Cross-platform QA.
- Read [visual-handoff.md](references/visual-handoff.md) only for `plan` visual proposals or after image intent is `yes`.
- Read [output-schema.md](references/output-schema.md) before creating or validating a filesystem delivery package.
- Search [industry-visual-routing.md](references/industry-visual-routing.md) by its exact `##` heading and read only the relevant industry sections.
- Read [open-source-visual-research.md](references/open-source-visual-research.md) when maintaining the prompt schema or adding visual categories.
- Read [third-party-notices.md](references/third-party-notices.md) before using, adapting, or distributing Xiaohei-derived rules, prompts, or examples.
