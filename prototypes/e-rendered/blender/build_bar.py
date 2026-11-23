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
M_GREEN = mat('menu_green', '#1f5a42', 0.45, coat=0.3)
M_GOLD = mat('gold', '#d8b25a', 0.25, 1.0)
M_HONEY = mat('honey', '#e0951c', 0.12, coat=1.0)
M_JAR = mat('jarlid', '#f0e7d8', 0.7)
M_TWINE = mat('twine', '#a3172a', 0.6)
M_DIPPER = mat('dipper', '#b98552', 0.5)
M_IVORY = mat('ivory', '#f3ead6', 0.25, coat=0.6)
M_PIP = mat('pip', '#b3172a', 0.3)


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
# Each bottle is real glass: a thick shell (outer and inner wall, a heavy base, a punt), a separate
# liquid volume inside it filled to below the shoulder, paper labels that sit on the glass, and a
# closure per Family. Profiles are (height above the base, radius) key points in prototype B's svg
# units (1 unit is about 3 mm on a real bottle); a monotone cubic makes them smooth, so shoulders
# curve into the neck and the lip is a real bead. Family silhouettes keep B's widths and heights.
PROFILES = {
    'whisky': [(0, 21.6), (1.2, 23.2), (4, 23.8), (54, 23.8), (60, 22.6), (65, 18), (69, 11), (72, 8), (75, 7.4),
               (84, 7.2), (84.8, 8.4), (87.6, 8.4), (88.4, 7.4)],
    'gin': [(0, 12.4), (1, 13.7), (3, 14.2), (58, 14.2), (64, 13.4), (69, 10.4), (73, 7.4), (76, 6.2), (85, 6),
            (85.6, 6.8), (88, 6.8)],
    'rum': [(0, 19.4), (1.2, 20.8), (4, 21.2), (44, 21.2), (50, 20), (55, 15), (59, 9), (62, 6), (64, 5.3), (82, 5.1),
            (82.8, 6.3), (86, 6.3), (86.6, 5.6)],
    'tequila': [(0, 16.6), (1, 17.6), (3, 17.8), (20, 17.2), (48, 15.6), (56, 14), (61, 10), (65, 6.6), (68, 5.4),
                (82, 5.2), (82.8, 6.2), (85.6, 6.2), (86.2, 5.5)],
    'vodka': [(0, 10.6), (1, 11.7), (3, 12.1), (52, 12.1), (58, 11.4), (63, 8.6), (67, 5.6), (70, 4.8), (84, 4.6),
              (84.6, 5.4), (87, 5.4)],
    'brandy': [(0, 11.5), (1, 13.2), (4, 17.6), (10, 22.2), (18, 25), (26, 25.2), (34, 23.4), (42, 18.4), (49, 11.5),
               (54, 7), (58, 5.2), (82, 4.9), (82.8, 6), (85.6, 6), (86.2, 5.3)],
    'aperitif': [(0, 14.4), (1.2, 15.8), (4, 16.2), (50, 16.2), (56, 15.4), (62, 11.8), (67, 7.6), (71, 5.2),
                 (85, 4.6), (85.6, 5.4), (88.4, 5.4)],
    'bitters': [(0, 13.4), (1, 14.8), (3, 15.2), (46, 15.2), (52, 14.2), (58, 10), (62, 6), (65, 4.4), (71, 4.2),
                (71.6, 5.2), (74, 5.2)],
    'mixer': [(0, 12.4), (1, 13.7), (3, 14.1), (36, 14.1), (42, 13.4), (50, 10.6), (58, 8), (68, 6.4), (74.6, 6),
              (75.2, 7.2), (77, 7.2), (77.6, 6.4)],
}
BOTTLE_SCALE = {'bitters': 0.78, 'mixer': 0.9}
# a few Styles have their own silhouette inside the Family (same width class and height)
STYLE_PROFILE = {
    'islay scotch': [(0, 20), (1.2, 21.6), (4, 22), (48, 22), (56, 20.5), (63, 15), (68, 9.5), (72, 7.6), (84, 7.3),
                     (84.8, 8.4), (87.6, 8.4), (88.4, 7.4)],
    'irish whiskey': [(0, 18.4), (1.2, 20), (4, 20.4), (50, 20.4), (56, 18.6), (61, 12.5), (65, 7.6), (68, 6.4), (85, 6.2),
                      (85.8, 7.4), (88.6, 7.4), (89.2, 6.6)],
    'rye': [(0, 19.4), (1.2, 21), (4, 21.4), (58, 21.4), (62, 20.4), (66, 15), (69.5, 9), (72, 7.4), (85, 7.2),
            (85.8, 8.2), (88.6, 8.2), (89.2, 7.2)],
}
# per Family: wall, base thickness, punt height, fill line, squareness of the body (0 round .. 1 square,
# fading out over the shoulder between the two heights), glass tint
BOTTLE_FORM = {
    'whisky':   dict(wall=1.1, base=5.0, punt=1.2, fill=50, sq=(0.75, 56, 68), glass='#f6f7f2'),
    'gin':      dict(wall=1.0, base=4.0, punt=0.8, fill=55, sq=(0.55, 60, 72), glass='#e6f2e8'),
    'rum':      dict(wall=1.0, base=4.0, punt=1.0, fill=43, sq=None, glass='#f4f4ee'),
    'tequila':  dict(wall=1.0, base=5.0, punt=0.8, fill=46, sq=None, glass='#f6f7f2'),
    'vodka':    dict(wall=1.0, base=4.0, punt=0.6, fill=50, sq=None, glass='#f6f8f8'),
    'brandy':   dict(wall=1.0, base=3.5, punt=1.6, fill=36, sq=None, glass='#f4f2ea'),
    'aperitif': dict(wall=0.9, base=4.6, punt=3.4, fill=48, sq=None, glass='#f2f4ee'),
    'bitters':  dict(wall=0.9, base=3.0, punt=0.6, fill=44, sq=None, glass='#c88a44'),
    'mixer':    dict(wall=1.0, base=3.0, punt=0.8, fill=62, sq=None, glass='#eef4ee'),
}
# within a Family, a few Styles differ in body, stopper and label, so the shelf is not a row of clones
STYLE_FORM = {'islay scotch': dict(sq=None), 'irish whiskey': dict(sq=(0.3, 56, 68)), 'rye': dict(sq=(0.45, 56, 68)),
              'amaretto': dict(fill=40), 'cherry heering': dict(fill=33)}
