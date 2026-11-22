/* Prototype C: Painted. A Caravaggio-like scene: one hard light, deep shadow, painted in code on canvas layers
   that sit at different depths in CSS 3D. The camera dollies through them (translateZ + rotateY), so the layers part
   with real parallax. Dionysus is a painted still that breathes, polishes, turns his head, and works slowly. */
const $ = s => document.querySelector(s);
const lerp = (a, b, t) => a + (b - a) * t;
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
const seg = (p, a, b) => clamp((p - a) / (b - a), 0, 1);
const wait = ms => new Promise(r => setTimeout(r, ms));
const isPhone = () => innerWidth <= 640;
const portrait = () => innerWidth < innerHeight;
const RM = reduceMotion();

/* ---------------- Layers in depth ---------------- */
const PERS = 1000, HOME_F = [800, 470];
const LAYERS = {
  wall: { x: -700, y: -600, w: 3000, h: 2400, z: -900, res: .5 },
  sign: { x: 800, y: 34, w: 440, h: 130, z: -760 },
  shelf: { x: 300, y: 200, w: 840, h: 230, z: -720 },
  dio: { x: 400, y: -44, w: 640, h: 700, z: -430 },
  passing: { x: 560, y: 360, w: 320, h: 320, z: -300 },
  counter: { x: -300, y: 580, w: 2200, h: 820, z: -200 },
  menu: { x: 370, y: 462, w: 150, h: 190, z: -230 },
  panther: { x: 980, y: 436, w: 320, h: 190, z: -300 },
  dice: { x: 948, y: 600, w: 26, h: 26, z: -262 },
  amph: { x: -80, y: 560, w: 260, h: 420, z: 260 },
};
const passingCv = document.createElement('canvas'); passingCv.id = 'passing'; passingCv.className = 'layer'; $('#dio').after(passingCv);
const baseT = {};
for (const [id, L] of Object.entries(LAYERS)) {
  const e = document.getElementById(id), k = (PERS - L.z) / PERS;
  Object.assign(e.style, { left: L.x + 'px', top: L.y + 'px', width: L.w + 'px', height: L.h + 'px', transformOrigin: `${HOME_F[0] - L.x}px ${HOME_F[1] - L.y}px` });
  baseT[id] = `translateZ(${L.z}px) scale(${k})`; e.style.transform = baseT[id];
  if (e.tagName === 'CANVAS') { e.width = Math.round(L.w * (L.res || 1)); e.height = Math.round(L.h * (L.res || 1)); }
}
paintWall($('#wall')); paintCounter($('#counter')); paintMenuBook($('#menu')); paintPanther($('#panther')); paintAmphora($('#amph'));
(function grain() { const c = document.createElement('canvas'); c.width = c.height = 160; const x = c.getContext('2d'), d = x.createImageData(160, 160);
  for (let i = 0; i < d.data.length; i += 4) { const v = Math.random() * 255; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; } x.putImageData(d, 0, 0);
  $('#grain').style.backgroundImage = `url(${c.toDataURL()})`; })();
(function passingArt() { const x = passingCv.getContext('2d'); x.strokeStyle = '#1e3a14'; x.lineWidth = 7; x.beginPath(); x.moveTo(160, 0); x.bezierCurveTo(180, 90, 140, 150, 160, 200); x.stroke();
  for (const [dx, dy] of [[0, 0], [-16, 14], [16, 14], [-26, 32], [0, 32], [26, 32], [-14, 50], [14, 50], [0, 68], [-8, 84], [8, 84]]) { const g = x.createRadialGradient(160 + dx - 4, 200 + dy - 5, 1, 160 + dx, 200 + dy, 15); g.addColorStop(0, '#9a5aa8'); g.addColorStop(.5, '#3a1446'); g.addColorStop(1, '#0a0410'); x.fillStyle = g; x.beginPath(); x.arc(160 + dx, 200 + dy, 14, 0, 7); x.fill(); }
  const lg = x.createLinearGradient(100, 160, 160, 210); lg.addColorStop(0, '#5a8a3a'); lg.addColorStop(1, '#0c1a08'); x.fillStyle = lg; x.beginPath(); x.ellipse(132, 190, 34, 18, -.5, 0, 7); x.fill();
  passingCv.style.filter = 'blur(3px)'; passingCv.style.display = 'none'; })();

/* ---------------- The shelf ---------------- */
let shelfT = 1;
function drawShelf(animate) {
  const c = $('#shelf');
  if (!animate || RM) { paintShelf(c, shelfBottles(), BAR.filled, 1); return; }
  const t0 = performance.now();
  (function f(now) { const t = clamp((now - t0) / 2200, 0, 1); paintShelf(c, shelfBottles(), true, t); if (t < 1) requestAnimationFrame(f); })(t0);
}
drawShelf();

/* ---------------- Camera: a dolly through the layers ---------------- */
const SHOTS = {
  intro: { L: [1020, 100, 600, -4, 0], P: [1020, 100, 300, -4, 0] },
  home: { L: [800, 450, 0, -10, 2], P: [850, 560, 0, -3, 2] },
  menu: { L: [445, 560, 760, -2, 0], P: [445, 560, 700, -2, 0] },
  shelf: { L: [720, 330, 400, -6, 0], P: [720, 330, 300, -4, 0] },
  talk: { L: [900, 440, 330, -16, 2], P: [740, 560, 200, -8, 2] },
  recipe: { L: [930, 430, 220, -16, 2], P: [740, 1040, 140, -4, 2] },
  choice: { L: [990, 560, 480, -4, 0], P: [960, 560, 420, -4, 0] },
};
let shot = 'intro', par = [0, 0];
function fitScale() { return portrait() ? innerWidth / 980 : Math.min(innerWidth / 1280, innerHeight / 800); }
function applyCam() {
  const s = SHOTS[shot], [fx, fy, dz, ry, rx] = (portrait() && s.P) || s.L;
  $('#fit').style.transform = `scale(${fitScale()})`;
  $('#cam').style.transform = `translateZ(${dz}px) rotateX(${rx + par[1]}deg) rotateY(${ry + par[0]}deg) translate3d(${-fx}px,${-fy}px,0)`;
}
function cam(name, slow) {
  shot = name; const c = $('#cam'); c.classList.toggle('slow', !!slow); applyCam();
  return wait(RM ? 0 : slow ? 2600 : 1500);
}
addEventListener('resize', () => { applyCam(); placeBubble(); });
if (!RM) addEventListener('pointermove', e => { if (e.pointerType !== 'mouse') return; par = [(e.clientX / innerWidth - .5) * 3, -(e.clientY / innerHeight - .5) * 2]; applyCam(); });
$('#cam').style.transition = 'none'; applyCam(); $('#cam').offsetHeight; $('#cam').style.transition = '';

