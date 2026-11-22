/* Prototype E: Rendered. Prototype B's layout, logic and zoom model, with the bar rendered in Blender.
   The camera is still the SVG viewBox, in B's world units. The background is one rendered picture per camera
   position; touchables and bottles are separate rendered layers; Dionysus is his own layer (dio-layer.js). */
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
    const inner = el('g', { class: 'btl' + (BAR.filled ? '' : ' dusty') }, outer);
    img(L, inner);
    el('title', {}, inner).textContent = `${b.style} (${FAMILIES[b.family] || b.family})`;
    if (animate && !RM) inner.style.animation = `drop .7s ${0.06 * i}s cubic-bezier(.3,1.4,.5,1) both`;
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
  if (RM || dur === 0) { vb = to; setVB(); return Promise.resolve(); }
  const t0 = performance.now();
  return new Promise(res => {
    camAnim = now => { const p = ease(clamp((now - t0) / dur, 0, 1)); vb = from.map((v, i) => lerp(v, to[i], p)); setVB(); if (p >= 1) { camAnim = null; res(); } };
  });
}
const setVB = () => svg.setAttribute('viewBox', vb.map(v => v.toFixed(2)).join(' '));
addEventListener('resize', () => { vb = shotRect(shotName); setVB(); placeBubble(); });
vb = shotRect('intro'); setVB(); showPatch('intro');

/* ---------------- Dionysus: his own layer ---------------- */
const dio = makeDio($('#dio'));

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
  bubble.hidden = false; sayEl.innerHTML = html; sayEl.className = opts.cls || '';
  chips.innerHTML = '';
  (opts.chips || []).forEach(c => {
    if (c.label === '|') { const d = document.createElement('span'); d.className = 'chipbreak'; d.textContent = c.text || ''; chips.appendChild(d); return; }
    const b = document.createElement('button'); b.type = 'button'; b.className = 'chip ' + (c.cls || ''); b.innerHTML = c.label; b.onclick = c.go; chips.appendChild(b);
  });
  talkForm.hidden = !opts.talk; dio.lookUp(true); $('#talkBtn').hidden = true;
  requestAnimationFrame(placeBubble);
  if (opts.talk && !isPhone()) setTimeout(() => $('#talkIn').focus({ preventScroll: true }), 50);
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
function home() {
  screen = 'home'; clearScene(); $('#back').hidden = true; $('#talkBtn').hidden = false;
  hush(); return cam('home');
}
$('#back').onclick = () => home();
addEventListener('keydown', e => { if (e.key === 'Escape' && screen !== 'home' && screen !== 'intro') home(); });
function setScreen(name) { screen = name; $('#back').hidden = false; $('#talkBtn').hidden = true; clearScene(); }
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
  if (!BAR.filled) askWhatYouHave();
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
  $('#pcancel').onclick = home;
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
  $('#pex').onclick = () => { $('#pasteIn').value = JSON.stringify({ bottles: INVENTORY.have.map(k => ({ label: ING[k][0], style: k })), barware: ['shaker', 'strainer', 'jigger', 'spoon'] }); };
  $('#pcancel').onclick = home;
  $('#pread').onclick = () => {
    const res = readPasted($('#pasteIn').value);
    if (!res.found.length) { $('#pasteNote').textContent = "I couldn't find any bottles in that. Paste the AI's whole reply."; return; }
    confirmFound(res, res.unknown);
  };
}
function confirmFound(res, unknown = []) {
  const byKind = {}; res.found.forEach(k => { const f = isBottle(k) ? (FAMILIES[ING[k][3]] || { bitters: 'Bitters', mixer: 'Mixers' }[ING[k][3]] || 'Other') : 'In the kitchen'; (byKind[f] = byKind[f] || []).push(ING[k][0]); });
  panel.innerHTML = `<h2>Here's what he found</h2><ul class="found">${Object.entries(byKind).map(([f, l]) => `<li><b>${f}</b>${l.join(', ')}</li>`).join('')}</ul>
   ${unknown.length ? `<p class="pasteNote">Not on his list yet: ${unknown.map(u => String(u).replace(/[<>&]/g, '')).join(', ')}</p>` : ''}
   <p style="margin:0;font-weight:700">Barware: tick what you have</p>
   <div class="ticks">${Object.entries(BARWARE).map(([k, v]) => `<label><input type="checkbox" value="${k}" ${res.tools.includes(k) ? 'checked' : ''}> ${v}</label>`).join('')}</div>
   <div class="row"><button class="btn ghost" id="pcancel">Not now</button><button class="btn" id="pstock">Stock the shelf</button></div>`;
  $('#pcancel').onclick = home;
  $('#pstock').onclick = async () => {
    const tools = [...panel.querySelectorAll('.ticks input:checked')].map(i => i.value);
    applyReading(res, tools); panel.hidden = true; drawShelf(true);
    await wait(RM ? 0 : 1400); home();
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
    p.style.left = (r.left + r.width / 2) + 'px'; p.style.top = Math.max(60, r.top - 34) + 'px'; box.appendChild(p);
  });
  document.querySelectorAll('.touch').forEach(t => t.classList.add('hinting'));
  setTimeout(() => { box.innerHTML = ''; document.querySelectorAll('.touch').forEach(t => t.classList.remove('hinting')); }, 6000);
}
function openShelf() {
  if (!BAR.filled) return openPhotos();
  hush(); setScreen('shelf'); cam('shelf');
  const fam = {}; shelfBottles().forEach(b => (fam[FAMILIES[b.family] || 'Bitters and mixers'] = fam[FAMILIES[b.family] || 'Bitters and mixers'] || []).push(b.style));
  panel.className = 'panel sheet shelfsheet'; panel.hidden = false;
  panel.innerHTML = `<h2>Your shelf</h2><ul class="found">${Object.entries(fam).map(([f, l]) => `<li><b>${f}</b>${l.join(', ')}</li>`).join('')}</ul>
   <p style="margin:0 0 10px;font-size:14px">Barware: ${[...BAR.barware].map(b => BARWARE[b]).join(', ') || 'none yet'}</p>
   <div class="row"><button class="btn ghost" id="pmore">Add more</button><button class="btn" id="pdone">Back to the bar</button></div>`;
  $('#pmore').onclick = openPhotos; $('#pdone').onclick = home;
}
$('#shelf').addEventListener('click', e => { e.stopPropagation(); if (screen === 'home') openShelf(); });

