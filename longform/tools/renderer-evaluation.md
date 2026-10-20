# 长片渲染器评估：Multiplane 与 HyperFrames

核查日期：2026-10-21（北京时间）。这是只读源码、依赖和已有作业日志的评估，没有安装 HyperFrames、没有运行同场景 A/B 测速，也没有改动旧短视频、全局配置或现有依赖。

## 结论

建议长片主渲染继续使用已经验证的 **Multiplane 0.3.13**，以新的 Three/WebGL、Canvas、分层发光、相机与景深场景实现视觉升级。HyperFrames 适合保留为一个小规模、同场景的 A/B 候选；当前没有证据证明迁移本身会提高画质或缩短本机渲染时间。

两者最终都用 Chromium 截取网页画面，因此几何细节、材质、光照、粒子、分辨率、采样和调色才决定主要视觉上限。不能把“Multiplane”理解成只能做平面卡片，也不能把“HyperFrames”理解成自动升级到高精度 3D。该建议不要求降低视觉复杂度、取消动效或把 2160p 主片降为 1080p。

HyperFrames 在多种动画运行时、媒体时间线、多轨混音和编辑生态上更完整；Multiplane 的时间函数、切点保护、局部时间区间渲染及本项目已经通过的确定性流程，更直接匹配当前程序动画长片。

## 核查版本与环境

- 已安装 Multiplane：`node_modules/multiplane/package.json` = `0.3.13`。
- HyperFrames npm 查询：`hyperframes@0.8.181`；源码核查固定于 Git commit `c8f322c25910ed224e29ca5d1a62a521e62544cc`。没有把 main 上的功能宣称为本机已经验证。
- 本机：Apple M1、8 CPU 核、16 GiB 统一内存；现有 Chromium 153.0.8010.12、ANGLE Metal 硬件加速；Node 24.17.0；FFmpeg 7.1。
- 核查时磁盘可用约 42 GiB。5 分钟 30 fps 是 9,000 帧，若保存全片未压缩 RGBA，仅 1080p / 1440p / 2160p 像素就约 69.5 / 123.6 / 278.1 GiB。宜使用流式编码或已编码片段；PNG 的占用取决于内容，不能按固定压缩比保证。

## 关键能力比较

| 需求 | Multiplane 0.3.13 | HyperFrames 0.8.181 / 核查主干 |
| --- | --- | --- |
| 自定义程序 3D | `render(t)` 可驱动任意确定性 WebGL/Three；可选 `multiplane/three` 提供卡片、原生 scene/camera、累积景深 | `hf-seek` 适配 Three，场景由项目拥有；也有 TypeGPU/WebGPU 适配及 GPU 完成等待 |
| Canvas / SVG / 多层 glow | 原生浏览器渲染；Canvas backing resolution 必须匹配 DPR，DOM/SVG/text 自动按 scale 重绘 | 同样可渲染；Three 适配不替项目创建 bloom、材质或景深；它们仍需要作者实现 |
| 真正全帧快门采样 | 内建；线性光平均；声明 `cuts` 后采样不跨硬切；自适应按局部差异增加采样 | 内建 engine `motionBlur`；真实子帧重绘，支持 Canvas/祖先 transform；默认 sRGB 平均，可指定 `blend: "linear"` |
| 快门控制 | `motionBlur`、`maxMotionBlur`、`shutter`、`blurAt(t)`；`shutter=0.5` 相当于 180° | `samplesPerFrame`、`shutterAngle`、`shutterPhase`、`blend`；默认 180° / -90°；未指定采样数时自适应 16 / 32 / 64 |
| 特效与快门兼容 | 页面内部 WebGL/bloom 与最终全帧采样可组合；累积景深有专门采样协作 | 采样仅 screenshot + PNG 路径；支持 SDR streaming/disk/segmented。HDR layered 路径，包括触发此路径的部分 shader transitions，明确拒绝 motionBlur；distributed 配置未暴露该选项 |
| 硬切保护 | 有公开 `cuts` 数组 | 在核查的 `motionBlurSampleTimes` 与捕获接口中未找到对应公开 cuts 参数，不能宣称已有同等级切点夹紧；硬切应专门检验边界帧 |
| 章节局部重渲 | CLI 直接 `--from` / `--to`，结束时间不含在内；可以共享完整时间轴 | CLI 没有 `--from`、`--to`、公开 frame-range；内部 frameRange 用于 distributed chunk。独立章节入口/子 composition 更合适 |
| 长作业恢复 | 约 10 秒编码片段；`status` / `resume`；对已加载资源和环境做兼容检查 | 有真实 `--resume` / `--keep-segments`，必须走分段捕获；并不是只有内存级重试。其限制见下节 |
| 音轨 | 接收一条已经混好的 `--audio` 和 `--audio-offset`；可先用 FFmpeg/Python 完成章节配音、音乐、音效及总线混音 | HTML 中有多个 audio/video clip、时间偏移与增益、效果/包络、音频组等，原生编排更丰富 |
| 当前本机性能证据 | 有真实旧片作业日志 | 没有本机同场景实测，不能宣布比 Multiplane 快或慢 |

