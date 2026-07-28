#!/usr/bin/env python3
"""Create a minimal Platform Connect file delivery from final platform Markdown."""

from __future__ import annotations

import argparse
from datetime import datetime
import html
import json
from pathlib import Path
import re
import sys


REQUIRED_SECTIONS = ("发布文案", "配图提示词", "交付说明")
INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
HEADING = re.compile(r"^(#{1,2})\s+(.+?)\s*$")


class DeliveryError(ValueError):
    """Raised when the requested delivery cannot be built safely."""


def safe_name(value: str, fallback: str) -> str:
    cleaned = INVALID_FILENAME.sub("-", value).strip().rstrip(".")
    cleaned = re.sub(r"\s+", " ", cleaned)
    if cleaned in {"", ".", ".."}:
        cleaned = fallback
    return cleaned[:80]


def parse_platform_file(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise DeliveryError(f"platform file does not exist: {path}")

    text = path.read_text(encoding="utf-8")
    platform = ""
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for line in text.splitlines():
        match = HEADING.match(line)
        if match and match.group(1) == "#":
            if not platform:
                platform = match.group(2).strip()
            continue
        if match and match.group(1) == "##":
            current = match.group(2).strip()
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)

    if not platform:
        raise DeliveryError(f"{path.name}: missing '# <平台>' heading")

    missing = [name for name in REQUIRED_SECTIONS if name not in sections]
    if missing:
        raise DeliveryError(
            f"{path.name}: missing required sections: {', '.join(missing)}"
        )

    normalized: dict[str, str] = {}
    for name in REQUIRED_SECTIONS:
        value = "\n".join(sections[name]).strip()
        if not value:
            raise DeliveryError(f"{path.name}: section '{name}' is empty")
        normalized[name] = value

    canonical = "\n".join(
        [
            f"# {platform}",
            "",
            "## 发布文案",
            "",
            normalized["发布文案"],
            "",
            "## 配图提示词",
            "",
            normalized["配图提示词"],
            "",
            "## 交付说明",
            "",
            normalized["交付说明"],
            "",
        ]
    )
    return {
        "platform": platform,
        "sections": normalized,
        "canonical": canonical,
        "source": path.resolve(),
    }


def render_inline(value: str) -> str:
    escaped = html.escape(value, quote=False)
    escaped = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*\n]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def render_markdown(value: str) -> str:
    lines = value.splitlines()
    output: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    list_type: str | None = None
    code_lines: list[str] = []
    in_code = False

    def flush_paragraph() -> None:
        if paragraph:
            text = "<br>".join(render_inline(line) for line in paragraph)
            output.append(f"<p>{text}</p>")
            paragraph.clear()

    def flush_list() -> None:
        nonlocal list_type
        if list_items and list_type:
            items = "".join(f"<li>{render_inline(item)}</li>" for item in list_items)
            output.append(f"<{list_type}>{items}</{list_type}>")
            list_items.clear()
            list_type = None

    for line in lines:
        if line.strip().startswith("```"):
            flush_paragraph()
            flush_list()
            if in_code:
                output.append(
                    f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>"
                )
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue

        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        bullet = re.match(r"^[-*]\s+(.+)$", stripped)
        numbered = re.match(r"^\d+[.)]\s+(.+)$", stripped)
        if bullet or numbered:
            flush_paragraph()
            next_type = "ul" if bullet else "ol"
            if list_type and list_type != next_type:
                flush_list()
            list_type = next_type
            list_items.append((bullet or numbered).group(1))
            continue

        flush_list()
        if stripped.startswith("> "):
            flush_paragraph()
            output.append(
                f"<blockquote>{render_inline(stripped[2:])}</blockquote>"
            )
        else:
            paragraph.append(stripped)

    if in_code:
        output.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
    flush_paragraph()
    flush_list()
    return "\n".join(output)


