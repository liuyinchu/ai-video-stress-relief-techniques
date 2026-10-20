# 长片原创配乐：缓下来之后，仍有向前的力量

本版单独位于 `longform/`。旧短片的音乐、音效、混音与视频均不覆盖。配乐由 NumPy 原创合成，没有使用录音采样、Suno 歌曲、现成旋律或系统语音。

## 声音方向

108 BPM，4/4 拍，采用半拍感：低频主要每两拍推进一次，让节奏清楚而不催促。暖模拟质感和声、带早期反射与附点八分音符延迟的拨弦、节制的钢片泛音构成主色。主体声部的频率重心低于女声清晰度的重要区域，高泛音只在短时间出现。

音乐先作为有主题、有和声行进的作品成立，然后在混音时与旁白建立比例。上一版讲话时人声高于底乐约 17–19 dB；本版目标是在活跃语音窗口中，人声高于音乐 **约 10 dB**，每章中位值接受范围为 8–12 dB。主题与节奏会明显进入观众的注意范围。

## 主题与结构

八小节原创主题以 D minor / Dm9 为核心，首句是 **D4 — F4 — A4 — E4**，后续以 F4 — D4 — A3 — C4 回答。主和声包含 Dm9、Bbmaj9、Fmaj9、Cadd9、Gm9 与 Asus7；片尾落在开放的 Dsus2，保留温暖空间。

前约 17 秒使用自由节奏引子，逐渐引入拨弦与低频。标题落点作为 108 BPM 正式拍网格的起点，落一次明确而克制的重拍，同时进入主题与更宽的空间。正式时间从 `music.title_at` 读取，不强迫实际 TTS 时长去适配 17 秒。

正文每两小节约 **4.44 秒**有和声或配器变化，每八小节改变转位或主题片段，每十六小节真的撤去拨弦并减弱低频，再让其回归。拨弦起音有不超过约 9 ms 的微小变化，力度变化不超过约 8%；重要镜头重拍保持准确。随机化仅用来柔化演奏，不代替编排。

主题完整陈述集中在标题；正文使用不同片段和音区回答，避免持续旋律抢占旁白。片尾回扣单独调度，落在同一拍网格上；之前的主题不会继续跨入回扣区间。Pad、低音和拨弦共同读取一个整数小节和声索引，避免章节边界不同相位造成碰撞。

## 章级配器

| 章节 id | 主体变化 | 章际音色 |
| --- | --- | --- |
| hook / title | 暗色 pad 到开放主题，标题进入低频重拍 | 暖空气抬升与一颗克制泛音 |
| breath | 稀疏拨弦、较少打击、舒展和声 | 抽象气流，不模拟真人呼吸 |
| cold | 清亮钢片泛音，低频保持半拍推进 | 三颗轻玻璃质感音粒 |
| ear | 较干、温暖、近距离木质拨弦 | 轻柔摩擦与短木音 |
| shake | 切分低音、较活跃的颗粒节奏 | 三次轻刷动，左右有空间 |
| paper | 干燥材质打击与克制的低鼓感 | 程序合成纸质细节 |
| fractal | 大幅撤去脉冲，让长和声与空间拨弦展开 | 细风与较长泛音 |
| order | 稳定脉冲回归，声部逐步归位 | 三颗温暖摆放音 |
| closing | 主题回扣，开放和弦、自然渐弱 | 低音量空气过渡 |

章际声音与镜头边界绑定；具体动作声通过 `audio_cues` 单独声明，避免把转场声误当作动作命中。示例：`{"kind":"paper","start":150.4,"duration":0.8}`。

## Timeline 接口

```json
{
  "duration": 360,
  "music": {"title_at": 17},
  "chapters": [
    {"id":"hook","start":0,"end":17},
    {"id":"title","start":17,"end":21.4},
    {"id":"breath","start":21.4,"end":68}
  ],
  "audio_segments": [
    {
      "id":"breath",
      "start":21.9,
      "end":66.5,
      "audio":"longform/assets/voice/raw/breath.wav",
      "source_sha256":"可选：实际源文件的 SHA256"
    }
  ],
  "segments": [
    {"id":"breath-01","start":21.9,"end":30,"text":"字幕分段文本"}
  ]
}
```

