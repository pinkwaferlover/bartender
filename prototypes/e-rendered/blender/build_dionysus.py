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
import numpy as np
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.dirname(HERE)
ARGS = sys.argv[1:]
PREVIEW = '--preview' in ARGS
ONLY_LOOP = ARGS[ARGS.index('--only') + 1] if '--only' in ARGS else None

# ---------------------------------------------------------------- the bar's scene, camera and lights
src = open(os.path.join(HERE, 'build_bar.py'), encoding='utf8').read()
src = src[:src.index('MANIFEST_PATH = ')]          # everything up to where build_bar writes its outputs
sys.argv = [os.path.join(HERE, 'build_bar.py'), '--only', 'none']
G = {'__file__': os.path.join(HERE, 'build_bar.py'), '__name__': 'build_bar'}
exec(compile(src, 'build_bar.py', 'exec'), G)
scene, cam, P, push, render_region, bbox_world = G['scene'], G['cam'], G['P'], G['push'], G['render_region'], G['bbox_world']
srgb, smooth, mat, link, lathe, WORK = G['srgb'], G['smooth'], G['mat'], G['link'], G['lathe'], G['WORK']
r = scene.render; cy = scene.cycles
OUT = os.path.join(PROTO, 'img', 'dio')

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


# ---------------------------------------------------------------- materials: painted marble (Q8 default)
def marble_material():
    m = bpy.data.materials.new('marble'); m.use_nodes = True
    nt = m.node_tree; n = nt.nodes; L = nt.links
    b = n['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.38
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
    base = n.new('ShaderNodeMix'); base.data_type = 'RGBA'
    base.inputs['A'].default_value = srgb('#b9b3ab'); base.inputs['B'].default_value = srgb('#efe8de')
    L.new(vr.outputs['Result'], base.inputs['Factor'])
    # paint: lips and cheeks, from the body's 'paint' colour attribute (alpha = how much paint)
    attr = n.new('ShaderNodeAttribute'); attr.attribute_name = 'paint'
    paint = n.new('ShaderNodeMix'); paint.data_type = 'RGBA'
    L.new(attr.outputs['Alpha'], paint.inputs['Factor']); L.new(base.outputs['Result'], paint.inputs['A']); L.new(attr.outputs['Color'], paint.inputs['B'])
    L.new(paint.outputs['Result'], b.inputs['Base Color'])
    return m


M_MARBLE = marble_material()
M_HAIR = mat('hair_marble', '#d8cfc2', 0.5)       # hair carved in marble, a touch warmer and rougher
M_IVY = mat('ivy_painted', '#3f7a34', 0.45)
M_IVY2 = mat('ivy_painted2', '#2f6428', 0.45)
M_GRAPE = mat('grape_painted', '#5b2a6b', 0.3, coat=0.5)


def himation_material():
    m = bpy.data.materials.new('himation'); m.use_nodes = True
    nt = m.node_tree; n = nt.nodes; L = nt.links
    b = n['Principled BSDF']; b.inputs['Roughness'].default_value = 0.6
    b.inputs['Sheen Weight'].default_value = 0.5
    attr = n.new('ShaderNodeAttribute'); attr.attribute_name = 'edge'
    ramp = n.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].position = 0.0; cr.elements[0].color = srgb('#8e2a22')
    cr.elements[1].position = 0.8; cr.elements[1].color = srgb('#8e2a22')
    e = cr.elements.new(0.83); e.color = srgb('#2f5a32')
    e = cr.elements.new(0.9); e.color = srgb('#2f5a32')
    e = cr.elements.new(0.92); e.color = srgb('#d8b25a')
    e = cr.elements.new(1.0); e.color = srgb('#d8b25a')
    L.new(attr.outputs['Fac'], ramp.inputs['Fac']); L.new(ramp.outputs['Color'], b.inputs['Base Color'])
    return m


M_HIMATION = mat('himation_red', '#8e2a22', 0.62)
M_HIMATION.node_tree.nodes['Principled BSDF'].inputs['Sheen Weight'].default_value = 0.6
body.data.materials.clear(); body.data.materials.append(M_MARBLE)
for p in body.data.polygons: p.use_smooth = True
sub = body.modifiers.new('subd', 'SUBSURF'); sub.levels = 1; sub.render_levels = 1

