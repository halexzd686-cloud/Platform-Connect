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
        self.assertIn("Never use `inferred` for `image_intent=yes`", policy)

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
        self.assertIn("two platforms by default", skill)
        self.assertIn("platform selection, image intent", policy)

    def test_showcase_is_outcome_first(self) -> None:
        html = (
            SKILL / "assets" / "static-showcase" / "index.html"
        ).read_text(encoding="utf-8")
        app = (
            SKILL / "assets" / "static-showcase" / "app.js"
        ).read_text(encoding="utf-8")
        self.assertIn("OUTCOME CONSOLE", html)
        self.assertIn("最终平台图文", html)
        self.assertIn("<img", app)
        self.assertIn("platform_recommendations", app)

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
            "npx skills add halexzd686-cloud/Platform-Connect",
            readme,
        )
        self.assertIn("--agent codex", readme)
        self.assertIn("--skill platform-connect", readme)
        self.assertIn("--global", readme)
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
