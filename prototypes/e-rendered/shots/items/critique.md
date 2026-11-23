# Item critique: why the counter and shelf props read as toys

Looked at: 01-bar, 02-menu, 04-recipe-step, 05-shelf, 06-phone-bar, every `before-*` crop, the raw layers (touch-menu/honey/dice, bottle-*, touch-panther), and `blender/build_bar.py`.

## Problems shared by every item (fix these first)

The leopard looks real because it has **surface information**: fur texture, roughness that changes across the body, small shadows in the creases, and a scale we recognise. Every hand-built item has none of these. Each one is one flat Principled colour on a smooth lathe or cube, lit by one big soft key light. That is the vinyl-toy / clay-render look.

1. **One material per object, no texture.** `mat()` sets a single Base Color, one roughness value and often a clearcoat (`coat=0.25..1.0`, coat roughness 0.08). It adds no roughness map, no bump, no fingerprints and no wear. Clearcoat over flat colour is the "plastic toy" material.
2. **Nothing is glass.** No material in the file uses Transmission. The bottles and the honey jar are opaque, painted solids.
3. **Lighting is a product-shot setup.** The `key` area light is 1100 W, 4 m wide, and sits in front and above. It puts one round white highlight in the same spot on every item (honey jar, every bottle shoulder, the die's top edge). There is no rim or back light, so glass edges, liquid and silhouettes never catch light. The only accent is the pink `neonwash`, which turns every bottle cap magenta.
4. **No grounding.** Touch layers are rendered with the world hidden from the camera (`set_visible` plus `film_transparent`). The counter and shelf are not in the layer, so no contact shadow or reflection is baked in. The background is rendered without the items, so they cast nothing there either. On top of that, `dice()` sets `visible_shadow = False`. Every item looks pasted on. The CSS glow halo (yellow fuzz around the honey jar and the shelf bottles in 04 and 05) makes them look even more like stickers.
5. **Render settings.**
   - `view_transform = 'Standard'` clips highlights to flat white blobs (the honey jar's dot, the bottle shoulders) and leaves saturated oranges and reds harsh. Use **AgX** (or Filmic) with a Medium-High Contrast look, and re-pick the colours under it.
   - `transmission_bounces = 2`, `glossy_bounces = 2`, `max_bounces = 4` are too low for glass with liquid inside. Each bottle has 4 surfaces: glass, liquid, liquid, glass. Use transmission 8–12, glossy 4–6, max 12, transparent 8.
   - Bottle layers render at **32 spp** and touch layers at 64 spp, then go through OIDN. The denoiser smears this into a waxy, plasticky surface. Use 256+ spp for small transparent layers, and add denoising albedo/normal passes (or turn the denoiser off for glass).
   - Caustics are off. That is fine, but use a fake: a light-path trick, or a soft coloured light patch under the bottles.
6. **Scale against the leopard.** Measured on 01-bar, the leopard's head is about 45 px (about 20 cm in life), so 1 px ≈ 0.45 cm on the counter:
   - die about 32 px ≈ **14 cm** (a real die is 1.6–1.9 cm)
   - honey jar about 60×80 px ≈ **27×36 cm**
   - menu about 110 px high ≈ **50 cm**

   Next to a photoreal animal these read as oversized toys. Either shrink them toward real size, or keep the tap-target size in CSS hit areas and not in the model.
7. **Shared fixes for a rebuild.** Use AgX. Add a warm low key from the side (from the sconce direction) plus a narrow rim light behind the counter for glass edges. For the touch layers, render a shadow-catcher counter (`is_shadow_catcher`) so each layer carries its own contact shadow and a faint reflection. Give every material a roughness texture (noise or grunge, 0.25–0.45 range) and a micro bump.

---

## Bottles (26 layers, 9 Family profiles)

**What makes them toys**
- **Opaque coloured plastic.** The body material is `mat('btl_'+colour, colour, 0.32, coat=0.25, spec=0.35)`. The Style colour *is* the bottle. There is no glass, no liquid, no fill line and no thickness, so whisky, rum and bitters look like painted wooden skittles. Gin and vodka come out as opaque cream: milk bottles.
- **Hard cone shoulders.** `PROFILES` are 7–9 straight points copied from prototype B's 2D SVG outlines, and `lathe()` adds no subdivision. Shoulders are straight cones joined at sharp angles, with smooth shading over 40 segments. Real bottles have an S-curve from shoulder to neck, a heel radius at the base, and a lip or finish at the top. None of these exist here.
- **Labels are coloured stripes.**
  - `LABEL_BAND` makes one bare cylinder per band, 0.004 BU off the body: no paper, no edge thickness, no print, no curl. They read as painted rings.
  - **Bug: brandy.** `r_at()` searches the profile from the base, and for brandy it picks a radius smaller than the body where the band sits. The dark band is buried, so the cognac and amaretto label shows as a thin brown pinstripe (bottles-sheet, positions 1, 7, 10).
  - **Bug: bitters.** For bitters `r_at(44)` returns the neck radius (3). The famous oversized wrap label is buried inside the body, and only a pale ring shows at the neck. Angostura has lost its one recognisable feature.
- **One cap for every bottle.** `cap` is the same matte `#1c1410` cylinder (neck radius + 1.2) on every family. No cork, foil, screw-cap knurl, wax or crown cap, and the pink neon turns it magenta.
- **Shelf layout.** All bottles sit at the same height, touching each other, with no shelf shadow. Same-family bottles are identical clones that differ only in hue (the five whiskies on the left of 05).

**Touchable true colour vs muted bar.** The shelf is the most saturated block in the frame: 12+ orange and red bodies plus bright cream labels. Because colour is carried by opaque paint and not by liquid behind glass, it looks like candy and not like the drinks' real colour. Real spirits seen through glass in low light are darker and richer, and would sit in the muted bar while still being "true colour". Clear spirits (gin, vodka, white rum, tequila blanco, soda, tonic) should be nearly invisible clear glass with a label. At the moment they are the brightest objects on the shelf.

**Rebuild directions (priority order)**
1. **Glass shell plus liquid volume.**
   - Glass: Transmission 1, IOR 1.5, roughness 0.02–0.05, tinted per family only where real (green gin and Islay glass, amber cognac, brown bitters).
   - Wall: solidify 2–3 mm, a thick base with a **punt** for wine-style bottles (vermouth, aperitif), and a heavy flat base for whisky.
   - Liquid: a separate inner mesh (IOR 1.33–1.36, Volume Absorption in the Style colour, density tuned so whisky shows amber at the edges and darker in the middle), filled to a **fill line** about 85% up the shoulder, with a meniscus.
2. **Real silhouettes per family.** Use 20–30 point profiles or bezier lathes with subdivision:
   - whisky: square-shouldered decanter, or a squared body with a short thick neck
   - gin: tall, straight, square-section or faceted
   - rum: short stocky body with a long neck
   - tequila: tall, tapered body with a wide flat base
   - brandy: wide round belly, narrow neck
   - aperitif and vermouth: slim wine-bottle shape with a long neck and punt
   - bitters: small, oversized paper label, dasher cap
   - mixer: short crown-cap glass bottle

   Add a lip or finish ring and a heel radius on every bottle.
3. **Labels as paper.**
   - A separate mesh that follows the body (shrinkwrap, not a cylinder), about 0.2 mm thick with a visible edge.
   - Off-white paper with a fibre bump and roughness 0.6–0.8.
   - A family-specific layout drawn as texture with no words: a border rule, a crest-like ornament, a stripe, embossed or foil-stamped areas (metallic gold or bronze with a bump).
   - Fix `r_at()` so every band sits on the body's real radius at both ends.
4. **Closures per family.**
   - natural cork with a wooden or black T-top (whisky, brandy)
   - aluminium screw cap with knurling and a perforation ring (gin, vodka, rum, vermouth)
   - wax dip (some bourbon)
   - foil capsule (aperitif)
   - crown cap (mixers)
   - plastic dasher (bitters)
5. **Embossing.** Shoulder or base embossed patterns (raised glass ridges and dots, no lettering) via a displacement or bump map on the glass.
6. **Light the glass from behind.** Use the existing `undershelf` light plus a narrow rim light so each bottle gets bright edge lines and a liquid glow. Glass is drawn by its edges, not by a front highlight.
7. **Arrangement.** Vary heights by family, leave 5–15 mm gaps, add a slight turn so labels are not all square to camera, and render a contact shadow plus a faint reflection on the shelf.
8. **Render quality.** At least 256 spp per bottle layer, and render at 2× the displayed size and downsample, so the thin neck and highlight edges stay crisp.

---

## Honey jar

**What makes it a toy**
- **The jar is solid honey.** `body` uses `M_HONEY = mat('honey', '#e0951c', 0.12, coat=1.0)`: an opaque saturated orange with a full clearcoat. There is no glass, no honey seen through glass and no air gap at the top. Under Standard view it reads as an orange plastic pot or a paint tin, with one clipped white highlight dot (04).
- **The lid looks like whipped cream.** `cloth` is a smooth lathe dome in cream (`#f0e7d8`, rough 0.7). There are no folds, no fabric weave and no overhang drape, so it reads as a marshmallow or a cartoon froth top (before-honey-recipe).
- **The twine is invisible.** Its torus has `major_radius=0.235`, but the cloth is 0.25–0.29 wide. The red twine (`M_TWINE`), which was the one thing that sold "cloth tied over a jar", is buried inside the cloth.
- **The dipper is a stick.** It is a 16-segment cylinder with radius 0.022. The grooved `dipperhead` sits at negative height, so it is buried in the jar and only a plain smooth stick pokes out: a lollipop stick or straw, uniform tan (`#b98552`) with no grain.
- **Silhouette and scale.** The profile is a squat barrel with a tiny shoulder, and at about 27 cm wide it is as wide as the leopard's chest. There is no contact shadow, and the yellow CSS halo makes it float (04).

**Colour rule.** It passes "true colour", but too loudly. Opaque `#e0951c` with clearcoat is the most saturated, most specular object on the counter. Real honey in low warm light is dark amber at the core, glowing gold only where light passes through the thin edges. That reads richer and sits better against the muted bar.

**Rebuild directions**
1. **A glass jar with honey inside.**
   - Glass: an outer shell with Transmission 1, IOR 1.5, 2–3 mm walls, a thick base and a moulded thread at the neck.
   - Honey: an inner volume (IOR 1.49, Volume Absorption amber `#c77a10`-ish with high density, plus slight Subsurface or Volume Scatter for the glow), filled to about 80%, with a meniscus and a few tiny suspended bubbles.
   - Add a back or rim light so the honey glows at the edges.
2. **Classic jar shape, smaller.** A hexagonal or straight-sided jar, about 8 cm wide and 10 cm high in the leopard's scale, so it sits next to the paw as a real object.
3. **A real lid.** Either:
   - a gingham or linen square draped over the lid with a cloth sim or hand-shaped folds, a weave texture and a frayed edge, tied with *visible* twine (fix the torus radius and use a twisted-rope curve with a bow), or
   - a metal screw lid with a honeycomb-cell emboss.
4. **A proper honey dipper.** Turned wood with 4–6 deep grooves at the head and a tapered handle with a knob. Give it wood-grain texture (end grain on the knob) and a honey coating on the grooved head, with a drip strand hanging off. Have it rest on the rim or lean out at a believable angle, so the head shows.
5. **Spills and wear.** A small honey smear or drip down the outside of the glass, a ring of honey on the counter under the jar (adds grounding), a faint thumbprint on the glass via roughness map.
6. **Contact shadow and caustic glow.** Use the shadow catcher, plus a soft amber light patch on the counter beside it, to fake light through honey.

---

## Menu

**What makes it a toy**
- **A sidewalk sign at doll's-house scale.** The tent is 108 wide at the base, 76 at the top and 104 high: a strongly tapered A-frame. At about 50 cm high next to the leopard, it reads like a café pavement board shrunk down, or a board-game piece.
- **Thick board with sharp edges.** `SOLIDIFY` thickness 0.03 BU on a 1.08 BU card is about 3% of its width: a slab, not a card. There is no bevel, so the rim is a razor-sharp green box edge. The back panel is another plain green slab, and there is no hinge, fold, ribbon or stand.
- **Flat cartoon face.** `menu_texture()` is a 512×640 PIL drawing: a flat green field, a lighter top block, a yellow-ochre border, "MENU" in a condensed font, and three solid ochre bars standing in for text. The gold is *paint*, not metal: same Principled base colour, no metallic, no foil sheen. The fake text bars read as a UI icon, not print. 512 px is soft at the 6 px/unit close-up (`SHOTS['menu']`, 02).
- **Plastic sheen.** Roughness 0.42 plus coat 0.3 gives a uniform satin plastic, with no paper, leather or fabric quality.
- **Colour.** Saturated mid-green `#1f5a42` with ochre. It passes "true colour" and invites a tap, but it is the only cool colour on the warm counter, and its bright flat face is the largest uniform colour area in the scene. It reads as a UI card rendered in 3D.
- **Ungrounded.** No contact shadow (a faint dark line only). It does not look like it sits on the counter.

**Rebuild directions**
1. **A real bar-menu object.** Choose one:
   - **a leather or bookcloth folder** standing in a small brass or wooden stand, or leaning on a bottle, with rounded corners, stitched edges and a slightly open cover;
   - **a heavy card in a wooden or brass card stand** with a thin card (about 1 mm), a gently bowed face and a small foot.

   Drop the tapered A-frame.
2. **Material.** Deep bottle-green leather or bookcloth: a grain normal map, roughness 0.45–0.6 with variation, worn and darker corners, slight edge polish.
3. **Gold that is metal.** Foil-stamped "MENU" and a border rule as a metallic material (gold `#c9a44a`, metallic 1, roughness 0.25), slightly debossed via bump, catching the warm key as a narrow glint. A gilded page edge if it is a folder.
4. **Legibility.** Render "MENU" large and centred, with real letter-spacing and a classical serif or Bodoni-like face matching the Dionysus theme. Texture at least 2048 px. Drop the three fake text bars, or replace them with a small engraved ornament.
5. **Scale.** About 25–30 cm high at counter scale, so the leopard's head is comparable to the folder's width.
6. **Grounding.** A contact shadow, a soft reflection on the counter's sheen, and a slightly darker footprint where the stand meets the wood.

---

## Die

**What makes it a toy**
- **Impossible die.** The faces shown are 3 (front), **2 (top) and 5 (right)**. On a real die opposite faces sum to 7, so 2 and 5 are opposite each other and can never both be visible. Anyone who plays games sees "wrong" at a glance. The pip spacing also varies by face (±0.07 vs ±0.06).
- **Foam-cube corners.** The `add_bevel(d, 0.035, 4)` bevel on a 0.27 cube is a 13% radius. Together with smooth shading this makes a pillowy cushion, the look of a foam or plush die (before-dice-recipe).
- **Pips are bumps, not holes.** They are squashed UV spheres placed at `s/2 - 0.008` with a 0.45 squash, so they sit *on* the surface as red domes or stickers. Real pips are drilled concave cups filled with paint, and you can see a dark rim and a small shadow inside each.
- **Glossy plastic material.** `M_IVORY` is cream `#f3ead6`, rough 0.25, coat 0.6: shiny cream plastic. It has no translucency, no bone or ivory grain, no yellowing at the edges and no wear.
- **Scale.** About 14 cm on the counter, larger than the leopard's paw. It is the clearest single "toy" cue in the scene.
- **No shadow at all.** `visible_shadow = False` is set explicitly in the touch render, so the die floats. Its rotation is the only grounding cue.

**Colour rule.** Passes (it is a touchable, and true ivory plus red is fine). But it is now the brightest near-white object on the counter besides the statue. Bone or ivory in warm low light should sit around cream mid-tones, with the specular doing the inviting.

**Rebuild directions**
1. **Correct face layout.** Use standard right-handed die faces, for example 1 on top, 2 front, 3 right, with opposite faces summing to 7. Use the classic layout: diagonal 2 and 3, a pattern of 5.
2. **Real scale and proportion.** About 16–19 mm. Or, if the die must stay a big tap target, make it a pair of dice, or a die on a small felt or leather dice tray that carries the target size.
3. **Sharp-ish corners.** Bevel about 4–6% of the edge with 3 segments, or a casino-style crisp edge with a tiny chamfer. Add slight edge wear: a roughness and colour mask brighter on the edges.
4. **Drilled pips.** Boolean-subtract spherical cups (depth about 0.6 of the radius), then fill with a separate slightly recessed paint disc: deep red `#8f1420` or black, matte, roughness 0.6. The cup walls should show a dark ring of shadow.
5. **Bone or ivory material.**
   - Base `#e9dcc0`, with Subsurface weight 0.1–0.2 and a warm radius.
   - Fine grain or Schreger-line noise in the colour, roughness 0.35–0.5 with polish variation, and a hint of yellowing at the corners.
   - Drop the clearcoat.
6. **Shadow and contact.** Turn shadows back on and render the die over a shadow catcher. It needs a tight dark contact shadow plus a soft key shadow falling away from the sconce side.

---

## Rule check: touchable true colour vs muted bar

| Item | Status | Risk |
|---|---|---|
| Bottles | True colour **but wrong carrier**: opaque paint, so it reads as candy | The shelf is the loudest colour block in the scene and competes with the neon and the god. Clear spirits are the brightest cream shapes, which breaks the "cream only as highlight" rule. |
| Honey jar | Passes, over-saturated | Clipped highlight; opaque orange looks plastic. Honey seen through glass would be richer *and* calmer. |
| Menu | Passes | The only cool hue, and a large flat area of it. It reads as UI. Leather plus metallic gold keeps the colour but makes it an object. |
| Die | Passes | A near-white large shape. Bone tones plus smaller scale fix it. |

Highest-value single changes, in order:
1. Glass and liquid with proper transmission bounces, plus AgX.
2. Shadow-catcher grounding for every layer.
3. Correct real-world scale against the leopard.
4. Surface texture (roughness and bump) on every material.
