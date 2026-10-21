"""Run exports independently of SSH, recording the phase and process exit."""
import json,os,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[2];base=root/'longform/onetake';mode=sys.argv[1] if len(sys.argv)>1 else 'all'
if mode not in ('preview','final','all'):raise SystemExit('mode must be preview, final or all')
status=base/'output'/f'{mode}-process.json';env=os.environ.copy();env['PATH']='/opt/homebrew/opt/node@24/bin:'+env.get('PATH','')
def save(data):
 temp=status.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2)+'\n');temp.replace(status)
start=time.time();phases=['preview','final'] if mode=='all' else [mode];results=[]
for phase in phases:
 save({'mode':mode,'phase':phase,'state':'running','pid':os.getpid(),'started':start,'results':results})
 rc=subprocess.call([str(root/'.tools/venv/bin/python'),str(base/'render.py'),'--mode',phase,'--resume'],cwd=root,env=env)
 results.append({'phase':phase,'exit_code':rc,'ended':time.time()})
 if rc:save({'mode':mode,'phase':phase,'state':'failed','pid':os.getpid(),'started':start,'ended':time.time(),'results':results});raise SystemExit(rc)
save({'mode':mode,'state':'completed','pid':os.getpid(),'started':start,'ended':time.time(),'results':results})
