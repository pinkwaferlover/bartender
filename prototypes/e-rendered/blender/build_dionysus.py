"""Dionysus for prototype E (R3, R4, R13): a MakeHuman (MPFB2) base shaped towards the Louvre "Richelieu"
Dionysus, in painted marble, rigged, and rendered as one loop per action (polish, stir, pour, shake, reach, story).

Needs MPFB2 installed as a Blender extension (user_default repository):
    git clone --depth 1 https://github.com/makehumancommunity/mpfb2
    cp -r mpfb2/src/mpfb ~/.config/blender/5.3/extensions/user_default/
Run from the repository root:
    .venv-blender/bin/python prototypes/e-rendered/blender/build_dionysus.py --preview   # one still per loop
    .venv-blender/bin/python prototypes/e-rendered/blender/build_dionysus.py             # all loops
    .venv-blender/bin/python prototypes/e-rendered/blender/build_dionysus.py --only stir # one loop

It reuses build_bar.py's scene, camera and lights (without writing any of build_bar's outputs), so his
light matches the bar, and renders him alone on a transparent film in one fixed world rectangle, which
dio-layer.js places in B's world units. It writes img/dio/<loop>/NNNN.webp and dio-loops.json.
No MakeHuman system assets are needed: a marble statue's eyes, hair, wreath and drapery are modelled here.
"""
import bpy, bmesh, math, os, sys, json, time, importlib, addon_utils
from mathutils.bvhtree import BVHTree
import numpy as np
from mathutils import Vector, Matrix, Euler

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
STILL_SCALE = float(_arg('--scale', '1'))  # pixels per world unit, as a multiple of K
STILL_CROP = _arg('--crop', 'full')        # full | head | grip (a close-up around his head or right fist)
STILL_OUT = _arg('--out')                  # folder for --still images (default: build_bar's _work folder)

# ---------------------------------------------------------------- the bar's scene, camera and lights
src = open(os.path.join(HERE, 'build_bar.py'), encoding='utf8').read()
src = src[:src.index('MANIFEST_PATH = ')]          # everything up to where build_bar writes its outputs
sys.argv = [os.path.join(HERE, 'build_bar.py'), '--only', 'none']
G = {'__file__': os.path.join(HERE, 'build_bar.py'), '__name__': 'build_bar'}
exec(compile(src, 'build_bar.py', 'exec'), G)
scene, cam, P, push, render_region, bbox_world = G['scene'], G['cam'], G['P'], G['push'], G['render_region'], G['bbox_world']
srgb, smooth, mat, link, lathe, WORK = G['srgb'], G['smooth'], G['mat'], G['link'], G['lathe'], G['WORK']
r = scene.render; cy = scene.cycles
OUT = os.path.join(PROTO, 'img', 'dio' if FINISH == 'painted' else 'dio-' + FINISH)

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
rig.location = P(800, HEAD_TOP_Y + H_WORLD, 0) - Vector((0, 0, bot_z * S)) + Vector((0, 0, 0))
bpy.context.view_layer.update()


def W(p):  # rig-space point -> world
    return rig.matrix_world @ Vector(p)


# ---------------------------------------------------------------- materials, per finish (Q8)
# painted: painted marble (the default): marble skin with painted lips, cheeks and irises, painted hair-free
#          attributes (red himation with a green and gold hem, green ivy, purple grapes).
# white:   unpainted white marble: skin, eyes (blank), hair, wreath and drapery all marble. Props as they are.
# living:  a living young man: warm skin with subsurface scattering, dark brown hair, real eyes, brows,
#          the red himation with its hem, green ivy, purple grapes.
def _node_mix(n, L, fac, a, b_):
    m_ = n.new('ShaderNodeMix'); m_.data_type = 'RGBA'
    L.new(fac, m_.inputs['Factor'])
    for sock, v in (('A', a), ('B', b_)):
        if isinstance(v, (tuple, list)): m_.inputs[sock].default_value = v
        else: L.new(v, m_.inputs[sock])
    return m_.outputs['Result']


def marble_material(name='marble', paint=True, lo='#b9b3ab', hi='#efe8de', rough=0.38):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; n = nt.nodes; L = nt.links
    b = n['Principled BSDF']
    b.inputs['Roughness'].default_value = rough
    b.inputs['Subsurface Weight'].default_value = 0.35
    b.inputs['Subsurface Radius'].default_value = (0.12, 0.08, 0.06)
    b.inputs['Subsurface Scale'].default_value = 0.08
    b.inputs['Coat Weight'].default_value = 0.15; b.inputs['Coat Roughness'].default_value = 0.25
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
    L.new(col_, b.inputs['Base Color'])
    return m