HyperFrames 的 `data-hf-motion-blur` registry 组件是 DOM 元素复制叠加，和 engine 的真实全帧子时间采样是两条不同路线；本片 Canvas/3D 应比较后者。其 CLI 当前没有公开 motion-blur/shutter 参数，完整参数需通过 producer 的 `RenderConfig.motionBlur` 使用。

多层 glow 建议在场景本身中建立线性/HDR 工作缓冲、明确 tone mapping、受控 bloom 与局部层合成，再交给渲染器采样。是否输出 HDR 是另一个交付决定；不能把着色器高精度工作缓冲等同于最终视频已经是 HDR。

## 章节与恢复建议

新片独立放在 `longform/`，旧短片入口、脚本和输出保持原样。每章用一个独立场景模块，统一 `renderAt(globalTime)`、固定种子、全局字幕/音乐节拍；章节边界使用明确帧号。这样既能长镜头连续运动，也能只重渲改过的章节。

Multiplane 的实际可用调用：

```bash
cd /Users/yangshuyun/workspace/dev/ai-video/shortvideo-1020
source .tool-env
npx multiplane render longform/shots/landscape.html --from 60 --to 90 --scale 2 --workers 1 --out longform/output/chapter-03-2160p.mp4 --json
npx multiplane status <job-id> --json
npx multiplane resume <job-id> --workers 1 --json
```

上面的 `--scale 2` 仅在入口舞台固定为 1920×1080 时代表 3840×2160；所有 Canvas/WebGL backing buffers 也必须响应该像素倍率。1 worker 是控制峰值内存的候选，不会减少像素、几何细节或采样质量；真正并发数应在代表性重场景上实测。

HyperFrames resume 必须启用 `HF_SEGMENTED_CAPTURE=true`；从首跑就保留片段。其组成哈希来自编译后的 HTML，并不等价于所有同路径资源字节都被冻结。更换字体、纹理、脚本或音频资源后，不能盲目复用旧片段。另外，正常捕获/拼接后的片段清理早于最终 assemble，`--keep-segments` 能避免最终封装失败后片段已被删除。

HyperFrames 如果后续做实际试验，章节与恢复命令应使用真实公开参数；下面只是操作样例，本次没有执行：

```bash
npx hyperframes render --composition chapters/02.html --workers 2 --output renders/02.mp4
HF_SEGMENTED_CAPTURE=true HF_SEGMENT_FRAMES=900 HF_SEGMENT_BROWSER_RECYCLE=3 npx hyperframes render --workers 2 --keep-segments --output renders/final.mp4
HF_SEGMENTED_CAPTURE=true HF_SEGMENT_FRAMES=900 HF_SEGMENT_BROWSER_RECYCLE=3 npx hyperframes render --workers 2 --resume --keep-segments --output renders/final.mp4
```

