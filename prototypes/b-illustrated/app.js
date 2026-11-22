/* Prototype B: Illustrated. A flat, front-on, symmetrical poster drawn in SVG.
   The camera is the SVG viewBox. Dionysus is a flat figure whose arms are solved each frame (two-bone IK),
   so one set of drawings can perform every action. */
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

/* ---------------- Build the muted world ---------------- */
(function build() {
  const rays = $('#rays');
  for (let i = 0; i < 18; i++) {
    const a0 = Math.PI + i * Math.PI / 18, a1 = a0 + Math.PI / 36, r = 900;
    el('path', { d: `M800 760 L${800 + r * Math.cos(a0)} ${760 + r * Math.sin(a0)} L${800 + r * Math.cos(a1)} ${760 + r * Math.sin(a1)} Z`, fill: '#1d1612' }, rays);
  }
  el('circle', { cx: 800, cy: 760, r: 300, fill: '#1a1411' }, rays);
  el('circle', { cx: 800, cy: 760, r: 220, fill: '#1e1713' }, rays);
  const panels = $('#panels');
  for (let x = 180; x < 1420; x += 155) el('rect', { x: x + 8, y: 740, width: 139, height: 170, rx: 6 }, panels);
  const curls = $('#curls');
  [[-34, -284], [-22, -298], [-6, -304], [10, -303], [25, -296], [36, -282], [-40, -268], [41, -266], [-30, -292], [30, -290], [0, -296]]
    .forEach(([x, y]) => el('circle', { cx: x, cy: y, r: 13 }, curls));
  const wr = $('#wreath');
  for (let i = 0; i < 13; i++) {
    const a = Math.PI * (1.05 + i * 0.9 / 12), x = Math.cos(a) * 44, y = -270 + Math.sin(a) * 36;
    el('ellipse', { cx: x, cy: y, rx: 12, ry: 6.5, fill: i % 2 ? '#3f7a34' : '#2f6428', transform: `rotate(${a * 180 / Math.PI + 90} ${x} ${y})` }, wr);
  }
  [[-44, -246], [44, -246]].forEach(([x, y]) => [[0, 0], [-7, 7], [7, 7], [0, 14], [-4, 21], [4, 21]].forEach(([dx, dy]) =>
    el('circle', { cx: x + dx, cy: y + dy, r: 5.6, fill: '#5b2a6b' }, wr)));
  const ms = $('#mintsprout');
  [[-30, -312, -30], [-10, -322, -8], [14, -320, 14], [32, -308, 32]].forEach(([x, y, r]) =>
    el('ellipse', { cx: x, cy: y, rx: 6, ry: 12, fill: '#6fcf5a', transform: `rotate(${r} ${x} ${y})` }, ms));
  ms.setAttribute('transform', 'scale(0)');
})();

/* ---------------- Bottles: generic shape per Style, true colour, no logos ---------------- */
const SHAPES = { ...BOT, mixer: 'M24 18 h12 v10 q8 6 8 16 v48 q0 4 -4 4 h-20 q-4 0 -4 -4 v-48 q0 -10 8 -16 Z' };
const LABEL = { // label layout per Family, never wording
  whisky: '<rect x="12" y="52" width="36" height="26" rx="2" fill="#f1e6cf"/><rect x="16" y="58" width="28" height="3" fill="#6b4c33"/>',
  gin: '<rect x="18" y="44" width="24" height="40" rx="2" fill="#f4f1e8"/><circle cx="30" cy="58" r="7" fill="#2f5a7a"/>',
  rum: '<ellipse cx="30" cy="68" rx="15" ry="11" fill="#e8d7a8"/>',
  tequila: '<rect x="15" y="52" width="30" height="22" fill="#1f4a3a"/>',
  vodka: '<rect x="18" y="56" width="24" height="14" fill="#fff"/>',
  brandy: '<path d="M14 62 h32 l-4 14 h-24 Z" fill="#1c1410"/>',
  aperitif: '<rect x="14" y="56" width="32" height="18" fill="#f3ead6"/><rect x="14" y="60" width="32" height="3" fill="#c2141c"/>',
  bitters: '<rect x="11" y="44" width="38" height="44" rx="2" fill="#f4eedd"/>',
  mixer: '<rect x="16" y="50" width="28" height="12" fill="#2f5a7a"/>',
};
function drawShelf(animate) {
  const g = $('#bottles'); g.innerHTML = '';
  const list = shelfBottles(); const n = list.length;
  const gap = 96, left = 480, right = 1120, avail = right - left - gap;
  const step = Math.min(46, avail / Math.max(n, 1));
  const half = Math.ceil(n / 2);
  list.forEach((b, i) => {
    const side = i < half ? 0 : 1, j = side ? i - half : i;
    const span = side ? (n - half) : half;
    const x = side ? 800 + gap / 2 + j * step + 2 : 800 - gap / 2 - (span - j) * step + 2;
    const sh = SHAPES[b.family] ? b.family : 'vodka';
    const s = b.family === 'bitters' ? .78 : b.family === 'mixer' ? .9 : 1.04;
    const outer = el('g', { transform: `translate(${x} ${384 - 100 * s}) scale(${s})` }, g);
    const inner = el('g', { class: 'btl' + (BAR.filled ? '' : ' dusty') }, outer);
    inner.innerHTML = `<path d="${SHAPES[sh]}" fill="${b.colour}"/>${LABEL[sh] || ''}<rect x="${sh === 'bitters' ? 26 : 23}" y="${sh === 'bitters' ? 14 : sh === 'mixer' ? 12 : 2}" width="${sh === 'bitters' ? 8 : 14}" height="8" rx="2" fill="#1c1410"/>` +
      (BAR.filled ? '' : `<path d="${SHAPES[sh]}" fill="#6e655c" opacity=".55"/>`);
    el('title', {}, inner).textContent = `${b.style} (${FAMILIES[b.family] || b.family})`;
    if (animate && !RM) { inner.style.animation = `drop .7s ${0.06 * i}s cubic-bezier(.3,1.4,.5,1) both`; }
  });
  $('#cobweb').style.display = BAR.filled ? 'none' : '';
}
const st = document.createElement('style');
st.textContent = '@keyframes drop{from{transform:translateY(-360px)}to{transform:none}}';
document.head.appendChild(st);
drawShelf();

