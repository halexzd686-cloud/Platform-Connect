#!/usr/bin/env python3
"""Build a compact Markdown delivery index from a validated manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

from _shared import emit, fail, load_json_object
from validate_manifest import validate, validate_delivery


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        data = load_json_object(args.manifest)
    except (OSError, ValueError) as error:
        return fail(error, manifest=str(args.manifest.resolve()))
    errors = validate(data)
    errors.extend(
        validate_delivery(
            data,
            args.manifest.resolve().parent,
            require_showcase=True,
        )
    )
    if errors:
        emit({"status": "failed", "errors": errors})
        return 1

    locale = data["locale_assumptions"]
    source = data["source"]
    lines = [
        f"# {data['article_slug']} 交付索引",
        "",
        f"- 运行：`{data['run_id']}`",
        f"- 父运行：`{data['parent_run_id'] or 'none'}`",
        f"- Skill：`{data['skill_version']}`",
        f"- 模式：`{data['mode']}`",
        f"- 审阅策略：`{data['review_policy']}`",
        f"- 来源类型：`{source['input_type']}`",
        f"- 来源标题：{source['title']}",
        f"- 来源引用：`{source.get('reference') or 'pasted-content'}`",
        f"- 读取状态：`{source['read_status']}`",
        f"- 原文语言：`{locale['source_language']}`",
        f"- 目标语言：`{locale.get('target_language') or 'source-language'}`",
        f"- 目标市场：`{locale.get('market') or 'not-specified'}`",
        "",
        "## 决策状态",
        "",
        f"- 文案确认：`{data['copy_approval']}`",
        f"- 生图提示词：`{data['visual_prompt_intent']}`",
        f"- 提示词确认：`{data['visual_prompt_approval']}`",
        "",
        "## 决策来源",
        "",
        *(
            f"- {field}：`{source}`"
            for field, source in data["decision_provenance"].items()
        ),
        "",
        "## 平台",
        "",
    ]
    for platform in data["platforms"]:
        copy_path = data["copy_files"].get(platform, "未记录")
        count = sum(
            1
            for prompt in data["visual_prompts"]
            if prompt.get("platform") == platform
        )
        lines.append(f"- **{platform}**：文案 `{copy_path}`；生图提示词 {count} 条")

    if data["platform_recommendations"]:
        lines.extend(["", "## 平台推荐记录", ""])
        for recommendation in data["platform_recommendations"]:
            lines.append(
                f"- **{recommendation['platform']}** · "
                f"`{recommendation['selection_status']}`："
                f"{recommendation['rationale']}；"
                f"视觉方向：{recommendation['visual_direction']}"
            )

    lines.extend(["", "## 生图提示词", ""])
    if not data["visual_prompts"]:
        lines.append("本次未交付生图提示词。")
    for prompt in data["visual_prompts"]:
        lines.append(
            f"- `{prompt['id']}` · {prompt['platform']} · "
            f"{prompt['asset_type']} · {prompt['aspect_ratio']} · "
            f"{prompt['status']}"
        )

    if data.get("review_flags"):
        lines.extend(["", "## 待人工确认", ""])
        lines.extend(f"- {flag}" for flag in data["review_flags"])

    lines.extend(
        [
            "",
            "## 可视化展示",
            "",
            f"- `{data['showcase_file']}`",
        ]
    )

    out = args.out or args.manifest.with_name("index.md")
    try:
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError as error:
        return fail(error, index=str(out.resolve()))
    emit(
        {
            "status": "created",
            "index": str(out.resolve()),
            "platform_count": len(data["platforms"]),
            "visual_prompt_count": len(data["visual_prompts"]),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