/* ---------------- Dionysus ---------------- */
const fig = Figure(); fig.setLook(LOOK);
const dc = $('#dio'), dx = dc.getContext('2d');
const SH = { L: [-96, -166], R: [96, -166] }, L1 = 82, L2 = 78;
const hand = { L: [-36, -80], R: [0, -100] };
function ik(S, T, bend) {
  const ddx = T[0] - S[0], ddy = T[1] - S[1]; let d = Math.hypot(ddx, ddy);
  d = clamp(d, Math.abs(L1 - L2) + 2, L1 + L2 - 1);
  const a = Math.atan2(ddy, ddx), b = Math.acos(clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1));
  return [S, [S[0] + L1 * Math.cos(a + bend * b), S[1] + L1 * Math.sin(a + bend * b)], [S[0] + d * Math.cos(a), S[1] + d * Math.sin(a)]];
}
let mode = 'polish', act = { name: 'rest', p: 0, r: null, fruit: '#f2cf2e' }, lookUp = 0, rise = 0, riseT = 0, mintS = 0, turnNow = 0;

/* Hand targets and what's in view for the current action (phase p 0..1). Slow, soft movements. */
function pose(t) {
  const out = { L: [-60, -40], R: [60, -40], V: {} }, V = out.V;
  if (mode === 'polish') {
    const G = [-20, -96], w = t * 2.3;
    out.L = [G[0] - 6, G[1] + 18]; out.R = [G[0] + 14 + 12 * Math.cos(w), G[1] - 4 + 10 * Math.sin(w)];
    V.glass = G; V.cloth = [out.R[0] + 4, out.R[1], Math.sin(w) * .3];
    return out;
  }
  const { name, p } = act;
  switch (name) {
    case 'vine': {
      V.vine = { d: [[230, -420], [280, -300], [150, -230], [64, -160]], grow: seg(p, 0, .4) };
      const bp = ease(seg(p, .1, .45)), reach = seg(p, .4, .55), pour = seg(p, .55, .75);
      out.R = reach < 1 ? [lerp(60, 64, reach), lerp(-40, -140, reach)] : [lerp(64, 36, pour), lerp(-140, -124, pour)];
      V.bottle = reach < 1 ? [lerp(230, 64, bp), lerp(-420, -150, bp) - 40, 0] : [out.R[0], out.R[1] - 36, -1.85 * pour];
      if (pour > .6 && p < .97) V.stream = [6, -100, 40, act.r.colour];
      out.L = [-34, -60]; break;
    }
    case 'thyrsus': {
      const w = t * 4.5, tip = [6 * Math.cos(w), -34 + 2 * Math.sin(w)];
      out.R = [tip[0] + 26, tip[1] - 92]; out.L = [-34, -40]; V.thyrsus = { tip, hand: out.R }; break;
    }
    case 'lemon': {
      const grow = seg(p, 0, .35), ripe = seg(p, .2, .6), pick = seg(p, .6, .72), sq = seg(p, .75, 1);
      V.vine = { d: [[-230, -6], [-240, -90], [-150, -120], [-112, -182]], grow: seg(p, 0, .25) };
      const at = pick < 1 ? [-112, -170] : [lerp(-112, -14, Math.min(1, sq * 2)), lerp(-170, -110, Math.min(1, sq * 2))];
      out.L = pick > 0 ? [at[0] - 4, at[1] + 8] : [-60, -40];
      V.lemon = { at, s: (.25 + .75 * grow) * (sq > .6 ? lerp(1, .7, (sq - .6) / .4) : 1), col: mixc(act.fruit === '#86c03a' ? '#3d6a1e' : '#7a9a32', act.fruit, ripe) };
      if (sq > .5) V.drops = [at[0] + 4, at[1] + 14, (t * 50) % 40]; break;
    }
    case 'mint': {
      const sprout = seg(p, 0, .35), reach = seg(p, .35, .55), bring = seg(p, .6, .85);
      mintS = sprout; out.R = reach < 1 ? [lerp(60, 34, reach), lerp(-40, -300, reach)] : [lerp(34, 14, bring), lerp(-300, -92, bring)];
      if (reach >= 1) V.mint = [out.R[0], out.R[1] - 14]; break;
    }
    case 'honey': {
      const well = seg(p, 0, .4), dip = seg(p, .4, .6), drip = seg(p, .6, 1);
      V.honey = [-70, -6, 30 * well, 14 * well];
      const tip = dip < 1 ? [lerp(10, -70, dip), lerp(-110, -12, dip)] : [lerp(-70, 4, drip), lerp(-12, -100, drip)];
      out.R = [tip[0] + 30, tip[1] - 90]; out.L = [-30, -40]; V.thyrsus = { tip, hand: out.R };
      if (drip > .4) V.stream = [tip[0] - 2, tip[1] + 8, Math.max(0, -66 - tip[1] - 8 + 60), '#e0a224']; break;
    }
    case 'shake': { const k = Math.sin(t * 11) * 13, c = [70, -214 + k]; out.R = [c[0] + 12, c[1] + 18]; out.L = [c[0] - 18, c[1] - 22]; V.shaker = [c[0], c[1], .4 + k * .01]; break; }
    case 'strain': { const a = seg(p, 0, .3); out.R = [lerp(60, 44, a), lerp(-40, -150, a)]; out.L = [-30, -40]; V.shaker = [out.R[0] - 6, out.R[1] - 10, -1.75 * a]; if (a >= 1 && p < .95) V.stream = [10, -112, 46, act.r.colour]; break; }
    case 'ice': out.L = [-14, -150]; V.ice = p; break;
    case 'heat': V.steam = t; out.L = [-40, -50]; out.R = [40, -50]; break;
    default: V.spark = [24, -76, .6 + .4 * Math.sin(t * 5)]; out.L = [-40, -50]; out.R = [40, -50];
  }
  return out;
}
/* painted props */
function propsPaint(x, V, t) {
  if (V.vine) {
    const { d, grow } = V.vine; x.save(); x.lineCap = 'round';
    const p = new Path2D(); p.moveTo(...d[0]); p.bezierCurveTo(...d[1], ...d[2], ...d[3]);
    x.setLineDash([600]); x.lineDashOffset = 600 * (1 - grow); x.strokeStyle = '#1f3d16'; x.lineWidth = 8; x.stroke(p); x.strokeStyle = 'rgba(160,210,110,.5)'; x.lineWidth = 2; x.translate(-2, -2); x.stroke(p); x.restore();
    for (let i = 1; i < 4; i++) { const u = i / 4; if (u > grow) break; const bx = bez(d, u); x.save(); x.translate(bx[0], bx[1]); x.rotate(u * 5); const g = x.createLinearGradient(-10, -6, 10, 6); g.addColorStop(0, '#7fb055'); g.addColorStop(1, '#0c1a08'); x.fillStyle = g; x.beginPath(); x.ellipse(8, 0, 12, 6, 0, 0, 7); x.fill(); x.restore(); }
  }
  if (V.bottle) { const r = act.r, m = r.ing.find(i => ['spirit', 'liqueur', 'wine'].includes(ING[i.k][1])) || r.ing[0];
    x.save(); x.translate(V.bottle[0], V.bottle[1]); x.rotate(V.bottle[2]); paintBottle(x, ING[m.k][3], ING[m.k][2], -21, -35, .7, false, -100); x.restore(); }
  if (V.stream) { const [sx, sy, h, col] = V.stream, g = x.createLinearGradient(sx - 3, 0, sx + 3, 0); g.addColorStop(0, lighten(col, .4)); g.addColorStop(1, darken(col, .4)); x.fillStyle = g; x.fillRect(sx - 2.5, sy, 5, h); }
  if (V.thyrsus) {
    const { tip, hand: h } = V.thyrsus, ddx = h[0] - tip[0], ddy = h[1] - tip[1], L = Math.hypot(ddx, ddy), ux = ddx / L, uy = ddy / L, top = [h[0] + ux * 150, h[1] + uy * 150];
    x.save(); x.lineCap = 'round'; x.strokeStyle = '#4a2e14'; x.lineWidth = 7; x.beginPath(); x.moveTo(...tip); x.lineTo(...top); x.stroke();
    x.strokeStyle = 'rgba(255,210,150,.5)'; x.lineWidth = 2; x.beginPath(); x.moveTo(tip[0] - 2, tip[1]); x.lineTo(top[0] - 2, top[1]); x.stroke();
    x.translate(...top); x.rotate(Math.atan2(uy, ux) + Math.PI / 2); const g = x.createRadialGradient(-5, -8, 2, 0, 0, 24); g.addColorStop(0, '#c9b45a'); g.addColorStop(.5, '#5b6a24'); g.addColorStop(1, '#141a06');
    x.fillStyle = g; x.beginPath(); x.ellipse(0, 0, 13, 22, 0, 0, 7); x.fill(); x.restore();
  }
  if (V.lemon) { const { at, s, col } = V.lemon; x.save(); x.translate(...at); x.scale(s, s); const g = x.createRadialGradient(-5, -5, 1, 0, 0, 16); g.addColorStop(0, lighten(col, .5)); g.addColorStop(.5, col); g.addColorStop(1, darken(col, .7)); x.fillStyle = g; x.beginPath(); x.ellipse(0, 0, 15, 12, 0, 0, 7); x.fill(); x.restore(); }
  if (V.drops) for (let i = 0; i < 4; i++) { x.fillStyle = act.fruit; x.globalAlpha = .9; x.beginPath(); x.arc(V.drops[0] + (i - 1.5) * 4, V.drops[1] + ((V.drops[2] + i * 11) % 44), 3, 0, 7); x.fill(); x.globalAlpha = 1; }
  if (V.honey && V.honey[2] > 0) { const [hx, hy, rx, ry] = V.honey; glow(x, hx, hy - ry * .5, rx * 2.2, '#ffb000', .35); const g = x.createRadialGradient(hx - rx * .3, hy - ry * .6, 1, hx, hy, rx); g.addColorStop(0, '#fff0a0'); g.addColorStop(.5, '#e0a224'); g.addColorStop(1, '#6a3a08'); x.fillStyle = g; x.beginPath(); x.ellipse(hx, hy - ry * .4, rx, ry, 0, Math.PI, 0); x.fill(); }
  if (V.shaker) { x.save(); x.translate(V.shaker[0], V.shaker[1]); x.rotate(V.shaker[2]); x.scale(.9, .9);
    const cup = P2('M-20 -30 H20 L16 26 Q15 32 8 32 H-8 Q-15 32 -16 26 Z'); lit(x, cup, '#a8803a', [-20, -30, 20, 32], { hi: .5, term: .55 });
    x.strokeStyle = '#7a5a22'; x.lineWidth = 5; x.stroke(P2('M-26 -18 q-14 0 -14 14 q0 12 14 12 M26 -18 q14 0 14 14 q0 12 -14 12')); lit(x, P2('M-22 -38 h44 v10 h-44 Z'), '#8a6a2a', [-22, -38, 22, -28]); x.restore(); }
  if (V.mint) { x.save(); x.translate(...V.mint); [[-.3, 0], [.4, 8]].forEach(([r, o]) => { x.save(); x.rotate(r); const g = x.createLinearGradient(-6, -12, 6, 12); g.addColorStop(0, '#b6f08a'); g.addColorStop(1, '#2e6a22'); x.fillStyle = g; x.beginPath(); x.ellipse(o, 0, 6, 13, 0, 0, 7); x.fill(); x.restore(); }); x.restore(); }
  if (V.ice !== undefined) for (let i = 0; i < 3; i++) { const q = seg(V.ice, i * .22, i * .22 + .3); if (!q) continue; x.fillStyle = 'rgba(230,245,250,.55)'; x.strokeStyle = 'rgba(255,255,255,.8)'; x.lineWidth = 1; x.beginPath(); x.roundRect(-18 + i * 9, lerp(-150, -30 - i * 6, q), 12, 12, 3); x.fill(); x.stroke(); }
  if (V.steam !== undefined) { x.save(); x.strokeStyle = 'rgba(240,231,216,.35)'; x.lineWidth = 3; x.filter = 'blur(1.5px)'; for (let i = 0; i < 2; i++) { const o = (V.steam * 20 + i * 15) % 30; x.beginPath(); x.moveTo(-8 + i * 16, -78 - o); x.bezierCurveTo(-16 + i * 16, -96 - o, 0 + i * 16, -112 - o, -8 + i * 16, -130 - o); x.stroke(); } x.restore(); }
  if (V.spark) glow(x, V.spark[0], V.spark[1], 26, '#ffd890', .7 * V.spark[2]);
  if (V.glass) { const [gx, gy] = V.glass; x.save(); x.translate(gx, gy); const p = P2('M-14 -22 L-11 10 Q-10 14 -6 14 H6 Q10 14 11 10 L14 -22 Z'); x.fillStyle = 'rgba(255,240,220,.14)'; x.fill(p); x.strokeStyle = 'rgba(255,240,220,.65)'; x.lineWidth = 1.6; x.stroke(p); x.fillStyle = 'rgba(255,255,255,.85)'; x.fillRect(-9, -16, 2, 20); x.restore(); }
  if (V.cloth) { x.save(); x.translate(V.cloth[0], V.cloth[1]); x.rotate(V.cloth[2]); lit(x, P2('M-16 -8 Q-4 -22 14 -10 Q22 6 6 16 Q-12 18 -16 -8 Z'), '#a8743f', [-16, -22, 22, 18]); x.fillStyle = 'rgba(240,226,200,.8)'; x.beginPath(); x.arc(2, -2, 3, 0, 7); x.arc(-8, 6, 2.4, 0, 7); x.fill(); x.restore(); }
}
const bez = (d, u) => [0, 1].map(k => (1 - u) ** 3 * d[0][k] + 3 * (1 - u) ** 2 * u * d[1][k] + 3 * (1 - u) * u * u * d[2][k] + u ** 3 * d[3][k]);

