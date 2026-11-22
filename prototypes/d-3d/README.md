# Prototype D: the 3D bar

A throwaway prototype of the Dionysus bar scene, built in three.js. Open `index.html` straight from the file, or run `python3 -m http.server` from the repo root and go to `/prototypes/d-3d/`.

- **Dionysus** is the *Apollo Belvedere* scan (public domain, see credits below), mirrored, trimmed and rigged here so his arms can reach, stir and pour. His body lives in `dionysus-mesh.js` so the page still works from a file.
- **The bar** follows the owner's references: panelled wood, an arched back bar lit from behind, dark marble on fluted leather, brass, a checked floor, palms, a velvet curtain and fringed lamps.
- **Look** settings: finish (painted marble, white marble, living) and coverage (classical, modest, cheeky). Cheeky is adult and off until switched on.
- `shots/` holds the review screenshots. `tools/` holds the scripts that turned the scan into `dionysus-mesh.js` (gltfpack to simplify, then `extract.mjs` and `rig.mjs`).

## Credits

- Body: "Apollo Belvedere" by SMK – National Gallery of Denmark, CC0 Public Domain, on Sketchfab (sketchfab.com/3d-models/apollo-belvedere-fe5c0cffdc2a4f3985872212c692af0c).
- Recipes and stories: `src/data.js` and `src/stories.js` in this repo.
