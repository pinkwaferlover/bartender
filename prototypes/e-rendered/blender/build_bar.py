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
# --preview menu|honey|dice|bottles: build only that item, render it alone large and in the bar, write
# nothing to img/ or layers.js (pictures go to _work/preview/). --styles a,b limits the bottles built.
ITEM = args[args.index('--preview') + 1] if '--preview' in args else None
STYLES = args[args.index('--styles') + 1].split(',') if '--styles' in args else None
if ITEM: ONLY = 'preview'
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
MENU_W, MENU_H, MENU_T, MENU_R = 1.0, 1.08, 0.028, 0.045   # the board, Blender units: about 30 x 32 cm, 8 mm thick
MENU_SOFT = 8                                              # watts, the menu's own soft light


def _menu_grain(n, L, scale=115.0):
    """Pebbled leather grain: Voronoi cells (object space), their edges cut a touch deeper by a fine noise."""
    tc = n.new('ShaderNodeTexCoord')
    wn = n.new('ShaderNodeTexNoise'); wn.inputs['Scale'].default_value = 40.0; wn.inputs['Detail'].default_value = 3
    L.new(tc.outputs['Object'], wn.inputs['Vector'])
    mx = n.new('ShaderNodeMix'); mx.data_type = 'VECTOR'; mx.inputs['Factor'].default_value = 0.012
    L.new(tc.outputs['Object'], mx.inputs['A']); L.new(wn.outputs['Color'], mx.inputs['B'])
    vo = n.new('ShaderNodeTexVoronoi'); vo.feature = 'F1'; vo.inputs['Scale'].default_value = scale
    vo.inputs['Randomness'].default_value = 0.9
    L.new(mx.outputs['Result'], vo.inputs['Vector'])
    pw = n.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 0.55
    L.new(vo.outputs['Distance'], pw.inputs[0])
    inv = n.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    L.new(pw.outputs[0], inv.inputs[1])
    return inv.outputs[0]          # 1 on the pebble tops, 0 in the creases


def _menu_leather_back():
    """Plain bottle-green leather for the back and edges of the board (no print)."""
    if 'menu_green' in MATS: return MATS['menu_green']
    m = bpy.data.materials.new('menu_green'); m.use_nodes = True; n, L = m.node_tree.nodes, m.node_tree.links
    b = n['Principled BSDF']
    b.inputs['Base Color'].default_value = srgb('#0c5536'); b.inputs['Roughness'].default_value = 0.52
    b.inputs['Sheen Weight'].default_value = 0.12; b.inputs['Sheen Tint'].default_value = srgb('#3f8f68')
    b.inputs['Specular IOR Level'].default_value = 0.3
    g = _menu_grain(n, L)
    bu = n.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = 0.3; bu.inputs['Distance'].default_value = 0.0012
    L.new(g, bu.inputs['Height']); L.new(bu.outputs['Normal'], b.inputs['Normal'])
    MATS['menu_green'] = m
    return m


def _menu_brass():
    """Polished brass for the stand: metallic, a faint brushed grain along its length, uneven polish."""
    if 'gold' in MATS: return MATS['gold']
    m = bpy.data.materials.new('gold'); m.use_nodes = True; n, L = m.node_tree.nodes, m.node_tree.links
    b = n['Principled BSDF']
    b.inputs['Base Color'].default_value = srgb('#d2a048'); b.inputs['Metallic'].default_value = 1.0
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (2, 90, 90)
    L.new(tc.outputs['Object'], mp.inputs[0])
    br = n.new('ShaderNodeTexNoise'); br.inputs['Scale'].default_value = 6.0; br.inputs['Detail'].default_value = 6
    L.new(mp.outputs[0], br.inputs['Vector'])
    sm = n.new('ShaderNodeTexNoise'); sm.inputs['Scale'].default_value = 7.0; sm.inputs['Detail'].default_value = 3
    L.new(tc.outputs['Object'], sm.inputs['Vector'])
    rr = n.new('ShaderNodeMapRange'); rr.inputs['From Min'].default_value = 0.35; rr.inputs['From Max'].default_value = 0.65
    rr.inputs['To Min'].default_value = 0.2; rr.inputs['To Max'].default_value = 0.34
    L.new(sm.outputs['Fac'], rr.inputs['Value']); L.new(rr.outputs['Result'], b.inputs['Roughness'])
    bu = n.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = 0.08; bu.inputs['Distance'].default_value = 0.0005
    L.new(br.outputs['Fac'], bu.inputs['Height']); L.new(bu.outputs['Normal'], b.inputs['Normal'])
    MATS['gold'] = m
    return m


M_GREEN = _menu_leather_back()
M_GOLD = _menu_brass()
M_IVORY = mat('ivory', '#f3ead6', 0.25, coat=0.6)
M_PIP = mat('pip', '#b3172a', 0.3)