def skin_material():
    """Living skin: warm, with subsurface scattering, faint mottling, natural lips and cheeks, and brows."""
    m = bpy.data.materials.new('skin'); m.use_nodes = True
    nt = m.node_tree; n = nt.nodes; L = nt.links
    b = n['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.46
    b.inputs['Subsurface Weight'].default_value = 1.0
    b.inputs['Subsurface Radius'].default_value = (1.0, 0.42, 0.25)
    b.inputs['Subsurface Scale'].default_value = 0.025 * S       # a few millimetres of skin, at his scale
    b.inputs['Specular IOR Level'].default_value = 0.45
    tc = n.new('ShaderNodeTexCoord')
    nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 9.0; nz.inputs['Detail'].default_value = 3.0
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    col_ = _node_mix(n, L, nz.outputs['Fac'], srgb('#b77a5c'), srgb('#d29b7c'))
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
    L.new(attr.outputs['Fac'], ramp.inputs['Fac']); L.new(ramp.outputs['Color'], b.inputs['Base Color'])
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


if FINISH == 'painted':
    M_SKIN = marble_material()
    M_EYE = eye_material()
    M_HAIR = mat('hair_marble', '#d8cfc2', 0.5)       # hair carved in marble, a touch warmer and rougher
    M_IVY = mat('ivy_painted', '#3f7a34', 0.45); M_IVY2 = mat('ivy_painted2', '#2f6428', 0.45)
    M_GRAPE = mat('grape_painted', '#5b2a6b', 0.3, coat=0.5)
    M_HIMATION = himation_material()
elif FINISH == 'white':
    M_SKIN = marble_material('marble_white', paint=False, lo='#c3bdb4', hi='#f2ede5')
    M_EYE = M_SKIN                                       # blank classical eyes
    M_HAIR = marble_material('hair_white', paint=False, lo='#bfb7aa', hi='#ece5d9', rough=0.45)
    M_IVY = M_IVY2 = M_GRAPE = M_HAIR
    M_HIMATION = marble_material('drape_white', paint=False, lo='#c6c0b6', hi='#efe9df', rough=0.42)
else:
    M_SKIN = skin_material()
    M_EYE = eye_material(iris='#4b2f1d', pupil='#0b0806', white='#e9e1d7', name='eye_living', gloss=1.0)
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
    d = np.linalg.norm((V - c) / np.array([0.024, 0.03, 0.02]), axis=1)
    cheek = np.clip(1 - d, 0, 1) ** 1.5 * 0.28
    blend = cheek / np.maximum(a + cheek, 1e-6)
    tint = np.array(srgb('#d98c78')[:3])
    col[:, :3] = col[:, :3] * (1 - blend[:, None]) + tint[None] * blend[:, None]
    a = np.maximum(a, cheek)
col[:, 3] = a
ca = body.data.color_attributes.new('paint', 'FLOAT_COLOR', 'POINT')
ca.data.foreach_set('color', col.astype(np.float32).ravel())
brow = np.zeros(len(V))
for eye in (eyeL, eyeR):     # an arch over each eye, on the front of the brow ridge
    u_ = (V[:, 0] - eye[0] * 1.05) / 0.024
    zc = eye[2] + 0.0175 - 0.006 * u_ ** 2 + 0.002 * np.sign(eye[0]) * (V[:, 0] - eye[0]) / 0.024 * 0
    band = np.clip(1 - np.abs(V[:, 2] - zc) / 0.0032, 0, 1) * np.clip(1 - np.abs(u_), 0, 1) ** 0.4
    brow = np.maximum(brow, band * (V[:, 1] < eye[1] + 0.005) * 0.85)
ba = body.data.attributes.new('brow', 'FLOAT', 'POINT'); ba.data.foreach_set('value', brow.astype(np.float32))

# eyes: marble eyeballs with a painted iris (ancient statues were painted); blank in white marble
EXTRA = []   # everything that belongs to him (rendered with him)
def helper_sphere(group):
    gi_ = body.vertex_groups[group].index
    pts = np.array([V[v.index] for v in body.data.vertices if any(g.group == gi_ and g.weight > 0.5 for g in v.groups)])
    c = pts.mean(axis=0); return c, float(np.linalg.norm(pts - c, axis=1).mean())
EYES = {'L': helper_sphere('helper-l-eye'), 'R': helper_sphere('helper-r-eye')}
print('[eyes]', {k: (tuple(np.round(c, 4)), round(r_, 4)) for k, (c, r_) in EYES.items()})
for side in 'LR':
    e, eye_r = EYES[side]
    bpy.ops.mesh.primitive_uv_sphere_add(radius=eye_r, segments=32, ring_count=16, location=(0, 0, 0))
    ob = bpy.context.active_object; ob.name = 'eye' + side; ob.data.materials.append(M_EYE); smooth(ob)
    ob.parent = rig; ob.parent_type = 'BONE'; ob.parent_bone = 'head'
    ob.matrix_world = rig.matrix_world @ Matrix.Translation(Vector(e))
    EXTRA.append(ob)


def parent_head(ob, bone='head'):
    """Parent an object modelled in rig space (at rest) to one of the rig's bones."""
    ob.parent = rig; ob.parent_type = 'BONE'; ob.parent_bone = bone
    ob.matrix_world = rig.matrix_world.copy()
    EXTRA.append(ob)
    return ob


# ---------------------------------------------------------------- hair: the Louvre (Richelieu) Dionysus's
# Parted in the centre and swept back from the forehead in thick waves to a knot at the back of the head,
# curls at the temples, and long corkscrew locks falling onto the shoulders. The forehead shows below the
# parting. Each wave is a tube laid on the scalp (found by ray casts against the head) over a thin cap.
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
HO = Vector((0.0, float(head_c[1]) - 0.006, float(brow_z) + 0.002))   # a point inside the cranium


def sdir(phi, th, side):
    """Direction from HO: phi 0 at the front, 90 at his side (side -1 right, +1 left), 180 behind; th up."""
    p_, t_ = math.radians(phi), math.radians(th)
    return Vector((side * math.cos(t_) * math.sin(p_), -math.cos(t_) * math.cos(p_), math.sin(t_)))


def scalp(phi, th, side, off=0.0):
    d = sdir(phi, th, side)
    hit = HBVH.ray_cast(HO + d * 0.3, -d)
    if hit[0] is None: return HO + d * (0.09 + off)
    return hit[0] + d * off


def hairline_th(phi):
    """Elevation of the hairline: high and rounded over the forehead, lower at the temples, above the ears."""
    z_ = float(np.interp(phi, (0, 25, 55, 80, 100, 180), (brow_z + 0.040, brow_z + 0.034, brow_z + 0.016,
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

# the cap: the scalp above the hairline, a little thick, hidden under the waves
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
parent_head(cap)
sol = cap.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.008; sol.offset = 1.0
sd = cap.modifiers.new('sub', 'SUBSURF'); sd.levels = 1; sd.render_levels = 1

TAPER = {}
def taper_curve(key, pts_):
    if key not in TAPER:
        tc_ = bpy.data.curves.new('taper_' + key, 'CURVE'); ts = tc_.splines.new('POLY'); ts.points.add(len(pts_) - 1)
        for p_, (x_, y_) in zip(ts.points, pts_): p_.co = (x_, y_, 0, 1)
        tob = bpy.data.objects.new('taper_' + key, tc_); link(tob); tob.hide_render = True; tob.hide_viewport = True
        TAPER[key] = tob
    return TAPER[key]


def tube(name, pts_, radius, taper, bone='head', mat_=None, res=3):
    cu_ = bpy.data.curves.new(name, 'CURVE'); cu_.dimensions = '3D'; cu_.bevel_depth = radius; cu_.bevel_resolution = res
    cu_.use_fill_caps = True; cu_.resolution_u = 6
    sp_ = cu_.splines.new('NURBS'); sp_.points.add(len(pts_) - 1)
    for p_, v in zip(sp_.points, pts_): p_.co = (*v, 1)
    sp_.order_u = 4; sp_.use_endpoint_u = True
    if taper: cu_.taper_object = taper
    ob = bpy.data.objects.new(name, cu_); link(ob); cu_.materials.append(mat_ or M_HAIR)
    return parent_head(ob, bone)


def catmull(ctrl, n):
    """Points along a Catmull-Rom spline through `ctrl` (list of tuples), n samples."""
    c = [ctrl[0]] + list(ctrl) + [ctrl[-1]]; out = []
    segs = len(ctrl) - 1
    for i in range(n):
        t = i / (n - 1) * segs; k = min(int(t), segs - 1); u = t - k
        p0, p1, p2, p3 = (np.array(c[k + j]) for j in range(4))
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    return out


# the waves: from the parting (front to crown) sideways and back to the knot
R_W = 0.0105                   # a wave's tube radius (rig metres)
CAP = 0.006
NW = 9
t_wave = taper_curve('wave', [(0, 0.55), (0.12, 1.0), (0.75, 1.0), (1.0, 0.6)])
for side in (-1, 1):
    for i in range(NW):
        u = i / (NW - 1)
        th0 = hl(0) + 2 + (104 - hl(0) - 2) * u ** 0.9
        front_path = [(1.5, th0), (28, hl(28) + 3.5), (58, hl(58) + 4.5), (88, hl(88) + 6), (122, hl(122) + 9), (152, -2), (172, -4)]
        crown_path = [(1.5, th0), (25, th0 - 12), (60, 62), (100, 40), (135, 20), (158, 6), (174, 0)]
        ctrl = [tuple(np.array(f_) * (1 - u) + np.array(c_) * u) for f_, c_ in zip(front_path, crown_path)]
        ctrl[0] = (1.5, th0)
        path = catmull(ctrl, 46)
        pts_ = []; s_acc = 0.0; prev = None
        raw = [scalp(ph, th, side, 0) for ph, th in path]
        for j, (ph, th) in enumerate(path):
            if j: s_acc += (raw[j] - raw[j - 1]).length
            wave = math.sin(2 * math.pi * s_acc / 0.032 + 0.4 * u)
            d = sdir(ph, th, side)
            tang = (raw[min(j + 1, len(raw) - 1)] - raw[max(j - 1, 0)]).normalized()
            lat = d.cross(tang).normalized()
            off = CAP + R_W * 0.85 + 0.0035 * max(0.0, wave) - 0.002 * u * (j < 3)
            pts_.append(raw[j] + d * off + lat * (0.0045 * wave * side))
        tube(f'wave{side}{i}', pts_, R_W * (1.0 - 0.12 * u), t_wave)

# the knot at the back: a twisted roll of hair
kc = scalp(180, -4, 1, 0); kd = sdir(180, -4, 1)
kx, kz = Vector((1, 0, 0)), kd.cross(Vector((1, 0, 0))).normalized()
for ring, (rx, rz, rad, out_) in enumerate(((0.036, 0.022, 0.015, 0.018), (0.02, 0.012, 0.013, 0.03))):
    pts_ = []
    for j in range(41):
        a_ = 2 * math.pi * j / 40
        pts_.append(kc + kd * (out_ + 0.004 * math.sin(6 * a_)) + kx * rx * math.cos(a_) + kz * rz * math.sin(a_))
    tube(f'knot{ring}', pts_, rad, None)

# curls at the temples, in front of the ears
def corkscrew(start, length, turns, radius, tube_r, name, sway=(0, 0), bone='head', taper=None):
    pts_ = []
    for i in range(61):
        t = i / 60; a_ = turns * 2 * math.pi * t
        rr = radius * (0.6 + 0.4 * t)
        pts_.append(Vector(start) + Vector((rr * math.cos(a_) + sway[0] * t, rr * math.sin(a_) + sway[1] * t, -length * t)))
    return tube(name, pts_, tube_r, taper or taper_curve('lock', [(0, 1), (0.5, 0.9), (1, 0.35)]), bone)


for side in (-1, 1):
    for k, ph in enumerate((70, 82)):
        st_ = scalp(ph, hl(ph) + 2, side, CAP + 0.004)
        corkscrew(st_, 0.034 - 0.006 * k, 2.2, 0.0055, 0.0042, f'temple{side}{k}', (side * 0.004, -0.002))

# long corkscrew locks from behind the ears onto the shoulders
for side in (-1, 1):
    for k, (ph, th, ln_, tw) in enumerate(((112, -16, 0.19, 3.4), (128, -20, 0.20, 3.8), (144, -22, 0.17, 3.2))):
        st_ = scalp(ph, th, side, CAP + 0.006)
        corkscrew(st_, ln_, tw, 0.011, 0.0085, f'lock{side}{k}', (side * 0.016, -0.03 + 0.012 * k), bone='neck03')

# ---------------------------------------------------------------- the ivy wreath on the hair, grapes at the temples
WTH = lambda ph: float(np.interp(ph, (0, 45, 90, 135, 180), (hl(0) + 13, hl(45) + 16, hl(90) + 22, 12, 14)))
W_OFF = CAP + 2 * R_W + 0.009
NL = 15
for side in (-1, 1):
    for i in range(NL + 1):
        if side == -1 and i in (0, NL): continue        # the front and back leaves once
        ph = 180 * i / NL
        pos = scalp(ph, WTH(ph), side, W_OFF); nrm = sdir(ph, WTH(ph), side)
        nxt = scalp(ph + 2, WTH(ph + 2), side, W_OFF); tang = (nxt - pos).normalized()
        bin_ = tang.cross(nrm).normalized(); nrm = bin_.cross(tang).normalized()
        rot = Matrix((tang, nrm, bin_)).transposed() @ Matrix.Rotation(math.radians(25 * (1 if i % 2 else -1)), 3, 'Y')
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.021, segments=16, ring_count=8, location=(0, 0, 0)); lf = bpy.context.active_object
        lf.data.materials.append(M_IVY if (i + (side > 0)) % 2 else M_IVY2); smooth(lf)
        lf.parent = rig; lf.parent_type = 'BONE'; lf.parent_bone = 'head'
        lf.matrix_world = rig.matrix_world @ Matrix.LocRotScale(pos, rot.to_quaternion(), Vector((1.0, 0.33, 0.72)))
        EXTRA.append(lf)
for side in (-1, 1):
    ph = 74
    base_ = scalp(ph, WTH(ph), side, W_OFF + 0.004) + Vector((0, 0, -0.012))
    for (gx, gz) in ((0, 0), (-.009, -.011), (.009, -.011), (0, -.022), (-.006, -.031), (.006, -.031), (0, -.04)):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0095, segments=12, ring_count=8, location=(0, 0, 0)); g_ = bpy.context.active_object
        g_.data.materials.append(M_GRAPE); smooth(g_)
        g_.parent = rig; g_.parent_type = 'BONE'; g_.parent_bone = 'head'
        g_.matrix_world = rig.matrix_world @ Matrix.Translation(base_ + Vector((gx * 0.6, -abs(gx) * 0.6 - 0.002, gz)))
        EXTRA.append(g_)

# ---------------------------------------------------------------- the himation: a rolled drape over his left shoulder
# It runs from behind his left shoulder, over it, and down across his chest to the right hip (below the
# counter, where it would wrap his hips). It follows the body's surface and is parented to the chest.
# It is built as a curve with a flattened, folded cross-section, then made a mesh whose 'edge' attribute
# (0 along the middle, 1 at both long edges) gives the cloth its green and gold hem.
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
    sp = surface(x, z, 0.018 + 0.01 * math.sin(math.pi * t))
    if sp is not None: front.append(sp)
print('[himation] front points', len(front))
pts = back + over + front
cu = bpy.data.curves.new('himation_c', 'CURVE'); cu.dimensions = '3D'
cu.bevel_mode = 'OBJECT'
prof = bpy.data.curves.new('him_prof', 'CURVE'); ps = prof.splines.new('BEZIER'); ps.bezier_points.add(7)
for i, bp in enumerate(ps.bezier_points):   # a flattened, folded cross-section
    a_ = 2 * math.pi * i / 8; rr = 1 + 0.18 * math.cos(3 * a_)
    bp.co = (0.075 * rr * math.cos(a_), 0.022 * rr * math.sin(a_), 0); bp.handle_left_type = bp.handle_right_type = 'AUTO'
ps.use_cyclic_u = True; prof.resolution_u = 8
pob = bpy.data.objects.new('him_prof', prof); link(pob); pob.hide_render = True
cu.bevel_object = pob; cu.use_fill_caps = True
sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1)
for i, (p_, v) in enumerate(zip(sp.points, pts)):
    p_.co = (*v, 1); p_.tilt = 0.6 * math.sin(i * 0.9)
sp.order_u = 4; sp.use_endpoint_u = True; cu.resolution_u = 12; cu.twist_mode = 'MINIMUM'
him_c = bpy.data.objects.new('himation_c', cu); link(him_c)
him_c.matrix_world = Matrix.Identity(4)
bpy.context.view_layer.update()
dg_ = bpy.context.evaluated_depsgraph_get()
hm = bpy.data.meshes.new_from_object(him_c.evaluated_get(dg_))
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

# ---------------------------------------------------------------- arms: IK to animated targets
def empty(name):
    e = bpy.data.objects.new(name, None); link(e); return e


IKT = {s: empty('ik_' + s) for s in 'LR'}
POLE = {s: empty('pole_' + s) for s in 'LR'}
for s in 'LR':
    c = PB['lowerarm02.' + s].constraints.new('IK'); c.target = IKT[s]; c.chain_count = 4
    c.pole_target = POLE[s]; c.pole_angle = math.radians(-90)
    PB['wrist.' + s].rotation_mode = 'XYZ'
for b in PB: b.rotation_mode = 'XYZ'


def grip(side, amount):
    """Curl the fingers; 0 open, 1 a firm grip."""
    for f in range(1, 6):
        for j in (1, 2, 3):
            nme = f'finger{f}-{j}.{side}'
            if nme in PB:
                k = (0.55 if f == 1 else 1.0) * amount
                PB[nme].rotation_euler = (math.radians(55 * k if j > 1 or f > 1 else 20 * k), 0, 0)


def wpt(x, y, d):    # a world point from world units and depth (Blender units)
    return P(x, y, d)


# shoulders in world, for sensible pole placement
def place_poles():
    for s, sx in (('L', 1), ('R', -1)):
        sh = rig.matrix_world @ rig.data.bones['upperarm01.' + s].head_local
        POLE[s].location = sh + Vector((sx * 2.2, 3.0, -2.0))    # elbows out and back


def world_units(pt):
    """World (Blender) point -> B's world units (x, y) as the camera sees it."""
    from bpy_extras.object_utils import world_to_camera_view
    r.resolution_x, r.resolution_y = G['FW'], G['FH']
    co = world_to_camera_view(scene, cam, pt)
    return G['FRAME'][0] + co.x * G['FW'], G['FRAME'][1] + (1 - co.y) * G['FH']


def head_rect():
    """World rect of his head (hair, face, wreath), for the speech bubble."""
    x0, y0, x1, y1 = bbox_world([cap], 0)
    return [round(x0), round(y0), round(x1 - x0), round((y1 - y0) * 1.25)]


# ---------------------------------------------------------------- props (rendered with him)
M_GLASS = mat('dio_glass', '#e9e4da', 0.08, coat=1.0)
M_CLOTH = mat('fawn', '#b98552', 0.8)
M_WOOD = mat('thyrsus_wood', '#7a5530', 0.55)
M_CONE = mat('pinecone', '#5b7a2e', 0.6)
M_STEEL = mat('shaker', '#c9a24a', 0.22, 1.0)
M_BOTTLE = mat('dio_bottle', '#b8661c', 0.3, coat=0.3)
M_LABEL = mat('dio_label', '#f1e6cf', 0.7)


def prop_glass():
    g_ = lathe('p_glass', [(0, 0), (0, 0.2), (0.02, 0.22), (0.48, 0.23), (0.5, 0.215), (0.04, 0.19)], M_GLASS, 32)
    return [g_]


def prop_cloth():
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, segments=16, ring_count=8); c = bpy.context.active_object
    c.scale = (1.0, 0.7, 0.55); c.data.materials.append(M_CLOTH); smooth(c)
    d = c.modifiers.new('d', 'DISPLACE'); t = bpy.data.textures.new('crumple', 'CLOUDS'); t.noise_scale = 0.05; d.texture = t; d.strength = 0.03
    return [c]


