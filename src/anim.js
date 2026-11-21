/* Step animations: each one copies a working bartender's own movement for that step.
   Drawn in a 96 x 96 box. Lines in --ink, liquid in the drink's own colour.
   Studied from frame-by-frame references: the shake is a big arc over the shoulder, the stir runs the
   spoon's back round the inside wall (behind the ice, then in front) while the ice turns as one,
   a double strain pools in a hand-held cone and leaves as one thin stream. */
const LN = 'fill="none" stroke="var(--ink)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"';
const HAIR = 'fill="none" stroke="var(--ink)" stroke-width="1" stroke-linecap="round" opacity=".55"';
const TIN = (x, y, h = 52, w = 30) => `<path d="M${x} ${y} L${x + w} ${y} L${x + w - 5} ${y + h} L${x + 5} ${y + h} Z" ${LN}/>`;
const ROCKS = (x, y) => `<path d="M${x} ${y} L${x + 3} ${y + 30} Q${x + 3.5} ${y + 33} ${x + 7} ${y + 33} L${x + 33} ${y + 33} Q${x + 36.5} ${y + 33} ${x + 37} ${y + 30} L${x + 40} ${y}" ${LN}/>`;
const CUBE = (x, y, s = 10) => `<rect x="${x}" y="${y}" width="${s}" height="${s}" rx="2.4" fill="#eef6f8" fill-opacity=".38" stroke="#eef6f8" stroke-width="1.2" stroke-opacity=".8"/>`;
const ROCK_ICE = (x, y, s = 22) => `<rect x="${x}" y="${y}" width="${s}" height="${s}" rx="5" fill="#eef6f8" fill-opacity=".45" stroke="#eef6f8" stroke-width="1.5"/>`;
const JIGGER = `<path d="M-9 -16 L9 -16 L2 0 L9 16 L-9 16 L-2 0 Z" ${LN}/>`;
const SPOUT_BOTTLE = (c) => `<path d="M-7 -22 h14 v30 a4 4 0 0 1 -4 4 h-6 a4 4 0 0 1 -4 -4 Z" fill="${c}" opacity=".85"/><path d="M-7 -22 h14 v30 a4 4 0 0 1 -4 4 h-6 a4 4 0 0 1 -4 -4 Z" ${LN}/><path d="M-3 -22 v-6 l7 -5" ${LN}/>`;
const WHISKY_BOTTLE = (c) => `<path d="M-4 -30 h8 v8 q0 3 5 6 q5 3 5 9 v28 a3 3 0 0 1 -3 3 h-22 a3 3 0 0 1 -3 -3 v-28 q0 -6 5 -9 q5 -3 5 -6 Z" fill="${c}" opacity=".9"/><path d="M-4 -30 h8 v8 q0 3 5 6 q5 3 5 9 v28 a3 3 0 0 1 -3 3 h-22 a3 3 0 0 1 -3 -3 v-28 q0 -6 5 -9 q5 -3 5 -6 Z" ${LN}/>`;
const JAR = (c) => `<path d="M-11 -14 h22 v22 a5 5 0 0 1 -5 5 h-12 a5 5 0 0 1 -5 -5 Z" fill="${c}" opacity=".9"/><path d="M-11 -14 h22 v22 a5 5 0 0 1 -5 5 h-12 a5 5 0 0 1 -5 -5 Z M-8 -14 v-4 h16 v4" ${LN}/>`;
/* A mixing glass: straight sides, a pouring spout, cut facets low down */
const MIXGLASS = `<path d="M26 28 V84 Q26 89 31 89 H65 Q70 89 70 84 V28" ${LN}/><path d="M70 28 L76 23" ${LN}/><path d="M28 74 L36 86 L44 74 L52 86 L60 74 L68 86" ${HAIR}/>`;
/* The glass a drink lands in, with a fill that rises (class "rise") */
function target(glass, colour, x0 = 0, y0 = 0) {
  if (glass === 'coupe' || glass === 'martini') {
    const bowl = glass === 'coupe' ? `M${x0 + 24} ${y0 + 62} Q${x0 + 48} ${y0 + 92} ${x0 + 72} ${y0 + 62} Z` : `M${x0 + 24} ${y0 + 60} L${x0 + 48} ${y0 + 82} L${x0 + 72} ${y0 + 60} Z`;
    return `<clipPath id="tg"><path d="${bowl}"/></clipPath><g clip-path="url(#tg)"><rect class="rise" x="${x0 + 20}" y="${y0 + 60}" width="56" height="34" fill="${colour}"/></g>
      <path d="${bowl}" ${LN}/><path d="M${x0 + 48} ${y0 + (glass === 'coupe' ? 77 : 82)} V${y0 + 92} M${x0 + 38} ${y0 + 94} H${x0 + 58}" ${LN}/>`;
  }
  return `<clipPath id="tg"><path d="M${x0 + 30} ${y0 + 62} L${x0 + 33} ${y0 + 92} L${x0 + 63} ${y0 + 92} L${x0 + 66} ${y0 + 62} Z"/></clipPath>
    <g clip-path="url(#tg)"><rect class="rise" x="${x0 + 28}" y="${y0 + 62}" width="40" height="32" fill="${colour}"/>${ROCK_ICE(x0 + 38, y0 + 70, 20)}</g>${ROCKS(x0 + 28, y0 + 60)}`;
}

