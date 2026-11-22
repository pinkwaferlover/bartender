# Critic A: Dionysus bar prototypes B, C, D

Judged against `bartender/docs/process/dionysus-journey.md` (Q1–Q12, build-list rows 1–8) and the epic test: on the kitchen tablet, a drink in three taps or fewer from bottles in the house, recipe readable from a metre.

Evidence: shots I took this session are in `scratchpad/arena/A-shots/` (named below), made by the scripts in `scratchpad/arena/scripts/` (`first.js`, `bc.js`, `d.js`, `looks.js`, `dlook.js`, `talk.js`). Chromium via Playwright, three.js 0.160.0 served from npm through `page.route`, WebGL on SwiftShader (software). Google Fonts are blocked in the container, so every page falls back to system fonts; that is the only console error on any of the three.

## Scores

| Criterion | B illustrated | C painted | D 3D |
|---|---|---|---|
| 1. Brief coverage | 4 | 3 | 4 |
| 2. Dionysus | 3 | 2 | 4 |
| 3. Touchable vs muted | 4 | 2 | 2 |
| 4. Spatial model | 3 | 2 | 3 |
| 5. Tablet and phone | 4 | 3 | 2 |
| 6. Base for the real app | 4 | 3 | 2 |
| **Total /30** | **22** | **15** | **17** |

## Measured numbers

| Measure | B | C | D |
|---|---|---|---|
| Bytes loaded (1280×800) | 0.11 MB | 0.12 MB | 2.20 MB (`dionysus-mesh.js` alone is 1.39 MB) |
| Frame rate in this container | 60 fps | 27 fps tablet, 38 phone | 1–3 fps (software GL, see caveat) |
| Onboarding taps (photos → stocked) | 3 | 3 | 4 (bottles, snap, read, fill) |
| Bar → recipe via the menu | 2 taps | 2 taps | 2 taps (a real canvas tap on the 3D menu at 166,545 opened it) |
| Barman's choice | 1 tap | 1 tap | 1 tap |
| Bar → recipe via talking | 5 taps (talk, "Warm me up", spirit, feel, drink) | same code | similar |
| Recipe step text | 15 px | 19 px | 15 px |
| Recipe sheet, content/box height (tablet) | 766/692 | 861/698 | 828/700 |
| Recipe sheet (phone) | 860/490 | 1017/506 | 837/523 |
| Horizontal scroll at 390 px | none | none | none |

Caveat on D's frame rate: SwiftShader is a CPU renderer, so 1–3 fps says nothing about a real tablet's GPU. It does show that D has no fallback: the frame loop caps `dt` at 0.05 s (`index.html:822`), so on a weak device every animation slows down instead of skipping frames. C's 27 fps on a 0.12 MB page is a real cost: it repaints the canvas figure every frame (`paint.js`).

## 1. Brief coverage

B and C share `logic.js`, `data.js`, `draw.js`, `stories.js` and `inventory.js` byte for byte (`cmp`). Their brief coverage is the same apart from rendering.