900 帧在 30 fps 下为 30 秒，是这里选的检查点间隔；默认片段长度是 3000 帧。分段捕获限 MP4/MOV、可 streaming 且不走 HDR/shader-transition 路由。只有 `<template>` 的 nested composition 不能单独作章节入口。分布式 SDK 的 `renderChunkV2(..., {frameRange:{startFrame,endFrame}})` 虽可渲局部帧范围，但要求既有 plan、chunk 范围和环境校验，并要求 software browser GPU，不是本 M1 硬件 3D 渲染的轻量替代。[CLI 参数](https://github.com/heygen-com/hyperframes/blob/c8f322c25910ed224e29ca5d1a62a521e62544cc/packages/cli/src/commands/render.ts)、[分段路由与清理实现](https://github.com/heygen-com/hyperframes/blob/c8f322c25910ed224e29ca5d1a62a521e62544cc/packages/producer/src/services/renderOrchestrator.ts)、[分布式帧范围实现](https://github.com/heygen-com/hyperframes/blob/c8f322c25910ed224e29ca5d1a62a521e62544cc/packages/producer/src/services/distributed/renderChunk.ts)

## 配音与音轨分段

无论用哪个渲染器，都应把旁白按章节/句段保存，记录每段起点、源文件入点、持续时间，再对齐统一音乐与音效时间轴；章节画面重渲不要求重复生成配音。

HyperFrames 的 `data-start` 是 composition 起点秒数，`data-media-start` 是源音频入点，`data-duration` 是片段时间线长度，`data-volume` 是增益。不要把源音频裁切误写成仅 `data-playback-start`。多个 clip 可重叠；`<hf-audio-group>` 与 `data-audio-group` 可建立旁白/音乐/SFX 总线，组内先混 WAV，再应用组 FX 与自动化，最后总混。clip 自动化相对自身起点，group 自动化相对 composition 0 秒，master FX 可以挂根 composition。[音频属性](https://github.com/heygen-com/hyperframes/blob/c8f322c25910ed224e29ca5d1a62a521e62544cc/docs/reference/html-schema.mdx)、[音效与分组](https://github.com/heygen-com/hyperframes/blob/c8f322c25910ed224e29ca5d1a62a521e62544cc/docs/reference/audio-effects.mdx)、[实际 FFmpeg 混音器](https://github.com/heygen-com/hyperframes/blob/c8f322c25910ed224e29ca5d1a62a521e62544cc/packages/engine/src/services/audioMixer.ts)

Multiplane 可继续使用项目自己的 PCM/FFmpeg 混音程序：每句旁白按 manifest 放到绝对时间，音乐与 SFX 保留独立 stems，完成 EQ、ducking、loudness 与 true-peak 核验后生成一个最终 WAV。画面各章无音频渲染，最终统一 mux，避免章节独立有损音频编码造成拼接处延迟或间隙。章节试听可另导出参考 mix。

## 可复用依赖检查

只读遍历了本仓库与 `/Users/yangshuyun/workspace/dev/ai-video` 下可见项目的 package.json 和相关 vendor 文件名。

- 现有两个 Multiplane 0.3.13 包：本仓库及 `proj1-1019/engine/node_modules/multiplane`。
- 没找到可直接复用的 `three`、`simplex-noise`、`glsl-noise`、`glslify`、`regl`、`gsap`、`pixi.js` 已安装包，也没有找到 Three vendor JS。
- Multiplane 的 `src/three/index.js` 和 `licenses/three-LICENSE` 是适配层/许可文件，不能代替实际 Three 库。
- 后续若选内建 Three 层，需要在新片工程局部固定 `three@0.180.0`，与 Multiplane 指定兼容版本一致。本次没有安装。
- 确定性 noise 可以使用固定种子的项目代码或明确版本的依赖；不能用每帧无种子的随机数。

## 5 分钟渲染成本：实测与估计分开

已完成短片的真实记录（30 fps、2 workers、1080p、无累积景深）：

| 已有作业 | 片长 | 渲染耗时 | 平均快门采样 | 进程树采样峰值 |
| --- | ---: | ---: | ---: | ---: |
| `20261020-151943-landscape-116e` | 62 s | 185.459 s | 2.284 | 3.57 GiB |
| `20261020-152801-landscape-1cd2` | 62 s | 273.546 s | 3.095 | 3.59 GiB |
| `20261020-175852-landscape-minimax-dda3` | 62 s | 249.285 s | 3.206 | 3.35 GiB |

这些是旧平面墙场景的实测，不能当作新增高精 3D 的实测；日志也可能包含同期其他作业的资源竞争。

下面全是估计，均按单个画幅、300 秒、30 fps 计算。第二列仅把旧片耗时按时长和像素面积线性外推；第三列是“新复杂场景比旧片再慢 2–6 倍”的规划情景，不是测量结果，也不是承诺或上限。

| 输出分辨率 | 旧场景外推估计 | 高精 3D / 多层 glow 规划情景估计 |
| --- | ---: | ---: |
| 1920×1080 | 15–22 min | 30–132 min |
| 2560×1440 | 27–40 min | 54–240 min |
| 3840×2160 | 60–90 min | 120–540 min |

实际变化不会严格按像素线性增长：浏览器截图固定开销、几何量、透明 overdraw、shader 分支、纹理尺寸、bloom passes、快门采样和累积景深会改变曲线；内存换页和 GPU 争抢可能使耗时超过表格。横竖两版若分别渲染，工作量大致相加；同时跑并不保证更快。

合理做法是保留目标画质，完成真实重场景后渲染 10–12 秒代表段，记录 elapsedMs、blurSamples、dofSamples、GPU 与 peakMemoryBytes，再用实际测得的每帧成本按章节帧数估算。可以使用预览分辨率检查构图，但最终是否 2160p、1440p 或1080p由交付目标决定，不能为省时默默降低。

## 公平 A/B 的最小试验设计

同一份 `setupScene()` / `renderAt(t)` 配两份薄适配入口：一个接 `Shot.define`，另一个接 `hf-seek`。12 秒中包含稳定细节、缓推、快速位移、纵深遮挡/景深、停稳可读字幕。使用相同本地字体与纹理、随机种子、30 fps、同像素尺寸、Metal、180°快门、固定8或16采样及线性混合；先比关键 PNG，再统一编码条件比较视频。不得把 HyperFrames 默认16–64采样和 Multiplane目前2–12采样直接作速度比较。

重点检查：发光边缘色调、细线闪烁、透明叠加、快速移动残影、字幕落定锐度、切点前后帧、异序 seek、断点恢复前后边界、实际峰值内存。只有这样才有依据决定是否切换。

## 官方来源

- [HyperFrames 仓库与总体机制](https://github.com/heygen-com/hyperframes)
- [HyperFrames engine README](https://github.com/heygen-com/hyperframes/blob/c8f322c25910ed224e29ca5d1a62a521e62544cc/packages/engine/README.md)
- [Three 适配与确定性约定](https://github.com/heygen-com/hyperframes/blob/c8f322c25910ed224e29ca5d1a62a521e62544cc/skills/hyperframes-animation/adapters/three.md)
- [TypeGPU/WebGPU 等待与浏览器限制](https://github.com/heygen-com/hyperframes/blob/c8f322c25910ed224e29ca5d1a62a521e62544cc/skills/hyperframes-animation/adapters/typegpu.md)
- [真实快门采样实现](https://github.com/heygen-com/hyperframes/blob/c8f322c25910ed224e29ca5d1a62a521e62544cc/packages/engine/src/services/motionBlur.ts)
- [快门采样可用渲染路径](https://github.com/heygen-com/hyperframes/blob/c8f322c25910ed224e29ca5d1a62a521e62544cc/packages/producer/src/services/render/motionBlurRoute.ts)
- [HyperFrames render CLI 参数](https://github.com/heygen-com/hyperframes/blob/c8f322c25910ed224e29ca5d1a62a521e62544cc/packages/cli/src/commands/render.ts)
- [Multiplane 使用与输出协议](https://github.com/LBEILC/Multiplane/blob/main/docs/protocol.zh-CN.md)

Multiplane 对照另直接读取了已安装 0.3.13 的 `src/post.mjs`、`src/three/index.js`、CLI help 和本仓库 `out/jobs/*/status.json`。上述性能数来自这些既有作业，未新增性能测试。
