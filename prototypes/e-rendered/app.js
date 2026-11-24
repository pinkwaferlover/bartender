/* Prototype E: Rendered. Prototype B's layout, logic and zoom model, with the bar rendered in Blender.
   The camera is still the SVG viewBox, in B's world units. The background is one rendered picture per camera
   position; touchables and bottles are separate rendered layers; Dionysus is his own layer (dio-layer.js). */
/* Halo's step glyphs (src/anim.js, copied unchanged). Loaded first, before anything can open a recipe. */
const ANIM = (function loadAnim() { const s = document.createElement('script'); s.src = 'anim.js'; s.async = false; document.head.append(s); return s; })();
const $ = s => document.querySelector(s);
const NS = 'http://www.w3.org/2000/svg';
const svg = $('#scene');
const el = (tag, attrs = {}, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
const lerp = (a, b, t) => a + (b - a) * t;
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
const seg = (p, a, b) => clamp((p - a) / (b - a), 0, 1);
const isPhone = () => innerWidth <= 640;
const RM = reduceMotion();
const wait = ms => new Promise(r => setTimeout(r, ms));
const esc = t => String(t).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

/* ---------------- Halo's drawings and pieces (src/app.js), renamed where E already uses the name ---------------- */
/* The brief's four Feels drawn with Halo's feel icons */
const FEEL_ICON4 = { rich: 'sweet', sharp: 'fresh', bitter: 'bitter', dry: 'strong' };
const feelIcon = (r, h) => feelIco(FEEL_ICON4[feelOf(r)], h);
const stepsTotal = r => r.steps.reduce((a, s) => a + (s[1] || 0), 0);
const LONGEST = Math.max(...R.map(stepsTotal));
const fmt = s => s >= 60 ? `${Math.floor(s / 60)} min${s % 60 ? ' ' + (s % 60) + ' s' : ''}` : `${s} s`;
/* pies are static labels: prep time against the longest recipe, seconds for a shake or stir. Never a countdown (R6). */
const pie = (f, size, col = 'var(--acc)') => `<svg viewBox="0 0 40 40" width="${size}" height="${size}" aria-hidden="true"><circle cx="20" cy="20" r="17" fill="var(--faint)"/><path d="${arc(20, 20, 17, 0, Math.min(f, 1))}" fill="${col}"/></svg>`;
const timePie = (r, size) => pie(stepsTotal(r) / LONGEST, size);
const ICON = {
  back: `<svg viewBox="0 0 40 40" width="28" height="28" aria-hidden="true"><path d="M24 8 L12 20 L24 32" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  mic: `<svg viewBox="0 0 40 40" width="24" height="24" aria-hidden="true"><rect x="14" y="5" width="12" height="20" rx="6" fill="currentColor"/><path d="M9 19 q0 11 11 11 q11 0 11 -11 M20 30 v6" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/></svg>`,
};
/* Halo's two dice, drawn in 3D. They sit in panels; on the counter the rendered panther and die stay the touchable. */
const PIPS = { 1: [5], 2: [1, 9], 3: [1, 5, 9], 4: [1, 3, 7, 9], 5: [1, 3, 5, 7, 9], 6: [1, 3, 4, 6, 7, 9] };
const dFace = (n, cls) => `<div class="face ${cls}">${[1, 2, 3, 4, 5, 6, 7, 8, 9].map(p => `<i${PIPS[n].includes(p) ? ' class="on"' : ''}></i>`).join('')}</div>`;
const oneDie = k => `<div class="die ${k}">${dFace(1, 'f1')}${dFace(6, 'f6')}${dFace(2, 'f2')}${dFace(5, 'f5')}${dFace(3, 'f3')}${dFace(4, 'f4')}</div>`;
const diceHTML = size => `<span class="dice" style="--ds:${size}px"><span class="pair">${oneDie('d1')}${oneDie('d2')}</span></span>`;
function rollDice(box, then) {
  if (!box || box.classList.contains('rolling')) return;
  if (RM) return then();
  box.classList.add('rolling');
  box.querySelectorAll('.die').forEach((d, n) => {
    const x = 720 + 90 * Math.floor(Math.random() * 4), y = 720 + 90 * Math.floor(Math.random() * 4), z = n ? -30 : 25;
    d.style.transition = 'transform 1.05s cubic-bezier(.15,.75,.25,1)';
    d.style.transform = `rotateX(${x}deg) rotateY(${y}deg) rotateZ(${z}deg)`;
  });
  setTimeout(then, 1150);
}
/* Halo's strip: follows the finger, carries momentum, settles on a card. A drag never counts as a tap. */
class Strip {
  constructor(host, o) {
    this.h = host; this.track = host.querySelector('.track'); this.items = [...this.track.children]; this.n = this.items.length;
    this.w = o.itemW; this.gap = o.gap ?? 22; this.pad = o.pad ?? 24;
    this.items.forEach(e => { e.style.width = this.w + 'px'; });
    this.W = host.clientWidth; this.step = this.w + this.gap;
    this.maxX = this.pad; this.minX = Math.min(this.maxX, this.W - this.pad - this.n * this.step + this.gap);
    this.x = this.maxX; this.raf = 0; this.dragged = false;
    this.bind(); this.draw();
  }
  clamp(x) { return Math.max(this.minX, Math.min(this.maxX, x)); }
  draw() { this.items.forEach((e, k) => { e.style.transform = `translate3d(${(this.x + k * this.step).toFixed(1)}px,0,0)`; }); }
  animateTo(target) {
    cancelAnimationFrame(this.raf);
    if (RM) { this.x = target; return this.draw(); }
    const x0 = this.x, t0 = performance.now(), dur = 520, ez = t => 1 - Math.pow(1 - t, 4);
    const tick = now => { const t = Math.min(1, (now - t0) / dur); this.x = x0 + (target - x0) * ez(t); this.draw(); if (t < 1) this.raf = requestAnimationFrame(tick); };
    this.raf = requestAnimationFrame(tick);
  }
  settle(v) { const proj = this.x + v * 260, k = Math.round((this.maxX - proj) / this.step); this.animateTo(this.clamp(this.maxX - k * this.step)); }
  bind() {
    let p = null, samples = [];
    this.h.addEventListener('pointerdown', e => { cancelAnimationFrame(this.raf); this.dragged = false; p = { x: e.clientX, x0: this.x, moved: false, id: e.pointerId }; samples = [[performance.now(), this.x]]; });
    this.h.addEventListener('pointermove', e => {
      if (!p) return; const dx = e.clientX - p.x;
      if (Math.abs(dx) > 6 && !p.moved) { p.moved = this.dragged = true; try { this.h.setPointerCapture(p.id); } catch (_) {} }
      if (!p.moved) return;
      let x = p.x0 + dx; if (x > this.maxX) x = this.maxX + (x - this.maxX) * .35; if (x < this.minX) x = this.minX + (x - this.minX) * .35;
      this.x = x; this.draw(); samples.push([performance.now(), x]); if (samples.length > 6) samples.shift();
    });
    const up = () => {
      if (!p) return; const was = p; p = null; if (!was.moved) return;
      const [t0, x0] = samples[0], [t1, x1] = samples[samples.length - 1]; this.settle(t1 > t0 ? (x1 - x0) / (t1 - t0) : 0);
    };
    this.h.addEventListener('pointerup', up); this.h.addEventListener('pointercancel', () => { if (p) { p = null; this.settle(0); } });
    this.h.addEventListener('click', e => { if (this.dragged) { e.stopPropagation(); e.preventDefault(); this.dragged = false; } }, true);
    let wt; this.h.addEventListener('wheel', e => { if (Math.abs(e.deltaX) <= Math.abs(e.deltaY)) return; e.preventDefault(); cancelAnimationFrame(this.raf); this.x = this.clamp(this.x - e.deltaX); this.draw(); clearTimeout(wt); wt = setTimeout(() => this.settle(0), 120); }, { passive: false });
    /* keyboard: a focused card is brought into view by the strip, not by the browser scrolling it */
    this.h.addEventListener('focusin', e => { this.h.scrollLeft = 0; const k = this.items.indexOf(e.target.closest('.track > *')); if (k < 0) return;
      const left = this.x + k * this.step; if (left < this.pad || left + this.w > this.W - this.pad) this.animateTo(this.clamp(this.pad - k * this.step)); });
  }
}
const img = (L, parent, attrs = {}) => el('image', { href: L.src, x: L.x, y: L.y, width: L.w, height: L.h, preserveAspectRatio: 'none', ...attrs }, parent);

/* ---------------- The rendered layers ---------------- */
const BG = {};
(function build() {
  const g = $('#bg');
  BG.bar = img(LAYERS.bg.bar, g, { id: 'bg-bar' });
  ['shelf', 'mid', 'menu', 'sign', 'signOff'].forEach(k => { BG[k] = img(LAYERS.bg[k], g, { class: 'patch', id: 'bg-' + k, decoding: 'async' }); });
  $('#behindRect').setAttribute('height', 3000 + LAYERS.counterBackY);
  img(LAYERS.touch.honey, $('#honey'));
  img(LAYERS.touch.menu, $('#menu'));
  img(LAYERS.touch.panther, $('#pantherBody'));
  const d = LAYERS.touch.dice;
  img({ ...d, x: -d.w / 2, y: -d.h / 2 }, $('#dice'));
})();
const HONEY_AT = [LAYERS.touch.honey.x + LAYERS.touch.honey.w * .45, LAYERS.touch.honey.y + LAYERS.touch.honey.h * .18];
/* which close-up render each camera position uses */
const PATCH = { intro: 'sign', shelf: 'shelf', talk: 'mid', recipe: 'mid', choice: 'mid', menu: 'menu' };
function showPatch(shot) {
  const want = PATCH[shot];
  ['shelf', 'mid', 'menu', 'sign', 'signOff'].forEach(k => BG[k].classList.toggle('on', k === want || (want === 'sign' && k === 'signOff')));
}

/* ---------------- Bottles: one rendered bottle per Style, true colour, no logos ---------------- */
function drawShelf(animate) {
  const g = $('#bottles'); g.innerHTML = '';
  const list = shelfBottles(); const n = list.length;
  const gap = 96, left = 480, right = 1120, avail = right - left - gap;
  const step = Math.min(46, avail / Math.max(n, 1));
  const half = Math.ceil(n / 2);
  list.forEach((b, i) => {
    const side = i < half ? 0 : 1, j = side ? i - half : i, span = side ? (n - half) : half;
    const x = side ? 800 + gap / 2 + j * step + 2 : 800 - gap / 2 - (span - j) * step + 2;
    const L = LAYERS.bottles[b.k]; if (!L) return;
    const outer = el('g', { transform: `translate(${(x + step / 2 - L.ax).toFixed(1)} 0)` }, g);
    const inner = el('g', { class: 'btl' + (BAR.filled && !b.out ? '' : ' dusty') }, outer);
    img(L, inner);
    el('title', {}, inner).textContent = `${b.style} (${FAMILIES[b.family] || b.family})${b.out ? ', run out' : ''}`;
    if (animate && !RM) inner.style.animation = `bdrop .7s ${0.06 * i}s cubic-bezier(.3,1.4,.5,1) both`;
  });
}
drawShelf();

/* ---------------- Camera: the viewBox ---------------- */
const MENU_R = LAYERS.touch.menu;
const SHOTS = {
  intro: { L: [440, 40, 720, 200], P: [452, 40, 696, 200] },
  home: { L: [160, 20, 1280, 800], P: [446, -60, 830, 1250] },
  menu: { L: [MENU_R.x - 30, MENU_R.y - 14, MENU_R.w + 60, MENU_R.h + 28], P: [MENU_R.x - 8, MENU_R.y - 6, MENU_R.w + 16, MENU_R.h + 12] },
  shelf: { L: [420, 200, 760, 475], P: [440, 180, 720, 400] },
  talk: { L: [470, 300, 800, 430], P: [600, 300, 400, 420] },
  /* R10: the card on the left, Dionysus sharp on the right, doing the step */
  recipe: { L: [300, 296, 736, 470], P: [560, 236, 480, 560] },
  choice: { L: [700, 500, 560, 240], P: [880, 450, 400, 300] },
};
let vb = [440, 40, 720, 200], camAnim = null, shotName = 'intro';
function fit([x, y, w, h], anchor) {
  const A = innerWidth / innerHeight, cx = x + w / 2, cy = y + h / 2;
  if (w / h > A) { const h2 = w / A; return [x, anchor === 'top' ? y : cy - h2 / 2, w, h2]; }
  const w2 = h * A; return [cx - w2 / 2, y, w2, h];
}
function shotRect(name) {
  const s = SHOTS[name], phone = innerWidth < innerHeight && s.P;
  return fit(phone ? s.P : s.L, phone && name === 'recipe' ? 'top' : null);
}
function cam(name, dur = 900) {
  shotName = name; showPatch(name); const to = shotRect(name), from = vb.slice();
  if (RM || dur === 0) { vb = to; setVB(); sizeHits(); return Promise.resolve(); }
  const t0 = performance.now();
  return new Promise(res => {
    camAnim = now => { const p = ease(clamp((now - t0) / dur, 0, 1)); vb = from.map((v, i) => lerp(v, to[i], p)); setVB(); if (p >= 1) { camAnim = null; sizeHits(); res(); } };
  });
}
const setVB = () => svg.setAttribute('viewBox', vb.map(v => v.toFixed(2)).join(' '));
addEventListener('resize', () => { vb = shotRect(shotName); setVB(); placeBubble(); sizeHits(); });
vb = shotRect('intro'); setVB(); showPatch('intro');

/* ---------------- Dionysus: his own layer ---------------- */
const dio = makeDio($('#dio'));

/* ---------------- Touchables in a dark bar ----------------
   Each counter touchable's art moves into a .lift group (rim light, lift on press), with a .ring for keyboard focus
   and a transparent .hit grown to at least 44 CSS px. A pool of lamplight on the counter beneath each one wakes
   when it is touched; the pools live in their own group so the touchables' own boxes stay tight. */
const LIFTED = ['honey', 'menu', 'lamp', 'panther'];
(function liftTouchables() {
  const defs = svg.querySelector('defs');
  const gr = el('radialGradient', { id: 'poolGrad' }, defs);
  el('stop', { offset: '0', 'stop-color': '#ffd08a', 'stop-opacity': '.75' }, gr); el('stop', { offset: '.55', 'stop-color': '#e2ae5c', 'stop-opacity': '.28' }, gr); el('stop', { offset: '1', 'stop-color': '#e2ae5c', 'stop-opacity': '0' }, gr);
  const wrap = (host, nodes) => { const g = el('g', { class: 'lift' }); host.insertBefore(g, nodes[0]); nodes.forEach(n => g.appendChild(n)); return g; };
  LIFTED.forEach(id => { const t = $('#' + id); wrap(t, [...t.children]); });
  wrap($('#shelf'), [$('#bottles')]);
  [...LIFTED, 'shelf'].forEach(id => { const t = $('#' + id);
    t.insertBefore(el('rect', { class: 'hit' }), t.firstChild); t.appendChild(el('rect', { class: 'ring', rx: 8 })); });
  const pools = el('g', { id: 'pools', 'pointer-events': 'none' }); svg.insertBefore(pools, $('#counterThings'));
  LIFTED.forEach(id => {
    const L = id === 'lamp' ? { x: 690 - 18, y: 655 - 100, w: 36, h: 100 } : id === 'panther' ? LAYERS.touch.panther : LAYERS.touch[id];
    el('ellipse', { class: 'lpool', 'data-for': id, cx: L.x + L.w / 2, cy: L.y + L.h + 1, rx: Math.max(56, L.w * .85), ry: 18, fill: 'url(#poolGrad)' }, pools);
  });
  /* press: lift a little; keyboard: Enter or Space acts like a tap on any touchable */
  svg.addEventListener('pointerdown', e => { const t = e.target.closest('.touch'); if (t) { t.classList.add('pressed'); if (screen === 'home') cameFrom = t; } });
  $('#talkBtn').addEventListener('pointerdown', () => { if (screen === 'home') cameFrom = $('#talkBtn'); });
  const unpress = () => document.querySelectorAll('.touch.pressed').forEach(t => t.classList.remove('pressed'));
  addEventListener('pointerup', unpress); addEventListener('pointercancel', unpress); svg.addEventListener('pointerleave', unpress);
  svg.addEventListener('keydown', e => { if (e.key !== 'Enter' && e.key !== ' ') return; const t = e.target.closest('.touch'); if (!t) return;
    e.preventDefault(); e.stopPropagation(); t.dispatchEvent(new MouseEvent('click', { bubbles: true })); });
})();
/* 44 px targets at every camera position: hit and ring follow the art, in each touchable's own units */
function sizeHits() {
  [...LIFTED, 'shelf'].forEach(id => {
    const t = $('#' + id), lift = t.querySelector('.lift'), hit = t.querySelector('.hit'), ring = t.querySelector('.ring');
    if (!lift || !t.getScreenCTM()) return;
    let b; try { b = id === 'shelf' ? $('#shelfHit').getBBox() : lift.getBBox(); } catch (_) { return; }
    const m = t.getScreenCTM(), px = Math.hypot(m.a, m.b) || 1, min = 44 / px, pad = 5 / px;
    if (!b.width) return;
    const w = Math.max(b.width, min), h = Math.max(b.height, min);
    if (id !== 'shelf') { hit.setAttribute('x', b.x + b.width / 2 - w / 2); hit.setAttribute('y', b.y + b.height / 2 - h / 2); hit.setAttribute('width', w); hit.setAttribute('height', h); }
    ring.setAttribute('x', b.x - pad); ring.setAttribute('y', b.y - pad); ring.setAttribute('width', b.width + 2 * pad); ring.setAttribute('height', b.height + 2 * pad); ring.setAttribute('rx', 10 / px);
  });
}
sizeHits();
/* Dionysus gets the same gold focus ring, drawn round his figure */
(function dioRing() {
  const d = $('#dio'), ring = el('rect', { class: 'ring', rx: 14 }); d.appendChild(ring);
  d.addEventListener('focus', () => {
    const shape = d.querySelector('#dioLoops path') || d.querySelector('#body');
    try { const b = shape.getBBox(), m = d.getScreenCTM(), px = Math.hypot(m.a, m.b) || 1, pad = 6 / px;
      ring.setAttribute('x', b.x - pad); ring.setAttribute('y', b.y - pad); ring.setAttribute('width', b.width + 2 * pad); ring.setAttribute('height', b.height + 2 * pad); ring.setAttribute('rx', 14 / px); } catch (_) {}
  });
})();

/* ---------------- Main loop ---------------- */
let last = performance.now(), T = 0;
function frame(now) {
  const dt = Math.min(.05, (now - last) / 1000); last = now; T += RM ? 0 : dt;
  if (camAnim) camAnim(now);
  dio.tick(T, dt);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

/* ---------------- The drink on the counter (recipe) ---------------- */
let golden = false;
function drinkGlass(r, prog, garnish) {
  const G = GL[r.glass], s = .58;
  $('#liqrect').setAttribute('y', 120 - 120 * prog); $('#liqrect').setAttribute('height', 120 * prog);
  const [rx, ry] = G.rim, top = G.g.match(/M\s*([\d.]+)\s+([\d.]+)/);
  // Q9+, grafted from D: a rare golden rim, the god's own touch
  const rim = golden ? `<path d="M${(100 - rx).toFixed(0)} ${ry} L${rx} ${ry}" stroke="#e8c45a" stroke-width="5" stroke-linecap="round"/><circle cx="${rx}" cy="${ry}" r="3" fill="#fff3c4"/>` : '';
  $('#drink').innerHTML = `<g transform="translate(${-50 * s} ${-120 * s}) scale(${s})"><path d="${G.g}" fill="rgba(240,231,216,.22)" stroke="${golden ? '#e8c45a' : '#f0e7d8'}" stroke-width="2.4"/>
    <path d="${G.l}" fill="${r.colour}" clip-path="url(#liqclip)"/>${r.ice && G.ice && prog > .2 ? G.ice : ''}${garnish ? garnSide(r.garnish, G) : ''}${rim}</g>`;
}
$('#drink').setAttribute('transform', `translate(800 ${LAYERS.counterBackY + 10})`);

/* ---------------- UI: bubble ---------------- */
const bubble = $('#bubble'), sayEl = $('#say'), chips = $('#chips'), talkForm = $('#talk');
function placeBubble() {
  if (bubble.hidden || isPhone()) { bubble.style.left = ''; bubble.style.top = ''; return; }
  const r = dio.headRect(), bw = bubble.offsetWidth, bh = bubble.offsetHeight;
  let x = r.right + 28, y = r.top - 10;
  if (x + bw > innerWidth - 16) x = Math.max(16, r.left - bw - 28);
  y = clamp(y, 70, innerHeight - bh - 16);
  bubble.style.left = x + 'px'; bubble.style.top = y + 'px';
}
function speak(html, opts = {}) {
  bubble.hidden = false; sayEl.innerHTML = html; sayEl.className = opts.cls || ''; bubble.classList.toggle('storyb', opts.cls === 'story');
  chips.innerHTML = '';
  (opts.chips || []).forEach(c => {
    if (c.label === '|') { const d = document.createElement('span'); d.className = 'chipbreak'; d.textContent = c.text || ''; chips.appendChild(d); return; }
    const b = document.createElement('button'); b.type = 'button'; b.className = 'chip ' + (c.cls || ''); b.innerHTML = c.label; b.onclick = c.go; chips.appendChild(b);
  });
  talkForm.hidden = !opts.talk; dio.lookUp(true); $('#talkBtn').hidden = true;
  requestAnimationFrame(placeBubble);
  if (opts.talk && !isPhone()) setTimeout(() => $('#talkIn').focus({ preventScroll: true }), 50);
  else if (!opts.talk) focusIn(chips.querySelector('.chip'));
}
function hush() { bubble.hidden = true; dio.lookUp(false); if (screen === 'home') $('#talkBtn').hidden = false; }
$('#bubbleX').onclick = () => { hush(); if (shotName !== 'home') home(); };

/* ---------------- Screens ---------------- */
let screen = 'intro';
const panel = $('#panel');
function clearScene() {
  panel.hidden = true; panel.className = 'panel'; svg.classList.remove('dim'); document.body.classList.remove('recipe-on');
  recipeState = null; $('#drink').innerHTML = ''; dio.idle(); lightUp(null);
}
/* Focus: a panel takes focus when it opens; going home gives it back to the touchable (or the talk pill) you came from.
   While a panel is open, the scene's touchables leave the Tab order. */
let cameFrom = null;
const focusIn = sel => requestAnimationFrame(() => { const e = typeof sel === 'string' ? panel.querySelector(sel) : sel; if (e && !e.closest('[hidden]')) e.focus({ preventScroll: true }); });
function sceneTabbable(on) { document.querySelectorAll('#scene .touch').forEach(t => { if (t.id !== 'lamp') t.setAttribute('tabindex', on ? '0' : '-1'); }); }
function home() {
  screen = 'home'; clearScene(); $('#back').hidden = true; $('#talkBtn').hidden = false;
  hush(); sceneTabbable(true);
  const back = cameFrom, a = document.activeElement; cameFrom = null;
  if (back && back.isConnected && !back.hidden && (!a || a === document.body || panel.contains(a) || bubble.contains(a) || a === $('#back'))) back.focus({ preventScroll: true });
  return cam('home');
}
$('#back').onclick = () => home();
$('#back').innerHTML = ICON.back;
/* Halo's search pill: talking to him is the search (Q3). The cycling words are things you can say (R12), never buttons. */
$('#talkBtn').innerHTML = `<span class="tl">Talk to Dionysus</span><span class="cyc" aria-hidden="true">${['“warm me up”', '“something smoky”', '“after dinner”', '“fresh, with gin”', '“not too strong”'].map((t, n) => `<em style="animation-delay:${n * 3}s">${t}</em>`).join('')}</span><span class="mi" aria-hidden="true">${ICON.mic}</span>`;
$('#talkBtn').setAttribute('aria-label', 'Talk to Dionysus');
addEventListener('keydown', e => { if (e.key !== 'Escape') return; if (!settings.hidden) { settings.hidden = true; $('#lamp').focus({ preventScroll: true }); return; } if (screen !== 'home' && screen !== 'intro') home(); });
function setScreen(name) { if (screen === 'home' && !cameFrom) { const a = document.activeElement; cameFrom = a && a.closest && (a.closest('.touch') || a.closest('#talkBtn')) || null; } screen = name; $('#back').hidden = false; $('#talkBtn').hidden = true; clearScene(); sceneTabbable(false); }
function lightUp(id) { document.querySelectorAll('.touch.lit').forEach(t => t.classList.remove('lit')); if (id) $('#' + id).classList.add('lit'); }

/* 1. Opening: the big word becomes the neon sign */
async function intro() {
  $('#talkBtn').hidden = true;
  await wait(RM ? 0 : 700);
  document.body.classList.add('lit', 'flick');
  await wait(RM ? 0 : 1300);
  BG.signOff.classList.remove('on');
  await cam('home', 2200);
  if (screen !== 'intro') return;
  screen = 'home'; $('#talkBtn').hidden = false;
  await wait(RM ? 0 : 500);
  if (!BAR.filled && screen === 'home') askWhatYouHave();
}

/* 3. "What do you have?" Two routes (Q5): photos, or a list pasted from your own AI tool */
function askWhatYouHave() {
  speak('What do you have? My shelf is looking thin.', { chips: [
    { label: 'Show him some photos', cls: 'go', go: openPhotos },
    { label: 'Paste from your own AI', go: openPaste },
    { label: 'Later', cls: 'skip', go: hush }] });
}
const PHOTO_ART = {
  cupboard: '<rect width="160" height="120" fill="#3a2719"/><rect y="70" width="160" height="6" fill="#5a3f2a"/>' + [['#b8661c', 14], ['#a9561a', 34], ['#c98a2c', 52], ['#9a6a2a', 72], ['#d39a3a', 90], ['#cfe2e8', 110], ['#e9e0c8', 130]].map(([c, x]) => `<rect x="${x}" y="28" width="14" height="42" rx="3" fill="${c}"/><rect x="${x + 4}" y="20" width="6" height="10" fill="${c}"/>`).join(''),
  fridge: '<rect width="160" height="120" fill="#cfd8da"/><rect x="10" y="10" width="140" height="100" rx="6" fill="#e9eef0"/><rect x="10" y="64" width="140" height="5" fill="#b8c4c8"/>' + [['#7a2418', 20], ['#e6dfb6', 42], ['#8a2a14', 64], ['#e07a1c', 80], ['#e6c88a', 98], ['#e4eef2', 118]].map(([c, x]) => `<rect x="${x}" y="24" width="14" height="40" rx="3" fill="${c}"/>`).join('') + '<ellipse cx="40" cy="88" rx="12" ry="9" fill="#f3eedf"/><circle cx="80" cy="88" r="6" fill="#9b1020"/>',
  bowl: '<rect width="160" height="120" fill="#6b4c33"/><path d="M20 70 Q80 130 140 70 Z" fill="#e9dcc4"/>' + [['#f2cf2e', 50, 62], ['#86c03a', 72, 58], ['#ef8a22', 94, 62], ['#f0826a', 114, 66], ['#f2cf2e', 64, 46]].map(([c, x, y]) => `<circle cx="${x}" cy="${y}" r="13" fill="${c}"/>`).join('') + '<path d="M26 40 q10 -20 22 -4" stroke="#4c9a48" stroke-width="6" fill="none"/>',
  drawer: '<rect width="160" height="120" fill="#2b1d14"/><rect x="8" y="16" width="144" height="92" rx="4" fill="#4a3324"/><path d="M30 30 L46 30 L42 90 L34 90 Z" fill="#c9ccd0"/><path d="M60 30 h16 l-6 26 l6 26 h-16 l6 -26 Z" fill="#c9ccd0"/><rect x="92" y="26" width="4" height="70" fill="#c9ccd0"/><circle cx="124" cy="56" r="16" fill="none" stroke="#c9ccd0" stroke-width="4"/>',
};
function openPhotos() {
  hush(); setScreen('shelf'); cam('shelf');
  const picked = new Set(['cupboard', 'fridge', 'bowl', 'drawer']);
  panel.className = 'panel sheet'; panel.hidden = false;
  panel.innerHTML = `<h2>Show him your bar</h2><p>Pick photos of your bottles and your tools. (This prototype uses sample photos and pretends to read them.)</p>
   <div class="photos">${PHOTOS.map(p => `<button class="photo" data-id="${p.id}" aria-pressed="true"><svg viewBox="0 0 160 120">${PHOTO_ART[p.id]}</svg><span>${p.name}</span></button>`).join('')}</div>
   <p class="paste">No photos handy? <a href="#" id="pasteL">Paste a list from your own AI tool</a> instead.</p>
   <div class="row"><button class="btn ghost" id="pcancel">Not now</button><button class="btn" id="pread">Read these photos</button></div>`;
  panel.querySelectorAll('.photo').forEach(b => b.onclick = () => { const id = b.dataset.id; picked.has(id) ? picked.delete(id) : picked.add(id); b.setAttribute('aria-pressed', picked.has(id)); });
  $('#pasteL').onclick = e => { e.preventDefault(); openPaste(); };
  $('#pcancel').onclick = home; focusIn('#pread');
  $('#pread').onclick = async () => {
    if (!picked.size) return;
    panel.innerHTML = `<h2>Show him your bar</h2><div class="reading"><i></i> Dionysus is reading your photos…</div>`;
    await wait(RM ? 300 : 1800);
    confirmFound(readPhotos([...picked]));
  };
}
/* Grafted from D, made real: copy the prompt, paste the reply, he reads it (nothing leaves the page) */
function openPaste() {
  hush(); setScreen('shelf'); cam('shelf');
  panel.className = 'panel sheet'; panel.hidden = false;
  panel.innerHTML = `<h2>Paste from your own AI</h2>
   <ol class="howto"><li>Copy this prompt into your own AI tool (ChatGPT, Claude, Gemini…), with photos of your bottles and tools.</li><li>Paste its reply below.</li></ol>
   <div class="prompt"><pre id="aiPrompt"></pre><button class="btn small" id="copyP">Copy the prompt</button></div>
   <textarea id="pasteIn" rows="5" placeholder='Paste the reply here, e.g. {"bottles":[{"label":"Springbank 15","style":"islay scotch"}],"barware":["shaker"]}'></textarea>
   <p class="pasteNote" id="pasteNote"></p>
   <div class="row"><button class="btn ghost" id="pex">Use an example reply</button><button class="btn ghost" id="pcancel">Not now</button><button class="btn" id="pread">Read the reply</button></div>`;
  $('#aiPrompt').textContent = AI_PROMPT();
  $('#copyP').onclick = () => { navigator.clipboard && navigator.clipboard.writeText(AI_PROMPT()).catch(() => {}); $('#copyP').textContent = 'Copied'; };
  focusIn('#pasteIn');
  $('#pex').onclick = () => { $('#pasteIn').value = JSON.stringify({ bottles: INVENTORY.have.map(k => ({ label: ING[k][0], style: k })), barware: ['shaker', 'strainer', 'jigger', 'spoon'] }); };
  $('#pcancel').onclick = home;
  $('#pread').onclick = () => {
    const res = readPasted($('#pasteIn').value);
    if (!res.found.length) { $('#pasteNote').textContent = "I couldn't find any bottles in that. Paste the AI's whole reply."; return; }
    confirmFound(res, res.unknown);
  };
}
const famName = k => isBottle(k) ? GROUP_NAME(groupOf(k)) : 'In the kitchen';
function confirmFound(res, unknown = []) {
  const byKind = {}; res.found.forEach(k => { const f = famName(k); (byKind[f] = byKind[f] || []).push(k); });
  panel.innerHTML = `<h2>Here's what he found</h2><ul class="found">${Object.entries(byKind).map(([f, l]) => `<li><b>${f}</b>${l.map(k => `<span class="fi">${ingIco(k, 22)}${esc(ING[k][0])}</span>`).join('')}</li>`).join('')}</ul>
   ${unknown.length ? `<p class="pasteNote">Not on his list yet: ${unknown.map(u => String(u).replace(/[<>&]/g, '')).join(', ')}</p>` : ''}
   <p class="lbl">Barware: tick what you have</p>
   <div class="ticks">${Object.entries(BARWARE).map(([k, v]) => `<label><input type="checkbox" value="${k}" ${res.tools.includes(k) ? 'checked' : ''}> ${v}</label>`).join('')}</div>
   <div class="row"><button class="btn ghost" id="pcancel">Not now</button><button class="btn" id="pstock">Stock the shelf</button></div>`;
  $('#pcancel').onclick = home; focusIn('#pstock');
  $('#pstock').onclick = async () => {
    const tools = [...panel.querySelectorAll('.ticks input:checked')].map(i => i.value);
    applyReading(res, tools); panel.hidden = true; drawShelf(true);
    await wait(RM ? 0 : 1400); await home();
    showHints();
    setTimeout(() => speak(`That's more like it. ${R.filter(canMake).length} drinks I can make you now. Tap the menu, or talk to me.`, { chips: [{ label: 'OK', cls: 'go', go: hush }] }), RM ? 0 : 950);
  };
}
/* First stocked visit: say what can be touched (grafted from D's hint pills) */
function showHints() {
  const box = $('#hints'); box.innerHTML = '';
  [['menu', 'The menu'], ['panther', "Barman's choice"], ['shelf', 'Your shelf'], ['honey', 'Honey']].forEach(([id, t]) => {
    const r = $('#' + id).getBoundingClientRect(); if (!r.width) return;
    const p = document.createElement('span'); p.className = 'hint'; p.textContent = t;
    p.style.left = clamp(r.left + r.width / 2, 64, innerWidth - 64) + 'px'; p.style.top = Math.max(60, r.top - 34) + 'px'; box.appendChild(p);
  });
  document.querySelectorAll('.touch').forEach(t => t.classList.add('hinting'));
  setTimeout(() => { box.innerHTML = ''; document.querySelectorAll('.touch').forEach(t => t.classList.remove('hinting')); }, 6000);
}
/* The shelf becomes Halo's "Your bar": tap a Bottle to mark it run out (it stays on the shelf, dusty), and
   "One bottle away": each Bottle you lack, with the drinks it alone would open. */
