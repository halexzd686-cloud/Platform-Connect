#!/usr/bin/env python3
"""Render the bundled offline Skill execution showcase."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

from _shared import emit, fail, load_json_object
from validate_manifest import validate, validate_delivery


TOKEN = "__PLATFORM_CONNECT_CASE_JSON__"
PLATFORM_LABELS = {
    "douyin": "抖音",
    "xiaohongshu": "小红书",
    "wechat-channels": "微信视频号",
    "bilibili": "Bilibili",
    "kuaishou": "快手",
    "tiktok": "TikTok",
    "youtube-shorts": "YouTube Shorts",
    "youtube-long": "YouTube",
    "instagram-reels": "Instagram Reels",
    "facebook-reels": "Facebook Reels",
    "linkedin": "LinkedIn",
    "x": "X",
    "threads": "Threads",
    "pinterest": "Pinterest",
    "snapchat-spotlight": "Snapchat Spotlight",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def clean_lines(text: str) -> list[str]:
    return [
        line.strip().lstrip("#").strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("```")
    ]


def load_display_data(path: Path | None) -> dict:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("showcase data root must be an object")
    return payload


def build_case(manifest: dict, run_root: Path, display: dict) -> dict:
    brief_text = read_text(run_root / "source-brief.md")
    brief_lines = clean_lines(brief_text)
    copies = []
    for platform in manifest["platforms"]:
        copy_path = run_root / manifest["copy_files"][platform]
        copy_text = read_text(copy_path)
        copy_lines = clean_lines(copy_text)
        copies.append(
            {
                "platform": platform,
                "platform_label": PLATFORM_LABELS.get(platform, platform),
                "title": copy_lines[0] if copy_lines else PLATFORM_LABELS.get(platform, platform),
                "content": copy_text.strip() or "当前运行尚未写入平台文案。",
            }
        )

    locale = manifest["locale_assumptions"]
    case = {
        "manifest": manifest,
        "locale_assumptions": locale,
        "source": {
            "file_name": f"{manifest['article_slug']}.md",
            "title": display.get("source", {}).get(
                "title",
                brief_lines[0] if brief_lines else manifest["article_slug"],
            ),
            "language": locale.get("source_language"),
            "summary_paragraphs": brief_lines[1:4],
        },
        "brief": {
            "core_thesis": brief_lines[0] if brief_lines else "等待写入共享内容简报",
            "author_stance": "见 source-brief.md",
            "audience": "见 source-brief.md",
            "audience_need": "见 source-brief.md",
            "tone": "保持原文",
            "protected_claims": [],
        },
        "platforms": [
            {
                "id": platform,
                "label": PLATFORM_LABELS.get(platform, platform),
                "language": locale.get("target_language") or locale.get("source_language"),
                "market": locale.get("market"),
            }
            for platform in manifest["platforms"]
        ],
        "copies": copies,
        "visual_directions": [],
        "assets": manifest["assets"],
        "review_flags": manifest["review_flags"],
        "review_policy": manifest["review_policy"],
        "decision_provenance": manifest["decision_provenance"],
        "decisions": {
            "brief": "approved",
            "platforms": "approved",
        },
        "trace": {},
        "deliverables": [
            "source-brief.md",
            "manifest.json",
            *manifest["copy_files"].values(),
            "index.md",
            manifest["showcase_file"],
        ],
    }

    for key in (
        "source",
        "brief",
        "platforms",
        "copies",
        "visual_directions",
        "decisions",
        "trace",
        "deliverables",
    ):
        if key in display:
            if isinstance(case.get(key), dict) and isinstance(display[key], dict):
                case[key].update(display[key])
            else:
                case[key] = display[key]
    return case


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--data", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    try:
        manifest = load_json_object(args.manifest)
        errors = validate(manifest)
        errors.extend(validate_delivery(manifest, args.manifest.resolve().parent))
        if errors:
            raise ValueError("; ".join(errors))
        display = load_display_data(args.data)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        return fail(error, manifest=str(args.manifest.resolve()))

    run_root = args.manifest.resolve().parent
    output_dir = (args.output_dir or run_root / "showcase").resolve()

    skill_root = Path(__file__).resolve().parents[1]
    template_root = skill_root / "assets" / "static-showcase"
    template = read_text(template_root / "index.html")
    if TOKEN not in template:
        return fail("showcase template token is missing")

    case = build_case(manifest, run_root, display)
    encoded = json.dumps(case, ensure_ascii=False).replace("</", "<\\/")
    rendered = template.replace(TOKEN, encoded)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "index.html").write_text(rendered, encoding="utf-8")
        shutil.copyfile(template_root / "app.js", output_dir / "app.js")
        shutil.copyfile(template_root / "styles.css", output_dir / "styles.css")
    except OSError as error:
        return fail(error, showcase=str(output_dir))
    emit(
        {
            "status": "created",
            "showcase": str((output_dir / "index.html").resolve()),
            "files": ["index.html", "app.js", "styles.css"],
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
