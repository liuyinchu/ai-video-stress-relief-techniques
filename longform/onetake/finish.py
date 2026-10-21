"""Record the new picture delivery and prove that approved audio/old films stayed intact."""
import hashlib,json,subprocess,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'longform/onetake';OUT=BASE/'output'
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def require(x,message):
 if not x:raise RuntimeError(message)
spec=importlib.util.spec_from_file_location('picture_render',BASE/'render.py')
render=importlib.util.module_from_spec(spec);spec.loader.exec_module(render)
preview=read(OUT/'preview/report.json');final=read(OUT/'final/report.json');motion=read(OUT/'motion-audit.json')
for report,fps,width,height,frames in [(preview,30,1920,1080,12025),(final,60,3840,2160,24050)]:
 require(report['complete'] and report['audio_unchanged'],'Incomplete export or changed audio.')
 require(report['fingerprint']==render.fingerprint(report['mode'])[0],'Rendered picture no longer matches source.')
 verification=read(OUT/report['mode']/'verify-receipt.json')
 require(verification['fingerprint']==report['fingerprint'] and verification['result']['data']['passed'],'Determinism verification does not match picture.')
 require((report['fps'],report['width'],report['height'],report['frames'])==(fps,width,height,frames),'Unexpected native output format.')
 require(sha(Path(report['output']))==report['sha256'],'Output hash changed after validation.')
require(preview['audio_packet_hash']==final['audio_packet_hash'],'Preview/final approved sound packet hashes differ.')
locked=[]
for item in read(BASE/'locked-inputs.json'):
 require(sha(ROOT/item['path'])==item['sha256'],'Locked input changed: '+item['path']);locked.append(item)
oldLong=read(ROOT/'longform/content/delivery-receipt.json')
preserved=[{'path':'longform/output/master-landscape.mp4','sha256':oldLong['master_sha256']},{'path':'longform/output/master-landscape-1080p.mp4','sha256':oldLong['delivery_1080_sha256']}]+read(ROOT/'longform/content/preserved-shortfilms.json')
for item in preserved:require(sha(ROOT/item['path'])==item['sha256'],'Earlier film was modified: '+item['path'])
require(motion['passed'],'Motion continuity audit failed.')
visual=read(OUT/'visual-qa.json')
require(visual['preview_sha256']==preview['sha256'] and not visual['findings'],'Visual review does not match delivered preview.')
receipt={'complete':True,'preview':preview,'final':final,'audio_unchanged':True,'audio_packet_hash':final['audio_packet_hash'],'locked_inputs':locked,'preserved_films':preserved,'visual_qa':visual,'motion_audit':{'persistent_geometry':motion['heroIdentityPreserved'],'minimum_projected_in_frame_fraction':min(t['minVisibleFraction'] for t in motion['transitions']),'locked_holds':motion['lockedHolds']},'review':'http://127.0.0.1:18878/longform/onetake/output/review.html','scope':'Full frame/audio decoding, deterministic rendering, continuity geometry and sampled visual QA; audio is copied from the approved version.'}
(BASE/'delivery-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
(OUT/'delivery-validation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
text=f'''# 连续镜头版制作与交付

总长400.833333秒。完整审片版1920×1080 / 30fps / 12025帧；成片3840×2160 / 60fps / 24050帧。全部画面重新绘制，4K由WebGL原生像素尺寸与DOM字体按2倍像素密度生成。

## 声音与已有版本

旁白、音乐、音效和最终总混文件保持原样。新片直接复制上一版已确认的AAC音轨，没有重新编码；1080p与4K版的音频包哈希一致。四个旧短片和两个旧长片文件的SHA256均未变。记录见 `delivery-receipt.json`。

## 画面实现

Multiplane 0.3.13 + Three.js 0.180.0。七个场景处在同一三维世界中，摄像机按连续轨迹移动。主体金线由同一组512个中心点与固定拓扑的管状网格贯穿，透明度始终为1；纸张与叶片共享变形网格，揉、撕、抛投时主体线直接取其真实边缘。

摄像机采用最小加加速度轨迹，边界速度与加速度为零，提前主体0.18秒行进；讲解处停稳。收纳物件使用解析阻尼动作，纸张落点带有幅度受限的镜头反应。九次交接的投影边界检查通过，八处指定停镜区间位移为零。

运动模糊由Multiplane在线性光中平均真实时间子帧：快速交接5次采样、较慢动作3次、静止段1次，快门比例0.45；文字切点单独保护。所有画面只由时间t决定，并通过重排时间、重载与不同worker数量的确定性校验。

材质为暖灰陶瓷、雾蓝玻璃、香槟金线与纸张。深蓝黑背景沿用风格手册，物件采用立体光照、倒角、细织纹和接触阴影。逐段分镜见 `storyboard.md`，衔接设计见 `design.md`。

## 输出

- `output/review.html`：审片页，含1080p/4K切换与九处交接的单段播放。
- `output/film-1080p30.mp4`：完整审片版。
- `output/film-4k60.mp4`：原生4K60成片。
- `output/poster.png`：4K封面。
- `output/final-keyframes/`：35段讲解与额外交接位置的实渲染关键帧。
- `output/motion-audit.json`：连续轨迹与同一主体检查记录。
- `output/visual-qa.json`、`output/transition-sheets/`：成片九处交接的108帧连续取样与目视检查。
- `output/preview/report.json`、`output/final/report.json`：完整解码、帧数、编码与音频一致性。

## 重建

在远端仓库根 `/Users/yangshuyun/workspace/dev/ai-video/shortvideo-1020` 执行：

```sh
source .tool-env
node longform/onetake/audit.mjs
.tools/venv/bin/python longform/onetake/render.py --mode preview --resume
.tools/venv/bin/python longform/onetake/render.py --mode final --resume
.tools/venv/bin/python longform/onetake/inspect_transitions.py
# 检查新生成的九处交接取样图并更新 output/visual-qa.json 后，再生成交付记录。
.tools/venv/bin/python longform/onetake/finish.py
.tools/venv/bin/python longform/onetake/review.py
```

进度可用 `.tools/venv/bin/python longform/onetake/progress.py` 查看。长导出可用 `background.py all` 依次运行两个规格，状态记录在 `output/all-process.json`。续跑只复用与源码指纹及文件哈希一致的章节。分段仅用于恢复与编码，画面与摄像机仍为同一次连续时间函数。

声音包SHA256：`{final['audio_packet_hash']}`。
'''
(BASE/'README.md').write_text(text)
print(json.dumps({'complete':True,'duration':final['duration'],'final_size_mb':round(final['bytes']/1e6,2),'audio_unchanged':True,'preserved_films':len(preserved)},ensure_ascii=False))
