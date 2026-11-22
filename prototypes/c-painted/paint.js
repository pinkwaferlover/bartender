/* Prototype C: the painting kit. Everything is painted in code on canvas: one hard light from the upper left,
   deep shadow everywhere else (tenebrism), then a brush-stroke texture and grain on top. */

const hex = h => h.match(/\w\w/g).map(x => parseInt(x, 16));
const rgb = (a, al = 1) => `rgba(${a[0] | 0},${a[1] | 0},${a[2] | 0},${al})`;
const mixc = (a, b, t) => { const A = hex(a), B = hex(b); return '#' + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, '0')).join(''); };
const darken = (c, t) => mixc(c, '#050304', t);
const lighten = (c, t) => mixc(c, '#fff4e2', t);
const rand = (s => () => (s = (s * 16807) % 2147483647) / 2147483647)(7);

/* One painterly texture, reused everywhere: short, mostly diagonal strokes of light and dark */
const TEX = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 512; const x = c.getContext('2d');
  for (let i = 0; i < 3400; i++) {
    const px = rand() * 512, py = rand() * 512, len = 3 + rand() * 12, a = rand() * Math.PI, light = rand() > .5;
    x.strokeStyle = light ? `rgba(255,240,220,${.04 + rand() * .07})` : `rgba(0,0,0,${.05 + rand() * .1})`;
    x.lineWidth = 1 + rand() * 3.5; x.lineCap = 'round';
    x.beginPath(); x.moveTo(px, py); x.quadraticCurveTo(px + Math.cos(a) * len * .5 + rand() * 3, py + Math.sin(a) * len * .5, px + Math.cos(a) * len, py + Math.sin(a) * len); x.stroke();
  }
  return c;
})();
function texture(ctx, w, h, alpha = .9, ox = 0, oy = 0) {
  ctx.save(); ctx.globalCompositeOperation = 'source-atop'; ctx.globalAlpha = alpha;
  const p = ctx.createPattern(TEX, 'repeat'); ctx.translate(ox, oy); ctx.fillStyle = p; ctx.fillRect(-ox, -oy, w, h); ctx.restore();
}
/* Fill a path lit from the upper left */
function lit(ctx, path, base, box, o = {}) {
  const [x0, y0, x1, y1] = box, g = ctx.createLinearGradient(x0, y0, x1, y1);
  g.addColorStop(0, lighten(base, o.hi ?? .35)); g.addColorStop(o.mid ?? .38, base); g.addColorStop(o.term ?? .62, darken(base, .55)); g.addColorStop(1, darken(base, .88));
  ctx.fillStyle = g; ctx.fill(path);
}
function glow(ctx, x, y, r, col, a) { const g = ctx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, rgb(hex(col), a)); g.addColorStop(1, rgb(hex(col), 0)); ctx.fillStyle = g; ctx.fillRect(x - r, y - r, r * 2, r * 2); }
const P2 = d => new Path2D(d);

/* ---------- The wall: one shaft of light from high on the left ---------- */
function paintWall(c) {
  const w = c.width, h = c.height, x = c.getContext('2d');
  x.fillStyle = '#0b0809'; x.fillRect(0, 0, w, h);
  const g = x.createRadialGradient(w * .4, h * .33, 10, w * .42, h * .38, w * .32);
  g.addColorStop(0, '#5a3e2a'); g.addColorStop(.35, '#2e1f16'); g.addColorStop(.75, '#130d0b'); g.addColorStop(1, '#0b0809');
  x.fillStyle = g; x.fillRect(0, 0, w, h);
  // the diagonal shaft
  x.save(); x.globalCompositeOperation = 'screen'; x.filter = 'blur(30px)';
  x.fillStyle = 'rgba(255,210,150,.10)'; x.beginPath(); x.moveTo(w * .2, 0); x.lineTo(w * .3, 0); x.lineTo(w * .52, h * .6); x.lineTo(w * .4, h * .6); x.fill(); x.restore();
  // plaster: blotches
  for (let i = 0; i < 90; i++) { const px = rand() * w, py = rand() * h; glow(x, px, py, 30 + rand() * 120, rand() > .5 ? '#3a2a1e' : '#000000', .12 + rand() * .1); }
  texture(x, w, h, .25);
  // a pilaster in shadow on the right
  x.fillStyle = 'rgba(0,0,0,.35)'; x.fillRect(w * .86, 0, w * .05, h);
  x.fillStyle = 'rgba(90,60,40,.12)'; x.fillRect(w * .855, 0, w * .006, h);
}

