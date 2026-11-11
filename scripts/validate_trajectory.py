# -*- coding: utf-8 -*-
"""四项验收：极角/机位高/半径单调、主体出画(NDC)、组间穿模增量、天花板高度。

运行（务必在已完成相机动画的场景上跑）：
blender.exe -b scene.blend --python validate_trajectory.py -- \
  --center 0.95 1.98 --ceiling 2.75 \
  --keys Person_Head,Person_Torso,Desk_Top,Monitor_H_Body,Chair_Seat \
  --moving Minion_,Monitor,PC_Case,Person_,Desk_Top,Desk_Leg,Chair

说明：
- 穿模检测按对象名首段（下划线前）自动分组，同组内接触不计（椅座与椅柱、桌腿与桌面本来就贴合）。
- 跨组干涉以「首帧基线」为参照，只把重叠深度相对基线增加超过 --tol 的帧判为新增穿模，
  这样"人坐在椅子上"这类设计允许的静态接触不会被误报。
- 退出码：0 全过，1 有问题。
"""
import sys, math
def arg(name, default=None, n=1):
    if "--" not in sys.argv: return default
    a = sys.argv[sys.argv.index("--") + 1:]
    if name not in a: return default
    i = a.index(name)
    return a[i + 1] if n == 1 else a[i + 1:i + 1 + n]

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

cx, cy = arg("--center", None, 2) or ["0", "0"]
cx, cy = float(cx), float(cy)
keys = [k for k in (arg("--keys", "Person_Head,Person_Torso,Desk_Top") or "").split(",") if k]
prefixes = [p for p in (arg("--moving", "") or "").split(",") if p]
ceiling = float(arg("--ceiling", "2.75"))
margin = float(arg("--margin", "0.1"))
tol = float(arg("--tol", "0.05"))
ndc_lo, ndc_hi = 0.02, 0.98

sc = bpy.context.scene
cam = sc.camera
f0, f1 = sc.frame_start, sc.frame_end

def group_of(name):
    return name.split("_")[0]

def world_aabb(ob):
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))

def depth(a, b):
    """三轴重叠的最小值，>0 表示相交，越大越深。"""
    a1, a2 = a; b1, b2 = b
    ox = min(a2.x, b2.x) - max(a1.x, b1.x)
    oy = min(a2.y, b2.y) - max(a1.y, b1.y)
    oz = min(a2.z, b2.z) - max(a1.z, b1.z)
    if ox <= 0 or oy <= 0 or oz <= 0:
        return 0.0
    return min(ox, oy, oz)

findings = {"angle_monotonic": True, "camz_monotonic": True, "rad_monotonic": True,
            "ndc_out_frames": [], "new_collisions": [], "ceiling_violation": [],
            "frames": 0, "ndc_checks": 0}

# --- 轨迹单调性 ---
angs, zs, rs = [], [], []
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    loc = cam.matrix_world.translation
    angs.append(math.degrees(math.atan2(loc.y - cy, loc.x - cx)))
    zs.append(loc.z)
    rs.append(math.hypot(loc.x - cx, loc.y - cy))

def unwrap(a):
    out = [a[0]]
    for v in a[1:]:
        d = v - out[-1]
        while d > 180: d -= 360
        while d < -180: d += 360
        out.append(out[-1] + d)
    return out

def sign_set(seq, eps=1e-6):
    d = [seq[i + 1] - seq[i] for i in range(len(seq) - 1)]
    return set(0 if abs(v) < eps else (1 if v > 0 else -1) for v in d) - {0}

ua = unwrap(angs)
findings["angle_monotonic"] = len(sign_set(ua)) <= 1
findings["camz_monotonic"] = len(sign_set(zs)) <= 1
findings["rad_monotonic"] = len(sign_set(rs)) <= 1
findings["angle_range"] = [round(min(ua), 2), round(max(ua), 2)]
findings["rad_range"] = [round(min(rs), 3), round(max(rs), 3)]
findings["camz_range"] = [round(min(zs), 3), round(max(zs), 3)]

# --- 首帧基线 ---
movers = [o for o in bpy.data.objects if o.type == "MESH" and any(o.name.startswith(p) for p in prefixes)]
pairs = []
for i in range(len(movers)):
    for j in range(i + 1, len(movers)):
        a, b = movers[i], movers[j]
        if group_of(a.name) == group_of(b.name):
            continue
        pairs.append((a.name, b.name))
baseline = {}
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    for n1, n2 in pairs:
        a, b = bpy.data.objects[n1], bpy.data.objects[n2]
        baseline[(n1, n2)] = depth(world_aabb(a), world_aabb(b))
    break

# --- 逐帧检查 ---
prev_pitch = None
pitches = []
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    findings["frames"] = f
    loc = cam.matrix_world.translation
    fwd = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    pitches.append(math.degrees(math.asin(max(-1.0, min(1.0, fwd.z)))))

    for k in keys:
        ob = bpy.data.objects.get(k)
        if not ob: continue
        findings["ndc_checks"] += 1
        co = world_to_camera_view(sc, cam, ob.matrix_world.translation)
        if not (ndc_lo <= co.x <= ndc_hi and ndc_lo <= co.y <= ndc_hi):
            findings["ndc_out_frames"].append([f, k, round(co.x, 3), round(co.y, 3)])

    for ob in movers:
        top = max((ob.matrix_world @ Vector(c)).z for c in ob.bound_box)
        if top > ceiling - margin:
            findings["ceiling_violation"].append([f, ob.name, round(top, 3)])

    for n1, n2 in pairs:
        d = depth(world_aabb(bpy.data.objects[n1]), world_aabb(bpy.data.objects[n2]))
        if d > baseline.get((n1, n2), 0.0) + tol:
            findings["new_collisions"].append([f, n1, n2, round(d, 3)])

findings["pitch_range"] = [round(min(pitches), 2), round(max(pitches), 2)]
pitch_sign = sign_set(pitches, 1e-6)
findings["pitch_crosses_zero"] = (len(pitch_sign) > 1)

ok = (findings["angle_monotonic"] and findings["camz_monotonic"] and findings["rad_monotonic"]
      and not findings["ndc_out_frames"] and not findings["new_collisions"]
      and not findings["ceiling_violation"])

print("=== VALIDATION REPORT ===")
print("frames: %d  (start=%d end=%d)" % (findings["frames"], f0, f1))
print("angle monotonic:", findings["angle_monotonic"], "range:", findings["angle_range"])
print("camz monotonic :", findings["camz_monotonic"], "range:", findings["camz_range"])
print("rad  monotonic :", findings["rad_monotonic"], "range:", findings["rad_range"])
print("pitch range    :", findings["pitch_range"], "crosses zero:", findings["pitch_crosses_zero"])
print("ndc checks     : %d, out of frame: %d" % (findings["ndc_checks"], len(findings["ndc_out_frames"])))
print("new collisions :", len(findings["new_collisions"]))
print("ceiling issues :", len(findings["ceiling_violation"]))
for tag in ("ndc_out_frames", "new_collisions", "ceiling_violation"):
    if findings[tag]:
        print("  %s sample:" % tag, findings[tag][:8])
print("RESULT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
