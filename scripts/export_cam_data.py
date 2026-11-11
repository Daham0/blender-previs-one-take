# -*- coding: utf-8 -*-
"""导出逐帧实测数据 JSON，供写提示词引用。
运行：blender.exe -b scene.blend --python export_cam_data.py -- --out data.json --center 0.95 1.98 [--keys Person_Head,Desk_Top,...]
输出：[{f, cam:[x,y,z], rad, ang, pitch, 各对象:[x,y,z]} ...]
"""
import sys, os, json, math
def arg(name, default=None, n=1):
    if "--" not in sys.argv: return default
    a = sys.argv[sys.argv.index("--") + 1:]
    if name not in a: return default
    i = a.index(name)
    return a[i + 1] if n == 1 else a[i + 1:i + 1 + n]

import bpy
out = arg("--out", os.path.abspath("cam_data.json"))
cx, cy = arg("--center", None, 2) or ["0", "0"]
cx, cy = float(cx), float(cy)
keys = (arg("--keys", "") or "").split(",")
keys = [k for k in keys if k]

sc = bpy.context.scene
cam = sc.camera
rows = []
for f in range(sc.frame_start, sc.frame_end + 1):
    sc.frame_set(f)
    loc = cam.matrix_world.translation
    dx, dy = loc.x - cx, loc.y - cy
    rad = math.hypot(dx, dy)
    ang = math.degrees(math.atan2(dy, dx))
    fwd = cam.matrix_world.to_quaternion() @ __import__("mathutils").Vector((0, 0, -1))
    pitch = math.degrees(math.asin(max(-1, min(1, fwd.z))))
    row = {"f": f, "cam": [round(loc.x, 3), round(loc.y, 3), round(loc.z, 3)],
           "rad": round(rad, 3), "ang": round(ang, 2), "pitch": round(pitch, 2)}
    for k in keys:
        ob = bpy.data.objects.get(k)
        if ob:
            w = ob.matrix_world.translation
            row[k] = [round(w.x, 3), round(w.y, 3), round(w.z, 3)]
    rows.append(row)
open(out, "w", encoding="utf-8").write(json.dumps(rows, ensure_ascii=False, indent=1))
print("[ok] %d frames -> %s" % (len(rows), out))
