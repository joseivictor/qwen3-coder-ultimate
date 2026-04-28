/* ============================================================
   JOSÉ VICTOR — PORTFOLIO APP
   Single-file vanilla JS. Carrega data/*.json, renderiza tudo.
   ============================================================ */

const $  = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const STATE = {
  config:   null,
  experts:  [],
  videos:   [],
  courses:  [],
  motion:   [],
  flyers:   [],
  filters:  { experts: new Set(), levels: new Set(), categories: new Set() },
  budget:   { qty: 8, style: 'medio' }
};

/* ---------- DATA LOADERS ---------- */
async function loadJSON(path) {
  try {
    const useDraft = new URLSearchParams(location.search).get('draft') === '1';
    const localDraft = localStorage.getItem('jv_admin_' + path.split('/').pop().replace('.json', ''));
    if (useDraft && localDraft) return JSON.parse(localDraft);
    const r = await fetch(path + '?t=' + Date.now());
    if (!r.ok) throw new Error(r.status);
    return await r.json();
  } catch (e) {
    console.warn('[load] falhou:', path, e);
    return null;
  }
}

async function loadAllData() {
  const [config, experts, videos, courses, motion, flyers] = await Promise.all([
    loadJSON('data/config.json'),
    loadJSON('data/experts.json'),
    loadJSON('data/videos.json'),
    loadJSON('data/courses.json'),
    loadJSON('data/motion.json'),
    loadJSON('data/flyers.json')
  ]);
  STATE.config  = config;
  STATE.experts = experts?.experts ?? [];
  STATE.videos  = videos?.videos   ?? [];
  STATE.courses = courses?.courses ?? [];
  STATE.motion  = motion?.motion   ?? [];
  STATE.flyers  = flyers?.flyers   ?? [];
}

/* ---------- WHATSAPP HELPERS ---------- */
function waLink(message) {
  const num = STATE.config?.site?.whatsapp_digits || '5522981481742';
  return `whatsapp://send?phone=${num}&text=${encodeURIComponent(message)}`;
}

/* ---------- PORTAL ENTRY (lisinho — sem blur, sem burst pesado) ---------- */
function setupPortal() {
  const portal = $('#portal');
  const enter  = $('#enterBtn');
  if (!portal || !enter) return;

  enter.addEventListener('click', () => {
    portal.classList.add('exiting');
    setTimeout(() => {
      portal.style.display = 'none';
      $('#app').classList.remove('hidden');
      $('#bear')?.classList.remove('hidden');
      $('#bear')?.classList.add('playful');
      bearSay('Bem-vindo! 🐻');
      setTimeout(() => bearHide(), 3500);
    }, 850);
  });

  // ENTER tecla também ativa
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && portal.style.display !== 'none') enter.click();
  }, { once: true });
}

/* ---------- TABS ---------- */
function setupTabs() {
  $$('.tabs button').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.tab;
      $$('.tabs button').forEach(b => b.classList.toggle('active', b === btn));
      $$('.tab').forEach(t => t.classList.toggle('active', t.id === 'tab-' + id));
      window.scrollTo({ top: 0, behavior: 'smooth' });

      const says = {
        portfolio: 'Portfolio principal.',
        youtube:   'Videos 16:9.',
        orcamento: 'Orcamento direto.',
        sobre:     'Sobre meu trabalho.'
      };
      if (says[id]) { bearSay(says[id]); setTimeout(bearHide, 2200); }
    });
  });
}

/* ---------- EXPERT LOOKUP ---------- */
function expertById(id) {
  return STATE.experts.find(e => e.id === id);
}

/* ---------- VIDEO RENDER ---------- */
function videoCard(v) {
  const isViral = (v.views || 0) >= 100000;
  const code = shortCode(v.instagram_url || '');
  const catLabel = categoryLabel(v.category);

  const poster = v.thumb
    ? `<img class="video-poster" src="${v.thumb}" alt="${v.title}">`
    : `<div class="video-poster reference-poster">
         <span>${catLabel}</span>
         <strong>${code}</strong>
         <small>Assistir aqui</small>
       </div>`;

  const stats = (v.views || v.likes)
    ? `<div class="stats-row">
         ${v.views ? `<span class="stat-views">${formatNum(v.views)}</span>` : ''}
         ${v.likes ? `<span class="stat-likes">${formatNum(v.likes)}</span>` : ''}
       </div>`
    : '';

  return `
    <div class="video-card ${v.category === 'youtube' ? 'horizontal-card' : ''}" data-id="${v.id}" data-cat="${v.category||''}">
      ${isViral ? '<span class="viral-badge">🔥 Viral</span>' : ''}
      ${poster}
      <div class="play-overlay">
        <div class="video-meta">
          <div class="video-title">${v.title || 'Sem título'}</div>
          ${stats}
        </div>
        <div class="play-icon">▶</div>
      </div>
    </div>`;
}

function formatNum(n) {
  if (n >= 1e6) return (n/1e6).toFixed(1).replace('.0','') + 'M';
  if (n >= 1e3) return (n/1e3).toFixed(1).replace('.0','') + 'K';
  return String(n);
}

function shortCode(url) {
  if (!url) return 'video';
  const clean = url.split('?')[0];
  const ig = clean.match(/instagram\.com\/(?:reel|p)\/([^/]+)/);
  if (ig) return ig[1];
  const yt = url.match(/(?:youtu\.be\/|youtube\.com\/watch\?v=)([A-Za-z0-9_-]+)/);
  return yt ? yt[1] : 'video';
}

function embedURL(url) {
  if (!url) return '';
  const clean = url.split('?')[0].replace(/\/?$/, '/');
  if (clean.includes('instagram.com')) return clean + 'embed/';
  const yt = url.match(/(?:youtu\.be\/|youtube\.com\/watch\?v=)([A-Za-z0-9_-]+)/);
  return yt ? `https://www.youtube.com/embed/${yt[1]}` : '';
}

function categoryLabel(id) {
  const found = STATE.config?.categories?.find(c => c.id === id);
  return found?.label || id || 'Portfolio';
}

