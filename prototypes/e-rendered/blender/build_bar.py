"""Dionysus bar, prototype E: the bar scene built and rendered headless with Blender (bpy).

Run from the repository root:
    python3.13 -m venv .venv-blender && .venv-blender/bin/pip install bpy==5.3.0 pillow
    .venv-blender/bin/python prototypes/e-rendered/blender/build_bar.py            # full render
    .venv-blender/bin/python prototypes/e-rendered/blender/build_bar.py --quick    # fast preview
    .venv-blender/bin/python prototypes/e-rendered/blender/build_bar.py --only bg  # bg | bottles | touch

It writes WebP layers to prototypes/e-rendered/img/ and a manifest, prototypes/e-rendered/layers.js.

How the picture lines up with the app
-------------------------------------
Prototype B's scene is an SVG whose camera is the viewBox, in "world units" (the bar is about 1600 wide,
the counter top at y=658, Dionysus stands at x=800). This scene keeps those coordinates.
One perspective camera, level and front-on (so verticals stay vertical, like B's poster), sees the
rectangle x 0..1600, y -240..1360 of the reference plane (depth 0, where Dionysus stands), at 100 world
units per Blender unit. Every object is modelled on that reference plane in world units and then pushed
back or forward along the camera's rays (`push`), so it keeps its place in the picture but gains real
depth, perspective on the counter top, and real light and shadow.
Each close-up "camera position" is the same camera rendered at a higher resolution with a border
(crop), so every layer is a rectangle of one picture and drops into the SVG at known world coordinates.

Layers
------
background  : everything that can't be touched (wall, sunburst, arch, columns, sign, shelf, counter).
              One image per camera position: bar (whole), sign (intro, lit and unlit), shelf, mid
              (talk, recipe, barman's choice) and menu.
touchables  : menu, panther, dice, honey jar, rendered alone on a transparent film (the rest of the
              scene still lights and shadows them), so they keep true colour and can light up.
bottles     : one per Style, rendered on the shelf and cropped, placed by the app.
Dionysus is not rendered (R13): the app draws prototype B's figure in its own swappable layer.
"""
import bpy, bmesh, math, os, sys, json, time
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.dirname(HERE)
OUT = os.path.join(PROTO, 'img')
WORK = os.path.join(HERE, '_work')
FONT = os.path.join(HERE, 'fonts', 'BebasNeue-Regular.ttf')
args = sys.argv[1:]
QUICK = '--quick' in args
ONLY = args[args.index('--only') + 1] if '--only' in args else 'all'
PREVIEW = ONLY == 'panther'
os.makedirs(OUT, exist_ok=True); os.makedirs(WORK, exist_ok=True)

# ---------------------------------------------------------------- camera and the world-unit mapping
FRAME = (0, -240, 1600, 1360)        # world rect the full camera sees
EYE_Y = 250                          # world y of the eye (camera height): we look slightly down on the counter
DIST = 25.0                          # camera to reference plane, Blender units
C = Vector((0, -DIST, (760 - EYE_Y) / 100))
U = 0.01                             # one world unit in Blender units, on the reference plane


def P(x, y, d=0.0):
    """World (x, y) on the reference plane, offset d Blender units in depth (no projection)."""
    return Vector(((x - 800) * U, d, (760 - y) * U))


def scale_for(Y):
    return (DIST + Y) / DIST


def push(obj, Y):
    """Move an object built on the reference plane to depth Y, keeping its place in the picture."""
    s = scale_for(Y)
    obj.location = C + (obj.location - C) * s
    obj.scale = obj.scale * s
    return obj


def surface_y(Y, front_y=658, front_Y=-1.3):
    """World y where the counter top appears at depth Y (the top is a horizontal plane)."""
    zt = C.z + ((760 - front_y) * U - C.z) * scale_for(front_Y)
    z_ref = C.z + (zt - C.z) / scale_for(Y)
    return 760 - z_ref / U


# ---------------------------------------------------------------- scene reset and helpers
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.view_settings.view_transform = 'Standard'   # true colour: material colours come out as written
scene.view_settings.look = 'None'
world = bpy.data.worlds.new('world'); scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.004, 0.0035, 0.004, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 1.0


def srgb(h, a=1.0):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (*lin, a)


MATS = {}


def mat(name, colour, rough=0.6, metal=0.0, coat=0.0, emit=None, emit_strength=0.0, spec=0.5):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = srgb(colour)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Specular IOR Level'].default_value = spec
    if coat: b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = 0.08
    if emit:
        b.inputs['Emission Color'].default_value = srgb(emit); b.inputs['Emission Strength'].default_value = emit_strength
    MATS[name] = m
    return m


def link(obj, coll=None):
    (coll or scene.collection).objects.link(obj); return obj


def mesh_obj(name, verts, faces, material=None):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    ob = bpy.data.objects.new(name, me); link(ob)
    if material: ob.data.materials.append(material)
    return ob


def box(name, x0, y0, x1, y1, d0, d1, material, bevel=0.0):
    """A box spanning world x0..x1, y0..y1 on the reference plane, depth d0..d1 (Blender units)."""
    vs = [P(x, y, d) for d in (d0, d1) for (x, y) in ((x0, y1), (x1, y1), (x1, y0), (x0, y0))]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; o = P(cx, cy, (d0 + d1) / 2)
    vs = [v - o for v in vs]
    ob = mesh_obj(name, vs, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], material)
    ob.location = o
    if bevel: add_bevel(ob, bevel)
    return ob


def add_bevel(ob, w, segs=3):
    m = ob.modifiers.new('bevel', 'BEVEL'); m.width = w; m.segments = segs; m.limit_method = 'ANGLE'
    return m


def smooth(ob):
    for p in ob.data.polygons: p.use_smooth = True


def lathe(name, profile, material, segs=40):
    """profile: list of (height, radius) in Blender units, bottom to top. Revolved about local Z."""
    bm = bmesh.new(); rings = []
    for h, r in profile:
        ring = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), h)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs; bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); link(ob); ob.data.materials.append(material); smooth(ob)
    return ob


def curve_obj(name, splines, bevel, material, closed=False, fill='FULL'):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    cu.bevel_depth = bevel; cu.bevel_resolution = 3; cu.fill_mode = fill
    for pts in splines:
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for p, v in zip(sp.points, pts): p.co = (*v, 1)
        sp.use_cyclic_u = closed
    ob = bpy.data.objects.new(name, cu); link(ob); cu.materials.append(material)
    return ob


def group(name, objs, Y):
    """Parent objects built on the reference plane to an empty, then push the whole group to depth Y."""
    e = bpy.data.objects.new(name, None); link(e)
    for o in objs:
        if o.parent is None: o.parent = e
    push(e, Y)
    return e


def children(e):
    return [o for o in bpy.data.objects if o.parent == e or (o.parent and o.parent.parent == e)]