STYLE_WOOD = {'rye': '#1a1412', 'islay scotch': '#2a1a10', 'irish whiskey': '#6a4626', 'blended scotch': '#1e1612',
              'amaretto': '#5a3a20', 'cherry heering': '#1a1210'}
STYLE_LAYOUT = {'islay scotch': 'whisky2', 'blended scotch': 'whisky2', 'cherry heering': 'whisky2', 'coffee liqueur': 'whisky2'}
STYLE_GLASS = {'islay scotch': '#d8ecd2', 'london dry gin': '#d6ecdc', 'sweet vermouth': '#eef0e4',
               'ginger beer': '#e2d6b8', 'ginger ale': '#dcecd6'}
# Paper labels per Family: (kind, h0, h1, half-angle in degrees). 'front' is a patch facing the camera,
# 'wrap' goes all round at a fixed radius (bitters' oversized label stands off the shoulder).
LABEL_BAND = {
    'whisky': [('front', 13, 45, 33), ('neck', 75.5, 81, 75)],
    'gin': [('front', 16, 52, 40), ('neck', 77, 82, 70)],
    'rum': [('front', 9, 36, 52)],
    'tequila': [('front', 12, 40, 48)],
    'vodka': [('front', 14, 44, 50)],
    'brandy': [('front', 10, 33, 46), ('neck', 66, 76, 65)],
    'aperitif': [('front', 14, 40, 58), ('neck', 64, 70, 62)],
    'bitters': [('wrap', 4, 55, 180)],
    'mixer': [('front', 14, 32, 64), ('neck', 61, 67, 70)],
}
LABEL_ACCENT = {'gin': '#2f6a52', 'vodka': '#2b3f66', 'rum': '#8a2a1c', 'tequila': '#1f4a3a', 'mixer': '#2f5a7a',
                'aperitif': '#1f3a5a', 'whisky': '#7a2a18', 'brandy': '#5a1a12', 'bitters': '#8a2a14'}
STYLE_ACCENT = {'triple sec': '#c8611c', 'tonic water': '#9a7a2a', 'ginger ale': '#2f5a3a', 'ginger beer': '#7a3a18'}
BOTTLE_SPP = 160          # glass with liquid needs more than the 32 spp the opaque bottles used


def _pchip(xs, ys):
    """Monotone cubic through the key points (no overshoot): a smooth radius for every height."""
    n = len(xs); d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(n - 1)]
    m = [d[0]] + [0.0 if d[i - 1] * d[i] <= 0 else
                  3 * (xs[i + 1] - xs[i - 1]) / ((2 * xs[i + 1] - xs[i] - xs[i - 1]) / d[i - 1] + (xs[i + 1] + xs[i] - 2 * xs[i - 1]) / d[i])
                  for i in range(1, n - 1)] + [d[-1]]

    def f(x):
        x = min(max(x, xs[0]), xs[-1]); i = max(j for j in range(n - 1) if xs[j] <= x) if x < xs[-1] else n - 2
        h = xs[i + 1] - xs[i]; t = (x - xs[i]) / h
        return ((2 * t ** 3 - 3 * t ** 2 + 1) * ys[i] + (t ** 3 - 2 * t ** 2 + t) * h * m[i]
                + (-2 * t ** 3 + 3 * t ** 2) * ys[i + 1] + (t ** 3 - t ** 2) * h * m[i + 1])
    return f


def _heights(h0, h1, keys, step=0.6):
    hs = {round(h0, 4), round(h1, 4)} | {round(k, 4) for k in keys if h0 < k < h1}
    n = max(2, int((h1 - h0) / step)); hs |= {round(h0 + (h1 - h0) * i / n, 4) for i in range(n + 1)}
    return sorted(hs)


