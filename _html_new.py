
# This file is merged into tts_studio.py — do not run directly
def _html():  # noqa: C901
    kv  = __import__("json").dumps(KOKORO_VOICES, ensure_ascii=False)
    ev  = __import__("json").dumps(EDGE_VOICES,   ensure_ascii=False)
    eq  = __import__("json").dumps(list(EQ_PRESETS.keys()), ensure_ascii=False)
    er  = __import__("json").dumps(EDGE_RATES, ensure_ascii=False)
    ep  = __import__("json").dumps(EDGE_PITCHES, ensure_ascii=False)
    gpu = f"{GPU_NAME} {GPU_VRAM}".strip()

    H = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>QWN3 Studio — Professional Voice AI</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#020209;
  --s1:#080812;
  --s2:#0d0d1c;
  --s3:#121224;
  --s4:#1a1a30;
  --bd:rgba(255,255,255,0.07);
  --bd2:rgba(255,255,255,0.12);
  --t:#f1f5f9;
  --t2:#94a3b8;
  --t3:#475569;
  --ind:#818cf8;
  --ind2:#6366f1;
  --vio:#a78bfa;
  --cyn:#22d3ee;
  --em:#4ade80;
  --ros:#fb7185;
  --amb:#fbbf24;
  --kok:#818cf8;
  --f5c:#22d3ee;
  --cha:#4ade80;
  --edg:#fbbf24;
  --glow-ind:rgba(99,102,241,0.3);
  --glow-cyn:rgba(6,182,212,0.25);
}
html,body{height:100%;overflow:hidden;font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--t)}

/* ── BG ORBS ─────────────────────────────────────────── */
.orbs{position:fixed;inset:0;pointer-events:none;z-index:0;overflow:hidden}
.orb{position:absolute;border-radius:50%;filter:blur(90px)}
.orb1{width:900px;height:900px;top:-350px;left:-250px;
  background:radial-gradient(circle,rgba(99,102,241,0.13),transparent 65%);
  animation:o1 24s ease-in-out infinite alternate}
.orb2{width:650px;height:650px;bottom:-200px;right:-150px;
  background:radial-gradient(circle,rgba(6,182,212,0.10),transparent 65%);
  animation:o2 19s ease-in-out infinite alternate}
.orb3{width:500px;height:500px;top:45%;left:45%;
  background:radial-gradient(circle,rgba(139,92,246,0.08),transparent 65%);
  animation:o3 28s ease-in-out infinite alternate}
@keyframes o1{0%{transform:translate(0,0)}100%{transform:translate(70px,90px)}}
@keyframes o2{0%{transform:translate(0,0)}100%{transform:translate(-60px,-55px)}}
@keyframes o3{0%{transform:translate(-50%,-50%) scale(1)}100%{transform:translate(calc(-50% + 50px),calc(-50% - 40px)) scale(1.18)}}

/* ── LAYOUT ──────────────────────────────────────────── */
.shell{position:relative;z-index:1;display:flex;flex-direction:column;height:100vh}
header{height:58px;flex-shrink:0;display:flex;align-items:center;gap:16px;padding:0 20px;
  background:rgba(8,8,18,0.8);backdrop-filter:blur(20px);
  border-bottom:1px solid var(--bd)}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none}
.logo-mark{width:34px;height:34px;background:linear-gradient(135deg,#6366f1,#22d3ee);
  border-radius:10px;display:flex;align-items:center;justify-content:center;
  font-size:16px;font-weight:900;color:#fff;flex-shrink:0;
  box-shadow:0 0 20px rgba(99,102,241,0.4)}
.logo-text{font-size:15px;font-weight:800;color:var(--t);letter-spacing:-0.3px}
.logo-ver{font-size:10px;padding:2px 7px;background:rgba(99,102,241,0.15);
  border:1px solid rgba(99,102,241,0.3);border-radius:20px;color:var(--ind);font-weight:600}
.hbadge{padding:4px 12px;background:rgba(255,255,255,0.04);border:1px solid var(--bd);
  border-radius:20px;font-size:11px;color:var(--t2);white-space:nowrap}
.hbadge.live{color:var(--em);border-color:rgba(74,222,128,0.3);background:rgba(74,222,128,0.06)}
.hspacer{flex:1}
.app{display:flex;flex:1;overflow:hidden}

/* ── SIDEBAR ─────────────────────────────────────────── */
nav.sidebar{width:224px;flex-shrink:0;background:rgba(8,8,18,0.6);
  backdrop-filter:blur(20px);border-right:1px solid var(--bd);
  display:flex;flex-direction:column;overflow-y:auto;padding:12px 0}
.nav-sec{padding:10px 16px 5px;font-size:9px;font-weight:700;letter-spacing:2px;
  text-transform:uppercase;color:var(--t3)}
.nav-item{display:flex;align-items:center;gap:10px;padding:9px 16px;margin:1px 8px;
  border-radius:9px;cursor:pointer;color:var(--t2);font-size:12.5px;font-weight:500;
  border:1px solid transparent;transition:all .15s;user-select:none}
.nav-item:hover{background:rgba(255,255,255,0.05);color:var(--t)}
.nav-item.active{background:rgba(99,102,241,0.12);border-color:rgba(99,102,241,0.25);
  color:var(--ind)}
.nav-item .ni{font-size:15px;width:18px;text-align:center;flex-shrink:0}
.nav-bottom{margin-top:auto;padding:12px 8px 4px;border-top:1px solid var(--bd)}

/* ── MAIN ────────────────────────────────────────────── */
main{flex:1;overflow-y:auto;padding:22px 24px}
.page{display:none;max-width:1100px;margin:0 auto}
.page.active{display:block;animation:pfade .2s ease}
@keyframes pfade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.ph{font-size:20px;font-weight:800;margin-bottom:2px;letter-spacing:-0.4px}
.ps{font-size:12px;color:var(--t2);margin-bottom:20px}

/* ── GRID LAYOUTS ────────────────────────────────────── */
.studio-grid{display:grid;grid-template-columns:380px 1fr;gap:18px}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.g3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
@media(max-width:900px){.studio-grid{grid-template-columns:1fr}.g2,.g3,.g4{grid-template-columns:1fr 1fr}}

/* ── CARDS ───────────────────────────────────────────── */
.card{background:rgba(13,13,28,0.75);backdrop-filter:blur(16px);
  border:1px solid var(--bd);border-radius:14px;padding:18px;
  transition:border-color .2s}
.card:hover{border-color:var(--bd2)}
.card+.card{margin-top:14px}
.ct{font-size:10px;font-weight:700;letter-spacing:1.8px;text-transform:uppercase;
  color:var(--t3);margin-bottom:14px}

/* ── ENGINE TILES ────────────────────────────────────── */
.eng-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px}
.eng-tile{background:rgba(255,255,255,0.03);border:1px solid var(--bd);
  border-radius:11px;padding:12px 14px;cursor:pointer;transition:all .18s;
  display:flex;flex-direction:column;gap:5px}
.eng-tile:hover{background:rgba(255,255,255,0.06);border-color:var(--bd2)}
.eng-tile.active-kok{background:rgba(99,102,241,0.12);border-color:rgba(99,102,241,0.4);
  box-shadow:0 0 20px rgba(99,102,241,0.12)}
.eng-tile.active-f5{background:rgba(6,182,212,0.10);border-color:rgba(6,182,212,0.4);
  box-shadow:0 0 20px rgba(6,182,212,0.10)}
.eng-tile.active-cha{background:rgba(74,222,128,0.08);border-color:rgba(74,222,128,0.35);
  box-shadow:0 0 20px rgba(74,222,128,0.08)}
.eng-tile.active-edg{background:rgba(251,191,36,0.08);border-color:rgba(251,191,36,0.35);
  box-shadow:0 0 20px rgba(251,191,36,0.08)}
