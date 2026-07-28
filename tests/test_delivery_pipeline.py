from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills" / "platform-connect" / "scripts"


def run_script(name: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *arguments],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def approved_prompt(
    platform: str = "xiaohongshu",
    prompt_id: str = "xiaohongshu-cover-01",
) -> dict:
    return {
        "id": prompt_id,
        "platform": platform,
        "asset_type": "cover",
        "purpose": "表达文章核心判断",
        "source_anchor": "core-thesis",
        "core_idea": "AI 重组任务而不是直接替代岗位",
        "aspect_ratio": "3:4",
        "visual_direction": "克制的编辑部观点海报",
        "on_image_text": "重新分工",
        "prompt": "3:4 编辑部观点海报，以重新排列的任务卡片表达工作重组。",
        "negative_prompt": "不要机器人头像，不要虚构数据，不要科幻霓虹。",
        "factual_invariants": ["不把任务重组夸大为岗位必然消失"],
        "tool_notes": "文字不稳定时生成无字底图。",
        "status": "approved",
    }


def approve_full_manifest(manifest: dict, prompts: list[dict]) -> None:
    manifest.update(
        {
            "copy_approval": "approved",
            "visual_prompt_intent": "yes",
            "visual_prompt_approval": "approved",
            "decision_provenance": {
                "brief": "bundled",
                "platforms": manifest["decision_provenance"]["platforms"],
                "copy_approval": "bundled",
                "visual_prompt_intent": "explicit",
                "visual_prompt_approval": "bundled",
            },
            "visual_prompts": prompts,
        }
    )


