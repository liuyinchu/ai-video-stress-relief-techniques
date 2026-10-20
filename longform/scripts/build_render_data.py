#!/usr/bin/env python3
"""Package the selected longform timeline as a synchronous Multiplane preload.

This does not retime speech or manufacture alignment. Estimated input remains
marked estimated. All exported text changes are included in the blur cuts.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LF = ROOT/'longform'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--timeline',type=Path,default=LF/'content/estimated-timeline.json')
    ap.add_argument('--captions',type=Path,default=LF/'content/estimated-captions.json')
    ap.add_argument('--out',type=Path,default=LF/'content/render-data.js')
    ap.add_argument('--summary',type=Path,default=LF/'output/master-qa/render-data-summary.json')
    ap.add_argument('--action-cues',type=Path,default=LF/'content/action-cues.json')
    args=ap.parse_args()
    timeline=read(args.timeline); caption_source=read(args.captions)
    captions=caption_source if isinstance(caption_source,list) else caption_source['captions']
    fps=int(timeline.get('fps',30)); duration=float(timeline['duration'])
    if fps != 30: raise SystemExit('This master is authored for 30 fps; pass a 30 fps timeline.')
    chapters=[]
    for i,source in enumerate(timeline['chapters']):
        c={k:source[k] for k in ('id','title','start','end')}
        c.update(index=i,duration=source['end']-source['start'],silent=bool(source.get('silent',False)))
        c['segments']=[{**s,'beat':j,'start':int(s.get('start_frame',round(s['start']*fps)))/fps,'end':int(s.get('end_frame',round(s['end']*fps)))/fps} for j,s in enumerate(source['segments'])]
        if not c['segments'] or c['duration']<=0: raise SystemExit(f'Invalid chapter {c["id"]}')
        if chapters and c['start'] < chapters[-1]['end']-1e-5: raise SystemExit('Overlapping chapters')
        chapters.append(c)
    exported=[]; max_han=0
    for i,c in enumerate(captions):
        n=sum('\u4e00'<=ch<='\u9fff' for ch in c['text']);max_han=max(max_han,n)
        if n>24: raise SystemExit(f'Caption {c.get("id",i)} has {n} Han characters; split upstream at an aligned word boundary.')
        if '\n' in c['text']: raise SystemExit('Captions must be one line')
        sf=int(c.get('start_frame',round(float(c['start'])*fps)))
        ef=int(c.get('end_frame',round(float(c['end'])*fps)))
        if sf>=ef or sf<0 or ef>round(duration*fps)+1: raise SystemExit(f'Invalid caption interval: {c}')
        exported.append({**c,'start':sf/fps,'end':ef/fps,'start_frame':sf,'end_frame':ef})
    exported.sort(key=lambda c:(c['start_frame'],c['end_frame']))
    for a,b in zip(exported,exported[1:]):
        if a['end_frame']>b['start_frame']: raise SystemExit(f'Caption overlap: {a["id"]} / {b["id"]}')
    motion_remap={}; audio_cues=[]
    by_id={c['id']:c for c in chapters}
    word_cues={c['id']:c for c in timeline.get('word_cues',[])}
    def phrase_start(segment,term,fraction,cue_id=None):
        if cue_id in word_cues:
            cue=word_cues[cue_id]
            return int(cue.get('start_frame',round(cue['start']*fps)))/fps
        row=next((c for c in exported if c.get('segment_id')==segment['id'] and term in c['text']),None)
        return row['start'] if row else segment['start']+(segment['end']-segment['start'])*fraction
    def event(ident,kind,action,chapter,start,end):
        audio_cues.append({'id':ident,'kind':kind,'action':action,'chapter':chapter,
            'start':round(start,9),'duration':round(max(.05,end-start),9),
            'timing_source':'master animation mapping derived from '+timeline.get('timing_status','timeline'),
            'estimated':bool(timeline.get('estimated',False))})
    if 'breath' in by_id:
        seg=by_id['breath']['segments'][0]
        inhale=phrase_start(seg,'用鼻子',.4,'breath-inhale');topup=phrase_start(seg,'补一小口',.86,'breath-top-up')
        motion_remap[seg['id']]=[[seg['start'],0],[inhale,.4],[topup,.86],[seg['end'],1]]
        if len(by_id['breath']['segments'])>1:
            exhale=by_id['breath']['segments'][1]
            exhale_start=phrase_start(exhale,'用嘴慢慢呼出',0,'breath-first-exhale')
            motion_remap[exhale['id']]=[[exhale['start'],0],[exhale_start,0],[exhale['end'],1]]
            event('breath-first-exhale','breath','exhale','breath',exhale_start,exhale['end'])
    if 'paper' in by_id:
        seg=by_id['paper']['segments'][0]
        write=phrase_start(seg,'写下',.12,'paper-write');fold=phrase_start(seg,'揉成纸团',.65,'paper-crumple');toss=phrase_start(seg,'丢进纸篓',.85,'paper-toss')
        write_end=min(phrase_start(seg,'不用修饰',.60),fold-1/fps)
        motion_remap[seg['id']]=[[seg['start'],0],[write,.015/.95],[write_end,.24/.95],[fold,.27/.95],
            [max(fold,toss-1/fps),.64/.95],[toss,.72/.95],[seg['end'],1]]
        event('paper-crumple','paper','crumple','paper',fold,toss)
        landing=toss+(seg['end']-toss)*(.88-.72)/(.95-.72)
        event('paper-toss','paper','toss','paper',toss,landing)
        event('paper-land','paper','land','paper',landing,landing+.18)
        if len(by_id['paper']['segments'])>1:
            tear=by_id['paper']['segments'][1];start=phrase_start(tear,'慢慢撕',.08,'paper-tear');end=phrase_start(tear,'动作有开头',.70)
            motion_remap[tear['id']]=[[tear['start'],0],[start,.08],[end,.70],[tear['end'],1]]
            event('paper-tear','paper','tear','paper',start,end)
    if 'order' in by_id and len(by_id['order']['segments'])>1:
        first,second=by_id['order']['segments'][:2]
        # actions.js moveObj: p_start=.19+index*.077; p_end=p_start+.116.
        # First beat maps to p 0..0.60, second beat to p 0.60..0.96.
        for name,index in [('book',0),('cup',4)]:
            p_end=.19+index*.077+.116
            seg=first if p_end<=.60 else second
            fraction=p_end/.60 if p_end<=.60 else (p_end-.60)/.36
            at=seg['start']+(seg['end']-seg['start'])*fraction
            event('order-'+name+'-place','order',name+'_place','order',at,at+.16)
    for sid,points in motion_remap.items():
        if any(b[0]<a[0]-1e-7 or b[1]<a[1]-1e-7 for a,b in zip(points,points[1:])):
            raise SystemExit(f'Non-monotonic motion mapping for {sid}; inspect caption anchors.')
    cue_document={'schema':'longform-action-cues/1','estimated':bool(timeline.get('estimated',False)),
        'timing_status':timeline.get('timing_status','unknown'),'duration':duration,
        'motion_remap':motion_remap,'audio_cues':sorted(audio_cues,key=lambda c:c['start']),
        'word_cues_used':sorted(word_cues),
        'note':'start/duration are seconds on the master timeline; mappings are shared by master.js. Original ASR timeline is unchanged.'}
    args.action_cues.parent.mkdir(parents=True,exist_ok=True)
    args.action_cues.write_text(json.dumps(cue_document,ensure_ascii=False,indent=2)+'\n')
    transitions=[]
    for a,b in zip(chapters,chapters[1:]):
        mid=(a['end']+b['start'])/2
        transitions.append({'from':a['id'],'to':b['id'],'start':a['end']-.4,'mid':mid,'end':b['start']+.4})
    cuts={0.,duration}
    for c in chapters:
        cuts.update([c['start'],c['end']])
        for s in c['segments']: cuts.update([s['start'],s['end']])
    for c in exported: cuts.update([c['start'],c['end']])
    for tr in transitions:cuts.add(tr['mid'])
    cuts=sorted({round(x,9) for x in cuts if 0<=x<=duration})
    data={'schema':'longform-render/1','title':timeline['title'],
        'timing_status':timeline.get('timing_status','unknown'),'estimated':bool(timeline.get('estimated',False)),
        'width':2560,'height':1440,'logical_width':1920,'logical_height':1080,'fps':fps,
        'duration':duration,'frame_count':round(duration*fps),'chapters':chapters,'captions':exported,
        'transitions':transitions,'cuts':cuts,'motion_remap':motion_remap,'audio_cues':cue_document['audio_cues'],
        'caption_boundaries':sorted({v for c in exported for v in (c['start'],c['end'])}),
        'source':{'timeline':str(args.timeline.relative_to(ROOT)) if args.timeline.is_relative_to(ROOT) else str(args.timeline),
            'captions':str(args.captions.relative_to(ROOT)) if args.captions.is_relative_to(ROOT) else str(args.captions),
            'timeline_sha256':hashlib.sha256(args.timeline.read_bytes()).hexdigest(),
            'captions_sha256':hashlib.sha256(args.captions.read_bytes()).hexdigest()}}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text('/* Generated by build_render_data.py; do not hand edit. */\nwindow.LONG_RENDER_DATA = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
    keyframes=[]
    for c in chapters:
        for j,s in enumerate(c['segments']):
            if j==0 or (c['id'] in ('breath','cold','ear','paper','fractal','order') and j<len(c['segments'])):
                keyframes.append({'chapter':c['id'],'beat':j,'time':round((s['start']+s['end'])/2*fps)/fps})
    summary={k:data[k] for k in ('schema','timing_status','estimated','duration','frame_count','source')}
    summary.update(chapters=len(chapters),captions=len(exported),maximum_caption_han=max_han,cuts=len(cuts),audio_cues=len(audio_cues),keyframes=keyframes)
    args.summary.parent.mkdir(parents=True,exist_ok=True);args.summary.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='keyframes'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