/* 4. The menu: zoom in, by spirit, by feel, A–Z. R9: every drink, the ones you can't make marked "needs X" */
const mini = r => glassSide(r, 34);
function drinkBtn(r) {
  const need = missingFor(r);
  return `<button class="drink${need.length ? ' need' : ''}" data-id="${r.id}">${mini(r)}<span>${r.name}<small>${need.length ? 'needs ' + need.map(x => ING[x.k][0]).join(', ') : FEELS[feelOf(r)]}</small></span></button>`;
}
function menuBody(tab) {
  if (tab === 'spirit') return Object.entries(FAMILIES).map(([k, v]) => { const l = R.filter(r => r.spirit === k); return l.length ? `<h3>${v}</h3>${l.map(drinkBtn).join('')}` : ''; }).join('');
  if (tab === 'feel') return Object.entries(FEELS).map(([k, v]) => `<h3>${v}</h3>${R.filter(r => feelOf(r) === k).map(drinkBtn).join('')}`).join('');
  return `<div class="letters">${[...R].sort((a, b) => a.name.localeCompare(b.name)).map(drinkBtn).join('')}</div>`;
}
async function openMenu(tab = 'spirit') {
  hush(); setScreen('menu');
  await cam('menu', 850);
  panel.className = 'panel menucard'; panel.hidden = false; svg.classList.add('dim');
  const n = R.filter(canMake).length;
  panel.innerHTML = `<h2>MENU</h2><p class="menunote">${R.length} drinks · ${n} you can make now</p><div class="tabs" role="tablist">${[['spirit', 'By spirit'], ['feel', 'By feel'], ['az', 'A–Z']].map(([k, v]) => `<button class="tab" role="tab" data-t="${k}" aria-selected="${k === tab}">${v}</button>`).join('')}</div><div class="list">${menuBody(tab)}</div>`;
  panel.querySelectorAll('.tab').forEach(b => b.onclick = () => { panel.querySelectorAll('.tab').forEach(x => x.setAttribute('aria-selected', x === b)); panel.querySelector('.list').innerHTML = menuBody(b.dataset.t); wireDrinks(); });
  wireDrinks();
}
function wireDrinks() { panel.querySelectorAll('.drink').forEach(b => b.onclick = () => openRecipe(b.dataset.id)); }
$('#menu').addEventListener('click', e => { e.stopPropagation(); if (screen === 'home') openMenu(); });

