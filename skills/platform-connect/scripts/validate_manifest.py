#!/usr/bin/env python3
"""Validate a Platform Connect prompt-first delivery manifest."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from _shared import PLATFORMS, SCHEMA_VERSION, emit, fail, load_json_object


RATIO = re.compile(r"^\d{1,2}:\d{1,2}$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
APPROVALS = {"pending", "approved", "needs-revision"}
PROMPT_INTENTS = {"pending", "yes", "no"}
REVIEW_POLICIES = {"strict", "compact", "autopilot"}
SOURCE_TYPES = {"pasted", "file", "url"}
SOURCE_READ_STATES = {"pending", "complete", "blocked"}
RECOMMENDATION_STATES = {"selected", "not-selected"}
PROVENANCE = {
    "pending",
    "explicit",
    "inferred",
    "profile",
    "bundled",
    "preauthorized",
}
DECISION_FIELDS = {
    "brief",
    "platforms",
    "copy_approval",
    "visual_prompt_intent",
    "visual_prompt_approval",
}
REQUIRED = {
    "schema_version",
    "skill_version",
    "article_slug",
    "run_id",
    "parent_run_id",
    "mode",
    "review_policy",
    "platforms",
    "source",
    "platform_recommendations",
    "locale_assumptions",
    "copy_approval",
    "visual_prompt_intent",
    "visual_prompt_approval",
    "visual_prompt_limit",
    "decision_provenance",
    "copy_files",
    "showcase_file",
    "visual_prompts",
    "review_flags",
}
PROMPT_REQUIRED = {
    "id",
    "platform",
    "asset_type",
    "purpose",
    "source_anchor",
    "core_idea",
    "aspect_ratio",
    "visual_direction",
    "on_image_text",
    "prompt",
    "negative_prompt",
    "factual_invariants",
    "tool_notes",
    "status",
}
FORBIDDEN_PROMPT_FIELDS = {
    "file",
    "generation_status",
    "qa",
}


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
    if data.get("review_policy") not in REVIEW_POLICIES:
        errors.append("review_policy must be strict, compact, or autopilot")

    source = data.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object")
    else:
        if source.get("input_type") not in SOURCE_TYPES:
            errors.append("source.input_type must be pasted, file, or url")
        if source.get("read_status") not in SOURCE_READ_STATES:
            errors.append("source.read_status must be pending, complete, or blocked")
        if source.get("read_status") != "complete":
            errors.append("source must be completely read before delivery")
        if not isinstance(source.get("title"), str) or not source.get("title"):
            errors.append("source.title is required")
        if source.get("input_type") in {"file", "url"} and not source.get("reference"):
            errors.append("source.reference is required for file or url input")
        supporting = source.get("supporting_references", [])
        if not isinstance(supporting, list) or not all(
            isinstance(item, str) and item for item in supporting
        ):
            errors.append("source.supporting_references must be a list of strings")

    platforms = data.get("platforms", [])
    if not isinstance(platforms, list) or not platforms:
        errors.append("platforms must be a non-empty list")
        platforms = []
    elif not all(isinstance(platform, str) and platform for platform in platforms):
        errors.append("every platform must be a non-empty string")
    if len(platforms) != len(set(platforms)):
        errors.append("platforms contains duplicates")
    unsupported = sorted(set(platforms) - PLATFORMS)
    if unsupported:
        errors.append("unsupported platforms: " + ", ".join(unsupported))

    recommendations = data.get("platform_recommendations")
    if not isinstance(recommendations, list):
        errors.append("platform_recommendations must be a list")
        recommendations = []
    if len(recommendations) > 3:
        errors.append("platform_recommendations must contain at most three items")
    if recommendations and len(recommendations) < 2:
        errors.append("platform_recommendations must contain two or three items")
    recommended_platforms: set[str] = set()
    selected_recommendations: set[str] = set()
    for index, recommendation in enumerate(recommendations):
        label = f"platform_recommendations[{index}]"
        if not isinstance(recommendation, dict):
            errors.append(f"{label} must be an object")
            continue
        platform = recommendation.get("platform")
        if not isinstance(platform, str) or not platform:
            errors.append(f"{label}.platform is required")
        elif platform not in PLATFORMS:
            errors.append(f"{label}.platform is unsupported")
        elif platform in recommended_platforms:
            errors.append(f"duplicate recommended platform: {platform}")
        else:
            recommended_platforms.add(platform)
        if not recommendation.get("rationale"):
            errors.append(f"{label}.rationale is required")
        if not recommendation.get("visual_direction"):
            errors.append(f"{label}.visual_direction is required")
        if recommendation.get("selection_status") not in RECOMMENDATION_STATES:
            errors.append(f"{label}.selection_status is invalid")
        if recommendation.get("selection_status") == "selected":
            selected_recommendations.add(platform)
    if not selected_recommendations.issubset(set(platforms)):
        errors.append("selected platform recommendations must appear in platforms")
    if recommendations and not selected_recommendations:
        errors.append("platform_recommendations must record the selected result")

    locale = data.get("locale_assumptions")
    if not isinstance(locale, dict):
        errors.append("locale_assumptions must be an object")
    elif not locale.get("source_language"):
        errors.append("locale_assumptions.source_language is required")

    for field in ("copy_approval", "visual_prompt_approval"):
        if data.get(field) not in APPROVALS:
            errors.append(f"{field} must be pending, approved, or needs-revision")
    if data.get("visual_prompt_intent") not in PROMPT_INTENTS:
        errors.append("visual_prompt_intent must be pending, yes, or no")
    if data.get("mode") == "copy" and data.get("visual_prompt_intent") == "yes":
        errors.append("copy mode must change to full before visual prompt work")
    if (
        data.get("mode") == "full"
        and data.get("review_policy") == "strict"
        and data.get("visual_prompt_approval") != "pending"
        and data.get("copy_approval") != "approved"
    ):
        errors.append("visual prompts cannot be approved before copy approval")

    prompt_limit = data.get("visual_prompt_limit")
    if not isinstance(prompt_limit, int) or isinstance(prompt_limit, bool):
        errors.append("visual_prompt_limit must be an integer")
        prompt_limit = 0
    elif not 1 <= prompt_limit <= 12:
        errors.append("visual_prompt_limit must be between 1 and 12")

    provenance = data.get("decision_provenance")
    if not isinstance(provenance, dict):
        errors.append("decision_provenance must be an object")
        provenance = {}
    else:
        missing_provenance = DECISION_FIELDS - provenance.keys()
        if missing_provenance:
            errors.append(
                "decision_provenance missing: "
                + ", ".join(sorted(missing_provenance))
            )
        for field in DECISION_FIELDS:
            if field in provenance and provenance[field] not in PROVENANCE:
                errors.append(f"decision_provenance.{field} is invalid")
    if provenance.get("platforms") == "pending":
        errors.append("selected platforms must record decision provenance")
    for field in ("copy_approval", "visual_prompt_approval"):
        if (
            data.get(field) == "approved"
            and provenance.get(field) in {"pending", "inferred", None}
        ):
            errors.append(f"{field} approval provenance is required")
    if data.get("review_policy") == "autopilot":
        allowed = {"explicit", "profile", "preauthorized"}
        for field in ("copy_approval", "visual_prompt_approval"):
            if data.get(field) == "approved" and provenance.get(field) not in allowed:
                errors.append(
                    f"autopilot {field} must be explicit, profile, or preauthorized"
                )

    copy_files = data.get("copy_files")
    if not isinstance(copy_files, dict):
        errors.append("copy_files must be an object")
    else:
        for platform in platforms:
            if platform not in copy_files:
                errors.append(f"copy_files missing selected platform: {platform}")

    prompts = data.get("visual_prompts", [])
    if not isinstance(prompts, list):
        errors.append("visual_prompts must be a list")
        prompts = []
    if prompt_limit and len(prompts) > prompt_limit:
        errors.append("visual_prompts exceeds visual_prompt_limit")
    if data.get("mode") == "copy" and prompts:
        errors.append("copy mode cannot contain visual prompts")
    if data.get("visual_prompt_intent") == "no" and prompts:
        errors.append("visual_prompts must be empty when visual_prompt_intent is no")
    if (
        data.get("mode") == "full"
        and data.get("visual_prompt_intent") == "yes"
        and data.get("visual_prompt_approval") == "approved"
        and not prompts
    ):
        errors.append("approved full delivery requires at least one visual prompt")

    seen: set[str] = set()
    for index, prompt_package in enumerate(prompts):
        label = f"visual_prompts[{index}]"
        if not isinstance(prompt_package, dict):
            errors.append(f"{label} must be an object")
            continue
        prompt_missing = PROMPT_REQUIRED - prompt_package.keys()
        if prompt_missing:
            errors.append(f"{label} missing: {', '.join(sorted(prompt_missing))}")
        forbidden = FORBIDDEN_PROMPT_FIELDS & prompt_package.keys()
        if forbidden:
            errors.append(
                f"{label} contains image-generation fields: "
                + ", ".join(sorted(forbidden))
            )

        prompt_id = prompt_package.get("id")
        if not isinstance(prompt_id, str) or not prompt_id:
            errors.append(f"{label}.id must be a non-empty string")
        elif prompt_id in seen:
            errors.append(f"duplicate visual prompt id: {prompt_id}")
        else:
            seen.add(prompt_id)
        if prompt_package.get("platform") not in platforms:
            errors.append(f"{label}.platform is not selected")
        for field in (
            "asset_type",
            "purpose",
            "source_anchor",
            "core_idea",
            "visual_direction",
            "prompt",
            "negative_prompt",
        ):
            if not isinstance(prompt_package.get(field), str) or not prompt_package.get(field):
                errors.append(f"{label}.{field} is required")
        if not RATIO.fullmatch(str(prompt_package.get("aspect_ratio", ""))):
            errors.append(f"{label}.aspect_ratio must look like 9:16")
        invariants = prompt_package.get("factual_invariants")
        if not isinstance(invariants, list) or not all(
            isinstance(item, str) and item for item in invariants
        ):
            errors.append(f"{label}.factual_invariants must be a list of strings")
        if prompt_package.get("status") not in {"proposed", "edited", "approved"}:
            errors.append(f"{label}.status is invalid")
        if (
            data.get("visual_prompt_approval") == "approved"
            and prompt_package.get("status") != "approved"
        ):
            errors.append(f"{label} must be approved in an approved delivery")
    return errors


def validate_delivery(
    data: dict,
    run_root: Path,
    *,
    require_showcase: bool = False,
) -> list[str]:
    errors: list[str] = []
    root = run_root.resolve()

    def require_file(value: object, label: str) -> None:
        if not isinstance(value, str) or not value:
            errors.append(f"{label} must be a non-empty relative file path")
            return
        candidate = (root / value).resolve()
        if candidate != root and root not in candidate.parents:
            errors.append(f"{label} escapes the run directory")
        elif not candidate.is_file():
            errors.append(f"{label} does not exist: {value}")

    require_file("source-brief.md", "source brief")

    copy_files = data.get("copy_files")
    if isinstance(copy_files, dict):
        for platform in data.get("platforms", []):
            require_file(copy_files.get(platform), f"copy_files.{platform}")

    if require_showcase:
        require_file(data.get("showcase_file"), "showcase_file")
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
    errors.extend(validate_delivery(data, args.manifest.resolve().parent))
    payload = {
        "status": "failed" if errors else "passed",
        "manifest": str(args.manifest.resolve()),
        "errors": errors,
        "visual_prompt_count": (
            len(data.get("visual_prompts", [])) if isinstance(data, dict) else 0
        ),
    }
    emit(payload)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