let shelfTab = 'bar';
function openShelf(tab) {
  if (!BAR.filled) return openPhotos();
  if (tab) shelfTab = tab;
  hush(); setScreen('shelf'); cam('shelf');
  panel.className = 'panel sheet shelfsheet barsheet'; panel.hidden = false;
  panel.innerHTML = `<div class="bhead"><h2>${shelfTab === 'bar' ? 'Your bar' : 'One bottle away'}</h2>
     <div class="fbs" role="tablist">${[['bar', 'Your bar'], ['away', 'One bottle away']].map(([k, v]) => `<button class="fb" role="tab" data-t="${k}" aria-selected="${k === shelfTab}">${v}</button>`).join('')}</div></div>
   <div id="barBody"></div>
   <div class="row"><button class="btn ghost" id="pmore">Add more</button><button class="btn" id="pdone">Back to the bar</button></div>`;
  panel.querySelectorAll('.bhead .fb').forEach(b => b.onclick = () => { shelfTab = b.dataset.t; panel.querySelectorAll('.bhead .fb').forEach(x => x.setAttribute('aria-selected', x === b)); panel.querySelector('.bhead h2').textContent = b.textContent; fillBar(); });
  $('#pmore').onclick = openPhotos; $('#pdone').onclick = home;
  fillBar();
  focusIn('#barBody .it');
}
function fillBar() {
  const box = $('#barBody'); if (!box) return;
  if (shelfTab === 'away') {
    const m = oneBottleAway();
    box.innerHTML = `<div class="away">${m.length ? m.map(([k, rs]) => `<div class="ar"><div class="ak">${ingIco(k, 48)}<span class="nm">${esc(ING[k][0])}</span><span class="un">+${rs.length} drink${rs.length > 1 ? 's' : ''}</span></div>
      <div class="ad">${rs.map(r => `<button class="mini" data-id="${r.id}">${glassSide(r, 56)}<span>${esc(r.name)}</span></button>`).join('')}</div></div>`).join('') : '<p class="none">Nothing is one bottle away: you can make everything on the menu.</p>'}</div>`;
    box.querySelectorAll('.mini').forEach(b => b.onclick = () => openRecipe(b.dataset.id));
    return;
  }
  const fam = {}; shelfBottles().forEach(b => { const f = GROUP_NAME(groupOf(b.k)); (fam[f] = fam[f] || []).push(b); });
  const outN = BAR.out.size;
  box.innerHTML = `<p class="sub">${shelfBottles().length - outN} bottles${outN ? ` · ${outN} run out` : ''}. Tap a bottle when it runs out.</p>
   <div class="bfams">${Object.entries(fam).map(([f, l]) => `<section class="bfam"><h3>${f}</h3><div class="ig">${l.map(b => `<button class="it${b.out ? ' off' : ''}" data-k="${b.k}" aria-pressed="${!b.out}" aria-label="${esc(b.style)}${b.out ? ', run out' : ''}">${ingIco(b.k, 40, { ghost: b.out })}<span>${esc(b.style)}</span>${b.out ? '<small>run out</small>' : ''}</button>`).join('')}</div></section>`).join('')}</div>
   <h3 class="lbl" style="margin-top:10px">Barware</h3>
   <div class="tools">${Object.entries(BARWARE).map(([k, v]) => `<button class="tool" data-k="${k}" aria-pressed="${BAR.barware.has(k)}">${v}</button>`).join('')}</div>`;
  box.querySelectorAll('.it').forEach(b => b.onclick = () => { setRunOut(b.dataset.k, !BAR.out.has(b.dataset.k)); drawShelf(); fillBar(); const n = box.querySelector(`.it[data-k="${b.dataset.k}"]`); if (n) n.focus({ preventScroll: true }); });
  box.querySelectorAll('.tool').forEach(b => b.onclick = () => { const k = b.dataset.k; BAR.barware.has(k) ? BAR.barware.delete(k) : BAR.barware.add(k); b.setAttribute('aria-pressed', BAR.barware.has(k)); });
}
$('#shelf').addEventListener('click', e => { e.stopPropagation(); if (screen === 'home') openShelf(); });

