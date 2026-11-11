#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探测本机 Blender（只读，不安装）。
用法：python check_blender.py [--json]
输出：JSON {found, path, source, version}
"""
import json, os, sys, glob, subprocess, platform

ENV_KEY = "BLENDER_PATH"

def candidates():
    out = []
    if os.environ.get(ENV_KEY):
        out.append((os.environ[ENV_KEY], ENV_KEY))
    exe = "blender.exe" if platform.system() == "Windows" else "blender"
    for p in os.environ.get("PATH", "").split(os.pathsep):
        c = os.path.join(p, exe)
        if os.path.isfile(c):
            out.append((c, "PATH"))
    patterns = []
    if platform.system() == "Windows":
        patterns += [
            r"D:/Agent/Marvis/blender-*/blender.exe",
            r"D:/Agent/*/blender-*/blender.exe",
            r"D:/Program Files/Blender Foundation/Blender*/blender.exe",
            r"C:/Program Files/Blender Foundation/Blender*/blender.exe",
            r"C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe",
        ]
    else:
        patterns += ["/Applications/Blender.app/Contents/MacOS/Blender", "/usr/bin/blender", "/usr/local/bin/blender"]
    for pat in patterns:
        for c in sorted(glob.glob(pat), reverse=True):
            out.append((c, "common_path"))
    return out

def version_of(path):
    try:
        r = subprocess.run([path, "-b", "--python-expr", "import bpy;print('VER:'+bpy.app.version_string)"],
                           capture_output=True, text=True, timeout=90)
        for line in (r.stdout or "").splitlines():
            if line.startswith("VER:"):
                return line[4:].strip()
    except Exception:
        pass
    return None

def main():
    as_json = "--json" in sys.argv
    for path, src in candidates():
        if os.path.isfile(path):
            info = {"found": True, "path": path.replace("\\", "/"), "source": src, "version": version_of(path)}
            print(json.dumps(info, ensure_ascii=False, indent=2) if as_json else
                  "Blender found: {path} (source={source}, version={version})".format(**info))
            return 0
    info = {"found": False, "path": None, "source": None, "version": None,
            "hint": "未安装。可装便携版到非系统盘，或改用 Three.js 分支。"}
    print(json.dumps(info, ensure_ascii=False, indent=2) if as_json else
          "Blender not found. " + info["hint"])
    return 1

if __name__ == "__main__":
    sys.exit(main())
