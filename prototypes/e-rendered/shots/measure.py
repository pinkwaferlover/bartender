"""Saturation check for Q7 ("touchable = true colour, the rest muted"), from the tablet bar screenshot.
Touchable pixels are those that change when the touchables are hidden (shot bar.png vs bar-bg.png),
inside each touchable's box. Everything else is the muted world, split into named regions.
Reports mean HSV saturation (as critic A measured) and mean chroma (max-min of RGB), which is steadier
in near-black pixels, where HSV saturation runs high on tiny differences."""
import json, os, sys
import numpy as np
from PIL import Image
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'measure')
a = np.asarray(Image.open(os.path.join(D, 'bar.png')).convert('RGB')).astype(np.float32) / 255
b = np.asarray(Image.open(os.path.join(D, 'bar-bg.png')).convert('RGB')).astype(np.float32) / 255
boxes = json.load(open(os.path.join(D, 'boxes.json')))
H, W, _ = a.shape
changed = np.abs(a - b).max(axis=2) > 0.06
mx, mn = a.max(axis=2), a.min(axis=2)
S = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0); CH = mx - mn
def stats(mask):
    n = int(mask.sum())
    return {'pixels': n, 'S': round(float(S[mask].mean()), 3) if n else None, 'chroma': round(float(CH[mask].mean()), 3) if n else None,
            'V': round(float(mx[mask].mean()), 3) if n else None}
def boxmask(x0, y0, x1, y1):
    m = np.zeros((H, W), bool); m[max(0, y0):min(H, y1), max(0, x0):min(W, x1)] = True; return m
out = {'touchable': {}, 'muted': {}}
anytouch = np.zeros((H, W), bool)
for k, (x0, y0, x1, y1) in boxes.items():
    m = boxmask(x0, y0, x1, y1) & changed; anytouch |= m
    out['touchable'][k] = stats(m)
bg = ~changed
regions = {   # tablet 1280x800 home shot, screen pixels
    'wall (left of arch)': (0, 220, 230, 600), 'wall (right of arch)': (1050, 220, 1280, 600),
    'columns': (70, 210, 190, 610), 'neon sign (board)': (290, 30, 990, 210), 'arch and sunburst': (260, 200, 1020, 620),
    'counter top and front': (0, 615, 1280, 800), 'shelf plank': (300, 350, 980, 400),
}
for k, r in regions.items():
    out['muted'][k] = stats(boxmask(*r) & bg)
out['muted']['all untouchable pixels'] = stats(bg)
out['touchable']['all touchable pixels'] = stats(anytouch)
tmin = min(v['chroma'] for k, v in out['touchable'].items() if v['chroma'] is not None)
mmax = max(v['chroma'] for k, v in out['muted'].items() if v['chroma'] is not None)
out['rule'] = {'least saturated touchable (chroma)': tmin, 'most saturated untouchable (chroma)': mmax, 'holds': mmax < tmin}
json.dump(out, open(os.path.join(D, 'saturation.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))