/* 4. The menu: zoom in, by spirit, by feel, A–Z. R9: every drink, the ones you can't make marked "needs X" */
const needText = r => { const m = missingFor(r); return m.length ? 'needs ' + m.map(x => ING[x.k][0]).join(', ') : ''; };
/* Halo's drink card. R9: every drink stays in its place; one you can't make is ghosted and says what it needs. */
function drinkCard(r, by) {
  const need = needText(r);
  const meta = by === 'feel' ? `${spIco(r.spirit, 14)}<span>${FAMILIES[r.spirit]}</span>` : `${feelIcon(r, 14)}<span>${FEELS[feelOf(r)]}</span>`;
  return `<button class="drink dc${need ? ' need' : ''}" data-id="${r.id}" aria-label="${esc(r.name)}${need ? ', ' + need : ''}"><span class="pic">${glassSide(r, phoneMenu() ? 84 : 96, { ghost: !!need })}</span><span class="nm">${esc(r.name)}</span>
    <span class="meta">${meta}</span>${need ? `<span class="needs">${esc(need)}</span>` : `<span class="meta">${timePie(r, 13)}<span>${fmt(stepsTotal(r))}</span></span>`}</button>`;
}
const phoneMenu = () => innerWidth <= 640;
const byMake = l => [...l].sort((a, b) => canMake(b) - canMake(a));
function menuBody(tab) {
  const sec = (icon, name, l, by) => l.length ? `<section class="msec"><h3>${icon}<span>${name}</span><em>${l.filter(canMake).length} of ${l.length}</em></h3><div class="strip"><div class="track">${byMake(l).map(r => drinkCard(r, by)).join('')}</div></div></section>` : '';
  if (tab === 'spirit') return Object.entries(FAMILIES).map(([k, v]) => sec(spIco(k, 30), v, R.filter(r => r.spirit === k), 'spirit')).join('');
  if (tab === 'feel') return Object.entries(FEELS).map(([k, v]) => sec(feelIco(FEEL_ICON4[k], 26), v, R.filter(r => feelOf(r) === k), 'feel')).join('');
  return `<div class="az" id="az" tabindex="0" aria-label="A to Z. Arrow keys move round the letters."></div>`;
}
function fillMenu(tab) {
  const body = panel.querySelector('.mbody'); body.innerHTML = menuBody(tab); body.scrollTop = 0;
  body.querySelectorAll('.strip').forEach(h => new Strip(h, { itemW: phoneMenu() ? 124 : 150, gap: phoneMenu() ? 12 : 20, pad: phoneMenu() ? 16 : 24 }));
  if (tab === 'az') mountAZ($('#az'));
  wireDrinks();
}
async function openMenu(tab = 'spirit') {
  hush(); setScreen('menu');
  await cam('menu', 850);
  panel.className = 'panel menucard'; panel.hidden = false; svg.classList.add('dim');
  const n = R.filter(canMake).length;
  panel.innerHTML = `<h2>MENU</h2><p class="menunote">${R.length} drinks · ${n} you can make now</p><div class="fbs" role="tablist">${[['spirit', 'By spirit'], ['feel', 'By feel'], ['az', 'A–Z']].map(([k, v]) => `<button class="fb" role="tab" data-t="${k}" aria-selected="${k === tab}">${v}</button>`).join('')}</div><div class="mbody"></div>`;
  panel.querySelectorAll('.fbs .fb').forEach(b => b.onclick = () => { panel.querySelectorAll('.fbs .fb').forEach(x => x.setAttribute('aria-selected', x === b)); fillMenu(b.dataset.t); });
  fillMenu(tab);
  focusIn('.fbs .fb[aria-selected=true]');
}
function wireDrinks() { panel.querySelectorAll('.dc').forEach(b => b.onclick = () => openRecipe(b.dataset.id)); }
/* Halo's A–Z ring: the letters swell under the finger (or the mouse); lift on a letter and its drinks pop out as an
   inner ring; lift on a drink to open it. Every drink is there (R9): the ones you can't make are ghosted, "needs X". */