/* ---------- The shelf and its bottles ---------- */
const BSH = { // bottle silhouettes per Family (width units 0..1 of a 60 x 100 box), no logos
  whisky: 'M23 6 h14 v14 q0 4 6 7 q9 5 9 14 v51 q0 4 -4 4 h-36 q-4 0 -4 -4 v-51 q0 -9 9 -14 q6 -3 6 -7 Z',
  gin: 'M24 6 h12 v16 l8 8 v62 q0 4 -4 4 h-20 q-4 0 -4 -4 v-62 l8 -8 Z',
  rum: 'M25 6 h10 v22 q16 6 16 22 v42 q0 4 -4 4 h-34 q-4 0 -4 -4 v-42 q0 -16 16 -22 Z',
  tequila: 'M25 6 h10 v18 l12 10 v58 q0 4 -4 4 h-26 q-4 0 -4 -4 v-58 l12 -10 Z',
  vodka: 'M26 6 h8 v22 q8 4 8 12 v52 q0 4 -4 4 h-16 q-4 0 -4 -4 v-52 q0 -8 8 -12 Z',
  brandy: 'M25 6 h10 v24 q20 10 20 34 q0 32 -25 32 q-25 0 -25 -32 q0 -24 20 -34 Z',
  aperitif: 'M26 6 h8 v26 q12 6 12 20 v40 q0 4 -4 4 h-24 q-4 0 -4 -4 v-40 q0 -14 12 -20 Z',
  bitters: 'M27 20 h6 v24 q14 6 14 22 q0 30 -17 30 q-17 0 -17 -30 q0 -16 14 -22 Z',
  mixer: 'M24 18 h12 v10 q8 6 8 16 v48 q0 4 -4 4 h-20 q-4 0 -4 -4 v-48 q0 -10 8 -16 Z',
};
const BLABEL = { whisky: [12, 52, 36, 26], gin: [18, 44, 24, 40], rum: [16, 60, 28, 18], tequila: [15, 52, 30, 22], vodka: [18, 56, 24, 14], brandy: [14, 62, 32, 14], aperitif: [14, 56, 32, 18], bitters: [11, 44, 38, 44], mixer: [16, 50, 28, 12] };
function paintBottle(x, fam, col, X, Y, s, dusty, lightX) {
  const sh = BSH[fam] ? fam : 'vodka', p = P2(BSH[sh]);
  x.save(); x.translate(X, Y); x.scale(s, s);
  // cast shadow to the lower right, away from the light
  x.save(); x.transform(1, 0, -.6, .25, 0, 75); x.fillStyle = 'rgba(0,0,0,.55)'; x.filter = 'blur(4px)'; x.fill(p); x.restore();
  const near = 1 - Math.min(1, Math.abs(lightX) / 900); // bottles nearer the light catch more of it
  lit(x, p, mixc(col, '#2a1a10', .25 + .35 * (1 - near)), [0, 0, 60, 100], { hi: .2 + .35 * near, mid: .3, term: .58 });
  const L = BLABEL[sh]; if (L) { const g = x.createLinearGradient(L[0], 0, L[0] + L[2], 0); g.addColorStop(0, '#efe3c8'); g.addColorStop(.6, '#9c8a6c'); g.addColorStop(1, '#2e241a'); x.fillStyle = g; x.globalAlpha = .9; x.fillRect(...L); x.globalAlpha = 1; }
  // the glint: one hard highlight on the lit edge
  x.save(); x.clip(p); x.fillStyle = `rgba(255,244,226,${.35 + .45 * near})`; x.fillRect(sh === 'bitters' ? 18 : 14, 26, 3, 56); x.restore();
  x.fillStyle = '#120c0a'; x.fillRect(sh === 'bitters' ? 26 : 23, sh === 'bitters' ? 14 : 2, sh === 'bitters' ? 8 : 14, 8);
  if (dusty) { x.save(); x.clip(p); x.fillStyle = 'rgba(120,110,98,.55)'; x.fillRect(0, 0, 60, 100); x.restore(); }
  x.restore();
}
function paintShelf(c, bottles, filled, t = 1) {
  const w = c.width, h = c.height, x = c.getContext('2d'); x.clearRect(0, 0, w, h);
  // the plank, lit from the left
  const py = h - 40; const g = x.createLinearGradient(0, 0, w, 0); g.addColorStop(0, '#6a4a30'); g.addColorStop(.4, '#3a2619'); g.addColorStop(1, '#120b08');
  x.fillStyle = g; x.fillRect(0, py, w, 16); x.fillStyle = 'rgba(255,220,170,.25)'; x.fillRect(0, py, w * .6, 2);
  x.fillStyle = 'rgba(0,0,0,.6)'; x.fillRect(0, py + 16, w, 14);
  const n = bottles.length, span = w - 60, step = Math.min(56, span / Math.max(1, n));
  bottles.forEach((b, i) => {
    const s = b.family === 'bitters' ? .9 : b.family === 'mixer' ? 1.05 : 1.18, X = 30 + i * step + (step - 60 * s) / 2, Y = py - 100 * s;
    x.globalAlpha = clamp01(t * n - i); paintBottle(x, b.family, b.colour, X, Y, s, !filled, X - 120); x.globalAlpha = 1;
  });
  if (!filled) { // cobweb, top right
    x.strokeStyle = 'rgba(200,190,170,.22)'; x.lineWidth = 1;
    for (let i = 0; i < 6; i++) { x.beginPath(); x.moveTo(w - 4, py - 140); x.lineTo(w - 10 - i * 24, py); x.stroke(); }
    for (let r = 30; r < 140; r += 26) { x.beginPath(); x.arc(w - 4, py - 140, r, Math.PI * .5, Math.PI * .95); x.stroke(); }
  }
  texture(x, w, h, .5);
}
const clamp01 = v => Math.max(0, Math.min(1, v));

