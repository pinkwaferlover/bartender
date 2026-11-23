"""Dionysus for prototype E (R3, R4, R8, R13): a MakeHuman (MPFB2) base shaped towards the Louvre "Richelieu"
Dionysus, rigged, in three finishes (Q8), and rendered as one loop per action (polish, stir, pour, shake, reach,
story, dip).

Needs MPFB2 installed as a Blender extension (user_default repository):
    git clone --depth 1 https://github.com/makehumancommunity/mpfb2
    cp -r mpfb2/src/mpfb ~/.config/blender/5.3/extensions/user_default/
Run from the repository root:
    .venv-blender/bin/python prototypes/e-rendered/blender/build_dionysus.py --preview   # one still per loop
    .venv-blender/bin/python prototypes/e-rendered/blender/build_dionysus.py             # all loops
    .venv-blender/bin/python prototypes/e-rendered/blender/build_dionysus.py --only stir # one loop
Options:
    --finish painted|white|living   Q8 finish (default painted). Frames go to img/dio/<finish>/<loop>/NNNN.webp;
                                    all finishes share one manifest, dio-loops.json (painted is its `loops`, the
                                    others are under `finishes`).
    --still <loop> [--frame N] [--crop full|head|grip|left] [--scale k] [--out DIR]
                                    one frame for inspection (default: middle frame, full rect, scale 1), written
                                    to DIR/still_<finish>_<loop>_<NN>_<crop>.png (default DIR: blender/_work).
    --stills loop:frame:crop:scale,...   several stills in one run (same naming)
    --sheet loop,loop,...           every frame of each loop at --scale (default 0.4) with few samples, tiled
                                    into DIR/sheet_<finish>_<loop>.jpg: a check for snapping and clipping.
    --sheets-from-frames            no rendering: contact sheets and face crops from the frames in img/dio/ into
                                    shots/dio/ (run after a full render of every finish).

It reuses build_bar.py's scene, camera and lights (without writing any of build_bar's outputs), so his
light matches the bar, and renders him alone on a transparent film in one fixed world rectangle, which
dio-layer.js places in B's world units. No MakeHuman system assets are needed: the statue's eyes, hair,
wreath, drapery and props are modelled here.
"""
import bpy, bmesh, math, os, sys, json, time, importlib, addon_utils, shutil
from mathutils.bvhtree import BVHTree
import numpy as np
from mathutils import Vector, Matrix, Euler, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.dirname(HERE)
ARGS = sys.argv[1:]
def _arg(flag, default=None):
    return ARGS[ARGS.index(flag) + 1] if flag in ARGS else default


PREVIEW = '--preview' in ARGS
ONLY_LOOP = _arg('--only')
FINISH = _arg('--finish', 'painted')       # Q8: painted (default) | white | living
assert FINISH in ('painted', 'white', 'living'), FINISH
STILL = _arg('--still')                    # one loop's frame only, for inspection (written to --out, not img/)
STILL_FRAME = _arg('--frame')              # default: the loop's middle frame
STILL_SCALE = float(_arg('--scale', '0.4' if '--sheet' in ARGS else '1'))
STILL_CROP = _arg('--crop', 'full')        # full | head | grip | left (close-ups around his head or a fist)
STILL_OUT = _arg('--out')                  # folder for --still images (default: build_bar's _work folder)
STILLS = _arg('--stills')
SHEET = _arg('--sheet')
SHEETS_ONLY = '--sheets-from-frames' in ARGS
DEBUG = '--debug' in ARGS
FRAMES_ARG = _arg('--frames')              # a full render of only these frame numbers (comma list), for re-renders

DIO = os.path.join(PROTO, 'img', 'dio')
SHOTS = os.path.join(PROTO, 'shots', 'dio')
MAN_P = os.path.join(PROTO, 'dio-loops.json')
FINISHES = ('painted', 'white', 'living')
LOOP_NAMES = ('polish', 'stir', 'pour', 'shake', 'reach', 'story', 'dip')


