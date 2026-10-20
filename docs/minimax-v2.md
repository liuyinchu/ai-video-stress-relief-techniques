# MiniMax 正式配音版 v2

2026-10-21，按导演要求通过 Computer Use 操作 Chrome，在已登录的MiniMax中文站逐段生成9个WAV，导入远端仓库。模型speech-2.8-hd，音色「温暖闺蜜」，语速1、声调0、音量1；使用340声贝，没有购买或升级订阅。

## 音频与同步

原始WAV保存在assets/audio/minimax/raw/，保留原始文件和SHA256。每段转换为48kHz单声道PCM24供混音。只有开场去掉0.107秒末尾空白并加速2.84%；其余八段保持原速和全部句中停顿。旧Tingting及v1视频完整保留。

字幕使用既有离线模型独立ASR及声学停顿辅助对齐，未给参考文本提示词。ASR是估计结果，不等于人工听音或强制对齐。出现的数词/同音字转写差异已核对并在报告中保留，未发现确定需要重做的内容错误。字幕与动作切点对齐到30fps，换字帧取消运动模糊。

呼吸补吸提示在6.9667秒、长呼提示在8.5秒；长呼圆环保持至15秒。揉纸在36.6333–37.4333秒，丢纸在37.6667–38.1667秒，揉纸音效同步更新。所有动作仍在同一面连续墙上。

## 混音

先单独调整人声电平，再与配乐及音效合成，语音期间底乐自动降低。PCM混音独立测量-16.05 LUFS、-1.66dBTP；256kbps AAC验证-16.06 LUFS、-1.66dBTP。时长62.000秒，无削波。原配乐与原版音效均保留。

## 输出

- output/review-landscape-minimax-v2.mp4
- output/review-portrait-minimax-v2.mp4
- output/review-minimax.html（新版审片页）
- output/review-v1.html（旧版对照）
- output/narration-minimax.srt
- assets/audio/minimax-narrated-mix.wav
- output/minimax/chrome-generation-proof.jpg

技术记录：output/minimax/import-report.json、timing-analysis.json、sync-report.json、audio-validation.json。content/minimax-provenance.json保留来源信息；content/captions-minimax.json及minimax-render-config.js为本版可重复渲染的时间参数。
