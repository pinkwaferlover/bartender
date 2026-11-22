# Judge: two critiques of the Dionysus bar prototypes

Judged against `bartender/docs/process/dionysus-journey.md` (Q1–Q12) and the epic test: on the kitchen tablet, pick a drink in three taps or fewer, from bottles actually in the house, and read the recipe from a metre away. Both critiques read end to end before scoring.

## Verification Gate

- **Critique.** The strongest reason this could be wrong: both critics ran the same container (software WebGL, fonts blocked), so they share the same blind spots. Neither saw D on a real tablet GPU, and nobody has read any recipe from a metre on a real screen. Their agreement on "B" is partly agreement on what a CPU renderer shows. It does not settle how D's figure feels on real hardware.
- **Framing.** The critiques do not diverge wildly. Totals are B 22/22, C 15/16, D 17/16, and the base pick is the same. The one real split is D's Dionysus (A 4, B 3), and it comes from evidence, not framing: A could not catch the reach and marked the tear "not verified"; B caught it with motion on (`D-40-perf-1`). B's score stands.
- **Rubric.** No rubric for judging critiques was supplied, so I used the six below. Defines a format, not yet wired: nothing downstream reads these scores.
- **Empirical grounding.** The 36–40 px "readable at a metre" figure is critic B's rule of thumb. *Unverified hypothesis; no empirical evidence established.* The cost estimates in the recommendation are my judgement, not measured.

## What I checked myself

| Claim | Critic | Source | Result |
|---|---|---|---|
| D breaks Q7: the red curtain, red stools and orange back bar outshine the touchables | A | `A-shots/d-tab-4-stocked.png` | **Confirmed.** The menu is a small dull card at the far left, and the dice is a speck. Hint pills patch it. |
| D's panther can't be tapped | A | D `index.html:667` | **Confirmed.** `panther` is in the raycast list, but nothing gives it `userData.tap` (lines 290–480 tag shelf, menu, dice and dio only). |
| D's mesh stretches and tears when he reaches | B | `B-shots/D-40-perf-1.png` | **Confirmed.** The torso balloons into a smooth egg, the forearm stretches, and the cloak breaks into red patches. |
| B/C: "Here's what's closest" can return nothing | B | B `logic.js:136–143` | **Confirmed.** It drops only the last answer, then returns `matches(a).slice(0,6)` with no check for empty. |
| B/C: barman's choice falls back to all 34 when fewer than 3 can be made | B | B `logic.js:87` | **Confirmed.** |
| B step text is 15 px | both | B `style.css:114` | **Confirmed.** D `index.html:107` is also 15 px. |

**Two things neither critic caught:**

1. **D's "drop answers until something fits" loops forever.** Critic B recommends grafting it. In `ask()` (D `index.html:704`), `last=[...T.asked].pop()` reads a copy, so `T.asked` never shrinks. If dropping one answer still leaves nothing, it drops the same key again every 1.3 s and keeps saying "Let me drop the feel". Take the idea, not the code.
2. **D also opens off-brief.** Its home bubble offers "Warm me up / After dinner" (`index.html:718`), the same as B's. Critic B scored D's Q11 "present" and B's "partial". Critic A was right that both stray from the four agreed questions.

## 1. Scores for each critique (1–5)

| Criterion | Critic A | Critic B |
|---|---|---|
| Evidence and reproducibility | **5**: a shot, file:line or grep behind every row, with scripts saved, plus measured saturation per region. | **5**: the same, plus hit-box sizes and a motion-on performance run of D. |
| Accuracy | **4**: no errors found. It scored D's figure 4 while flagging the tear as unverified, which is honest but too generous. | **4**: it caught the tear, but overstated D's Q11 and offered D's looping `ask()` as a fix. |
| Coverage of the brief and the epic test | **4**: full Q1–Q12 table. It missed the thin-shelf fallback that breaks "bottles in the house". | **5**: also found the empty "closest" bug, the thin-shelf fallback, the story pool, timer-driven steps and touch targets under 44 px. |
| Weight given to the owner's taste (a lifelike, animated Dionysus) | **3**: it says "fix it inside B's SVG" but gives no cost and no route to lifelike. | **3**: it calls the arms "a drawing problem inside one SVG group" and doesn't face the owner's "lifelike". |
| Actionability of the recommendation and grafts | **4**: four concrete grafts with sources, and a measurable test for "muted". | **4**: four concrete grafts, but graft 1 carries D's bug. |
| Quality of the brief changes | **4**: a size number, a "muted" check, talk taps, the fifth axis, strength. | **5**: adds who advances the steps, the thin shelf, the counter clash between Q7 and Q9+, keeping touchables in the phone crop, and the story pool. |
| **Total /30** | **24** | **26** |