.eng-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.eng-hd{display:flex;align-items:center;gap:7px;font-size:12px;font-weight:700;color:var(--t)}
.eng-sub{font-size:10px;color:var(--t3);padding-left:15px}

/* ── VOICE GRID ──────────────────────────────────────── */
.vg{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
.vc{background:rgba(255,255,255,0.03);border:1px solid var(--bd);border-radius:10px;
  padding:10px 8px;cursor:pointer;text-align:center;transition:all .15s;
  display:flex;flex-direction:column;align-items:center;gap:5px}
.vc:hover{background:rgba(255,255,255,0.06);border-color:var(--bd2)}
.vc.sel{border-color:var(--ind);background:rgba(99,102,241,0.12)}
.va{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;font-size:11px;font-weight:800;flex-shrink:0}
.va.F{background:linear-gradient(135deg,#6366f1,#a78bfa)}
.va.M{background:linear-gradient(135deg,#0891b2,#22d3ee)}
.vn{font-size:11px;font-weight:600;color:var(--t)}
.vd{font-size:9px;color:var(--t3);line-height:1.3;text-align:center}
.vc.sel .vd{color:var(--ind)}

/* ── FORM ELEMENTS ───────────────────────────────────── */
label{font-size:11px;color:var(--t2);display:block;margin-bottom:5px;margin-top:12px;font-weight:500}
label:first-child{margin-top:0}
select,input[type=text],input[type=number]{width:100%;background:rgba(255,255,255,0.04);
  border:1px solid var(--bd);color:var(--t);padding:9px 12px;border-radius:9px;
  font-size:12px;font-family:inherit;outline:none;transition:border .15s;appearance:none}
select:focus,input:focus{border-color:var(--ind)}
textarea{width:100%;background:rgba(255,255,255,0.03);border:1px solid var(--bd);
  color:var(--t);padding:14px;border-radius:11px;font-size:13px;font-family:inherit;
  outline:none;resize:vertical;min-height:180px;line-height:1.7;transition:border .15s}
textarea:focus{border-color:rgba(99,102,241,0.5);background:rgba(255,255,255,0.04)}
textarea::placeholder{color:var(--t3)}
input[type=range]{width:100%;accent-color:var(--ind);cursor:pointer;height:4px;border-radius:4px;
  background:var(--s4);border:none;padding:0;outline:none}

/* ── SLIDER ROW ──────────────────────────────────────── */
.srow{display:flex;align-items:center;gap:10px;margin-top:4px}
.sv{font-size:11px;color:var(--ind);min-width:38px;text-align:right;font-weight:600}

/* ── TOGGLES ─────────────────────────────────────────── */
.tog-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:8px}
.tog{display:flex;align-items:center;gap:8px;background:rgba(255,255,255,0.03);
  border:1px solid var(--bd);border-radius:9px;padding:9px 11px;cursor:pointer;
  font-size:11px;color:var(--t2);transition:all .15s;user-select:none}
.tog:hover{background:rgba(255,255,255,0.06);color:var(--t)}
.tog.on{border-color:rgba(99,102,241,0.4);background:rgba(99,102,241,0.10);color:var(--ind)}
.tdot{width:7px;height:7px;border-radius:50%;background:var(--s4);flex-shrink:0;transition:.15s}
.tog.on .tdot{background:var(--ind)}

/* ── BUTTONS ─────────────────────────────────────────── */
.gen-btn{width:100%;padding:15px;border:none;border-radius:12px;
  background:linear-gradient(135deg,#4f46e5 0%,#7c3aed 50%,#0e7490 100%);
  background-size:200% 200%;animation:gbg 5s ease infinite;
  color:#fff;font-size:14px;font-weight:700;cursor:pointer;
  position:relative;overflow:hidden;letter-spacing:.4px;margin-top:14px;
  font-family:inherit;transition:transform .2s,box-shadow .2s}
.gen-btn:hover{transform:translateY(-2px);box-shadow:0 10px 35px rgba(99,102,241,0.35)}
.gen-btn:active{transform:translateY(0)}
.gen-btn:disabled{opacity:.45;cursor:default;animation:none;transform:none;box-shadow:none}
.gen-btn::after{content:'';position:absolute;inset:0;
  background:linear-gradient(105deg,transparent 33%,rgba(255,255,255,0.14) 50%,transparent 67%);
  animation:shimmer 3.5s ease-in-out infinite}
@keyframes gbg{0%,100%{background-position:0% 50%}50%{background-position:100% 50%}}
@keyframes shimmer{0%{transform:translateX(-100%)}100%{transform:translateX(100%)}}

.btn-sm{background:rgba(255,255,255,0.05);border:1px solid var(--bd);color:var(--t2);
  padding:7px 14px;border-radius:8px;cursor:pointer;font-size:11px;font-weight:500;
  font-family:inherit;transition:all .15s}
.btn-sm:hover{background:rgba(255,255,255,0.09);border-color:var(--bd2);color:var(--t)}
.btn-sm.primary{background:rgba(99,102,241,0.15);border-color:rgba(99,102,241,0.4);color:var(--ind)}
.btn-sm.primary:hover{background:rgba(99,102,241,0.25)}
.btn-sm.danger{background:rgba(251,113,133,0.08);border-color:rgba(251,113,133,0.3);color:var(--ros)}
.btn-sm.danger:hover{background:rgba(251,113,133,0.16)}
.brow{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px}

/* ── STATUS / TOAST ──────────────────────────────────── */
.status{display:none;align-items:center;gap:9px;padding:10px 14px;border-radius:10px;
  font-size:12px;margin-top:10px}
.status.show{display:flex}
.status.ok{background:rgba(74,222,128,0.08);border:1px solid rgba(74,222,128,0.25);color:var(--em)}
.status.err{background:rgba(251,113,133,0.08);border:1px solid rgba(251,113,133,0.25);color:var(--ros)}
.status.load{background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.25);color:var(--ind)}
.spin{width:14px;height:14px;border:2px solid rgba(99,102,241,0.25);
  border-top-color:var(--ind);border-radius:50%;animation:sp .7s linear infinite;flex-shrink:0}
@keyframes sp{to{transform:rotate(360deg)}}

#toasts{position:fixed;bottom:24px;right:24px;z-index:9999;
  display:flex;flex-direction:column;gap:8px;pointer-events:none}
.toast{background:rgba(13,13,28,0.95);backdrop-filter:blur(20px);
  border:1px solid var(--bd2);border-radius:11px;padding:12px 16px;
  font-size:12px;color:var(--t);display:flex;align-items:center;gap:9px;
  min-width:220px;max-width:320px;pointer-events:auto;
  animation:tin .3s ease;box-shadow:0 8px 32px rgba(0,0,0,0.5)}
.toast.out{animation:tout .3s ease forwards}
@keyframes tin{from{opacity:0;transform:translateX(40px)}to{opacity:1;transform:none}}
@keyframes tout{to{opacity:0;transform:translateX(40px)}}

/* ── AUDIO PLAYER ────────────────────────────────────── */
.player-card{background:rgba(13,13,28,0.85);border:1px solid var(--bd);
  border-radius:14px;padding:18px;margin-top:14px;display:none}
.player-card.show{display:block;animation:pfade .25s ease}
audio{width:100%;height:36px;border-radius:8px;margin-bottom:10px;outline:none;
  filter:invert(0.9) hue-rotate(180deg) saturate(0.8)}
canvas#wv{width:100%;height:64px;border-radius:10px;background:rgba(255,255,255,0.02);
  cursor:pointer;display:block}
.ameta{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:12px}
.am{background:rgba(255,255,255,0.03);border:1px solid var(--bd);border-radius:9px;
  padding:9px;text-align:center}
.am-v{font-size:15px;font-weight:700;color:var(--t)}
.am-l{font-size:9px;color:var(--t3);text-transform:uppercase;letter-spacing:1px;margin-top:2px}

/* ── WAVEFORM LOADING ────────────────────────────────── */
.wv-loader{width:100%;height:64px;border-radius:10px;background:rgba(255,255,255,0.02);
  display:flex;align-items:center;justify-content:center;gap:3px;padding:8px}
.wvb{width:4px;border-radius:3px;background:linear-gradient(to top,var(--ind2),var(--cyn));
  animation:wvp 1s ease-in-out infinite}
@keyframes wvp{0%,100%{transform:scaleY(.15)}50%{transform:scaleY(1)}}

/* ── UPLOAD ZONE ─────────────────────────────────────── */
.upzone{border:2px dashed var(--bd);border-radius:11px;padding:28px;
  text-align:center;cursor:pointer;position:relative;transition:all .2s}
.upzone:hover,.upzone.drag{border-color:var(--ind);background:rgba(99,102,241,0.05)}
.upzone.has{border-color:var(--em);background:rgba(74,222,128,0.05)}
.upzone input{position:absolute;inset:0;opacity:0;cursor:pointer}
.upzone .up-ico{font-size:30px;display:block;margin-bottom:8px}
.upzone p{font-size:12px;color:var(--t2)}

/* ── CHAR COUNT ──────────────────────────────────────── */
.cbar{display:flex;justify-content:space-between;font-size:10px;color:var(--t3);margin-top:5px}
.cbar span{color:var(--ind);font-weight:600}

/* ── HISTORY ITEM ────────────────────────────────────── */
.hi{background:rgba(255,255,255,0.03);border:1px solid var(--bd);border-radius:10px;
  padding:11px 14px;display:flex;align-items:center;gap:10px;margin-bottom:7px;
  transition:border-color .15s}
.hi:hover{border-color:var(--bd2)}
.htxt{flex:1;font-size:11px;color:var(--t2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.hbdg{padding:2px 8px;border-radius:10px;font-size:9px;font-weight:600;flex-shrink:0}
.hbdg.kokoro{background:rgba(99,102,241,0.15);color:var(--ind)}
.hbdg.f5{background:rgba(6,182,212,0.15);color:var(--cyn)}
.hbdg.chatterbox{background:rgba(74,222,128,0.12);color:var(--em)}
.hbdg.edge{background:rgba(251,191,36,0.12);color:var(--amb)}

/* ── STAT CARD ───────────────────────────────────────── */
.sc{background:rgba(255,255,255,0.03);border:1px solid var(--bd);border-radius:12px;
  padding:18px;text-align:center}
.sn{font-size:28px;font-weight:800;
  background:linear-gradient(135deg,var(--ind),var(--cyn));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:4px}
.sl{font-size:10px;color:var(--t3);text-transform:uppercase;letter-spacing:1.2px}

/* ── ENGINE PANEL ────────────────────────────────────── */
.ep{display:none}.ep.act{display:block}

/* ── SEARCH ──────────────────────────────────────────── */
.search-box{width:100%;background:rgba(255,255,255,0.04);border:1px solid var(--bd);
  color:var(--t);padding:9px 14px;border-radius:9px;font-size:12px;
  font-family:inherit;outline:none;margin-bottom:14px;transition:border .15s}
.search-box:focus{border-color:var(--ind)}

/* ── SCROLLBAR ───────────────────────────────────────── */
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.1);border-radius:4px}
::-webkit-scrollbar-track{background:transparent}

/* ── BATCH TABLE ─────────────────────────────────────── */
.bt-row{display:flex;align-items:center;gap:8px;padding:8px 12px;
  background:rgba(255,255,255,0.03);border:1px solid var(--bd);
  border-radius:9px;margin-bottom:6px;font-size:11px}
.bt-ok{color:var(--em)}.bt-err{color:var(--ros)}

/* ── COST BANNER ─────────────────────────────────────── */
.cost-banner{background:linear-gradient(135deg,rgba(99,102,241,0.08),rgba(6,182,212,0.06));
  border:1px solid rgba(99,102,241,0.2);border-radius:11px;padding:14px 16px;
  display:none;margin-top:10px}
.cost-banner.show{display:block;animation:pfade .2s ease}
</style>
</head>
<body>
<div class="orbs">
  <div class="orb orb1"></div>
  <div class="orb orb2"></div>
  <div class="orb orb3"></div>
</div>
<div class="shell">

<!-- HEADER -->
<header>
  <div class="logo">
    <div class="logo-mark">Q</div>
    <span class="logo-text">QWN3 STUDIO</span>
    <span class="logo-ver">v5.0</span>
  </div>
  <div class="hspacer"></div>
  <div class="hbadge live" id="b-eng">carregando engines...</div>
  <div class="hbadge" id="b-gpu">__GPU__</div>
</header>

<div class="app">
<!-- SIDEBAR -->
<nav class="sidebar">
  <div class="nav-sec">Gerar</div>
  <div class="nav-item active" data-page="studio">
    <span class="ni">⚡</span>Studio
  </div>
  <div class="nav-item" data-page="clone">
    <span class="ni">🔬</span>Clonar Voz
  </div>
  <div class="nav-item" data-page="batch">
    <span class="ni">🚀</span>Batch
  </div>
  <div class="nav-item" data-page="podcast">
    <span class="ni">🎙</span>Podcast
  </div>
  <div class="nav-sec">Gerenciar</div>
  <div class="nav-item" data-page="vbank">
    <span class="ni">🗄️</span>Banco de Vozes
  </div>
  <div class="nav-item" data-page="history">
    <span class="ni">📋</span>Histórico
  </div>
  <div class="nav-item" data-page="projects">
    <span class="ni">📁</span>Projetos
  </div>
  <div class="nav-item" data-page="pron">
    <span class="ni">📖</span>Pronúncia
  </div>
  <div class="nav-sec">Análise</div>
  <div class="nav-item" data-page="stats">
    <span class="ni">📊</span>Analytics
  </div>
  <div class="nav-item" data-page="api">
    <span class="ni">🔌</span>API Docs
  </div>
  <div class="nav-bottom">
    <div style="font-size:10px;color:var(--t3);text-align:center">
      Sem limites · $0.00 · 100% local
    </div>
  </div>
</nav>

<main>

<!-- ══ STUDIO ══════════════════════════════════════════ -->
<div id="page-studio" class="page active">
  <div class="ph">⚡ Studio</div>
  <div class="ps">Síntese profissional · 4 engines · Sem limite de tamanho</div>
  <div class="studio-grid">

    <!-- LEFT PANEL -->
    <div>
      <div class="card">
        <div class="ct">Engine de Voz</div>
        <div class="eng-grid">
          <div class="eng-tile active-kok" data-eng="kokoro" onclick="setEng(this,'kokoro')">
            <div class="eng-hd"><div class="eng-dot" style="background:var(--kok)"></div>Kokoro</div>
            <div class="eng-sub">Qualidade máxima · Local</div>
          </div>
          <div class="eng-tile" data-eng="f5" onclick="setEng(this,'f5')">
            <div class="eng-hd"><div class="eng-dot" style="background:var(--f5c)"></div>F5-TTS</div>
            <div class="eng-sub">Clone zero-shot</div>
          </div>
          <div class="eng-tile" data-eng="chatterbox" onclick="setEng(this,'chatterbox')">
            <div class="eng-hd"><div class="eng-dot" style="background:var(--cha)"></div>Chatterbox</div>
            <div class="eng-sub">Controle emocional</div>
          </div>
          <div class="eng-tile" data-eng="edge" onclick="setEng(this,'edge')">
            <div class="eng-hd"><div class="eng-dot" style="background:var(--edg)"></div>Edge TTS</div>
            <div class="eng-sub">322 vozes Microsoft</div>
          </div>
        </div>

        <!-- Kokoro params -->
        <div id="ep-kokoro" class="ep act">
          <div class="ct" style="margin-bottom:10px">Voz Kokoro</div>
          <div class="vg" id="kvg"></div>
          <label>Velocidade</label>
          <div class="srow">
            <input type="range" id="k-spd" min="0.5" max="2" step="0.05" value="1"
              oninput="document.getElementById('k-sv').textContent=this.value+'x'">
            <span class="sv" id="k-sv">1.0x</span>
          </div>
        </div>

        <!-- F5 params -->
        <div id="ep-f5" class="ep">
          <div style="font-size:11px;color:var(--t2);margin-bottom:10px">
            Grave 5–30s de qualquer voz e clone instantaneamente
          </div>
          <div class="upzone" id="f5-uz">
            <input type="file" id="f5-ref" accept="audio/*" onchange="onUp(this,'f5-uz','f5-lbl')">
            <span class="up-ico">🎤</span>
            <p id="f5-lbl">Arraste o áudio de referência aqui</p>
          </div>
          <label>Transcrição do áudio (melhora muito a qualidade)</label>
          <textarea id="f5-rt" rows="2" placeholder="O que o áudio diz..."></textarea>
        </div>

        <!-- Chatterbox params -->
        <div id="ep-chatterbox" class="ep">
          <div class="upzone" id="cb-uz">
            <input type="file" id="cb-ref" accept="audio/*" onchange="onUp(this,'cb-uz','cb-lbl')">
            <span class="up-ico">🎭</span>
            <p id="cb-lbl">Referência de voz (opcional)</p>
          </div>
          <label>Intensidade emocional</label>
          <div class="srow">
            <input type="range" id="cb-ex" min="0" max="1" step="0.05" value="0.5"
              oninput="document.getElementById('cb-ev').textContent=this.value">
            <span class="sv" id="cb-ev">0.5</span>
          </div>
        </div>

        <!-- Edge params -->
        <div id="ep-edge" class="ep">
          <label>Voz Microsoft</label>
          <select id="edge-v"></select>
          <label>Velocidade</label>
          <select id="edge-r"></select>
          <label>Tom (pitch)</label>
          <select id="edge-p"></select>
        </div>
      </div>

      <!-- FX CARD -->
      <div class="card">
        <div class="ct">Processamento de Áudio</div>
        <label>Pitch (semitons)</label>
        <div class="srow">
          <input type="range" id="g-pitch" min="-6" max="6" step="0.5" value="0"
            oninput="document.getElementById('g-pv').textContent=this.value">
          <span class="sv" id="g-pv">0</span>
        </div>
        <label>EQ Preset</label>
        <select id="g-eq"></select>
        <div class="tog-grid" style="margin-top:12px">
          <div class="tog" onclick="tog(this,'normalize')"><div class="tdot"></div>Normalizar</div>
          <div class="tog" onclick="tog(this,'trim')"><div class="tdot"></div>Cortar Silêncio</div>
          <div class="tog" onclick="tog(this,'reverb')"><div class="tdot"></div>Reverb</div>
          <div class="tog" onclick="tog(this,'echo')"><div class="tdot"></div>Echo</div>
          <div class="tog" onclick="tog(this,'denoise')"><div class="tdot"></div>Denoise</div>
          <div class="tog" onclick="tog(this,'compress')"><div class="tdot"></div>Compressão</div>
          <div class="tog" onclick="tog(this,'fade')"><div class="tdot"></div>Fade In/Out</div>
          <div class="tog" onclick="tog(this,'padding')"><div class="tdot"></div>Padding</div>
        </div>
        <div style="margin-top:12px" class="tog-grid">
          <div class="tog" onclick="tog(this,'export_mp3')"><div class="tdot"></div>Exportar MP3</div>
          <div class="tog" onclick="tog(this,'generate_srt')"><div class="tdot"></div>Legendas SRT</div>
        </div>
      </div>
    </div>

    <!-- RIGHT PANEL -->
    <div>
      <div class="card">
        <div class="ct">Texto</div>
        <textarea id="g-txt" placeholder="Escreva o texto para sintetizar...&#10;&#10;Ctrl+Enter para gerar."
          oninput="onTxt(this)"></textarea>
        <div class="cbar">
          <span id="g-words"></span>
          <span><span id="g-cnt" style="color:var(--ind)">0</span> chars</span>
        </div>
        <button class="gen-btn" id="g-btn" onclick="doGen()">⚡ GERAR ÁUDIO</button>
      </div>

      <div id="g-status" class="status"></div>

      <!-- PLAYER -->
      <div id="g-player" class="player-card">
        <audio id="g-audio" controls></audio>
        <div id="g-wv-wrap">
          <canvas id="wv" height="64"></canvas>
        </div>
        <div class="ameta" id="g-ameta"></div>
        <div class="brow">
          <a id="g-dl" class="btn-sm" download>💾 WAV</a>
          <a id="g-dl-mp3" class="btn-sm" style="display:none" download>🎵 MP3</a>
          <a id="g-dl-srt" class="btn-sm" style="display:none" download>📄 SRT</a>
          <button class="btn-sm primary" onclick="saveToBank()">🗄️ Salvar Voz</button>
          <button class="btn-sm" onclick="showCost()">💰 vs ElevenLabs</button>
        </div>
        <div id="g-cost" class="cost-banner"></div>
      </div>
    </div>
  </div>
</div>

<!-- ══ CLONE ═══════════════════════════════════════════ -->
<div id="page-clone" class="page">
  <div class="ph">🔬 Clonar Voz</div>
  <div class="ps">F5-TTS ou Chatterbox · Qualquer áudio · Zero treinamento</div>
  <div class="g2">
    <div class="card">
      <label>Engine de Clonagem</label>
      <select id="cl-eng">
        <option value="f5">F5-TTS — Máxima fidelidade</option>
        <option value="chatterbox">Chatterbox — Controle emocional</option>
      </select>
      <label>Áudio de referência</label>
      <div class="upzone" id="cl-uz">
        <input type="file" id="cl-ref" accept="audio/*" onchange="onUp(this,'cl-uz','cl-lbl')">
        <span class="up-ico">🎤</span>
        <p id="cl-lbl">Qualquer áudio · Sem limite de tamanho</p>
      </div>
      <label>Transcrição do áudio (melhora F5-TTS)</label>
      <textarea id="cl-rt" rows="2" placeholder="O que o áudio de referência diz..."></textarea>
      <label>Texto novo para sintetizar</label>
      <textarea id="cl-txt" rows="4" placeholder="Este texto será falado com a voz clonada..."></textarea>
      <button class="gen-btn" id="cl-btn" onclick="doClone()">🔬 CLONAR E GERAR</button>
    </div>
    <div>
      <div id="cl-status" class="status"></div>
      <div id="cl-player" class="player-card">
        <audio id="cl-audio" controls></audio>
        <div class="brow"><a id="cl-dl" class="btn-sm" download>💾 Baixar WAV</a></div>
      </div>
    </div>
  </div>
</div>

<!-- ══ BATCH ════════════════════════════════════════════ -->
<div id="page-batch" class="page">
  <div class="ph">🚀 Batch — Geração em Massa</div>
  <div class="ps">Centenas de áudios · Sem filas · Sem limites</div>
  <div class="g2">
    <div class="card">
      <label>Engine</label>
      <select id="bt-eng">
        <option value="kokoro">Kokoro</option>
        <option value="edge">Edge TTS</option>
      </select>
      <label>Voz Kokoro (se selecionado)</label>
      <select id="bt-v"></select>
      <label>Textos (um por linha)</label>
      <textarea id="bt-txt" rows="10" placeholder="Linha 1: primeiro áudio&#10;Linha 2: segundo áudio&#10;..."></textarea>
      <button class="gen-btn" id="bt-btn" onclick="doBatch()">🚀 GERAR TUDO</button>
    </div>
    <div>
      <div id="bt-status" class="status"></div>
      <div id="bt-results"></div>
    </div>
  </div>
</div>

<!-- ══ PODCAST ══════════════════════════════════════════ -->
<div id="page-podcast" class="page">
  <div class="ph">🎙 Podcast — Múltiplos Locutores</div>
  <div class="ps">Crie diálogos e podcasts com vozes diferentes</div>
  <div class="card">
    <div class="ct">Script</div>
    <div id="pod-lines"></div>
    <div class="brow">
      <button class="btn-sm primary" onclick="addPodLine()">+ Linha</button>
      <button class="btn-sm" onclick="doPodcast()">🎙 Gerar Podcast</button>
    </div>
  </div>
  <div id="pod-status" class="status" style="margin-top:12px"></div>
  <div id="pod-player" class="player-card">
    <audio id="pod-audio" controls></audio>
    <div class="brow"><a id="pod-dl" class="btn-sm" download>💾 Baixar</a></div>
  </div>
</div>

<!-- ══ VOICE BANK ═══════════════════════════════════════ -->
<div id="page-vbank" class="page">
  <div class="ph">🗄️ Banco de Vozes</div>
  <div class="ps">Salve e reutilize configurações de voz perfeitas</div>
  <div class="g2">
    <div class="card">
      <div class="ct">Nova Voz</div>
      <label>Nome da Voz</label>
      <input type="text" id="vb-name" placeholder="Ex: Narrador Documentário">
      <label>Descrição</label>
      <input type="text" id="vb-desc" placeholder="Quando usar...">
      <button class="btn-sm primary" style="width:100%;margin-top:12px" onclick="saveVoice()">
        💾 Salvar Voz Atual
      </button>
    </div>
    <div>
      <div class="ct">Vozes Salvas</div>
      <div id="vb-list"></div>
    </div>
  </div>
</div>

<!-- ══ HISTORY ══════════════════════════════════════════ -->
<div id="page-history" class="page">
  <div class="ph">📋 Histórico</div>
  <div class="ps">Todos os áudios gerados · Busca · Reexportar</div>
  <div style="margin-bottom:14px;display:flex;gap:10px;align-items:center">
    <input class="search-box" id="h-q" placeholder="Buscar no histórico..." oninput="loadHistory()"
      style="margin-bottom:0;max-width:320px">
    <a class="btn-sm" href="/api/history/export" download>📥 Exportar CSV</a>
  </div>
  <div id="h-list"></div>
</div>

<!-- ══ PROJECTS ═════════════════════════════════════════ -->
<div id="page-projects" class="page">
  <div class="ph">📁 Projetos</div>
  <div class="ps">Salve estados completos do estúdio — volte onde parou</div>
  <div class="g2">
    <div class="card">
      <div class="ct">Salvar Projeto</div>
      <label>Nome do Projeto</label>
      <input type="text" id="pj-name" placeholder="Meu Projeto">
      <button class="btn-sm primary" style="width:100%;margin-top:12px" onclick="saveProject()">
        💾 Salvar Projeto Atual
      </button>
    </div>
    <div>
      <div class="ct">Projetos Salvos</div>
      <div id="pj-list"></div>
    </div>
  </div>
</div>

<!-- ══ PRONUNCIAÇÃO ═════════════════════════════════════ -->
<div id="page-pron" class="page">
  <div class="ph">📖 Dicionário de Pronúncia</div>
  <div class="ps">Corrija pronúncias específicas de palavras técnicas ou nomes</div>
  <div class="g2">
    <div class="card">
      <label>Palavra</label>
      <input type="text" id="pr-w" placeholder="Ex: API">
      <label>Pronúncia fonética</label>
      <input type="text" id="pr-p" placeholder="Ex: A-P-I">
      <button class="btn-sm primary" style="width:100%;margin-top:12px" onclick="addPron()">
        + Adicionar
      </button>
    </div>
    <div>
      <div class="ct">Dicionário</div>
      <div id="pr-list"></div>
    </div>
  </div>
</div>

<!-- ══ STATS ════════════════════════════════════════════ -->
<div id="page-stats" class="page">
  <div class="ph">📊 Analytics</div>
  <div class="ps">Métricas de uso e economia vs serviços pagos</div>
  <div class="g3" id="st-cards"></div>
  <div class="card" style="margin-top:16px" id="st-cost"></div>
</div>

<!-- ══ API ══════════════════════════════════════════════ -->
<div id="page-api" class="page">
  <div class="ph">🔌 API Reference</div>
  <div class="ps">REST API local — integre com qualquer sistema</div>
  <div class="card">
    <div class="ct">Endpoints</div>
    <pre style="font-size:11px;color:var(--t2);line-height:2;background:var(--s3);padding:16px;border-radius:9px;overflow-x:auto">
POST /api/generate
  { "engine": "kokoro|f5|chatterbox|edge",
    "text": "...",
    "params": { "voice": "af_heart", "speed": 1.0 },
    "opts": { "normalize": true, "trim": true } }

POST /api/generate/clone
  multipart/form-data: text, engine, audio_ref (file), ref_text

POST /api/batch
  { "engine": "...", "texts": ["...", "..."], "params": {...} }

POST /api/podcast
  { "script": [{"text":"...","engine":"kokoro","voice":"af_heart"}] }

GET  /api/history          GET  /api/stats
GET  /api/voices/saved     POST /api/voices/saved
GET  /api/projects         POST /api/projects
GET  /api/pronunciations   POST /api/pronunciations
GET  /api/audio/{filename}
    </pre>
  </div>
</div>

</main>
</div><!-- .app -->
</div><!-- .shell -->

<div id="toasts"></div>

<script>
// ── DATA (injected by server) ─────────────────────────
const KV = __KV__;
const EV = __EV__;
const EQ = __EQ__;
const ER = __ER__;
const EP = __EP__;

// ── STATE ─────────────────────────────────────────────
let curEng = 'kokoro';
let curKV  = 'af_heart';
let curEV  = 'pt-BR-FranciscaNeural';
let toggs  = {};
let lastRes = null;
let wvRaf = null;
let wvCtx = null;

// ── NAVIGATION ────────────────────────────────────────
document.querySelectorAll('.nav-item').forEach(el => {
  el.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(x => x.classList.remove('active'));
    el.classList.add('active');
    const pg = el.dataset.page;
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('page-'+pg).classList.add('active');
    if (pg==='history') loadHistory();
    if (pg==='stats') loadStats();
    if (pg==='vbank') loadVBank();
    if (pg==='projects') loadProjects();
    if (pg==='pron') loadPron();
  });
});