/* the drink on the counter */
function paintDrink(x, r, prog, garnish) {
  const G = GL[r.glass], s = .58; x.save(); x.translate(-50 * s, -6 - 120 * s); x.scale(s, s);
  x.save(); x.beginPath(); x.rect(0, 120 - 120 * prog, 100, 120 * prog); x.clip(); const lg = x.createLinearGradient(0, 0, 100, 0); lg.addColorStop(0, lighten(r.colour, .25)); lg.addColorStop(.6, r.colour); lg.addColorStop(1, darken(r.colour, .6)); x.fillStyle = lg; x.fill(P2(G.l)); x.restore();
  x.fillStyle = 'rgba(255,240,220,.12)'; x.fill(P2(G.g)); x.strokeStyle = 'rgba(255,240,220,.6)'; x.lineWidth = 2; x.stroke(P2(G.g));
  if (garnish) { const [gx, gy] = G.rim, g = r.garnish;
    if (WHEEL[g]) { glow(x, gx, gy, 22, WHEEL[g][0], .5); x.fillStyle = WHEEL[g][0]; x.beginPath(); x.arc(gx, gy, 11, 0, 7); x.fill(); x.fillStyle = WHEEL[g][1]; x.beginPath(); x.arc(gx, gy, 7.5, 0, 7); x.fill(); }
    else if (g === 'orange') { x.fillStyle = '#ef8a22'; x.fill(P2(`M${gx - 12} ${gy + 5} Q${gx - 2} ${gy - 12} ${gx + 12} ${gy - 3} Q${gx} ${gy - 4} ${gx - 7} ${gy + 9} Z`)); }
    else if (g === 'cherry') { const [a, b] = G.cherry; x.fillStyle = '#9b1020'; x.beginPath(); x.arc(a, b, 6, 0, 7); x.fill(); }
    else if (g === 'mint') { x.fillStyle = '#4c9a48'; x.beginPath(); x.ellipse(gx - 6, gy - 9, 5, 10, -.5, 0, 7); x.ellipse(gx + 4, gy - 11, 5, 10, .4, 0, 7); x.fill(); }
    else if (g === 'foam' || g === 'cream') { x.fillStyle = '#f2e7d1'; x.fill(P2(G.foam)); }
    else if (g === 'ginger') { x.fillStyle = '#e6c27a'; x.fillRect(gx - 8, gy - 9, 16, 12); } }
  x.restore();
}

