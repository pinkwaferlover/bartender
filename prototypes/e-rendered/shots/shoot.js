/* Screenshots and checks for prototype E. Run from the repository root:
     python3 -m http.server 8765 &   then   node prototypes/e-rendered/shots/shoot.js
   Writes JPEG shots next to this file, plus measure/*.png and measure/boxes.json for the saturation check. */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const URL = process.env.URL || 'http://localhost:8765/prototypes/e-rendered/index.html';
const OUT = __dirname, MEAS = path.join(OUT, 'measure');
fs.mkdirSync(MEAS, { recursive: true });
const errors = [], report = { taps: {}, checks: {} };
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function page(browser, opts) {
  const ctx = await browser.newContext(opts);
  const p = await ctx.newPage();
  p.on('pageerror', e => errors.push(`[${opts.label}] pageerror: ${e.message}`));
  p.on('console', m => { if (m.type() === 'error') errors.push(`[${opts.label}] console: ${m.text()}`); });
  p.on('requestfailed', r => { if (!/fonts\.g/.test(r.url())) errors.push(`[${opts.label}] request failed: ${r.url()}`); });
  return p;
}
const shot = (p, name) => p.screenshot({ path: path.join(OUT, name + '.jpg'), type: 'jpeg', quality: 82 });
const recipeOpen = p => p.evaluate(() => !document.querySelector('#panel').hidden && document.querySelector('#panel').classList.contains('recipe'));
async function stock(p) {   // the real onboarding: photos -> found -> stock the shelf
  await p.waitForSelector('#bubble:not([hidden])', { timeout: 15000 });
  await p.click('text=Show him some photos'); await sleep(400);
  await p.click('#pread'); await p.waitForSelector('#pstock', { timeout: 8000 });
  await p.click('#pstock'); await sleep(2600);
  await p.click('#bubble .chip.go'); await sleep(300);
}
async function home(p) { await p.evaluate(() => proto.home()); await sleep(1100); }

