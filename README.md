# 先松一口气 · shortvideo-1020

62秒中文短视频，连续发光墙镜头，横版1920×1080与竖版1080×1920。所有工程在远端 `yangshuyun@10.10.10.1:/Users/yangshuyun/workspace/dev/ai-video/shortvideo-1020`。

## 当前制作状态

- 台本与时间轴：`content/timeline.json`、`content/narration.txt`
- 分镜：`docs/storyboard.md`
- 健康表述核验：`docs/evidence.md`
- 配音交接：`docs/tts-handoff.md`
- 发布文案：`docs/publish-copy.md`
- 风格参考：`reference/style/style-guide.pdf`（用户提供，作为参考资料）
- 画面源代码：`shots/wall.js`、`shots/illustrations.js`，两个画幅分别取景
- 原创程序音轨：`scripts/synth_audio.py`；混音：`scripts/mix_audio.py`

所有画面由Multiplane逐帧渲染。没有使用PowerPoint或图片翻页。相机短移、停稳；主体通过时间驱动的Canvas绘制。图像素材均为程序绘制，没有调用生成式图像服务。

## 运行环境

```bash
cd /Users/yangshuyun/workspace/dev/ai-video/shortvideo-1020
source .tool-env
npm run doctor
```

Node24；Multiplane锁定0.3.13；Playwright Chromium；Python3.12 venv；imageio-ffmpeg内置FFmpeg7.1。字体使用远端系统PingFang SC及Arial。跨机器需安装等同字体并重新verify，不保证跨字体像素一致。依赖不进入Git。

## 检查与渲染

```bash
npx multiplane lint shots/landscape.html --json
npx multiplane stills shots/landscape.html --at 2.6,8,19,25,31,38,45,52,58 --out output/stills-landscape --json
npx multiplane verify shots/landscape.html --at 2,5,10,18,28,43,56 --workers 2 --json
bash scripts/render.sh landscape
bash scripts/render.sh portrait
```

先通过verify再渲染。视频和截图在`output/`；编码、核验作业在`out/jobs/`。默认2 workers，避免与其他远端项目抢占过多资源。另有`draft`参数用于低清快速预览，不作为最终画质交付。

## 语音与声音

`content/timeline.json`以每段start/end/audio声明旁白。MiniMax网页可逐段生成并替换音频文件；导入后重新核对字幕与动作。`scripts/temp_voice.py`仅生成macOS Tingting临时配音，须明确标注临时音色，不能冒充MiniMax成品。

原创配乐与音效可在Python中固定种子重新生成，无外部歌曲依赖。最终目标-16 LUFS、true peak不超过-1.5dBTP。保留无旁白版本便于导演试听或换声。

本仓库没有外发或发布操作。影视版权和健康说明参考`docs/publish-copy.md`与`docs/evidence.md`。

## 一键重建与审片

```bash
# 使用现有分段旁白文件重建：
bash scripts/build.sh
# 仅当需要明确标注的临时女声时：
bash scripts/build.sh --scratch-voice
```

脚本不会调用或冒充MiniMax；导入真实MiniMax语音后，需要更新审片页的临时声线说明，并核对`content/captions.json`的时间点。最终审片素材的显示状态以页面说明为准。

通过SSH转发在本机审片（保持这个连接运行）：

```bash
ssh -L 18877:127.0.0.1:18877 yangshuyun@10.10.10.1 \
  'cd ~/workspace/dev/ai-video/shortvideo-1020 && .tools/venv/bin/python -m http.server 18877 --bind 127.0.0.1'
```

然后打开 `http://127.0.0.1:18877/output/review.html`。服务仅监听远端回环地址，没有公网发布。