# ---------------------------------------------------------------- contact sheets from rendered frames (no Blender)
def sheets_from_frames():
    from PIL import Image, ImageDraw
    man = json.load(open(MAN_P)); os.makedirs(SHOTS, exist_ok=True)
    rect = man['rect']; head = man['head']
    for fin in FINISHES:
        loops = man['loops'] if fin == 'painted' else man['finishes'][fin]['loops']
        for name, L in loops.items():
            ims = [Image.open(os.path.join(PROTO, f)).convert('RGBA') for f in L['frames']]
            k = 0.42; w, h = int(ims[0].width * k), int(ims[0].height * k)
            cols = min(len(ims), 6); rows = (len(ims) + cols - 1) // cols
            sh = Image.new('RGB', (cols * w, rows * h + 24), (24, 20, 22)); d = ImageDraw.Draw(sh)
            d.text((6, 5), f'{fin} / {name}: {len(ims)} frames at {L["fps"]} fps, hold from frame {L["hold"]}', fill=(240, 231, 216))
            for i, im in enumerate(ims):
                bg = Image.new('RGBA', im.size, (52, 40, 34, 255)); bg.alpha_composite(im)
                x, y = (i % cols) * w, 24 + (i // cols) * h
                sh.paste(bg.convert('RGB').resize((w, h), Image.LANCZOS), (x, y))
                d.text((x + 4, y + 3), str(i) + (' hold' if L['hold'] and i >= L['hold'] else ''), fill=(240, 200, 120))
            sh.save(os.path.join(SHOTS, f'{fin}-{name}.jpg'), quality=72, optimize=True)
            if fin == 'painted' or name == 'polish':
                # the face, from the frame where he is most expressive (the hold, or the last third of a cycle)
                kk = ims[0].width / rect[2]
                pick = sorted(set([0, L['hold'] or len(ims) * 2 // 3, len(ims) - 2]))
                faces = []
                for i in pick:
                    hx0 = (head[0] - 30 - rect[0]) * kk; hy0 = (head[1] - 10 - rect[1]) * kk
                    box = (int(hx0), int(hy0), int(hx0 + (head[2] + 60) * kk), int(hy0 + (head[3] * 0.8 + 10) * kk))
                    bg = Image.new('RGBA', ims[i].size, (52, 40, 34, 255)); bg.alpha_composite(ims[i])
                    faces.append(bg.crop(box).convert('RGB'))
                fw = sum(f.width for f in faces); fh = faces[0].height
                fs = Image.new('RGB', (fw, fh + 20), (24, 20, 22)); dd = ImageDraw.Draw(fs); x = 0
                for i, f in zip(pick, faces):
                    fs.paste(f, (x, 20)); dd.text((x + 4, 4), f'{fin} {name} frame {i}', fill=(240, 231, 216)); x += f.width
                fs = fs.resize((fs.width * 2, fs.height * 2), Image.LANCZOS)
                nm = f'face-{name}.jpg' if fin == 'painted' else f'face-{name}-{fin}.jpg'
                fs.save(os.path.join(SHOTS, nm), quality=80, optimize=True)
                if name == 'polish' and fin == 'painted': shutil.copy(os.path.join(SHOTS, nm), os.path.join(SHOTS, 'face-polish-painted.jpg'))
    print('[sheets] written to', SHOTS)


if SHEETS_ONLY:
    sheets_from_frames(); sys.exit(0)

# ---------------------------------------------------------------- the bar's scene, camera and lights
src = open(os.path.join(HERE, 'build_bar.py'), encoding='utf8').read()
src = src[:src.index('MANIFEST_PATH = ')]          # everything up to where build_bar writes its outputs
sys.argv = [os.path.join(HERE, 'build_bar.py'), '--only', 'none']
G = {'__file__': os.path.join(HERE, 'build_bar.py'), '__name__': 'build_bar'}
exec(compile(src, 'build_bar.py', 'exec'), G)
scene, cam, P, push, render_region, bbox_world = G['scene'], G['cam'], G['P'], G['push'], G['render_region'], G['bbox_world']
srgb, smooth, mat, link, lathe, WORK = G['srgb'], G['smooth'], G['mat'], G['link'], G['lathe'], G['WORK']
CAM_C, DIST = G['C'], G['DIST']
r = scene.render; cy = scene.cycles
OUT = os.path.join(DIO, FINISH)


def S2W(x, y, d):
    """The Blender point at depth d (Blender units in front of (-) or behind (+) the reference plane) that the
    camera sees at world (x, y): where to put something so it appears at (x, y) in B's world units."""
    return CAM_C + (P(x, y, 0) - CAM_C) * ((DIST + d) / DIST)


# ---------------------------------------------------------------- MPFB
addon_utils.enable('bl_ext.user_default.mpfb', default_set=True)
I = lambda m: importlib.import_module('bl_ext.user_default.mpfb.' + m)
HS = I('services.humanservice').HumanService

# A youthful man with a soft build, the Louvre Dionysus's proportions rather than an athlete's.
MACRO = {"gender": 1.0, "age": 0.40, "muscle": 0.42, "weight": 0.56, "proportions": 0.85, "height": 0.55,
         "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.05, "caucasian": 0.9, "african": 0.05}}
body = HS.create_human(macro_detail_dict=MACRO)
rig = HS.add_builtin_rig(body, 'default')
bpy.context.view_layer.update()
PB = rig.pose.bones


def bone_head(name):   # rest position in the rig's object space (MakeHuman metres)
    return rig.data.bones[name].head_local.copy()


# ---------------------------------------------------------------- where he stands
HEAD_TOP_Y = 336            # world y of the top of his head (B's figure: about 340)
H_WORLD = 880               # his height in world units
verts_rest = np.array([v.co[:] for v in body.data.vertices])
top_z, bot_z = verts_rest[:, 2].max(), verts_rest[:, 2].min()
S = (H_WORLD * 0.01) / (top_z - bot_z)
rig.scale = (S, S, S)
rig.location = P(800, HEAD_TOP_Y + H_WORLD, 0) - Vector((0, 0, bot_z * S))
bpy.context.view_layer.update()


# ---------------------------------------------------------------- materials, per finish (Q8)
# painted: painted marble (the default): a warm flesh wash over the marble, painted lips, cheeks and irises,
#          red-brown painted hair; red himation with a green and gold hem, green ivy, purple grapes.
# white:   unpainted white marble, cool and pale: skin, eyes (blank), hair, wreath, drapery and the thyrsus
#          all marble, the drape a step darker with shaded folds. Other props as they are.
# living:  a living young man: skin with subsurface scattering, dark brown hair, real eyes and brows,
#          the red himation with its hem, green ivy, purple grapes.
def _node_mix(n, L, fac, a, b_):
    m_ = n.new('ShaderNodeMix'); m_.data_type = 'RGBA'
    L.new(fac, m_.inputs['Factor'])
    for sock, v in (('A', a), ('B', b_)):
        if isinstance(v, (tuple, list)): m_.inputs[sock].default_value = v
        else: L.new(v, m_.inputs[sock])
    return m_.outputs['Result']


def _ao(n, L, col_, strength, dist):
    """Darken creases and cavities (Cycles ambient occlusion): carved marble reads by its shadows."""
    ao = n.new('ShaderNodeAmbientOcclusion'); ao.samples = 8; ao.inputs['Distance'].default_value = dist
    mr = n.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 1 - strength
    L.new(ao.outputs['AO'], mr.inputs['Value'])
    mm = n.new('ShaderNodeMix'); mm.data_type = 'RGBA'; mm.blend_type = 'MULTIPLY'; mm.inputs['Factor'].default_value = 1.0
    L.new(col_, mm.inputs['A']); cc = n.new('ShaderNodeCombineColor')
    for k in ('Red', 'Green', 'Blue'): L.new(mr.outputs['Result'], cc.inputs[k])
    L.new(cc.outputs['Color'], mm.inputs['B'])
    return mm.outputs['Result']


def marble_material(name='marble', paint=True, lo='#c2a690', hi='#ecd6c2', rough=0.38, hem=False, ao=0.0,
                    ao_dist=0.06, sss=(0.12, 0.08, 0.06), coat=0.15):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; n = nt.nodes; L = nt.links
    b = n['Principled BSDF']
    b.inputs['Roughness'].default_value = rough
    b.inputs['Subsurface Weight'].default_value = 0.35
    b.inputs['Subsurface Radius'].default_value = sss
    b.inputs['Subsurface Scale'].default_value = 0.08
    b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = 0.25
    tc = n.new('ShaderNodeTexCoord')
    # faint grey veins
    wv = n.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 1.4; wv.inputs['Distortion'].default_value = 9.0
    wv.inputs['Detail'].default_value = 4.0; wv.inputs['Detail Scale'].default_value = 1.5
    L.new(tc.outputs['Object'], wv.inputs['Vector'])
    vr = n.new('ShaderNodeMapRange'); vr.inputs['From Min'].default_value = 0.0; vr.inputs['From Max'].default_value = 0.12
    L.new(wv.outputs['Fac'], vr.inputs['Value'])
    col_ = _node_mix(n, L, vr.outputs['Result'], srgb(lo), srgb(hi))
    if paint:   # lips and cheeks, from the body's 'paint' colour attribute (alpha = how much paint)
        attr = n.new('ShaderNodeAttribute'); attr.attribute_name = 'paint'
        col_ = _node_mix(n, L, attr.outputs['Alpha'], col_, attr.outputs['Color'])
    if hem:     # a carved border along the drape's edges: a faintly darker band with a groove line
        ed = n.new('ShaderNodeAttribute'); ed.attribute_name = 'edge'
        rp = n.new('ShaderNodeValToRGB'); cr = rp.color_ramp; cr.interpolation = 'CONSTANT'
        cr.elements[0].color = (1, 1, 1, 1); cr.elements[1].position = 0.66; cr.elements[1].color = (0.5, 0.5, 0.5, 1)
        e = cr.elements.new(0.71); e.color = (0.78, 0.78, 0.78, 1)
        L.new(ed.outputs['Fac'], rp.inputs['Fac'])
        mm = n.new('ShaderNodeMix'); mm.data_type = 'RGBA'; mm.blend_type = 'MULTIPLY'; mm.inputs['Factor'].default_value = 1.0
        L.new(col_, mm.inputs['A']); L.new(rp.outputs['Color'], mm.inputs['B']); col_ = mm.outputs['Result']
    if ao: col_ = _ao(n, L, col_, ao, ao_dist)
    L.new(col_, b.inputs['Base Color'])
    return m


def skin_material():
    """Living skin: a neutral light tan, subsurface scattering, faint mottling, natural lips and cheeks, brows."""
    m = bpy.data.materials.new('skin'); m.use_nodes = True
    nt = m.node_tree; n = nt.nodes; L = nt.links
    b = n['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.5
    b.inputs['Subsurface Weight'].default_value = 0.5
    b.inputs['Subsurface Radius'].default_value = (0.7, 0.35, 0.2)
    b.inputs['Subsurface Scale'].default_value = 0.006 * S       # a few millimetres of skin, at his scale
    b.inputs['Specular IOR Level'].default_value = 0.45
    tc = n.new('ShaderNodeTexCoord')
    nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 9.0; nz.inputs['Detail'].default_value = 3.0
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    col_ = _node_mix(n, L, nz.outputs['Fac'], srgb('#ab8a7c'), srgb('#c4a494'))
    attr = n.new('ShaderNodeAttribute'); attr.attribute_name = 'paint'
    k = n.new('ShaderNodeMath'); k.operation = 'MULTIPLY'; k.inputs[1].default_value = 0.45
    L.new(attr.outputs['Alpha'], k.inputs[0])
    col_ = _node_mix(n, L, k.outputs[0], col_, attr.outputs['Color'])
    br = n.new('ShaderNodeAttribute'); br.attribute_name = 'brow'
    col_ = _node_mix(n, L, br.outputs['Fac'], col_, srgb('#3a2417'))
    L.new(col_, b.inputs['Base Color'])
    return m


def himation_material(red='#8e2a22', green='#2f5a32', gold='#d8b25a', name='himation'):
    """The drape's cloth: red, with a green band and a thin gold line at both edges, from the mesh's 'edge'
    attribute (0 along the middle of the drape, 1 at its edges)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; n = nt.nodes; L = nt.links
    b = n['Principled BSDF']; b.inputs['Roughness'].default_value = 0.62
    b.inputs['Sheen Weight'].default_value = 0.6
    attr = n.new('ShaderNodeAttribute'); attr.attribute_name = 'edge'
    ramp = n.new('ShaderNodeValToRGB'); cr = ramp.color_ramp; cr.interpolation = 'CONSTANT'
    cr.elements[0].position = 0.0; cr.elements[0].color = srgb(red)
    cr.elements[1].position = 0.66; cr.elements[1].color = srgb(gold)
    e = cr.elements.new(0.71); e.color = srgb(green)
    e = cr.elements.new(0.97); e.color = srgb(gold)
    L.new(attr.outputs['Fac'], ramp.inputs['Fac'])
    L.new(_ao(n, L, ramp.outputs['Color'], 0.45, 0.08), b.inputs['Base Color'])
    # the gold thread is a little metallic and glossier
    gm = n.new('ShaderNodeMath'); gm.operation = 'COMPARE'; gm.inputs[1].default_value = 0.685; gm.inputs[2].default_value = 0.025
    L.new(attr.outputs['Fac'], gm.inputs[0])
    gm2 = n.new('ShaderNodeMath'); gm2.operation = 'GREATER_THAN'; gm2.inputs[1].default_value = 0.97
    L.new(attr.outputs['Fac'], gm2.inputs[0])
    gs = n.new('ShaderNodeMath'); gs.operation = 'MAXIMUM'; L.new(gm.outputs[0], gs.inputs[0]); L.new(gm2.outputs[0], gs.inputs[1])
    mt = n.new('ShaderNodeMath'); mt.operation = 'MULTIPLY'; mt.inputs[1].default_value = 0.6
    L.new(gs.outputs[0], mt.inputs[0]); L.new(mt.outputs[0], b.inputs['Metallic'])
    return m


def eye_material(iris='#6b4c33', pupil='#1c1410', white='#efe8de', name='eye_painted', gloss=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; n = nt.nodes; L = nt.links
    b = n['Principled BSDF']; b.inputs['Roughness'].default_value = 0.25; b.inputs['Coat Weight'].default_value = gloss
    tc = n.new('ShaderNodeTexCoord'); sep = n.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])
    comb = n.new('ShaderNodeCombineXYZ'); L.new(sep.outputs['X'], comb.inputs['X']); L.new(sep.outputs['Z'], comb.inputs['Y'])
    ln = n.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; L.new(comb.outputs[0], ln.inputs[0])
    nrm_ = n.new('ShaderNodeMath'); nrm_.operation = 'DIVIDE'; nrm_.inputs[1].default_value = 0.0118
    L.new(ln.outputs['Value'], nrm_.inputs[0])
    front = n.new('ShaderNodeMath'); front.operation = 'LESS_THAN'; front.inputs[1].default_value = 0.0; L.new(sep.outputs['Y'], front.inputs[0])
    ramp = n.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].position = 0.0; cr.elements[0].color = srgb(pupil)
    e = cr.elements.new(0.22); e.color = srgb(pupil)
    e = cr.elements.new(0.27); e.color = srgb(iris)
    e = cr.elements.new(0.48); e.color = srgb(iris)
    cr.elements[-1].position = 0.53; cr.elements[-1].color = srgb(white)
    L.new(nrm_.outputs[0], ramp.inputs['Fac'])
    mix = n.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.inputs['A'].default_value = srgb(white)
    L.new(front.outputs[0], mix.inputs['Factor']); L.new(ramp.outputs['Color'], mix.inputs['B'])
    L.new(mix.outputs['Result'], b.inputs['Base Color'])
    return m


def fawn_material():
    """The fawn skin (his polishing cloth): tawny with pale spots, in the cloth's own UVs so the spots stay put."""
    m = bpy.data.materials.new('fawn'); m.use_nodes = True; nt = m.node_tree; n = nt.nodes; L = nt.links
    b = n['Principled BSDF']; b.inputs['Roughness'].default_value = 0.85; b.inputs['Sheen Weight'].default_value = 0.8
    tc = n.new('ShaderNodeTexCoord'); vo = n.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 9.0
    vo.inputs['Randomness'].default_value = 0.8
    L.new(tc.outputs['UV'], vo.inputs['Vector'])
    lt = n.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.16
    L.new(vo.outputs['Distance'], lt.inputs[0])
    nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 6.0; L.new(tc.outputs['UV'], nz.inputs['Vector'])
    base = _node_mix(n, L, nz.outputs['Fac'], srgb('#a07650'), srgb('#c49a6c'))
    L.new(_node_mix(n, L, lt.outputs[0], base, srgb('#f0e4cc')), b.inputs['Base Color'])
    return m


def glass_material():
    m = bpy.data.materials.new('dio_glass'); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = srgb('#e8c98a'); b.inputs['Roughness'].default_value = 0.05
    b.inputs['Transmission Weight'].default_value = 1.0; b.inputs['IOR'].default_value = 1.48
    return m


if FINISH == 'painted':
    M_SKIN = marble_material()
    M_EYE = eye_material()
    M_HAIR = marble_material('hair_painted', paint=False, lo='#4a2a1c', hi='#7a4a2e', rough=0.5, ao=0.55, ao_dist=0.05)
    M_IVY = mat('ivy_painted', '#3f7a34', 0.45); M_IVY2 = mat('ivy_painted2', '#2f6428', 0.45)
    M_GRAPE = mat('grape_painted', '#5b2a6b', 0.3, coat=0.5)
    M_HIMATION = himation_material()
elif FINISH == 'white':
    M_SKIN = marble_material('marble_white', paint=False, lo='#c9d4e2', hi='#eef4fb', sss=(0.1, 0.11, 0.14), coat=0.1)   # cool, so it reads white under the bar's warm key
    M_EYE = M_SKIN                                       # blank classical eyes
    M_HAIR = marble_material('hair_white', paint=False, lo='#bcc7d4', hi='#e4ecf5', rough=0.45, ao=0.6, ao_dist=0.05)
    M_IVY = M_IVY2 = M_GRAPE = M_HAIR
    M_HIMATION = marble_material('drape_white', paint=False, lo='#949eaa', hi='#bcc5d0', rough=0.6, hem=True, ao=0.6, ao_dist=0.1)
else:
    M_SKIN = skin_material()
    M_EYE = eye_material(iris='#6a4428', pupil='#0b0806', white='#cdbfb1', name='eye_living', gloss=1.0)
    M_HAIR = mat('hair_living', '#2e1d14', 0.42)
    M_HAIR.node_tree.nodes['Principled BSDF'].inputs['Sheen Weight'].default_value = 0.4
    M_IVY = mat('ivy_living', '#3d7330', 0.4); M_IVY2 = mat('ivy_living2', '#2b5a24', 0.4)
    M_GRAPE = mat('grape_living', '#4a1d5a', 0.25, coat=0.6)
    M_HIMATION = himation_material(name='himation_living')
M_MARBLE = M_SKIN
body.data.materials.clear(); body.data.materials.append(M_SKIN)
for p in body.data.polygons: p.use_smooth = True
sub = body.modifiers.new('subd', 'SUBSURF'); sub.levels = 1; sub.render_levels = 1

# ---------------------------------------------------------------- paint on the face: lips and cheeks (and brows, living)
V = verts_rest
mouth = np.mean([bone_head(b) for b in ('oris01', 'oris02', 'oris05', 'oris06')], axis=0)
eyeL, eyeR = np.array(bone_head('eye.L')), np.array(bone_head('eye.R'))
front_y = V[np.linalg.norm(V[:, [0, 2]] - mouth[[0, 2]], axis=1) < 0.02][:, 1].min()
col = np.zeros((len(V), 4)); col[:, :3] = srgb('#b0564c')[:3]
dx, dz = (V[:, 0] - mouth[0]) / 0.026, (V[:, 2] - (mouth[2] - 0.002)) / 0.009
lips = np.clip(1.4 - (dx ** 2 + dz ** 2), 0, 1) * (V[:, 1] < front_y + 0.018)
a = lips * 0.75
for eye in (eyeL, eyeR):
    c = np.array([eye[0] * 1.15, front_y + 0.03, (eye[2] + mouth[2]) / 2 - 0.004])
    d = np.linalg.norm((V - c) / np.array([0.026, 0.03, 0.022]), axis=1)
    cheek = np.clip(1 - d, 0, 1) ** 1.2 * 0.5
    blend = cheek / np.maximum(a + cheek, 1e-6)
    tint = np.array(srgb('#d2604e')[:3])
    col[:, :3] = col[:, :3] * (1 - blend[:, None]) + tint[None] * blend[:, None]
    a = np.maximum(a, cheek)
col[:, 3] = a
ca = body.data.color_attributes.new('paint', 'FLOAT_COLOR', 'POINT')
ca.data.foreach_set('color', col.astype(np.float32).ravel())
brow = np.zeros(len(V))
for eye in (eyeL, eyeR):     # an arch over each eye, on the front of the brow ridge
    u_ = (V[:, 0] - eye[0] * 1.05) / 0.024
    zc = eye[2] + 0.0175 - 0.006 * u_ ** 2
    band = np.clip(1 - np.abs(V[:, 2] - zc) / 0.0032, 0, 1) * np.clip(1 - np.abs(u_), 0, 1) ** 0.4
    brow = np.maximum(brow, band * (V[:, 1] < eye[1] + 0.005) * 0.85)
ba = body.data.attributes.new('brow', 'FLOAT', 'POINT'); ba.data.foreach_set('value', brow.astype(np.float32))

# eyes: marble eyeballs with a painted iris (ancient statues were painted); blank in white marble.
# Parented to the eye bones, so the face rig can turn them.
EXTRA = []   # everything that belongs to him (rendered with him)
def helper_sphere(group):
    gi_ = body.vertex_groups[group].index
    pts = np.array([V[v.index] for v in body.data.vertices if any(g.group == gi_ and g.weight > 0.5 for g in v.groups)])
    c = pts.mean(axis=0); return c, float(np.linalg.norm(pts - c, axis=1).mean())
EYES = {'L': helper_sphere('helper-l-eye'), 'R': helper_sphere('helper-r-eye')}
for side in 'LR':
    e, eye_r = EYES[side]
    bpy.ops.mesh.primitive_uv_sphere_add(radius=eye_r, segments=32, ring_count=16, location=(0, 0, 0))
    ob = bpy.context.active_object; ob.name = 'eye' + side; ob.data.materials.append(M_EYE); smooth(ob)
    ob.parent = rig; ob.parent_type = 'BONE'; ob.parent_bone = 'eye.' + side
    ob.matrix_world = rig.matrix_world @ Matrix.Translation(Vector(e))
    EXTRA.append(ob)


def parent_head(ob, bone='head'):
    """Parent an object modelled in rig space (at rest) to one of the rig's bones."""
    ob.parent = rig; ob.parent_type = 'BONE'; ob.parent_bone = bone
    ob.matrix_world = rig.matrix_world.copy()
    EXTRA.append(ob)
    return ob


def skin_to(ob, weights):
    """Parent a mesh modelled in rig space to the rig with an armature modifier; weights: {bone: per-vertex array}."""
    ob.parent = rig; ob.parent_type = 'OBJECT'; ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.matrix_basis = Matrix.Identity(4)
    for bn, w in weights.items():
        vg = ob.vertex_groups.new(name=bn)
        for i, wi in enumerate(w):
            if wi > 1e-3: vg.add([i], float(wi), 'REPLACE')
    md = ob.modifiers.new('arm', 'ARMATURE'); md.object = rig
    EXTRA.append(ob)
    return ob


# ---------------------------------------------------------------- hair: the Louvre (Richelieu) Dionysus's
# Parted in the centre; a few thick S-shaped waves from the parting sweep sideways and back over the temples,
# under the wreath, to a knot at the back of the head; long curls at the temples frame the face, and thick
# twisted locks fall from behind the ears onto the shoulders. The forehead shows below the parting.
def group_w(name):
    gi_ = body.vertex_groups[name].index; w = np.zeros(len(V))
    for v in body.data.vertices:
        for g in v.groups:
            if g.group == gi_: w[v.index] = g.weight
    return w


w_head, w_body, w_ears = group_w('head'), group_w('body'), group_w('ears')
hb = rig.data.bones['head']; head_c = (hb.head_local + hb.tail_local) / 2
brow_z = max(eyeL[2], eyeR[2]) + 0.022
skin_head = (w_head > 0.5) & (w_body > 0.5)
HBVH = BVHTree.FromPolygons([tuple(v) for v in V], [tuple(p.vertices) for p in body.data.polygons
                                                     if all(skin_head[i] and w_ears[i] < 0.3 for i in p.vertices)])
BODYBVH = BVHTree.FromPolygons([tuple(v) for v in V], [tuple(p.vertices) for p in body.data.polygons
                                                       if all(w_body[i] > 0.5 for i in p.vertices)])
HO = Vector((0.0, float(head_c[1]) - 0.006, float(brow_z) + 0.002))   # a point inside the cranium


def push_out(p, clear):
    """Move a point (rig space, rest) out of the body so it is at least `clear` from the skin."""
    loc, nrm, _, _ = BODYBVH.find_nearest(p)
    if loc is None: return p
    dd = (p - loc).dot(nrm)
    return loc + nrm * clear + (p - loc - nrm * dd) if dd < clear else p


def sdir(phi, th, side):
    """Direction from HO: phi 0 at the front, 90 at his side (side -1 right, +1 left), 180 behind; th up."""
    p_, t_ = math.radians(phi), math.radians(th)
    return Vector((side * math.cos(t_) * math.sin(p_), -math.cos(t_) * math.cos(p_), math.sin(t_)))


def _ellipsoid_r(d):   # a smooth stand-in for the skull where the mesh has a hole (the ears)
    ax = Vector((0.076, 0.098 if d.y < 0 else 0.094, 0.092))
    return 1.0 / math.sqrt((d.x / ax.x) ** 2 + (d.y / ax.y) ** 2 + (d.z / ax.z) ** 2)


def scalp(phi, th, side, off=0.0):
    """The point of the scalp in direction (phi, th) from inside the head, pushed `off` outwards."""
    d = sdir(phi, th, side)
    hit = HBVH.ray_cast(HO, d, 0.2)
    rr = (hit[0] - HO).length if hit[0] is not None else _ellipsoid_r(d)
    return HO + d * (rr + off)


def hairline_th(phi):
    """Elevation of the hairline: high and rounded over the forehead, lower at the temples, above the ears."""
    z_ = float(np.interp(phi, (0, 25, 55, 80, 100, 180), (brow_z + 0.047, brow_z + 0.036, brow_z + 0.016,
                                                          brow_z - 0.006, brow_z - 0.012, brow_z - 0.07)))
    lo, hi = -70.0, 89.0
    for _ in range(30):
        mid = (lo + hi) / 2
        if scalp(phi, mid, 1).z > z_: hi = mid
        else: lo = mid
    return (lo + hi) / 2


HL = {ph: hairline_th(ph) for ph in range(0, 181, 5)}
def hl(phi): return float(np.interp(phi, list(HL), list(HL.values())))
print('[hair] hairline elevation at 0/45/90/135/180:', [round(hl(p_), 1) for p_ in (0, 45, 90, 135, 180)])

# the cap: the scalp above the hairline under the waves. It thins to nothing at its edge (no lip shows).
CAP = 0.006
dV = V - np.array(HO)
phiV = np.degrees(np.arctan2(np.abs(dV[:, 0]), -dV[:, 1])); thV = np.degrees(np.arcsin(dV[:, 2] / np.linalg.norm(dV, axis=1)))
hairsel = skin_head & (w_ears < 0.2) & (thV > np.interp(phiV, list(HL), list(HL.values())) + 6) & (dV[:, 2] > -0.11)
bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
keep = set(np.nonzero(hairsel)[0].tolist())
for f in [f for f in bm.faces if not all(v.index in keep for v in f.verts)]:
    bm.faces.remove(f)
for v in [v for v in bm.verts if not v.link_faces]:
    bm.verts.remove(v)
hme = bpy.data.meshes.new('haircap'); bm.to_mesh(hme); bm.free()
for a_ in list(hme.attributes):
    if a_.name in ('paint', 'brow'): hme.attributes.remove(a_)
cap = bpy.data.objects.new('haircap', hme); link(cap); cap.data.materials.append(M_HAIR)
for p in cap.data.polygons: p.use_smooth = True
cw = cap.vertex_groups.new(name='thick')
for v in hme.vertices:
    d_ = Vector(v.co) - HO; ph_ = math.degrees(math.atan2(abs(d_.x), -d_.y)); th_ = math.degrees(math.asin(d_.z / d_.length))
    cw.add([v.index], float(np.clip((th_ - hl(ph_) - 6) / 9, 0, 1)), 'REPLACE')
parent_head(cap)
sol = cap.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = CAP; sol.offset = 1.0
sol.vertex_group = 'thick'; sol.thickness_vertex_group = 0.0
sd = cap.modifiers.new('sub', 'SUBSURF'); sd.levels = 1; sd.render_levels = 1

TAPER = {}
def taper_curve(key, pts_):
    if key not in TAPER:
        tc_ = bpy.data.curves.new('taper_' + key, 'CURVE'); ts = tc_.splines.new('POLY'); ts.points.add(len(pts_) - 1)
        for p_, (x_, y_) in zip(ts.points, pts_): p_.co = (x_, y_, 0, 1)
        tob = bpy.data.objects.new('taper_' + key, tc_); link(tob); tob.hide_render = True; tob.hide_viewport = True
        TAPER[key] = tob
    return TAPER[key]


def curve_tube(name, pts_, radius, taper, mat_=None, res=3):
    pts_ = [Vector(p_) for p_ in pts_]
    while len(pts_) < 5:     # a NURBS curve of order 4 needs enough points
        pts_ = [pts_[0]] + [x for i in range(len(pts_) - 1) for x in (pts_[i].lerp(pts_[i + 1], 0.5), pts_[i + 1])]
    cu_ = bpy.data.curves.new(name, 'CURVE'); cu_.dimensions = '3D'; cu_.bevel_depth = radius; cu_.bevel_resolution = res
    cu_.use_fill_caps = True; cu_.resolution_u = 6
    sp_ = cu_.splines.new('NURBS'); sp_.points.add(len(pts_) - 1)
    for p_, v in zip(sp_.points, pts_): p_.co = (*v, 1)
    sp_.order_u = 4; sp_.use_endpoint_u = True
    if taper: cu_.taper_object = taper
    ob = bpy.data.objects.new(name, cu_); link(ob); cu_.materials.append(mat_ or M_HAIR)
    return ob


def tube(name, pts_, radius, taper, bone='head', mat_=None, res=3):
    return parent_head(curve_tube(name, pts_, radius, taper, mat_, res), bone)


def catmull(ctrl, n):
    """Points along a Catmull-Rom spline through `ctrl` (list of tuples), n samples."""
    c = [ctrl[0]] + list(ctrl) + [ctrl[-1]]; out = []
    segs = len(ctrl) - 1
    for i in range(n):
        t = i / (n - 1) * segs; k = min(int(t), segs - 1); u = t - k
        p0, p1, p2, p3 = (np.array(c[k + j]) for j in range(4))
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    return out


def sweep_bm(bm, rows, ring=20, ridges=0, ridge_depth=0.0, cap_ends=True):
    """Add a tube with an elliptical cross-section to a bmesh. rows: (centre, out, across, half_w, half_h);
    the outer half of the section is carved with `ridges` + 1 rounded strands of hair."""
    R = []
    for (c, o, ac, w, h) in rows:
        rv = []
        for j in range(ring):
            ang = 2 * math.pi * j / ring; x_ = math.cos(ang); y_ = math.sin(ang); k = 1.0
            if ridges and y_ > 0:
                k = 1 - ridge_depth * (0.5 - 0.5 * math.cos(2 * math.pi * ridges * (x_ + 1) / 2)) * y_
            rv.append(bm.verts.new(c + ac * (w * x_) + o * (h * y_ * k)))
        R.append(rv)
    for r0, r1 in zip(R, R[1:]):
        for j in range(ring):
            bm.faces.new((r0[j], r0[(j + 1) % ring], r1[(j + 1) % ring], r1[j]))
    if cap_ends:
        for rv, row in ((R[0], rows[0]), (R[-1], rows[-1])):
            cv = bm.verts.new(row[0])
            for j in range(ring): bm.faces.new((rv[j], rv[(j + 1) % ring], cv))
    return R


def bm_object(name, bm, mats, subd=1):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); link(ob)
    for m_ in mats: me.materials.append(m_)
    for p in me.polygons: p.use_smooth = True
    if subd: s_ = ob.modifiers.new('sub', 'SUBSURF'); s_.levels = subd; s_.render_levels = subd
    return ob


def smoothstep(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0))); return t * t * (3 - 2 * t)


# the waves: five thick S-shaped strands a side, from the parting sideways and back over the temples to the knot
WAVES = ((33, 0.0150, 0.0055, 0.085, 0.3), (46, 0.0168, 0.0075, 0.075, 1.9), (59, 0.0152, 0.0062, 0.092, 3.6),
         (72, 0.0170, 0.0080, 0.080, 0.9), (85, 0.0140, 0.0050, 0.070, 2.7))   # start elevation, half width, S amplitude, wavelength, phase
WAVE_TOP = 0.0
hbm = bmesh.new()
for side in (-1, 1):
    for i, (th0, w0, amp, lam, ph0) in enumerate(WAVES):
        u = i / (len(WAVES) - 1)
        w0 *= 1.0 + 0.06 * side * (1 if i % 2 else -1); ph0 += 0.7 * (side > 0)
        front_path = [(0.8, th0), (18, hl(18) + 6), (45, hl(45) + 7), (78, hl(78) + 8), (112, hl(112) + 10), (146, -2), (170, -5)]
        crown_path = [(0.8, th0), (25, th0 - 6), (60, 60), (100, 40), (135, 22), (158, 7), (174, 0)]
        ctrl = [tuple(np.array(f_) * (1 - u) + np.array(c_) * u) for f_, c_ in zip(front_path, crown_path)]
        ctrl[0] = (0.8, th0)
        path = catmull(ctrl, 60)
        raw = [scalp(ph, th, side, 0) for ph, th in path]
        s_ = [0.0]
        for j in range(1, len(raw)): s_.append(s_[-1] + (raw[j] - raw[j - 1]).length)
        tot = s_[-1]; rows = []
        for j in range(len(raw)):
            sj = s_[j] / tot
            d = (raw[j] - HO).normalized()
            tang = (raw[min(j + 1, len(raw) - 1)] - raw[max(j - 1, 0)]).normalized()
            lat = d.cross(tang).normalized()
            env = smoothstep(0.0, 0.16, sj)                 # the root runs straight out of the parting
            tap = float(np.interp(sj, (0, 0.05, 0.45, 1.0), (0.72, 1.0, 0.95, 0.4)))
            wv_ = 2 * math.pi * s_[j] / lam + ph0
            h = w0 * 0.6 * tap * (1 + 0.22 * math.sin(wv_ + math.pi / 2) * env)
            c = raw[j] + d * (CAP * 0.5 + h * 0.6) + lat * (amp * math.sin(wv_) * env)
            rows.append((c, d, lat, w0 * tap, h))
            WAVE_TOP = max(WAVE_TOP, CAP * 0.5 + h * 1.6)
        sweep_bm(hbm, rows, ridges=2, ridge_depth=0.22)
waves = parent_head(bm_object('waves', hbm, [M_HAIR]))

# the knot at the back: a twisted roll of hair
kc = scalp(180, -4, 1, 0); kd = sdir(180, -4, 1)
kx, kz = Vector((1, 0, 0)), kd.cross(Vector((1, 0, 0))).normalized()
for ring_, (rx, rz, rad, out_) in enumerate(((0.036, 0.022, 0.015, 0.016), (0.02, 0.012, 0.013, 0.028))):
    pts_ = []
    for j in range(41):
        a_ = 2 * math.pi * j / 40
        pts_.append(kc + kd * (out_ + 0.004 * math.sin(6 * a_)) + kx * rx * math.cos(a_) + kz * rz * math.sin(a_))
    tube(f'knot{ring_}', pts_, rad, None)


def coil(start, length, turns, radius, sway, phase=0.0, n=80, grow=(0.6, 0.4), wobble=0.0):
    """A corkscrew curl hanging from `start` (rig space)."""
    pts_ = []
    for i in range(n):
        t = i / (n - 1); a_ = phase + turns * 2 * math.pi * t
        rr = radius * (grow[0] + grow[1] * t) * (1 + wobble * math.sin(3.1 * a_))
        pts_.append(Vector(start) + Vector((rr * math.cos(a_) + sway[0] * t, rr * math.sin(a_) + sway[1] * t, -length * t)))
    return pts_


# curls at the temples: long, thick, brought forward in front of the ears to frame the face
t_lock = taper_curve('lock', [(0, 1), (0.6, 0.85), (1, 0.4)])
for side in (-1, 1):
    for k, (ph, ln_, tw, rr_, tr, ph_) in enumerate(((60, 0.072, 2.4, 0.0085, 0.0074, 0.4), (73, 0.060, 2.1, 0.0095, 0.0068, 2.2))):
        st_ = scalp(ph, hl(ph) + 3, side, CAP + 0.004)
        pts_ = coil(st_, ln_, tw, rr_, (side * 0.007, -0.016), phase=ph_ + (side > 0) * 1.3, wobble=0.12)
        pts_ = [push_out(p_, tr * 1.1 + 0.002) for p_ in pts_]
        tube(f'temple{side}{k}', pts_, tr, t_lock)

# long twisted locks from behind the ears onto the shoulders: thick, few turns, each its own; the upper part
# follows the head and the ends rest on the shoulders (skinned to head, neck and chest)
t_long = taper_curve('long', [(0, 0.9), (0.15, 1.0), (0.7, 0.82), (1, 0.45)])
sh_z = float(bone_head('clavicle.L')[2])
for side in (-1, 1):
    for k, (ph, th, ln_, tw, rr_, ph_) in enumerate(((112, -14, 0.19, 1.7, 0.013, 0.0), (132, -20, 0.205, 2.1, 0.016, 2.1),
                                                     (150, -24, 0.17, 1.5, 0.011, 4.0))):
        if side > 0: ph_ += 1.1; ln_ *= 0.96 + 0.05 * k
        st_ = scalp(ph, th, side, CAP + 0.008)
        pts_ = coil(st_, ln_, tw, rr_, (side * (0.018 + 0.006 * k), -0.026 + 0.014 * k), phase=ph_, wobble=0.15)
        pts_ = [push_out(p_, 0.012 * 1.05 + 0.002) for p_ in pts_]
        cob = curve_tube(f'lockc{side}{k}', pts_, 0.012, t_long)
        dg_ = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(cob.evaluated_get(dg_)); bpy.data.objects.remove(cob, do_unlink=True)
        lk = bpy.data.objects.new(f'lock{side}{k}', me); link(lk)
        for p in me.polygons: p.use_smooth = True
        zs = np.array([v.co.z for v in me.vertices]); z_top = float(st_.z)
        wh = np.array([smoothstep(0, 1, 1 - (z_top - z) / 0.08) for z in zs])
        below = np.array([smoothstep(0, 1, (sh_z + 0.03 - z) / 0.06) for z in zs]) * (1 - wh)
        skin_to(lk, {'head': wh, 'neck03': (1 - wh) - below, 'spine01': below * 0.6,
                     ('clavicle.L' if side > 0 else 'clavicle.R'): below * 0.4})

# ---------------------------------------------------------------- the ivy wreath on the hair, grapes at the temples
def ivy_outline(n=60):
    """A five-lobed ivy leaf in its plane (x across, y up the leaf), the stalk at the bottom; about 1.3 tall."""
    lobes = ((90, 1.0), (32, 0.68), (148, 0.68), (-22, 0.46), (202, 0.46))
    out = []
    for i in range(n):
        th = 360 * i / n - 90
        rr = 0.3
        for a_, L_ in lobes:
            dd = math.radians(((th - a_ + 180) % 360) - 180)
            rr = max(rr, L_ * max(0.0, math.cos(dd)) ** 5)
        dn = ((th + 90 + 180) % 360) - 180
        rr *= 1 - 0.55 * math.exp(-(dn / 14) ** 2)
        out.append((rr * math.cos(math.radians(th)), rr * math.sin(math.radians(th)) + 0.25))
    return out


IVY = ivy_outline()


def ivy_leaf(bm, M, size, mat_index=0, thick=0.08):
    """Add a flat ivy leaf (cupped a little, folded along the midrib, with thickness) to bm. Leaf plane: local XZ,
    tip +Z, thickness along Y; the stalk at the origin."""
    def P3(x_, y_, face):
        return M @ Vector((x_ * size, (0.12 * abs(x_) - 0.08 * (x_ * x_ + (y_ - 0.5) ** 2)) * size + face * thick * size * 0.5, y_ * size))
    top = [bm.verts.new(P3(x_, y_, -1)) for x_, y_ in IVY]; bot = [bm.verts.new(P3(x_, y_, 1)) for x_, y_ in IVY]
    ct = bm.verts.new(P3(0, 0.5, -1)); cb = bm.verts.new(P3(0, 0.5, 1)); n = len(IVY)
    for j in range(n):
        k = (j + 1) % n
        for f in (bm.faces.new((top[j], top[k], ct)), bm.faces.new((bot[k], bot[j], cb)), bm.faces.new((top[k], top[j], bot[j], bot[k]))):
            f.material_index = mat_index


WTH = lambda ph: float(np.interp(ph, (0, 45, 90, 135, 180), (hl(0) + 30, hl(45) + 30, hl(90) + 33, 18, 16)))
W_OFF = CAP + 0.018 + 0.004
NL = 14
wbm = bmesh.new()
band = []
for side in (-1, 1):
    for i in range(NL + 1):
        if side == -1 and i in (0, NL): continue        # the front and back leaves once
        ph = 180 * i / NL
        pos = scalp(ph, WTH(ph), side, W_OFF); nrm = sdir(ph, WTH(ph), side)
        nxt = scalp(ph + 2, WTH(ph + 2), side, W_OFF); tang = (nxt - pos).normalized()
        bin_ = tang.cross(nrm).normalized()
        if bin_.z < 0: bin_, tang = -bin_, -tang          # the same way up on both sides
        nrm = bin_.cross(tang).normalized()
        # each leaf stands up off the hair, leaning out, alternately turned (ivy leaves on a band)
        rot = (Matrix((tang, nrm, bin_)).transposed() @ Matrix.Rotation(math.radians(-38), 3, 'X')
               @ Matrix.Rotation(math.radians(24 * (1 if i % 2 else -1)), 3, 'Y'))
        M = Matrix.Translation(pos - bin_ * 0.004) @ rot.to_4x4()
        ivy_leaf(wbm, M, 0.03 * (1.0 + 0.12 * math.sin(i * 2.3 + side)), (i + (side > 0)) % 2)
for ph in range(0, 181, 6):
    band.append(scalp(ph, WTH(ph), 1, W_OFF - 0.004))
band = [Vector((-p_.x, p_.y, p_.z)) for p_ in reversed(band[1:])] + band
wreath = parent_head(bm_object('wreath', wbm, [M_IVY, M_IVY2], subd=0))
tube('vine', band, 0.0026, None, mat_=M_IVY2)

# grapes: a bunch of 14 at each temple, hanging past the temple in front of the ear
gbm = bmesh.new()
for side in (-1, 1):
    ph = 80
    top_ = scalp(ph, WTH(ph) - 4, side, W_OFF + 0.008)
    out_ = sdir(ph, 0, side); out_.z = 0; out_.normalize()
    axis_ = Vector((0, -0.12 * 1, -1)).normalized()
    stem = [top_ + Vector((0, 0, 0.01)), top_ + Vector((0, 0, 0.004)), top_ + axis_ * 0.006, top_ + axis_ * 0.014]
    tube(f'grapestem{side}', stem, 0.0018, None, mat_=M_IVY2)
    rowsg = ((4, 0.0105), (4, 0.0098), (3, 0.0082), (2, 0.0062), (1, 0.0))
    j = 0
    for ri, (nb, rad) in enumerate(rowsg):
        for b_ in range(nb):
            a_ = 2 * math.pi * b_ / nb + ri * 0.8
            c = top_ + axis_ * (0.017 + 0.0125 * ri) + out_ * (0.004 + rad * math.cos(a_)) \
                + Vector((0, 1, 0)).cross(out_).normalized() * (rad * math.sin(a_) * side)
            c = push_out(c, 0.009)
            rr = 0.0084 * (1 + 0.08 * math.sin(j * 1.7)); j += 1
            bmesh.ops.create_uvsphere(gbm, u_segments=14, v_segments=8, radius=rr, matrix=Matrix.Translation(c))
grapes = parent_head(bm_object('grapes', gbm, [M_GRAPE], subd=0))

# ---------------------------------------------------------------- the himation: a rolled drape over his left shoulder
# It runs from behind his left shoulder, over it, and down across his chest to the right hip (below the
# counter, where it would wrap his hips). It follows the body's surface and is parented to the chest.
# It is built as a curve with a pleated cross-section (a few broad folds along its length), then made a mesh
# whose 'edge' attribute (0 along the middle, 1 at both long edges) gives the cloth its green and gold hem.
shL = np.array(bone_head('upperarm01.L')); hipR = np.array(bone_head('upperleg01.R'))
names = [g.name for g in body.vertex_groups]
def wsum(prefixes):
    idx = [i for i, nme in enumerate(names) if any(nme.startswith(p) for p in prefixes)]
    w = np.zeros(len(V))
    for v in body.data.vertices:
        for g in v.groups:
            if g.group in idx: w[v.index] += g.weight
    return w
torso = (wsum(('upperarm', 'lowerarm', 'wrist', 'finger', 'metacarpal')) < 0.3) & (wsum(('head', 'neck', 'jaw')) < 0.3)
tfaces = [tuple(p.vertices) for p in body.data.polygons if all(torso[i] for i in p.vertices)]
BVH = BVHTree.FromPolygons([tuple(v) for v in V], tfaces)
def surface(x, z, off):
    hit = BVH.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)))
    return None if hit[0] is None else hit[0] + Vector((0, -off, 0))