| Item | B | C | D | Evidence |
|---|---|---|---|---|
| Row 1 / Q2: neon fade, tablet landscape | present | present | present | `b-tab-0s`, `c-tab-5s`, `d-tab-5s` |
| Q2: phone gets a cropped, taller view | partial: sign cut to "IONYSU" | partial: Dionysus tiny, menu cut off at left | present | `phones-bcd.png`, `row-b-phone.png`, `row-c-phone.png`, `row-d-phone.png` |
| Row 1 / Q8: he polishes a glass | present | present | present | home shots; D `idle()` at `index.html:566` |
| Row 2 / Q5: "What do you have?" then photos then list | present | present | present | `b-tab-1-ask`, `d-tab-2b-snapped`, `d-tab-3-found` |
| Q5: barware (photo or tick list) | present | present | present | tick lists in `b-tab-3-found`, `c-tab-3-found`, `d-tab-3-found` |
| Q5: second route (prompt pasted into your own AI tool) | **missing** | **missing** | present ("Paste a list from your own AI tool") | `grep -ciE "paste\|own ai\|api key\|prompt"`: B app.js 0, C app.js 0, D 3; `d-tab-2b-snapped` |
| Row 3 / Q6: shelf of your bottles, brand-family art | partial: one shape per Family (`draw.js` SHAPES), not per brand family | partial, same code | partial: lathe profiles per shape (`makeBottle`, `index.html:363`) | `b-tab-4-stocked`, `d-tab-4-stocked` |
| Row 4 / Q11: menu by spirit, feel, A–Z | present | present ("Bibenda") | present | tabs read by script: all three print `["By spirit","By feel","A–Z"]` |
| Row 5 / Q3: search is talking to him (bubble and mic) | present | present | present | `b-tab-10-talk`, `c-tab-10-talk`, D `#q` and `#mic` (`index.html:160-161`) |
| Q4: "Feel", never "craving" | present | present | present | no "craving" in the UI; feels use the four names |
| Q11: up to four skippable questions, stops when a handful fit | present, but adds a fifth axis, "warm" | same | present | `talk.js` run: "What spirit… (11 fit so far)", then feel, then a list of 5; `logic.js:22-23` and `:103` add `warm` |
| Row 6: tap him for a story | present | present | present | `b-tab-9-story`, `c-tab-9-story`, `d-tab-9-story` |
| Row 6: barman's choice (panther, dice) | present: panther swipe and dice (`app.js:474-494`) | present (panther and dice both tappable, `app.js:384-385`) | present, but only the dice is a tap target; the panther is not (`pick()`, `index.html:667`: `tap='dice'`, no `tap='panther'`) | `b-tab-8-choice`, `c-tab-8-choice` |
| Row 7 / Q12: recipe in front, he makes it behind | partial: he is behind, but blurred | partial: same blur | partial: blurred, and so large that only his torso shows | `b-tab-6-recipe`, `c-tab-6-recipe`, `d-tab-6-recipe` |
| Q12: missing barware gives a swap, never hidden | present ("No muddler? Use the end of a rolling pin.") | present | present (three swap lines) | same shots; `logic.js:36`, D `index.html:226` |
| Row 8: back zooms out, always to the bar | present | present | present (+ Escape key, `index.html:727`) | `b-tab-7-back`, `c-tab-7-back` |
| Q7: touchable in true colour, bar muted | present | partial | **inverted** | see criterion 3 |
| Q8: three finishes; regal reds and greens | present | present | present | `grid-looks-bc.png`, `grid-d-looks.png` |
| Q9: coverage, cheeky off until switched on | present (`cheeky disabled before adult: true`) | present (same) | present (`#sAdult` toggle) | `b-look-panel`, `d-look-panel` |
| Q9+: thyrsus, wreath mint, vines, lemons, kantharos, fawn-skin cloth, panther dice | present as step labels plus animated props | present | present, all animated in 3D | `logic.js:171-182`; D `toolFor()` `index.html:649`, `sprout()` 612, `honeyWell()` 613 |
| Q9+: rare golden rim | **missing** | **missing** | present (15%, `index.html:655`) | `grep -ciE "golden\|gold rim\|\brim\b\|rare"`: B app.js and logic.js 0; C's only hit is `G.rim`, a garnish anchor (`app.js:182`) |
| Q7: patrons he can serve | **missing** | **missing** | **missing** | `grep -ciE "patron\|customer\|\bguest"`: 0 in every app file (the only hit is a story text in `stories.js`). Behaviour check: no figure other than Dionysus and the panther in any of my shots. Tracked in issue #4, so this is expected, but the brief's diagram has no patrons row either. |
| Q10: the real 34 recipes | present (`R.length` = 34; `data.js` is identical to `src/data.js`) | present | present (loads `../../src/data.js` directly) | `cmp` output |

## 2. Dionysus

