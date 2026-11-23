/* Side-by-side: Halo (repo root index.html, left) and prototype E (right), one JPEG per screen.
   Run from the repository root with the static server up:  node prototypes/e-rendered/shots/halo/compare.js */
const { chromium } = require('playwright');
const path = require('path');
const BASE = process.env.BASE || 'http://localhost:8765/';
const OUT = __dirname;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const SCREENS = ['home', 'menu', 'recipe', 'talk', 'bar'];

(async () => {
  const browser = await chromium.launch();
  const vp = { viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1 };
  const shots = {};
  // Halo: the app is #frame inside a reviewer bench
  const h = await (await browser.newContext(vp)).newPage();
  await h.goto(BASE + 'index.html'); await sleep(1200);
  // Halo restarts its entrance animations on the resize an element screenshot causes; show the settled state
  await h.addStyleTag({ content: '#tab *{animation-delay:0s!important;animation-duration:0s!important}' });
  const halo = {
    home: () => home(),
    menu: () => { home(); go('drinks', { spirit: 'whisky' }); },
    recipe: () => { home(); go('recipe', { rid: 'penicillin' }); },
    talk: () => { home(); S.q = 'warm me up'; go('search'); },
    bar: () => { home(); go('bar'); },
  };
  for (const k of SCREENS) {
    await h.evaluate(`(${halo[k].toString()})()`); await sleep(1800);
    shots['h-' + k] = (await (await h.$('#frame')).screenshot({ type: 'png' })).toString('base64');
  }
  // E: the real onboarding, then each screen
  const e = await (await browser.newContext(vp)).newPage();
  await e.goto(BASE + 'prototypes/e-rendered/index.html');
  await e.waitForSelector('#bubble:not([hidden])', { timeout: 15000 });
  await e.click('text=Show him some photos'); await sleep(400);
  await e.click('#pread'); await e.waitForSelector('#pstock', { timeout: 8000 });
  await e.click('#pstock'); await sleep(2600); await e.click('#bubble .chip.go'); await sleep(6500);
  const grab = async k => { await e.mouse.move(1279, 799); await sleep(300); shots['e-' + k] = (await e.screenshot({ type: 'png' })).toString('base64'); };
  await grab('home');
  await e.click('#menu'); await sleep(1400); await grab('menu');
  await e.evaluate(() => proto.openRecipe('penicillin')); await sleep(4800); await grab('recipe');
  await e.evaluate(() => proto.home()); await sleep(1100);
  await e.click('#talkBtn'); await sleep(900); await e.fill('#talkIn', 'warm me up'); await e.click('#talk .send'); await sleep(700); await grab('talk');
  await e.evaluate(() => proto.home()); await sleep(1100);
  await e.click('#bottles > g >> nth=0'); await sleep(1400); await grab('bar');

  // compose
  const c = await (await browser.newContext({ viewport: { width: 1920, height: 640 }, deviceScaleFactor: 1 })).newPage();
  for (const k of SCREENS) {
    await c.setContent(`<body style="margin:0;background:#0b0a0c;display:flex;gap:16px;padding:16px;box-sizing:border-box;height:640px;font:14px system-ui;color:#9d9488">
      <figure style="margin:0;flex:1;display:flex;flex-direction:column;gap:6px"><figcaption>Halo · ${k}</figcaption><img style="width:100%;height:calc(100% - 26px);object-fit:contain;object-position:left top" src="data:image/png;base64,${shots['h-' + k]}"></figure>
      <figure style="margin:0;flex:1;display:flex;flex-direction:column;gap:6px"><figcaption>Prototype E · ${k}</figcaption><img style="width:100%;height:calc(100% - 26px);object-fit:contain;object-position:left top" src="data:image/png;base64,${shots['e-' + k]}"></figure></body>`);
    await sleep(200);
    await c.screenshot({ path: path.join(OUT, k + '.jpg'), type: 'jpeg', quality: 82 });
  }
  await browser.close();
  console.log('saved', SCREENS.map(k => k + '.jpg').join(', '));
})();
