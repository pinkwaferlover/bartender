/* Dionysus: the app. Screens: home, spirits, feels, drinks, az, search, recipe, away, bar.
   Three levels at most from home to a recipe. No instructions on screen: if a screen needs one, the screen is wrong. */

/* ---------- The Penicillin, step by step, the way a good bartender makes it ---------- */
RB.penicillin.steps = [
  ['muddle', 20, 'Muddle 3 coins of ginger in the tin'],
  ['pour-spirit', 8, '50 ml blended Scotch'],
  ['pour-citrus', 8, '22.5 ml lemon'],
  ['pour-syrup', 8, '20 ml honey syrup'],
  ['seal', 6, 'Ice in, close the tins'],
  ['shake', 12, 'Shake hard'],
  ['ice', 5, 'One big rock in the glass'],
  ['double-strain', 10, 'Double strain over the rock'],
  ['float', 8, '7.5 ml Islay over the back of a spoon']
];
R.forEach(r => r.total = r.steps.reduce((a, s) => a + s[1], 0));
const LONGEST = Math.max(...R.map(r => r.total));
const TIMED = { shake: 1, stir: 1, 'double-strain': 0 };

/* ---------- State ---------- */
const S = { scr: 'home', hist: [], spirit: null, kind: null, feel: null, letter: null, rid: null, q: '', filter: 'all', story: false,
  inv: new Set(INV0), made: { penicillin: 6, oldfashioned: 3, goldrush: 2 }, taps: 0 };
try { const v = JSON.parse(localStorage.getItem('dion-bar') || 'null'); if (v && v.length) S.inv = new Set(v); } catch (e) {}
const have = k => STAPLE.has(k) || S.inv.has(k);
function stat(r) { const miss = [], subs = []; for (const g of r.ing) { if (have(g.k)) continue; const s = g.subs.find(have); if (s) { subs.push([g.k, s]); continue; } if (g.o) continue; miss.push(g.k); } return { miss, subs, can: !miss.length }; }
const can = r => stat(r).can;
const season = () => { const m = new Date().getMonth() + 1; return m === 12 || m < 3 ? 'winter' : m < 6 ? 'spring' : m < 9 ? 'summer' : 'autumn'; };
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const fmt = s => s >= 60 ? `${Math.floor(s / 60)} min${s % 60 ? ' ' + (s % 60) + ' s' : ''}` : `${s} s`;
const lbl = k => (ING[k] || [k])[0];
function awayMap() { const m = {}; for (const r of R) { const s = stat(r); if (s.miss.length === 1) (m[s.miss[0]] = m[s.miss[0]] || []).push(r); } return Object.entries(m).sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0])); }

