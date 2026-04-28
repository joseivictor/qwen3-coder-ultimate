/* ============================================================
   ADMIN PANEL — JOSÉ VICTOR PORTFOLIO
   ============================================================ */

const $  = (s, r=document) => r.querySelector(s);
const $$ = (s, r=document) => Array.from(r.querySelectorAll(s));

const STATE = {
  authed: false,
  staticMode: false,
  config:  null,
  experts: [],
  videos:  [],
  courses: [],
  motion:  [],
  flyers:  [],
  editing: null  // current item being edited
};

/* ---------- API ---------- */
async function api(method, path, body) {
  const opts = { method, credentials: 'include', headers: {} };
  if (body && !(body instanceof FormData)) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  } else if (body instanceof FormData) {
    opts.body = body;
  }
  const r = await fetch(path, opts);
  let data; try { data = await r.json(); } catch { data = {}; }
  if (!r.ok) throw new Error(data.error || `HTTP ${r.status}`);
  return data;
}

function canUseStaticAdmin() {
  return true;
}

function applyLocalDraft(key, data) {
  const draft = localStorage.getItem('jv_admin_' + key);
  if (!draft) return data;
  try { return JSON.parse(draft); } catch { return data; }
}

function staticBanner() {
  if (!STATE.staticMode || $('#staticAdminBanner')) return;
  const div = document.createElement('div');
  div.id = 'staticAdminBanner';
  div.className = 'static-admin-banner';
  div.innerHTML = `
    <strong>Admin no Vercel em modo celular/rascunho.</strong>
    <span>As edicoes aparecem no painel e no preview com ?draft=1. Para publicar para todo mundo, precisa conectar Supabase, Vercel Blob ou GitHub.</span>
    <button class="chip" id="exportDraftBtn" type="button">Exportar backup</button>
    <a class="chip" href="/?draft=1" target="_blank">Preview rascunho</a>
  `;
  $('#adminApp').prepend(div);
  $('#exportDraftBtn').addEventListener('click', exportDrafts);
}

function exportDrafts() {
  const payload = {};
  ['config','experts','videos','courses','motion','flyers'].forEach(k => {
    const v = localStorage.getItem('jv_admin_' + k);
    if (v) payload[k] = JSON.parse(v);
  });
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'jv-portfolio-backup.json';
  a.click();
  URL.revokeObjectURL(a.href);
}

/* ---------- TOAST ---------- */
function toast(msg, type='') {
  const t = $('#toast');
  t.className = 'toast ' + type;
  t.textContent = msg;
  t.classList.remove('hidden');
  clearTimeout(toast._tm);
  toast._tm = setTimeout(() => t.classList.add('hidden'), 3500);
}

/* ---------- LOGIN ---------- */
$('#loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const pw = $('#adminPw').value;
  try {
    await api('POST', '/api/login', { password: pw });
    STATE.authed = true;
    $('#adminLogin').classList.add('hidden');
    $('#adminApp').classList.remove('hidden');
    bootAdmin();
  } catch (err) {
    if (canUseStaticAdmin() && pw === (localStorage.getItem('jv_admin_pw') || 'joseivictor2026')) {
      STATE.authed = true;
      STATE.staticMode = true;
      $('#adminLogin').classList.add('hidden');
      $('#adminApp').classList.remove('hidden');
      bootAdmin();
    } else {
      $('#loginErr').style.display = 'block';
      $('#loginErr').textContent = err.message;
    }
  }
});

$('#logoutBtn').addEventListener('click', async () => {
  await api('POST', '/api/logout');
  location.reload();
});

/* ---------- TABS ---------- */
$$('.admin-tabs button').forEach(btn => {
  btn.addEventListener('click', () => {
    const id = btn.dataset.atab;
    $$('.admin-tabs button').forEach(b => b.classList.toggle('active', b===btn));
    $$('.atab').forEach(t => t.classList.toggle('active', t.id === 'atab-'+id));
  });
});

/* ---------- LOAD DATA ---------- */
async function loadData() {
  const [c,e,v,co,mo,fl] = await Promise.all([
    fetch('data/config.json').then(r=>r.json()),
    fetch('data/experts.json').then(r=>r.json()),
    fetch('data/videos.json').then(r=>r.json()),
    fetch('data/courses.json').then(r=>r.json()),
    fetch('data/motion.json').then(r=>r.json()),
    fetch('data/flyers.json').then(r=>r.json()),
  ]);
  STATE.config = applyLocalDraft('config', c);
  STATE.experts = (applyLocalDraft('experts', e).experts) || [];
  STATE.videos  = (applyLocalDraft('videos', v).videos)  || [];
  STATE.courses = (applyLocalDraft('courses', co).courses) || [];
  STATE.motion  = (applyLocalDraft('motion', mo).motion) || [];
  STATE.flyers  = (applyLocalDraft('flyers', fl).flyers) || [];
}

async function bootAdmin() {
  await loadData();
  staticBanner();
  renderVideosTable();
  renderExpertsTable();
  renderSimpleTable('courses', STATE.courses);
  renderSimpleTable('motion',  STATE.motion);
  renderSimpleTable('flyers',  STATE.flyers);
  renderConfigEditor();
  loadAdminStatus();
}

