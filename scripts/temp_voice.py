"""macOS Tingting scratch narration; never label this MiniMax output."""
import json, subprocess, wave, os
from pathlib import Path
import imageio_ffmpeg
root=Path(__file__).resolve().parents[1]
ff=imageio_ffmpeg.get_ffmpeg_exe()
data=json.loads((root/"content/timeline.json").read_text())
report=[]
for s in data["segments"]:
 out=root/s["audio"]
 out.parent.mkdir(parents=True,exist_ok=True)
 raw=out.with_suffix(".aiff")
 subprocess.run(["/usr/bin/say","-v","Tingting","-r","180","-o",str(raw),s["text"]],check=True)
 wav=out.with_name(out.stem+"-raw.wav")
 subprocess.run([ff,"-y","-loglevel","error","-i",str(raw),"-ar","48000","-ac","1",str(wav)],check=True)
 with wave.open(str(wav)) as w:duration=w.getnframes()/w.getframerate()
 target=s["end"]-s["start"]-.1
 speed=max(.82,min(1.3,duration/target))
 subprocess.run([ff,"-y","-loglevel","error","-i",str(wav),"-af",f"atempo={speed:.7f},afade=t=in:d=0.015,afade=t=out:st={max(0,target-.08)}:d=0.08","-ar","48000","-ac","1",str(out)],check=True)
 with wave.open(str(out)) as w:actual=w.getnframes()/w.getframerate()
 report.append({"id":s["id"],"raw_seconds":duration,"fit_seconds":actual,"slot":target,"tempo":speed,"provider":"macOS Tingting TEMP"})
print(json.dumps(report,ensure_ascii=False,indent=2))
(root/"output/temp-voice-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