# ---------------------------------------------------------------- paint on the face: lips and cheeks
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

# eyes: marble eyeballs with a painted iris (ancient statues were painted)
def eye_material():
    m = bpy.data.materials.new('eye_painted'); m.use_nodes = True; nt = m.node_tree; n = nt.nodes; L = nt.links
    b = n['Principled BSDF']; b.inputs['Roughness'].default_value = 0.25; b.inputs['Coat Weight'].default_value = 0.6
    tc = n.new('ShaderNodeTexCoord'); sep = n.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])
    comb = n.new('ShaderNodeCombineXYZ'); L.new(sep.outputs['X'], comb.inputs['X']); L.new(sep.outputs['Z'], comb.inputs['Y'])
    ln = n.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; L.new(comb.outputs[0], ln.inputs[0])
    nrm_ = n.new('ShaderNodeMath'); nrm_.operation = 'DIVIDE'; nrm_.inputs[1].default_value = 0.0118
    L.new(ln.outputs['Value'], nrm_.inputs[0])
    front = n.new('ShaderNodeMath'); front.operation = 'LESS_THAN'; front.inputs[1].default_value = 0.0; L.new(sep.outputs['Y'], front.inputs[0])
    ramp = n.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].position = 0.0; cr.elements[0].color = srgb('#1c1410')
    e = cr.elements.new(0.22); e.color = srgb('#1c1410')
    e = cr.elements.new(0.27); e.color = srgb('#6b4c33')
    e = cr.elements.new(0.48); e.color = srgb('#6b4c33')
    cr.elements[-1].position = 0.53; cr.elements[-1].color = srgb('#efe8de')
    L.new(nrm_.outputs[0], ramp.inputs['Fac'])
    mix = n.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.inputs['A'].default_value = srgb('#efe8de')
    L.new(front.outputs[0], mix.inputs['Factor']); L.new(ramp.outputs['Color'], mix.inputs['B'])
    L.new(mix.outputs['Result'], b.inputs['Base Color'])
    return m


M_EYE = eye_material()
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

# ---------------------------------------------------------------- hair: a wavy cap and long corkscrew locks
hb = rig.data.bones['head']; head_c = (hb.head_local + hb.tail_local) / 2
brow_z = max(eyeL[2], eyeR[2]) + 0.022
head_w = [i for i, g in enumerate(body.vertex_groups) if g.name == 'head']
gi = head_w[0]
w_head = np.zeros(len(V))
for v in body.data.vertices:
    for g in v.groups:
        if g.group == gi: w_head[v.index] = g.weight
face_front = (V[:, 1] < head_c[1] - 0.02) & (V[:, 2] < brow_z)
hairsel = (w_head > 0.5) & ~face_front & (V[:, 2] > eyeL[2] - 0.04)
hairsel &= ~((np.abs(V[:, 0]) > 0.062) & (V[:, 2] < brow_z - 0.0) & (V[:, 1] < head_c[1] + 0.03))   # keep ears visible a little
bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
keep = set(np.nonzero(hairsel)[0].tolist())
for f in [f for f in bm.faces if not all(v.index in keep for v in f.verts)]:
    bm.faces.remove(f)
for v in [v for v in bm.verts if not v.link_faces]:
    bm.verts.remove(v)
hme = bpy.data.meshes.new('haircap'); bm.to_mesh(hme); bm.free()
for a_ in list(hme.attributes):
    if a_.name == 'paint': hme.attributes.remove(a_)
cap = bpy.data.objects.new('haircap', hme); link(cap); cap.data.materials.append(M_HAIR)
for p in cap.data.polygons: p.use_smooth = True
cap.parent = rig; cap.parent_type = 'BONE'; cap.parent_bone = 'head'
cap.matrix_world = rig.matrix_world.copy()
sol = cap.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.012; sol.offset = 1.0
sd = cap.modifiers.new('sub', 'SUBSURF'); sd.levels = 2; sd.render_levels = 2
tex = bpy.data.textures.new('waves', 'MARBLE'); tex.marble_type = 'SHARPER'; tex.noise_scale = 0.03; tex.turbulence = 4.0; tex.noise_depth = 2
dp = cap.modifiers.new('waves', 'DISPLACE'); dp.texture = tex; dp.strength = 0.006; dp.mid_level = 0.3
EXTRA.append(cap)