# ---------------------------------------------------------------- materials: the muted world (Q7)
# Low saturation, low value: the bar is near-black and dark brown; cream only as a highlight.
def wall_material():
    m = bpy.data.materials.new('wall'); m.use_nodes = True
    nt = m.node_tree; n = nt.nodes; L = nt.links
    b = n['Principled BSDF']; b.inputs['Roughness'].default_value = 0.85
    tc = n.new('ShaderNodeTexCoord'); sep = n.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])
    comb = n.new('ShaderNodeCombineXYZ'); L.new(sep.outputs['X'], comb.inputs['X']); L.new(sep.outputs['Z'], comb.inputs['Y'])
    sc = n.new('ShaderNodeVectorMath'); sc.operation = 'SCALE'; sc.inputs['Scale'].default_value = 1 / 0.22
    L.new(comb.outputs[0], sc.inputs[0])
    fr = n.new('ShaderNodeVectorMath'); fr.operation = 'FRACTION'; L.new(sc.outputs[0], fr.inputs[0])
    sub = n.new('ShaderNodeVectorMath'); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = (0.5, 0.5, 0)
    L.new(fr.outputs[0], sub.inputs[0])
    ln = n.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; L.new(sub.outputs[0], ln.inputs[0])
    dot = n.new('ShaderNodeMath'); dot.operation = 'LESS_THAN'; dot.inputs[1].default_value = 0.11
    L.new(ln.outputs['Value'], dot.inputs[0])
    mix = n.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = srgb('#120e0c'); mix.inputs['B'].default_value = srgb('#211915')
    L.new(dot.outputs[0], mix.inputs['Factor']); L.new(mix.outputs['Result'], b.inputs['Base Color'])
    bump = n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.35
    L.new(dot.outputs[0], bump.inputs['Height']); L.new(bump.outputs[0], b.inputs['Normal'])
    return m


M_WALL = wall_material()
M_RAY = mat('ray', '#1f1814', 0.8)
M_SUN1 = mat('sun1', '#1b1512', 0.8)
M_SUN2 = mat('sun2', '#211915', 0.8)
M_ARCH = mat('arch', '#2e241d', 0.55)
M_COL = mat('column', '#241c17', 0.6)
M_COL2 = mat('column2', '#1d1612', 0.7)
M_BOARD = mat('board', '#151112', 0.5)
M_FRAME = mat('frame', '#2c231d', 0.45, 0.3)
M_ROD = mat('rod', '#2a221c', 0.4, 0.6)
M_WOOD = mat('shelfwood', '#3a2a1e', 0.45)
M_TOP = mat('countertop', '#3b2a1e', 0.3, coat=0.4)
M_FRONT = mat('counterfront', '#231812', 0.6)
M_PANEL = mat('panel', '#2a1d15', 0.55)
M_KEY = mat('meander', '#4a3a2b', 0.35, 0.65)
M_BRASS = mat('brass', '#5a4a36', 0.3, 0.8)
M_BULB = mat('bulb', '#ffcf8a', 0.5, emit='#ffc27a', emit_strength=18)
M_NEON = mat('neon', '#ff7aa0', 0.4, emit='#ff5c8a', emit_strength=14)
M_NEON_OFF = mat('neon_off', '#5a4a4c', 0.25, coat=0.5)

# ---------------------------------------------------------------- the muted world
WORLD = []      # everything that is background
T = {}          # touchables: name -> [objects]

wall = box('wall', -900, -900, 2500, 1800, -0.05, 0.05, M_WALL)
push(wall, 3.3); WORLD.append(wall)

# sunburst: raised rays and two half-discs behind Dionysus (B: centre 800,760)
rays = []
for i in range(18):
    if i % 2: continue
    a0 = math.pi + i * math.pi / 18; a1 = a0 + math.pi / 18; r = 900
    pts = [P(800, 760, 0)] + [P(800 + r * math.cos(a), 760 + r * math.sin(a), 0) for a in (a0, (a0 + a1) / 2, a1)]
    pts2 = [p + Vector((0, -0.04, 0)) for p in pts]
    ob = mesh_obj(f'ray{i}', pts + pts2, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], M_RAY)
    rays.append(ob)
for rr, d, m_ in ((300, -0.07, M_SUN1), (220, -0.11, M_SUN2)):
    n = 48; pts = [P(800 + rr * math.cos(math.pi + math.pi * i / n), 760 + rr * math.sin(math.pi + math.pi * i / n), 0) for i in range(n + 1)]
    front = [p + Vector((0, d, 0)) for p in pts]
    vs = pts + front; N = len(pts)
    faces = [tuple(range(N - 1, -1, -1)), tuple(range(N, 2 * N))] + [(i, i + 1, N + i + 1, N + i) for i in range(N - 1)]
    rays.append(mesh_obj(f'sun{rr}', vs, faces, m_))
WORLD += rays; group('sunburst', rays, 3.25)

# the arch: a round moulding, legs at x 430 and 1170, crown at y -40
arch_pts = [P(430, 780, 0), P(430, 330, 0)]
arch_pts += [P(800 - 370 * math.cos(math.pi * i / 40), 330 - 370 * math.sin(math.pi * i / 40), 0) for i in range(1, 40)]
arch_pts += [P(1170, 330, 0), P(1170, 780, 0)]
arch = curve_obj('arch', [arch_pts], 0.13, M_ARCH); WORLD.append(arch)
arch2 = curve_obj('arch_inner', [[p + Vector((0, -0.02, 0)) for p in arch_pts]], 0.05, M_FRAME)
arch2.location = (0, 0, 0); WORLD.append(arch2)
# offset the inner bead slightly inward so it reads as a second moulding
for sp in arch2.data.splines:
    for pt in sp.points:
        v = Vector(pt.co[:3]); c0 = P(800, 330, 0)
        if v.z > c0.z:
            dv = (v - c0); dv.y = 0; v = c0 + dv * (1 - 0.28 / max(dv.length, 1e-3)) + Vector((0, -0.06, 0))
        else:
            v = v + Vector((0.28 if v.x < 0 else -0.28, -0.06, 0))
        pt.co = (*v, 1)
group('archgrp', [arch, arch2], 3.0)


