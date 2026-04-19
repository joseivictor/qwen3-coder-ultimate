"""
QWEN3-CODER ULTIMATE — Web UI v2.0
FastAPI + WebSocket streaming chat. Full dark-mode UI.
Features: file tree, tool visualization, BUDDY widget, session stats, multi-tab.
"""

import asyncio
import json
import os
import sys
import threading
import time
from pathlib import Path

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse, JSONResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QWEN3-CODER Ultimate</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #0d1117; --surface: #161b22; --surface2: #1c2128;
  --border: #30363d; --text: #e6edf3; --dim: #7d8590;
  --accent: #58a6ff; --green: #3fb950; --red: #f85149;
  --yellow: #d29922; --purple: #bc8cff; --orange: #ffa657;
  --code-bg: #1f2428; --buddy: #ff79c6;
}
body { background: var(--bg); color: var(--text); font-family: 'SF Mono', Consolas, monospace; font-size: 13px; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }

/* HEADER */
#header { background: var(--surface); border-bottom: 1px solid var(--border); padding: 10px 16px; display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
#header h1 { font-size: 15px; color: var(--accent); font-weight: 700; letter-spacing: 0.5px; }
#header .badge { background: var(--surface2); border: 1px solid var(--border); color: var(--dim); padding: 2px 8px; border-radius: 12px; font-size: 11px; }
#conn-status { margin-left: auto; font-size: 11px; color: var(--dim); display: flex; align-items: center; gap: 6px; }
#conn-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--dim); transition: background 0.3s; }
#conn-dot.connected { background: var(--green); box-shadow: 0 0 6px var(--green); }
#conn-dot.error { background: var(--red); }

/* LAYOUT */
#main { flex: 1; display: flex; overflow: hidden; }