function renderVideos() {
  const grid = $('#videoGrid');
  if (!grid) return;

  // Apply filters
  let list = STATE.videos.filter(v => v.category !== 'youtube');
  if (STATE.filters.categories.size) list = list.filter(v => STATE.filters.categories.has(v.category));

  // Sort by portfolio priority. Disruptivo first.
  const categoryRank = { disruptivo: 9, criativos: 8, podcast: 7, live: 6, youtube: 5, unboxing: 4, vlog: 3, entretenimento: 2, fitness: 1 };
  list.sort((a,b) =>
    (categoryRank[b.category] || 0) - (categoryRank[a.category] || 0) ||
    (b.views||0) - (a.views||0)
  );

  if (list.length === 0) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1;">
      <strong>Nenhum vídeo aqui ainda.</strong><br>
      <small>Adicione vídeos pelo painel admin (admin.html) ou ajuste os filtros.</small>
    </div>`;
    return;
  }

  grid.innerHTML = list.map(videoCard).join('');

  // Wire up clicks. Heavy videos load only inside the modal.
  $$('.video-card', grid).forEach(card => {
    const v = list.find(x => x.id === card.dataset.id);
    card.addEventListener('click', () => openModal(v));
  });
}

/* ---------- FILTER CHIPS (inline no portfolio: categoria) ---------- */
function renderFilterChips() {
  const wrap = $('#filterChips');
  if (!wrap) return;
  const catCounts = {};
  STATE.videos.forEach(v => { if (v.category && v.category !== 'youtube') catCounts[v.category] = (catCounts[v.category]||0) + 1; });
  const cats   = (STATE.config?.categories || []).filter(c => catCounts[c.id]);
  const noActive = !STATE.filters.categories.size;

  wrap.innerHTML = `
    <div class="filter-row">
      <span class="filter-row-label">Estilo</span>
      <div class="filter-row-chips">
        <button class="chip ${noActive ? 'active' : ''}" data-clear>Todos</button>
        ${cats.map(c => `<button class="chip ${STATE.filters.categories.has(c.id)?'active':''}" data-cat="${c.id}">${c.label}</button>`).join('')}
      </div>
    </div>
  `;
  $$('.chip', wrap).forEach(chip => {
    chip.addEventListener('click', () => {
      if (chip.dataset.clear !== undefined) {
        STATE.filters.categories.clear();
      } else if (chip.dataset.cat) toggleSet(STATE.filters.categories, chip.dataset.cat);
      renderVideos();
      renderFilterChips();
    });
  });
}
function toggleSet(set, val) { set.has(val) ? set.delete(val) : set.add(val); }

/* ---------- ADVANCED FILTERS PAGE ---------- */
function renderFiltersPage() {
  const wrap = $('#tab-filtros .filter-side');
  if (!wrap) return;
  const cats = STATE.config?.categories || [];

  wrap.innerHTML = `
    <div class="filter-group">
      <h4>Categoria</h4>
      <div class="options">
        ${cats.map(c => `
          <label>
            <input type="checkbox" data-filter="cat" value="${c.id}" ${STATE.filters.categories.has(c.id)?'checked':''}>
            ${c.label}
          </label>`).join('')}
      </div>
    </div>
    <button class="chip" id="clearFilters" style="margin-top:1rem;">Limpar filtros</button>
  `;

  $$('input[type=checkbox]', wrap).forEach(input => {
    input.addEventListener('change', () => {
      toggleSet(STATE.filters.categories, input.value);
      renderFilterResults();
      renderVideos();
      renderFilterChips();
    });
  });
  $('#clearFilters', wrap)?.addEventListener('click', () => {
    STATE.filters.categories.clear();
    renderFiltersPage();
    renderFilterResults();
    renderVideos();
    renderFilterChips();
  });
}

function renderFilterResults() {
  const out = $('#filterResults');
  if (!out) return;
  let list = STATE.videos.slice();
  if (STATE.filters.categories.size) list = list.filter(v => STATE.filters.categories.has(v.category));
  const categoryRank = { disruptivo: 9, criativos: 8, podcast: 7, live: 6, youtube: 5, unboxing: 4, vlog: 3, entretenimento: 2, fitness: 1 };
  list.sort((a,b) =>
    (categoryRank[b.category] || 0) - (categoryRank[a.category] || 0) ||
    (b.views||0) - (a.views||0)
  );

  $('#filterCount').textContent = list.length;
  out.innerHTML = list.length
    ? list.map(videoCard).join('')
    : `<div class="empty-state" style="grid-column:1/-1;"><strong>Nenhum vídeo bate com esses filtros.</strong></div>`;

  $$('.video-card', out).forEach(card => {
    const v = list.find(x => x.id === card.dataset.id);
    card.addEventListener('click', () => openModal(v));
  });
}

function syncFiltersUI() {
  // re-render filter page if visible
  if ($('#tab-filtros')?.classList.contains('active')) renderFiltersPage();
}

/* ---------- MODAL ---------- */
function openModal(v) {
  const embed = embedURL(v.instagram_url);
  const videoSide = v.src
    ? `<video controls autoplay playsinline preload="metadata" poster="${v.thumb||''}"><source src="${v.src}" type="video/mp4"></video>`
    : embed
      ? `<iframe class="modal-embed" src="${embed}" loading="lazy" allowfullscreen allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"></iframe>`
      : `<div class="placeholder-msg"><p style="font-size:3rem;margin-bottom:1rem;">▶</p><p>Abra o original para assistir.</p></div>`;

  const metaItems = [
    v.post_author || v.channel ? ['Perfil', v.post_author || v.channel] : null,
    v.duration_string ? ['Duracao', v.duration_string] : null,
    v.published_at ? ['Publicado', v.published_at] : null,
    v.views ? ['Visualizacoes', formatNum(v.views)] : null,
    v.likes ? ['Curtidas', formatNum(v.likes)] : null,
    v.comments ? ['Comentarios', formatNum(v.comments)] : null
  ].filter(Boolean);

  const metaBlock = metaItems.length ? `
    <div class="modal-data-grid">
      ${metaItems.map(([k,val]) => `<div><span>${k}</span><strong>${escapeHtml(val)}</strong></div>`).join('')}
    </div>` : '';

  const process = v.category === 'youtube'
    ? ['Estrutura de narrativa', 'Corte de respiros e repeticoes', 'Tratamento de audio', 'Ritmo para manter retencao']
    : v.category === 'live'
      ? ['Curadoria dos melhores momentos da live', 'Corte para clareza e impacto', 'Legenda e ritmo para Reels', 'Finalizacao para publicacao']
      : v.category === 'podcast'
        ? ['Selecao do trecho com maior potencial', 'Corte de pausas', 'Legendas e enfase visual', 'Finalizacao vertical']
        : ['Analise do material', 'Corte com foco em retencao', 'Ritmo, som e acabamento', 'Entrega pronta para publicar'];

  const caption = v.caption ? `<p class="modal-caption">${escapeHtml(v.caption).slice(0, 260)}${v.caption.length > 260 ? '...' : ''}</p>` : '';
  const waMsg = `Ola Jose! Vi o video "${v.title}" no seu portfolio e quero videos assim. Me passa um orcamento?`;

  const modal = document.createElement('div');
  modal.className = 'modal';
  modal.innerHTML = `
    <div class="modal-burst"></div>
    <button class="modal-close" aria-label="Fechar">×</button>
    <div class="modal-box">
      <div class="modal-video-side">${videoSide}</div>
      <div class="modal-info-side">
        <h2>${v.title || 'Sem titulo'}</h2>
        ${metaBlock}
        ${caption}
        <div class="modal-section compact">
          <h4>Como esse video foi trabalhado</h4>
          <ul>${process.map(p => `<li>${p}</li>`).join('')}</ul>
        </div>
        <div class="modal-actions">
          <a class="btn-cta btn-wa" href="${waLink(waMsg)}" target="_blank" rel="noopener">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M20.5 3.5A11.5 11.5 0 0 0 3.6 19l-1.6 5.5 5.6-1.5a11.5 11.5 0 0 0 17.4-9.7 11.4 11.4 0 0 0-4.5-9.8zm-8.5 18a9.5 9.5 0 0 1-4.8-1.3l-.3-.2-3.3.9.9-3.2-.2-.3a9.5 9.5 0 1 1 7.7 4.1zm5.4-7.1c-.3-.2-1.7-.8-2-.9-.3-.1-.5-.2-.7.2-.2.3-.8.9-1 1.1-.2.2-.4.2-.7.1-.3-.2-1.3-.5-2.4-1.5-.9-.8-1.5-1.8-1.7-2.1-.2-.3 0-.5.1-.6l.5-.6.3-.5c0-.2 0-.4-.1-.5L9 6.7c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.5 0-.7.3-.2.3-1 .9-1 2.3s1 2.7 1.2 2.9c.2.3 2 3 4.8 4.2 2.8 1.2 2.8.8 3.3.7.5 0 1.7-.7 2-1.4.3-.7.3-1.2.2-1.4-.1-.1-.3-.2-.6-.4z"/></svg>
            Quero videos assim
          </a>
          ${v.instagram_url ? `<a class="btn-cta btn-ig" href="${v.instagram_url}" target="_blank" rel="noopener">Ver original →</a>` : ''}
        </div>
      </div>
    </div>`;

  document.body.appendChild(modal);
  document.body.style.overflow = 'hidden';

  const close = () => {
    modal.style.opacity = '0';
    setTimeout(() => { modal.remove(); document.body.style.overflow=''; }, 300);
  };
  $('.modal-close', modal).addEventListener('click', close);
  modal.addEventListener('click', (e) => { if (e.target === modal) close(); });
  document.addEventListener('keydown', function esc(e) {
    if (e.key === 'Escape') { close(); document.removeEventListener('keydown', esc); }
  });
}

