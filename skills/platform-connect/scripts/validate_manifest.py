#!/usr/bin/env python3
"""Validate a Platform Connect delivery manifest using only the stdlib."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from _shared import SCHEMA_VERSION, emit, fail, load_json_object


RATIO = re.compile(r"^\d{1,2}:\d{1,2}$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
APPROVALS = {"pending", "approved", "needs-revision"}
IMAGE_INTENTS = {"pending", "yes", "no"}
QA_STATES = {"pending", "passed", "failed"}
REQUIRED = {
    "schema_version",
    "skill_version",
    "article_slug",
    "run_id",
    "parent_run_id",
    "mode",
    "platforms",
    "locale_assumptions",
    "copy_approval",
    "image_intent",
    "visual_direction_approval",
    "visual_manifest_approval",
    "copy_files",
    "showcase_file",
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
QA_REQUIRED = {"facts", "text", "composition", "style"}


def validate(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["manifest root must be an object"]

    missing = REQUIRED - data.keys()
    if missing:
        errors.append(f"missing manifest fields: {', '.join(sorted(missing))}")

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if not SEMVER.fullmatch(str(data.get("skill_version", ""))):
        errors.append("skill_version must be semantic version text such as 1.0.0")
    if data.get("mode") not in {"plan", "copy", "full"}:
        errors.append("mode must be plan, copy, or full")

    platforms = data.get("platforms", [])
    if not isinstance(platforms, list) or not platforms:
        errors.append("platforms must be a non-empty list")
        platforms = []
    elif not all(isinstance(platform, str) and platform for platform in platforms):
        errors.append("every platform must be a non-empty string")
    if len(platforms) != len(set(platforms)):
        errors.append("platforms contains duplicates")

    locale = data.get("locale_assumptions")
    if not isinstance(locale, dict):
        errors.append("locale_assumptions must be an object")
    elif not locale.get("source_language"):
        errors.append("locale_assumptions.source_language is required")

    for field in (
        "copy_approval",
        "visual_direction_approval",
        "visual_manifest_approval",
    ):
        if data.get(field) not in APPROVALS:
            errors.append(f"{field} must be pending, approved, or needs-revision")
    if data.get("image_intent") not in IMAGE_INTENTS:
        errors.append("image_intent must be pending, yes, or no")
    if data.get("image_intent") != "pending" and data.get("copy_approval") != "approved":
        errors.append("image_intent cannot be decided before copy approval")

    copy_files = data.get("copy_files")
    if not isinstance(copy_files, dict):
        errors.append("copy_files must be an object")
    else:
        for platform in platforms:
            if platform not in copy_files:
                errors.append(f"copy_files missing selected platform: {platform}")

    assets = data.get("assets", [])
    if not isinstance(assets, list):
        errors.append("assets must be a list")
        assets = []
    if data.get("image_intent") == "no" and assets:
        errors.append("assets must be empty when image_intent is no")

    seen: set[str] = set()
    generation_allowed = (
        data.get("copy_approval") == "approved"
        and data.get("image_intent") == "yes"
        and data.get("visual_direction_approval") == "approved"
        and data.get("visual_manifest_approval") == "approved"
    )

    for index, asset in enumerate(assets):
        label = f"assets[{index}]"
        if not isinstance(asset, dict):
            errors.append(f"{label} must be an object")
            continue
        asset_missing = ASSET_REQUIRED - asset.keys()
        if asset_missing:
            errors.append(f"{label} missing: {', '.join(sorted(asset_missing))}")

        asset_id = asset.get("id")
        if not isinstance(asset_id, str) or not asset_id:
            errors.append(f"{label}.id must be a non-empty string")
        elif asset_id in seen:
            errors.append(f"duplicate asset id: {asset_id}")
        else:
            seen.add(asset_id)

        if asset.get("platform") not in platforms:
            errors.append(f"{label}.platform is not selected")
        if not asset.get("purpose"):
            errors.append(f"{label}.purpose is required")
        if not asset.get("source_anchor"):
            errors.append(f"{label}.source_anchor is required")
        if not RATIO.fullmatch(str(asset.get("aspect_ratio", ""))):
            errors.append(f"{label}.aspect_ratio must look like 9:16")
        if asset.get("planning_status") not in {"proposed", "edited", "approved"}:
            errors.append(f"{label}.planning_status is invalid")

        generation_status = asset.get("generation_status")
        if generation_status not in {
            "not-requested",
            "generating",
            "ready",
            "needs-review",
        }:
            errors.append(f"{label}.generation_status is invalid")
        if generation_status in {"generating", "ready"}:
            if not generation_allowed:
                errors.append(f"{label} cannot generate before all visual gates are approved")
            if asset.get("planning_status") != "approved":
                errors.append(f"{label} cannot generate before asset planning is approved")

        qa = asset.get("qa")
        if not isinstance(qa, dict):
            errors.append(f"{label}.qa must be an object")
        else:
            missing_qa = QA_REQUIRED - qa.keys()
            if missing_qa:
                errors.append(f"{label}.qa missing: {', '.join(sorted(missing_qa))}")
            for field in QA_REQUIRED:
                if field in qa and qa[field] not in QA_STATES:
                    errors.append(f"{label}.qa.{field} is invalid")
            if generation_status == "ready" and any(
                qa.get(field) != "passed" for field in QA_REQUIRED
            ):
                errors.append(f"{label} cannot be ready until every QA field passes")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        data = load_json_object(args.manifest)
    except (OSError, ValueError) as error:
        return fail(error, manifest=str(args.manifest.resolve()))

    errors = validate(data)
    payload = {
        "status": "failed" if errors else "passed",
        "manifest": str(args.manifest.resolve()),
        "errors": errors,
        "asset_count": len(data.get("assets", [])) if isinstance(data, dict) else 0,
    }
    emit(payload)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
