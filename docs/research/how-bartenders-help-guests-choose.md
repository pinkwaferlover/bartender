# How bartenders help a guest choose a drink

Researched 22 November 2026. Written for Dionysus, the home cocktail app.

**Read this first: no source page could be opened.** Every page I tried failed to load because the session's network blocks the host (see "Could not reach"). The source claims below come only from search-result summaries, not from the pages themselves. All of them are marked **Unverified**. The proposal in section 3 is my own design from those summaries and from the owner's brief. It is not a sourced fact.

## Summary

- Unverified: bartenders narrow a choice by asking about taste and drink style, not by asking for a named cocktail. The questions come up again and again: sweet, sour or bitter? stirred and boozy, or shaken and refreshing? which spirit? what do you usually drink? what do you dislike?
- Unverified: the most common split is "spirit-forward" (stirred, short, boozy) against "refreshing" (shaken or long, citrusy). Spirit and taste come next. Moment (before dinner, after dinner) and season were not in the summaries I could see, so I cannot say how much bartenders lean on them.
- Unverified: guests are told to give descriptors (tart, bitter, sweet, boozy) and one spirit. "Not too sweet" is said to cause more questions, because sweetness means different things to different people.
- Unverified: the Cocktail Codex (Death & Co) groups drinks into six root families: Old-Fashioned, Martini, Daiquiri, Sidecar, Whisky Highball and Flip. That is a way to organise recipes, not a way to ask a guest what they want.
- The 34 recipes fit one model of three short questions (spirit, taste, kick), with moment as a label on each drink. Table in section 3.

## Proposed feel model (my design, not sourced)

Dionysus asks at most three questions, then names a drink. Each can be skipped with "Any".

| # | Question | Choices |
|---|---|---|
| 1 | What are you drinking? | Whisky, Gin, Rum, Something else (tequila, vodka, brandy, aperitif), Any |
| 2 | What do you feel like? | Sweet or rich, Sharp and fresh, Bitter, Dry and boozy |
| 3 | How big a kick? (skipped if Q2 was "Dry and boozy") | Light and long, Middling, Strong |

Two things sit beside the questions rather than in them:

- **Moment** is a label on each drink: Before dinner, With food, After dinner, Anytime. It powers three search chips (below), not a fourth question.
- **Season** stays as it is in the data. Use today's date to put in-season drinks first.

This keeps the owner's word *feel*. The old six feels fold in like this: Sweet and Decadent become "Sweet or rich"; Balanced and Fresh become "Sharp and fresh"; Bitter stays; Spirit-forward becomes "Dry and boozy". Cutting fat is covered by the "With food" label, which I give to bitter or sharp, dry drinks (Negroni, Martini, Americano). That reasoning is mine and is **Unverified**. I found no source for it.

### What happens to the current search chips (`SUGQ`)

| Chip now | Verdict | Why |
|---|---|---|
| Smoky | Goes as a chip | Only Penicillin matches (Islay float). Stays searchable as a word. |
| Honey | Goes as a chip | It is an ingredient, not a feel. Stays searchable. |
| Warm me up | Survives | Temperature is not in the model, so keep it as a chip (Hot Toddy, Irish Coffee, Whisky Mac). |
| Long and fresh | Merges | Becomes Q2 "Sharp and fresh" plus Q3 "Light and long". |
| Bitter | Merges | Becomes Q2 "Bitter". |
| After dinner | Survives | Becomes the "After dinner" moment label. |
| New: Before dinner | Added | Aperitif moment from the owner's brief. |
| New: With food | Added | Palate-cleanser moment from the owner's brief. |

Result: two old chips stay (Warm me up, After dinner), two new ones are added (Before dinner, With food), and the question flow replaces the rest.

### All 34 recipes mapped

Spirit, taste, kick and moment are my own readings of each recipe's ingredients. They are not sourced and need the owner's check. "Now" is the current `feel` in `src/data.js`.

