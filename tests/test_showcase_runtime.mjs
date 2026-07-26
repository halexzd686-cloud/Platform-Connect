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


test("runtime exposes all seven skill stages", () => {
  for (const label of [
    "内容简报",
    "平台与语言",
    "文案审阅",
    "配图意图",
    "视觉方向",
    "资产清单",
    "生成交付",
  ]) {
    assert.match(app, new RegExp(label));
  }
  assert.match(styles, /repeat\(7,/);
});

test("showcase is a read-only decision record with review provenance", () => {
  assert.match(html, /OFFLINE REPORT/);
  assert.match(html, /DECISION RECORD/);
  assert.match(app, /review_policy/);
  assert.match(app, /decision_provenance/);
  assert.match(app, /本次适配平台与语言市场/);
  assert.doesNotMatch(app, /classList\.toggle\("selected"\)/);
});


test("visual language uses the green gray brown system", () => {
  assert.match(styles, /--forest:/);
  assert.match(styles, /--paper:/);
  assert.match(styles, /--brown:/);
  assert.match(styles, /\.score\s*\{/);
});