/* ---------- Counter: polished top in three-quarter, dark front ---------- */
function paintCounter(c) {
  const w = c.width, h = c.height, x = c.getContext('2d');
  const top = P2(`M0 40 L${w} 0 L${w} 46 L0 96 Z`); // receding to the right
  const g = x.createLinearGradient(0, 0, w, 0); g.addColorStop(0, '#7a5638'); g.addColorStop(.35, '#4a3020'); g.addColorStop(1, '#140c08');
  x.fillStyle = g; x.fill(top);
  x.strokeStyle = 'rgba(255,226,180,.55)'; x.lineWidth = 2; x.beginPath(); x.moveTo(0, 96); x.lineTo(w * .55, 41); x.stroke();
  const f = x.createLinearGradient(0, 0, w, h); f.addColorStop(0, '#3a2516'); f.addColorStop(.4, '#1e130c'); f.addColorStop(1, '#070405');
  x.fillStyle = f; x.beginPath(); x.moveTo(0, 96); x.lineTo(w, 46); x.lineTo(w, h); x.lineTo(0, h); x.fill();
  for (let i = 0; i < 9; i++) { const px = 60 + i * (w / 9); x.fillStyle = 'rgba(0,0,0,.35)'; x.fillRect(px, 140 - i * 5, 6, h); x.fillStyle = 'rgba(255,210,160,.05)'; x.fillRect(px - 3, 140 - i * 5, 2, h); }
  // brass rail catches the light near the source only
  x.strokeStyle = '#6c5232'; x.lineWidth = 6; x.beginPath(); x.moveTo(0, 230); x.lineTo(w, 180); x.stroke();
  x.strokeStyle = 'rgba(255,220,150,.6)'; x.lineWidth = 1.5; x.beginPath(); x.moveTo(0, 227); x.lineTo(w * .4, 207); x.stroke();
  texture(x, w, h, .8);
}