def _sq_dir(a, q):
    """Unit direction at angle a on a rounded square (superellipse), q 0 = circle .. 1 = squarish."""
    if q <= 0.001: return math.cos(a), math.sin(a)
    e = 2 / (2 + q * 8); c, s = math.cos(a), math.sin(a)
    return math.copysign(abs(c) ** e, c), math.copysign(abs(s) ** e, s)


def _revolve(name, path, material, sqf, segs=72, a0=0.0, a1=2 * math.pi, uv=None):
    """Revolve a (height, radius) path. sqf(h) gives the squareness. A partial sweep (a0..a1) makes a
    patch with UVs (u along the sweep, v from uv=(h0, h1)); a full sweep is closed."""
    full = abs(a1 - a0 - 2 * math.pi) < 1e-6
    bm = bmesh.new(); rings = []; cols = segs if full else segs + 1
    for h, rr in path:
        q = sqf(h); ring = []
        for i in range(cols):
            a = a0 + (a1 - a0) * i / segs; cx, sy = _sq_dir(a, q)
            ring.append(bm.verts.new((rr * cx, rr * sy, h)))
        rings.append(ring)
    faces = []
    for k, (ra, rb) in enumerate(zip(rings, rings[1:])):
        for i in range(segs):
            j = (i + 1) % cols
            try: faces.append((bm.faces.new((ra[i], ra[j], rb[j], rb[i])), i, k))
            except ValueError: pass
    if uv:
        lay = bm.loops.layers.uv.new(); h0, h1 = uv; bm.verts.index_update(); uvs = {}
        for k, ring in enumerate(rings):   # u by arc length, so a squarish face is not stretched in the middle
            cum = [0.0]
            for va, vb in zip(ring, ring[1:]): cum.append(cum[-1] + (vb.co - va.co).length)
            tot = cum[-1] or 1.0
            for i, v in enumerate(ring): uvs[v.index] = (cum[i] / tot, (path[k][0] - h0) / (h1 - h0))
        for f, i, k in faces:
            for lp in f.loops: lp[lay].uv = uvs[lp.vert.index]
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    if full: bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); link(ob); ob.data.materials.append(material); smooth(ob)
    return ob


def _nodes(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links, m.node_tree.nodes['Principled BSDF']


def _noise(n, L, scale, detail=4, coord='Object'):
    tc = n.new('ShaderNodeTexCoord'); nz = n.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = detail
    L.new(tc.outputs[coord], nz.inputs['Vector']); return nz


def _maprange(n, L, src, a, b):
    mr = n.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = a; mr.inputs['To Max'].default_value = b
    L.new(src, mr.inputs['Value']); return mr.outputs['Result']


def glass_material(tint):
    key = 'glass_' + tint
    if key in MATS: return MATS[key]
    m, n, L, b = _nodes(key)
    b.inputs['Base Color'].default_value = srgb(tint); b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 1.5
    nz = _noise(n, L, 9.0, 6)        # faint smudges: roughness 0.01..0.07
    L.new(_maprange(n, L, nz.outputs['Fac'], 0.0, 0.07), b.inputs['Roughness'])
    MATS[key] = m; return m


def liquid_material(colour, d_ref):
    """Clear liquid surface (IOR 1.36) with a Volume Absorption tuned so that light crossing the bottle's
    full width comes out in the Style's colour: richer in the middle, lighter at the thin edges."""
    key = f'liquid_{colour}'
    if key in MATS: return MATS[key]
    m, n, L, b = _nodes(key)
    b.inputs['Base Color'].default_value = (1, 1, 1, 1); b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.0; b.inputs['IOR'].default_value = 1.36
    c = srgb(colour)[:3]; lum = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    if lum > 0.55: c = [x ** 0.35 for x in c]          # clear spirits and sodas: only a faint tint
    sig = [-math.log(max(x, 0.004)) / d_ref for x in c]; D = max(max(sig), 1e-4)
    va = n.new('ShaderNodeVolumeAbsorption'); va.inputs['Color'].default_value = (*[1 - s / D for s in sig], 1)
    va.inputs['Density'].default_value = D
    L.new(va.outputs[0], n['Material Output'].inputs['Volume'])
    MATS[key] = m; return m


def _darker(h, k):
    c = [int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)]
    return '#%02x%02x%02x' % tuple(int(x * k) for x in c)


