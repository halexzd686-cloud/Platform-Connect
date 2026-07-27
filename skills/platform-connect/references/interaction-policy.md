# Interaction policy

Use output scope to decide what to produce and review policy to decide how many user turns are required.

## Contents

- Compact
- Strict
- Autopilot
- Decision provenance
- Project profile
- Blocking questions

## Compact

Use by default.

1. Read the full source and build the factual brief.
2. Use explicitly named platforms. If none are named, return one compact recommendation packet with two or three candidates. Prefer a useful domestic and overseas mix when the article and audience support both.
3. For each candidate, include platform fit, audience, language and market, a preliminary article-specific visual direction, and one trade-off. Do not draft every candidate before the user chooses.
4. Ask for platform selection, whether to include visual prompts, and completion preference in the same reply. Accept natural language; a compact reply such as `小红书 + X；需要生图提示词；按推荐直接完成` is sufficient.
5. If the user authorizes direct completion, continue under `autopilot` with the recorded scope. Otherwise produce one combined review packet:
   - factual brief and review flags;
   - platform and locale assumptions;
   - editable platform copy;
   - for `full`, visual direction and production-ready prompt packages.
6. Ask for one combined approval or one consolidated set of revisions.
7. Record approved decisions with provenance `bundled`.

Do not ask a question that can be handled as a visible, reversible default.

### Recommendation packet

Keep this packet short and decision-ready:

```text
推荐发布
1. 小红书 — 适合原因；初步配图方向；主要取舍
2. X — 适合原因；初步配图方向；主要取舍

请一次回复：选择哪些平台；是否需要生图提示词；审阅后继续，还是按推荐直接完成。
```

Recommend two platforms by default. Use three only when the third adds a genuinely different audience or format.

## Strict

Use when requested or when material risk requires separate review.

Resolve these in order:

1. platforms and locale;
2. copy approval;
3. visual prompt approval.

Expose only the current gate. Record direct user choices as `explicit`.

## Autopilot

Use only when the user explicitly requests direct completion without intermediate confirmation or a user-authored profile grants that authority.

- Record delegated choices as `preauthorized` or `profile`.
- Auto-select platforms only when platform choice was delegated.
- Stop despite preauthorization when facts conflict, identity is unclear, localization changes meaning, or legal, medical, financial, brand, copyright, or safety risk is material.
- Return assumptions and provenance with the final delivery so the user can audit what was delegated.
- Never call an image-generation or image-editing tool; `full` delivers prompt text only.

## Decision provenance

Use these values:

- `pending`: unresolved;
- `explicit`: directly specified by the user;
- `inferred`: selected by the Agent as a reversible default;
- `profile`: supplied by a user-authored project profile;
- `bundled`: approved in one combined review;
- `preauthorized`: delegated through an explicit no-confirmation instruction.

## Project profile

When `platform-connect.profile.json` exists in the working directory, treat it as user-authored defaults. The current request overrides it.

```json
{
  "review_policy": "compact",
  "default_platforms": ["xiaohongshu", "linkedin"],
  "target_languages": {
    "xiaohongshu": "zh-CN",
    "linkedin": "en"
  },
  "market": "global",
  "visual_prompt_intent": "yes",
  "visual_prompt_limit": 3,
  "allow_agent_direction": true
}
```

Record profile-derived decisions as `profile`. For backward compatibility, interpret a legacy
`image_intent: "yes"` profile value as a request for visual prompts only. It never authorizes
image generation.

## Blocking questions

Ask one consolidated question only when the answer materially affects:

- factual accuracy or author stance;
- target language or market meaning;
- identity, brand, copyright, or safety constraints;
- an unsupported platform's required format and audience when no delegation exists.

Do not ask separately about tone, CTA, prompt count, or other reversible preferences when a stated default is safe.