def platform_article(item: dict[str, object], index: int, folder_name: str) -> str:
    platform = str(item["platform"])
    sections = item["sections"]
    assert isinstance(sections, dict)
    copy_text = str(sections["发布文案"])
    prompt_text = str(sections["配图提示词"])
    notes_text = str(sections["交付说明"])
    file_name = f"{safe_name(platform, f'platform-{index + 1}')}.md"
    href = f"{folder_name}/{file_name}"

    return f"""
    <article class="platform-card" id="platform-{index + 1}">
      <header class="platform-head">
        <div>
          <p class="eyebrow">PLATFORM RESULT</p>
          <h2>{html.escape(platform)}</h2>
        </div>
        <a class="file-link" href="{html.escape(href, quote=True)}" download>下载 Markdown</a>
      </header>
      <section class="result-block copy-block">
        <div class="block-head">
          <h3>发布文案</h3>
          <button type="button" data-copy="copy-{index}">复制文案</button>
        </div>
        <div class="prose">{render_markdown(copy_text)}</div>
        <textarea id="copy-{index}" class="copy-source" aria-hidden="true">{html.escape(copy_text)}</textarea>
      </section>
      <section class="result-block prompt-block">
        <div class="block-head">
          <h3>配图提示词</h3>
          <button type="button" data-copy="prompt-{index}">复制提示词</button>
        </div>
        <div class="prompt-text">{render_markdown(prompt_text)}</div>
        <textarea id="prompt-{index}" class="copy-source" aria-hidden="true">{html.escape(prompt_text)}</textarea>
      </section>
      <footer class="delivery-note">
        <strong>交付说明</strong>
        <div>{render_markdown(notes_text)}</div>
      </footer>
    </article>
    """


