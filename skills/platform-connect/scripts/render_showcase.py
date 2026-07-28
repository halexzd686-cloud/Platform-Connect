#!/usr/bin/env python3
"""Render the bundled offline Skill execution showcase."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import zipfile

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


def display_copy(text: str) -> str:
    """Remove the first Markdown title from the on-screen body only."""
    lines = text.strip().splitlines()
    if lines and lines[0].lstrip().startswith("#"):
        lines = lines[1:]
    return "\n".join(lines).strip()


def prompt_markdown(prompts: list[dict]) -> str:
    lines = ["# 配图提示词", ""]
    for index, item in enumerate(prompts, start=1):
        label = PLATFORM_LABELS.get(item.get("platform"), item.get("platform", "通用"))
        lines.extend(
            [
                f"## {index}. {label}｜{item.get('visual_direction', '视觉方向')}",
                "",
                f"- 用途：{item.get('purpose', '')}",
                f"- 资产类型：{item.get('asset_type', '')}",
                f"- 比例：{item.get('aspect_ratio', '')}",
                f"- 来源锚点：{item.get('source_anchor', '')}",
                "",
                "### 正向提示词",
                "",
                item.get("prompt", ""),
                "",
                "### 使用约束",
                "",
                f"- 画面文字：{item.get('on_image_text') or '建议无文字'}",
                f"- 负面约束：{item.get('negative_prompt', '')}",
                f"- 事实不变量：{'；'.join(item.get('factual_invariants', []))}",
                f"- 使用建议：{item.get('tool_notes', '')}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def create_downloads(manifest: dict, run_root: Path, output_dir: Path) -> dict:
    """Create user-facing files and one deterministic ZIP beside the showcase."""
    download_root = output_dir.parent / "downloads"
    download_root.mkdir(parents=True, exist_ok=True)
    files: list[dict] = []
    archive_members: list[tuple[Path, str]] = []

    for platform in manifest["platforms"]:
        label = PLATFORM_LABELS.get(platform, platform)
        file_name = f"{label}-文案.md"
        target = download_root / file_name
        source = run_root / manifest["copy_files"][platform]
        target.write_text(read_text(source).rstrip() + "\n", encoding="utf-8")
        files.append(
            {
                "path": f"downloads/{file_name}",
                "label": file_name,
                "description": f"{label}最终平台文案",
                "kind": "copy",
                "platform": platform,
            }
        )
        archive_members.append((target, file_name))

    prompts = manifest.get("visual_prompts", [])
    if prompts:
        prompt_name = "配图提示词.md"
        prompt_target = download_root / prompt_name
        prompt_target.write_text(prompt_markdown(prompts), encoding="utf-8")
        files.append(
            {
                "path": f"downloads/{prompt_name}",
                "label": prompt_name,
                "description": "全部平台的配图方向、提示词与使用约束",
                "kind": "visual-prompts",
            }
        )
        archive_members.append((prompt_target, prompt_name))

    notes_name = "交付说明.md"
    notes_target = download_root / notes_name
    labels = [PLATFORM_LABELS.get(item, item) for item in manifest["platforms"]]
    notes = "\n".join(
        [
            "# Platform Connect 交付说明",
            "",
            f"- 运行编号：{manifest['run_id']}",
            f"- 发布平台：{'、'.join(labels)}",
            f"- 最终文案：{len(manifest['copy_files'])} 份",
            f"- 配图提示词：{len(prompts)} 条",
            "- 说明：本目录是面向用户的可下载成果；来源与执行记录保留在看板折叠区。",
            "",
        ]
    )
    notes_target.write_text(notes, encoding="utf-8")
    files.append(
        {
            "path": f"downloads/{notes_name}",
            "label": notes_name,
            "description": "本次运行的交付范围与文件说明",
            "kind": "delivery-notes",
        }
    )
    archive_members.append((notes_target, notes_name))

    bundle_name = "Platform-Connect-成果包.zip"
    bundle_target = download_root / bundle_name
    with zipfile.ZipFile(bundle_target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source, archive_name in archive_members:
            archive.write(source, archive_name)

    return {
        "bundle": {
            "path": f"downloads/{bundle_name}",
            "description": f"包含 {len(files)} 个可直接使用的交付文件。",
            "file_count": len(files),
        },
        "files": files,
    }


def build_case(
    manifest: dict,
    run_root: Path,
    display: dict,
    downloads: dict,
) -> dict:
    brief_text = read_text(run_root / "source-brief.md")
    brief_lines = clean_lines(brief_text)
    manifest_source = manifest.get("source", {})
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
                "content": display_copy(copy_text) or "当前运行尚未写入平台文案。",
            }
        )

    locale = manifest["locale_assumptions"]
    visual_prompts = manifest["visual_prompts"]
    prompt_ready = (
        manifest.get("visual_prompt_intent") != "yes"
        or (
            bool(visual_prompts)
            and manifest.get("visual_prompt_approval") == "approved"
            and all(item.get("status") == "approved" for item in visual_prompts)
        )
    )
    case = {
        "manifest": manifest,
        "locale_assumptions": locale,
        "source": {
            "file_name": manifest_source.get("reference")
            or f"{manifest['article_slug']}.md",
            "title": display.get("source", {}).get(
                "title",
                manifest_source.get("title")
                or (brief_lines[0] if brief_lines else manifest["article_slug"]),
            ),
            "input_type": manifest_source.get("input_type", "pasted"),
            "media_type": manifest_source.get("media_type"),
            "read_status": manifest_source.get("read_status"),
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
        "platform_recommendations": manifest.get("platform_recommendations", []),
        "visual_prompts": visual_prompts,
        "outcome": {
            "platform_count": len(manifest["platforms"]),
            "copy_count": len(copies),
            "visual_prompt_count": len(visual_prompts),
            "status": (
                "ready"
                if manifest.get("copy_approval") == "approved"
                and prompt_ready
                else "in-progress"
            ),
        },
        "review_flags": manifest["review_flags"],
        "review_policy": manifest["review_policy"],
        "decision_provenance": manifest["decision_provenance"],
        "decisions": {
            "brief": "approved",
            "platforms": "approved",
        },
        "trace": {},
        "downloads": downloads,
    }

    for key in (
        "source",
        "brief",
        "platforms",
        "copies",
        "platform_recommendations",
        "visual_prompts",
        "outcome",
        "decisions",
        "trace",
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

    try:
        downloads = create_downloads(manifest, run_root, output_dir)
        case = build_case(manifest, run_root, display, downloads)
        encoded = json.dumps(case, ensure_ascii=False).replace("</", "<\\/")
        rendered = template.replace(TOKEN, encoded)
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
            "downloads": downloads,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