p0 = shL + np.array([-0.035, 0, 0.055])          # top of the left shoulder
end = hipR + np.array([0.0, 0, 0.03])
back = [Vector((p0[0] + 0.01, 0.08, p0[2] - 0.14)), Vector((p0[0], 0.065, p0[2] - 0.04))]
over = [Vector((p0[0] - 0.005, 0.01, p0[2] + 0.02))]
front = []
for t in np.linspace(0.08, 1.0, 18):
    x = p0[0] + (end[0] - p0[0]) * t; z = p0[2] + (end[2] - p0[2]) * t
    sp = surface(x, z, 0.022 + 0.012 * math.sin(math.pi * t))
    if sp is not None: front.append(sp)
pts = back + over + front
cu = bpy.data.curves.new('himation_c', 'CURVE'); cu.dimensions = '3D'
cu.bevel_mode = 'OBJECT'
prof = bpy.data.curves.new('him_prof', 'CURVE'); ps = prof.splines.new('POLY'); NPF = 56; ps.points.add(NPF - 1)
def _him_prof(pleat):
    for i, pp in enumerate(ps.points):   # a pleated cross-section: broad folds across the width
        a_ = 2 * math.pi * i / NPF; x_ = 0.088 * math.cos(a_)
        y_ = 0.013 * math.sin(a_) + pleat * 0.017 * math.sin(3.4 * math.pi * x_ / 0.088 + 0.5) * (1 - 0.3 * abs(x_) / 0.088)
        pp.co = (x_, y_, 0, 1)
