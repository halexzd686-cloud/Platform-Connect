from __future__ import annotations

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
        self.assertTrue(fields["description"].startswith("Adapts "))
        self.assertLessEqual(len(fields["description"]), 1024)

    def test_skill_uses_one_default_flow(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for removed in (
            "`plan`",
            "`copy`",
            "`full`",
            "`compact`",
            "`strict`",
            "`autopilot`",
            "manifest.json",
            "source-brief.md",
            "platform-connect.profile.json",
            "decision provenance",
        ):
            self.assertNotIn(removed, skill)
        self.assertIn("Deliver in chat by default", skill)
        self.assertIn("Create files only when the user asks", skill)
        self.assertIn("recommend two suitable platforms", skill)

    def test_only_minimal_references_remain(self) -> None:
        names = {
            path.name for path in (SKILL / "references").glob("*.md")
        }
        self.assertEqual(
            names,
            {
                "source-intake.md",
                "platform-adapters.md",
                "visual-handoff.md",
                "output-schema.md",
            },
        )
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for name in names:
            self.assertIn(f"references/{name}", skill)

    def test_delivery_is_one_script_and_no_frontend_bundle(self) -> None:
        scripts = {
            path.name for path in (SKILL / "scripts").glob("*.py")
        }
        self.assertEqual(scripts, {"deliver.py"})
        self.assertFalse((SKILL / "assets" / "static-showcase").exists())
        deliver = (SKILL / "scripts" / "deliver.py").read_text(encoding="utf-8")
        self.assertIn("<style>", deliver)
        self.assertIn("<script>", deliver)
        self.assertNotRegex(deliver, r"\bmanifest\b")

    def test_direct_source_intake_is_preserved(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        intake = (SKILL / "references" / "source-intake.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("[source-intake.md](references/source-intake.md)", skill)
        for extension in (".txt", ".md", ".docx", ".pdf", ".html"):
            self.assertIn(extension, intake)
        self.assertIn("Article URL", intake)
        self.assertIn("Do not fetch a URL merely because", intake)

    def test_image_requests_only_create_prompt_text(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        handoff = (SKILL / "references" / "visual-handoff.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Never call an image-generation", skill)
        self.assertIn("one editable prompt per selected platform", handoff)
        self.assertNotIn("Xiaohei", skill)
        self.assertNotIn("approval", handoff.lower())

    def test_behavior_eval_catalog_matches_simplified_contract(self) -> None:
        cases = json.loads(
            (REPO_ROOT / "tests" / "evals" / "platform-connect.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertGreaterEqual(len(cases), 4)
        self.assertEqual(len({case["id"] for case in cases}), len(cases))
        for case in cases:
            self.assertTrue(case["prompt"])
            self.assertTrue(case["expected_behavior"])
            self.assertTrue(case["forbidden_behavior"])
            self.assertNotIn("mode", case)
            self.assertNotIn("review_policy", case)

    def test_repository_text_is_utf8(self) -> None:
        roots = [SKILL, REPO_ROOT / "README.md"]
        for root in roots:
            paths = root.rglob("*") if root.is_dir() else [root]
            for path in paths:
                if path.is_file() and path.suffix in {
                    ".md",
                    ".py",
                    ".yaml",
                    ".json",
                    ".html",
                    ".css",
                    ".js",
                }:
                    text = path.read_text(encoding="utf-8")
                    self.assertNotIn("\ufffd", text, str(path))

    def test_readme_uses_canonical_install_command(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("skills/platform-connect", readme)
        self.assertIn(
            "npx skills add https://github.com/halexzd686-cloud/Platform-Connect",
            readme,
        )
        self.assertEqual(readme.count("npx skills"), 1)
        self.assertNotIn("86188", readme)

    def test_project_skill_lock_targets_the_canonical_skill(self) -> None:
        lock = json.loads(
            (REPO_ROOT / "skills-lock.json").read_text(encoding="utf-8")
        )
        entry = lock["skills"]["platform-connect"]
        self.assertEqual(entry["source"], "halexzd686-cloud/Platform-Connect")
        self.assertEqual(entry["skillPath"], "skills/platform-connect/SKILL.md")
        self.assertRegex(entry["computedHash"], re.compile(r"^[0-9a-f]{64}$"))


if __name__ == "__main__":
    unittest.main()
