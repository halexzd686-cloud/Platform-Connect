import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";


const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const templateRoot = path.join(
  repoRoot,
  "skills",
  "platform-connect",
  "assets",
  "static-showcase",
);
const html = fs.readFileSync(path.join(templateRoot, "index.html"), "utf8");
const app = fs.readFileSync(path.join(templateRoot, "app.js"), "utf8");
const styles = fs.readFileSync(path.join(templateRoot, "styles.css"), "utf8");


test("template stays offline and data-driven", () => {
  const combined = `${html}\n${app}\n${styles}`;
  assert.match(html, /__PLATFORM_CONNECT_CASE_JSON__/);
  assert.doesNotMatch(combined, /https?:\/\//i);
  assert.doesNotMatch(combined, /\bfetch\s*\(/);
  assert.match(app, /document\.getElementById\("case-data"\)/);
});


test("runtime is outcome-first and renders delivered content", () => {
  for (const label of [
    "从一份表达，",
    "各平台最终文案",
    "配图建议与提示词",
    "下载本次成果",
  ]) {
    assert.match(html, new RegExp(label));
  }
  assert.match(html, /到多种抵达/);
  assert.doesNotMatch(html, /这组内容从哪里来/);
  assert.match(app, /data-platform-tab/);
  assert.match(app, /visual_prompts/);
  assert.match(app, /data-copy-prompt/);
  assert.doesNotMatch(html, /outcome-index/);
  assert.doesNotMatch(app, /<img/);
  assert.doesNotMatch(app, /assetUrl/);
  assert.match(styles, /\.package-shell/);
  assert.match(styles, /\.prompt-gallery/);
});

test("showcase is a read-only delivery board with collapsed provenance", () => {
  assert.match(html, /OFFLINE REPORT/);
  assert.match(html, /查看来源与执行记录/);
  assert.match(app, /review_policy/);
  assert.match(app, /decision_provenance/);
  assert.match(app, /platform_recommendations/);
  assert.match(html, /切换平台只改变当前查看的定稿/);
  assert.match(app, /downloadPrimary/);
  assert.doesNotMatch(app, /classList\.toggle\("selected"\)/);
  assert.doesNotMatch(html, /选择平台|确认生成|开始生成/);
  assert.doesNotMatch(app, /generation_status|view_image|lightbox/);
});


test("visual language uses the green gray brown system", () => {
  assert.match(styles, /--forest:/);
  assert.match(styles, /--paper:/);
  assert.match(styles, /--brown:/);
  assert.match(styles, /--reading:/);
  assert.match(styles, /\.prompt-card summary/);
  assert.match(styles, /\.download-primary/);
});
