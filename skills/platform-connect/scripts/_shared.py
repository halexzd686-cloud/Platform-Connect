"""Shared constants and JSON result helpers for Platform Connect scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.4"
SKILL_VERSION = "1.4.1"
PLATFORMS = frozenset(
    {
        "douyin",
        "xiaohongshu",
        "wechat-channels",
        "bilibili",
        "kuaishou",
        "tiktok",
        "youtube-shorts",
        "youtube-long",
        "instagram-reels",
        "facebook-reels",
        "linkedin",
        "x",
        "threads",
        "pinterest",
        "snapchat-spotlight",
    }
)


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def fail(error: Exception | str, **fields: Any) -> int:
    payload: dict[str, Any] = {
        "status": "failed",
        "errors": [str(error)],
    }
    payload.update(fields)
    emit(payload)
    return 1


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} root must be an object")
    return payload