/* ---------------- Camera: the viewBox ---------------- */
const SHOTS = {
  intro: { L: [440, 40, 720, 200], P: [452, 40, 696, 200] },
  home: { L: [160, 20, 1280, 800], P: [440, -60, 720, 1250] },
  menu: { L: [540, 548, 140, 128], P: [548, 552, 124, 120] },
  shelf: { L: [440, 230, 720, 210], P: [450, 220, 700, 300] },
  talk: { L: [470, 300, 800, 430], P: [600, 300, 400, 420] },
  recipe: { L: [300, 330, 760, 380], P: [580, 272, 440, 952] },
  choice: { L: [700, 520, 520, 220], P: [760, 450, 420, 300] },
};
let vb = [440, 40, 720, 200], camAnim = null, shotName = 'intro';
function fit([x, y, w, h]) {
  const A = innerWidth / innerHeight, cx = x + w / 2, cy = y + h / 2;
  if (w / h > A) h = w / A; else w = h * A;
  return [cx - w / 2, cy - h / 2, w, h];
}
function shotRect(name) { const s = SHOTS[name]; return fit(innerWidth < innerHeight && s.P ? s.P : s.L); }
function cam(name, dur = 900) {
  shotName = name; const to = shotRect(name), from = vb.slice();
  if (RM || dur === 0) { vb = to; setVB(); return Promise.resolve(); }
  const t0 = performance.now();
  return new Promise(res => {
    camAnim = now => { const p = ease(clamp((now - t0) / dur, 0, 1)); vb = from.map((v, i) => lerp(v, to[i], p)); setVB(); if (p >= 1) { camAnim = null; res(); } };
  });
}
const setVB = () => svg.setAttribute('viewBox', vb.map(v => v.toFixed(2)).join(' '));
addEventListener('resize', () => { vb = shotRect(shotName); setVB(); placeBubble(); });
vb = shotRect('intro'); setVB();

/* ---------------- Dionysus: pose, IK, props ---------------- */
const SH = { L: [-96, -166], R: [96, -166] }, L1 = 82, L2 = 78;
const hand = { L: [-36, -80], R: [0, -100] };
function ik(S, T, bend) {
  const dx = T[0] - S[0], dy = T[1] - S[1]; let d = Math.hypot(dx, dy);
  d = clamp(d, Math.abs(L1 - L2) + 2, L1 + L2 - 1);
  const a = Math.atan2(dy, dx), b = Math.acos(clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1));
  const E = [S[0] + L1 * Math.cos(a + bend * b), S[1] + L1 * Math.sin(a + bend * b)];
  const H = [S[0] + d * Math.cos(a), S[1] + d * Math.sin(a)];
  return { E, H };
}
const props = $('#props');
props.innerHTML = `
 <g id="pGlass"><path d="M-14 -22 L-11 10 Q-10 14 -6 14 H6 Q10 14 11 10 L14 -22 Z" fill="rgba(240,231,216,.28)" stroke="#f0e7d8" stroke-width="2.4"/><path d="M-8 -14 L-7 6" stroke="#fff" stroke-width="2" opacity=".7"/></g>
 <g id="pCloth"><path d="M-16 -8 Q-4 -22 14 -10 Q22 6 6 16 Q-12 18 -16 -8 Z" fill="#b98552"/><circle cx="2" cy="-2" r="3" fill="#efe2c8"/><circle cx="-8" cy="6" r="2.4" fill="#efe2c8"/></g>
 <path id="pVine" fill="none" stroke="#3f7a34" stroke-width="6" stroke-linecap="round"/>
 <g id="pVineLeaves"></g>
 <g id="pBottle"><path fill="#b8661c"/></g>
 <rect id="pStream" width="5" rx="2.5" fill="#d9a441"/>
 <g id="pThyrsus"><line id="pStaff" stroke="#7a5530" stroke-width="7" stroke-linecap="round"/><g id="pCone"><ellipse rx="13" ry="22" fill="#5b7a2e"/><path d="M-11 -6 h22 M-12 6 h24 M-10 16 h20" stroke="#3f5a1f" stroke-width="3"/></g></g>
 <g id="pLemon"><ellipse id="pLemonBody" rx="14" ry="11"/><path d="M0 -11 q4 -8 12 -8" stroke="#3f7a34" stroke-width="3" fill="none"/></g>
 <g id="pDrops"></g>
 <ellipse id="pHoney" fill="#e0a224"/>
 <g id="pShaker"><path d="M-20 -30 H20 L16 26 Q15 32 8 32 H-8 Q-15 32 -16 26 Z" fill="#c9a24a"/><path d="M-26 -18 q-14 0 -14 14 q0 12 14 12 M26 -18 q14 0 14 14 q0 12 -14 12" fill="none" stroke="#c9a24a" stroke-width="5"/><rect x="-22" y="-38" width="44" height="10" rx="4" fill="#a88838"/></g>
 <g id="pMint"><ellipse rx="6" ry="12" fill="#6fcf5a" transform="rotate(-20)"/><ellipse cx="8" rx="6" ry="12" fill="#5fbf4a" transform="rotate(25)"/></g>
 <g id="pIce"></g>
 <g id="pSteam" fill="none" stroke="#f0e7d8" stroke-width="3" stroke-linecap="round" opacity=".6"><path d="M-10 -80 q-8 -14 0 -26 q8 -12 0 -26"/><path d="M10 -86 q-8 -14 0 -26 q8 -12 0 -26"/></g>
 <g id="pSpark" fill="#ffd2df"><path d="M0 -12 L3 -3 L12 0 L3 3 L0 12 L-3 3 L-12 0 L-3 -3 Z"/></g>`;