// ── ENGINE SELECTOR ───────────────────────────────────
function setEng(el, name) {
  curEng = name;
  document.querySelectorAll('.eng-tile').forEach(t => {
    t.className = 'eng-tile';
  });
  const map = {kokoro:'active-kok',f5:'active-f5',chatterbox:'active-cha',edge:'active-edg'};
  el.classList.add(map[name]||'');
  document.querySelectorAll('.ep').forEach(p => p.classList.remove('act'));
  document.getElementById('ep-'+name).classList.add('act');
}

// ── VOICE GRID ────────────────────────────────────────
function buildKVG() {
  const vg = document.getElementById('kvg');
  Object.entries(KV).forEach(([k, v]) => {
    const d = document.createElement('div');
    d.className = 'vc' + (k===curKV?' sel':'');
    d.innerHTML = `<div class="va ${v.gender}">${v.label[0]}</div>
      <div class="vn">${v.label}</div>
      <div class="vd">${v.desc.substring(0,22)}</div>`;
    d.onclick = () => {
      document.querySelectorAll('.vc').forEach(x=>x.classList.remove('sel'));
      d.classList.add('sel'); curKV = k;
    };
    vg.appendChild(d);
  });
}

// ── EDGE SELECTS ──────────────────────────────────────
function buildEdge() {
  const vs = document.getElementById('edge-v');
  Object.entries(EV).forEach(([k,v]) => {
    const o = document.createElement('option');
    o.value = k; o.textContent = `${v.label} (${v.lang})`;
    vs.appendChild(o);
  });
  const rs = document.getElementById('edge-r');
  ER.forEach(r => { const o=document.createElement('option'); o.value=r; o.textContent=r; rs.appendChild(o); });
  rs.value = '+0%';
  const ps = document.getElementById('edge-p');
  EP.forEach(p => { const o=document.createElement('option'); o.value=p; o.textContent=p; ps.appendChild(o); });
  ps.value = '+0Hz';
}

