# 长片制作记录

远端仓库：`/Users/yangshuyun/workspace/dev/ai-video/shortvideo-1020`，SSH 用户与主机：`yangshuyun@10.10.10.1`。本次新增工程与交付均在 `longform/`。

## 已完成交付

长版 **400.833333 秒（6 分 40 秒 25 帧）**，共 **12025 帧**。主片为 2560×1440 / 30 fps，另提供 1920×1080 播放版。H.264、yuv420p、48 kHz 双声道 AAC 320 kbps；全片画面与音频已完整解码检查，帧数、时间戳和章节衔接通过。

- `output/review.html`：审片页，含章节跳转、完整台本、字幕和声音试听。
- `output/master-landscape.mp4`：1440p 主片。
- `output/master-landscape-1080p.mp4`：1080p 播放版。
- `output/cover-landscape.png`：2560×1440 封面；源码 `cover.html`。
- `output/narration.srt`、`output/narration.vtt`：157 条正式字幕。
- `content/publish-copy.md`：标题与发布文案。
- `docs/evidence.md`：事实核验和来源。

## 内容与视觉

35 段台本包含 34 段旁白及一个独立标题，约 1597 个汉字。七种方法均讲到具体操作、机制解释和证据边界；对原稿中证据过强的表述作了校正。台本见 `content/script.json`。

使用风格手册的近黑蓝背景、琥珀金和少量冷蓝，在统一暗色空间中展示人体与微观结构。镜头以停稳为主，由呼吸、粒子、折纸、叶脉生长和物件归位推进节奏。脑部沟回、肺泡毛细血管、耳部浮雕、纸张网格及桌面材质均由代码绘制；场景模块为 `shots/biology.js`、`actions.js`、`nature.js`，统一合成为 `shots/master.js`。

画面逻辑尺寸 1920×1080，以 4/3 倍输出 1440p；正文字幕为逻辑 46px。静止段采用单样本，快速动作与转场采用三次真实子帧采样；字幕切点前后一帧保护，保持文字锐利。

## 渲染与复现

渲染核心 **Multiplane 0.3.13**，M1 Metal 图形加速，2 workers、standard 质量、x264 编码。比较样例中 2 workers 快于 4 workers，因此采用 2 workers。十个分章范围覆盖全片并包含章间留白，按整数帧拼接。输入指纹与输出 SHA 校验保证续跑文件属于同一版本。

从远端仓库根执行：

```sh
source .tool-env
.tools/venv/bin/python longform/scripts/build_render_data.py --timeline longform/content/timeline.json --captions longform/content/captions.json
.tools/venv/bin/python longform/scripts/score.py render --timeline longform/content/timeline.json
.tools/venv/bin/python longform/scripts/score.py mix --timeline longform/content/timeline.json
.tools/venv/bin/python longform/scripts/render_film.py --resume --raster gpu --delivery-1080
.tools/venv/bin/python longform/scripts/finish_delivery.py
.tools/venv/bin/python longform/scripts/build_delivery.py --require-actual
```

审片服务器支持 HTTP 字节范围读取，浏览器可直接跳转章节。在本机建立转发：

```sh
ssh -L 18878:127.0.0.1:18878 yangshuyun@10.10.10.1 'cd /Users/yangshuyun/workspace/dev/ai-video/shortvideo-1020 && .tools/venv/bin/python longform/scripts/serve_review.py'
```

然后打开 `http://127.0.0.1:18878/longform/output/review.html`。

详细选项见 `docs/render-pipeline.md`。HyperFrames 的源码比较记录在 `tools/renderer-evaluation.md`；本片实际使用 Multiplane。

## 配音、配乐与混音

配音使用 Chrome 中的 MiniMax Audio 网页，模型 `speech-2.8-hd`，音色「温暖闺蜜」。九个原始 WAV 共 371.476813 秒，按原速摆位。生成记录为 `output/minimax-proof.jpg` 与 `content/voice-provenance.json`；原文件保存在 `assets/voice/raw/`。

实际录音经独立离线 ASR 与静音检测对齐，形成 157 条单行字幕以及吸气、补吸、呼气、揉纸和抛纸等真实动作词锚点。字幕与动作音效共用时间数据。识别同音字差异和低概率提示保留在 `content/asr-report.md`。

配乐与音效由 NumPy 原创合成。108 BPM、4/4 拍、半拍感；暖和弦、拨弦、低频脉冲与细节打击随章节增减，标题进入主题，片尾回扣。人声高于音乐的全片中位差约 10.79 dB，九章均通过预设平衡范围。正式 MP4 的 AAC 实测为 **-15.51 LUFS / -1.70 dBTP**。

`assets/audio/` 包含配乐、旁白、音效及总混；`output/mix-comparison.json` 提供正式比例与音乐提高 1.5 dB 的同段试听。音乐设计详见 `docs/music-design.md`。

## 核验记录与审片范围

- `output/master-report.json`：全部视频帧、时间戳、编码、音频解码与源文件 SHA。
- `output/delivery-validation.json`：最终 AAC 响度、封面与旧片保留校验。
- `content/timing-validation.json`：台本、字幕文字守恒及帧边界检查。
- `output/production-qa.json`：实际输出的关键帧、动作和字幕边界抽检，具体范围见报告。

已完成自动完整解码、实际语音对齐和视觉抽检。未把这些检查表述为完整人工听审；导演仍可在审片页逐章回看和提出调整。

## 旧短片保留

四个旧片的字节数与 SHA-256 均与制作前记录一致：

- `output/review-landscape-minimax-v2.mp4`
- `output/review-portrait-minimax-v2.mp4`
- `output/review-landscape-v1.mp4`
- `output/review-portrait-v1.mp4`

以上路径相对于仓库根；长片交付路径相对于 `longform/`。原版入口仍在原 `output/` 目录，长片独立存放。
