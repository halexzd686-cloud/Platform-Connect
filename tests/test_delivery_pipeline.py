from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
DELIVER = REPO_ROOT / "skills" / "platform-connect" / "scripts" / "deliver.py"


def platform_markdown(
    platform: str,
    copy: str = "这是一份平台原生文案。",
    prompt: str = "本次未请求配图提示词",
    notes: str = "无额外说明",
) -> str:
    return (
        f"# {platform}\n\n"
        f"## 发布文案\n\n{copy}\n\n"
        f"## 配图提示词\n\n{prompt}\n\n"
        f"## 交付说明\n\n{notes}\n"
    )


def run_delivery(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(DELIVER), *arguments],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class DeliveryPipelineTests(unittest.TestCase):
    def test_builds_exact_minimal_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "drafts"
            source.mkdir()
            xhs = source / "xhs.md"
            x = source / "x.md"
            xhs.write_text(
                platform_markdown(
                    "小红书",
                    "HTML 到底是什么？\n\n- 网页结构\n- 内容标记",
                    "3:4 教育信息图，保持 HTML 示例准确。",
                ),
                encoding="utf-8",
            )
            x.write_text(
                platform_markdown(
                    "X",
                    "HTML gives a webpage its document structure.",
                    "16:9 developer-note illustration; do not invent browser behavior.",
                    "面向全球中文技术读者。",
                ),
                encoding="utf-8",
            )

            result = run_delivery(
                str(xhs),
                str(x),
                "--title",
                "HTML 入门",
                "--output-root",
                str(root / "outputs"),
                "--run-id",
                "20260729-120000",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "completed")

            run_root = Path(payload["run_root"])
            showcase = run_root / "showcase.html"
            result_dir = run_root / "HTML 入门"
            self.assertEqual(
                {
                    path.relative_to(run_root).as_posix()
                    for path in run_root.rglob("*")
                    if path.is_file()
                },
                {
                    "showcase.html",
                    "HTML 入门/小红书.md",
                    "HTML 入门/X.md",
                },
            )

            document = showcase.read_text(encoding="utf-8")
            self.assertIn("<style>", document)
            self.assertIn("<script>", document)
            self.assertIn("从一份表达，", document)
            self.assertIn("HTML 到底是什么", document)
            self.assertIn('href="HTML 入门/小红书.md"', document)
            self.assertNotIn("FACT REMINDERS", document)
            self.assertNotIn("使用前需要保留的事实", document)
            self.assertNotIn("<link", document)
            self.assertNotIn('src="app.js"', document)
            self.assertNotRegex(document, r"https?://")
            self.assertTrue((result_dir / "小红书.md").is_file())

    def test_rejects_missing_required_section(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "bad.md"
            source.write_text(
                "# 小红书\n\n## 发布文案\n\n只有文案。\n",
                encoding="utf-8",
            )
            result = run_delivery(
                str(source),
                "--title",
                "测试",
                "--output-root",
                str(root / "outputs"),
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stderr)
            self.assertEqual(payload["status"], "failed")
            self.assertIn("missing required sections", payload["error"])
            self.assertFalse((root / "outputs").exists())

    def test_rejects_duplicate_platforms(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "one.md"
            second = root / "two.md"
            first.write_text(platform_markdown("X"), encoding="utf-8")
            second.write_text(platform_markdown("x"), encoding="utf-8")
            result = run_delivery(
                str(first),
                str(second),
                "--title",
                "测试",
                "--output-root",
                str(root / "outputs"),
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("duplicate platform", result.stderr)

    def test_refuses_to_overwrite_existing_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "x.md"
            source.write_text(platform_markdown("X"), encoding="utf-8")
            arguments = (
                str(source),
                "--title",
                "测试",
                "--output-root",
                str(root / "outputs"),
                "--run-id",
                "same-run",
            )
            first = run_delivery(*arguments)
            second = run_delivery(*arguments)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 2)
            self.assertIn("already exists", second.stderr)


if __name__ == "__main__":
    unittest.main()
