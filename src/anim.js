/* Step animations: each one shows the bartender's own movement for that step.
   Drawn in a 96 x 96 box. Lines in --ink, liquid in the drink's own colour.
   Nothing spins on the spot: things move the way a hand moves them. */
const LN = 'fill="none" stroke="var(--ink)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"';
const TIN = (x, y, h = 52, w = 30) => `<path d="M${x} ${y} L${x + w} ${y} L${x + w - 5} ${y + h} L${x + 5} ${y + h} Z" ${LN}/>`;
const ROCKS = (x, y) => `<path d="M${x} ${y} L${x + 3} ${y + 30} Q${x + 3.5} ${y + 33} ${x + 7} ${y + 33} L${x + 33} ${y + 33} Q${x + 36.5} ${y + 33} ${x + 37} ${y + 30} L${x + 40} ${y}" ${LN}/>`;
const JIGGER = `<path d="M-9 -16 L9 -16 L2 0 L9 16 L-9 16 L-2 0 Z" ${LN}/>`;
const SPOUT_BOTTLE = (c) => `<path d="M-7 -22 h14 v30 a4 4 0 0 1 -4 4 h-6 a4 4 0 0 1 -4 -4 Z" fill="${c}" opacity=".85"/><path d="M-7 -22 h14 v30 a4 4 0 0 1 -4 4 h-6 a4 4 0 0 1 -4 -4 Z" ${LN}/><path d="M-3 -22 v-6 l7 -5" ${LN}/>`;
const WHISKY_BOTTLE = (c) => `<path d="M-4 -30 h8 v8 q0 3 5 6 q5 3 5 9 v28 a3 3 0 0 1 -3 3 h-22 a3 3 0 0 1 -3 -3 v-28 q0 -6 5 -9 q5 -3 5 -6 Z" fill="${c}" opacity=".9"/><path d="M-4 -30 h8 v8 q0 3 5 6 q5 3 5 9 v28 a3 3 0 0 1 -3 3 h-22 a3 3 0 0 1 -3 -3 v-28 q0 -6 5 -9 q5 -3 5 -6 Z" ${LN}/>`;
const JAR = (c) => `<path d="M-11 -14 h22 v22 a5 5 0 0 1 -5 5 h-12 a5 5 0 0 1 -5 -5 Z" fill="${c}" opacity=".9"/><path d="M-11 -14 h22 v22 a5 5 0 0 1 -5 5 h-12 a5 5 0 0 1 -5 -5 Z M-8 -14 v-4 h16 v4" ${LN}/>`;
const ROCK_ICE = (x, y, s = 22) => `<rect x="${x}" y="${y}" width="${s}" height="${s}" rx="5" fill="#eef6f8" opacity=".55" stroke="#eef6f8" stroke-width="1.5"/>`;

/* Pour from a bottle into the jigger, then tip the jigger into the tin.
   bottleFn draws the bottle centred at 0,0; colour is the liquid. */
function pourTwoStage(bottleFn, colour, cls = '') {
  return `<g class="p2 ${cls}">
    <g class="p2-bottle">${bottleFn(colour)}</g>
    <rect class="p2-stream1" x="37" y="21" width="${cls === 'syrup' ? 4 : 2.4}" height="10" rx="1.2" fill="${colour}"/>
    <g class="p2-jig"><g transform="translate(38 46)">
      <clipPath id="jc"><path d="M-9 -16 L9 -16 L2 0 L-2 0 Z"/></clipPath>
      <rect class="p2-jfill" x="-10" y="-16" width="20" height="16" fill="${colour}" clip-path="url(#jc)"/>
      ${JIGGER}</g></g>
    <rect class="p2-stream2" x="58" y="50" width="${cls === 'syrup' ? 4 : 2.4}" height="16" rx="1.2" fill="${colour}"/>
    ${TIN(56, 40, 48, 30)}
  </g>`;
}