/* Pour from a bottle into the jigger, then tip the jigger into the tin. */
/* How a bartender measures: the jigger is held level just above the tin's mouth; the bottle tips into
   its top cup; then a flick of the wrist turns the jigger over about its waist and the measure drops
   straight into the tin. Syrup runs slower and thicker. */
const JIG_CUP = 'M-9 -13 L9 -13 L2 0 L-2 0 Z';
const JIG = `<path d="M-9 -13 L9 -13 L2 0 L9 13 L-9 13 L-2 0 Z" ${LN}/>`;
const TINFILL = `<clipPath id="tf"><path d="M40 56 L72 56 L68 90 L44 90 Z"/></clipPath><g clip-path="url(#tf)"><rect class="p2-tin" x="38" y="70" width="36" height="22" fill="currentColor" opacity=".55"/></g>`;
function pourTwoStage(bottleFn, colour, cls = '', bx = 16, by = 36) {
  const w = cls === 'syrup' ? 3.4 : 2.2;
  return `<g class="p2 ${cls}" style="color:${colour}">
    ${TINFILL}${TIN(40, 56, 34, 32)}
    <rect class="p2-stream2" x="${61 - w / 2}" y="48" width="${w}" height="${cls === 'syrup' ? 18 : 22}" rx="${w / 2}" fill="${colour}"/>
    <g class="p2-jig"><g transform="translate(50 42)">
      <clipPath id="jc"><path d="${JIG_CUP}"/></clipPath>
      <g clip-path="url(#jc)"><rect class="p2-jfill" x="-10" y="-13" width="20" height="13" fill="${colour}"/></g>${JIG}</g></g>
    <rect class="p2-stream1" x="${47 - w / 2}" y="22" width="${w}" height="9" rx="${w / 2}" fill="${colour}"/>
    <g class="p2-bottle" style="transform-origin:${bx}px ${by}px"><g transform="translate(${bx} ${by})">${bottleFn(colour)}</g></g>
  </g>`;
}