// ── EQ SELECT ─────────────────────────────────────────
function buildEQ() {
  const s = document.getElementById('g-eq');
  EQ.forEach(e => { const o=document.createElement('option'); o.value=e; o.textContent=e; s.appendChild(o); });
  // batch voice
  const bv = document.getElementById('bt-v');
  Object.entries(KV).forEach(([k,v])=>{ const o=document.createElement('option'); o.value=k; o.textContent=v.label; bv.appendChild(o); });
}

// ── TOGGLES ───────────────────────────────────────────
function tog(el, name) {
  el.classList.toggle('on');
  toggs[name] = el.classList.contains('on');
}

// ── TEXT INPUT ────────────────────────────────────────
function onTxt(el) {
  const c = el.value.length;
  const w = el.value.trim().split(/\s+/).filter(Boolean).length;
  document.getElementById('g-cnt').textContent = c;
  document.getElementById('g-words').textContent = w ? w+' palavras' : '';
  localStorage.setItem('qwn3_draft', el.value);
}

// ── FILE UPLOAD ───────────────────────────────────────
function onUp(inp, zoneId, lblId) {
  const f = inp.files[0];
  if (!f) return;
  document.getElementById(zoneId).classList.add('has');
  document.getElementById(lblId).textContent = '✓ ' + f.name;
}

