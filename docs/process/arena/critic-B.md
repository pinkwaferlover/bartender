# Critic B: judging prototypes B, C and D against the Dionysus brief

All the screenshots cited are mine. I ran them this session with Playwright against `python3 -m http.server` (wt-bc on :8701, wt-d on :8702). They are in `/tmp/claude-0/-home-user/8f30a1e5-9478-5947-974c-ed94868ed67e/scratchpad/arena/B-shots/`, and shot names below are relative to that folder. The scripts are in `.../scratchpad/arena/run/`.

**Test conditions you need to know before reading the scores**

- I blocked Google Fonts on purpose, so every page fell back to its own fallback font. The single console error on every page (`net::ERR_FAILED`) is that block, not a prototype bug. C's serif fallback could change how its text wraps.
- WebGL ran on SwiftShader (CPU), at about 2.7 fps for D. **That number says nothing about a real tablet GPU.** It does mean D's motion runs about 10× slow here, because `dt` is clamped to 0.05 per frame. That is why I ran most of D's journey with reduced motion on, and ran its recipe performance separately with motion on.
- "Build list items 1–8" isn't numbered in `docs/process/dionysus-journey.md`. I read them as the eight rows in the journey's YOU column: 1 open app, 2 first visit, 3 tap shelf, 4 tap menu, 5 talk to him, 6 tap Dionysus for a story, 7 barman's choice, 8 recipe then back.

## Score table

| Criterion | B illustrated | C painted | D 3D |
|---|---|---|---|
| 1 Brief coverage | 4 | 4 | 4 |
| 2 Dionysus | 3 | 2 | 3 |
| 3 Touchable vs muted | **4** | 2 | 2 |
| 4 Spatial model and readability | 3 | 3 | 3 |
| 5 Tablet and phone | **4** | 2 | 2 |
| 6 Base for the real app | **4** | 3 | 2 |
| **Total /30** | **22** | 16 | 16 |

No prototype passes the epic's own test in full. All three reach a recipe in 2 taps, but none has recipe text readable from a metre (criterion 4).

---

## 1. Brief coverage

B and C share their domain code byte for byte. `cmp` shows `data.js`, `logic.js`, `draw.js`, `stories.js` and `inventory.js` are identical, and `data.js` equals `/home/user/bartender/src/data.js`. So B and C differ only in rendering and copy. D is one 858-line `index.html` that loads `../../src/data.js` directly.

