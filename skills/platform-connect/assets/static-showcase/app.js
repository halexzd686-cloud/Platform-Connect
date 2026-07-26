(() => {
  "use strict";

  const dataElement = document.getElementById("case-data");
  const data = JSON.parse(dataElement.textContent);
  const $ = id => document.getElementById(id);
  const list = value => Array.isArray(value) ? value : [];
  const text = value => value === null || value === undefined || value === "" ? "未记录" : String(value);
  const escapeHtml = value => text(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
  const multiline = value => escapeHtml(value).replaceAll("\n", "<br>");

  const manifest = data.manifest || {};
  const platforms = list(data.platforms);
  const copies = list(data.copies);
  const assets = list(data.assets);
  const readyAssets = assets.filter(asset => asset.generation_status === "ready" && asset.file);
  const outcome = data.outcome || {};
  let currentPlatform = platforms[0]?.id || manifest.platforms?.[0] || "";
  let activeFilter = "all";
  let toastTimer;

  const provenanceLabels = {
    pending: "待确认",
    explicit: "用户指定",
    inferred: "Agent 推荐",
    profile: "用户配置",
    bundled: "联合确认",
    preauthorized: "预授权",
  };

  function platformLabel(platformId) {
    const platform = platforms.find(item => item.id === platformId);
    return platform?.label || platformId;
  }

  function assetUrl(file) {
    if (!file) return "";
    return "../" + String(file).split("/").map(encodeURIComponent).join("/");
  }

  function showToast(message) {
    $("toast").textContent = message;
    $("toast").classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => $("toast").classList.remove("show"), 1800);
  }

  function copyText(value) {
    const content = String(value || "");
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(content)
        .then(() => showToast("文案已复制"))
        .catch(() => fallbackCopy(content));
      return;
    }
    fallbackCopy(content);
  }

  function fallbackCopy(content) {
    const field = document.createElement("textarea");
    field.value = content;
    field.setAttribute("readonly", "");
    field.style.position = "fixed";
    field.style.opacity = "0";
    document.body.appendChild(field);
    field.select();
    const copied = document.execCommand("copy");
    field.remove();
    showToast(copied ? "文案已复制" : "请手动选中文案复制");
  }

  function renderSource() {
    const source = data.source || {};
    const fileName = source.file_name || manifest.source?.reference || `${manifest.article_slug}.md`;
    const inputType = source.input_type || manifest.source?.input_type || "pasted";
    const typeLabel = inputType === "url"
      ? "URL"
      : (String(fileName).split(".").pop() || "DOC").slice(0, 4).toUpperCase();
    $("sourceType").textContent = typeLabel;
    $("sourceTitle").textContent = fileName;
    $("sourceMeta").textContent = [
      source.unit_label,
      source.language || data.locale_assumptions?.source_language,
      source.read_status === "complete" ? "已完整读取" : source.read_status,
    ].filter(Boolean).join(" · ");
    $("sourceHeadline").textContent = source.title || manifest.source?.title || manifest.article_slug;
    $("sourceSummary").innerHTML = list(source.summary_paragraphs)
      .slice(0, 3)
      .map(item => `<p>${escapeHtml(item)}</p>`)
      .join("");
    $("sideFacts").innerHTML = [
      ["发布平台", platforms.map(item => item.label || item.id).join(" · ")],
      ["文案版本", `${copies.length} 份`],
      ["视觉资产", `${readyAssets.length} 张`],
      ["质量检查", readyAssets.length && readyAssets.every(asset =>
        Object.values(asset.qa || {}).every(value => value === "passed"))
        ? "全部通过"
        : "见交付状态"],
    ].map(([label, value]) => `
      <div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>
    `).join("");
  }

  function renderHero() {
    const sourceTitle = data.source?.title || manifest.source?.title || manifest.article_slug;
    const labels = platforms.map(item => item.label || item.id).join("与");
    const assetSentence = readyAssets.length
      ? `和 ${readyAssets.length} 张视觉资产`
      : "";
    $("outcomeSentence").innerHTML = `本次读取了<strong>《${escapeHtml(sourceTitle)}》</strong>，最终选择<strong>${escapeHtml(labels || "已记录平台")}</strong>，完成 ${copies.length} 份平台原生文案${assetSentence}；最终成果与事实基线已整理为可复核的交付包。`;
    $("caseId").innerHTML = [
      `CASE ${escapeHtml(manifest.run_id)}`,
      `${escapeHtml(data.locale_assumptions?.source_language)} / ${escapeHtml(data.locale_assumptions?.target_language || "SOURCE")}`,
      escapeHtml(outcome.status || "in-progress").toUpperCase(),
    ].map(item => `<span>${item}</span>`).join("");
    const summary = [
      ["INPUT", `${escapeHtml((data.source?.input_type || "source").toUpperCase())} · COMPLETE`],
      ["PLATFORMS", platforms.map(item => escapeHtml(item.label || item.id)).join(" · ")],
      ["COPY", `${copies.length} 份定稿`],
      ["VISUALS", `${readyAssets.length} 张配图`],
      ["QA", outcome.status === "ready" ? "● PASSED" : "● IN PROGRESS"],
    ];
    $("summaryStrip").innerHTML = summary.map(([label, value], index) => `
      <div><small>${label}</small><strong class="${index === 4 ? "ready" : ""}">${value}</strong></div>
    `).join("");
  }

  function renderPackageTabs() {
    $("packageTabs").innerHTML = platforms.map(platform => {
      const active = platform.id === currentPlatform;
      return `
        <button class="${active ? "active" : ""}" data-platform-tab="${escapeHtml(platform.id)}" aria-pressed="${active}">
          <strong>${escapeHtml(platform.label || platform.id)}</strong>
          <span>${escapeHtml(platform.language || data.locale_assumptions?.target_language || data.locale_assumptions?.source_language)} · ${escapeHtml(platform.market || data.locale_assumptions?.market || "source")}</span>
        </button>`;
    }).join("") + `<p>${platforms.length} / ${platforms.length} PACKAGES<br>FINAL COPY + VISUALS</p>`;
    document.querySelectorAll("[data-platform-tab]").forEach(button => {
      button.addEventListener("click", () => {
        currentPlatform = button.dataset.platformTab;
        renderPackages();
      });
    });
  }

  function renderAssetPreview(asset, compact = false) {
    if (!asset || !asset.file) {
      return `<div class="visual-empty"><span>NO IMAGE</span><strong>本平台未交付图片</strong></div>`;
    }
    const url = assetUrl(asset.file);
    return `
      <button class="asset-preview ${compact ? "compact" : ""}" data-preview-asset="${escapeHtml(asset.id)}">
        <img src="${escapeHtml(url)}" alt="${escapeHtml(asset.on_image_text || asset.purpose || asset.id)}">
        <span>${escapeHtml(asset.asset_type)} · ${escapeHtml(asset.aspect_ratio)}</span>
      </button>`;
  }

  function renderPackages() {
    renderPackageTabs();
    const copy = copies.find(item => item.platform === currentPlatform) || copies[0];
    const platform = platforms.find(item => item.id === currentPlatform) || {};
    const packageAssets = readyAssets.filter(asset => asset.platform === currentPlatform);
    const title = copy?.title || platformLabel(currentPlatform);
    const content = copy?.content || "当前运行未写入平台文案。";
    const primary = packageAssets[0];
    const secondary = packageAssets.slice(1, 3);
    $("packageView").innerHTML = `
      <article class="copy-pane">
        <div class="chips">
          <span class="strong">FINAL</span>
          <span>${escapeHtml(currentPlatform)}</span>
          <span>${escapeHtml(platform.language || data.locale_assumptions?.target_language || data.locale_assumptions?.source_language)}</span>
        </div>
        <h3>${escapeHtml(title)}</h3>
        <div class="copy-content">${multiline(content)}</div>
        <div class="copy-foot">
          <small>${content.length} 字符 · ${escapeHtml(platformLabel(currentPlatform))}</small>
          <button id="copyCurrent">复制文案</button>
        </div>
      </article>
      <div class="visual-pane">
        <div class="visual-grid ${secondary.length ? "" : "single"}">
          ${renderAssetPreview(primary)}
          ${secondary.length ? `<div class="visual-stack">${secondary.map(asset => renderAssetPreview(asset, true)).join("")}</div>` : ""}
        </div>
        <p><span>${packageAssets.length} ASSETS</span><strong>${packageAssets.every(asset => Object.values(asset.qa || {}).every(value => value === "passed")) ? "QA PASSED" : "QA PENDING"}</strong></p>
      </div>`;
    $("copyCurrent").addEventListener("click", () => copyText(content));
    bindAssetPreviews();
  }

  function renderBaseline() {
    const brief = data.brief || {};
    const claims = list(brief.protected_claims);
    const flags = list(data.review_flags);
    $("baselineGrid").innerHTML = `
      <article class="baseline-primary">
        <p>CORE THESIS</p>
        <h3>${escapeHtml(brief.core_thesis)}</h3>
        <div class="baseline-facts">
          <div><span>作者立场</span><strong>${escapeHtml(brief.author_stance)}</strong></div>
          <div><span>目标受众</span><strong>${escapeHtml(brief.audience)}</strong></div>
          <div><span>沟通任务</span><strong>${escapeHtml(brief.audience_need)}</strong></div>
          <div><span>语气</span><strong>${escapeHtml(brief.tone)}</strong></div>
        </div>
      </article>
      <article class="baseline-secondary">
        <p>PROTECTED CLAIMS</p>
        <ul>${claims.length ? claims.map(item => `<li><b>L</b><span>${escapeHtml(item)}</span></li>`).join("") : "<li><span>暂无不可漂移声明</span></li>"}</ul>
        ${flags.length ? `<p class="flag-title">REVIEW FLAGS</p><ul>${flags.map(item => `<li><b>!</b><span>${escapeHtml(item)}</span></li>`).join("")}</ul>` : ""}
      </article>`;
  }

  function renderFilters() {
    const filterPlatforms = platforms.filter(platform =>
      readyAssets.some(asset => asset.platform === platform.id));
    $("assetFilters").innerHTML = [
      `<button class="${activeFilter === "all" ? "active" : ""}" data-filter="all">全部 ${readyAssets.length}</button>`,
      ...filterPlatforms.map(platform => {
        const count = readyAssets.filter(asset => asset.platform === platform.id).length;
        return `<button class="${activeFilter === platform.id ? "active" : ""}" data-filter="${escapeHtml(platform.id)}">${escapeHtml(platform.label || platform.id)} ${count}</button>`;
      }),
    ].join("");
    document.querySelectorAll("[data-filter]").forEach(button => {
      button.addEventListener("click", () => {
        activeFilter = button.dataset.filter;
        renderGallery();
      });
    });
  }

  function renderGallery() {
    renderFilters();
    const filtered = activeFilter === "all"
      ? readyAssets
      : readyAssets.filter(asset => asset.platform === activeFilter);
    $("assetGallery").innerHTML = filtered.length ? filtered.map(asset => `
      <article class="asset-card">
        ${renderAssetPreview(asset)}
        <div>
          <header><strong>${escapeHtml(asset.purpose || asset.id)}</strong><span>${escapeHtml(asset.id)}</span></header>
          <dl>
            <div><dt>平台</dt><dd>${escapeHtml(platformLabel(asset.platform))}</dd></div>
            <div><dt>比例</dt><dd>${escapeHtml(asset.aspect_ratio)}</dd></div>
            <div><dt>来源</dt><dd>${escapeHtml(asset.source_anchor)}</dd></div>
            <div><dt>QA</dt><dd class="passed">${Object.values(asset.qa || {}).every(value => value === "passed") ? "PASSED" : "PENDING"}</dd></div>
          </dl>
        </div>
      </article>
    `).join("") : `<div class="empty-state"><strong>本次没有最终图片</strong><span>文案交付仍可正常查看。</span></div>`;
    bindAssetPreviews();
  }

  function deliverableType(path) {
    const extension = String(path).split(".").pop().toUpperCase();
    return extension.length <= 4 ? extension : "FILE";
  }

  function renderDelivery() {
    const deliverables = list(data.deliverables);
    $("deliveryList").innerHTML = deliverables.map(path => `
      <a href="../${escapeHtml(String(path).split("/").map(encodeURIComponent).join("/"))}">
        <b>${escapeHtml(deliverableType(path))}</b>
        <span><strong>${escapeHtml(path)}</strong><small>交付文件 · 可离线访问</small></span>
        <em>READY</em>
      </a>
    `).join("");
    const ready = outcome.status === "ready";
    $("deliveryStatus").innerHTML = `
      <span>${String(deliverables.length).padStart(2, "0")}</span>
      <h3>${ready ? "成果已经归档" : "成果仍在整理"}</h3>
      <p>从原始文档到平台文案、视觉资产与来源记录，本次内容工作已经形成可复核的交付闭环。</p>
      <strong>${ready ? "READY TO DELIVER" : "IN PROGRESS"}</strong>`;
  }

  function renderTrace() {
    const recommendations = list(data.platform_recommendations);
    const provenance = data.decision_provenance || {};
    const recommendationHtml = recommendations.length ? `
      <article>
        <p>PLATFORM RECOMMENDATIONS</p>
        ${recommendations.map(item => `
          <div class="recommendation">
            <b>${escapeHtml(platformLabel(item.platform))}</b>
            <span>${escapeHtml(item.rationale)}</span>
            <small>${escapeHtml(item.visual_direction)} · ${escapeHtml(item.selection_status)}</small>
          </div>
        `).join("")}
      </article>` : "";
    const decisionHtml = `
      <article>
        <p>DECISION PROVENANCE</p>
        ${Object.entries(provenance).map(([key, value]) => `
          <div class="decision"><span>${escapeHtml(key)}</span><strong>${escapeHtml(provenanceLabels[value] || value)}</strong></div>
        `).join("")}
      </article>`;
    const traceEvents = Object.entries(data.trace || {}).flatMap(([stage, events]) =>
      list(events).map(event => ({ stage, ...event })));
    const eventsHtml = `
      <article>
        <p>EXECUTION TRACE</p>
        ${traceEvents.length ? traceEvents.map(event => `
          <div class="trace-event"><b>${escapeHtml(event.mark || "S")}</b><span><strong>${escapeHtml(event.label || event.stage)}</strong><small>${escapeHtml(event.text)}</small></span></div>
        `).join("") : '<div class="trace-event"><span><strong>执行记录已归档</strong><small>本次没有额外事件说明。</small></span></div>'}
      </article>`;
    $("traceContent").innerHTML = recommendationHtml + decisionHtml + eventsHtml;
  }

  function bindAssetPreviews() {
    document.querySelectorAll("[data-preview-asset]").forEach(button => {
      button.addEventListener("click", () => openLightbox(button.dataset.previewAsset));
    });
  }

  function openLightbox(assetId) {
    const asset = assets.find(item => item.id === assetId);
    if (!asset || !asset.file) return;
    $("lightboxImage").src = assetUrl(asset.file);
    $("lightboxImage").alt = asset.on_image_text || asset.purpose || asset.id;
    $("lightboxTitle").textContent = asset.purpose || asset.id;
    $("lightboxMeta").innerHTML = `
      <span>${escapeHtml(platformLabel(asset.platform))}</span>
      <span>${escapeHtml(asset.aspect_ratio)}</span>
      <span>${escapeHtml(asset.source_anchor)}</span>
      <span>${Object.values(asset.qa || {}).every(value => value === "passed") ? "QA PASSED" : "QA PENDING"}</span>`;
    $("lightbox").classList.add("open");
    document.body.classList.add("no-scroll");
    $("lightboxClose").focus();
  }

  function closeLightbox() {
    $("lightbox").classList.remove("open");
    document.body.classList.remove("no-scroll");
  }

  function bindGlobalInteractions() {
    $("traceToggle").addEventListener("click", () => {
      const open = $("trace").classList.toggle("open");
      $("traceToggle").setAttribute("aria-expanded", String(open));
    });
    $("lightboxClose").addEventListener("click", closeLightbox);
    $("lightbox").addEventListener("click", event => {
      if (event.target === $("lightbox")) closeLightbox();
    });
    document.addEventListener("keydown", event => {
      if (event.key === "Escape" && $("lightbox").classList.contains("open")) {
        closeLightbox();
      }
    });
  }

  $("runtimeLabel").textContent = `${text(manifest.mode).toUpperCase()} · ${text(manifest.review_policy).toUpperCase()} · ${text(outcome.status).toUpperCase()}`;
  $("runMeta").innerHTML = `SCHEMA ${escapeHtml(manifest.schema_version)}<br>SKILL ${escapeHtml(manifest.skill_version)}`;

  renderSource();
  renderHero();
  renderPackages();
  renderBaseline();
  renderGallery();
  renderDelivery();
  renderTrace();
  bindGlobalInteractions();
})();
