#!/usr/bin/env python3
"""Independent offline chapter ASR -> observed word alignment -> film timeline.

Run with ../proj1-1019/engine/.venv/bin/python (MLX Whisper already installed).
No script or hint is passed to ASR. No downloads, TTS, speed changes, or old voice
substitutions. Formal timeline is published only when all nine WAVs and their
current SHA-keyed ASR caches exist and every caption has observed word anchors.
--estimate-only writes explicitly estimated preview files, never timeline.json.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
import unicodedata
import wave

ROOT = Path(__file__).resolve().parents[2]
LONG = ROOT / 'longform'
CONTENT = LONG / 'content'
RAW = LONG / 'assets/voice/raw'
ASR = LONG / 'assets/voice/asr'
MODEL = ROOT.parent / 'proj1-1019/out/models/whisper-large-v3-turbo-q4'
FPS = 30
VERSION = 'observed-words-v1'
WORD_CUES = [
 ('breath-inhale','s04','用鼻子吸一口气'),
 ('breath-top-up','s04','再短短地补一小口'),
 ('breath-first-exhale','s05','用嘴慢慢呼出'),
 ('paper-write','s22','写下'),
 ('paper-crumple','s22','然后揉成纸团'),
 ('paper-toss','s22','丢进纸篓'),
 ('paper-tear','s23','慢慢撕一张废纸'),
 ('order-clear-paper','s30','丢掉废纸'),
 ('order-cup-place','s30','把杯子放好'),
 ('order-items-place','s30','各归其位'),
]
TITLES = {'hook': '压力上来，先让身体缓一缓', 'title': '七种生理与心理小技巧',
          'breath': '双吸长呼', 'cold': '借一点凉意', 'ear': '轻揉耳廓',
          'shake': '松动身体', 'paper': '把烦心事写下来',
          'fractal': '把目光借给自然', 'order': '整理一平米', 'closing': '找到自己的节奏'}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temp.replace(path)


def load_json(path):
    return json.loads(path.read_text())


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def norm(text):
    return ''.join(c.lower() for c in unicodedata.normalize('NFKC', text)
                   if unicodedata.category(c)[0] in 'LN')


def han_count(text):
    return len(re.findall(r'[\u3400-\u9fff]', text))


def floor_frame(t):
    return max(0, math.floor(t * FPS + 1e-7)) / FPS


def ceil_frame(t):
    return max(0, math.ceil(t * FPS - 1e-7)) / FPS


def r(t):
    return round(t, 6)


def ffmpeg_path(explicit=None):
    if explicit:
        return explicit
    if os.environ.get('MULTIPLANE_FFMPEG'):
        return os.environ['MULTIPLANE_FFMPEG']
    files = list((ROOT / '.tools/venv/lib').glob('python*/site-packages/imageio_ffmpeg/binaries/ffmpeg-*'))
    if not files:
        raise RuntimeError('Existing local FFmpeg was not found; pass --ffmpeg.')
    return str(files[0])


def audio_info(path, ffmpeg):
    try:
        with wave.open(str(path), 'rb') as wav:
            return {'duration': wav.getnframes() / wav.getframerate(),
                    'sample_rate': wav.getframerate(), 'sample_frames': wav.getnframes(),
                    'channels': wav.getnchannels()}
    except wave.Error:
        # Some MiniMax WAVs use extensible/float headers. Decode unchanged rate to
        # PCM for sample counting; this fallback never changes the placed source.
        proc = subprocess.run([ffmpeg, '-hide_banner', '-i', str(path), '-f', 'null', '-'],
                              text=True, capture_output=True, check=True)
        rate = re.search(r'(\d+) Hz', proc.stderr)
        if not rate:
            raise RuntimeError('Cannot inspect WAV sample rate: ' + str(path))
        sample_rate = int(rate.group(1))
        pcm = subprocess.check_output([ffmpeg, '-v', 'error', '-i', str(path),
                                       '-ac', '1', '-f', 's16le', '-'])
        frames = len(pcm) // 2
        return {'duration': frames / sample_rate, 'sample_rate': sample_rate,
                'sample_frames': frames, 'channels': None, 'inspection': 'decoded PCM sample count'}


def silence_intervals(path, ffmpeg, duration, threshold=-42):
    result = subprocess.run([ffmpeg, '-hide_banner', '-nostdin', '-i', str(path),
        '-af', f'silencedetect=noise={threshold}dB:d=0.10', '-f', 'null', '-'],
        capture_output=True, text=True, check=True)
    pending, intervals = None, []
    for event, number in re.findall(r'silence_(start|end): ([0-9.]+)', result.stderr):
        value = min(duration, float(number))
        if event == 'start':
            pending = value
        elif pending is not None:
            intervals.append({'start': pending, 'end': value, 'duration': r(value-pending)})
            pending = None
    if pending is not None:
        intervals.append({'start': pending, 'end': duration, 'duration': r(duration-pending)})
    return intervals


def transcribe(chapter, ffmpeg, model, force=False):
    path = RAW / (chapter['id'] + '.wav')
    if not path.exists():
        return None
    digest = sha(path)
    cache = ASR / (chapter['id'] + '.json')
    model_revision = load_json(model/'provenance.json').get('revision') if (model/'provenance.json').exists() else None
    if cache.exists() and not force:
        old = load_json(cache)
        if (old.get('source_sha256') == digest and old.get('model_path') == str(model)
                and old.get('model_revision') == model_revision and old.get('words')
                and old.get('reference_prompt_used') is False):
            print(chapter['id'] + ': ASR cache current', flush=True)
            return old
    if not (model / 'weights.npz').is_file() or not (model / 'config.json').is_file():
        raise RuntimeError('Local model missing; refusing any model download.')
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    import numpy as np
    import mlx_whisper
    info = audio_info(path, ffmpeg)
    pcm = subprocess.check_output([ffmpeg, '-v', 'error', '-i', str(path),
                                  '-ar', '16000', '-ac', '1', '-f', 'f32le', '-'])
    began = time.monotonic()
    # Intentionally no initial_prompt, prefix, script, hotwords, or previous text.
    data = mlx_whisper.transcribe(np.frombuffer(pcm, dtype='<f4').copy(),
        path_or_hf_repo=str(model), language='zh', task='transcribe', temperature=0.0,
        condition_on_previous_text=False, word_timestamps=True, verbose=False)
    words = []
    for part in data.get('segments', []):
        for word in part.get('words', []):
            item = {k: word[k] for k in ['word', 'start', 'end', 'probability'] if k in word}
            item['index'] = len(words)
            words.append(item)
    row = {'id': chapter['id'], 'audio': str(path.relative_to(ROOT)),
           'source_sha256': digest, 'model_path': str(model), 'model_revision': model_revision,
           'offline': True, 'reference_prompt_used': False,
           'timestamp_origin': 'seconds from unchanged raw chapter WAV start',
           'asr_seconds': r(time.monotonic()-began), 'audio_info': info,
           'recognized_text': data.get('text', ''), 'words': words,
           'asr_segments': data.get('segments', []),
           'silence': {str(db): silence_intervals(path, ffmpeg, info['duration'], db)
                       for db in [-42, -36]},
           'generated_at_utc': dt.datetime.now(dt.timezone.utc).isoformat()}
    # A browser download being replaced during transcription must not poison cache.
    if sha(path) != digest:
        raise RuntimeError('Source audio changed during ASR: ' + chapter['id'])
    write_json(cache, row)
    print(json.dumps({'chapter': chapter['id'], 'audio_seconds': info['duration'],
                      'asr_seconds': row['asr_seconds'], 'text': row['recognized_text']}, ensure_ascii=False), flush=True)
    return row


def align_chars(expected, recognized):
    """Monotonic global edit alignment. Character mappings inherit WHOLE word times.

    Never interpolates a clock within a multi-character ASR word. A substitution
    is retained as uncertain evidence, not silently rewritten as an exact match.
    """
    n, m = len(expected), len(recognized)
    costs = [[0]*(m+1) for _ in range(n+1)]
    for i in range(n+1): costs[i][0] = i
    for j in range(m+1): costs[0][j] = j
    for i in range(1, n+1):
        for j in range(1, m+1):
            costs[i][j] = min(costs[i-1][j-1] + (expected[i-1] != recognized[j-1]),
                              costs[i-1][j] + 1, costs[i][j-1] + 1)
    i, j, steps = n, m, []
    while i or j:
        if i and j and costs[i][j] == costs[i-1][j-1] + (expected[i-1] != recognized[j-1]):
            steps.append(('equal' if expected[i-1] == recognized[j-1] else 'replace', i-1, j-1))
            i -= 1; j -= 1
        elif i and costs[i][j] == costs[i-1][j] + 1:
            steps.append(('delete', i-1, None)); i -= 1
        else:
            steps.append(('insert', None, j-1)); j -= 1
    steps.reverse()
    return steps


def split_caption_text(text, max_han=24):
    chunks=[]
    prefix=''
    for piece in re.findall(r'.+?(?:[，。！？；：,.!?;:]|$)', text):
        if norm(piece):
            chunks.append(prefix+piece); prefix=''
        elif chunks:
            chunks[-1] += piece
        else:
            prefix += piece

    combined=[]
    for chunk in chunks:
        if (combined and han_count(combined[-1]) < 6
                and re.search(r'[，：、,:]$',combined[-1])
                and han_count(combined[-1]+chunk) <= max_han):
            combined[-1] += chunk
        else:
            combined.append(chunk)
    result = []
    for chunk in combined:
        while han_count(chunk) > max_han:
            # Prefer explicit list separators, then a short connective boundary.
            candidate = None
            for match in re.finditer(r'、|(?=不过|但是|而且|也不|不能|可以|让|再|同时|目前|并不)', chunk):
                cut = match.end() if match.group() else match.start()
                if 9 <= han_count(chunk[:cut]) <= max_han:
                    candidate = cut
            if candidate is None:
                count, candidate = 0, len(chunk)
                for k, char in enumerate(chunk):
                    count += bool(re.match(r'[\u3400-\u9fff]', char))
                    if count == max_han:
                        candidate = k + 1; break
            result.append(chunk[:candidate]); chunk = chunk[candidate:]
        if norm(chunk): result.append(chunk)
    if ''.join(result) != text:
        raise RuntimeError('Subtitle splitting changed script text.')
    return result


def differences(steps, expected, recognized, char_to_word, words):
    groups, current = [], None
    for op, ei, ai in steps:
        if op == 'equal':
            current = None; continue
        if current is None or current['operation'] != op:
            current = {'operation': op, 'expected': '', 'recognized': '', 'expected_char_indices': [], 'word_indices': []}
            groups.append(current)
        if ei is not None:
            current['expected'] += expected[ei]; current['expected_char_indices'].append(ei)
        if ai is not None:
            current['recognized'] += recognized[ai]
            wi = char_to_word[ai]
            if wi not in current['word_indices']: current['word_indices'].append(wi)
    for group in groups:
        if group['word_indices']:
            group['start'] = words[group['word_indices'][0]]['start']
            group['end'] = words[group['word_indices'][-1]]['end']
    return groups


def aligned_chapter(chapter, script_segments, cache):
    selected = [s for s in script_segments if s['chapter'] == chapter['id']]
    expected = ''.join(norm(s['text']) for s in selected)
    if expected != norm(chapter['text']):
        raise RuntimeError('Chapter script differs from frozen segments: ' + chapter['id'])
    words = cache['words']
    audio_duration=cache['audio_info']['duration']
    invalid_words=[]
    for wi,word in enumerate(words):
        try:
            a,b=float(word['start']),float(word['end'])
            valid=math.isfinite(a) and math.isfinite(b) and 0 <= a <= b <= audio_duration+1e-6
        except (KeyError,ValueError,TypeError):
            valid=False
        if not valid: invalid_words.append(wi)
    if invalid_words:
        return {'id':chapter['id'],'source_sha256':cache['source_sha256'],
                'expected_text':chapter['text'],'recognized_text':cache['recognized_text'],
                'exact_char_ratio':0,'differences':[],'segments':[],'captions':[],
                'warnings':[],'errors':['Invalid/out-of-audio ASR word times: '+str(invalid_words)],'needs_review':True}
    recognized, char_to_word = '', []
    for wi, word in enumerate(words):
        token = norm(word['word'])
        recognized += token; char_to_word.extend([wi]*len(token))
    steps = align_chars(expected, recognized)
    mapping, kinds = {}, {}
    for op, ei, ai in steps:
        if ei is not None:
            kinds[ei] = op
            if ai is not None: mapping[ei] = char_to_word[ai]
    diffs = differences(steps, expected, recognized, char_to_word, words)
    alerts, errors, segs, captions = [], [], [], []
    pauses = cache.get('silence', {}).get('-42', [])
    offset = 0
    span_by_id={}
    for segment in selected:
        text_norm = norm(segment['text'])
        lo, hi = offset, offset + len(text_norm)
        span_by_id[segment['id']] = (lo,hi)
        indices = sorted(set(mapping[i] for i in range(lo, hi) if i in mapping))
        exact = sum(kinds.get(i) == 'equal' for i in range(lo, hi))
        if not indices:
            errors.append(segment['id'] + ': no observed ASR word anchors'); offset = hi; continue
        row = {'id': segment['id'], 'chapter': chapter['id'], 'text': segment['text'],
               'start': words[indices[0]]['start'], 'end': words[indices[-1]]['end'],
               'first_word': indices[0], 'last_word': indices[-1],
               'exact_char_ratio': round(exact / max(1, len(text_norm)), 4),
               'missing_chars': sum(i not in mapping for i in range(lo, hi)),
               'timing_source': 'independent ASR whole-word anchors', 'visual_intent': segment.get('visual_intent')}
        if row['exact_char_ratio'] < .90:
            alerts.append(segment['id'] + ': exact normalized character agreement below 90%')
        if row['exact_char_ratio'] < .55:
            errors.append(segment['id'] + ': too few exact lexical anchors for automatic timing')
        segs.append(row)
        chunk_offset, pending = lo, []
        for chunk in split_caption_text(segment['text']):
            size = len(norm(chunk)); a, b = chunk_offset, chunk_offset+size; chunk_offset = b
            wis = sorted(set(mapping[i] for i in range(a,b) if i in mapping))
            item = {'text': chunk, 'segment_id': segment['id'], 'chapter': chapter['id'],
                    'expected_char_range': [a,b], 'word_indices': wis,
                    'exact_chars': sum(kinds.get(i) == 'equal' for i in range(a,b)),
                    'substituted_chars': sum(kinds.get(i) == 'replace' for i in range(a,b)),
                    'missing_chars': sum(i not in mapping for i in range(a,b)), 'warnings': []}
            if not wis:
                errors.append(segment['id'] + ': unanchored caption ' + chunk)
                item['warnings'].append('No ASR word anchors; no fabricated timing assigned.')
                pending.append(item); continue
            if pending and pending[-1]['word_indices'] and set(pending[-1]['word_indices']) & set(wis):
                # Subtitle boundary fell inside one indivisible observed ASR word.
                prev = pending[-1]
                prev['text'] += chunk
                prev['expected_char_range'][1] = b
                prev['word_indices'] = sorted(set(prev['word_indices']) | set(wis))
                for key in ['exact_chars','substituted_chars','missing_chars']: prev[key] += item[key]
                prev['warnings'].append('Merged at shared ASR word; word time was not divided by character count.')
            else:
                pending.append(item)
        for item in pending:
            wis = item['word_indices']
            if not wis: continue
            first, last = words[wis[0]], words[wis[-1]]
            start, end = float(first['start']), float(last['end'])
            item.update({'raw_word_start': start, 'raw_word_end': end, 'pause_refinements': []})
            item.update({'start':start, 'end':end, 'speech_start':start, 'speech_end':end,
                         'first_word':wis[0], 'last_word':wis[-1],
                         'asr_text': ''.join(words[i]['word'] for i in range(wis[0],wis[-1]+1)),
                         'timing_source':'ASR whole-word anchors with nearby observed silence edges',
                         'low_probability_words':[{'index':i, **words[i]} for i in wis
                            if words[i].get('probability',1) < .65]})
            if end <= start:
                errors.append(segment['id']+': non-positive observed caption duration: '+item['text'])
            if item['missing_chars'] or item['substituted_chars']:
                item['warnings'].append('ASR differs from script; read the independent evidence and listen.')
            if item['low_probability_words']:
                item['warnings'].append('ASR word probability below review threshold 0.65; not a calibrated confidence interval.')
            if han_count(item['text']) > 24:
                item['warnings'].append('More than 24 Han characters because an observed word boundary could not be split safely.')
                errors.append(segment['id']+': long shared-word caption needs manual re-segmentation')
            a,b = item['expected_char_range']
            if a not in mapping or b-1 not in mapping:
                errors.append(segment['id']+': missing caption boundary word: '+item['text'])
            if item['exact_chars']==0:
                errors.append(segment['id']+': caption has no exact lexical anchor: '+item['text'])
            if kinds.get(a) != 'equal' or kinds.get(b-1) != 'equal':
                item['warnings'].append('Non-exact lexical boundary anchor; review onset/end.')
            captions.append(item)
        offset = hi
    # Refine each inter-caption boundary jointly. Whisper often includes the
    # sentence pause in its next word. A measured quiet interval inside the two
    # boundary words can assign the actual silence edges without dividing words.
    for previous, current in zip(captions,captions[1:]):
        low = float(words[previous['last_word']]['start'])
        high = float(words[current['first_word']]['end'])
        midpoint = (previous['raw_word_end']+current['raw_word_start'])/2
        candidates = [p for p in pauses if p['duration'] >= .14
            and p['start'] >= low-.015 and p['end'] <= high+.015
            and abs((p['start']+p['end'])/2-midpoint) <= .5]
        if candidates:
            pause = min(candidates,key=lambda p:abs((p['start']+p['end'])/2-midpoint))
            previous['speech_end'] = previous['end'] = pause['start']
            current['speech_start'] = current['start'] = pause['end']
            previous['pause_refinements'].append({'edge':'end','silence':pause,'method':'joint adjacent-word pause'})
            current['pause_refinements'].append({'edge':'start','silence':pause,'method':'joint adjacent-word pause'})
    if captions:
        first, last = captions[0], captions[-1]
        for pause in pauses:
            if pause['start'] <= .005 and pause['end'] <= float(words[first['first_word']]['end']):
                first['speech_start'] = first['start'] = pause['end']
                first['pause_refinements'].append({'edge':'start','silence':pause,'method':'observed file head silence'})
            if (pause['end'] >= cache['audio_info']['duration']-.005
                    and pause['start'] >= float(words[last['last_word']]['start'])):
                last['speech_end'] = last['end'] = pause['start']
                last['pause_refinements'].append({'edge':'end','silence':pause,'method':'observed file tail silence'})
    for previous, current in zip(captions,captions[1:]):
        if current['speech_start'] < previous['speech_end'] - .001:
            errors.append('Overlapping observed captions '+previous['segment_id']+'/'+current['segment_id'])
    for segment in segs:
        children=[c for c in captions if c['segment_id']==segment['id']]
        if children:
            segment['raw_word_start']=segment['start']; segment['raw_word_end']=segment['end']
            segment['start']=children[0]['speech_start']; segment['end']=children[-1]['speech_end']
    # Compute all display starts before holds, so no later lead-in adjustment can
    # create an overlap. Holds are presentation metadata, not speech timestamps.
    for item in captions:
        if not (0 <= item['speech_start'] < item['speech_end'] <= audio_duration+1e-6):
            errors.append('Invalid refined speech interval: '+item['text'])
        item['start'] = floor_frame(max(0,item['speech_start']-.033))
    for i,item in enumerate(captions):
        next_start = captions[i+1]['start'] if i+1<len(captions) else ceil_frame(cache['audio_info']['duration'])
        item['end'] = min(ceil_frame(item['speech_end']+.14), next_start)
        if item['end'] <= item['start']:
            errors.append('Non-positive display interval: '+item['text'])
        item['start_frame']=round(item['start']*FPS); item['end_frame']=round(item['end']*FPS)
        item['id'] = chapter['id'] + '-c' + str(i+1).zfill(3)
    word_cues=[]
    for cue_id,segment_id,phrase in WORD_CUES:
        if segment_id not in span_by_id:continue
        a,b=span_by_id[segment_id]
        pos=expected.find(norm(phrase),a,b)
        if pos<0:continue
        stop=pos+len(norm(phrase))
        wis=sorted(set(mapping[i] for i in range(pos,stop) if i in mapping))
        if not wis:continue
        first,last=wis[0],wis[-1]
        start,end=float(words[first]['start']),float(words[last]['end'])
        # Use the same observed pauses as caption edges where available.
        for cap in captions:
            ca,cb=cap['expected_char_range']
            if ca==pos:start=cap['speech_start']
            if cb==stop:end=cap['speech_end']
        if first>0:
            low=float(words[first-1]['start']); high=float(words[first]['end'])
            center=(float(words[first-1]['end'])+float(words[first]['start']))/2
            candidates=[p for p in pauses if p['duration']>=.14 and p['start']>=low-.015
                and p['end']<=high+.015 and abs((p['start']+p['end'])/2-center)<=.5]
            if candidates:start=min(candidates,key=lambda p:abs((p['start']+p['end'])/2-center))['end']
        ratio=sum(kinds.get(i)=='equal' for i in range(pos,stop))/max(1,stop-pos)
        word_cues.append({'id':cue_id,'chapter':chapter['id'],'segment_id':segment_id,'phrase':phrase,
            'start':start,'end':end,'source_start':start,'source_end':end,
            'first_word':first,'last_word':last,'exact_char_ratio':round(ratio,4),
            'needs_review':ratio<1 or any(i not in mapping for i in range(pos,stop)),
            'timing_source':'independent ASR whole-word anchors and observed phrase-onset silence'})
    return {'id':chapter['id'], 'source_sha256':cache['source_sha256'],
            'expected_text':chapter['text'], 'recognized_text':cache['recognized_text'],
            'exact_char_ratio':round(sum(op=='equal' for op,_,_ in steps)/max(1,len(expected)),4),
            'differences':diffs, 'segments':segs, 'captions':captions, 'word_cues':word_cues,
            'warnings':alerts, 'errors':errors,
            'needs_review':bool(diffs or alerts or errors or any(c['warnings'] for c in captions))}


def estimated_alignment(chapter, script_segments):
    elapsed, segs, captions = 0., [], []
    for segment in [s for s in script_segments if s['chapter']==chapter['id']]:
        length = max(1,han_count(segment['text']))/4.5
        segs.append({**segment, 'start':elapsed,'end':elapsed+length,'timing_source':'ESTIMATE ONLY: 4.5 Han characters/s'})
        cap_time = elapsed
        for chunk in split_caption_text(segment['text']):
            cap_length = han_count(chunk)/4.5
            captions.append({'id':chapter['id']+'-e'+str(len(captions)+1).zfill(3),
                'chapter':chapter['id'],'segment_id':segment['id'],'text':chunk,
                'start':cap_time,'end':cap_time+cap_length,'timing_source':'ESTIMATE ONLY; not ASR'})
            cap_time += cap_length
        elapsed += length
    return {'id':chapter['id'],'segments':segs,'captions':captions,'estimated_audio_duration':elapsed}


def assemble(chapter_specs, script, aligned, caches, estimated=False):
    cursor, chapters, segments, captions, audio_segments, word_cues = 0., [], [], [], [], []
    title_at = None
    for ci, chapter in enumerate(chapter_specs):
        ident = chapter['id']
        if ci>0 and ident not in ['title','breath']:
            cursor = ceil_frame(cursor+.9)
        chapter_start = cursor
        if ident == 'title':
            title_at = cursor
            end = ceil_frame(cursor+4.4)
            title_seg = next(s for s in script['segments'] if s['chapter']=='title')
            placed = [{**title_seg,'start':cursor,'end':end,'timing_source':'authored silent title','start_frame':round(cursor*FPS),'end_frame':round(end*FPS)}]
            chapter_row={'id':ident,'title':TITLES[ident],'start':cursor,'end':end,
                         'duration':r(end-cursor),'segments':placed,'silent':True}
        else:
            row = aligned[ident]
            source_duration = row['estimated_audio_duration'] if estimated else caches[ident]['audio_info']['duration']
            audio_start = ceil_frame(cursor+.5)
            audio_end = audio_start+source_duration
            end = ceil_frame(audio_end+(2.0 if ident=='closing' else 1.5))
            placed=[]
            for segment in row['segments']:
                child_caps=[c for c in row['captions'] if c['segment_id']==segment['id']]
                frame_start=round((audio_start+(child_caps[0]['start'] if child_caps else segment['start']))*FPS)
                frame_end=round((audio_start+(child_caps[-1]['end'] if child_caps else segment['end']))*FPS)
                placed.append({**segment,'speech_start':audio_start+segment['start'],
                    'speech_end':audio_start+segment['end'],'start':frame_start/FPS,'end':frame_end/FPS,
                    'start_frame':frame_start,'end_frame':frame_end})
            for cue in row.get('word_cues',[]):
                sf=round((audio_start+cue['start'])*FPS);ef=round((audio_start+cue['end'])*FPS)
                word_cues.append({**cue,'start':sf/FPS,'end':ef/FPS,'start_frame':sf,'end_frame':ef,
                                  'speech_start':audio_start+cue['start'],'speech_end':audio_start+cue['end']})
            for caption in row['captions']:
                start_frame=round((audio_start+caption['start'])*FPS)
                end_frame=round((audio_start+caption['end'])*FPS)
                copy={**caption,'start':start_frame/FPS,'end':end_frame/FPS,
                      'start_frame':start_frame,'end_frame':end_frame}
                if not estimated:
                    copy['source_speech_start']=copy.pop('speech_start'); copy['source_speech_end']=copy.pop('speech_end')
                captions.append(copy)
            audio_row={'id':ident,'chapter':ident,'start':audio_start,'end':audio_end,
                       'duration':r(source_duration),'source_audio_duration':source_duration,
                       'audio':f'longform/assets/voice/raw/{ident}.wav','playback_rate':1.0,
                       'source_in':0,'source_out':source_duration,'estimated':estimated}
            if not estimated: audio_row['source_sha256']=caches[ident]['source_sha256']
            audio_segments.append(audio_row)
            chapter_row={'id':ident,'title':TITLES[ident],'start':chapter_start,'end':end,
                         'duration':r(end-chapter_start),'audio_start':audio_start,'audio_end':audio_end,
                         'head_hold':.5,'tail_hold':2.0 if ident=='closing' else 1.5,'segments':placed}
        chapters.append(chapter_row); segments.extend(placed); cursor=end
    duration=ceil_frame(cursor)
    cuts=sorted({round(t*FPS)/FPS for c in captions for t in [c['start'],c['end']]}
                |{round(t*FPS)/FPS for c in chapters for t in [c['start'],c['end']]})
    return {'schema':'longform-timeline/1','timing_status':'estimated-preview' if estimated else 'independent-asr-observed',
            'estimated':estimated,'duration':duration,'fps':FPS,'width':2560,'height':1440,
            'frame_count':round(duration*FPS),'title':script['title'],'chapters':chapters,
            'segments':segments,'captions':captions,'word_cues':word_cues,'audio_segments':audio_segments,'narration':audio_segments,
            'music':{'title_at':title_at},'cuts':cuts,'cut_frames':[round(t*FPS) for t in cuts],
            'narration_playback_rate':1.0,'timing_policy':{'chapter_head':.5,'chapter_tail':1.5,
                'closing_tail':2,'between_body_chapters':.9,'silent_title':4.4},
            'limitations':['ASR word times are estimates, not phoneme forced alignment or human listening.',
                          'No clock is divided proportionally inside an ASR word.',
                          'Original ASR differences and low probability words are retained for review.']}


def report_markdown(report):
    lines=['# 长片独立 ASR 与字幕对齐报告','',
        '全离线；没有台本提示词；原速原文件。差异是复听线索，不等于确认读错。',
        '正式字幕边界来自匹配到的原始 ASR 词区间及邻近静音，未按字数切分词内时间。',
        '识别 probability 门槛只是人工复核规则，不是经过校准的置信度。','',
        f"当前章节：{len(report['chapters'])}/9；缺失：{', '.join(report['missing_chapters']) or '无'}",'',
        '| 章 | 精确字符一致率 | 差异数 | 字幕复核数 | 阻断问题 |','| --- | ---: | ---: | ---: | --- |']
    for row in report['chapters']:
        lines.append(f"| {row['id']} | {row['exact_char_ratio']:.1%} | {len(row['differences'])} | {sum(bool(c['warnings']) for c in row['captions'])} | {'；'.join(row['errors']) or '无'} |")
    for row in report['chapters']:
        lines += ['', '## '+row['id'],'','台本：'+row['expected_text'],'','原始识别：'+row['recognized_text'],'']
        for diff in row['differences']:
            lines.append('- '+diff['operation']+': '+(diff['expected'] or '∅')+' → '+(diff['recognized'] or '∅'))
        for caption in row['captions']:
            if caption['warnings']:
                lines.append(f"- {caption['id']} [{caption['start']:.2f}–{caption['end']:.2f}s 原章音频] {caption['text']}："+'；'.join(caption['warnings']))
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('chapters',nargs='*',help='Only transcribe these chapters; build using all current caches.')
    parser.add_argument('--estimate-only',action='store_true')
    parser.add_argument('--build-only',action='store_true')
    parser.add_argument('--force-asr',action='store_true')
    parser.add_argument('--model',type=Path,default=MODEL)
    parser.add_argument('--ffmpeg')
    args=parser.parse_args()
    script=load_json(CONTENT/'script.json'); specs=load_json(CONTENT/'tts-chapters.json')
    if len(script['segments'])!=35 or sum(bool(norm(s['text'])) for s in script['segments'])!=34:
        raise RuntimeError('Frozen script must contain 35 segments, 34 voiced.')
    expected_ids=[c['id'] for c in specs if norm(c['text'])]
    if len(expected_ids)!=9 or set(args.chapters)-set(expected_ids):
        raise RuntimeError('Expected exactly nine valid voice chapter IDs.')
    estimate_rows={c['id']:estimated_alignment(c,script['segments']) for c in specs if norm(c['text'])}
    estimate=assemble(specs,script,estimate_rows,{},estimated=True)
    write_json(CONTENT/'estimated-timeline.json',estimate)
    write_json(CONTENT/'estimated-captions.json',{'schema':'longform-captions/1','estimated':True,
              'duration':estimate['duration'],'fps':FPS,'cuts':estimate['cuts'],
              'cut_frames':estimate['cut_frames'],'captions':estimate['captions']})
    print('Estimated preview: '+str(estimate['duration'])+' s; never used as official timeline.',flush=True)
    if args.estimate_only:return
    ffmpeg=ffmpeg_path(args.ffmpeg)
    if not args.build_only:
        for chapter in specs:
            if norm(chapter['text']) and (not args.chapters or chapter['id'] in args.chapters):
                transcribe(chapter,ffmpeg,args.model,args.force_asr)
    caches, aligned, missing={},{},[]
    model_revision=load_json(args.model/'provenance.json').get('revision') if (args.model/'provenance.json').exists() else None
    for chapter in specs:
        ident=chapter['id']
        if not norm(chapter['text']):continue
        path=RAW/(ident+'.wav'); cache_path=ASR/(ident+'.json')
        if not path.exists() or not cache_path.exists():missing.append(ident);continue
        cache=load_json(cache_path)
        if (cache.get('source_sha256')!=sha(path) or not cache.get('words')
                or cache.get('model_path') != str(args.model)
                or cache.get('model_revision') != model_revision
                or cache.get('reference_prompt_used') is not False
                or cache.get('offline') is not True):
            missing.append(ident);continue
        caches[ident]=cache
        aligned[ident]=aligned_chapter(chapter,script['segments'],cache)
        write_json(ASR/(ident+'.alignment.json'),aligned[ident])
    report={'schema':'longform-asr-report/1','offline':True,'reference_prompt_used':False,
            'model':str(args.model),'alignment_version':VERSION,'missing_chapters':missing,
            'chapters':[aligned[c] for c in expected_ids if c in aligned],
            'automatic_review_thresholds':{'word_probability':.65,'segment_exact_ratio':.90},
            'limitations':['Independent ASR may misrecognize correct speech.',
                          'No reference text was supplied to recognition.',
                          'Only whole ASR word intervals and measured pauses determine formal caption timing.']}
    write_json(CONTENT/'asr-report.json',report)
    (CONTENT/'asr-report.md').write_text(report_markdown(report))
    errors=[e for row in aligned.values() for e in row['errors']]
    status={'complete':not missing and not errors,'missing_chapters':missing,'alignment_errors':errors,
            'processed_chapters':list(aligned),'estimated_duration':estimate['duration'],
            'audio_durations':{ident:cache['audio_info']['duration'] for ident,cache in caches.items()}}
    if missing or errors:
        write_json(CONTENT/'timeline-status.json',status)
        # Do not let a renderer accidentally consume an obsolete official clock.
        for name in ['timeline.json','captions.json']:
            path=CONTENT/name
            if path.exists():
                path.replace(CONTENT/(path.stem+'.stale.json'))
        print(json.dumps({'formal_timeline_written':False,**status},ensure_ascii=False),flush=True)
        return
    timeline=assemble(specs,script,aligned,caches)
    timeline['needs_review']=any(row['needs_review'] for row in aligned.values())
    timeline['asr_report']='longform/content/asr-report.json'
    timeline['script_sha256']=sha(CONTENT/'script.json')
    write_json(CONTENT/'timeline.json',timeline)
    write_json(CONTENT/'captions.json',{'schema':'longform-captions/1','estimated':False,
        'duration':timeline['duration'],'fps':FPS,'cuts':timeline['cuts'],
        'cut_frames':timeline['cut_frames'],'captions':timeline['captions']})
    status.update({'duration':timeline['duration'],'captions':len(timeline['captions']),
                   'needs_review':timeline['needs_review']})
    write_json(CONTENT/'timeline-status.json',status)
    print(json.dumps({'formal_timeline_written':True,'duration':timeline['duration'],
                      'captions':len(timeline['captions']),'needs_review':timeline['needs_review']},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