## 2. Base critique: Critic B

**Why.** B found more of the defects that fail the epic test itself: barman's choice and the menu leave the house's bottles, steps run on a timer you can't follow at a counter, and D's dice is a 22×16 px target. It also verified D's tear instead of leaving it open. Its brief list is the more complete one.

**Grafts from Critic A**

| Graft | Source |
|---|---|
| Talking takes 5 taps, so the main search fails the three-tap test | A §4, the "Bar → recipe via talking" row |
| A measurable "muted" rule: no untouchable region more saturated than the least saturated touchable | A §3 (HSV table), "What the brief got wrong" |
| Hint pills on the first stocked visit, Escape for Back, a "needs Double cream" flag on menu rows | A, grafts 2–3 (`index.html:727-728`, `row-d-phone.png`) |
| Q11 grew a fifth axis ("warm") in **all three** builds | A §1 and the brief list (corrects B) |
| D has no low-power path: `dt` capped at 0.05 s, so a weak tablet plays everything in slow motion | A, frame-rate caveat (`index.html:822`) |
| D's cheeky glimpse is unverified either way | A §2 |
| C shows no pointer cursor on its canvas; B's cobweb has a stray pointer cursor | A §3 |

## 3. What both critics found on their own (the strongest signal)

1. Build on **B (illustrated)**: same total, 22/30.
2. B and C share their domain code byte for byte (`logic.js`, `data.js`, `draw.js`, `stories.js`, `inventory.js`), so C adds only a heavier renderer.
3. **No build passes "read the recipe from a metre"**: steps are 15 px (B, D) and 19 px (C).
4. **"Recipe in front, he makes it behind" undoes itself**: every build blurs him, so the Q9+ bar-tool show is mostly unseen.
5. **D breaks Q7**: the red curtain, red stools and lit back bar outshine small, dull touchables.
6. **D's panther can't be tapped.** Only the dice rolls barman's choice.
7. Q5's second route (paste into your own AI tool) and the 15% golden rim exist **only in D**.
8. **No patrons** in any build (issue #4).
9. **Strength is inconsistent**: the Penicillin is "regular" in B and "strong" in D. No rule exists.
10. **C's Dionysus is a mannequin**, and its finishes are hard to tell apart.
11. **B's Dionysus is stiff**: tube arms, a four-line face.
12. **D's figure is the most lifelike at rest**, but D is heavy (2.2 MB, 1.39 MB of mesh) and is one 858-line file.
13. **B's phone view clips the sign** to "IONYSU".
14. Both say the brief needs **a minimum step size** and a decision on the recipe screen against the show.

## 4. Recommendation

**Build on B: its scene, its domain code, its SVG bar.** It is the only build that is light (0.11 MB, 60 fps), honest about touchables, and split cleanly into logic, data and drawing. Neither critic's evidence supports building on C or D.

**Dionysus is where the owner's taste and the evidence part ways.** B's figure is the stiffest, yet the owner wants him lifelike and the most animated thing on screen. So, plainly: **build B's scene now with Dionysus behind one swappable figure layer** (one interface: `pose(action, progress)`, driven by `logic.js`'s `actionFor`). Ship a redrawn SVG figure first, and decide the lifelike route as open question 1 below. Costs are my estimates, unmeasured:

| Route for Dionysus | What it buys | What it costs |
|---|---|---|
| Redrawn SVG rig in B (real elbows and wrists, layered shading, a face with expression) | Colourful, light, animates freely, fits the scene's style | About 1–2 focused sessions. Will read as an illustration, not lifelike. |
| D's 3D statue in its own transparent canvas over B's SVG bar | The lifelike look the owner liked | About 2.2 MB and a real GPU. The tear needs reskinning, or the cloak as its own mesh. Needs a fallback for weak tablets. A realistic statue in a flat scene may clash. A spike of 1–2 sessions, with a pass/fail test, before committing. |
| Frames of the statue rendered from D's model (or painted) into sprite sheets, placed in B's scene | A lifelike look at B's weight | Animation only as rich as the frames drawn. Needs a render pipeline for every tool action (9 or more). |

**Grafts and fixes, in priority order**