def prop_thyrsus():
    st = lathe('p_staff', [(-1.5, 0.022), (1.35, 0.022)], M_WOOD, 16)
    cone = lathe('p_cone', [(1.3, 0.0), (1.33, 0.07), (1.45, 0.095), (1.58, 0.07), (1.66, 0.02), (1.68, 0)], M_CONE, 24)
    cone.parent = st
    for i in range(4):   # ribbons of ivy under the cone
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, segments=12, ring_count=6, location=(0.05 * math.cos(i * 1.6), 0.05 * math.sin(i * 1.6), 1.26 - i * 0.03))
        lf = bpy.context.active_object; lf.scale = (1, 0.35, 0.7); lf.data.materials.append(M_IVY); smooth(lf); lf.parent = st
    return [st, cone] + [o for o in bpy.data.objects if o.parent == st and o not in (cone,)]


def prop_bottle():
    b_ = lathe('p_bottle', [(0, 0), (0, 0.2), (0.03, 0.24), (0.52, 0.24), (0.64, 0.15), (0.72, 0.07), (0.96, 0.07), (0.97, 0)], M_BOTTLE, 32)
    lb = lathe('p_label', [(0.2, 0.243), (0.42, 0.243)], M_LABEL, 32); lb.parent = b_
    return [b_, lb]


