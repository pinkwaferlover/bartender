/* The Dionysus layer (R4, R13). The bar talks to Dionysus only through this interface, so how he is
   drawn can change without touching the scene. Two implementations:

   LoopDio  : the default. Rendered loops, one per action, each a list of frames or a video (R4), from
              blender/build_dionysus.py (a MakeHuman base in painted marble, R3). Manifest: dio-loops.json;
              another can be given with ?loops=<manifest.json>. See dio-loops.example.json for the format.
   SvgDio   : prototype B's flat figure, solved each frame (two-bone IK). Shown until the loops have loaded,
              and kept if they can't load (for example from file://), or always with ?dio=svg.

   Interface (both):
     el                      the layer's root <g>, in world units (he stands at x 800, his feet at y 672)
     idle()                  polish a glass: the resting loop
     story()                 tell a story: the story loop
     perform(action, ctx)    act out one recipe step, then hold and wait (R6: no timer, the user taps on).
                             action is logic.js actionFor(): thyrsus vine lemon mint honey shake strain ice heat garnish.
                             ctx: { r (recipe), fruit (colour), honeyAt ([x,y] world) }. Returns a Promise that
                             resolves when the step has been acted out.
     lookUp(on)              head up while he is talking
     setLook(LOOK)           finish and coverage (Q8, Q9)
     tick(t, dt)             called every frame
     headRect()              screen rect of his head, for the speech bubble
*/
const DIO_LOOPS = ['polish', 'stir', 'pour', 'shake', 'reach', 'story'];
/* Every recipe action is one of the six loops. */
const LOOP_OF = { thyrsus: 'stir', honey: 'stir', vine: 'pour', strain: 'pour', lemon: 'reach', mint: 'reach', ice: 'reach', garnish: 'reach', shake: 'shake', heat: 'polish' };
const ACT_S = 3.2;   // how long acting out one step takes, before he waits for your tap

function makeDio(root) {
  const q = new URLSearchParams(location.search);
  const svgDio = SvgDio(root);
  if (q.get('dio') === 'svg') return svgDio;
  // Start with the drawn figure, switch to the rendered loops once their manifest and first frames are in.
  let cur = svgDio; const loops = LoopDio(root);
  fetch(q.get('loops') || 'dio-loops.json').then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(m => loops.load(m)).then(() => { loops.copyState(cur); cur = loops; })
    .catch(e => { console.warn('Dionysus loops not loaded (' + e.message + '); keeping the drawn figure.'); loops.fail(); });
  const api = {};
  ['idle', 'story', 'perform', 'lookUp', 'setLook', 'tick', 'headRect'].forEach(k => { api[k] = (...a) => { if (k === 'setLook' || k === 'lookUp') { svgDio[k](...a); loops[k](...a); } return cur[k](...a); }; });
  Object.defineProperty(api, 'kind', { get: () => cur.kind });
  Object.defineProperty(api, 'acting', { get: () => cur.acting });
  Object.defineProperty(api, 'el', { get: () => cur.el });
  return api;
}

