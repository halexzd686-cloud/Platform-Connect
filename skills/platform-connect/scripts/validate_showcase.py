#!/usr/bin/env python3
"""Validate a rendered offline Platform Connect showcase."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re


REQUIRED_FILES = {"index.html", "app.js", "styles.css"}
REMOTE_PATTERN = re.compile(r"""(?:https?:)?//""", re.IGNORECASE)


class CaseDataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.capture = False
        self.case_data = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "script" and values.get("id") == "case-data":
            self.capture = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.capture:
            self.capture = False

    def handle_data(self, data: str) -> None:
        if self.capture:
            self.case_data += data


def validate(showcase: Path) -> list[str]:
    errors: list[str] = []
    if not showcase.is_dir():
        return ["showcase path must be a directory"]

    files = {path.name for path in showcase.iterdir() if path.is_file()}
    missing = REQUIRED_FILES - files
    extra = files - REQUIRED_FILES
    if missing:
        errors.append(f"missing showcase files: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"unexpected showcase files: {', '.join(sorted(extra))}")
    if missing:
        return errors

    html = (showcase / "index.html").read_text(encoding="utf-8")
    app = (showcase / "app.js").read_text(encoding="utf-8")
    css = (showcase / "styles.css").read_text(encoding="utf-8")
    combined = "\n".join((html, app, css))

    if "__PLATFORM_CONNECT_CASE_JSON__" in html:
        errors.append("showcase data token was not replaced")
    if REMOTE_PATTERN.search(combined):
        errors.append("showcase contains a remote URL")
    if re.search(r"\bfetch\s*\(", combined):
        errors.append("showcase must not call fetch()")
    if "Platform Connect" not in html:
        errors.append("showcase title is missing")
    if "repeat(7" not in css:
        errors.append("seven-step layout contract is missing")

    parser = CaseDataParser()
    parser.feed(html)
    try:
        case = json.loads(parser.case_data)
    except json.JSONDecodeError as error:
        errors.append(f"embedded case data is invalid JSON: {error}")
        case = {}
    manifest = case.get("manifest", {}) if isinstance(case, dict) else {}
    for field in ("run_id", "mode", "schema_version"):
        if not manifest.get(field):
            errors.append(f"embedded manifest missing {field}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("showcase", type=Path)
    args = parser.parse_args()
    errors = validate(args.showcase)
    print(
        json.dumps(
            {
                "status": "failed" if errors else "passed",
                "showcase": str(args.showcase.resolve()),
                "errors": errors,
            },
            ensure_ascii=False,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