_him_prof(0.0)
ps.use_cyclic_u = True
pob = bpy.data.objects.new('him_prof', prof); link(pob); pob.hide_render = True
cu.bevel_object = pob; cu.use_fill_caps = True
sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1)
for i, (p_, v) in enumerate(zip(sp.points, pts)):
    p_.co = (*v, 1); p_.tilt = 0.5 * math.sin(i * 0.9)
sp.order_u = 4; sp.use_endpoint_u = True; cu.resolution_u = 12; cu.twist_mode = 'MINIMUM'
him_c = bpy.data.objects.new('himation_c', cu); link(him_c)
him_c.matrix_world = Matrix.Identity(4)
bpy.context.view_layer.update()
dg_ = bpy.context.evaluated_depsgraph_get()
hm_flat = bpy.data.meshes.new_from_object(him_c.evaluated_get(dg_))
_him_prof(1.0); prof.update_tag(); him_c.data.update_tag(); bpy.context.view_layer.update(); dg_ = bpy.context.evaluated_depsgraph_get()
hm = bpy.data.meshes.new_from_object(him_c.evaluated_get(dg_))
nring = len(hm.vertices) // NPF
for i, (vf, vp) in enumerate(zip(hm_flat.vertices, hm.vertices)):   # flat over the shoulder, folded down the chest
    k_ = smoothstep(0.1, 0.32, (i // NPF) / max(1, nring - 1)) * 0.85 + 0.15
    vp.co = Vector(vf.co).lerp(Vector(vp.co), k_)
prof_pts = [Vector(v.co) for v in bpy.data.meshes.new_from_object(pob.evaluated_get(dg_)).vertices]
NP_ = len(prof_pts)
assert len(hm.vertices) % NP_ == 0, (len(hm.vertices), NP_)
half_w = max(abs(p_.x) for p_ in prof_pts)
edge = np.array([abs(prof_pts[i % NP_].x) / half_w for i in range(len(hm.vertices))], dtype=np.float32)
ea = hm.attributes.new('edge', 'FLOAT', 'POINT'); ea.data.foreach_set('value', edge)
bpy.data.objects.remove(him_c, do_unlink=True)
him = bpy.data.objects.new('himation', hm); link(him); hm.materials.clear(); hm.materials.append(M_HIMATION)
for p in hm.polygons: p.use_smooth = True
parent_head(him, 'spine02')
print('[himation] mesh', len(hm.vertices), 'verts,', NP_, 'per ring')

# ---------------------------------------------------------------- the rig: IK arms, posing helpers
# Posing reads only bone matrices, so modifiers are off in the viewport depsgraph while posing (renders use
# their render settings): the frequent view-layer updates stay cheap.
def viewport_mods(on):
    for o in [body] + EXTRA:
        for md in o.modifiers: md.show_viewport = on


def empty(name):
    e = bpy.data.objects.new(name, None); link(e); return e


def upd(): bpy.context.view_layer.update()


IKT = {s: empty('ik_' + s) for s in 'LR'}
POLE = {s: empty('pole_' + s) for s in 'LR'}
for s in 'LR':
    c = PB['lowerarm02.' + s].constraints.new('IK'); c.target = IKT[s]; c.chain_count = 4
    c.pole_target = POLE[s]; c.pole_angle = math.radians(-90)
FINGER = [b.name for b in PB if b.name.startswith('finger')]
for b in PB: b.rotation_mode = 'XYZ' if b.name in FINGER else 'QUATERNION'
MW = rig.matrix_world
SIDE_X = {'L': 1, 'R': -1}


def rot(bone, axis, deg):
    """Turn a bone about an armature-space axis (x: his left, -y: his front, z: up), on top of its pose.
    Positive about x bends forward / opens the jaw / looks down; about z turns to his left; about y leans left."""
    pb = PB[bone]; B3 = rig.data.bones[bone].matrix_local.to_3x3()
    q = Quaternion((B3.inverted() @ Vector(axis)).normalized(), math.radians(deg))
    pb.rotation_quaternion = q @ pb.rotation_quaternion


def nudge(bone, delta):
    """Move an unconnected bone by `delta` (armature space, rig metres)."""
    PB[bone].location = PB[bone].location + rig.data.bones[bone].matrix_local.to_3x3().inverted() @ Vector(delta)


def wpos(bone, tail=False):
    pb = PB[bone]; return MW @ (pb.tail if tail else pb.head)


def hand_frame(side):
    """World matrix of the palm: origin on the palm, Y along the fingers, Z out of the palm, X = Y x Z."""
    wr = wpos('wrist.' + side)
    k2, k5, k3 = wpos('finger2-1.' + side), wpos('finger5-1.' + side), wpos('finger3-1.' + side)
    yv = (k3 - wr).normalized(); xv = (k2 - k5).normalized()
    zv = -yv.cross(xv).normalized() * (1 if side == 'R' else -1)
    xv = yv.cross(zv).normalized()
    o = wr.lerp(k3, 0.55) + zv * 0.012 * S
    M = Matrix((xv, yv, zv)).transposed().to_4x4(); M.translation = o
    return M


def palm_n(side): return hand_frame(side).col[2].xyz
def finger_dir(side): return hand_frame(side).col[1].xyz


def fist_point(side):
    """World point in the middle of the closed fist: the centre of the loop each curled finger makes
    (knuckle, middle joints, fingertip), for the index to little fingers."""
    pts = []
    for f in (2, 3, 4, 5):
        pts += [wpos(f'finger{f}-1.{side}'), wpos(f'finger{f}-2.{side}'), wpos(f'finger{f}-3.{side}'), wpos(f'finger{f}-3.{side}', True)]
    return sum(pts, Vector()) / len(pts)


def fist_axis(side):
    """World direction through the fist, from the little finger's side to the index finger's."""
    return (wpos(f'finger2-1.{side}') - wpos(f'finger5-1.{side}')).normalized()


def turn_wrist(side, q):
    wb = PB['wrist.' + side]; piv = MW @ wb.head
    Rw = Matrix.Translation(piv) @ q.to_matrix().to_4x4() @ Matrix.Translation(-piv)
    wb.matrix = MW.inverted() @ Rw @ MW @ wb.matrix


def align_wrist(side, vec_fn, want, turns=3, amount=1.0):
    """Turn the wrist (from its IK-given pose) so vec_fn(side) points along `want`."""
    for _ in range(turns):
        upd(); q = vec_fn(side).rotation_difference(Vector(want).normalized())
        if amount < 1: q = Quaternion().slerp(q, amount)
        turn_wrist(side, q)
    upd()


def clavicle_follow(side, tgt):
    """The shoulder girdle follows the hand: up when the hand is high, forward when it reaches in front."""
    sh = MW @ rig.data.bones['shoulder01.' + side].head_local
    rel = (tgt - sh) / (0.55 * S); sx = SIDE_X[side]
    elev = max(-0.3, min(1.2, rel.z + 0.25)); fwd = max(0.0, min(1.0, -rel.y - 0.1)); across = max(0.0, min(1.0, -sx * rel.x))
    rot('clavicle.' + side, (0, 1, 0), -sx * 16 * elev)
    rot('clavicle.' + side, (0, 0, 1), -sx * (7 * fwd + 6 * across))


def set_pole(side, off):
    sh = MW @ rig.data.bones['upperarm01.' + side].head_local
    POLE[side].location = sh + Vector((SIDE_X[side] * off[0], off[1], off[2]))


def place_palm(side, want, face=None, along=None, iters=3, wrist_amount=1.0):
    """Move the hand (IK) so the palm's centre is at `want`, turning the wrist so the palm faces `face`
    and/or the fingers point `along` (each optional)."""
    want = Vector(want)
    if not hasattr(place_palm, 'off'): place_palm.off = {}
    off = place_palm.off.get(side, Vector((0, 0, 0)))
    IKT[side].location = want - off
    for _ in range(iters):
        upd()
        if face is not None: align_wrist(side, palm_n, face, 2, wrist_amount)
        if along is not None: align_wrist(side, finger_dir, along, 2, wrist_amount)
        err = want - hand_frame(side).translation
        IKT[side].location = IKT[side].location + err
    upd()
    place_palm.off[side] = want - IKT[side].location
    if DEBUG: print(f'[palm {side}] miss {(want - hand_frame(side).translation).length:.3f} at', tuple(round(v) for v in world_units(want)), flush=True)


def grip(side, amount, thumb=None):
    """Curl the fingers; 0 open, 1 a firm grip."""
    th = amount if thumb is None else thumb
    for f in range(1, 6):
        for j in (1, 2, 3):
            nme = f'finger{f}-{j}.{side}'
            if nme in PB:
                k = (0.5 * th) if f == 1 else amount * (1.0 + 0.08 * (f - 2))
                PB[nme].rotation_euler = (math.radians((55 if j > 1 or f > 1 else 20) * k), 0, 0)


def hold_axis(side, tip, root, offset=0.0, turns=4):
    """Turn the wrist so the fist's axis lines up with a staff or bottle neck, then run it from `tip` (its lower
    end's aim, e.g. in the glass) up through the middle of the fist. offset moves the object along its axis."""
    for _ in range(turns):
        upd()
        up = (fist_point(side) - tip).normalized()
        turn_wrist(side, fist_axis(side).rotation_difference(up))
    upd()
    g = fist_point(side); ax = (g - tip).normalized()
    root.matrix_world = axis_matrix(tip + ax * offset, ax) @ Matrix.Diagonal((*root.scale, 1))
    upd()
    return math.degrees(fist_axis(side).angle(ax))


def axis_matrix(origin, axis, up=Vector((0, -1, 0))):
    z = Vector(axis).normalized(); x = up.cross(z)
    if x.length < 1e-4: x = Vector((1, 0, 0))
    x.normalize(); y = z.cross(x)
    M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = origin; return M


def world_units(pt):
    """World (Blender) point -> B's world units (x, y) as the camera sees it."""
    from bpy_extras.object_utils import world_to_camera_view
    r.resolution_x, r.resolution_y = G['FW'], G['FH']
    co = world_to_camera_view(scene, cam, pt)
    return G['FRAME'][0] + co.x * G['FW'], G['FRAME'][1] + (1 - co.y) * G['FH']


def head_rect():
    """World rect of his head (hair, face, wreath), for the speech bubble."""
    x0, y0, x1, y1 = bbox_world([cap, wreath], 0)
    return [round(x0), round(y0), round(x1 - x0), round((y1 - y0) * 1.25)]


# ---------------------------------------------------------------- keyframes
def track(t, keys, cyc=True):
    """Smooth (Hermite) interpolation through keys [(time 0..1, value[, 'h'])]; 'h' marks a key he settles on
    (zero velocity). Cyclic tracks wrap at 1."""
    n = len(keys); ts = [k[0] for k in keys]; vs = [np.atleast_1d(np.array(k[1], float)) for k in keys]
    hold = [len(k) > 2 and k[2] == 'h' for k in keys]
    if cyc:
        tim = lambda j: ts[j % n] + (j // n); val = lambda j: vs[j % n]; hd = lambda j: hold[j % n]
        tt = t % 1.0
        if tt < ts[0]: tt += 1
        i = 0
        while tim(i + 1) <= tt: i += 1
    else:
        tim = lambda j: ts[max(0, min(n - 1, j))]; val = lambda j: vs[max(0, min(n - 1, j))]
        hd = lambda j: hold[max(0, min(n - 1, j))] or j <= 0 or j >= n - 1
        tt = max(ts[0], min(ts[-1], t)); i = 0
        while i < n - 2 and ts[i + 1] <= tt: i += 1
    t0, t1 = tim(i), tim(i + 1); h = max(1e-6, t1 - t0); u = (tt - t0) / h
    def tan(j):
        if hd(j): return 0 * vs[0]
        dt_ = tim(j + 1) - tim(j - 1)
        return (val(j + 1) - val(j - 1)) / dt_ if dt_ > 1e-6 else 0 * vs[0]
    m0, m1 = tan(i), tan(i + 1)
    out = (2 * u ** 3 - 3 * u ** 2 + 1) * val(i) + (u ** 3 - 2 * u ** 2 + u) * h * m0 + (-2 * u ** 3 + 3 * u ** 2) * val(i + 1) + (u ** 3 - u ** 2) * h * m1
    return float(out[0]) if out.size == 1 else out


def bump(t, a, b):
    """0 outside [a, b], a smooth hump to 1 in its middle."""
    if t <= a or t >= b: return 0.0
    return math.sin(math.pi * (t - a) / (b - a)) ** 2


# ---------------------------------------------------------------- body: spine, head, breath, face
def body_pose(bend=0.0, twist=0.0, lean=0.0, pitch=0.0, yaw=0.0, roll=0.0, breath=0.0):
    """bend forward, twist to his left, lean to his left (degrees, spread over the spine); head pitch (down +),
    yaw (to his left +), roll (to his left shoulder +), spread over neck and head; breath 0..1."""
    for b_, k in (('spine05', 0.15), ('spine04', 0.25), ('spine03', 0.3), ('spine02', 0.3)):
        rot(b_, (1, 0, 0), bend * k); rot(b_, (0, 0, 1), twist * k); rot(b_, (0, 1, 0), lean * k)
    rot('spine02', (1, 0, 0), -1.4 * breath); rot('spine01', (1, 0, 0), -0.6 * breath)
    for b_, k in (('neck01', 0.2), ('neck02', 0.25), ('neck03', 0.15), ('head', 0.4)):
        rot(b_, (1, 0, 0), pitch * k); rot(b_, (0, 0, 1), yaw * k); rot(b_, (0, 1, 0), roll * k)


def face(smile=0.0, open_=0.0, brow=(0.0, 0.0), wink=(0.0, 0.0), look=(0.0, 0.0), squint=0.0):
    """Expression from the default rig's face bones (MPFB ships no expression data). smile 0..1 (a warm
    closed-to-open smile), open_ 0..1 (jaw), brow (left, right) raise 0..1, wink (left, right) 0..1,
    look (yaw to his left, pitch up) degrees for the eyes, squint 0..1 (lower lids up, as in a real smile)."""
    pass


def rest_pose():
    for b in PB:
        b.rotation_euler = (0, 0, 0); b.rotation_quaternion = (1, 0, 0, 0); b.location = (0, 0, 0); b.scale = (1, 1, 1)
    for s in 'LR': set_pole(s, (2.0, 2.2, -3.2))


# ---------------------------------------------------------------- props (rendered with him)
def pmat(name, *a, **k):
    m_ = mat(name, *a, **k); return m_


M_GLASS = glass_material()
M_CLOTH = fawn_material()
M_STEEL = mat('shaker', '#e2d2ae', 0.3, 0.55)
M_STEEL2 = mat('shaker_cap', '#c9a24a', 0.3, 0.7)
M_BOTTLE = mat('dio_bottle', '#7a3612', 0.18, coat=0.6)
M_BOTTLE2 = mat('dio_bottle2', '#2f4a2a', 0.18, coat=0.6)
M_LABEL = mat('dio_label', '#f1e6cf', 0.7)
M_CORK = mat('dio_cork', '#c9a24a', 0.35, 0.8)
M_HONEYD = mat('honey_drip', '#d98a12', 0.08, coat=1.0)
M_HONEYD.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value = 0.35
M_POUR = mat('pour_stream', '#c8741a', 0.05, coat=1.0)
M_POUR.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value = 0.5
if FINISH == 'white':
    M_WOOD = M_CONE = M_SCALE = M_RIBBON = M_RIBBON2 = marble_material('thyrsus_white', paint=False, lo='#bcc7d4', hi='#e4ecf5', ao=0.5, ao_dist=0.08)
    M_TIVY = (M_WOOD, M_WOOD)
else:
    M_WOOD = mat('thyrsus_wood', '#6e4a28', 0.55)
    M_CONE = mat('pinecone', '#4d3016', 0.6)
    M_SCALE = mat('pinescale', '#9c6c2a', 0.42, 0.25)
    M_RIBBON = mat('ribbon', '#8e2a22', 0.6); M_RIBBON2 = mat('ribbon2', '#2f5a32', 0.6)
    M_TIVY = (M_IVY, M_IVY2)


GLASS_R = 0.225
CUP_S = 1.3
def prop_glass():
    """His kantharos (Q9+), in gold-tinted glass (transmissive; the film lets the bar show through it): a deep
    bowl on a short stem and foot, with two tall loop handles. Origin at the foot."""
    g_ = lathe('p_glass', [(0, 0), (0, 0.12), (0.025, 0.13), (0.045, 0.045), (0.15, 0.04), (0.19, 0.075), (0.27, 0.17), (0.37, 0.215),
                           (0.5, GLASS_R), (0.512, 0.212), (0.37, 0.2), (0.27, 0.155), (0.21, 0.07)], M_GLASS, 40)
    smooth(g_)
    for sx in (-1, 1):
        pts_ = [Vector((sx * x_, 0, z_)) for x_, z_ in ((0.205, 0.46), (0.25, 0.56), (0.32, 0.6), (0.37, 0.55), (0.36, 0.42), (0.3, 0.32), (0.235, 0.27))]
        h_ = curve_tube('p_handle', pts_, 0.022, None, M_GLASS, 3); h_.parent = g_
    g_.scale = (CUP_S, CUP_S, CUP_S)
    return g_


def prop_thyrsus():
    """Origin at the staff's lower end; held about 0.8 up, the pine cone 1.15 above the hand. Returns the staff
    (the root); cone, scales, ribbons and ivy are parented to it."""
    o_ = 0.8; Lh = 1.15; R_ = 0.04
    st = lathe('p_staff', [(0.0, 0.0), (0.0, 0.032), (0.02, R_), (Lh + o_, R_ * 0.9)], M_WOOD, 16); smooth(st)
    zc0 = Lh + o_ - 0.06
    prof = [(0.0, 0.0), (0.02, 0.06), (0.08, 0.098), (0.18, 0.108), (0.28, 0.088), (0.36, 0.05), (0.42, 0.0)]
    cone = lathe('p_cone', [(zc0 + z, r_) for z, r_ in prof], M_CONE, 24); smooth(cone); cone.parent = st
    bm = bmesh.new(); n = 96; ga = math.pi * (3 - math.sqrt(5))
    zs, rs = [p_[0] for p_ in prof], [p_[1] for p_ in prof]
    for i in range(n):
        f = (i + 0.5) / n; z = 0.03 + 0.37 * f
        rr = float(np.interp(z, zs, rs)); a_ = i * ga
        er = Vector((math.cos(a_), math.sin(a_), 0)); et = Vector((-math.sin(a_), math.cos(a_), 0)); ez = Vector((0, 0, 1))
        size = 0.03 * (0.55 + 0.6 * math.sin(math.pi * min(1.0, f * 1.05)))
        R3 = Matrix((et, ez, er)).transposed() @ Matrix.Rotation(math.radians(-35), 3, 'X')
        M = Matrix.Translation(Vector((0, 0, zc0 + z)) + er * (rr * 0.92)) @ R3.to_4x4() @ Matrix.Diagonal((size * 0.95, size * 1.15, size * 0.42, 1))
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0, matrix=M)
    sc = bm_object('p_scales', bm, [M_SCALE], subd=0); sc.parent = st
    # a red fillet wound round the staff under the cone, its two ends hanging, and an ivy vine with leaves
    rb = bmesh.new()
    rows = []
    for i in range(60):
        f = i / 59; a_ = 2.6 * 2 * math.pi * f; z = zc0 - 0.32 + 0.3 * f
        c = Vector((math.cos(a_) * (R_ + 0.006), math.sin(a_) * (R_ + 0.006), z))
        rows.append((c, Vector((math.cos(a_), math.sin(a_), 0)), Vector((0, 0, 1)), 0.03, 0.005))
    sweep_bm(rb, rows, ring=8)
    for k, a0 in enumerate((0.3, 1.2)):
        rows = []
        for i in range(24):
            f = i / 23; er = Vector((math.cos(a0), math.sin(a0), 0))
            c = Vector((0, 0, zc0 - 0.33)) + er * (R_ + 0.01 + 0.09 * f) + Vector((0, 0, -0.34 * f)) \
                + Vector((-math.sin(a0), math.cos(a0), 0)) * (0.025 * math.sin(f * 7 + k))
            rows.append((c, Vector((-math.sin(a0), math.cos(a0), 0)), er.cross(Vector((0, 0, 1))).cross(er).normalized(), 0.028 * (1 - 0.3 * f), 0.005))
        sweep_bm(rb, rows, ring=8)
    rib = bm_object('p_ribbon', rb, [M_RIBBON], subd=0); rib.parent = st
    lb = bmesh.new()
    for k in range(5):
        a_ = k * 2.4; z = zc0 - 0.05 - 0.07 * k
        er = Vector((math.cos(a_), math.sin(a_), 0)); et = Vector((-math.sin(a_), math.cos(a_), 0))
        R3 = Matrix((et, er, Vector((0, 0, 1)))).transposed() @ Matrix.Rotation(math.radians(-60), 3, 'X')
        ivy_leaf(lb, Matrix.Translation(Vector((0, 0, z)) + er * R_) @ R3.to_4x4(), 0.13, k % 2, thick=0.06)
    lv = bm_object('p_tivy', lb, list(M_TIVY), subd=0); lv.parent = st
    return st


def prop_bottle(name='p_bottle', r0=0.17, h=1.25, m_=None):
    """A wine bottle: body, shoulder, neck (held at the neck's base, about 0.95 up), a gold cap and a label."""
    k = h / 1.25
    b_ = lathe(name, [(0, 0), (0, r0 * 0.9), (0.02 * k, r0), (0.74 * k, r0), (0.86 * k, r0 * 0.7), (0.95 * k, 0.065), (1.2 * k, 0.058),
                      (1.22 * k, 0.07), (1.25 * k, 0.066), (1.25 * k, 0)], m_ or M_BOTTLE, 32); smooth(b_)
    lb = lathe(name + '_label', [(0.22 * k, r0 + 0.004), (0.55 * k, r0 + 0.004)], M_LABEL, 32); lb.parent = b_
    cp = lathe(name + '_cap', [(1.13 * k, 0.064), (1.26 * k, 0.072), (1.27 * k, 0)], M_CORK, 24); cp.parent = b_
    return b_


def prop_shaker():
    """A two-part shaker: a tin and its cap. Origin at the bottom; about 0.9 tall."""
    s_ = lathe('p_shaker', [(0, 0), (0, 0.15), (0.03, 0.165), (0.55, 0.205), (0.57, 0.21), (0.6, 0.195)], M_STEEL, 32); smooth(s_)
    c_ = lathe('p_shaker_cap', [(0.56, 0.2), (0.62, 0.21), (0.72, 0.17), (0.8, 0.1), (0.86, 0.09), (0.9, 0.0)], M_STEEL2, 32); smooth(c_)
    c_.parent = s_
    return s_


def remove_obj(name):
    o = bpy.data.objects.get(name)
    if o: bpy.data.objects.remove(o, do_unlink=True)


def cloth_mesh(wad_lo, wad_hi, anchor, out, size=1.0):
    """The fawn skin, rebuilt every frame in world space: a crumpled wad pushed into the glass (from wad_lo,
    in the glass, up to wad_hi, in his fist) and a flap hanging from his hand over the rim and down outside."""
    remove_obj('p_cloth')
    bm = bmesh.new(); uv = bm.loops.layers.uv.new()
    ax = (wad_hi - wad_lo); ln_ = ax.length; ax.normalize()
    ex = ax.cross(Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0))).normalized(); ey = ax.cross(ex)
    NU, NV = 14, 9; grid = []
    for i in range(NV):
        v_ = i / (NV - 1); row = []
        for j in range(NU):
            a_ = 2 * math.pi * j / NU
            rr = (0.1 + 0.03 * math.sin(3 * a_ + 5 * v_) + 0.02 * math.sin(7 * a_ - 3 * v_)) * size * (0.75 + 0.35 * math.sin(math.pi * v_))
            row.append(bm.verts.new(wad_lo + ax * (ln_ * v_ - 0.04) + (ex * math.cos(a_) + ey * math.sin(a_)) * rr))
        grid.append(row)
    for i in range(NV - 1):
        for j in range(NU):
            f = bm.faces.new((grid[i][j], grid[i][(j + 1) % NU], grid[i + 1][(j + 1) % NU], grid[i + 1][j]))
            for lp, (uu, vv) in zip(f.loops, ((j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1))): lp[uv].uv = (uu / NU * 0.6, vv / NV * 0.4)
    for rowi, sgn in ((0, -1), (NV - 1, 1)):
        cv = bm.verts.new(wad_lo + ax * (-0.06 if sgn < 0 else ln_ + 0.02))
        for j in range(NU): bm.faces.new((grid[rowi][(j + 1) % NU], grid[rowi][j], cv) if sgn < 0 else (grid[rowi][j], grid[rowi][(j + 1) % NU], cv))
    # the flap: out over the rim, then down, with a few broad folds
    out = Vector((out.x, out.y, 0)).normalized(); side_ = Vector((0, 0, 1)).cross(out).normalized()
    FU, FV = 9, 12; fl = []
    for i in range(FV):
        v_ = i / (FV - 1); row = []
        for j in range(FU):
            u_ = j / (FU - 1) - 0.5
            w_ = (0.22 + 0.16 * v_) * size
            p_ = anchor + out * (0.16 * size * smoothstep(0, 0.35, v_) + 0.035 * math.sin(u_ * 2.6 * math.pi + v_ * 2.0)) \
                + side_ * (u_ * w_) + Vector((0, 0, -0.55 * size * v_ + 0.06 * size * (1 - smoothstep(0, 0.3, v_))))
            row.append(bm.verts.new(p_))
        fl.append(row)
    for i in range(FV - 1):
        for j in range(FU - 1):
            f = bm.faces.new((fl[i][j], fl[i][j + 1], fl[i + 1][j + 1], fl[i + 1][j]))
            for lp, (uu, vv) in zip(f.loops, ((j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1))): lp[uv].uv = (0.5 + uu / FU * 0.5, vv / FV)
    me = bpy.data.meshes.new('p_cloth'); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('p_cloth', me); link(ob); me.materials.append(M_CLOTH)
    for p in me.polygons: p.use_smooth = True
    so = ob.modifiers.new('sol', 'SOLIDIFY'); so.thickness = 0.012
    sd_ = ob.modifiers.new('sub', 'SUBSURF'); sd_.levels = 1; sd_.render_levels = 1
    return ob


