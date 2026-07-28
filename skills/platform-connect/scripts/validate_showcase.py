#!/usr/bin/env python3
"""Validate a rendered offline Platform Connect showcase."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import zipfile

from _shared import emit, fail


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
    for marker in (
        "summary-strip",
        "package-shell",
        "prompt-gallery",
        "delivery-board",
        "trace-toggle",
    ):
        if marker not in combined:
            errors.append(f"outcome-first showcase marker is missing: {marker}")
    if "visual_prompts" not in app:
        errors.append("showcase runtime must render visual prompt packages")
    if "<img" in app:
        errors.append("showcase runtime must not render generated images")
    if "data-platform-tab" not in app:
        errors.append("showcase runtime must expose platform result switching")

    parser = CaseDataParser()
    parser.feed(html)
    try:
        case = json.loads(parser.case_data)
    except json.JSONDecodeError as error:
        errors.append(f"embedded case data is invalid JSON: {error}")
        case = {}
    manifest = case.get("manifest", {}) if isinstance(case, dict) else {}
    for field in ("run_id", "mode", "review_policy", "schema_version"):
        if not manifest.get(field):
            errors.append(f"embedded manifest missing {field}")
    source = case.get("source", {}) if isinstance(case, dict) else {}
    if source.get("read_status") != "complete":
        errors.append("embedded source must record complete intake")

    downloads = case.get("downloads", {}) if isinstance(case, dict) else {}
    bundle = downloads.get("bundle", {}) if isinstance(downloads, dict) else {}
    download_files = downloads.get("files", []) if isinstance(downloads, dict) else []
    declared = [bundle, *download_files]
    delivery_root = showcase.parent.resolve()
    for item in declared:
        relative = item.get("path") if isinstance(item, dict) else None
        if not relative:
            errors.append("embedded download entry is missing path")
            continue
        target = (delivery_root / relative).resolve()
        try:
            target.relative_to(delivery_root)
        except ValueError:
            errors.append(f"download path escapes delivery root: {relative}")
            continue
        if not target.is_file():
            errors.append(f"download file is missing: {relative}")

    bundle_path = bundle.get("path") if isinstance(bundle, dict) else None
    if bundle_path:
        archive_path = (delivery_root / bundle_path).resolve()
        if archive_path.is_file():
            try:
                with zipfile.ZipFile(archive_path) as archive:
                    archive_names = set(archive.namelist())
                    expected_names = {
                        Path(item["path"]).name
                        for item in download_files
                        if isinstance(item, dict) and item.get("path")
                    }
                    if archive.testzip() is not None:
                        errors.append("download bundle contains a corrupt member")
                    if archive_names != expected_names:
                        errors.append("download bundle contents do not match declared files")
            except zipfile.BadZipFile:
                errors.append("download bundle is not a valid ZIP archive")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("showcase", type=Path)
    args = parser.parse_args()
    try:
        errors = validate(args.showcase)
    except OSError as error:
        return fail(error, showcase=str(args.showcase.resolve()))
    emit(
        {
            "status": "failed" if errors else "passed",
            "showcase": str(args.showcase.resolve()),
            "errors": errors,
        }
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