- **B (3).** Colourful and friendly, and the props really move: in `b-tab-8-choice` a green vine reaches across the bar to fetch the bottle. But he is a flat poster: tube arms, a face of four lines. "Lifelike" is not met. All three finishes and coverages read clearly at a glance (`grid-looks-bc.png`, top row). Cheeky is implied: a bare torso with a vine in front.
- **C (2).** The builder's own weak spot holds. In `c-tab-5s` he is a grey jointed mannequin with block arms. His colours are muddied under the brown wash, so he is not the most colourful thing on screen; the green menu card is. The finishes do switch (`grid-looks-bc.png`, bottom row), but living skin and painted marble look nearly the same at tablet size.
- **D (4).** The only one that reads as a lifelike figure: a real statue with a red cloak, wreath and thyrsus (`d-tab-5s`, `d-tab-4-stocked`). White marble is convincing (`d-look-white-classical`). Faults I saw myself:
  - Modest coverage is a flat green slab over his hip and legs, with no folds (`d-look-living-modest`, crop 2 of `grid-d-looks.png`).
  - Cheeky: across 10 samples over about 80 s of wall time I never caught the turn or the glimpse (`d-cheeky-t0`…`t9`). The turn runs at 14.6–18.6 s of animation time (`index.html:571`), which at software frame rates is beyond my sample window. **Not verified either way.** I could not confirm the builder's "barely visible".
  - Cloak tear on the left-arm reach and the flank blob: **not verified**. My recipe-time shots were covered by the recipe sheet and the depth-of-field blur (`d-reach-t*`), so I have no clear frame of the reach.
  - On the recipe screen he is so close and so blurred (`d-tab-6-recipe`) that you see a smear of cloak, not him making the drink.

## 3. Touchable versus muted

Mean HSV saturation and value of crops from my home-screen shots:

| Region | B | C | D |
|---|---|---|---|
| Background (should be muted) | wall S .37 V .11 | wall S .51 V .10 | curtain S **.98**, stools S **.91**, back-bar glow S **.95** |
| Menu (touchable) | S .55 V .34 | S .49 V .25 | S .50 V .29 |
| Other touchable | | bottles S .37 | dice S .32 |

- **B (4).** Dark, low-value wall. Bottles, menu, dice, panther and Dionysus all carry colour. Every touchable SVG node has a pointer cursor (the script lists `shelf, dio, menu, panther, dice…`). One fault: the cobweb also has a pointer cursor.
- **C (2).** The wall (.51) is as saturated as the menu (.49), and the bottles are duller still (.37). Nothing says "tap me" apart from the green card. The canvas gives no cursor feedback: the pointer-cursor list is empty.
- **D (2).** **Q7 is inverted.** The red curtain, red stools and orange back bar are the most saturated things on screen, and none of them can be touched. The touchable menu is a small dull card at the far left. The "Tap the menu / Talk to him / Roll the dice" hint pills (`d-tab-4-stocked`) are a good patch, but they exist because the scene does not show what can be touched.

## 4. Spatial model

- **Three taps:** met by all three through the menu (2 taps) and barman's choice (1 tap). **Not met by talking** (5 taps in B; C shares the code; D is the same shape), which the brief treats as the main way to search.
- **Readable from a metre:** none of the three is comfortable. B and D use 15 px step text, C uses 19 px. The recipe sheet overflows on all three, worst on the phone (C 1017/506). On C's phone view, "Another, please" sits on top of step 1 (`row-c-phone.png`, third frame), and on the tablet step V is cut off behind the buttons (`grid-c1.png`). On a tablet at a metre, 15 px with the current step below the fold fails the test.
- **Zoom in and out:** B moves the SVG viewBox (`cam()`, `app.js:98`) and D flies the camera (`fly()`, `index.html:546`). Both are real zooms. C scales a CSS stage. All three return to the bar on Back. B's zoomed framings crop the sign at the top (`b-tab-3-found`).

## 5. Tablet and phone

- **B (4).** 60 fps, 0.11 MB, no errors, `prefers-reduced-motion` honoured in JavaScript (`RM`, `app.js:13`). The reduced-motion run completed the same flow (`b-tab-rm-*`). The phone view crops the neon sign to "IONYSU" (`b-phone-5s`).
- **C (3).** 27 fps for a near-static scene. Reduced motion is handled in both JavaScript and CSS (`style.css:156`). On the phone Dionysus is tiny on the home screen and the recipe buttons overlap the steps.
- **D (2).** 2.2 MB before textures, and it depends on a CDN. Its reduced-motion handling exists (`grep` finds 2 hits). On my phone run every view framed well (`row-d-phone.png`), with the best phone layout of the three. But there is no low-power path, and the typewriter bubble showed only "Wh" after 5 s on this machine (`phones-bcd.png`).