def cloth_bunch(palm, pn, fd):
    """The fawn skin, rebuilt every frame: a crumpled bunch between his right palm (centre `palm`, palm normal
    `pn`, fingers along `fd`) and the bowl, and its tail hanging from the bottom of his hand in soft folds."""
    remove_obj('p_cloth')
    bm = bmesh.new(); uv = bm.loops.layers.uv.new()
    ac = pn.cross(fd).normalized(); c0 = palm + pn * 0.03
    NU, NV = 16, 9; grid = []
    for i in range(NV):
        v_ = i / (NV - 1); row = []
        for j in range(NU):
            a_ = 2 * math.pi * j / NU; b_ = math.pi * (v_ - 0.5)
            k_ = 1 + 0.16 * math.sin(3 * a_ + 4 * v_) + 0.1 * math.sin(5 * a_ - 2 * v_ + 1)
            p_ = c0 + (fd * (0.13 * math.cos(b_) * math.cos(a_)) + ac * (0.1 * math.cos(b_) * math.sin(a_)) + pn * (0.04 * math.sin(b_))) * k_
            row.append(bm.verts.new(p_))
        grid.append(row)
    for i in range(NV - 1):
        for j in range(NU):
            f = bm.faces.new((grid[i][j], grid[i][(j + 1) % NU], grid[i + 1][(j + 1) % NU], grid[i + 1][j]))
            for lp, (uu, vv) in zip(f.loops, ((j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1))): lp[uv].uv = (uu / NU * 1.4, vv / NV * 0.7)
    # the tail: from the bunch's lowest side, down, a little toward you, turning as it falls
    low = min((c0 + fd * 0.12 * math.cos(a_) + ac * 0.1 * math.sin(a_) for a_ in np.linspace(0, 2 * math.pi, 24)), key=lambda q: q.z)
    FU, FV = 8, 12; fl = []
    for i in range(FV):
        v_ = i / (FV - 1); row = []
        tw = 0.6 * v_
        across = Vector((math.cos(tw), -0.3 * math.sin(tw), 0)).normalized(); nrm = Vector((0, 0, 1)).cross(across)
        for j in range(FU):
            u_ = j / (FU - 1) - 0.5
            p_ = low + Vector((0.04 * v_, -0.08 * v_, -0.5 * v_)) + across * (u_ * (0.1 + 0.14 * v_)) \
                + nrm * (0.03 * math.sin(u_ * 2.6 * math.pi + v_ * 3) * (0.3 + v_))
            row.append(bm.verts.new(p_))
        fl.append(row)
    for i in range(FV - 1):
        for j in range(FU - 1):
            f = bm.faces.new((fl[i][j], fl[i][j + 1], fl[i + 1][j + 1], fl[i + 1][j]))
            for lp, (uu, vv) in zip(f.loops, ((j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1))): lp[uv].uv = (0.4 + uu / FU * 0.6, 0.7 + vv / FV * 1.2)
    me = bpy.data.meshes.new('p_cloth'); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('p_cloth', me); link(ob); me.materials.append(M_CLOTH)
    for p in me.polygons: p.use_smooth = True
    so = ob.modifiers.new('sol', 'SOLIDIFY'); so.thickness = 0.012
    sd_ = ob.modifiers.new('sub', 'SUBSURF'); sd_.levels = 1; sd_.render_levels = 1
    return ob