const ALPHA = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
function mountAZ(az) {
  if (!az) return;
  const small = phoneMenu();
  const byL = {}; [...R].sort((a, b) => a.name.localeCompare(b.name)).forEach(r => { const k = r.name[0].toUpperCase(); (byL[k] = byL[k] || []).push(r); });
  const W = az.clientWidth, H = az.clientHeight, cx = W / 2, cy = H / 2, RR = Math.min(W, H) * (small ? .43 : .44), R2 = RR * .55, LH = small ? 20 : 24, IW = small ? 43 : 52;
  const els = [...ALPHA].map(c => { const e = document.createElement('div'); e.className = 'lt' + (byL[c] ? '' : ' none'); e.textContent = c; e.setAttribute('aria-hidden', 'true'); az.appendChild(e); return e; });
  const pos = (n, N, r) => { const a = (n / N) * 2 * Math.PI - Math.PI / 2; return [cx + r * Math.cos(a), cy + r * Math.sin(a), a]; };
  const fish = (d, sd) => Math.exp(-(d * d) / (2 * sd * sd));
  let fL = null, fD = null, mode = null, letter = null, shown = null, live = false, inner = [], last = -1;
  const drawLetters = () => els.forEach((e, n) => { let d = fL == null ? 99 : Math.abs(n - fL); if (fL != null) d = Math.min(d, 26 - d); const b = fish(d, 1.3);
    const [x, y, a] = pos(n, 26, RR), p = 16 * b; e.style.transform = `translate(${x + p * Math.cos(a) - LH}px,${y + p * Math.sin(a) - LH}px) scale(${1 + (small ? 1.2 : 1.6) * b})`;
    e.classList.toggle('hot', ALPHA[n] === letter || d < .5); });
  const drawInner = () => { const N = inner.length; inner.forEach((e, n) => { let d = fD == null ? 99 : Math.abs(n - fD); if (fD != null) d = Math.min(d, N - d); const b = N > 1 ? fish(d, .7) : 0;
    const [x, y] = N === 1 ? [cx, cy] : pos(n, N, R2); e.style.setProperty('--dx', (cx - x) + 'px'); e.style.setProperty('--dy', (cy - y) + 'px'); e.style.transform = `translate(${x - IW}px,${y - IW}px) scale(${1 + .3 * b})`; e.style.zIndex = 5 + Math.round(b * 5); }); };
  const buildInner = (L, active) => {
    shown = L; inner.forEach(e => e.remove()); inner = [];
    (byL[L] || []).forEach((r, n) => { const e = document.createElement('button'); const need = needText(r);
      e.className = 'drink ic' + (active ? ' live' : ''); e.dataset.id = r.id; e.setAttribute('aria-label', r.name + (need ? ', ' + need : ''));
      e.innerHTML = `${glassSide(r, small ? 46 : 60, { ghost: !!need })}<span>${esc(r.name)}</span>${need ? `<small>${esc(need)}</small>` : ''}`;
      e.style.animationDelay = (active ? n * 45 : 0) + 'ms';
      e.onclick = ev => { if (ev.detail === 0) openRecipe(r.id); };   // keyboard; pointer lifts are handled below
      az.appendChild(e); inner.push(e); });
    live = active; fD = null; drawInner();
  };
  const polar = e => { const b = az.getBoundingClientRect(); const x = e.clientX - b.left - cx, y = e.clientY - b.top - cy; return { d: Math.hypot(x, y), a: ((Math.atan2(y, x) + Math.PI / 2) / (2 * Math.PI) + 1) % 1 }; };
  const nearestL = v => { let best = null, bd = 99; [...ALPHA].forEach((c, n) => { if (!byL[c]) return; let d = Math.abs(n - v); d = Math.min(d, 26 - d); if (d < bd) { bd = d; best = n; } }); return best; };
  const zone = p => p.d > (RR + R2) / 2 ? 'letters' : (inner.length > 1 && p.d > R2 * .45 ? 'drinks' : 'centre');
  const pickLetter = n => { letter = ALPHA[n]; fL = n; last = -1; buildInner(letter, true); drawLetters(); };
  const aim = p => { if (mode === 'letters') { fL = p.a * 26; drawLetters(); const k = Math.round(fL) % 26; if (k !== last) { last = k; if (byL[ALPHA[k]] && ALPHA[k] !== shown) buildInner(ALPHA[k], true); try { navigator.vibrate && navigator.vibrate(4); } catch (_) {} } }
    else if (mode === 'drinks') { fD = p.a * inner.length; drawInner(); } };
  drawLetters();
  az.addEventListener('pointerdown', e => { const p = polar(e); mode = zone(p); if (mode === 'centre') { mode = null; return; } try { az.setPointerCapture(e.pointerId); } catch (_) {} aim(p); });
  const rest = () => { fL = letter ? ALPHA.indexOf(letter) : null; drawLetters(); if (fD != null) { fD = null; drawInner(); } };
  az.addEventListener('pointermove', e => { const p = polar(e); if (mode) return aim(p); if (e.pointerType !== 'mouse') return; const z = zone(p);
    if (z === 'letters') { fL = p.a * 26; drawLetters(); const k = Math.round(fL) % 26; if (k !== last) { last = k; if (byL[ALPHA[k]] && ALPHA[k] !== shown) buildInner(ALPHA[k], true); } if (fD != null) { fD = null; drawInner(); } }
    else if (z === 'drinks') { fD = p.a * inner.length; drawInner(); }
    else rest(); });
  az.addEventListener('pointerup', e => { const p = polar(e), m = mode; mode = null;
    const t = document.elementFromPoint(e.clientX, e.clientY), hit = t && t.closest('.ic');
    if (!m) { if (hit) return openRecipe(hit.dataset.id); if (live && inner.length > 1) { letter = null; fL = null; inner.forEach(x => x.remove()); inner = []; live = false; shown = null; drawLetters(); } return; }
    if (m === 'letters') { const n = nearestL(fL); if (n == null) return; const ls = byL[ALPHA[n]]; if (ls.length === 1) return openRecipe(ls[0].id); return pickLetter(n); }
    if (m === 'drinks') { const k = hit ? inner.indexOf(hit) : (fD == null ? -1 : Math.round(fD) % inner.length); if (k >= 0) openRecipe(inner[k].dataset.id); } });
  az.addEventListener('pointerleave', () => { if (mode) return; last = -1; if (letter) { if (shown !== letter) buildInner(letter, true); } else { inner.forEach(x => x.remove()); inner = []; shown = null; live = false; } rest(); });
  az.addEventListener('keydown', e => { if (e.target !== az) return; const has = [...ALPHA].map((c, n) => byL[c] ? n : -1).filter(n => n >= 0);
    const i = has.indexOf(letter ? ALPHA.indexOf(letter) : -1);
    if (['ArrowRight', 'ArrowDown'].includes(e.key)) { e.preventDefault(); pickLetter(has[(i + 1) % has.length]); }
    else if (['ArrowLeft', 'ArrowUp'].includes(e.key)) { e.preventDefault(); pickLetter(has[(i - 1 + has.length) % has.length]); }
    else if (e.key === 'Enter' && inner.length) { e.preventDefault(); inner[0].focus(); } });
}
$('#menu').addEventListener('click', e => { e.stopPropagation(); if (screen === 'home') openMenu(); });