## 6. Base for the real app

- **B (4).** Split files: `logic.js` (pure: Moments, Strength, Conversation, swaps, `actionFor`), `data.js`, `draw.js` (bottle SHAPES and LABEL per family), and a 554-line `app.js`. A `window.proto` hook makes it scriptable. The hundreds of bottle artworks in issue #3 fit naturally as SVG symbols keyed by Style. Patron vignettes (issue #4) fit as more SVG groups.
- **C (3).** It reuses B's logic and data, but draws the figure by hand with canvas paths (`paint.js`, 261 lines). Every new artwork means new paint code, at a 27 fps cost.
- **D (2).** One 858-line `index.html` with 22 lines over 300 characters (minified style), plus a 1.39 MB mesh inside a JS file. It reads data from `src/` (good reuse), but the scene, rig, UI and conversation logic are all in one module. Bottles are procedural lathes, so hundreds of brand-family bottles would need a modelling pipeline, and each patron would need a rigged model.

## Recommended base

**Build on B.** It is the only one that keeps the bar muted and the touchables in colour, runs light on a tablet, and has code that splits cleanly into the app. Its clear gap is that Dionysus is not lifelike. Fix that inside B's SVG world (a jointed figure with real elbows and shading layers) rather than switching to a 1.4 MB 3D statue that inverts Q7 and has no low-power path.

## Grafts

1. **From D: the second Q5 route.** The "Paste a list from your own AI tool" link, the "I found 28 things" grouped list, and barware tick boxes with swap wording (`d-tab-2b-snapped`, `d-tab-3-found`). B has no paste route.
2. **From D: the rare golden rim** (`index.html:655`, 15% chance) and the "needs Double cream" flag on menu rows you can't make (`row-d-phone.png`, menu frame).
3. **From D: the hint pills on the stocked bar** ("Tap the menu · Talk to him · Roll the dice · Tap him for a story") and the Escape key for Back (`index.html:727-728`). These are a cheap first-visit safety net for touchability.
4. **From C: the larger recipe type and its CSS reduced-motion rule.** Start from C's 19 px (`style.css:156` for the rule) and go larger: aim at 24 px or more for the current step, with the sheet sized so the current step never falls under the buttons.

## What the brief got wrong or left open, now that it can be seen

- **"Readable from a metre" has no number.** All three builders shipped 15–19 px. The brief needs a minimum size for the current step (I suggest at least 24 px) and a rule that the current step is always visible above the buttons.
- **The three-tap test only counts menu and barman's choice.** Talking takes 5 taps, yet the brief makes talking the main search (Q3). Say whether talking must also fit in three taps, for example by having his opening chips lead straight to a shortlist.
- **"Muted" is not measurable.** D's warm hotel-bar lighting satisfies "light and shade" in the brief yet makes the untouchable curtain and stools the most saturated things on screen. Add a check: no untouchable region more saturated than the least saturated touchable thing.
- **"He makes it behind" clashes with a readable recipe.** All three blur him to keep the card legible, so the Q9+ bar-tool show is mostly lost while you read. Decide whether the recipe sits beside him (tablet landscape has the room) or he pauses between steps.
- **Q11 grew a fifth axis.** B and C's "Warm me up" (`logic.js:22`) and D's chips are not one of the four agreed questions. Either add it to the brief or drop it.
- **Strength isn't defined.** B/C call the Penicillin "Regular strength"; D calls it "strong" (`b-tab-6-recipe` vs `d-tab-6-recipe`). The rule that turns a recipe into a strength band needs writing down once.
- **Patrons appear in Q7 but not in the journey diagram**, and no prototype drew one. Until issue #4 lands, "Dionysus touches only touchable things, plus patrons" cannot be judged.
- **Q5 doesn't say whether the fake camera step counts toward onboarding taps.** D adds one tap for it.