class DeliveryPipelineTests(unittest.TestCase):
    def test_complete_prompt_first_offline_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            prepared = run_script(
                "prepare_workspace.py",
                "ai-work",
                "--platforms",
                "xiaohongshu",
                "linkedin",
                "--mode",
                "full",
                "--root",
                str(root),
                "--run-id",
                "smoke-001",
                "--target-language",
                "en",
                "--market",
                "global",
            )
            self.assertEqual(prepared.returncode, 0, prepared.stdout + prepared.stderr)
            run_root = Path(json.loads(prepared.stdout)["workspace"])
            manifest_path = run_root / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["skill_version"], "1.4.1")
            self.assertEqual(manifest["schema_version"], "1.4")
            self.assertFalse((run_root / "xiaohongshu" / "images").exists())

            (run_root / "source-brief.md").write_text(
                "# AI 重新分配工作\n\nAI 改变岗位内部的任务组合。\n",
                encoding="utf-8",
            )
            (run_root / "xiaohongshu" / "copy.md").write_text(
                "# AI 不先拿走工作\n\n它先重新分配任务。",
                encoding="utf-8",
            )
            (run_root / "linkedin" / "copy.md").write_text(
                "# AI redistributes tasks\n\nThe role remains accountable.",
                encoding="utf-8",
            )
            prompts = [
                approved_prompt(),
                approved_prompt("linkedin", "linkedin-cover-01")
                | {
                    "aspect_ratio": "4:5",
                    "on_image_text": "TASKS × JUDGMENT",
                },
            ]
            approve_full_manifest(manifest, prompts)
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            finalized = run_script("finalize_delivery.py", str(manifest_path))
            self.assertEqual(finalized.returncode, 0, finalized.stdout + finalized.stderr)
            completion = json.loads(finalized.stdout)
            self.assertEqual(completion["status"], "completed")
            self.assertEqual(Path(completion["run_root"]), run_root)
            self.assertEqual(
                Path(completion["showcase"]),
                run_root / "showcase" / "index.html",
            )
            self.assertEqual(
                Path(completion["bundle"]),
                run_root / "downloads" / "Platform-Connect-成果包.zip",
            )
            showcase = run_root / "showcase"
            index_text = (run_root / "index.md").read_text(encoding="utf-8")
            self.assertIn("生图提示词", index_text)
            self.assertNotIn("尚未生成", index_text)
            self.assertEqual(
                {path.name for path in showcase.iterdir()},
                {"index.html", "app.js", "styles.css"},
            )
            downloads = run_root / "downloads"
            self.assertTrue((downloads / "Platform-Connect-成果包.zip").is_file())
            self.assertTrue((downloads / "小红书-文案.md").is_file())
            self.assertTrue((downloads / "LinkedIn-文案.md").is_file())
            self.assertTrue((downloads / "配图提示词.md").is_file())
            self.assertTrue((downloads / "交付说明.md").is_file())
            with zipfile.ZipFile(downloads / "Platform-Connect-成果包.zip") as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {
                        "小红书-文案.md",
                        "LinkedIn-文案.md",
                        "配图提示词.md",
                        "交付说明.md",
                    },
                )
                self.assertIsNone(archive.testzip())

    def test_finalizer_creates_showcase_for_copy_without_explicit_file_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prepared = run_script(
                "prepare_workspace.py",
                "copy-only",
                "--platforms",
                "xiaohongshu",
                "--mode",
                "copy",
                "--review-policy",
                "autopilot",
                "--root",
                temp_dir,
                "--run-id",
                "copy-002",
            )
            self.assertEqual(prepared.returncode, 0, prepared.stdout + prepared.stderr)
            run_root = Path(json.loads(prepared.stdout)["workspace"])
            manifest_path = run_root / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["copy_approval"] = "approved"
            manifest["decision_provenance"].update(
                {
                    "brief": "preauthorized",
                    "copy_approval": "preauthorized",
                    "visual_prompt_intent": "inferred",
                }
            )
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (run_root / "source-brief.md").write_text(
                "# 核心判断\n\n这是一份完整简报。\n",
                encoding="utf-8",
            )
            (run_root / "xiaohongshu" / "copy.md").write_text(
                "# 最终文案\n\n这是已经确认的平台文案。\n",
                encoding="utf-8",
            )

            finalized = run_script("finalize_delivery.py", str(manifest_path))
            self.assertEqual(finalized.returncode, 0, finalized.stdout + finalized.stderr)
            completion = json.loads(finalized.stdout)
            self.assertEqual(completion["status"], "completed")
            self.assertTrue(Path(completion["showcase"]).is_file())
            self.assertTrue(Path(completion["bundle"]).is_file())
            self.assertFalse((run_root / "downloads" / "配图提示词.md").exists())

    def test_finalizer_blocks_incomplete_copy_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prepared = run_script(
                "prepare_workspace.py",
                "unfinished-copy",
                "--platforms",
                "xiaohongshu",
                "--mode",
                "copy",
                "--root",
                temp_dir,
                "--run-id",
                "copy-001",
            )
            self.assertEqual(prepared.returncode, 0, prepared.stdout + prepared.stderr)
            manifest_path = Path(json.loads(prepared.stdout)["manifest"])
            finalized = run_script("finalize_delivery.py", str(manifest_path))
            self.assertNotEqual(finalized.returncode, 0)
            payload = json.loads(finalized.stdout)
            self.assertEqual(payload["status"], "failed")
            self.assertIn("copy approval must be approved", payload["errors"][0])
            self.assertFalse((manifest_path.parent / "showcase" / "index.html").exists())

    def test_image_generation_fields_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prepared = run_script(
                "prepare_workspace.py",
                "no-image-tools",
                "--platforms",
                "xiaohongshu",
                "--mode",
                "full",
                "--root",
                temp_dir,
                "--run-id",
                "prompt-001",
            )
            manifest_path = Path(json.loads(prepared.stdout)["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            prompt = approved_prompt() | {
                "file": "xiaohongshu/images/cover.png",
                "generation_status": "ready",
                "qa": {"facts": "passed"},
            }
            approve_full_manifest(manifest, [prompt])
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = run_script("validate_manifest.py", str(manifest_path))
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(
                any(
                    "image-generation fields" in error
                    for error in json.loads(result.stdout)["errors"]
                )
            )

    def test_visual_prompt_limit_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prepared = run_script(
                "prepare_workspace.py",
                "prompt-limit",
                "--platforms",
                "xiaohongshu",
                "--mode",
                "full",
                "--root",
                temp_dir,
                "--run-id",
                "prompt-002",
            )
            manifest_path = Path(json.loads(prepared.stdout)["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            prompts = [
                approved_prompt(prompt_id=f"prompt-{index}")
                for index in range(4)
            ]
            approve_full_manifest(manifest, prompts)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = run_script("validate_manifest.py", str(manifest_path))
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(
                any(
                    "visual_prompt_limit" in error
                    for error in json.loads(result.stdout)["errors"]
                )
            )

    def test_copy_mode_rejects_visual_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prepared = run_script(
                "prepare_workspace.py",
                "copy-only",
                "--platforms",
                "linkedin",
                "--mode",
                "copy",
                "--root",
                temp_dir,
                "--run-id",
                "copy-001",
            )
            manifest_path = Path(json.loads(prepared.stdout)["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["visual_prompt_intent"] = "yes"
            manifest["visual_prompts"] = [
                approved_prompt("linkedin", "linkedin-cover-01")
            ]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = run_script("validate_manifest.py", str(manifest_path))
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(
                any(
                    "copy mode" in error
                    for error in json.loads(result.stdout)["errors"]
                )
            )

    def test_compact_policy_accepts_one_bundled_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prepared = run_script(
                "prepare_workspace.py",
                "compact-review",
                "--platforms",
                "xiaohongshu",
                "--mode",
                "full",
                "--review-policy",
                "compact",
                "--platform-source",
                "inferred",
                "--root",
                temp_dir,
                "--run-id",
                "compact-001",
            )
            manifest_path = Path(json.loads(prepared.stdout)["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            approve_full_manifest(manifest, [approved_prompt()])
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = run_script("validate_manifest.py", str(manifest_path))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_autopilot_accepts_recorded_preauthorization(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prepared = run_script(
                "prepare_workspace.py",
                "autopilot-valid",
                "--platforms",
                "linkedin",
                "--mode",
                "full",
                "--review-policy",
                "autopilot",
                "--platform-source",
                "preauthorized",
                "--root",
                temp_dir,
                "--run-id",
                "autopilot-001",
            )
            manifest_path = Path(json.loads(prepared.stdout)["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.update(
                {
                    "copy_approval": "approved",
                    "visual_prompt_approval": "approved",
                    "decision_provenance": {
                        "brief": "preauthorized",
                        "platforms": "preauthorized",
                        "copy_approval": "preauthorized",
                        "visual_prompt_intent": "inferred",
                        "visual_prompt_approval": "preauthorized",
                    },
                    "visual_prompts": [
                        approved_prompt("linkedin", "linkedin-cover-01")
                    ],
                }
            )
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = run_script("validate_manifest.py", str(manifest_path))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_file_source_and_platform_recommendations_are_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prepared = run_script(
                "prepare_workspace.py",
                "document-intake",
                "--platforms",
                "xiaohongshu",
                "x",
                "--platform-source",
                "inferred",
                "--source-type",
                "file",
                "--source-ref",
                "article.pdf",
                "--source-title",
                "AI 与工作重组",
                "--source-media-type",
                "application/pdf",
                "--root",
                temp_dir,
                "--run-id",
                "source-001",
            )
            manifest_path = Path(json.loads(prepared.stdout)["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["platform_recommendations"] = [
                {
                    "platform": "xiaohongshu",
                    "rationale": "适合用收藏型结构拆解判断框架",
                    "visual_direction": "编辑部观点海报",
                    "selection_status": "selected",
                },
                {
                    "platform": "x",
                    "rationale": "适合用短线程表达核心观点",
                    "visual_direction": "双语任务拆解图",
                    "selection_status": "selected",
                },
            ]
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False),
                encoding="utf-8",
            )
            result = run_script("validate_manifest.py", str(manifest_path))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_pasted_source_can_record_supporting_url_without_refetch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prepared = run_script(
                "prepare_workspace.py",
                "pasted-with-url",
                "--platforms",
                "linkedin",
                "--source-type",
                "pasted",
                "--supporting-ref",
                "https://example.com/article",
                "--root",
                temp_dir,
                "--run-id",
                "source-002",
            )
            self.assertEqual(prepared.returncode, 0, prepared.stdout + prepared.stderr)
            manifest = json.loads(
                Path(json.loads(prepared.stdout)["manifest"]).read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(manifest["source"]["input_type"], "pasted")
            self.assertEqual(
                manifest["source"]["supporting_references"],
                ["https://example.com/article"],
            )

    def test_incomplete_source_blocks_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prepared = run_script(
                "prepare_workspace.py",
                "blocked-source",
                "--platforms",
                "linkedin",
                "--root",
                temp_dir,
                "--run-id",
                "source-003",
            )
            manifest_path = Path(json.loads(prepared.stdout)["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["source"]["read_status"] = "blocked"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = run_script("validate_manifest.py", str(manifest_path))
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(
                any(
                    "completely read" in error
                    for error in json.loads(result.stdout)["errors"]
                )
            )

    def test_single_platform_recommendation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prepared = run_script(
                "prepare_workspace.py",
                "bad-recommendations",
                "--platforms",
                "linkedin",
                "--platform-source",
                "inferred",
                "--root",
                temp_dir,
                "--run-id",
                "recommend-001",
            )
            manifest_path = Path(json.loads(prepared.stdout)["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["platform_recommendations"] = [
                {
                    "platform": "linkedin",
                    "rationale": "专业受众",
                    "visual_direction": "编辑图解",
                    "selection_status": "selected",
                }
            ]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = run_script("validate_manifest.py", str(manifest_path))
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(
                any(
                    "two or three" in error
                    for error in json.loads(result.stdout)["errors"]
                )
            )

    def test_prepare_workspace_refuses_overwrite_with_json_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            arguments = (
                "same-run",
                "--platforms",
                "linkedin",
                "--root",
                temp_dir,
                "--run-id",
                "fixed",
            )
            first = run_script("prepare_workspace.py", *arguments)
            second = run_script("prepare_workspace.py", *arguments)
            self.assertEqual(first.returncode, 0)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(json.loads(second.stdout)["status"], "failed")

    def test_script_failures_are_structured_json(self) -> None:
        result = run_script(
            "prepare_workspace.py",
            "../escape",
            "--platforms",
            "linkedin",
        )
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "failed")
        self.assertTrue(payload["errors"])


if __name__ == "__main__":
    unittest.main()
