# Platform Connect

<p align="center">
  <strong>把一篇文章，变成面向不同平台的完整图文交付。</strong>
</p>

<p align="center">
  面向 Agent Skills 生态的开源内容工作流：直接读取正文、文档或文章链接，
  建立共享事实基线，生成平台原生文案、经确认的视觉资产与结果型离线看板。
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> ·
  <a href="#交付结果">交付结果</a> ·
  <a href="#工作原理">工作原理</a> ·
  <a href="#开发与测试">开发与测试</a>
</p>

## 为什么选择 Platform Connect

Platform Connect 不是 React/FastAPI AI 应用，也不是把同一段文案换标题后批量分发。它是一套
可安装的 Agent Skill：Agent 负责理解原文、适配平台、协作决策与调用图像工具；仓库脚本负责
可重复的目录创建、Manifest 校验、交付索引和静态页面渲染。

| 能力 | 说明 |
| --- | --- |
| 直接读取常见来源 | 支持粘贴正文、TXT、Markdown、Word、PDF、HTML 文件和文章链接 |
| 事实基线 | 先建立共享内容简报，平台文案和视觉资产都从同一事实来源派生 |
| 平台推荐 | 未指定目标时推荐 2–3 个适合的平台，并兼顾国内外发布场景 |
| 原生文案适配 | 针对平台调整开场、节奏、结构与 CTA，不改变原文事实 |
| 可控视觉生成 | 配图必须经过明确授权，并记录方向、用途、比例、来源和 QA 状态 |
| 结果型离线看板 | 最终文案与真实图片集中展示，可通过 `file://` 打开，不依赖服务器或 CDN |

## 交付结果

### 同一事实，不同表达

每个平台获得独立的内容结构，而不是同一份文案的机械复制。小红书可以强调共鸣与收藏价值，
LinkedIn 可以保留专业判断与讨论空间，其他平台则遵循各自的内容节奏和交互习惯。

### 图文资产集中交付

最终看板优先展示已经确认的平台文案和实际图片。来源简报、推荐依据、审批记录与 QA 信息仍然
保留，但默认折叠，不干扰用户查看最终成果。

### 一次运行，一个可追溯目录

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

每次修改创建新的 `run_id`；`parent_run_id` 指向上一次运行，避免覆盖已经确认的交付结果。

## 快速开始

### 1. 安装最新正式版

当前最新正式版为 `v1.2.0`。默认安装到当前项目：

```powershell
npx skills add halexzd686-cloud/Platform-Connect@v1.2.0 `
  --agent codex `
  --skill platform-connect `
  --yes `
  --copy
```

项目级安装是默认选择。只有明确需要在多个项目间复用时，才增加 `--global` 安装到当前用户。

### 2. 交给 Agent

在 Codex、Claude Code 或其他兼容 Agent 中调用 `$platform-connect`，直接发送文章正文、文件或链接：

> 使用 $platform-connect 处理这篇文章。如果我没有指定平台，请推荐 2–3 个国内外平台和配图方向，再让我一次完成选择。

不需要先编写复杂提示词。目标平台未指定时，Agent 只返回决策所需的推荐，不会提前为全部候选
平台生成完整文案。

### 3. 一次确认关键选择

默认 `compact` 流程把平台、是否配图和完成方式合并确认；随后再用一次联合审阅处理文案、视觉
方向和资产清单。用户也可以明确使用 `autopilot`：

> 使用 $platform-connect 的 full + autopilot。发布到小红书和 LinkedIn，需要配图，无需中途确认，直接完成最终交付。

图片生成始终需要明确授权，不能由 Agent 推断。

### 4. 打开交付看板

运行完成后，直接打开：

```text
outputs/<article-slug>/<run-id>/showcase/index.html
```

看板是最终成果的可视化总结，不承担与 Agent 对话或替代 Agent 决策的职责。

## 工作原理

```mermaid
flowchart LR
    A["正文 / 文件 / 链接"] --> B["完整读取来源"]
    B --> C["建立事实简报"]
    C --> D["推荐或确认平台"]
    D --> E["生成平台原生文案"]
    E --> F["联合确认图文方案"]
    F --> G["生成图片并 QA"]
    G --> H["渲染结果型离线看板"]
```