// ── STATUS ────────────────────────────────────────────
function setStatus(id, type, msg) {
  const el = document.getElementById(id);
  el.className = 'status show ' + type;
  el.innerHTML = type==='load'
    ? `<div class="spin"></div>${msg}`
    : `<span style="font-size:15px">${type==='ok'?'✓':'✕'}</span>${msg}`;
}
function clrStatus(id) {
  document.getElementById(id).className = 'status';
}

// ── TOAST ─────────────────────────────────────────────
function toast(msg, icon='✓', dur=3000) {
  const t = document.createElement('div');
  t.className = 'toast';
  t.innerHTML = `<span style="font-size:16px">${icon}</span>${msg}`;
  document.getElementById('toasts').appendChild(t);
  setTimeout(() => {
    t.classList.add('out');
    setTimeout(() => t.remove(), 300);
  }, dur);
}

// ── WAVEFORM CANVAS ───────────────────────────────────
function initWV() {
  const c = document.getElementById('wv');
  const dpr = window.devicePixelRatio || 1;
  c.width  = c.offsetWidth * dpr;
  c.height = c.offsetHeight * dpr;
  wvCtx = c.getContext('2d');
  wvCtx.scale(dpr, dpr);
  return wvCtx;
}

function drawWVBars(ctx, data, loading) {
  const W = ctx.canvas.offsetWidth || ctx.canvas.width;
  const H = ctx.canvas.offsetHeight || ctx.canvas.height;
  ctx.clearRect(0, 0, W, H);
  const n = data.length || 80;
  const bw = W / n * 0.55;
  const gap = W / n * 0.45;
  const t = Date.now();
  for (let i = 0; i < n; i++) {
    let h;
    if (loading) {
      h = (Math.sin(t * 0.003 + i * 0.35) * 0.4 + 0.6) * H * 0.75;
    } else {
      h = Math.max((data[i] || 0) * H * 0.92, 2);
    }
    const x = i * (bw + gap);
    const y = (H - h) / 2;
    const grad = ctx.createLinearGradient(0, y, 0, y+h);
    grad.addColorStop(0, '#818cf8');
    grad.addColorStop(1, '#22d3ee');
    ctx.fillStyle = grad;
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(x, y, Math.max(bw,1.5), h, 2);
    else ctx.rect(x, y, Math.max(bw,1.5), h);
    ctx.fill();
  }
}