/* LEFT SIDEBAR - file tree */
#sidebar-left { width: 200px; background: var(--surface); border-right: 1px solid var(--border); display: flex; flex-direction: column; overflow: hidden; }
#sidebar-left h3 { padding: 10px 12px 6px; font-size: 10px; text-transform: uppercase; color: var(--dim); letter-spacing: 1px; border-bottom: 1px solid var(--border); }
#file-tree { flex: 1; overflow-y: auto; padding: 4px 0; font-size: 12px; }
.tree-item { padding: 3px 12px; cursor: pointer; color: var(--dim); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tree-item:hover { background: var(--surface2); color: var(--text); }
.tree-item.dir { color: var(--accent); }
.tree-item.py { color: var(--yellow); }
.tree-item.ts, .tree-item.js { color: var(--green); }
.tree-item.json { color: var(--orange); }

/* CHAT AREA */
#chat-area { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
#messages { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; scroll-behavior: smooth; }
.msg { display: flex; gap: 10px; animation: fadeIn 0.15s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(3px); } to { opacity: 1; } }
.avatar { width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 13px; flex-shrink: 0; margin-top: 2px; }
.msg.user .avatar { background: #1f6feb; }
.msg.assistant .avatar { background: #238636; }
.msg.tool .avatar { background: #6e40c9; }
.msg.system .avatar { background: #444; }
.msg.buddy .avatar { background: #ff79c620; border: 1px solid var(--buddy); }
.msg-body { flex: 1; min-width: 0; }
.msg-role { font-size: 10px; color: var(--dim); margin-bottom: 3px; text-transform: uppercase; letter-spacing: 0.5px; }
.msg-text { line-height: 1.65; white-space: pre-wrap; word-break: break-word; }
.msg.user .msg-text { color: #a5d6ff; }
.msg.buddy .msg-text { color: var(--buddy); font-style: italic; }
.msg.tool .msg-text { color: var(--dim); font-size: 12px; border-left: 2px solid #6e40c9; padding-left: 8px; max-height: 120px; overflow: hidden; transition: max-height 0.3s; cursor: pointer; }
.msg.tool .msg-text.expanded { max-height: 600px; }

/* Tool call block */
.tool-call { background: var(--surface2); border: 1px solid var(--border); border-radius: 6px; padding: 8px 12px; margin: 4px 0; font-size: 12px; }
.tool-call-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.tool-name { color: var(--purple); font-weight: 600; }
.tool-status { font-size: 10px; padding: 1px 6px; border-radius: 10px; }
.tool-status.running { background: var(--yellow)20; color: var(--yellow); }
.tool-status.done { background: var(--green)20; color: var(--green); }
.tool-status.error { background: var(--red)20; color: var(--red); }
.tool-args { color: var(--dim); font-size: 11px; max-height: 60px; overflow: hidden; }

/* Code blocks */
.msg-text code { background: var(--code-bg); padding: 1px 4px; border-radius: 3px; font-family: 'SF Mono', Consolas, monospace; color: var(--orange); font-size: 12px; }
.msg-text pre { background: var(--code-bg); padding: 10px 12px; border-radius: 6px; overflow-x: auto; border: 1px solid var(--border); margin: 4px 0; }
.msg-text pre code { background: none; padding: 0; color: var(--text); }

/* INPUT */
#input-area { background: var(--surface); border-top: 1px solid var(--border); padding: 12px 16px; display: flex; gap: 8px; align-items: flex-end; flex-shrink: 0; }
#msg-input { flex: 1; background: var(--surface2); border: 1px solid var(--border); color: var(--text); padding: 9px 12px; border-radius: 8px; font-family: inherit; font-size: 13px; resize: none; min-height: 38px; max-height: 160px; outline: none; line-height: 1.5; transition: border-color 0.2s; }
#msg-input:focus { border-color: var(--accent); }
#msg-input::placeholder { color: var(--dim); }
#send-btn { background: var(--accent); color: #000; border: none; padding: 9px 16px; border-radius: 8px; cursor: pointer; font-weight: 700; font-size: 13px; transition: opacity 0.2s; flex-shrink: 0; }
#send-btn:hover { opacity: 0.85; }
#send-btn:disabled { opacity: 0.4; cursor: default; }

/* RIGHT SIDEBAR */
#sidebar-right { width: 220px; background: var(--surface); border-left: 1px solid var(--border); display: flex; flex-direction: column; overflow: hidden; }
.panel { border-bottom: 1px solid var(--border); }
.panel-header { padding: 8px 12px; font-size: 10px; text-transform: uppercase; color: var(--dim); letter-spacing: 1px; cursor: pointer; display: flex; align-items: center; justify-content: space-between; }
.panel-header:hover { background: var(--surface2); }
.panel-body { padding: 8px 12px; font-size: 11px; color: var(--dim); }

/* BUDDY widget */
#buddy-panel .panel-body { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 12px; }
#buddy-icon { font-size: 32px; }
#buddy-name { color: var(--buddy); font-weight: 600; font-size: 12px; }
#buddy-level { font-size: 10px; color: var(--dim); }
#buddy-mood { font-size: 11px; }
.buddy-bar { width: 100%; background: var(--surface2); border-radius: 4px; height: 4px; overflow: hidden; }
.buddy-bar-fill { height: 100%; background: var(--buddy); border-radius: 4px; transition: width 0.5s; }

/* Session stats */
.stat-row { display: flex; justify-content: space-between; margin-bottom: 3px; }
.stat-key { color: var(--dim); }
.stat-val { color: var(--text); }

/* Quick actions */
#quick-actions { padding: 8px; display: flex; flex-direction: column; gap: 4px; }
.qa-btn { background: none; border: 1px solid var(--border); color: var(--text); padding: 5px 8px; border-radius: 5px; cursor: pointer; font-size: 11px; text-align: left; width: 100%; font-family: inherit; transition: all 0.15s; }
.qa-btn:hover { background: var(--surface2); border-color: var(--accent); color: var(--accent); }

/* Typing indicator */
#typing { display: none; align-items: center; gap: 6px; color: var(--dim); font-size: 12px; padding: 0 16px 8px; }
#typing.visible { display: flex; }
.dot { width: 5px; height: 5px; border-radius: 50%; background: var(--dim); animation: blink 1.2s infinite; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0%,80%,100% { opacity: 0.3; } 40% { opacity: 1; } }

/* Scrollbars */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--dim); }

/* Markdown-ish rendering */
.h1 { font-size: 16px; font-weight: 700; color: var(--text); margin: 8px 0 4px; border-bottom: 1px solid var(--border); padding-bottom: 4px; }
.h2 { font-size: 14px; font-weight: 700; color: var(--text); margin: 6px 0 3px; }
.h3 { font-size: 13px; font-weight: 700; color: var(--accent); margin: 4px 0 2px; }
.bold { font-weight: 700; color: var(--text); }
</style>
</head>
<body>

<div id="header">
  <h1>⚡ QWEN3-CODER ULTIMATE</h1>
  <span class="badge">v9.0</span>
  <span class="badge" id="model-badge">...</span>
  <div id="conn-status">
    <div id="conn-dot"></div>
    <span id="conn-text">Connecting...</span>
  </div>
</div>

<div id="main">
  <!-- File Tree -->
  <div id="sidebar-left">
    <h3>Explorer</h3>
    <div id="file-tree">Loading...</div>
  </div>

  <!-- Chat -->
  <div id="chat-area">
    <div id="messages">
      <div class="msg system">
        <div class="avatar">⚡</div>
        <div class="msg-body">
          <div class="msg-role">system</div>
          <div class="msg-text">QWEN3-CODER ULTIMATE v9.0 — Web UI pronto. Digite sua mensagem abaixo.</div>
        </div>
      </div>
    </div>
    <div id="typing"><div class="dot"></div><div class="dot"></div><div class="dot"></div><span>QWEN pensando...</span></div>
    <div id="input-area">
      <textarea id="msg-input" placeholder="Digite sua mensagem... (Enter para enviar, Shift+Enter para nova linha)" rows="1"></textarea>
      <button id="send-btn">Enviar</button>
    </div>
  </div>

  <!-- Right Sidebar -->
  <div id="sidebar-right">
    <!-- BUDDY -->
    <div class="panel" id="buddy-panel">
      <div class="panel-header" onclick="togglePanel('buddy-body')">BUDDY <span>▾</span></div>
      <div class="panel-body" id="buddy-body">
        <div id="buddy-icon">🐼</div>
        <div id="buddy-name">Pandinha</div>
        <div id="buddy-level">Nível 1 — Filhote</div>
        <div id="buddy-mood">😊 Feliz</div>
        <div class="buddy-bar"><div class="buddy-bar-fill" id="buddy-xp-bar" style="width:0%"></div></div>
      </div>
    </div>

    <!-- Session Stats -->
    <div class="panel">
      <div class="panel-header" onclick="togglePanel('stats-body')">Sessão <span>▾</span></div>
      <div class="panel-body" id="stats-body">
        <div class="stat-row"><span class="stat-key">Turns</span><span class="stat-val" id="stat-turns">0</span></div>
        <div class="stat-row"><span class="stat-key">Tokens</span><span class="stat-val" id="stat-tokens">0</span></div>
        <div class="stat-row"><span class="stat-key">Contexto</span><span class="stat-val" id="stat-ctx">0%</span></div>
        <div class="stat-row"><span class="stat-key">Ferramentas</span><span class="stat-val" id="stat-tools">0</span></div>
        <div class="stat-row"><span class="stat-key">Modelo</span><span class="stat-val" id="stat-model" style="font-size:10px">—</span></div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="panel">
      <div class="panel-header">Ações Rápidas</div>
      <div id="quick-actions">
        <button class="qa-btn" onclick="sendQuick('/tree')">🌳 File Tree</button>
        <button class="qa-btn" onclick="sendQuick('/plan ')">📋 Criar Plano</button>
        <button class="qa-btn" onclick="sendQuick('/debug ')">🐛 Debug</button>
        <button class="qa-btn" onclick="sendQuick('/security ')">🔒 Security Scan</button>
        <button class="qa-btn" onclick="sendQuick('/test ')">🧪 Gerar Testes</button>
        <button class="qa-btn" onclick="sendQuick('/refactor ')">♻ Refatorar</button>
        <button class="qa-btn" onclick="sendQuick('/review ')">👁 Code Review</button>
        <button class="qa-btn" onclick="sendQuick('/buddy')">🐾 BUDDY Status</button>
        <button class="qa-btn" onclick="sendQuick('/allstats')">📊 All Stats</button>
        <button class="qa-btn" onclick="sendQuick('/clear')">🗑 Limpar</button>
      </div>
    </div>
  </div>
</div>

<script>
const messagesEl = document.getElementById('messages');
const inputEl    = document.getElementById('msg-input');
const sendBtn    = document.getElementById('send-btn');
const typingEl   = document.getElementById('typing');
const connDot    = document.getElementById('conn-dot');
const connText   = document.getElementById('conn-text');

let ws = null;
let currentAssistantMsg = null;
let reconnectTimer = null;
let statsInterval = null;

// ── WEBSOCKET ─────────────────────────────────────────────────────────────
function connect() {
  ws = new WebSocket('ws://' + location.host + '/ws');

  ws.onopen = () => {
    connDot.className = 'connected';
    connText.textContent = 'Conectado';
    loadFileTree();
    startStatsPolling();
  };

  ws.onclose = () => {
    connDot.className = 'error';
    connText.textContent = 'Desconectado — reconectando...';
    reconnectTimer = setTimeout(connect, 3000);
  };

  ws.onerror = () => {
    connDot.className = 'error';
  };

  ws.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data);
      handleMessage(data);
    } catch {
      appendToken(ev.data);
    }
  };
}

function handleMessage(data) {
  switch (data.type) {
    case 'token':
      showTyping(true);
      appendToken(data.content);
      break;
    case 'done':
      showTyping(false);
      finalizeAssistant();
      updateStats(data.stats || {});
      updateBuddy(data.buddy || {});
      break;
    case 'tool_call':
      showToolCall(data);
      break;
    case 'tool_result':
      updateToolResult(data);
      break;
    case 'buddy':
      appendBuddyMsg(data.content);
      updateBuddy(data.state || {});
      break;
    case 'kairos':
      appendSystemMsg('KAIROS: ' + data.content, '#d29922');
      break;
    case 'error':
      appendSystemMsg('Erro: ' + data.content, '#f85149');
      showTyping(false);
      break;
    case 'file_tree':
      renderFileTree(data.tree);
      break;
    case 'stats':
      updateStats(data);
      break;
    case 'model':
      document.getElementById('model-badge').textContent = data.name.split('/').pop().substring(0, 20);
      document.getElementById('stat-model').textContent = data.name.split('/').pop().substring(0, 16);
      break;
  }
}

// ── SEND ─────────────────────────────────────────────────────────────────
function send() {
  const text = inputEl.value.trim();
  if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;

  appendUserMsg(text);
  inputEl.value = '';
  inputEl.style.height = 'auto';
  showTyping(true);
  sendBtn.disabled = true;
  currentAssistantMsg = null;

  ws.send(JSON.stringify({ type: 'message', content: text }));
}

function sendQuick(cmd) {
  inputEl.value = cmd;
  inputEl.focus();
  if (cmd.endsWith(' ')) return; // user fills in the rest
  send();
}

// ── MESSAGES ─────────────────────────────────────────────────────────────
function appendUserMsg(text) {
  const el = createMsg('user', '👤', 'Você', escapeHtml(text));
  messagesEl.appendChild(el);
  scrollBottom();
}

function appendToken(token) {
  if (!currentAssistantMsg) {
    const wrapper = document.createElement('div');
    wrapper.className = 'msg assistant';
    wrapper.innerHTML = `<div class="avatar">🤖</div><div class="msg-body"><div class="msg-role">QWEN</div><div class="msg-text" id="current-response"></div></div>`;
    messagesEl.appendChild(wrapper);
    currentAssistantMsg = document.getElementById('current-response');
    scrollBottom();
  }
  currentAssistantMsg.textContent += token;
  if (messagesEl.scrollTop + messagesEl.clientHeight > messagesEl.scrollHeight - 80) scrollBottom();
}

function finalizeAssistant() {
  if (currentAssistantMsg) {
    currentAssistantMsg.innerHTML = renderMarkdown(currentAssistantMsg.textContent);
    currentAssistantMsg = null;
  }
  sendBtn.disabled = false;
}

function showToolCall(data) {
  const id = 'tc-' + data.id;
  const el = document.createElement('div');
  el.className = 'msg tool';
  el.id = id;
  el.innerHTML = `
    <div class="avatar">🔧</div>
    <div class="msg-body">
      <div class="msg-role">Tool Call</div>
      <div class="tool-call">
        <div class="tool-call-header">
          <span class="tool-name">${escapeHtml(data.name)}</span>
          <span class="tool-status running" id="${id}-status">running</span>
        </div>
        <div class="tool-args">${escapeHtml(JSON.stringify(JSON.parse(data.args || '{}'), null, 1).substring(0, 200))}</div>
      </div>
    </div>`;
  messagesEl.appendChild(el);
  scrollBottom();
}

function updateToolResult(data) {
  const statusEl = document.getElementById('tc-' + data.id + '-status');
  if (statusEl) {
    statusEl.textContent = data.error ? 'error' : 'done';
    statusEl.className = 'tool-status ' + (data.error ? 'error' : 'done');
  }
  const el = document.createElement('div');
  el.className = 'msg tool';
  el.innerHTML = `<div class="avatar">↳</div><div class="msg-body"><div class="msg-role">Result</div><div class="msg-text" onclick="this.classList.toggle('expanded')">${escapeHtml((data.result || '').substring(0, 1000))}</div></div>`;
  messagesEl.appendChild(el);
  scrollBottom();
}

function appendBuddyMsg(text) {
  const el = createMsg('buddy', '🐾', 'BUDDY', text);
  messagesEl.appendChild(el);
  scrollBottom();
}

function appendSystemMsg(text, color = '') {
  const el = document.createElement('div');
  el.className = 'msg system';
  el.innerHTML = `<div class="avatar">⚙</div><div class="msg-body"><div class="msg-role">system</div><div class="msg-text" style="color:${color}">${escapeHtml(text)}</div></div>`;
  messagesEl.appendChild(el);
  scrollBottom();
}

function createMsg(cls, icon, role, content) {
  const el = document.createElement('div');
  el.className = 'msg ' + cls;
  el.innerHTML = `<div class="avatar">${icon}</div><div class="msg-body"><div class="msg-role">${role}</div><div class="msg-text">${content}</div></div>`;
  return el;
}

// ── FILE TREE ─────────────────────────────────────────────────────────────
async function loadFileTree() {
  try {
    const r = await fetch('/api/files');
    const data = await r.json();
    renderFileTree(data.tree);
  } catch {}
}

function renderFileTree(items) {
  const el = document.getElementById('file-tree');
  el.innerHTML = '';
  (items || []).forEach(item => {
    const div = document.createElement('div');
    const ext = item.name.split('.').pop();
    div.className = 'tree-item ' + (item.is_dir ? 'dir' : ext);
    div.textContent = (item.is_dir ? '📁 ' : '  ') + item.name;
    div.title = item.path;
    if (!item.is_dir) {
      div.onclick = () => {
        inputEl.value = `/open ${item.path}`;
        send();
      };
    }
    el.appendChild(div);
  });
}

// ── BUDDY ─────────────────────────────────────────────────────────────────
function updateBuddy(state) {
  if (!state || !state.name) return;
  document.getElementById('buddy-icon').textContent  = state.icon  || '🐼';
  document.getElementById('buddy-name').textContent  = state.name  || 'Buddy';
  document.getElementById('buddy-level').textContent = `Nível ${state.level || 1} — ${state.level_name || 'Ovo'}`;
  document.getElementById('buddy-mood').textContent  = state.mood  || '😊';
  const xpPct = Math.min(100, ((state.xp || 0) % 100));
  document.getElementById('buddy-xp-bar').style.width = xpPct + '%';
}

// ── STATS ─────────────────────────────────────────────────────────────────
function updateStats(stats) {
  if (stats.turns   !== undefined) document.getElementById('stat-turns').textContent  = stats.turns;
  if (stats.tokens  !== undefined) document.getElementById('stat-tokens').textContent = stats.tokens.toLocaleString();
  if (stats.ctx_pct !== undefined) document.getElementById('stat-ctx').textContent    = Math.round(stats.ctx_pct * 100) + '%';
  if (stats.tools   !== undefined) document.getElementById('stat-tools').textContent  = stats.tools;
  if (stats.model   !== undefined) document.getElementById('stat-model').textContent  = stats.model.split('/').pop().substring(0, 16);
}

function startStatsPolling() {
  clearInterval(statsInterval);
  statsInterval = setInterval(async () => {
    try {
      const r = await fetch('/api/stats');
      updateStats(await r.json());
    } catch {}
  }, 5000);
}

// ── HELPERS ───────────────────────────────────────────────────────────────
function scrollBottom() {
  requestAnimationFrame(() => { messagesEl.scrollTop = messagesEl.scrollHeight; });
}

function showTyping(visible) {
  typingEl.className = visible ? 'visible' : '';
}

function togglePanel(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = el.style.display === 'none' ? '' : 'none';
}

function escapeHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function renderMarkdown(text) {
  return escapeHtml(text)
    .replace(/^### (.+)$/gm, '<div class="h3">$1</div>')
    .replace(/^## (.+)$/gm, '<div class="h2">$1</div>')
    .replace(/^# (.+)$/gm, '<div class="h1">$1</div>')
    .replace(/\*\*(.+?)\*\*/g, '<span class="bold">$1</span>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/```[\w]*\n?([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
}

// ── INPUT HANDLING ────────────────────────────────────────────────────────
inputEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
});

inputEl.addEventListener('input', () => {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 160) + 'px';
});

sendBtn.addEventListener('click', send);

// ── BOOT ──────────────────────────────────────────────────────────────────
connect();
</script>
</body>
</html>"""


def create_app(qwen_instance=None):
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI not installed. Run: pip install fastapi uvicorn")

    app = FastAPI(title="QWEN3-CODER Ultimate Web UI")
    connections: list[WebSocket] = []

    @app.get("/", response_class=HTMLResponse)
    async def root():
        return HTML

    @app.get("/api/stats")
    async def stats():
        if qwen_instance is None:
            return {}
        s = {}
        ss = getattr(qwen_instance, "sess_state", None)
        if ss:
            s["turns"]   = ss.turn_count
            s["tokens"]  = ss.tokens_used
            s["ctx_pct"] = ss.context_pct
            s["tools"]   = ss.tool_calls_total
            s["model"]   = ss.model or qwen_instance.model
        else:
            s["model"] = getattr(qwen_instance, "model", "unknown")
            s["turns"]  = getattr(qwen_instance, "token_ctr", None) and 0
        return s

    @app.get("/api/files")
    async def files():
        cwd = os.getcwd()
        items = []
        try:
            for entry in sorted(Path(cwd).iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
                if entry.name.startswith(".") or entry.name in ("__pycache__", "node_modules"):
                    continue
                items.append({
                    "name":   entry.name,
                    "path":   str(entry),
                    "is_dir": entry.is_dir(),
                })
                if entry.is_dir():
                    for sub in sorted(entry.iterdir(), key=lambda e: e.name.lower()):
                        if sub.name.startswith(".") or sub.name == "__pycache__":
                            continue
                        items.append({
                            "name":   "  " + sub.name,
                            "path":   str(sub),
                            "is_dir": sub.is_dir(),
                        })
        except Exception:
            pass
        return {"tree": items}

    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket):
        await ws.accept()
        connections.append(ws)

        # Send initial state
        if qwen_instance:
            buddy = getattr(qwen_instance, "buddy", None)
            if buddy:
                await ws.send_json({
                    "type": "buddy",
                    "content": buddy.on_session_start(),
                    "state": _buddy_state(buddy),
                })
            model = getattr(qwen_instance, "model", "")
            await ws.send_json({"type": "model", "name": model})

        try:
            while True:
                data = await ws.receive_json()
                if data.get("type") == "message":
                    await handle_chat(ws, data["content"], qwen_instance)
        except WebSocketDisconnect:
            pass
        finally:
            connections.remove(ws)

    async def handle_chat(ws: WebSocket, user_input: str, qwen):
        if qwen is None:
            await ws.send_json({"type": "error", "content": "QWEN instance not connected."})
            return

        loop = asyncio.get_event_loop()

        def _stream_wrapper():
            import io
            import sys as _sys
            import queue

            q = queue.Queue()

            class StreamCapture(io.TextIOBase):
                def write(self, s):
                    if s.strip():
                        q.put(("token", s))
                    return len(s)

            # Run send_message synchronously in thread, capture stdout
            old_stdout = _sys.stdout
            try:
                _sys.stdout = StreamCapture()
                qwen.send_message(user_input)
            finally:
                _sys.stdout = old_stdout

            q.put(("done", None))
            return q

        try:
            import queue as _queue
            q = _queue.Queue()

            def _run():
                try:
                    import io, sys as _sys

                    class QueueCapture(io.TextIOBase):
                        def write(self, s):
                            if s.strip():
                                q.put(("token", s))
                            return len(s)

                    old = _sys.stdout
                    _sys.stdout = QueueCapture()
                    try:
                        qwen.send_message(user_input)
                    finally:
                        _sys.stdout = old
                    q.put(("done", None))
                except Exception as e:
                    q.put(("error", str(e)))

            t = threading.Thread(target=_run, daemon=True)
            t.start()

            while True:
                try:
                    item = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: q.get(timeout=60)),
                        timeout=65,
                    )
                except asyncio.TimeoutError:
                    break

                kind, val = item
                if kind == "token":
                    await ws.send_json({"type": "token", "content": val})
                elif kind == "done":
                    # Collect stats and buddy state
                    stats_data = {}
                    ss = getattr(qwen, "sess_state", None)
                    if ss:
                        stats_data = {
                            "turns": ss.turn_count, "tokens": ss.tokens_used,
                            "ctx_pct": ss.context_pct, "tools": ss.tool_calls_total,
                            "model": ss.model,
                        }
                    buddy_state = {}
                    buddy = getattr(qwen, "buddy", None)
                    if buddy:
                        buddy_state = _buddy_state(buddy)
                    await ws.send_json({"type": "done", "stats": stats_data, "buddy": buddy_state})
                    break
                elif kind == "error":
                    await ws.send_json({"type": "error", "content": val})
                    break

        except Exception as e:
            await ws.send_json({"type": "error", "content": str(e)})

    return app


def _buddy_state(buddy) -> dict:
    if not buddy:
        return {}
    s = buddy.state
    species = buddy.SPECIES.get(s.species, {})
    return {
        "name":       s.name,
        "icon":       species.get("icon", "🐾"),
        "level":      s.level,
        "level_name": buddy.LEVEL_NAMES[min(s.level, len(buddy.LEVEL_NAMES) - 1)],
        "xp":         s.xp,
        "mood":       buddy.MOODS.get(s.mood, {}).get("icon", "😊") + " " + s.mood,
    }


def run_with_qwen(qwen_instance=None, port: int = 8000, open_browser: bool = True):
    """Start Web UI in background thread. Call from qwen_ultimate."""
    if not FASTAPI_AVAILABLE:
        print("[WebUI] FastAPI not installed. Run: pip install fastapi uvicorn")
        return None

    app = create_app(qwen_instance)

    def _serve():
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")

    t = threading.Thread(target=_serve, daemon=True)
    t.start()

    if open_browser:
        import webbrowser, time
        time.sleep(1.5)
        webbrowser.open(f"http://localhost:{port}")

    print(f"[WebUI] Running at http://localhost:{port}")
    return t


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    app = create_app()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