# columns: fluted shafts with Ionic-ish capitals (B: x 250..320 and 1280..1350)
def column(cx):
    parts = []
    n = 32; r0 = 0.36; bm = bmesh.new(); top = []; bot = []
    for i in range(n):
        a = 2 * math.pi * i / n; r = r0 * (0.9 if i % 2 else 1.0)
        bot.append(bm.verts.new((r * math.cos(a), r * math.sin(a), 0)))
        top.append(bm.verts.new((r * math.cos(a), r * math.sin(a), 5.0)))
    for i in range(n):
        j = (i + 1) % n; bm.faces.new((bot[i], bot[j], top[j], top[i]))
    me = bpy.data.meshes.new('shaft'); bm.to_mesh(me); bm.free()
    sh = bpy.data.objects.new('shaft', me); link(sh); sh.data.materials.append(M_COL)
    sh.location = P(cx, 770, 0); parts.append(sh)
    parts.append(box('cap', cx - 49, 236, cx + 49, 258, -0.45, 0.45, M_COL, 0.03))
    parts.append(box('abacus', cx - 44, 226, cx + 44, 238, -0.42, 0.42, M_COL2, 0.02))
    parts.append(box('base', cx - 46, 752, cx + 46, 772, -0.46, 0.46, M_COL, 0.03))
    for vx in (cx - 33, cx + 33):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.1, minor_radius=0.045, location=P(vx, 247, -0.42), rotation=(math.pi / 2, 0, 0))
        t = bpy.context.active_object; t.data.materials.append(M_COL); smooth(t); parts.append(t)
    # a warm sconce on each column: the practical light
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, location=P(cx, 470, -0.5)); b_ = bpy.context.active_object
    b_.data.materials.append(M_BULB); smooth(b_); parts.append(b_)
    cup = lathe('sconce', [(-0.16, 0.0), (-0.16, 0.06), (-0.06, 0.2), (0.04, 0.22), (0.05, 0.2)], M_BRASS, 24)
    cup.location = P(cx, 470, -0.5); parts.append(cup)
    arm = box('sconce_arm', cx - 4, 478, cx + 4, 488, -0.5, -0.32, M_BRASS); parts.append(arm)
    WORLD.extend(parts)
    g = group(f'col{cx}', parts, 2.4)
    return g


for cx in (285, 1315): column(cx)

# the neon sign, the tallest thing (B: board 452..1148 x 58..226)
sign_parts = [box('board', 452, 58, 1148, 226, -0.1, 0.1, M_BOARD, 0.06),
              box('boardrim', 446, 52, 1154, 232, 0.02, 0.12, M_FRAME, 0.02)]
for x in (560, 1040):
    sign_parts.append(box('rod', x - 3, -400, x + 3, 58, -0.03, 0.03, M_ROD))
fc = bpy.data.curves.new('neon', 'FONT'); fc.body = 'DIONYSUS'
if os.path.exists(FONT): fc.font = bpy.data.fonts.load(FONT)
fc.align_x = 'CENTER'; fc.align_y = 'BOTTOM_BASELINE'; fc.space_character = 1.12
fc.fill_mode = 'NONE'; fc.bevel_depth = 0.028; fc.bevel_resolution = 3; fc.resolution_u = 10
neon = bpy.data.objects.new('neon', fc); link(neon); fc.materials.append(M_NEON)
neon.rotation_euler = (math.pi / 2, 0, 0)
fc.size = 1.0
bpy.context.view_layer.update()
w = neon.dimensions.x
fc.size = 5.9 / max(w, 1e-3)
neon.location = P(800, 200, -0.16)
sign_parts.append(neon); WORLD += sign_parts
SIGN = group('sign', sign_parts, 2.0)

# the shelf under the sign (B: plank 460..1140 at y 384..400)
shelf_parts = [box('plank', 460, 384, 1140, 400, -0.3, 0.3, M_WOOD, 0.015),
               box('lip', 460, 384, 1140, 388, -0.31, -0.29, M_FRAME)]
for x in (492, 1108):
    shelf_parts.append(box('bracket', x - 10, 400, x + 10, 430, -0.2, 0.2, M_WOOD, 0.01))
WORLD += shelf_parts
SHELF_Y = 1.0
group('shelf', shelf_parts, SHELF_Y)

# the counter: a real slab with a perspective top, panels and a Greek-key band on the front
FRONT_Y, BACK_Y = -1.3, 0.45
s_front = scale_for(FRONT_Y)
zt = C.z + ((760 - 658) * U - C.z) * s_front
top = mesh_obj('countertop', [], [], M_TOP)
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
bm.to_mesh(top.data); bm.free()
top.scale = (30, BACK_Y - FRONT_Y + 0.06, 0.16 * s_front)
top.location = (0, (BACK_Y + FRONT_Y) / 2 - 0.03, zt - 0.08 * s_front)
add_bevel(top, 0.02); WORLD.append(top)
front_ob = mesh_obj('counterfront', [], [], M_FRONT)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(front_ob.data); bm.free()
front_ob.scale = (30, 0.6, 12); front_ob.location = (0, FRONT_Y + 0.3, zt - 0.16 * s_front - 6)
WORLD.append(front_ob)
cparts = []
for x in range(180 - 155 * 4, 1420 + 155 * 4, 155):
    x0, x1 = x + 8, x + 147
    cparts.append(box('panel', x0, 740, x1, 910, -0.05, 0.0, M_PANEL, 0.01))
    cparts.append(box('panelin', x0 + 12, 752, x1 - 12, 898, -0.03, 0.0, M_FRONT, 0.008))
cparts.append(box('trim', -900, 924, 2500, 934, -0.06, 0.0, M_KEY))
cparts.append(box('band_top', -900, 694, 2500, 697, -0.04, 0.0, M_KEY))
cparts.append(box('band_bot', -900, 725, 2500, 728, -0.04, 0.0, M_KEY))
key = []
for x0 in range(-900, 2500, 44):
    key.append([P(x0 + 2, 720, -0.03), P(x0 + 2, 702, -0.03), P(x0 + 30, 702, -0.03), P(x0 + 30, 714, -0.03),
                P(x0 + 14, 714, -0.03), P(x0 + 14, 708, -0.03), P(x0 + 22, 708, -0.03)])
    key.append([P(x0 + 30, 720, -0.03), P(x0 + 42, 720, -0.03), P(x0 + 42, 702, -0.03)])
cparts.append(curve_obj('greekkey', key, 0.016, M_KEY))
WORLD += cparts
group('counterfront_details', cparts, FRONT_Y - 0.001)

# ---------------------------------------------------------------- touchables: true colour (Q7)
M_GREEN = mat('menu_green', '#1f5a42', 0.45, coat=0.3)
M_GOLD = mat('gold', '#d8b25a', 0.25, 1.0)
M_HONEY = mat('honey', '#e0951c', 0.12, coat=1.0)
M_JAR = mat('jarlid', '#f0e7d8', 0.7)
M_TWINE = mat('twine', '#a3172a', 0.6)
M_DIPPER = mat('dipper', '#b98552', 0.5)
M_IVORY = mat('ivory', '#f3ead6', 0.25, coat=0.6)
M_PIP = mat('pip', '#b3172a', 0.3)
M_EYE = mat('eye', '#b8d84a', 0.15, coat=1.0, emit='#a8c83a', emit_strength=0.8)
M_NOSE = mat('nose', '#3a2a2e', 0.4)
M_IVY = mat('ivy', '#3f8a34', 0.4)


