# Epic: Dionysus, a cocktail menu from what's on the shelf

On the kitchen tablet, pick a drink in three taps or fewer, from bottles and mixers actually in the house, and read the recipe from a metre away while making it.

**Test:** with the owner's real inventory loaded, choosing whisky lists at least 5 real whisky cocktails that can be made now (checked by an automated test against the inventory file), and a recipe opens in at most 3 taps from home.

Updated 21 November 2026.

| # | Story | Done when | Slice |
|---|---|---|---|
| S1 | **Surprise me**: one tap gives a drink I can make now | Only drinks with every essential ingredient in stock; never the same twice running; "Another" | 1 |
| S2 | **By spirit**: start from whisky, gin, rum… | Home → spirit → recipe in ≤ 3 taps; only spirits I own appear | 1 |
| S3 | **By feel**: sweet, balanced, bitter, decadent, spirit-forward, fresh | Items sit still in a radial menu and are tapped, not spun | 1 |
| S4 | **One bottle away**, growing into an **encyclopaedia**: every recipe I could make, ranked by the one bottle or ingredient that unlocks the most | Each missing item shows how many drinks it unlocks; sorted by that count | 2 |
| S5 | **Recipe readable from a metre**, with an animation per step that matches the action (shake, muddle, stir, pour) | Step text ≥ 32 px; nothing spins for no reason; screen stays awake | 1 |
| S6 | **Inventory from photos** via the owner's own AI tool, to a JSON file matching the schema | Schema and prompt in the repo; unknown items flagged, never guessed | 2 |
| S7 | **Private inventory**: my file lives on my computer / Google Drive and is loaded into the app; a sample ships in the public repo | `inventory.json` gitignored; `inventory.example.json` public; loading is a clearly labelled action, not a bare icon | 1 |
| S8 | **Example bar for anyone who clones it** | Fresh clone works with the example; README: photograph, run the prompt, load the file | 1 |
| S9 | **Home Assistant** later | Later: build the app first | — |
| S10 | **Mark a bottle as run out** from the tablet | Lists update at once and the change survives a reload | 3 |
| S11 | **One chosen look**, ultra-minimal, image first | One look chosen from the drawn options and kept on every screen | 1 |
| S12 | **A–Z finder**: a radial alphabet that magnifies under the finger or mouse | Letter under the pointer largest, neighbours smaller with distance; letting go lists that letter's drinks | 1 |
| S13 | **Search** with a mic and cycling suggestions | Every suggestion and result shows the drink's picture, its spirit and its feel | 1 |
| S14 | **Prep time as a pie**: the longest recipe is a full pie; shake and stir steps show their seconds | No countdown: it suggests time for the right dilution, it isn't a race | 1 |
| S15 | **A story for every drink**, told like a barkeeper leaning over the counter | What's on record said plainly; legends called legends | 1 |
| S16 | **Substitutions** for missing ingredients | Offered only for non-essential ingredients; essentials are marked and never substituted | 2 |
| S17 | **Seasonal suggestions** | Home shows a few drinks suited to the season | 3 |
| S18 | **Preferences learnt automatically** from what I make | Drinks made are recorded on the device; suggestions lean towards them | 3 |
| S19 | **Long lists**: radial when the items fit; otherwise a straight left-to-right swipe, or the A–Z finder | Switches automatically above the count that fits a circle | 1 |