def prop_shaker():
    s_ = lathe('p_shaker', [(0, 0), (0, 0.16), (0.04, 0.17), (0.5, 0.22), (0.52, 0.2), (0.62, 0.18), (0.66, 0.12), (0.72, 0.1), (0.74, 0)], M_STEEL, 32)
    return [s_]


def hand_frame(side):
    """World matrix of the palm: origin at the palm, Y along the fingers, Z out of the palm."""
    pb = rig.pose.bones; m = rig.matrix_world
    wr = m @ pb['wrist.' + side].head
    k2, k5 = m @ pb['finger2-1.' + side].head, m @ pb['finger5-1.' + side].head
    k3 = m @ pb['finger3-1.' + side].head
    yv = (k3 - wr).normalized(); xv = (k2 - k5).normalized()
    zv = yv.cross(xv).normalized() * (1 if side == 'R' else -1)
    xv = zv.cross(yv).normalized()
    o = wr.lerp(k3, 0.55) + zv * 0.022 * S
    M = Matrix((xv, yv, zv)).transposed().to_4x4(); M.translation = o
    return M


def attach(objs, side, local):
    """Put a prop in the hand: `local` is its matrix in the palm frame (rig-scale units), parented to the wrist."""
    bpy.context.view_layer.update()
    M = hand_frame(side) @ local          # props are modelled in world (Blender) units
    root = objs[0]
    root.parent = rig; root.parent_type = 'BONE'; root.parent_bone = 'wrist.' + side
    bpy.context.view_layer.update()
    root.matrix_world = M
    return objs