/* ---------- OTHER WORKS (courses / motion / flyers) ---------- */
function renderOtherWorks() {
  const sections = [
    { key: 'courses', selector: '#courses-grid', label: 'cursos editados',
      msg: 'Editei cursos completos pra criadores. Os exemplos estão sendo montados aqui — quer ver os trabalhos diretos?' },
    { key: 'motion',  selector: '#motion-grid',  label: 'peças de motion',
      msg: 'Aberturas, vinhetas, animações tipográficas. Tenho um portfólio offline — bora ver?' },
    { key: 'flyers',  selector: '#flyers-grid',  label: 'flyers',
      msg: 'Designs de flyers e artes pra evento. Posso te mandar o que tenho separado.' }
  ];
  sections.forEach(({key, selector, label, msg}) => {
    const grid = $(selector);
    if (!grid) return;
    const items = STATE[key];
    if (!items || items.length === 0) {
      const wa = waLink(`Olá José! Vi seu portfólio e quero ver os ${label} que você fez. Pode me mostrar?`);
      grid.innerHTML = `
        <div class="empty-cta-card" style="grid-column:1/-1;">
          <div class="empty-icon">${key==='courses'?'📚':key==='motion'?'🎨':'📢'}</div>
          <div class="empty-msg">${msg}</div>
          <a class="btn-cta btn-wa" href="${wa}" target="_blank" rel="noopener">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M20.5 3.5A11.5 11.5 0 0 0 3.6 19l-1.6 5.5 5.6-1.5a11.5 11.5 0 0 0 17.4-9.7 11.4 11.4 0 0 0-4.5-9.8z"/></svg>
            Quero ver no WhatsApp
          </a>
        </div>`;
      return;
    }
    grid.innerHTML = items.map(item => `
      <div class="video-card" data-cat="${key}">
        ${item.thumb ? `<img class="video-poster" src="${item.thumb}" alt="${item.title}">` : `<div class="video-poster placeholder">📁</div>`}
        <div class="play-overlay">
          <div class="video-meta">
            <div class="video-title">${item.title}</div>
            ${item.client ? `<div class="video-expert"><span>${item.client}</span></div>` : ''}
          </div>
        </div>
      </div>`).join('');
  });
}

function renderYoutubeVideos() {
  const grid = $('#youtubeGrid');
  if (!grid) return;
  const list = STATE.videos.filter(v => v.category === 'youtube');
  grid.innerHTML = list.length
    ? list.map(videoCard).join('')
    : '<div class="empty-state" style="grid-column:1/-1;"><strong>Videos longos ainda serao adicionados aqui.</strong></div>';
  $$('.video-card', grid).forEach(card => {
    const v = list.find(x => x.id === card.dataset.id);
    card.addEventListener('click', () => openModal(v));
  });
}

/* ---------- BUDGET CALCULATOR (refatorado: 2 formatos + refs + briefing) ---------- */
STATE.budget = { format: 'reel', longType: 'youtube', qty: 8, style: 'medio', styleMix: null, refs: [], recorded: null, deadline: '' };

function budgetMode() {
  if (STATE.budget.format === 'longform') return STATE.budget.longType || 'youtube';
  return STATE.budget.format || 'reel';
}

function budgetMoodCopy(mode) {
  const map = {
    reel: ['9:16', 'Reels em volume.', 'Escolha quantidade, estilo e referencias. Aqui o orcamento sai na hora.', 'Pipeline rapido para Reels, Shorts e TikTok.'],
    youtube: ['16:9', 'YouTube 16:9.', 'Videos longos com narrativa, tratamento de audio e ritmo de retencao.', 'Ideal para canal, aulas abertas e conteudo horizontal recorrente.'],
    vsl: ['VSL', 'Briefing de VSL.', 'VSL muda por oferta, referencia e nivel de motion. Me envie o contexto antes do preco.', 'Preciso entender oferta, referencia e material bruto.'],
    curso: ['Curso', 'Curso sob medida.', 'Curso depende de horas gravadas, modulos, padrao visual e revisoes.', 'Melhor resolver pelo WhatsApp com escopo completo.'],
    motion: ['AE', 'Motion design.', 'Vinhetas, letterings, aberturas e pecas em After Effects precisam de briefing.', 'O preco varia por duracao, complexidade e prazo.']
  };
  const v = map[mode] || map.reel;
  return { badge: v[0], title: v[1], sub: v[2], note: v[3] };
}