def leopard_material(scale=7.0, name='leopard'):
    """Gold coat with broken rosettes: rings from a distorted Voronoi, broken up by noise, darker gold inside."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; n = nt.nodes; L = nt.links
    b = n['Principled BSDF']; b.inputs['Roughness'].default_value = 0.62
    b.inputs['Sheen Weight'].default_value = 0.6; b.inputs['Sheen Roughness'].default_value = 0.4
    tc = n.new('ShaderNodeTexCoord')
    warp = n.new('ShaderNodeTexNoise'); warp.inputs['Scale'].default_value = 3.0; warp.inputs['Detail'].default_value = 2.0
    L.new(tc.outputs['Object'], warp.inputs['Vector'])
    mixv = n.new('ShaderNodeMix'); mixv.data_type = 'VECTOR'; mixv.inputs['Factor'].default_value = 0.12
    L.new(tc.outputs['Object'], mixv.inputs['A']); L.new(warp.outputs['Color'], mixv.inputs['B'])
    vor = n.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = scale; vor.inputs['Randomness'].default_value = 1.0
    L.new(mixv.outputs['Result'], vor.inputs['Vector'])
    # ring: dark where the distance to the cell centre is between ~0.22 and ~0.34
    r1 = n.new('ShaderNodeMapRange'); r1.inputs['From Min'].default_value = 0.18; r1.inputs['From Max'].default_value = 0.23
    r2 = n.new('ShaderNodeMapRange'); r2.inputs['From Min'].default_value = 0.37; r2.inputs['From Max'].default_value = 0.31
    L.new(vor.outputs['Distance'], r1.inputs['Value']); L.new(vor.outputs['Distance'], r2.inputs['Value'])
    ring = n.new('ShaderNodeMath'); ring.operation = 'MINIMUM'
    L.new(r1.outputs['Result'], ring.inputs[0]); L.new(r2.outputs['Result'], ring.inputs[1])
    brk = n.new('ShaderNodeTexNoise'); brk.inputs['Scale'].default_value = scale * 4.5; brk.inputs['Detail'].default_value = 1.0
    L.new(tc.outputs['Object'], brk.inputs['Vector'])
    gate = n.new('ShaderNodeMapRange'); gate.inputs['From Min'].default_value = 0.36; gate.inputs['From Max'].default_value = 0.44
    L.new(brk.outputs['Fac'], gate.inputs['Value'])
    spots = n.new('ShaderNodeMath'); spots.operation = 'MULTIPLY'
    L.new(ring.outputs[0], spots.inputs[0]); L.new(gate.outputs['Result'], spots.inputs[1])
    inner = n.new('ShaderNodeMapRange'); inner.inputs['From Min'].default_value = 0.26; inner.inputs['From Max'].default_value = 0.12
    L.new(vor.outputs['Distance'], inner.inputs['Value'])
    base = n.new('ShaderNodeMix'); base.data_type = 'RGBA'
    base.inputs['A'].default_value = srgb('#cf9f52'); base.inputs['B'].default_value = srgb('#b87a36')
    L.new(inner.outputs['Result'], base.inputs['Factor'])
    col = n.new('ShaderNodeMix'); col.data_type = 'RGBA'
    L.new(base.outputs['Result'], col.inputs['A']); col.inputs['B'].default_value = srgb('#24140a')
    L.new(spots.outputs[0], col.inputs['Factor'])
    L.new(col.outputs['Result'], b.inputs['Base Color'])
    return m


M_LEO = leopard_material(9.5)
M_LEO_HEAD = leopard_material(16.0, 'leopard_head')
M_MUZZLE = mat('muzzle', '#efd9b0', 0.6)
M_EAR_IN = mat('ear_in', '#3a2414', 0.7)


def menu_texture():
    """The menu card's face, drawn as a texture: green card, gold rule, MENU, three gold lines."""
    from PIL import Image, ImageDraw, ImageFont
    W, H = 512, 640; im = Image.new('RGB', (W, H), '#1f5a42'); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 230], fill='#2a6b50')
    d.rectangle([14, 14, W - 15, H - 15], outline='#d8b25a', width=8)
    d.rectangle([60, 70, W - 60, 76], fill='#d8b25a')
    f = ImageFont.truetype(FONT, 150) if os.path.exists(FONT) else ImageFont.load_default()
    d.text((W / 2, 168), 'MENU', font=f, fill='#e2bf64', anchor='mm')
    for i, (a, b) in enumerate(((90, 422), (120, 392), (90, 422))):
        d.rectangle([a, 330 + i * 70, b, 342 + i * 70], fill='#d8b25a')
    p = os.path.join(WORK, 'menu_face.png'); im.save(p)
    return p


def menu():
    """A standing tent card, B's shape (108 wide at the base, 76 at the top, 104 high), moved left to x 460..568."""
    Y = -0.75; yb = surface_y(Y)
    m = bpy.data.materials.new('menu_face'); m.use_nodes = True; nt = m.node_tree
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(menu_texture())
    b = nt.nodes['Principled BSDF']; nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.42; b.inputs['Coat Weight'].default_value = 0.3
    h = 104; tilt = 0.24
    vs = [P(460, yb, -tilt), P(568, yb, -tilt), P(552, yb - h, 0), P(476, yb - h, 0)]
    o = P(514, yb, 0); vs = [v - o for v in vs]
    face = mesh_obj('menu_face', vs, [(0, 1, 2, 3)], m); face.location = o
    uv = face.data.uv_layers.new(); [setattr(uv.data[i], 'uv', c) for i, c in enumerate(((0, 0), (1, 0), (1, 1), (0, 1)))]
    sol = face.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.03; sol.offset = 1
    face.data.materials.append(M_GREEN); sol.material_offset = 1; sol.material_offset_rim = 1
    back = mesh_obj('menu_back', [P(460, yb, tilt) - o, P(568, yb, tilt) - o, P(552, yb - h, 0) - o, P(476, yb - h, 0) - o],
                    [(3, 2, 1, 0)], M_GREEN); back.location = o
    sb = back.modifiers.new('sol', 'SOLIDIFY'); sb.thickness = 0.03
    parts = [face, back]
    g = group('menu', parts, Y)
    return parts