const P = id => document.getElementById(id);
for (let i = 0; i < 3; i++) el('rect', { width: 12, height: 12, rx: 3, fill: '#eef6f8', opacity: .8 }, P('pIce'));
for (let i = 0; i < 4; i++) el('circle', { r: 3.4, fill: '#f2cf2e' }, P('pDrops'));
const show = (id, on) => { P(id).style.display = on ? '' : 'none'; };
const place = (id, x, y, rot = 0, s = 1) => P(id).setAttribute('transform', `translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${rot.toFixed(1)}) scale(${s})`);
const ALLPROPS = ['pGlass', 'pCloth', 'pVine', 'pVineLeaves', 'pBottle', 'pStream', 'pThyrsus', 'pLemon', 'pDrops', 'pHoney', 'pShaker', 'pMint', 'pIce', 'pSteam', 'pSpark'];

let mode = 'polish';      // 'polish' | 'recipe'
let act = { name: 'rest', p: 0, r: null, fruit: '#f2cf2e' };
let lookUp = 0, rise = 0, riseT = 0;

/* Returns hand targets and draws props for the current action at phase p (0..1) */
function pose(t) {
  const out = { L: [-60, -40], R: [60, -40], vis: {} };
  const V = out.vis;
  if (mode === 'polish') {
    const G = [-20, -96], w = t * 4.2;
    out.L = [G[0] - 6, G[1] + 18]; out.R = [G[0] + 14 + 13 * Math.cos(w), G[1] - 4 + 11 * Math.sin(w)];
    V.pGlass = [G[0], G[1], 0]; V.pCloth = [out.R[0] + 4, out.R[1], Math.sin(w) * 20];
    return out;
  }
  const { name, p } = act, glassTop = [0, -66];
  switch (name) {
    case 'vine': {
      const grow = seg(p, 0, .4);
      const path = `M210 -300 C260 -230 150 -210 120 -190 S70 -160 64 -150`;
      P('pVine').setAttribute('d', path); P('pVine').style.strokeDasharray = 420; P('pVine').style.strokeDashoffset = 420 * (1 - grow);
      V.pVine = 1;
      const bp = seg(p, .1, .45), bx = lerp(210, 64, ease(bp)), by = lerp(-300, -150, ease(bp));
      const reach = seg(p, .4, .55), pour = seg(p, .55, .75);
      out.R = reach < 1 ? [lerp(60, 64, reach), lerp(-40, -140, reach)] : [lerp(64, 36, pour), lerp(-140, -124, pour)];
      const tilt = -105 * pour;
      V.pBottle = reach < 1 ? [bx, by - 40, 0, .7] : [out.R[0], out.R[1] - 36, tilt, .7];
      if (pour > .6 && p < .97) { V.pStream = [6, -100, 0, 1, 40]; }
      out.L = [-34, -60];
      break;
    }
    case 'thyrsus': {
      const w = t * 7, tip = [0 + 6 * Math.cos(w), -34 + 2 * Math.sin(w)];
      out.R = [tip[0] + 26, tip[1] - 92]; out.L = [-34, -40];
      V.pThyrsus = { tip, hand: out.R };
      break;
    }
    case 'lemon': {
      const grow = seg(p, 0, .35), ripe = seg(p, .2, .55), pick = seg(p, .55, .7), sq = seg(p, .75, 1);
      P('pVine').setAttribute('d', 'M-220 -6 C-230 -80 -150 -110 -170 -150 S-130 -190 -112 -182');
      P('pVine').style.strokeDasharray = 300; P('pVine').style.strokeDashoffset = 300 * (1 - seg(p, 0, .25));
      V.pVine = 1;
      const unripe = act.fruit === '#86c03a' ? '#4d7a26' : '#86a83a';
      P('pLemonBody').setAttribute('fill', ripe < 1 ? mix(unripe, act.fruit, ripe) : act.fruit);
      const lemonAt = pick < 1 ? [lerp(-112, -112, pick), -170] : [lerp(-112, -14, sq * 2 > 1 ? 1 : sq * 2), lerp(-170, -110, Math.min(1, sq * 2))];
      out.L = pick > 0 ? [lemonAt[0] - 4, lemonAt[1] + 8] : [-60, -40];
      V.pLemon = [lemonAt[0], lemonAt[1], 0, (.25 + .75 * grow) * (sq > .6 ? lerp(1, .7, (sq - .6) / .4) : 1)];
      if (sq > .5) V.pDrops = [lemonAt[0] + 4, lemonAt[1] + 14, (t * 60) % 40];
      break;
    }
    case 'mint': {
      const sprout = seg(p, 0, .35), reach = seg(p, .35, .55), bring = seg(p, .6, .85);
      $('#mintsprout').setAttribute('transform', `translate(0 ${-300 * (1 - sprout) * 0}) scale(${sprout})`);
      $('#mintsprout').style.transformOrigin = '0 -300px';
      out.R = reach < 1 ? [lerp(60, 34, reach), lerp(-40, -300, reach)] : [lerp(34, 14, bring), lerp(-300, -92, bring)];
      if (reach >= 1) V.pMint = [out.R[0], out.R[1] - 14, 0];
      break;
    }
    case 'honey': {
      const well = seg(p, 0, .4), dip = seg(p, .4, .6), drip = seg(p, .6, 1);
      V.pHoney = [-70, -6, 30 * well, 16 * well];
      const tip = dip < 1 ? [lerp(10, -70, dip), lerp(-110, -12, dip)] : [lerp(-70, 4, drip), lerp(-12, -100, drip)];
      out.R = [tip[0] + 30, tip[1] - 90]; out.L = [-30, -40];
      V.pThyrsus = { tip, hand: out.R };
      if (drip > .4) V.pStream = [tip[0] - 2, tip[1] + 8, 0, 1, Math.max(0, -66 - tip[1] - 8 + 60), '#e0a224'];
      break;
    }
    case 'shake': {
      const k = Math.sin(t * 16) * 16, c = [70, -214 + k];
      out.R = [c[0] + 12, c[1] + 18]; out.L = [c[0] - 18, c[1] - 22];
      V.pShaker = [c[0], c[1], 25 + k * .6, .9];
      break;
    }
    case 'strain': {
      const a = seg(p, 0, .3);
      out.R = [lerp(60, 44, a), lerp(-40, -150, a)]; out.L = [-30, -40];
      V.pShaker = [out.R[0] - 6, out.R[1] - 10, -100 * a, .8];
      if (a >= 1 && p < .95) V.pStream = [10, -112, 0, 1, 46, act.r.colour];
      break;
    }
    case 'ice': {
      out.L = [-14, -150]; out.R = [60, -40];
      V.pIce = p;
      break;
    }
    case 'heat': V.pSteam = 1; out.L = [-40, -50]; out.R = [40, -50]; break;
    default: V.pSpark = [24, -76, t * 90, .6 + .4 * Math.sin(t * 8)]; out.L = [-40, -50]; out.R = [40, -50];
  }
  return out;
}
function mix(a, b, t) { const pa = a.match(/\w\w/g).map(h => parseInt(h, 16)), pb = b.match(/\w\w/g).map(h => parseInt(h, 16)); return '#' + pa.map((v, i) => Math.round(lerp(v, pb[i], t)).toString(16).padStart(2, '0')).join(''); }

