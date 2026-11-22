/* Shared prototype logic (copied identically into each prototype folder, so each one stands alone).
   Uses the globals from data.js (R, RB, ING, STAPLE), stories.js (STORY) and inventory.js (INVENTORY).
   Words follow CONTEXT.md: Bottle, Style, Family, Feel, Moment, Strength, Barman's choice. */

/* ---------- The four Feels (shared by the menu and by Dionysus) ---------- */
const FEELS = { rich: 'Sweet and rich', sharp: 'Sharp and fresh', bitter: 'Bitter', dry: 'Dry and boozy' };
const FEEL_OF = { sweet: 'rich', decadent: 'rich', fresh: 'sharp', balanced: 'sharp', bitter: 'bitter', strong: 'dry' };
const feelOf = r => FEEL_OF[r.feel];

/* ---------- Families, for browsing by spirit ---------- */
const FAMILIES = { whisky: 'Whisky', gin: 'Gin', rum: 'Rum', tequila: 'Tequila', vodka: 'Vodka', brandy: 'Brandy', aperitif: 'Aperitifs' };

/* ---------- Moments ---------- */
const MOMENTS = { before: 'Before dinner', food: 'With food', after: 'After dinner', any: 'Just because' };
function momentsOf(r) {
  const m = new Set(['any']);
  if (r.feel === 'bitter' || r.spirit === 'aperitif' || ['martini', 'gimlet', 'daiquiri', 'margarita', 'sidecar'].includes(r.id)) m.add('before');
  if (/long|light|fizzy/.test(r.tags)) m.add('food');
  if (r.feel === 'decadent' || r.feel === 'sweet' || r.feel === 'strong' || /after dinner/.test(r.tags)) m.add('after');
  return m;
}
/* "Warm me up": hot drinks first, then winter warmers */
const isWarm = r => r.steps.some(s => s[0] === 'heat') || /warm|hot/.test(r.tags) || (r.season.includes('winter') && !r.season.includes('summer') && r.feel !== 'fresh');

/* ---------- Strength: from the alcohol in the glass ---------- */
const ABV = { spirit: .4, liqueur: .25, wine: .16, bitters: .45 };
function pureMl(r) {
  return r.ing.reduce((a, x) => { const k = (ING[x.k] || [])[1]; return a + (ABV[k] && /ml/.test(x.u) ? x.q * ABV[k] : 0); }, 0);
}
const STRENGTHS = { none: 'None', low: 'Low', regular: 'Regular', strong: 'Strong' };
function strengthOf(r) { const p = pureMl(r); if (p === 0) return 'none'; if (/low/.test(r.tags) || p < 13) return 'low'; if (p >= 24) return 'strong'; return 'regular'; }

/* ---------- Your bar ---------- */
const BARWARE = { shaker: 'Shaker tin', strainer: 'Strainer', jigger: 'Jigger', spoon: 'Bar spoon', mixing: 'Mixing glass', muddler: 'Muddler' };
/* Q12: never hide a drink for a tool. Offer a swap instead. */
const SWAP = { shaker: 'a jam jar with a tight lid', strainer: 'a tea strainer', jigger: 'an egg cup (about 30 ml)', spoon: 'a chopstick', mixing: 'a pint glass', muddler: 'the end of a rolling pin' };
function barwareFor(r) {
  const need = new Set(['jigger']);
  r.steps.forEach(([t]) => {
    if (t === 'shake') need.add('shaker');
    if (t === 'stir') { need.add('mixing'); need.add('spoon'); }
    if (t === 'strain') need.add('strainer');
    if (t === 'muddle') need.add('muddler');
    if (t === 'float') need.add('spoon');
  });
  return [...need];
}

/* The shelf starts threadbare: two dusty Bottles. */
const BAR = {
  have: new Set(['bourbon', 'sweet vermouth']),
  barware: new Set(),
  filled: false,
};
const isBottle = k => ['spirit', 'wine', 'liqueur', 'bitters', 'mixer'].includes((ING[k] || [])[1]);
const shelfBottles = () => [...BAR.have].filter(isBottle).map(k => ({ k, style: ING[k][0], kind: ING[k][1], colour: ING[k][2], family: ING[k][3] }))
  .sort((a, b) => ORDER.indexOf(a.family) - ORDER.indexOf(b.family));
const ORDER = ['whisky', 'gin', 'vodka', 'rum', 'tequila', 'brandy', 'aperitif', 'bitters', 'mixer'];

function missingFor(r) { // ingredients you lack (no swap held)
  return r.ing.filter(x => !x.o && !STAPLE.has(x.k) && !BAR.have.has(x.k) && !x.subs.some(s => BAR.have.has(s)));
}
const canMake = r => missingFor(r).length === 0;
function swapsFor(r) { return barwareFor(r).filter(b => !BAR.barware.has(b)).map(b => ({ tool: BARWARE[b], use: SWAP[b] })); }