# ---------------------------------------------------------------- loops
CX = 800
COUNTER = G['MAN']['counterBackY'] if 'MAN' in G else 631


def rest_pose():
    for b in PB:
        b.rotation_euler = (0, 0, 0); b.location = (0, 0, 0)
    place_poles()


def set_hands(L, R):
    IKT['L'].location = wpt(*L); IKT['R'].location = wpt(*R)


def look(yaw=0, pitch=0, roll=0):
    PB['head'].rotation_euler = (math.radians(pitch), math.radians(roll), math.radians(yaw))
    PB['neck02'].rotation_euler = (math.radians(pitch * 0.4), 0, math.radians(yaw * 0.4))


def ease(t): return 0.5 - 0.5 * math.cos(math.pi * t)


DH = -1.2   # hand depth: over the counter, well in front of his chest (about -0.6)


def L_polish(t):   # glass in the left hand, the fawn-skin cloth circling inside it
    a = 2 * math.pi * t
    set_hands((CX + 40, 585, DH), (CX - 10 + 16 * math.cos(a), 560 + 12 * math.sin(a), DH - 0.15))
    look(6 * math.sin(a * 0.5), 14, 0)
    grip('L', 0.7); grip('R', 0.55)


def L_stir(t):     # the thyrsus as a bar spoon: small circles in the glass on the counter
    a = 2 * math.pi * t
    set_hands((CX + 95, 615, DH + 0.2), (CX - 30 + 8 * math.cos(a), 545 + 4 * math.sin(a), DH))
    look(-4, 16, 0); grip('L', 0.25); grip('R', 0.9)


