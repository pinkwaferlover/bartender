/* Prototype logic. Started as B's shared logic.js; prototype E changes it for round 2 (R6-R12), marked "E:".
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
  out: new Set(),   // Bottles marked run out on Your bar: they stay on the shelf, dusty, and drinks that need them say so
};
try { const v = JSON.parse(localStorage.getItem('dio-bar') || 'null'); if (v && Array.isArray(v.out)) v.out.forEach(k => { BAR.out.add(k); BAR.have.delete(k); }); } catch (e) {}
function saveBar() { try { localStorage.setItem('dio-bar', JSON.stringify({ out: [...BAR.out] })); } catch (e) {} }
/* Your bar: tap a Bottle to mark it run out, tap again when you've bought more */
function setRunOut(k, out) {
  if (out) { BAR.have.delete(k); BAR.out.add(k); } else { BAR.out.delete(k); BAR.have.add(k); }
  saveBar();
}
const isBottle = k => ['spirit', 'wine', 'liqueur', 'bitters', 'mixer'].includes((ING[k] || [])[1]);
const shelfBottles = () => [...new Set([...BAR.have, ...BAR.out])].filter(isBottle).map(k => ({ k, style: ING[k][0], kind: ING[k][1], colour: ING[k][2], family: ING[k][3], out: BAR.out.has(k) }))
  /* a stable order: by group, then by the inventory's own order, so marking a Bottle run out never moves it */
  .sort((a, b) => ORDER.indexOf(groupOf(a.k)) - ORDER.indexOf(groupOf(b.k)) || INV0.indexOf(a.k) - INV0.indexOf(b.k) || a.style.localeCompare(b.style));
const ORDER = ['whisky', 'gin', 'vodka', 'rum', 'tequila', 'brandy', 'liqueur', 'aperitif', 'bitters', 'mixer'];
/* Shelf groups from the data: a liqueur (kind 'liqueur', not an aperitif) is a Liqueur, whatever spirit it is made from */
const groupOf = k => ING[k][1] === 'liqueur' && ING[k][3] !== 'aperitif' ? 'liqueur' : ING[k][3];
const GROUP_NAME = g => FAMILIES[g] || { liqueur: 'Liqueurs', bitters: 'Bitters', mixer: 'Mixers' }[g] || 'Other';

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
  res.found.forEach(k => { if (!BAR.out.has(k)) BAR.have.add(k); });   // what you marked run out stays run out
  BAR.barware = new Set(toolsTicked);
  BAR.filled = true;
}

/* ---------- E: the "paste from your own AI" route (Q5, grafted from prototype D) ----------
   A fixed expected output defines the prompt: the user pastes this into their own AI tool with their
   photos, then pastes the reply back. Nothing leaves the page. */
const AI_PROMPT = () => `Look at my photos of my drinks cupboard, fridge, fruit bowl and bar tools.
List every bottle and every piece of barware you can see.
Reply with only this JSON, nothing else:
{"bottles":[{"label":"the name as printed on the label","style":"one of the styles below"}],"barware":["one of: ${Object.keys(BARWARE).join(', ')}"]}
Styles: ${Object.keys(ING).filter(k => !STAPLE.has(k)).join(', ')}`;
function matchStyle(text) {
  const t = String(text || '').toLowerCase().trim(); if (!t) return null;
  if (ING[t]) return t;
  const keys = Object.keys(ING).sort((x, y) => y.length - x.length);
  return keys.find(k => t.includes(k)) || keys.find(k => t.includes(ING[k][0].toLowerCase())) || keys.find(k => k.includes(t)) || null;
}
/* Reads the reply: the JSON above, or a plain list (one thing per line) as a fallback. */
function readPasted(text) {
  const found = new Set(), tools = new Set(), unknown = [];
  let data = null; const j = String(text).match(/\{[\s\S]*\}/);
  if (j) { try { data = JSON.parse(j[0]); } catch (e) { data = null; } }
  const items = data ? [...(data.bottles || []), ...(data.have || [])] : String(text).split(/\n|,/).map(x => x.replace(/^[-*\d.\s]+/, '')).filter(Boolean);
  items.forEach(it => {
    const k = typeof it === 'string' ? matchStyle(it) : (matchStyle(it.style) || matchStyle(it.label));
    if (k) found.add(k); else unknown.push(typeof it === 'string' ? it : (it.label || it.style));
  });
  (data ? data.barware || [] : items).forEach(b => { const t = String(b).toLowerCase(); const k = Object.keys(BARWARE).find(x => t.includes(x) || t.includes(BARWARE[x].toLowerCase())); if (k) tools.add(k); });
  return { found: [...found], tools: [...tools], unknown };
}