def lock(start, length, turns, radius, tube, name, sway=(0, 0)):
    """A corkscrew curl hanging from `start` (rig space)."""
    pts = []
    n = 60
    for i in range(n + 1):
        t = i / n; a = turns * 2 * math.pi * t
        rr = radius * (0.6 + 0.4 * t)
        pts.append(Vector(start) + Vector((rr * math.cos(a) + sway[0] * t, rr * math.sin(a) + sway[1] * t, -length * t)))
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = tube; cu.bevel_resolution = 3
    sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1)
    for p_, v in zip(sp.points, pts): p_.co = (*v, 1)
    sp.order_u = 4; sp.use_endpoint_u = True
    taper = bpy.data.curves.new(name + '_t', 'CURVE'); ts = taper.splines.new('POLY'); ts.points.add(2)
    ts.points[0].co = (0, 1, 0, 1); ts.points[1].co = (0.5, 0.9, 0, 1); ts.points[2].co = (1, 0.35, 0, 1)
    tob = bpy.data.objects.new(name + '_t', taper); link(tob); tob.hide_render = True
    cu.taper_object = tob
    ob = bpy.data.objects.new(name, cu); link(ob); cu.materials.append(M_HAIR)
    ob.parent = rig; ob.parent_type = 'BONE'; ob.parent_bone = 'neck03'
    ob.matrix_world = rig.matrix_world.copy()
    EXTRA.append(ob)
    return ob


hr = 0.085   # about the head's half width
for side in (-1, 1):
    for k, (dy, ln_, tw) in enumerate(((0.0, 0.17, 3.2), (0.025, 0.19, 3.6), (0.05, 0.15, 3.0))):
        lock((side * (hr - 0.004 + 0.004 * k), head_c[1] + dy - 0.005, eyeL[2] - 0.01), ln_, tw, 0.011, 0.0085, f'lock{side}{k}', (side * 0.012, 0.01 + 0.012 * k))

# ---------------------------------------------------------------- the ivy wreath with grapes at the temples
wz = brow_z + 0.018
for i in range(26):
    a = math.pi * 2 * i / 26
    if abs(math.sin(a)) > 0.98 and math.cos(a) < 0: pass
    x, y = math.cos(a) * 0.103, head_c[1] + 0.004 + math.sin(a) * 0.112
    zz = wz + 0.012 * math.sin(a) + 0.006 * (i % 2)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.022, segments=16, ring_count=8, location=(0, 0, 0)); lf = bpy.context.active_object
    lf.data.materials.append(M_IVY if i % 2 else M_IVY2); smooth(lf)
    lf.scale = (1.0, 0.35, 0.75)
    lf.rotation_euler = (math.radians(15 * (1 if i % 2 else -1)), 0, a + math.pi / 2)
    lf.parent = rig; lf.parent_type = 'BONE'; lf.parent_bone = 'head'
    lf.matrix_world = rig.matrix_world @ Matrix.LocRotScale(Vector((x, y, zz)), lf.rotation_euler, lf.scale)
    EXTRA.append(lf)
for side in (-1, 1):
    base_ = Vector((side * 0.094, head_c[1] - 0.045, wz - 0.016))
    for (gx, gz) in ((0, 0), (-.009, -.011), (.009, -.011), (0, -.022), (-.006, -.031), (.006, -.031), (0, -.04)):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0095, segments=12, ring_count=8, location=(0, 0, 0)); g_ = bpy.context.active_object
        g_.data.materials.append(M_GRAPE); smooth(g_)
        g_.parent = rig; g_.parent_type = 'BONE'; g_.parent_bone = 'head'
        g_.matrix_world = rig.matrix_world @ Matrix.Translation(base_ + Vector((gx * side * 0.3, -abs(gx) * 0.8 - 0.004, gz)))
        EXTRA.append(g_)

# ---------------------------------------------------------------- the himation: a rolled drape over his left shoulder
# It runs from behind his left shoulder, over it, and down across his chest to the right hip (below the
# counter, where it would wrap his hips). It follows the body's surface and is parented to the chest.
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
from mathutils.bvhtree import BVHTree
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
cu = bpy.data.curves.new('himation', 'CURVE'); cu.dimensions = '3D'
cu.bevel_mode = 'OBJECT'
prof = bpy.data.curves.new('him_prof', 'CURVE'); ps = prof.splines.new('BEZIER'); ps.bezier_points.add(7)
for i, bp in enumerate(ps.bezier_points):   # a flattened, folded cross-section
    a_ = 2 * math.pi * i / 8; rr = 1 + 0.18 * math.cos(3 * a_)
    bp.co = (0.075 * rr * math.cos(a_), 0.022 * rr * math.sin(a_), 0); bp.handle_left_type = bp.handle_right_type = 'AUTO'
