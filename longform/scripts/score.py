#!/usr/bin/env python3
"""Original long-form cinematic score, effects, demo and speech-aware mixing.

All outputs default inside longform/. No pre-existing short-film file is changed.
Requires NumPy and FFmpeg (or imageio-ffmpeg). Examples:
  score.py demo
  score.py render --timeline longform/content/timeline.json
  score.py mix --timeline longform/content/timeline.json
"""
from __future__ import annotations
import argparse
from collections import deque
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import wave
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / '.scratch'
SCRATCH.mkdir(parents=True, exist_ok=True)
SR = 48000
BPM = 108.0
BEAT = 60 / BPM
BAR = 4 * BEAT
SEED = 102021
CHORDS = {
    'Dm9': [38, 57, 60, 64, 65], 'Bbmaj9': [34, 53, 57, 60, 62],
    'Fmaj9': [41, 57, 60, 64, 67], 'Cadd9': [36, 55, 60, 62, 64],
    'Gm9': [43, 53, 57, 62, 65], 'Asus7': [45, 55, 57, 62, 64],
    'Dsus2': [38, 57, 62, 64, 69], 'Ebmaj7': [39, 55, 58, 62, 67],
}
PROGRESSIONS = {
    'intro': ['Dm9', 'Bbmaj9', 'Gm9', 'Asus7'],
    'breath': ['Dm9', 'Bbmaj9', 'Fmaj9', 'Cadd9'],
    'cool': ['Bbmaj9', 'Fmaj9', 'Cadd9', 'Dm9'],
    'ear': ['Gm9', 'Dm9', 'Bbmaj9', 'Asus7'],
    'shake': ['Fmaj9', 'Cadd9', 'Dm9', 'Bbmaj9'],
    'paper': ['Dm9', 'Bbmaj9', 'Gm9', 'Asus7'],
    'nature': ['Bbmaj9', 'Fmaj9', 'Cadd9', 'Gm9'],
    'order': ['Dm9', 'Fmaj9', 'Bbmaj9', 'Cadd9'],
    'outro': ['Dm9', 'Bbmaj9', 'Fmaj9', 'Dsus2'],
}
# Arrangement palette: pad, pulse, pluck, metallic colour, percussion.
PALETTES = {
    'intro': (.85, .30, .65, .35, .15), 'breath': (1.00, .55, .80, .22, .30),
    'cool': (.80, .72, .90, .80, .35), 'ear': (.75, .55, .95, .10, .55),
    'shake': (.80, 1.00, .70, .28, .85), 'paper': (.70, .75, .85, .12, .70),
    'nature': (1.12, .12, .68, .65, .10), 'order': (.90, .82, .95, .38, .58),
    'outro': (1.05, .38, 1.00, .70, .18),
}
# Newly composed eight-bar theme. Values are beats within the phrase, MIDI pitch,
# and approximate ringing duration in beats. Under speech use deliberate fragments.
THEME = [
    (0, 62, .9), (1, 65, .5), (1.5, 69, .5), (2, 64, 1.0),
    (4, 65, .9), (5, 62, .5), (5.5, 57, .5), (6, 60, 1.0),
    (8, 57, .5), (8.5, 60, .5), (9, 65, 1.5), (10.5, 64, .5), (11, 62, .5),
    (12, 64, .9), (13, 67, .5), (13.5, 62, .5), (14, 60, 1.0),
    (16, 62, .9), (17, 65, .5), (17.5, 69, .5), (18, 72, .75), (18.75, 69, .25),
    (20, 70, .9), (21, 69, .5), (21.5, 67, .5), (22, 65, 1.0),
    (24, 65, .9), (25, 64, .5), (25.5, 62, .5), (26, 60, 1.0),
    (28, 64, .75), (28.75, 62, .25), (29, 57, 1.0), (30.5, 62, 1.4),
]


def ffmpeg_binary(explicit=None):
    if explicit:
        return explicit
    if os.environ.get('FFMPEG_BINARY'):
        return os.environ['FFMPEG_BINARY']
    if shutil.which('ffmpeg'):
        return shutil.which('ffmpeg')
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def write_wav(path, samples):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    data = samples if samples.ndim == 2 else samples[:, None]
    with wave.open(str(path), 'wb') as out:
        out.setnchannels(data.shape[1]); out.setsampwidth(3); out.setframerate(SR)
        for start in range(0, len(data), SR * 4):
            pcm = np.rint(np.clip(data[start:start + SR * 4], -1, 1 - 2**-23) * (2**23 - 1)).astype(np.int32).reshape(-1)
            packed = np.empty((len(pcm), 3), dtype=np.uint8)
            for byte in range(3):
                packed[:, byte] = (pcm >> (8 * byte)) & 255
            out.writeframes(packed.tobytes())


def read_audio(path, ffmpeg):
    run = subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-nostdin', '-i', str(path),
                          '-vn', '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True)
    if run.returncode:
        raise RuntimeError(run.stderr.decode(errors='replace'))
    return np.frombuffer(run.stdout, dtype='<f4').reshape(-1, 2).copy()


