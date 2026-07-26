#!/usr/bin/env python3
"""Create an immutable delivery workspace and starter manifest."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import re
from pathlib import Path

from _shared import PLATFORMS, SCHEMA_VERSION, SKILL_VERSION, emit, fail

SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
RUN_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}$")


def default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("slug")
    parser.add_argument("--platforms", nargs="+", required=True)
    parser.add_argument("--mode", choices=("plan", "copy", "full"), default="copy")
    parser.add_argument(
        "--review-policy",
        choices=("strict", "compact", "autopilot"),
        default="compact",
    )
    parser.add_argument(
        "--platform-source",
        choices=("explicit", "inferred", "profile", "preauthorized"),
        default="explicit",
    )
    parser.add_argument("--root", default="outputs")
    parser.add_argument("--run-id", default=default_run_id())
    parser.add_argument("--parent-run-id")
    parser.add_argument("--source-language", default="zh-CN")
    parser.add_argument("--target-language")
    parser.add_argument("--market")
    args = parser.parse_args()

    if not SLUG.fullmatch(args.slug):
        return fail("slug must use lowercase letters, digits, and hyphens")
    if not RUN_ID.fullmatch(args.run_id):
        return fail("run-id contains unsupported characters")
    if args.parent_run_id and not RUN_ID.fullmatch(args.parent_run_id):
        return fail("parent-run-id contains unsupported characters")

    unknown = sorted(set(args.platforms) - PLATFORMS)
    if unknown:
        return fail(f"unsupported platforms: {', '.join(unknown)}")
    platforms = list(dict.fromkeys(args.platforms))

    root = Path(args.root).resolve()
    article_root = (root / args.slug).resolve()
    workspace = (article_root / args.run_id).resolve()
    if root not in article_root.parents or article_root not in workspace.parents:
        return fail("resolved workspace escapes output root")
    if workspace.exists():
        return fail(
            f"run already exists and will not be overwritten: {workspace}",
            workspace=str(workspace),
        )

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "skill_version": SKILL_VERSION,
        "article_slug": args.slug,
        "run_id": args.run_id,
        "parent_run_id": args.parent_run_id,
        "mode": args.mode,
        "review_policy": args.review_policy,
        "platforms": platforms,
        "locale_assumptions": {
            "source_language": args.source_language,
            "target_language": args.target_language,
            "market": args.market,
        },
        "copy_approval": "pending",
        "image_intent": "pending",
        "visual_direction_approval": "pending",
        "visual_manifest_approval": "pending",
        "decision_provenance": {
            "brief": "pending",
            "platforms": args.platform_source,
            "copy_approval": "pending",
            "image_intent": "pending",
            "visual_direction_approval": "pending",
            "visual_manifest_approval": "pending",
        },
        "global_style_id": None,
        "platform_overrides": {},
        "copy_files": {
            platform: f"{platform}/copy.md" for platform in platforms
        },
        "showcase_file": "showcase/index.html",
        "assets": [],
        "review_flags": [],
    }
    manifest_path = workspace / "manifest.json"
    try:
        workspace.mkdir(parents=True)
        for platform in platforms:
            (workspace / platform / "images").mkdir(parents=True)
            (workspace / platform / "copy.md").write_text("", encoding="utf-8")
        (workspace / "source-brief.md").write_text("", encoding="utf-8")
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as error:
        return fail(error, workspace=str(workspace))
    emit(
        {
            "status": "created",
            "workspace": str(workspace),
            "manifest": str(manifest_path),
            "platforms": platforms,
            "run_id": args.run_id,
            "review_policy": args.review_policy,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
