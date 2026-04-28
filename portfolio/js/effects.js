/* ============================================================
   EFFECTS — cinema + 3D + surpresas
   carregado APÓS app.js
   ============================================================ */

(() => {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fine    = matchMedia('(hover: hover) and (pointer: fine)').matches;
  const studioCalm = true;

  /* -------------------- BLOB BACKGROUND (SVG) -------------------- */
  const blobSVG = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid slice">
      <defs>
        <radialGradient id="g1" cx="30%" cy="20%">
          <stop offset="0%"  stop-color="#0f7bff" stop-opacity=".62"/>
          <stop offset="100%" stop-color="#0f7bff" stop-opacity="0"/>
        </radialGradient>
        <radialGradient id="g2" cx="80%" cy="30%">
          <stop offset="0%"  stop-color="#8fd3ff" stop-opacity=".42"/>
          <stop offset="100%" stop-color="#8fd3ff" stop-opacity="0"/>
        </radialGradient>
        <radialGradient id="g3" cx="50%" cy="80%">
          <stop offset="0%"  stop-color="#2d64ff" stop-opacity=".36"/>
          <stop offset="100%" stop-color="#2d64ff" stop-opacity="0"/>
        </radialGradient>
        <radialGradient id="g4" cx="20%" cy="65%">
          <stop offset="0%"  stop-color="#d7e8ff" stop-opacity=".18"/>
          <stop offset="100%" stop-color="#d7e8ff" stop-opacity="0"/>
        </radialGradient>
        <filter id="warp" x="-20%" y="-20%" width="140%" height="140%">
          <feTurbulence type="fractalNoise" baseFrequency="0.005 0.012" numOctaves="2" seed="3">
            <animate attributeName="baseFrequency" dur="22s" values="0.005 0.012; 0.011 0.006; 0.005 0.012" repeatCount="indefinite"/>
          </feTurbulence>
          <feDisplacementMap in="SourceGraphic" scale="120"/>
        </filter>
      </defs>
      <g filter="url(#warp)">
        <ellipse class="blob"   cx="350" cy="200" rx="380" ry="320" fill="url(#g1)"/>
        <ellipse class="blob blob-2" cx="900" cy="280" rx="420" ry="350" fill="url(#g2)"/>
        <ellipse class="blob blob-3" cx="600" cy="650" rx="500" ry="380" fill="url(#g3)"/>
        <ellipse class="blob"   cx="200" cy="600" rx="350" ry="280" fill="url(#g4)"/>
      </g>
    </svg>`;
  // Replace existing shader-bg with blob stage
  const oldBg = document.querySelector('.shader-bg');
  if (oldBg) {
    const stage = document.createElement('div');
    stage.className = 'blob-stage';
    stage.setAttribute('aria-hidden', 'true');
    stage.innerHTML = blobSVG;
    oldBg.replaceWith(stage);
  }

  // Add vignette
  if (!document.querySelector('.vignette')) {
    const v = document.createElement('div');
    v.className = 'vignette';
    v.setAttribute('aria-hidden','true');
    document.body.appendChild(v);
  }

  /* -------------------- PARTICLES (fireflies) -------------------- */
  if (!studioCalm && !reduced) {
    const pwrap = document.createElement('div');
    pwrap.className = 'particles';
    pwrap.setAttribute('aria-hidden','true');
    for (let i = 0; i < 18; i++) {
      const s = document.createElement('span');
      const left = Math.random() * 100;
      const dur  = 12 + Math.random() * 18;
      const delay = -Math.random() * dur;
      s.style.left = left + '%';
      s.style.bottom = '-10px';
      s.style.animationDuration = dur + 's';
      s.style.animationDelay    = delay + 's';
      s.style.setProperty('--tx', (Math.random() * 200 - 100) + 'px');
      s.style.opacity = '.6';
      s.style.background = ['#d4a574','#ff6f3d','#a78bfa','#06b6d4'][i % 4];
      pwrap.appendChild(s);
    }
    document.body.appendChild(pwrap);
  }

  /* -------------------- MAGNETIC CURSOR -------------------- */
  if (!studioCalm && fine && !reduced) {
    document.body.classList.add('has-cursor');
    const cur = document.createElement('div');
    cur.className = 'mag-cursor';
    document.body.appendChild(cur);
    let x = innerWidth/2, y = innerHeight/2, tx = x, ty = y;
    addEventListener('mousemove', e => { tx = e.clientX; ty = e.clientY; });
    addEventListener('mousedown', () => cur.classList.add('click'));
    addEventListener('mouseup',   () => cur.classList.remove('click'));
    function tick() {
      x += (tx - x) * .22;
      y += (ty - y) * .22;
      cur.style.transform = `translate(${x}px, ${y}px) translate(-50%,-50%)`;
      requestAnimationFrame(tick);
    }
    tick();
    document.addEventListener('mouseover', e => {
      const i = e.target.closest('a, button, [role=button], input, select, textarea, .video-card, .expert-mini, .style-option, .plan-card, .style-chip');
      cur.classList.toggle('hover', !!i);
    });
  }

  /* -------------------- 3D TILT on .tilt-target / .video-card -------------------- */
  if (!studioCalm && fine && !reduced) {
    document.addEventListener('mousemove', (e) => {
      const card = e.target.closest('.video-card, .plan-card, .stat-card, .offer-card');
      if (!card) return;
      if (!card.classList.contains('tilt-card')) {
        card.classList.add('tilt-card');
        // wrap children in tilt-inner if not already? we apply transform on card itself
      }
      const r = card.getBoundingClientRect();
      const px = (e.clientX - r.left) / r.width;
      const py = (e.clientY - r.top)  / r.height;
      const rx = (py - 0.5) * -10;  // rotateX
      const ry = (px - 0.5) *  12;  // rotateY
      card.classList.add('tilting');
      card.style.transform = `perspective(900px) rotateX(${rx}deg) rotateY(${ry}deg) translateZ(0)`;
      // shine
      card.style.setProperty('--mx', (px*100)+'%');
      card.style.setProperty('--my', (py*100)+'%');
      // ensure shine span exists
      if (!card.querySelector('.tilt-shine')) {
        const sh = document.createElement('div');
        sh.className = 'tilt-shine';
        card.appendChild(sh);
      }
    });
    document.addEventListener('mouseout', (e) => {
      const card = e.target.closest('.video-card, .plan-card, .stat-card, .offer-card');
      if (!card || card.contains(e.relatedTarget)) return;
      card.classList.remove('tilting');
      card.style.transform = '';
    });
  }

  /* -------------------- PARALLAX (hero, bear) -------------------- */
  if (fine && !reduced) {
    let mx = 0, my = 0;
    addEventListener('mousemove', e => {
      mx = (e.clientX / innerWidth  - .5);
      my = (e.clientY / innerHeight - .5);
    });
    function loop() {
      document.querySelectorAll('[data-parallax]').forEach(el => {
        const f = parseFloat(el.dataset.parallax) || 10;
        el.style.transform = `translate3d(${mx * f}px, ${my * f}px, 0)`;
      });
      // background blob subtle parallax
      const stage = document.querySelector('.blob-stage svg');
      if (stage) stage.style.transform = `translate3d(${mx * -30}px, ${my * -30}px, 0)`;
      requestAnimationFrame(loop);
    }
    loop();
  }

  /* -------------------- STATS COUNT-UP ON SCROLL -------------------- */
  function renderStatsHero() {
    const cfg = window.STATE?.config;
    const stats = cfg?.stats;
    if (!stats || !stats.length) return;
    const portfolioTab = document.getElementById('tab-portfolio');
    if (!portfolioTab) return;
    if (document.getElementById('statsHero')) return;
    const owner = cfg.site.owner_name || 'José Victor';
    const html = `
      <section id="statsHero" class="stats-hero">
        <h3 style="font-size: clamp(1.4rem, 2.8vw, 2.2rem); font-weight:900; letter-spacing:0; max-width:24ch; margin-top:1.5rem;">
          Não é talk. É <em style="font-family:'Playfair Display',serif; font-style:italic; background:linear-gradient(120deg,var(--orange-glow),var(--gold-bright)); -webkit-background-clip:text; background-clip:text; color:transparent;">execução.</em>
        </h3>
        <div class="stats-grid">
          ${stats.map((s,i) => `
            <div class="stat-card" data-parallax="${4 + (i%2)*3}">
              <div class="num"><span class="scramble" data-target="${s.value}">0</span><span class="suffix">${s.suffix||''}</span></div>
              <div class="lbl">${s.label}</div>
              <div class="note">${s.note||''}</div>
            </div>
          `).join('')}
        </div>
      </section>
    `;
    // insert after first hero-headline
    const headline = portfolioTab.querySelector('.hero-headline');
    if (headline && headline.nextElementSibling) {
      headline.nextElementSibling.insertAdjacentHTML('afterend', html);
    } else {
      portfolioTab.insertAdjacentHTML('afterbegin', html);
    }
    // count-up: dispara já se já tá visível, senão IntersectionObserver
    const hero = document.getElementById('statsHero');
    const fire = () => hero.querySelectorAll('.scramble').forEach(el => countUp(el));
    const r = hero.getBoundingClientRect();
    const visible = r.top < innerHeight && r.bottom > 0;
    if (visible) {
      // pequeno delay pra animar com a entrada
      setTimeout(fire, 250);
    } else {
      const io = new IntersectionObserver(entries => {
        entries.forEach(en => { if (en.isIntersecting) { fire(); io.disconnect(); } });
      }, { threshold: 0.2 });
      io.observe(hero);
    }
  }

  function countUp(el) {
    const target = parseFloat(el.dataset.target) || 0;
    if (target === 0) { el.textContent = '0'; return; }
    const dur = 1600;
    const start = performance.now();
    function frame(t) {
      const p = Math.min(1, (t - start) / dur);
      const eased = 1 - Math.pow(1-p, 3);
      const v = target * eased;
      el.textContent = target >= 100 ? Math.round(v) : v.toFixed(target % 1 ? 1 : 0);
      if (p < 1) requestAnimationFrame(frame);
      else el.textContent = String(target);
    }
    requestAnimationFrame(frame);
  }

  /* -------------------- TEXT SCRAMBLE ON HEADLINE -------------------- */
  function scrambleText(el, finalText, dur=1200) {
    const chars = '!<>-_\\/[]{}—=+*^?#________';
    const len = finalText.length;
    const start = performance.now();
    function frame(t) {
      const p = Math.min(1, (t - start) / dur);
      let out = '';
      for (let i = 0; i < len; i++) {
        if (i / len < p) out += finalText[i];
        else out += chars[Math.floor(Math.random() * chars.length)];
      }
      el.textContent = out;
      if (p < 1) requestAnimationFrame(frame);
      else el.textContent = finalText;
    }
    requestAnimationFrame(frame);
  }

  /* -------------------- HERO ENHANCEMENT (italic accent + parallax tag) -------------------- */
  function enhanceHero() {
    const cfg = window.STATE?.config;
    const word = cfg?.site?.hero_serif_word || 'viral';
    const heros = document.querySelectorAll('.hero-headline');
    heros.forEach(h => {
      h.setAttribute('data-parallax', '4');
      // wrap word in <em> if not already
      const html = h.innerHTML;
      if (!html.includes('<em>')) {
        const re = new RegExp(`\\b(${word})\\b`, 'i');
        h.innerHTML = html.replace(re, '<em>$1</em>');
      }
    });

    const subs = document.querySelectorAll('.hero-sub');
    subs.forEach(s => s.setAttribute('data-parallax', '8'));
    // ursinho não tem parallax — ele faz roaming próprio
  }

  /* -------------------- PORTAL (apenas accent laranja + parallax) -------------------- */
  function enhancePortal() {
    const portal = document.getElementById('portal');
    const enter  = document.getElementById('enterBtn');
    if (!portal || !enter) return;
    enter.classList.remove('hot');
    // parallax leve no nome
    const name = portal.querySelector('.portal-name');
    if (name) name.setAttribute('data-parallax', '8');
    const tag = portal.querySelector('.portal-tag');
    if (tag)  tag.setAttribute('data-parallax', '4');
    // o app.js cuida do .exiting class — não precisamos de outra animação
  }

  /* -------------------- KONAMI EASTER EGG -------------------- */
  const KONAMI = ['ArrowUp','ArrowUp','ArrowDown','ArrowDown','ArrowLeft','ArrowRight','ArrowLeft','ArrowRight','b','a'];
  let konamiIdx = 0;
  addEventListener('keydown', (e) => {
    const k = e.key;
    if (k === KONAMI[konamiIdx]) {
      konamiIdx++;
      if (konamiIdx === KONAMI.length) {
        konamiIdx = 0;
        triggerKonami();
      }
    } else {
      konamiIdx = (k === KONAMI[0]) ? 1 : 0;
    }
  });
  function triggerKonami() {
    const flash = document.createElement('div');
    flash.className = 'konami-flash';
    flash.innerHTML = '<span>🐻 BOSS BEAR UNLOCKED 🔥</span>';
    document.body.appendChild(flash);
    setTimeout(() => flash.remove(), 2600);
    document.getElementById('bear')?.classList.add('boss');
    if (window.bearSay) {
      window.bearSay('Modo BOSS! Vamos virar!');
    }
    // shower of particles
    for (let i = 0; i < 60; i++) {
      const p = document.createElement('span');
      p.style.cssText = `position:fixed; left:50%; top:50%; width:8px; height:8px; border-radius:50%;
        background:${['#d4a574','#ff3d00','#a78bfa','#06b6d4','#f472b6'][i%5]};
        pointer-events:none; z-index:1000;`;
      document.body.appendChild(p);
      const ang = (i / 60) * Math.PI * 2;
      const dist = 200 + Math.random() * 400;
      p.animate([
        { transform: 'translate(-50%,-50%) scale(1)', opacity: 1 },
        { transform: `translate(calc(-50% + ${Math.cos(ang)*dist}px), calc(-50% + ${Math.sin(ang)*dist}px)) scale(0)`, opacity: 0 }
      ], { duration: 1200 + Math.random()*800, easing: 'cubic-bezier(.22,1,.36,1)' });
      setTimeout(() => p.remove(), 2000);
    }
  }

  /* -------------------- WHATSAPP QR MODAL — SURPRESA -------------------- */
  function setupQRTrigger() {
    // Triple-click on WhatsApp FAB opens QR instead of going direct
    const fab = document.getElementById('waFAB');
    if (!fab) return;
    let clicks = 0, timer = null;
    fab.addEventListener('click', (e) => {
      clicks++;
      clearTimeout(timer);
      if (clicks >= 3) {
        e.preventDefault();
        clicks = 0;
        showQR();
      } else {
        timer = setTimeout(() => clicks = 0, 600);
      }
    });
  }
  function showQR() {
    const cfg = window.STATE?.config?.site || {};
    const num = cfg.whatsapp_digits || '5522981481742';
    const msg = encodeURIComponent('Olá José! Vim do portfólio.');
    const url = `https://wa.me/${num}?text=${msg}`;
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=240x240&data=${encodeURIComponent(url)}&color=050514&bgcolor=ffffff&margin=10`;
    const m = document.createElement('div');
    m.className = 'qr-modal';
    m.innerHTML = `
      <div class="qr-card">
        <button class="close-qr" aria-label="Fechar">✕</button>
        <h3>Escaneia aí 📱</h3>
        <p>Ou usa o link normal — ambos abrem no WhatsApp.</p>
        <img id="qrCode" src="${qrUrl}" alt="QR WhatsApp" width="240" height="240">
        <div class="num">${cfg.whatsapp || '+55 22 98148-1742'}</div>
      </div>`;
    document.body.appendChild(m);
    const close = () => m.remove();
    m.querySelector('.close-qr').addEventListener('click', close);
    m.addEventListener('click', e => { if (e.target === m) close(); });
  }

  /* -------------------- BEAR EMOTION STATE MACHINE -------------------- */
  // Estados emocionais — visíveis via filter, escala, breath e bubble
  const BEAR_STATES = {
    idle:       { hue: 0,   scale: 1.00, breath: '3s', bubble: null,         hop: true },
    curious:    { hue: 35,  scale: 1.06, breath: '1.4s', bubble: 'Que isso? 👀', hop: false },
    happy:      { hue: 25,  scale: 1.05, breath: '1.8s', bubble: 'Eba! 😊',    hop: true },
    excited:    { hue: 15,  scale: 1.12, breath: '0.9s', bubble: 'Boraaa! 🔥', hop: true },
    lovestruck: { hue: 340, scale: 1.10, breath: '1.5s', bubble: 'Aaai 🥺',    hop: false },
    sleepy:     { hue: 220, scale: 0.95, breath: '5s',   bubble: 'Zzz... 😴',  hop: false },
    proud:      { hue: 10,  scale: 1.06, breath: '2s',   bubble: 'Esse rasgou! 😎', hop: true },
    surprised:  { hue: 50,  scale: 1.10, breath: '1.2s', bubble: 'Uau! 😮',     hop: true },
  };

  let currentMood = 'idle';
  let moodLockUntil = 0;

  function setBearMood(mood, lockMs=0) {
    if (Date.now() < moodLockUntil) return;
    if (lockMs) moodLockUntil = Date.now() + lockMs;
    currentMood = mood;
    const s = BEAR_STATES[mood] || BEAR_STATES.idle;
    const bear = document.getElementById('bear');
    if (!bear) return;
    bear.style.setProperty('--bear-scale', s.scale);
    bear.style.setProperty('--bear-breath', s.breath);
    bear.style.filter = `drop-shadow(0 6px 12px rgba(0,0,0,.5)) hue-rotate(${s.hue}deg)`;
    if (s.bubble && window.bearSay) {
      window.bearSay(s.bubble);
      setTimeout(() => window.bearHide && window.bearHide(), 2200);
    }
  }
  // Expor pro app.js usar
  window.bearMood = setBearMood;

  /* -------------------- BEAR ROAMING + HEARTS (dono do projeto) -------------------- */
  function setupRoamingBear() {
    const bear = document.getElementById('bear');
    if (!bear) return;

    // Posiciono via top/left fixos — o CSS faz transform pra animação
    bear.style.bottom = 'auto';
    bear.style.left   = '0';
    bear.style.top    = '0';

    let bx = 0, by = 0;             // posição atual
    let scrollY = window.scrollY;
    let lastScroll = Date.now();

    function moveBear(x, y, hop=true) {
      bx = x; by = y;
      bear.classList.toggle('hopping', hop);
      bear.style.transform = `translate3d(${x}px, ${y}px, 0)`;
      // remove hopping class após anim
      if (hop) setTimeout(() => bear.classList.remove('hopping'), 900);
    }

    // Anchor selectors — pontos de interesse na página
    function getAnchors() {
      const sels = [
        '#statsHero',
        '.video-grid .video-card:nth-child(1)',
        '.video-grid .video-card:nth-child(2)',
        '.budget-calc',
        '.plan-card.highlight',
        '.sobre-photo',
        '#tab-portfolio .hero-headline',
        '#tab-orcamento .hero-headline',
        'footer .foot-links',
        '.app-header .logo'
      ];
      const anchors = [];
      for (const sel of sels) {
        const el = document.querySelector(sel);
        if (!el) continue;
        const r = el.getBoundingClientRect();
        // skip elements offscreen-vertical mais que 200px
        if (r.bottom < -200 || r.top > innerHeight + 800) continue;
        // posição absoluta no documento
        const x = r.left + window.scrollX + (r.width  - 80) * Math.random();
        const y = r.top  + window.scrollY + (r.height - 80) * Math.random();
        // converter pra viewport-fixed (subtrair scroll atual)
        anchors.push({ x: r.left + (r.width - 96) * Math.random() - 8,
                       y: Math.max(60, r.top - 70 + (r.height - 80) * Math.random()) });
      }
      return anchors;
    }

    // inicial: canto inferior esquerdo
    setTimeout(() => moveBear(20, innerHeight - 120, false), 100);

    // Hop a cada 6-10s
    let hopTimer = null;
    function scheduleHop() {
      clearTimeout(hopTimer);
      const delay = 6000 + Math.random() * 4000;
      hopTimer = setTimeout(() => {
        const anchors = getAnchors();
        if (anchors.length) {
          const a = anchors[Math.floor(Math.random() * anchors.length)];
          // jitter
          const x = Math.max(8, Math.min(innerWidth - 100, a.x));
          const y = Math.max(60, Math.min(innerHeight - 100, a.y));
          moveBear(x, y, true);
          // small say sometimes
          if (Math.random() < .3 && window.bearSay) {
            const phrases = ['Olha esse!', 'Curtiu? 🔥', 'Tô vendo tudo 🐻', 'Esse aqui rasgou!', 'Bora!'];
            window.bearSay(phrases[Math.floor(Math.random()*phrases.length)]);
            setTimeout(() => window.bearHide && window.bearHide(), 2200);
          }
        }
        scheduleHop();
      }, delay);
    }
    scheduleHop();

    // Re-aproxima do topo quando scroll muda muito (sem ficar perdido fora da view)
    addEventListener('scroll', () => {
      const now = Date.now();
      const dy = window.scrollY - scrollY;
      scrollY = window.scrollY;
      // se rolou rápido, hop de novo no próximo tick
      if (Math.abs(dy) > 400 && now - lastScroll > 600) {
        lastScroll = now;
        const x = bx;
        const y = Math.max(60, Math.min(innerHeight - 120, by));
        moveBear(x, y, false);
      }
    }, { passive: true });

    addEventListener('resize', () => {
      const x = Math.max(8, Math.min(innerWidth - 100, bx));
      const y = Math.max(60, Math.min(innerHeight - 100, by));
      moveBear(x, y, false);
    });

    // Hover/touch → lovestruck mood + corações
    function emitHeart() {
      const r = bear.getBoundingClientRect();
      const h = document.createElement('div');
      h.className = 'bear-heart';
      h.textContent = ['❤️','💛','🧡','💖'][Math.floor(Math.random()*4)];
      h.style.left = (r.left + r.width/2 - 10) + 'px';
      h.style.top  = (r.top - 10) + 'px';
      h.style.setProperty('--tx', (Math.random()*60 - 30) + 'px');
      document.body.appendChild(h);
      setTimeout(() => h.remove(), 1700);
    }

    let petTimer = null;
    bear.addEventListener('mouseenter', () => {
      setBearMood('lovestruck', 1500);
      emitHeart();
      petTimer = setInterval(emitHeart, 380);
    });
    bear.addEventListener('mouseleave', () => {
      clearInterval(petTimer);
      setTimeout(() => { setBearMood('idle'); window.bearHide && window.bearHide(); }, 800);
    });

    // Touch (mobile)
    bear.addEventListener('touchstart', () => {
      setBearMood('lovestruck', 1500);
      emitHeart();
      petTimer = setInterval(emitHeart, 380);
    }, { passive: true });
    bear.addEventListener('touchend', () => {
      clearInterval(petTimer);
      setTimeout(() => { setBearMood('idle'); window.bearHide && window.bearHide(); }, 800);
    });

    // Mood por tab — usa state machine
    const tabMoods = { portfolio: 'proud', orcamento: 'excited', sobre: 'happy' };
    document.querySelectorAll('.tabs button').forEach(btn => {
      btn.addEventListener('click', () => {
        const m = tabMoods[btn.dataset.tab];
        if (m) setBearMood(m, 1800);
      });
    });

    // Hover em vídeo card → curious
    document.addEventListener('mouseover', (e) => {
      if (e.target.closest('.video-card') && Date.now() > moodLockUntil) {
        setBearMood('curious', 800);
      }
    });

    // Idle detection (sem mouse 25s) → sleepy
    let idleTimer = null;
    function resetIdle() {
      clearTimeout(idleTimer);
      if (currentMood === 'sleepy') setBearMood('idle');
      idleTimer = setTimeout(() => setBearMood('sleepy'), 25000);
    }
    ['mousemove','click','scroll','keydown','touchstart'].forEach(ev =>
      document.addEventListener(ev, resetIdle, { passive: true }));
    resetIdle();

    // ===== SURPRESA: CASINHA DO URSO =====
    // Drag o bear pra cantinho com a casinha (canto inferior direito) → ele dorme lá
    setupBearHouse(bear, moveBear);
  }

  /* -------------------- BEAR HOUSE — surpresa drag pra dormir -------------------- */
  function setupBearHouse(bear, moveBear) {
    // Cria a casinha (visível apenas quando user começa a arrastar o urso)
    const house = document.createElement('div');
    house.className = 'bear-house';
    house.innerHTML = `
      <div class="house-icon">🏠</div>
      <div class="house-label">Solta aqui<br>pra ele descansar</div>
    `;
    document.body.appendChild(house);

    let dragging = false, startX = 0, startY = 0, origBx = 0, origBy = 0;
    let cx = 0, cy = 0;

    function onDown(e) {
      dragging = true;
      const t = e.touches ? e.touches[0] : e;
      startX = t.clientX; startY = t.clientY;
      const m = bear.style.transform.match(/translate3d\((-?\d+(?:\.\d+)?)px,\s*(-?\d+(?:\.\d+)?)px/);
      origBx = m ? parseFloat(m[1]) : 0;
      origBy = m ? parseFloat(m[2]) : 0;
      bear.style.transition = 'none';
      house.classList.add('show');
    }
    function onMove(e) {
      if (!dragging) return;
      const t = e.touches ? e.touches[0] : e;
      cx = origBx + (t.clientX - startX);
      cy = origBy + (t.clientY - startY);
      bear.style.transform = `translate3d(${cx}px, ${cy}px, 0)`;
      // hover sobre casinha?
      const hr = house.getBoundingClientRect();
      const br = bear.getBoundingClientRect();
      const overlap = !(br.right < hr.left || br.left > hr.right ||
                        br.bottom < hr.top || br.top > hr.bottom);
      house.classList.toggle('hover', overlap);
    }
    function onUp() {
      if (!dragging) return;
      dragging = false;
      bear.style.transition = '';
      const hr = house.getBoundingClientRect();
      const br = bear.getBoundingClientRect();
      const overlap = !(br.right < hr.left || br.left > hr.right ||
                        br.bottom < hr.top || br.top > hr.bottom);
      if (overlap) {
        // dropa o urso na casinha
        const x = hr.left + hr.width/2 - 48;
        const y = hr.top + 8;
        moveBear(x, y, true);
        setTimeout(() => {
          setBearMood('sleepy');
          if (window.bearSay) window.bearSay('Casinha aconchegante 💤');
          house.classList.add('occupied');
        }, 200);
      } else {
        house.classList.remove('hover');
      }
      house.classList.remove('show');
      // re-show after 6s if dropped in house
      setTimeout(() => house.classList.remove('occupied'), 8000);
    }

    bear.addEventListener('mousedown', onDown);
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    bear.addEventListener('touchstart', onDown, { passive: true });
    document.addEventListener('touchmove', onMove, { passive: true });
    document.addEventListener('touchend', onUp);
  }

  /* -------------------- BOOT (after main app) -------------------- */
  function bootEffects() {
    enhanceHero();
    enhancePortal();
    renderStatsHero();
    setupQRTrigger();
    // Mantem o urso no cantinho: vivo, mas sem atravessar a UI nem resetar o sono.

    // scramble headlines after small delay
    setTimeout(() => {
      document.querySelectorAll('.hero-headline').forEach(h => {
        // skip if has <em>, scramble plain text part
        const txt = h.textContent;
        if (txt && txt.length < 80) {
          // we'd lose the <em> — instead apply a brief opacity wave
          h.animate([
            { filter: 'blur(8px)', opacity: 0 },
            { filter: 'blur(0)',   opacity: 1 }
          ], { duration: 900, easing: 'cubic-bezier(.22,1,.36,1)' });
        }
      });
    }, 100);
  }

  // wait for app.js to finish boot (it sets window.STATE)
  function ready() {
    if (window.STATE && window.STATE.config) bootEffects();
    else setTimeout(ready, 80);
  }
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(ready, 50);
  } else {
    document.addEventListener('DOMContentLoaded', () => setTimeout(ready, 50));
  }
})();