def fit_length(x, seconds):
    target = np.zeros((round(seconds * SR), 2), np.float32)
    target[:min(len(target), len(x))] = x[:len(target)]
    return target


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-12))


def measure(x):
    return {'peak_dbfs': round(float(db(np.max(np.abs(x)))), 3),
            'rms_dbfs': round(float(db(np.sqrt(np.mean(x*x, dtype=np.float64)))), 3)}


def add(dst, source, start, gain=1, pan=0):
    offset = round(start * SR); trim = max(0, -offset); offset = max(0, offset)
    size = min(len(source) - trim, len(dst) - offset)
    if size <= 0: return
    s = source[trim:trim + size]
    if s.ndim == 1:
        angle = (np.clip(pan, -1, 1) + 1) * np.pi / 4
        dst[offset:offset + size, 0] += s * gain * np.cos(angle)
        dst[offset:offset + size, 1] += s * gain * np.sin(angle)
    else:
        dst[offset:offset + size] += s * gain


def hz(note):
    return 440 * 2 ** ((note - 69) / 12)


def envelope(t, length, attack=.04, release=.6):
    a = np.sin(np.minimum(t / max(attack, .001), 1) * np.pi / 2) ** 2
    r = np.sin(np.minimum(np.maximum(length - t, 0) / max(release, .001), 1) * np.pi / 2) ** 2
    return a * r


def pad(notes, duration, rng, brightness=.55):
    t = np.arange(round(duration * SR)) / SR
    out = np.zeros((len(t), 2), np.float32)
    env = envelope(t, duration, .26, .9)
    for i, note in enumerate(notes[1:]):
        f = hz(note); phase = rng.uniform(0, 2*np.pi)
        drift = .011*np.sin(2*np.pi*(.11+i*.017)*t)
        body = (np.sin(2*np.pi*f*t+phase+drift)
                + .22*brightness*np.sin(2*np.pi*2*f*t+phase)
                + .09*brightness*np.sin(2*np.pi*3*f*t+phase))
        width = np.sin(2*np.pi*f*1.0023*t+phase+drift)*.20
        gain = [.7, .52, .36, .26][i]
        out[:, 0] += ((body + width)*env*gain*.024).astype(np.float32)
        out[:, 1] += ((body + np.sin(2*np.pi*f*.9977*t+phase)*.20)*env*gain*.024).astype(np.float32)
    return out


def pluck(note, ring=.7, metal=False):
    length = min(3.5, max(.65, ring*2.0))
    t = np.arange(round(length * SR)) / SR; f = hz(note)
    attack = 1-np.exp(-t/.004)
    if metal:
        x = (.78*np.sin(2*np.pi*f*t)*np.exp(-t/(ring*.78))
             + .15*np.sin(2*np.pi*f*2.76*t)*np.exp(-t/.14)
             + .045*np.sin(2*np.pi*f*5.4*t)*np.exp(-t/.045))
    else:
        x = (np.sin(2*np.pi*f*t)*np.exp(-t/ring)
             + .24*np.sin(2*np.pi*f*2*t)*np.exp(-t/(ring*.34))
             + .075*np.sin(2*np.pi*f*3*t)*np.exp(-t/(ring*.15)))
    return (x*attack*envelope(t, length, .003, .18)).astype(np.float32)


def space_note(dst, note, start, gain, pan, ring=.6, metal=False, echo=.22):
    sound = pluck(note, ring, metal)
    add(dst, sound, start, gain, pan)
    add(dst, sound, start+.043, gain*.10, -pan)
    add(dst, sound, start+BEAT*.75, gain*echo, -.65*pan)
    add(dst, sound, start+BEAT*1.5, gain*echo*.43, .5*pan)
    add(dst, sound, start+BEAT*2.25, gain*echo*.16, -pan)


def bass(note, duration=.65):
    t = np.arange(round(duration*SR))/SR; f = hz(note)
    body = np.sin(2*np.pi*f*t)+.24*np.sin(2*np.pi*2*f*t)+.05*np.sin(2*np.pi*3*f*t)
    return (body*(1-np.exp(-t/.012))*np.exp(-t/.30)*envelope(t,duration,.012,.15)).astype(np.float32)


def noise(length, rng, low=200, high=2500):
    n = round(length*SR); f = np.fft.rfftfreq(n,1/SR)
    spec = np.fft.rfft(rng.standard_normal(n))
    filt = (1-np.exp(-(f/max(low,1))**2))*np.exp(-(f/high)**4)
    x = np.fft.irfft(spec*filt,n=n); x /= max(float(np.std(x)),1e-9)
    return x.astype(np.float32)


def brush(length, rng, high=1800, swelling=False):
    t = np.arange(round(length*SR))/SR
    env = np.sin(np.pi*t/length)**2 if swelling else (1-np.exp(-t/.004))*np.exp(-t/(length*.19))
    return noise(length,rng,160,high)*env.astype(np.float32)


