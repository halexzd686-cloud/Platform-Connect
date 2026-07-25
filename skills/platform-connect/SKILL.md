---
name: platform-connect
description: Adapt a user-provided article into a fact-preserving content brief, editable platform-native copy, visual directions, image manifests, and confirmed generated images. Use when the user wants to repurpose, localize, rewrite, script, illustrate, or package content for Chinese platforms or overseas platforms including TikTok, YouTube, Instagram, Facebook, LinkedIn, X, Threads, Pinterest, and Snapchat.
---

# Platform Connect

Turn one source article into selected platform-native content packages without changing its factual claims or author stance.

## Modes

- `plan`: create the shared brief, adaptation strategy, visual directions, and proposed asset list; do not draft final copy or generate images.
- `copy`: create the shared brief and platform copy, request copy confirmation, then ask the mandatory image-intent question.
- `full`: create copy, visual plan, and images, while preserving the copy, image-intent, visual-direction, and manifest approval gates below.

Infer `full` only when the user explicitly asks for images or 配图. Otherwise use `copy`. A mode never overrides an approval gate.

The required flow below supersedes the mode default after copy confirmation: always offer the explicit image-intent choice, even when the initial mode is `copy`.

## Required flow

1. Read the entire source before drafting.
2. After receiving the article, ask which platforms the user wants only if they did not already specify them. Allow one platform, any combination, or an explicit all-platform choice. Start with none selected; never assume all platforms. Offer the supported choices in [platform-adapters.md](references/platform-adapters.md), including overseas platforms.
3. For overseas platforms, ask for target language and market. Keep the source language when the user does not request localization. When an unlisted platform is requested, ask for its content format and audience, then create a clearly labeled provisional adapter without claiming platform-specific rules.
4. Build one shared content brief using [content-brief-schema.md](references/content-brief-schema.md).
5. Read only the selected platform entries in [platform-adapters.md](references/platform-adapters.md).
6. Generate visibly different platform versions from the shared brief.
7. Present every copy as editable draft content and request confirmation unless the user explicitly chose a quick/automatic mode.
8. Stop the response at the copy-review gate. Do not include visual directions in the same response as the initial copy drafts. Wait for explicit copy approval.
9. Immediately after the user confirms that the copy is usable, proactively ask: "文案已确认，是否要基于这篇内容生成配图？" Present exactly two clear choices: `是，生成配图` and `否，暂不生成`. Do this even when the user did not independently mention images; never require an additional request such as "我需要生图".
10. If the user chooses `否`, finish the copy workflow and offer only non-visual next actions. Do not present visual directions or call an image tool.
11. If the user chooses `是`, continue with [visual-handoff.md](references/visual-handoff.md): classify the industry and communication job, then recommend 3–5 content-specific image-generation directions. Each direction must include a concise, editable sample prompt and explain its fit. Always include `自定义提示词` as an equal option so the user can supply or revise the prompt instead of selecting a recommendation.
12. Wait for the user to choose a global direction, optional platform overrides, or a custom direction. Then create an editable asset manifest using [output-schema.md](references/output-schema.md). If the user supplies a custom prompt, preserve its intent and ask only questions needed to resolve material factual, brand, or safety constraints.
13. Stop at the visual-manifest gate. Generate no images until the user explicitly approves the manifest.
14. After approval, use the available image-generation tool once per distinct asset. Inspect every output, apply the QA checklist in [visual-handoff.md](references/visual-handoff.md), and iterate one change at a time when necessary.
15. Save or organize deliverables with the deterministic scripts below when filesystem output is requested. Create a new immutable run directory for every revision; never overwrite a prior approved run.
16. When the user needs a visible execution artifact, render the bundled offline showcase from the manifest, brief, copy packages, visual decisions, and QA state. The showcase visualizes this skill's work; it is not a separate AI application.

## Non-negotiable boundaries

- Preserve names, numbers, dates, causal claims, quotations, examples, and the author's stated position.
- Do not invent evidence, success claims, credentials, product capabilities, or platform rules.
- Adapt the angle, opening, pacing, structure, duration, CTA, and packaging—not the underlying facts.
- Mark unclear source claims for human review instead of silently repairing them.
- Localize for language and market context; do not perform mechanical sentence-by-sentence translation.
- Never generate images before the user sees and confirms visual directions and an editable asset list.
- Treat copy approval, image intent, visual-direction selection, and visual-manifest approval as separate user decisions. Do not infer any of them from the original request.
- After copy approval, always ask the explicit yes/no image-intent question before ending the turn. A copy-only request does not excuse skipping this offer; the user's `否` is the decision that ends visual work.
- Recommend visual directions from the actual article's subject, audience, industry, and communication job. Do not offer generic style labels without an article-specific rationale and editable prompt.
- A user-written custom prompt is a first-class visual direction. Keep it editable, record it in the manifest, and reconcile it with factual invariants instead of replacing it wholesale.
- Route the visual plan through the source article's industry and communication job; industry determines factual risks and visual vocabulary, not a fixed aesthetic.
- Treat Xiaohei as one optional visual preset, not the product's default identity or industry scope.

## Output order

Return results in this order:

1. selected platforms and locale assumptions;
2. content brief;
3. one copy package per platform;
4. factual or editorial review flags;
5. next action: edit, approve, regenerate, or proceed to visual direction.

Keep platform labels explicit. Do not merge several platform scripts into one generic version.

## Deterministic scripts

Use these scripts for file operations; do not manually recreate their behavior:

- `scripts/prepare_workspace.py <slug> --platforms ...` creates an immutable versioned run directory and starter manifest.
- `scripts/validate_manifest.py <manifest.json>` validates required fields, platform selection, duplicate assets, ratios, and approval state.
- `scripts/build_delivery_index.py <manifest.json>` builds a Markdown delivery index after assets and copy paths are recorded.
- `scripts/render_showcase.py <manifest.json>` renders the bundled offline execution showcase.
- `scripts/validate_showcase.py <showcase-dir>` checks the rendered showcase contract and offline constraints.

Run scripts from the repository or skill consumer's working directory. Use `--root` to choose a different output root.

## Reference routing

- Always read [content-brief-schema.md](references/content-brief-schema.md) before creating the shared brief.
- Read [platform-adapters.md](references/platform-adapters.md) only for the selected platforms.
- Read [visual-handoff.md](references/visual-handoff.md) only after copy generation or when the user explicitly asks for visuals.
- Read [output-schema.md](references/output-schema.md) before creating or validating a filesystem delivery package.
- For visual work, read the relevant entries in [industry-visual-routing.md](references/industry-visual-routing.md); do not load or apply unrelated industries.
- Read [open-source-visual-research.md](references/open-source-visual-research.md) when maintaining the prompt schema or adding visual categories.
- Read [third-party-notices.md](references/third-party-notices.md) before reusing or distributing Xiaohei-derived rules, prompts, or examples.
