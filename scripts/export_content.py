"""Export edit-friendly narration, SRT, and the production index."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
data=json.loads((root/"content/timeline.json").read_text())
def timestamp(s):
 ms=round(s*1000);return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"
rows=[]
for i,s in enumerate(json.loads((root/"content/captions.json").read_text()),1):
 rows.append(f"{i}\n{timestamp(s['start'])} --> {timestamp(s['end'])}\n{s['text']}\n")
(root/"output/narration.srt").write_text("\n".join(rows))
(root/"content/narration.txt").write_text("\n\n".join(s["text"] for s in data["segments"]))
(root/"docs/tts-handoff.md").write_text("# MiniMax分段配音稿\n\n声线：平静、温暖的普通话女声。自然交谈、轻柔坚定，避免广告播音腔。每段单独生成；导出后保存为对应id音频。不要读编号标签、文件名和时长。\n\n"+"\n\n".join(f"## {s['id']} / {s['end']-s['start']:.1f}秒内\n\n{s['text']}\n\n目标：`{s['audio']}`" for s in data["segments"])+"\n\n目前审片中的macOS Tingting仅为临时配音，不能标注为MiniMax。最终语音到位后，先核对时长及发音，再重跑混音和封装。\n")