def section_kind(item, index):
    s = (str(item.get('id',''))+' '+str(item.get('title',''))+' '+str(item.get('label',''))).lower()
    names = {'intro':['intro','hook','title','opening','开场','序章','标题'], 'outro':['outro','closing','片尾','结尾'],
             'breath':['breath','呼吸','叹气'], 'cool':['cool','cold','冷','凉'],
             'ear':['ear','耳'], 'shake':['shake','抖','肩'], 'paper':['paper','纸'],
             'nature':['nature','fractal','自然','分形'], 'order':['order','tidy','整理']}
    for key, words in names.items():
        if any(word in s for word in words): return key
    return ['breath','cool','ear','shake','paper','nature','order'][index%7]


def load_plan(path=None, duration=None, title_at=17):
    data = json.loads(Path(path).read_text()) if path else {}
    seconds = float(duration or data.get('duration',data.get('duration_seconds',360)))
    if seconds < 2 or seconds > 1200: raise ValueError('Duration must be 2–1200 seconds')
    music = data.get('music',{})
    title = float(music.get('title_at', data.get('title_at',title_at)))
    raw = data.get('chapters',data.get('stations',[])); chapters=[]
    for i,item in enumerate(raw):
        start=float(item.get('start',0)); end=float(item.get('end',start+item.get('duration',0)))
        if end<=start: continue
        chapters.append({**item,'start':start,'end':min(end,seconds),'kind':section_kind(item,i)})
    if not chapters:
        chapters=[{'id':'intro','kind':'intro','start':0,'end':min(title,seconds)}]
        if seconds<=45:
            chapters.append({'id':'breath','kind':'breath','start':min(title,seconds),'end':seconds})
        else:
            body_start=title; body_end=max(body_start,seconds-18)
            for i,key in enumerate(['breath','cool','ear','shake','paper','nature','order']):
                chapters.append({'id':key,'kind':key,'start':body_start+(body_end-body_start)*i/7,
                                 'end':body_start+(body_end-body_start)*(i+1)/7})
            chapters.append({'id':'outro','kind':'outro','start':body_end,'end':seconds})
    chapters.sort(key=lambda x:x['start'])
    return {'duration':seconds,'title_at':title,'chapters':chapters,'source':data}


def active_chapter(plan,time):
    eligible=[c for c in plan['chapters'] if c['start']<=time<c['end']]
    if eligible: return eligible[-1]
    return min(plan['chapters'],key=lambda c:abs(c['start']-time))


