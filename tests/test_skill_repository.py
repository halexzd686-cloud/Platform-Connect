from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import subprocess
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "skills" / "platform-connect"


class SkillRepositoryTests(unittest.TestCase):
    def test_skill_has_one_canonical_source(self) -> None:
        self.assertTrue((SKILL / "SKILL.md").is_file())
        tracked = subprocess.run(
            [
                "git",
                "ls-files",
                ".agents/skills/platform-connect/**",
                ".claude/skills/platform-connect/**",
            ],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(tracked, "")

    def test_installation_directories_are_ignored(self) -> None:
        rules = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("/.agents/", rules)
        self.assertIn("/.claude/", rules)

    def test_skill_frontmatter_is_valid(self) -> None:
        lines = (SKILL / "SKILL.md").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], "---")
        closing = lines.index("---", 1)
        fields = {}
        for line in lines[1:closing]:
            key, separator, value = line.partition(":")
            self.assertEqual(separator, ":")
            fields[key.strip()] = value.strip()
        self.assertEqual(set(fields), {"name", "description"})
        self.assertEqual(fields["name"], SKILL.name)
        self.assertRegex(fields["name"], re.compile(r"^[a-z0-9-]{1,64}$"))
        self.assertTrue(fields["description"])
        self.assertTrue(fields["description"].startswith("Adapts "))
        self.assertLessEqual(len(fields["description"]), 1024)

    def test_long_references_have_contents_and_no_nested_routes(self) -> None:
        references = SKILL / "references"
        markdown_link = re.compile(r"\]\((?!https?://)([^)]+\.md)(?:#[^)]+)?\)")
        for path in references.glob("*.md"):
            text = path.read_text(encoding="utf-8")
            if len(text.splitlines()) > 100:
                self.assertIn("## Contents", text, str(path))
            self.assertEqual(
                markdown_link.findall(text),
                [],
                f"reference-to-reference routing belongs in SKILL.md: {path}",
            )

    def test_shared_versions_match_delivery_example(self) -> None:
        shared = (SKILL / "scripts" / "_shared.py").read_text(encoding="utf-8")
        tree = ast.parse(shared)
        constants = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name) and target.id in {
                    "SCHEMA_VERSION",
                    "SKILL_VERSION",
                }:
                    constants[target.id] = ast.literal_eval(node.value)
        schema = (SKILL / "references" / "output-schema.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(f'"schema_version": "{constants["SCHEMA_VERSION"]}"', schema)
        self.assertIn(f'"skill_version": "{constants["SKILL_VERSION"]}"', schema)

    def test_review_policies_are_routed_and_default_to_compact(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        policy = (
            SKILL / "references" / "interaction-policy.md"
        ).read_text(encoding="utf-8")
        self.assertIn("[interaction-policy.md](references/interaction-policy.md)", skill)
        self.assertIn("`compact` is the default", skill)
        for name in ("Compact", "Strict", "Autopilot"):
            self.assertIn(f"## {name}", policy)
        self.assertIn("Never call an image-generation", skill)
        self.assertIn("visual prompt approval", policy.lower())

    def test_direct_source_intake_and_recommendations_are_routed(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        intake = (SKILL / "references" / "source-intake.md").read_text(
            encoding="utf-8"
        )
        policy = (
            SKILL / "references" / "interaction-policy.md"
        ).read_text(encoding="utf-8")
        self.assertIn("[source-intake.md](references/source-intake.md)", skill)
        for extension in (".txt", ".md", ".docx", ".pdf", ".html"):
            self.assertIn(extension, intake)
        self.assertIn("Article URL", intake)
        self.assertIn("Do not fetch a URL merely because", intake)
        self.assertIn("two platforms by default", skill)
        self.assertIn("whether to include visual prompts", policy)

    def test_showcase_is_outcome_first(self) -> None:
        html = (
            SKILL / "assets" / "static-showcase" / "index.html"
        ).read_text(encoding="utf-8")
        app = (
            SKILL / "assets" / "static-showcase" / "app.js"
        ).read_text(encoding="utf-8")
        self.assertIn("OUTCOME CONSOLE", html)
        self.assertIn("从一份表达，", html)
        self.assertIn("到多种抵达", html)
        self.assertIn("各平台最终文案", html)
        self.assertIn("配图建议与提示词", html)
        self.assertIn("下载本次成果", html)
        self.assertNotIn("这组内容从哪里来", html)
        self.assertNotIn("outcome-index", html)
        self.assertIn("visual_prompts", app)
        self.assertIn("downloads", app)
        self.assertNotIn("<img", app)
        self.assertIn("platform_recommendations", app)

    def test_copy_and_full_require_verified_showcase(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "For every `copy` or `full` run",
            skill,
        )
        self.assertIn(
            "even when the user did not ask to save files or generate HTML",
            skill,
        )
        self.assertIn(
            "Never finish a `copy` or `full` run with chat content alone",
            skill,
        )
        self.assertIn(
            "downloads/Platform-Connect-成果包.zip",
            skill,
        )
        self.assertIn("scripts/finalize_delivery.py", skill)
        self.assertTrue((SKILL / "scripts" / "finalize_delivery.py").is_file())
        self.assertNotIn("When filesystem output is requested", skill)

    def test_skill_never_calls_image_tools(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        handoff = (SKILL / "references" / "visual-handoff.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Never call an image-generation", skill)
        self.assertIn("Do not generate preview images", handoff)
        self.assertIn("Do not use `view_image`", handoff)
        self.assertNotIn("once per distinct asset", skill)

    def test_behavior_eval_catalog_is_actionable(self) -> None:
        path = REPO_ROOT / "tests" / "evals" / "platform-connect.json"
        cases = json.loads(path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(cases), 3)
        self.assertEqual(len({case["id"] for case in cases}), len(cases))
        for case in cases:
            self.assertIn(case["mode"], {"plan", "copy", "full"})
            self.assertIn(
                case["review_policy"],
                {"strict", "compact", "autopilot"},
            )
            self.assertTrue(case["prompt"])
            self.assertTrue(case["expected_behavior"])
            self.assertTrue(case["forbidden_behavior"])

    def test_repository_text_is_utf8(self) -> None:
        roots = [SKILL, REPO_ROOT / "README.md"]
        for root in roots:
            paths = root.rglob("*") if root.is_dir() else [root]
            for path in paths:
                if path.is_file() and path.suffix in {".md", ".py", ".yaml", ".json", ".html", ".css", ".js"}:
                    text = path.read_text(encoding="utf-8")
                    self.assertNotIn("\ufffd", text, str(path))

    def test_readme_uses_canonical_name(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("skills/platform-connect", readme)
        self.assertNotIn("skills/adapt-content-for-platforms", readme)

    def test_readme_documents_project_install_without_tracking_copies(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "npx skills add https://github.com/halexzd686-cloud/Platform-Connect",
            readme,
        )
        self.assertIn("--skill platform-connect", readme)
        self.assertIn("--global", readme)
        self.assertIn("安装当前版本 v1.4.1", readme)
        self.assertEqual(readme.count("npx skills"), 1)
        self.assertIn("不要直接修改安装副本", readme)

    def test_project_skill_lock_targets_the_canonical_skill(self) -> None:
        lock = json.loads(
            (REPO_ROOT / "skills-lock.json").read_text(encoding="utf-8")
        )
        entry = lock["skills"]["platform-connect"]
        self.assertEqual(entry["source"], "halexzd686-cloud/Platform-Connect")
        self.assertEqual(
            entry["skillPath"],
            "skills/platform-connect/SKILL.md",
        )
        self.assertRegex(entry["computedHash"], re.compile(r"^[0-9a-f]{64}$"))


if __name__ == "__main__":
    unittest.main()
