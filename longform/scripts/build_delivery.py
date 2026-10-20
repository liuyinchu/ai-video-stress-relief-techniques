#!/usr/bin/env python3
"""Build longform review assets. Does not render or alter speech, video or old outputs."""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import math
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
LONG = ROOT / 'longform'
OUT = LONG / 'output'
NAMES = {'hook':'身体的警戒','title':'七种生理与心理小技巧','breath':'双吸长呼','cold':'借一点凉意 · 潜水反射','ear':'轻触耳部','shake':'松动身体','paper':'把烦心事写下来','fractal':'把目光借给自然','order':'整理一平米','closing':'给自己重新选择的空间'}
METHODS = ['breath','cold','ear','shake','paper','fractal','order']
OLD = [('横屏短片 · MiniMax v2','../../output/review-landscape-minimax-v2.mp4'),('竖屏短片 · MiniMax v2','../../output/review-portrait-minimax-v2.mp4')]

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))

def esc(text):
    return html.escape(str(text), quote=True)

def write(name, text):
    path = OUT / name
    path.write_text(text, encoding='utf-8')
    return path

def clock(seconds, sep='.'):
    ms = max(0, round(float(seconds)*1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02}:{m:02}:{s:02}{sep}{ms:03}'

def cue_time(cue, edge, fps):
    frame = cue.get(edge + '_frame')
    return float(frame)/fps if frame is not None else float(cue[edge])

def subtitle_files(captions, fps, estimated):
    rows = []
    previous_end = 0.0
    for cue in captions:
        text = str(cue.get('text','')).strip()
        if not text:
            continue
        start, end = cue_time(cue,'start',fps), cue_time(cue,'end',fps)
        if not all(math.isfinite(n) for n in (start,end)) or start < 0 or end <= start:
            raise ValueError(f'Invalid subtitle interval: {cue.get("id")}')
        if start < previous_end - 0.00001:
            raise ValueError(f'Overlapping subtitle interval: {cue.get("id")}')
        rows.append((start,end,text))
        previous_end = end
    if not rows:
        return {}, 0
    prefix = 'narration-preview' if estimated else 'narration'
    srt = '\n\n'.join(f'{i}\n{clock(a,",")} --> {clock(b,",")}\n{t}' for i,(a,b,t) in enumerate(rows,1))+'\n'
    note = 'NOTE Estimated preview timing; not final ASR alignment.\n\n' if estimated else ''
    vtt = 'WEBVTT\n\n'+note+'\n\n'.join(f'{clock(a)} --> {clock(b)}\n{html.escape(t)}' for a,b,t in rows)+'\n'
    write(prefix+'.srt', srt)
    write(prefix+'.vtt', vtt)
    return {'srt':prefix+'.srt','vtt':prefix+'.vtt'}, len(rows)

def cover_svg():
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="2560" height="1440" viewBox="0 0 2560 1440" role="img" aria-labelledby="ct cd">
<title id="ct">压力上来，先让身体缓一缓</title><desc id="cd">深色背景中的暖色呼吸轨迹与七个蓝色触点，七种生理与心理小技巧。</desc>
<defs><radialGradient id="bg"><stop stop-color="#142536"/><stop offset="1" stop-color="#070a10"/></radialGradient><radialGradient id="halo"><stop stop-color="#daa27d" stop-opacity=".2"/><stop offset="1" stop-color="#daa27d" stop-opacity="0"/></radialGradient><linearGradient id="line"><stop stop-color="#daa27d"/><stop offset="1" stop-color="#8cabb8"/></linearGradient><filter id="blur"><feGaussianBlur stdDeviation="18"/></filter></defs>
<rect width="2560" height="1440" fill="#070a10"/><rect x="1000" width="1560" height="1440" fill="url(#bg)"/>
<circle cx="2010" cy="690" r="660" fill="url(#halo)"/>
<g fill="none" stroke="#8cabb8" opacity=".12"><circle cx="2080" cy="720" r="570"/><circle cx="2080" cy="720" r="460"/><circle cx="2080" cy="720" r="350"/><path d="M1560 230v980M1810 100v1250M2060 100v1250M2310 100v1250"/></g>
<path d="M1510 950 C1690 970 1660 450 1875 445 C2000 445 1930 325 2040 320 C2200 315 2140 1070 2480 1010" fill="none" stroke="#daa27d" stroke-width="24" opacity=".25" filter="url(#blur)"/>
<path d="M1510 950 C1690 970 1660 450 1875 445 C2000 445 1930 325 2040 320 C2200 315 2140 1070 2480 1010" fill="none" stroke="url(#line)" stroke-width="7" stroke-linecap="round"/>
<g fill="#8cabb8"><circle cx="1560" cy="944" r="10"/><circle cx="1700" cy="715" r="10"/><circle cx="1800" cy="470" r="10"/><circle cx="1940" cy="420" r="10"/><circle cx="2060" cy="330" r="10"/><circle cx="2210" cy="850" r="10"/><circle cx="2440" cy="1014" r="10"/></g>
<g font-family="PingFang SC,Arial,sans-serif"><text x="170" y="230" font-size="38" letter-spacing="8" fill="#9fb2bf">七种生理与心理小技巧</text><text x="160" y="580" font-size="188" font-weight="600" fill="#f4ede7">压力上来，</text><text x="160" y="820" font-size="188" font-weight="600" fill="#efc8aa">先让身体</text><text x="160" y="1060" font-size="188" font-weight="600" fill="#f4ede7">缓一缓。</text><text x="172" y="1250" font-size="42" fill="#9fb2bf">从呼吸开始，给自己一点空间。</text></g></svg>'''

BASE_CSS = '''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#090c12;color:#e9e9ec;font:16px/1.7 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",Arial,sans-serif}a{color:#a9c8d8;text-underline-offset:4px}button,select{font:inherit}button,a,select{touch-action:manipulation}button:focus-visible,a:focus-visible,select:focus-visible{outline:2px solid #efc8aa;outline-offset:5px}main{max-width:1480px;margin:0 auto;padding:42px 44px 80px}.eyebrow{font:11px/1.4 Arial,sans-serif;letter-spacing:.2em;color:#8b9caa;text-transform:uppercase}h1{font-size:clamp(30px,3vw,46px);font-weight:550;line-height:1.3;letter-spacing:-.03em;margin:14px 0}h2{font-size:23px;font-weight:550;margin:0 0 22px}h3{font-size:16px;font-weight:550}.muted{color:#8b9caa}.small{font-size:13px}.top{display:flex;align-items:flex-start;justify-content:space-between;gap:30px;margin-bottom:30px}.status{display:inline-block;border:1px solid #36404b;border-radius:100px;padding:5px 13px;color:#b4c3cd;font-size:12px;white-space:nowrap}.status.ready{color:#d4dfd7;border-color:#4a625b}.layout{display:grid;grid-template-columns:minmax(0,1fr) 275px;gap:32px;align-items:start}.screen{aspect-ratio:16/9;background:#03050a;border:1px solid #202833;position:relative;overflow:hidden}.screen video,.screen .cover{width:100%;height:100%;object-fit:contain;display:block}.screen video[hidden],.screen .cover[hidden]{display:none}.waiting{position:absolute;left:20px;bottom:16px;margin:0;background:rgba(6,10,16,.85);padding:6px 12px;border:1px solid #34404b;font-size:12px;color:#b7c6d0}.toolbar{display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;padding:14px 0 18px;border-bottom:1px solid #252c35}.button,button,select{border:1px solid #37424d;background:#111821;color:#d7e3ea;padding:7px 12px;border-radius:5px;font-size:13px;text-decoration:none;cursor:pointer}button:hover,.button:hover{border-color:#8cabb8}button:disabled{cursor:default;opacity:.45}.links{display:flex;gap:15px;flex-wrap:wrap;font-size:13px}aside{position:sticky;top:24px}.chapters{display:flex;flex-direction:column;gap:0}.chapter{display:grid;grid-template-columns:28px 1fr 42px;align-items:center;text-align:left;gap:7px;border:0;border-top:1px solid #28313b;border-radius:0;background:transparent;padding:13px 2px;font-size:13px;line-height:1.5}.chapter:last-child{border-bottom:1px solid #28313b}.chapter .num{font:11px Arial,sans-serif;color:#daa27d}.chapter time{font:11px Arial,sans-serif;text-align:right;color:#8b9caa}.chapter.active{color:#efc8aa;background:linear-gradient(90deg,rgba(218,162,125,.1),transparent)}section{margin-top:48px;padding-top:28px;border-top:1px solid #28313b}.audio-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px 36px}.audio-item{border-top:1px solid #28313b;padding-top:13px}.audio-item h3{margin:0 0 4px}.audio-item p{margin:0 0 10px}audio{display:block;width:100%;height:38px}.pending{font-size:12px;color:#8b9caa}.compare{margin-top:28px}.compare-options{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}.compare-options button[aria-pressed=true]{color:#efc8aa;border-color:#daa27d}.downloads{display:flex;flex-wrap:wrap;gap:12px 22px}.archive{display:grid;grid-template-columns:1fr 1fr;gap:24px}.archive a{display:block;padding:15px 0;border-top:1px solid #28313b}.archive code{display:block;font-size:11px;color:#8b9caa;margin-top:3px;overflow-wrap:anywhere}.footer{margin-top:45px;font-size:12px;color:#71818e}.transcript{max-width:900px}.transcript article{padding:24px 0;border-top:1px solid #28313b}.transcript p{font-size:18px;line-height:1.95}.seg-id{font:10px Arial;color:#71818e;margin-right:10px}.transcript .lead{font-size:15px;color:#8b9caa}@media(max-width:1000px){main{padding:28px 24px 60px}.layout{grid-template-columns:1fr}aside{position:static}.chapters{display:grid;grid-template-columns:1fr 1fr;column-gap:20px}.top{gap:15px}}@media(max-width:600px){main{padding:24px 16px 48px}.top{display:block}.top .status{margin-top:12px}.audio-grid,.archive{grid-template-columns:1fr}.chapter{font-size:12px}.toolbar{align-items:flex-start}.waiting{left:10px;bottom:8px;font-size:10px}.transcript p{font-size:17px}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}'''

REVIEW = r'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>先让身体缓一缓 · 长版审片</title><style>__CSS__</style></head><body><main>
<header class="top"><div><div class="eyebrow">LONGFORM / DIRECTOR REVIEW</div><h1>压力上来，先让身体缓一缓</h1><div class="muted small">七种生理与心理小技巧 · 连续墙面叙事 · 原速温暖女声</div></div><span id="status" class="status">交付页面就绪 · 等待长片</span></header>
<div class="layout"><div><div class="screen"><img class="cover" id="cover" src="cover-landscape.svg" alt="压力上来，先让身体缓一缓，七种生理与心理小技巧封面"><video id="film" controls preload="metadata" playsinline hidden aria-label="长版横屏视频"><track id="subtitle-track" kind="subtitles" srclang="zh-CN" label="中文"></video><p id="waiting" class="waiting">长片正在渲染，可先查看封面、台本与声音。</p></div>
<div class="toolbar"><div class="links"><a id="movie-link" hidden download>下载横屏成片</a><a id="video1080-link" hidden download>下载 1080p 版</a><a id="cover-link" href="cover-landscape.svg" download>封面 SVG</a><a href="fullscript.html">完整台本</a><a href="storyboard.html">分镜与关键帧</a></div><button id="captions-toggle" disabled aria-pressed="false">外挂字幕：关</button></div>
<p id="timing-note" class="small muted"></p><div class="links"><a id="srt-link" hidden download>SRT 字幕</a><a id="vtt-link" hidden download>VTT 字幕</a><a href="../content/publish-copy.md">发布文案</a><a href="../docs/evidence.md">事实核验与来源</a><a href="../docs/production.md">制作说明</a></div></div>
<aside aria-label="章节导航"><div class="eyebrow" style="margin-bottom:14px">CHAPTERS</div><nav class="chapters" id="chapters"></nav><p class="small muted" id="chapter-note">章节时间以实际配音对齐为准。</p></aside></div>
<section aria-labelledby="sound-title"><div class="eyebrow">SOUND ROOM</div><h2 id="sound-title">听见节奏，也听清每一句话</h2><p class="muted small">原创程序合成配乐与音效。单独听音乐，再与总混比较；各播放器互斥播放，避免叠音。</p><div class="audio-grid" id="audio-grid"></div><div class="compare" id="comparison"><h3>混音 A/B 对比</h3><p class="small muted" id="compare-note">对比样例待生成；会保留相同片段，切换时维持播放位置。</p><div class="compare-options" id="compare-options"></div><audio id="compare-player" controls preload="none" hidden></audio></div></section>
<section aria-labelledby="files-title"><div class="eyebrow">PROJECT NOTES</div><h2 id="files-title">素材与制作记录</h2><div class="downloads"><a href="../content/script.json">冻结台本 JSON</a><a id="timeline-link" href="../content/estimated-timeline.json">章节时间轴</a><a href="delivery-manifest.json">交付清单</a><a href="../docs/music-design.md">音乐设计</a><a href="../docs/timing-pipeline.md">原声与字幕对齐</a><a href="minimax-proof.jpg">MiniMax 网页生成记录</a><a href="../content/voice-provenance.json">配音来源 JSON</a></div><p class="small muted">画面已内嵌字幕，外挂字幕默认关闭。可按章节审片，也可分别试听配乐、旁白和总混。</p></section>
<section aria-labelledby="archive-title"><div class="eyebrow">PRESERVED SHORT FILMS</div><h2 id="archive-title">原横屏、竖屏短片保持原样</h2><div class="archive"><a href="../../output/review-landscape-minimax-v2.mp4">横屏短片 · MiniMax v2<code>output/review-landscape-minimax-v2.mp4</code></a><a href="../../output/review-portrait-minimax-v2.mp4">竖屏短片 · MiniMax v2<code>output/review-portrait-minimax-v2.mp4</code></a></div><p class="small muted">v1 横竖版也保留在原 output 目录。长版素材、代码与交付均在 longform 下。</p></section><footer class="footer">本地审片 · <span id="built"></span></footer>
</main><script id="delivery-data" type="application/json">__DATA__</script><script>
'use strict';
const DATA=JSON.parse(document.getElementById('delivery-data').textContent), $=id=>document.getElementById(id), film=$('film');
let timeline=DATA.timeline, mediaReady=false, subtitleURL=null, subtitleObjectURL=null, compareVariants=[];
const mmss=s=>`${Math.floor(s/60)}:${String(Math.floor(s%60)).padStart(2,'0')}`;
function isLocal(){return location.protocol==='file:';}
async function available(path,known=false){if(isLocal())return known;try{const r=await fetch(path,{method:'HEAD',cache:'no-store'});return r.ok;}catch{return known;}}
async function json(path){if(isLocal())return null;try{const r=await fetch(path,{cache:'no-store'});return r.ok?await r.json():null;}catch{return null;}}
function appendText(tag,text,parent,cls){const e=document.createElement(tag);e.textContent=text;if(cls)e.className=cls;parent.append(e);return e;}
function stamp(t,sep='.'){let n=Math.max(0,Math.round(t*1000));const h=Math.floor(n/3600000);n%=3600000;const m=Math.floor(n/60000);n%=60000;const s=Math.floor(n/1000);return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}${sep}${String(n%1000).padStart(3,'0')}`;}
function cueSeconds(c,edge){return Number.isFinite(c[edge+'_frame'])?c[edge+'_frame']/(timeline.fps||30):c[edge];}
function installCaptions(){const cues=(timeline.captions||[]).filter(c=>c.text);if(!cues.length)return;const escape=t=>t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');const vtt='WEBVTT\n\n'+cues.map(c=>`${stamp(cueSeconds(c,'start'))} --> ${stamp(cueSeconds(c,'end'))}\n${escape(c.text)}`).join('\n\n');const srt=cues.map((c,i)=>`${i+1}\n${stamp(cueSeconds(c,'start'),',')} --> ${stamp(cueSeconds(c,'end'),',')}\n${c.text}`).join('\n\n');subtitleObjectURL=URL.createObjectURL(new Blob([vtt],{type:'text/vtt'}));$('subtitle-track').src=subtitleObjectURL;subtitleURL=subtitleObjectURL;$('captions-toggle').disabled=false;for(const [kind,body,type] of [['srt',srt,'application/x-subrip'],['vtt',vtt,'text/vtt']]){const e=$(kind+'-link');e.href=URL.createObjectURL(new Blob([body],{type}));e.download='narration'+(timeline.estimated?'-preview':'')+'.'+kind;e.textContent=(timeline.estimated?'预估 ':'')+kind.toUpperCase()+' 字幕';e.hidden=false;}}
function drawChapters(){const parent=$('chapters');parent.replaceChildren();let n=0;for(const chapter of timeline.chapters||[]){if(chapter.id==='title')continue;const button=document.createElement('button');button.className='chapter';button.type='button';button.dataset.chapter=chapter.id;button.disabled=!mediaReady;const numbered=DATA.methods.includes(chapter.id);appendText('span',numbered?String(++n).padStart(2,'0'):'—',button,'num');appendText('span',DATA.names[chapter.id]||chapter.title||chapter.id,button);appendText('time',Number.isFinite(chapter.start)?mmss(chapter.start):'待定',button);button.addEventListener('click',()=>{film.currentTime=chapter.start;film.scrollIntoView({block:'center',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});film.focus();});parent.append(button);}const estimate=timeline.estimated!==false;$('timing-note').textContent=estimate?'章节与字幕当前使用预估时间，只用于结构审阅。':'章节与字幕来自实际配音时间轴。配音原速播放，片长由声音与留白决定。';$('chapter-note').textContent=estimate?'预估时间 · 正式配音对齐后更新':'实际配音时间 · 点击章节定位';$('timeline-link').href=estimate?'../content/estimated-timeline.json':'../content/timeline.json';}
film.addEventListener('timeupdate',()=>{for(const e of document.querySelectorAll('.chapter')){const c=timeline.chapters.find(x=>x.id===e.dataset.chapter);const active=c&&film.currentTime>=c.start&&film.currentTime<c.end;e.classList.toggle('active',Boolean(active));if(active)e.setAttribute('aria-current','true');else e.removeAttribute('aria-current');}});
$('captions-toggle').addEventListener('click',()=>{const show=$('captions-toggle').getAttribute('aria-pressed')!=='true';for(const t of film.textTracks)t.mode=show?'showing':'hidden';$('captions-toggle').setAttribute('aria-pressed',String(show));$('captions-toggle').textContent='外挂字幕：'+(show?'开':'关');});
document.addEventListener('play',e=>{if(e.target instanceof HTMLMediaElement)for(const m of document.querySelectorAll('audio,video'))if(m!==e.target)m.pause();},true);
async function audioRoom(){for(const item of DATA.audio){const box=document.createElement('div');box.className='audio-item';appendText('h3',item.label,box);appendText('p',item.note,box,'small muted');if(await available(item.path,item.exists)){const a=document.createElement('audio');a.controls=true;a.preload='none';a.src=item.path;a.setAttribute('aria-label',item.label);box.append(a);const link=appendText('a','下载音轨',box,'small');link.href=item.path;link.download='';}else appendText('span','待生成',box,'pending');$('audio-grid').append(box);}const compare=await json('mix-comparison.json')||DATA.comparison;for(const variant of compare?.variants||[]){if(await available(variant.path,variant.exists))compareVariants.push(variant);}if(compareVariants.length){$('compare-player').hidden=false;$('compare-note').textContent=compare.note||'同一片段的混音对比；切换保留播放位置。';for(const [index,item] of compareVariants.entries()){const b=document.createElement('button');b.textContent=item.label;b.setAttribute('aria-pressed','false');b.addEventListener('click',()=>switchCompare(index));$('compare-options').append(b);}switchCompare(0);}}
function switchCompare(index){const a=$('compare-player'),time=a.currentTime||0,playing=!a.paused,variant=compareVariants[index];a.src=variant.path;a.onloadedmetadata=()=>{a.currentTime=Math.min(time,Math.max(0,a.duration-.1));if(playing)a.play().catch(()=>{});};for(const [i,b] of [...$('compare-options').children].entries())b.setAttribute('aria-pressed',String(i===index));}
(async()=>{$('built').textContent='页面生成于 '+DATA.generated_at;const actual=await json('../content/timeline.json');if(actual&&actual.estimated===false&&Array.isArray(actual.chapters))timeline=actual;drawChapters();installCaptions();if(await available('cover-landscape.png',DATA.files.cover_png.exists)){$('cover').src='cover-landscape.png';$('cover-link').href='cover-landscape.png';$('cover-link').textContent='封面 PNG';}if(await available('master-landscape.mp4',DATA.files.video.exists)){mediaReady=true;film.src='master-landscape.mp4';film.poster=$('cover').src;film.hidden=false;$('cover').hidden=true;$('waiting').hidden=true;$('status').textContent='长版成片 · 1440p / 30fps';$('status').classList.add('ready');$('movie-link').href='master-landscape.mp4';$('movie-link').hidden=false;drawChapters();film.addEventListener('error',()=>{$('status').textContent='长片文件暂时无法播放';$('waiting').textContent='视频加载失败，可检查文件或重新生成交付页面。';$('waiting').hidden=false;});}if(await available('master-landscape-1080p.mp4',DATA.files.video_1080.exists)){$('video1080-link').href='master-landscape-1080p.mp4';$('video1080-link').hidden=false;}await audioRoom();})();
</script></body></html>'''


def build_storyboard(script, timeline):
    # Join actual timing to the frozen text and visual intent by stable ID.
    observed = timeline.get('segments') or [seg for chapter in timeline.get('chapters', []) for seg in chapter.get('segments', [])]
    timing = {}
    for seg in observed:
        if seg['id'] in timing:
            raise ValueError('Duplicate storyboard timing ID: ' + seg['id'])
        timing[seg['id']] = seg
    estimated = timeline.get('estimated') is not False
    fps = float(timeline.get('fps', 30))
    rows = []
    for seg in script['segments']:
        actual = timing.get(seg['id'])
        if actual is None and not estimated:
            raise ValueError('Actual timeline missing storyboard segment: ' + seg['id'])
        time_html = '<span class="muted">待对齐</span>'
        if actual and all(k in actual or k+'_frame' in actual for k in ('start', 'end')):
            start, end = cue_time(actual, 'start', fps), cue_time(actual, 'end', fps)
            if not all(math.isfinite(v) for v in (start,end)) or start < 0 or end <= start:
                raise ValueError('Invalid storyboard timing: ' + seg['id'])
            time_html = f'<time>{clock(start)}</time><span class="range-separator">至</span><time>{clock(end)}</time><small>{end-start:.2f} 秒</small>'
        text_html = esc(seg['text']) if seg['text'] else '<span class="muted">无旁白 · 标题停顿</span>'
        rows.append(f'<tr id="{esc(seg["id"])}" data-segment-id="{esc(seg["id"])}"><th scope="row"><span class="segment-name">{esc(seg["id"])} · {esc(NAMES.get(seg["chapter"],seg["chapter"]))}</span>{time_html}</th><td data-label="旁白">{text_html}</td><td class="intent" data-label="画面意图">{esc(seg["visual_intent"])}</td></tr>')
    sheet = 'master-qa/actual-keyframes/_sheet.png'
    sheet_exists = (OUT/sheet).exists()
    if sheet_exists:
        sheet_html = f'<figure><a href="{sheet}" target="_blank" rel="noopener"><img src="{sheet}" alt="已实际生成画面的离散关键帧总览，点击查看原图"></a><figcaption>实际关键帧总览 · 点击查看原图。离散抽帧不表示全片连续播放，也不代表下列每一段都附有对应截图。</figcaption></figure>'
    else:
        sheet_html = '<p class="muted">实际关键帧总览尚未生成；此处不使用设计图冒充渲染帧。</p>'
    status = '预估段落时间 · 仅供结构审阅' if estimated else '实际配音时间轴 · 按段落 ID 对应冻结台本'
    css = '''.storyboard{max-width:1480px}.storyboard figure{margin:26px 0 34px}.storyboard figure img{display:block;width:100%;height:auto;border:1px solid #28313b}.storyboard figcaption{color:#8b9caa;font-size:13px;padding-top:10px}.storyboard table{width:100%;border-collapse:collapse;table-layout:fixed}.storyboard caption{text-align:left;color:#8b9caa;font-size:13px;padding:0 0 14px}.storyboard col:first-child{width:23%}.storyboard col:nth-child(2){width:39%}.storyboard col:nth-child(3){width:38%}.storyboard thead th{font-size:13px;color:#9cb2c0;font-weight:500;text-align:left;padding:13px 16px;border-bottom:1px solid #45515f;background:#10161f}.storyboard tbody th,.storyboard td{text-align:left;vertical-align:top;padding:20px 16px;border-bottom:1px solid #28313b;font-size:15px;line-height:1.85;font-weight:400;overflow-wrap:anywhere}.storyboard tbody tr:target{background:#152333}.segment-name{display:block;color:#efc8aa;font-size:13px;margin-bottom:10px}.storyboard time{display:block;font:12px/1.8 Arial,sans-serif;font-variant-numeric:tabular-nums;color:#b8c8d2}.range-separator{display:block;color:#607482;font-size:10px;line-height:1.3}.storyboard small{display:block;color:#71818e;font-size:11px;margin-top:8px}.storyboard .intent{color:#adb9c3}.chapter-links{display:flex;flex-wrap:wrap;gap:10px 20px;font-size:13px;padding:20px 0;border-top:1px solid #28313b}@media(max-width:700px){.storyboard table,.storyboard tbody,.storyboard tr,.storyboard th,.storyboard td{display:block;width:100%}.storyboard colgroup,.storyboard thead{display:none}.storyboard tbody tr{border-top:1px solid #45515f;padding:16px 0}.storyboard tbody th,.storyboard td{border:0;padding:8px 0}.storyboard td:before{content:attr(data-label);display:block;color:#71818e;font-size:11px;letter-spacing:.08em;margin-bottom:6px}.storyboard time,.range-separator{display:inline;margin-right:8px}.storyboard small{display:inline}.segment-name{margin-bottom:6px}}'''
    seen=set()
    nav=[]
    for seg in script['segments']:
        if seg['chapter'] in seen: continue
        seen.add(seg['chapter'])
        nav.append(f'<a href="#{esc(seg["id"])}">{esc(NAMES.get(seg["chapter"],seg["chapter"]))}</a>')
    caption = '时间为预估的段落起止，仅用于结构审阅。' if estimated else '时间为实际时间轴中的段落起止，段间可能另有留白；空旁白的标题段一并保留。'
    page = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>分镜与关键帧 · 先让身体缓一缓</title><style>'+BASE_CSS+css+'</style></head><body><main class="storyboard"><div class="links"><a href="review.html">返回审片页</a><a href="fullscript.html">完整台本</a><a href="../docs/evidence.md">事实核验</a></div><div class="eyebrow" style="margin-top:28px">STORYBOARD / ACTUAL KEYFRAMES</div><h1>分镜与关键帧</h1><p class="muted">'+str(len(rows))+' 段 · '+status+'。旁白与画面意图直接读取冻结台本；画面意图是设计记录，实际效果请结合关键帧和成片审阅。</p>'+sheet_html+'<nav class="chapter-links" aria-label="分镜章节">'+''.join(nav)+'</nav><table><caption>'+caption+'</caption><colgroup><col><col><col></colgroup><thead><tr><th scope="col">段落与时间</th><th scope="col">旁白</th><th scope="col">画面意图 · 冻结台本</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table><p class="footer">本地分镜记录 · 不以离散关键帧替代连续播放检查。</p></main></body></html>'
    write('storyboard.html', page)
    return {'path':'storyboard.html','exists':True,'segments':len(rows),'timing_status':'estimated-preview' if estimated else timeline.get('timing_status','actual'),'actual_keyframe_sheet':{'path':sheet,'exists':sheet_exists}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeline', type=Path, help='Actual or explicitly marked estimated timeline; relative to repository root')
    parser.add_argument('--require-actual', action='store_true', help='Fail when no actual speech-aligned timeline exists')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    script_path=LONG/'content/script.json'
    script_bytes=script_path.read_bytes()
    script=json.loads(script_bytes)
    if args.timeline:
        path=args.timeline if args.timeline.is_absolute() else ROOT/args.timeline
        timeline=read_json(path)
    else:
        path=LONG/'content/timeline.json'
        if not path.exists(): path=LONG/'content/estimated-timeline.json'
        timeline=read_json(path) if path.exists() else {'estimated':True,'fps':30,'chapters':[],'captions':[]}
    estimated=timeline.get('estimated') is not False
    if args.require_actual and estimated:
        parser.error('Actual timeline is not available; no delivery assets were generated.')
    timeline['estimated']=estimated
    if not timeline.get('chapters'):
        timeline['chapters']=[{'id':c,'title':NAMES.get(c,c)} for c in dict.fromkeys(x['chapter'] for x in script['segments'])]
    if not timeline.get('captions'):
        cp=LONG/'content'/('estimated-captions.json' if estimated else 'captions.json')
        if cp.exists():
            caption_data=read_json(cp)
            if (caption_data.get('estimated') is not False)!=estimated:
                raise ValueError('Caption timing status does not match timeline')
            timeline['captions']=caption_data.get('captions',[])
    subs,cue_count=subtitle_files(timeline.get('captions',[]),float(timeline.get('fps',30)),estimated)
    # Remove only obsolete final subtitle exports when no valid final timeline remains.
    if estimated:
        for name in ['narration.srt','narration.vtt']:
            f=OUT/name
            if f.exists(): f.unlink()
    svg=cover_svg()
    write('cover-landscape.svg',svg)
    write('cover-landscape.html','<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>长版封面 · 可渲染源</title><style>html,body{margin:0;width:2560px;height:1440px;overflow:hidden;background:#070a10}svg{display:block}</style>'+svg+'</html>')
    grouped={}
    for seg in script['segments']:
        grouped.setdefault(seg['chapter'],[]).append(seg)
    articles=[]
    for chapter,segments in grouped.items():
        if not any(s['text'] for s in segments):continue
        paragraphs=''.join(f'<p><span class="seg-id">{esc(s["id"])}</span>{esc(s["text"])}</p>' for s in segments if s['text'])
        articles.append(f'<article id="{esc(chapter)}"><h2>{esc(NAMES.get(chapter,chapter))}</h2>{paragraphs}</article>')
    write('fullscript.html','<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>完整台本 · 先让身体缓一缓</title><style>'+BASE_CSS+'</style></head><body><main class="transcript"><a href="review.html">返回审片页</a><div class="eyebrow" style="margin-top:24px">FULL NARRATION</div><h1>'+esc(script['title'])+'</h1><p class="lead">冻结台本 · 34 段旁白 · 章节标题不配音。<a href="../docs/evidence.md">查看事实核验与来源</a></p>'+''.join(articles)+'</main></body></html>')
    storyboard=build_storyboard(script,timeline)
    audio=[{'label':'原创音乐 · 独立 stem','path':'../assets/audio/music.wav','note':'完整配乐；单独判断主题、和声与章际呼吸。'}, {'label':'正式总混','path':'../assets/audio/final-mix.wav','note':'原速 MiniMax 旁白、音乐与音效的完整混音。'}, {'label':'旁白 · 独立 stem','path':'../assets/audio/narration.wav','note':'按时间轴摆位与独立增益后的原速 MiniMax 旁白。'}, {'label':'配乐方向 · 30 秒样例','path':'music-demo.wav','note':'独立音色与主题样例，不代表长片正式混音。'}, {'label':'音效 · 独立 stem','path':'../assets/audio/sfx.wav','note':'气流、纸质与轻触等原创程序音效。'}]
    for a in audio:a['exists']=(OUT/a['path']).exists()
    compare_path=OUT/'mix-comparison.json'
    compare=read_json(compare_path) if compare_path.exists() else {'variants':[]}
    for a in compare.get('variants',[]):a['exists']=(OUT/a['path']).exists()
    manifest={'schema':'longform-delivery/1','generated_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds'),'render_status':'ready-for-director-review' if (OUT/'master-landscape.mp4').exists() and (OUT/'delivery-validation.json').exists() else 'media-present' if (OUT/'master-landscape.mp4').exists() else 'not-rendered','timing_status':'estimated-preview' if estimated else timeline.get('timing_status','actual'),'source_script_sha256':hashlib.sha256(script_bytes).hexdigest(),'source_timeline':str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),'subtitle_cues':cue_count,'subtitle_files':subs,'files':{'video':{'path':'master-landscape.mp4','exists':(OUT/'master-landscape.mp4').exists()},'video_1080':{'path':'master-landscape-1080p.mp4','exists':(OUT/'master-landscape-1080p.mp4').exists()},'cover_png':{'path':'cover-landscape.png','exists':(OUT/'cover-landscape.png').exists()},'cover_svg':{'path':'cover-landscape.svg','exists':True},'fullscript':{'path':'fullscript.html','exists':True},'storyboard':storyboard},'audio':audio,'comparison':compare,'preserved_shortfilms':[{'label':label,'path':path,'exists':(OUT/path).exists()} for label,path in OLD]}
    write('delivery-manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    data={**manifest,'timeline':timeline,'names':NAMES,'methods':METHODS}
    safe_json=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</',r'<\/')
    write('review.html',REVIEW.replace('__CSS__',BASE_CSS).replace('__DATA__',safe_json))
    if script_path.read_bytes()!=script_bytes:raise RuntimeError('Frozen script changed during delivery generation')
    print(json.dumps({'review':'longform/output/review.html','timing_status':manifest['timing_status'],'render_status':manifest['render_status'],'subtitle_cues':cue_count,'files':['review.html','fullscript.html','storyboard.html','cover-landscape.svg','cover-landscape.html','delivery-manifest.json',*subs.values()]},ensure_ascii=False))

if __name__=='__main__':
    main()
