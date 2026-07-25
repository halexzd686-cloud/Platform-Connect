#!/usr/bin/env python3
"""Validate a platform-content delivery manifest using only the stdlib."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


RATIO = re.compile(r"^\d{1,2}:\d{1,2}$")
REQUIRED = {
    "schema_version",
    "article_slug",
    "mode",
    "platforms",
    "copy_approval",
    "visual_approval",
    "copy_files",
    "assets",
    "review_flags",
}
ASSET_REQUIRED = {
    "id",
    "platform",
    "asset_type",
    "purpose",
    "source_anchor",
    "core_idea",
    "aspect_ratio",
    "style_id",
    "on_image_text",
    "planning_status",
    "generation_status",
    "qa",
}


def validate(data: dict) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED - data.keys()
    if missing:
        errors.append(f"missing manifest fields: {', '.join(sorted(missing))}")
    platforms = data.get("platforms", [])
    if not isinstance(platforms, list) or not platforms:
        errors.append("platforms must be a non-empty list")
        platforms = []
    if len(platforms) != len(set(platforms)):
        errors.append("platforms contains duplicates")
    for field in ("copy_approval", "visual_approval"):
        if data.get(field) not in {"pending", "approved"}:
            errors.append(f"{field} must be pending or approved")
    if data.get("mode") not in {"plan", "copy", "full"}:
        errors.append("mode must be plan, copy, or full")

    seen: set[str] = set()
    for index, asset in enumerate(data.get("assets", [])):
        label = f"assets[{index}]"
        if not isinstance(asset, dict):
            errors.append(f"{label} must be an object")
            continue
        asset_missing = ASSET_REQUIRED - asset.keys()
        if asset_missing:
            errors.append(f"{label} missing: {', '.join(sorted(asset_missing))}")
        asset_id = asset.get("id")
        if asset_id in seen:
            errors.append(f"duplicate asset id: {asset_id}")
        if asset_id:
            seen.add(asset_id)
        if asset.get("platform") not in platforms:
            errors.append(f"{label}.platform is not selected")
        if not RATIO.fullmatch(str(asset.get("aspect_ratio", ""))):
            errors.append(f"{label}.aspect_ratio must look like 9:16")
        if asset.get("planning_status") not in {"proposed", "edited", "approved"}:
            errors.append(f"{label}.planning_status is invalid")
        if asset.get("generation_status") not in {"not-requested", "generating", "ready", "needs-review"}:
            errors.append(f"{label}.generation_status is invalid")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors = validate(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

