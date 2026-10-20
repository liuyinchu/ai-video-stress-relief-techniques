# 长片渲染与封装

这条管线只在远端仓库的 `longform/` 内写文件，保留既有短片。画面核心为仓库已安装的 Multiplane 0.3.13。最终输出为 2560 × 1440、30 fps、H.264 High / yuv420p，配 48 kHz 双声道 AAC 320 kbps。

## 前置文件

- `longform/index.html`：主镜头，固定 2560 × 1440 stage。
- `longform/content/timeline.json`：实际 MiniMax 音频与 ASR 对齐后的时间线；`estimated` 必须为 `false`，fps 为 30。
- `longform/assets/audio/final-mix.wav`：完整混音，48 kHz 双声道；长度与时间线至多差一帧。

在远端仓库执行：

```sh
cd /Users/yangshuyun/workspace/dev/ai-video/shortvideo-1020
source .tool-env
```

## 常用命令

先检查整数帧分段计划，不启动浏览器：

```sh
python3 longform/scripts/render_film.py --prepare
```

只检查主镜头尺寸、总帧数与确定性：

```sh
python3 longform/scripts/render_film.py --verify-only
```

首次全片制作，另生成 1080p 交付版：

```sh
python3 longform/scripts/render_film.py --delivery-1080
```

中断后继续；只跳过源码和成片哈希都匹配的成功章节：

```sh
python3 longform/scripts/render_film.py --resume --delivery-1080
```

先制作指定章节用于审查；本命令不会拼接全片：

```sh
python3 longform/scripts/render_film.py --chapter paper,order --resume
```

所有章节已完成、仅调整混音之后重新封装：

```sh
python3 longform/scripts/render_film.py --mux-only --resume --delivery-1080
```

`--workers` 只接受 1 或 2。章节按顺序处理，不同时启动多个章节，因此浏览器 worker 总上限始终为 2。默认 `--raster software --quality standard`；可根据已做的机器测试显式选择 `--raster gpu`。更改画面设置会使旧章节失效并重渲染。没有使用 `--draft`。

实际时间线未完成时，只允许制作标注为估算的计划，不能据此正式渲染：

```sh
python3 longform/scripts/render_film.py \
  --prepare --allow-estimated \
  --timeline longform/content/estimated-timeline.json \
  --output-dir longform/output/estimated-render-plan
```

## 帧边界与验证

管线以整数帧作为唯一分段依据。每段渲染范围是 `[本章 start, 下一章 start)`，最后一章到全片 `frame_count`。章节尾部到下一章的停留／转场时间被纳入前一段，因此不存在拼接遗漏。Multiplane 的 `--to` 是排他的；只在调用 CLI 时将整数帧转换成 12 位小数秒。

开始渲染之前，先对整部镜头执行 `inspect` 和 `verify`。验证点覆盖每章开头、中点与末帧，全部在整数帧时刻。确定性检查未返回 `ok: true` 时立即终止。`--resume` 可复用同一画面指纹的成功验证记录。

每章完成后必须同时满足：

1. Multiplane 返回成功，帧数、尺寸与 fps 符合计划，且不是 draft。
2. FFmpeg 完整解码无错误；逐帧 showinfo 验证编号、连续 PTS、yuv420p 与 2560 × 1440。
3. 独立 stream-copy 计数所得视频 packet 数与解码帧数一致。
4. 写入成功 receipt，记录源码指纹、范围、验证结果与成片 SHA-256。

续跑以 receipt 与实际文件哈希为准。只有文件存在、没有 receipt 的情况视为未成功。修改主 HTML、场景代码、视觉资源、字幕、实际时间线、`render-data.js`、动作 cue 或 `build_render_data.py` 之后会重新验证与渲染。音频制作和交付文档生成器不在画面指纹内。正式全片开渲前冻结上述画面输入；渲染中不要修改。混音不影响无声章节的复用。

所有章节验证通过后，使用 concat demuxer 直接复制视频流，不二次编码。拼接结果再次验证完整帧数与连续 PTS。混音按 `总帧数 × 1600` 个音频采样精确 pad／trim，禁止用 `-shortest` 隐藏音画长度错误。封装后再次完整解码视频与 AAC。最终文件先写 `.partial.mp4`，通过验证再原子替换正式文件。

1080p 交付版从最终母版以 Lanczos 缩放，H.264 High、CRF 17、yuv420p，AAC 直接复制；缩放后仍验证总帧数与音频解码。

## 输出

- `longform/output/master-landscape.mp4`：1440p 带混音母版。
- `longform/output/master-landscape-silent.mp4`：直接拼接的无声画面。
- `longform/output/master-landscape-1080p.mp4`：可选 1080p 版。
- `longform/output/chapters/`：逐章 MP4 与成功 receipt。
- `longform/output/render-plan.json`：整数帧分段及可复现 CLI 命令。
- `longform/output/master-report.json`：最终音画规格、哈希与验证结果。
- `longform/output/logs/`：Multiplane JSONL、FFmpeg 编码、解码与 packet 验证日志。
- `longform/output/jobs/`：Multiplane 作业记录与诊断预览。

不输出整片 PNG/raw 帧序列。Multiplane 自身可能保存少量诊断预览及中断恢复用的已编码小段；渲染完成后其内部编码段自动清理。管线不修改旧的 `output/`。

## 本次管线自检

独立测试镜头和 2 秒测试音频保存在 `longform/output/pipeline-qa/`，与正式影片隔离。测试覆盖两个 30 帧章节，其中第一章含 3 帧章间空档；检验确定性、整数帧范围、章节渲染、流复制拼接、AAC 封装、1080p 缩放与续跑。该素材仅用于管线验证，不是正式影片预览。