function animWV(data, loading) {
  if (!wvCtx) initWV();
  if (wvRaf) cancelAnimationFrame(wvRaf);
  if (loading) {
    const loop = () => { drawWVBars(wvCtx, [], true); wvRaf = requestAnimationFrame(loop); };
    loop();
  } else {
    if (wvRaf) cancelAnimationFrame(wvRaf);
    drawWVBars(wvCtx, data, false);
  }
}

// ── GENERATE ─────────────────────────────────────────
async function doGen() {
  const txt = document.getElementById('g-txt').value.trim();
  if (!txt) { toast('Escreva um texto primeiro', '✕'); return; }
  const btn = document.getElementById('g-btn');
  btn.disabled = true;
  setStatus('g-status','load','Gerando com '+curEng+'...');
  document.getElementById('g-player').classList.remove('show');

  let params = {};
  if (curEng==='kokoro') {
    params = { voice: curKV, speed: parseFloat(document.getElementById('k-spd').value) };
  } else if (curEng==='edge') {
    params = {
      voice: document.getElementById('edge-v').value,
      rate:  document.getElementById('edge-r').value,
      pitch: document.getElementById('edge-p').value
    };
  } else if (curEng==='f5') {
    const f = document.getElementById('f5-ref').files[0];
    if (!f) { btn.disabled=false; toast('Selecione um áudio de referência','✕'); clrStatus('g-status'); return; }
    return doCloneFrom('f5', txt, f, document.getElementById('f5-rt').value);
  } else if (curEng==='chatterbox') {
    const f = document.getElementById('cb-ref').files[0];
    return doCloneFrom('chatterbox', txt, f, '', parseFloat(document.getElementById('cb-ex').value));
  }

  const opts = Object.assign({}, toggs, {
    pitch: parseFloat(document.getElementById('g-pitch').value),
    eq: document.getElementById('g-eq').value
  });

  // show waveform loader
  const pc = document.getElementById('g-player');
  pc.classList.add('show');
  if (!wvCtx) initWV(); else { if(wvRaf) cancelAnimationFrame(wvRaf); }
  animWV([], true);

  try {
    const res = await fetch('/api/generate', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({engine:curEng, text:txt, params, opts})
    });
    const d = await res.json();
    if (d.error) throw new Error(d.error);
    renderResult(d);
    setStatus('g-status','ok',`✓ ${d.stats.duration_s}s gerado em ${d.duration_s}s · ${d.engine} · ${d.voice}`);
    toast('Áudio gerado com sucesso', '🎵');
  } catch(e) {
    setStatus('g-status','err', e.message);
    animWV([], false);
    toast('Erro: '+e.message, '✕', 5000);
  }
  btn.disabled = false;
}

async function doCloneFrom(eng, text, file, rtext, exag=0.5) {
  const fd = new FormData();
  fd.append('text', text);
  fd.append('engine', eng);
  fd.append('ref_text', rtext||'');
  fd.append('exaggeration', exag);
  if (file) fd.append('audio_ref', file);

  const pc = document.getElementById('g-player');
  pc.classList.add('show');
  if (!wvCtx) initWV();
  animWV([], true);

  try {
    const res = await fetch('/api/generate/clone', {method:'POST', body:fd});
    const d = await res.json();
    if (d.error) throw new Error(d.error);
    renderResult(d);
    setStatus('g-status','ok','✓ Voz clonada com sucesso');
    toast('Voz clonada!', '🔬');
  } catch(e) {
    setStatus('g-status','err', e.message);
    toast('Erro: '+e.message, '✕', 5000);
  }
  document.getElementById('g-btn').disabled = false;
}