function quoteFormHTML(mode, title, description) {
  const fields = {
    vsl: [['Objetivo da oferta', 'Ex: vender mentoria, produto, evento...'], ['Referencia principal', 'Cole link ou descreva o estilo'], ['Material bruto', 'Ex: video gravado, roteiro, criativos...']],
    curso: [['Horas gravadas', 'Ex: 8 aulas de 30 minutos'], ['Formato de entrega', 'Ex: modulos, plataforma, cortes extras'], ['Padrao visual', 'Ex: simples, identidade pronta, motion...']],
    motion: [['Tipo de peca', 'Ex: abertura, lettering, vinheta, VFX'], ['Duracao estimada', 'Ex: 8s, 30s, pacote mensal'], ['Referencia visual', 'Cole link ou descreva o estilo']]
  }[mode] || [];
  return `
    <div class="quote-note quote-note-${mode}">
      <span class="quote-kicker">${budgetMoodCopy(mode).badge}</span>
      <strong>${title}</strong>
      <p>${description}</p>
      <div class="quote-mini-form" data-quote-mode="${mode}">
        ${fields.map(([label, placeholder]) => `
          <label>
            <span>${label}</span>
            <input class="quote-field" data-label="${label}" placeholder="${placeholder}">
          </label>`).join('')}
        <button class="btn-cta btn-wa quote-submit" type="button">Enviar briefing no WhatsApp</button>
      </div>
    </div>`;
}

function wireQuoteForm(mode) {
  const box = $('.quote-mini-form');
  const btn = $('.quote-submit');
  if (!box || !btn) return;
  btn.addEventListener('click', () => {
    const label = mode === 'vsl' ? 'uma VSL' : mode === 'curso' ? 'um curso' : 'motion design';
    const lines = [`Ola Jose! Quero orcar ${label}.`, ''];
    $$('.quote-field', box).forEach(input => {
      if (input.value.trim()) lines.push(`*${input.dataset.label}:* ${input.value.trim()}`);
    });
    if (STATE.budget.refs.length) {
      lines.push('', '*Referencias escolhidas:*');
      STATE.budget.refs.forEach((r, i) => lines.push(`${i + 1}. ${r.title} - ${r.url}`));
    }
    location.href = waLink(lines.join('\n'));
  });
}

function roundMoney(n) {
  return Math.round(n / 10) * 10;
}

function unitPrice(formatId, qty, styleId = STATE.budget.style) {
  const cfg = STATE.config?.budget;
  const fmt = cfg?.formats?.find(f => f.id === formatId);
  if (!cfg || !fmt || !fmt.tiers?.length) return 0;
  const tier = fmt.tiers.find(t => qty >= t.min && qty <= t.max) || fmt.tiers[fmt.tiers.length - 1];
  return Math.round((tier.price || 0) * (cfg.style_multipliers[styleId] ?? 1));
}

function normalizeStyleMix() {
  const qty = Math.max(1, STATE.budget.qty || 1);
  const styles = STATE.config?.edit_levels?.map(l => l.id) || ['simples', 'medio', 'avancado'];
  if (!STATE.budget.styleMix) {
    STATE.budget.styleMix = Object.fromEntries(styles.map(id => [id, id === STATE.budget.style ? qty : 0]));
    return STATE.budget.styleMix;
  }
  styles.forEach(id => { if (!Number.isFinite(STATE.budget.styleMix[id])) STATE.budget.styleMix[id] = 0; });
  const total = styles.reduce((sum, id) => sum + (parseInt(STATE.budget.styleMix[id], 10) || 0), 0);
  if (total !== qty) {
    STATE.budget.styleMix = Object.fromEntries(styles.map(id => [id, id === STATE.budget.style ? qty : 0]));
  }
  return STATE.budget.styleMix;
}

function styleMixSummary() {
  const mix = normalizeStyleMix();
  return (STATE.config?.edit_levels || [])
    .map(l => ({ label: l.label, id: l.id, qty: parseInt(mix[l.id], 10) || 0 }))
    .filter(x => x.qty > 0)
    .map(x => `${x.qty} ${x.label.toLowerCase()}`)
    .join(' + ');
}

function currentBudgetTotals() {
  const formatId = STATE.budget.format === 'longform' ? 'longform' : 'reel';
  const mix = normalizeStyleMix();
  const lines = (STATE.config?.edit_levels || []).map(level => {
    const qty = parseInt(mix[level.id], 10) || 0;
    const unit = unitPrice(formatId, STATE.budget.qty, level.id);
    return { id: level.id, label: level.label, qty, unit, total: qty * unit };
  }).filter(x => x.qty > 0);
  return {
    lines,
    total: lines.reduce((sum, x) => sum + x.total, 0)
  };
}

function monthlyRecommendationsHTML() {
  const qty = STATE.budget.qty;
  const budgetCfg = STATE.config?.budget || {};
  const minMonthly = parseInt(budgetCfg.monthly_min_videos, 10) || 8;
  const discount = Math.max(0, Math.min(90, parseFloat(budgetCfg.monthly_discount_percent) || 20));
  const benefits = Array.isArray(budgetCfg.monthly_benefits) && budgetCfg.monthly_benefits.length
    ? budgetCfg.monthly_benefits
    : ['Capinhas conforme o nivel do pacote', 'Organizacao mensal e prioridade na fila', 'Revisoes inclusas dentro do escopo'];
  const coupon = budgetCfg.coupon || {};
  const couponActive = coupon.active && (parseFloat(coupon.percent) || 0) > 0;
  const couponPercent = Math.max(0, Math.min(90, parseFloat(coupon.percent) || 0));
  const couponCode = (coupon.code || 'CUPOM').trim();
  const canAutoMonthly = (STATE.budget.format === 'reel') || (STATE.budget.format === 'longform' && STATE.budget.longType === 'youtube');
  const totals = currentBudgetTotals();
  const avulso = totals.total;
  const mensalBase = roundMoney(avulso * (1 - discount / 100));
  const mensal = couponActive ? roundMoney(mensalBase * (1 - couponPercent / 100)) : mensalBase;
  const summary = styleMixSummary();

  const consultation = `
    <div class="plan-card consultation-card">
      <span class="plan-badge">Sempre</span>
      <div class="nm">Sob consulta</div>
      <div class="pr">
        <span class="num">Sob consulta</span>
        <span class="per">projeto fora do padrao</span>
      </div>
      <div class="plan-saving">Cursos, VSL, motion pesado, prazos urgentes ou pacote com varios formatos.</div>
      <ul>
        <li>Analiso escopo, referencia e material bruto</li>
        <li>Serve para empresa que precisa de tudo junto</li>
        <li>Negociacao direta pelo WhatsApp</li>
      </ul>
      <a class="plan-cta" href="${waLink('Ola Jose! Quero montar um plano sob consulta com varios tipos de video. Pode me ajudar?')}" target="_blank">Montar sob consulta</a>
    </div>`;

  if (canAutoMonthly && qty >= minMonthly && avulso > 0) {
    const unitLabel = STATE.budget.format === 'reel' ? 'reels' : 'videos 16:9';
    return `
      <div class="plan-card highlight">
        <span class="plan-badge">Recomendado</span>
        <div class="nm">Mensal recorrente</div>
        <div class="pr">
          <span class="num">R$${formatNum(mensal)}</span>
          <span class="per">/mes - ${qty} ${unitLabel}</span>
        </div>
        <div class="plan-saving">Avulso daria R$${formatNum(avulso)}. Mensal aplica ${discount}% de desconto em cima do total atual.${couponActive ? ` Cupom ${escapeHtml(couponCode)} aplica mais ${couponPercent}%.` : ''}</div>
        <ul>
          <li>${summary}</li>
          ${benefits.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
        </ul>
        <a class="plan-cta" href="${waLink(`Ola Jose! Quero fechar mensal recorrente com ${qty} ${unitLabel}: ${summary}. Avulso R$${formatNum(avulso)}, mensal com ${discount}% off R$${formatNum(mensal)}.`)}" target="_blank">Quero esse mensal</a>
      </div>${consultation}`;
  }

  return `
    <div class="plan-card plan-waiting">
      <div class="nm">Mensal a partir de ${minMonthly} videos</div>
      <div class="plan-saving">Quando chegar em ${minMonthly} videos, aparece automaticamente ${discount}% de desconto sobre o total atual.</div>
      <ul>
        <li>Voce pode misturar estilos de edicao</li>
        <li>O valor acompanha a quantidade e dificuldade selecionadas</li>
      </ul>
    </div>${consultation}`;
}