| Recipe | Spirit | Taste | Kick | Moment | Now |
|---|---|---|---|---|---|
| Penicillin | Whisky | Sharp and fresh | Middling | Anytime | balanced |
| Old Fashioned | Whisky | Dry and boozy | Strong | After dinner | strong |
| Manhattan | Whisky | Dry and boozy | Strong | Before dinner | strong |
| Rob Roy | Whisky | Dry and boozy | Strong | Before dinner | strong |
| Whisky Sour | Whisky | Sharp and fresh | Middling | Anytime | balanced |
| Gold Rush | Whisky | Sweet or rich | Middling | Anytime | sweet |
| Whisky Highball | Whisky | Sharp and fresh | Light and long | With food | fresh |
| Mamie Taylor | Whisky | Sharp and fresh | Light and long | Anytime | fresh |
| Godfather | Whisky | Sweet or rich | Strong | After dinner | decadent |
| Brown Derby | Whisky | Sharp and fresh | Middling | Before dinner | fresh |
| Whisky Smash | Whisky | Sharp and fresh | Middling | Anytime | fresh |
| Hot Toddy | Whisky | Sweet or rich | Middling | After dinner (warm) | sweet |
| Mint Julep | Whisky | Dry and boozy | Strong | Anytime | strong |
| Irish Coffee | Whisky | Sweet or rich | Middling | After dinner (warm) | decadent |
| Boulevardier | Whisky | Bitter | Strong | Before dinner, With food | bitter |
| Old Pal | Whisky | Bitter | Strong | Before dinner, With food | bitter |
| Blood and Sand | Whisky | Sweet or rich | Middling | Anytime | sweet |
| Whisky Mac | Whisky | Sweet or rich | Strong | After dinner (warm) | sweet |
| Paper Plane | Whisky | Sharp and fresh | Middling | Before dinner | balanced |
| Gin & Tonic | Gin | Sharp and fresh | Light and long | Before dinner, With food | fresh |
| Dry Martini | Gin | Dry and boozy | Strong | Before dinner, With food | strong |
| Bee's Knees | Gin | Sweet or rich | Middling | Anytime | sweet |
| Negroni | Gin | Bitter | Strong | Before dinner, With food | bitter |
| Tom Collins | Gin | Sharp and fresh | Light and long | Anytime | fresh |
| Gimlet | Gin | Sharp and fresh | Middling | Before dinner | fresh |
| Southside | Gin | Sharp and fresh | Middling | Anytime | fresh |
| Daiquiri | Rum | Sharp and fresh | Middling | Before dinner | balanced |
| Mojito | Rum | Sharp and fresh | Light and long | Anytime | fresh |
| Americano | Aperitif | Bitter | Light and long | Before dinner, With food | bitter |
| Margarita | Tequila | Sharp and fresh | Middling | With food | fresh |
| Paloma | Tequila | Sharp and fresh | Light and long | With food | fresh |
| Sidecar | Brandy | Sharp and fresh | Middling | After dinner | balanced |
| Moscow Mule | Vodka | Sharp and fresh | Light and long | Anytime | fresh |
| Espresso Martini | Vodka | Sweet or rich | Middling | After dinner | decadent |

Count by taste: Sharp and fresh 17, Sweet or rich 8, Dry and boozy 5, Bitter 4. Bitter is thin: Paper Plane is bittersweet and could move there if the owner prefers. Sweet drinks are thin outside whisky and gin (no rum or tequila). The app may need a rum or tequila drink that is sweet or rich.

## 1. Questions bartenders ask (all Unverified)

From a search summary only, naming these publications and people:

- Do you want something sweet? Do you prefer a Manhattan style or something on the rocks? One bartender's checklist. Source: Tales of the Cocktail, https://talesofthecocktail.org/ad-libbing-cocktails-what-to-ask/ (page not opened).
- Bitter, sweet, sour; stirred and up, or on the rocks. A Phoenix bartender. Source: a Phoenix publication, name unclear in the summary. **Unclear.**
- "Shaken and citrusy" against "stirred and spirit-forward", from Attaboy's general manager. Source: a search summary of an article I could not identify. **Unclear.**
- Spirit preference, refreshing or boozy, aversions or allergies. Described as a Founding Farmers-style approach. Source unclear.
- What do you usually drink? A simple sour is a gateway: a Daiquiri for rum drinkers, a Whiskey Sour for bourbon or rye fans. Source unclear.
- Describe taste (tart, bitter, sweet, boozy) rather than "not too sweet"; one bar manager says it just leads to more questions. VinePair, https://vinepair.com/articles/stop-asking-for-drinks-not-too-sweet (not opened).
- "Sweetness isn't a linear thing", a New York bartender. Guests should name drinks they like. Source unclear.
- Name a spirit and a style word such as spirit-forward, fruity or tart. Rob Barter and Lex Madden are named. Source: Tasting Table, https://www.tastingtable.com/2245826/how-order-cocktails-like-know-what-doing/ (not opened).
- Say what you dislike and why. Dan Murphy's, https://www.danmurphys.com.au/dans-daily/learn/bar-etiquette-questions-and-answers (not opened).
- Expect a drink in the spirit of what you described, not a copy. Death & Co, https://fashioned.deathandcompany.com/pages/bartender-s-choice-how-to-order-off-the-menu-drinks-like-a-pro (not opened).
- Bartender's choice is a mini dialogue that starts with your preferences. VinePair, https://vinepair.com/articles/dont-screw-up-bartenders-choice/ (not opened).

**Order of questions: Unverified, no source gave a ranked order.** From the above, the order that appears most is spirit, then taste (sweet, sour, bitter), then strength or style (stirred and boozy against shaken and refreshing). My model follows that order. It is a guess.

**Not found:** anything on body or texture, temperature, season, or palate-cleanser pairing as a question bartenders ask. I did not reach any source on aperitivo, digestivo, or cutting fat with bitterness and acid. Those parts of the owner's brief are unsupported here. Do not present them as bartender practice.

## 2. Frameworks

- Cocktail Codex, by Alex Day, Nick Fauchald and David Kaplan (Death & Co), Clarkson Potter, 2018. Six roots: Old-Fashioned, Martini, Daiquiri, Sidecar, Whisky Highball, Flip. Each is described as core spirit, balance and seasoning. **Unverified**: from a search summary. Publisher page: https://www.penguinrandomhouse.com/books/534533/cocktail-codex-by-alex-day-nick-fauchald-and-david-kaplan/ (not opened). VinePair also reported it (https://vinepair.com/articles/6-important-cocktails-recipe-guide/, not opened) and names Devon Tarby as a fourth author, which conflicts with the publisher listing. **Unclear.**
- Fit with Dionysus: the six roots describe how drinks are built, not how a guest picks. Of the 34 recipes, the Old Fashioned, Manhattan, Rob Roy and Mint Julep sit near the Old-Fashioned root; the Dry Martini near the Martini root; Daiquiri, Gimlet, Gold Rush and the sours near the Daiquiri root; Sidecar near its root; Whisky Highball near its root. That grouping is my own reading.
- Difford's Guide flavour descriptors, and Imbibe or PUNCH practice: **not reached**. The PUNCH result was a recipe article ("Bartender's Choice: Spicy, With Tequila", https://punchdrink.com/articles/bartenders-choice-cocktails-spicy-tequila-cocktail-recipe/), not a how-to-order guide, and I did not open it.

## Could not reach

All failed with a host-not-found error, meaning the session's network does not allow them. After the first failures the tool told me to stop trying other sites, so I did. These need adding to the session's allowed hosts:

- https://talesofthecocktail.org/ad-libbing-cocktails-what-to-ask/
- https://vinepair.com/articles/dont-screw-up-bartenders-choice/
- https://vinepair.com/articles/6-important-cocktails-recipe-guide/
- https://fashioned.deathandcompany.com/pages/bartender-s-choice-how-to-order-off-the-menu-drinks-like-a-pro

Listed above as not opened, because I never tried them: Tasting Table, Dan Murphy's, Penguin Random House, PUNCH, the other VinePair page. Not searched at all: Difford's Guide, Imbibe, published bartender training material, food-pairing guidance.

## Next step

Allow those hosts, then rerun this research so each claim in section 1 can be opened and quoted, and look for sources on moment, season and food pairing.