def L_pour(t):     # lift the bottle, tip it over the glass, hold the pour
    up = ease(min(1, t / 0.4)); tip = ease(max(0, min(1, (t - 0.35) / 0.4)))
    set_hands((CX + 90, 615, DH + 0.2), (CX - 95 + 25 * up, 600 - 60 * up, DH))
    look(-6, 14, 0); grip('L', 0.25); grip('R', 0.95)


def L_shake(t):    # shaker held in both hands at the shoulder, shaking hard
    k = math.sin(2 * math.pi * t * 2)
    c = (CX - 85, 500 + 18 * k, DH + 0.15)
    set_hands((c[0] + 8, c[1] - 62, c[2] - 0.05), (c[0], c[1], c[2]))
    look(-10, 4, 5 * k); grip('L', 0.8); grip('R', 0.9)


def L_reach(t):    # reaches up to the shelf, brings something down, holds it out
    up = ease(min(1, t / 0.45)); down = ease(max(0, min(1, (t - 0.55) / 0.4)))
    hx = CX - 60 - 60 * up + 50 * down; hy = 610 - 250 * up + 230 * down
    set_hands((CX + 90, 615, DH + 0.2), (hx, hy, DH + 0.9 * up * (1 - down)))
    look(-18 * up * (1 - down), -20 * up * (1 - down) + 10 * down, 0); grip('L', 0.25); grip('R', 0.3 + 0.6 * down)


