# Platform Connect

Platform Connect 是一个可安装的 Agent Skill：读取用户提供的完整文章，建立共享事实基线，再为明确选择的平台生成独立文案、视觉方向、可编辑资产清单、确认后的图片和离线执行展示页。

它不是 React/FastAPI AI 应用。Agent 负责理解、写作、决策协作与图像工具调用；仓库中的脚本只负责确定性的目录创建、Manifest 校验、交付索引和静态页面渲染。

## 快速安装

默认安装到当前项目：

```powershell
npx skills add halexzd686-cloud/Platform-Connect `
  --agent codex `
  --skill platform-connect `
  --yes
```

安装到当前用户、供多个项目使用时，显式增加 `--global`：

```powershell
npx skills add halexzd686-cloud/Platform-Connect `
  --agent codex `
  --skill platform-connect `
  --global `
  --yes
```

安装完成后，在新的 Agent 会话中使用 `$platform-connect`，并提供完整文章、目标平台及需要的运行模式。项目级安装是默认选择；只有明确需要跨项目复用时才使用用户级安装。

## 核心流程

```text
完整读取原文
  → 共享内容简报
  → 平台与语言市场
  → 独立平台文案
  → 文案确认
  → 明确选择是否配图
  → 视觉方向确认
  → 资产清单确认
  → 逐张生成与 QA
  → 离线展示页和交付索引
```

四个决策保持独立：

1. 文案审批；
2. 配图意图；
3. 视觉方向审批；
4. 视觉资产清单审批。

未批准视觉资产清单时，Skill 不得生成图片。

## Skill 目录

正式源码只有一份：

```text
skills/platform-connect/
├── SKILL.md
├── agents/openai.yaml
├── references/
├── scripts/
└── assets/static-showcase/
```

`.agents/` 和 `.claude/` 是安装目标，不作为仓库源码维护。

三类目录承担不同职责：

- `skills/platform-connect/`：GitHub 仓库中的唯一源码，所有修复从这里开始。
- `.agents/skills/platform-connect/` 或 Agent 对应目录：项目级安装副本，可删除、可重装，不提交 Git。
- `skills-lock.json`：项目级安装来源与内容哈希，可提交 Git，用于依赖核对和恢复。
- 用户级 Skill 目录：跨项目安装副本，不属于本仓库。

不要直接修改安装副本。需要修复时修改唯一源码、运行测试并重新安装。

## 运行模式

- `plan`：内容简报、适配策略、视觉方向和拟议资产，不生成最终文案或图片。
- `copy`：内容简报和平台文案；文案确认后必须询问是否生成配图。
- `full`：执行文案、视觉规划、Manifest、图片生成和 QA，但不跳过任何审批门。

## 确定性脚本

```powershell
python skills/platform-connect/scripts/prepare_workspace.py demo `
  --platforms xiaohongshu linkedin `
  --run-id 20260726-143500 `
  --target-language en `
  --market global

python skills/platform-connect/scripts/validate_manifest.py `
  outputs/demo/20260726-143500/manifest.json

python skills/platform-connect/scripts/render_showcase.py `
  outputs/demo/20260726-143500/manifest.json

python skills/platform-connect/scripts/validate_showcase.py `
  outputs/demo/20260726-143500/showcase

python skills/platform-connect/scripts/build_delivery_index.py `
  outputs/demo/20260726-143500/manifest.json
```

所有脚本都使用显式路径、向 stdout 输出 JSON，并在失败时返回非零退出码。

## 输出结构

```text
outputs/<article-slug>/<run-id>/
├── source-brief.md
├── manifest.json
├── index.md
├── showcase/
│   ├── index.html
│   ├── app.js
│   └── styles.css
└── <platform>/
    ├── copy.md
    └── images/
```

每次修改创建新的 `run_id`；`parent_run_id` 指向上一次运行，避免覆盖已经确认的结果。

## 开发与测试

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
node --test tests/test_showcase_runtime.mjs
```

官方 Skill 校验：

```powershell
python -X utf8 C:\Users\86188\.codex\skills\.system\skill-creator\scripts\quick_validate.py `
  skills/platform-connect
```

运行要求：

- Python 3.10+
- Node.js 20+（仅用于仓库级页面回归测试）
- 支持 Agent Skills 的 Agent 环境

## 更新与回退

更新当前项目中的安装副本：

```powershell
npx skills update platform-connect --project --yes
```

重新安装一个已经发布的明确版本：

```powershell
npx skills add halexzd686-cloud/Platform-Connect@v1.0.0 `
  --agent codex `
  --skill platform-connect `
  --yes `
  --copy
```

执行或升级出现问题时：

1. 保留失败运行的 `outputs/<article-slug>/<run-id>/`，不要覆盖已确认产物。
2. 在仓库中定位最后一个通过测试的 Git tag 或 commit。
3. 修复 `skills/platform-connect/` 下的源码，不直接修补 `.agents/`、`.claude/` 或生成后的展示页。
4. 重新运行仓库测试与官方 Skill 校验。
5. 删除或更新项目级安装副本，再从已确认的 GitHub 版本重新安装。

发布版本、Git tag 和安装副本应保持一一对应，便于确认当前项目实际运行的是哪一版 Skill。

## 设计原则

- 原文始终是事实来源。
- 不默认选择所有平台。
- 平台适配改变开场、节奏、结构与 CTA，不改变事实。
- 海外平台明确记录目标语言和市场。
- 自定义提示词与推荐视觉方向地位相同。
- 静态展示页可通过 `file://` 直接打开，无 CDN、无远程请求、无服务器。

## 许可证

本项目采用 [MIT License](LICENSE)。第三方来源与署名要求见 Skill 内的 `references/third-party-notices.md`。