/* ---------- Barman's choice ---------- */
/* E (R7, fixes B logic.js:87): he draws only from drinks you can make now, plus one drink marked
   "worth buying a bottle for": a drink one bottle away, using the bottle that would open the most drinks. */
function worthBuying(exceptId) {
  const near = R.filter(r => { const m = missingFor(r); return m.length === 1 && isBottle(m[0].k); });
  if (!near.length) return null;
  const count = {}; near.forEach(r => { const k = missingFor(r)[0].k; count[k] = (count[k] || 0) + 1; });
  const best = Object.keys(count).sort((x, y) => count[y] - count[x] || x.localeCompare(y))[0];
  const opts = near.filter(r => missingFor(r)[0].k === best && r.id !== exceptId);
  if (!opts.length) return null;
  return { r: opts[Math.floor(Math.random() * opts.length)], bottle: best, opens: count[best] };
}
/* One bottle away: each missing Bottle with the drinks it alone would open, most first */
function oneBottleAway() {
  const m = {};
  R.forEach(r => { const x = missingFor(r); if (x.length === 1 && isBottle(x[0].k)) (m[x[0].k] = m[x[0].k] || []).push(r); });
  return Object.entries(m).sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0]));
}
/* Returns { r, worth } (worth is null for a drink you can make), or null when there is nothing to draw. */
function barmansChoice(exceptId) {
  const pool = R.filter(r => canMake(r) && r.id !== exceptId).map(r => ({ r, worth: null }));
  const w = worthBuying(exceptId); if (w) pool.push({ r: w.r, worth: w });
  return pool.length ? pool[Math.floor(Math.random() * pool.length)] : null;
}

/* ---------- Talking to Dionysus ---------- */
const QUESTIONS = [
  { k: 'spirit', ask: 'Got a spirit in mind?', opts: FAMILIES },
  { k: 'feel', ask: 'How should it taste?', opts: FEELS },
  { k: 'moment', ask: "When's it for?", opts: MOMENTS },
  { k: 'strength', ask: 'How strong?', opts: STRENGTHS },
];
const HANDFUL = 5, SHORTLIST = 4;
function matches(a0) {
  const a = {}; Object.keys(a0).forEach(k => { if (a0[k] !== '-') a[k] = a0[k]; });
  return R.filter(r => (!a.spirit || r.spirit === a.spirit) && (!a.feel || feelOf(r) === a.feel) &&
    (!a.moment || momentsOf(r).has(a.moment)) && (!a.strength || strengthOf(r) === a.strength) && (!a.warm || isWarm(r)))
    .sort((x, y) => (canMake(y) - canMake(x)) || x.name.localeCompare(y.name));
}
/* Words he understands when you type or speak instead of tapping.
   E (R12): "warm me up", "after dinner" and the like are words, not buttons. */
function hear(text) {
  const t = text.toLowerCase(), a = {};
  const byName = R.find(r => t.includes(r.name.toLowerCase()));
  if (byName) a.recipe = byName.id;
  const sp = [['whisk', 'whisky'], ['scotch', 'whisky'], ['bourbon', 'whisky'], ['rye', 'whisky'], ['gin', 'gin'], ['rum', 'rum'], ['tequila', 'tequila'],
    ['vodka', 'vodka'], ['brandy', 'brandy'], ['cognac', 'brandy'], ['campari', 'aperitif'], ['aperitif', 'aperitif'], ['vermouth', 'aperitif']].find(([w]) => new RegExp('\\b' + w).test(t));
  if (sp) a.spirit = sp[1];
  if (/sweet|rich|dessert|creamy/.test(t)) a.feel = 'rich';
  else if (/sour|sharp|fresh|citrus|zesty|tart|light and/.test(t)) a.feel = 'sharp';
  else if (/bitter/.test(t)) a.feel = 'bitter';
  else if (/dry|boozy|stiff|stirred/.test(t)) a.feel = 'dry';
  if (/after dinner|nightcap|dessert|after supper/.test(t)) a.moment = 'after';
  else if (/before dinner|aperitivo|aperitif|pre.dinner/.test(t)) a.moment = 'before';
  else if (/with food|with dinner|with lunch|with supper/.test(t)) a.moment = 'food';
  if (/no alcohol|alcohol.free|non.alcoholic|mocktail|sober/.test(t)) a.strength = 'none';
  else if (/\blow\b|light|weak|easy/.test(t)) a.strength = 'low';
  else if (/strong|big|heavy/.test(t)) a.strength = 'strong';
  if (/warm|cold out|freezing|cosy|cozy|\bhot\b|chilly/.test(t)) a.warm = true;
  if (/^(skip|don.t mind|any|whatever|no idea|pass)/.test(t.trim())) a.skip = true;
  return a;
}
const ANSWER_WORDS = { spirit: v => FAMILIES[v], feel: v => FEELS[v].toLowerCase(), moment: v => MOMENTS[v].toLowerCase(), strength: v => STRENGTHS[v].toLowerCase() + ' strength', warm: () => 'warming' };
/* A conversation (Q11): up to four skippable questions, but every answer already shows a shortlist,
   so a tap on any chip can lead straight to a drink (E: talk reaches a recipe in three taps).
   Returns {say, results?, q?, opts?, count?}. */