function drawDio(t) {
  const o = pose(t), k = RM ? 1 : .12;
  ['L', 'R'].forEach(s => { hand[s][0] = lerp(hand[s][0], o[s][0], k); hand[s][1] = lerp(hand[s][1], o[s][1], k); });
  if (mode !== 'recipe' || act.name !== 'mint') mintS = Math.max(0, mintS - .03);
  const turnTo = RM ? 0 : lookUp ? .9 : mode === 'polish' ? Math.sin(t * .3) * .7 + Math.sin(t * .09) * .3 : -.4;
  turnNow = lerp(turnNow, turnTo, .04);
  dx.setTransform(1, 0, 0, 1, 0, 0); dx.clearRect(0, 0, dc.width, dc.height); dx.translate(320, 650);
  fig.draw(dx, { t, breath: RM ? 0 : Math.sin(t * 1.3), turn: turnNow, tilt: lookUp ? -4 : mode === 'polish' ? 6 : 3, rise, mint: mintS, armL: ik(SH.L, hand.L, 1), armR: ik(SH.R, hand.R, -1) });
  dx.save(); dx.translate(0, -rise); propsPaint(dx, o.V, t); dx.restore();
  if (mode === 'recipe' && recipeState) paintDrink(dx, recipeState.r, recipeState.prog, recipeState.garnish);
  dx.setTransform(1, 0, 0, 1, 0, 0);
  dx.save(); dx.globalCompositeOperation = 'source-atop'; const sh = dx.createLinearGradient(150, 200, 560, 700);
  sh.addColorStop(0, 'rgba(255,236,200,.10)'); sh.addColorStop(.35, 'rgba(0,0,0,0)'); sh.addColorStop(.7, 'rgba(12,6,4,.55)'); sh.addColorStop(1, 'rgba(6,3,2,.85)');
  dx.fillStyle = sh; dx.fillRect(0, 0, dc.width, dc.height); dx.restore();
  texture(dx, dc.width, dc.height, .45);
}