function drawDio(t) {
  const o = pose(t);
  const k = RM ? 1 : .3;
  ['L', 'R'].forEach(s => { hand[s][0] = lerp(hand[s][0], o[s][0], k); hand[s][1] = lerp(hand[s][1], o[s][1], k); });
  ['L', 'R'].forEach(s => {
    const { E, H } = ik(SH[s], hand[s], s === 'L' ? 1 : -1);
    const d = `M${SH[s][0]} ${SH[s][1]} L${E[0].toFixed(1)} ${E[1].toFixed(1)} L${H[0].toFixed(1)} ${H[1].toFixed(1)}`;
    P('arm' + s).setAttribute('d', d); P('arm' + s + 'v').setAttribute('d', d);
    P('hand' + s).setAttribute('cx', H[0].toFixed(1)); P('hand' + s).setAttribute('cy', H[1].toFixed(1));
  });
  ALLPROPS.forEach(id => show(id, o.vis[id] !== undefined));
  const V = o.vis;
  if (V.pGlass) place('pGlass', ...V.pGlass);
  if (V.pCloth) place('pCloth', ...V.pCloth);
  if (V.pBottle) place('pBottle', V.pBottle[0], V.pBottle[1], V.pBottle[2], V.pBottle[3]);
  if (V.pStream) { const s = P('pStream'); s.setAttribute('x', V.pStream[0] - 2.5); s.setAttribute('y', V.pStream[1]); s.setAttribute('height', Math.max(0, V.pStream[4])); s.setAttribute('fill', V.pStream[5] || (act.r && act.r.colour) || '#d9a441'); s.removeAttribute('transform'); }
  if (V.pThyrsus) {
    const { tip, hand: h } = V.pThyrsus, dx = h[0] - tip[0], dy = h[1] - tip[1], L = Math.hypot(dx, dy), ux = dx / L, uy = dy / L;
    const top = [h[0] + ux * 150, h[1] + uy * 150];
    const s = P('pStaff'); s.setAttribute('x1', tip[0]); s.setAttribute('y1', tip[1]); s.setAttribute('x2', top[0]); s.setAttribute('y2', top[1]);
    P('pCone').setAttribute('transform', `translate(${top[0]} ${top[1]}) rotate(${Math.atan2(uy, ux) * 180 / Math.PI + 90})`);
  }
  if (V.pLemon) place('pLemon', ...V.pLemon);
  if (V.pDrops) [...P('pDrops').children].forEach((c, i) => { c.setAttribute('cx', V.pDrops[0] + (i - 1.5) * 4); c.setAttribute('cy', V.pDrops[1] + ((V.pDrops[2] + i * 11) % 44)); c.setAttribute('fill', act.fruit); });
  if (V.pHoney) { const h = P('pHoney'); h.setAttribute('cx', V.pHoney[0]); h.setAttribute('cy', V.pHoney[1]); h.setAttribute('rx', V.pHoney[2]); h.setAttribute('ry', V.pHoney[3]); }
  if (V.pShaker) place('pShaker', ...V.pShaker);
  if (V.pMint) place('pMint', ...V.pMint);
  if (V.pIce !== undefined) [...P('pIce').children].forEach((c, i) => { const q = seg(V.pIce, i * .22, i * .22 + .3); c.setAttribute('x', -18 + i * 9); c.setAttribute('y', lerp(-150, -30 - i * 6, q)); c.setAttribute('opacity', q > 0 ? .85 : 0); });
  if (V.pSpark) place('pSpark', ...V.pSpark);
  if (act.name !== 'mint' || mode !== 'recipe') $('#mintsprout').setAttribute('transform', 'scale(0)');
  // breathing, head turn, the cheeky reach
  const br = RM ? 0 : Math.sin(t * 1.6);
  $('#torso').setAttribute('transform', `translate(0 ${br * 1.2}) scale(1 ${1 + br * .006})`);
  const turn = RM ? 0 : (mode === 'polish' ? Math.sin(t * .37) * .6 + Math.sin(t * .11) * .4 : -.3);
  const tilt = lookUp ? -4 : (mode === 'polish' ? 6 : 2);
  $('#head').setAttribute('transform', `rotate(${(turn * 4).toFixed(2)} 0 -220)`);
  $('#face').setAttribute('transform', `translate(${(turn * 7).toFixed(2)} ${tilt})`);
  $('#body').setAttribute('transform', `translate(0 ${(-rise).toFixed(1)})`);
}