def honey_strand(name, pts_, r0, r1):
    """A thread of honey (thin, glossy, amber) through pts_, tapering from r0 to r1, with a drop at its end."""
    remove_obj(name); remove_obj(name + '_drop')
    if len(pts_) < 2: return []
    t_ = taper_curve('honey', [(0, 1), (0.6, 0.55), (1, r1 / r0)])
    ob = curve_tube(name, pts_, r0, t_, M_HONEYD, 2)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r0 * 1.6, segments=12, ring_count=8, location=pts_[-1] + Vector((0, 0, -r0 * 0.8)))
    d_ = bpy.context.active_object; d_.name = name + '_drop'; d_.scale = (1, 1, 1.35); d_.data.materials.append(M_HONEYD); smooth(d_)
    return [ob, d_]


# ---------------------------------------------------------------- where things are on the counter (B's world units)
CX = 800
def _layers():
    t_ = open(os.path.join(PROTO, 'layers.js'), encoding='utf8').read()
    t_ = t_[t_.index('{'):]; depth = 0
    for i, ch in enumerate(t_):
        depth += ch == '{'; depth -= ch == '}'
        if depth == 0: return json.loads(t_[:i + 1])
LAY = _layers()
HJ = LAY['touch']['honey']
JAR_MOUTH = (HJ['x'] + HJ['w'] * 0.5, HJ['y'] + HJ['h'] * 0.295)   # the top of the jar's cloth cover, where the dipper comes out
COUNTER_Y = LAY.get('counterBackY', 629.9)                          # the app clips him below this
DRINK = (CX, COUNTER_Y + 10)                                         # app.js: the drink glass stands here (base centre), rim ~50 above
D_HAND = -1.3                                                        # hands over the counter, in front of his chest
print('[counter] jar mouth', tuple(round(v, 1) for v in JAR_MOUTH), 'clip', COUNTER_Y)


def free_left(t, sway=0.0):
    """His left hand at rest: hanging by his hip, below the counter's edge, fingers loosely curled."""
    set_pole('L', (2.6, 1.6, -3.4))
    tgt = S2W(CX + 118 + 3 * sway, 676, -0.62)
    place_palm('L', tgt, face=Vector((-1, 0.1, 0.1)), along=Vector((0.1, -0.15, -1)), iters=2, wrist_amount=0.6)
    grip('L', 0.35, 0.3)