/* ---------- Small drawings ---------- */
const pie = (f, size, col = 'var(--acc)') => `<svg viewBox="0 0 40 40" width="${size}" height="${size}" aria-hidden="true"><circle cx="20" cy="20" r="17" fill="var(--faint)"/><path d="${arc(20, 20, 17, 0, Math.min(f, 1))}" fill="${col}"/></svg>`;
const timePie = (r, size) => pie(r.total / LONGEST, size);
const glass = (r, h, ghost) => glassSide(r, h, { ghost });
const ICON = {
  back: `<svg viewBox="0 0 40 40" width="34" height="34"><path d="M24 8 L12 20 L24 32" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  search: `<svg viewBox="0 0 40 40" width="28" height="28"><circle cx="17" cy="17" r="10" fill="none" stroke="currentColor" stroke-width="2.6"/><path d="M25 25 L33 33" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/></svg>`,
  mic: `<svg viewBox="0 0 40 40" width="26" height="26"><rect x="14" y="5" width="12" height="20" rx="6" fill="currentColor"/><path d="M9 19 q0 11 11 11 q11 0 11 -11 M20 30 v6" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/></svg>`,
  story: `<svg viewBox="0 0 40 40" width="30" height="30"><path d="M8 10 h24 M10 14 h20 M12 14 v16 M20 14 v16 M28 14 v16 M8 32 h24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>`,
  load: `<svg viewBox="0 0 40 40" width="28" height="28"><path d="M20 26 V8 M12 15 L20 7 L28 15" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M7 26 v6 h26 v-6" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  grapes: `<svg viewBox="0 0 40 40" width="40" height="40"><path d="M20 9 q4 -6 11 -5 q-3 7 -11 5z" fill="var(--grape)" opacity=".7"/><g fill="var(--grape)"><circle cx="13" cy="15" r="5"/><circle cx="23" cy="15" r="5"/><circle cx="18" cy="23" r="5"/><circle cx="28" cy="22" r="4.5"/><circle cx="13" cy="25" r="4.5" opacity=".8"/><circle cx="23" cy="31" r="4.5"/></g></svg>`
};
const SPIRITS_ICON = h => `<svg viewBox="0 0 120 100" width="${h * 1.2}" height="${h}" aria-hidden="true"><g transform="translate(4 8) scale(.9)"><path d="${BOT.gin}" fill="${SPIRIT.gin[1]}"/></g><g transform="translate(30 0)"><path d="${BOT.whisky}" fill="${SPIRIT.whisky[1]}"/></g><g transform="translate(66 14) scale(.86)"><path d="${BOT.rum}" fill="${SPIRIT.rum[1]}"/></g></svg>`;
const FEEL_ICON = h => { let s = `<svg viewBox="0 0 100 100" width="${h}" height="${h}" aria-hidden="true">`; Object.keys(FEEL).forEach((f, n) => { const a = n / 6 * 2 * Math.PI - Math.PI / 2; s += `<circle cx="${50 + 32 * Math.cos(a)}" cy="${50 + 32 * Math.sin(a)}" r="13" fill="var(${FEEL[f][1]})"/>`; }); return s + '</svg>'; };
/* A–Z: three letters with the middle one swollen, the way the finder behaves */
const AZ_ICON = h => `<svg viewBox="0 0 120 100" width="${h * 1.2}" height="${h}" aria-hidden="true" style="font-family:var(--display)"><text x="22" y="66" text-anchor="middle" font-size="30" fill="var(--mute)">A</text><text x="60" y="76" text-anchor="middle" font-size="64" fill="var(--ink)">B</text><text x="98" y="66" text-anchor="middle" font-size="30" fill="var(--mute)">C</text></svg>`;
const BAR_ICON = h => `<svg viewBox="0 0 120 100" width="${h * 1.2}" height="${h}" aria-hidden="true"><g transform="translate(2 18) scale(.8)"><path d="${BOT.aperitif}" fill="#7a2418"/></g><g transform="translate(32 4) scale(.96)"><path d="${BOT.whisky}" fill="#b8661c"/></g><g transform="translate(74 22) scale(.76)"><path d="${BOT.gin}" fill="#cfe2e8"/></g></svg>`;

/* Two dice, drawn in 3D. Hover jiggles; a tap rolls them, then the drink appears. */
const PIPS = { 1: [5], 2: [1, 9], 3: [1, 5, 9], 4: [1, 3, 7, 9], 5: [1, 3, 5, 7, 9], 6: [1, 3, 4, 6, 7, 9] };
const face = (n, cls) => `<div class="face ${cls}">${[1, 2, 3, 4, 5, 6, 7, 8, 9].map(p => `<i${PIPS[n].includes(p) ? ' class="on"' : ''}></i>`).join('')}</div>`;
const die = (k) => `<div class="die ${k}">${face(1, 'f1')}${face(6, 'f6')}${face(2, 'f2')}${face(5, 'f5')}${face(3, 'f3')}${face(4, 'f4')}</div>`;
const dice = (size, label) => `<button class="dice" data-act="surprise" style="--ds:${size}px" aria-label="Surprise me"><span class="pair">${die('d1')}${die('d2')}</span>${label ? `<span class="cap">${label}</span>` : ''}</button>`;
function roll(btn, then) {
  if (btn.classList.contains('rolling')) return;
  btn.classList.add('rolling');
  btn.querySelectorAll('.die').forEach((d, n) => {
    const x = 720 + 90 * Math.floor(Math.random() * 4), y = 720 + 90 * Math.floor(Math.random() * 4), z = n ? -30 : 25;
    d.style.transition = 'transform 1.05s cubic-bezier(.15,.75,.25,1)';
    d.style.transform = `rotateX(${x}deg) rotateY(${y}deg) rotateZ(${z}deg)`;
  });
  setTimeout(() => { then(); }, 1150);
}

/* ---------- The smooth strip: follows the finger, carries momentum, settles gently ---------- */
class Strip {
  constructor(host, n, o) {
    this.h = host; this.n = n; this.w = o.itemW; this.gap = o.gap ?? 28; this.lift = o.lift ?? .16; this.start = o.start ?? 0; this.align = o.align || 'center'; this.onTap = o.onTap;
    this.track = host.querySelector('.track'); this.items = [...this.track.children];
    this.items.forEach((el, k) => { el.style.width = this.w + 'px'; });
    this.W = host.clientWidth; this.step = this.w + this.gap;
    this.fx = this.align === 'center' ? this.W / 2 : (o.pad ?? 40) + this.w / 2;          // where the focus sits
    this.maxX = this.fx - this.w / 2 - (this.align === 'center' ? 0 : 0);                   // first item at focus
    this.minX = Math.min(this.maxX, this.fx - (n - 1) * this.step - this.w / 2);           // last item at focus
    if (this.align !== 'center') this.minX = Math.min(this.maxX, this.W - (o.pad ?? 40) - n * this.step + this.gap);
    this.x = this.clamp(this.maxX - this.start * this.step); this.v = 0; this.raf = 0;
    this.bind(); this.draw();
  }
  clamp(x) { return Math.max(this.minX, Math.min(this.maxX, x)); }
  draw() {
    this.items.forEach((el, k) => {
      const left = this.x + k * this.step, c = left + this.w / 2, d = (c - this.fx) / this.step, a = Math.abs(d);
      const s = 1 + this.lift * Math.max(0, 1 - a);
      el.style.transform = `translate3d(${left}px,0,0) scale(${s})`;
      el.style.opacity = this.lift ? Math.max(.35, 1 - Math.max(0, a - 1.2) * .22) : 1;
      el.style.zIndex = 10 - Math.round(a);
    });
  }
  animateTo(target) {
    cancelAnimationFrame(this.raf); const x0 = this.x, t0 = performance.now(), dur = 520;
    const ease = t => 1 - Math.pow(1 - t, 4);
    const tick = now => { const t = Math.min(1, (now - t0) / dur); this.x = x0 + (target - x0) * ease(t); this.draw(); if (t < 1) this.raf = requestAnimationFrame(tick); };
    this.raf = requestAnimationFrame(tick);
  }
  settle(v) {
    const proj = this.x + v * 260;                                 // where momentum would carry it
    const k = Math.round((this.maxX - proj) / this.step);
    this.animateTo(this.clamp(this.maxX - k * this.step));
  }
  bind() {
    let p = null, samples = [];
    const sx = e => e.clientX / SCALE;
    this.h.addEventListener('pointerdown', e => { cancelAnimationFrame(this.raf); p = { x: sx(e), x0: this.x, moved: false, id: e.pointerId }; samples = [[performance.now(), this.x]]; });
    this.h.addEventListener('pointermove', e => {
      if (!p) return; const dx = sx(e) - p.x; if (Math.abs(dx) > 6 && !p.moved) { p.moved = true; this.h.setPointerCapture(p.id); }
      if (!p.moved) return;
      let x = p.x0 + dx; if (x > this.maxX) x = this.maxX + (x - this.maxX) * .35; if (x < this.minX) x = this.minX + (x - this.minX) * .35;
      this.x = x; this.draw(); samples.push([performance.now(), x]); if (samples.length > 6) samples.shift();
    });
    const up = e => {
      if (!p) return; const was = p; p = null;
      if (!was.moved) { const it = e.target.closest('.track > *'); if (it && this.onTap) { S.taps++; this.onTap(this.items.indexOf(it), it); } return; }
      const [t0, x0] = samples[0], [t1, x1] = samples[samples.length - 1]; const v = t1 > t0 ? (x1 - x0) / (t1 - t0) : 0;
      swipes++; meter(); this.settle(v);
    };
    this.h.addEventListener('pointerup', up); this.h.addEventListener('pointercancel', () => { p = null; this.settle(0); });
    let wt; this.h.addEventListener('wheel', e => { e.preventDefault(); cancelAnimationFrame(this.raf); this.x = this.clamp(this.x - (Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY)); this.draw(); clearTimeout(wt); wt = setTimeout(() => this.settle(0), 120); }, { passive: false });
  }
}
let swipes = 0;
function strip(id, n, o) { const h = document.getElementById(id); if (h && n) new Strip(h, n, o); }

/* ---------- Navigation ---------- */
const view = () => document.getElementById('screen');
function go(scr, patch = {}) { if (S.scr !== scr || patch.rid) S.hist.push({ scr: S.scr, spirit: S.spirit, kind: S.kind, feel: S.feel, letter: S.letter, rid: S.rid }); Object.assign(S, { story: false }, patch, { scr }); render(); }
function back() { const h = S.hist.pop(); if (!h) return home(); Object.assign(S, h, { story: false }); render(); }
function home() { S.hist = []; S.taps = 0; swipes = 0; Object.assign(S, { scr: 'home', spirit: null, kind: null, feel: null, letter: null, story: false, q: '' }); render(); }
function surprise(btn, pool) {
  const list = (pool || R).filter(can).filter(r => r.id !== S.rid);
  roll(btn, () => { const r = list[Math.floor(Math.random() * list.length)] || R.find(can); go('recipe', { rid: r.id, fromDice: true }); });
}
function meter() { const m = document.getElementById('meter'); if (m) m.innerHTML = `Taps <b>${S.taps}</b> · swipes <b>${swipes}</b> · screen <b>${S.scr}</b>`; }

/* ---------- Shared pieces ---------- */
const header = (title, sub, right = '') => `<header class="hd"><button class="ib" data-act="back" aria-label="Back">${ICON.back}</button>
  <div class="ttl">${title}${sub ? `<span class="sub">${sub}</span>` : ''}</div><div class="hr">${right}</div></header>`;
const searchBar = (live) => `<form class="sb" data-act="searchform" role="search"><span class="mi">${ICON.search}</span>
  <input id="q" type="search" inputmode="search" enterkeyhint="search" autocomplete="off" placeholder=" " aria-label="Search drinks, spirits, flavours or ingredients" value="${esc(S.q)}" ${live ? '' : 'data-act="tosearch" readonly'}>
  <span class="cyc" aria-hidden="true">${['something smoky', 'honey', 'warm me up', 'long and fresh', 'bitter'].map((t, n) => `<em style="animation-delay:${n * 3}s">${t}</em>`).join('')}</span>
  <button type="button" class="mic" data-act="mic" aria-label="Speak">${ICON.mic}</button></form>`;
const drinkCard = (r, extra = '') => { const s = stat(r); return `<button class="dc${s.can ? '' : ' near'}" data-rid="${r.id}" aria-label="${esc(r.name)}">
  <span class="pic">${glass(r, 150)}</span><span class="nm">${esc(r.name)}</span>
  <span class="meta">${feelIco(r.feel, 16)}<span>${FEEL[r.feel][0]}</span><span class="dotsep"></span>${timePie(r, 16)}<span>${fmt(r.total)}</span></span>
  ${s.can ? '' : `<span class="need">+ ${esc(lbl(s.miss[0]))}</span>`}${extra}</button>`; };
const miniCard = (r, cap) => `<button class="mc" data-rid="${r.id}" aria-label="${esc(r.name)}"><span class="pic">${glass(r, 124)}</span><span class="nm">${esc(r.name)}</span><span class="cap">${cap}</span></button>`;

/* ---------- Screens ---------- */
function scrHome() {
  const ready = R.filter(can), ss = season();
  const tonight = ready.filter(r => r.season.includes(ss)).sort((a, b) => (S.made[b.id] || 0) - (S.made[a.id] || 0));
  const fav = ready.filter(r => S.made[r.id]).sort((a, b) => S.made[b.id] - S.made[a.id]);
  const away = R.filter(r => stat(r).miss.length === 1).slice(0, 4);
  const seen = new Set(); const sug = [];
  const add = (r, cap) => { if (!seen.has(r.id)) { seen.add(r.id); sug.push(miniCard(r, cap)); } };
  fav.slice(0, 2).forEach(r => add(r, `Your usual`));
  tonight.slice(0, 5).forEach(r => add(r, ss === 'winter' || ss === 'autumn' ? 'For a cold night' : 'For a warm evening'));
  away.forEach(r => add(r, `+ ${lbl(stat(r).miss[0])}`));
  return `<div class="home">
    <div class="brand">DIONYSUS</div>${searchBar(false)}
    <button class="barbtn" data-go="bar">${BAR_ICON(40)}<span><b>Your bar</b><small>${S.inv.size} bottles</small></span></button>
    <div class="ways">
      <button class="way" data-go="spirits">${SPIRITS_ICON(110)}<span class="cap">By spirit</span></button>
      <button class="way" data-go="feels">${FEEL_ICON(110)}<span class="cap">By feel</span></button>
      ${dice(64, 'Surprise me').replace('class="dice"', 'class="dice way"')}
      <button class="way" data-go="az">${AZ_ICON(110)}<span class="cap">A–Z</span></button>
    </div>
    <div class="sugwrap" id="sug"><div class="track">${sug.join('')}</div></div>
  </div>`;
}
/* By spirit and by feel open the way search does: one row per choice, its drinks previewed. */
const FILTERS = () => `<div class="filt">${[['all', 'All'], ['now', 'Make now'], ['one', 'One more bottle']].map(([k, t]) => `<button class="fb${S.filter === k ? ' on' : ''}" data-filter="${k}">${t}</button>`).join('')}</div>`;
const keepF = r => S.filter === 'all' || (S.filter === 'now' ? can(r) : stat(r).miss.length === 1);
function groupRow(attr, label, icon, list) {
  const hits = list.filter(keepF).sort((a, b) => can(b) - can(a));
  return `<button class="sg grp" ${attr}><span class="nm">${icon}<span>${label}</span></span><span class="peek">${hits.slice(0, 4).map(r => glass(r, 46, !can(r))).join('')}</span>
    <span class="names">${hits.slice(0, 3).map(r => esc(r.name)).join(' · ')}</span><span class="st">${hits.length}</span></button>`;
}
function scrSpirits() {
  const ks = Object.keys(SPIRIT).filter(k => R.some(r => r.spirit === k));
  return header('By spirit') + FILTERS() + `<div class="res" id="res">${ks.map(k => groupRow(`data-spirit="${k}"`, SPIRIT[k][0], spIco(k, 34), R.filter(r => r.spirit === k))).join('')}</div>`;
}
function scrFeels() {
  return header('By feel') + FILTERS() + `<div class="res" id="res">${Object.keys(FEEL).map(f => groupRow(`data-feel="${f}"`, FEEL[f][0], feelIco(f, 30), R.filter(r => r.feel === f))).join('')}</div>`;
}
function drinksPool() { return R.filter(r => (S.spirit ? r.spirit === S.spirit : true) && (S.feel ? r.feel === S.feel : true) && (S.kind ? r.ing.some(g => g.k === S.kind) : true)); }
function scrDrinks() {
  const pool = drinksPool(), ready = pool.filter(can), near = pool.filter(r => stat(r).miss.length === 1);
  const title = S.spirit ? `${spIco(S.spirit, 44)}<span>${SPIRIT[S.spirit][0]}</span>` : `${feelIco(S.feel, 36)}<span>${FEEL[S.feel][0]}</span>`;
  const kinds = S.spirit === 'whisky' ? WH.filter(have) : [];
  const right = (kinds.length ? `<div class="kinds">${kinds.map(k => `<button class="kind${S.kind === k ? ' on' : ''}" data-kind="${k}">${ingIco(k, 40)}<small>${lbl(k).replace(' whiskey', '').replace(' Scotch', '').replace('Blended', 'Blended')}</small></button>`).join('')}</div>` : '') + dice(30);
  return header(title, `${ready.length}`, right) + `<div class="list" id="dl"><div class="track">${ready.map(r => drinkCard(r)).join('')}</div></div>
    ${near.length ? `<div class="rowlbl">One bottle more</div><div class="nearrow" id="nr"><div class="track">${near.map(r => miniCard(r, `+ ${esc(lbl(stat(r).miss[0]))}`)).join('')}</div></div>` : ''}`;
}
const ALPHA = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
function scrAZ() { return header('A–Z') + `<div class="az" id="az"></div>`; }
/* Outer ring: letters, swelling under the finger. Lift on a letter and its cocktails pop out of the centre as an inner ring,
   which swells under the finger the same way. Lift on a cocktail to open it; tap the empty centre to close the inner ring. */
function mountAZ() {
  const az = document.getElementById('az'); if (!az) return;
  const byL = {}; R.forEach(r => { const k = r.name[0].toUpperCase(); (byL[k] = byL[k] || []).push(r); });
  const W = az.clientWidth, H = az.clientHeight, cx = W / 2, cy = H / 2 + 4, RR = Math.min(W, H) * .44, R2 = RR * .56;
  const els = [...ALPHA].map(c => { const e = document.createElement('div'); e.className = 'lt' + (byL[c] ? '' : ' none'); e.textContent = c; az.appendChild(e); return e; });
  const pos = (n, N, r) => { const a = (n / N) * 2 * Math.PI - Math.PI / 2; return [cx + r * Math.cos(a), cy + r * Math.sin(a), a]; };
  const fish = (d, sd) => Math.exp(-(d * d) / (2 * sd * sd));
  let fL = null, fD = null, mode = null, letter = S.letter, live = false, inner = [], last = -1;
  const drawLetters = () => els.forEach((e, n) => { let d = fL == null ? 99 : Math.abs(n - fL); if (fL != null) d = Math.min(d, 26 - d); const b = fish(d, 1.3);
    const [x, y, a] = pos(n, 26, RR), p = 22 * b; e.style.transform = `translate(${x + p * Math.cos(a) - 28}px,${y + p * Math.sin(a) - 28}px) scale(${1 + 1.9 * b})`;
    e.classList.toggle('hot', ALPHA[n] === letter || d < .5); });
  const buildInner = (L, active) => {
    shown = L; inner.forEach(e => e.remove()); inner = [];
    const ls = byL[L] || []; const N = ls.length;
    ls.forEach((r, n) => { const e = document.createElement('button'); e.className = 'ic' + (active ? ' live' : ''); e.dataset.rid = r.id;
      e.innerHTML = `${glass(r, 84, !can(r))}<span>${esc(r.name)}</span>`; e.style.animationDelay = (active ? n * 45 : 0) + 'ms'; az.appendChild(e); inner.push(e); });
    live = active; fD = null; drawInner();
  };
  const drawInner = () => { const N = inner.length; inner.forEach((e, n) => { let d = fD == null ? 99 : Math.abs(n - fD); if (fD != null) d = Math.min(d, N - d); const b = N > 1 ? fish(d, .7) : 0;
    const [x, y] = N === 1 ? [cx, cy] : pos(n, N, R2); e.style.setProperty('--dx', (cx - x) + 'px'); e.style.setProperty('--dy', (cy - y) + 'px'); e.style.transform = `translate(${x - 60}px,${y - 62}px) scale(${1 + .5 * b})`; e.style.zIndex = 5 + Math.round(b * 5); }); };
  const polar = e => { const b = az.getBoundingClientRect(); const x = (e.clientX - b.left) / SCALE - cx, y = (e.clientY - b.top) / SCALE - cy;
    return { d: Math.hypot(x, y), a: ((Math.atan2(y, x) + Math.PI / 2) / (2 * Math.PI) + 1) % 1 }; };
  const nearestL = v => { let best = null, bd = 99; [...ALPHA].forEach((c, n) => { if (!byL[c]) return; let d = Math.abs(n - v); d = Math.min(d, 26 - d); if (d < bd) { bd = d; best = n; } }); return best; };
  const zone = p => p.d > (RR + R2) / 2 ? 'letters' : (inner.length && p.d > R2 * .45 ? 'drinks' : 'centre');
  let shown = null;
  const aim = p => { if (mode === 'letters') { fL = p.a * 26; drawLetters(); const k = Math.round(fL) % 26; if (k !== last) { last = k; if (byL[ALPHA[k]] && ALPHA[k] !== shown) buildInner(ALPHA[k], true); try { navigator.vibrate && navigator.vibrate(4); } catch (_) {} } }
    else if (mode === 'drinks' && inner.length > 1) { fD = p.a * inner.length; drawInner(); } };
  drawLetters(); if (letter) buildInner(letter, true);
  az.addEventListener('pointerdown', e => { const p = polar(e); mode = zone(p); if (mode === 'centre') { mode = null; return; } az.setPointerCapture(e.pointerId); aim(p); });
  /* Mouse hover swells letters and cocktails the same way a held finger does; nothing is chosen until a click. */
  const rest = () => { fL = letter ? ALPHA.indexOf(letter) : null; drawLetters(); if (fD != null) { fD = null; drawInner(); } };
  az.addEventListener('pointermove', e => { const p = polar(e); if (mode) return aim(p); if (e.pointerType !== 'mouse') return; const z = zone(p);
    if (z === 'letters') { fL = p.a * 26; drawLetters(); const k = Math.round(fL) % 26; if (k !== last) { last = k; if (byL[ALPHA[k]] && ALPHA[k] !== shown) buildInner(ALPHA[k], true); } if (fD != null) { fD = null; drawInner(); } }
    else if (z === 'drinks' && inner.length > 1) { fD = p.a * inner.length; drawInner(); if (fL != null && fL !== ALPHA.indexOf(letter)) { fL = letter ? ALPHA.indexOf(letter) : null; drawLetters(); } }
    else rest(); });
  az.addEventListener('pointerup', e => { const p = polar(e), m = mode; mode = null;
    if (!m) { if (zone(p) === 'centre' && live) { letter = S.letter = null; fL = null; inner.forEach(x => x.remove()); inner = []; live = false; drawLetters(); } return; }
    if (m === 'letters') { const n = nearestL(fL); if (n == null) return; S.taps++; letter = S.letter = ALPHA[n]; fL = n; last = -1; const ls = byL[letter];
      if (ls.length === 1) return go('recipe', { rid: ls[0].id }); buildInner(letter, true); drawLetters(); return; }
    if (m === 'drinks') { const t = document.elementFromPoint(e.clientX, e.clientY); const hit = t && t.closest('.ic');
      const k = hit ? inner.indexOf(hit) : (fD == null ? -1 : Math.round(fD) % inner.length); if (k >= 0) { S.taps++; go('recipe', { rid: inner[k].dataset.rid }); } } });
  az.addEventListener('pointerleave', () => { if (mode) return; last = -1; if (letter) { if (shown !== letter) buildInner(letter, true); } else { inner.forEach(x => x.remove()); inner = []; shown = null; live = false; } rest(); });
}
const SUGQ = [['something smoky', 'Smoky'], ['honey', 'Honey'], ['warm me up', 'Warm'], ['long and fresh', 'Long and fresh'], ['bitter', 'Bitter'], ['after dinner', 'After dinner']];
function searchR(q) {
  q = q.toLowerCase().trim(); if (!q) return [];
  const words = q.replace(/\b(something|anything|with|and|a|the|me|up)\b/g, ' ').split(/\s+/).filter(w => w.length > 1);
  const syn = { warm: 'hot warm', smoky: 'smoky peaty islay', long: 'long highball', fresh: 'fresh', bitter: 'bitter campari', dinner: 'after dinner coffee almond' };
  return R.map(r => { const hay = (r.name + ' ' + SPIRIT[r.spirit][0] + ' ' + FEEL[r.feel][0] + ' ' + r.ing.map(g => lbl(g.k)).join(' ') + ' ' + r.tags + ' ' + r.glass).toLowerCase();
    let sc = 0; words.forEach(w => { const alts = (syn[w] || w).split(' '); if (r.name.toLowerCase().startsWith(w)) sc += 5; else if (alts.some(a => hay.includes(a))) sc += 2; }); return [r, sc]; })
    .filter(x => x[1] >= 2).sort((a, b) => b[1] - a[1]).map(x => x[0]);
}
function statusCell(r) { const s = stat(r); return s.can ? `<span class="ok">${s.subs.length ? 'Make now · swap' : 'Make now'}</span>` : `<span class="no">+ ${esc(lbl(s.miss[0]))}${s.miss.length > 1 ? ` +${s.miss.length - 1}` : ''}</span>`; }
function resultRow(r) { return `<button class="rr" data-rid="${r.id}">${glass(r, 64, !can(r))}<span class="nm">${esc(r.name)}</span>
  <span class="at">${spIco(r.spirit, 26)}<span>${SPIRIT[r.spirit][0]}</span></span><span class="at">${feelIco(r.feel, 18)}<span>${FEEL[r.feel][0]}</span></span><span class="st">${statusCell(r)}</span></button>`; }
function scrSearch() {
  const fl = FILTERS();
  return `<header class="hd"><button class="ib" data-act="back" aria-label="Back">${ICON.back}</button>${searchBar(true)}</header>${fl}<div class="res" id="res"></div>`;
}
function fillSearch() {
  const box = document.getElementById('res'); if (!box) return;
  const keep = r => S.filter === 'all' || (S.filter === 'now' ? can(r) : stat(r).miss.length === 1);
  if (!S.q.trim()) {
    box.innerHTML = SUGQ.map(([q, t], n) => { const hits = searchR(q).filter(keep); return `<button class="sg" data-q="${q}" style="animation-delay:${n * 40}ms"><span class="nm">${t}</span>
      <span class="peek">${hits.slice(0, 4).map(r => glass(r, 46, !can(r))).join('')}</span><span class="names">${hits.slice(0, 3).map(r => esc(r.name)).join(' · ')}</span><span class="st">${hits.length}</span></button>`; }).join('');
    return;
  }
  const res = searchR(S.q).filter(keep);
  box.innerHTML = res.length ? res.slice(0, 8).map(resultRow).join('') : `<div class="none">Nothing for “${esc(S.q)}”.</div>`;
}
function scrRecipe() {
  const r = RB[S.rid], s = stat(r), subs = Object.fromEntries(s.subs);
  const st = STORY[r.id];
  const ingRows = r.ing.map(g => { const ok = have(g.k), sub = subs[g.k];
    const q = typeof g.q === 'number' ? (Number.isInteger(g.q) ? g.q : g.q.toFixed(1)) : g.q;
    let unit = g.u || '', name = lbl(g.k); const m = unit.match(/^ml (\w+)$/);
    if (m) { unit = 'ml'; name = m[1] === 'juice' ? name + ' juice' : m[1] === 'espresso' ? 'Espresso' : m[1] === 'hot' ? 'Hot ' + name.toLowerCase() : name; }
    const right = ok ? '' : sub ? `<span class="swap">→ ${esc(lbl(sub))}</span>` : g.o ? `<span class="opt">optional</span>` : `<span class="need">need</span>`;
    return `<div class="ir${ok || sub ? '' : ' miss'}"><span class="ii">${ingIco(g.k, 34, { ghost: !ok && !sub })}</span><span class="iq">${q}</span><span class="iu">${esc(unit)}</span><span class="in">${esc(name)}</span><span class="ix">${right}</span></div>`; }).join('');
  const steps = r.steps.map(([a0, sec, t], n) => { const a = a0 === 'strain' && r.steps.slice(0, n).some(x => x[0] === 'stir') ? 'strain-glass' : a0; const timed = a === 'shake' || a === 'stir';
    return `<div class="step"><div class="sa">${act(a, r.colour, { glass: r.glass })}</div><div class="sn">${n + 1}</div><div class="stx">${esc(t)}</div>${timed ? `<div class="sec">${pie(sec / 30, 18)}<span>${sec} s</span></div>` : ''}</div>`; }).join('');
  return header('', '', `<button class="storyb${S.story ? ' on' : ''}" data-act="story">${ICON.story}<span>Story</span></button>${dice(30)}`) + `
  <div class="rp">
    <div class="rl"><div class="rg">${glass(r, 250)}</div><h1 class="rn">${esc(r.name)}</h1>
      <div class="rm"><span>${spIco(r.spirit, 26)}${SPIRIT[r.spirit][0]}</span><span>${feelIco(r.feel, 20)}${FEEL[r.feel][0]}</span><span>${timePie(r, 20)}${fmt(r.total)}</span></div></div>
    <div class="rr2"><div class="ing">${ingRows}</div></div>
  </div>
  <div class="steps" id="stp"><div class="track">${steps}</div></div>
  ${S.story && st ? `<aside class="story"><div class="sq">${esc(st.tell)}</div><div class="sm"><b>${esc(st.by)}</b><span>${esc(st.at)}</span><span>${esc(st.when)}</span>${st.kind === 'legend' ? '<span class="lg">as legend has it</span>' : ''}</div></aside>` : ''}`;
}
function scrAway() {
  const m = awayMap();
  return header('One bottle away', `${m.length}`) + `<div class="away">${m.map(([k, rs]) => `<div class="ar"><div class="ak">${ingIco(k, 56)}<span class="nm">${esc(lbl(k))}</span><span class="un">+${rs.length}</span></div>
    <div class="ad">${rs.map(r => `<button class="mini" data-rid="${r.id}">${glass(r, 70)}<span>${esc(r.name)}</span></button>`).join('')}</div></div>`).join('')}</div>`;
}
const GROUPS = [['Spirits', k => ING[k][1] === 'spirit'], ['Wines and aperitifs', k => ['wine', 'liqueur'].includes(ING[k][1]) && ING[k][3] === 'aperitif'], ['Liqueurs', k => ING[k][1] === 'liqueur' && ING[k][3] !== 'aperitif'], ['Bitters', k => ING[k][1] === 'bitters'], ['Fresh', k => ['fruit', 'herb'].includes(ING[k][1])], ['Sweet', k => ING[k][1] === 'sweet'], ['Mixers and more', k => ['mixer', 'other'].includes(ING[k][1]) && k !== 'hot water']];
function scrBar() {
  const right = `<label class="loadb">${ICON.load}<span>Load my bar</span><input type="file" id="file" accept=".json,application/json" hidden></label>`;
  return header('Your bar', `${S.inv.size}`, right) + `<div class="inv">${GROUPS.map(([g, f]) => { const ks = Object.keys(ING).filter(f); return `<section><h3>${g}</h3><div class="ig">${ks.map(k => `<button class="it${have(k) ? '' : ' off'}" data-inv="${k}">${ingIco(k, 48, { ghost: !have(k) })}<span>${esc(lbl(k))}</span></button>`).join('')}</div></section>`; }).join('')}</div>`;
}

/* ---------- Render and wiring ---------- */
function render() {
  const v = view();
  v.innerHTML = { home: scrHome, spirits: scrSpirits, feels: scrFeels, drinks: scrDrinks, az: scrAZ, search: scrSearch, recipe: scrRecipe, away: scrAway, bar: scrBar }[S.scr]();
  v.dataset.scr = S.scr;
  const tapRid = (i, el) => go('recipe', { rid: el.dataset.rid });
  strip('sug', v.querySelectorAll('#sug .track > *').length, { itemW: 168, gap: 26, align: 'left', pad: 48, lift: 0, onTap: tapRid });
  const n = v.querySelectorAll('#dl .track > *').length; strip('dl', n, { itemW: 210, gap: 44, lift: .1, start: Math.min(2, Math.floor((n - 1) / 2)), onTap: tapRid });
  strip('nr', v.querySelectorAll('#nr .track > *').length, { itemW: 140, gap: 18, align: 'left', pad: 48, lift: 0, onTap: tapRid });
  const sn = v.querySelectorAll('#stp .track > *').length; if (sn * 196 > 1024 - 80) strip('stp', sn, { itemW: 180, gap: 16, align: 'left', pad: 40, lift: 0 }); else v.querySelector('#stp')?.classList.add('fixed');
  if (S.scr === 'az') mountAZ();
  if (S.scr === 'search') { fillSearch(); const q = document.getElementById('q'); q.focus(); q.setSelectionRange(q.value.length, q.value.length); }
  meter();
}
document.addEventListener('click', e => {
  const t = e.target.closest('[data-act],[data-go],[data-rid],[data-kind],[data-filter],[data-q],[data-inv],[data-spirit],[data-feel]'); if (!t || t.closest('.track') && !t.matches('.dice') || t.closest('.az')) return;
  const a = t.dataset.act;
  if (t.matches('.dice')) { e.preventDefault(); S.taps++; surprise(t, S.scr === 'drinks' ? drinksPool() : null); return; }
  if (a === 'back') return back();
  if (a === 'story') { S.taps++; S.story = !S.story; return render(); }
  if (a === 'tosearch') { S.taps++; return go('search'); }
  if (a === 'mic') { const SR = window.SpeechRecognition || window.webkitSpeechRecognition; if (S.scr !== 'search') go('search'); const q = document.getElementById('q'); if (!SR) { q && q.focus(); return; }
    try { const rec = new SR(); rec.lang = 'en-GB'; t.classList.add('on'); rec.onresult = ev => { S.q = [...ev.results].map(x => x[0].transcript).join(''); const qq = document.getElementById('q'); if (qq) qq.value = S.q; fillSearch(); }; rec.onend = () => t.classList.remove('on'); rec.start(); } catch (_) { q && q.focus(); } return; }
  if (t.dataset.go) { S.taps++; return go(t.dataset.go); }
  if (t.dataset.rid) { S.taps++; return go('recipe', { rid: t.dataset.rid }); }
  if (t.dataset.spirit && t.matches('.grp')) { S.taps++; return go('drinks', { spirit: t.dataset.spirit, feel: null, kind: null }); }
  if (t.dataset.feel && t.matches('.grp')) { S.taps++; return go('drinks', { feel: t.dataset.feel, spirit: null, kind: null }); }
  if (t.dataset.kind) { S.taps++; S.kind = S.kind === t.dataset.kind ? null : t.dataset.kind; return render(); }
  if (t.dataset.filter) { S.filter = t.dataset.filter; return S.scr === 'search' ? (document.querySelectorAll('.fb').forEach(b => b.classList.toggle('on', b === t)), fillSearch()) : render(); }
  if (t.dataset.q) { S.taps++; S.q = t.dataset.q; document.getElementById('q').value = S.q; return fillSearch(); }
  if (t.dataset.inv) { const k = t.dataset.inv; S.inv.has(k) ? S.inv.delete(k) : S.inv.add(k); try { localStorage.setItem('dion-bar', JSON.stringify([...S.inv])); } catch (_) {} return render(); }
});
document.addEventListener('input', e => { if (e.target.id === 'q') { S.q = e.target.value; fillSearch(); } });
document.addEventListener('submit', e => { e.preventDefault(); const r = searchR(S.q)[0]; if (r) { S.taps++; go('recipe', { rid: r.id }); } });
document.addEventListener('change', e => { if (e.target.id !== 'file') return; const f = e.target.files[0]; if (!f) return; const rd = new FileReader();
  rd.onload = () => { try { const j = JSON.parse(rd.result); const list = Array.isArray(j) ? j : j.have || (j.items || []).map(x => x.id || x); if (!list.length) throw 0; S.inv = new Set(list.map(x => String(x).toLowerCase())); try { localStorage.setItem('dion-bar', JSON.stringify([...S.inv])); } catch (_) {} render(); } catch (_) { const h = document.querySelector('.ttl .sub'); if (h) h.textContent = '×'; } };
  rd.readAsText(f); });

/* ---------- Fit the 1024 x 768 screen to the frame ---------- */
let SCALE = 1;
function fit() { const fr = document.getElementById('frame'); SCALE = fr.clientWidth / 1024; document.getElementById('tab').style.transform = `scale(${SCALE})`; fr.style.height = 768 * SCALE + 'px'; }
window.addEventListener('resize', () => { fit(); render(); });
