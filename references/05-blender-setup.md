# 05 Blender 安装与连接（未安装时的完整引导）

本技能的核心精度来自 Blender：只有它能给出**可导出的逐帧世界坐标**。没装不等于做不了，但要先把选择权交给用户。

## 第一步：探测（只读，不做任何变更）

```bash
python scripts/check_blender.py          # 人读
python scripts/check_blender.py --json   # 机读，供脚本判断
```

探测顺序：环境变量 `BLENDER_PATH` → PATH → 常见安装路径（`D:/Agent/Marvis/blender-*`、`Program Files/Blender Foundation/*`、Steam 版）。

返回 `found=true` 直接进分支 A；`found=false` 才进入安装引导。

## 第二步：把两条路摆给用户（一次只问一个问题）

> 本机没有 Blender。两条路：
> 1）我装便携版 Blender（约 380MB，装到非系统盘，便携模式，不写注册表，可整目录删除）——精度最高，能导出逐帧实测坐标；
> 2）不装，我用 Three.js 在浏览器里生成白模运镜参考（几分钟出结果，坐标精度略低）。
> 选哪个？

用户选 1 → 第三步；选 2 → `references/06-threejs-fallback.md`，其余流程（校验、写词、出片）完全一致。

## 第三步：安装便携版（推荐，落非系统盘）

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_blender.ps1 -DryRun
powershell -ExecutionPolicy Bypass -File scripts/install_blender.ps1 -TargetDir "D:\Agent\Marvis"
```

脚本行为：
1. 解析版本：抓 `release/Blender4.5/` 目录列表取最新 `blender-x.y.z-windows-x64.zip`（不写死版本号）。
2. 自动回退镜像：`download.blender.org` → `mirrors.aliyun.com/blender` → `mirrors.tuna.tsinghua.edu.cn/blender`。
   **实测：官方站部分网络 403，阿里云镜像可取到 4.5.16（约 380MB）。**
3. 下载 → 解压到 `-TargetDir` → 在 `blender.exe` 同级创建空的 `portable` 目录（关键：有它才不往 `%APPDATA%` 写配置，C 盘不涨）。
4. 写入用户环境变量 `BLENDER_PATH`，并后台自检打印版本号。

先跑 `-DryRun` 确认镜像与版本再真装，避免白下 380MB。

## 第四步：连接（"自动连上"的实际含义）

Blender 不需要常驻服务，Agent 通过**命令行后台调用**连接，不依赖 GUI：

```bash
# 版本自检
blender.exe -b --python-expr "import bpy;print('VER:'+bpy.app.version_string)"

# 跑任意脚本（-- 之后是本脚本自己的参数）
blender.exe -b "场景.blend" --python scripts/export_cam_data.py -- --out data.json
```

要点：
- `-b`（background）模式无窗口，适合自动化；每次调用都是独立进程，跑完即退。
- 所有自定义参数必须放在 `--` 之后，否则会被 Blender 自己吞掉。
- 若用户已打开 GUI，**不要**直接抢同一个 .blend 覆盖保存，先复制一份落到 temp 再处理。

## 第五步：环境适配与常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| `check_blender.py` 返回 found=false，但用户说装过 | 便携版没进 PATH | 用 `-json` 看常见路径候选，或让用户给 `blender.exe` 绝对路径并写进 `BLENDER_PATH` |
| 官方下载 403 | 网络对 download.blender.org 不友好 | 脚本自动切阿里云/清华；手工安装也走镜像 |
| 安装后 C 盘涨了几百 MB | 缺 `portable` 目录，配置/缓存写进 %APPDATA% | 在 exe 同级建 `portable` 空目录后重启 Blender |
| `-b` 渲染报 GPU/OpenGL 错误 | 无头环境无显示上下文 | 加 `--python render_previs.py -- --engine WORKBENCH` 走工作台渲染 |
| 脚本中文输出乱码 | Windows 控制台 GBK 与 UTF-8 混用 | 调用侧用 `encoding="utf-8", errors="replace"` 捕获 |
| 用户拒绝安装 | 空间/权限/时间考虑 | 直接转 Three.js 分支，不要在安装上反复劝说 |

## 性能与磁盘约定

- 程序与工程一律落非系统盘（如 `D:\Agent\Marvis\`、项目盘 `Z:\...`），不写 `C:`。
- 预演渲染先 480×270 或 960×540、2–4 采样验证管线，再上正式参数。
- 导出统一 `.blend` + `.csv`（坐标清单）+ `.json`（逐帧相机与物体数据），三件套齐了才算"可复现"。

## 卸载/回滚

删除 `-TargetDir` 下对应版本目录，并清除用户环境变量 `BLENDER_PATH`。因是便携模式，无注册表残留、无系统组件依赖。