/* the cheeky "glimpse": every so often he reaches up; a passing vine of grapes swings across the counter */
const passing = $('#passing');
passing.innerHTML = `<g id="grapes"><path d="M0 -200 C10 -120 -10 -60 0 0" stroke="#3f7a34" stroke-width="5" fill="none"/>${[[0, 0], [-10, 10], [10, 10], [-16, 22], [0, 22], [16, 22], [-8, 34], [8, 34], [0, 46]].map(([x, y]) => `<circle cx="${x}" cy="${y}" r="10" fill="#5b2a6b"/>`).join('')}<ellipse cx="-14" cy="-10" rx="16" ry="9" fill="#3f7a34" transform="rotate(-30 -14 -10)"/></g>`;
const grapes = $('#grapes'); grapes.style.display = 'none';
function cheekyTick(t, dt) {
  if (LOOK.coverage !== 'cheeky' || mode !== 'polish' || RM) { rise = lerp(rise, 0, .2); grapes.style.display = 'none'; return; }
  riseT += dt; const cyc = riseT % 9;
  const up = cyc > 6 ? Math.sin(Math.PI * (cyc - 6) / 3) : 0; rise = 30 * up;
  grapes.style.display = up > 0 ? '' : 'none';
  if (up > 0) grapes.setAttribute('transform', `translate(${lerp(700, 900, (cyc - 6) / 3)} 620) rotate(${Math.sin(t * 3) * 8})`);
}

