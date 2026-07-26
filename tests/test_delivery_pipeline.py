from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


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


class DeliveryPipelineTests(unittest.TestCase):
    def test_complete_offline_smoke_pipeline(self) -> None:
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
            prepared_payload = json.loads(prepared.stdout)
            run_root = Path(prepared_payload["workspace"])
            manifest_path = run_root / "manifest.json"
            self.assertEqual(
                json.loads(manifest_path.read_text(encoding="utf-8"))["skill_version"],
                "1.0.0",
            )

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
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.update(
                {
                    "copy_approval": "approved",
                    "image_intent": "yes",
                    "visual_direction_approval": "approved",
                    "visual_manifest_approval": "approved",
                    "global_style_id": "editorial-poster",
                    "assets": [
                        {
                            "id": "xiaohongshu-cover-01",
                            "platform": "xiaohongshu",
                            "asset_type": "cover",
                            "purpose": "表达任务重组",
                            "source_anchor": "core-thesis",
                            "core_idea": "工作被重新拆分",
                            "aspect_ratio": "3:4",
                            "style_id": "editorial-poster",
                            "on_image_text": "重新分工",
                            "custom_prompt": "",
                            "planning_status": "approved",
                            "generation_status": "ready",
                            "file": "xiaohongshu/images/cover-01.png",
                            "qa": {
                                "facts": "passed",
                                "text": "passed",
                                "composition": "passed",
                                "style": "passed",
                            },
                        }
                    ],
                }
            )
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            validated = run_script("validate_manifest.py", str(manifest_path))
            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)
            self.assertEqual(json.loads(validated.stdout)["status"], "passed")

            rendered = run_script("render_showcase.py", str(manifest_path))
            self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
            showcase = run_root / "showcase"

            checked = run_script("validate_showcase.py", str(showcase))
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            self.assertEqual(json.loads(checked.stdout)["status"], "passed")

            indexed = run_script("build_delivery_index.py", str(manifest_path))
            self.assertEqual(indexed.returncode, 0, indexed.stdout + indexed.stderr)
            self.assertTrue((run_root / "index.md").is_file())
            self.assertEqual(
                {path.name for path in showcase.iterdir()},
                {"index.html", "app.js", "styles.css"},
            )

    def test_generation_is_blocked_before_visual_approval(self) -> None:
        manifest = {
            "schema_version": "1.1",
            "skill_version": "1.0.0",
            "article_slug": "blocked",
            "run_id": "blocked-001",
            "parent_run_id": None,
            "mode": "full",
            "platforms": ["douyin"],
            "locale_assumptions": {
                "source_language": "zh-CN",
                "target_language": None,
                "market": None,
            },
            "copy_approval": "approved",
            "image_intent": "yes",
            "visual_direction_approval": "approved",
            "visual_manifest_approval": "pending",
            "copy_files": {"douyin": "douyin/copy.md"},
            "showcase_file": "showcase/index.html",
            "assets": [
                {
                    "id": "douyin-cover-01",
                    "platform": "douyin",
                    "asset_type": "cover",
                    "purpose": "开场",
                    "source_anchor": "thesis",
                    "core_idea": "one idea",
                    "aspect_ratio": "9:16",
                    "style_id": "editorial",
                    "on_image_text": "",
                    "planning_status": "approved",
                    "generation_status": "ready",
                    "qa": {
                        "facts": "passed",
                        "text": "passed",
                        "composition": "passed",
                        "style": "passed",
                    },
                }
            ],
            "review_flags": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = run_script("validate_manifest.py", str(manifest_path))
            self.assertNotEqual(result.returncode, 0)
            errors = json.loads(result.stdout)["errors"]
            self.assertTrue(any("all visual gates" in error for error in errors))

    def test_script_failures_are_structured_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_manifest = Path(temp_dir) / "missing.json"
            for script in (
                "validate_manifest.py",
                "render_showcase.py",
                "build_delivery_index.py",
            ):
                result = run_script(script, str(missing_manifest))
                self.assertNotEqual(result.returncode, 0, script)
                self.assertEqual(result.stderr, "", script)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["status"], "failed", script)
                self.assertTrue(payload["errors"], script)

            missing_showcase = Path(temp_dir) / "missing-showcase"
            result = run_script("validate_showcase.py", str(missing_showcase))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["status"], "failed")

    def test_prepare_workspace_refuses_overwrite_with_json_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            arguments = (
                "immutable-run",
                "--platforms",
                "linkedin",
                "--root",
                temp_dir,
                "--run-id",
                "same-run",
            )
            first = run_script("prepare_workspace.py", *arguments)
            second = run_script("prepare_workspace.py", *arguments)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(second.stderr, "")
            payload = json.loads(second.stdout)
            self.assertEqual(payload["status"], "failed")
            self.assertTrue(any("will not be overwritten" in item for item in payload["errors"]))


if __name__ == "__main__":
    unittest.main()