/* ---------- Menu: a leather book standing on the counter ---------- */
function paintMenuBook(c) {
  const x = c.getContext('2d'), w = c.width, h = c.height; x.clearRect(0, 0, w, h);
  const p = P2(`M20 ${h - 10} L34 20 Q36 10 46 10 L${w - 30} 14 Q${w - 20} 16 ${w - 22} 26 L${w - 16} ${h - 14} Z`);
  lit(x, p, '#3a5a2a', [0, 0, w, h], { hi: .3, term: .7 });
  x.strokeStyle = '#c99a44'; x.lineWidth = 2; x.stroke(P2(`M44 30 L${w - 36} 32 L${w - 30} ${h - 30} L36 ${h - 28} Z`));
  x.fillStyle = '#e8c67a'; x.font = '600 22px "Cormorant Garamond", Georgia, serif'; x.textAlign = 'center';
  x.save(); x.translate(w / 2 + 4, h / 2); x.rotate(.02); x.fillText('Bibenda', 0, -6); x.font = 'italic 14px "Cormorant Garamond", Georgia, serif'; x.fillText('the menu', 0, 16); x.restore();
  texture(x, w, h, .7);
}
/* ---------- The panther, lying on the far end of the bar ---------- */
function paintPanther(c, paw = 0) {
  const x = c.getContext('2d'), w = c.width, h = c.height; x.clearRect(0, 0, w, h);
  const body = P2('M60 170 C50 120 110 92 180 96 C250 98 300 120 304 170 Z');
  lit(x, body, '#2a2630', [40, 80, 300, 180], { hi: .18, term: .5 });
  const head = P2('M30 150 C20 112 50 92 80 96 C108 100 116 126 108 150 C100 168 40 170 30 150 Z M38 104 L34 82 L56 98 Z M92 98 L108 84 L106 108 Z');
  lit(x, head, '#2c2832', [20, 80, 120, 170], { hi: .22, term: .52 });
  glow(x, 54, 128, 9, '#b6f06a', .9); glow(x, 86, 128, 9, '#b6f06a', .9);
  x.fillStyle = '#d9ff9a'; x.beginPath(); x.ellipse(54, 128, 4.5, 3, 0, 0, 7); x.ellipse(86, 128, 4.5, 3, 0, 0, 7); x.fill();
  x.fillStyle = '#0a0a0d'; x.fillRect(53, 125, 2, 6); x.fillRect(85, 125, 2, 6);
  x.save(); x.translate(40 - paw * 34, 168 - paw * 26); x.rotate(-paw * .5);
  lit(x, P2('M-18 0 C-22 -16 -8 -26 8 -22 C20 -18 22 -4 18 2 Z'), '#2c2832', [-20, -26, 20, 4]); x.restore();
  x.strokeStyle = 'rgba(255,230,200,.25)'; x.lineWidth = 2; x.beginPath(); x.moveTo(120, 102); x.quadraticCurveTo(200, 92, 270, 118); x.stroke();
  texture(x, w, h, .6);
}
function paintAmphora(c) { // out-of-focus foreground jug, for depth
  const x = c.getContext('2d'), w = c.width, h = c.height;
  const p = P2(`M${w * .38} 10 h${w * .24} v${h * .12} q${w * .3} ${h * .1} ${w * .32} ${h * .38} q0 ${h * .4} ${-w * .44} ${h * .48} q${-w * .44} ${-h * .08} ${-w * .44} ${-h * .48} q0 ${-h * .28} ${w * .32} ${-h * .38} Z`);
  lit(x, p, '#6a3a22', [0, 0, w, h], { hi: .25, term: .5 });
}

/* ---------- Dionysus, painted ---------- */
const FIN = {
  painted: { skin: '#e2cdb2', hair: '#3a2416', lip: '#a4483e', cheek: .32, vein: .16 },
  white: { skin: '#ece7df', hair: '#cfc8bd', lip: '#cbbfb3', cheek: 0, vein: .38 },
  living: { skin: '#bf8358', hair: '#1d120b', lip: '#7c3a2c', cheek: .26, vein: 0 },
};
const VEIN = (() => { const c = document.createElement('canvas'); c.width = c.height = 256; const x = c.getContext('2d'); x.strokeStyle = 'rgba(80,76,72,.9)'; x.lineWidth = 1;
  for (let i = 0; i < 9; i++) { x.beginPath(); let px = rand() * 256, py = rand() * 256; x.moveTo(px, py); for (let k = 0; k < 6; k++) { px += (rand() - .3) * 50; py += (rand() - .5) * 40; x.lineTo(px, py); } x.stroke(); } return c; })();