/* 5. Talking to Dionysus: tap Talk, tap a spirit, tap a drink (three taps) */
let conv = null;
/* A drink he names: Halo's result row, small. Status in E's words (R9): "Make now", "Make now · swap", "needs Campari". */
const resChip = r => { const need = needText(r), swap = r.ing.some(x => !x.o && !STAPLE.has(x.k) && !BAR.have.has(x.k) && x.subs.some(k => BAR.have.has(k)));
  return { label: `${glassSide(r, 30, { ghost: !!need })}<span class="rt"><b>${esc(r.name)}</b><small class="${need ? 'no' : 'ok'}">${need ? esc(need) : swap ? 'Make now · swap' : 'Make now'}</small></span>`, cls: 'res', go: () => openRecipe(r.id) }; };
async function startTalk() {
  setScreen('talk'); hush(); cam('talk', 800);
  conv = Conversation(); render(conv.start());
}
function render(s) {
  if (s.open) return openRecipe(s.open);
  const ch = [];
  if (s.results) s.results.forEach(r => ch.push(resChip(r)));
  if (s.q) {
    if (s.results) ch.push({ label: '|' });
    (s.opts || []).forEach(([k, v]) => ch.push({ label: v, go: () => render(conv.answer(s.q, k)) }));
    ch.push({ label: 'Skip', cls: 'skip', go: () => render(conv.answer(s.q, '-')) });
  } else ch.push({ label: 'Start again', cls: 'skip', go: () => render((conv = Conversation()).start()) });
  speak(s.say, { chips: ch, talk: true });
}
talkForm.onsubmit = e => { e.preventDefault(); const v = $('#talkIn').value.trim(); if (!v) return; $('#talkIn').value = ''; if (!conv) conv = Conversation(); render(conv.say(v)); };
$('#talkBtn').onclick = startTalk;
$('#mic').onclick = () => {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition, m = $('#mic');
  if (!SR) { $('#talkIn').placeholder = 'Speech isn’t available in this browser. Type instead.'; $('#talkIn').focus(); return; }
  const rec = new SR(); rec.lang = 'en-GB'; m.classList.add('on');
  rec.onresult = ev => { $('#talkIn').value = ev.results[0][0].transcript; talkForm.requestSubmit(); };
  rec.onend = () => m.classList.remove('on'); rec.start();
};

