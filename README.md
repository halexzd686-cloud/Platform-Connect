# adapt-content-for-platforms

一个面向中文内容创作者的 Codex Skill：读取一篇原始文章，先让用户选择目标平台，再生成共享内容母版、平台原生文案、行业化视觉方向、可编辑配图清单和最终图片。

Skill 目录：[`skills/adapt-content-for-platforms`](skills/adapt-content-for-platforms)

核心交互门槛：

1. 用户未指定平台时先询问，不默认全平台；
2. 文案草稿必须经用户确认；
3. 文案确认后才推荐视觉方向；
4. 配图清单再次确认后才逐张生图。

校验：

```powershell
python C:\Users\86188\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\adapt-content-for-platforms
python skills\adapt-content-for-platforms\scripts\prepare_workspace.py demo --platforms douyin bilibili
python skills\adapt-content-for-platforms\scripts\validate_manifest.py outputs\demo\manifest.json
python skills\adapt-content-for-platforms\scripts\build_delivery_index.py outputs\demo\manifest.json
```