/* The pretend photo step: what "reading" each sample photo finds. */
const PHOTOS = [
  { id: 'cupboard', name: 'Drinks cupboard', finds: INVENTORY.have.filter(k => ['spirit', 'liqueur'].includes(ING[k][1])), tools: [] },
  { id: 'fridge', name: 'Fridge door', finds: INVENTORY.have.filter(k => ['wine', 'mixer', 'bitters'].includes(ING[k][1]) || ['egg white', 'cocktail cherries'].includes(k)), tools: [] },
  { id: 'bowl', name: 'Fruit bowl', finds: INVENTORY.have.filter(k => ['fruit', 'herb', 'sweet', 'other'].includes(ING[k][1]) && !['egg white', 'cocktail cherries'].includes(k)), tools: [] },
  { id: 'drawer', name: 'Tools drawer', finds: [], tools: ['shaker', 'strainer', 'jigger', 'spoon'] },
];
function readPhotos(ids) {
  const found = new Set(), tools = new Set();
  PHOTOS.filter(p => ids.includes(p.id)).forEach(p => { p.finds.forEach(k => found.add(k)); p.tools.forEach(t => tools.add(t)); });
  return { found: [...found], tools: [...tools] };
}
function applyReading(res, toolsTicked) {
  res.found.forEach(k => BAR.have.add(k));
  BAR.barware = new Set(toolsTicked);
  BAR.filled = true;
}

/* ---------- Barman's choice ---------- */
function barmansChoice(exceptId) {
  let pool = R.filter(canMake);
  if (pool.length < 3) pool = R; // threadbare shelf: he picks from everything and offers swaps
  pool = pool.filter(r => r.id !== exceptId);
  return pool[Math.floor(Math.random() * pool.length)];
}

