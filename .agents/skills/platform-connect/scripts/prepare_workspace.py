#!/usr/bin/env python3
"""Create a safe delivery workspace and starter manifest."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
PLATFORMS = {
    "douyin",
    "xiaohongshu",
    "wechat-channels",
    "bilibili",
    "kuaishou",
    "tiktok",
    "youtube-shorts",
    "youtube-long",
    "instagram-reels",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("slug")
    parser.add_argument("--platforms", nargs="+", required=True)
    parser.add_argument("--mode", choices=("plan", "copy", "full"), default="copy")
    parser.add_argument("--root", default="outputs")
    args = parser.parse_args()

    if not SLUG.fullmatch(args.slug):
        parser.error("slug must use lowercase letters, digits, and hyphens")
    unknown = sorted(set(args.platforms) - PLATFORMS)
    if unknown:
        parser.error(f"unsupported platforms: {', '.join(unknown)}")
    platforms = list(dict.fromkeys(args.platforms))

    root = Path(args.root).resolve()
    workspace = (root / args.slug).resolve()
    if root not in workspace.parents:
        parser.error("resolved workspace escapes output root")
    workspace.mkdir(parents=True, exist_ok=True)
    for platform in platforms:
        (workspace / platform / "images").mkdir(parents=True, exist_ok=True)
        copy_file = workspace / platform / "copy.md"
        copy_file.touch(exist_ok=True)
    (workspace / "source-brief.md").touch(exist_ok=True)

    manifest_path = workspace / "manifest.json"
    if manifest_path.exists():
        raise SystemExit(f"manifest already exists: {manifest_path}")
    manifest = {
        "schema_version": "1.0",
        "article_slug": args.slug,
        "mode": args.mode,
        "platforms": platforms,
        "copy_approval": "pending",
        "visual_approval": "pending",
        "global_style_id": None,
        "platform_overrides": {},
        "copy_files": {platform: f"{platform}/copy.md" for platform in platforms},
        "assets": [],
        "review_flags": [],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

