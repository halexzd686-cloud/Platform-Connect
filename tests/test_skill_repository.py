from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