1. **The recipe from a metre.** One current step large (at least 36 px, a hypothesis to test on the real tablet at a real counter). Steps advance when you tap. No timer and no looping back to step 1. *Source: both; the size from Critic B.*
2. **The recipe screen shows him working.** Card on the left, Dionysus unblurred on the right doing the current step. D's tablet layout (`D-40-perf-1`) is already close. *Source: both critics' brief notes, plus my look at `D-40-perf-1`.*
3. **A better Dionysus, behind a swappable layer.** Redraw the SVG rig now. Owner question 1 picks the lifelike route. *Source: both on the stiffness; the hybrid is mine.*
4. **From the bottles in the house.** Barman's choice never falls back to all 34. A thin shelf follows owner question 3. *Source: Critic B (`logic.js:87`).*
5. **Talking fits in three taps** and follows Q11: open with the spirit question as chips, and let any chip lead straight to a shortlist. When nothing fits, drop answers one at a time. Take D's idea, but fix its loop (remove the dropped key from `asked`) and B's empty "closest" result. *Source: Critic A on taps; Critic B on the bugs; the loop is mine.*
6. **Touchables you can find and hit.** Every target at least 44 px. Hint pills on the first stocked visit. The phone crop keeps the menu, dice, panther and the whole sign. A "muted" saturation check. Escape for Back. *Source: Critic B on targets; Critic A on pills and the check; D's code.*
7. **Q5's two routes**: D's paste link, plus the own-API-key route that no build has. *Source: both; D `index.html:787`.*
8. **Small grafts from D**: the 15% golden rim (`index.html:654`), "needs X" on menu rows, and loading `src/data.js` instead of a copy. *Source: both.*

## 5. Changes to the brief

- The current recipe step is at least 36 px on the kitchen tablet, one step in focus, always above the buttons. Confirm the number at a metre on the real device.
- Steps advance when you tap. He acts out each step, then waits. No timer.
- The recipe screen: card on one side, Dionysus unblurred on the other, doing the step shown.
- The three-tap test covers talking too, not only the menu and barman's choice.
- Barman's choice and stories come only from drinks you can make now. A thin shelf follows owner question 3.
- The menu shows drinks you can't make, marked "needs X" (owner question 5).
- "Muted" is measured: no untouchable region more saturated than the least saturated touchable. List any allowed exceptions (the neon sign).
- Touch targets are at least 44 px. Every touchable, the panther included, can be tapped.
- The phone crop keeps every touchable and the whole sign in frame.
- Q7 against Q9+: honey comes from a touchable honey jar, not the counter (owner question 4).
- Q11 is the four questions. Say whether "warm me up" is a fifth (owner question 6).
- Write a strength rule (for example by ABV per serve) so every build labels a drink the same way.
- Q5 names both routes: own API key on the device, and a prompt pasted into your own AI tool. Say whether the fake camera step counts toward onboarding taps.
- Q8: the finishes must be told apart at a glance at tablet size (C failed this, and so did D's painted and living).
- Dionysus is one swappable layer with a fixed pose interface, so his drawing method can change without touching the scene.
- Keep issue #4 (patrons) linked beside Q7, so nobody reads patrons as built.

## 6. Open questions only the owner can answer

Written to be read aloud.

**1. How should Dionysus be drawn on top of B's bar?**
Option A: a better flat drawing, with real elbows, shading and expression. Light and colourful, but it will look illustrated, not lifelike.
Option B: the 3D statue from prototype D, placed over B's bar. The most lifelike, but heavy on the tablet. Its tearing must be fixed first, and it may clash with the flat scene.
Option C: frames rendered from the 3D statue, used like a flip-book in B's bar. Lifelike and light, but he can only move in the ways someone has drawn.
**My recommendation: A now, so the journey ships, with a short trial of B that passes only if he never tears across every bar action and runs smoothly on your actual tablet.**

**2. Who moves the recipe steps on?**
Option A: a timer, as now. Option B: you tap for the next step. Option C: he does each step and then waits for your tap.
**My recommendation: C.** You set the pace, and he still performs.

**3. When your shelf can make fewer than three drinks, what does barman's choice do?**
Option A: picks from every drink and offers swaps, as now. That breaks "from bottles in the house".
Option B: picks only from what you can make, and tells you so when there's little.
Option C: picks from what you can make, then adds one drink clearly marked "worth buying a bottle for".
**My recommendation: C.** It keeps the promise and still gives you a next step.

**4. Can Dionysus touch the counter, for the honey trick?**
Option A: yes, the counter is an exception to the rule. Option B: no, honey comes from a honey jar you can tap. Option C: drop the honey trick.
**My recommendation: B.** It keeps the rule and the trick.

**5. Should the menu show drinks you can't make?**
Option A: show them all, marked "needs this bottle". Option B: show them greyed out at the bottom. Option C: hide them.
**My recommendation: A**, matching your rule that a drink is never hidden for want of a tool.

**6. Is "warm me up" a fifth thing he asks about?**
Option A: add it to the brief as a fifth question. Option B: drop it. Option C: keep it only as something you can type or say, not a question he asks.
**My recommendation: C.** The four questions stay as agreed, and natural phrases still work.
