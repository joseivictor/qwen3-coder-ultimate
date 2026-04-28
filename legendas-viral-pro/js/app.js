(function () {
  const cs = new CSInterface();
  const state = {
    extensionPath: "",
    host: "BROWSER",
    projectId: "sem_projeto",
    sequenceId: "sem_sequencia",
    captions: [],
    processed: [],
    selectedCaptionIds: new Set(),
    templates: [],
    activeLineCount: 1,
    activeTemplateId: ""
  };

  const $ = (id) => document.getElementById(id);
  const log = LVP.Logger;

  function setLog() {
    $("logOutput").textContent = log.text();
  }

  function callHost(functionName, payload) {
    return new Promise(resolve => {
      const raw = payload === undefined ? "" : JSON.stringify(JSON.stringify(payload));
      const script = payload === undefined ? `${functionName}();` : `${functionName}(${raw});`;
      cs.evalScript(script, result => {
        try { resolve(JSON.parse(result)); }
        catch (_) { resolve({ ok: false, error: result || "Resposta host invalida" }); }
      });
    });
  }

  function initHost() {
    const extensionKey = window.SystemPath && window.SystemPath.EXTENSION ? window.SystemPath.EXTENSION : "extension";
    state.extensionPath = cs.getSystemPath ? cs.getSystemPath(extensionKey) : "";
    try {
      const env = cs.getHostEnvironment();
      state.host = env.appName || "BROWSER";
    } catch (_) {}
    $("hostStatus").textContent = state.host === "BROWSER" ? "Preview local" : state.host;
    callHost("LVP_getContext").then(ctx => {
      if (ctx && ctx.ok) {
        state.projectId = ctx.projectId || state.projectId;
        state.sequenceId = ctx.sequenceId || state.sequenceId;
        log.info("Contexto host carregado", ctx);
      } else {
        log.warn("Host offline ou sem contexto", ctx);
      }
      setLog();
    });
  }

  function currentStyle() {
    return {
      fontHighlight: $("fontHighlight").value.trim(),
      fontSupport: $("fontSupport").value.trim(),
      colorHighlight: $("colorHighlight").value,
      colorSupport: $("colorSupport").value
    };
  }

  function preferredTemplates() {
    const map = {};
    [1, 2, 3, 4, 5].forEach(n => {
      const value = $(`preferred${n}`).value;
      if (value) map[n] = value;
    });
    return map;
  }

  function renderTemplateSelectors() {
    const grouped = LVP.Templates.byLineCount(state.templates);
    [1, 2, 3, 4, 5].forEach(n => {
      const select = $(`preferred${n}`);
      select.innerHTML = `<option value="">${n}L auto</option>` + (grouped[n] || []).map(t => (
        `<option value="${t.id}">${n}L ${t.name}</option>`
      )).join("");
    });
  }

  function renderTemplateTabs() {
    $("templateTabs").innerHTML = [1, 2, 3, 4, 5].map(n => (
      `<button type="button" class="${state.activeLineCount === n ? "active" : ""}" data-line-tab="${n}">${n}L</button>`
    )).join("");
    document.querySelectorAll("[data-line-tab]").forEach(button => {
      button.addEventListener("click", () => {
        state.activeLineCount = Number(button.dataset.lineTab);
        renderTemplates();
      });
    });
  }

  function renderTemplates() {
    renderTemplateTabs();
    const list = state.templates.filter(t => Number(t.lineCount) === state.activeLineCount);
    $("templateGrid").innerHTML = list.map(template => {
      const thumb = template.thumb ? `<span class="template-thumb" style="background-image:url('file:///${String(template.thumb).replace(/\\/g, "/")}')"></span>` : "";
      const origin = template.source ? `${template.source}<br>` : "";
      return (
      `<button type="button" class="template-card ${state.activeTemplateId === template.id ? "active" : ""}" data-template-id="${template.id}">
        ${thumb}
        <strong>${template.name}</strong>
        <small>${origin}${template.category || `${template.lineCount} linhas`}<br>${template.sfx ? "SFX: sim" : "SFX: nao"}</small>
      </button>`
      );
    }).join("") || `<p>Nenhum modelo encontrado para ${state.activeLineCount} linhas. Adicione .mogrt/.cgt/.aep nesta pasta.</p>`;
    document.querySelectorAll("[data-template-id]").forEach(button => {
      button.addEventListener("click", () => {
        state.activeTemplateId = button.dataset.templateId;
        renderTemplates();
      });
    });
    $("templateStatus").textContent = `${state.templates.length} modelos`;
  }

  function loadTemplates() {
    state.templates = LVP.Templates.list(state.extensionPath);
    if (!state.activeTemplateId && state.templates[0]) state.activeTemplateId = state.templates[0].id;
    renderTemplateSelectors();
    renderTemplates();
  }

  function parseSrtText(text, sourceName) {
    const captions = LVP.SRT.parse(text);
    state.captions = captions;
    state.processed = captions;
    state.selectedCaptionIds.clear();
    const payload = { sourceName: sourceName || "texto_colado", original: text, captions, processed: captions };
    LVP.Cache.save(state.projectId, state.sequenceId, payload);
    $("srtStatus").textContent = captions.length ? `${captions.length} legendas importadas` : "Nada encontrado";
    log.info("SRT processado", { sourceName, captions: captions.length });
    renderCaptions();
    setLog();
  }

  function renderCaptions() {
    const captions = state.processed.length ? state.processed : state.captions;
    $("captionCount").textContent = `${captions.length} itens`;
    $("captionList").innerHTML = captions.map(caption => {
      const checked = state.selectedCaptionIds.has(caption.id) ? "checked" : "";
      const viral = caption.selectedForViral ? "viral" : "";
      const meta = `${LVP.SRT.secondsToSrtTime(caption.start)} - ${LVP.SRT.secondsToSrtTime(caption.end)} | score ${caption.viralScore || 0}`;
      const hit = caption.highlightText ? `<div class="caption-hit">Destaque: ${caption.highlightText}</div>` : "";
      return `<article class="caption-item ${viral}">
        <input type="checkbox" data-caption-id="${caption.id}" ${checked}>
        <div>
          <div class="caption-meta">${meta}</div>
          <div class="caption-text">${caption.text}</div>
          ${hit}
        </div>
      </article>`;
    }).join("");
    document.querySelectorAll("[data-caption-id]").forEach(input => {
      input.addEventListener("change", () => {
        const id = Number(input.dataset.captionId);
        input.checked ? state.selectedCaptionIds.add(id) : state.selectedCaptionIds.delete(id);
      });
    });
  }

  function runViralAnalysis() {
    if (!state.captions.length) {
      log.warn("Importe um SRT antes de analisar");
      setLog();
      return [];
    }
    const selectedIds = $("applyScope").value === "selected" ? Array.from(state.selectedCaptionIds) : null;
    state.processed = LVP.ViralAnalyzer.analyze(state.captions, {
      intensity: $("viralIntensity").value,
      type: $("viralType").value,
      maxHighlights: Number($("maxHighlights").value || 24),
      selectedIds,
      preferredTemplates: preferredTemplates(),
      sfxEnabled: $("sfxEnabled").checked
    });
    const count = state.processed.filter(c => c.selectedForViral).length;
    $("viralSummary").textContent = `${count} destaques escolhidos`;
    LVP.Cache.save(state.projectId, state.sequenceId, {
      captions: state.captions,
      processed: state.processed,
      original: $("srtRawInput").value || ""
    });
    log.info("Destaque viral analisado", { count });
    renderCaptions();
    setLog();
    return state.processed.filter(c => c.selectedForViral);
  }

  function templateById(id, lineCount) {
    return state.templates.find(t => t.id === id) ||
      state.templates.find(t => Number(t.lineCount) === Number(lineCount)) ||
      null;
  }

  function buildApplyPayload(items, mode) {
    return {
      mode,
      extensionPath: state.extensionPath,
      style: currentStyle(),
      sfxEnabled: $("sfxEnabled").checked,
      items: items.map(item => {
        const template = templateById(item.templateId || state.activeTemplateId, item.templateLineCount || item.lineCount || 1);
        return {
          id: item.id,
          start: item.start,
          end: item.end,
          text: item.text,
          highlightText: item.highlightText || "",
          supportText: item.supportText || "",
          highlightLines: item.highlightLines || [],
          supportLines: item.supportLines || LVP.LineBreaker.breakSmart(item.text, { maxLines: item.lineCount || 2 }),
          lineCount: item.templateLineCount || item.lineCount || 1,
          template,
          sfx: $("sfxEnabled").checked && template ? template.sfx : ""
        };
      })
    };
  }

  function applyItems(items, mode) {
    if (!items.length) {
      log.warn("Nenhum item para aplicar");
      setLog();
      return;
    }
    const payload = buildApplyPayload(items, mode);
    log.info("Enviando lote para host", { mode, items: payload.items.length });
    setLog();
    callHost("LVP_applyCaptionTemplateBatch", payload).then(result => {
      if (result && result.ok) log.info("Host concluiu aplicacao", result);
      else log.error("Falha na aplicacao host", result);
      setLog();
    });
  }

  function bindEvents() {
    $("srtFileInput").addEventListener("change", event => {
      const file = event.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {
        $("srtRawInput").value = String(reader.result || "");
        parseSrtText(reader.result, file.name);
      };
      reader.readAsText(file, "utf-8");
    });
    $("parsePastedBtn").addEventListener("click", () => parseSrtText($("srtRawInput").value, "texto_colado"));
    $("loadCacheBtn").addEventListener("click", () => {
      const cached = LVP.Cache.load(state.projectId, state.sequenceId);
      if (!cached) {
        log.warn("Sem cache para projeto/sequencia atual");
      } else {
        state.captions = cached.captions || [];
        state.processed = cached.processed || state.captions;
        $("srtStatus").textContent = `${state.captions.length} legendas recuperadas`;
        log.info("Cache recuperado", { captions: state.captions.length });
        renderCaptions();
      }
      setLog();
    });
    $("clearCacheBtn").addEventListener("click", () => {
      LVP.Cache.clear(state.projectId, state.sequenceId);
      state.captions = [];
      state.processed = [];
      renderCaptions();
      log.info("Cache limpo");
      setLog();
    });
    $("analyzeBtn").addEventListener("click", runViralAnalysis);
    $("applyViralBtn").addEventListener("click", () => applyItems(runViralAnalysis(), "viral-auto"));
    $("applyManualBtn").addEventListener("click", () => {
      const ids = state.selectedCaptionIds;
      const items = (state.processed.length ? state.processed : state.captions).filter(item => ids.has(item.id));
      applyItems(items, "manual-selected");
    });
    $("applyBatchBtn").addEventListener("click", () => {
      const items = (state.processed.length ? state.processed : state.captions).map(item => {
        const lines = LVP.LineBreaker.breakSmart(item.text, { maxLines: 5 });
        return Object.assign({}, item, { supportLines: lines, lineCount: Math.min(5, lines.length), templateLineCount: Math.min(5, lines.length) });
      });
      applyItems(items, "full-batch");
    });
    $("applyIndividualBtn").addEventListener("click", () => {
      const lines = $("individualText").value.split(/\n+/).map(s => s.trim()).filter(Boolean);
      if (!lines.length) return;
      const nowItem = {
        id: "individual",
        start: null,
        end: null,
        text: lines.join(" "),
        supportLines: lines,
        lineCount: Math.min(5, lines.length),
        templateLineCount: Math.min(5, lines.length)
      };
      applyItems([nowItem], "individual");
    });
    $("copyLogsBtn").addEventListener("click", () => navigator.clipboard && navigator.clipboard.writeText(log.text()));
  }

  document.addEventListener("DOMContentLoaded", () => {
    initHost();
    loadTemplates();
    bindEvents();
    renderCaptions();
    log.info("Legendas Viral Pro iniciado");
    setLog();
  });
})();
