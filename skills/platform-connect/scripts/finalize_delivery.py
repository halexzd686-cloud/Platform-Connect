#!/usr/bin/env python3
"""Finalize and verify one Platform Connect copy/full delivery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from _shared import emit, fail, load_json_object


def run_stage(script_root: Path, name: str, arguments: list[str]) -> dict:
    command = [sys.executable, str(script_root / name), *arguments]
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    output = result.stdout.strip()
    try:
        payload = json.loads(output) if output else {}
    except json.JSONDecodeError:
        payload = {}
    if result.returncode != 0 or payload.get("status") == "failed":
        details = payload.get("errors") or [result.stderr.strip() or output or "unknown error"]
        raise ValueError(f"{name} failed: {'; '.join(str(item) for item in details)}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--data", type=Path)
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    run_root = manifest_path.parent
    script_root = Path(__file__).resolve().parent
    try:
        manifest = load_json_object(manifest_path)
        if manifest.get("mode") not in {"copy", "full"}:
            raise ValueError("final delivery is only valid for copy or full mode")
        if manifest.get("copy_approval") != "approved":
            raise ValueError("copy approval must be approved before final delivery")
        if manifest.get("mode") == "full":
            if manifest.get("visual_prompt_intent") != "yes":
                raise ValueError("full delivery requires visual_prompt_intent: yes")
            if manifest.get("visual_prompt_approval") != "approved":
                raise ValueError(
                    "visual prompt approval must be approved before final delivery"
                )

        stages = {
            "manifest": run_stage(
                script_root,
                "validate_manifest.py",
                [str(manifest_path)],
            )
        }
        render_arguments = [str(manifest_path)]
        if args.data:
            render_arguments.extend(["--data", str(args.data.resolve())])
        stages["render"] = run_stage(
            script_root,
            "render_showcase.py",
            render_arguments,
        )

        showcase_path = run_root / manifest["showcase_file"]
        stages["showcase"] = run_stage(
            script_root,
            "validate_showcase.py",
            [str(showcase_path.parent)],
        )
        stages["index"] = run_stage(
            script_root,
            "build_delivery_index.py",
            [str(manifest_path)],
        )

        bundle_path = run_root / "downloads" / "Platform-Connect-成果包.zip"
        required = {
            "manifest": manifest_path,
            "index": run_root / "index.md",
            "showcase": showcase_path,
            "bundle": bundle_path,
        }
        missing = [label for label, path in required.items() if not path.is_file()]
        if missing:
            raise ValueError(f"required delivery files are missing: {', '.join(missing)}")
    except (OSError, KeyError, ValueError) as error:
        return fail(error, manifest=str(manifest_path))

    emit(
        {
            "status": "completed",
            "run_root": str(run_root),
            "manifest": str(manifest_path),
            "index": str(required["index"]),
            "showcase": str(required["showcase"]),
            "bundle": str(required["bundle"]),
            "stages": stages,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