function renderResult(d) {
  lastRes = d;
  const b64 = 'data:audio/wav;base64,' + d.audio_b64;
  const aud = document.getElementById('g-audio');
  aud.src = b64;

  // waveform
  animWV(d.waveform || [], false);

  // meta
  const s = d.stats || {};
  const metas = [
    {v: s.duration_s+'s', l:'Duração'},
    {v: s.peak_db+'dB', l:'Peak'},
    {v: (s.sample_rate/1000)+'kHz', l:'Sample Rate'},
    {v: d.engine, l:'Engine'},
  ];
  document.getElementById('g-ameta').innerHTML = metas.map(m =>
    `<div class="am"><div class="am-v">${m.v}</div><div class="am-l">${m.l}</div></div>`
  ).join('');

  // download links
  const dlw = document.getElementById('g-dl');
  dlw.href = b64; dlw.download = d.filename || 'audio.wav';

  if (d.exports && d.exports.mp3) {
    const dlm = document.getElementById('g-dl-mp3');
    dlm.href = '/api/audio/'+d.exports.mp3.split(/[\\/]/).pop();
    dlm.style.display = '';
  }
  if (d.exports && d.exports.srt) {
    const dls = document.getElementById('g-dl-srt');
    dls.href = '/api/audio/'+d.exports.srt.split(/[\\/]/).pop();
    dls.style.display = '';
  }
}

function showCost() {
  if (!lastRes) return;
  const c = lastRes.cost || {};
  const el = document.getElementById('g-cost');
  el.classList.add('show');
  el.innerHTML = `
    <div style="font-size:12px;line-height:2.2;color:var(--t2)">
      ElevenLabs cobraria: <b style="color:var(--ros)">$${c.elevenlabs_usd||0}</b>
      por ${c.chars||0} chars<br>
      QWN3-TTS: <b style="color:var(--em)">$0.00</b> — economia de
      <b style="color:var(--ind)">100%</b>
    </div>`;
}

// ── CLONE PAGE ───────────────────────────────────────
async function doClone() {
  const file = document.getElementById('cl-ref').files[0];
  if (!file) { toast('Selecione um áudio de referência','✕'); return; }
  const txt = document.getElementById('cl-txt').value.trim();
  if (!txt) { toast('Escreva o texto','✕'); return; }
  const eng = document.getElementById('cl-eng').value;
  document.getElementById('cl-btn').disabled = true;
  setStatus('cl-status','load','Clonando voz...');
  const fd = new FormData();
  fd.append('text',txt); fd.append('engine',eng);
  fd.append('ref_text', document.getElementById('cl-rt').value);
  fd.append('audio_ref', file);
  try {
    const d = await (await fetch('/api/generate/clone',{method:'POST',body:fd})).json();
    if (d.error) throw new Error(d.error);
    const b = 'data:audio/wav;base64,'+d.audio_b64;
    document.getElementById('cl-audio').src = b;
    document.getElementById('cl-dl').href = b;
    document.getElementById('cl-dl').download = d.filename||'clone.wav';
    document.getElementById('cl-player').classList.add('show');
    setStatus('cl-status','ok','Voz clonada com sucesso!');
    toast('Clonagem concluída!','🔬');
  } catch(e) {
    setStatus('cl-status','err', e.message);
    toast('Erro: '+e.message,'✕',5000);
  }
  document.getElementById('cl-btn').disabled = false;
}

// ── BATCH ─────────────────────────────────────────────
async function doBatch() {
  const lines = document.getElementById('bt-txt').value.split('\\n').filter(l=>l.trim());
  if (!lines.length) { toast('Adicione textos','✕'); return; }
  const eng = document.getElementById('bt-eng').value;
  const params = eng==='kokoro' ? {voice: document.getElementById('bt-v').value} : {};
  document.getElementById('bt-btn').disabled = true;
  setStatus('bt-status','load','Gerando '+lines.length+' áudios...');
  document.getElementById('bt-results').innerHTML = '';
  try {
    const d = await (await fetch('/api/batch',{
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({engine:eng, texts:lines, params, opts:{}})
    })).json();
    const div = document.getElementById('bt-results');
    d.results.forEach(r => {
      div.innerHTML += `<div class="bt-row">
        <span class="${r.ok?'bt-ok':'bt-err'}">${r.ok?'✓':'✕'}</span>
        <span style="flex:1;font-size:11px;color:var(--t2)">${r.text}</span>
        ${r.ok ? `<span style="font-size:10px;color:var(--t3)">${r.audio_s}s</span>
          <a class="btn-sm" href="/api/audio/${r.filename}" download>⬇</a>` : ''}
      </div>`;
    });
    setStatus('bt-status','ok',`${d.results.filter(r=>r.ok).length}/${d.total} gerados`);
  } catch(e) {
    setStatus('bt-status','err', e.message);
  }
  document.getElementById('bt-btn').disabled = false;
}

// ── PODCAST ───────────────────────────────────────────
function addPodLine() {
  const id = Date.now();
  const div = document.createElement('div');
  div.id = 'pl-'+id;
  div.style.cssText = 'display:flex;gap:8px;margin-bottom:8px;align-items:flex-start';
  const voiceOpts = Object.entries(KV).map(([k,v])=>`<option value="${k}">${v.label}</option>`).join('');
  div.innerHTML = `
    <select style="width:130px;flex-shrink:0">${voiceOpts}</select>
    <textarea rows="2" placeholder="Fala do locutor..." style="flex:1;min-height:52px"></textarea>
    <button class="btn-sm danger" onclick="document.getElementById('pl-${id}').remove()">✕</button>`;
  document.getElementById('pod-lines').appendChild(div);
}

async function doPodcast() {
  const lines = document.getElementById('pod-lines').querySelectorAll('div[id^="pl-"]');
  const script = [...lines].map(l => ({
    voice: l.querySelector('select').value,
    text:  l.querySelector('textarea').value.trim(),
    engine:'kokoro'
  })).filter(s=>s.text);
  if (!script.length) { toast('Adicione linhas ao script','✕'); return; }
  setStatus('pod-status','load','Gerando podcast...');
  try {
    const d = await (await fetch('/api/podcast',{
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({script})
    })).json();
    if (d.error) throw new Error(d.error);
    const b = 'data:audio/wav;base64,'+d.audio_b64;
    document.getElementById('pod-audio').src = b;
    document.getElementById('pod-dl').href = b;
    document.getElementById('pod-dl').download = d.filename||'podcast.wav';
    document.getElementById('pod-player').classList.add('show');
    setStatus('pod-status','ok','Podcast gerado: '+d.duration_s+'s');
    toast('Podcast pronto!','🎙');
  } catch(e) { setStatus('pod-status','err',e.message); }
}

// ── VOICE BANK ────────────────────────────────────────
async function saveToBank() {
  const name = prompt('Nome para esta configuração de voz:');
  if (!name) return;
  const params = curEng==='kokoro'
    ? {voice:curKV, speed:parseFloat(document.getElementById('k-spd').value)}
    : curEng==='edge'
    ? {voice:document.getElementById('edge-v').value, rate:document.getElementById('edge-r').value, pitch:document.getElementById('edge-p').value}
    : {};
  await fetch('/api/voices/saved',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({name, engine:curEng, params, description:name})
  });
  toast('Voz salva!','🗄️');
}

async function saveVoice() {
  const name = document.getElementById('vb-name').value.trim();
  if (!name) { toast('Escreva um nome','✕'); return; }
  const params = curEng==='kokoro'
    ? {voice:curKV, speed:parseFloat(document.getElementById('k-spd').value)}
    : {};
  await fetch('/api/voices/saved',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({name, engine:curEng, params, description:document.getElementById('vb-desc').value})
  });
  toast('Voz salva!','🗄️'); loadVBank();
}

