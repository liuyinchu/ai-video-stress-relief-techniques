#!/usr/bin/env python3
"""Render one continuous shot in resumable ranges; copy the approved AAC track."""
import argparse, hashlib, importlib.util, json, os, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'longform/onetake'
spec=importlib.util.spec_from_file_location('checks',ROOT/'longform/scripts/render_film.py')
checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
def read(p): return json.loads(p.read_text())
def write(p,d): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def fingerprint(mode):
    paths=[BASE/'index.html',BASE/'scene.js',BASE/'data.js',BASE/'locked-inputs.json',ROOT/'package-lock.json',ROOT/'longform/scripts/render_film.py']
    obj={'mode':mode,'sources':{str(p.relative_to(ROOT)):checks.sha256(p) for p in paths}}
    return hashlib.sha256(json.dumps(obj,sort_keys=True).encode()).hexdigest(),obj

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['preview','final'],default='preview');ap.add_argument('--resume',action='store_true');ap.add_argument('--only');ap.add_argument('--mux-only',action='store_true');args=ap.parse_args()
 fps,scale=(30,1) if args.mode=='preview' else (60,2)
 width,height=1920*scale,1080*scale
 checks.FPS=fps;checks.WIDTH=width;checks.HEIGHT=height
 out=BASE/'output'/args.mode;logs=out/'logs';jobs=out/'jobs';parts=out/'chapters'
 for p in (out,logs,jobs,parts):p.mkdir(parents=True,exist_ok=True)
 for row in read(BASE/'locked-inputs.json'):
  if checks.sha256(ROOT/row['path'])!=row['sha256']:raise RuntimeError('Approved input changed: '+row['path'])
 timeline=read(ROOT/'longform/content/timeline.json');duration=timeline['duration'];frames=round(duration*fps)
 start=[round(c['start']*fps) for c in timeline['chapters']];end=start[1:]+[frames]
 plan=[{'id':c['id'],'first':a,'end':b,'frames':b-a,'file':f'{i:02d}-{c["id"]}.mp4'} for i,(c,a,b) in enumerate(zip(timeline['chapters'],start,end),1)]
 fp,inputs=fingerprint(args.mode);write(out/'inputs.json',inputs);write(out/'plan.json',{'fps':fps,'width':width,'height':height,'duration':duration,'frames':frames,'fingerprint':fp,'chapters':plan})
 ffmpeg=checks.find_ffmpeg();cli=str(ROOT/'node_modules/.bin/multiplane');shot=str(BASE/'index.html')
 common=['--root',str(ROOT),'--fps',str(fps),'--scale',str(scale),'--raster','gpu','--workers','2','--quality','standard','--job-dir',str(jobs),'--no-hosted','--json']
 receipt=out/'verify-receipt.json'
 if not(args.resume and receipt.exists() and read(receipt).get('fingerprint')==fp):
  times=[10,25,64,94,150,188,235,245,281,332,376,384,397]
  print(f'Verifying {args.mode}: {width}x{height}, {fps} fps.',flush=True)
  result=checks.run_logged([cli,'verify',shot,*common,'--at',','.join(str(round(t*fps)/fps) for t in times)],logs/'verify.jsonl',events=True)
  write(receipt,{'fingerprint':fp,'passed':True,'result':result})
 for p in plan:
  if args.only and p['id'] not in args.only.split(','):continue
  path=parts/p['file'];rec=path.with_suffix('.receipt.json')
  if (args.resume or args.mux_only) and rec.exists() and path.exists() and read(rec).get('fingerprint')==fp and read(rec).get('sha256')==checks.sha256(path):
   print('Reuse '+p['id'],flush=True);continue
  if args.mux_only:raise RuntimeError('No verified chapter: '+p['id'])
  print(f'Rendering {p["id"]}: {p["frames"]} frames.',flush=True)
  result=checks.run_logged([cli,'render',shot,*common,'--from',f'{p["first"]/fps:.12f}','--to',f'{p["end"]/fps:.12f}','--encoder','x264','--ffmpeg',ffmpeg,'--max-bitrate','65','--out',str(path),'--overwrite'],logs/f'{p["id"]}.jsonl',events=True)
  data=result['data']
  if (data['width'],data['height'],data['fps'],data['frames'])!=(width,height,fps,p['frames']):raise RuntimeError('Output dimensions or frame count changed.')
  probe=checks.decode_probe(ffmpeg,path,logs/f'decode-{p["id"]}.log',p['frames'],width,height)
  if fingerprint(args.mode)[0]!=fp:raise RuntimeError('Picture source changed during render.')
  write(rec,{'fingerprint':fp,'sha256':checks.sha256(path),'probe':probe,'result':result});print('Verified '+p['id'],flush=True)
 if args.only:return
 concat=out/'chapters.ffconcat';concat.write_text('ffconcat version 1.0\n'+''.join(f'file chapters/{p["file"]}\nduration {p["frames"]/fps:.12f}\n' for p in plan))
 silent=out/'silent.mp4';checks.run_logged([ffmpeg,'-hide_banner','-nostdin','-y','-f','concat','-safe','1','-i',str(concat),'-map','0:v:0','-c','copy','-an','-movflags','+faststart',str(silent)],logs/'concat.log')
 label='film-1080p30.mp4' if args.mode=='preview' else 'film-4k60.mp4'
 final=BASE/'output'/label;partial=final.with_suffix('.partial.mp4');approved=ROOT/'longform/output/master-landscape.mp4'
 print('Muxing unchanged approved AAC.',flush=True)
 checks.run_logged([ffmpeg,'-hide_banner','-nostdin','-y','-i',str(silent),'-i',str(approved),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','copy','-map_metadata','-1','-metadata','title=先让身体缓一缓 · 连续镜头版','-movflags','+faststart',str(partial)],logs/'mux.log')
 probe=checks.decode_probe(ffmpeg,partial,logs/'decode-master.log',frames,width,height,audio=True)
 def audio_hash(file):
  cmd=[ffmpeg,'-hide_banner','-v','error','-i',str(file),'-map','0:a:0','-c','copy','-f','hash','-hash','sha256','-']
  return subprocess.check_output(cmd,text=True).strip()
 ah=audio_hash(partial)
 if ah!=audio_hash(approved):raise RuntimeError('Approved compressed audio changed.')
 partial.replace(final)
 report={'complete':True,'mode':args.mode,'output':str(final),'sha256':checks.sha256(final),'bytes':final.stat().st_size,'duration':duration,'frames':frames,'fps':fps,'width':width,'height':height,'audio_packet_hash':ah,'audio_unchanged':True,'probe':probe,'fingerprint':fp}
 write(out/'report.json',report);print(json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