/* ---------------- Main loop ---------------- */
let last = performance.now(), T = 0;
function frame(now) {
  const dt = Math.min(.05, (now - last) / 1000); last = now; T += RM ? 0 : dt;
  if (camAnim) camAnim(now);
  if (mode === 'recipe' && recipeState) recipeTick(dt);
  cheekyTick(T, dt);
  drawDio(T);
  if (!RM) $('#ptail').setAttribute('transform', `rotate(${Math.sin(T * 1.3) * 6} 1150 652)`);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

/* ---------------- The drink on the counter (recipe) ---------------- */
function drinkGlass(r, prog, garnish) {
  const G = GL[r.glass], s = .58;
  $('#liqrect').setAttribute('y', 120 - 120 * prog); $('#liqrect').setAttribute('height', 120 * prog);
  $('#liqrect').setAttribute('x', 0); $('#liqrect').setAttribute('width', 100);
  $('#drink').innerHTML = `<g transform="translate(${-50 * s} ${-120 * s}) scale(${s})"><path d="${G.g}" fill="rgba(240,231,216,.22)" stroke="#f0e7d8" stroke-width="2.4"/>
    <path d="${G.l}" fill="${r.colour}" clip-path="url(#liqclip)"/>${r.ice && G.ice && prog > .2 ? G.ice : ''}${garnish ? garnSide(r.garnish, G) : ''}</g>`;
}

/* ---------------- UI: bubble ---------------- */
const bubble = $('#bubble'), sayEl = $('#say'), chips = $('#chips'), talkForm = $('#talk');
function placeBubble() {
  if (bubble.hidden || isPhone()) { bubble.style.left = ''; bubble.style.top = ''; return; }
  const r = $('#head').getBoundingClientRect(), bw = bubble.offsetWidth, bh = bubble.offsetHeight;
  let x = r.right + 28, y = r.top - 10;
  if (x + bw > innerWidth - 16) x = Math.max(16, r.left - bw - 28);
  y = clamp(y, 70, innerHeight - bh - 16);
  bubble.style.left = x + 'px'; bubble.style.top = y + 'px';
}
function speak(html, opts = {}) {
  bubble.hidden = false; sayEl.innerHTML = html; sayEl.className = opts.cls || '';
  chips.innerHTML = '';
  (opts.chips || []).forEach(c => { const b = document.createElement('button'); b.type = 'button'; b.className = 'chip ' + (c.cls || ''); b.innerHTML = c.label; b.onclick = c.go; chips.appendChild(b); });
  talkForm.hidden = !opts.talk; lookUp = 1; $('#talkBtn').hidden = true;
  requestAnimationFrame(placeBubble);
  if (opts.talk && !isPhone()) setTimeout(() => $('#talkIn').focus({ preventScroll: true }), 50);
}
function hush() { bubble.hidden = true; lookUp = 0; if (screen === 'home') $('#talkBtn').hidden = false; }
$('#bubbleX').onclick = () => { hush(); if (shotName !== 'home') home(); };

/* ---------------- Screens ---------------- */
let screen = 'intro';
const panel = $('#panel');
function home() {
  screen = 'home'; panel.hidden = true; panel.className = 'panel'; svg.classList.remove('blur', 'dim');
  mode = 'polish'; recipeState = null; $('#drink').innerHTML = ''; $('#back').hidden = true; $('#talkBtn').hidden = false;
  $('#thyrsusRest').style.display = '';
  hush(); return cam('home');
}
$('#back').onclick = () => home();
addEventListener('keydown', e => { if (e.key === 'Escape' && screen !== 'home' && screen !== 'intro') home(); });
function setScreen(name) { screen = name; $('#back').hidden = false; $('#talkBtn').hidden = true; panel.hidden = true; svg.classList.remove('blur', 'dim'); mode = 'polish'; recipeState = null; $('#drink').innerHTML = ''; $('#thyrsusRest').style.display = ''; }

/* 1. Opening: the big word becomes the neon sign */
async function intro() {
  $('#talkBtn').hidden = true;
  await wait(RM ? 0 : 700);
  svg.classList.add('lit', 'flick');
  await wait(RM ? 0 : 1300);
  await cam('home', 2200);
  if (screen !== 'intro') return;
  screen = 'home'; $('#talkBtn').hidden = false;
  await wait(RM ? 0 : 500);
  if (!BAR.filled) askWhatYouHave();
}
const wait = ms => new Promise(r => setTimeout(r, ms));

/* 3. "What do you have?" */
function askWhatYouHave() {
  speak('What do you have? My shelf is looking thin.', { chips: [
    { label: 'Show him some photos', cls: 'go', go: openPhotos },
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
   <div class="row"><button class="btn ghost" id="pcancel">Not now</button><button class="btn" id="pread">Read these photos</button></div>`;
  panel.querySelectorAll('.photo').forEach(b => b.onclick = () => { const id = b.dataset.id; picked.has(id) ? picked.delete(id) : picked.add(id); b.setAttribute('aria-pressed', picked.has(id)); });
  $('#pcancel').onclick = home;
  $('#pread').onclick = async () => {
    if (!picked.size) return;
    panel.innerHTML = `<h2>Show him your bar</h2><div class="reading"><i></i> Dionysus is reading your photos…</div>`;
    await wait(RM ? 300 : 1800);
    const res = readPhotos([...picked]);
    const byKind = {}; res.found.forEach(k => { const f = isBottle(k) ? (FAMILIES[ING[k][3]] || { bitters: 'Bitters', mixer: 'Mixers' }[ING[k][3]] || 'Other') : 'In the kitchen'; (byKind[f] = byKind[f] || []).push(ING[k][0]); });
    panel.innerHTML = `<h2>Here's what he found</h2><ul class="found">${Object.entries(byKind).map(([f, l]) => `<li><b>${f}</b>${l.join(', ')}</li>`).join('')}</ul>
     <p style="margin:0;font-weight:700">Barware: tick what you have</p>
     <div class="ticks">${Object.entries(BARWARE).map(([k, v]) => `<label><input type="checkbox" value="${k}" ${res.tools.includes(k) ? 'checked' : ''}> ${v}</label>`).join('')}</div>
     <div class="row"><button class="btn ghost" id="pcancel">Not now</button><button class="btn" id="pstock">Stock the shelf</button></div>`;
    $('#pcancel').onclick = home;
    $('#pstock').onclick = async () => {
      const tools = [...panel.querySelectorAll('.ticks input:checked')].map(i => i.value);
      applyReading(res, tools); panel.hidden = true; drawShelf(true);
      await wait(RM ? 0 : 1400); home();
      setTimeout(() => speak(`That's more like it. ${R.filter(canMake).length} drinks I can make you now. Tap the menu, or talk to me.`, { chips: [{ label: 'OK', cls: 'go', go: hush }] }), RM ? 0 : 950);
    };
  };
}
function openShelf() {
  if (!BAR.filled) return openPhotos();
  hush(); setScreen('shelf'); cam('shelf');
  const fam = {}; shelfBottles().forEach(b => (fam[FAMILIES[b.family] || 'Bitters and mixers'] = fam[FAMILIES[b.family] || 'Bitters and mixers'] || []).push(b.style));
  panel.className = 'panel sheet'; panel.hidden = false;
  panel.innerHTML = `<h2>Your shelf</h2><ul class="found">${Object.entries(fam).map(([f, l]) => `<li><b>${f}</b>${l.join(', ')}</li>`).join('')}</ul>
   <p style="margin:0 0 10px;font-size:14px">Barware: ${[...BAR.barware].map(b => BARWARE[b]).join(', ') || 'none yet'}</p>
   <div class="row"><button class="btn ghost" id="pmore">Add more photos</button><button class="btn" id="pdone">Back to the bar</button></div>`;
  $('#pmore').onclick = openPhotos; $('#pdone').onclick = home;
}
$('#shelf').addEventListener('click', e => { e.stopPropagation(); if (screen === 'home') openShelf(); });

/* 4. The menu: zoom in, by spirit, by feel, A–Z */
const mini = r => glassSide(r, 34);
function drinkBtn(r) {
  const need = missingFor(r);
  return `<button class="drink${need.length ? ' need' : ''}" data-id="${r.id}">${mini(r)}<span>${r.name}<small>${need.length ? 'Needs ' + need.map(x => ING[x.k][0]).join(', ') : FEELS[feelOf(r)]}</small></span></button>`;
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
  panel.innerHTML = `<h2>MENU</h2><div class="tabs" role="tablist">${[['spirit', 'By spirit'], ['feel', 'By feel'], ['az', 'A–Z']].map(([k, v]) => `<button class="tab" role="tab" data-t="${k}" aria-selected="${k === tab}">${v}</button>`).join('')}</div><div class="list">${menuBody(tab)}</div>`;
  panel.querySelectorAll('.tab').forEach(b => b.onclick = () => { panel.querySelectorAll('.tab').forEach(x => x.setAttribute('aria-selected', x === b)); panel.querySelector('.list').innerHTML = menuBody(b.dataset.t); wireDrinks(); });
  wireDrinks();
}
function wireDrinks() { panel.querySelectorAll('.drink').forEach(b => b.onclick = () => openRecipe(b.dataset.id)); }
$('#menu').addEventListener('click', e => { e.stopPropagation(); if (screen === 'home') openMenu(); });

/* 5. Talking to Dionysus */
let conv = null;
async function startTalk() {
  setScreen('talk'); hush(); cam('talk', 800);
  conv = Conversation(); render(conv.start());
}
function render(s) {
  if (s.open) return openRecipe(s.open);
  const ch = [];
  if (s.results) {
    s.results.forEach(r => ch.push({ label: `${glassSide(r, 22)} ${r.name}`, cls: 'res', go: () => openRecipe(r.id) }));
    ch.push({ label: 'Start again', cls: 'skip', go: () => render((conv = Conversation()).start()) });
  } else {
    (s.opts || []).forEach(([k, v]) => ch.push({ label: v, go: () => render(conv.answer(s.q, k)) }));
    if (s.q !== 'open') ch.push({ label: 'Skip', cls: 'skip', go: () => render(conv.answer(s.q, '-')) });
  }
  const n = s.count ? ` <small style="color:#7a5a40">(${s.count} fit so far)</small>` : '';
  speak(s.say + n, { chips: ch, talk: true });
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

/* 6. Tap him for a story */
function tellStory(exceptId) {
  setScreen('story'); cam('talk', 800);
  const pool = R.filter(r => STORY[r.id] && (canMake(r) || !BAR.filled) && r.id !== exceptId);
  const r = pool[Math.floor(Math.random() * pool.length)], s = STORY[r.id];
  speak(`<span class="who">${r.name} · ${s.by}, ${s.at}, ${s.when} · ${s.kind === 'legend' ? 'a legend' : 'on record'}</span><br>${s.tell}`, {
    cls: 'story', chips: [{ label: 'Make me one', cls: 'go', go: () => openRecipe(r.id) }, { label: 'Another story', go: () => tellStory(r.id) }] });
}
$('#dio').addEventListener('click', e => { e.stopPropagation(); if (screen === 'home' || screen === 'story' || screen === 'talk') tellStory(); });

/* 6b. Barman's choice: the panther bats the dice off the counter */
let rolling = false;
const dice = $('#dice'); const DICE0 = [940, 651]; dice.setAttribute('transform', `translate(${DICE0[0]} ${DICE0[1]})`);
async function barmansChoiceGo() {
  if (rolling) return; rolling = true; screen = 'choice'; $('#talkBtn').hidden = true; hush();
  const r = barmansChoice();
  if (!RM) {
    await cam('choice', 500);
    const paw = $('#ppaw'), head = $('#phead'), t0 = performance.now();
    await new Promise(res => {
      (function f(now) {
        const p = (now - t0) / 1300;
        const swipe = Math.sin(clamp(p / .3, 0, 1) * Math.PI);
        paw.setAttribute('transform', `translate(${-22 * swipe} ${-14 * swipe})`); head.setAttribute('transform', `rotate(${-8 * swipe} 1000 640)`);
        const q = seg(p, .18, 1), x = DICE0[0] - 260 * q, y = DICE0[1] - 70 * Math.sin(Math.PI * Math.min(q * 1.4, 1)) + (q > .7 ? 260 * (q - .7) : 0);
        dice.setAttribute('transform', `translate(${x} ${y}) rotate(${-720 * q})`);
        if (p < 1) requestAnimationFrame(f); else res();
      })(t0);
    });
  }
  dice.setAttribute('transform', `translate(${DICE0[0]} ${DICE0[1]})`); rolling = false;
  openRecipe(r.id, true);
}
$('#panther').addEventListener('click', e => { e.stopPropagation(); if (screen === 'home') barmansChoiceGo(); });

/* 7. The recipe in front, Dionysus making it behind */
let recipeState = null;
function openRecipe(id, chosen) {
  const r = RB[id]; hush(); setScreen('recipe');
  svg.classList.add('blur'); cam('recipe', 900);
  mode = 'recipe'; $('#thyrsusRest').style.display = 'none';
  const s = STORY[id], miss = missingFor(r), swaps = swapsFor(r);
  panel.className = 'panel recipe'; panel.hidden = false;
  panel.innerHTML = `${chosen ? '<p class="meta" style="margin:0 0 2px">🎲 Barman’s choice</p>' : ''}<h2>${r.name}</h2>
   <p class="meta">${FEELS[feelOf(r)]} · ${STRENGTHS[strengthOf(r)]} strength · ${r.glass} glass${s ? ` · ${s.by}, ${s.when}` : ''}</p>
   <ul>${r.ing.map(x => { const m = miss.includes(x); return `<li class="${m ? 'miss' : ''}"><span>${ING[x.k][0]}${x.o ? ' (optional)' : ''}${m ? ' · you’re out' : ''}</span><span>${fmtQty(x)}</span></li>`; }).join('')}</ul>
   ${swaps.length ? `<div class="swap"><b>No ${swaps.map(s => s.tool.toLowerCase()).join(', ')}?</b> ${swaps.map(s => `Use ${s.use}`).join('. ')}.</div>` : ''}
   <ol id="steps">${r.steps.map((st, i) => `<li data-i="${i}">${st[2]}<em>${ACTION_LABEL[actionFor(st, r)]}</em></li>`).join('')}</ol>
   ${s ? `<p class="tellme">“${s.tell.split('. ').slice(0, 2).join('. ')}.”</p>` : ''}
   <div class="row"><button class="btn ghost" id="again">Another, please</button><button class="btn" id="rdone">Back to the bar</button></div>`;
  $('#again').onclick = () => openRecipe(barmansChoice(id).id, true); $('#rdone').onclick = home;
  panel.querySelectorAll('#steps li').forEach(li => li.onclick = () => { recipeState.i = +li.dataset.i; recipeState.t = 0; });
  recipeState = { r, i: 0, t: 0, done: 0 };
  drinkGlass(r, 0, false); setAct();
}
const STEP_S = 3.6;
function setAct() {
  const { r, i } = recipeState, st = r.steps[i], name = actionFor(st, r);
  const fk = ['lime', 'grapefruit', 'lemon'].find(f => st[2].toLowerCase().includes(f)) || 'lemon';
  act = { name, p: 0, r, fruit: ING[fk][2] };
  const main = r.ing.find(x => ['spirit', 'liqueur', 'wine'].includes(ING[x.k][1])) || r.ing[0];
  const fam = SHAPES[ING[main.k][3]] ? ING[main.k][3] : 'vodka';
  P('pBottle').innerHTML = `<g transform="translate(-30 -50)"><path d="${SHAPES[fam]}" fill="${ING[main.k][2]}"/>${LABEL[fam] || ''}</g>`;
  document.querySelectorAll('#steps li').forEach((li, j) => li.classList.toggle('now', j === i));
}
function recipeTick(dt) {
  const s = recipeState; if (RM) { act.p = .8; drinkGlass(s.r, (s.i + 1) / s.r.steps.length, s.i === s.r.steps.length - 1); return; }
  s.t += dt; act.p = clamp(s.t / STEP_S, 0, 1);
  const n = s.r.steps.length, prog = clamp((s.i + act.p) / n, 0, 1);
  drinkGlass(s.r, ['pour', 'top', 'strain', 'float'].includes(s.r.steps[s.i][0]) || s.i > 0 ? prog : 0, s.i === n - 1 && act.p > .5);
  if (s.t > STEP_S) { s.t = 0; s.i = (s.i + 1) % n; if (s.i === 0) s.t = -2; setAct(); }
}

/* 2. Look settings: finish and coverage */
function applyLook() {
  document.body.className = `fin-${LOOK.finish} cov-${LOOK.coverage}`;
}
const settings = $('#settings');
function renderSettings() {
  settings.innerHTML = `<h3>His look</h3>
   <fieldset><legend>Finish</legend><div class="seg">${Object.entries(FINISHES).map(([k, v]) => `<label><input type="radio" name="fin" value="${k}" ${LOOK.finish === k ? 'checked' : ''}>${v}</label>`).join('')}</div></fieldset>
   <fieldset><legend>Coverage</legend><div class="seg">${Object.entries(COVERAGES).map(([k, v]) => `<label><input type="radio" name="cov" value="${k}" ${LOOK.coverage === k ? 'checked' : ''} ${k === 'cheeky' && !LOOK.adult ? 'disabled' : ''}>${k === 'cheeky' ? 'Cheeky<span class="badge">ADULT</span>' : v}</label>`).join('')}</div></fieldset>
   <label class="adult"><input type="checkbox" id="adult" ${LOOK.adult ? 'checked' : ''}> <span>Allow adult looks. Cheeky stays implied: a fig leaf, and something always passes in front.</span></label>`;
  settings.querySelectorAll('input[name=fin]').forEach(i => i.onchange = () => { LOOK.finish = i.value; applyLook(); });
  settings.querySelectorAll('input[name=cov]').forEach(i => i.onchange = () => { LOOK.coverage = i.value; riseT = 0; applyLook(); });
  $('#adult').onchange = e => { LOOK.adult = e.target.checked; if (!LOOK.adult && LOOK.coverage === 'cheeky') LOOK.coverage = 'classical'; applyLook(); renderSettings(); };
}
$('#gear').onclick = () => { settings.hidden = !settings.hidden; if (!settings.hidden) renderSettings(); };
document.addEventListener('click', e => { if (!settings.hidden && !settings.contains(e.target) && !$('#gear').contains(e.target)) settings.hidden = true; });
applyLook();

/* hooks for the screenshot script */
window.proto = { home, openMenu, startTalk, render: s => render(s), conv: () => conv, openRecipe, tellStory, openPhotos, barmansChoiceGo, setLook: (f, c, a) => { riseT = 0; LOOK.finish = f; if (a !== undefined) LOOK.adult = a; if (c) LOOK.coverage = c; applyLook(); renderSettings(); settings.hidden = false; }, fill: () => { applyReading(readPhotos(PHOTOS.map(p => p.id)), ['shaker', 'strainer', 'jigger', 'spoon']); drawShelf(); } };
intro();