/* 6. Tap him for a story (only drinks you can make, once your shelf is stocked) */
function tellStory(exceptId) {
  setScreen('story'); cam('talk', 800); dio.story();
  const pool = R.filter(r => STORY[r.id] && (canMake(r) || !BAR.filled) && r.id !== exceptId);
  if (!pool.length) return speak("Stock the shelf and I'll tell you about the drinks on it.", { chips: [{ label: 'OK', cls: 'go', go: home }] });
  const r = pool[Math.floor(Math.random() * pool.length)], s = STORY[r.id];
  speak(`<span class="sname">${esc(r.name)}</span><span class="sq">${esc(s.tell)}</span><span class="sm"><b>${esc(s.by)}</b><span>${esc(s.at)}</span><span>${esc(s.when)}</span>${s.kind === 'legend' ? '<span class="lg">as legend has it</span>' : ''}</span>`, {
    cls: 'story', chips: [{ label: 'Make me one', cls: 'go', go: () => openRecipe(r.id) }, { label: 'Another story', go: () => tellStory(r.id) }] });
  dio.story();
}
$('#dio').addEventListener('click', e => { e.stopPropagation(); if (screen === 'home' || screen === 'story' || screen === 'talk') tellStory(); });

/* 6b. Barman's choice: the panther bats the dice off the counter (one tap) */
let rolling = false;
const dice = $('#dice'), DICE0 = [LAYERS.touch.dice.x + LAYERS.touch.dice.w / 2, LAYERS.touch.dice.y + LAYERS.touch.dice.h / 2];
dice.setAttribute('transform', `translate(${DICE0[0]} ${DICE0[1]})`);
async function barmansChoiceGo() {
  if (rolling) return;
  const pick = barmansChoice();
  if (!pick) return speak("Nothing I can make you yet. Show me what's in the house.", { chips: [{ label: 'Show him some photos', cls: 'go', go: openPhotos }, { label: 'Later', cls: 'skip', go: hush }] });
  rolling = true; screen = 'choice'; $('#talkBtn').hidden = true; hush(); lightUp('panther');
  if (!RM) {
    await cam('choice', 500);
    const t0 = performance.now(), pb = $('#pantherBody');
    await new Promise(res => {
      (function f(now) {
        const p = (now - t0) / 1300, swipe = Math.sin(clamp(p / .3, 0, 1) * Math.PI);
        pb.setAttribute('transform', `translate(${-8 * swipe} ${-4 * swipe})`);
        const q = seg(p, .18, 1), x = DICE0[0] - 260 * q, y = DICE0[1] - 70 * Math.sin(Math.PI * Math.min(q * 1.4, 1)) + (q > .7 ? 180 * (q - .7) : 0);
        dice.setAttribute('transform', `translate(${x} ${y}) rotate(${-720 * q})`);
        if (p < 1) requestAnimationFrame(f); else res();
      })(t0);
    });
    pb.removeAttribute('transform');
  }
  dice.setAttribute('transform', `translate(${DICE0[0]} ${DICE0[1]})`); rolling = false;
  openRecipe(pick.r.id, pick);
}
$('#panther').addEventListener('click', e => { e.stopPropagation(); if (screen === 'home') barmansChoiceGo(); });