function Conversation() {
  const a = {}, order = []; let qi = 0;
  function set(k, v) { a[k] = v; const i = order.indexOf(k); if (i >= 0) order.splice(i, 1); order.push(k); }
  function nextQ() {
    while (qi < QUESTIONS.length && a[QUESTIONS[qi].k] !== undefined) qi++;
    return qi < QUESTIONS.length ? QUESTIONS[qi] : null;
  }
  function step(say) {
    let m = matches(a), dropped = [];
    // E (fixes B logic.js:136-143): when nothing fits, let go of answers one at a time, newest first,
    // until something does, so "here's what's closest" always lists drinks.
    while (m.length === 0) {
      const k = [...order].reverse().find(x => a[x] !== undefined && a[x] !== '-');
      if (!k) { m = matches({}); break; }
      if (k === 'strength' && a.strength === 'none') { a.strength = 'low'; dropped.push('none'); }
      else { dropped.push(ANSWER_WORDS[k] ? ANSWER_WORDS[k](a[k]) : k); delete a[k]; order.splice(order.indexOf(k), 1); }
      m = matches(a);
    }
    if (dropped.length) {
      const note = dropped[0] === 'none' ? "Nothing alcohol-free on my list yet. That's coming. Here's the lightest I have:"
        : `Nothing fits all of that. Here's what's closest, without ${dropped.join(' or ')}:`;
      return { say: note, results: m.slice(0, 6), answers: { ...a } };
    }
    const q = nextQ();
    if (m.length <= HANDFUL || !q) return { say: say || (m.length === 1 ? 'Just the one. This:' : m.length > 6 ? 'My pick of them:' : 'These, then:'), results: m.slice(0, 6), answers: { ...a } };
    const opts = Object.entries(q.opts).filter(([k]) => matches({ ...a, [q.k]: k }).length > 0);
    return { say: (say ? say + ' ' : '') + (Object.keys(a).length ? `${m.length} fit. Try one, or narrow it: ` : '') + q.ask,
      results: Object.keys(a).length ? m.slice(0, SHORTLIST) : null, q: q.k, opts, count: m.length, answers: { ...a } };
  }
  return {
    start() { return step(); },
    answer(qk, v) {
      if (v === '-') { a[qk] = '-'; qi++; return step(); } // skipped
      set(qk, v);
      return step();
    },
    say(text) {
      const h = hear(text);
      if (h.recipe) return { say: 'Good choice.', open: h.recipe };
      if (h.skip) { const q = nextQ(); return q ? this.answer(q.k, '-') : step(); }
      let any = false; ['spirit', 'feel', 'moment', 'strength', 'warm'].forEach(k => { if (h[k] !== undefined) { set(k, h[k]); any = true; } });
      const heard = [h.warm && 'something to warm you', h.moment && MOMENTS[h.moment].toLowerCase()].filter(Boolean);
      return step(any ? (heard.length ? `${heard.join(', ')[0].toUpperCase() + heard.join(', ').slice(1)}. I hear you.` : 'I hear you.') : "I didn't catch a spirit or a taste in that.");
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
  honey: 'He dips his thyrsus in the honey jar',
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
