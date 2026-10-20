# 长片制作说明

记录日期：2026-10-21（北京时间）。工作目录：`/Users/yangshuyun/workspace/dev/ai-video/shortvideo-1020`，通过 `ssh yangshuyun@10.10.10.1` 操作。新长片工作集中在 `longform/`。

## 当前范围与状态

长片采用冻结稿 `longform/content/script.json`（`longform-v1`）：35 段，其中 34 段旁白、1 段无旁白标题；共 1,597 个汉字，正文含标点 1,807 字符。保留七章操作、机制及适用边界。文稿估计时长约 6 分 15 秒至 6 分 50 秒，最终片长由实际 MiniMax 语音及留白决定。

**长片制作中，尚不能声称正式整片已渲染、混音完成或通过终验。** 截至本次更新，九章真实语音已到齐，正式 `timeline.json` 已生成，时间轴总长为 400.833 秒（约 6 分 41 秒），157 条字幕来自实际配音对齐。`timeline-status.json` 的 `complete` 为 `true`，`needs_review` 仍为 `true`，需要继续复听对齐提示与审片。估算时间轴、静帧、局部场景预览及音乐样例都不是正式成片。后续状态以正式输出和核验记录为准。

## 视觉与镜头

沿用风格手册已提取的近黑蓝背景、琥珀金主体与少量冷蓝强调，统一墙面纹理、字体层级和留白。七章处在同一面连续的墙上，邻近区域和连接线维持空间关系。相机按内容移动，讲动作和解释重点时停稳；呼吸、触觉、自然观看等段落保留安静的观察时间。

长片通过程序绘制的人体、肺泡、神经路径、纸张、自然分枝与桌面物件承载内容。以层次、材质、光照和受控发光增加空间感；字与图分别组织，字幕保持可读。局部运动可以采用轻微快门模糊，静止文字保持锐利。具体医学图示须遵守 `longform/docs/evidence.md`，不把比喻画成已经证实的疗效或因果。

`longform/shots/biology.js`、`actions.js`、`nature.js` 为当前场景模块；出现这些代码或 QA 图不表示它们已经整合为完成的长片。当前时间轴契约为横版 2560×1440、30 fps；最终画幅、入口尺寸和像素倍率须与实际渲染命令核对，不从计划推断已交付分辨率。

## Multiplane 渲染核心

继续采用本仓库已经安装的 **Multiplane 0.3.13**。完整评估见 `longform/tools/renderer-evaluation.md`：评估读取源码、依赖及旧短片作业日志，没有安装 HyperFrames，也没有完成同场景 A/B 测速。不能宣称另一个引擎更快或自动提高画质。

场景必须能够由确定性时间函数驱动，固定随机种子；字幕边界和章节边界采用整数帧。需要模糊时使用真实子帧采样并保护切点。长片宜先检查代表性重场景，再据实选择 worker 数与局部重渲范围；旧短片的耗时不能当作长片高复杂度场景的实测。

正式时间轴、场景入口和渲染配置就位后，先输出局部审片段，检查字幕、动作命中、停镜锐度、运动残影与边界帧，再进入整片渲染。分辨率与采样质量须记录，不为缩短耗时而默默降级。渲染器支持 `status` 与 `resume`；恢复前仍需确认输入资源与配置一致。

## MiniMax 原速旁白与真实时序

配音方向为 MiniMax 中文温暖女声，延续「温暖闺蜜」的亲近、平静表达；采用网页生成的真实 WAV，按九个有声章节保存：`hook`、`breath`、`cold`、`ear`、`shake`、`paper`、`fractal`、`order`、`closing`。标题章不配音。

源文件位于 `longform/assets/voice/raw/`。原声以 `playback_rate=1` 放入时间轴，不通过加速旁白压缩片长，不自动截断整章。字幕使用冻结台本文字，对齐依据为实际音频的离线 ASR 词时间和静音记录；ASR 差异用于定位复听，不能单凭识别结果断言配音读错。

详细流程见 `longform/docs/timing-pipeline.md`。九章齐备且对齐检查通过后，才产生正式 `longform/content/timeline.json` 和 `captions.json`。`estimated-timeline.json` 与 `estimated-captions.json` 明确标记为估算，不用于冒充正式字幕时序。

从远端仓库根执行：

