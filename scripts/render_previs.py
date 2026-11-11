# -*- coding: utf-8 -*-
"""低采样预演渲染（白模），输出 mp4。
运行：
  blender.exe -b scene.blend --python render_previs.py -- --out "Z:/proj/previs.mp4"
可选：--res 960x540  --samples 4  --fps 24  --start 1  --end 240  --engine EEVEE|WORKBENCH
说明：EEVEE 在无显卡的后台环境可能失败，失败时自动回退 WORKBENCH。
"""
import sys, os
def arg(name, default=None):
    if "--" not in sys.argv: return default
    a = sys.argv[sys.argv.index("--") + 1:]
    return a[a.index(name) + 1] if name in a else default

import bpy

out = arg("--out", os.path.abspath("previs.mp4"))
res = arg("--res", "960x540")
samples = int(arg("--samples", "4"))
fps = int(arg("--fps", "24"))
engine = (arg("--engine", "EEVEE") or "EEVEE").upper()

sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = [int(v) for v in res.lower().split("x")]
sc.render.resolution_percentage = 100
sc.render.fps = fps
if arg("--start"): sc.frame_start = int(arg("--start"))
if arg("--end"):   sc.frame_end = int(arg("--end"))

if engine == "WORKBENCH":
    sc.render.engine = "BLENDER_WORKBENCH"
else:
    for cand in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            sc.render.engine = cand
            break
        except TypeError:
            continue
    try:
        sc.eevee.taa_render_samples = samples
    except Exception:
        pass

sc.render.image_settings.file_format = "FFMPEG"
sc.render.ffmpeg.format = "MPEG4"
sc.render.ffmpeg.codec = "H264"
sc.render.filepath = out
if not sc.camera:
    cams = [o for o in bpy.data.objects if o.type == "CAMERA"]
    if cams:
        sc.camera = cams[0]
print("[render] engine=%s frames=%d-%d -> %s (%dx%d @%dfps)" % (
    sc.render.engine, sc.frame_start, sc.frame_end, out,
    sc.render.resolution_x, sc.render.resolution_y, fps))
bpy.ops.render.render(animation=True)
print("[ok] %s" % out)
