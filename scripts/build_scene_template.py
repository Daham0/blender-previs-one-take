# -*- coding: utf-8 -*-
"""生成白模场景骨架（悬浮办公模板），可选一键生成环绕轨迹与分层失重动画。

运行：
  blender.exe -b --python build_scene_template.py -- --out "Z:/proj/scene_base.blend" --csv "Z:/proj/coords.csv"
  加 --orbit 1 则同时写入相机环绕轨迹与各物体失重关键帧（逐帧 K，线性插值，杜绝曲线回弹）。

参数：--center cx cy（环绕圆心，默认 0.0 0.15；务必落在主体上）
      --orbit 1  --dur 10  --fps 24
      --a0 186 --a1 300 --r0 3.45 --r1 2.45 --z0 0.78 --z1 1.20 --l0 1.12 --l1 1.54
约定：1 单位 = 1 米，z 轴向上，原点在地面中心。
"""
import sys, os, csv, math

def arg(name, default=None, n=1):
    if "--" not in sys.argv:
        return default
    a = sys.argv[sys.argv.index("--") + 1:]
    if name not in a:
        return default
    i = a.index(name)
    return a[i + 1] if n == 1 else a[i + 1:i + 1 + n]

import bpy
from mathutils import Vector

def box(name, loc, size, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return ob

def sphere(name, loc, r):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    return ob

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.scale_length = 1.0

# ---------------- 场景 ----------------
def build_room(L=6.8, W=6.4, H=2.75, cx=0.0, cy=0.0):
    box("Floor", (cx, cy, 0), (L, W, 0.02))
    box("Ceiling", (cx, cy, H), (L, W, 0.02))
    t = 0.08
    box("Wall_Back",  (cx, cy + W / 2, H / 2), (L, t, H))
    box("Wall_Front", (cx, cy - W / 2, H / 2), (L, t, H))
    box("Wall_Left",  (cx - L / 2, cy, H / 2), (t, W, H))
    box("Wall_Right", (cx + L / 2, cy, H / 2), (t, W, H))
    for i in range(6):
        box("Louvers_%02d" % i, (cx - L / 2 + 0.09, cy + 0.4, 1.0 + i * 0.22), (0.06, 2.4, 0.06))

def build_desk(cx=0.0, cy=0.7, table_h=0.75, w=2.4, d=0.9):
    box("Desk_Top", (cx, cy, table_h), (w, d, 0.06))
    for i, (dx, dy) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
        box("Desk_Leg_%d" % i, (cx + dx * (w / 2 - 0.08), cy + dy * (d / 2 - 0.08), table_h / 2),
            (0.06, 0.06, table_h))
    return Vector((cx, cy, table_h))

def build_screens(desk_center):
    cx, cy, th = desk_center
    box("Monitor_H_Body", (cx - 0.35, cy + 0.12, th + 0.42), (0.62, 0.03, 0.36))
    box("Monitor_V_Body", (cx + 0.32, cy + 0.12, th + 0.45), (0.34, 0.03, 0.60))
    box("Monitor_H_Stand", (cx - 0.35, cy + 0.16, th + 0.20), (0.06, 0.06, 0.20))
    box("Monitor_V_Stand", (cx + 0.32, cy + 0.16, th + 0.20), (0.06, 0.06, 0.20))
    box("PC_Case", (cx - 1.05, cy + 0.1, th + 0.24), (0.22, 0.45, 0.48))
    box("Keyboard", (cx - 0.02, cy - 0.18, th + 0.035), (0.45, 0.15, 0.03))
    box("MousePad", (cx + 0.26, cy - 0.18, th + 0.012), (0.30, 0.24, 0.01))
    box("Mouse", (cx + 0.30, cy - 0.18, th + 0.03), (0.06, 0.10, 0.03))

def build_chair(cx=0.0, cy=-0.55, seat_h=0.455):
    box("Chair_Seat", (cx, cy, seat_h), (0.50, 0.50, 0.09))
    box("Chair_Back", (cx, cy - 0.26, seat_h + 0.34), (0.48, 0.08, 0.55))
    box("Chair_Post", (cx, cy, seat_h / 2), (0.08, 0.08, seat_h))
    box("Chair_Base", (cx, cy, 0.05), (0.55, 0.55, 0.05))

def build_person(cx=0.0, cy=-0.42, seat_h=0.455):
    box("Person_Torso", (cx, cy, seat_h + 0.42), (0.40, 0.24, 0.55))
    sphere("Person_Head", (cx, cy, seat_h + 0.80), 0.13)
    box("Person_Hat", (cx, cy, seat_h + 0.92), (0.26, 0.26, 0.06))
    for s, sx in (("L", -0.24), ("R", 0.24)):
        box("Person_UpperArm_" + s, (cx + sx, cy, seat_h + 0.48), (0.10, 0.10, 0.34))
        box("Person_ForeArm_" + s, (cx + sx * 0.9, cy + 0.22, seat_h + 0.30), (0.09, 0.09, 0.32))
        box("Person_Thigh_" + s, (cx + sx * 0.5, cy + 0.20, seat_h + 0.02), (0.14, 0.44, 0.14))
        box("Person_Shin_" + s, (cx + sx * 0.5, cy + 0.38, seat_h / 2), (0.12, 0.12, seat_h))
        box("Person_Shoe_" + s, (cx + sx * 0.5, cy + 0.44, 0.05), (0.12, 0.24, 0.08))

def build_shelf(cx=1.6, cy=1.6):
    for i in range(3):
        box("Shelf_Board_%d" % i, (cx, cy, 0.6 + i * 0.55), (0.9, 0.32, 0.04))
    for i, dx in enumerate((-0.42, 0.42)):
        box("Shelf_Post_%d" % i, (cx + dx, cy, 0.9), (0.04, 0.30, 1.8))
    for i in range(3):
        sphere("Minion_%d" % (i + 1), (cx - 0.25 + i * 0.25, cy, 0.78), 0.07)
    box("Turntable", (cx + 1.15, cy, 0.95), (0.42, 0.32, 0.14))
    box("Turntable_Cab", (cx + 1.15, cy, 0.42), (0.50, 0.40, 0.84))

def lights_and_cam(target):
    bpy.ops.object.light_add(type="AREA", location=(0, 0, 3.0))
    key = bpy.context.active_object
    key.name = "Key_Light"
    key.data.energy = 400
    key.data.size = 3.0
    bpy.ops.object.camera_add(location=(-3.5, 1.4, 0.9))
    cam = bpy.context.active_object
    cam.name = "Camera"
    cam.data.lens = 20
    d = (Vector(target) - cam.location)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    world = bpy.data.worlds.new("W")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = None
    for n in world.node_tree.nodes:
        if n.type == "BACKGROUND":
            bg = n
            break
    if bg is None:
        bg = world.node_tree.nodes.new("ShaderNodeBackground")
        out = next((n for n in world.node_tree.nodes if n.type == "OUTPUT_WORLD"), None)
        if out is None:
            out = world.node_tree.nodes.new("ShaderNodeOutputWorld")
        world.node_tree.links.new(bg.outputs[0], out.inputs[0])
    bg.inputs[0].default_value = (0.8, 0.8, 0.8, 1)
    bg.inputs[1].default_value = 0.6
    return cam

def export_coords(csv_path):
    rows = []
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        w = ob.matrix_world.translation
        rows.append([ob.name, round(w.x, 3), round(w.y, 3), round(w.z, 3),
                     round(ob.dimensions.x, 3), round(ob.dimensions.y, 3), round(ob.dimensions.z, 3)])
    rows.sort()
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.writer(f)
        wr.writerow(["name", "x", "y", "z", "dim_x", "dim_y", "dim_z"])
        wr.writerows(rows)
    print("[coords] %d objects -> %s" % (len(rows), csv_path))

# ---------------- 动画 ----------------
def ease(u):
    u = max(0.0, min(1.0, u))
    return 2 * u * u if u < 0.5 else 1 - pow(-2 * u + 2, 2) / 2

# 分层失重时序（秒）：前缀 -> (起飞, 到位, 升起高度)
SCHEDULE = [
    ("Minion_", 1.58, 3.46, 0.58),
    ("Monitor_H", 2.46, 4.25, 1.27),
    ("Monitor_V", 2.79, 4.58, 1.12),
    ("PC_Case", 3.29, 5.08, 1.29),
    ("Keyboard", 3.29, 5.08, 1.29),
    ("Mouse", 3.29, 5.08, 1.29),
    ("Person_", 5.46, 9.50, 1.10),
    ("Desk_Top", 5.50, 9.50, 1.18),
    ("Desk_Leg", 5.50, 9.50, 1.18),
    ("Chair_", 7.83, 9.58, 0.85),
]

def linearize(ob):
    ad = ob.animation_data
    if not ad or not ad.action:
        return
    for fc in ad.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"

def keyframe_orbit(cam, center, dur, fps, a0, a1, r0, r1, z0, z1, l0, l1):
    sc = bpy.context.scene
    sc.render.fps = fps
    total = int(round(dur * fps))
    sc.frame_start = 1
    sc.frame_end = total
    cx, cy = center
    for f in range(1, total + 1):
        t = (f - 1) / fps
        u = max(0.0, min(1.0, t / max(1e-6, dur)))
        ang = math.radians(a0 + (a1 - a0) * u)
        rad = r0 + (r1 - r0) * u
        cz = z0 + (z1 - z0) * u
        lz = l0 + (l1 - l0) * u
        loc = Vector((cx + rad * math.cos(ang), cy + rad * math.sin(ang), cz))
        cam.location = loc
        cam.rotation_euler = (Vector((cx, cy, lz)) - loc).to_track_quat("-Z", "Y").to_euler()
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
    linearize(cam)
    print("[orbit] %d frames @ %dfps written" % (total, fps))

def keyframe_movers(dur, fps):
    total = int(round(dur * fps))
    done = 0
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        hit = None
        for pre, s, e, rise in SCHEDULE:
            if ob.name.startswith(pre):
                hit = (s, e, rise)
                break
        if not hit:
            continue
        s, e, rise = hit
        base = ob.location.copy()
        for f in range(1, total + 1):
            t = (f - 1) / fps
            u = max(0.0, min(1.0, (t - s) / max(1e-6, e - s)))
            z = base.z + rise * ease(u)
            ob.location = Vector((base.x, base.y, z))
            if ob.name.startswith("Chair_"):
                bu = max(0.0, min(1.0, (t - (s - 0.6)) / 0.6))
                ob.location.y = base.y - 0.42 * ease(bu)
            ob.keyframe_insert("location", frame=f)
        linearize(ob)
        done += 1
    print("[movers] %d objects keyframed" % done)

def main():
    out = arg("--out", os.path.abspath("scene_base.blend"))
    csvp = arg("--csv", os.path.splitext(out)[0] + "_coords.csv")
    c = arg("--center", None, 2) or ["0.0", "0.15"]
    center = (float(c[0]), float(c[1]))
    do_orbit = str(arg("--orbit", "0")) in ("1", "true", "True", "yes")
    dur = float(arg("--dur", "10"))
    fps = int(arg("--fps", "24"))
    a0 = float(arg("--a0", "186")); a1 = float(arg("--a1", "300"))
    r0 = float(arg("--r0", "3.45")); r1 = float(arg("--r1", "2.45"))
    z0 = float(arg("--z0", "0.78")); z1 = float(arg("--z1", "1.20"))
    l0 = float(arg("--l0", "1.05")); l1 = float(arg("--l1", "1.45"))

    reset()
    build_room()
    desk = build_desk()
    build_screens(desk)
    build_chair()
    build_person()
    build_shelf()
    cam = lights_and_cam((center[0], center[1], l0))
    sc = bpy.context.scene
    sc.render.fps = fps
    sc.frame_start = 1
    sc.frame_end = int(round(dur * fps))

    if do_orbit:
        keyframe_orbit(cam, center, dur, fps, a0, a1, r0, r1, z0, z1, l0, l1)
        keyframe_movers(dur, fps)

    export_coords(csvp)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print("[ok] saved %s" % out)

main()
