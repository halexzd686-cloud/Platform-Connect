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
  const paragraphs = value => String(value || "")
    .split(/\n\s*\n/)
    .filter(Boolean)
    .map(item => `<p>${multiline(item.trim())}</p>`)
    .join("");

  const manifest = data.manifest || {};
  const platforms = list(data.platforms);
  const copies = list(data.copies);
  const visualPrompts = list(data.visual_prompts);
  const downloads = data.downloads || {};
  const outcome = data.outcome || {};
  let currentPlatform = platforms[0]?.id || manifest.platforms?.[0] || "";
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

  function relativeUrl(path) {
    return `../${String(path || "").split("/").map(encodeURIComponent).join("/")}`;
  }

  function showToast(message) {
    $("toast").textContent = message;
    $("toast").classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => $("toast").classList.remove("show"), 1800);
  }

  function copyText(value, successMessage) {
    const content = String(value || "");
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(content)
        .then(() => showToast(successMessage))
        .catch(() => fallbackCopy(content, successMessage));
      return;
    }
    fallbackCopy(content, successMessage);
  }

  function fallbackCopy(content, successMessage) {
    const field = document.createElement("textarea");
    field.value = content;
    field.setAttribute("readonly", "");
    field.style.position = "fixed";
    field.style.opacity = "0";
    document.body.appendChild(field);
    field.select();
    const copied = document.execCommand("copy");
    field.remove();
    showToast(copied ? successMessage : "请手动选中内容复制");
  }

  function renderSource() {
    const source = data.source || {};
    const brief = data.brief || {};
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
    $("sourceHeadline").textContent = brief.core_thesis || source.title || manifest.source?.title || manifest.article_slug;
    $("sideFacts").innerHTML = [
      ["作者立场", brief.author_stance],
      ["目标读者", brief.audience],
      ["已选平台", platforms.map(item => item.label || item.id).join(" · ")],
    ].map(([label, value]) => `
      <div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>
    `).join("");
  }

  function renderHero() {
    const labels = platforms.map(item => item.label || item.id);
    const promptSentence = visualPrompts.length
      ? `，并准备好 <strong>${visualPrompts.length} 条配图提示词</strong>`
      : "";
    $("outcomeSentence").innerHTML = `已完成<strong>${escapeHtml(labels.join("与") || "已记录平台")}</strong>的最终文案${promptSentence}。`;
    const routeItems = [
      "<span>SOURCE</span>",
      ...labels.flatMap(label => ["<i></i>", `<span>${escapeHtml(label)}</span>`]),
      `<b>${outcome.status === "ready" ? "READY" : "IN PROGRESS"}</b>`,
    ];
    $("deliveryRoute").innerHTML = routeItems.join("");
    const summary = [
      ["原始内容", "1 篇", "完整读取"],
      ["发布平台", `${platforms.length} 个`, "平台原生"],
      ["最终文案", `${copies.length} 份`, "已经定稿"],
      ["配图提示词", `${visualPrompts.length} 条`, "可复制"],
    ];
    $("summaryStrip").innerHTML = summary.map(([label, value, note]) => `
      <div><small>${escapeHtml(label)}</small><strong>${escapeHtml(value)}</strong><span>${escapeHtml(note)}</span></div>
    `).join("");
  }

  function renderPackageTabs() {
    $("packageTabs").innerHTML = platforms.map(platform => {
      const active = platform.id === currentPlatform;
      return `
        <button class="${active ? "active" : ""}" data-platform-tab="${escapeHtml(platform.id)}" aria-pressed="${active}">
          <span>${escapeHtml(platform.label || platform.id)}</span>
          <small>${escapeHtml(platform.language || data.locale_assumptions?.target_language || data.locale_assumptions?.source_language)} · ${escapeHtml(platform.market || data.locale_assumptions?.market || "source")}</small>
        </button>`;
    }).join("") + `
      <p><b>${String(platforms.length).padStart(2, "0")}</b><span>FINAL<br>DRAFTS</span></p>`;
    document.querySelectorAll("[data-platform-tab]").forEach(button => {
      button.addEventListener("click", () => {
        currentPlatform = button.dataset.platformTab;
        renderPackages();
      });
    });
  }

  function renderPackages() {
    renderPackageTabs();
    const copy = copies.find(item => item.platform === currentPlatform) || copies[0] || {};
    const platform = platforms.find(item => item.id === currentPlatform) || {};
    const content = copy.content || "当前运行未写入平台文案。";
    const copyDownload = list(downloads.files).find(item =>
      item.kind === "copy" && item.platform === currentPlatform);
    $("packageView").innerHTML = `
      <article class="copy-sheet">
        <div class="copy-meta">
          <span class="status-chip">FINAL</span>
          <span>${escapeHtml(platformLabel(currentPlatform))}</span>
          <span>${escapeHtml(platform.language || data.locale_assumptions?.target_language || data.locale_assumptions?.source_language)}</span>
        </div>
        <h3>${escapeHtml(copy.title || platformLabel(currentPlatform))}</h3>
        <div class="copy-body">${paragraphs(content)}</div>
        <footer>
          <small>${content.length} 字符 · ${escapeHtml(platformLabel(currentPlatform))}定稿</small>
          <div class="button-row">
            <button class="button button-quiet" type="button" id="copyCurrent">复制文案</button>
            ${copyDownload ? `<a class="button button-dark" href="${relativeUrl(copyDownload.path)}" download>下载文案</a>` : ""}
          </div>
        </footer>
      </article>`;
    $("copyCurrent").addEventListener("click", () => copyText(content, "文案已复制"));
    bindDownloadToasts();
  }

  function renderPromptGallery() {
    $("promptGallery").innerHTML = visualPrompts.length
      ? visualPrompts.map((item, index) => `
        <article class="prompt-card ${index % 2 ? "prompt-card-dark" : ""}">
          <header>
            <div>
              <span>${escapeHtml(platformLabel(item.platform))}</span>
              <small>${escapeHtml(item.asset_type)} · ${escapeHtml(item.aspect_ratio)}</small>
            </div>
            <b>${String(index + 1).padStart(2, "0")}</b>
          </header>
          <h3>${escapeHtml(item.visual_direction)}</h3>
          <p class="prompt-purpose">${escapeHtml(item.purpose)}</p>
          <div class="prompt-copy">${multiline(item.prompt)}</div>
          <details>
            <summary>查看使用约束</summary>
            <p><strong>画面文字</strong>${escapeHtml(item.on_image_text || "建议无文字")}</p>
            <p><strong>负面约束</strong>${escapeHtml(item.negative_prompt)}</p>
            <p><strong>事实不变量</strong>${list(item.factual_invariants).map(escapeHtml).join("；")}</p>
            <p><strong>使用建议</strong>${escapeHtml(item.tool_notes)}</p>
          </details>
          <div class="card-actions">
            <span>来源：${escapeHtml(item.source_anchor)}</span>
            <button type="button" data-copy-prompt="${escapeHtml(item.id)}">复制提示词</button>
          </div>
        </article>
      `).join("")
      : `<div class="empty-state"><strong>本次没有配图提示词</strong><span>平台文案仍可正常查看和下载。</span></div>`;
    bindPromptCopies();
  }

  function bindPromptCopies() {
    document.querySelectorAll("[data-copy-prompt]").forEach(button => {
      button.addEventListener("click", () => {
        const promptPackage = visualPrompts.find(item => item.id === button.dataset.copyPrompt);
        if (promptPackage) copyText(promptPackage.prompt, "配图提示词已复制");
      });
    });
  }

  function deliverableType(path) {
    const extension = String(path).split(".").pop().toUpperCase();
    return extension.length <= 4 ? extension : "FILE";
  }

  function renderDelivery() {
    const bundle = downloads.bundle || {};
    const files = list(downloads.files);
    $("downloadPrimary").innerHTML = `
      <span class="package-number">${String(files.length).padStart(2, "0")}</span>
      <div>
        <small>PLATFORM CONNECT · DELIVERY PACKAGE</small>
        <h3>${outcome.status === "ready" ? "本次成果已经整理完毕" : "本次成果仍在整理"}</h3>
        <p>${escapeHtml(bundle.description || `包含 ${files.length} 个用户可直接使用的文件。`)}</p>
      </div>
      ${bundle.path ? `
        <a class="download-all" href="${relativeUrl(bundle.path)}" download>
          <span>下载全部成果</span><small>ZIP · ${files.length} FILES</small>
        </a>` : ""}`;
    $("deliveryList").innerHTML = files.map(item => `
      <a href="${relativeUrl(item.path)}" download>
        <b>${escapeHtml(deliverableType(item.path))}</b>
        <span><strong>${escapeHtml(item.label || item.path)}</strong><small>${escapeHtml(item.description || "最终交付文件")}</small></span>
        <em>下载</em>
      </a>
    `).join("");
    bindDownloadToasts();
  }

  function renderTrace() {
    const brief = data.brief || {};
    const recommendations = list(data.platform_recommendations);
    const provenance = data.decision_provenance || {};
    const reviewPolicy = manifest.review_policy || "compact";
    const sourceHtml = `
      <article>
        <p>SOURCE & FACTS</p>
        <div class="trace-summary"><b>共享事实基线</b><span>${escapeHtml(brief.core_thesis)}</span></div>
        ${list(brief.protected_claims).map(item => `<div class="trace-line"><span>${escapeHtml(item)}</span></div>`).join("")}
      </article>`;
    const recommendationHtml = recommendations.length ? `
      <article>
        <p>PLATFORM DECISIONS · ${escapeHtml(reviewPolicy)}</p>
        ${recommendations.map(item => `
          <div class="recommendation">
            <b>${escapeHtml(platformLabel(item.platform))}</b>
            <span>${escapeHtml(item.rationale)}</span>
            <small>${escapeHtml(item.selection_status)}</small>
          </div>
        `).join("")}
      </article>` : `
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
    $("traceContent").innerHTML = sourceHtml + recommendationHtml + eventsHtml;
  }

  function bindDownloadToasts() {
    document.querySelectorAll("a[download]").forEach(link => {
      if (link.dataset.toastBound === "true") return;
      link.dataset.toastBound = "true";
      link.addEventListener("click", () => {
        const fileName = decodeURIComponent(link.getAttribute("href").split("/").pop());
        showToast(`正在下载：${fileName}`);
      });
    });
  }

  function bindGlobalInteractions() {
    $("traceToggle").addEventListener("click", () => {
      const trace = $("trace");
      const open = trace.classList.toggle("open");
      $("traceToggle").setAttribute("aria-expanded", String(open));
    });
  }

  function renderMeta() {
    $("runMeta").innerHTML = `CASE ${escapeHtml(manifest.run_id)}<br>SKILL ${escapeHtml(manifest.skill_version)}`;
    $("runtimeLabel").textContent = outcome.status === "ready" ? "DELIVERY READY" : "DELIVERY IN PROGRESS";
  }

  renderSource();
  renderHero();
  renderPackages();
  renderPromptGallery();
  renderDelivery();
  renderTrace();
  renderMeta();
  bindGlobalInteractions();
})();