function setupBudget() {
  const root = $('#tab-orcamento');
  if (!root) return;
  const cfg = STATE.config?.budget;
  if (!cfg || !cfg.formats) return;
  const mode = budgetMode();
  const mood = budgetMoodCopy(mode);
  root.dataset.budgetMode = mode;

  const formatTabs = cfg.formats.map(f => `
    <button class="fmt-tab ${f.id===STATE.budget.format?'active':''}" data-fmt="${f.id}">
      <span class="ic">${f.icon}</span>
      <span class="lb">
        <strong>${f.label}</strong>
        <small>${f.subtitle}</small>
      </span>
    </button>`).join('');

  const stylesHTML = STATE.config.edit_levels.map(l => `
    <button class="style-option ${STATE.budget.style===l.id?'active':''}" data-style="${l.id}">
      <div class="nm" style="color:${l.color}">${l.label}</div>
      <div class="ds">${l.description}</div>
    </button>`).join('');

  normalizeStyleMix();
  const mixHTML = (STATE.config.edit_levels || []).map(l => `
    <label class="mix-row">
      <span>
        <strong>${l.label}</strong>
        <small>${l.description}</small>
      </span>
      <input class="mix-input" data-mix-style="${l.id}" type="number" min="0" max="${STATE.budget.qty}" value="${STATE.budget.styleMix[l.id] || 0}">
    </label>`).join('');

  const longTypesHTML = `
    <div class="long-type-picker" id="longTypePicker">
      <button class="long-type ${STATE.budget.longType === 'youtube' ? 'active' : ''}" data-long-type="youtube" type="button">
        <strong>YouTube</strong><span>Orcamento automatico</span>
      </button>
      <button class="long-type ${STATE.budget.longType === 'vsl' ? 'active' : ''}" data-long-type="vsl" type="button">
        <strong>VSL</strong><span>Precisa referencia</span>
      </button>
      <button class="long-type ${STATE.budget.longType === 'curso' ? 'active' : ''}" data-long-type="curso" type="button">
        <strong>Curso</strong><span>Negociacao direta</span>
      </button>
    </div>`;

  const plansHTML = monthlyRecommendationsHTML();

  root.innerHTML = `
    <h2 class="hero-headline">Orcamento<br>de edicao.</h2>
    <p class="hero-sub">Valores estimados para edicao de Reels, Shorts, YouTube, VSLs e cursos. O preco final pode variar conforme roteiro, material bruto e nivel de finalizacao.</p>

    <div class="fmt-toggle">${formatTabs}</div>
    ${longTypesHTML}

    <div class="budget-atmosphere budget-atmosphere-${mode}">
      <span>${mood.badge}</span>
      <strong>${mood.title}</strong>
      <p>${mood.note}</p>
    </div>

    <div class="budget-wrap">
      <div class="budget-calc">
        <h3 id="budgetTitle">${mood.title}</h3>
        <div class="sub" id="budgetSub">${mood.sub}</div>

        <div class="qty-control">
          <button class="qty-btn" id="qtyMinus" type="button">−</button>
          <div class="qty-display"><span id="qtyNum">${STATE.budget.qty}</span><small id="qtySmall">vídeos</small></div>
          <button class="qty-btn" id="qtyPlus" type="button">+</button>
        </div>
        <input type="range" min="1" max="60" value="${STATE.budget.qty}" class="qty-slider" id="qtySlider">

        <h4 class="mini-label">Estilo de edição</h4>
        <div class="style-picker">${stylesHTML}</div>
        <div class="style-mix-box">
          <div class="mix-head">
            <strong>Distribuicao por estilo</strong>
            <span id="mixTotalStatus"></span>
          </div>
          <div class="mix-grid">${mixHTML}</div>
        </div>

        <h4 class="mini-label">Referências <span class="opt">(opcional, mas ajuda)</span></h4>
        <div id="refList" class="ref-list"></div>
        <div class="ref-actions">
          <input type="url" id="refInput" placeholder="cola um link do Instagram aqui">
          <button class="ref-btn" id="addRefURL" type="button">+ Adicionar link</button>
          <button class="ref-btn alt" id="pickFromPort" type="button">📁 Do meu portfólio</button>
        </div>

        <h4 class="mini-label">Briefing rápido</h4>
        <div class="briefing-grid">
          <div class="bf-item">
            <span class="bf-q">Vídeo já gravado?</span>
            <div class="bf-pills">
              <button class="bf-pill" data-rec="yes" type="button">Sim, tá pronto</button>
              <button class="bf-pill" data-rec="partial" type="button">Algumas cenas</button>
              <button class="bf-pill" data-rec="no" type="button">Ainda não</button>
            </div>
          </div>
          <div class="bf-item">
            <span class="bf-q">Quando precisa pronto?</span>
            <input type="text" id="bfDeadline" placeholder="Ex: 'até sexta', '15/06', 'sem pressa'">
          </div>
        </div>

        <div class="price-out" id="priceOut"></div>
      </div>

      <div>
        <h3 class="section-title" style="margin-top:0;">Recomendacao mensal</h3>
        <p style="font-size:.88rem; color:var(--ink-2); margin-bottom:1.2rem;">So aparece plano quando o volume faz sentido. O desconto usa o valor real do formato e do estilo escolhido.</p>
        <div class="plans">${plansHTML}</div>
      </div>
    </div>

    <!-- Modal: pick reference from portfolio -->
    <div id="portRefModal" class="port-ref-modal hidden">
      <div class="port-ref-box">
        <button class="modal-close" id="portRefClose" type="button">✕</button>
        <h3>Escolha referências do meu portfólio</h3>
        <p class="sub">Click pra adicionar — você pode escolher várias.</p>
        <div id="portRefGrid" class="port-ref-grid"></div>
      </div>
    </div>
  `;

  // wiring
  const slider = $('#qtySlider');
  const num    = $('#qtyNum');
  const small  = $('#qtySmall');
  const refInput = $('#refInput');

  function currentFormat() {
    return cfg.formats.find(f => f.id === STATE.budget.format) || cfg.formats[0];
  }

  function update() {
    const fmt = currentFormat();
    const max = fmt.max || 60;
    slider.max = max;
    if (STATE.budget.qty > max) STATE.budget.qty = max;
    normalizeStyleMix();
    slider.value = STATE.budget.qty;
    num.textContent = STATE.budget.qty;
    small.textContent = STATE.budget.qty === 1 ? (fmt.id==='reel'?'reel':'vídeo') : (fmt.id==='reel'?'reels':'vídeos');
    slider.style.setProperty('--fill', (STATE.budget.qty / max * 100) + '%');
    updateMixStatus();
    refreshPrice();
  }

  function updateMixStatus() {
    const status = $('#mixTotalStatus');
    if (!status) return;
    const mix = normalizeStyleMix();
    const total = Object.values(mix).reduce((sum, n) => sum + (parseInt(n, 10) || 0), 0);
    status.textContent = `${total}/${STATE.budget.qty} videos`;
    status.classList.toggle('bad', total !== STATE.budget.qty);
  }

  function readMixInputs(changedInput = null) {
    const inputs = $$('.mix-input', root);
    const mix = {};
    inputs.forEach(input => {
      mix[input.dataset.mixStyle] = Math.max(0, parseInt(input.value, 10) || 0);
    });
    let total = Object.values(mix).reduce((sum, n) => sum + n, 0);
    if (changedInput && total > STATE.budget.qty) {
      let overflow = total - STATE.budget.qty;
      const others = inputs.filter(input => input !== changedInput).reverse();
      for (const input of others) {
        const id = input.dataset.mixStyle;
        const take = Math.min(mix[id], overflow);
        mix[id] -= take;
        input.value = mix[id];
        overflow -= take;
        if (overflow <= 0) break;
      }
      if (overflow > 0) {
        const id = changedInput.dataset.mixStyle;
        mix[id] = Math.max(0, mix[id] - overflow);
        changedInput.value = mix[id];
      }
    } else if (changedInput && total < STATE.budget.qty) {
      const id = changedInput.dataset.mixStyle;
      mix[id] += STATE.budget.qty - total;
      changedInput.value = mix[id];
    }
    STATE.budget.styleMix = mix;
    const main = Object.entries(mix).sort((a,b) => b[1] - a[1])[0];
    if (main?.[0]) STATE.budget.style = main[0];
    $$('.style-option', root).forEach(x => x.classList.toggle('active', x.dataset.style === STATE.budget.style));
    updateMixStatus();
    refreshPrice();
    const planWrap = $('.plans', root);
    if (planWrap) planWrap.innerHTML = monthlyRecommendationsHTML();
  }

  slider.addEventListener('input', () => { STATE.budget.qty = parseInt(slider.value,10); STATE.budget.styleMix = null; setupBudget(); });
  $('#qtyMinus').addEventListener('click', () => { STATE.budget.qty = Math.max(1, STATE.budget.qty - 1); STATE.budget.styleMix = null; setupBudget(); });
  $('#qtyPlus').addEventListener('click',  () => {
    const max = currentFormat().max || 60;
    STATE.budget.qty = Math.min(max, STATE.budget.qty + 1); STATE.budget.styleMix = null; setupBudget();
  });

  $$('.fmt-tab', root).forEach(b => {
    b.addEventListener('click', () => {
      STATE.budget.format = b.dataset.fmt;
      $$('.fmt-tab', root).forEach(x => x.classList.toggle('active', x === b));
      $('#longTypePicker')?.classList.toggle('show', STATE.budget.format === 'longform');
      setupBudget();
      if (window.bearMood) window.bearMood('excited');
      return;
    });
  });

  $$('.long-type', root).forEach(b => {
    b.addEventListener('click', () => {
      STATE.budget.longType = b.dataset.longType;
      $$('.long-type', root).forEach(x => x.classList.toggle('active', x === b));
      setupBudget();
    });
  });
  $('#longTypePicker')?.classList.toggle('show', STATE.budget.format === 'longform');

  $$('.style-option', root).forEach(b => {
    b.addEventListener('click', () => {
      STATE.budget.style = b.dataset.style;
      STATE.budget.styleMix = null;
      setupBudget();
    });
  });

  $$('.mix-input', root).forEach(input => {
    input.addEventListener('input', () => readMixInputs(input));
  });

  // References
  function renderRefs() {
    const list = $('#refList');
    if (!list) return;
    if (!STATE.budget.refs.length) {
      list.innerHTML = `<div class="ref-empty">Sem referência ainda. Adicione um link ou escolha do meu portfólio.</div>`;
      return;
    }
    list.innerHTML = STATE.budget.refs.map((r,i) => `
      <div class="ref-item">
        ${r.thumb ? `<img src="${r.thumb}" alt="">` : `<div class="ref-thumb">🔗</div>`}
        <div class="ref-info">
          <div class="ref-title">${escapeHtml(r.title || 'Referência')}</div>
          <a class="ref-link" href="${r.url}" target="_blank" rel="noopener">${r.url.length > 38 ? r.url.slice(0,38)+'…' : r.url}</a>
        </div>
        <button class="ref-x" data-rm="${i}" type="button" aria-label="Remover">✕</button>
      </div>`).join('');
    $$('[data-rm]', list).forEach(b => b.addEventListener('click', () => {
      STATE.budget.refs.splice(parseInt(b.dataset.rm,10), 1);
      renderRefs();
      refreshPrice();
    }));
  }
  renderRefs();

  $('#addRefURL').addEventListener('click', () => {
    const url = (refInput.value || '').trim();
    if (!url || !/^https?:\/\//.test(url)) {
      refInput.focus();
      refInput.style.borderColor = '#ff6b6b';
      setTimeout(()=> refInput.style.borderColor = '', 1200);
      return;
    }
    STATE.budget.refs.push({ url, title: 'Link externo', thumb: null });
    refInput.value = '';
    renderRefs();
    refreshPrice();
    if (window.bearMood) window.bearMood('happy');
  });

  refInput.addEventListener('keydown', e => { if (e.key === 'Enter') $('#addRefURL').click(); });

  // Pick from portfolio
  const portModal = $('#portRefModal');
  $('#pickFromPort').addEventListener('click', () => {
    const grid = $('#portRefGrid');
    grid.innerHTML = STATE.videos
      .filter(v => v.category === 'youtube' || v.thumb || v.src || v.instagram_url)
      .map(v => `
      <div class="port-ref-card" data-id="${v.id}">
        ${v.thumb ? `<img src="${v.thumb}" alt="${v.title}">` : '<div class="ref-thumb">🎬</div>'}
        <div class="port-ref-title">${escapeHtml(v.title)}</div>
      </div>`).join('') || '<div class="empty-state">Sem vídeos pra escolher ainda.</div>';
    portModal.classList.remove('hidden');
    $$('.port-ref-card', grid).forEach(c => c.addEventListener('click', () => {
      const v = STATE.videos.find(x => x.id === c.dataset.id);
      if (!v) return;
      const already = STATE.budget.refs.some(r => r.url === v.instagram_url);
      if (!already) STATE.budget.refs.push({
        url: v.instagram_url || `#${v.id}`,
        title: v.title,
        thumb: v.thumb
      });
      renderRefs();
      refreshPrice();
      portModal.classList.add('hidden');
      if (window.bearMood) window.bearMood('happy');
    }));
  });
  $('#portRefClose').addEventListener('click', () => portModal.classList.add('hidden'));
  portModal.addEventListener('click', e => { if (e.target === portModal) portModal.classList.add('hidden'); });

  // Briefing pills
  $$('.bf-pill', root).forEach(p => {
    p.addEventListener('click', () => {
      $$('.bf-pill', root).forEach(x => x.classList.remove('active'));
      p.classList.add('active');
      STATE.budget.recorded = p.dataset.rec;
      refreshPrice();
    });
  });
  $('#bfDeadline').addEventListener('input', e => {
    STATE.budget.deadline = e.target.value;
    refreshPrice();
  });

  update();
}

