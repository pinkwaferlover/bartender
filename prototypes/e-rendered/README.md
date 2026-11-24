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
| Dionysus | prototype B's drawn figure, his own swappable layer | `dio-layer.js` |

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

`dio-layer.js` defines the interface. When rendered loops exist, open `index.html?dio=loops&loops=<manifest>`; `dio-loops.example.json` shows the manifest's shape (one loop per action: polish, stir, pour, shake, reach, story; frames or a video).

## Checks

`node prototypes/e-rendered/shots/shoot.js` (with the server running) takes the shots and checks taps, errors, reduced motion and page weight; `shots/measure.py` measures saturation.