/* ---------- VIDEOS TABLE ---------- */
function renderVideosTable() {
  const wrap = $('#videosTable');
  if (STATE.videos.length === 0) {
    wrap.innerHTML = `<div class="empty-state">
      <strong>Nenhum vídeo ainda.</strong><br>
      Click em "+ Adicionar vídeo" para começar.
    </div>`;
    return;
  }
  wrap.innerHTML = STATE.videos.map((v, i) => {
    const expert = STATE.experts.find(e => e.id === v.expert_id);
    return `
      <div class="row-card" data-i="${i}">
        ${v.thumb
          ? `<img class="thumb" src="${v.thumb}" alt="">`
          : `<div class="thumb">▶</div>`}
        <div class="info">
          <div class="nm">${escapeHtml(v.title || '(sem título)')}</div>
          <div class="meta">
            ${expert ? expert.name : '— sem expert'}
            · ${v.level || 'sem nível'}
            · ${v.category || 'sem categoria'}
            · ${formatNum(v.views||0)} views
          </div>
        </div>
        <div class="actions">
          <button class="btn-icon" data-action="edit-video" data-i="${i}" title="Editar">✏️</button>
          <button class="btn-icon danger" data-action="del-video" data-i="${i}" title="Excluir">🗑️</button>
        </div>
      </div>`;
  }).join('');
}

/* ---------- EXPERTS TABLE ---------- */
function renderExpertsTable() {
  const wrap = $('#expertsTable');
  wrap.innerHTML = STATE.experts.map((e, i) => `
    <div class="row-card" data-i="${i}">
      <img class="thumb" src="${e.photo}" alt="">
      <div class="info">
        <div class="nm">${escapeHtml(e.name)} ${e.is_owner?'<span style="color:var(--gold); font-size:.7rem;">[VOCÊ]</span>':''}</div>
        <div class="meta">${e.instagram || '—'} · ${escapeHtml(e.role || '')}</div>
      </div>
      <div class="actions">
        <button class="btn-icon" data-action="edit-expert" data-i="${i}" title="Editar">✏️</button>
        <button class="btn-icon danger" data-action="del-expert" data-i="${i}" title="Excluir">🗑️</button>
      </div>
    </div>
  `).join('');
}

/* ---------- SIMPLE TABLE (courses, motion, flyers) ---------- */
function renderSimpleTable(kind, list) {
  const wrap = $(`#${kind}Table`);
  if (!wrap) return;
  if (!list.length) {
    wrap.innerHTML = `<div class="empty-state">Nenhum item ainda.</div>`;
    return;
  }
  wrap.innerHTML = list.map((it, i) => `
    <div class="row-card" data-i="${i}">
      ${it.thumb ? `<img class="thumb" src="${it.thumb}" alt="">` : `<div class="thumb">📁</div>`}
      <div class="info">
        <div class="nm">${escapeHtml(it.title || '(sem título)')}</div>
        <div class="meta">${escapeHtml(it.client || '')} ${it.year ? '· '+it.year : ''}</div>
      </div>
      <div class="actions">
        <button class="btn-icon" data-action="edit-${kind}" data-i="${i}" title="Editar">✏️</button>
        <button class="btn-icon danger" data-action="del-${kind}" data-i="${i}" title="Excluir">🗑️</button>
      </div>
    </div>
  `).join('');
}

/* ---------- DELEGATED ACTIONS ---------- */
document.addEventListener('click', async (e) => {
  const btn = e.target.closest('button[data-action], button[data-add]');
  if (!btn) return;

  // Add buttons
  if (btn.dataset.add) {
    openSimpleForm(btn.dataset.add, null);
    return;
  }

  const action = btn.dataset.action;
  const i = parseInt(btn.dataset.i, 10);

  // Video actions
  if (action === 'edit-video')  return openVideoForm(STATE.videos[i], i);
  if (action === 'del-video') {
    if (!confirm(`Excluir "${STATE.videos[i].title}"?`)) return;
    STATE.videos.splice(i, 1);
    await saveAndReload('videos', { videos: STATE.videos });
    renderVideosTable();
  }

  // Expert actions
  if (action === 'edit-expert') return openExpertForm(STATE.experts[i], i);
  if (action === 'del-expert') {
    if (!confirm(`Excluir expert ${STATE.experts[i].name}?`)) return;
    STATE.experts.splice(i, 1);
    await saveAndReload('experts', { experts: STATE.experts });
    renderExpertsTable();
  }

  // Simple actions (courses, motion, flyers)
  for (const kind of ['courses','motion','flyers']) {
    if (action === `edit-${kind}`) return openSimpleForm(kind, STATE[kind][i], i);
    if (action === `del-${kind}`) {
      if (!confirm(`Excluir item?`)) return;
      STATE[kind].splice(i, 1);
      const wrapper = { [kind]: STATE[kind] };
      await saveAndReload(kind, wrapper);
      renderSimpleTable(kind, STATE[kind]);
    }
  }
});

$('#addVideoBtn').addEventListener('click', () => openVideoForm(null, null));
$('#addExpertBtn').addEventListener('click', () => openExpertForm(null, null));

