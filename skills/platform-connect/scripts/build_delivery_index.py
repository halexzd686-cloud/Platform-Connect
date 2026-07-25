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
        raise SystemExit("manifest is invalid; run validate_manifest.py")

    lines = [
        f"# {data['article_slug']} 交付索引",
        "",
        f"- 模式：`{data['mode']}`",
        f"- 文案确认：`{data['copy_approval']}`",
        f"- 视觉清单确认：`{data['visual_approval']}`",
        "",
        "## 平台",
        "",
    ]
    for platform in data["platforms"]:
        copy_path = data.get("copy_files", {}).get(platform, "未记录")
        count = sum(1 for asset in data["assets"] if asset.get("platform") == platform)
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

    out = args.out or args.manifest.with_name("index.md")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