def held_axis_place(side, fist_at, tip=None, root=None, offset=0.0, axis=None, iters=5):
    """IK the hand so the middle of its fist is at fist_at, the fist turned along the held object: a staff
    from `tip` (its lower end, kept where it is, e.g. in the glass) through the fist, or an object along
    `axis` (a bottle, a cup) placed through the fist with its origin `offset` below it."""
    off = getattr(held_axis_place, 'off', {}).get(side, Vector((0, 0, 0)))
    IKT[side].location = fist_at - off
    for _ in range(iters):
        upd()
        for _ in range(2):
            d_ = Vector(axis).normalized() if axis is not None else (fist_point(side) - tip).normalized()
            turn_wrist(side, fist_axis(side).rotation_difference(d_)); upd()
        IKT[side].location = IKT[side].location + (fist_at - fist_point(side))
    upd()
    g = fist_point(side)
    d_ = Vector(axis).normalized() if axis is not None else (g - tip).normalized()
    turn_wrist(side, fist_axis(side).rotation_difference(d_)); upd(); g = fist_point(side)
    if root is not None:
        org = (g - d_ * offset) if axis is not None else tip
        root.matrix_world = axis_matrix(org, d_) @ Matrix.Diagonal((*root.scale, 1)); upd()
    held_axis_place.off = getattr(held_axis_place, 'off', {}); held_axis_place.off[side] = fist_at - IKT[side].location
    if DEBUG: print(f'[hold {side}] miss {(fist_at - g).length:.3f} axis {math.degrees(fist_axis(side).angle(d_)):.0f} deg at', tuple(round(v) for v in world_units(fist_at)), flush=True)
    return g