音轨优先读取 `audio_segments`，其次 `narration`，最后才读取带 `audio` 的 `segments`。这与字幕分段分离，避免把同一章完整 WAV 播放多次。每章原声按照 `start` 摆位，不自动变速或截断。超出总片长或标注槽位会报错；有 SHA256 时校验源文件。未提供真实语音时，混音命令会拒绝执行，不会自行合成声音。

## 混音方式与验收

1. 先对真实旁白单独做活跃语音 RMS 标准化，并保留峰值余量。音乐不跟随低电平 TTS 一起被整体粗暴放大。
2. 基础 sidechain ducking 仅约 **3 dB**，起音 45 ms、释放 450 ms，保留音乐的存在感。
3. 用 BS.1770 K 加权的 400 ms 窗、100 ms 步长，分别测量旁白与音乐，按章作缓慢增益调整，目标差值约 10 dB。活跃语音使用绝对门限和相对能量门限，避免把长停顿当作轻声。
4. 弱句增加至多 5 dB 的短时保护；较强语音下音乐最多回升 3 dB。这层调整有平滑包络，并在报告中记录实际使用量，不是整段一直压低。
5. **处理后的 stem 会重新实际测量**，报告全片和各章的中位数、p10、p90，并单独比较人声与 `music+sfx`。如章中位数超出 8–12 dB，或轻声窗口 p10 低于 6 dB，会明确写入 `balance_warnings`，用于复听软尾字、技巧名称和音乐瞬态。
6. 最后两遍 loudnorm，目标 **-15.5 LUFS、true peak ≤ -1.7 dBTP**，为交付要求 ≤ -1.5 dBTP 留余量。正式封装后还需复测 AAC。

这些指标属于制作目标，不能替代听审。重点比较普通耳机、手机外放和单声道：主题是否完整可辨，轻声尾字是否清楚，章间的音乐是否自然抬起。

## 命令

以下命令均从远端短片仓库根目录执行：

```sh
# 30秒独立音乐样例；17秒标题落点，含主题前半段
.tools/venv/bin/python longform/scripts/score.py demo

# 实际TTS与timeline确定后，生成整片音乐和音效
.tools/venv/bin/python longform/scripts/score.py render \
  --timeline longform/content/timeline.json

# 按真实旁白混音
.tools/venv/bin/python longform/scripts/score.py mix \
  --timeline longform/content/timeline.json
```

默认输出：

- `longform/output/music-demo.wav` 与 `music-demo-report.json`
- `longform/assets/audio/music.wav`、`sfx.wav`
- `longform/assets/audio/final-mix.wav`
- `longform/output/score-report.json`、`mix-report.json`

可用 `--voice-music-gap 9` 让音乐再靠前约 1 dB，或 `--voice-music-gap 11` 给旁白多一点空间；允许范围 8–12。`--sfx-gain` 是音效线性增益，默认 0.8。`--lufs` 默认 -15.5。随机种子固定为 102021，音乐可复现。

临时工作文件也限定在 `longform/.scratch/` 内并自动清理。

## 已完成的检验

- 已实际生成 30 秒、48 kHz、立体声、PCM24 音乐样例。它用于确认音色和标题结构，30 秒中只包含八小节完整主题的前半段。
- 已在内存中完整合成六分钟音乐：81 次和声事件，3 种实际转位，7 次真实撤层；片尾回扣在 108 BPM 网格上，未出现非有限样本或削波。报告：`output/score-structure-check.json`。
- 已只读复用旧短片中的四段真实 MiniMax 音频做混音校准，测试音频随后自动删除。处理后 K 加权人声／音乐中位差 **10.49 dB**，两个测试章分别 **10.45 / 10.68 dB**；整混输出约 **-15.50 LUFS / -1.70 dBTP**。报告：`output/mixer-calibration-report.json`。
- 校准中的最轻语音窗口仍需留意，尤其测试人为把旁白放在标题重拍后 0.5 秒的位置；正式长片使用真实章间静场后，再逐章验收。该测试不代表长片正式旁白已经生成。