def build_html(
    title: str,
    items: list[dict[str, object]],
    folder_name: str,
) -> str:
    navigation = "".join(
        f'<a href="#platform-{index + 1}">{html.escape(str(item["platform"]))}</a>'
        for index, item in enumerate(items)
    )
    articles = "".join(
        platform_article(item, index, folder_name)
        for index, item in enumerate(items)
    )
    created = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")

    document = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>__TITLE__ · Platform Connect</title>
  <style>
    :root {
      --forest: #20332a;
      --green: #506b5c;
      --mist: #dfe4df;
      --paper: #f5f4ef;
      --white: #fbfaf6;
      --brown: #8c684f;
      --ink: #1d2a23;
      --muted: #667169;
      --line: #c8cec8;
      --display: "Songti SC", "STSong", "Noto Serif CJK SC", serif;
      --reading: "Segoe UI Variable Text", "Aptos", "PingFang SC", "Microsoft YaHei UI", sans-serif;
      --mono: "SFMono-Regular", Consolas, monospace;
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      color: var(--ink);
      background:
        linear-gradient(90deg, rgba(80,107,92,.05) 1px, transparent 1px) 0 0 / 48px 48px,
        var(--paper);
      font-family: var(--reading);
      -webkit-font-smoothing: antialiased;
    }
    a { color: inherit; }
    button, a { -webkit-tap-highlight-color: transparent; }
    .topbar {
      position: sticky;
      top: 0;
      z-index: 5;
      display: flex;
      align-items: center;
      justify-content: space-between;
      min-height: 58px;
      padding: 0 5vw;
      color: var(--white);
      background: rgba(32,51,42,.96);
      border-bottom: 1px solid #344a3e;
      backdrop-filter: blur(12px);
    }
    .brand { font-weight: 750; letter-spacing: -.02em; }
    .brand small {
      display: block;
      margin-top: 2px;
      color: #aebbb3;
      font: 9px/1.2 var(--mono);
      letter-spacing: .16em;
    }
    .status { color: #cbd4ce; font: 10px/1 var(--mono); letter-spacing: .12em; }
    .status::before {
      content: "";
      display: inline-block;
      width: 7px;
      height: 7px;
      margin-right: 8px;
      border-radius: 50%;
      background: #90aa98;
      box-shadow: 0 0 0 4px rgba(144,170,152,.12);
    }
    main { width: min(1080px, calc(100% - 40px)); margin: 0 auto; padding: 62px 0 80px; }
    .hero {
      display: grid;
      grid-template-columns: minmax(0, 1.4fr) minmax(260px, .6fr);
      gap: 48px;
      align-items: end;
      padding-bottom: 42px;
      border-bottom: 1px solid var(--line);
    }
    .eyebrow {
      margin: 0 0 12px;
      color: var(--brown);
      font: 10px/1.2 var(--mono);
      letter-spacing: .17em;
    }
    h1 {
      max-width: 760px;
      margin: 0;
      font: 700 clamp(42px, 7vw, 78px)/.98 var(--display);
      letter-spacing: -.06em;
    }
    h1 em { color: var(--green); font-style: normal; }
    .hero-summary {
      padding-left: 24px;
      border-left: 2px solid var(--brown);
      color: var(--muted);
      font-size: 14px;
      line-height: 1.8;
    }
    .hero-summary strong { color: var(--ink); font-size: 18px; }
    .platform-nav {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      padding: 22px 0 6px;
    }
    .platform-nav a {
      padding: 9px 14px;
      text-decoration: none;
      background: var(--white);
      border: 1px solid var(--line);
      font-size: 12px;
      font-weight: 700;
    }
    .platform-nav a:hover, .platform-nav a:focus-visible {
      color: var(--white);
      background: var(--forest);
      outline: none;
    }
    .platform-card {
      margin-top: 42px;
      background: var(--white);
      border: 1px solid #b8c0ba;
      box-shadow: 0 20px 50px rgba(36,52,44,.08);
      scroll-margin-top: 84px;
    }
    .platform-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 24px;
      padding: 28px 32px;
      color: var(--white);
      background: var(--forest);
    }
    .platform-head .eyebrow { color: #b9c8bf; }
    .platform-head h2 { margin: 0; font: 700 34px/1 var(--display); }
    .file-link {
      padding: 10px 14px;
      color: var(--white);
      border: 1px solid #72877a;
      text-decoration: none;
      font-size: 12px;
      font-weight: 700;
    }
    .result-block { padding: 30px 32px; border-bottom: 1px solid var(--line); }
    .block-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      margin-bottom: 22px;
    }
    .block-head h3 { margin: 0; font: 700 24px/1.2 var(--display); }
    button {
      padding: 9px 13px;
      color: var(--forest);
      background: transparent;
      border: 1px solid #96a39b;
      font: 700 11px/1 var(--reading);
      cursor: pointer;
    }
    button:hover, button:focus-visible { color: var(--white); background: var(--brown); border-color: var(--brown); outline: none; }
    .prose, .prompt-text { max-width: 780px; font-size: 15px; line-height: 1.85; }
    .prose p:first-child, .prompt-text p:first-child { margin-top: 0; }
    .prose p:last-child, .prompt-text p:last-child { margin-bottom: 0; }
    .prose li, .prompt-text li { margin: 7px 0; }
    code { padding: 2px 5px; background: #e7ebe7; font-family: var(--mono); font-size: .9em; }
    pre { overflow: auto; padding: 16px; color: #e5ebe7; background: #17271f; }
    pre code { padding: 0; background: transparent; }
    blockquote { margin: 18px 0; padding-left: 18px; color: var(--muted); border-left: 2px solid var(--brown); }
    .prompt-block { background: #edf0ec; }
    .prompt-text {
      padding: 20px;
      color: #e9efeb;
      background: var(--forest);
      font-size: 13px;
      line-height: 1.8;
    }
    .prompt-text code { color: #fff; background: #3b5145; }
    .delivery-note {
      display: grid;
      grid-template-columns: 140px 1fr;
      gap: 24px;
      padding: 22px 32px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.7;
    }
    .delivery-note strong { color: var(--ink); }
    .delivery-note p { margin: 0; }
    .page-foot {
      display: flex;
      justify-content: space-between;
      gap: 20px;
      margin-top: 30px;
      padding-top: 20px;
      color: var(--muted);
      border-top: 1px solid var(--line);
      font: 10px/1.5 var(--mono);
    }
    .copy-source { position: fixed; left: -9999px; width: 1px; height: 1px; opacity: 0; }
    @media (max-width: 760px) {
      main { width: min(100% - 24px, 1080px); padding-top: 38px; }
      .hero { grid-template-columns: 1fr; gap: 26px; }
      .hero-summary { padding-left: 16px; }
      .platform-head, .block-head, .page-foot { align-items: flex-start; flex-direction: column; }
      .platform-head, .result-block, .delivery-note { padding-left: 20px; padding-right: 20px; }
      .delivery-note { grid-template-columns: 1fr; gap: 8px; }
    }
    @media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="brand">Platform Connect<small>FINAL DELIVERY</small></div>
    <div class="status">READY</div>
  </header>
  <main>
    <section class="hero">
      <div>
        <p class="eyebrow">PLATFORM-NATIVE RESULTS</p>
        <h1>从一份表达，<br><em>到多种抵达</em></h1>
      </div>
      <div class="hero-summary">
        <strong>__TITLE__</strong><br>
        已整理 __COUNT__ 个平台成果。文案、配图提示词与交付说明已归入各平台文件。
      </div>
    </section>
    <nav class="platform-nav" aria-label="平台成果">__NAV__</nav>
    __ARTICLES__
    <footer class="page-foot">
      <span>__CREATED__ · PLATFORM CONNECT</span>
      <span>__FOLDER__ · __COUNT__ FILES</span>
    </footer>
  </main>
  <script>
    document.querySelectorAll("[data-copy]").forEach((button) => {
      button.addEventListener("click", async () => {
        const source = document.getElementById(button.dataset.copy);
        const value = source ? source.value : "";
        try {
          await navigator.clipboard.writeText(value);
        } catch {
          source.focus();
          source.select();
          document.execCommand("copy");
        }
        const previous = button.textContent;
        button.textContent = "已复制";
        window.setTimeout(() => { button.textContent = previous; }, 1400);
      });
    });
  </script>
</body>
</html>
"""
    return (
        document.replace("__TITLE__", html.escape(title))
        .replace("__COUNT__", str(len(items)))
        .replace("__NAV__", navigation)
        .replace("__ARTICLES__", articles)
        .replace("__CREATED__", created)
        .replace("__FOLDER__", html.escape(folder_name))
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build one self-contained HTML page and one platform-result folder."
    )
    parser.add_argument("platform_files", nargs="+", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    parser.add_argument("--run-id")
    parser.add_argument("--folder")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        items = [parse_platform_file(path.resolve()) for path in args.platform_files]
        platforms = [str(item["platform"]).casefold() for item in items]
        if len(platforms) != len(set(platforms)):
            raise DeliveryError("duplicate platform headings are not allowed")

        run_id = safe_name(
            args.run_id or datetime.now().astimezone().strftime("%Y%m%d-%H%M%S"),
            "delivery",
        )
        folder_name = safe_name(args.folder or args.title, "platform-results")
        run_root = args.output_root.resolve() / run_id
        result_dir = run_root / folder_name
        if run_root.exists():
            raise DeliveryError(f"run directory already exists: {run_root}")

        result_dir.mkdir(parents=True)
        files: list[Path] = []
        used_names: set[str] = set()
        for index, item in enumerate(items):
            platform = str(item["platform"])
            file_name = f"{safe_name(platform, f'platform-{index + 1}')}.md"
            key = file_name.casefold()
            if key in used_names:
                raise DeliveryError(f"platform file name collision: {file_name}")
            used_names.add(key)
            destination = result_dir / file_name
            destination.write_text(str(item["canonical"]), encoding="utf-8")
            files.append(destination)

        showcase = run_root / "showcase.html"
        showcase.write_text(
            build_html(args.title, items, folder_name),
            encoding="utf-8",
        )

        expected = {showcase.resolve(), *(path.resolve() for path in files)}
        actual = {path.resolve() for path in run_root.rglob("*") if path.is_file()}
        if actual != expected:
            raise DeliveryError("delivery contains unexpected or missing files")

        payload = {
            "status": "completed",
            "run_root": str(run_root),
            "showcase": str(showcase),
            "results_folder": str(result_dir),
            "platform_files": [str(path) for path in files],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except (DeliveryError, OSError, UnicodeError) as error:
        print(
            json.dumps(
                {"status": "failed", "error": str(error)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