function refreshPrice() {
  const cfg = STATE.config?.budget;
  if (!cfg || !cfg.formats) return;
  const minMonthly = parseInt(cfg.monthly_min_videos, 10) || 8;
  const discount = Math.max(0, Math.min(90, parseFloat(cfg.monthly_discount_percent) || 20));
  const coupon = cfg.coupon || {};
  const couponActive = coupon.active && (parseFloat(coupon.percent) || 0) > 0;
  const couponPercent = Math.max(0, Math.min(90, parseFloat(coupon.percent) || 0));
  const couponCode = (coupon.code || 'CUPOM').trim();
  const fmt = cfg.formats.find(f => f.id === STATE.budget.format) || cfg.formats[0];
  const qty = STATE.budget.qty;

  if (fmt.id === 'motion') {
    $('#priceOut').innerHTML = `
      ${quoteFormHTML('motion', 'Motion design precisa de briefing.', 'Vinheta, abertura, lettering animado, VFX e animacoes variam por duracao e complexidade. Preencha o basico e me chama com uma referencia.')}
    `;
    wireQuoteForm('motion');
    return;
  }
  const tier = fmt.tiers.find(t => qty >= t.min && qty <= t.max) || fmt.tiers[fmt.tiers.length-1];
  const totals = currentBudgetTotals();
  const total = totals.total;
  const couponTotal = couponActive ? roundMoney(total * (1 - couponPercent / 100)) : null;

  if (fmt.id === 'longform' && STATE.budget.longType === 'curso') {
    $('#priceOut').innerHTML = `
      ${quoteFormHTML('curso', 'Curso precisa de negociacao personalizada.', 'Aulas, modulos, duracao total, captacao, padrao visual e revisoes mudam muito o escopo. Preencha o basico e eu avalio certinho.')}
    `;
    wireQuoteForm('curso');
    return;
  }

  if (fmt.id === 'longform' && STATE.budget.longType === 'vsl') {
    $('#priceOut').innerHTML = `
      ${quoteFormHTML('vsl', 'VSL depende da referencia antes do preco.', 'Preciso ver objetivo da oferta, material bruto, referencia e nivel de motion/copy visual. Depois disso te retorno com o valor correto.')}
    `;
    wireQuoteForm('vsl');
    return;
  }

  // Build full briefing message
  const lines = [
    `Olá José! Quero fechar com você.`,
    ``,
    `📐 *Formato:* ${fmt.label}`,
    `🎬 *Quantidade:* ${qty} ${fmt.id==='reel'?'reels':'vídeos'}`,
    `🎨 *Distribuicao:* ${styleMixSummary()}`,
    `💰 *Investimento estimado:* R$${formatNum(total)}`,
  ];
  const recMap = { yes: '✅ Sim, vídeo já gravado', partial: '🟡 Algumas cenas prontas', no: '⏳ Ainda não gravei' };
  if (STATE.budget.recorded) lines.push(`📹 *Status do material:* ${recMap[STATE.budget.recorded]}`);
  if (STATE.budget.deadline) lines.push(`⏱️ *Prazo desejado:* ${STATE.budget.deadline}`);
  if (STATE.budget.refs.length) {
    lines.push(``, `🔗 *Referências (${STATE.budget.refs.length}):*`);
    STATE.budget.refs.forEach((r,i) => lines.push(`${i+1}. ${r.title} — ${r.url}`));
  }
  lines.push(``, `Confere se faz sentido pra mim e me dá um retorno! 🐻`);
  const waMsg = lines.join('\n');

  $('#priceOut').innerHTML = `
    <span class="price-tier-badge">${tier.label}</span>
    ${totals.lines.map(line => `<div class="row"><span>${line.qty} ${line.label} x R$${line.unit}</span><span class="v">R$${formatNum(line.total)}</span></div>`).join('')}
    <div class="row total"><span>Total estimado</span><span class="v">R$${formatNum(total)}</span></div>
    ${couponActive ? `<div class="coupon-row">Cupom ${escapeHtml(couponCode)}: ${couponPercent}% off fica R$${formatNum(couponTotal)}</div>` : ''}
    ${qty >= minMonthly ? `
      <div class="monthly-cta">
        Mensal recorrente com <strong>${discount}% de desconto</strong>: R$${formatNum(roundMoney((couponTotal || total) * (1 - discount / 100)))}/mes.
      </div>` : ''}
    <a class="btn-cta btn-wa" id="bookCTA" style="display:flex;width:100%;margin-top:1rem;" href="${waLink(waMsg)}" target="_blank" rel="noopener">
      Mandar briefing pro WhatsApp
    </a>
  `;
}

