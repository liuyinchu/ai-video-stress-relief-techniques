"""Read export progress without attaching to or interrupting the render."""
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent;OUT=BASE/'output'
def read(p):return json.loads(p.read_text())
state=read(OUT/'all-process.json')
phase=state.get('phase','final')
plan=read(OUT/phase/'plan.json')
verified=0;current=None
for chapter in plan['chapters']:
 receipt=OUT/phase/'chapters'/Path(chapter['file']).with_suffix('.receipt.json')
 if receipt.exists() and read(receipt).get('fingerprint')==plan['fingerprint']:
  verified+=chapter['frames']
 elif current is None:
  current=chapter
captured=0;fps=None;stage='complete' if current is None else 'starting'
if current:
 log=OUT/phase/'logs'/(current['id']+'.jsonl')
 if log.exists() and log.stat().st_mtime>=(OUT/phase/'plan.json').stat().st_mtime:
  for line in reversed(log.read_text().splitlines()):
   try:event=json.loads(line)
   except json.JSONDecodeError:continue
   if event.get('phase')=='capture':
    captured=event.get('done',0);fps=event.get('fps');stage='capture' if captured<current['frames'] else 'decode';break
print(json.dumps({'state':state['state'],'phase':phase,'chapter':current['id'] if current else None,'stage':stage,'verified_frames':verified,'captured_current':captured,'total_frames':plan['frames'],'progress_percent':round(100*(verified+captured)/plan['frames'],1),'capture_fps':round(fps,2) if fps else None},ensure_ascii=False))