/* ---------- Talking to Dionysus ---------- */
const QUESTIONS = [
  { k: 'spirit', ask: 'What spirit are you in the mood for?', opts: FAMILIES },
  { k: 'feel', ask: 'And how should it taste?', opts: FEELS },
  { k: 'moment', ask: "When's it for?", opts: MOMENTS },
  { k: 'strength', ask: 'How strong?', opts: STRENGTHS },
];
const HANDFUL = 5;
function matches(a0) {
  const a = {}; Object.keys(a0).forEach(k => { if (a0[k] !== '-') a[k] = a0[k]; });
  return R.filter(r => (!a.spirit || r.spirit === a.spirit) && (!a.feel || feelOf(r) === a.feel) &&
    (!a.moment || momentsOf(r).has(a.moment)) && (!a.strength || strengthOf(r) === a.strength) && (!a.warm || isWarm(r)))
    .sort((x, y) => (canMake(y) - canMake(x)) || x.name.localeCompare(y.name));
}
/* Words he understands when you type or speak instead of tapping */
function hear(text) {
  const t = text.toLowerCase(), a = {};
  const byName = R.find(r => t.includes(r.name.toLowerCase()));
  if (byName) a.recipe = byName.id;
  const sp = [['whisk', 'whisky'], ['scotch', 'whisky'], ['bourbon', 'whisky'], ['rye', 'whisky'], ['gin', 'gin'], ['rum', 'rum'], ['tequila', 'tequila'],
    ['vodka', 'vodka'], ['brandy', 'brandy'], ['cognac', 'brandy'], ['campari', 'aperitif'], ['aperitif', 'aperitif'], ['vermouth', 'aperitif']].find(([w]) => t.includes(w));
  if (sp) a.spirit = sp[1];
  if (/sweet|rich|dessert|creamy/.test(t)) a.feel = 'rich';
  else if (/sour|sharp|fresh|citrus|zesty|tart|light and/.test(t)) a.feel = 'sharp';
  else if (/bitter/.test(t)) a.feel = 'bitter';
  else if (/dry|boozy|stiff|stirred/.test(t)) a.feel = 'dry';
  if (/after dinner|nightcap|dessert/.test(t)) a.moment = 'after';
  else if (/before dinner|aperitivo|aperitif/.test(t)) a.moment = 'before';
  else if (/with food|with dinner|with lunch/.test(t)) a.moment = 'food';
  if (/no alcohol|alcohol.free|non.alcoholic|mocktail|sober/.test(t)) a.strength = 'none';
  else if (/\blow\b|light|weak|easy/.test(t)) a.strength = 'low';
  else if (/strong|big|heavy/.test(t)) a.strength = 'strong';
  if (/warm|cold out|freezing|cosy|cozy|hot/.test(t)) a.warm = true;
  if (/^(skip|don.t mind|any|whatever|no idea|pass)/.test(t.trim())) a.skip = true;
  return a;
}
/* A conversation: call next(answer) repeatedly. Returns {say, opts?, q?, results?} */
function Conversation() {
  const a = {}; let qi = 0;
  function nextQ() {
    while (qi < QUESTIONS.length && a[QUESTIONS[qi].k] !== undefined) qi++;
    return qi < QUESTIONS.length ? QUESTIONS[qi] : null;
  }
  function step(say) {
    const m = matches(a);
    if (m.length === 0) {
      // nothing fits: drop the last thing said and offer what's closest
      const keys = Object.keys(a).filter(k => a[k] && a[k] !== '-');
      const last = keys.pop(); const note = last === 'strength' && a.strength === 'none'
        ? "Nothing alcohol-free on my list yet. That's coming. Here's the lightest I have." : "Nothing fits all of that. Here's what's closest.";
      if (last === 'strength' && a.strength === 'none') a.strength = 'low'; else delete a[last];
      return { say: note, results: matches(a).slice(0, 6), answers: { ...a } };
    }
    const q = nextQ();
    if (m.length <= HANDFUL || !q) return { say: say || (m.length === 1 ? 'Just the one. This:' : `${m.length > 6 ? 'Plenty. My pick of them' : 'These, then'}:`), results: m.slice(0, 6), answers: { ...a } };
    const opts = Object.entries(q.opts).filter(([k]) => matches({ ...a, [q.k]: k }).length > 0 || (q.k === 'strength' && k === 'none'));
    return { say: (say ? say + ' ' : '') + q.ask, q: q.k, opts, count: m.length, answers: { ...a } };
  }
  return {
    start() { return { say: 'What are you after tonight? Tell me, or pick.', opts: [['__warm', 'Warm me up'], ['__after', 'After dinner']], q: 'open', answers: {} }; },
    answer(qk, v) {
      if (v === '__warm') { a.warm = true; return step('Something to warm you.'); }
      if (v === '__after') { a.moment = 'after'; return step('After dinner it is.'); }
      if (v === '-') { if (qk !== 'open') a[qk] = '-'; qi++; return step(); } // skipped
      if (qk !== 'open') a[qk] = v;
      return step();
    },
    say(text) {
      const h = hear(text);
      if (h.recipe) return { say: 'Good choice.', open: h.recipe };
      if (h.skip) return this.answer(nextQ() ? nextQ().k : 'open', '-');
      let any = false; ['spirit', 'feel', 'moment', 'strength', 'warm'].forEach(k => { if (h[k] !== undefined) { a[k] = h[k]; any = true; } });
      return step(any ? 'I hear you.' : "I didn't catch a spirit or a taste in that.");
    },
    get answers() { const o = {}; Object.keys(a).forEach(k => { if (a[k] !== '-') o[k] = a[k]; }); return o; },
  };
}

/* ---------- What he does for each step: his attributes as bar tools ---------- */
const ACTION_LABEL = {
  thyrsus: 'His thyrsus stirs, as a bar spoon',
  vine: 'A vine fetches the bottle',
  lemon: 'A lemon ripens on the vine',
  mint: 'His wreath sprouts mint',
  honey: 'Honey wells up from the counter',
  shake: 'He shakes in his kantharos',
  strain: 'He strains through the vine leaves',
  ice: 'Ice into the glass',
  heat: 'He warms the glass',
  garnish: 'A finishing touch',
};
function actionFor(step, r) {
  const [t, , txt] = step, s = txt.toLowerCase();
  if (/honey/.test(s)) return 'honey';
  if (/mint/.test(s) || (t === 'garnish' && r.garnish === 'mint')) return 'mint';
  if (t === 'stir' || t === 'float') return 'thyrsus';
  if (/lemon|lime|grapefruit|citrus/.test(s) && t !== 'strain') return 'lemon';
  if (t === 'pour' || t === 'top') return 'vine';
  if (t === 'shake') return 'shake';
  if (t === 'strain') return 'strain';
  if (t === 'build') return 'ice';
  if (t === 'heat') return 'heat';
  if (t === 'muddle') return 'thyrsus';
  return 'garnish';
}
const fmtQty = x => (x.q ? `${x.q} ${x.u}` : x.u);

/* ---------- Look settings ---------- */
const LOOK = { finish: 'painted', coverage: 'classical', adult: false };
const FINISHES = { painted: 'Painted marble', white: 'White marble', living: 'Living skin' };
const COVERAGES = { classical: 'Classical', modest: 'Modest', cheeky: 'Cheeky (adult)' };

const reduceMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;
