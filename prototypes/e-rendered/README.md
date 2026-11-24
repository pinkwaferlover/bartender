# Prototype E: rendered

Prototype B's layout, logic and zoom model, with the bar rendered in Blender (R1, R2, R5).

**Open it:** from the repository root run `python3 -m http.server 8765`, then open
<http://localhost:8765/prototypes/e-rendered/index.html>. It needs a server (not `file://`) only for the optional loops manifest.

## Layers

| Layer | Source | Files |
|---|---|---|
| Background, one per camera position (bar, sign lit and unlit, shelf, mid for talk/recipe/choice, menu) | `blender/build_bar.py` | `img/bg-*.webp` |
| Touchables: menu, panther with dice, honey jar | rendered alone on a transparent film | `img/touch-*.webp` |
| Bottles, one per Style (26) | rendered on the shelf, placed by the app | `img/bottle-*.webp` |
| Dionysus | rendered loops of a MakeHuman figure, his own swappable layer (B's drawn figure is the fallback) | `blender/build_dionysus.py`, `img/dio/<finish>/<loop>/*.webp`, `dio-loops.json`, `dio-layer.js` |

`layers.js` is written by the build script and says where each image sits in B's world units.

## Re-render

```sh
python3.13 -m venv .venv-blender && .venv-blender/bin/pip install bpy==5.3.0 pillow
.venv-blender/bin/python prototypes/e-rendered/blender/build_bar.py           # everything, about 20 minutes on 4 CPU cores
.venv-blender/bin/python prototypes/e-rendered/blender/build_bar.py --quick   # preview, about 30 seconds
.venv-blender/bin/python prototypes/e-rendered/blender/build_bar.py --only bottles   # bg | touch | bottles
.venv-blender/bin/python prototypes/e-rendered/blender/build_bar.py --preview menu   # menu | honey | dice | bottles: one item alone and in the bar, into blender/_work/preview/
```

Cycles on the CPU (Eevee needs a GPU here), adaptive sampling and OpenImageDenoise, Standard view transform so colours come out true. Up to 10 bounces, 10 of them through glass, so the bottles and honey jar read as glass. Bottles render at 160 samples (about 4 minutes for all 26), the touchable items at 64 (10–47 s each), the backgrounds in about 14 minutes. A partial render (`--only`, `--preview`) keeps the other entries in `layers.js`.

## Dionysus loops (R4)

`blender/build_dionysus.py` builds him on a MakeHuman base (MPFB2, R3) shaped towards the Louvre Dionysus and renders one loop per action: polish (idle), stir, pour, shake, reach, story, and dip (the thyrsus into the honey jar, R8). Each loop is rendered in three finishes (Q8): painted marble (the default), white marble and living skin. Coverage stays classical in every finish; modest and cheeky apply only to the drawn fallback figure (Q9).

```sh
git clone --depth 1 https://github.com/makehumancommunity/mpfb2
cp -r mpfb2/src/mpfb ~/.config/blender/5.3/extensions/user_default/
.venv-blender/bin/python prototypes/e-rendered/blender/build_dionysus.py                  # all loops, painted
.venv-blender/bin/python prototypes/e-rendered/blender/build_dionysus.py --finish white   # white | living
.venv-blender/bin/python prototypes/e-rendered/blender/build_dionysus.py --only stir      # one loop
.venv-blender/bin/python prototypes/e-rendered/blender/build_dionysus.py --still stir --crop head --scale 3   # a close-up to check
```

`dio-loops.json` lists the frames: `loops` is painted marble, `finishes.white` and `finishes.living` hold the other two; `dio-loops.example.json` shows the shape. `dio-layer.js` plays them:

- The drawn figure stays hidden while the loops load, and shows only if they fail or take longer than 1.5 s.
- A recipe step plays its loop for at least 3.2 s, then holds on its tail (from `hold`) until you tap (R6). Honey steps play `dip`.
- The look setting's finish switches frame sets in place, loading a finish only when it is chosen.
- Changing loop crossfades for 180 ms. With reduced motion, every loop is one still frame and there is no crossfade.
- `?dio=svg` shows the drawn figure instead; `?loops=<manifest>` loads another manifest.

Contact sheets of every loop and finish, and face crops, are in `shots/dio/`.

## Checks

`node prototypes/e-rendered/shots/shoot.js` (with the server running) takes the shots and checks taps, errors, reduced motion and page weight; `shots/measure.py` measures saturation.
