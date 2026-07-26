# Interaction policy

Use output scope to decide what to produce and review policy to decide how many user turns are required.

## Compact

Use by default.

1. Read the full source and build the factual brief.
2. Use explicitly named platforms. If none are named, recommend and provisionally select at most three platforms from the content, audience, and communication job.
3. State inferred platform, language, and market assumptions visibly.
4. Produce one combined review packet:
   - factual brief and review flags;
   - platform and locale assumptions;
   - editable platform copy;
   - for `full`, image intent, visual directions, and proposed assets.
5. Ask for one combined approval or one consolidated set of revisions.
6. Record approved decisions with provenance `bundled`.

Do not ask a question that can be handled as a visible, reversible default.

## Strict

Use when requested or when material risk requires separate review.

Resolve these in order:

1. platforms and locale;
2. copy approval;
3. image intent;
4. visual direction;
5. asset manifest.

Expose only the current gate. Record direct user choices as `explicit`.

## Autopilot

Use only when the user explicitly requests direct completion without intermediate confirmation or a user-authored profile grants that authority.

- Record delegated choices as `preauthorized` or `profile`.
- Auto-select platforms only when platform choice was delegated.
- Generate images only when image intent is explicitly `yes` or a profile explicitly enables it.
- Stop despite preauthorization when facts conflict, identity is unclear, localization changes meaning, or legal, medical, financial, brand, copyright, or safety risk is material.
- Return assumptions and provenance with the final delivery so the user can audit what was delegated.

## Decision provenance

Use these values:

- `pending`: unresolved;
- `explicit`: directly specified by the user;
- `inferred`: selected by the Agent as a reversible default;
- `profile`: supplied by a user-authored project profile;
- `bundled`: approved in one combined review;
- `preauthorized`: delegated through an explicit no-confirmation instruction.

Never use `inferred` for `image_intent=yes`.

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
  "image_intent": "yes",
  "visual_asset_limit": 3,
  "allow_agent_direction": true
}
```

Record profile-derived decisions as `profile`. A profile with `image_intent=yes` is valid image authorization because the user authored it; do not treat the mere existence of a profile as permission for unspecified actions.

## Blocking questions

Ask one consolidated question only when the answer materially affects:

- factual accuracy or author stance;
- target language or market meaning;
- identity, brand, copyright, or safety constraints;
- permission to generate images;
- an unsupported platform's required format and audience when no delegation exists.

Do not ask separately about tone, CTA, asset count, or other reversible preferences when a stated default is safe.