let ACTN = 0;
function act(a, colour = '#d9a441', o = {}) {
  let b = '';
  const u = ++ACTN, glass = o.glass || 'rocks';
  switch (a) {
    case 'pour-spirit': b = pourTwoStage(WHISKY_BOTTLE, colour, '', 18, 34); break;
    case 'pour-citrus': b = pourTwoStage(SPOUT_BOTTLE, '#f2d24a', '', 16, 36); break;
    case 'pour-syrup': b = pourTwoStage(SPOUT_BOTTLE, '#e0a224', 'syrup', 16, 36); break;
    /* A measure already in the jigger, turned over into the tin */
    case 'pour': b = pourTwoStage(() => '', colour, 'tiponly'); break;
    case 'muddle': b = `${TIN(30, 30, 58, 36)}
      <g class="coins"><ellipse cx="41" cy="82" rx="6" ry="3" fill="#e6c27a"/><ellipse cx="51" cy="83" rx="6" ry="3" fill="#e6c27a"/><ellipse cx="56" cy="79" rx="5" ry="2.6" fill="#d9b060"/></g>
      <g class="muddler"><rect x="44" y="8" width="8" height="58" rx="4" fill="#9a6a3a"/><rect x="42" y="62" width="12" height="10" rx="3" fill="#7d5530"/></g>`; break;
    /* Ice in, then the small tin goes in upside-down at an angle and gets a firm tap to seal */
    case 'seal': b = `${TIN(16, 40, 50, 34)}
      <g class="seal-ice">${CUBE(22, 70)}${CUBE(34, 74)}${CUBE(27, 58)}</g>
      <g class="seal-tin"><path d="M20 44 L46 40 L42 4 L22 8 Z" ${LN}/></g>
      <path class="seal-tap" d="M60 30 l8 -4 M62 38 l9 0" ${LN} stroke-width="2"/>`; break;
    /* A big arc over the shoulder: the joined tins travel the arc and the ice slams end to end */
    case 'shake': b = `<path d="M14 74 Q48 6 84 30" fill="none" stroke="var(--ink)" stroke-width="1.2" stroke-dasharray="2 5" opacity=".35"/>
      <g class="shaker"><g transform="rotate(-30 48 50)">
        <path d="M18 42 L58 39 L58 61 L18 58 Z" ${LN}/><path d="M52 41 L80 43.5 L80 56.5 L52 59 Z" ${LN}/>
        <g class="slam">${CUBE(24, 45, 8)}${CUBE(34, 48, 8)}</g></g></g>`; break;
    /* The spoon's back runs round the inside wall: behind the ice, then in front; the ice turns with it */
    case 'stir': b = `${MIXGLASS}<rect x="28" y="62" width="40" height="25" fill="${colour}" opacity=".6"/>
      <g class="spoon-b"><path d="M48 4 V78" stroke="var(--ink)" stroke-width="2" opacity=".45"/><ellipse cx="48" cy="80" rx="3.4" ry="2" fill="var(--ink)" opacity=".45"/></g>
      <g class="icespin">${CUBE(33, 44, 12)}${CUBE(48, 40, 12)}${CUBE(41, 54, 12)}</g>
      <g class="spoon-f"><path d="M48 4 V78" stroke="var(--ink)" stroke-width="2.2" stroke-linecap="round"/><path d="M48 10 q-3 3 0 6 q3 3 0 6 q-3 3 0 6 q3 3 0 6" ${LN} stroke-width="1.3"/><ellipse cx="48" cy="80" rx="3.4" ry="2" fill="var(--ink)"/></g>`; break;
    case 'ice': b = `${ROCKS(28, 50)}<g class="dropice">${ROCK_ICE(37, 56, 22)}</g>`; break;
    case 'build': b = `${ROCKS(28, 50)}<g class="dropice">${ROCK_ICE(34, 58, 12)}</g><g class="dropice d2">${ROCK_ICE(48, 64, 12)}</g>`; break;
    /* The tin pours through its strainer into a hand-held cone; the cone pools, one thin stream leaves it */
    case 'double-strain': b = `<g transform="rotate(-118 70 18)"><path d="M60 4 L82 4 L79 34 L63 34 Z" ${LN}/><path d="M58 4 q13 -6 26 0" ${LN} stroke-width="1.6"/></g>
      <rect class="ds-in" x="57" y="16" width="2.6" height="20" rx="1.3" fill="${colour}"/>
      <clipPath id="cone"><path d="M36 34 L64 34 L50 52 Z"/></clipPath><g clip-path="url(#cone)"><rect class="pool" x="34" y="34" width="32" height="20" fill="${colour}"/></g>
      <path d="M36 34 L64 34 L50 52 Z" ${LN}/><path d="M40 38 L60 38 M43 42 L57 42 M46 46 L54 46" ${HAIR}/><path d="M36 34 L14 30" ${LN}/>
      <rect class="ds-out" x="49" y="52" width="2" height="12" rx="1" fill="${colour}"/>${target(glass, colour, 0, 2)}`; break;
    /* Stirred drinks: the mixing glass tips over the glass and pours a thin stream from its spout */
    case 'strain-glass': b = `<g class="tilt"><g transform="rotate(-52 34 30)" >
      <path d="M14 8 V42 Q14 46 18 46 H44 Q48 46 48 42 V8" ${LN}/><path d="M48 8 L53 4" ${LN}/>${CUBE(19, 22, 9)}${CUBE(30, 18, 9)}<path d="M12 8 h38" ${LN} stroke-width="1.4"/></g></g>
      <rect class="sg-stream" x="53" y="26" width="2" height="34" rx="1" fill="${colour}"/>${target(glass, colour, 6, 0)}`; break;
    case 'strain': b = `<g transform="rotate(-50 52 24)"><path d="M42 6 L64 6 L61 40 L45 40 Z" ${LN}/><path d="M41 40 q12 6 24 0" ${LN} stroke-width="1.8"/></g>
      <rect class="ds-out" x="40" y="40" width="2.4" height="22" fill="${colour}"/>${target(glass, colour, -8, 0)}`; break;
    case 'float': b = `${ROCKS(28, 50)}<rect x="32" y="62" width="32" height="19" fill="${colour}"/><rect class="layer" x="32" y="58" width="32" height="5" fill="#8a5a22"/>
      <g transform="rotate(-25 50 44)"><path d="M50 8 L50 42" stroke="var(--ink)" stroke-width="2" stroke-linecap="round"/><path d="M45 44 q5 -6 10 0" ${LN}/></g>
      <rect class="fl-stream" x="49" y="22" width="2" height="18" fill="#8a5a22"/>`; break;
    case 'top': b = `<path d="M30 20 L33 90 L63 90 L66 20" ${LN}/><rect x="32" y="40" width="32" height="48" fill="${colour}" opacity=".6"/>
      ${[38, 46, 54, 58].map((x, n) => `<circle class="bub" style="animation-delay:${n * .35}s" cx="${x}" cy="84" r="${1.6 + n % 2}" fill="#fff" opacity=".8"/>`).join('')}`; break;
    case 'garnish': b = `${ROCKS(28, 50)}<rect x="32" y="62" width="32" height="19" fill="${colour}"/><g class="drop-garn"><circle cx="48" cy="56" r="6" fill="#9b1020"/><path d="M48 50 q2 -10 10 -14" ${LN} stroke-width="1.6"/></g>`; break;
    case 'express': b = `${ROCKS(28, 54)}<rect x="32" y="66" width="32" height="19" fill="${colour}"/><g class="peel"><path d="M34 26 q14 -10 28 0 q-14 8 -28 0 Z" fill="#ef8a22"/></g>
      ${[40, 48, 56].map((x, n) => `<circle class="mist" style="animation-delay:${n * .15}s" cx="${x}" cy="36" r="1.4" fill="#ef8a22"/>`).join('')}`; break;
    case 'heat': b = `<path d="M28 34 L31 88 L63 88 L66 34 M65 46 q14 0 14 14 q0 14 -14 16" ${LN}/>${[40, 54].map((x, n) => `<path class="steam" style="animation-delay:${n * 1.1}s" d="M${x} 28 q-5 -6 0 -12 q5 -6 0 -12" ${LN} stroke-width="1.8"/>`).join('')}`; break;
    default: b = ROCKS(28, 50);
  }
  b = b.replace(/id="([\w-]+)"/g, (m, i) => `id="${i}_${u}"`).replace(/url\(#([\w-]+)\)/g, (m, i) => i === 'gold' ? m : `url(#${i}_${u})`);
  return `<svg class="act a-${a}" viewBox="0 0 96 96" aria-hidden="true">${b}</svg>`;
}