/* Cheeky: every so often he reaches up; a blurred vine of grapes swings past in front */
function cheekyTick(dt) {
  if (LOOK.coverage !== 'cheeky' || mode !== 'polish' || RM) { rise = lerp(rise, 0, .1); passingCv.style.display = 'none'; return; }
  riseT += dt; const cyc = riseT % 10, up = cyc > 6.5 ? Math.sin(Math.PI * (cyc - 6.5) / 3.5) : 0; rise = 34 * up;
  passingCv.style.display = up > 0 ? '' : 'none';
  if (up > 0) passingCv.style.transform = `${baseT.passing} translateX(${lerp(-60, 60, (cyc - 6.5) / 3.5)}px) rotate(${Math.sin(cyc * 3) * 6}deg)`;
}

let last = performance.now(), T = 0;
function frame(now) {
  const dt = Math.min(.05, (now - last) / 1000); last = now; T += RM ? 0 : dt;
  if (mode === 'recipe' && recipeState) recipeTick(dt);
  cheekyTick(dt); drawDio(T);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

/* ---------------- Speech ---------------- */
const bubble = $('#bubble'), sayEl = $('#say'), chips = $('#chips'), talkForm = $('#talk');
function placeBubble() {
  if (bubble.hidden || isPhone()) { bubble.style.left = ''; bubble.style.top = ''; return; }
  const r = dc.getBoundingClientRect(), hx = r.left + r.width * .5, hy = r.top + r.height * (380 / 700), bw = bubble.offsetWidth, bh = bubble.offsetHeight;
  let x = hx + r.width * .14, y = hy - bh - 10;
  x = clamp(x, 16, innerWidth - bw - 16); y = clamp(y, 76, innerHeight - bh - 16);
  bubble.style.left = x + 'px'; bubble.style.top = y + 'px';
}
function speak(html, o = {}) {
  bubble.hidden = false; sayEl.innerHTML = html; sayEl.className = o.cls || ''; chips.innerHTML = '';
  (o.chips || []).forEach(c => { const b = document.createElement('button'); b.type = 'button'; b.className = 'chip ' + (c.cls || ''); b.innerHTML = c.label; b.onclick = c.go; chips.appendChild(b); });
  talkForm.hidden = !o.talk; lookUp = 1; $('#talkBtn').hidden = true; requestAnimationFrame(placeBubble); setTimeout(placeBubble, RM ? 0 : 1550);
  if (o.talk && !isPhone()) setTimeout(() => $('#talkIn').focus({ preventScroll: true }), 60);
}
function hush() { bubble.hidden = true; lookUp = 0; if (screen === 'home') $('#talkBtn').hidden = false; }
$('#bubbleX').onclick = () => { hush(); if (shot !== 'home') home(); };

/* ---------------- Screens ---------------- */
let screen = 'intro'; const panel = $('#panel'), stage = $('#stage');
function home() {
  screen = 'home'; panel.hidden = true; panel.className = 'panel'; stage.classList.remove('blur', 'dim');
  mode = 'polish'; recipeState = null; $('#back').hidden = true; $('#talkBtn').hidden = false; hush(); return cam('home');
}
function setScreen(n) { screen = n; $('#back').hidden = false; $('#talkBtn').hidden = true; panel.hidden = true; stage.classList.remove('blur', 'dim'); mode = 'polish'; recipeState = null; }
$('#back').onclick = () => home();
addEventListener('keydown', e => { if (e.key === 'Escape' && screen !== 'home' && screen !== 'intro') home(); });

/* 1. Opening: the big word flies into the sign and lights as neon */
async function intro() {
  await Promise.race([document.fonts.ready, wait(1500)]);
  const w = $('#word'), r0 = w.getBoundingClientRect();
  Object.assign(w.style, { transition: 'none', left: r0.left + 'px', top: r0.top + 'px', transform: 'none' }); w.offsetHeight; w.style.transition = '';
  await wait(RM ? 0 : 900);
  stage.classList.add('on');
  await wait(RM ? 0 : 900);
  const s = $('#sign span').getBoundingClientRect(), r1 = w.getBoundingClientRect(), k = s.width / r1.width;
  w.style.transform = `translate(${s.left - r1.left}px, ${s.top - r1.top + (s.height - r1.height * k) / 2}px) scale(${k})`;
  await wait(RM ? 0 : 1500);
  stage.classList.add('lit', 'flick'); w.classList.add('gone');
  await wait(RM ? 0 : 900);
  await cam('home', true);
  if (screen !== 'intro') return;
  screen = 'home'; $('#talkBtn').hidden = false;
  if (!BAR.filled) askWhatYouHave();
}

/* 3. "What do you have?" */
function askWhatYouHave() {
  speak('What do you have? My shelf is all dust and cobweb.', { chips: [{ label: 'Show him some photos', cls: 'go', go: openPhotos }, { label: 'Later', cls: 'skip', go: hush }] });
}
const PHOTO_ART = {
  cupboard: '<rect width="160" height="120" fill="#3a2719"/><rect y="70" width="160" height="6" fill="#5a3f2a"/>' + [['#b8661c', 14], ['#a9561a', 34], ['#c98a2c', 52], ['#9a6a2a', 72], ['#d39a3a', 90], ['#cfe2e8', 110], ['#e9e0c8', 130]].map(([c, x]) => `<rect x="${x}" y="28" width="14" height="42" rx="3" fill="${c}"/><rect x="${x + 4}" y="20" width="6" height="10" fill="${c}"/>`).join(''),
  fridge: '<rect width="160" height="120" fill="#cfd8da"/><rect x="10" y="10" width="140" height="100" rx="6" fill="#e9eef0"/><rect x="10" y="64" width="140" height="5" fill="#b8c4c8"/>' + [['#7a2418', 20], ['#e6dfb6', 42], ['#8a2a14', 64], ['#e07a1c', 80], ['#e6c88a', 98], ['#e4eef2', 118]].map(([c, x]) => `<rect x="${x}" y="24" width="14" height="40" rx="3" fill="${c}"/>`).join('') + '<ellipse cx="40" cy="88" rx="12" ry="9" fill="#f3eedf"/><circle cx="80" cy="88" r="6" fill="#9b1020"/>',
  bowl: '<rect width="160" height="120" fill="#6b4c33"/><path d="M20 70 Q80 130 140 70 Z" fill="#e9dcc4"/>' + [['#f2cf2e', 50, 62], ['#86c03a', 72, 58], ['#ef8a22', 94, 62], ['#f0826a', 114, 66], ['#f2cf2e', 64, 46]].map(([c, x, y]) => `<circle cx="${x}" cy="${y}" r="13" fill="${c}"/>`).join('') + '<path d="M26 40 q10 -20 22 -4" stroke="#4c9a48" stroke-width="6" fill="none"/>',
  drawer: '<rect width="160" height="120" fill="#2b1d14"/><rect x="8" y="16" width="144" height="92" rx="4" fill="#4a3324"/><path d="M30 30 L46 30 L42 90 L34 90 Z" fill="#c9ccd0"/><path d="M60 30 h16 l-6 26 l6 26 h-16 l6 -26 Z" fill="#c9ccd0"/><rect x="92" y="26" width="4" height="70" fill="#c9ccd0"/><circle cx="124" cy="56" r="16" fill="none" stroke="#c9ccd0" stroke-width="4"/>',
};
function openPhotos() {
  hush(); setScreen('shelf'); cam('shelf');
  const picked = new Set(PHOTOS.map(p => p.id));
  panel.className = 'panel sheet'; panel.hidden = false;
  panel.innerHTML = `<h2>Show him your bar</h2><p>Lay out photos of your bottles and tools. <i>(Sample photos; this prototype only pretends to read them.)</i></p>
   <div class="polaroids">${PHOTOS.map(p => `<button class="photo" data-id="${p.id}" aria-pressed="true"><svg viewBox="0 0 160 120">${PHOTO_ART[p.id]}</svg><span>${p.name}</span></button>`).join('')}</div>
   <div class="row"><button class="btn ghost" id="pcancel">Not now</button><button class="btn" id="pread">Let him read them</button></div>`;
  panel.querySelectorAll('.photo').forEach(b => b.onclick = () => { const id = b.dataset.id; picked.has(id) ? picked.delete(id) : picked.add(id); b.setAttribute('aria-pressed', picked.has(id)); });
  $('#pcancel').onclick = home;
  $('#pread').onclick = async () => {
    if (!picked.size) return;
    panel.innerHTML = `<h2>Show him your bar</h2><div class="reading"><span class="candle"></span> He holds them to the candle, reading…</div>`;
    await wait(RM ? 300 : 2000);
    const res = readPhotos([...picked]), byKind = {};
    res.found.forEach(k => { const f = isBottle(k) ? (FAMILIES[ING[k][3]] || { bitters: 'Bitters', mixer: 'Mixers' }[ING[k][3]] || 'Other') : 'In the kitchen'; (byKind[f] = byKind[f] || []).push(ING[k][0]); });
    panel.innerHTML = `<h2>He found</h2><ul class="found">${Object.entries(byKind).map(([f, l]) => `<li><b>${f}</b>${l.join(', ')}</li>`).join('')}</ul>
     <p><b>Barware.</b> Tick what you have:</p>
     <div class="ticks">${Object.entries(BARWARE).map(([k, v]) => `<label><input type="checkbox" value="${k}" ${res.tools.includes(k) ? 'checked' : ''}> ${v}</label>`).join('')}</div>
     <div class="row"><button class="btn ghost" id="pcancel">Not now</button><button class="btn" id="pstock">Stock the shelf</button></div>`;
    $('#pcancel').onclick = home;
    $('#pstock').onclick = async () => {
      applyReading(res, [...panel.querySelectorAll('.ticks input:checked')].map(i => i.value)); panel.hidden = true; drawShelf(true);
      await wait(RM ? 0 : 2400); await home();
      speak(`Better. ${R.filter(canMake).length} drinks within reach now. Open the menu, or tell me what you're after.`, { chips: [{ label: 'Good', cls: 'go', go: hush }] });
    };
  };
}
function openShelf() {
  if (!BAR.filled) return openPhotos();
  hush(); setScreen('shelf'); cam('shelf');
  const fam = {}; shelfBottles().forEach(b => { const f = FAMILIES[b.family] || 'Bitters and mixers'; (fam[f] = fam[f] || []).push(b.style); });
  panel.className = 'panel sheet'; panel.hidden = false;
  panel.innerHTML = `<h2>Your shelf</h2><ul class="found">${Object.entries(fam).map(([f, l]) => `<li><b>${f}</b>${l.join(', ')}</li>`).join('')}</ul><p>Barware: ${[...BAR.barware].map(b => BARWARE[b]).join(', ') || 'none yet'}</p>
   <div class="row"><button class="btn ghost" id="pmore">More photos</button><button class="btn" id="pdone">Back to the bar</button></div>`;
  $('#pmore').onclick = openPhotos; $('#pdone').onclick = home;
}
$('#shelf').addEventListener('click', () => { if (screen === 'home') openShelf(); });

/* 4. The menu */
function drinkBtn(r) {
  const need = missingFor(r);
  return `<button class="drink${need.length ? ' need' : ''}" data-id="${r.id}"><span>${r.name}</span><span class="dots"></span><small>${need.length ? 'wants ' + need.map(x => ING[x.k][0].toLowerCase()).join(', ') : FEELS[feelOf(r)].toLowerCase()}</small></button>`;
}
function menuBody(tab) {
  if (tab === 'spirit') return Object.entries(FAMILIES).map(([k, v]) => { const l = R.filter(r => r.spirit === k); return l.length ? `<h3>${v}</h3>${l.map(drinkBtn).join('')}` : ''; }).join('');
  if (tab === 'feel') return Object.entries(FEELS).map(([k, v]) => `<h3>${v}</h3>${R.filter(r => feelOf(r) === k).map(drinkBtn).join('')}`).join('');
  return `<div class="letters">${[...R].sort((a, b) => a.name.localeCompare(b.name)).map(drinkBtn).join('')}</div>`;
}
async function openMenu(tab = 'spirit') {
  hush(); setScreen('menu'); await cam('menu'); stage.classList.add('dim');
  panel.className = 'panel book'; panel.hidden = false;
  panel.innerHTML = `<div class="page"><h2>Bibenda</h2><p class="sub">things to be drunk</p><div class="tabs" role="tablist">${[['spirit', 'By spirit'], ['feel', 'By feel'], ['az', 'A–Z']].map(([k, v]) => `<button class="tab" role="tab" data-t="${k}" aria-selected="${k === tab}">${v}</button>`).join('')}</div><div class="list">${menuBody(tab)}</div></div>`;
  panel.querySelectorAll('.tab').forEach(b => b.onclick = () => { panel.querySelectorAll('.tab').forEach(x => x.setAttribute('aria-selected', x === b)); panel.querySelector('.list').innerHTML = menuBody(b.dataset.t); wire(); });
  wire();
}
function wire() { panel.querySelectorAll('.drink').forEach(b => b.onclick = () => openRecipe(b.dataset.id)); }
$('#menu').addEventListener('click', () => { if (screen === 'home') openMenu(); });

/* 5. Speaking to him */
let conv = null;
function startTalk() { setScreen('talk'); hush(); cam('talk'); conv = Conversation(); render(conv.start()); }
function render(s) {
  if (s.open) return openRecipe(s.open);
  const ch = [];
  if (s.results) { s.results.forEach(r => ch.push({ label: `${glassSide(r, 22)} ${r.name}`, cls: 'res', go: () => openRecipe(r.id) })); ch.push({ label: 'Start again', cls: 'skip', go: () => render((conv = Conversation()).start()) }); }
  else { (s.opts || []).forEach(([k, v]) => ch.push({ label: v, go: () => render(conv.answer(s.q, k)) })); if (s.q !== 'open') ch.push({ label: 'Skip', cls: 'skip', go: () => render(conv.answer(s.q, '-')) }); }
  speak(s.say + (s.count ? ` <small style="opacity:.6">(${s.count} would do)</small>` : ''), { chips: ch, talk: true });
}
talkForm.onsubmit = e => { e.preventDefault(); const v = $('#talkIn').value.trim(); if (!v) return; $('#talkIn').value = ''; if (!conv) conv = Conversation(); render(conv.say(v)); };
$('#talkBtn').onclick = startTalk;
$('#mic').onclick = () => {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition, m = $('#mic');
  if (!SR) { $('#talkIn').placeholder = 'Speech isn’t available here. Type instead.'; $('#talkIn').focus(); return; }
  const rec = new SR(); rec.lang = 'en-GB'; m.classList.add('on'); rec.onresult = ev => { $('#talkIn').value = ev.results[0][0].transcript; talkForm.requestSubmit(); }; rec.onend = () => m.classList.remove('on'); rec.start();
};

/* 6. A story */
function tellStory(except) {
  setScreen('story'); cam('talk');
  const pool = R.filter(r => STORY[r.id] && (canMake(r) || !BAR.filled) && r.id !== except), r = pool[Math.floor(Math.random() * pool.length)], s = STORY[r.id];
  speak(`<span class="who">${r.name} · ${s.by} · ${s.at} · ${s.when} · ${s.kind === 'legend' ? 'a legend' : 'on record'}</span>${s.tell}`, { cls: 'story', chips: [{ label: 'Make me one', cls: 'go', go: () => openRecipe(r.id) }, { label: 'Another', go: () => tellStory(r.id) }] });
}
$('#dio').addEventListener('click', () => { if (['home', 'story', 'talk'].includes(screen)) tellStory(); });

/* 6b. Barman's choice: the panther bats the die off the bar */
let rolling = false;
async function barmansChoiceGo() {
  if (rolling) return; rolling = true; screen = 'choice'; $('#talkBtn').hidden = true; hush(); const r = barmansChoice();
  if (!RM) {
    await cam('choice');
    const pc = $('#panther'), die = $('#dice'), cube = die.querySelector('.cube'), t0 = performance.now();
    await new Promise(res => { (function f(now) {
      const p = (now - t0) / 1500, sw = Math.sin(clamp(p / .3, 0, 1) * Math.PI); paintPanther(pc, sw);
      const q = seg(p, .2, 1);
      die.style.transform = `${baseT.dice} translate3d(${-240 * q}px, ${-60 * Math.sin(Math.PI * Math.min(1, q * 1.5)) + (q > .66 ? 400 * (q - .66) : 0)}px, ${120 * q}px)`;
      cube.style.transform = `rotateX(${-20 - 720 * q}deg) rotateY(${30 + 540 * q}deg)`;
      if (p < 1) requestAnimationFrame(f); else res(); })(t0); });
    paintPanther(pc, 0); die.style.transform = baseT.dice; cube.style.transform = '';
  }
  rolling = false; openRecipe(r.id, true);
}
$('#panther').addEventListener('click', () => { if (screen === 'home') barmansChoiceGo(); });
$('#dice').addEventListener('click', () => { if (screen === 'home') barmansChoiceGo(); });

/* 7. Recipe in front; he makes it behind, blurred */
let recipeState = null; const STEP_S = 4.4;
function openRecipe(id, chosen) {
  const r = RB[id]; hush(); setScreen('recipe'); stage.classList.remove('dim'); stage.classList.add('blur'); cam('recipe'); mode = 'recipe';
  const s = STORY[id], miss = missingFor(r), swaps = swapsFor(r);
  panel.className = 'panel recipe'; panel.hidden = false;
  panel.innerHTML = `${chosen ? '<p class="kicker">The panther chose</p>' : '<p class="kicker">He makes you</p>'}<h2>${r.name}</h2>
   <p class="meta">${FEELS[feelOf(r)]}, ${STRENGTHS[strengthOf(r)].toLowerCase()} strength, in a ${r.glass} glass${s ? `. ${s.by}, ${s.when}` : ''}.</p>
   <ul>${r.ing.map(x => { const m = miss.includes(x); return `<li class="${m ? 'miss' : ''}"><span>${ING[x.k][0]}${x.o ? ' <i>(optional)</i>' : ''}${m ? ' <i>— you’re out</i>' : ''}</span><span>${fmtQty(x)}</span></li>`; }).join('')}</ul>
   ${swaps.length ? `<div class="swap">No ${swaps.map(s => s.tool.toLowerCase()).join(', ')}? ${swaps.map(s => `Use ${s.use}`).join('. ')}.</div>` : ''}
   <ol id="steps">${r.steps.map((st, i) => `<li data-i="${i}">${st[2]}<em>${ACTION_LABEL[actionFor(st, r)]}</em></li>`).join('')}</ol>
   ${s ? `<p class="tellme">“${s.tell.split('. ').slice(0, 2).join('. ')}.”</p>` : ''}
   <div class="row"><button class="btn ghost" id="again">Another, please</button><button class="btn" id="rdone">Back to the bar</button></div>`;
  $('#again').onclick = () => openRecipe(barmansChoice(id).id, true); $('#rdone').onclick = home;
  panel.querySelectorAll('#steps li').forEach(li => li.onclick = () => { recipeState.i = +li.dataset.i; recipeState.t = 0; setAct(); });
  recipeState = { r, i: 0, t: 0, prog: 0, garnish: false }; setAct();
}
function setAct() {
  const { r, i } = recipeState, st = r.steps[i], fk = ['lime', 'grapefruit', 'lemon'].find(f => st[2].toLowerCase().includes(f)) || 'lemon';
  act = { name: actionFor(st, r), p: 0, r, fruit: ING[fk][2] };
  document.querySelectorAll('#steps li').forEach((li, j) => li.classList.toggle('now', j === i));
}
function recipeTick(dt) {
  const s = recipeState, n = s.r.steps.length;
  if (RM) { act.p = .8; s.prog = 1; return; }
  s.t += dt; act.p = clamp(s.t / STEP_S, 0, 1);
  s.prog = s.i === 0 && !['pour', 'top'].includes(s.r.steps[0][0]) ? 0 : clamp((s.i + act.p) / n, 0, 1);
  s.garnish = s.i === n - 1 && act.p > .5;
  if (s.t > STEP_S) { s.t = 0; s.i = (s.i + 1) % n; if (s.i === 0) s.t = -2.5; setAct(); }
}

/* 2. His look */
function applyLook() { document.body.className = `fin-${LOOK.finish} cov-${LOOK.coverage}`; fig.setLook(LOOK); if (stage.classList.contains('on')) {} }
const settings = $('#settings');
function renderSettings() {
  settings.innerHTML = `<h3>His look</h3>
   <fieldset><legend>Finish</legend><div class="seg">${Object.entries(FINISHES).map(([k, v]) => `<label><input type="radio" name="fin" value="${k}" ${LOOK.finish === k ? 'checked' : ''}>${v}</label>`).join('')}</div></fieldset>
   <fieldset><legend>Coverage</legend><div class="seg">${Object.entries(COVERAGES).map(([k, v]) => `<label><input type="radio" name="cov" value="${k}" ${LOOK.coverage === k ? 'checked' : ''} ${k === 'cheeky' && !LOOK.adult ? 'disabled' : ''}>${k === 'cheeky' ? 'Cheeky<span class="badge">ADULT</span>' : v}</label>`).join('')}</div></fieldset>
   <label class="adult"><input type="checkbox" id="adult" ${LOOK.adult ? 'checked' : ''}> <span>Allow adult looks. Cheeky is only ever implied: a fig leaf, and something always passes in front.</span></label>`;
  settings.querySelectorAll('input[name=fin]').forEach(i => i.onchange = () => { LOOK.finish = i.value; applyLook(); });
  settings.querySelectorAll('input[name=cov]').forEach(i => i.onchange = () => { LOOK.coverage = i.value; riseT = 0; applyLook(); });
  $('#adult').onchange = e => { LOOK.adult = e.target.checked; if (!LOOK.adult && LOOK.coverage === 'cheeky') LOOK.coverage = 'classical'; applyLook(); renderSettings(); };
}
$('#gear').onclick = () => { settings.hidden = !settings.hidden; if (!settings.hidden) renderSettings(); };
document.addEventListener('click', e => { if (!settings.hidden && !settings.contains(e.target) && !$('#gear').contains(e.target)) settings.hidden = true; });
applyLook();

window.proto = { home, openMenu, startTalk, openRecipe, tellStory, openPhotos, barmansChoiceGo, conv: () => conv,
  setLook: (f, c, a) => { riseT = 0; LOOK.finish = f; if (a !== undefined) LOOK.adult = a; if (c) LOOK.coverage = c; applyLook(); renderSettings(); settings.hidden = false; },
  fill: () => { applyReading(readPhotos(PHOTOS.map(p => p.id)), ['shaker', 'strainer', 'jigger', 'spoon']); drawShelf(); } };
document.fonts.ready.then(() => paintMenuBook($('#menu')));
intro();