## 正式全长音频交付

已根据 **independent-asr-observed / estimated=false** 的实际时间轴完成正式配乐、音效与混音。总长 **400.833333 秒**，标题重拍随真实配音移动到 **21.700 秒**。九章原始 MiniMax WAV 均原速摆位，读取源 SHA256 校验，没有音频裁切或变速。

正式素材：

- `assets/audio/music.wav`：原创全长配乐。
- `assets/audio/sfx.wav`：包含七条真实动作锚点的音效。
- `assets/audio/narration.wav`：完成独立增益标准化、按实际时间轴摆位的旁白 stem。
- `assets/audio/music-in-mix.wav`、`sfx-in-mix.wav`：最终 loudnorm 之前已经完成平衡／ducking 的制作 stem。
- `assets/audio/final-mix.wav`：正式交付总混。

独立解码后实测：**-15.51 LUFS / -1.70 dBTP / LRA 3.50 LU**。按 256 kbps AAC 编码再测，数值相同。48 kHz、立体声、PCM24，19,240,000 帧；削波与 NaN/Inf 样本均为 0。最终封装的视频仍可再做一次容器内音轨复测。

全片人声／音乐 K 加权差中位数 **10.788 dB**，第 10 百分位 **7.245 dB**。各章中位数均通过 8–12 dB 目标：

| 章节 | 人声高于音乐的中位数 | 第 10 百分位 |
| --- | ---: | ---: |
| hook | 10.828 dB | 7.768 dB |
| breath | 10.558 dB | 6.669 dB |
| cold | 10.856 dB | 7.628 dB |
| ear | 10.923 dB | 7.814 dB |
| shake | 10.673 dB | 7.017 dB |
| paper | 11.009 dB | 7.109 dB |
| fractal | 10.643 dB | 7.085 dB |
| order | 10.867 dB | 7.528 dB |
| closing | 11.065 dB | 7.278 dB |

正式混音无 `balance_warnings`。旁白单独增加 12.811 dB 后才叠加音乐；基本 ducking 3 dB，弱句额外保护平均约 1.645 dB，保留较明确的音乐存在感。

声音与画面从 `content/action-cues.json` 共享动作时点：呼气 39.233333 秒；揉纸 244.233333 秒；抛纸 245.766667 秒；落点 246.323188 秒；撕纸 248.933333 秒；书放置 336.898 秒；杯放置 342.389815 秒。七条事件的起点和持续时间均已逐项核对。

重建分步命令：

```sh
.tools/venv/bin/python longform/scripts/score.py music \
  --timeline longform/content/timeline.json
.tools/venv/bin/python longform/scripts/score.py effects \
  --timeline longform/content/timeline.json \
  --actions longform/content/action-cues.json
.tools/venv/bin/python longform/scripts/score.py mix \
  --timeline longform/content/timeline.json \
  --actions longform/content/action-cues.json \
  --voice-music-gap 10
.tools/venv/bin/python longform/scripts/mix_comparison.py
```

`render` 可合并音乐和音效生成。存在 `action-cues.json` 时，`render/effects/mix` 默认读取它；estimated cue、总长不一致或过期 cue 哈希会阻止正式混音，避免预估动作声音混入实际时间轴。

`output/mix-comparison.json` 为审片页面提供两条 **36.466667 秒**的真实配音对比：正式平衡版 `mix-demo-balanced.wav` 与音乐额外 +1.5 dB 的 `mix-demo-forward.wav`。两个片段使用同一段正式 MiniMax 配音、同一配乐，且总响度都约 -15.5 LUFS；正式总混仍采用 voice gap 10 的平衡版。

完整证据：`output/audio-validation.json`、`mix-report.json`、`effects-report.json`、`score-report.json`。旧短片的任何音轨均未覆盖。
