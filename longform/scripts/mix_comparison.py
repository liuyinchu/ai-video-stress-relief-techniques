#!/usr/bin/env python3
"""Create equal-loudness listening comparisons from the actual long-film stems."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import numpy as np
import score


def excerpt(path,start,duration,ffmpeg):
    run=subprocess.run([ffmpeg,'-v','error','-nostdin','-ss',f'{start:.9f}','-i',str(path),
                        '-t',f'{duration:.9f}','-ar','48000','-ac','2','-f','f32le','-'],capture_output=True,check=True)
    return np.frombuffer(run.stdout,dtype='<f4').reshape(-1,2).copy()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--timeline',type=Path,default=score.ROOT/'content/timeline.json')
    p.add_argument('--start',type=float);p.add_argument('--end',type=float)
    a=p.parse_args();data=json.loads(a.timeline.read_text())
    if data.get('estimated',True):raise ValueError('Actual timeline required')
    start=a.start if a.start is not None else float(data['music']['title_at'])
    breath=next(c for c in data['chapters'] if c['id']=='breath')
    end=a.end if a.end is not None else float(breath['segments'][min(2,len(breath['segments'])-1)]['end'])+.2
    duration=end-start;ffmpeg=score.ffmpeg_binary();folder=score.ROOT/'assets/audio'
    voice=excerpt(folder/'narration.wav',start,duration,ffmpeg)
    music=excerpt(folder/'music-in-mix.wav',start,duration,ffmpeg)
    sfx=excerpt(folder/'sfx-in-mix.wav',start,duration,ffmpeg)
    n=min(len(voice),len(music),len(sfx));voice=voice[:n];music=music[:n];sfx=sfx[:n]
    variants=[]
    with tempfile.TemporaryDirectory(prefix='comparison-',dir=score.SCRATCH) as d:
        d=Path(d)
        for name,label,lift,note in [
            ('balanced','正式平衡版',0,'正式片采用此比例；全片目标人声比音乐高约10 dB。'),
            ('forward','音乐再靠前一点',1.5,'同一段真实旁白与配乐；仅将音乐增加1.5 dB，整体响度再匹配。')]:
            samples=voice+music*10**(lift/20)+sfx
            fade=min(int(.02*score.SR),len(samples)//2)
            samples[:fade]*=np.linspace(0,1,fade)[:,None];samples[-fade:]*=np.linspace(1,0,fade)[:,None]
            peak=float(np.max(abs(samples)))
            if peak>.96:samples*=.96/peak
            premix=d/f'{name}.wav';score.write_wav(premix,samples)
            output=score.ROOT/f'output/mix-demo-{name}.wav'
            loudness=score.loudnorm(premix,output,ffmpeg,-15.5,-1.7)
            variants.append({'label':label,'path':output.name,'note':note,'music_extra_db':lift,'normalization':loudness})
    manifest={'title':'真实旁白与音乐比例对比','timing_status':data['timing_status'],'estimated':False,
              'start':start,'end':start+n/score.SR,'duration':n/score.SR,'variants':variants,
              'note':'两个试听使用同一段正式MiniMax旁白，整体都匹配到约-15.5 LUFS；未修改正式总混。'}
    (score.ROOT/'output/mix-comparison.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(manifest,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