def label_texture(fam, aspect):
    """A paper label drawn as masks, no words: R = accent print, G = dark ink, B = gold foil, A = paper."""
    from PIL import Image, ImageDraw
    p = os.path.join(WORK, f'bottle_label_{fam}_{aspect:.2f}.png')
    H = 512; W = max(64, int(H * aspect)); im = Image.new('RGBA', (W, H), (0, 0, 0, 255)); d = ImageDraw.Draw(im)
    R, G, B = (255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255)
    cx, cy = W / 2, H / 2
    def rule(y, w, c, x0=0.08, x1=0.92): d.rectangle([W * x0, y, W * x1, y + w], fill=c)
    if fam == 'whisky':
        d.rectangle([10, 10, W - 11, H - 11], outline=R, width=10); d.rectangle([28, 28, W - 29, H - 29], outline=B, width=4)
        d.rectangle([28, H * 0.62, W - 29, H * 0.8], fill=R)
        d.ellipse([cx - H * 0.2, H * 0.14, cx + H * 0.2, H * 0.52], outline=B, width=8)
        d.polygon([(cx, H * 0.23), (cx + H * 0.07, H * 0.33), (cx, H * 0.43), (cx - H * 0.07, H * 0.33)], fill=B)
        rule(H * 0.86, 5, G, 0.25, 0.75)
    elif fam == 'whisky2':   # a dark field with a foil frame and a pale panel
        d.rectangle([0, 0, W, H], fill=G); d.rectangle([14, 14, W - 15, H - 15], outline=B, width=5)
        d.rectangle([W * 0.16, H * 0.3, W * 0.84, H * 0.66], fill=(0, 0, 0, 255))
        d.rectangle([W * 0.16, H * 0.3, W * 0.84, H * 0.66], outline=R, width=8)
        d.ellipse([cx - H * 0.08, H * 0.08, cx + H * 0.08, H * 0.24], outline=B, width=5)
        rule(H * 0.76, 6, R, 0.3, 0.7); rule(H * 0.84, 4, B, 0.36, 0.64)
    elif fam == 'gin':
        d.rectangle([8, 8, W - 9, H - 9], outline=R, width=6)
        d.polygon([(cx, H * 0.12), (W * 0.86, cy), (cx, H * 0.88), (W * 0.14, cy)], outline=R, width=9)
        d.polygon([(cx, H * 0.22), (W * 0.76, cy), (cx, H * 0.78), (W * 0.24, cy)], fill=R)
        d.ellipse([cx - H * 0.08, cy - H * 0.08, cx + H * 0.08, cy + H * 0.08], fill=B)
        rule(H * 0.05, 4, B); rule(H * 0.94, 4, B)
    elif fam == 'rum':
        d.rectangle([0, 0, W, H * 0.42], fill=R); rule(H * 0.42, 8, B, 0, 1)
        d.ellipse([cx - H * 0.2, H * 0.2, cx + H * 0.2, H * 0.6], fill=(0, 0, 0, 255), outline=B, width=10)
        d.ellipse([cx - H * 0.08, H * 0.32, cx + H * 0.08, H * 0.48], fill=R)
        rule(H * 0.8, 6, G, 0.2, 0.8); rule(H * 0.88, 6, G, 0.3, 0.7)
    elif fam == 'tequila':
        d.rectangle([12, 12, W - 13, H - 13], outline=R, width=18)
        for k in range(16):
            a = 2 * math.pi * k / 16
            d.polygon([(cx, cy * 0.9), (cx + math.cos(a - 0.1) * H * 0.3, cy * 0.9 + math.sin(a - 0.1) * H * 0.3),
                       (cx + math.cos(a + 0.1) * H * 0.3, cy * 0.9 + math.sin(a + 0.1) * H * 0.3)], fill=B)
        d.ellipse([cx - H * 0.13, cy * 0.9 - H * 0.13, cx + H * 0.13, cy * 0.9 + H * 0.13], fill=R)
        rule(H * 0.82, 6, G, 0.2, 0.8)
    elif fam == 'vodka':
        rule(H * 0.1, 4, R, 0.06, 0.94); rule(H * 0.88, 4, R, 0.06, 0.94)
        d.rectangle([0, H * 0.44, W, H * 0.58], fill=R); rule(H * 0.4, 3, B, 0, 1); rule(H * 0.61, 3, B, 0, 1)
        d.ellipse([cx - H * 0.07, H * 0.2, cx + H * 0.07, H * 0.34], outline=G, width=5)
    elif fam == 'brandy':
        d.rectangle([0, 0, W, H], fill=(0, 0, 0, 0))
        d.ellipse([6, 6, W - 7, H - 7], fill=(0, 0, 0, 255), outline=R, width=14)
        d.ellipse([30, 30, W - 31, H - 31], outline=B, width=5)
        d.rectangle([W * 0.12, H * 0.56, W * 0.88, H * 0.7], fill=R)
        d.polygon([(cx, H * 0.16), (cx + H * 0.1, H * 0.3), (cx, H * 0.44), (cx - H * 0.1, H * 0.3)], fill=B)
    elif fam == 'aperitif':
        d.rectangle([0, 0, W, H], outline=B, width=6)
        d.rectangle([0, H * 0.36, W, H * 0.64], fill=R); rule(H * 0.33, 4, G, 0, 1); rule(H * 0.66, 4, G, 0, 1)
        d.ellipse([cx - H * 0.11, H * 0.06, cx + H * 0.11, H * 0.28], outline=B, width=6)
        rule(H * 0.78, 5, G, 0.3, 0.7); rule(H * 0.86, 5, G, 0.38, 0.62)
    elif fam == 'bitters':
        d.rectangle([W * 0.3, 14, W * 0.7, H - 15], outline=R, width=8)
        d.rectangle([W * 0.3 + 18, 32, W * 0.7 - 19, H - 33], outline=G, width=3)
        for k in range(9):
            y = H * 0.18 + k * H * 0.07; rule(y, 4, G, 0.36, 0.64 - (k % 3) * 0.03)
        for x in (0.05, 0.85): d.rectangle([W * x, H * 0.2, W * (x + 0.1), H * 0.8], outline=G, width=3)
        d.ellipse([cx - W * 0.04, H * 0.03, cx + W * 0.04, H * 0.11], fill=B)
    elif fam == 'mixer':
        d.rectangle([0, 0, W, H], fill=R)
        d.ellipse([W * 0.2, H * 0.1, W * 0.8, H * 0.9], fill=(0, 0, 0, 255), outline=B, width=8)
        d.ellipse([cx - H * 0.12, cy - H * 0.12, cx + H * 0.12, cy + H * 0.12], outline=R, width=10)
    else:  # neck labels: a band with a foil rule
        d.rectangle([0, 0, W, H], fill=R); rule(H * 0.18, H * 0.08, B, 0, 1); rule(H * 0.74, H * 0.08, B, 0, 1)
        d.ellipse([cx - H * 0.2, cy - H * 0.2, cx + H * 0.2, cy + H * 0.2], fill=(0, 0, 0, 255))
    im.save(p)
    return p