def honey_jar():
    """New in E (R8): honey comes from a jar he dips into, never from the counter."""
    Y = -0.85; x = 640; yb = surface_y(Y)
    parts = []
    body = lathe('jar', [(0, 0), (0, 0.24), (0.03, 0.29), (0.38, 0.31), (0.52, 0.27), (0.56, 0.21), (0.64, 0.21), (0.66, 0.0)], M_HONEY, 48)
    body.location = P(x, yb, 0); parts.append(body)
    cloth = lathe('cloth', [(0.5, 0.0), (0.5, 0.25), (0.58, 0.29), (0.64, 0.27), (0.7, 0.18), (0.72, 0.0)], M_JAR, 48)
    cloth.location = P(x, yb, 0); parts.append(cloth)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.235, minor_radius=0.018, location=P(x, yb - 55, 0)); tw = bpy.context.active_object
    tw.data.materials.append(M_TWINE); smooth(tw); parts.append(tw)
    # the dipper, leaning out of the jar
    stick = lathe('dipper', [(0, 0.022), (0.55, 0.022), (0.6, 0.03)], M_DIPPER, 16)
    head = lathe('dipperhead', [(-0.12, 0.0), (-0.11, 0.05), (-0.08, 0.065), (-0.05, 0.05), (-0.03, 0.065), (0.0, 0.05), (0.02, 0.03), (0.03, 0.0)], M_DIPPER, 20)
    head.parent = stick
    stick.location = P(x + 6, yb - 52, 0); stick.rotation_euler = (0.25, -0.5, 0)
    parts += [stick, head]
    group('honeyjar', parts, Y)
    return parts


def dice():
    Y = -1.0; yb = surface_y(Y); s = 0.27
    bpy.ops.mesh.primitive_cube_add(size=s, location=P(938, yb - 13.5, 0)); d = bpy.context.active_object
    add_bevel(d, 0.035, 4); d.data.materials.append(M_IVORY); smooth(d)
    pips = []
    for (px, pz) in ((-0.07, 0.07), (0, 0), (0.07, -0.07)):            # front face: three
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.027, location=(px, -s / 2 + 0.008, pz)); p = bpy.context.active_object
        p.scale = (1, 0.45, 1); p.data.materials.append(M_PIP); smooth(p); p.parent = d; pips.append(p)
    for (px, py) in ((-0.07, -0.07), (0.07, 0.07)):                    # top face: two
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.027, location=(px, py, s / 2 - 0.008)); p = bpy.context.active_object
        p.scale = (1, 1, 0.45); p.data.materials.append(M_PIP); smooth(p); p.parent = d; pips.append(p)
    for (py, pz) in ((-0.06, 0.06), (0.0, 0.0), (0.06, -0.06), (-0.06, -0.06), (0.06, 0.06)):  # right face: five
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.024, location=(s / 2 - 0.008, py, pz)); p = bpy.context.active_object
        p.scale = (0.45, 1, 1); p.data.materials.append(M_PIP); smooth(p); p.parent = d; pips.append(p)
    d.rotation_euler = (0, 0, math.radians(-22))
    push(d, Y)
    return [d] + pips


def skin_body(name, verts, edges, radii, material, subdiv=2):
    """An organic body from a skeleton: Skin modifier (radius per joint) smoothed by subdivision."""
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], edges, []); me.update()
    ob = bpy.data.objects.new(name, me); link(ob); ob.data.materials.append(material)
    sk = ob.modifiers.new('skin', 'SKIN'); sk.use_smooth_shade = True; sk.branch_smoothing = 1.0
    sv = me.skin_vertices[0].data
    for i, r in enumerate(radii):
        sv[i].radius = r
    sv[0].use_root = True
    sd = ob.modifiers.new('subd', 'SUBSURF'); sd.levels = subdiv; sd.render_levels = subdiv
    return ob


def panther():
    """Dionysus' panther: the spotted kind of the old mosaics, lying sphinx-style on the counter,
    head turned to look at you. Built from a skeleton, not blobs."""
    Y = -0.55; yb = surface_y(Y)
    near, far = -0.2, 0.2                         # the two sides of the body, in depth
    J = {   # joint: (x, y above the counter, depth)
        'rump': (1166, 40, 0.0), 'back': (1110, 46, 0.0), 'chest': (1042, 48, 0.0), 'neck': (1024, 80, -0.07), 'nape': (1012, 100, -0.12),
        'tail0': (1190, 30, 0.04), 'tail1': (1222, 12, 0.02), 'tail2': (1250, 14, -0.02), 'tail3': (1262, 36, -0.05), 'tail4': (1254, 60, -0.07), 'tail5': (1240, 66, -0.08),
        'shN': (1036, 30, near), 'elN': (1020, 10, near - 0.02), 'wrN': (982, 7, near - 0.02), 'pawN': (960, 7, near - 0.02),
        'shF': (1036, 30, far), 'elF': (1022, 10, far), 'wrF': (990, 7, far), 'pawF': (970, 7, far),
        'hipN': (1146, 32, near * 0.55), 'knN': (1118, 14, near - 0.04), 'hkN': (1160, 8, near - 0.05), 'ftN': (1126, 6, near - 0.06),
    }
    names = list(J)
    verts = [P(x, yb - h, d) for (x, h, d) in J.values()]
    E = [('rump', 'back'), ('back', 'chest'), ('chest', 'neck'), ('neck', 'nape'), ('rump', 'tail0'), ('tail0', 'tail1'), ('tail1', 'tail2'), ('tail2', 'tail3'), ('tail3', 'tail4'), ('tail4', 'tail5'),
         ('chest', 'shN'), ('shN', 'elN'), ('elN', 'wrN'), ('wrN', 'pawN'), ('chest', 'shF'), ('shF', 'elF'), ('elF', 'wrF'), ('wrF', 'pawF'),
         ('rump', 'hipN'), ('hipN', 'knN'), ('knN', 'hkN'), ('hkN', 'ftN')]
    edges = [(names.index(a_), names.index(b_)) for a_, b_ in E]
    R_ = {'rump': (0.4, 0.37), 'back': (0.37, 0.35), 'chest': (0.42, 0.36), 'neck': (0.27, 0.26), 'nape': (0.24, 0.23),
          'tail0': (0.07, 0.07), 'tail1': (0.06, 0.06), 'tail2': (0.055, 0.055), 'tail3': (0.05, 0.05), 'tail4': (0.045, 0.045), 'tail5': (0.05, 0.05),
          'shN': (0.14, 0.13), 'elN': (0.08, 0.08), 'wrN': (0.065, 0.065), 'pawN': (0.08, 0.06),
          'shF': (0.13, 0.12), 'elF': (0.075, 0.075), 'wrF': (0.06, 0.06), 'pawF': (0.075, 0.055),
          'hipN': (0.3, 0.28), 'knN': (0.13, 0.12), 'hkN': (0.07, 0.07), 'ftN': (0.075, 0.055)}
    body = skin_body('panther', verts, edges, [R_[k] for k in names], M_LEO)
    parts = [body]
    # the head, turned to the viewer: skull, muzzle, chin, nose, eyes, ears
    hc = P(1008, yb - 114, -0.17)
    def sph(name, loc, r, sc, m_, seg=32):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=seg // 2); o = bpy.context.active_object
        o.name = name; o.scale = sc; o.data.materials.append(m_); smooth(o); parts.append(o); return o
    sph('skull', hc, 0.26, (1.1, 0.95, 0.88), M_LEO_HEAD)
    sph('cheekL', hc + Vector((-0.11, -0.1, -0.06)), 0.12, (1, 0.9, 0.85), M_LEO_HEAD)
    sph('cheekR', hc + Vector((0.11, -0.1, -0.06)), 0.12, (1, 0.9, 0.85), M_LEO_HEAD)
    sph('muzzle', hc + Vector((0, -0.19, -0.1)), 0.09, (1.25, 0.7, 0.62), M_MUZZLE)
    sph('chin', hc + Vector((0, -0.15, -0.15)), 0.06, (1, 0.7, 0.6), M_MUZZLE)
    nose = sph('nose', hc + Vector((0, -0.285, -0.05)), 0.04, (1.2, 0.7, 0.7), M_NOSE)
    for sx in (-1, 1):
        e = sph('eye', hc + Vector((sx * 0.095, -0.205, 0.04)), 0.042, (1.25, 0.55, 0.85), M_EYE)
        e.rotation_euler = (0, sx * 0.25, 0)
        sph('pupil', hc + Vector((sx * 0.095, -0.228, 0.04)), 0.014, (0.6, 0.4, 1.5), M_NOSE, 16)
        bpy.ops.mesh.primitive_cone_add(radius1=0.085, radius2=0.012, depth=0.15, vertices=24,
                                        location=hc + Vector((sx * 0.17, 0.02, 0.21)), rotation=(math.radians(-12), sx * math.radians(28), 0))
        ear = bpy.context.active_object; ear.scale = (1, 0.45, 1); ear.data.materials.append(M_LEO_HEAD); smooth(ear); parts.append(ear)
        bpy.ops.mesh.primitive_cone_add(radius1=0.055, radius2=0.008, depth=0.1, vertices=24,
                                        location=hc + Vector((sx * 0.168, -0.02, 0.2)), rotation=(math.radians(-12), sx * math.radians(28), 0))
        ei = bpy.context.active_object; ei.scale = (1, 0.3, 1); ei.data.materials.append(M_EAR_IN); smooth(ei); parts.append(ei)
    # an ivy collar, lying on the neck and chest
    for k in range(6):
        a_ = math.pi * (0.12 + 0.76 * k / 5)
        loc = P(1022 + 24 * math.cos(a_), yb - 86 + 10 * math.sin(a_), -0.36 + 0.12 * abs(math.cos(a_)))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.055, location=loc); lf = bpy.context.active_object
        lf.scale = (0.8, 0.35, 0.55); lf.rotation_euler = (0, a_ + math.pi / 2, 0); lf.data.materials.append(M_IVY); smooth(lf); parts.append(lf)
    group('panthergrp', parts, Y)
    return parts