(async () => {
  const browser = await chromium.launch();
  // ---------------- tablet 1280x800
  const t = await page(browser, { viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1, label: 'tablet' });
  await t.goto(URL); await sleep(900);
  await shot(t, '00-intro-sign');
  await stock(t); await sleep(6500);   // let the hint pills fade
  await shot(t, '01-bar');
  // measure: the bar with and without the touchables
  await t.screenshot({ path: path.join(MEAS, 'bar.png') });
  const boxes = await t.evaluate(() => {
    const r = id => { const b = document.getElementById(id).getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom].map(Math.round); };
    return { menu: r('menu'), panther: r('panther'), honey: r('honey'), shelf: r('bottles'), dio: r('dio') };
  });
  await t.evaluate(() => { ['menu', 'panther', 'honey', 'bottles', 'dioLayer', 'drink'].forEach(id => document.getElementById(id).style.visibility = 'hidden'); document.getElementById('talkBtn').hidden = true; });
  await sleep(200); await t.screenshot({ path: path.join(MEAS, 'bar-bg.png') });
  await t.evaluate(() => { ['menu', 'panther', 'honey', 'bottles', 'dioLayer', 'drink'].forEach(id => document.getElementById(id).style.visibility = ''); document.getElementById('talkBtn').hidden = false; });
  fs.writeFileSync(path.join(MEAS, 'boxes.json'), JSON.stringify(boxes));

  // menu: 2 taps (menu, drink)
  await t.click('#menu'); await sleep(1300);
  await shot(t, '02-menu');
  await t.click('#panel .drink >> nth=0'); await sleep(1300);
  report.taps.menu = { taps: 2, recipe: await recipeOpen(t) };
  await home(t);

  // talk: 3 taps (Talk, a spirit, a drink)
  await t.click('#talkBtn'); await sleep(1000);
  await t.click('#chips .chip >> text=Gin'); await sleep(500);
  await shot(t, '03-talk');
  await t.click('#chips .chip.res >> nth=0'); await sleep(1200);
  report.taps.talk = { taps: 3, recipe: await recipeOpen(t) };
  await home(t);
  // talk by words (R12): "warm me up" is understood, not a button
  await t.click('#talkBtn'); await sleep(900);
  report.checks.warmButton = await t.evaluate(() => [...document.querySelectorAll('#chips .chip')].some(c => /warm me up|after dinner/i.test(c.textContent)));
  await t.fill('#talkIn', 'warm me up after dinner'); await t.click('#talk .send'); await sleep(400);
  report.checks.warmHeard = await t.evaluate(() => document.querySelector('#say').textContent);
  await t.fill('#talkIn', 'tequila and bitter'); await t.click('#talk .send'); await sleep(400);
  report.checks.closest = await t.evaluate(() => ({ say: document.querySelector('#say').textContent, results: document.querySelectorAll('#chips .chip.res').length }));
  await home(t);

  // barman's choice: 1 tap (the panther)
  await t.click('#panther'); await sleep(2600);
  report.taps.choice = { taps: 1, recipe: await recipeOpen(t), kicker: await t.evaluate(() => (document.querySelector('.recipe .kicker') || {}).textContent) };
  await home(t);

  // a recipe step: Penicillin (honey from the jar), step 2 acted out and waiting
  await t.evaluate(() => proto.openRecipe('penicillin')); await sleep(1200);
  const honeyStep = await t.evaluate(() => RB.penicillin.steps.findIndex(s => actionFor(s, RB.penicillin) === 'honey'));
  await t.evaluate(i => proto.goStep(i), honeyStep); await sleep(1700);
  await shot(t, '04b-recipe-honey-acting');
  await sleep(2400);
  await shot(t, '04-recipe-step');
  report.checks.stepSize = await t.evaluate(() => getComputedStyle(document.querySelector('#stepText')).fontSize);
  report.checks.waiting = await t.evaluate(() => document.querySelector('#stepbox').classList.contains('waiting'));
  report.checks.dioBlur = await t.evaluate(() => getComputedStyle(document.querySelector('#scene')).filter);
  await t.click('#nextS'); await sleep(300);
  report.checks.advancedByTap = await t.evaluate(() => proto.state().step);
  await home(t);

  // the shelf
  await t.click('#bottles > g >> nth=0'); await sleep(1300);   // a bottle: the shelf's centre is behind his head
  await shot(t, '05-shelf');
  await home(t);
  // the paste route
  await t.evaluate(() => proto.openPaste()); await sleep(1000);
  await t.click('#pex'); await t.click('#pread'); await sleep(300);
  report.checks.pasteRead = await t.evaluate(() => document.querySelectorAll('.found li').length);
  await shot(t, '07-paste-route');
  await home(t);

  // ---------------- phone 390x844
  const ph = await page(browser, { viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true, label: 'phone' });
  await ph.goto(URL); await sleep(500);
  await stock(ph); await sleep(6500);
  await shot(ph, '06-phone-bar');
  report.checks.phoneInFrame = await ph.evaluate(() => ['menu', 'panther', 'honey', 'bottles'].map(id => { const b = document.getElementById(id).getBoundingClientRect(); return [id, b.left >= -2 && b.right <= innerWidth + 2]; }));
  await ph.tap('#panther'); await sleep(2600);
  report.taps.phoneChoice = { recipe: await recipeOpen(ph) };
  await sleep(3400);
  await shot(ph, '06b-phone-recipe');
  await ph.evaluate(() => proto.home()); await sleep(1000);
  await ph.tap('#talkBtn'); await sleep(900); await ph.tap('#chips .chip >> text=Whisky'); await sleep(500);
  await ph.tap('#chips .chip.res >> nth=0'); await sleep(1000);
  report.taps.phoneTalk = { taps: 3, recipe: await recipeOpen(ph) };

  // ---------------- reduced motion
  const rm = await page(browser, { viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1, reducedMotion: 'reduce', label: 'reduced-motion' });
  await rm.goto(URL); await sleep(600);
  await stock(rm);
  report.checks.reducedMotion = await rm.evaluate(async () => {
    const vb0 = document.querySelector('#scene').getAttribute('viewBox');
    proto.openRecipe('oldfashioned'); await new Promise(r => setTimeout(r, 120));
    const vb1 = document.querySelector('#scene').getAttribute('viewBox');
    const anims = document.getAnimations().filter(a => a.playState === 'running').length;
    return { camJumps: vb0 !== vb1, runningAnimations: anims, waiting: document.querySelector('#stepbox').classList.contains('waiting') };
  });

  // page weight
  const w = await page(browser, { viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1, label: 'weight' });
  let bytes = 0; const seen = {};
  w.on('response', async r => { try { const b = await r.body(); if (!/fonts\.g/.test(r.url())) { bytes += b.length; seen[r.url().split('/').pop()] = b.length; } } catch (e) {} });
  await w.goto(URL); await sleep(1500);
  await w.evaluate(() => { proto.fill(); proto.openMenu(); }); await sleep(1200);
  await w.evaluate(() => proto.openRecipe('penicillin')); await sleep(1200);
  await w.evaluate(() => proto.openShelf()); await sleep(1200);
  report.weightMB = +(bytes / 1048576).toFixed(2);
  report.files = Object.keys(seen).length;

  report.errors = errors;
  fs.writeFileSync(path.join(MEAS, 'report.json'), JSON.stringify(report, null, 1));
  console.log(JSON.stringify(report, null, 1));
  await browser.close();
})();
