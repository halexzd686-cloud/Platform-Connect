# Optional file delivery

Use filesystem delivery only when the user asks to save, package, download, or receive an HTML page.

## Platform files

Create one UTF-8 Markdown source file per platform. Each file must contain:

```markdown
# <平台>
## 发布文案
## 配图提示词
## 交付说明
```

Put final copy and the prompt in the same platform file. When prompts were not requested, write `本次未请求配图提示词` under that heading. Put only useful factual, risk, locale, or usage notes under `交付说明`.

## Delivery command

Pass the platform files to:

```text
python scripts/deliver.py <平台文件...> --title "<本次主题>" --output-root outputs
```

Optional arguments:

- `--run-id <value>` chooses the run directory name; the default is a local timestamp.
- `--folder <value>` chooses the result-folder name; the default is the title.

The output contains exactly one self-contained HTML page and one result folder:

```text
<run-id>/
├── showcase.html
└── <本次主题>/
    ├── <平台>.md
    └── <平台>.md
```

The HTML must use inline CSS and JavaScript, work offline, link to each Markdown file, and avoid remote requests. The command validates required headings, duplicate platforms, file existence, and final output presence.
