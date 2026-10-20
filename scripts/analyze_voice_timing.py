#!/usr/bin/env python3
"""Offline ASR word timing plus acoustic silence bounds for MiniMax narration.

Run with the existing sibling ASR venv; models are read locally and never fetched.
Writes only the analysis JSON. Audio, captions and picture timing are untouched.
ASR timestamps are estimates, not forced alignment or a human listening check.
"""
from __future__ import annotations
import argparse
import datetime
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import unicodedata
import wave

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = ROOT.parent / 'proj1-1019/out/models/whisper-large-v3-turbo-q4'
PHRASES = {
    'intro': ['压力上来', '先别急着说服自己', '给身体一点缓冲'],
    'breath': ['一', '鼻子吸气', '再轻轻补一小口', '嘴巴慢慢呼出', '不要用力', '头晕就停'],
    'cool': ['二', '用凉毛巾轻敷脸颊', '保持自然呼吸'],
    'ear': ['三', '轻揉耳廓', '以舒服为准'],
    'shake': ['四', '轻轻抖动手脚', '放松肩膀', '别甩头'],
    'paper': ['五', '把烦心事写下来', '揉成纸团', '再丢掉'],
    'nature': ['六', '看一会儿树叶', '云朵', '让目光慢下来'],
    'order': ['七', '只整理桌面一小块', '让眼前恢复一点秩序'],
    'outro': ['不必全做', '挑一个就好', '先松一口气', '再处理眼前的事'],
}
# Observed spelling differences are retained in each row's differences field.
# These aliases only recover timing anchors; they never rewrite ASR evidence.
ASR_ORTHOGRAPHIC_VARIANTS = {
    '二': '2', '三': '3', '四': '4', '七': '7',
    '轻揉耳廓': '轻柔耳阔', '把烦心事写下来': '把凡心事写下来',
}



def normalize(text):
    return ''.join(c.lower() for c in unicodedata.normalize('NFKC', text)
                   if unicodedata.category(c)[0] in 'LN')


def ffmpeg_path(explicit):
    if explicit:
        return explicit
    if os.environ.get('MULTIPLANE_FFMPEG'):
        return os.environ['MULTIPLANE_FFMPEG']
    found = list((ROOT / '.tools/venv/lib').glob('python*/site-packages/imageio_ffmpeg/binaries/ffmpeg-*'))
    if not found:
        raise RuntimeError('Pass --ffmpeg; local bundled binary was not found')
    return str(found[0])


def silence_bounds(path, ffmpeg, duration, threshold):
    result = subprocess.run([ffmpeg, '-hide_banner', '-nostdin', '-i', str(path),
        '-af', f'silencedetect=noise={threshold}dB:d=0.08', '-f', 'null', '-'],
        capture_output=True, text=True, check=True)
    events = re.findall(r'silence_(start|end): ([0-9.]+)', result.stderr)
    intervals, pending = [], None
    for event, value in events:
        value = float(value)
        if event == 'start':
            pending = value
        elif pending is not None:
            intervals.append({'start': pending, 'end': value, 'duration': round(value-pending, 6)})
            pending = None
    if pending is not None:
        intervals.append({'start': pending, 'end': duration, 'duration': round(duration-pending, 6)})
    return intervals


def phrase_bounds(words, phrases):
    chars = ''
    mapping = []
    for index, word in enumerate(words):
        normalized = normalize(word['word'])
        chars += normalized
        mapping.extend([index] * len(normalized))
    result = []
    cursor = 0
    for phrase in phrases:
        target = normalize(phrase)
        position = chars.find(target, cursor)
        recognized_variant = None
        if position < 0 and phrase in ASR_ORTHOGRAPHIC_VARIANTS:
            # Explicitly retain observed ASR orthographic differences in the report.
            variant = ASR_ORTHOGRAPHIC_VARIANTS[phrase]
            position = chars.find(normalize(variant), cursor)
            if position >= 0:
                recognized_variant = variant
        row = {'phrase': phrase, 'matched': position >= 0}
        if recognized_variant:
            row['asr_orthographic_variant'] = recognized_variant
            row['variant_caution'] = 'Observed numeral/homophone spelling difference, retained in differences; not proof of correct or incorrect pronunciation.'
        if position >= 0:
            first, last = mapping[position], mapping[position+len(target)-1]
            row.update({'start': words[first]['start'], 'end': words[last]['end'],
                'asr_first_word': words[first]['word'], 'asr_last_word': words[last]['word'],
                'method': ('explicitly recorded ASR orthographic variant' if recognized_variant else 'exact normalized phrase match in independent ASR word stream'),
                'timing_status': 'estimated; inspect nearby acoustic pauses before using as an animation cue'})
            cursor = position + len(target)
        result.append(row)
    return result


