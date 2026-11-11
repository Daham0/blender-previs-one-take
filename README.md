# blender-previs-one-take — 一镜到底白模预演与提示词交付

**给它一张参考图，或者给一句描述，它先把运镜搭成 3D 白模跑一遍给你看；一起改到满意，再写详细提示词；最后白模视频 + 提示词一起丢给 Seedance 2.5 出成片。**

长镜头不靠玄学提示词，靠先把相机怎么走算清楚、并且让你亲眼看过确认。

## 怎么用（用户只做三步）

| 步 | 你做什么 | 它做什么 |
|---|---|---|
| 1 | 发一张参考图，或说一句话（"10 秒，从我背后绕到侧前方，桌上东西先飘起来"） | 探测环境、搭同构白模、设计相机轨迹、出第一版白模视频 |
| 2 | 看片，用大白话说"再高点""飞慢点""椅子撞腿了" | 翻译成参数，只改这一项，出新版本视频 |
| 3 | 说"就是这个感觉" | 四项校验锁死，按白模实测运镜写六栏目提示词，交付白模视频 + 提示词 |

## 四件事它自动完成

| | 能力 | 说明 |
|---|---|---|
| Tip 1 | **探测建模** | 有 Blender 直接建高精度场景并导出逐帧实测坐标；没有就引导装便携版（非系统盘、不写注册表、可整体删除）；不想装则用 Three.js 在网页生成白模参考视频 |
| Tip 2 | **自动检查** | 生成视频前跑四项严格校验：极角单调、主体不出画、跨组零穿模、物体不穿顶。穿模卡顿在 3D 里解决，不到视频模型里抽卡 |
| Tip 3 | **先出白模预演** | 先给你能播放的白模视频，有问题随时改，大白话即可，几乎零门槛 |
| Tip 4 | **对着运镜写词** | 按白模实测的机位、半径、仰角、时序写模型能读的运镜提示词——对着真实运动描述，不瞎猜、不跑偏；白模视频带上去做参考，环绕、升空、失重都丝滑，不会突然穿模变形 |

## 产出物

本次任务最终交三样：

1. 白模预演视频（mp4 / webm）——视频模型里的**运动参考**
2. 逐帧实测数据（JSON / CSV）——提示词里每个坐标的出处
3. 六栏目视频提示词——`【Generation Unit】【参考】【连续性】【旁白和声音】【时间轴·带坐标】【反向提示词】`

对接口径：白模视频标注"运动/机位/时序参考，不参考画面"；用户参考图标注"画面唯一参考"；提示词首句强调"严格复刻参考视频的相机运动与起飞顺序"。

## 三条路线

| 情况 | 路线 | 产物 |
|---|---|---|
| 已装 Blender | 分支 A：Blender 白模 + 逐帧实测 | mp4 + JSON + 提示词 |
| 未装、同意安装 | 安装脚本（便携版落非系统盘，镜像自动回退）→ 分支 A | 同上 |
| 未装、拒绝安装 | 分支 B：Three.js 单文件网页白模 | webm + JSON + 提示词 |

三条路线走同一套六阶段流程（接需求 → 探环境 → 首版白模视频 → 迭代 → 校验写词 → 出片交付），差异只在渲染手段。

## 目录

```
SKILL.md                            主流程六阶段、六条铁律、路线决策、执行手册、参数速查、自检状态
README.md                           本文件
references/00-flow-intake-iteration.md  流程总纲：入口、必问项、大白话翻译表、版本管理、Seedance 对接
references/01-scene-spec.md         场景搭建与坐标标定
references/02-camera-motion.md      运镜设计（单向环绕、半径前推、跟随上抬）
references/03-levitation-timing.md  分层失重时序与防穿模规则
references/04-prompt-format.md      提示词六栏目模板与写作技巧（含高频失效对策）
references/05-blender-setup.md      安装引导、连接方式、镜像与便携模式
references/06-threejs-fallback.md   网页白模降级方案与差异说明
references/07-qa-checklist.md       关卡式验收清单 + 实测踩坑库
scripts/check_blender.py            探测本机 Blender（只读）
scripts/install_blender.ps1         便携版安装（镜像自动回退、建 portable、写 BLENDER_PATH）
scripts/build_scene_template.py     生成白模场景 + 可选轨迹与失重动画 + 坐标 CSV
scripts/validate_trajectory.py      四项校验（单调 / 出画 / 穿模 / 穿顶），退出码即结论
scripts/export_cam_data.py          导出逐帧实测 JSON
scripts/render_previs.py            低采样预演渲染 mp4
scripts/threejs_previs.html         单文件网页白模（透视/顶视、导出 JSON、录 webm）
knowledge/kb-levitation-office.md   悬浮办公项目实测参数、时序与自检结果
```

## 快速开始（Blender 分支）

```bash
python scripts/check_blender.py

# 首版白模视频（阶段 ③）：建场景 + 轨迹 + 出片，先给用户看
"$BLENDER" -b --python scripts/build_scene_template.py -- --orbit 1 --out scene.blend --csv coords.csv
"$BLENDER" -b scene.blend --python scripts/render_previs.py -- --out previs_v1.mp4 --start 1 --end 240

# 迭代（阶段 ④）：改参数 → 重跑上面两条 → 出 previs_v2.mp4

# 定稿（阶段 ⑤）：校验必须 PASS，再导出数据写词
"$BLENDER" -b scene.blend --python scripts/validate_trajectory.py -- --center 0.0 0.15 --ceiling 2.75 \
  --keys Person_Head,Person_Torso,Desk_Top,Monitor_H_Body --moving Minion_,Monitor,PC_Case,Keyboard,Mouse,Person_,Desk_,Chair_
"$BLENDER" -b scene.blend --python scripts/export_cam_data.py -- --out cam.json --center 0.0 0.15
```

顺序不能反：**先出片给用户看，再写词。**

## 装到哪

- Agent / Claude 技能目录：整个文件夹放进 skills 目录，`SKILL.md` 为入口。
- 单文件平台（如即梦 Web-Skill）：frontmatter 仅 `name` + `description`，`name` 为纯字母数字连字符，符合规范。

## 依赖

- 分支 A：Blender 4.5 LTS 便携版（不依赖任何第三方插件）。
- 分支 B：现代浏览器 + 联网（CDN 拉 three），无需 Node。

## 磁盘约定

程序与工程落非系统盘；预演中间文件落 temp；最终产物落 output，不写 `C:`。

---

**有了这个一镜到底的 Skill，长运镜稳得可怕。做 AI 视频，还需要花大把时间学那些玄学提示词吗？**
