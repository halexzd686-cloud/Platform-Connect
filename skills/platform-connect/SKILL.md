---
name: platform-connect
description: Adapts a pasted article, TXT, Markdown, Word, PDF, HTML file, or article URL into fact-preserving platform-native copy and optional image-generation prompts. Use when the user asks to repurpose, localize, rewrite, script, illustrate, or package an article for Chinese or overseas social platforms including Xiaohongshu, Douyin, WeChat, Bilibili, TikTok, YouTube, Instagram, Facebook, LinkedIn, X, Threads, Pinterest, and Snapchat.
---

# Platform Connect

Turn one complete source into clearly different platform-native versions without changing its facts or author stance. Accept the source directly; do not require a specially formatted prompt.

## Workflow

1. Read [source-intake.md](references/source-intake.md), identify the input type, and read the complete available source before drafting.
2. Extract names, numbers, dates, quotations, examples, causal claims, uncertainty, and the author's position as an internal factual baseline. Do not create a separate brief file unless the user asks for one.
3. If platforms are specified, continue directly. If not, recommend two suitable platforms, preferably covering useful domestic and overseas contexts, explain each choice briefly, and ask the user to choose once. Do not create a recommendation report or draft every candidate.
4. Read only the selected platform sections in [platform-adapters.md](references/platform-adapters.md), then produce visibly different versions with platform-appropriate openings, pacing, structure, language, and CTA.
5. Include one editable image-generation prompt per platform only when the user requests 配图、生图、visual guidance, or prompts. Read [visual-handoff.md](references/visual-handoff.md) for the prompt format. Never call an image-generation or image-editing tool.
6. Complete the work without intermediate approval by default. Ask one consolidated question only when incomplete source access or material legal, medical, financial, safety, identity, or brand risk could change the result.
7. Deliver in chat by default. Present: a short source brief, each platform result, and factual or risk reminders.
8. Create files only when the user asks to save, package, download, or generate an HTML result page. Follow [output-schema.md](references/output-schema.md) and use `scripts/deliver.py`; do not recreate its output manually.

## Content boundaries

- Preserve supported facts and the author's stated position.
- Do not claim complete reading when a file, page, OCR passage, or URL body is missing.
- Do not invent evidence, credentials, results, product capabilities, quotations, or current platform rules.
- Adapt expression and packaging, not underlying facts.
- Mark uncertain or high-risk claims clearly instead of silently repairing them.
- Localize for language and market context; do not translate mechanically.
- Keep platform versions separate rather than merging them into one generic script.
- Keep visual prompts tied to the article topic and platform use case; do not introduce unsupported facts.
- Do not use persistent profiles, approval state machines, manifests, immutable run trees, or execution-provenance records.

## Chat delivery format

Use this compact order:

1. `内容简报` — the thesis, intended audience, and facts that must not drift;
2. `平台成果` — one clearly labeled final version per platform;
3. `配图提示词` — only when requested, one editable prompt beneath each platform;
4. `事实提醒` — only real uncertainty or risk that the user should know.

Do not force filesystem output when chat delivery satisfies the request.

## Optional file delivery

Prepare one Markdown file per selected platform:

```markdown
# 小红书

## 发布文案

最终平台文案。

## 配图提示词

一条可编辑提示词；未请求时写“本次未请求配图提示词”。

## 交付说明

必要的事实提醒、语言市场或使用说明；没有额外提醒时写“无额外说明”。
```

Then run:

```text
python scripts/deliver.py <平台文件...> --title "<本次主题>" --output-root outputs
```

The command creates only:

```text
<run-id>/
├── showcase.html
└── <本次主题>/
    ├── 小红书.md
    └── X.md
```

Return the actual `showcase.html` and result-folder paths. Treat a nonzero exit code or a missing output file as a failed package operation, but keep the completed chat result available.

## Reference routing

- Always read [source-intake.md](references/source-intake.md) for source handling.
- Search [platform-adapters.md](references/platform-adapters.md) by exact `##` heading and read only selected platform sections plus cross-platform QA.
- Read [visual-handoff.md](references/visual-handoff.md) only when prompts are requested.
- Read [output-schema.md](references/output-schema.md) only when filesystem delivery is requested.