/* 6c. The honey jar (R8): honey comes from here. Tap it for the drinks that use it. */
function honeyTalk() {
  setScreen('talk'); cam('talk', 800); lightUp('honey');
  const l = R.filter(r => r.ing.some(x => x.k === 'honey')).sort((a, b) => (canMake(b) - canMake(a)) || a.name.localeCompare(b.name));
  speak('Honey. The oldest sweetener there is. These want it:', { chips: [...l.map(resChip), { label: 'Back to the bar', cls: 'skip', go: home }] });
}
$('#honey').addEventListener('click', e => { e.stopPropagation(); if (screen === 'home') honeyTalk(); });

/* 7. The recipe. R6: he acts out each step, then waits for your tap. R10: he stands sharp beside the card. */
let recipeState = null;
const haveK = k => STAPLE.has(k) || BAR.have.has(k);
/* Halo's rule: a strain after a stir pours from the mixing glass */
const glyphAct = (r, n) => { const a0 = r.steps[n][0]; return a0 === 'strain' && r.steps.slice(0, n).some(x => x[0] === 'stir') ? 'strain-glass' : a0; };
const glyph = (r, n) => typeof act === 'function' ? act(glyphAct(r, n), r.colour, { glass: r.glass }) : '';
/* Halo's ingredient grid: icon, quantity, unit, name, status (Style swap in gold, optional, needs) */
function ingRow(x) {
  const ok = haveK(x.k), sub = ok ? null : x.subs.find(k => BAR.have.has(k));
  const q = typeof x.q === 'number' ? (Number.isInteger(x.q) ? x.q : x.q.toFixed(1)) : (x.q || '');
  let unit = x.u || '', name = ING[x.k][0]; const m = unit.match(/^ml (\w+)$/);
  if (m) { unit = 'ml'; name = m[1] === 'juice' ? name + ' juice' : m[1] === 'espresso' ? 'Espresso' : m[1] === 'hot' ? 'Hot ' + name.toLowerCase() : name; }
  const right = ok ? '' : sub ? `<span class="sub">→ ${esc(ING[sub][0])}</span>` : x.o ? `<span class="opt">optional</span>` : `<span class="needx">needs</span>`;
  return `<div class="ir${ok || sub ? '' : ' miss'}"><span class="ii">${ingIco(x.k, 22, { ghost: !ok && !sub })}</span><span class="iq">${q}</span><span class="iu">${esc(unit)}</span><span class="in">${esc(name)}</span><span class="ix">${right}</span></div>`;
}
function openRecipe(id, chosen) {
  const r = RB[id]; if (!r) return home();
  hush(); setScreen('recipe');
  document.body.classList.add('recipe-on'); cam('recipe', 900);
  golden = Math.random() < .15;
  const swaps = swapsFor(r);
  const worth = chosen && chosen.worth;
  let pic = glassSide(r, 88); if (golden) pic = pic.replace('fill="var(--glass)"/>', 'fill="var(--glass)" stroke="#e8c45a" stroke-width="3"/>');
  panel.className = 'panel recipe'; panel.hidden = false;
  panel.innerHTML = `<div class="rtop">${chosen ? `<div class="kicker">${diceHTML(14)}<span>Barman’s choice${worth ? ` · <b>worth buying a bottle for</b>` : ''}</span></div>` : ''}
   <button class="again" id="againDice" aria-label="Another barman’s choice">${diceHTML(22)}</button>
   <div class="head"><div class="rg">${pic}</div><div><h2>${esc(r.name)}</h2>
     <div class="rm"><span>${spIco(r.spirit, 18)}${FAMILIES[r.spirit]}</span><span>${feelIcon(r, 15)}${FEELS[feelOf(r)]}</span><span>${timePie(r, 15)}${fmt(stepsTotal(r))}</span><span>${STRENGTHS[strengthOf(r)]} strength</span></div></div></div>
   ${worth ? `<p class="worth">Needs ${ING[worth.bottle][0]}. One bottle, and ${worth.opens > 1 ? `${worth.opens} drinks open up` : 'this one is yours'}.</p>` : ''}
   ${golden ? '<p class="golden">A golden rim. The god’s own touch: it happens one time in seven.</p>' : ''}
   <div class="ing">${r.ing.map(ingRow).join('')}</div>
   ${swaps.length ? `<div class="toolswap"><b>No ${swaps.map(s => s.tool.toLowerCase()).join(', ')}?</b> ${swaps.map(s => `Use ${s.use}`).join('. ')}.</div>` : ''}</div>
   <div class="stepbox" id="stepbox" aria-live="polite"><div class="stxt"><p class="stepno" id="stepno"></p><p class="step" id="stepText"></p><p class="sact" id="stepAct"></p></div><div class="glyph" id="glyph"></div></div>
   <div class="thumbs" id="thumbs">${r.steps.map((st, n) => `<button class="th" data-i="${n}" aria-label="Step ${n + 1}: ${esc(st[2])}">${glyph(r, n)}</button>`).join('')}</div>
   <div class="row steprow"><button class="btn ghost" id="prevS">Back a step</button><button class="btn" id="nextS">Done, next</button></div>`;
  $('#prevS').onclick = () => goStep(recipeState.i - 1);
  $('#nextS').onclick = () => recipeState.i < r.steps.length - 1 ? goStep(recipeState.i + 1) : finishRecipe();
  $('#stepbox').onclick = () => $('#nextS').click();
  panel.querySelectorAll('.thumbs .th').forEach(b => b.onclick = () => goStep(+b.dataset.i));
  $('#againDice').onclick = () => another($('#againDice .dice'));
  recipeState = { r, i: 0, chosen };
  drinkGlass(r, 0, false); goStep(0);
  focusIn('#nextS');
  /* if Halo's glyphs are still loading, draw them the moment they arrive */
  if (typeof act !== 'function') ANIM.addEventListener('load', () => { if (!recipeState || recipeState.r !== r) return;
    panel.querySelectorAll('.thumbs .th').forEach((b, n) => { b.innerHTML = glyph(r, n); }); const g = $('#glyph'); if (g) g.insertAdjacentHTML('afterbegin', glyph(r, recipeState.i)); }, { once: true });
}
/* "Another": Halo's dice roll, then a new barman's choice (R7 pool) */
function another(diceBox) {
  const r = recipeState && recipeState.r; if (!r) return;
  rollDice(diceBox, () => { const p = barmansChoice(r.id); p ? openRecipe(p.r.id, p) : home(); });
}
function goStep(i) {
  const s = recipeState; if (!s || i < 0) return;
  const r = s.r, n = r.steps.length, st = r.steps[i], action = actionFor(st, r);
  if (i >= n) return;
  s.i = i;
  $('#stepno').innerHTML = `Step <i>${i + 1}</i> of ${n}`;
  $('#stepText').textContent = st[2];
  const label = ACTION_LABEL[action];
  $('#stepAct').textContent = label && label.toLowerCase() !== st[2].toLowerCase() ? label : '';
  const a = glyphAct(r, i), timed = a === 'shake' || a === 'stir';
  $('#glyph').innerHTML = glyph(r, i) + (timed && st[1] ? `<span class="sec">${pie(st[1] / 30, 16)}<span>${st[1]} s</span></span>` : '');
  panel.querySelectorAll('.thumbs .th').forEach((b, k) => { b.classList.toggle('cur', k === i); b.classList.toggle('done', k < i); b.setAttribute('aria-current', k === i ? 'step' : 'false'); });
  const cur = panel.querySelector('.thumbs .th.cur'); if (cur) { const T = $('#thumbs'); T.scrollLeft = Math.max(0, cur.offsetLeft - T.clientWidth / 2 + cur.offsetWidth / 2); }
  $('#prevS').disabled = i === 0;
  $('#nextS').textContent = i === n - 1 ? 'Done, it’s ready' : 'Done, next';
  $('#stepbox').classList.remove('waiting');
  const fk = ['lime', 'grapefruit', 'lemon'].find(f => st[2].toLowerCase().includes(f)) || 'lemon';
  const main = r.ing.find(x => ['spirit', 'liqueur', 'wine'].includes(ING[x.k][1])) || r.ing[0];
  const B = LAYERS.bottles[main.k];
  const bottle = B ? `<image href="${B.src}" x="${-B.w / 2}" y="${-B.h * .75}" width="${B.w}" height="${B.h}"/>` : '';
  lightUp(action === 'honey' ? 'honey' : null);
  const pour = ['pour', 'top', 'strain', 'float'].includes(st[0]) || i > 0;
  drinkGlass(r, pour ? i / n : 0, false);
  /* R6: he acts the step out, then waits for your tap. No timer moves you on. */
  dio.perform(action, { r, fruit: ING[fk][2], honeyAt: HONEY_AT, bottle }).then(done => {
    if (!done || !recipeState || recipeState.i !== i) return;
    drinkGlass(r, pour ? (i + 1) / n : 0, i === n - 1);
    $('#stepbox').classList.add('waiting');
    $('#stepAct').textContent = i === n - 1 ? 'Ready. Your turn: tap when you’ve done it.' : 'Your turn. Tap when you’ve done it.';
  });
}
function finishRecipe() {
  const r = recipeState.r; drinkGlass(r, 1, true); dio.idle(); lightUp(null);
  $('#stepbox').innerHTML = `<p class="step done">There it is. ${golden ? 'Golden rim and all. ' : ''}Enjoy your ${esc(r.name)}.</p>`;
  $('#stepbox').onclick = null;
  panel.querySelectorAll('.thumbs .th').forEach(b => { b.classList.remove('cur'); b.classList.add('done'); });
  const row = panel.querySelector('.steprow');
  row.innerHTML = `<button class="btn ghost" id="again">Another, please</button><button class="btn" id="rdone">Back to the bar</button>`;
  $('#again').onclick = () => another($('#againDice .dice'));
  $('#rdone').onclick = home;
}