const TORSO = 'M-112 4 L-104 -150 Q-100 -184 -60 -191 L-20 -198 H20 L60 -191 Q100 -184 104 -150 L112 4 Z';
const CHITON = 'M-109 4 L-101 -150 Q-97 -180 -60 -187 Q-30 -168 0 -166 Q30 -168 60 -187 Q97 -180 101 -150 L109 4 Z';
const HIMATION = 'M28 -197 Q92 -194 104 -150 L112 4 L-112 4 L-108 -36 Q-26 -66 28 -197 Z';
const FAWN = 'M-104 -150 Q-98 -188 -54 -193 L-34 -152 Q-16 -84 44 -24 L26 4 Q-62 -54 -104 -150 Z';
const FIGLEAF = 'M0 6 C-30 -6 -36 -26 -22 -30 C-30 -44 -12 -50 -4 -40 C-2 -56 14 -54 12 -40 C24 -50 38 -40 26 -28 C40 -24 30 -4 0 6 Z';

function Figure() {
  const torsoCv = document.createElement('canvas'); torsoCv.width = 300; torsoCv.height = 240; // pre-painted body, -150..150 x -230..10
  let look = null;
  function prepaint(L) {
    look = L; const f = FIN[L.finish], x = torsoCv.getContext('2d'); x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, 300, 240); x.translate(150, 230);
    const box = [-120, -210, 120, 10];
    lit(x, P2(TORSO), f.skin, box, { hi: .4, mid: .32, term: .66 });
    // musculature in paint: soft shadows under the pecs and down the centre
    x.save(); x.clip(P2(TORSO)); x.filter = 'blur(6px)'; x.strokeStyle = 'rgba(40,24,16,.45)'; x.lineWidth = 7;
    x.beginPath(); x.moveTo(-64, -136); x.quadraticCurveTo(-32, -116, -4, -134); x.moveTo(6, -134); x.quadraticCurveTo(34, -116, 64, -136); x.moveTo(2, -118); x.lineTo(4, -30); x.stroke(); x.filter = 'none';
    if (f.vein) { x.globalAlpha = f.vein; x.drawImage(VEIN, -128, -230); x.globalAlpha = 1; }
    x.restore();
    if (L.coverage === 'modest') { lit(x, P2(CHITON), '#2f5a2c', box, { hi: .3, term: .6 }); x.strokeStyle = '#a8843a'; x.lineWidth = 4; x.stroke(P2('M-60 -187 Q-30 -168 0 -166 Q30 -168 60 -187')); }
    if (L.coverage !== 'cheeky') {
      lit(x, P2(HIMATION), '#8e1f1a', [-110, -200, 110, 10], { hi: .35, term: .55 });
      x.save(); x.clip(P2(HIMATION)); x.filter = 'blur(3px)'; x.lineWidth = 6;
      [['M-80 -30 Q-10 -70 40 -170', .55], ['M-40 0 Q20 -60 70 -150', .5], ['M20 4 Q60 -60 90 -120', .45]].forEach(([d, a]) => { x.strokeStyle = `rgba(20,2,2,${a})`; x.stroke(P2(d)); });
      x.translate(-4, -4); x.strokeStyle = 'rgba(255,140,110,.25)'; x.lineWidth = 3; x.stroke(P2('M-80 -30 Q-10 -70 40 -170')); x.restore();
    } else {
      lit(x, P2(FIGLEAF), '#4f7d34', [-36, -56, 40, 6]);
    }
    lit(x, P2(FAWN), '#a8743f', [-104, -194, 44, 4], { hi: .35, term: .6 });
    x.save(); x.clip(P2(FAWN)); x.fillStyle = 'rgba(240,226,200,.85)';
    [[-70, -160, 5], [-52, -130, 4], [-36, -100, 5], [-14, -70, 4], [8, -44, 5], [-80, -130, 3.5]].forEach(([a, b, r]) => { x.beginPath(); x.arc(a, b, r, 0, 7); x.fill(); });
    x.restore();
    texture(x, 300, 240, .9, 150, 230);
  }
  function limb(x, S, E, H, f) {
    const pts = [S, E, H], wd = [17, 14, 12];
    for (let i = 0; i < 2; i++) {
      const [a, b] = [pts[i], pts[i + 1]], ang = Math.atan2(b[1] - a[1], b[0] - a[0]), nx = -Math.sin(ang), ny = Math.cos(ang);
      const p = new Path2D(); p.moveTo(a[0] + nx * wd[i], a[1] + ny * wd[i]); p.lineTo(b[0] + nx * wd[i + 1], b[1] + ny * wd[i + 1]);
      p.arc(b[0], b[1], wd[i + 1], ang + Math.PI / 2, ang - Math.PI / 2, true); p.lineTo(a[0] - nx * wd[i], a[1] - ny * wd[i]); p.arc(a[0], a[1], wd[i], ang - Math.PI / 2, ang + Math.PI / 2, true);
      // light falls on the side facing the upper left
      const side = (nx * -0.7 + ny * -0.7) > 0 ? 1 : -1;
      const g = x.createLinearGradient(a[0] + nx * wd[i] * side, a[1] + ny * wd[i] * side, a[0] - nx * wd[i] * side, a[1] - ny * wd[i] * side);
      g.addColorStop(0, lighten(f.skin, .3)); g.addColorStop(.45, f.skin); g.addColorStop(1, darken(f.skin, .75));
      x.fillStyle = g; x.fill(p);
    }
    const hg = x.createRadialGradient(H[0] - 5, H[1] - 6, 2, H[0], H[1], 16); hg.addColorStop(0, lighten(f.skin, .3)); hg.addColorStop(1, darken(f.skin, .6));
    x.fillStyle = hg; x.beginPath(); x.arc(H[0], H[1], 14, 0, 7); x.fill();
  }
  function head(x, turn, tilt, f, t) {
    x.save(); x.translate(0, -222); x.rotate(turn * .05); x.translate(0, 222);
    // hair mass behind
    x.fillStyle = darken(f.hair, .3); x.beginPath(); x.ellipse(0, -262, 48, 52, 0, 0, 7); x.fill();
    // neck
    lit(x, P2('M-17 -226 H17 V-186 H-17 Z'), darken(f.skin, .15), [-17, -226, 17, -186]);
    const face = new Path2D(); face.ellipse(turn * 4, -256, 37, 46, 0, 0, 7);
    const g = x.createRadialGradient(-22 + turn * 6, -280, 6, turn * 4 + 6, -250, 64);
    g.addColorStop(0, lighten(f.skin, .45)); g.addColorStop(.45, f.skin); g.addColorStop(.8, darken(f.skin, .6)); g.addColorStop(1, darken(f.skin, .9));
    x.fillStyle = g; x.fill(face);
    if (f.vein) { x.save(); x.clip(face); x.globalAlpha = f.vein; x.drawImage(VEIN, -70, -320); x.restore(); }
    const fx = turn * 9, fy = tilt;
    x.save(); x.clip(face);
    if (f.cheek) { glow(x, -18 + fx, -236 + fy, 14, '#d0705a', f.cheek); glow(x, 20 + fx, -236 + fy, 12, '#d0705a', f.cheek * .6); }
    // eye sockets in shadow, lids lowered over the glass
    glow(x, -15 + fx, -260 + fy, 13, '#2a1810', .35); glow(x, 15 + fx, -260 + fy, 13, '#2a1810', .45);
    x.strokeStyle = darken(f.hair, .2); x.lineWidth = 2.6; x.lineCap = 'round';
    x.beginPath(); x.moveTo(-25 + fx, -260 + fy); x.quadraticCurveTo(-15 + fx, -264 + fy, -6 + fx, -260 + fy); x.moveTo(6 + fx, -260 + fy); x.quadraticCurveTo(15 + fx, -264 + fy, 25 + fx, -260 + fy); x.stroke();
    x.lineWidth = 3; x.beginPath(); x.moveTo(-27 + fx, -271 + fy); x.quadraticCurveTo(-16 + fx, -277 + fy, -6 + fx, -272 + fy); x.moveTo(7 + fx, -272 + fy); x.quadraticCurveTo(17 + fx, -277 + fy, 27 + fx, -271 + fy); x.stroke();
    // nose: lit ridge, shadow cast to the right
    x.fillStyle = 'rgba(30,16,10,.45)'; x.beginPath(); x.moveTo(1 + fx, -258 + fy); x.lineTo(9 + fx, -240 + fy); x.lineTo(1 + fx, -238 + fy); x.fill();
    x.fillStyle = 'rgba(255,240,220,.35)'; x.fillRect(-2 + fx, -258 + fy, 2.4, 16);
    x.fillStyle = f.lip; x.beginPath(); x.moveTo(-11 + fx, -228 + fy); x.quadraticCurveTo(fx, -222 + fy, 11 + fx, -228 + fy); x.quadraticCurveTo(fx, -224 + fy, -11 + fx, -228 + fy); x.fill();
    x.restore();
    // curls, lit on top-left
    [[-34, -284], [-22, -298], [-6, -304], [10, -303], [25, -296], [36, -282], [-40, -268], [41, -266], [-30, -292], [30, -290], [0, -296], [-44, -250], [44, -248]].forEach(([cx, cy]) => {
      const cg = x.createRadialGradient(cx - 4 + turn * 3, cy - 5, 1, cx + turn * 3, cy, 14); cg.addColorStop(0, lighten(f.hair, .35)); cg.addColorStop(.5, f.hair); cg.addColorStop(1, darken(f.hair, .8));
      x.fillStyle = cg; x.beginPath(); x.arc(cx + turn * 3, cy, 12, 0, 7); x.fill();
    });
    // wreath of vine leaves and grapes
    for (let i = 0; i < 13; i++) {
      const a = Math.PI * (1.05 + i * .9 / 12), lx = Math.cos(a) * 46 + turn * 3, ly = -270 + Math.sin(a) * 36;
      x.save(); x.translate(lx, ly); x.rotate(a + Math.PI / 2); const lg = x.createLinearGradient(-12, -6, 12, 6); lg.addColorStop(0, '#7fb055'); lg.addColorStop(.5, '#2f5a26'); lg.addColorStop(1, '#0c1a08');
      x.fillStyle = lg; x.beginPath(); x.ellipse(0, 0, 13, 7, 0, 0, 7); x.fill(); x.restore();
    }
    [[-46, -246], [46, -246]].forEach(([gx, gy]) => [[0, 0], [-7, 7], [7, 7], [0, 14], [-4, 21], [4, 21]].forEach(([dx, dy]) => {
      const cx = gx + dx + turn * 3, cy = gy + dy, gg = x.createRadialGradient(cx - 2, cy - 2, .5, cx, cy, 6); gg.addColorStop(0, '#b77ac2'); gg.addColorStop(.5, '#4a1e58'); gg.addColorStop(1, '#12051a');
      x.fillStyle = gg; x.beginPath(); x.arc(cx, cy, 5.8, 0, 7); x.fill();
    }));
    x.restore();
  }
  return {
    setLook(L) { prepaint(L); },
    draw(x, st) {
      const f = FIN[look.finish];
      x.save();
      x.translate(0, -st.rise);
      // breathing: the whole chest lifts a little
      x.save(); x.translate(0, st.breath * 1.4); x.scale(1, 1 + st.breath * .007); x.drawImage(torsoCv, -150, -230); x.restore();
      head(x, st.turn, st.tilt, f, st.t);
      st.mint > 0 && [[-30, -318, -.5], [-10, -328, -.1], [14, -326, .25], [32, -314, .55]].forEach(([mx, my, r]) => {
        x.save(); x.translate(mx, my + 10); x.scale(st.mint, st.mint); x.rotate(r); const g = x.createLinearGradient(-6, -12, 6, 12); g.addColorStop(0, '#b6f08a'); g.addColorStop(1, '#2e6a22');
        x.fillStyle = g; x.beginPath(); x.ellipse(0, -10, 6, 13, 0, 0, 7); x.fill(); x.restore(); });
      limb(x, ...st.armL, f); limb(x, ...st.armR, f);
      x.restore();
    },
  };
}