if ONLY == 'panther':
    T['panther'] = panther()
if ONLY in ('all', 'bg', 'touch'):
    T['menu'] = menu(); T['honey'] = honey_jar(); T['dice'] = dice(); T['panther'] = panther()


# ---------------------------------------------------------------- bottles: one per Style (Q6)
# Profiles follow prototype B's family silhouettes (draw.js BOT): (svg y, half-width), svg y 96 is the base.
PROFILES = {
    'whisky': [(96, 0), (96, 20), (93, 24), (41, 24), (30, 15), (22, 7), (6, 7), (5, 0)],
    'gin': [(96, 0), (96, 12), (92, 14), (32, 14), (24, 6), (6, 6), (5, 0)],
    'rum': [(96, 0), (96, 18), (92, 21), (52, 21), (38, 14), (30, 5), (6, 5), (5, 0)],
    'tequila': [(96, 0), (96, 14), (92, 17), (34, 17), (25, 5), (6, 5), (5, 0)],
    'vodka': [(96, 0), (96, 10), (92, 12), (40, 12), (31, 4), (6, 4), (5, 0)],
    'brandy': [(96, 0), (95, 12), (88, 20), (74, 25), (60, 24), (46, 15), (34, 5), (6, 5), (5, 0)],
    'aperitif': [(96, 0), (96, 13), (92, 16), (52, 16), (38, 9), (32, 4), (6, 4), (5, 0)],
    'bitters': [(96, 0), (95, 9), (88, 15), (72, 17), (58, 13), (46, 3), (20, 3), (19, 0)],
    'mixer': [(96, 0), (96, 12), (92, 14), (44, 14), (32, 8), (26, 6), (18, 6), (17, 0)],
}
BOTTLE_SCALE = {'bitters': 0.78, 'mixer': 0.9}
LABEL_BAND = {  # (svg y top, svg y bottom, colour) per Family: a label layout, never wording
    'whisky': [(52, 78, '#f1e6cf')], 'gin': [(44, 84, '#f4f1e8')], 'rum': [(58, 78, '#e8d7a8')],
    'tequila': [(52, 74, '#1f4a3a')], 'vodka': [(56, 70, '#ffffff')], 'brandy': [(62, 76, '#1c1410')],
    'aperitif': [(56, 74, '#f3ead6'), (60, 63, '#c2141c')], 'bitters': [(44, 88, '#f4eedd')], 'mixer': [(50, 62, '#2f5a7a')],
}


def read_styles():
    """Bottle Styles from the shared recipe data (prototype B's data.js), so the art tracks the data."""
    import re
    src = open(os.path.join(PROTO, 'data.js'), encoding='utf8').read()
    out = []
    for k, label, kind, colour, shape in re.findall(r"'([^']+)':\['([^']+)','(\w+)','(#[0-9a-fA-F]{6})','(\w+)'\]", src):
        if kind in ('spirit', 'wine', 'liqueur', 'bitters', 'mixer'):
            out.append((k, label, colour, shape))
    return out


def make_bottle(style, colour, fam):
    prof = PROFILES.get(fam, PROFILES['vodka']); s = BOTTLE_SCALE.get(fam, 1.04) * U
    body = lathe('bottle_' + style, [((96 - y) * s, r * s) for y, r in prof],
                 mat('btl_' + colour, colour, 0.32, coat=0.25, spec=0.35), 40)
    parts = [body]
    for (ya, yb_, col) in LABEL_BAND.get(fam, []):
        rmax = max(r for y, r in prof if ya <= y <= yb_ or True) * s
        r_at = lambda yy: next((r for y, r in prof if y <= yy), prof[-1][1])
        rr = min(r_at(ya), r_at(yb_)) * s + 0.004
        lb = lathe('label', [((96 - yb_) * s, rr), ((96 - ya) * s, rr)], mat('lbl_' + col, col, 0.7), 40)
        parts.append(lb)
    cap_y = min(y for y, r in prof); cap_r = [r for y, r in prof if y <= cap_y + 1][-1] if False else prof[-2][1]
    cap = lathe('cap', [((96 - cap_y - 2) * s, (cap_r + 1.2) * s), ((96 - cap_y + 8) * s, (cap_r + 1.2) * s)], mat('cap', '#1c1410', 0.4), 24)
    parts.append(cap)
    for p in parts:
        p.location = P(800, 384, 0)
        push(p, SHELF_Y)
    return parts


