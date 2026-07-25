#!/usr/bin/env python3
"""Build a compact Markdown delivery index from a validated manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_manifest import validate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors = validate(data)
    if errors:
        print(
            json.dumps(
                {"status": "failed", "errors": errors},
                ensure_ascii=False,
            )
        )
        return 1

    locale = data["locale_assumptions"]
    lines = [
        f"# {data['article_slug']} 交付索引",
        "",
        f"- 运行：`{data['run_id']}`",
        f"- 父运行：`{data['parent_run_id'] or 'none'}`",
        f"- Skill：`{data['skill_version']}`",
        f"- 模式：`{data['mode']}`",
        f"- 原文语言：`{locale['source_language']}`",
        f"- 目标语言：`{locale.get('target_language') or 'source-language'}`",
        f"- 目标市场：`{locale.get('market') or 'not-specified'}`",
        "",
        "## 决策状态",
        "",
        f"- 文案确认：`{data['copy_approval']}`",
        f"- 配图意图：`{data['image_intent']}`",
        f"- 视觉方向：`{data['visual_direction_approval']}`",
        f"- 资产清单：`{data['visual_manifest_approval']}`",
        "",
        "## 平台",
        "",
    ]
    for platform in data["platforms"]:
        copy_path = data["copy_files"].get(platform, "未记录")
        count = sum(
            1 for asset in data["assets"] if asset.get("platform") == platform
        )
        lines.append(f"- **{platform}**：文案 `{copy_path}`；视觉资产 {count} 张")

    lines.extend(["", "## 视觉资产", ""])
    if not data["assets"]:
        lines.append("尚未规划视觉资产。")
    for asset in data["assets"]:
        file_path = asset.get("file") or "尚未生成"
        lines.append(
            f"- `{asset['id']}` · {asset['platform']} · {asset['asset_type']} · "
            f"{asset['aspect_ratio']} · {asset['generation_status']} · {file_path}"
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
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "created",
                "index": str(out.resolve()),
                "platform_count": len(data["platforms"]),
                "asset_count": len(data["assets"]),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