let ACTN = 0;
function act(a, colour = '#d9a441') {
  let b = '';
  const u = ++ACTN;
  switch (a) {
    case 'pour-spirit': b = pourTwoStage(c => `<g transform="translate(12 34)">${WHISKY_BOTTLE(c)}</g>`, colour); break;
    case 'pour-citrus': b = pourTwoStage(c => `<g transform="translate(12 36)">${SPOUT_BOTTLE(c)}</g>`, '#f2d24a'); break;
    case 'pour-syrup': b = pourTwoStage(c => `<g transform="translate(14 40)">${JAR(c)}</g>`, '#e0a224', 'syrup'); break;
    case 'pour': b = `<g class="tip"><g transform="translate(30 30)"><clipPath id="jg"><path d="M-9 -16 L9 -16 L2 0 L-2 0 Z"/></clipPath><rect class="tip-fill" x="-10" y="-16" width="20" height="16" fill="${colour}" clip-path="url(#jg)"/>${JIGGER}</g></g>
      <rect class="tip-stream" x="47" y="40" width="2.4" height="22" rx="1.2" fill="${colour}"/>${TIN(36, 44, 44, 30)}`; break;
    case 'muddle': b = `${TIN(30, 30, 58, 36)}
      <g class="coins"><ellipse cx="41" cy="82" rx="6" ry="3" fill="#e6c27a"/><ellipse cx="51" cy="83" rx="6" ry="3" fill="#e6c27a"/><ellipse cx="56" cy="79" rx="5" ry="2.6" fill="#d9b060"/></g>
      <g class="muddler"><rect x="44" y="8" width="8" height="58" rx="4" fill="#9a6a3a"/><rect x="42" y="62" width="12" height="10" rx="3" fill="#7d5530"/></g>`; break;
    case 'shake': b = `<g class="shaker"><path d="M36 16 L60 16 L57 50 L39 50 Z" ${LN}/><path d="M34 50 L62 50 L58 88 L38 88 Z" ${LN}/>
      <rect class="cube c1" x="42" y="62" width="7" height="7" rx="1.5" fill="#eef6f8" opacity=".7"/><rect class="cube c2" x="50" y="70" width="7" height="7" rx="1.5" fill="#eef6f8" opacity=".7"/></g>
      <path class="rattle" d="M20 30 l-6 -4 M18 44 l-8 0 M76 64 l8 0 M74 78 l6 4" ${LN} stroke-width="2"/>`; break;
    case 'stir': b = `<path d="M26 34 L70 34 L66 86 L30 86 Z" ${LN}/><rect x="31" y="56" width="34" height="28" fill="${colour}" opacity=".55"/>
      <g class="stirspoon"><path d="M50 8 L50 76" stroke="var(--ink)" stroke-width="2.2" stroke-linecap="round"/><path d="M50 14 q-3 3 0 6 q3 3 0 6 q-3 3 0 6 q3 3 0 6" ${LN} stroke-width="1.4"/><ellipse cx="50" cy="78" rx="3.5" ry="2.2" fill="var(--ink)"/></g>`; break;
    case 'ice': b = `${ROCKS(28, 50)}<g class="dropice">${ROCK_ICE(37, 56, 22)}</g>`; break;
    case 'build': b = `${ROCKS(28, 50)}<g class="dropice">${ROCK_ICE(34, 58, 12)}</g><g class="dropice d2">${ROCK_ICE(48, 64, 12)}</g>`; break;
    case 'double-strain': b = `<g transform="rotate(-38 58 26)"><path d="M48 6 L72 6 L69 40 L51 40 Z" ${LN}/><path d="M47 40 q13 6 26 0" ${LN} stroke-width="1.8"/><path d="M49 43 q2 3 4 0 q2 3 4 0 q2 3 4 0 q2 3 4 0 q2 3 4 0" ${LN} stroke-width="1.2"/></g>
      <rect class="ds-stream" x="49" y="38" width="2.4" height="12" fill="${colour}"/>
      <path d="M38 50 L62 50 L50 66 Z" ${LN}/><path d="M42 54 L58 54 M45 58 L55 58" stroke="var(--ink)" stroke-width="1" opacity=".6"/>
      <circle class="drip dd1" cx="50" cy="68" r="1.8" fill="${colour}"/><circle class="drip dd2" cx="50" cy="68" r="1.8" fill="${colour}"/>
      <clipPath id="dsg"><path d="M30 64 L33 92 L67 92 L70 64 Z"/></clipPath>
      <g clip-path="url(#dsg)"><rect class="ds-fill" x="28" y="64" width="44" height="30" fill="${colour}"/>${ROCK_ICE(41, 72, 18)}</g>${ROCKS(30, 62)}`; break;
    case 'float': b = `${ROCKS(28, 50)}<rect x="32" y="62" width="32" height="19" fill="${colour}"/><rect class="layer" x="32" y="58" width="32" height="5" fill="#8a5a22"/>
      <g transform="rotate(-25 50 44)"><path d="M50 8 L50 42" stroke="var(--ink)" stroke-width="2" stroke-linecap="round"/><path d="M45 44 q5 -6 10 0" ${LN}/></g>
      <rect class="fl-stream" x="49" y="22" width="2" height="18" fill="#8a5a22"/>`; break;
    case 'strain': b = `<g transform="rotate(-50 52 24)"><path d="M42 6 L64 6 L61 40 L45 40 Z" ${LN}/><path d="M41 40 q12 6 24 0" ${LN} stroke-width="1.8"/></g>
      <rect class="ds-stream" x="40" y="40" width="2.4" height="26" fill="${colour}"/><clipPath id="stg"><path d="M28 60 L31 90 L65 90 L68 60 Z"/></clipPath><g clip-path="url(#stg)"><rect class="ds-fill" x="26" y="60" width="44" height="32" fill="${colour}"/></g>${ROCKS(28, 58)}`; break;
    case 'top': b = `<path d="M30 20 L33 90 L63 90 L66 20" ${LN}/><rect x="32" y="40" width="32" height="48" fill="${colour}" opacity=".6"/>
      ${[38, 46, 54, 58].map((x, n) => `<circle class="bub" style="animation-delay:${n * .35}s" cx="${x}" cy="84" r="${1.6 + n % 2}" fill="#fff" opacity=".8"/>`).join('')}`; break;
    case 'garnish': b = `${ROCKS(28, 50)}<rect x="32" y="62" width="32" height="19" fill="${colour}"/><g class="drop-garn"><circle cx="48" cy="56" r="6" fill="#9b1020"/><path d="M48 50 q2 -10 10 -14" ${LN} stroke-width="1.6"/></g>`; break;
    case 'express': b = `${ROCKS(28, 54)}<rect x="32" y="66" width="32" height="19" fill="${colour}"/><g class="peel"><path d="M34 26 q14 -10 28 0 q-14 8 -28 0 Z" fill="#ef8a22"/></g>
      ${[40, 48, 56].map((x, n) => `<circle class="mist" style="animation-delay:${n * .15}s" cx="${x}" cy="36" r="1.4" fill="#ef8a22"/>`).join('')}`; break;
    case 'heat': b = `<path d="M28 34 L31 88 L63 88 L66 34 M65 46 q14 0 14 14 q0 14 -14 16" ${LN}/>${[40, 54].map((x, n) => `<path class="steam" style="animation-delay:${n * 1.1}s" d="M${x} 28 q-5 -6 0 -12 q5 -6 0 -12" ${LN} stroke-width="1.8"/>`).join('')}`; break;
    default: b = ROCKS(28, 50);
  }
  b = b.replace(/(id="|url\(#)(jc|jg|dsg|stg)/g, `$1$2_${u}`);
  return `<svg class="act a-${a}" viewBox="0 0 96 96" aria-hidden="true">${b}</svg>`;
}
