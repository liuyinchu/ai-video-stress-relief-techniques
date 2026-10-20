"""Mux completed Multiplane picture with an explicitly selected mix, preserving video."""
import argparse, json, subprocess, wave
from pathlib import Path
import imageio_ffmpeg
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--format',choices=['landscape','portrait'],required=True)
p.add_argument('--audio',default='assets/audio/temp-narrated-mix.wav')
p.add_argument('--name',default=None)
a=p.parse_args()
ff=imageio_ffmpeg.get_ffmpeg_exe()
src=root/'output'/f'{a.format}-silent.mp4'
dst=root/'output'/(a.name or f'review-{a.format}-v1.mp4')
audio=root/a.audio
with wave.open(str(audio)) as w:dur=w.getnframes()/w.getframerate()
if abs(dur-62)>.05:raise RuntimeError(f'Expected 62-second audio, got {dur}')
subprocess.run([ff,'-y','-loglevel','error','-i',str(src),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','256k','-ar','48000','-movflags','+faststart','-t','62',str(dst)],check=True)
# Decode entire deliverable to catch malformed/corrupt streams.
subprocess.run([ff,'-v','error','-i',str(dst),'-f','null','-'],check=True)
print(json.dumps({'file':str(dst),'bytes':dst.stat().st_size,'audio':str(audio),'picture_engine':'Multiplane 0.3.13','voice':'macOS Tingting TEMP' if 'temp-' in a.audio else 'selected external narration','decoded_ok':True},ensure_ascii=False))