def L_story(t):    # an open-handed gesture, head tilting as he talks
    a = 2 * math.pi * t
    set_hands((CX + 90, 610, DH + 0.2), (CX - 110 + 14 * math.sin(a), 560 + 16 * math.sin(a * 2), DH))
    look(10 * math.sin(a), 4, 5 * math.sin(a)); grip('L', 0.25); grip('R', 0.1)
    PB['wrist.R'].rotation_euler = (math.radians(-30), 0, math.radians(20))


LOOPS = {   # name: (pose function, frames, fps, hold frame, props)
    'polish': (L_polish, 14, 10, 0, 'polish'),
    'stir': (L_stir, 12, 12, 0, 'stir'),
    'pour': (L_pour, 14, 10, 9, 'pour'),
    'shake': (L_shake, 12, 14, 0, 'shake'),
    'reach': (L_reach, 14, 10, 11, 'reach'),
    'story': (L_story, 14, 8, 0, 'story'),
}
RECT = (560, 290, 1040, 640)     # world rect of every frame (the counter clips him below ~631 in the app)
K = 1.5                          # pixels per world unit


def props_for(kind):
    out = []
    if kind == 'polish':
        out += attach(prop_glass(), 'L', Matrix.LocRotScale(Vector((0, 0.02, 0.06)), Euler((math.radians(-90), 0, 0)), Vector((1, 1, 1))))
        out += attach(prop_cloth(), 'R', Matrix.Translation(Vector((0, 0.02, 0.02))))
    elif kind == 'stir':
        out += prop_thyrsus()
    elif kind == 'pour':
        out += prop_bottle(); out[0].scale = (1.4, 1.4, 1.4)
    elif kind == 'shake':
        out += prop_shaker(); out[0].scale = (1.6, 1.6, 1.6)
    return out


HELD = {}   # props placed in world space every frame: name -> function(props) using the current pose


def axis_matrix(origin, axis):
    z = Vector(axis).normalized(); x = Vector((0, 1, 0)).cross(z)
    if x.length < 1e-4: x = Vector((1, 0, 0))
    x.normalize(); y = z.cross(x)
    M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = origin; return M


def place_held(kind, t, props):
    if not props: return
    bpy.context.view_layer.update()
    root = props[0]; sc = root.scale.copy()
    palm = hand_frame('R').translation
    if kind == 'stir':
        a = 2 * math.pi * t
        tip = wpt(CX + 6 * math.cos(a), 625, -1.05 + 0.03 * math.sin(a))
        hold_staff('R', tip, root)                       # the staff runs from the glass up through his fist
    elif kind == 'pour':
        tip = ease(max(0, min(1, (t - 0.35) / 0.4)))
        ang = math.radians(115 * tip)
        axis = Vector((math.sin(ang), 0, math.cos(ang)))
        root.matrix_world = axis_matrix(palm - axis * 0.55, axis) @ Matrix.Diagonal((*sc, 1))
    elif kind == 'shake':
        axis = Vector((-0.35, -0.15, 1.0))
        root.matrix_world = axis_matrix(palm - axis.normalized() * 0.5, axis) @ Matrix.Diagonal((*sc, 1))


def fist_point(side):
    """World point in the middle of the closed fist: the centre of the loop each curled finger makes
    (knuckle, middle joints, fingertip), for the index to little fingers."""
    m = rig.matrix_world; pb = rig.pose.bones; pts = []
    for f in (2, 3, 4, 5):
        pts += [m @ pb[f'finger{f}-1.{side}'].head, m @ pb[f'finger{f}-2.{side}'].head,
                m @ pb[f'finger{f}-3.{side}'].head, m @ pb[f'finger{f}-3.{side}'].tail]
    return sum(pts, Vector()) / len(pts)


def fist_axis(side):
    """World direction through the fist, from the little finger's side to the index finger's."""
    m = rig.matrix_world; pb = rig.pose.bones
    return (m @ pb[f'finger2-1.{side}'].head - m @ pb[f'finger5-1.{side}'].head).normalized()