/* 2. Look settings: finish and coverage */
function applyLook() { document.body.classList.remove(...[...document.body.classList].filter(c => /^(fin|cov)-/.test(c))); document.body.classList.add(`fin-${LOOK.finish}`, `cov-${LOOK.coverage}`); dio.setLook(LOOK); }
const settings = $('#settings');
/* Text size: one scale for the recipe step and the reading panels; remembered on this device */
const TEXT_STEPS = [0.8, 0.9, 1, 1.15, 1.3, 1.5];
let textI = 2; try { const v = +localStorage.getItem('dio-text'); if (v >= 0 && v < TEXT_STEPS.length && localStorage.getItem('dio-text') !== null) textI = v; } catch (e) {}
function applyText() { const s = TEXT_STEPS[textI], d = document.documentElement; d.style.setProperty('--text-scale', s); d.style.setProperty('--step-size', Math.round(36 * s) + 'px');
  if (textI >= TEXT_STEPS.length - 2) d.dataset.big = ''; else delete d.dataset.big;   // phone: at the largest sizes the step glyph moves above the words
  try { localStorage.setItem('dio-text', textI); } catch (e) {} }
applyText();
function renderSettings() {
  settings.innerHTML = `<h3>Settings</h3>
   <fieldset><legend>Text size</legend><div class="sizer"><button type="button" class="btn" id="txtDown" aria-label="Smaller text" ${textI === 0 ? 'disabled' : ''}>A−</button><span class="sizeprev"><b style="font-size:${Math.round(36 * TEXT_STEPS[textI])}px">Aa</b><small>${Math.round(36 * TEXT_STEPS[textI])} px recipe steps</small></span><button type="button" class="btn" id="txtUp" aria-label="Larger text" ${textI === TEXT_STEPS.length - 1 ? 'disabled' : ''}>A+</button></div></fieldset>
   <h3>His look</h3>
   <fieldset><legend>Finish</legend><div class="seg">${Object.entries(FINISHES).map(([k, v]) => `<label><input type="radio" name="fin" value="${k}" ${LOOK.finish === k ? 'checked' : ''}>${v}</label>`).join('')}</div></fieldset>
   <fieldset><legend>Coverage</legend><div class="seg">${Object.entries(COVERAGES).map(([k, v]) => `<label><input type="radio" name="cov" value="${k}" ${LOOK.coverage === k ? 'checked' : ''} ${k === 'cheeky' && !LOOK.adult ? 'disabled' : ''}>${k === 'cheeky' ? 'Cheeky<span class="badge">ADULT</span>' : v}</label>`).join('')}</div></fieldset>
   <label class="adult"><input type="checkbox" id="adult" ${LOOK.adult ? 'checked' : ''}> <span>Allow adult looks. Cheeky stays implied: a fig leaf, and something always passes in front.</span></label>
   <p class="note">All three finishes are rendered. In the renders his coverage stays classical; the other coverages apply to the drawn fallback figure.</p>
   <p class="note">Leopard: “Prowling Leopard 3D Model Free” by iRahulRajput, <a href="https://sketchfab.com/3d-models/prowling-leopard-3d-model-free-d02a9709556348968fef810684b4e3fa" target="_blank" rel="noopener">Sketchfab</a>, CC BY 4.0, rendered in Blender.</p>`;
  $('#txtDown').onclick = () => { if (textI > 0) { textI--; applyText(); renderSettings(); } };
  $('#txtUp').onclick = () => { if (textI < TEXT_STEPS.length - 1) { textI++; applyText(); renderSettings(); } };
  settings.querySelectorAll('input[name=fin]').forEach(i => i.onchange = () => { LOOK.finish = i.value; applyLook(); });
  settings.querySelectorAll('input[name=cov]').forEach(i => i.onchange = () => { LOOK.coverage = i.value; applyLook(); });
  $('#adult').onchange = e => { LOOK.adult = e.target.checked; if (!LOOK.adult && LOOK.coverage === 'cheeky') LOOK.coverage = 'classical'; applyLook(); renderSettings(); };
}
const openSettings = e => { if (e) e.stopPropagation(); settings.hidden = !settings.hidden; if (!settings.hidden) renderSettings(); };
$('#gear').onclick = openSettings;
$('#lamp').addEventListener('click', openSettings);
settings.addEventListener('click', e => e.stopPropagation());
document.addEventListener('click', e => { if (!settings.hidden && !settings.contains(e.target) && !$('#lamp').contains(e.target)) settings.hidden = true; });
applyLook();

/* hooks for the screenshot script */
window.proto = { home, openMenu, startTalk, render: s => render(s), conv: () => conv, openRecipe, goStep, tellStory, openPhotos, openPaste, openShelf, honeyTalk, barmansChoiceGo, showHints,
  state: () => ({ screen, shot: shotName, step: recipeState && recipeState.i }),
  setLook: (f, c, a) => { LOOK.finish = f; if (a !== undefined) LOOK.adult = a; if (c) LOOK.coverage = c; applyLook(); renderSettings(); settings.hidden = false; },
  fill: () => { applyReading(readPhotos(PHOTOS.map(p => p.id)), ['shaker', 'strainer', 'jigger', 'spoon']); drawShelf(); } };
intro();