# ---------------------------------------------------------------- lights
def light(name, kind, loc, energy, colour='#ffffff', size=0.5, rot=None):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = srgb(colour)[:3]
    if kind == 'AREA': ld.size = size; ld.shape = 'DISK'
    else: ld.shadow_soft_size = size
    ob = bpy.data.objects.new(name, ld); link(ob); ob.location = loc
    if rot: ob.rotation_euler = rot
    return ob


# warm key from above the counter, in front: soft shadows
light('key', 'AREA', (1.0, -8, 7.5), 1100, '#ffd9b0', 4.0, (math.radians(52), 0, math.radians(6)))
# a dim cool fill from the left
light('fill', 'AREA', (-9, -12, 5), 70, '#9aa6c8', 6.0, (math.radians(80), 0, math.radians(-38)))
# the sconces' warm practical light on the wall
for cx in (285, 1315):
    p = P(cx, 470, -0.5); s_ = scale_for(2.4); loc = C + (p - C) * s_
    light('sconce', 'POINT', loc + Vector((0, -0.4, 0)), 55, '#ffb35c', 0.15)
# warm bar light under the shelf, washing the back wall and the god
p = P(800, 410, 0); loc = C + (p - C) * scale_for(SHELF_Y)
light('undershelf', 'AREA', loc + Vector((0, -0.35, -0.08)), 90, '#ffc47a', 3.0, (math.radians(25), 0, 0))
# the neon's own wash on the board and wall, so the sign lights the room
p = P(800, 150, -0.6); loc = C + (p - C) * scale_for(2.0)
NEON_WASH = light('neonwash', 'AREA', loc, 60, '#ff6a95', 6.0, (math.radians(100), 0, 0))

# ---------------------------------------------------------------- camera
cd = bpy.data.cameras.new('cam'); cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36
cd.lens = 36 * DIST / ((FRAME[2] - FRAME[0]) * U)
cd.shift_y = -((FRAME[1] + FRAME[3]) / 2 - EYE_Y) / (FRAME[2] - FRAME[0])
cd.clip_start = 0.1; cd.clip_end = 200
cam = bpy.data.objects.new('cam', cd); link(cam); cam.location = C; cam.rotation_euler = (math.pi / 2, 0, 0)
scene.camera = cam

# ---------------------------------------------------------------- rendering
r = scene.render
r.resolution_percentage = 100
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGBA'; r.image_settings.color_depth = '8'
cy = scene.cycles
cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.02
cy.use_denoising = True
try: cy.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
cy.max_bounces = 4; cy.diffuse_bounces = 2; cy.glossy_bounces = 2; cy.transmission_bounces = 2; cy.transparent_max_bounces = 4
cy.caustics_reflective = False; cy.caustics_refractive = False
cy.use_light_tree = True
try: cy.threads_mode = 'AUTO'
except Exception: pass

ALL_TOUCH = [o for parts in T.values() for o in parts]
LOG = []
FW, FH = FRAME[2] - FRAME[0], FRAME[3] - FRAME[1]


def set_visible(visible):
    vis = set(visible)
    for o in bpy.data.objects:
        if o.type in ('MESH', 'CURVE', 'META', 'FONT', 'SURFACE'):
            o.visible_camera = o in vis


def render_region(name, region, k, visible, transparent, samples):
    """Render world rect `region` (x0,y0,x1,y1) of the one camera at k pixels per world unit."""
    x0, y0, x1, y1 = region
    if QUICK: k = k * 0.35; samples = max(8, samples // 4)
    r.resolution_x = int(round(FW * k)); r.resolution_y = int(round(FH * k))
    r.use_border = True; r.use_crop_to_border = True
    r.border_min_x = (x0 - FRAME[0]) / FW; r.border_max_x = (x1 - FRAME[0]) / FW
    r.border_min_y = 1 - (y1 - FRAME[1]) / FH; r.border_max_y = 1 - (y0 - FRAME[1]) / FH
    r.film_transparent = transparent
    cy.samples = samples
    set_visible(visible)
    path = os.path.join(WORK, name + '.png'); r.filepath = path
    t = time.time(); bpy.ops.render.render(write_still=True); dt = time.time() - t
    w, h = r.resolution_x * (r.border_max_x - r.border_min_x), r.resolution_y * (r.border_max_y - r.border_min_y)
    LOG.append({'layer': name, 'px': [round(w), round(h)], 'samples': samples, 'seconds': round(dt, 1)})
    print(f'[render] {name}: {round(w)}x{round(h)} px, {samples} spp, {dt:.1f}s', flush=True)
    return path


def bbox_world(objs, margin=10):
    from bpy_extras.object_utils import world_to_camera_view
    r.resolution_x, r.resolution_y = FW, FH          # the projection depends on the frame's aspect
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    xs, ys = [], []
    for o in objs:
        oe = o.evaluated_get(dg)
        for c in oe.bound_box:
            co = world_to_camera_view(scene, cam, oe.matrix_world @ Vector(c))
            xs.append(FRAME[0] + co.x * FW); ys.append(FRAME[1] + (1 - co.y) * FH)
    return (min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin)


# ---------------------------------------------------------------- post: neon bloom, crop, WebP
def post_bg(png, bloom_src=None, region=None, k=1.0):
    from PIL import Image, ImageFilter
    import numpy as np
    im = Image.open(png).convert('RGB'); a = np.asarray(im).astype(np.float32) / 255
    if bloom_src is not None:
        bx0, by0, bk, bim = bloom_src
        x0, y0, x1, y1 = region
        crop = bim.crop((int((x0 - bx0) * bk), int((y0 - by0) * bk), int((x1 - bx0) * bk), int((y1 - by0) * bk))).resize(im.size, Image.BILINEAR)
        g = np.asarray(crop).astype(np.float32) / 255
        a = 1 - (1 - a) * (1 - g)     # screen
    out = Image.fromarray((np.clip(a, 0, 1) * 255).astype('uint8'))
    return out


def make_bloom(png, k):
    """A soft pink halo from the bright neon pixels of the full bar render."""
    from PIL import Image, ImageFilter
    import numpy as np
    im = Image.open(png).convert('RGB'); a = np.asarray(im).astype(np.float32) / 255
    lum = a.max(axis=2); pink = (a[..., 0] > 0.55) & (a[..., 0] > a[..., 1] * 1.25)
    m = np.where(pink & (lum > 0.6), 1.0, 0.0)[..., None] * a
    src = Image.fromarray((m * 255).astype('uint8'))
    b1 = np.asarray(src.filter(ImageFilter.GaussianBlur(9 * k))).astype(np.float32) / 255
    b2 = np.asarray(src.filter(ImageFilter.GaussianBlur(34 * k))).astype(np.float32) / 255
    g = np.clip(b1 * 1.1 + b2 * 1.4, 0, 1)
    return Image.fromarray((g * 255).astype('uint8'))


def save_webp(im, name, q=80):
    p = os.path.join(OUT, name + '.webp'); im.save(p, 'WEBP', quality=q, method=6)
    return 'img/' + name + '.webp'


def crop_alpha(png, region, k, name, q=86):
    from PIL import Image
    im = Image.open(png).convert('RGBA'); bb = im.getchannel('A').point(lambda v: 255 if v > 3 else 0).getbbox()
    if not bb: return None
    pad = 2; bb = (max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.width, bb[2] + pad), min(im.height, bb[3] + pad))
    im = im.crop(bb)
    x0, y0 = region[0], region[1]; kk = (r.resolution_x / FW)
    rect = [round(x0 + bb[0] / kk, 2), round(y0 + bb[1] / kk, 2), round(im.width / kk, 2), round(im.height / kk, 2)]
    src = save_webp(im, name, q)
    return {'src': src, 'x': rect[0], 'y': rect[1], 'w': rect[2], 'h': rect[3]}


