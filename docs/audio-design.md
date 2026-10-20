# 声音设计：给身体一个缓冲

62 秒，48 kHz / 双声道 / 24-bit PCM。配音气质为平静、温暖的中文女声。配乐与音效均为本仓库程序原创合成，没有采样外部唱片、素材包或 Suno 音乐，也没有把临时语音标记为 MiniMax。

## 音乐

78 BPM。以柔软的 Dmaj9 → Gmaj9 → Bm9 → Asus2 → Dadd9 和声为骨架，低谐波正弦音色组成环境 pad，少量带毛毡质感的木质敲击承接四音动机。左右声道只有轻微宽度与漂移，兼容手机单声道播放。前 2.7 秒加入极轻的缓慢拍频，随后消散；末尾以开放和弦和 3.5 秒渐弱收束。

音乐没有连续鼓点、警报、心跳或情绪爆点。呼吸演示留出空白，不用音乐强迫观众跟随某个呼吸频率。Music 原始 stem 的 RMS 目标为 -30 dBFS、峰值上限 -17 dBFS，为中文旁白保留空间。

## 音效与时间点

| 时间 | 视觉内容 | 声音处理 |
| --- | --- | --- |
| 0–5 秒 | 压力引入 | 轻微拍频消散，pad 打开 |
| 5–17 秒 | 双吸长呼 | 相机落点一阵极轻空气；呼气段只有抽象气流纹理 |
| 17–23 秒 | 凉毛巾 | 轻柔转场，一颗低音量玻璃／木质泛音 |
| 23–28 秒 | 轻揉耳廓 | 极轻空气转场，不强调医疗效果 |
| 28–34 秒 | 松肩、手脚 | 两次细小布料感沙沙声 |
| 34–42 秒 | 写纸、揉团 | 程序噪声合成短纸团摩擦，力度受控 |
| 42–49 秒 | 自然纹理 | 较长而低音量的空气过渡 |
| 49–55 秒 | 整理小块 | 三个越来越轻的温暖摆放声 |
| 55–62 秒 | 结束 | 温和落点、自然渐弱，结尾不加成功提示音 |

SFX 峰值上限 -23 dBFS，出声密度低；过渡音跟随区域切换，不跟随每个字或每次微小移动。时间点优先从 timeline 的 stations 读取（画面落点），没有 stations 时才读 segments；按 id 或 audio_cue 字段匹配，避免把旁白起点误当作镜头落点。

## 合成与混音命令

在远端仓库根目录运行：

```sh
.tools/venv/bin/python scripts/synth_audio.py --timeline content/timeline.json
```

输出 `assets/audio/music.wav` 与 `assets/audio/sfx.wav`。默认随机种子为 1020，可复现。所有生成音频严格等长。

分段旁白按 timeline 中的 `start` 定位。支持 `voice_start` 覆盖该段音频起点，支持 `audio`、`voice_file` 或 `narration_audio` 指向音频文件；不改变原配音速度、不静默截断超出总时长的配音。示例：

```json
{
  "duration": 62,
  "segments": [
    {"id": "intro", "start": 0, "end": 5, "audio": "assets/audio/voice/intro.wav"},
    {"id": "breath", "start": 5, "end": 17, "audio": "assets/audio/voice/breath.wav"}
  ]
}
```

```sh
.tools/venv/bin/python scripts/mix_audio.py --timeline content/timeline.json
```

如果语音文件按 segment id 命名，可用：

```sh
.tools/venv/bin/python scripts/mix_audio.py --timeline content/timeline.json --voice-dir assets/audio/voice
```

也支持单条完整配音或独立分段清单：

```sh
.tools/venv/bin/python scripts/mix_audio.py --voice assets/audio/narration.wav --duration 62
.tools/venv/bin/python scripts/mix_audio.py --segments content/voice-segments.json --duration 62
```

独立清单格式为 `[{"start": 5.2, "path": "assets/audio/voice/breath.mp3"}]`。WAV、AIFF、MP3、AAC、M4A 均由 FFmpeg 解码到 48 kHz 双声道。相对路径先按当前工作目录，再按清单所在目录与其上一级解析。

正式混音保留原配音的停顿，按活跃语音将音乐最多压低约 9.6 dB，使用 60 ms attack 与 450 ms release，音效仅轻微降低。之后进行 FFmpeg 两遍 loudnorm，目标 **-16 LUFS / true peak ≤ -1.5 dBTP / LRA 7**。输出 `assets/audio/final_mix.wav`。终端 JSON 报告包含每段配音的实际时间、响度测量与可能跨越画面区间的提示。用 `--report PATH` 可保存该报告。

始终同时保留 `assets/audio/music_sfx_mix.wav`，目标 -24 LUFS，适用于无旁白审片。需要先生成无配音预览时，不传含有 audio 字段的 timeline：

```sh
.tools/venv/bin/python scripts/mix_audio.py --duration 62
```

此时 `final_mix.wav` 也是无配音预览，报告 `has_narration: false`。正式旁白到位后重跑分段混音即可替换。`--music-gain` 和 `--sfx-gain` 是线性增益，默认 1。可通过 `--ffmpeg PATH` 或 `FFMPEG_BINARY` 指定 FFmpeg；默认依次查找系统 FFmpeg 和 imageio-ffmpeg 随包二进制。

## 第一轮实测

- Music stem：峰值 -17.52 dBFS，RMS -30.00 dBFS。
- SFX stem：峰值 -23.00 dBFS，RMS -50.32 dBFS。
- 无配音混音：-23.89 LUFS、true peak -12.86 dBTP、LRA 1.70 LU。
- 时长：62.000 秒，两个声道，采样率 48,000 Hz。

配音提供者以主制作记录为准：MiniMax 尚未导出的情况下，临时系统配音只用于检查节奏，不作为 MiniMax 成品对外表述。

## 临时旁白审片混音验证

文件 `assets/audio/temp-narrated-mix.wav` 使用主制作流程提供的 macOS Tingting 临时女声，只用于审片节奏。9 段按 timeline 位置摆放，均未超过各自画面区间；原始旁白未被此混音脚本加速或截断。

独立重新解码与测量：62.000 秒、48 kHz、双声道、24 bit；综合响度 -16.01 LUFS，true peak -2.13 dBTP，LRA 4.60 LU；削波样本为 0，NaN/Inf 样本为 0。最多 ducking 9.63 dB。原始两遍混音报告为 `output/temp-mix-report.json`。

另使用临时正弦测试片段验证了分段起点、严格等长输出、ducking，以及 -16 LUFS 的两遍混音通路；测试素材已经自动删除，不属于作品。