def hold_staff(side, tip, root, turns=4):
    """Turn the wrist so the fist's axis lines up with the staff, then run the staff from `tip` (its lower
    end's aim, e.g. in the glass) up through the middle of the fist. Any pose holding the thyrsus uses this."""
    m = rig.matrix_world; wb = rig.pose.bones['wrist.' + side]
    for _ in range(turns):
        bpy.context.view_layer.update()
        up = (fist_point(side) - tip).normalized()
        q = fist_axis(side).rotation_difference(up)
        piv = m @ wb.head
        Rw = Matrix.Translation(piv) @ q.to_matrix().to_4x4() @ Matrix.Translation(-piv)
        wb.matrix = m.inverted() @ Rw @ m @ wb.matrix
    bpy.context.view_layer.update()
    g = fist_point(side)
    root.matrix_world = axis_matrix(g, (g - tip).normalized())
    bpy.context.view_layer.update()
    print(f'[grip] fist axis vs staff: {math.degrees(fist_axis(side).angle((g - tip).normalized())):.1f} deg', flush=True)


def clear_props():
    for o in [o for o in bpy.data.objects if o.name.startswith('p_')]:
        bpy.data.objects.remove(o, do_unlink=True)


scene.view_settings.exposure = -1.1   # his marble is pale: keep it from blowing out under the bar's warm key


def render_loop(name):
    fn, nf, fps, hold, kind = LOOPS[name]
    clear_props(); rest_pose(); fn(0.0); bpy.context.view_layer.update()
    props = props_for(kind) if kind else []
    allp = [o for o in bpy.data.objects if o.name.startswith('p_')]
    vis = [body] + EXTRA + allp
    if STILL: frames = [int(STILL_FRAME) if STILL_FRAME is not None else nf // 2]
    else: frames = [nf // 2] if PREVIEW else list(range(nf))
    rel = os.path.relpath(OUT, PROTO).replace(os.sep, '/')
    if not (PREVIEW or STILL): os.makedirs(os.path.join(OUT, name), exist_ok=True)
    out = []; times = []
    from PIL import Image
    for f in frames:
        rest_pose(); fn(f / nf); bpy.context.view_layer.update()
        place_held(kind, f / nf, props if kind in ('stir', 'pour', 'shake') else None)
        region, k = RECT, K * (1.3 if PREVIEW else 1)
        if STILL:
            k = K * STILL_SCALE
            if STILL_CROP == 'head':
                region = bbox_world([o for o in EXTRA if o.type == 'CURVE' or o.name == 'haircap'] + [o for o in EXTRA if o.parent_bone == 'head'], 14)
            elif STILL_CROP == 'grip':
                gx, gy = world_units(fist_point('R')); region = (gx - 70, gy - 60, gx + 70, gy + 60)
        t0 = time.time()
        png = render_region(f'dio_{name}_{f:02d}', region, k, vis, True, 24)
        times.append(time.time() - t0)
        im = Image.open(png).convert('RGBA')
        if PREVIEW or STILL:
            bg = Image.new('RGBA', im.size, (40, 30, 26, 255)); bg.alpha_composite(im)
            if STILL:
                d_ = STILL_OUT or WORK; os.makedirs(d_, exist_ok=True)
                bg.save(os.path.join(d_, f'still_{FINISH}_{name}_{f:02d}_{STILL_CROP}.png'))
            else:
                bg.save(os.path.join(WORK, f'preview_{name}.png' if FINISH == 'painted' else f'preview_{name}_{FINISH}.png'))
            continue
        p = os.path.join(OUT, name, f'{f + 1:04d}.webp'); im.save(p, 'WEBP', quality=68, method=6)
        out.append(f'{rel}/{name}/{f + 1:04d}.webp')
    return {'frames': out, 'fps': fps, 'hold': hold, 'secondsPerFrame': round(sum(times) / len(times), 1)} if out else None


if __name__ == 'build_dionysus' or True:
    names = [STILL] if STILL else [ONLY_LOOP] if ONLY_LOOP else list(LOOPS)
    man_p = os.path.join(PROTO, 'dio-loops.json' if FINISH == 'painted' else f'dio-loops-{FINISH}.json')
    man = json.load(open(man_p)) if os.path.exists(man_p) and not PREVIEW else {'loops': {}}
    for nm in names:
        res = render_loop(nm)
        if res: man['loops'][nm] = res
        print('[loop]', nm, res and res['secondsPerFrame'], flush=True)
    if not (PREVIEW or STILL):
        rest_pose(); L_polish(0); bpy.context.view_layer.update()
        man['rect'] = [RECT[0], RECT[1], RECT[2] - RECT[0], RECT[3] - RECT[1]]
        man['head'] = head_rect()
        man['finish'] = FINISH
        man['about'] = (f'Dionysus, MakeHuman (MPFB2) base, finish {FINISH}, rendered by blender/build_dionysus.py. '
                        'rect and head are in world units (prototype B\'s SVG space).')
        man['render'] = {'engine': 'Cycles (CPU)', 'samples': 24, 'denoiser': 'OpenImageDenoise', 'pxPerWorldUnit': K}
        json.dump(man, open(man_p, 'w'), indent=1)
