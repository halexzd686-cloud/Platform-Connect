# Open-source visual prompt research

Research checked on 2026-07-21. This project adopts structural methods and writes its own industry guidance; it does not bundle third-party prompt galleries or example images.

## Selected sources

### OpenAI Codex sample imagegen skill

- Source: <https://github.com/openai/codex/tree/main/codex-rs/skills/src/assets/samples/imagegen>
- License: Apache-2.0
- Useful method: a labeled prompt schema covering use case, asset type, subject, scene, medium, composition, lighting, palette, exact text, constraints and avoid items; one prompt per distinct asset; single-change iteration with invariants repeated.

### Garden Skills — gpt-image-2

- Source: <https://github.com/ConardLi/garden-skills/tree/main/skills/gpt-image-2>
- License: MIT
- Useful method: progressive category routing rather than loading a full prompt gallery, plus separate handling for posters, product visuals, infographics, research figures, technical diagrams, storyboards, UI and editing.

### mcp-image image-generation skill

- Source: <https://github.com/shinpr/mcp-image>
- License: MIT
- Useful method: Subject–Context–Style scaffolding, purpose-aware prompting, aspect-ratio planning, character consistency, and composition/editing guidance that can remain model-neutral.

### YouMind prompt recommender skill

- Source: <https://github.com/YouMind-OpenLab/nano-banana-pro-prompts-recommend-skill>
- License: MIT
- Useful method: route a large prompt collection by use case, retrieve only a few relevant candidates, let the user choose, then remix for the actual content. This supports the product rule that recommendations precede generation.

### Qwen-Image prompt utilities

- Source: <https://github.com/QwenLM/Qwen-Image/blob/main/src/examples/tools/prompt_utils.py>
- License: Apache-2.0
- Useful method: bilingual prompt rewriting with explicit subject traits, spatial relationships, text placement, information-graphic logic and edit invariants. Do not copy generic quality suffixes across every industry.

### GPT-Image2-Skill prompt gallery

- Source: <https://github.com/wuyoscar/GPT-Image2-Skill/tree/main/skills/gpt-image>
- License: MIT
- Useful method: category-split reference loading across product and food, research figures, UI/UX, data visualization, technical illustration, architecture, science, fashion, events and other domains. Outside-source items in that repository retain their own source labels, so do not copy them without checking item-level provenance.

### Fooocus

- Source: <https://github.com/lllyasviel/Fooocus>
- License: GPL-3.0
- Useful method: separate prompt content from selectable style presets and support reusable style configuration. Do not copy GPL-covered code or bundled style files into this skill.

### ComfyUI

- Source: <https://github.com/Comfy-Org/ComfyUI>
- License: GPL-3.0
- Useful method: represent complex generation as explicit, inspectable workflows and keep model/tool execution separate from the editorial asset manifest. Do not copy GPL-covered implementation code into this skill.

### ComfyUI workflow templates

- Source: <https://github.com/Comfy-Org/workflow_templates>
- License: MIT
- Useful method: pair reusable workflow templates with a manifest and schema validation. This is a useful model for validating our own asset manifests without adopting ComfyUI as a required runtime.

### Stable Diffusion Dynamic Prompts

- Source: <https://github.com/adieyal/sd-dynamic-prompts>
- License: MIT
- Useful method: compose nested prompt slots such as industry, subject, setting, composition, light and material while controlling combination counts. In this product, sample only a few deliberate directions; never expand all combinations by default.

## Maintenance rule

Before importing any prompt, image, script, or style file, inspect the exact file's license and provenance. A repository-level license may not cover third-party examples. Prefer extracting a general workflow and authoring original prompt language.