def make_score(plan,seed=SEED):
    duration=plan['duration'];title=plan['title_at'];rng=np.random.default_rng(seed)
    music=np.zeros((round(duration*SR),2),np.float32);events=[]
    # Free-time prologue. Its 17-second title hit becomes the metrical origin.
    intro_end=min(title,duration)
    for i,start in enumerate(np.arange(-.4,intro_end,4.3)):
        chord=CHORDS[PROGRESSIONS['intro'][i%4]]
        add(music,pad(chord,5.2,rng,.3+.06*i),float(start),.8)
        if start>1:
            space_note(music,[62,65,69,64][i%4],float(start)+.7,.035,(-1)**i*.25,.95,False,.18)
    for i,start in enumerate(np.arange(5.7,max(5.7,intro_end-1),BEAT*2)):
        add(music,bass(38,.75),float(start),.033*(.65+.35*i/max(1,int(intro_end/BEAT/2))),0)
    if title<duration:
        t=np.arange(round(1.6*SR))/SR
        impact=np.sin(2*np.pi*(52*t+18*(1-np.exp(-t/.08))*.08))*np.exp(-t/.37)*(1-np.exp(-t/.006))
        add(music,impact,title,.095,0)
        space_note(music,62,title,.09,-.15,1.25,False,.28)
        space_note(music,74,title,.038,.28,1.0,True,.25)
        events.append({'time':title,'event':'title downbeat: D bass, theme, open stereo field'})
    bars=max(0,math.ceil((duration-title)/BAR))
    cadence_start=(title+math.floor((duration-11.1-title)/BAR)*BAR) if duration>45 else duration
    for bar in range(bars):
        start=title+bar*BAR; chapter=active_chapter(plan,start+.1);kind=chapter['kind']
        if kind=='intro': kind='breath'
        palette=PALETTES[kind];progress=PROGRESSIONS[kind]
        first_bar=max(0,math.ceil((chapter['start']-title-.1)/BAR-1e-9))
        local_bar=max(0,bar-first_bar)
        chord_name=progress[(local_bar//2)%len(progress)];chord=list(CHORDS[chord_name])
        inversion=(local_bar//8)%3
        if inversion==1: chord=[chord[0]]+sorted([chord[1]+12]+chord[2:])
        elif inversion==2: chord=[chord[0]]+sorted(chord[1:4]+[chord[4]-12])
        withdrawn=local_bar%16 in [12,13]
        # Last cadence is open D; no final percussive jump.
        if start>duration-5: chord_name='Dsus2';chord=CHORDS[chord_name]
        if local_bar%2==0:
            next_boundary=title+math.ceil((chapter['end']-title-.1)/BAR-1e-9)*BAR
            pad_length=max(.95,min(BAR*2+.95,next_boundary-start+.75))
            add(music,pad(chord,pad_length,rng,.42+palette[3]*.3),start-.08,palette[0])
            events.append({'time':round(start,3),'chapter':chapter.get('id',kind),'chord':chord_name,
                           'midi_voicing':chord,'inversion':inversion,'bass_reduced':withdrawn,
                           'arpeggio_withdrawn':withdrawn,'layer_return':local_bar%16==14})
        # Half-time bass creates forward motion without an anxious heartbeat.
        pulse_steps=[(0,.066),(2,.047)]
        if kind in ['shake','order'] and bar%4 in [1,3]: pulse_steps.append((3.25,.030))
        for step,gain in pulse_steps:
            if bar%8==7 and step==2: continue
            if start+step*BEAT>duration-3.5: continue
            note=chord[0] if step!=2 or bar%2==0 else chord[0]+7
            add(music,bass(note,.82),start+step*BEAT,gain*palette[1]*(.3 if withdrawn else 1)*(1+rng.uniform(-.065,.065)),0)
        # An evolving arpeggio uses inversion and rests, not a copied loop.
        pattern=[(.75,1),(2.5,3)] if bar%2==0 else [(1.25,2),(3.25,4)]
        if bar%8 in [3,7]: pattern=pattern[:1]
        if (kind=='nature' and bar%2) or withdrawn: pattern=[]
        for step,index in pattern:
            if start+step*BEAT>duration-4:continue
            pitch=chord[index]+(12 if (bar//8)%3==1 and index<3 else 0)
            space_note(music,pitch,start+step*BEAT+rng.uniform(-.009,.009),
                       .027*palette[2]*(1+rng.uniform(-.08,.08)),(-1)**(bar+index)*.34,
                       .52+.12*palette[3],palette[3]>.6,.18)
        # Dry, quiet material accents change every two bars.
        for step in ([1.5,3.5] if bar%4 in [0,1] else [2.75]):
            if start+step*BEAT>duration-5:continue
            tick=pluck(50+(bar%3)*3,.13,True)
            add(music,tick,start+step*BEAT,.012*palette[4],(-1)**bar*.32)
        if bar%4==3 and palette[4]>.3 and start<duration-5:
            add(music,brush(.23,rng,2500),start+3.5*BEAT,.0038*palette[4],.28)
        # Theme appears fully at the title and return; in the body, fragments
        # rotate every eight bars so the narrator retains the foreground.
        if local_bar%8==0 and start<min(duration-7,cadence_start) and (bar==0 or start>=title+8*BAR):
            full=(bar==0)
            notes=THEME if full else [THEME[j] for j in ([0,1,2,3,14,16] if (bar//8)%2 else [0,2,3,17,18,20])]
            for pos,note,length in notes:
                at=start+pos*BEAT
                if at>duration-2.5 or at>=cadence_start or (at>=chapter['end'] and not full):continue
                if not full and at>=start+8*BAR:continue
                gain=(.064 if full else .040)*(.92 if kind=='nature' else 1)
                register=12 if kind=='cool' and not full else 0
                space_note(music,note+register,at if pos==0 else at+rng.uniform(-.007,.007),
                           gain*(1+rng.uniform(-.06,.06)),(-1)**int(pos)*.23,
                           max(.45,length*BEAT*.9),kind in ['cool','nature'],.24)
    # Cadence answers the initial motif instead of fading mid-pattern.
    if duration>45:
        outro_start=max(title,cadence_start)
        for pos,note,length in [(0,62,1),(1,65,.5),(1.5,69,.5),(2,64,1),(4,65,1),(6,64,1),(8,62,3.2)]:
            space_note(music,note,outro_start+pos*BEAT,.055,(-1)**int(pos)*.2,length*BEAT,False,.25)
        add(music,pad(CHORDS['Dsus2'],7.2,rng,.35),duration-7.4,1.1)
        events.append({'time':outro_start,'event':'theme return and open D cadence'})
    # Smooth the master edges; music remains at a useful standalone stem level.
    fade_in=min(len(music),round(.7*SR)); music[:fade_in]*=np.linspace(0,1,fade_in)[:,None]
    fade_out=min(len(music),round(3.4*SR)); music[-fade_out:]*=(np.cos(np.linspace(0,np.pi/2,fade_out))**2)[:,None]
    rms=float(np.sqrt(np.mean(music*music, dtype=np.float64)));peak=float(np.max(np.abs(music)))
    music*=min(10**(-23/20)/max(rms,1e-9),10**(-5/20)/max(peak,1e-9))
    return music,events


def make_effects(plan,seed=SEED+1):
    rng=np.random.default_rng(seed);duration=plan['duration'];out=np.zeros((round(duration*SR),2),np.float32);events=[]
    title=plan['title_at']
    if title<duration:
        add(out,brush(1.35,rng,1200,True),title-1.25,.012,0)
        space_note(out,86,title,.018,.3,.8,True,.13)
        events.append({'time':title,'kind':'title','sound':'warm air lift and restrained glint'})
    for i,chapter in enumerate(plan['chapters']):
        key=chapter['kind'];start=float(chapter['start'])
        if key=='intro' or start<1:continue
        if key=='breath':
            add(out,brush(1.8,rng,1100,True),start-.35,.010,-.12)
        elif key=='cool':
            for j,note in enumerate([86,81,74]):space_note(out,note,start+j*.13,.012-j*.002,(-1)**j*.35,.5,True,.2)
        elif key=='ear':
            add(out,brush(.42,rng,900),start+.04,.008,-.25);space_note(out,62,start,.023,.1,.3,False,.08)
        elif key=='shake':
            for j in range(3):add(out,brush(.22,rng,1600),start+j*.19,.008,(-1)**j*.45)
        elif key=='paper':
            for j in range(6):add(out,brush(.09,rng,3000),start+j*.085+rng.uniform(0,.025),.006,(-1)**j*.18)
        elif key=='nature':
            add(out,brush(2.6,rng,1500,True),start-.6,.008,.25);space_note(out,81,start+.35,.010,-.3,1.2,True,.28)
        elif key=='order':
            for j,note in enumerate([62,65,69]):space_note(out,note,start+j*.16,.020-j*.002,-.3+j*.3,.25,False,.1)
        elif key=='outro':
            add(out,brush(1.8,rng,850,True),start-.45,.008,0)
        events.append({'time':start,'kind':key,'sound':'chapter colour accent; no alarm or impact blast'})
    # Optional exact, director-reviewed action cues, separate from transitions.
    for cue in plan['source'].get('audio_cues',[]):
        start=float(cue['start']);kind=cue.get('kind','air');length=float(cue.get('duration',.8));action=cue.get('action','')
        if kind=='paper' and action in ['','crumple']:
            count=max(3,int(length/.12))
            for j in range(count):
                at=start+j*max(0,length-.09)/max(1,count-1)
                add(out,brush(min(.09,length),rng,2600),at,.009*(.7+.3*np.sin(np.pi*(j+1)/(count+1))),(-1)**j*.15)
        elif action=='toss':add(out,brush(length,rng,1600,True),start,.004,.2)
        elif action=='land':
            hit=bass(45,max(.06,length))[:round(length*SR)]
            add(out,hit,start,.020,-.1)
        elif action=='tear':
            t=np.arange(round(length*SR))/SR
            friction=noise(length,rng,350,2600)*np.sin(np.pi*t/length)**2
            friction*=.55+.45*np.sin(2*np.pi*5.7*t)**2
            add(out,friction,start,.005,-.1)
        elif action in ['book_place','cup_place']:
            sound=pluck(50 if action=='book_place' else 81,.07,action=='cup_place')[:round(length*SR)]
            t=np.arange(len(sound))/SR;sound*=envelope(t,length,.003,min(.035,length/3))
            add(out,sound,start,.028 if action=='book_place' else .024,-.15 if action=='book_place' else .18)
        else:add(out,brush(length,rng,1000,True),start,.006,0)
        events.append({'time':start,'duration':length,'id':cue.get('id'),'kind':kind,'action':action,
                       'sound':'explicit director-reviewed shared action cue','timing_source':cue.get('timing_source')})
    peak=float(np.max(abs(out)))
    if peak>10**(-15/20):out*=10**(-15/20)/peak
    return out,events


def loudnorm(source,output,ffmpeg,target=-15.5,true_peak=-1.7):
    def parse(log):
        chunks=re.findall(r'\{\s*"input_i".*?\}',log,re.S)
        if not chunks:raise RuntimeError(log[-2000:])
        return json.loads(chunks[-1])
    spec=f'loudnorm=I={target}:TP={true_peak}:LRA=11:print_format=json'
    first=subprocess.run([ffmpeg,'-hide_banner','-nostdin','-i',str(source),'-af',spec,'-f','null','-'],capture_output=True,text=True,check=True)
    x=parse(first.stderr)
    if x['input_i']=='-inf':raise ValueError('Cannot normalize silence')
    second=(f'loudnorm=I={target}:TP={true_peak}:LRA=11:measured_I={x["input_i"]}:'
            f'measured_TP={x["input_tp"]}:measured_LRA={x["input_lra"]}:'
            f'measured_thresh={x["input_thresh"]}:offset={x["target_offset"]}:linear=true:print_format=json')
    output.parent.mkdir(parents=True,exist_ok=True)
    run=subprocess.run([ffmpeg,'-y','-hide_banner','-nostdin','-i',str(source),'-af',second,
                        '-ar',str(SR),'-ac','2','-c:a','pcm_s24le',str(output)],capture_output=True,text=True,check=True)
    return parse(run.stderr)


# BS.1770 K weighting at 48 kHz. FFmpeg executes the two biquads continuously;
# only compact 400 ms / 100 ms-hop energy windows are retained in Python.
K_FILTER=('biquad=b0=1.53512485958697:b1=-2.69169618940638:b2=1.19839281085285:'
          'a0=1:a1=-1.69065929318241:a2=0.73248077421585,'
          'biquad=b0=1:b1=-2:b2=1:a0=1:a1=-1.99004745483398:a2=0.99007225036621')


def k_levels(path,ffmpeg):
    process=subprocess.Popen([ffmpeg,'-v','error','-nostdin','-i',str(path),'-af',K_FILTER,
                              '-ar',str(SR),'-ac','2','-f','f32le','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    size=4800*2*4;queue=deque(maxlen=4);values=[];centers=[];frame=0
    while True:
        chunk=process.stdout.read(size)
        if not chunk:break
        data=np.frombuffer(chunk[:len(chunk)//8*8],dtype='<f4').reshape(-1,2)
        queue.append(float(np.mean(np.sum(data.astype(np.float64)**2,axis=1))))
        if len(queue)==4:
            values.append(-.691+10*np.log10(max(sum(queue)/4,1e-14)));centers.append((frame-1)*.1)
        frame+=1
    error=process.stderr.read();status=process.wait()
    if status:raise RuntimeError(error.decode(errors='replace'))
    return np.asarray(centers),np.asarray(values)


def voice_track(plan,ffmpeg):
    duration=plan['duration'];out=np.zeros((round(duration*SR),2),np.float32);clips=[]
    for seg in plan['source'].get('audio_segments',plan['source'].get('narration',plan['source'].get('segments',[]))):
        source=seg.get('audio',seg.get('voice_file'))
        if not source:continue
        path=Path(source)
        if not path.is_absolute():
            candidates=[ROOT/path,ROOT.parent/path,Path.cwd()/path]
            path=next((x for x in candidates if x.is_file()),candidates[0])
        if not path.is_file():raise FileNotFoundError(path)
        checksum=hashlib.sha256(path.read_bytes()).hexdigest()
        expected_sha=seg.get('source_sha256',seg.get('sha256',seg.get('audio_sha256')))
        if expected_sha and expected_sha!=checksum:raise ValueError(f'Voice checksum mismatch: {path}')
        audio=read_audio(path,ffmpeg);start=float(seg.get('voice_start',seg.get('start',0)))
        end=start+len(audio)/SR
        if end>duration+.025:raise ValueError(f'Voice {seg.get("id")} overruns the film: {end:.3f}s')
        if seg.get('end') is not None and end>float(seg['end'])+.08:
            raise ValueError(f'Voice {seg.get("id")} overruns its chapter slot: {end:.3f}s > {seg["end"]}')
        add(out,audio,start,10**(float(seg.get('gain_db',0))/20))
        clips.append({'id':seg.get('id'), 'path':str(path), 'sha256':checksum, 'start':start,'end':end,'duration':len(audio)/SR})
    if not clips:raise ValueError('No real narration audio found; mix refuses to synthesize or invent speech')
    # Normalize narration alone, before any music is added.
    block=960;padded=np.pad(out,((0,(-len(out))%block),(0,0)))
    energy=np.sqrt(np.mean(padded.reshape(-1,block,2)**2,axis=(1,2),dtype=np.float64))
    active=energy>max(.0005,float(np.max(energy))*.04)
    active_rms=float(np.sqrt(np.mean(energy[active]**2)))
    gain=min(10**(-20/20)/max(active_rms,1e-9),10**(-3/20)/max(float(np.max(abs(out))),1e-9))
    out*=gain
    return out,clips,float(db(gain))


def ducking(voice):
    block=960;padded=np.pad(voice,((0,(-len(voice))%block),(0,0)))
    rms=np.sqrt(np.mean(padded.reshape(-1,block,2)**2,axis=(1,2),dtype=np.float64))
    activity=np.clip((rms-.004)/.018,0,1)
    desired=1-activity*(1-10**(-3/20));result=np.ones(len(desired));current=1
    for i,value in enumerate(desired):
        tau=.045 if value<current else .45
        a=np.exp(-.02/tau);current=a*current+(1-a)*value;result[i]=current
    return np.interp(np.arange(len(voice)),np.arange(len(result))*block+block/2,result).astype(np.float32)


def mix(plan,args):
    ffmpeg=ffmpeg_binary(args.ffmpeg);duration=plan['duration']
    if plan.get('action_metadata') and args.sfx.resolve()==(ROOT/'assets/audio/sfx.wav').resolve():
        effects_report=ROOT/'output/effects-report.json'
        if not effects_report.is_file():raise ValueError('Render actual effects before mixing')
        recorded=json.loads(effects_report.read_text())
        if recorded.get('shared_action_cues',{}).get('sha256')!=plan['action_metadata']['sha256']:
            raise ValueError('SFX action-cue hash is stale; rerun score.py effects with current actual cues')
        if abs(float(recorded.get('duration',-1))-duration)>1/SR:
            raise ValueError('SFX duration differs from current actual timeline')
    voice,clips,voice_gain=voice_track(plan,ffmpeg)
    narration_output=ROOT/'assets/audio/narration.wav'
    write_wav(narration_output,voice)
    music=fit_length(read_audio(args.music,ffmpeg),duration)
    sfx=fit_length(read_audio(args.sfx,ffmpeg),duration)*args.sfx_gain
    duck=ducking(voice);music*=duck[:,None]
    with tempfile.TemporaryDirectory(prefix='longform-mix-', dir=SCRATCH) as directory:
        work=Path(directory);write_wav(work/'voice.wav',voice);write_wav(work/'music.wav',music)
        times,vdb=k_levels(work/'voice.wav',ffmpeg);mtimes,mdb=k_levels(work/'music.wav',ffmpeg)
        count=min(len(vdb),len(mdb));times=times[:count];vdb=vdb[:count];mdb=mdb[:count]
        preliminary=vdb>-45
        integrated_voice=10*np.log10(np.mean(10**(vdb[preliminary]/10)))
        voice_gate=max(-40,float(integrated_voice)-10)
        active=(vdb>voice_gate) & np.isfinite(mdb)
        if np.count_nonzero(active)<3:raise ValueError('Insufficient active narration for music balancing')
        difference=vdb-mdb;global_gain=float(np.median(difference[active])-args.voice_music_gap)
        gains=[]
        for chapter in plan['chapters']:
            mask=active&(times>=chapter['start'])&(times<chapter['end'])
            local=float(np.median(difference[mask])-args.voice_music_gap) if mask.sum()>4 else global_gain
            local=float(np.clip(local,global_gain-3,global_gain+3))
            gains.append({'id':chapter.get('id',chapter['kind']),'center':(chapter['start']+chapter['end'])/2,'gain_db':local})
        anchors=np.array([x['center'] for x in gains]);levels=np.array([x['gain_db'] for x in gains])
        gain_db=np.interp(np.arange(len(music))/SR,anchors,levels).astype(np.float32)
        music*=10**(gain_db[:,None]/20)
        # Phrase balance stays bounded: protect weak words by at most 5 dB,
        # and allow at most 3 dB lift under strong speech. The score is not held
        # 18 dB below every sentence; the base sidechain duck is only 3 dB.
        estimated=difference-np.interp(times,anchors,levels)
        desired_protection=np.where(active,np.clip(estimated-args.voice_music_gap,-5.0,3.0),0.0)
        protection=np.zeros(len(times));current=0.0
        for i,value in enumerate(desired_protection):
            tau=.08 if value<current else .28
            a=np.exp(-.1/tau);current=a*current+(1-a)*value;protection[i]=current
        sample_protection=np.interp(np.arange(len(music))/SR,times,protection).astype(np.float32)
        music*=10**(sample_protection[:,None]/20)
        processed_sfx=sfx*(.80+.20*duck[:,None])
        # Measure the processed stems; the report is not an algebraic estimate.
        write_wav(work/'balanced-music.wav',music)
        _,actual_mdb=k_levels(work/'balanced-music.wav',ffmpeg)
        count=min(len(vdb),len(actual_mdb));actual_gap=vdb[:count]-actual_mdb[:count]
        gate=active[:count]
        balance={str(q):round(float(np.percentile(actual_gap[gate],q)),3) for q in [10,25,50,75,90]}
        write_wav(work/'balanced-background.wav',music+processed_sfx)
        _,actual_bgdb=k_levels(work/'balanced-background.wav',ffmpeg)
        bg_gap=vdb[:count]-actual_bgdb[:count]
        bg_balance={str(q):round(float(np.percentile(bg_gap[gate],q)),3) for q in [10,25,50,75,90]}
        chapter_balance=[]
        for chapter in plan['chapters']:
            mask=gate&(times[:count]>=chapter['start'])&(times[:count]<chapter['end'])
            if mask.sum()<3:continue
            values={str(q):round(float(np.percentile(actual_gap[mask],q)),3) for q in [10,50,90]}
            chapter_balance.append({'id':chapter.get('id',chapter['kind']),'voice_minus_music_db':values,
                                    'median_in_target_range':8<=values['50']<=12})
        write_wav(ROOT/'assets/audio/music-in-mix.wav',music)
        write_wav(ROOT/'assets/audio/sfx-in-mix.wav',processed_sfx)
        combined=voice+music+processed_sfx
        peak=float(np.max(abs(combined)))
        if peak>.96:combined*=.96/peak
        write_wav(work/'premix.wav',combined)
        normalization=loudnorm(work/'premix.wav',args.output,ffmpeg,args.lufs,-1.7)
    report={'duration':duration,'sample_rate':SR,'channels':2,'voice_only_gain_db':round(voice_gain,3),
            'target_integrated_lufs':args.lufs,'target_true_peak_dbtp':-1.7,
            'music_gap_target_db':args.voice_music_gap,'measurement':'BS.1770 K-weighted 400 ms windows, 100 ms hop, active speech only',
            'voice_activity_gate_lufs':round(voice_gate,3),
            'voice_minus_music_db_percentiles':balance,'voice_minus_background_db_percentiles':bg_balance,
            'chapter_balance':chapter_balance,'music_gain_automation':gains,
            'base_ducking_max_db':3.0,'weak_phrase_extra_reduction_max_db':round(float(-np.min(protection)),3),
            'weak_phrase_extra_reduction_mean_active_db':round(float(np.mean(np.maximum(-protection[active],0))),3),
            'strong_phrase_music_lift_max_db':round(float(np.max(protection)),3),
            'balance_warnings':([f'Chapter median outside 8–12 dB: {c["id"]}' for c in chapter_balance if not c['median_in_target_range']]
                                + (['Quietest active speech windows below 6 dB; listen to soft endings and music transients'] if balance['10']<6 else [])),
            'narration_stem':str(narration_output),'narration':clips,'normalization':normalization,'output':str(args.output)}
    report.update({'timing_status':plan['source'].get('timing_status'),'estimated':plan['source'].get('estimated',False),
                   'timeline_sha256':hashlib.sha256(args.timeline.read_bytes()).hexdigest() if getattr(args,'timeline',None) else None,
                   'music_sha256':hashlib.sha256(args.music.read_bytes()).hexdigest(),
                   'sfx_sha256':hashlib.sha256(args.sfx.read_bytes()).hexdigest(),
                   'shared_action_cues':plan.get('action_metadata'),
                   'music_in_mix_stem':str(ROOT/'assets/audio/music-in-mix.wav'),
                   'sfx_in_mix_stem':str(ROOT/'assets/audio/sfx-in-mix.wav')})
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['demo','render','music','effects','mix'])
    p.add_argument('--timeline',type=Path);p.add_argument('--duration',type=float);p.add_argument('--title-at',type=float,default=17)
    p.add_argument('--actions',type=Path);p.add_argument('--allow-estimated',action='store_true')
    p.add_argument('--seed',type=int,default=SEED);p.add_argument('--ffmpeg')
    p.add_argument('--output',type=Path);p.add_argument('--report',type=Path)
    p.add_argument('--music',type=Path,default=ROOT/'assets/audio/music.wav')
    p.add_argument('--sfx',type=Path,default=ROOT/'assets/audio/sfx.wav')
    p.add_argument('--sfx-gain',type=float,default=.8)
    p.add_argument('--voice-music-gap',type=float,default=10)
    p.add_argument('--lufs',type=float,default=-15.5)
    args=p.parse_args()
    if args.actions is None and args.command in ['render','effects','mix'] and (ROOT/'content/action-cues.json').is_file():
        args.actions=ROOT/'content/action-cues.json'
    if not 8<=args.voice_music_gap<=12:p.error('Voice/music target must be 8–12 dB')
    if args.command=='demo' and args.duration is None:args.duration=30
    if args.command=='mix' and not args.timeline:p.error('mix requires a real narration timeline')
    plan=load_plan(args.timeline,args.duration,args.title_at)
    if args.timeline and plan['source'].get('estimated',False) and not args.allow_estimated:
        p.error('Estimated timeline rejected; use actual ASR timing for production')
    action_metadata=None
    if args.actions:
        actions=json.loads(args.actions.read_text())
        if actions.get('estimated',True) or any(c.get('estimated',True) for c in actions.get('audio_cues',[])):
            p.error('Estimated action cues rejected')
        if abs(float(actions.get('duration',-1))-plan['duration'])>1/30:
            p.error('Action cues and timeline durations differ')
        plan['source']['audio_cues']=actions.get('audio_cues',[])
        action_metadata={'path':str(args.actions),'sha256':hashlib.sha256(args.actions.read_bytes()).hexdigest(),'timing_status':actions.get('timing_status'),'estimated':False}
        plan['action_metadata']=action_metadata
    if args.command=='mix':
        args.output=args.output or ROOT/'assets/audio/final-mix.wav';args.report=args.report or ROOT/'output/mix-report.json'
        mix(plan,args);return
    music,arrangement=(None,[]) if args.command=='effects' else make_score(plan,args.seed)
    sfx,effects=(None,[]) if args.command=='music' else make_effects(plan,args.seed+1)
    report={'version':'longform-score-v1','generated_at_utc':datetime.now(timezone.utc).isoformat(),
            'duration':plan['duration'],'sample_rate':SR,'channels':2,'bit_depth':24,'bpm':BPM,'title_at':plan['title_at'],
            'seed':args.seed,'chapters':[{k:v for k,v in c.items() if k!='segments'} for c in plan['chapters']],
            'music_signal':measure(music) if music is not None else None,'sfx_signal':measure(sfx) if sfx is not None else None,
            'timeline_sha256':hashlib.sha256(args.timeline.read_bytes()).hexdigest() if args.timeline else None,
            'timing_status':plan['source'].get('timing_status'),'estimated':plan['source'].get('estimated',False),'shared_action_cues':action_metadata,
            'arrangement_events':arrangement,'effects_events':effects,
            'provenance':'Original procedural composition and synthesis; no samples, Suno output or generated speech'}
    if args.command=='demo':
        args.output=args.output or ROOT/'output/music-demo.wav';args.report=args.report or ROOT/'output/music-demo-report.json'
        with tempfile.TemporaryDirectory(prefix='longform-demo-', dir=SCRATCH) as d:
            premix=Path(d)/'demo.wav';write_wav(premix,music+sfx*.8)
            report['demo_normalization']=loudnorm(premix,args.output,ffmpeg_binary(args.ffmpeg),-17.0,-1.7)
        report['output']=str(args.output)
    else:
        if music is not None:write_wav(args.music,music)
        if sfx is not None:write_wav(args.sfx,sfx)
        args.report=args.report or ROOT/('output/effects-report.json' if args.command=='effects' else 'output/score-report.json')
        report['outputs']={**({'music':str(args.music)} if music is not None else {}),**({'sfx':str(args.sfx)} if sfx is not None else {})}
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if args.command=='render' and action_metadata is not None:
        (ROOT/'output/effects-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['arrangement_events','effects_events','chapters']},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