ps.use_cyclic_u = True
pob = bpy.data.objects.new('him_prof', prof); link(pob); pob.hide_render = True
cu.bevel_object = pob; cu.use_fill_caps = True
sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1)
for i, (p_, v) in enumerate(zip(sp.points, pts)):
    p_.co = (*v, 1); p_.tilt = 0.6 * math.sin(i * 0.9)
sp.order_u = 4; sp.use_endpoint_u = True; cu.resolution_u = 12; cu.twist_mode = 'MINIMUM'
him = bpy.data.objects.new('himation', cu); link(him); cu.materials.append(M_HIMATION)
him.parent = rig; him.parent_type = 'BONE'; him.parent_bone = 'spine02'
him.matrix_world = rig.matrix_world.copy()
EXTRA.append(him)

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
        axis = (palm - tip).normalized()
        root.matrix_world = axis_matrix(palm, axis)      # the staff runs from the glass up through his hand
    elif kind == 'pour':
        tip = ease(max(0, min(1, (t - 0.35) / 0.4)))
        ang = math.radians(115 * tip)
        axis = Vector((math.sin(ang), 0, math.cos(ang)))
        root.matrix_world = axis_matrix(palm - axis * 0.55, axis) @ Matrix.Diagonal((*sc, 1))
    elif kind == 'shake':
        axis = Vector((-0.35, -0.15, 1.0))
        root.matrix_world = axis_matrix(palm - axis.normalized() * 0.5, axis) @ Matrix.Diagonal((*sc, 1))


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
    frames = [nf // 2] if PREVIEW else list(range(nf))
    os.makedirs(os.path.join(OUT, name), exist_ok=True)
    out = []; times = []
    for f in frames:
        rest_pose(); fn(f / nf); bpy.context.view_layer.update()
        place_held(kind, f / nf, props if kind in ('stir', 'pour', 'shake') else None)
        t0 = time.time()
        png = render_region(f'dio_{name}_{f:02d}', RECT, K * (1.3 if PREVIEW else 1), vis, True, 24)
        times.append(time.time() - t0)
        from PIL import Image
        im = Image.open(png).convert('RGBA')
        if PREVIEW:
            bg = Image.new('RGBA', im.size, (40, 30, 26, 255)); bg.alpha_composite(im); bg.save(os.path.join(WORK, f'preview_{name}.png'))
            continue
        p = os.path.join(OUT, name, f'{f + 1:04d}.webp'); im.save(p, 'WEBP', quality=68, method=6)
        out.append(f'img/dio/{name}/{f + 1:04d}.webp')
    return {'frames': out, 'fps': fps, 'hold': hold, 'secondsPerFrame': round(sum(times) / len(times), 1)} if out else None


if __name__ == 'build_dionysus' or True:
    names = [ONLY_LOOP] if ONLY_LOOP else list(LOOPS)
    man_p = os.path.join(PROTO, 'dio-loops.json')
    man = json.load(open(man_p)) if os.path.exists(man_p) and not PREVIEW else {'loops': {}}
    for nm in names:
        res = render_loop(nm)
        if res: man['loops'][nm] = res
        print('[loop]', nm, res and res['secondsPerFrame'], flush=True)
    if not PREVIEW:
        rest_pose(); L_polish(0); bpy.context.view_layer.update()
        man['rect'] = [RECT[0], RECT[1], RECT[2] - RECT[0], RECT[3] - RECT[1]]
        man['head'] = head_rect()
        man['about'] = ('Dionysus, MakeHuman (MPFB2) base in painted marble, rendered by blender/build_dionysus.py. '
                        'rect and head are in world units (prototype B\'s SVG space).')
        man['render'] = {'engine': 'Cycles (CPU)', 'samples': 24, 'denoiser': 'OpenImageDenoise', 'pxPerWorldUnit': K}
        json.dump(man, open(man_p, 'w'), indent=1)