/* ---------------------------------------------------------------- SvgDio: B's figure */
function SvgDio(root) {
  const NS = 'http://www.w3.org/2000/svg';
  const q = s => root.querySelector(s);
  const mk = (tag, attrs = {}, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
  const lerp = (a, b, t) => a + (b - a) * t, clamp = (x, a, b) => Math.max(a, Math.min(b, x));
  const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  const seg = (p, a, b) => clamp((p - a) / (b - a), 0, 1);
  const RM = reduceMotion();

  // curls, wreath, the mint that sprouts from it
  [[-34, -284], [-22, -298], [-6, -304], [10, -303], [25, -296], [36, -282], [-40, -268], [41, -266], [-30, -292], [30, -290], [0, -296]]
    .forEach(([x, y]) => mk('circle', { cx: x, cy: y, r: 13 }, q('#curls')));
  for (let i = 0; i < 13; i++) {
    const a = Math.PI * (1.05 + i * 0.9 / 12), x = Math.cos(a) * 44, y = -270 + Math.sin(a) * 36;
    mk('ellipse', { cx: x, cy: y, rx: 12, ry: 6.5, fill: i % 2 ? '#3f7a34' : '#2f6428', transform: `rotate(${a * 180 / Math.PI + 90} ${x} ${y})` }, q('#wreath'));
  }
  [[-44, -246], [44, -246]].forEach(([x, y]) => [[0, 0], [-7, 7], [7, 7], [0, 14], [-4, 21], [4, 21]].forEach(([dx, dy]) =>
    mk('circle', { cx: x + dx, cy: y + dy, r: 5.6, fill: '#5b2a6b' }, q('#wreath'))));
  [[-30, -312, -30], [-10, -322, -8], [14, -320, 14], [32, -308, 32]].forEach(([x, y, r]) =>
    mk('ellipse', { cx: x, cy: y, rx: 6, ry: 12, fill: '#6fcf5a', transform: `rotate(${r} ${x} ${y})` }, q('#mintsprout')));
  q('#mintsprout').setAttribute('transform', 'scale(0)');

  q('#props').innerHTML = `
 <g id="pGlass"><path d="M-14 -22 L-11 10 Q-10 14 -6 14 H6 Q10 14 11 10 L14 -22 Z" fill="rgba(240,231,216,.28)" stroke="#f0e7d8" stroke-width="2.4"/><path d="M-8 -14 L-7 6" stroke="#fff" stroke-width="2" opacity=".7"/></g>
 <g id="pCloth"><path d="M-16 -8 Q-4 -22 14 -10 Q22 6 6 16 Q-12 18 -16 -8 Z" fill="#b98552"/><circle cx="2" cy="-2" r="3" fill="#efe2c8"/><circle cx="-8" cy="6" r="2.4" fill="#efe2c8"/></g>
 <path id="pVine" fill="none" stroke="#3f7a34" stroke-width="6" stroke-linecap="round"/>
 <g id="pBottle"></g>
 <rect id="pStream" width="5" rx="2.5" fill="#d9a441"/>
 <g id="pThyrsus"><line id="pStaff" stroke="#7a5530" stroke-width="7" stroke-linecap="round"/><g id="pCone"><ellipse rx="13" ry="22" fill="#5b7a2e"/><path d="M-11 -6 h22 M-12 6 h24 M-10 16 h20" stroke="#3f5a1f" stroke-width="3"/></g></g>
 <g id="pLemon"><ellipse id="pLemonBody" rx="14" ry="11"/><path d="M0 -11 q4 -8 12 -8" stroke="#3f7a34" stroke-width="3" fill="none"/></g>
 <g id="pDrops"></g>
 <g id="pHoneyDrip"><circle r="5" fill="#e0951c"/></g>
 <g id="pShaker"><path d="M-20 -30 H20 L16 26 Q15 32 8 32 H-8 Q-15 32 -16 26 Z" fill="#c9a24a"/><path d="M-26 -18 q-14 0 -14 14 q0 12 14 12 M26 -18 q14 0 14 14 q0 12 -14 12" fill="none" stroke="#c9a24a" stroke-width="5"/><rect x="-22" y="-38" width="44" height="10" rx="4" fill="#a88838"/></g>
 <g id="pMint"><ellipse rx="6" ry="12" fill="#6fcf5a" transform="rotate(-20)"/><ellipse cx="8" rx="6" ry="12" fill="#5fbf4a" transform="rotate(25)"/></g>
 <g id="pIce"></g>
 <g id="pSteam" fill="none" stroke="#f0e7d8" stroke-width="3" stroke-linecap="round" opacity=".6"><path d="M-10 -80 q-8 -14 0 -26 q8 -12 0 -26"/><path d="M10 -86 q-8 -14 0 -26 q8 -12 0 -26"/></g>
 <g id="pSpark" fill="#ffd2df"><path d="M0 -12 L3 -3 L12 0 L3 3 L0 12 L-3 3 L-12 0 L-3 -3 Z"/></g>`;
  const P = id => root.querySelector('#' + id);
  for (let i = 0; i < 3; i++) mk('rect', { width: 12, height: 12, rx: 3, fill: '#eef6f8', opacity: .8 }, P('pIce'));
  for (let i = 0; i < 4; i++) mk('circle', { r: 3.4, fill: '#f2cf2e' }, P('pDrops'));
  const ALLPROPS = ['pGlass', 'pCloth', 'pVine', 'pBottle', 'pStream', 'pThyrsus', 'pLemon', 'pDrops', 'pHoneyDrip', 'pShaker', 'pMint', 'pIce', 'pSteam', 'pSpark'];
  const show = (id, on) => { P(id).style.display = on ? '' : 'none'; };
  const place = (id, x, y, rot = 0, s = 1) => P(id).setAttribute('transform', `translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${rot.toFixed(1)}) scale(${s})`);

  const SH = { L: [-96, -166], R: [96, -166] }, L1 = 82, L2 = 78;
  const hand = { L: [-36, -80], R: [0, -100] };
  function ik(S, Tg, bend) {
    const dx = Tg[0] - S[0], dy = Tg[1] - S[1]; let d = Math.hypot(dx, dy);
    d = clamp(d, Math.abs(L1 - L2) + 2, L1 + L2 - 1);
    const a = Math.atan2(dy, dx), b = Math.acos(clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1));
    return { E: [S[0] + L1 * Math.cos(a + bend * b), S[1] + L1 * Math.sin(a + bend * b)], H: [S[0] + d * Math.cos(a), S[1] + d * Math.sin(a)] };
  }
  function mix(a, b, t) { const pa = a.match(/\w\w/g).map(h => parseInt(h, 16)), pb = b.match(/\w\w/g).map(h => parseInt(h, 16)); return '#' + pa.map((v, i) => Math.round(lerp(v, pb[i], t)).toString(16).padStart(2, '0')).join(''); }

  let mode = 'polish';            // polish | story | step | wait
  let act = { name: 'rest', p: 0, r: null, fruit: '#f2cf2e', honeyAt: [-160, -40] }, actT = 0, actDone = null;
  let look = 0, rise = 0, riseT = 0;

  function pose(t) {
    const out = { L: [-60, -40], R: [60, -40], vis: {} }, V = out.vis;
    if (mode === 'polish' || mode === 'story') {
      const G = [-20, -96], w = t * (mode === 'story' ? 1.2 : 4.2);
      out.L = [G[0] - 6, G[1] + 18]; out.R = [G[0] + 14 + 13 * Math.cos(w), G[1] - 4 + 11 * Math.sin(w)];
      if (mode === 'story') { out.R = [70 + 16 * Math.sin(t * 1.7), -150 + 10 * Math.cos(t * 2.3)]; }
      V.pGlass = [G[0], G[1], 0]; if (mode === 'polish') V.pCloth = [out.R[0] + 4, out.R[1], Math.sin(w) * 20];
      return out;
    }
    if (mode === 'wait') {   // done: hands rest either side of the glass, a little sparkle over it
      out.L = [-46, -44]; out.R = [46, -44]; V.pSpark = [30, -80, t * 40, .45 + .2 * Math.sin(t * 3)];
      return out;
    }
    const { name, p } = act;
    switch (name) {
      case 'vine': {
        const grow = seg(p, 0, .4);
        P('pVine').setAttribute('d', 'M210 -300 C260 -230 150 -210 120 -190 S70 -160 64 -150');
        P('pVine').style.strokeDasharray = 420; P('pVine').style.strokeDashoffset = 420 * (1 - grow); V.pVine = 1;
        const bp = seg(p, .1, .45), bx = lerp(210, 64, ease(bp)), by = lerp(-300, -150, ease(bp));
        const reach = seg(p, .4, .55), pour = seg(p, .55, .75);
        out.R = reach < 1 ? [lerp(60, 64, reach), lerp(-40, -140, reach)] : [lerp(64, 36, pour), lerp(-140, -124, pour)];
        V.pBottle = reach < 1 ? [bx, by - 40, 0, .7] : [out.R[0], out.R[1] - 36, -105 * pour, .7];
        if (pour > .6 && p < .97) V.pStream = [6, -100, 0, 1, 40];
        out.L = [-34, -60]; break;
      }
      case 'thyrsus': {
        const w = t * 7, tip = [6 * Math.cos(w), -34 + 2 * Math.sin(w)];
        out.R = [tip[0] + 26, tip[1] - 92]; out.L = [-34, -40]; V.pThyrsus = { tip, hand: out.R }; break;
      }
      case 'lemon': {
        const grow = seg(p, 0, .35), ripe = seg(p, .2, .55), pick = seg(p, .55, .7), sq = seg(p, .75, 1);
        P('pVine').setAttribute('d', 'M-220 -6 C-230 -80 -150 -110 -170 -150 S-130 -190 -112 -182');
        P('pVine').style.strokeDasharray = 300; P('pVine').style.strokeDashoffset = 300 * (1 - seg(p, 0, .25)); V.pVine = 1;
        const unripe = act.fruit === '#86c03a' ? '#4d7a26' : '#86a83a';
        P('pLemonBody').setAttribute('fill', ripe < 1 ? mix(unripe, act.fruit, ripe) : act.fruit);
        const lemonAt = pick < 1 ? [-112, -170] : [lerp(-112, -14, Math.min(1, sq * 2)), lerp(-170, -110, Math.min(1, sq * 2))];
        out.L = pick > 0 ? [lemonAt[0] - 4, lemonAt[1] + 8] : [-60, -40];
        V.pLemon = [lemonAt[0], lemonAt[1], 0, (.25 + .75 * grow) * (sq > .6 ? lerp(1, .7, (sq - .6) / .4) : 1)];
        if (sq > .5) V.pDrops = [lemonAt[0] + 4, lemonAt[1] + 14, (t * 60) % 40];
        break;
      }
      case 'mint': {
        const sprout = seg(p, 0, .35), reach = seg(p, .35, .55), bring = seg(p, .6, .85);
        q('#mintsprout').setAttribute('transform', `scale(${sprout})`); q('#mintsprout').style.transformOrigin = '0 -300px';
        out.R = reach < 1 ? [lerp(60, 34, reach), lerp(-40, -300, reach)] : [lerp(34, 14, bring), lerp(-300, -92, bring)];
        if (reach >= 1) V.pMint = [out.R[0], out.R[1] - 14, 0];
        break;
      }
      case 'honey': {
        // E (R8): he dips the thyrsus into the honey jar on the counter, never into the counter itself
        const J = act.honeyAt, dip = seg(p, .1, .45), lift = seg(p, .5, .8);
        const tip = dip < 1 ? [lerp(10, J[0], ease(dip)), lerp(-110, J[1], ease(dip))] : [lerp(J[0], 4, ease(lift)), lerp(J[1], -104, ease(lift))];
        const dir = [tip[0] < -60 ? 0.55 : 0.28, -1]; const dl = Math.hypot(...dir);
        out.R = [tip[0] + 96 * dir[0] / dl, tip[1] + 96 * dir[1] / dl]; out.L = [-30, -40];
        V.pThyrsus = { tip, hand: out.R };
        if (lift > .2) { const k = (t * 1.6) % 1; V.pHoneyDrip = [tip[0], tip[1] + 6 + 30 * k, 0, 1 - k * .5]; }
        break;
      }
      case 'shake': {
        const k = Math.sin(t * 16) * 16, c = [70, -214 + k];
        out.R = [c[0] + 12, c[1] + 18]; out.L = [c[0] - 18, c[1] - 22]; V.pShaker = [c[0], c[1], 25 + k * .6, .9]; break;
      }
      case 'strain': {
        const a = seg(p, 0, .3);
        out.R = [lerp(60, 44, a), lerp(-40, -150, a)]; out.L = [-30, -40];
        V.pShaker = [out.R[0] - 6, out.R[1] - 10, -100 * a, .8];
        if (a >= 1 && p < .95) V.pStream = [10, -112, 0, 1, 46, act.r.colour];
        break;
      }
      case 'ice': out.L = [-14, -150]; out.R = [60, -40]; V.pIce = p; break;
      case 'heat': V.pSteam = 1; out.L = [-40, -50]; out.R = [40, -50]; break;
      default: V.pSpark = [24, -76, t * 90, .6 + .4 * Math.sin(t * 8)]; out.L = [-40, -50]; out.R = [40, -50];
    }
    return out;
  }

  function draw(t) {
    const o = pose(t), k = RM ? 1 : .3;
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
    if (V.pStream) { const s = P('pStream'); s.setAttribute('x', V.pStream[0] - 2.5); s.setAttribute('y', V.pStream[1]); s.setAttribute('height', Math.max(0, V.pStream[4])); s.setAttribute('fill', V.pStream[5] || (act.r && act.r.colour) || '#d9a441'); }
    if (V.pThyrsus) {
      const { tip, hand: h } = V.pThyrsus, dx = h[0] - tip[0], dy = h[1] - tip[1], L = Math.hypot(dx, dy) || 1, ux = dx / L, uy = dy / L;
      const top = [h[0] + ux * 150, h[1] + uy * 150], s = P('pStaff');
      s.setAttribute('x1', tip[0]); s.setAttribute('y1', tip[1]); s.setAttribute('x2', top[0]); s.setAttribute('y2', top[1]);
      P('pCone').setAttribute('transform', `translate(${top[0]} ${top[1]}) rotate(${Math.atan2(uy, ux) * 180 / Math.PI + 90})`);
    }
    if (V.pLemon) place('pLemon', ...V.pLemon);
    if (V.pDrops) [...P('pDrops').children].forEach((c, i) => { c.setAttribute('cx', V.pDrops[0] + (i - 1.5) * 4); c.setAttribute('cy', V.pDrops[1] + ((V.pDrops[2] + i * 11) % 44)); c.setAttribute('fill', act.fruit); });
    if (V.pHoneyDrip) place('pHoneyDrip', V.pHoneyDrip[0], V.pHoneyDrip[1], 0, V.pHoneyDrip[3]);
    if (V.pShaker) place('pShaker', ...V.pShaker);
    if (V.pMint) place('pMint', ...V.pMint);
    if (V.pIce !== undefined) [...P('pIce').children].forEach((c, i) => { const s = seg(V.pIce, i * .22, i * .22 + .3); c.setAttribute('x', -18 + i * 9); c.setAttribute('y', lerp(-150, -30 - i * 6, s)); c.setAttribute('opacity', s > 0 ? .85 : 0); });
    if (V.pSpark) place('pSpark', ...V.pSpark);
    if (act.name !== 'mint' || mode !== 'step') q('#mintsprout').setAttribute('transform', 'scale(0)');
    q('#thyrsusRest').style.display = (mode === 'polish' || mode === 'story') ? '' : 'none';
    const br = RM ? 0 : Math.sin(t * 1.6);
    q('#torso').setAttribute('transform', `translate(0 ${br * 1.2}) scale(1 ${1 + br * .006})`);
    const turn = RM ? 0 : (mode === 'polish' ? Math.sin(t * .37) * .6 + Math.sin(t * .11) * .4 : -.3);
    const tilt = look ? -4 : (mode === 'polish' ? 6 : 2);
    q('#head').setAttribute('transform', `rotate(${(turn * 4).toFixed(2)} 0 -220)`);
    q('#face').setAttribute('transform', `translate(${(turn * 7).toFixed(2)} ${tilt})`);
    q('#body').setAttribute('transform', `translate(0 ${(-rise).toFixed(1)})`);
  }

  // the cheeky "glimpse": every so often he reaches up; a vine of grapes always passes in front (Q9)
  const passing = document.getElementById('passing');
  passing.innerHTML = `<g id="grapes"><path d="M0 -200 C10 -120 -10 -60 0 0" stroke="#3f7a34" stroke-width="5" fill="none"/>${[[0, 0], [-10, 10], [10, 10], [-16, 22], [0, 22], [16, 22], [-8, 34], [8, 34], [0, 46]].map(([x, y]) => `<circle cx="${x}" cy="${y}" r="10" fill="#5b2a6b"/>`).join('')}<ellipse cx="-14" cy="-10" rx="16" ry="9" fill="#3f7a34" transform="rotate(-30 -14 -10)"/></g>`;
  const grapes = document.getElementById('grapes'); grapes.style.display = 'none';
  let lookCfg = LOOK;
  function cheeky(t, dt) {
    if (lookCfg.coverage !== 'cheeky' || mode !== 'polish' || RM) { rise = lerp(rise, 0, .2); grapes.style.display = 'none'; return; }
    riseT += dt; const cyc = riseT % 9, up = cyc > 6 ? Math.sin(Math.PI * (cyc - 6) / 3) : 0; rise = 30 * up;
    grapes.style.display = up > 0 ? '' : 'none';
    if (up > 0) grapes.setAttribute('transform', `translate(${lerp(700, 900, (cyc - 6) / 3)} 620) rotate(${Math.sin(t * 3) * 8})`);
  }

  return {
    kind: 'svg', el: root,
    idle() { mode = 'polish'; act.name = 'rest'; },
    story() { mode = 'story'; },
    perform(action, ctx = {}) {
      mode = 'step'; actT = 0;
      act = { name: action, p: 0, r: ctx.r, fruit: ctx.fruit || '#f2cf2e', honeyAt: ctx.honeyAt ? [ctx.honeyAt[0] - 800, ctx.honeyAt[1] - 672] : [-160, -40] };
      if (ctx.bottle) P('pBottle').innerHTML = ctx.bottle;
      if (actDone) actDone(false);
      return new Promise(res => { actDone = res; if (RM) { act.p = .8; mode = 'wait'; actDone = null; res(true); } });
    },
    lookUp(on) { look = on ? 1 : 0; },
    setLook(L) { lookCfg = L; riseT = 0; },
    tick(t, dt) {
      if (mode === 'step' && !RM) {
        actT += dt; act.p = clamp(actT / ACT_S, 0, 1);
        if (actT >= ACT_S + .3) { mode = 'wait'; const d = actDone; actDone = null; if (d) d(true); }
      }
      cheeky(t, dt); draw(t);
    },
    get acting() { return mode === 'step'; },
    headRect() { return q('#head').getBoundingClientRect(); },
  };
}