def menu_texture():
    """The board's leather face at 2K, drawn with PIL. Two maps, same layout:
    menu_face.png (colour: bottle-green leather, darker and burnished toward the turned edge, tonal stitching,
    gold foil) and menu_data.png (R foil mask -> metallic, G roughness, B height: the foil and the stitch
    channel are debossed into the leather). Foil: a thin and a thick rule round the face, MENU in Bebas Neue,
    a short rule with a lozenge under it, and a bunch of grapes on a vine below."""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import numpy as np
    W = 2048; H = int(round(W * MENU_H / MENU_W)); S = 2; W2, H2 = W * S, H * S
    px = W2 / MENU_W                                       # supersampled pixels per Blender unit
    foil = Image.new('L', (W2, H2), 0); fd = ImageDraw.Draw(foil)
    groove = Image.new('L', (W2, H2), 0); gd = ImageDraw.Draw(groove)
    thread = Image.new('L', (W2, H2), 0); td = ImageDraw.Draw(thread)
    R = MENU_R * px

    def rrect(drw, inset, width, fill=255):
        drw.rounded_rectangle([inset, inset, W2 - 1 - inset, H2 - 1 - inset], radius=max(4, R - inset * 0.55), outline=fill, width=int(width))

    # a creased line just in from the turned edge, then the saddle stitch in its channel
    rrect(gd, 0.010 * px, 0.0028 * px)
    si = 0.024 * px; rrect(gd, si, 0.0055 * px, 150)
    # stitches: walk the inset rounded rectangle and lay short slanted dashes
    rr = max(4, R - si * 0.55); x0, y0, x1, y1 = si, si, W2 - 1 - si, H2 - 1 - si
    path = []
    def seg(ax, ay, bx, by, n):
        for i in range(n): path.append((ax + (bx - ax) * i / n, ay + (by - ay) * i / n))
    def arc(cx, cy, a0, n):
        for i in range(n):
            a = math.radians(a0 + 90 * i / n); path.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    seg(x0 + rr, y0, x1 - rr, y0, 900); arc(x1 - rr, y0 + rr, -90, 60)
    seg(x1, y0 + rr, x1, y1 - rr, 960); arc(x1 - rr, y1 - rr, 0, 60)
    seg(x1 - rr, y1, x0 + rr, y1, 900); arc(x0 + rr, y1 - rr, 90, 60)
    seg(x0, y1 - rr, x0, y0 + rr, 960); arc(x0 + rr, y0 + rr, 180, 60)
    P_ = np.array(path); d = np.r_[0, np.cumsum(np.hypot(*np.diff(P_, axis=0).T))]
    pitch = 0.0105 * px; dash = 0.0072 * px; k = 0
    while k * pitch + dash < d[-1]:
        a = np.interp(k * pitch, d, np.arange(len(P_))); b = np.interp(k * pitch + dash, d, np.arange(len(P_)))
        pa, pb = P_[int(a)], P_[min(int(b), len(P_) - 1)]
        tw = 0.0016 * px                                    # a slight twist: the thread lies at an angle
        td.line([(pa[0] - tw, pa[1] - tw), (pb[0] + tw, pb[1] + tw)], fill=255, width=int(0.0042 * px))
        k += 1
    # foil frame: a thin rule and a thick one
    rrect(fd, 0.052 * px, 0.0032 * px)
    rrect(fd, 0.064 * px, 0.0085 * px)
    # MENU, tracked out, centred a little above the middle
    cx = W2 / 2; cy = 0.40 * H2
    size = 200
    def word_w(f, tr): return sum(f.getlength(ch) for ch in 'MENU') + tr * 3
    while True:
        f = ImageFont.truetype(FONT, size); tr = 0.16 * size
        if word_w(f, tr) > 0.56 * W2: break
        size += 8
    x = cx - word_w(f, tr) / 2
    for ch in 'MENU':
        fd.text((x, cy), ch, font=f, fill=255, anchor='ls'); x += f.getlength(ch) + tr
    capb = f.getbbox('M', anchor='ls'); cap = -capb[1]
    # rules above and below the word, each with a lozenge
    for ry, half in ((cy - cap - 0.075 * H2, 0.17), (cy + 0.07 * H2, 0.24)):
        hw = half * W2; th = 0.0032 * px
        fd.rectangle([cx - hw, ry - th / 2, cx - 0.03 * W2, ry + th / 2], fill=255)
        fd.rectangle([cx + 0.03 * W2, ry - th / 2, cx + hw, ry + th / 2], fill=255)
        z = 0.016 * W2; fd.polygon([(cx - z, ry), (cx, ry - z * 0.7), (cx + z, ry), (cx, ry + z * 0.7)], fill=255)
        for sx in (-1, 1): fd.ellipse([cx + sx * hw - th * 1.6, ry - th * 1.6, cx + sx * hw + th * 1.6, ry + th * 1.6], fill=255)
    # the vine device: a bunch of grapes hanging from a short stem off a vine branch, a big leaf and a
    # small one on the branch, a tendril curling off its end
    gx, gy = cx, 0.705 * H2; gr = 0.023 * W2
    for ri, nrow in enumerate((4, 3, 3, 2, 1)):
        yy = gy + ri * gr * 1.68
        for j in range(nrow):
            xx = gx + (j - (nrow - 1) / 2) * gr * 1.86 + (0.25 * gr if ri % 2 else 0)
            fd.ellipse([xx - gr * 0.8, yy - gr * 0.8, xx + gr * 0.8, yy + gr * 0.8], fill=255)
    lw = int(0.0052 * px)
    def bez(p0, p1, p2, n=40):
        return [((1 - t) ** 2 * p0[0] + 2 * t * (1 - t) * p1[0] + t * t * p2[0],
                 (1 - t) ** 2 * p0[1] + 2 * t * (1 - t) * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]
    by = gy - 2.5 * gr
    branch = bez((gx - 0.15 * W2, by + 0.012 * W2), (gx - 0.02 * W2, by - 0.03 * W2), (gx + 0.13 * W2, by - 0.004 * W2))
    fd.line(branch, fill=255, width=lw, joint='curve')
    fd.line(bez((gx, gy - 0.6 * gr), (gx - 0.004 * W2, by + 0.01 * W2), (gx + 0.004 * W2, by - 0.012 * W2), 20), fill=255, width=int(lw * 0.9), joint='curve')

    def leaf(lx, ly, rad, rot):
        """A five-lobed vine leaf pointing along rot (radians, image space), the stalk notch opposite."""
        pts = []
        for i in range(160):
            t = 2 * math.pi * i / 160
            lobes = 0.64 + 0.36 * (1 - abs(math.sin(2.5 * t))) ** 0.9     # lobed, softly pointed
            notch = 1 - 0.45 * math.exp(-((t - math.pi) / 0.22) ** 2)
            rr_ = rad * lobes * notch * (0.88 + 0.12 * math.cos(t))
            pts.append((lx + rr_ * math.cos(t + rot), ly + rr_ * math.sin(t + rot)))
        fd.polygon(pts, fill=255)
        bx_, by_ = lx + 0.5 * rad * math.cos(rot + math.pi), ly + 0.5 * rad * math.sin(rot + math.pi)
        for a in (-1.26, 0.0, 1.26):                 # veins from the stalk, cut back out of the foil
            fd.line([(bx_, by_), (lx + 0.8 * rad * math.cos(rot + a), ly + 0.8 * rad * math.sin(rot + a))], fill=0, width=max(3, lw // 3))
        return bx_, by_
    sx_, sy_ = leaf(gx - 0.085 * W2, by - 0.058 * W2, 0.058 * W2, math.radians(-110))
    fd.line([(sx_, sy_), (gx - 0.06 * W2, by - 0.012 * W2)], fill=255, width=int(lw * 0.8))
    sx_, sy_ = leaf(gx + 0.065 * W2, by - 0.04 * W2, 0.036 * W2, math.radians(-60))
    fd.line([(sx_, sy_), (gx + 0.05 * W2, by - 0.016 * W2)], fill=255, width=int(lw * 0.7))
    # a tendril: a tightening spiral off the branch's end; a short cut stub at its other end
    ex, ey = branch[-1]; spts = [(ex, ey)]
    for i in range(70):
        t = i / 69; a = math.pi + t * 3.6 * math.pi; rad = 0.026 * W2 * (1 - 0.82 * t)
        spts.append((ex + 0.026 * W2 + rad * math.cos(a), ey - 0.022 * W2 + rad * math.sin(a)))
    fd.line(spts, fill=255, width=int(lw * 0.6), joint='curve')
    fd.line(bez((gx - 0.15 * W2, by + 0.012 * W2), (gx - 0.165 * W2, by + 0.018 * W2), (gx - 0.172 * W2, by + 0.03 * W2), 10), fill=255, width=int(lw * 0.8), joint='curve')

    def down(im, blur=0.0):
        im = im.resize((W, H), Image.LANCZOS)
        return np.asarray(im.filter(ImageFilter.GaussianBlur(blur)) if blur else im).astype(np.float32) / 255
    fm, gm, tm = down(foil), down(groove), down(thread)
    fsoft = down(foil, 2.2)                                  # the stamp's soft shoulder
    # leather: low-frequency mottle, a little darker and more burnished toward the turned edge
    rng = np.random.default_rng(7)
    def lowfreq(n, s):
        a = Image.fromarray((rng.random((n, int(n * H / W))) * 255).astype('uint8')).resize((W, H), Image.BICUBIC)
        return np.asarray(a.filter(ImageFilter.GaussianBlur(s))).astype(np.float32) / 255
    mott = 0.6 * lowfreq(24, 30) + 0.4 * lowfreq(90, 6)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    Rp = MENU_R * W / MENU_W
    qx = np.abs(xx - W / 2) - (W / 2 - Rp); qy = np.abs(yy - H / 2) - (H / 2 - Rp)
    sdf = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - Rp   # <0 inside
    edge = np.clip(1 + sdf / (0.035 * W), 0, 1) ** 2           # 1 at the edge, 0 a few cm in
    green = np.array([0x0c, 0x5e, 0x3c], np.float32) / 255
    lea = green[None, None] * (0.9 + 0.2 * mott[..., None]) * (1 - 0.32 * edge[..., None])
    lea = lea * (1 - 0.35 * gm[..., None])                     # the crease and stitch channel sit darker
    thr = np.array([0x2a, 0x6e, 0x4c], np.float32) / 255
    lea = lea * (1 - tm[..., None]) + thr * tm[..., None] * (0.9 + 0.2 * mott[..., None])
    gold = np.array([0xe8, 0xb2, 0x3e], np.float32) / 255
    gold = gold[None, None] * (0.94 + 0.12 * lowfreq(60, 4)[..., None])
    col = lea * (1 - fm[..., None]) + gold * fm[..., None]
    rough = 0.55 + 0.1 * (mott - 0.5) - 0.12 * edge             # leather; burnished edge
    rough = rough * (1 - tm) + 0.7 * tm
    rough = rough * (1 - fm) + (0.24 + 0.1 * mott) * fm          # foil
    height = 0.75 - 0.55 * fsoft - 0.35 * gm + 0.2 * tm
    data = np.stack([fm, np.clip(rough, 0, 1), np.clip(height, 0, 1)], -1)
    pc = os.path.join(WORK, 'menu_face.png'); pdt = os.path.join(WORK, 'menu_data.png')
    Image.fromarray((np.clip(col, 0, 1) * 255).astype('uint8')).save(pc)
    Image.fromarray((data * 255).astype('uint8')).save(pdt)
    return pc, pdt


def _menu_face_material():
    pc, pdt = menu_texture()
    m = bpy.data.materials.new('menu_face'); m.use_nodes = True; n, L = m.node_tree.nodes, m.node_tree.links
    b = n['Principled BSDF']
    uv = n.new('ShaderNodeTexCoord')
    tc = n.new('ShaderNodeTexImage'); tc.image = bpy.data.images.load(pc); tc.interpolation = 'Cubic'
    td = n.new('ShaderNodeTexImage'); td.image = bpy.data.images.load(pdt); td.image.colorspace_settings.name = 'Non-Color'
    td.interpolation = 'Cubic'
    for t in (tc, td): L.new(uv.outputs['UV'], t.inputs['Vector'])
    sp = n.new('ShaderNodeSeparateColor'); L.new(td.outputs['Color'], sp.inputs[0])
    L.new(tc.outputs['Color'], b.inputs['Base Color'])
    L.new(sp.outputs['Red'], b.inputs['Metallic'])
    L.new(sp.outputs['Green'], b.inputs['Roughness'])
    inv = n.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; L.new(sp.outputs['Red'], inv.inputs[1])
    sh = n.new('ShaderNodeMath'); sh.operation = 'MULTIPLY'; sh.inputs[1].default_value = 0.12; L.new(inv.outputs[0], sh.inputs[0])
    L.new(sh.outputs[0], b.inputs['Sheen Weight']); b.inputs['Sheen Tint'].default_value = srgb('#3f8f68')
    b.inputs['Specular IOR Level'].default_value = 0.3   # leather's sheen stays soft; the key must not grey the green
    # the stamp and the stitch channel (from the map), then the pebble grain, weaker on the foil
    b1 = n.new('ShaderNodeBump'); b1.inputs['Strength'].default_value = 1.0; b1.inputs['Distance'].default_value = 0.0025
    L.new(sp.outputs['Blue'], b1.inputs['Height'])
    g = _menu_grain(n, L)
    gw = n.new('ShaderNodeMath'); gw.operation = 'MULTIPLY_ADD'; gw.inputs[1].default_value = -0.7; gw.inputs[2].default_value = 1.0
    L.new(sp.outputs['Red'], gw.inputs[0])
    gs = n.new('ShaderNodeMath'); gs.operation = 'MULTIPLY'; L.new(g, gs.inputs[0]); L.new(gw.outputs[0], gs.inputs[1])
    b2 = n.new('ShaderNodeBump'); b2.inputs['Strength'].default_value = 0.55; b2.inputs['Distance'].default_value = 0.0012
    L.new(gs.outputs[0], b2.inputs['Height']); L.new(b1.outputs['Normal'], b2.inputs['Normal'])
    L.new(b2.outputs['Normal'], b.inputs['Normal'])
    return m


def _menu_block(name, x0, x1, y0, y1, z0, z1, material, bevel=0.0, segs=3):
    """A box in local Blender units (x across, y depth, z up)."""
    vs = [(x, y, z) for z in (z0, z1) for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    ob = mesh_obj(name, vs, [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], material)
    if bevel: add_bevel(ob, bevel, segs); smooth(ob)
    return ob


def menu():
    """A bar menu on the counter: a leather-covered board (deep bottle-green pebbled leather, stitched round
    its turned edge, gold foil frame, MENU and a vine device stamped into it) leaning back in a polished brass
    stand: a base plate with a front lip the board sits behind, and a strut behind it."""
    Y = -0.75; yb = surface_y(Y)
    o = P(514, yb, 0)
    face_m = _menu_face_material()
    # the board: a rounded rectangle 8 mm thick, edges rounded over by a bevel (the leather turned round)
    bm = bmesh.new(); outline = []
    for cx_, cz_, a0 in ((MENU_W / 2 - MENU_R, MENU_R, -90), (MENU_W / 2 - MENU_R, MENU_H - MENU_R, 0),
                         (-MENU_W / 2 + MENU_R, MENU_H - MENU_R, 90), (-MENU_W / 2 + MENU_R, MENU_R, 180)):
        for i in range(9):
            a = math.radians(a0 + 90 * i / 8); outline.append((cx_ + MENU_R * math.cos(a), cz_ + MENU_R * math.sin(a)))
    fr = [bm.verts.new((x, 0.0, z)) for x, z in outline]
    bk = [bm.verts.new((x, MENU_T, z)) for x, z in outline]
    front = bm.faces.new(list(reversed(fr))); back = bm.faces.new(bk)
    nO = len(outline)
    for i in range(nO):
        j = (i + 1) % nO; bm.faces.new((fr[i], fr[j], bk[j], bk[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    uvl = bm.loops.layers.uv.new()
    for f in bm.faces:
        for lp in f.loops:
            v = lp.vert.co; lp[uvl].uv = ((v.x + MENU_W / 2) / MENU_W, v.z / MENU_H)
    me = bpy.data.meshes.new('menu_board'); bm.to_mesh(me); bm.free()
    board = bpy.data.objects.new('menu_board', me); link(board)
    board.data.materials.append(face_m); board.data.materials.append(M_GREEN)
    for p in board.data.polygons:
        if p.normal.y > 0.5: p.material_index = 1
    bv = add_bevel(board, 0.008, 4); bv.harden_normals = False; smooth(board)
    board.modifiers.new('wn', 'WEIGHTED_NORMAL').keep_sharp = True
    board.rotation_euler = (math.radians(-9), 0, 0)
    board.location = o + Vector((0, -0.045, 0.016))
    # the brass stand: base plate, front lip, a rod strut from the board's back down to the counter
    plate = _menu_block('menu_plate', -0.53, 0.53, -0.078, 0.11, 0.0, 0.016, M_GOLD, 0.006)
    lip = _menu_block('menu_lip', -0.53, 0.53, -0.078, -0.06, 0.0, 0.07, M_GOLD, 0.0075, 4)
    for ob in (plate, lip): ob.location = o
    top = Vector((0, MENU_T * math.cos(math.radians(9)) + 0.58 * math.sin(math.radians(9)) - 0.045 + 0.004, 0.58 + 0.016))
    st = curve_obj('menu_strut', [[tuple(o + top), tuple(o + Vector((0, 0.24, 0.3))), tuple(o + Vector((0, 0.40, 0.01)))]], 0.011, M_GOLD)
    st = _bake_curve(st)
    hinge = _menu_block('menu_hinge', -0.05, 0.05, 0.0, 0.012, -0.04, 0.04, M_GOLD, 0.004)
    hinge.location = o + top + Vector((0, -0.004, 0)); hinge.rotation_euler = (math.radians(-9), 0, 0)
    foot = _menu_block('menu_foot', -0.045, 0.045, 0.37, 0.43, 0.0, 0.01, M_GOLD, 0.004); foot.location = o
    parts = [board, plate, lip, st, hinge, foot]
    group('menu', parts, Y)
    # a soft warm light for the menu alone (light linking), where the foil mirrors it back to the camera:
    # in front, a little above and left of the eye line, so MENU and the frame catch it as a glint
    rc = bpy.data.collections.new('menu_lit')
    for ob in parts: rc.objects.link(ob)
    bpy.context.view_layer.update()
    c0 = board.matrix_world @ Vector((0, 0, MENU_H * 0.5))
    ld = bpy.data.lights.new('menu_soft', 'AREA'); ld.energy = MENU_SOFT; ld.color = srgb('#ffe0ad')[:3]
    ld.shape = 'RECTANGLE'; ld.size = 1.4; ld.size_y = 0.7
    lo = bpy.data.objects.new('menu_soft', ld); link(lo)
    lo.location = c0 + Vector((-0.45, -3.4, 0.75))
    lo.rotation_euler = (c0 - lo.location).to_track_quat('-Z', 'Y').to_euler()
    lo.visible_camera = False
    lo.light_linking.receiver_collection = rc
    return parts


# ---- honey jar: a glass jar of honey with a turned-wood dipper (touchable, true colour)
def _revolve(name, profile, material, segs=64):
    """Revolve (height, radius) about local Z, in order; a point with radius 0 becomes a pole.
    Unlike lathe() this takes a closed outline (outside up, over the lip, inside down), so walls have thickness."""
    bm = bmesh.new(); rings = []
    for h, r in profile:
        if r <= 1e-6: rings.append([bm.verts.new((0, 0, h))]); continue
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), h)) for i in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            if len(a) == 1: bm.faces.new((a[0], b[i], b[j]))
            elif len(b) == 1: bm.faces.new((a[i], b[0], a[j]))
            else: bm.faces.new((a[i], b[i], b[j], a[j]))
    for ring in (rings[0], rings[-1]):
        if len(ring) > 1: bm.faces.new(ring)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); link(ob); ob.data.materials.append(material); smooth(ob)
    return ob


def _bake_curve(ob):
    """A curve as a plain mesh object (curve bounding boxes ignore the bevel; meshes keep bbox_world honest)."""
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    mo = bpy.data.objects.new(ob.name, me); link(mo); mo.matrix_world = ob.matrix_world.copy()
    nm = ob.name; bpy.data.objects.remove(ob, do_unlink=True); mo.name = nm; smooth(mo)
    return mo


def _noise(n, L, scale, detail=4, stretch=None):
    tc = n.new('ShaderNodeTexCoord'); nz = n.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = detail
    if stretch:
        mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = stretch
        L.new(tc.outputs['Object'], mp.inputs[0]); L.new(mp.outputs[0], nz.inputs['Vector'])
    else:
        L.new(tc.outputs['Object'], nz.inputs['Vector'])
    return nz


def _ramp(n, L, src, stops):
    cr = n.new('ShaderNodeValToRGB'); e = cr.color_ramp.elements
    e[0].position, e[0].color = stops[0]; e[1].position, e[1].color = stops[1]
    for pos, col in stops[2:]:
        e.new(pos).color = col
    L.new(src, cr.inputs[0]); return cr


def _shadow_pass(m, tint=(1, 1, 1, 1)):
    """Let shadow rays through a clear material (caustics are off, so glass would otherwise be opaque to light
    and everything inside the jar would sit in the dark). The honey's volume still absorbs along the way."""
    n, L = m.node_tree.nodes, m.node_tree.links
    out = n['Material Output']; b = n['Principled BSDF']
    lp = n.new('ShaderNodeLightPath'); tr = n.new('ShaderNodeBsdfTransparent'); tr.inputs['Color'].default_value = tint
    mx = n.new('ShaderNodeMixShader')
    L.new(lp.outputs['Is Shadow Ray'], mx.inputs[0]); L.new(b.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])


def _hex_cells(n, L, vec, scale):
    """Distance from the centre of the nearest cell of a hexagonal (honeycomb) lattice wrapped round the
    jar: 0 at a cell's centre, about 0.5 on its walls. vec is object space; u runs round the jar."""
    sp = n.new('ShaderNodeSeparateXYZ'); L.new(vec, sp.inputs[0])
    at = n.new('ShaderNodeMath'); at.operation = 'ARCTAN2'; L.new(sp.outputs['Y'], at.inputs[0]); L.new(sp.outputs['X'], at.inputs[1])
    u = n.new('ShaderNodeMath'); u.operation = 'MULTIPLY_ADD'; L.new(at.outputs[0], u.inputs[0])
    u.inputs[1].default_value = round(0.3 * scale * 2 * math.pi) / (2 * math.pi)   # a whole number of cells round
    u.inputs[2].default_value = 100.0
    v = n.new('ShaderNodeMath'); v.operation = 'MULTIPLY_ADD'; L.new(sp.outputs['Z'], v.inputs[0]); v.inputs[1].default_value = scale; v.inputs[2].default_value = 100.0
    cv = n.new('ShaderNodeCombineXYZ'); L.new(u.outputs[0], cv.inputs[0]); L.new(v.outputs[0], cv.inputs[1])
    R = (1.0, math.sqrt(3), 0.0); H = (0.5, math.sqrt(3) / 2, 0.0)
    def wrap(src):
        m = n.new('ShaderNodeVectorMath'); m.operation = 'MODULO'; L.new(src, m.inputs[0]); m.inputs[1].default_value = R
        s_ = n.new('ShaderNodeVectorMath'); s_.operation = 'SUBTRACT'; L.new(m.outputs[0], s_.inputs[0]); s_.inputs[1].default_value = H
        ln = n.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; L.new(s_.outputs[0], ln.inputs[0])
        return ln.outputs['Value']
    sh = n.new('ShaderNodeVectorMath'); sh.operation = 'SUBTRACT'; L.new(cv.outputs[0], sh.inputs[0]); sh.inputs[1].default_value = H
    mn = n.new('ShaderNodeMath'); mn.operation = 'MINIMUM'; L.new(wrap(cv.outputs[0]), mn.inputs[0]); L.new(wrap(sh.outputs[0]), mn.inputs[1])
    return mn.outputs[0]


def honey_materials():
    """Glass, honey and turned wood for the honey jar."""
    if 'hj_glass' in MATS: return MATS['hj_glass'], MATS['hj_honey'], MATS['hj_wood']
    # glass: clear, IOR 1.5, faint smudges in the roughness and a slow wave in the surface (pressed glass)
    g = bpy.data.materials.new('hj_glass'); g.use_nodes = True; n, L = g.node_tree.nodes, g.node_tree.links
    b = n['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.93, 0.96, 0.93, 1)
    b.inputs['Transmission Weight'].default_value = 1.0; b.inputs['IOR'].default_value = 1.5
    b.inputs['Specular IOR Level'].default_value = 0.32   # tames the big key's reflection below clipping
    smudge = _noise(n, L, 9.0, 6)
    rr = _ramp(n, L, smudge.outputs['Fac'], [(0.45, (0.0, 0.0, 0.0, 1)), (0.75, (0.025, 0.025, 0.025, 1))])
    L.new(rr.outputs['Color'], b.inputs['Roughness'])
    wav = _noise(n, L, 3.0, 2); bu = n.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = 0.04
    L.new(wav.outputs['Fac'], bu.inputs['Height'])
    # a band of moulded honeycomb cells round the shoulder (object space: the jar's own height 0..0.65)
    tc = n.new('ShaderNodeTexCoord'); hexd = _hex_cells(n, L, tc.outputs['Object'], 21.0)
    sz = n.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sz.inputs[0])
    band = n.new('ShaderNodeMapRange'); band.interpolation_type = 'SMOOTHSTEP'
    band.inputs['From Min'].default_value = 0.29; band.inputs['From Max'].default_value = 0.33
    L.new(sz.outputs['Z'], band.inputs['Value'])
    band2 = n.new('ShaderNodeMapRange'); band2.interpolation_type = 'SMOOTHSTEP'
    band2.inputs['From Min'].default_value = 0.5; band2.inputs['From Max'].default_value = 0.46
    L.new(sz.outputs['Z'], band2.inputs['Value'])
    mk = n.new('ShaderNodeMath'); mk.operation = 'MULTIPLY'; L.new(band.outputs['Result'], mk.inputs[0]); L.new(band2.outputs['Result'], mk.inputs[1])
    mk2 = n.new('ShaderNodeMath'); mk2.operation = 'MULTIPLY'; mk2.inputs[1].default_value = 0.35; L.new(mk.outputs[0], mk2.inputs[0]); mk = mk2
    cell = n.new('ShaderNodeMapRange'); cell.interpolation_type = 'SMOOTHSTEP'
    cell.inputs['From Min'].default_value = 0.41; cell.inputs['From Max'].default_value = 0.5
    L.new(hexd, cell.inputs['Value'])
    hb = n.new('ShaderNodeBump'); hb.inputs['Distance'].default_value = 0.003
    L.new(mk.outputs[0], hb.inputs['Strength']); L.new(cell.outputs['Result'], hb.inputs['Height'])
    L.new(bu.outputs['Normal'], hb.inputs['Normal']); L.new(hb.outputs['Normal'], b.inputs['Normal'])
    _shadow_pass(g, (0.92, 0.94, 0.9, 1))
    MATS['hj_glass'] = g
    # honey: a clear dielectric (IOR 1.49) coloured by absorption in its volume: gold where thin, deep amber
    # in the core; it glows where the back light passes through it (a scatter volume costs too much here)
    h = bpy.data.materials.new('hj_honey'); h.use_nodes = True; n, L = h.node_tree.nodes, h.node_tree.links
    b = n['Principled BSDF']
    b.inputs['Base Color'].default_value = srgb('#ffe6a8')
    b.inputs['Transmission Weight'].default_value = 1.0; b.inputs['IOR'].default_value = 1.49
    b.inputs['Specular IOR Level'].default_value = 0.38
    # the open top is a touch soft (a skin of honey); sides and drips stay glassy
    geo = n.new('ShaderNodeNewGeometry'); sz = n.new('ShaderNodeSeparateXYZ'); mr = n.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.8; mr.inputs['From Max'].default_value = 0.98
    mr.inputs['To Min'].default_value = 0.02; mr.inputs['To Max'].default_value = 0.22
    L.new(geo.outputs['Normal'], sz.inputs[0]); L.new(sz.outputs['Z'], mr.inputs['Value']); L.new(mr.outputs['Result'], b.inputs['Roughness'])
    ab = n.new('ShaderNodeVolumeAbsorption'); ab.inputs['Color'].default_value = (0.95, 0.78, 0.05, 1)
    ab.inputs['Density'].default_value = 7.0
    L.new(ab.outputs[0], n['Material Output'].inputs['Volume'])
    _shadow_pass(h)
    MATS['hj_honey'] = h
    # turned wood: grain runs along the dipper (local Z), oiled sheen
    w = bpy.data.materials.new('hj_wood'); w.use_nodes = True; n, L = w.node_tree.nodes, w.node_tree.links
    b = n['Principled BSDF']
    grain = _noise(n, L, 6.0, 8, stretch=(14, 14, 0.6))
    col = _ramp(n, L, grain.outputs['Fac'], [(0.3, srgb('#7a4a24')), (0.7, srgb('#c78d55')), (0.5, srgb('#a46a3a'))])
    L.new(col.outputs['Color'], b.inputs['Base Color'])
    rg = _ramp(n, L, grain.outputs['Fac'], [(0.3, (0.62, 0.62, 0.62, 1)), (0.7, (0.42, 0.42, 0.42, 1))])
    L.new(rg.outputs['Color'], b.inputs['Roughness'])
    bu = n.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = 0.15; bu.inputs['Distance'].default_value = 0.002
    L.new(grain.outputs['Fac'], bu.inputs['Height']); L.new(bu.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Specular IOR Level'].default_value = 0.45
    MATS['hj_wood'] = w
    return g, h, w


def honey_jar():
    """New in E (R8): honey comes from a jar he dips into, never from the counter.
    A squat glass jar with a threaded neck and a rolled lip, honey to just under the shoulder, a turned-wood
    dipper resting in it (handle out to the upper left, where the app's dip point is) and a run of honey down
    the outside. Lit by the bar plus two lights linked to the jar only: a tall softbox (window-shaped
    highlights) and a warm back light so the honey glows against the dark wall."""
    Y = -0.85; x = 640; yb = surface_y(Y)
    M_GL, M_HN, M_WD = honey_materials()
    parts = []
    base = P(x, yb, 0)
    # glass: outside up, over the rolled lip, inside down; walls ~0.02, a thick base
    outer = [(0.0, 0.0), (0.0, 0.25), (0.004, 0.275), (0.016, 0.292), (0.04, 0.30), (0.12, 0.304), (0.26, 0.302),
             (0.33, 0.294), (0.39, 0.276), (0.44, 0.25), (0.48, 0.224), (0.505, 0.207), (0.52, 0.200), (0.61, 0.200),
             (0.614, 0.207), (0.624, 0.213), (0.636, 0.211), (0.644, 0.203), (0.646, 0.194)]
    inner = [(0.642, 0.185), (0.63, 0.181), (0.52, 0.181), (0.50, 0.188), (0.475, 0.205), (0.435, 0.232),
             (0.385, 0.258), (0.33, 0.275), (0.26, 0.282), (0.12, 0.283), (0.075, 0.279), (0.058, 0.265), (0.052, 0.24), (0.05, 0.0)]
    glass = _revolve('jar_glass', outer + inner, M_GL, 72); glass.location = base; parts.append(glass)
    # the inside surface is a touch less polished: its concave back wall otherwise mirrors the big key
    # light into one clipped white dot right where the honey meets the glass
    M_GLI = MATS.get('hj_glass_in')
    if not M_GLI:
        M_GLI = M_GL.copy(); M_GLI.name = 'hj_glass_in'; MATS['hj_glass_in'] = M_GLI
        bi = M_GLI.node_tree.nodes['Principled BSDF']
        for l in list(bi.inputs['Roughness'].links): M_GLI.node_tree.links.remove(l)
        bi.inputs['Roughness'].default_value = 0.045; bi.inputs['Specular IOR Level'].default_value = 0.25
    glass.data.materials.append(M_GLI)
    for f in glass.data.polygons:
        if f.index // 72 >= len(outer): f.material_index = 1
    # moulded thread on the neck: 1.6 turns of a raised glass bead, tapered at both ends
    th = []; N = 90
    for i in range(N + 1):
        t = i / N; a = math.radians(-30) + t * 1.6 * 2 * math.pi
        th.append((0.199 * math.cos(a), 0.199 * math.sin(a), 0.535 + t * 0.055))
    thread = curve_obj('jar_thread', [th], 0.0055, M_GL)
    for i, p in enumerate(thread.data.splines[0].points):
        t = i / N; p.radius = max(0.05, min(1.0, t / 0.08, (1 - t) / 0.08))
    thread.location = base; thread = _bake_curve(thread); parts.append(thread)
    # honey: follows the inside wall (a hair inside it) to the fill line, then a meniscus climbing the glass
    hf = 0.355; ins = 0.0015
    rw = 0.275 + (0.258 - 0.275) * (hf + 0.012 - 0.33) / (0.385 - 0.33) - ins
    hon = [(0.05 + ins, 0.0), (0.052 + ins, 0.238), (0.058 + ins, 0.262), (0.075 + ins, 0.276), (0.12, 0.282 - ins),
           (0.26, 0.281 - ins), (0.33, 0.274 - ins), (hf + 0.012, rw), (hf + 0.006, rw - 0.006), (hf + 0.002, rw - 0.02),
           (hf, rw - 0.045), (hf, 0.0)]
    honey = _revolve('jar_honey', hon, M_HN, 72); honey.location = base; parts.append(honey)
    # the dipper: one turned piece. Grooved head (5 rings), thin neck, collar, tapered handle, knob.
    prof = [(-0.088, 0.0), (-0.087, 0.014)]
    for i in range(41):
        t = i / 40; z = -0.085 + t * 0.17
        env = math.sin(math.pi * (0.06 + 0.88 * t)) ** 0.45
        prof.append((z, env * (0.047 + 0.012 * math.cos(2 * math.pi * 5 * t))))
    prof += [(0.09, 0.02), (0.10, 0.016), (0.125, 0.016), (0.13, 0.024), (0.142, 0.025), (0.148, 0.019),
             (0.20, 0.0185), (0.45, 0.0165), (0.56, 0.0175), (0.60, 0.0215), (0.61, 0.0175), (0.625, 0.0215),
             (0.65, 0.029), (0.675, 0.03), (0.698, 0.022), (0.708, 0.008), (0.71, 0.0)]
    dip = _revolve('dipper', prof, M_WD, 32)
    # honey clinging to the lower head, and a strand falling from its tip to the surface
    coat = [(-0.094, 0.0), (-0.092, 0.02)]
    for i in range(25):
        t = i / 24; z = -0.09 + t * 0.12
        env = math.sin(math.pi * (0.04 + 0.6 * t)) ** 0.5
        coat.append((z, env * 0.058 + 0.004 * math.cos(2 * math.pi * 5 * t)))
    coat += [(0.035, 0.03), (0.04, 0.0)]
    hcoat = _revolve('dipper_honey', coat, M_HN, 32); hcoat.parent = dip
    head = Vector((0.065, -0.03, 0.445)); axis = Vector((-0.5, -0.14, 1.0)).normalized()
    dip.rotation_euler = axis.to_track_quat('Z', 'Y').to_euler()
    dip.location = base + head
    tip = head - axis * 0.092
    spts = [tuple(base + tip + Vector((0.004 * math.sin(i), 0, -(tip.z - hf) * i / 8))) for i in range(9)]
    strand = curve_obj('dipper_strand', [spts], 0.006, M_HN)
    for i, p in enumerate(strand.data.splines[0].points): p.radius = [1.3, 0.8, 0.55, 0.45, 0.4, 0.45, 0.6, 1.0, 1.8][i]
    strand = _bake_curve(strand)
    parts += [dip, hcoat, strand]
    # a run of honey from the lip down the outside, front right, ending in a bead on the shoulder
    a = math.radians(-62); ca, sa = math.cos(a), math.sin(a)
    run = [(0.198, 0.647), (0.212, 0.637), (0.219, 0.62), (0.21, 0.6), (0.208, 0.565), (0.209, 0.53), (0.218, 0.505),
           (0.24, 0.48), (0.263, 0.455), (0.283, 0.425), (0.297, 0.395), (0.303, 0.37)]
    drip = curve_obj('jar_drip', [[tuple(base + Vector((rr * ca, rr * sa, hh))) for rr, hh in run]], 0.0075, M_HN)
    for i, p in enumerate(drip.data.splines[0].points): p.radius = [0.9, 1.0, 0.9, 0.8, 0.75, 0.7, 0.7, 0.72, 0.75, 0.85, 1.05, 1.25][i]
    parts.append(_bake_curve(drip))
    group('honeyjar', parts, Y)
    # lights for the jar alone (light linking, so the rest of the bar is untouched): a tall softbox up
    # front-left for window-shaped highlights, and a warm back light behind the jar so the honey glows
    rc = bpy.data.collections.new('honeyjar_lit')
    for o in parts: rc.objects.link(o)
    bpy.context.view_layer.update()
    c0 = glass.matrix_world.translation + Vector((0, 0, 0.3))
    for name, off, energy, colour, sx, sy in (('honey_soft', Vector((-1.6, -2.2, 1.4)), 20, '#ffe2bd', 0.35, 1.1),
                                              ('honey_back', Vector((0.1, 1.2, -0.2)), 42, '#ffb04a', 1.0, 0.22)):
        ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.color = srgb(colour)[:3]
        ld.shape = 'RECTANGLE'; ld.size = sx; ld.size_y = sy
        ob = bpy.data.objects.new(name, ld); link(ob)
        ob.location = c0 + off
        ob.rotation_euler = (c0 - ob.location).to_track_quat('-Z', 'Y').to_euler()
        ob.visible_camera = False
        ob.light_linking.receiver_collection = rc
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


# Dionysus' panther: a real leopard model from Sketchfab (see ../CREDITS.md), CC BY 4.0.
LEOPARD_UID = 'd02a9709556348968fef810684b4e3fa'
MODELS = os.environ.get('BAR_MODELS', os.path.join(WORK, 'models'))   # downloaded models, kept out of git
LEOPARD_GLB = os.path.join(MODELS, f'leopard-{LEOPARD_UID[:8]}.glb')


def fetch_leopard():
    """Download the model once (needs api.sketchfab.com with a token injected by the network, or
    SKETCHFAB_TOKEN set). After that the build runs offline from LEOPARD_GLB."""
    if os.path.exists(LEOPARD_GLB): return LEOPARD_GLB
    import urllib.request
    os.makedirs(os.path.dirname(LEOPARD_GLB), exist_ok=True)
    try:
        req = urllib.request.Request(f'https://api.sketchfab.com/v3/models/{LEOPARD_UID}/download')
        if os.environ.get('SKETCHFAB_TOKEN'): req.add_header('Authorization', 'Token ' + os.environ['SKETCHFAB_TOKEN'])
        url = json.load(urllib.request.urlopen(req, timeout=30))['glb']['url']
        urllib.request.urlretrieve(url, LEOPARD_GLB)
    except Exception as e:
        sys.exit(f'[panther] The leopard model is missing and could not be downloaded ({e}).\n'
                 f'Download "Prowling Leopard 3D Model Free" (glb) from https://sketchfab.com/3d-models/{LEOPARD_UID}\n'
                 f'and save it as {LEOPARD_GLB}')
    return LEOPARD_GLB


def panther():
    """The leopard stands on the counter right of Dionysus, head to the left, looking out at you
    (the model's own three-quarter pose from this side). No lying pose exists among the free models."""
    Y = -0.55; yb = surface_y(Y)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=fetch_leopard())
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    root = next(o for o in new if o.parent is None)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    H = 205 * U                                   # standing height in world units, tail tip included
    k = H / (hi.z - lo.z)
    holder = bpy.data.objects.new('panther_holder', None); link(holder)
    root.parent = holder
    root.location = (-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)   # base centre at the holder's origin
    holder.scale = (k, k, k)
    holder.rotation_euler = (0, 0, math.radians(-12))                  # a little more of his flank
    holder.location = P(1068, yb, 0)
    for o in meshes:
        for m_ in o.data.materials:
            if m_ and m_.node_tree and 'Principled BSDF' in m_.node_tree.nodes:
                m_.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.35
    push(holder, Y)
    return meshes


if ONLY == 'panther':
    T['panther'] = panther()
if ONLY in ('all', 'bg', 'touch'):
    T['menu'] = menu(); T['honey'] = honey_jar(); T['dice'] = dice(); T['panther'] = panther()
if ITEM in ('menu', 'honey', 'dice'):
    T[ITEM] = {'menu': menu, 'honey': honey_jar, 'dice': dice}[ITEM]()


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


def make_bottle(style, colour, fam, x=800):
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
        p.location = P(x, 384, 0)
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
cy.max_bounces = 10; cy.diffuse_bounces = 2; cy.glossy_bounces = 3; cy.transmission_bounces = 10; cy.transparent_max_bounces = 8   # glass needs the transmission bounces
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
def read_layers_js():
    """The committed layers.js, so a partial render (--only touch) keeps the other layers' entries."""
    p = os.path.join(PROTO, 'layers.js')
    if not os.path.exists(p): return {}
    src = open(p, encoding='utf8').read()
    a = src.index('const LAYERS = ') + len('const LAYERS = '); b = src.index(';\nconst RENDER_LOG')
    out = json.loads(src[a:b])
    out['renderLog'] = json.loads(src[src.index('const RENDER_LOG = ') + 19:].rstrip().rstrip(';'))
    return out


MAN = json.load(open(MANIFEST_PATH)) if os.path.exists(MANIFEST_PATH) else read_layers_js()
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

if ONLY == 'preview':
    # Look at it large, alone and in the bar, before it ships. Nothing here is written to img/ or layers.js.
    from PIL import Image
    PV = os.path.join(WORK, 'preview'); os.makedirs(PV, exist_ok=True)
    WORLD_OBJS = [o for o in bpy.data.objects if o.type in ('MESH', 'CURVE', 'META', 'FONT') and o not in ALL_TOUCH]
    if ITEM == 'bottles':
        styles = read_styles()
        if STYLES: styles = [t for t in styles if t[0] in STYLES]
        parts = []
        n = len(styles); step = min(52, 640 / max(n, 1))
        for i, (key, label, colour, fam) in enumerate(styles):
            parts += make_bottle(key, colour, fam, 800 - step * (n - 1) / 2 + i * step)
        ALL_TOUCH = parts
    else:
        parts = T[ITEM]
    reg = bbox_world(parts, 10)
    big = {'menu': 8.0, 'honey': 7.0, 'dice': 14.0, 'bottles': 5.0}[ITEM]
    png = render_region('preview_' + ITEM + '_alone', reg, big, parts, True, 96)
    im = Image.open(png).convert('RGBA'); bgc = Image.new('RGBA', im.size, (38, 27, 21, 255)); bgc.alpha_composite(im)
    bgc.convert('RGB').save(os.path.join(PV, ITEM + '-alone.png'))
    x0, y0, x1, y1 = reg; mx_, my_ = (x0 + x1) / 2, (y0 + y1) / 2; hw, hh = max(x1 - x0, 120), max(y1 - y0, 90)
    ctx = (mx_ - hw * 1.1, my_ - hh * 0.9, mx_ + hw * 1.1, my_ + hh * 0.75)
    png = render_region('preview_' + ITEM + '_bar', ctx, 4.0 if ITEM != 'dice' else 8.0, WORLD_OBJS + list(parts), False, 64)
    Image.open(png).convert('RGB').save(os.path.join(PV, ITEM + '-in-bar.png'))
    print('[preview]', PV, json.dumps(LOG), flush=True)
    sys.exit(0)

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