| 阶段 | 脚本 / 产物 | 责任 |
| --- | --- | --- |
| 运行初始化 | `prepare_workspace.py` | 创建独立运行目录和初始 Manifest |
| 来源简报 | Agent + `source-brief.md` | 固定核心观点、事实、受众与不可漂移内容 |
| 平台适配 | Agent + `<platform>/copy.md` | 生成平台原生文案并保留事实一致性 |
| 视觉交付 | 图像工具 + `<platform>/images/` | 按已批准清单生成图片并记录 QA |
| 页面渲染 | `render_showcase.py` | 生成离线看板三件套 |
| 完整性校验 | `validate_manifest.py`、`validate_showcase.py` | 检查状态、资产、数据和离线约束 |
| 交付索引 | `build_delivery_index.py` | 汇总运行结果与文件入口 |

## 审阅策略

| 策略 | 适用场景 | 交互方式 |
| --- | --- | --- |
| `compact` | 默认使用 | 合并关键选择，减少往返确认 |
| `strict` | 高风险内容或用户要求逐步控制 | 分阶段确认文案、视觉方向与资产清单 |
| `autopilot` | 用户明确要求直接完成 | 按预授权执行；生图仍必须有明确授权 |

输出范围与审阅策略相互独立：

- `plan`：只生成内容简报、适配策略和视觉计划。
- `copy`：生成内容简报与平台文案，不进入生图流程。
- `full`：完成文案、视觉资产、Manifest、QA 和离线看板。

高频用户可以在工作目录创建 `platform-connect.profile.json`，保存默认平台、语言、市场、图片意图
和审阅策略；当前请求始终优先于配置。

## 设计原则

- **原文是事实来源**：不因平台适配改写事实或引入未经支持的结论。
- **先理解，后分发**：所有平台内容都从共享内容简报派生。
- **推荐而不代替决定**：未指定平台时只推荐两个、最多三个，并解释适配理由。
- **减少对话往返**：默认合并可安全合并的确认，高风险歧义才拆分处理。
- **生图必须授权**：图片意图、视觉方向与资产清单均需有明确授权来源。
- **结果优先展示**：最终看板先呈现文案和真实图片，过程记录默认折叠。
- **唯一源码**：仓库只维护 `skills/platform-connect`，不直接修补安装副本或生成后的页面。
- **离线交付**：展示页不发起远程请求，也不要求用户安装前端运行环境。

## 项目结构

```text
Platform-Connect/
├── skills/
│   └── platform-connect/
│       ├── SKILL.md
│       ├── agents/
│       ├── assets/
│       ├── references/
│       └── scripts/
├── designs/
├── tests/
└── skills-lock.json
```

- `skills/platform-connect/` 是 GitHub 仓库中的唯一 Skill 源码。
- `.agents/skills/platform-connect/` 是项目级安装副本，可删除、可重装，不提交 Git。
- `skills-lock.json` 记录安装来源和内容哈希，用于依赖核对与恢复。

不要直接修改安装副本。发现问题时修改唯一源码、运行测试并重新安装，也不要修补 `.claude/`
或生成后的看板。

## 更新与回退

### 升级到当前正式版

重复执行带明确版本标签的安装命令，可以把项目级副本覆盖为当前正式版：

```powershell
npx skills add halexzd686-cloud/Platform-Connect@v1.2.0 `
  --agent codex `
  --skill platform-connect `
  --yes `
  --copy
```

### 跟随最新开发内容

```powershell
npx skills update platform-connect --project --yes
```

此命令适合希望跟随仓库最新内容的测试或开发场景。普通用户应优先安装带版本标签的正式版。

### 回退到上一稳定版

```powershell
npx skills add halexzd686-cloud/Platform-Connect@v1.1.0 `
  --agent codex `
  --skill platform-connect `
  --yes `
  --copy
```

回退前保留失败运行目录，定位最后一个通过测试的 Git tag 或提交；修复完成后重新运行测试，再从
已确认的 GitHub 版本安装。

## 开发与测试

运行完整回归测试：

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
node --test tests/test_showcase_runtime.mjs
```

运行官方 Skill 校验：

```powershell
python -X utf8 C:\Users\86188\.codex\skills\.system\skill-creator\scripts\quick_validate.py `
  skills/platform-connect
```

## 运行要求

- Python 3.10+
- Node.js 20+（仅开发和前端回归测试需要）
- 支持 Agent Skills 的 Agent 运行环境

## 参与贡献

欢迎提交问题报告与改进建议。若修改交互流程、Manifest Schema、确定性脚本或离线看板模板，请
同时补充对应回归测试，并确保生成结果仍可通过 `file://` 直接运行。

## License

本项目采用 [MIT License](LICENSE)。第三方来源与署名要求见
`skills/platform-connect/references/third-party-notices.md`。