def label_material(fam, accent, aspect):
    key = f'label_{fam}_{accent}_{aspect:.2f}'
    if key in MATS: return MATS[key]
    m, n, L, b = _nodes(key)
    tex = n.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(label_texture(fam, aspect))
    tex.image.colorspace_settings.name = 'Non-Color'; tex.interpolation = 'Cubic'
    sep = n.new('ShaderNodeSeparateColor'); L.new(tex.outputs['Color'], sep.inputs[0])
    fib = _noise(n, L, 140.0, 8, 'UV')                    # paper fibre: a little colour, roughness, bump
    paper = n.new('ShaderNodeMix'); paper.data_type = 'RGBA'
    paper.inputs['A'].default_value = srgb('#d6cab0'); paper.inputs['B'].default_value = srgb('#c2b394')
    L.new(fib.outputs['Fac'], paper.inputs['Factor'])
    c1 = n.new('ShaderNodeMix'); c1.data_type = 'RGBA'; c1.inputs['B'].default_value = srgb(accent)
    L.new(sep.outputs['Red'], c1.inputs['Factor']); L.new(paper.outputs['Result'], c1.inputs['A'])
    c2 = n.new('ShaderNodeMix'); c2.data_type = 'RGBA'; c2.inputs['B'].default_value = srgb('#1c1512')
    L.new(sep.outputs['Green'], c2.inputs['Factor']); L.new(c1.outputs['Result'], c2.inputs['A'])
    c3 = n.new('ShaderNodeMix'); c3.data_type = 'RGBA'; c3.inputs['B'].default_value = srgb('#c9a44a')
    L.new(sep.outputs['Blue'], c3.inputs['Factor']); L.new(c2.outputs['Result'], c3.inputs['A'])
    L.new(c3.outputs['Result'], b.inputs['Base Color'])
    L.new(sep.outputs['Blue'], b.inputs['Metallic'])
    L.new(_maprange(n, L, sep.outputs['Blue'], 0.72, 0.3), b.inputs['Roughness'])
    add = n.new('ShaderNodeMath'); add.operation = 'MULTIPLY_ADD'; add.inputs[1].default_value = 0.5
    L.new(sep.outputs['Blue'], add.inputs[0]); L.new(fib.outputs['Fac'], add.inputs[2])
    bump = n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.25; bump.inputs['Distance'].default_value = 0.002
    L.new(add.outputs[0], bump.inputs['Height']); L.new(bump.outputs[0], b.inputs['Normal'])
    # paper shape (brandy's oval): the texture's alpha cuts the label out
    tr = n.new('ShaderNodeBsdfTransparent'); mx = n.new('ShaderNodeMixShader')
    L.new(tex.outputs['Alpha'], mx.inputs['Fac']); L.new(tr.outputs[0], mx.inputs[1]); L.new(b.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], n['Material Output'].inputs['Surface'])
    MATS[key] = m; return m