MANIFEST_PATH = os.path.join(WORK, 'manifest.json')
MAN = json.load(open(MANIFEST_PATH)) if os.path.exists(MANIFEST_PATH) else {}
MAN.setdefault('bg', {}); MAN.setdefault('touch', {}); MAN.setdefault('bottles', {})
MAN['frame'] = FRAME
MAN['counterBackY'] = round(surface_y(BACK_Y), 1)
MAN['counterFrontY'] = 658
MAN['surface'] = {str(Y): round(surface_y(Y), 1) for Y in (-1.0, -0.85, -0.75, -0.55)}
T0 = time.time()

# camera positions (world rects). Each covers its shot on a 1280x800 tablet; the phone crops inside them.
SHOTS = {
    'bar': (FRAME, 1.25, 64),
    'sign': ((430, 20, 1170, 250), 2.0, 64),
    'shelf': ((420, 96, 1180, 580), 2.2, 64),
    'mid': ((280, 250, 1290, 810), 2.2, 64),
    'menu': ((400, 520, 630, 700), 6.0, 48),
}

if ONLY in ('all', 'bg'):
    WORLD_OBJS = [o for o in bpy.data.objects if o.type in ('MESH', 'CURVE', 'META', 'FONT') and o not in ALL_TOUCH]
    bar_png = render_region('bg_bar', SHOTS['bar'][0], SHOTS['bar'][1], WORLD_OBJS, False, SHOTS['bar'][2])
    kb = r.resolution_x / FW
    bloom = make_bloom(bar_png, kb)
    bloom_src = (FRAME[0], FRAME[1], kb, bloom)
    im = post_bg(bar_png, bloom_src, FRAME, kb)
    MAN['bg']['bar'] = {'src': save_webp(im, 'bg-bar', 78), 'x': FRAME[0], 'y': FRAME[1], 'w': FW, 'h': FH}
    for name in ('sign', 'shelf', 'mid', 'menu'):
        reg, k, spp = SHOTS[name]
        png = render_region('bg_' + name, reg, k, WORLD_OBJS, False, spp)
        im = post_bg(png, bloom_src, reg, k)
        MAN['bg'][name] = {'src': save_webp(im, 'bg-' + name, 80), 'x': reg[0], 'y': reg[1], 'w': reg[2] - reg[0], 'h': reg[3] - reg[1]}
    # the sign unlit, for the opening (the word becomes the neon sign)
    M_NEON.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.0
    M_NEON.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = srgb('#e9dccb')
    NEON_WASH.data.energy = 0
    reg, k, spp = SHOTS['sign']
    png = render_region('bg_sign_off', reg, k, WORLD_OBJS, False, spp)
    from PIL import Image
    MAN['bg']['signOff'] = {'src': save_webp(Image.open(png).convert('RGB'), 'bg-sign-off', 80), 'x': reg[0], 'y': reg[1], 'w': reg[2] - reg[0], 'h': reg[3] - reg[1]}
    M_NEON.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 14
    NEON_WASH.data.energy = 60

if PREVIEW:   # look at the panther large before it goes into the bar
    reg = bbox_world(T['panther'], 14)
    png = render_region('panther_preview', reg, 5.0, T['panther'], True, 48)
    print('preview', png, reg)
if ONLY in ('all', 'touch'):
    K = {'menu': 6.0, 'panther': 3.0, 'dice': 5.0, 'honey': 4.0}
    for name, parts in T.items():
        reg = bbox_world(parts, 14)
        if name == 'dice':
            for o in parts: o.visible_shadow = False
        png = render_region('t_' + name, reg, K[name], parts, True, 64)
        MAN['touch'][name] = crop_alpha(png, reg, K[name], 'touch-' + name)

if ONLY in ('all', 'bottles'):
    styles = read_styles()
    for i, (key, label, colour, fam) in enumerate(styles):
        parts = make_bottle(key, colour, fam)
        reg = bbox_world(parts, 6)
        png = render_region('b_' + key.replace(' ', '_'), reg, 2.6, parts, True, 32)
        info = crop_alpha(png, reg, 2.6, 'bottle-' + key.replace(' ', '-'), 84)
        info['ax'], info['ay'] = 800, 384          # anchor: base centre, on the shelf
        info['family'] = fam
        MAN['bottles'][key] = info
        for p in parts:
            bpy.data.objects.remove(p, do_unlink=True)

MAN['renderLog'] = MAN.get('renderLog', [])
MAN['renderLog'] = [x for x in MAN['renderLog'] if x['layer'] not in {l['layer'] for l in LOG}] + LOG
MAN['settings'] = {'engine': 'Cycles (CPU)', 'denoiser': 'OpenImageDenoise', 'adaptiveThreshold': 0.02, 'maxBounces': 4,
                   'viewTransform': 'Standard', 'quick': QUICK}
json.dump(MAN, open(MANIFEST_PATH, 'w'), indent=1)
with open(os.path.join(PROTO, 'layers.js'), 'w') as f:
    f.write('/* Written by blender/build_bar.py: where each rendered layer sits, in world units (prototype B\'s SVG space). */\n')
    f.write('const LAYERS = ' + json.dumps({k: v for k, v in MAN.items() if k != 'renderLog'}, indent=1) + ';\n')
    f.write('const RENDER_LOG = ' + json.dumps(MAN['renderLog']) + ';\n')
print(f'[done] {time.time() - T0:.1f}s total', flush=True)