/* ---------------------------------------------------------------- LoopDio: rendered loops (R4)
   manifest: { rect: [x, y, w, h] in world units (where the rendered frames sit),
               head: [x, y, w, h] (for the speech bubble),
               loops: { polish: { frames: ["a.webp", ...], fps: 12, hold: 8 } | { video: "polish.webm", hold: 1.6 }, ... } }
   idle (polish) and story repeat whole. A recipe step plays its loop for at least ACT_S seconds and at least
   once, then he waits for your tap: on the loop's tail from `hold` (a frame index, or seconds for video), or
   still on its first frame when hold is 0. With reduced motion every loop is a single still frame. */
function LoopDio(root) {
  const NS = 'http://www.w3.org/2000/svg', RM = reduceMotion();
  // the frames live inside #dio, so taps on him still reach the app's handler; B's figure (#body) is hidden
  const g = document.createElementNS(NS, 'g'); g.id = 'dioLoops'; root.appendChild(g);
  const OX = 800, OY = 672;   // #dio's own translate
  let M = null, cur = null, f = 0, ft = 0, actT = 0, done = null, ready = false, imgEl = null, vid = null, waiting = false;
  const cache = {};
  function preload(src) { if (cache[src]) return cache[src]; const im = new Image(); im.src = src; cache[src] = im.decode().catch(() => {}); return cache[src]; }
  function show(src) { if (imgEl) imgEl.setAttribute('href', src); }
  function set(name, oneShot) {
    if (!M || !M.loops[name]) name = 'polish';
    if (!M || !M.loops[name]) return;
    cur = { name, L: M.loops[name], oneShot }; f = 0; ft = 0; actT = 0; waiting = false;
    const [x, y, w, h] = M.rect;
    if (cur.L.video) {
      g.innerHTML = '';
      const fo = document.createElementNS(NS, 'foreignObject'); fo.setAttribute('x', x - OX); fo.setAttribute('y', y - OY); fo.setAttribute('width', w); fo.setAttribute('height', h);
      vid = document.createElement('video'); vid.src = cur.L.video; vid.muted = true; vid.playsInline = true; vid.autoplay = !RM; vid.style.cssText = 'width:100%;height:100%';
      vid.onended = () => { vid.currentTime = cur.L.hold || 0; vid.play(); finish(); };
      fo.appendChild(vid); g.appendChild(fo); imgEl = null;
    } else {
      if (!imgEl || !imgEl.isConnected) {
        g.innerHTML = ''; imgEl = document.createElementNS(NS, 'image');
        imgEl.setAttribute('x', x - OX); imgEl.setAttribute('y', y - OY); imgEl.setAttribute('width', w); imgEl.setAttribute('height', h);
        imgEl.setAttribute('preserveAspectRatio', 'none'); imgEl.setAttribute('pointer-events', 'none'); g.appendChild(imgEl); vid = null;
        // taps land on his shape, not on the frame's transparent box (which would cover the shelf behind him)
        const hd = M.head, hit = document.createElementNS(NS, 'path');
        const hx = hd[0] + hd[2] / 2 - OX, hy = hd[1] - OY;
        hit.setAttribute('d', `M${hx - hd[2] / 2} ${hy + hd[3] * .45} a${hd[2] / 2} ${hd[3] * .45} 0 1 1 ${hd[2]} 0 L${hx + 115} ${hy + hd[3] * 1.05} L${hx + 120} ${y + h - OY} L${hx - 120} ${y + h - OY} L${hx - 115} ${hy + hd[3] * 1.05} Z`);
        hit.setAttribute('fill', 'transparent'); g.appendChild(hit);
      }
      cur.L.frames.forEach(preload);
      f = RM ? Math.min(cur.L.hold || Math.floor(cur.L.frames.length / 2), cur.L.frames.length - 1) : 0;
      show(cur.L.frames[f]);
    }
  }
  function finish() { if (done) { const d = done; done = null; d(true); } }
  const self = {
    kind: 'loops', el: g,
    load(m) {
      M = m; const first = Object.values(m.loops).map(L => L.frames ? L.frames[0] : null).filter(Boolean);
      return Promise.all(first.map(preload)).then(() => {
        ready = true; const b = root.querySelector('#body'); if (b) b.style.display = 'none';
        set('polish');
        Object.values(m.loops).forEach(L => (L.frames || []).forEach(preload));
      });
    },
    copyState() {},
    fail() { g.remove(); },
    idle() { set('polish'); }, story() { set('story'); },
    perform(action, ctx) {
      if (done) { const d = done; done = null; d(false); }
      if (!ready) return Promise.resolve(true);
      set(LOOP_OF[action] || 'reach', true);
      if (RM) return Promise.resolve(true);
      return new Promise(res => { done = res; });
    },
    lookUp() {}, setLook() {},
    tick(t, dt) {
      if (!cur || !imgEl || RM) return;
      const fr = cur.L.frames, fps = cur.L.fps || 12;
      if (cur.oneShot) actT += dt;
      if (waiting && !cur.L.hold) return;              // waiting for your tap, still
      ft += dt; if (ft < 1 / fps) return; ft = 0; f++;
      if (f >= fr.length) {
        if (cur.oneShot && actT >= ACT_S) { waiting = true; finish(); f = cur.L.hold || 0; }
        else f = waiting ? (cur.L.hold || 0) : 0;
      }
      show(fr[Math.min(f, fr.length - 1)]);
    },
    get acting() { return !!done; },
    headRect() {
      if (!M || !M.head) return root.getBoundingClientRect();
      const svg = root.ownerSVGElement, pt = svg.createSVGPoint(), m = svg.getScreenCTM();
      const [x, y, w, h] = M.head; pt.x = x; pt.y = y; const a = pt.matrixTransform(m); pt.x = x + w; pt.y = y + h; const b = pt.matrixTransform(m);
      return { left: a.x, top: a.y, right: b.x, bottom: b.y, width: b.x - a.x, height: b.y - a.y };
    },
  };
  return self;
}