async function loadVBank() {
  const data = await fetch('/api/voices/saved').then(r=>r.json()).catch(()=>[]);
  const div = document.getElementById('vb-list');
  div.innerHTML = '';
  if (!data.length) { div.innerHTML='<div style="color:var(--t3);font-size:12px">Nenhuma voz salva.</div>'; return; }
  data.forEach(v => {
    const el = document.createElement('div');
    el.className = 'hi';
    el.innerHTML = `<span class="hbdg ${v.engine}">${v.engine}</span>
      <span class="htxt">${v.name}</span>
      <span style="font-size:10px;color:var(--t3)">${v.used}x</span>
      <button class="btn-sm danger" onclick="delVoice('${v.id}')">✕</button>`;
    div.appendChild(el);
  });
}

async function delVoice(id) {
  await fetch('/api/voices/saved/'+id, {method:'DELETE'});
  loadVBank(); toast('Voz removida','🗑️');
}

// ── HISTORY ───────────────────────────────────────────
async function loadHistory() {
  const q = document.getElementById('h-q')?.value||'';
  const data = await fetch('/api/history?q='+encodeURIComponent(q)).then(r=>r.json()).catch(()=>[]);
  const div = document.getElementById('h-list');
  div.innerHTML = '';
  if (!data.length) { div.innerHTML='<div style="color:var(--t3);font-size:12px">Nenhum histórico.</div>'; return; }
  data.forEach(h => {
    const el = document.createElement('div');
    el.className='hi';
    el.innerHTML = `<span class="hbdg ${h.engine||''}">${h.engine||'?'}</span>
      <span class="htxt">${h.text||''}</span>
      <span style="font-size:10px;color:var(--t3)">${(h.audio_s||0).toFixed?h.audio_s.toFixed(1)+'s':''}</span>
      ${h.path?`<a class="btn-sm" href="/api/audio/${h.path.split(/[\\/]/).pop()}" download>⬇</a>`:''}
      <button class="btn-sm danger" onclick="delHist('${h.id}')">✕</button>`;
    div.appendChild(el);
  });
}

async function delHist(id) {
  await fetch('/api/history/'+id,{method:'DELETE'}); loadHistory();
}

// ── PROJECTS ──────────────────────────────────────────
async function saveProject() {
  const name = document.getElementById('pj-name').value.trim();
  if (!name) { toast('Escreva um nome','✕'); return; }
  const data = { engine:curEng, voice:curKV, text:document.getElementById('g-txt').value };
  await fetch('/api/projects',{
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({name, data})
  });
  toast('Projeto salvo!','📁'); loadProjects();
}

async function loadProjects() {
  const names = await fetch('/api/projects').then(r=>r.json()).catch(()=>[]);
  const div = document.getElementById('pj-list');
  div.innerHTML = '';
  if (!names.length) { div.innerHTML='<div style="color:var(--t3);font-size:12px">Nenhum projeto.</div>'; return; }
  names.forEach(name => {
    const el=document.createElement('div');
    el.className='hi';
    el.innerHTML = `<span class="htxt">📁 ${name}</span>
      <button class="btn-sm" onclick="loadProject('${name}')">Abrir</button>
      <button class="btn-sm danger" onclick="delProject('${name}')">✕</button>`;
    div.appendChild(el);
  });
}

async function loadProject(name) {
  const d = await fetch('/api/projects/'+name).then(r=>r.json()).catch(()=>({}));
  if (d.text) document.getElementById('g-txt').value = d.text;
  toast('Projeto carregado: '+name,'📁');
  document.querySelector('[data-page="studio"]').click();
}

async function delProject(name) {
  await fetch('/api/projects/'+name,{method:'DELETE'}); loadProjects();
}

// ── PRONUNCIAÇÃO ──────────────────────────────────────
async function loadPron() {
  const data = await fetch('/api/pronunciations').then(r=>r.json()).catch(()=>({}));
  const div = document.getElementById('pr-list');
  div.innerHTML = '';
  if (!Object.keys(data).length) { div.innerHTML='<div style="color:var(--t3);font-size:12px">Dicionário vazio.</div>'; return; }
  Object.entries(data).forEach(([w,p]) => {
    const el=document.createElement('div');
    el.className='hi';
    el.innerHTML=`<span class="htxt"><b>${w}</b> → ${p}</span>
      <button class="btn-sm danger" onclick="delPron('${w}')">✕</button>`;
    div.appendChild(el);
  });
}

async function addPron() {
  const w=document.getElementById('pr-w').value.trim();
  const p=document.getElementById('pr-p').value.trim();
  if(!w||!p) return;
  await fetch('/api/pronunciations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({word:w,phonetic:p})});
  document.getElementById('pr-w').value='';
  document.getElementById('pr-p').value='';
  loadPron(); toast('Pronúncia adicionada','📖');
}

async function delPron(w) {
  await fetch('/api/pronunciations/'+encodeURIComponent(w),{method:'DELETE'}); loadPron();
}

// ── STATS ─────────────────────────────────────────────
async function loadStats() {
  const d = await fetch('/api/stats').then(r=>r.json()).catch(()=>({}));
  const cards=[
    {v:d.total_generated||0,l:'Áudios Gerados'},
    {v:d.total_chars||0,l:'Chars Processados'},
    {v:(d.total_seconds||0)+'s',l:'Áudio Total'},
    {v:d.history_count||0,l:'No Histórico'},
    {v:d.projects||0,l:'Projetos'},
    {v:'$0.00',l:'Custo Total'},
  ];
  document.getElementById('st-cards').innerHTML = cards.map(c=>
    `<div class="sc"><div class="sn">${c.v}</div><div class="sl">${c.l}</div></div>`
  ).join('');
  const cost = ((d.total_chars||0)/1000*0.30).toFixed(4);
  document.getElementById('st-cost').innerHTML = `
    <div class="ct">Economia vs ElevenLabs</div>
    <div style="font-size:13px;line-height:2.4;color:var(--t2)">
      ElevenLabs custaria: <b style="color:var(--ros)">$${cost}</b><br>
      QWN3-TTS: <b style="color:var(--em)">$0.00</b><br>
      Economia total: <b style="color:var(--ind);font-size:16px">$${cost} (100%)</b>
    </div>`;
}

// ── ENGINE STATUS POLL ────────────────────────────────
async function pollInfo() {
  try {
    const i = await fetch('/api/info').then(r=>r.json());
    const el = document.getElementById('b-eng');
    if (i.engines_loaded.length) {
      el.textContent = i.engines_loaded.length + ' engines · online';
      el.className = 'hbadge live';
    } else {
      el.textContent = 'carregando engines...';
    }
  } catch {}
}

// ── KEYBOARD SHORTCUTS ────────────────────────────────
document.addEventListener('keydown', e => {
  if ((e.ctrlKey||e.metaKey) && e.key==='Enter') {
    e.preventDefault();
    if (document.getElementById('page-studio').classList.contains('active')) doGen();
  }
});

// ── INIT ──────────────────────────────────────────────
window.onload = () => {
  buildKVG();
  buildEdge();
  buildEQ();

  // restore draft
  const draft = localStorage.getItem('qwn3_draft');
  if (draft) {
    const ta = document.getElementById('g-txt');
    ta.value = draft;
    onTxt(ta);
  }

  // poll engine status
  pollInfo();
  setInterval(pollInfo, 8000);

  // add default podcast line
  addPodLine();

  // resize canvas on window resize
  window.addEventListener('resize', () => { wvCtx = null; });
};
</script>
</body>
</html>"""
    return (H
        .replace("__KV__", kv)
        .replace("__EV__", ev)
        .replace("__EQ__", eq)
        .replace("__ER__", er)
        .replace("__EP__", ep)
        .replace("__GPU__", gpu)
    )