/* ---------- HELPERS ---------- */
function escapeHtml(s) { return String(s||'').replace(/[<>&"]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;'}[c])); }
function formatNum(n) {
  if (n >= 1e6) return (n/1e6).toFixed(1).replace('.0','')+'M';
  if (n >= 1e3) return (n/1e3).toFixed(1).replace('.0','')+'K';
  return String(n||0);
}
function uid(prefix='id') { return prefix + '_' + Math.random().toString(36).slice(2,9) + Date.now().toString(36); }

async function saveAndReload(key, payload) {
  if (STATE.staticMode) {
    localStorage.setItem('jv_admin_' + key, JSON.stringify(payload));
    toast('Rascunho salvo neste navegador. Use Preview rascunho; para aparecer para todos precisa publicar pelo Git/Supabase.', 'success');
    return;
  }
  await api('POST', '/api/save/'+key, payload);
  toast('💾 Salvo!', 'success');
}

/* ---------- MODAL FORM ---------- */
function openModal(htmlStr) {
  const m = $('#formModal');
  $('#formContent').innerHTML = htmlStr;
  m.style.display = 'grid';
  m.classList.remove('hidden');
}
function closeModal() {
  const m = $('#formModal');
  m.style.display = 'none';
  m.classList.add('hidden');
}
$('#formClose').addEventListener('click', closeModal);

/* ---------- VIDEO FORM ---------- */
function openVideoForm(v, idx) {
  v = v || { id: uid('vid'), title:'', expert_id:'', level:'medio', category:'reel',
             src:'', thumb:'', instagram_url:'', views:0, likes:0, shares:0,
             description:'', process:[], team:[] };

  const expertOptions = STATE.experts.map(e => `<option value="${e.id}" ${e.id===v.expert_id?'selected':''}>${escapeHtml(e.name)}</option>`).join('');
  const levelChips = (STATE.config.edit_levels||[]).map(l =>
    `<button type="button" class="style-chip ${l.id===v.level?'active':''}" data-level="${l.id}">${l.label}</button>`).join('');
  const catChips = (STATE.config.categories||[]).map(c =>
    `<button type="button" class="style-chip ${c.id===v.category?'active':''}" data-cat="${c.id}">${c.label}</button>`).join('');

  openModal(`
    <h3>${idx===null?'Novo vídeo':'Editar vídeo'}</h3>

    <label>Título</label>
    <input id="f-title" value="${escapeHtml(v.title)}" placeholder="Ex: Reel viral da Confeitaria Amena">

    <div class="grid-2">
      <div>
        <label>Expert</label>
        <select id="f-expert"><option value="">(nenhum)</option>${expertOptions}</select>
      </div>
      <div>
        <label>Link do post no Instagram</label>
        <input id="f-igurl" value="${escapeHtml(v.instagram_url)}" placeholder="https://instagram.com/p/...">
        <button class="chip" type="button" id="f-auto-video" style="margin-top:.45rem;width:100%;">Preencher pelo link</button>
      </div>
    </div>

    <label>Nível de edição</label>
    <div class="style-chips" id="f-levels">${levelChips}</div>

    <label>Categoria</label>
    <div class="style-chips" id="f-cats">${catChips}</div>

    <div class="grid-2">
      <div>
        <label>Vídeo (mp4)</label>
        <div class="upload-zone" id="f-vid-zone">
          <input type="file" accept="video/mp4,video/webm,video/quicktime" id="f-vid-file">
          <div>📹 ${v.src ? '<strong>'+v.src.split('/').pop()+'</strong>' : '<strong>Click ou arraste</strong> mp4'}</div>
          <div class="upload-progress hidden"><span></span></div>
        </div>
        <input id="f-src" value="${escapeHtml(v.src)}" placeholder="ou caminho assets/videos/..." style="margin-top:.5rem;">
      </div>
      <div>
        <label>Thumb (jpg/png)</label>
        <div class="upload-zone" id="f-thumb-zone">
          <input type="file" accept="image/*" id="f-thumb-file">
          <div>🖼️ ${v.thumb ? '<strong>'+v.thumb.split('/').pop()+'</strong>' : '<strong>Click ou arraste</strong>'}</div>
          <div class="upload-progress hidden"><span></span></div>
        </div>
        <input id="f-thumb" value="${escapeHtml(v.thumb)}" placeholder="assets/thumbs/..." style="margin-top:.5rem;">
      </div>
    </div>

    <div class="grid-2">
      <div><label>Views</label><input id="f-views" type="number" min="0" value="${v.views||0}"></div>
      <div><label>Curtidas</label><input id="f-likes" type="number" min="0" value="${v.likes||0}"></div>
    </div>
    <label>Compartilhamentos</label>
    <input id="f-shares" type="number" min="0" value="${v.shares||0}">

    <label>Descrição</label>
    <textarea id="f-desc" rows="3" placeholder="O que tem de especial nesse vídeo?">${escapeHtml(v.description)}</textarea>

    <label>Processo até a publicação <small style="color:var(--ink-2);">(uma etapa por linha)</small></label>
    <div class="list-editor" id="f-process">
      ${(v.process||[]).map(p => listItem(p)).join('')}
    </div>
    <div class="list-add" data-list="f-process">+ Adicionar etapa</div>

    <label>Envolvidos no projeto <small style="color:var(--ink-2);">(uma pessoa por linha)</small></label>
    <div class="list-editor" id="f-team">
      ${(v.team||[]).map(p => listItem(p)).join('')}
    </div>
    <div class="list-add" data-list="f-team">+ Adicionar pessoa</div>

    <div class="form-actions">
      <button class="chip" type="button" id="f-cancel">Cancelar</button>
      <button class="btn-primary" type="button" id="f-save">${idx===null?'Adicionar':'Salvar'}</button>
    </div>
  `);

  // Wire chips
  $$('#f-levels .style-chip').forEach(c => c.addEventListener('click', () => {
    $$('#f-levels .style-chip').forEach(x => x.classList.remove('active'));
    c.classList.add('active');
  }));
  $$('#f-cats .style-chip').forEach(c => c.addEventListener('click', () => {
    $$('#f-cats .style-chip').forEach(x => x.classList.remove('active'));
    c.classList.add('active');
  }));

  // List editor
  $$('.list-add').forEach(b => b.addEventListener('click', () => {
    const t = $('#'+b.dataset.list);
    t.insertAdjacentHTML('beforeend', listItem(''));
    bindListItems(t);
  }));
  bindListItems($('#f-process'));
  bindListItems($('#f-team'));

  // Upload zones
  setupUploadZone($('#f-vid-zone'), $('#f-vid-file'), 'video', (path) => $('#f-src').value = path);
  setupUploadZone($('#f-thumb-zone'), $('#f-thumb-file'), 'thumb', (path) => $('#f-thumb').value = path);
  $('#f-auto-video').addEventListener('click', () => autoFillVideoFromLink());

  // Save
  $('#f-cancel').addEventListener('click', closeModal);
  $('#f-save').addEventListener('click', async () => {
    const out = {
      id: v.id,
      title: $('#f-title').value.trim(),
      expert_id: $('#f-expert').value,
      instagram_url: $('#f-igurl').value.trim(),
      level: $('#f-levels .style-chip.active')?.dataset.level || 'medio',
      category: $('#f-cats .style-chip.active')?.dataset.cat || 'reel',
      src: $('#f-src').value.trim(),
      thumb: $('#f-thumb').value.trim(),
      views: parseInt($('#f-views').value, 10) || 0,
      likes: parseInt($('#f-likes').value, 10) || 0,
      shares: parseInt($('#f-shares').value, 10) || 0,
      description: $('#f-desc').value.trim(),
      process: collectList($('#f-process')),
      team: collectList($('#f-team'))
    };
    if (!out.title) return toast('Título é obrigatório', 'error');
    if (idx === null) STATE.videos.push(out);
    else              STATE.videos[idx] = out;

    await saveAndReload('videos', { videos: STATE.videos });
    renderVideosTable();
    closeModal();
  });
}

function extractPostCode(url) {
  const clean = String(url || '').split('?')[0];
  const m = clean.match(/instagram\.com\/(?:reel|p)\/([^/]+)/i);
  const y = clean.match(/(?:youtu\.be\/|youtube\.com\/watch\?v=)([A-Za-z0-9_-]+)/i);
  return m?.[1] || y?.[1] || '';
}

function autoFillVideoFromLink() {
  const url = ($('#f-igurl')?.value || '').trim();
  const code = extractPostCode(url);
  if (!code) return toast('Cole um link valido do Instagram ou YouTube primeiro.', 'error');
  const isYT = /youtu\.?be|youtube\.com/i.test(url);
  const category = isYT ? 'youtube' : ($('#f-cats .style-chip.active')?.dataset.cat || 'reel');
  const src = isYT ? '' : `assets/videos/ig/${code}.mp4`;
  const thumb = isYT ? `assets/thumbs/youtube/${code}.jpg` : `assets/thumbs/ig/${code}.jpg`;

  if (!$('#f-title').value.trim()) $('#f-title').value = isYT ? `Video YouTube ${code}` : `Reel ${code}`;
  if (src && !$('#f-src').value.trim()) $('#f-src').value = src;
  if (!$('#f-thumb').value.trim()) $('#f-thumb').value = thumb;
  $$('#f-cats .style-chip').forEach(c => c.classList.toggle('active', c.dataset.cat === category));
  toast('Preenchi codigo, caminho do video/capa e categoria. Ajuste o titulo e confira os arquivos.', 'success');
}

function listItem(text) {
  return `<div class="item">
    <input value="${escapeHtml(text)}">
    <button type="button" class="btn-icon danger" data-act="rm">✕</button>
  </div>`;
}
function bindListItems(container) {
  $$('.item button[data-act=rm]', container).forEach(b => {
    b.onclick = () => b.parentElement.remove();
  });
}
function collectList(container) {
  return $$('.item input', container).map(i => i.value.trim()).filter(Boolean);
}

/* ---------- UPLOAD ZONE ---------- */
function setupUploadZone(zone, fileInput, kind, onDone) {
  zone.addEventListener('click', () => fileInput.click());
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => {
    e.preventDefault(); zone.classList.remove('dragover');
    if (e.dataTransfer.files.length) doUpload(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) doUpload(fileInput.files[0]);
  });
  async function doUpload(file) {
    if (STATE.staticMode) {
      if (!file.type.startsWith('image/')) {
        toast('No Vercel sem storage, envie videos por link/caminho. Imagens de capa funcionam como rascunho.', 'error');
        return;
      }
      const reader = new FileReader();
      reader.onload = () => {
        onDone(reader.result);
        toast('Imagem salva como rascunho neste celular.', 'success');
        zone.querySelector('div').innerHTML = `✓ <strong>${file.name}</strong> · ${(file.size/1e6).toFixed(2)}MB`;
      };
      reader.readAsDataURL(file);
      return;
    }
    const fd = new FormData();
    fd.append('kind', kind);
    fd.append('file', file);
    const prog = zone.querySelector('.upload-progress');
    prog.classList.remove('hidden');
    prog.querySelector('span').style.width = '30%';
    try {
      const r = await api('POST', '/api/upload', fd);
      prog.querySelector('span').style.width = '100%';
      onDone(r.path);
      toast('Upload OK: ' + r.path, 'success');
      zone.querySelector('div').innerHTML = `✓ <strong>${file.name}</strong> · ${(file.size/1e6).toFixed(2)}MB`;
    } catch (err) {
      toast('Falha no upload: ' + err.message, 'error');
    } finally {
      setTimeout(() => prog.classList.add('hidden'), 800);
    }
  }
}

/* ---------- EXPERT FORM ---------- */
function openExpertForm(e, idx) {
  e = e || { id: uid('exp'), name:'', instagram:'', instagram_url:'', photo:'', role:'' };

  openModal(`
    <h3>${idx===null?'Novo expert':'Editar expert'}</h3>

    <label>Nome</label>
    <input id="f-name" value="${escapeHtml(e.name)}" placeholder="Nome do expert">

    <div class="grid-2">
      <div>
        <label>Handle Instagram</label>
        <input id="f-ig" value="${escapeHtml(e.instagram||'')}" placeholder="@usuario">
      </div>
      <div>
        <label>URL Instagram</label>
        <input id="f-igurl" value="${escapeHtml(e.instagram_url||'')}" placeholder="https://instagram.com/usuario">
      </div>
    </div>

    <label>O que faz / nicho</label>
    <input id="f-role" value="${escapeHtml(e.role||'')}" placeholder="Ex: Confeitaria, Engenheira, Fotógrafo de casamentos...">

    <label>Foto de perfil</label>
    <div class="upload-zone" id="f-photo-zone">
      <input type="file" accept="image/*" id="f-photo-file">
      <div>${e.photo ? '✓ <strong>'+e.photo.split('/').pop()+'</strong>' : '🖼️ <strong>Click ou arraste</strong>'}</div>
      <div class="upload-progress hidden"><span></span></div>
    </div>
    <input id="f-photo" value="${escapeHtml(e.photo||'')}" placeholder="assets/experts/..." style="margin-top:.5rem;">

    <div class="form-actions">
      <button class="chip" type="button" id="f-cancel">Cancelar</button>
      <button class="btn-primary" type="button" id="f-save">${idx===null?'Adicionar':'Salvar'}</button>
    </div>
  `);

  setupUploadZone($('#f-photo-zone'), $('#f-photo-file'), 'photo', (path) => $('#f-photo').value = path);

  $('#f-cancel').addEventListener('click', closeModal);
  $('#f-save').addEventListener('click', async () => {
    const out = {
      id: e.id || uid('exp'),
      name: $('#f-name').value.trim(),
      instagram: $('#f-ig').value.trim() || null,
      instagram_url: $('#f-igurl').value.trim() || null,
      role: $('#f-role').value.trim(),
      photo: $('#f-photo').value.trim(),
      is_owner: e.is_owner || false
    };
    if (!out.name) return toast('Nome é obrigatório', 'error');
    if (idx === null) STATE.experts.push(out);
    else              STATE.experts[idx] = { ...STATE.experts[idx], ...out };
    await saveAndReload('experts', { experts: STATE.experts });
    renderExpertsTable();
    closeModal();
  });
}

/* ---------- SIMPLE FORM (courses, motion, flyers) ---------- */
function openSimpleForm(kind, item, idx) {
  item = item || { id: uid(kind), title:'', client:'', year:new Date().getFullYear(), thumb:'', src:'', description:'' };
  const labels = {
    courses: { title: 'Curso', placeholder: 'Ex: Curso de marketing digital — Fulano' },
    motion:  { title: 'Peça de motion', placeholder: 'Ex: Abertura institucional — Cliente X' },
    flyers:  { title: 'Flyer', placeholder: 'Ex: Flyer evento Y' }
  };
  const lab = labels[kind];

  openModal(`
    <h3>${idx===undefined||idx===null?'Novo '+lab.title.toLowerCase():'Editar '+lab.title.toLowerCase()}</h3>

    <label>Título</label>
    <input id="f-title" value="${escapeHtml(item.title)}" placeholder="${lab.placeholder}">

    <div class="grid-2">
      <div>
        <label>Cliente / aluno</label>
        <input id="f-client" value="${escapeHtml(item.client||'')}">
      </div>
      <div>
        <label>Ano</label>
        <input id="f-year" type="number" value="${item.year || new Date().getFullYear()}">
      </div>
    </div>

    <label>Thumbnail</label>
    <div class="upload-zone" id="f-thumb-zone">
      <input type="file" accept="image/*" id="f-thumb-file">
      <div>${item.thumb ? '✓ <strong>'+item.thumb.split('/').pop()+'</strong>' : '🖼️ <strong>Click ou arraste</strong>'}</div>
      <div class="upload-progress hidden"><span></span></div>
    </div>
    <input id="f-thumb" value="${escapeHtml(item.thumb||'')}" placeholder="assets/thumbs/..." style="margin-top:.5rem;">

    ${kind === 'courses' || kind === 'motion' ? `
      <label>Vídeo demo (opcional)</label>
      <div class="upload-zone" id="f-src-zone">
        <input type="file" accept="video/*" id="f-src-file">
        <div>${item.src ? '✓ <strong>'+item.src.split('/').pop()+'</strong>' : '📹 <strong>Click ou arraste</strong>'}</div>
        <div class="upload-progress hidden"><span></span></div>
      </div>
      <input id="f-src" value="${escapeHtml(item.src||'')}" placeholder="assets/videos/..." style="margin-top:.5rem;">
    ` : ''}

    <label>Descrição</label>
    <textarea id="f-desc" rows="2">${escapeHtml(item.description||'')}</textarea>

    <div class="form-actions">
      <button class="chip" type="button" id="f-cancel">Cancelar</button>
      <button class="btn-primary" type="button" id="f-save">Salvar</button>
    </div>
  `);

  setupUploadZone($('#f-thumb-zone'), $('#f-thumb-file'), 'thumb', (path) => $('#f-thumb').value = path);
  if ($('#f-src-zone')) {
    setupUploadZone($('#f-src-zone'), $('#f-src-file'), 'video', (path) => $('#f-src').value = path);
  }

  $('#f-cancel').addEventListener('click', closeModal);
  $('#f-save').addEventListener('click', async () => {
    const out = {
      id: item.id,
      title: $('#f-title').value.trim(),
      client: $('#f-client').value.trim(),
      year: parseInt($('#f-year').value, 10) || new Date().getFullYear(),
      thumb: $('#f-thumb').value.trim(),
      src: $('#f-src') ? $('#f-src').value.trim() : '',
      description: $('#f-desc').value.trim()
    };
    if (!out.title) return toast('Título é obrigatório', 'error');
    if (idx === undefined || idx === null) STATE[kind].push(out);
    else                                   STATE[kind][idx] = out;
    await saveAndReload(kind, { [kind]: STATE[kind] });
    renderSimpleTable(kind, STATE[kind]);
    closeModal();
  });
}

/* ---------- CONFIG EDITOR ---------- */
function renderConfigEditor() {
  const c = STATE.config;
  if (!c) return;
  const el = $('#configEditor');
  const tierRows = (c.budget.formats || []).map((f, fi) => `
    <div style="margin-bottom:1rem;">
      <strong style="color:var(--ink-0);">${escapeHtml(f.label)}</strong>
      ${(f.tiers || []).map((t, ti) => `
        <div class="row" style="margin-bottom:.5rem;">
          <div><label>Min</label><input data-cfg="budget.formats.${fi}.tiers.${ti}.min" type="number" value="${t.min}"></div>
          <div><label>Max</label><input data-cfg="budget.formats.${fi}.tiers.${ti}.max" type="number" value="${t.max}"></div>
          <div><label>R$ por video</label><input data-cfg="budget.formats.${fi}.tiers.${ti}.price" type="number" value="${t.price}"></div>
          <div><label>Label</label><input data-cfg="budget.formats.${fi}.tiers.${ti}.label" value="${escapeHtml(t.label)}"></div>
        </div>`).join('')}
    </div>`).join('');
  el.innerHTML = `
    <div class="group">
      <h4>Contato e identidade</h4>
      <div class="row">
        <div><label>Nome</label><input data-cfg="site.owner_name" value="${escapeHtml(c.site.owner_name)}"></div>
        <div><label>Tagline</label><input data-cfg="site.tagline" value="${escapeHtml(c.site.tagline)}"></div>
      </div>
      <div class="row">
        <div><label>WhatsApp (com +)</label><input data-cfg="site.whatsapp" value="${escapeHtml(c.site.whatsapp)}"></div>
        <div><label>WhatsApp (só dígitos)</label><input data-cfg="site.whatsapp_digits" value="${escapeHtml(c.site.whatsapp_digits)}"></div>
      </div>
      <div class="row">
        <div><label>Instagram handle</label><input data-cfg="site.owner_instagram" value="${escapeHtml(c.site.owner_instagram)}"></div>
        <div><label>Instagram URL</label><input data-cfg="site.owner_instagram_url" value="${escapeHtml(c.site.owner_instagram_url)}"></div>
      </div>
      <div class="row">
        <div><label>Texto do botao de entrada</label><input data-cfg="site.portal_button" value="${escapeHtml(c.site.portal_button || 'Ver portfolio')}"></div>
        <div><label>Frase da entrada</label><input data-cfg="site.portal_tag" value="${escapeHtml(c.site.portal_tag || '')}"></div>
      </div>
      <div class="row">
        <div><label>Arquivo Rive do mascote (.riv)</label><input data-cfg="site.rive_file" value="${escapeHtml(c.site.rive_file || '')}" placeholder="assets/brand/bear.riv"></div>
        <div><label>State machine Rive</label><input data-cfg="site.rive_state_machine" value="${escapeHtml(c.site.rive_state_machine || 'State Machine 1')}"></div>
      </div>
      <div class="row">
        <div><label>Fundo</label><input data-cfg="site.theme.background" value="${escapeHtml(c.site.theme?.background || '#06101d')}"></div>
        <div><label>Superficie</label><input data-cfg="site.theme.surface" value="${escapeHtml(c.site.theme?.surface || '#081b2e')}"></div>
        <div><label>Azul principal</label><input data-cfg="site.theme.accent" value="${escapeHtml(c.site.theme?.accent || '#7dd3fc')}"></div>
        <div><label>Azul secundario</label><input data-cfg="site.theme.accent_2" value="${escapeHtml(c.site.theme?.accent_2 || '#2f86ff')}"></div>
      </div>
      <label>Subtítulo</label>
      <textarea data-cfg="site.subtitle" rows="2">${escapeHtml(c.site.subtitle||'')}</textarea>
    </div>

    <div class="group">
      <h4>📊 Stats Hero (números reais que aparecem na home)</h4>
      <p class="sub" style="margin-top:0;">Preencha com seus números verdadeiros. Vão animar contando até o valor.</p>
      ${(c.stats||[]).map((s,i) => `
        <div class="row" style="margin-bottom:.5rem;">
          <div><label>Ícone (emoji)</label><input data-cfg="stats.${i}.icon" value="${escapeHtml(s.icon||'')}" placeholder="🎬"></div>
          <div><label>Valor (número)</label><input data-cfg="stats.${i}.value" type="number" value="${s.value||0}"></div>
          <div><label>Sufixo</label><input data-cfg="stats.${i}.suffix" value="${escapeHtml(s.suffix||'')}" placeholder="+, M+, K+"></div>
          <div><label>Label</label><input data-cfg="stats.${i}.label" value="${escapeHtml(s.label||'')}"></div>
        </div>
        <label>Nota pequena</label>
        <input data-cfg="stats.${i}.note" value="${escapeHtml(s.note||'')}" style="margin-bottom:1rem;">
      `).join('')}
    </div>

    <div class="group">
      <h4>Palavra do hero em itálico serif</h4>
      <label>Qual palavra ganha destaque serif?</label>
      <input data-cfg="site.hero_serif_word" value="${escapeHtml(c.site.hero_serif_word||'viral')}">
    </div>

    <div class="group">
      <h4>Faixas de preço (preço por vídeo segundo quantidade)</h4>
      ${tierRows}
    </div>

    <div class="group">
      <h4>Categorias do portfolio</h4>
      <p class="sub" style="margin-top:0;">Edite id e label em JSON. Exemplo: {"id":"unboxing","label":"Unboxing"}.</p>
      <textarea id="categoriesJson" rows="8">${escapeHtml(JSON.stringify(c.categories || [], null, 2))}</textarea>
    </div>

    <div class="group">
      <h4>Area tipo Netflix / anuncios</h4>
      <p class="sub" style="margin-top:0;">Edite em JSON. Use active true quando quiser mostrar no topo do portfolio.</p>
      <textarea id="promosJson" rows="8">${escapeHtml(JSON.stringify(c.site.featured_promos || [], null, 2))}</textarea>
    </div>

    <div class="group">
      <h4>Multiplicadores por estilo</h4>
      <div class="row">
        ${Object.entries(c.budget.style_multipliers).map(([k,v]) =>
          `<div><label>${k}</label><input data-cfg="budget.style_multipliers.${k}" type="number" step="0.05" value="${v}"></div>`
        ).join('')}
      </div>
    </div>

    <div class="group">
      <h4>Orcamento dinamico</h4>
      <p class="sub" style="margin-top:0;">Controla a recomendacao mensal que aparece de acordo com quantidade, estilos e formato escolhidos pelo cliente.</p>
      <div class="row">
        <div><label>Videos minimos para mensal</label><input data-cfg="budget.monthly_min_videos" type="number" min="1" value="${c.budget.monthly_min_videos || 8}"></div>
        <div><label>Desconto mensal (%)</label><input data-cfg="budget.monthly_discount_percent" type="number" min="0" max="90" value="${c.budget.monthly_discount_percent || 20}"></div>
        <div><label>Cupom ativo?</label><select data-cfg="budget.coupon.active"><option value="false" ${!c.budget.coupon?.active?'selected':''}>Nao</option><option value="true" ${c.budget.coupon?.active?'selected':''}>Sim</option></select></div>
        <div><label>Desconto cupom (%)</label><input data-cfg="budget.coupon.percent" type="number" min="0" max="90" value="${c.budget.coupon?.percent || 0}"></div>
      </div>
      <div class="row">
        <div><label>Codigo do cupom</label><input data-cfg="budget.coupon.code" value="${escapeHtml(c.budget.coupon?.code || 'JV20')}"></div>
        <div><label>Nome do cupom</label><input data-cfg="budget.coupon.label" value="${escapeHtml(c.budget.coupon?.label || 'Cupom do portfolio')}"></div>
      </div>
      <label>Beneficios do mensal (um por linha)</label>
      <textarea rows="4" data-cfg-list="budget.monthly_benefits">${(c.budget.monthly_benefits || []).join('\n')}</textarea>
      <hr style="border:0;border-top:1px solid rgba(255,255,255,.08);margin:1.2rem 0;">
      <h4>Planos mensais antigos</h4>
      <p class="sub" style="margin-top:0;">Mantidos como backup. O site usa a regra dinamica acima.</p>
      ${c.budget.monthly_plans.map((p,i) => `
        <div class="row" style="margin-bottom:.5rem;">
          <div><label>Nome</label><input data-cfg="budget.monthly_plans.${i}.name" value="${escapeHtml(p.name)}"></div>
          <div><label>Vídeos/mês</label><input data-cfg="budget.monthly_plans.${i}.videos_per_month" type="number" value="${p.videos_per_month}"></div>
          <div><label>R$/mês</label><input data-cfg="budget.monthly_plans.${i}.price" type="number" value="${p.price}"></div>
          <div><label>Destaque</label><select data-cfg="budget.monthly_plans.${i}.highlight"><option value="false" ${!p.highlight?'selected':''}>Não</option><option value="true" ${p.highlight?'selected':''}>Sim</option></select></div>
        </div>
        <label>Features (uma por linha)</label>
        <textarea rows="3" data-cfg-list="budget.monthly_plans.${i}.features">${(p.features||[]).join('\n')}</textarea>
      `).join('')}
    </div>
  `;
}

$('#saveConfigBtn').addEventListener('click', async () => {
  const c = JSON.parse(JSON.stringify(STATE.config)); // clone
  $$('#configEditor [data-cfg]').forEach(el => {
    const path = el.dataset.cfg.split('.');
    let val = el.value;
    if (el.type === 'number') val = parseFloat(val);
    if (val === 'true')  val = true;
    if (val === 'false') val = false;
    setPath(c, path, val);
  });
  $$('#configEditor [data-cfg-list]').forEach(el => {
    const path = el.dataset.cfgList.split('.');
    setPath(c, path, el.value.split('\n').map(s=>s.trim()).filter(Boolean));
  });
  const cats = $('#categoriesJson');
  if (cats) {
    try {
      c.categories = JSON.parse(cats.value);
    } catch {
      return toast('JSON de categorias invalido', 'error');
    }
  }
  const promos = $('#promosJson');
  if (promos) {
    try {
      c.site.featured_promos = JSON.parse(promos.value);
    } catch {
      return toast('JSON de anuncios invalido', 'error');
    }
  }
  STATE.config = c;
  await saveAndReload('config', c);
  toast('Configurações salvas', 'success');
});

$('#reloadConfigBtn').addEventListener('click', async () => {
  await loadData();
  renderConfigEditor();
  toast('Recarregado', '');
});

function setPath(obj, path, val) {
  let o = obj;
  for (let i=0; i<path.length-1; i++) {
    const k = path[i];
    if (!(k in o)) o[k] = {};
    o = o[k];
  }
  o[path[path.length-1]] = val;
}

/* ---------- SECURITY ---------- */
$('#changePwBtn').addEventListener('click', async () => {
  const a = $('#newPw').value, b = $('#newPw2').value;
  if (a.length < 8) return toast('Senha curta — mín 8 caracteres', 'error');
  if (a !== b) return toast('Senhas não batem', 'error');
  await api('POST', '/api/admin-config', { new_password: a });
  $('#newPw').value = ''; $('#newPw2').value = '';
  toast('Senha trocada ✓', 'success');
});

$('#statusActive').addEventListener('click', async () => {
  await api('POST', '/api/admin-config', { site_status: 'active' });
  $('#currentStatus').textContent = 'active';
  toast('Site ativo', 'success');
});
$('#statusFrozen').addEventListener('click', async () => {
  await api('POST', '/api/admin-config', { site_status: 'frozen' });
  $('#currentStatus').textContent = 'frozen';
  toast('Site congelado', '');
});

async function loadAdminStatus() {
  try {
    const r = await api('GET', '/api/admin-config');
    $('#currentStatus').textContent = r.site_status || 'active';
  } catch {}
}

/* ---------- AUTO-LOGIN CHECK ---------- */
(async () => {
  try {
    const r = await fetch('/api/whoami').then(r=>r.json());
    if (r.authed) {
      $('#adminLogin').classList.add('hidden');
      $('#adminApp').classList.remove('hidden');
      bootAdmin();
    }
  } catch {}
})();