/* 5. Talking to Dionysus: tap Talk, tap a spirit, tap a drink (three taps) */
let conv = null;
const resChip = r => ({ label: `${glassSide(r, 22)} ${r.name}${canMake(r) ? '' : ' <small>needs ' + missingFor(r).map(x => ING[x.k][0]).join(', ') + '</small>'}`, cls: 'res', go: () => openRecipe(r.id) });
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
  speak(`<span class="who">${r.name} · ${s.by}, ${s.at}, ${s.when} · ${s.kind === 'legend' ? 'a legend' : 'on record'}</span><br>${s.tell}`, {
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
function openRecipe(id, chosen) {
  const r = RB[id]; hush(); setScreen('recipe');
  document.body.classList.add('recipe-on'); cam('recipe', 900);
  golden = Math.random() < .15;
  const s = STORY[id], miss = missingFor(r), swaps = swapsFor(r);
  const worth = chosen && chosen.worth;
  panel.className = 'panel recipe'; panel.hidden = false;
  panel.innerHTML = `${chosen ? `<p class="kicker">🎲 Barman’s choice${worth ? ` · <b>worth buying a bottle for</b>` : ''}</p>` : ''}<h2>${r.name}</h2>
   <p class="meta">${FEELS[feelOf(r)]} · ${STRENGTHS[strengthOf(r)]} strength · ${r.glass} glass${s ? ` · ${s.by}, ${s.when}` : ''}</p>
   ${worth ? `<p class="worth">Needs ${ING[worth.bottle][0]}. One bottle, and ${worth.opens > 1 ? `${worth.opens} drinks open up` : 'this one is yours'}.</p>` : ''}
   ${golden ? '<p class="golden">A golden rim. The god’s own touch: it happens one time in seven.</p>' : ''}
   <ul class="ing">${r.ing.map(x => { const m = miss.includes(x); return `<li class="${m ? 'miss' : ''}"><span>${ING[x.k][0]}${x.o ? ' (optional)' : ''}${m ? ' · you’re out' : ''}</span><span>${fmtQty(x)}</span></li>`; }).join('')}</ul>
   ${swaps.length ? `<div class="swap"><b>No ${swaps.map(s => s.tool.toLowerCase()).join(', ')}?</b> ${swaps.map(s => `Use ${s.use}`).join('. ')}.</div>` : ''}
   <div class="stepbox" id="stepbox" aria-live="polite"><p class="stepno" id="stepno"></p><p class="step" id="stepText"></p><p class="act" id="stepAct"></p></div>
   <div class="row steprow"><button class="btn ghost" id="prevS">Back a step</button><button class="btn" id="nextS">Done, next</button></div>`;
  $('#prevS').onclick = () => goStep(recipeState.i - 1);
  $('#nextS').onclick = () => recipeState.i < r.steps.length - 1 ? goStep(recipeState.i + 1) : finishRecipe();
  $('#stepbox').onclick = () => $('#nextS').click();
  recipeState = { r, i: 0, chosen };
  drinkGlass(r, 0, false); goStep(0);
}
function goStep(i) {
  const s = recipeState; if (!s || i < 0) return;
  const r = s.r, n = r.steps.length, st = r.steps[i], action = actionFor(st, r);
  s.i = i;
  $('#stepno').textContent = `Step ${i + 1} of ${n}`;
  $('#stepText').textContent = st[2];
  $('#stepAct').textContent = ACTION_LABEL[action];
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
  dio.perform(action, { r, fruit: ING[fk][2], honeyAt: HONEY_AT, bottle }).then(done => {
    if (!done || !recipeState || recipeState.i !== i) return;
    drinkGlass(r, pour ? (i + 1) / n : 0, i === n - 1);
    $('#stepbox').classList.add('waiting');
    $('#stepAct').textContent = i === n - 1 ? 'Ready. Your turn: tap when you’ve done it.' : 'Your turn. Tap when you’ve done it.';
  });
}
function finishRecipe() {
  const r = recipeState.r; drinkGlass(r, 1, true); dio.idle();
  $('#stepbox').innerHTML = `<p class="step">There it is. ${golden ? 'Golden rim and all. ' : ''}Enjoy your ${r.name}.</p>`;
  $('#stepbox').onclick = null;
  const row = panel.querySelector('.steprow');
  row.innerHTML = `<button class="btn ghost" id="again">Another, please</button><button class="btn" id="rdone">Back to the bar</button>`;
  $('#again').onclick = () => { const p = barmansChoice(r.id); p ? openRecipe(p.r.id, p) : home(); };
  $('#rdone').onclick = home;
}

/* 2. Look settings: finish and coverage */
function applyLook() { document.body.classList.remove(...[...document.body.classList].filter(c => /^(fin|cov)-/.test(c))); document.body.classList.add(`fin-${LOOK.finish}`, `cov-${LOOK.coverage}`); dio.setLook(LOOK); }
const settings = $('#settings');
function renderSettings() {
  settings.innerHTML = `<h3>His look</h3>
   <fieldset><legend>Finish</legend><div class="seg">${Object.entries(FINISHES).map(([k, v]) => `<label><input type="radio" name="fin" value="${k}" ${LOOK.finish === k ? 'checked' : ''}>${v}</label>`).join('')}</div></fieldset>
   <fieldset><legend>Coverage</legend><div class="seg">${Object.entries(COVERAGES).map(([k, v]) => `<label><input type="radio" name="cov" value="${k}" ${LOOK.coverage === k ? 'checked' : ''} ${k === 'cheeky' && !LOOK.adult ? 'disabled' : ''}>${k === 'cheeky' ? 'Cheeky<span class="badge">ADULT</span>' : v}</label>`).join('')}</div></fieldset>
   <label class="adult"><input type="checkbox" id="adult" ${LOOK.adult ? 'checked' : ''}> <span>Allow adult looks. Cheeky stays implied: a fig leaf, and something always passes in front.</span></label>
   <p class="note">Only the painted-marble finish is rendered so far; the other finishes and coverages apply to the drawn fallback figure.</p>`;
  settings.querySelectorAll('input[name=fin]').forEach(i => i.onchange = () => { LOOK.finish = i.value; applyLook(); });
  settings.querySelectorAll('input[name=cov]').forEach(i => i.onchange = () => { LOOK.coverage = i.value; applyLook(); });
  $('#adult').onchange = e => { LOOK.adult = e.target.checked; if (!LOOK.adult && LOOK.coverage === 'cheeky') LOOK.coverage = 'classical'; applyLook(); renderSettings(); };
}
$('#gear').onclick = () => { settings.hidden = !settings.hidden; if (!settings.hidden) renderSettings(); };
document.addEventListener('click', e => { if (!settings.hidden && !settings.contains(e.target) && !$('#gear').contains(e.target)) settings.hidden = true; });
applyLook();

/* hooks for the screenshot script */
window.proto = { home, openMenu, startTalk, render: s => render(s), conv: () => conv, openRecipe, goStep, tellStory, openPhotos, openPaste, openShelf, honeyTalk, barmansChoiceGo, showHints,
  state: () => ({ screen, shot: shotName, step: recipeState && recipeState.i }),
  setLook: (f, c, a) => { LOOK.finish = f; if (a !== undefined) LOOK.adult = a; if (c) LOOK.coverage = c; applyLook(); renderSettings(); settings.hidden = false; },
  fill: () => { applyReading(readPhotos(PHOTOS.map(p => p.id)), ['shaker', 'strainer', 'jigger', 'spoon']); drawShelf(); } };
intro();