def acoustic_phrase_bounds(row):
    """Label pause-separated regions only when count and independent ASR agree.

    The threshold sweep measures detector sensitivity, not a statistical CI.
    It deliberately keeps short within-phrase stops inside each phrase.
    """
    phrases = row.get('phrases', [])
    if not phrases or not all(p.get('matched') for p in phrases):
        return
    partitions = {}
    for threshold in ['-42', '-36']:
        cursor, regions = 0.0, []
        for pause in row['silence'][threshold]:
            if pause['duration'] < .16 and pause['start'] > .005 and pause['end'] < row['raw_duration'] - .005:
                continue
            if pause['start'] > cursor + .02:
                regions.append({'start': cursor, 'end': min(pause['start'], row['raw_duration'])})
            cursor = pause['end']
        if cursor < row['raw_duration'] - .02:
            regions.append({'start': cursor, 'end': row['raw_duration']})
        if len(regions) != len(phrases):
            row['acoustic_phrase_status'] = 'Unassigned: major-pause region count does not match phrase count.'
            return
        partitions[threshold] = regions
    for index, phrase in enumerate(phrases):
        region = partitions['-42'][index]
        overlap = max(0., min(region['end'], phrase['end']) - max(region['start'], phrase['start']))
        if overlap < .04:
            row['acoustic_phrase_status'] = 'Unassigned: ASR phrase does not overlap the acoustic region.'
            return
    row['acoustic_phrase_status'] = 'Bounded by pauses >=160ms; phrase count and order validated against independent ASR.'
    row['acoustic_phrases'] = []
    for index, phrase in enumerate(phrases):
        regions = [partitions[t][index] for t in ['-42', '-36']]
        row['acoustic_phrases'].append({
            'phrase': phrase['phrase'],
            'start': regions[0]['start'], 'end': regions[0]['end'],
            'start_threshold_sensitivity': [min(r['start'] for r in regions), max(r['start'] for r in regions)],
            'end_threshold_sensitivity': [min(r['end'] for r in regions), max(r['end'] for r in regions)],
            'method': 'Independent ASR labels plus -42dB silence edges; sensitivity sweep at -36dB.',
            'caution': 'Detector sensitivity is not a statistical confidence interval; quiet consonants can extend outside these bounds.'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ids', nargs='*')
    parser.add_argument('--model', type=Path, default=DEFAULT_MODEL)
    parser.add_argument('--ffmpeg')
    parser.add_argument('--output', type=Path, default=ROOT/'output/minimax/timing-analysis.json')
    parser.add_argument('--acoustic-only', action='store_true')
    args = parser.parse_args()
    ffmpeg = ffmpeg_path(args.ffmpeg)
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    import numpy as np
    if not args.acoustic_only:
        if not (args.model/'weights.npz').is_file():
            raise RuntimeError('Existing local model is missing; refusing to download')
        import mlx_whisper
    timeline = json.loads((ROOT/'content/timeline.json').read_text())
    previous = json.loads(args.output.read_text()) if args.output.exists() else {}
    retained = {row['id']: row for row in previous.get('segments', [])}
    report = {
        'generated_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'model': None if args.acoustic_only else str(args.model),
        'offline': True, 'reference_prompt_used': False,
        'timestamp_origin': 'seconds from start of the raw MiniMax WAV; not final placed/tempo-adjusted time',
        'limitations': ['ASR timestamps are estimated; not forced alignment.',
            'Acoustic silence can locate a pause but cannot label its linguistic meaning.',
            'No human listening claim; independent ASR may contain recognition errors.',
            'Raw timestamps must be transformed using the actual trimming, tempo and placement applied in the mix.'],
        'segments': [],
    }
    for segment in timeline['segments']:
        ident = segment['id']
        path = ROOT/'assets/audio/minimax/raw'/f'{ident}.wav'
        if not path.is_file() or (args.ids and ident not in args.ids):
            continue
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if (ident in retained and retained[ident].get('sha256') == sha
                and retained[ident].get('words') and previous.get('model') == str(args.model)
                and not args.acoustic_only):
            retained[ident]['phrases'] = phrase_bounds(retained[ident]['words'], PHRASES.get(ident, []))
            if ident == 'paper':
                retained[ident]['action_words'] = phrase_bounds(retained[ident]['words'], ['写下来', '揉成纸团', '再丢掉'])
            acoustic_phrase_bounds(retained[ident])
            report['segments'].append(retained[ident])
            print(ident+' cached', flush=True)
            continue
        with wave.open(str(path), 'rb') as wav:
            duration = wav.getnframes()/wav.getframerate()
            sample_rate = wav.getframerate()
        row = {'id': ident, 'file': str(path.relative_to(ROOT)), 'sha256': sha,
            'raw_duration': duration, 'sample_rate': sample_rate, 'expected_text': segment['text'],
            'silence': {str(threshold): silence_bounds(path, ffmpeg, duration, threshold)
                        for threshold in [-42,-36,-30]}}
        if not args.acoustic_only:
            start = time.monotonic()
            raw = subprocess.check_output([ffmpeg, '-v', 'error', '-i', str(path),
                '-ar', '16000', '-ac', '1', '-f', 'f32le', '-'])
            data = mlx_whisper.transcribe(np.frombuffer(raw, dtype='<f4').copy(),
                path_or_hf_repo=str(args.model), language='zh', task='transcribe',
                temperature=0., condition_on_previous_text=False, word_timestamps=True, verbose=False)
            row['asr_seconds'] = round(time.monotonic()-start, 3)
            row['recognized_text'] = data['text']
            row['words'] = [{k:w[k] for k in ['word','start','end','probability'] if k in w}
                for part in data.get('segments',[]) for w in part.get('words',[])]
            a,b = normalize(segment['text']), normalize(data['text'])
            row['differences'] = [{'expected':a[i:j], 'recognized':b[k:l], 'operation':op}
                for op,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes() if op!='equal']
            row['phrases'] = phrase_bounds(row['words'], PHRASES.get(ident, []))
            if ident == 'paper':
                row['action_words'] = phrase_bounds(row['words'], ['写下来', '揉成纸团', '再丢掉'])
            acoustic_phrase_bounds(row)
        report['segments'].append(row)
        print(json.dumps({'id':ident,'duration':duration,'text':row.get('recognized_text'),
            'phrases':row.get('phrases')},ensure_ascii=False), flush=True)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    present = {row['id'] for row in report['segments']}
    if args.ids:
        report['segments'].extend(row for ident,row in retained.items() if ident not in present)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')

if __name__ == '__main__':
    main()
