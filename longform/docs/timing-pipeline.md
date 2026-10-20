# 配音、字幕与时间轴管线

所有新增文件均在 `longform/`；旧短片台本、声音、时间轴与成片不改。

输入是冻结的 `content/script.json`（35 段，34 段有旁白）和 `content/tts-chapters.json`。九个网页生成的原始 WAV 放在 `assets/voice/raw/{hook,breath,cold,ear,shake,paper,fractal,order,closing}.wav`。

运行时复用现有离线 MLX Whisper venv 与本地 pinned 模型；不下载模型、不传台本提示词、不重生成语音、不改变播放速度。命令从远端仓库根执行：

```bash
/Users/yangshuyun/workspace/dev/ai-video/proj1-1019/engine/.venv/bin/python longform/scripts/prepare_timeline.py
```

只处理刚到的章节，并汇总所有已缓存章节：

```bash
/Users/yangshuyun/workspace/dev/ai-video/proj1-1019/engine/.venv/bin/python longform/scripts/prepare_timeline.py breath
```

每章缓存以 WAV SHA-256、模型路径和 revision 复用；ASR 原始文字、词、概率、Whisper 分段、静音检测与源音频采样帧数保留在 `longform/assets/voice/asr/`。`.alignment.json` 是以原章音频 0 秒为起点的对齐证据。

仅重新汇总、不转写：

```bash
.tools/venv/bin/python longform/scripts/prepare_timeline.py --build-only
```

仅估算预览：

```bash
.tools/venv/bin/python longform/scripts/prepare_timeline.py --estimate-only
```

预估按每秒 4.5 个汉字写入 `estimated-timeline.json` 和 `estimated-captions.json`，含清楚的 `estimated: true`，不能冒充正式时序。九章未齐、缓存过期、出现无锚点/越界/重叠等阻断问题时，不生成正式 timeline；已有正式文件会移为 `.stale.json`，防止误用。

## 正式数据契约

- `content/timeline.json`：duration、fps=30、width=2560、height=1440、整数 frame_count、chapters、segments、captions、audio_segments、narration、cuts、cut_frames。
- `chapters`：id、中文 title、start/end/duration、该章台本 segments；有声章另有 audio_start/audio_end。
- `segments`：35 条含空 title；34 个有声段落由观测词/停顿定位。start/end 与所属首末字幕同帧，并附 start_frame/end_frame；另以 speech_start/speech_end 保留未量化的观测语音边界。**不能用此数组重复播放整章 WAV。**
- `audio_segments`：九章各一条，音频路径相对仓库根，例如 `longform/assets/voice/raw/hook.wav`。含 start/end、source_audio_duration、source_sha256、source_in=0、playback_rate=1；narration 为同内容兼容字段。
- `music.title_at`：真实 title 章起点，由混音使用。
- `word_cues`：10 个独立词锚点（吸、补吸、呼、写、揉、丢、撕、整理三个动作），含全片帧边界及原章 source_start/source_end、ASR 词 ID 和匹配比例。它们供主渲染生成共享动作与音效 cue，不覆盖主渲染拥有的 action-cues.json。
- `content/captions.json`：单行字幕；每条有整数 start_frame/end_frame，以及未经六位小数截断的 frame/fps 秒数。比较时优先使用整数帧。相邻字幕不重叠，短句可留空档。
- `asr-report.json` / `asr-report.md`：保留真实识别差异、低概率词、匹配覆盖、边界及静音证据；差异是复听线索，不等于已确认配音读错。
- `timeline-status.json`：九章齐备/缺失及阻断问题；正式渲染前应检查 complete。

时间安排：第一章画面从 0 开始，旁白从 0.5 秒开始；每章留 0.5 秒章首、1.5 秒章尾，closing 章尾 2 秒；正文相邻章额外留 0.9 秒；hook 后安排独立 4.4 秒无语音 title。实际整章 WAV 原样放置，既有首尾空白保留，音频没有变速或裁切；最终总长按实际音频和留白向上对齐到帧。

## 对齐原则与边界

先把整章台本和独立 ASR 词流做单调字符编辑对齐，再找每段与每条字幕覆盖的真实 ASR 词。字符只继承所属词的完整时间区间，绝不把词时间按字数等分。同音/数字识别差异被保留并标记，显示字幕仍取冻结台本。

中文标点优先断句，短引导词与后句同屏，通常每行不超过 24 个汉字。若断点位于同一个不可拆 ASR 词内部，合并该字幕并保留说明；合并后超长则停止正式发布，等待人工重分。字幕缺失首尾锚点、整句没有精确词序锚点、时间越界或无法消除的重叠同样阻止正式发布。

声学静音只在相邻两条字幕的边界词范围中提供联合修正：前句止于静音开始，后句起于静音结束。字幕显示可提前一帧、尾部短暂保留，这与观测 speech_start/end 分开记录。概率阈值 0.65 和精确匹配阈值只是复核规则，并不是统计置信区间；ASR 不是音素级强制对齐，也不能代替逐句试听。

回归检查：

```bash
.tools/venv/bin/python longform/scripts/test_timeline.py
```

## 当前实际产物

2026-10-21：九章齐备，旁白源总长 371.4768125 秒；加留白与标题后正式总长 400.8333333333333 秒，即 12025 帧 / 6 分 40 秒 25 帧。标题从 21.7 秒开始。157 条单行字幕、最长 24 个汉字；全部源 SHA、字幕文字与标点守恒、帧边界、无重叠和区间有效性检查通过，详见 content/timing-validation.json。原始 ASR 有 27 组差异，43 条字幕附复核提示；这不是人工试听完成声明。