function escapeHtml(s) { return String(s||'').replace(/[<>&"]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;'}[c])); }

/* ---------- SOBRE PAGE ---------- */
function renderSobre() {
  const root = $('#tab-sobre');
  if (!root) return;
  const cfg = STATE.config.site;
  const me  = expertById('jose-victor');
  const others = STATE.experts.filter(e => !e.is_owner);
  const totalExperts = others.length;

  // Duplica experts pra carrossel infinito visual
  const carouselExperts = [...others, ...others];

  root.innerHTML = `
    <div class="sobre-grid">
      <div class="sobre-text">
        <h2>Editor de video<br>para conteudo de alta retencao.</h2>
        <p>Sou Jose Victor, editor com 3 anos de experiencia em Reels, Shorts, YouTube, VSLs, cursos e conteudos comerciais.</p>
        <p>Trabalho com Adobe Premiere, After Effects e outros programas de edicao pesada para entregar ritmo, clareza, som tratado e acabamento profissional.</p>
        <p><strong>Resultados:</strong> +1.000 videos editados por mim, +10 milhoes de visualizacoes geradas e +20 experts/marcas atendidos.</p>
      </div>
      <div class="sobre-photo">
        ${me?.photo ? `<img src="${me.photo}" alt="${me.name}" loading="lazy">` : '<div style="display:grid;place-items:center;height:100%;font-size:5rem;">JV</div>'}
      </div>
    </div>

    <div class="offerings">
      <div class="offer-card">
        <div class="icon">9:16</div>
        <h4>Reels & Shorts</h4>
        <p>Edicao vertical com cortes precisos, legenda, ritmo, sound design e acabamento para retencao.</p>
      </div>
      <div class="offer-card">
        <div class="icon">16:9</div>
        <h4>YouTube, VSL e cursos</h4>
        <p>Videos longos com narrativa, limpeza de pausas, audio tratado, ritmo e estrutura profissional.</p>
      </div>
      <div class="offer-card">
        <div class="icon">AE</div>
        <h4>Ferramentas profissionais</h4>
        <p>Premiere, After Effects, plugins, organizacao de projeto e finalizacao para cada plataforma.</p>
      </div>
      <div class="offer-card">
        <div class="icon">OK</div>
        <h4>Processo claro</h4>
        <p>Briefing, curadoria, edicao, revisao e entrega pronta para publicar.</p>
      </div>
    </div>

    <h3 class="section-title">+20 experts e marcas atendidos</h3>
    <p style="color:var(--ink-2); margin-bottom:1rem; font-size:.95rem;">
      Projetos para criadores, marcas, instituicoes e profissionais que precisam de conteudo bem editado.
    </p>
    <div class="experts-carousel">
      <div class="experts-track">
        ${carouselExperts.map(e => `
          <div class="expert-tile" onclick="${e.instagram_url?`window.open('${e.instagram_url}','_blank')`:''}">
            <div class="photo"><img src="${e.photo}" alt="${e.name}" loading="lazy"></div>
            <div class="name">${escapeHtml(e.name)}</div>
          </div>`).join('')}
      </div>
    </div>

    <div class="professional-cta">
      <h3>Precisa de um editor para manter constancia?</h3>
      <p>Me chama no WhatsApp com o tipo de video, quantidade e referencia. Eu avalio o material e te passo o melhor caminho.</p>
      <div style="display:flex; gap:.8rem; justify-content:center; flex-wrap:wrap;">
        <a class="btn-cta btn-wa" href="${waLink('Ola Jose! Vi seu portfolio e quero conversar sobre edicao de video.')}" target="_blank">
          ${cfg.whatsapp}
        </a>
        <a class="btn-cta btn-ig" href="${cfg.owner_instagram_url}" target="_blank">${cfg.owner_instagram}</a>
      </div>
    </div>
  `;
}

/* ---------- BEAR ---------- */
const BEAR_PHRASES = [
  'Bora fechar? 💰',
  'Quer um vídeo viral? 🎬',
  'Esse aqui rasgou! 🔥',
  'Pode me chamar 🐻',
  'Tô aqui se precisar ✨',
  'Quer ver o orçamento?',
  'Roça aí no slider!'
];
function bearSay(text) {
  const b = $('.bear-bubble');
  if (!b) return;
  b.textContent = text;
  b.classList.add('show');
}
function bearHide() { $('.bear-bubble')?.classList.remove('show'); }

function setupBear() {
  let idle;
  const reset = () => {
    clearTimeout(idle);
    idle = setTimeout(() => {
      const txt = BEAR_PHRASES[Math.floor(Math.random()*BEAR_PHRASES.length)];
      bearSay(txt);
      setTimeout(bearHide, 3000);
    }, 18000);
  };
  ['mousemove','click','scroll','keydown'].forEach(ev => document.addEventListener(ev, reset));
  reset();

  // Hover greet
  $('.bear-companion')?.addEventListener('mouseenter', () => {
    $('.bear-companion')?.classList.remove('playful');
    const phrases = ['Oi!','To aqui!','Bora ver os videos?','Clique em mim para dormir'];
    bearSay(phrases[Math.floor(Math.random()*phrases.length)]);
  });
  $('.bear-companion')?.addEventListener('mouseleave', () => {
    setTimeout(bearHide, 1500);
    setTimeout(() => $('.bear-companion')?.classList.add('playful'), 1800);
  });

  // Click -> sleep/wake. WhatsApp fica no botao verde, para o urso virar personagem.
  $('.bear-companion')?.addEventListener('click', () => {
    const bear = $('.bear-companion');
    const sleeping = bear.classList.toggle('sleeping');
    bear.classList.toggle('playful', !sleeping);
    bearSay(sleeping ? 'Zzz...' : 'Acordei!');
    setTimeout(bearHide, 1800);
  });

  setInterval(() => {
    const bear = $('.bear-companion');
    if (!bear || bear.classList.contains('hidden') || bear.classList.contains('sleeping')) return;
    const moods = ['bear-hop', 'bear-look', 'bear-wave'];
    const mood = moods[Math.floor(Math.random() * moods.length)];
    bear.classList.add(mood);
    if (Math.random() > .55) {
      const txt = BEAR_PHRASES[Math.floor(Math.random() * BEAR_PHRASES.length)];
      bearSay(txt);
      setTimeout(bearHide, 1800);
    }
    setTimeout(() => bear.classList.remove(mood), 1200);
  }, 6500);
}

/* ---------- HEADER CONTACT ---------- */
function renderHeaderContact() {
  const cfg = STATE.config?.site;
  if (!cfg) return;
  $('#headerIG')?.setAttribute('href', cfg.owner_instagram_url);
  $('#headerIG').textContent = cfg.owner_instagram;
  $('#waFAB')?.setAttribute('href', waLink('Olá José! Vim do seu portfólio.'));
  $('#footerWA')?.setAttribute('href', waLink('Olá José! Vim do seu portfólio.'));
  $('#footerIG')?.setAttribute('href', cfg.owner_instagram_url);
  $('#footerWANum').textContent = cfg.whatsapp;
}

/* ---------- BOOT ---------- */
async function boot() {
  await loadAllData();
  setupPortal();
  setupTabs();
  renderHeaderContact();
  renderFilterChips();
  renderVideos();
  renderYoutubeVideos();
  renderOtherWorks();
  setupBudget();
  renderFiltersPage();
  renderFilterResults();
  renderSobre();
  setupBear();

  // hash deep link
  if (location.hash) {
    const tab = location.hash.slice(1);
    $(`.tabs button[data-tab="${tab}"]`)?.click();
  }
}

// expose globals for effects.js
window.STATE = STATE;
window.bearSay = bearSay;
window.bearHide = bearHide;

document.addEventListener('DOMContentLoaded', boot);