| Item / decision | B | C | D | Evidence |
|---|---|---|---|---|
| 1 Open: word becomes neon sign (Q2) | present | present (sign cut off at top right) | present | `B-01-opening`, `C-02-bar-first`, `D-02-bar-first` |
| 2 First visit: "What do you have?" (Q5) | present | present | present | bubble text logged: B "What do you have? My shelf is looking thin.", D "What do you have?" |
| Q5 photos → list | faked, present | faked, present | faked, present | `B-03-found-barware`, `D-03-photo-step`, `D-03b-found-barware` |
| Q5 two routes (own API key / paste prompt) | **missing** | **missing** | partial: a paste link that fakes a read, and no API-key route | grep `api key\|paste\|your own ai` finds 0 hits in B/C `app.js`; B/C behaviour: `openPhotos()` (`app.js` ~370) offers only "Read these photos". D `index.html:787` `pasteL` simply calls `readLabels()` |
| Q5 barware tick list | present (6 tools) | present | present (12, including glasses) | D ticks logged: "Shaker tin … Mugs"; B `logic.js:34` |
| 3 Tap shelf → shelf by Family (Q6) | present, as a text list | present | present, as a text list | B `openShelf()`; D `openShelf()` line 776 |
| Q6 brand-family bottle art | partial: 7 family silhouettes, no brand family | partial | partial: procedural bottles | B `draw.js:40` `BOT` (one path per spirit family); D `makeBottle` line 363 |
| 4 Menu zoom: spirit · feel · A–Z (Q11) | present | present | present (camera flies to the 3D menu) | `B-05-menu`, `D-rm-05-menu` |
| Q4 "Feel", four feels | present | present | present | `logic.js:6` FEELS; D FEEL4 |
| 5 Talk = search, bubble + mic (Q3) | present | present | present | `B-10-talk-q1`, `D-rm-10-talk-q1` |
| Q11 up to four skippable questions, stops at a handful | **partial**: opens off-brief with "What are you after tonight?" plus Warm me up / After dinner, then spirit→feel→moment→strength | partial (same) | **present**: "Got a spirit in mind? Whisky Gin … Skip", then the occasion | logged talk1 for B and D; `logic.js:153` `start()` |
| Q11 strength includes none/low | present | present | present | `logic.js:30`; D `OPTS.strength` |
| 6 Tap Dionysus → story | present, from drinks you can make | present | present, but picks from **all** stories, makeable or not | B `app.js` `tellStory` filter `canMake(r)`; D `index.html:771` has no filter. `D-rm-09-story` (Mamie Taylor) |
| 7 Barman's choice: panther bats the dice | present (tap the panther) | present | present (tap the dice only; the panther has no `userData.tap`) | `B-08a-dice-mid`; D `index.html:408` gives only `dice` a tap tag |
| 8 Recipe in front, he makes it behind (Q12) | present | present | present | `B-06-recipe-2taps`, `D-40-perf-1` |
| Q12 swap, never hidden | present | present | present | B "No muddler? Use the end of a rolling pin."; D three swap lines |
| Back: zoom out to the bar | present | present | present | B/C `screen=home` logged after back; `D-rm-07-back-home` |
| Q7 muted / touchable | see criterion 3 | | | |
| Q8 finish setting | present | present, but the finishes are hard to tell apart | present, but painted and living look alike | `M1-looks-BC`, `M3-D` |
| Q9 coverage + adult gate | present | present | present (glimpse barely visible) | settings text logged for all three |
| Q9+ attributes as tools | present: thyrsus, vine, lemon, mint, honey, kantharos | present | present | `logic.js:171` ACTION_LABEL; D step tool labels in `D-rm-06` |
| Q9+ golden rim | **missing** | **missing** | present (15% chance) | grep `golden\|gold` finds 0 in B/C `app.js`; behaviour: no rim code in `drinkGlass`. D `index.html:654` `M.gold` torus |
| Q7 patrons | missing | missing | missing | grep `patron\|customer` finds 0 in all three (deferred to issue #4) |
| Q10 real 34 recipes | present | present | present | `.drink` count = 34 in every menu |

**Bug, B and C:** "Nothing fits all of that. Here's what's closest." can be followed by **no drinks at all**. `logic.js:136–143` drops only the last answer and returns `matches(a).slice(0,6)`, which can still be empty. Logged: `B typed: Nothing fits all of that. Here's what's closest. | Start again`. Screenshot: `B-12-talk-typed`. D handles this case by dropping keys one by one and re-asking (`index.html` `ask()`).

**Scores:** B 4, C 4, D 4. D covers more of Q5, Q9+ and Q11. B and C keep the story to drinks you can make and have the stronger domain module.

## 2. Dionysus

- **B:** flat, warm colour, the clearest face, and polishing a glass with the fawn skin at rest (`B-02-bar-first`). The finishes are clearly different: painted, white and living each read at a glance (`M1-looks-BC`, top row). Cheeky is a fig leaf with a vine passing in front, so it is implied, as Q9 asks. The builder's own weak spot is visible: arms are plain tubes and the pose is stiff. Score 3.
- **C:** reads as a painted shop mannequin, with cylinder arms and a peg neck (`C-04-bar-stocked`). The finishes barely differ under the heavy grain and dark grade (`M1-looks-BC`, bottom row: painted and living are nearly the same). He is the least lively of the three. Score 2.
- **D:** the most lifelike and the most impressive at rest (`D-02-bar-first`). He breaks badly once he works. In `D-40-perf-1` the reaching arm stretches, the torso balloons, and the cloak tears into red patches. Painted and living finishes look almost alike (`D-41-look-living-classical` against `D-02`). In white/modest his cloak seems to disappear (`D-41-look-white-modest`). In cheeky I cannot see any difference from classical (`D-41-look-painted-cheeky`), which matches the builder's "barely visible". Score 3: the best ceiling, but the worst failure at the moment that matters.
- In every prototype the recipe screen blurs him: B `blur(5px)` (logged), D `filter:blur(3.2px)` (`body.dof #c`). "He makes it behind" is therefore mostly unseen (`B-06-recipe-2taps`, `D-rm-06-recipe-2taps`).

## 3. Touchable versus muted

- **B:** clearest. Green menu, white dice, a black panther with green eyes and a colourful Dionysus, against a brown-black wall and counter (`B-02-bar-first`). Scene hit boxes: menu 108×104 px, panther 260×82 px (logged bounding boxes). Score 4. Dionysus does use a counter-honey action ("Honey wells up from the counter"), and the counter is muted. That is in the brief (Q9+), but it conflicts with Q7 (see the section on the brief).
- **C:** everything sits in one brown grade. Even the stocked shelf bottles are dull (`C-04-bar-stocked`). The dice is a 28×28 px `div` that is almost invisible behind the panther (logged `DIV#dice 28x28`). Score 2.
- **D:** breaks Q7 visibly. Non-touchable things carry the strongest colour on screen: the red velvet curtain, red stools, bright lamps and an orange-lit back bar (`D-04-bar-stocked`). The real touchables are small. Probed hit areas: menu 60×76 px, **dice 22×16 px**, **panther not tappable at all** (probe: "panther none"; `index.html:408` tags only the dice). A 22×16 px target is well under the usual 44 px minimum for touch. On the phone, the menu and dice drop out of frame (`D-42-phone-bar`). The page leans on the HUD hint pills ("Tap the menu, Talk to him, Roll the dice…") to make up for it. Score 2.

## 4. Spatial model, three taps, readability

| | B | C | D |
|---|---|---|---|
| Taps home → recipe via menu | 2 (menu, drink) | 2 | 2 (menu object, drink) |
| Barman's choice | 1 | 1 | 1 (dice) |
| Back returns to the bar | yes | yes | yes, camera flies back |
| Step text size, 1280×800 | **15px** | **19px** | **15px** (`index.html:107`) |
| Recipe title | 46px | 46px | 34px |

- **None is readable from a metre.** On a 10.1" 1280×800 tablet (about 149 CSS px per inch, an assumed device), 15px type is about 2.6 mm per em and 19px about 3.2 mm. A common rule of thumb for comfortable reading at 1 m is letters about 6–7 mm high, roughly 36–40px. *Unverified hypothesis; no empirical evidence established.* It needs a check with a real tablet at a real counter.
- Steps advance themselves on a timer: B every 3.6 s and looping back to step 1 (`app.js:516` `STEP_S = 3.6`, `recipeTick`); D's `perfTick` loops too. Someone following along at a counter can't keep that pace. Tapping a step does jump to it in B (`#steps li` onclick).
- **"From bottles actually in the house"** fails at the edges. When fewer than 3 drinks are makeable, barman's choice draws from all 34 (`logic.js:87` `if (pool.length < 3) pool = R`). D does the same when 0 are makeable (`index.html:757`). The menu always lists all 34, with "Needs …" on the 13 you can't make (logged `need: 13`). With the example inventory, I sampled 300 barman's choices and got 0 unmakeable picks in B and C (logged `cantMake: 0, makeable: 21`).
- C's step V is cut off behind the buttons at 1280×800 (`C-06b-recipe-later`). That could be partly my fallback font.
- Scores: B 3, C 3, D 3. Each meets three taps; each fails the one-metre test.

## 5. Tablet and phone

| | B | C | D |
|---|---|---|---|
| Weight loaded | **0.11 MB** | 0.12 MB | **2.20 MB** (mesh file 1.39 MB plus three.js) |
| rAF rate in this container | 60.7 fps | 24 fps (canvas grain repaint) | 2.7 fps (SwiftShader; not a GPU verdict) |
| Renderer cost signals | SVG | full-stage canvases | PCFSoft shadows, 1024 shadow map, antialias, 39,344-vertex skinned mesh (`index.html:241–245,333`; `dionysus-mesh.js` `"n":39344`) |
| Reduced motion | static (two screenshots 1 s apart identical) | static | honoured: flights snap, `RM` check at line 205 |
| Console errors (apart from my font block) | none | none | none besides GPU stall warnings |
| Phone 390×844 | sign clipped to "IONYSU" (`B-21-phone-bar`); panther box runs to x=404 > 390; recipe buttons cover step 1 (`B-23-phone-recipe`) | scene shrinks into the top half with an empty bottom half (`C-21-phone-bar`); recipe shows no steps in the first screen (`C-23-phone-recipe`) | menu, dice and panther cropped out (`D-42-phone-bar`); **recipe is the best of the three**, with steps visible at once (`D-43-phone-recipe`) |
| Horizontal scroll | none (scrollWidth 390) | none | none |

The neon text in B also spills past its sign board at tablet size (`B-02-bar-first`: letters run from x≈160 to 1110, the board from 290 to 990).

Scores: B 4, C 2, D 2.

## 6. Base for the real app

- **B:** separates the domain (`logic.js`: Feels, Moments, Strength, swaps, Conversation, barman's choice) from rendering (`draw.js` SVG strings, `app.js` scenes). There are `window.proto` hooks for tests. Bottle art is an SVG path per family (`draw.js:40` `BOT`, `:44` `bottle()`), so issue #3's hundreds of bottles become data: a path, a colour and a label layout for each brand family. Patron vignettes (issue #4) slot in as more SVG groups. Weaknesses: `data.js` is a copy of `src/data.js` (drift risk), `app.js` is a 38 KB file of globals, and the arms need a real rig.
- **C:** the same domain layer as B, but its art is procedural canvas painting (`paint.js`, 20 KB). Each new bottle or patron has to be hand-coded as paint calls, and it costs repaint time (24 fps here). Score 3.
- **D:** reads `src/data.js` directly (good: no copy). Everything else is one 102 KB HTML with lines up to 422 characters and logic and rendering mixed. Hundreds of bottle artworks would mean 3D assets or textured meshes. Patron vignettes would need more rigged characters, and the one rig D has already tears its cloak. Score 2.

---

## Recommended base: **B, illustrated**

B is the only one that is clear, light and honest about touchables, and it has a domain layer the real app can keep. Its weak spot (tube arms, stiff poses) is a drawing problem inside one SVG group. D's weak spots (a mesh that tears, heavy GPU cost, touchables too small to tap, touchables lost on the phone) are architectural.

## Grafts

1. **From D: the Q11 conversation.** Open with "Got a spirit in mind?" and walk spirit → feel → moment → strength, keeping the off-brief "What are you after tonight?" opener only as typed input. When nothing fits, drop answers one at a time until something does (D `ask()` around line 701). This also fixes B's empty "Here's what's closest" bug (`logic.js:136–143`).
2. **From D: the phone recipe layout and the data source.** D's recipe sheet shows the steps in the first phone screen with the tool line under each step (`D-43-phone-recipe`). D also loads `../../src/data.js` instead of a copy (`index.html:198`).
3. **From D: the Q5 paste route and the golden rim.** D has a "Paste a list from your own AI tool" link (line 787) and a 15% golden rim (line 654). B has neither.
4. **From C: the bigger step type and the "He makes you" header.** C's 19px is the floor to start from, not the target; the target is about 36px for the step currently showing.

## What the brief got wrong or left under-specified

- **"Readable from a metre" has no size.** All three ship 15–19px steps. The brief should state a minimum, for example "the current step at ≥ 36px, one step at a time" (hypothesis, to test on the real tablet).
- **"Recipe in front, he makes it behind" fights itself.** The card covers half the screen and the scene behind it is blurred in every build, so the show is mostly unseen. Decide which wins on the recipe screen: Dionysus beside one big step, or the full card.
- **Who moves the steps on?** Every build auto-advances on a timer. The brief should say that the reader taps, or that steps advance only when he finishes an action and then wait.
- **Thin shelf.** "Barman's choice = from what you can make now" doesn't cover 0–2 makeable drinks. The builds fall back to all 34 (`logic.js:87`, D line 757), which breaks the epic's "bottles actually in the house". The menu also lists unmakeable drinks. The brief should say whether those are shown, greyed or hidden.
- **Q7 against Q9+.** "Honey from the counter" makes Dionysus touch the muted counter. Q7 says he touches only touchables. Pick one.
- **Q7 needs a colour budget.** D followed the owner's references (red curtain, red stools, lit back bar) and so broke "the rest muted". The brief should list what non-touchable colour is allowed, if any.
- **"Phone gets a cropped, taller view"** says nothing about keeping touchables in frame. D's crop drops the menu and dice; B's crop clips the sign.
- **Story pool.** The brief doesn't say whether stories come only from drinks you can make. B and C filter; D doesn't.
- **Strength rule.** D labels the Penicillin "strong" and B labels it "regular strength" (`D-rm-06-recipe-2taps`, `B-06-recipe-2taps`). The glossary names the four levels but no thresholds.
- **Patrons** appear in Q7's touch rule but no prototype has one. Keep issue #4 linked from the brief so nobody reads it as built.
