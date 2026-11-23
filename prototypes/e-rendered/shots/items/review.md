# Independent visual review: rebuilt touchables (after round 1)

Looked at 01, 02, 04, 04b, 05, 06, 06b, every before/after crop, the raw layers (composited over green to check alpha), the builder previews and `measure/saturation.json`. Zoomed crops are in the scratchpad `review/` folder.

Overall: a big step up from the toys. Glass, liquid, paper labels, closures, leather and drilled pips all exist now. Each item still has one or two loud tells.

## Bottles
- **Verdict.** Home (01, 06): **nearly**. They read as a back-bar of bottles. Close-up (05, sheet): **nearly**. Up close, the tells below take over.
- **What gives them away**
  - **Pink neon smear on every shoulder.** *Confirmed: the worst tell.* It is a mottled magenta "dripping icing" texture, not a crisp tube reflection. It sits identically on all 26 shoulders (sheet, 05 left half). Real neon would show as a thin, sharp line on a few bottles only.
  - **Labels are the brightest flat area on the shelf.** *Confirmed.* They are cream, evenly lit and square to camera, with no curvature falloff toward the edges, so they read as stickers on a flat card (05, home shelf crop). The shelf's V of 0.61 is driven by the labels.
  - **Clear spirits look smoked, not clear.** Vodka, gin and white rum read grey-blue or dark. The glass is fully opaque in alpha (90–94% of pixels are alpha 255), with a dark baked background inside it, so the real wall and sunburst never show through the glass. Over green, the "empty" neck and shoulder are near-black.
  - **Clones.** The five whiskies at left are the same silhouette in the same pose, all square to camera. The Islay bottle has a white teardrop specular blob just above its label.
- **Edge and compositing**
  - A thin bright cream outline traces every silhouette (visible on green and at 05). Most of this is the rim light at full strength on a downsampled edge. On top of it sits the hover "lit" glow in 05 (yellow fuzz, `brightness(1.16)`, from the CSS), which makes the shelf look like stickers again.
  - Bottles still touch each other in the whisky group. The 2 px CSS drop shadow is adequate.
- **Colour rule.** True colour now comes through the liquid, which is right. The labels and the pink smear are what make the shelf loud, not the spirits.

## Honey jar
- **Verdict.** Home: **nearly**. Close-up (04, layer): **no, not quite**. It looks like a glowing lamp jar.
- **What gives it away**
  - **Two glowing horizontal slabs inside the honey.** A lens-shaped hot ellipse sits mid-jar, with a bright bar near the base (honey-foot crop, layer). They read as an emissive element or a candle inside, not as light through honey. This is the main tell.
  - **Shoulder glints.** *Confirmed.* The honeycomb emboss on the shoulder sparkles as a busy lace or doily band, with a clipped white glint where the dipper enters (04).
  - The dipper is good. It is turned, with a visible grooved head.
- **Edge and compositing**
  - The bright cream rim line at the base is lighter than the counter, so there is no dark contact line and the jar floats slightly (home).
  - The yellow CSS halo when the jar is the lit ingredient (04, 04b) re-introduces the sticker look.
- **Colour rule.** It fails "not garish". The jar has the highest chroma of any touchable (0.434, against 0.254 for the leopard). The saturated orange core comes from the glow slabs.

## Menu
- **Verdict.** Home: **yes, nearly**. It is the most convincing item. Close-up (layer, 05): **nearly**.
- **What gives it away**
  - **The brass lip reads muddy.** *Confirmed.* It is a brown strip with dark blotches (layer bottom, menu-foot crop): dirty bronze, not polished brass. There is no clean highlight line.
  - **The base plate under the stand is paler than the counter.** It reads as a second tan step, with no dark contact line.
  - The face is dead square to camera and evenly lit, so it reads as a flat print. It has no lean, no gradient and no edge thickness at home size.
  - **Vine device.** *Confirmed.* At home size the grape cluster becomes a yellow triangle blob (01, 06), and the two leaves become stars.
- **Colour rule.** Passes. The green is deep and the gold is metallic with grain; the gold foil itself is good.

## Die
- **Verdict.** Home: **no**. It is nearly unchanged from before (dice before/after crop). Close-up: **nearly**.
- **What gives it away**
  - **It reads as pale wood.** *Confirmed.* The horizontal streaky grain is birch, not bone, and the top face is flat and overexposed.
  - **Scale.** It is still about 30 px, roughly 14 cm against the leopard. That is still the biggest "toy" cue on the counter.
  - The face layout is now valid (1, 3 and 5), and the drilled red pips are good.
- **Edge and compositing.** The contact shadow is only a hairline (preview and home). The die floats a little.
- **Colour rule.** Passes, but it is a large near-white block. Bone mid-tones would sit better.

## Fix list for one round (most valuable first)
1. **Kill the pink shoulder smear on the bottles.**
   - How: make `neonwash` invisible to glossy on the bottle layers, or keep only a thin, sharp reflection on 3–4 bottles nearest the sign.
   - Payoff: the biggest single change. It touches all 26 bottles and every screen.
   - Risk: low. It needs only a bottle re-render.
2. **Calm the labels.**
   - How: bring the paper down about 25% in value, warmer (about `#d6c6a2`), with cylindrical falloff toward the label edges. Add a 5–15° turn on some bottles.
   - Payoff: the shelf stops being the loudest block, and the labels read as paper.
   - Risk: low.
3. **Remove the honey's two glow slabs and desaturate the honey.**
   - How: find the light patch or emissive being refracted (likely the fake caustic or counter patch). Darken the core absorption so the glow stays at the thin edges only.
   - Payoff: it turns the lamp into a jar, and fixes the garish chroma.
   - Risk: medium. Glass and volume tuning needs a couple of iterations.
4. **Fix the die.**
   - How: change the material to bone (fine speckle, not directional grain; slight edge yellowing; gentle subsurface). Shrink it about 40% and keep the tap target in the CSS hit area. Strengthen the contact shadow.
   - Payoff: removes the clearest remaining toy cue.
   - Risk: low to medium. The scale change touches layout and hit area.
5. **Glass alpha and edge.**
   - How: either render the bottles and the jar over the real shelf and wall plate (so what you see through the glass is the actual wall), or output true transmissive alpha. Halve the rim light so the cream outline becomes a thin edge glint.
   - Payoff: clear spirits look clear, and the sticker outline goes.
   - Risk: medium to high. It affects the compositing pipeline.
6. **Menu brass.**
   - How: make the lip polished brass (roughness about 0.15, no blotch texture) with one clean highlight line. Darken or remove the pale base plate and add a tight contact shadow.
   - Payoff: the most convincing item goes to "yes".
   - Risk: low.
7. **Simplify the menu's vine device.**
   - How: use 6–7 larger grapes with a dark keyline, or drop the leaves, so it survives at about 40 px.
   - Payoff: small but visible on phone and home.
   - Risk: low.
8. **Honey shoulder emboss.**
   - How: roughen the honeycomb emboss (glass roughness about 0.15 on the band), or make it shallower, so it stops sparkling. Clamp the clipped glint at the dipper entry.
   - Payoff: a quieter, more expensive-looking jar.
   - Risk: low.

Out of scope here, but worth flagging to the UI owner: the yellow CSS "lit" glow (05 shelf, 04 honey) undoes much of the grounding. A tighter, lower-alpha glow, or a brightness-only highlight, would help every item.
