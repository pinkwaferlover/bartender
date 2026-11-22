# Dionysus bar: the agreed brief

Agreed in a grill with the owner on 22 November 2026 (`grill-with-docs`, questions 1–12). Terms are defined in [`CONTEXT.md`](../../CONTEXT.md). Drawing: [`dionysus-journey.svg`](dionysus-journey.svg). This brief is what the three prototypes are judged against.

```text
── exists  ══ agreed ✓Q<n>

 YOU            │ THE BAR SCENE                                    │ YOUR BAR (DATA)
 ───────────────┼──────────────────────────────────────────────────┼──────────────────────
 open app ──────┼═▶ DIONYSUS fades to neon sign; tablet landscape ✓Q2
                │═  he polishes a glass (finish setting)       ✓Q8 │ ═ coverage setting ✓Q9
                │═  touchable = true colour, rest muted        ✓Q7 │
 first visit ───┼═▶ "What do you have?" bottles + barware      ✓Q5 ┼═▶ photos→prompt→list ✓Q5
 tap shelf ─────┼═▶ shelf of your bottles, brand-family art    ✓Q6 ┼═▶ Bottle→Style→Family ✓Q6
 tap menu ──────┼═▶ zoom into menu: spirit · feel · A–Z       ✓Q11 │
 talk to him ───┼═▶ search = speaking to Dionysus           ✓Q3,11 │
 tap Dionysus ──┼═▶ story  │  barman's choice (panther, dice)       │
                │═▶ recipe in front, he makes it behind       ✓Q12 │   34 recipes
 back ──────────┼═▶ zoom out, always to the bar                    │
```

## Decisions

| # | Decision |
|---|---|
| Q1 | Three prototypes, one per way of drawing Dionysus: B flat illustration in code; C painterly "painted still" look built in code with light motion (no image model in this session); D 3D model. |
| Q2 | Kitchen tablet, landscape, first. Phone gets a cropped, taller view. |
| Q3 | Search is talking to Dionysus (speech bubble or mic). |
| Q4 | "Feel", never "craving". Folded into Q11. |
| Q5 | Photos → list by two routes: the user's own API key on their device, or a prompt pasted into their own AI tool. A fixed expected output defines the prompt. Inventory covers bottles **and barware** (photo or tick list). Prototypes fake this step. |
| Q6 | Bottle → Style → Family. Bottle art per brand family (shape, colour, label layout), no logos or brand wording; quintessential brand as each Style's stand-in. [Issue #3](https://github.com/pinkwaferlover/bartender/issues/3). |
| Q7 | Touchable things keep true colour; the bar is muted (near-black `#0f0e10`, dark brown bar, cream `#f0e7d8` highlights, light and shade). Dionysus touches only touchable things, plus patrons. Patron scenes: [issue #4](https://github.com/pinkwaferlover/bartender/issues/4). |
| Q8 | Finish setting: painted marble (default), white marble, living skin. Clothing in natural, regal reds and greens. |
| Q9 | Coverage setting: classical (default), modest, cheeky (adult, off until switched on; implied, never shown). |
| Q9+ | His classical attributes are bar tools: thyrsus as bar spoon and honey-from-the-counter; wreath as garnish (sprouts mint); vines fetch bottles and ripen lemons; kantharos as mixing glass; fawn skin as polishing cloth; panther bats the dice for barman's choice; rare golden rim. |
| Q10 | Each prototype is a clickable page covering the whole journey with the real 34 recipes, apart from the live app. |
| Q11 | He asks up to four skippable questions (spirit, feel, moment, strength) and stops once a handful fit. Feels: sweet and rich, sharp and fresh, bitter, dry and boozy, shared with the menu. Strength includes none and low. Alcohol-free drinks: [issue #5](https://github.com/pinkwaferlover/bartender/issues/5). |
| Q12 | Missing barware: he still offers the drink with a swap (jam jar for a shaker, rolling pin for a muddler); never hidden for a tool. |

Still true from the epic: a drink in three taps or fewer from home (barman's choice is one).

Replaces story S11 ("one chosen look, ultra-minimal") in [`stories.md`](../stories.md).

## Round 2: after the arena (22 November 2026)

The arena (two Opus critics, one Opus judge, reports in [`arena/`](arena/)) picked prototype B. The owner agreed, and said B's style is closest to the feel, but not "SVGs everywhere", and D's 3D figure still looks wrong.

| # | Decision |
|---|---|
| R1 | Build on B's layout, logic and zoom model. |
| R2 | Make the art with Blender in a cloud session (the `bpy` Python package), not Blender MCP on the owner's PC. |
| R3 | Dionysus is built on a rigged human base (MakeHuman's free CC0 plug-in), shaped to the Louvre Dionysus reference, with a marble finish. It is not a scanned statue. |
| R4 | The app plays rendered loops of each action (polish, stir, pour, shake, reach, tell a story), not live 3D. |
| R5 | Blender renders the whole scene in B's style: layout, palette and poster composition, with real light and depth. Touchable things are separate layers. |
| R6 | Recipe steps: he acts out each step, then waits for the user's tap. No timer. |
| R7 | Barman's choice draws only from drinks you can make, plus one marked "worth buying a bottle for". |
| R8 | Honey comes from a honey jar the user can tap. He never touches the counter. |
| R9 | The menu shows every drink. The ones you can't make are marked "needs Campari" and so on. |
| R10 | On the recipe screen, Dionysus is sharp, beside the card. This replaces "blurred behind". |
| R11 | Text size is a setting the user changes (A− / A+), not a fixed number. Settings open from a brass lamp on the bar, not a cog. Changed 22 November 2026: the owner could not settle a size on the test page. |
| R12 | "Warm me up", "After dinner" and similar phrases are words he understands, not buttons. The four questions stay as they are. |
| R13 | His body waits until the MakeHuman sites are allowed. The bar scene and app changes go first. |

Grafts from the arena: the "paste from your own AI" route and the golden rim come from D. A talk search must reach a recipe in three taps or fewer (it takes 5 today). Bug fixes: "Here's what's closest" lists nothing (B `logic.js:136`); barman's choice falls back to all 34 drinks (B `logic.js:87`).