def closure_material(kind, colour):
    key = f'closure_{kind}_{colour}'
    if key in MATS: return MATS[key]
    m, n, L, b = _nodes(key)
    b.inputs['Base Color'].default_value = srgb(colour)
    if kind in ('metal', 'foil', 'crown'):
        b.inputs['Metallic'].default_value = 1.0
        nz = _noise(n, L, 60.0 if kind != 'foil' else 18.0, 6)
        L.new(_maprange(n, L, nz.outputs['Fac'], 0.18, 0.34 if kind != 'foil' else 0.45), b.inputs['Roughness'])
        bump = n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.08 if kind != 'foil' else 0.35
        L.new(nz.outputs['Fac'], bump.inputs['Height']); L.new(bump.outputs[0], b.inputs['Normal'])
    elif kind == 'wood':
        tc = n.new('ShaderNodeTexCoord'); wv = n.new('ShaderNodeTexWave'); wv.wave_type = 'RINGS'
        wv.inputs['Scale'].default_value = 6.0; wv.inputs['Distortion'].default_value = 6.0; wv.inputs['Detail'].default_value = 4
        L.new(tc.outputs['Object'], wv.inputs['Vector'])
        mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'
        mx.inputs['A'].default_value = srgb(colour); mx.inputs['B'].default_value = srgb(_darker(colour, 0.6))
        L.new(wv.outputs['Fac'], mx.inputs['Factor']); L.new(mx.outputs['Result'], b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = 0.42; b.inputs['Coat Weight'].default_value = 0.2
    elif kind == 'cork':
        nz = _noise(n, L, 220.0, 3)
        mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'
        mx.inputs['A'].default_value = srgb('#b48c5c'); mx.inputs['B'].default_value = srgb('#6e5030')
        L.new(nz.outputs['Fac'], mx.inputs['Factor']); L.new(mx.outputs['Result'], b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = 0.85
        bump = n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.5
        L.new(nz.outputs['Fac'], bump.inputs['Height']); L.new(bump.outputs[0], b.inputs['Normal'])
    else:  # plastic
        b.inputs['Roughness'].default_value = 0.38
    MATS[key] = m; return m


def _accent(style, colour, fam):
    if style in STYLE_ACCENT: return STYLE_ACCENT[style]
    c = srgb(colour); lum = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    return colour if 0.015 < lum < 0.5 else (_darker(colour, 1.6) if lum <= 0.015 else LABEL_ACCENT[fam])


_BOTTLE_RIG = {}
_GLOW_CARDS = []


def bottle_rig():
    """Lights that touch only the bottles (Cycles light linking): a tall window-shaped soft box at front
    left for the glint, and two narrow strips behind left and right so the glass edges catch light
    against the dark wall. Created once; each bottle joins the receiver collection."""
    if _BOTTLE_RIG: return _BOTTLE_RIG['coll']
    coll = bpy.data.collections.new('bottle_light_rx')
    base = C + (P(800, 340, 0) - C) * scale_for(SHELF_Y)
    for name, off, rot, energy, sx, sy, col in (
            ('bottle_window', (-2.6, -3.2, 1.3), (math.radians(72), 0, math.radians(-38)), 180, 0.55, 1.5, '#ffe2bd'),
            ('bottle_rim_l', (-1.5, 1.6, 0.25), (math.radians(90), 0, math.radians(-128)), 120, 0.12, 1.6, '#ffd2a0'),
            ('bottle_rim_r', (1.5, 1.6, 0.25), (math.radians(90), 0, math.radians(128)), 120, 0.12, 1.6, '#ffd2a0')):
        ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.color = srgb(col)[:3]
        ld.shape = 'RECTANGLE'; ld.size = sx; ld.size_y = sy
        ob = bpy.data.objects.new(name, ld); link(ob); ob.location = base + Vector(off); ob.rotation_euler = rot
        ob.visible_camera = False
        ob.light_linking.receiver_collection = coll
    _BOTTLE_RIG['coll'] = coll
    return coll


def make_bottle(style, colour, fam, x=800):
    """One Style's bottle, base centre on the shelf at world (x, 384)."""
    for gname, cd_ in list(_GLOW_CARDS):   # a removed bottle's glow card goes with it
        if gname not in bpy.data.objects:
            bpy.data.objects.remove(cd_, do_unlink=True); _GLOW_CARDS.remove((gname, cd_))
    keys = STYLE_PROFILE.get(style) or PROFILES.get(fam, PROFILES['vodka']); F = BOTTLE_FORM.get(fam, BOTTLE_FORM['vodka'])
    s = BOTTLE_SCALE.get(fam, 1.04) * U
    hk, rk = [h for h, _ in keys], [r for _, r in keys]; r_o = _pchip(hk, rk); top = hk[-1]
    F = dict(F, **STYLE_FORM.get(style, {})); sq = F['sq']
    def sqf(h):
        if not sq: return 0.0
        q, a, b = sq; return q if h <= a else (0.0 if h >= b else q * (0.5 + 0.5 * math.cos(math.pi * (h - a) / (b - a))))
    t, base_t, punt = F['wall'], F['base'], F['punt']
    # the inner wall follows the outside minus the wall, but runs straight down the neck past the lip bead
    neck_keys = [r for h, r in keys if h > top - 14]
    def r_i(h):
        lo = min(r_o(hh) for hh in (h - 3, h - 1.5, h, h + 1.5, h + 3)); return max(lo - t, 1.2)
    S = lambda pts: [(h * s, r * s) for h, r in pts]
    R0 = rk[0]
    bottom = [(punt, 0.0), (punt * 0.96, R0 * 0.18), (punt * 0.8, R0 * 0.38), (punt * 0.45, R0 * 0.6), (0.12, R0 * 0.8)]
    outer = [(h, r_o(h)) for h in _heights(0, top, hk)]
    inner = [(h, r_i(h)) for h in reversed(_heights(base_t, top, hk))]
    glass_path = bottom + outer + inner + [(base_t, 0.0)]
    gl = _revolve('bottle_' + style, S(glass_path), glass_material(STYLE_GLASS.get(style, F['glass'])), sqf)
    parts = [gl]
    # liquid: inside the inner wall with a small gap, a flat top with a meniscus at the wall
    g = 0.25; hf = F['fill']; hb = base_t + 0.2
    liq = [(hb, 0.0)] + [(h, r_i(h) - g) for h in _heights(hb, hf, hk)] + [(hf + 0.45, r_i(hf) - g - 0.05),
                                                                              (hf + 0.1, r_i(hf) - g - 0.9), (hf, 0.0)]
    d_ref = 2 * (r_i(hf * 0.5) - g) * s * scale_for(SHELF_Y)
    parts.append(_revolve('liquid_' + style, S(liq), liquid_material(colour, d_ref), sqf))
    # paper labels, on the glass: 0.35 units (about 1 mm) proud of the outer surface at every height
    accent = _accent(style, colour, fam)
    for kind, h0, h1, half in LABEL_BAND.get(fam, []):
        a0, a1 = -math.pi / 2 - math.radians(half), -math.pi / 2 + math.radians(half)
        hs = _heights(h0, h1, hk, 0.5)
        if kind == 'wrap':   # a straight paper tube: stands off the shoulder like Angostura's
            rr = max(r_o(h) for h in hs) + 0.4; path = [(h, rr) for h in hs]; a0, a1 = math.pi / 2, 2.5 * math.pi
        else:
            path = [(h, r_o(h) + 0.35) for h in hs]
        hm = (h0 + h1) / 2; rm = path[len(path) // 2][1]; qm = sqf(hm)   # true width of the paper at mid height
        pts = [_sq_dir(a0 + (a1 - a0) * i / 32, qm) for i in range(33)]
        aspect = sum(math.dist(u_, v_) for u_, v_ in zip(pts, pts[1:])) * rm / (h1 - h0)
        lf = fam if kind != 'neck' else 'neck'
        if kind == 'front' and style in STYLE_LAYOUT: lf = STYLE_LAYOUT[style]
        lb = _revolve(f'label_{kind}_' + style, S(path), label_material(lf, accent, aspect), sqf,
                      segs=48, a0=a0, a1=a1 if kind != 'wrap' else a1 - 1e-4, uv=(h0 * s, h1 * s))
        parts.append(lb)
    # closures
    lip = r_o(top - 1.6)
    if fam in ('whisky', 'brandy', 'rum', 'tequila'):
        wood = STYLE_WOOD.get(style) or {'whisky': '#4a2c18', 'brandy': '#3a1f12', 'rum': '#161210', 'tequila': '#8a6038'}[fam]
        th = {'whisky': 5.5, 'brandy': 6.5, 'rum': 5.0, 'tequila': 9.0}[fam]; wr = lip + {'tequila': 0.6}.get(fam, 1.4)
        parts.append(_revolve('cork_' + style, S([(top - 0.2, 0), (top - 0.2, lip - 1.2), (top + 1.2, lip - 1.0), (top + 1.2, 0)]),
                              closure_material('cork', '#b48c5c'), lambda h: 0.0, 40))
        bt = top + 1.0
        if fam == 'tequila':   # a tall turned stopper
            prof = [(bt, 0), (bt, wr * 0.92), (bt + 0.5, wr), (bt + th * 0.6, wr * 0.86), (bt + th * 0.85, wr * 1.05),
                    (bt + th - 0.5, wr * 0.8), (bt + th, 0)]
        elif fam == 'brandy':  # a mushroom top
            prof = [(bt, 0), (bt, wr * 0.9), (bt + 0.6, wr), (bt + th * 0.55, wr * 1.04), (bt + th * 0.85, wr * 0.86),
                    (bt + th, wr * 0.4), (bt + th, 0)]
        else:
            prof = [(bt, 0), (bt, wr * 0.94), (bt + 0.5, wr), (bt + th - 0.7, wr), (bt + th, wr * 0.9), (bt + th, 0)]
        parts.append(_revolve('stopper_' + style, S(prof), closure_material('wood', wood), lambda h: 0.0, 48))
    elif fam in ('gin', 'vodka'):   # aluminium screw cap with knurling and a perforation ring
        cr = lip + 0.7; h0 = top - 4.2; h1 = top + 6.5
        capcol = {'gin': _darker(accent, 1.0), 'vodka': '#b8b8b4'}[fam] if style != 'triple sec' else '#c8611c'
        path = [(h0, cr - 0.2), (h0 + 0.3, cr), (h0 + 2.2, cr), (h0 + 2.4, cr - 0.25), (h0 + 2.7, cr - 0.25), (h0 + 2.9, cr),
                (h1 - 0.6, cr), (h1, cr - 0.6), (h1, 0)]
        cap = _revolve('cap_' + style, S(path), closure_material('metal', capcol), lambda h: 0.0, 96)
        for v in cap.data.vertices:   # knurl: fine vertical ridges above the ring
            hh = v.co.z / s
            if h0 + 3.2 < hh < h1 - 0.8:
                a = math.atan2(v.co.y, v.co.x); k = 1 + 0.025 * math.cos(48 * a)
                v.co.x *= k; v.co.y *= k
        parts.append(cap)
    elif fam == 'aperitif':   # foil capsule over the neck and lip
        h0 = top - 18; hs = _heights(h0, top, hk, 0.4)
        path = [(h0, r_o(h0) + 0.25)] + [(h, r_o(h) + 0.3) for h in hs] + [(top + 0.4, lip * 0.9), (top + 0.45, 0)]
        foil = {'campari': '#8a1418', 'sweet vermouth': '#3a1a14', 'aperol': '#c8642a', 'amaro nonino': '#b8964a',
                'dry vermouth': '#c9b27a', 'ginger wine': '#2a4a32'}.get(style, '#b8964a')
        parts.append(_revolve('foil_' + style, S(path), closure_material('foil', foil), lambda h: 0.0, 64))
    elif fam == 'bitters':    # plastic dasher cap: a collar, a dome, a small spout
        cr = lip + 0.8; h0 = top - 4; capcol = {'angostura bitters': '#d6a630'}.get(style, '#2a1c16')
        path = [(h0, cr - 0.2), (h0 + 0.3, cr), (top + 3, cr), (top + 4.5, cr * 0.85), (top + 5.6, cr * 0.45),
                (top + 6, 1.5), (top + 8.5, 1.1), (top + 8.8, 0)]
        parts.append(_revolve('dasher_' + style, S(path), closure_material('plastic', capcol), lambda h: 0.0, 48))
    elif fam == 'mixer':      # crown cap with a crimped skirt
        cr = lip + 0.6; h0 = top - 2.2
        capcol = {'tonic water': '#c4a44e', 'soda water': '#b8bcc0', 'ginger ale': '#4a7a4a', 'ginger beer': '#8a4a1c'}.get(style, '#b8bcc0')
        path = [(h0, cr + 0.5), (h0 + 0.4, cr + 0.6), (top + 0.6, cr + 0.1), (top + 1.2, cr - 0.3), (top + 1.3, 0)]
        cap = _revolve('crown_' + style, S(path), closure_material('crown', capcol), lambda h: 0.0, 84)
        for v in cap.data.vertices:
            hh = v.co.z / s
            if hh < top + 0.7:
                a = math.atan2(v.co.y, v.co.x); k = 1 + 0.06 * max(0, math.cos(21 * a)) * (top + 0.7 - hh) / 2.9
                v.co.x *= k; v.co.y *= k
        parts.append(cap)
    # a little turn so the labels are not all square to the camera
    turn = math.radians(((sum(map(ord, style)) * 37) % 13 - 6) * 0.9)
    coll = bottle_rig()
    for p in parts:
        p.location = P(x, 384, 0); p.rotation_euler = (0, 0, turn)
        push(p, SHELF_Y); coll.objects.link(p)
    # behind the liquid only, an emitting card that is seen through the glass and nothing else: the
    # backlight a lit back bar gives, so the liquid shows its colour on the dark wall
    c = srgb(colour); lum = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    cw, ch = r_o(hf * 0.5) * 2.6 * s, (hf - 4.5 - base_t) * s
    card = mesh_obj('glow_' + style, [(-cw / 2, 0, 0), (cw / 2, 0, 0), (cw / 2, 0, ch), (-cw / 2, 0, ch)], [(0, 1, 2, 3)],
                    glow_material(0.2 + 1.15 * (1 - min(lum / 0.6, 1)) ** 1.5))
    card.location = P(x, 384, 0) + Vector((0, r_o(hf * 0.5) * s * 1.7, base_t * s))
    for a in ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_shadow', 'visible_volume_scatter'):
        setattr(card, a, False)
    push(card, SHELF_Y)
    _GLOW_CARDS.append((gl.name, card))   # not in parts: set_visible would show it to the camera
    return parts


def glow_material(strength):
    key = f'bottle_glow_{strength:.2f}'
    if key in MATS: return MATS[key]
    m = bpy.data.materials.new(key); m.use_nodes = True; n = m.node_tree.nodes; L = m.node_tree.links
    n.remove(n['Principled BSDF']); em = n.new('ShaderNodeEmission'); em.inputs['Color'].default_value = srgb('#ffe6c4')
    em.inputs['Strength'].default_value = strength
    L.new(em.outputs[0], n['Material Output'].inputs['Surface'])
    MATS[key] = m; return m


def read_styles():
    """Bottle Styles from the shared recipe data (prototype B's data.js), so the art tracks the data."""
    import re
    src = open(os.path.join(PROTO, 'data.js'), encoding='utf8').read()
    out = []
    for k, label, kind, colour, shape in re.findall(r"'([^']+)':\['([^']+)','(\w+)','(#[0-9a-fA-F]{6})','(\w+)'\]", src):
        if kind in ('spirit', 'wine', 'liqueur', 'bitters', 'mixer'):
            out.append((k, label, colour, shape))
    return out


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
        png = render_region('b_' + key.replace(' ', '_'), reg, 2.6, parts, True, BOTTLE_SPP)
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