# ---------------------------------------------------------------- loops
# Every loop poses the whole figure for t in [0, 1): spine, head, face, both arms (IK to the palm or the fist,
# with the shoulder girdle following, the wrist turned to the task and elbow poles chosen per loop), and
# places its props from the hands. Timing comes from keyframes with anticipation and settle (track()).
def L_polish(t, pr):
    """Idle (Q8 home): the glass upright on his left palm, his right hand rubbing round its outside with the
    fawn skin; halfway through he glances up at you with a raised brow and a warm smile, then back to work."""
    a = 2 * math.pi * t
    up = track(t, [(0.0, 0), (0.3, 0, 'h'), (0.42, 1.0), (0.66, 1.0, 'h'), (0.8, 0), (0.99, 0, 'h')])
    body_pose(bend=4 + 1.2 * math.sin(a), twist=-3 + 2 * math.sin(a + 0.4), lean=1.2 * math.sin(a + 1),
              pitch=17 - 21 * up, yaw=-2 + 3 * math.sin(a) + 4 * up, roll=2 + 5 * up, breath=0.5 + 0.5 * math.sin(a))
    face(smile=0.45 + 0.4 * up, brow=(0.75 * up, 0.2 * up), look=(4 * up, 14 * up - 6 * (1 - up)), squint=0.25 + 0.25 * up)
    fist = S2W(CX + 70 + 3 * math.sin(a + 0.5), 590 + 2 * math.cos(a), D_HAND - 0.1)
    clavicle_follow('L', fist)
    set_pole('L', (2.6, 1.2, -3.6)); set_pole('R', (2.6, 1.0, -3.2))
    up_ = Vector((0.05 * math.sin(a), -0.32, 1)).normalized()       # the cup tipped a little toward you
    grip('L', 0.85, 0.7)
    held_axis_place('L', fist, root=pr['glass'], axis=up_, offset=0.09 * CUP_S)
    gl = pr['glass']; n = (gl.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized(); base = gl.matrix_world.translation
    fr = (Vector((0, -1, 0)) - n * n.dot(Vector((0, -1, 0)))).normalized(); sd = n.cross(fr).normalized()
    if sd.x > 0: sd = -sd                                            # toward his right
    th = 1.35 + 0.3 * math.sin(a)                                     # on the bowl's outer side, rubbing round toward the front
    rad = fr * math.cos(th) + sd * math.sin(th)
    hgt = (0.34 + 0.05 * math.cos(a)) * CUP_S
    rp = base + n * hgt + rad * (GLASS_R * CUP_S + 0.075)
    clavicle_follow('R', rp)
    tang = n.cross(rad).normalized()
    place_palm('R', rp, face=-rad, along=n * 0.6 - tang * 0.6, wrist_amount=0.9)
    grip('R', 0.35, 0.3); upd()
    hf = hand_frame('R')
    cloth_bunch(hf.translation, hf.col[2].xyz, hf.col[1].xyz)


def L_stir(t, pr):
    """Recipe step (thyrsus): the thyrsus as a bar spoon, its lower end in the glass on the counter, his fist
    circling above it, the pine cone leaning out to his right, away from his face. Two stirs a loop; at the
    end of each loop (and the still he waits on, frame 0) a delighted look up at you."""
    a = 2 * math.pi * t * 2
    g = 1 - bump(t, 0.08, 0.72)                       # 1 around the loop's ends: the grin he waits on
    body_pose(bend=7 + 1.0 * math.sin(a), twist=-4 + 1.5 * math.sin(a + 0.6), lean=-1 + 1.0 * math.cos(a),
              pitch=20 - 16 * g, yaw=-3 + 2 * math.sin(a) + 4 * g, roll=1 + 6 * g, breath=0.5 + 0.5 * math.sin(a / 2))
    face(smile=0.35 + 0.6 * g, open_=0.25 * g, brow=(0.5 * g, 0.4 * g), look=(3 * g, 16 * g - 8 * (1 - g)), squint=0.2 + 0.35 * g)
    free_left(t, math.sin(a / 2))
    tip = S2W(DRINK[0] + 5 * math.cos(a), DRINK[1] - 18 + 2 * math.sin(a), D_HAND + 0.04 * math.sin(a))
    fist = S2W(CX - 82 + 10 * math.cos(a - 0.4), 540 + 5 * math.sin(a - 0.4), D_HAND - 0.15)
    clavicle_follow('R', fist); set_pole('R', (2.8, 1.6, -3.0))
    grip('R', 0.9, 0.8)
    held_axis_place('R', fist, tip, pr['thyrsus'])


def L_pour(t, pr):
    """Recipe step (pour, strain, vine): the bottle by its neck in his right fist; a small dip, lift it over
    the glass, tip it with the wrist and pour; he holds the pour (from `hold`) with a delighted grin."""
    k = [(0.0, (CX - 78, 612, 0.0)), (0.08, (CX - 82, 620, 0.0)), (0.34, (CX - 52, 548, 0.0)),
         (0.5, (CX - 30, 536, 0.6)), (0.62, (CX - 26, 532, 1.0)), (0.74, (CX - 24, 536, 1.0), 'h'),
         (0.87, (CX - 22, 532, 1.04)), (1.0, (CX - 24, 536, 1.0), 'h')]
    hx, hy, tip = track(t, k, cyc=False)
    g = smoothstep(0.62, 0.78, t)
    body_pose(bend=5 + 3 * smoothstep(0.1, 0.5, t), twist=-6 + 3 * smoothstep(0.2, 0.6, t), lean=-2 * smoothstep(0.1, 0.4, t),
              pitch=14 + 6 * smoothstep(0.1, 0.5, t) - 14 * g, yaw=-6 + 3 * g + 1.5 * math.sin(2 * math.pi * (t - 0.74) / 0.26) * g,
              roll=7 * g, breath=0.5 + 0.5 * math.sin(2 * math.pi * t))
    face(smile=0.4 + 0.6 * g, open_=0.35 * g, brow=(0.55 * g, 0.5 * g), look=(5 * g, 14 * g - 6 * (1 - g)), squint=0.2 + 0.4 * g)
    free_left(t)
    fist = S2W(hx, hy, D_HAND - 0.1)
    ang = math.radians(108 * tip)
    axis = Vector((math.sin(ang), -0.25 * math.sin(ang), math.cos(ang))).normalized()    # the bottle's up, tipping to his left
    clavicle_follow('R', fist); set_pole('R', (2.6, 1.8, -3.2))
    grip('R', 0.85, 0.7)
    held_axis_place('R', fist, root=pr['bottle'], axis=axis, offset=0.98)
    upd()
    for o in [o for o in bpy.data.objects if o.name.startswith('p_stream')]: bpy.data.objects.remove(o, do_unlink=True)
    if tip > 0.92:
        mouth_ = pr['bottle'].matrix_world @ Vector((0, 0, 1.27))
        bot = S2W(DRINK[0] + 2, DRINK[1] - 22, D_HAND)
        mid = mouth_.lerp(bot, 0.5) + Vector((0.03, 0, 0.02))
        wob = 0.01 * math.sin(t * 40)
        cu_ = curve_tube('p_stream', [mouth_ + Vector((0.02, 0, -0.02)), mid + Vector((wob, 0, 0)), bot], 0.028, taper_curve('stream', [(0, 1), (0.4, 0.7), (1, 0.55)]), M_POUR, 2)


def L_shake(t, pr):
    """Recipe step (shake): the shaker on a diagonal in front of his chest, the tin in his right hand, the cap
    under his left palm toward his left shoulder; two hard shakes a loop along its length, the body
    following a beat behind; a grin throughout."""
    sk = track(t * 2 % 1.0, [(0.0, -1.0), (0.1, -1.12), (0.42, 1.0), (0.52, 1.1), (0.86, -0.95)])
    lag = track((t * 2 - 0.07) % 1.0, [(0.0, -1.0), (0.1, -1.12), (0.42, 1.0), (0.52, 1.1), (0.86, -0.95)])
    body_pose(bend=4 + 1.2 * lag, twist=2 + 2.5 * lag, lean=1.5 * lag, pitch=8 - 3 * lag, yaw=-8 + 2 * lag,
              roll=6 + 2 * lag, breath=0.6)
    face(smile=0.85, open_=0.3 + 0.12 * lag, brow=(0.6, 0.55), look=(-6, 12), squint=0.5)
    axis = Vector((0.62, -0.3, 1.0)).normalized()
    c = S2W(CX + 2 + 13 * sk, 548 - 15 * sk, D_HAND - 0.1)
    sh = pr['shaker']; base = c - axis * 0.45
    sh.matrix_world = axis_matrix(base, axis); upd()
    set_pole('R', (2.8, 1.4, -3.2)); set_pole('L', (2.8, 1.6, -3.0))
    ex = axis.cross(Vector((0, -1, 0))).normalized()
    if ex.x > 0: ex = -ex                                   # across the shaker, toward his right and down
    rp = base + axis * 0.28 + ex * 0.24
    lp = base + axis * 0.99
    clavicle_follow('R', rp); clavicle_follow('L', lp)
    place_palm('R', rp, face=-ex, along=axis * 0.5 + Vector((0, -0.6, 0.2)), wrist_amount=0.85)
    place_palm('L', lp, face=-axis, along=Vector((-0.6, -0.5, 0.1)), wrist_amount=0.85)
    grip('R', 0.75, 0.6); grip('L', 0.4, 0.35)


def L_reach(t, pr):
    """Recipe step (lemon, mint, ice, garnish): he looks up, reaches up and back to the shelf, takes a small
    bottle by the neck, brings it down in front of him and holds it out over the counter, delighted."""
    k = [(0.0, (CX - 70, 600, -0.9)), (0.07, (CX - 74, 612, -0.95)), (0.28, (CX - 162, 365, 0.25)), (0.38, (CX - 170, 338, 0.45), 'h'),
         (0.45, (CX - 168, 342, 0.45), 'h'), (0.56, (CX - 178, 440, -0.4)), (0.67, (CX - 92, 530, -1.25)), (0.73, (CX - 62, 546, -1.32)),
         (0.79, (CX - 66, 538, -1.3), 'h'), (0.9, (CX - 67, 534, -1.3)), (1.0, (CX - 66, 538, -1.3), 'h')]
    hx, hy, hd = track(t, k, cyc=False)
    upv = bump(t, 0.05, 0.6) ** 0.7
    g = smoothstep(0.66, 0.8, t)
    body_pose(bend=3 - 5 * upv, twist=-4 - 12 * upv, lean=-5 * upv, pitch=10 - 32 * upv - 10 * g, yaw=-6 - 16 * upv + 6 * g,
              roll=-4 * upv + 7 * g, breath=0.5 + 0.5 * math.sin(2 * math.pi * t))
    face(smile=0.35 + 0.15 * upv + 0.5 * g, open_=0.1 * upv + 0.3 * g, brow=(0.3 * upv + 0.55 * g, 0.3 * upv + 0.5 * g),
         look=(-8 * upv + 5 * g, 14 * upv + 12 * g), squint=0.15 + 0.4 * g)
    free_left(t)
    fist = S2W(hx, hy, hd)
    closed = smoothstep(0.38, 0.45, t)
    clavicle_follow('R', fist); set_pole('R', (3.0, 2.4, -2.0 - 1.4 * (1 - upv)))
    b_ = pr['small']
    up_dir = Vector((0.15 * (1 - g), 0.1, 1)).normalized()
    if closed < 0.5:      # not holding it yet: the open hand, fingers up, palm toward the shelf
        b_.hide_render = True
        place_palm('R', fist, face=Vector((0.8, 0.55, -0.1)), along=Vector((-0.15, 0.25, 1)), wrist_amount=0.9)
        grip('R', 0.35 + 0.5 * closed, 0.3 + 0.4 * closed)
    else:
        b_.hide_render = False
        grip('R', 0.85, 0.7)
        held_axis_place('R', fist, root=b_, axis=up_dir, offset=0.62)


def L_story(t, pr):
    """Tap him: he tells a story: eyes up to you, brows raised, an open right hand turning out as he talks, the
    left hand lifting a little, head nodding and tilting, mouth moving."""
    a = 2 * math.pi * t
    body_pose(bend=1 + 1.5 * math.sin(a), twist=-3 + 3 * math.sin(a), lean=1.5 * math.sin(a + 1.2), pitch=-2 + 5 * math.sin(2 * a + 0.5),
              yaw=6 * math.sin(a + 0.3), roll=5 * math.sin(a + 0.9), breath=0.5 + 0.5 * math.sin(a))
    talk = 0.5 + 0.5 * math.sin(a * 4 + 0.3) * math.sin(a * 2 + 1.1)
    face(smile=0.55 + 0.2 * math.sin(a), open_=0.15 + 0.35 * talk, brow=(0.55 + 0.35 * math.sin(a * 2), 0.5 + 0.3 * math.sin(a * 2 + 0.3)),
         look=(3 * math.sin(a), 14), squint=0.2)
    rx = track(t, [(0.0, (CX - 92, 560)), (0.22, (CX - 146, 522)), (0.45, (CX - 118, 548)), (0.7, (CX - 156, 532)), (0.86, (CX - 110, 556))])
    rp = S2W(rx[0], rx[1], D_HAND + 0.1)
    turn = 0.5 + 0.5 * math.sin(a * 2)
    set_pole('R', (2.8, 1.4, -3.4)); clavicle_follow('R', rp)
    place_palm('R', rp, face=Vector((-0.45 * turn, -0.35, 0.85)).normalized(), along=Vector((-0.75, -0.6, 0.15)), wrist_amount=0.8)
    grip('R', 0.12 + 0.12 * (1 - turn), 0.1)
    lp = S2W(CX + 112 + 16 * math.sin(a + 2), 580 + 12 * math.sin(a * 2 + 1), D_HAND + 0.2)
    set_pole('L', (2.6, 1.4, -3.4)); clavicle_follow('L', lp)
    place_palm('L', lp, face=Vector((0.4, -0.3, 0.85)).normalized(), along=Vector((0.6, -0.75, 0.1)), wrist_amount=0.7)
    grip('L', 0.12, 0.15)


def L_dip(t, pr):
    """Recipe step (honey, R8): the thyrsus through his right fist, its lower end lowered into the honey jar on
    the counter, dipped, lifted dripping and carried over the glass, where he holds it as the honey runs
    (from `hold`), pleased with himself. The jar is the app's own layer; only his staff tip goes into it."""
    jx, jy = JAR_MOUTH
    k = [(0.0, (CX - 100, 560, CX - 104, 640)), (0.07, (CX - 104, 566, CX - 108, 646)),
         (0.27, (jx - 16, 516, jx + 2, jy - 6)), (0.34, (jx - 18, 530, jx, jy + 14), 'h'),
         (0.4, (jx - 17, 524, jx + 1, jy + 8)), (0.46, (jx - 18, 532, jx, jy + 16), 'h'),
         (0.62, (jx + 14, 486, jx + 34, jy - 36)), (0.76, (CX - 84, 522, DRINK[0] - 8, DRINK[1] - 66)),
         (0.82, (CX - 86, 526, DRINK[0] - 10, DRINK[1] - 62), 'h'), (0.91, (CX - 85, 524, DRINK[0] - 9, DRINK[1] - 64)),
         (1.0, (CX - 86, 526, DRINK[0] - 10, DRINK[1] - 62), 'h')]
    fx, fy, tx, ty = track(t, k, cyc=False)
    reach = bump(t, 0.05, 0.75) ** 0.6
    g = smoothstep(0.74, 0.84, t)
    body_pose(bend=5 + 6 * reach, twist=-3 - 5 * reach + 3 * g, lean=-1.5 * reach, pitch=14 + 10 * reach - 16 * g,
              yaw=-5 - 9 * reach + 8 * g, roll=-2 * reach + 7 * g, breath=0.5 + 0.5 * math.sin(2 * math.pi * t))
    face(smile=0.4 + 0.15 * reach + 0.45 * g, open_=0.1 * reach + 0.3 * g, brow=(0.2 * reach + 0.6 * g, 0.2 * reach + 0.5 * g),
         look=(-10 * reach * (1 - g) + 5 * g, -8 * reach * (1 - g) + 14 * g), squint=0.2 + 0.35 * g)
    free_left(t)
    fist = S2W(fx, fy, D_HAND - 0.05)
    tip = S2W(tx, ty, -0.85 + (D_HAND + 0.85) * smoothstep(0.55, 0.76, t))
    clavicle_follow('R', fist); set_pole('R', (2.6, 2.2, -2.8))
    grip('R', 0.9, 0.8)
    held_axis_place('R', fist, tip, pr['thyrsus'])
    upd()
    end = pr['thyrsus'].matrix_world @ Vector((0, 0, 0.0)); ax_ = (pr['thyrsus'].matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
    for o in [o for o in bpy.data.objects if o.name.startswith('p_honey')]: bpy.data.objects.remove(o, do_unlink=True)
    # honey: a coat on the tip once dipped; a thread back to the jar as it lifts, which thins and breaks;
    # then a drip from the tip, and over the glass a steady thread into it
    if t > 0.36:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.055, segments=16, ring_count=8, location=end + ax_ * 0.05)
        c_ = bpy.context.active_object; c_.name = 'p_honey_coat'; c_.scale = (1, 1, 2.0)
        c_.rotation_euler = ax_.to_track_quat('Z', 'Y').to_euler(); c_.data.materials.append(M_HONEYD); smooth(c_)
    jar = S2W(jx, jy + 4, -0.85)
    if 0.46 < t < 0.6:
        f = (t - 0.46) / 0.14
        mid = end.lerp(jar, 0.5) + Vector((0, 0, -0.1 * f))
        honey_strand('p_honey_thread', [end, mid, jar], 0.022 * (1 - 0.6 * f), 0.012)
    elif 0.6 <= t < 0.76:
        f = (t - 0.6) / 0.16
        honey_strand('p_honey_drip', [end, end + Vector((0, 0, -0.08 - 0.25 * f))], 0.02, 0.01)
    elif t >= 0.76:
        bot = S2W(DRINK[0] - 4, DRINK[1] - 26, D_HAND)
        ph = (t - 0.76) / 0.24
        honey_strand('p_honey_run', [end, end.lerp(bot, 0.5) + Vector((0.004 * math.sin(ph * 12), 0, 0)), bot], 0.02, 0.009)


# name: (pose, frames, fps, hold frame, props). Steps with a hold play once past the app's 3.2 s of acting,
# then loop from `hold`; steps with hold 0 are cycles whose frame 0 is the still he waits on.
LOOPS = {
    'polish': (L_polish, 20, 10, 0, ('glass',)),
    'stir': (L_stir, 14, 10, 0, ('thyrsus',)),
    'pour': (L_pour, 28, 8.5, 21, ('bottle',)),
    'shake': (L_shake, 12, 12, 0, ('shaker',)),
    'reach': (L_reach, 28, 8.5, 22, ('small',)),
    'story': (L_story, 18, 8, 0, ()),
    'dip': (L_dip, 28, 8.5, 22, ('thyrsus',)),
}
RECT = (560, 290, 1040, 640)     # world rect of every frame (the counter clips him below ~630 in the app)
K = float(_arg('--k', '1.3'))    # pixels per world unit
SAMPLES = int(_arg('--samples', '24'))
QUALITY = int(_arg('--q', '58'))


def props_for(kinds):
    pr = {}
    for kind in kinds:
        if kind == 'glass': pr['glass'] = prop_glass()
        elif kind == 'thyrsus': pr['thyrsus'] = prop_thyrsus()
        elif kind == 'bottle': pr['bottle'] = prop_bottle()
        elif kind == 'small': pr['small'] = prop_bottle('p_small', 0.11, 0.78, M_BOTTLE2)
        elif kind == 'shaker': pr['shaker'] = prop_shaker()
    return pr


def clear_props():
    for o in [o for o in bpy.data.objects if o.name.startswith('p_')]:
        bpy.data.objects.remove(o, do_unlink=True)
    place_palm.off = {}; held_axis_place.off = {}


scene.view_settings.exposure = -1.1   # his marble is pale: keep it from blowing out under the bar's warm key
cy.film_transparent_glass = True      # the glass lets the bar show through
cy.max_bounces = 8; cy.transmission_bounces = 8; cy.transparent_max_bounces = 8


def pose_frame(name, t, pr):
    rest_pose(); LOOPS[name][0](t, pr); upd()


def region_for(crop, k):
    if crop == 'head':
        hx, hy = world_units(wpos('head', True)); return (hx - 85, hy - 25, hx + 85, hy + 150)
    if crop in ('grip', 'left'):
        gx, gy = world_units(fist_point('R' if crop == 'grip' else 'L')); return (gx - 70, gy - 60, gx + 70, gy + 60)
    return RECT


def render_one(name, f, k, crop, samples, pr, tag):
    pose_frame(name, f / LOOPS[name][1], pr)
    vis = [body] + EXTRA + [o for o in bpy.data.objects if o.name.startswith('p_') and not o.hide_render]
    t0 = time.time()
    png = render_region(f'dio_{tag}_{name}_{f:02d}', region_for(crop, k), k, vis, True, samples)
    return png, time.time() - t0


def render_loop(name):
    from PIL import Image
    fn, nf, fps, hold, kinds = LOOPS[name]
    clear_props(); pr = props_for(kinds)
    frames = list(range(nf)) if not PREVIEW else [hold or nf // 2]
    if FRAMES_ARG: frames = [int(x) for x in FRAMES_ARG.split(',')]
    os.makedirs(os.path.join(OUT, name), exist_ok=True)
    times = []
    for f in frames:
        png, dt = render_one(name, f, K * (1.3 if PREVIEW else 1), 'full', SAMPLES, pr, FINISH)
        times.append(dt)
        im = Image.open(png).convert('RGBA')
        if PREVIEW:
            bg = Image.new('RGBA', im.size, (40, 30, 26, 255)); bg.alpha_composite(im)
            bg.save(os.path.join(WORK, f'preview_{name}_{FINISH}.png')); continue
        im.save(os.path.join(OUT, name, f'{f + 1:04d}.webp'), 'WEBP', quality=QUALITY, method=6, alpha_quality=80)
    rel = os.path.relpath(OUT, PROTO).replace(os.sep, '/')
    return {'frames': [f'{rel}/{name}/{f + 1:04d}.webp' for f in range(nf)], 'fps': fps, 'hold': hold,
            'secondsPerFrame': round(sum(times) / len(times), 1)}


def render_still(name, f, crop, scale, samples=24):
    from PIL import Image
    fn, nf, fps, hold, kinds = LOOPS[name]
    clear_props(); pr = props_for(kinds)
    f = nf // 2 if f is None else f
    png, dt = render_one(name, f, K * scale, crop, samples, pr, 'still')
    im = Image.open(png).convert('RGBA'); bg = Image.new('RGBA', im.size, (52, 40, 34, 255)); bg.alpha_composite(im)
    d_ = STILL_OUT or WORK; os.makedirs(d_, exist_ok=True)
    p = os.path.join(d_, f'still_{FINISH}_{name}_{f:02d}_{crop}.png'); bg.save(p)
    print('[still]', p, f'{dt:.1f}s', flush=True)


def render_sheet(name, scale):
    from PIL import Image, ImageDraw
    fn, nf, fps, hold, kinds = LOOPS[name]
    clear_props(); pr = props_for(kinds); ims = []
    for f in range(nf):
        png, dt = render_one(name, f, K * scale, 'full', 6, pr, 'sheet')
        im = Image.open(png).convert('RGBA'); bg = Image.new('RGBA', im.size, (52, 40, 34, 255)); bg.alpha_composite(im)
        ImageDraw.Draw(bg).text((3, 2), str(f), fill=(255, 220, 120)); ims.append(bg.convert('RGB'))
    cols = min(7, nf); w, h = ims[0].size; rows = (nf + cols - 1) // cols
    sh = Image.new('RGB', (cols * w, rows * h), (20, 18, 18))
    for i, im in enumerate(ims): sh.paste(im, ((i % cols) * w, (i // cols) * h))
    d_ = STILL_OUT or WORK; os.makedirs(d_, exist_ok=True)
    p = os.path.join(d_, f'sheet_{FINISH}_{name}.jpg'); sh.save(p, quality=85); print('[sheet]', p, flush=True)


ABOUT = ('Dionysus, a MakeHuman (MPFB2) base shaped towards the Louvre Dionysus, rendered by blender/build_dionysus.py '
         '(Cycles) in three finishes (Q8): loops is painted marble (the default); finishes.white and finishes.living '
         'hold the same seven loops. Coverage stays classical in every finish (Q9): the renders show the himation '
         'as modelled, and modest/cheeky apply to the drawn figure only. rect and head are in world units '
         "(prototype B's SVG space). Steps with a hold play once (past the app's 3.2 s of acting) and then loop "
         'from hold; steps with hold 0 are cycles whose frame 0 is the still he waits on.')

if __name__ == 'build_dionysus' or True:
    viewport_mods(False)
    if STILL or STILLS:
        specs = [(STILL, STILL_FRAME, STILL_CROP, STILL_SCALE)] if STILL else [tuple(s_.split(':')) for s_ in STILLS.split(',')]
        for nm, fr, crop, sc in specs:
            render_still(nm, None if fr in (None, '') else int(fr), crop or 'full', float(sc or 1))
    elif '--dry' in ARGS:
        for nm in _arg('--dry').split(','):
            clear_props(); pr = props_for(LOOPS[nm][4])
            for f in range(LOOPS[nm][1]):
                print(f'--- {nm} {f}', flush=True); pose_frame(nm, f / LOOPS[nm][1], pr)
    elif SHEET:
        for nm in SHEET.split(','): render_sheet(nm, STILL_SCALE)
    else:
        names = [ONLY_LOOP] if ONLY_LOOP else list(LOOPS)
        man = json.load(open(MAN_P)) if os.path.exists(MAN_P) else {}
        man.setdefault('loops', {}); man.setdefault('finishes', {})
        for nm in names:
            res = render_loop(nm)
            if PREVIEW: continue
            if FRAMES_ARG:       # a partial re-render keeps the manifest entry
                continue
            (man['loops'] if FINISH == 'painted' else man['finishes'].setdefault(FINISH, {'loops': {}})['loops'])[nm] = res
            print('[loop]', nm, res['secondsPerFrame'], flush=True)
        if not PREVIEW:
            rest_pose(); L_polish(0, props_for(('glass',))); upd()
            man['rect'] = [RECT[0], RECT[1], RECT[2] - RECT[0], RECT[3] - RECT[1]]
            man['head'] = head_rect()
            man['about'] = ABOUT
            man['render'] = {'engine': 'Cycles (CPU, 4 threads)', 'samples': SAMPLES, 'adaptiveThreshold': 0.02,
                             'denoiser': 'OpenImageDenoise', 'pxPerWorldUnit': K, 'webp': {'quality': QUALITY, 'alphaQuality': 80, 'method': 6}}
            man.pop('finish', None)
            out = {k_: man[k_] for k_ in ('rect', 'head', 'about', 'render', 'loops', 'finishes') if k_ in man}
            json.dump(out, open(MAN_P, 'w'), indent=1)
