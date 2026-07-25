(() => {
  "use strict";

  const dataElement = document.getElementById("case-data");
  const data = JSON.parse(dataElement.textContent);
  const $ = id => document.getElementById(id);
  const safe = value => value ?? "未记录";
  const list = value => Array.isArray(value) ? value : [];

  const steps = [
    { key: "brief", label: "内容简报", gate: "确认事实基线与作者立场" },
    { key: "platforms", label: "平台与语言", gate: "确认目标平台、语言和市场" },
    { key: "copies", label: "文案审阅", gate: "确认平台文案是否可用" },
    { key: "intent", label: "配图意图", gate: "明确选择是否生成配图" },
    { key: "directions", label: "视觉方向", gate: "选择全局方向或自定义提示词" },
    { key: "assets", label: "资产清单", gate: "确认每张资产的用途与约束" },
    { key: "delivery", label: "生成交付", gate: "检查生成状态与 QA" },
  ];

  let currentStep = 0;
  let currentCopy = 0;

  function textList(items) {
    if (!items.length) return '<div class="empty">暂无记录</div>';
    return `<ul class="list">${items.map(item => `<li>${item}</li>`).join("")}</ul>`;
  }

  function approval(label, value) {
    return `
      <div class="approval-bar">
        <div><strong>${label}</strong><small>审批决定保持独立，不从其他步骤推断</small></div>
        <span class="status">${safe(value)}</span>
      </div>`;
  }

  function renderBrief() {
    const brief = data.brief || {};
    return `
      <h2>共享内容简报</h2>
      <div class="screen-grid">
        <article class="panel">
          <div class="panel-label">Core thesis</div>
          <p class="thesis">${safe(brief.core_thesis)}</p>
          <div class="fact-grid">
            <div class="fact"><label>作者立场</label><strong>${safe(brief.author_stance)}</strong></div>
            <div class="fact"><label>目标受众</label><strong>${safe(brief.audience)}</strong></div>
            <div class="fact"><label>沟通任务</label><strong>${safe(brief.audience_need)}</strong></div>
            <div class="fact"><label>语气</label><strong>${safe(brief.tone)}</strong></div>
          </div>
        </article>
        <div>
          <article class="panel">
            <div class="panel-label">Protected claims</div>
            ${textList(list(brief.protected_claims))}
          </article>
          <article class="panel" style="margin-top:14px">
            <div class="panel-label">Review flags</div>
            ${textList(list(data.review_flags))}
          </article>
        </div>
      </div>
      ${approval("内容简报", data.decisions?.brief || "approved")}`;
  }

  function renderPlatforms() {
    const locale = data.locale_assumptions || {};
    const cards = list(data.platforms).map(platform => `
      <article class="platform-card">
        <span class="chip">${safe(platform.id || platform)}</span>
        <h3>${safe(platform.label || platform)}</h3>
        <p>${safe(platform.rationale || "从共享内容简报派生独立内容结构。")}</p>
        <div class="asset-meta">
          <span>语言 ${safe(platform.language || locale.target_language || locale.source_language)}</span>
          <span>市场 ${safe(platform.market || locale.market || "source")}</span>
        </div>
      </article>`).join("");
    return `
      <h2>平台与语言市场</h2>
      <div class="card-grid">${cards || '<div class="empty">尚未选择平台</div>'}</div>
      ${approval("平台选择", data.decisions?.platforms || "approved")}`;
  }

  function renderCopies() {
    const copies = list(data.copies);
    if (!copies.length) return `<h2>平台文案</h2><div class="empty">当前运行未包含最终文案。</div>`;
    currentCopy = Math.min(currentCopy, copies.length - 1);
    return `
      <h2>独立的 Copy Packages</h2>
      <article class="copy-card">
        <div class="copy-tabs">
          ${copies.map((copy, index) => `
            <button class="copy-tab ${index === currentCopy ? "active" : ""}" data-copy="${index}">
              ${safe(copy.platform_label || copy.platform)}
            </button>`).join("")}
        </div>
        <div class="copy-body">
          <h3>${safe(copies[currentCopy].title || copies[currentCopy].platform_label)}</h3>
          <pre>${safe(copies[currentCopy].content)}</pre>
        </div>
      </article>
      ${approval("文案审阅", data.manifest.copy_approval)}`;
  }

  function renderIntent() {
    const intent = data.manifest.image_intent;
    return `
      <h2>是否基于内容生成配图</h2>
      <div class="decision-grid">
        <article class="decision yes">
          <span class="chip">YES</span>
          <h3>是，生成配图</h3>
          <p>继续行业路由、视觉方向、资产清单和逐张生成。</p>
        </article>
        <article class="decision no">
          <span class="chip" style="background:var(--brown)">NO</span>
          <h3>否，暂不生成</h3>
          <p>结束视觉分支，只保留文案编辑、导出和重新适配。</p>
        </article>
      </div>
      ${approval("本次配图意图", intent)}`;
  }

  function renderDirections() {
    const directions = list(data.visual_directions);
    const cards = directions.map(direction => `
      <article class="direction-card">
        <span class="chip">${safe(direction.id)}</span>
        <h3>${safe(direction.name)}</h3>
        <p>${safe(direction.fit)}</p>
        <div class="score-row">
          <span>${safe(direction.platforms || "跨平台")}</span>
          <span>推荐 <strong class="score">${safe(direction.score || "—")}</strong></span>
        </div>
      </article>`).join("");
    return `
      <h2>内容特定的视觉方向</h2>
      <div class="card-grid">${cards || '<div class="empty">尚未进入视觉方向阶段</div>'}</div>
      ${approval("视觉方向", data.manifest.visual_direction_approval)}`;
  }

  function renderAssets() {
    const assets = list(data.assets);
    const cards = assets.map(asset => `
      <article class="asset-card">
        <span class="chip">${safe(asset.platform)}</span>
        <h3>${safe(asset.id)}</h3>
        <p>${safe(asset.purpose)}</p>
        <div class="asset-meta">
          <span>来源 ${safe(asset.source_anchor)}</span>
          <span>比例 ${safe(asset.aspect_ratio)}</span>
          <span>规划 ${safe(asset.planning_status)}</span>
          <span>生成 ${safe(asset.generation_status)}</span>
        </div>
      </article>`).join("");
    return `
      <h2>可追溯的资产清单</h2>
      <div class="card-grid">${cards || '<div class="empty">当前没有视觉资产</div>'}</div>
      ${approval("Visual manifest", data.manifest.visual_manifest_approval)}`;
  }

  function renderDelivery() {
    const assets = list(data.assets);
    const ready = assets.filter(asset => asset.generation_status === "ready").length;
    const qaPassed = assets.filter(asset => Object.values(asset.qa || {}).every(value => value === "passed")).length;
    return `
      <h2>生成、QA 与交付</h2>
      <div class="screen-grid">
        <article class="panel">
          <div class="panel-label">Run summary</div>
          <p class="thesis">${ready} / ${assets.length} 个资产已生成</p>
          <div class="fact-grid">
            <div class="fact"><label>QA passed</label><strong>${qaPassed}</strong></div>
            <div class="fact"><label>Copy packages</label><strong>${list(data.copies).length}</strong></div>
            <div class="fact"><label>Run ID</label><strong>${safe(data.manifest.run_id)}</strong></div>
            <div class="fact"><label>Parent run</label><strong>${safe(data.manifest.parent_run_id || "none")}</strong></div>
          </div>
        </article>
        <article class="panel">
          <div class="panel-label">Deliverables</div>
          ${textList(list(data.deliverables))}
        </article>
      </div>
      ${approval("交付状态", ready === assets.length && qaPassed === assets.length ? "ready" : "in-progress")}`;
  }

  const renderers = [
    renderBrief,
    renderPlatforms,
    renderCopies,
    renderIntent,
    renderDirections,
    renderAssets,
    renderDelivery,
  ];

  function renderTrace() {
    const events = list(data.trace?.[steps[currentStep].key]);
    $("traceTitle").textContent = `${String(currentStep + 1).padStart(2, "0")} · ${steps[currentStep].label}`;
    $("gateLabel").textContent = steps[currentStep].gate;
    $("traceList").innerHTML = events.length ? events.map(event => `
      <article class="trace-event">
        <span class="trace-mark">${safe(event.mark || "S")}</span>
        <div><strong>${safe(event.label || "Skill")}</strong><p>${safe(event.text)}</p></div>
      </article>`).join("") : '<div class="empty">暂无执行记录</div>';
  }

  function render() {
    document.querySelectorAll(".step").forEach((button, index) => {
      button.classList.toggle("active", index === currentStep);
      button.classList.toggle("done", index < currentStep);
    });
    $("screen").innerHTML = renderers[currentStep]();
    document.querySelectorAll("[data-copy]").forEach(button => {
      button.addEventListener("click", () => {
        currentCopy = Number(button.dataset.copy);
        render();
      });
    });
    renderTrace();
  }

  $("runtimeLabel").textContent = `${safe(data.manifest.mode).toUpperCase()} · ${safe(data.manifest.run_id)}`;
  $("runMeta").innerHTML = `SCHEMA ${safe(data.manifest.schema_version)}<br>SKILL ${safe(data.manifest.skill_version)}`;
  $("sourceTitle").textContent = safe(data.source?.file_name || `${data.manifest.article_slug}.md`);
  $("sourceMeta").textContent = `${safe(data.source?.language || data.locale_assumptions?.source_language)} · 完整读取`;
  $("sourceHeadline").textContent = safe(data.source?.title || data.manifest.article_slug);
  $("sourceSummary").innerHTML = list(data.source?.summary_paragraphs).map(item => `<p>${item}</p>`).join("");
  $("caseId").innerHTML = `CASE REPLAY<br>${safe(data.manifest.run_id)}<br>${safe(data.manifest.mode)} MODE`;

  $("stepper").innerHTML = steps.map((step, index) => `
    <button class="step ${index === 0 ? "active" : ""}" data-step="${index}">
      <span class="step-index">${String(index + 1).padStart(2, "0")}</span>
      <span class="step-label">${step.label}</span>
    </button>`).join("");
  document.querySelectorAll("[data-step]").forEach(button => {
    button.addEventListener("click", () => {
      currentStep = Number(button.dataset.step);
      render();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });

  render();
})();