```sh
# 已到齐的真实章节进行离线识别与对齐
/Users/yangshuyun/workspace/dev/ai-video/proj1-1019/engine/.venv/bin/python longform/scripts/prepare_timeline.py

# 仅重新汇总已存在的有效缓存
.tools/venv/bin/python longform/scripts/prepare_timeline.py --build-only
```

## 原创程序配乐、音效与混音

配乐由 NumPy 原创合成，使用固定种子。**没有使用 Suno 歌曲、录音采样或现成旋律。** 音效也由程序生成，章际声音与具体动作命中分别声明。详见 `longform/docs/music-design.md`。

音乐为 108 BPM、4/4 拍的半拍感，暖和声、拨弦与节制泛音构成主体。八小节主题以 D minor / Dm9 为核心；标题进入明确拍网格，正文按章节改变配器，自然纹理段撤去部分脉冲，片尾回扣主题。标题落点读取真实 `music.title_at`，不强迫语音适配预估的 17 秒。

已生成 30 秒独立音乐样例，并完成内存中的六分钟结构检验与旧短片 MiniMax 语音的混音校准。校准记录不代表长片正式旁白全部生成，更不代表长片总混已经完成。

正式混音目标为活跃语音窗口中人声高于音乐约 10 dB，各章中位值接受范围 8–12 dB；基础 ducking 约 3 dB。目标响度为 -15.5 LUFS，true peak 不高于 -1.7 dBTP，封装 AAC 后复测。声音测量需要结合耳机、手机外放与单声道复听，尤其检查轻声尾字和标题重拍附近。

```sh
# 正式 timeline 确定后生成全片音乐和音效
.tools/venv/bin/python longform/scripts/score.py render --timeline longform/content/timeline.json

# 使用真实 MiniMax 原声生成混音及报告
.tools/venv/bin/python longform/scripts/score.py mix --timeline longform/content/timeline.json
```

混音读取 `audio_segments` 的九条整章语音，避免按字幕段落重复播放同一 WAV。正式输出为 `longform/assets/audio/music.wav`、`sfx.wav`、`narration.wav`、`final-mix.wav`，对应报告位于 `longform/output/`。画面可分章渲染，最终统一封装音轨，减少独立有损音频编码造成的边界问题。

## 审阅资料生成与更新

审阅资料构建入口已就位，从远端仓库根运行：

```sh
.tools/venv/bin/python longform/scripts/build_delivery.py
```

正式 `timeline.json` 已就位，当前已生成真实时序的 SRT / VTT。成片、封面或音轨更新后可重跑此命令，更新 review 资料、章节索引和可用输出链接。它是资料生成入口；只有实际渲染输出及对应核验记录存在，才可把长片状态标为已渲染或可审片。正式交付仍需确认画面全长、音画同步、字幕边界、音量与编码回读。

## 旧短片保留

旧两版 MiniMax v2 短片保留在原路径，可继续审阅：

- 横版：`output/review-landscape-minimax-v2.mp4`
- 竖版：`output/review-portrait-minimax-v2.mp4`

v1 对照版也保持：

- 横版：`output/review-landscape-v1.mp4`
- 竖版：`output/review-portrait-v1.mp4`

保留记录位于 `longform/content/preserved-shortfilms.json`，包含上述四个文件的字节数与 SHA-256。长片输出统一位于 `longform/output/`，不得用这些旧短片文件名覆盖旧版本。旧短片已完成的验证不能代替长片终验。

## 审片文件约定

- 主片：`longform/output/master-landscape.mp4`；轻量替代下载：`longform/output/master-landscape-1080p.mp4`。文件出现才启用播放或下载，不以文件名证明已经终验。
- 正式封面：`longform/output/cover-landscape.png`；`longform/cover.html` 为单独制作的正式封面入口。交付脚本不会覆盖这两个文件。
- `longform/output/cover-landscape.svg` 和 `cover-landscape.html` 只由交付脚本提供代码占位预览，不代替正式主体资产封面。
- 完整台本：`longform/output/fullscript.html`；正式字幕：`narration.srt` / `narration.vtt`。
- 配音生成记录：`longform/output/minimax-proof.jpg` 与 `longform/content/voice-provenance.json`。
- 音频 A/B 可读取 `longform/output/mix-comparison.json` 中的 `variants`，每项含 `label`、相对于 output 的 `path`，可选 `note`。对比样例尚未产生时显示“待生成”。
