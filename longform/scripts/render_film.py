#!/usr/bin/env python3
"""Frame-exact, resumable Multiplane long-film rendering and delivery packaging.

Run from the repository after `source .tool-env`. No raw frame sequence is saved.
The chapter ranges include each following transition gap and partition [0, N).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time
import wave

ROOT = Path(__file__).resolve().parents[2]
LONG = ROOT / 'longform'
FPS, WIDTH, HEIGHT = 30, 2560, 1440


def fail(message):
    raise RuntimeError(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def resolve(path):
    p = Path(path)
    return p.resolve() if p.is_absolute() else (ROOT / p).resolve()


def seconds(frame):
    # Multiplane computes ceil(t * fps - 1e-9). Twelve decimal places are well
    # inside its tolerance at 30 fps; all arithmetic before this stays integer.
    return format(frame / FPS, '.12f')


def frame_at(value, label):
    f = float(value) * FPS
    n = round(f)
    if not math.isfinite(f) or abs(f - n) > 1e-5:
        fail(f'{label} is not aligned to {FPS} fps: {value!r}')
    return n


def make_plan(timeline, allow_estimated=False):
    d = read_json(timeline)
    if d.get('estimated', False) or 'estimated' in str(d.get('timing_status', '')).lower():
        if not allow_estimated:
            fail('Refusing an estimated timeline. Finish MiniMax/ASR alignment and generate longform/content/timeline.json first.')
    if (d.get('fps'), d.get('width'), d.get('height')) != (FPS, WIDTH, HEIGHT):
        fail(f'Timeline must specify {WIDTH}x{HEIGHT} @ {FPS} fps.')
    total = frame_at(d['duration'], 'duration')
    if total < 1 or d.get('frame_count') != total:
        fail('timeline.frame_count must equal the integer frame count of duration.')
    chapters = d.get('chapters', [])
    if not chapters:
        fail('Timeline has no chapters.')
    starts = [frame_at(ch['start'], ch['id'] + '.start') for ch in chapters]
    if starts[0] != 0 or starts != sorted(set(starts)) or starts[-1] >= total:
        fail('Chapter starts must be unique, increasing, and begin at frame zero.')
    ranges, seen = [], set()
    for i, ch in enumerate(chapters):
        cid = ch['id']
        if not re.fullmatch(r'[a-z0-9_-]+', cid) or cid in seen:
            fail(f'Unsafe or duplicate chapter ID: {cid!r}')
        seen.add(cid)
        first, end = starts[i], starts[i + 1] if i + 1 < len(starts) else total
        authored_end = frame_at(ch['end'], cid + '.end')
        if not first < authored_end <= end:
            fail(f'{cid}: chapter end overlaps the next chapter or precedes its own start.')
        ranges.append({'index': i + 1, 'id': cid, 'title': ch.get('title', cid),
                       'first_frame': first, 'end_frame': end, 'frames': end - first,
                       'from': seconds(first), 'to': seconds(end),
                       'chapter_end_frame': authored_end,
                       'included_transition_frames': end - authored_end,
                       'filename': f'{i + 1:02d}-{cid}.mp4'})
    if sum(r['frames'] for r in ranges) != total:
        fail('Internal error: chapter ranges do not partition the whole film.')
    return {'schema': 'longform-render-plan/1', 'timeline': str(timeline),
            'timeline_sha256': sha256(timeline), 'estimated': bool(d.get('estimated', False)),
            'width': WIDTH, 'height': HEIGHT, 'fps': FPS, 'frames': total,
            'duration': total / FPS, 'chapters': ranges}


def find_ffmpeg(explicit=None):
    candidates = [explicit, os.environ.get('MULTIPLANE_FFMPEG'), shutil.which('ffmpeg')]
    candidates += list((ROOT / '.tools/venv/lib').glob('python*/site-packages/imageio_ffmpeg/binaries/ffmpeg-*'))
    for item in candidates:
        if item and Path(item).is_file() and os.access(item, os.X_OK):
            return str(Path(item).resolve())
    fail('FFmpeg was not found. Source .tool-env or pass --ffmpeg; installation is not performed by this pipeline.')


def source_fingerprint(timeline, shot, options):
    paths = {timeline, shot, ROOT / 'node_modules/multiplane/package.json'}
    for folder in (LONG / 'shots', LONG / 'assets'):
        if folder.exists():
            for p in folder.rglob('*'):
                # The silent picture does not depend on speech/audio files.
                if p.is_file() and p.suffix.lower() in {'.js', '.html', '.css', '.svg', '.png', '.jpg', '.jpeg', '.webp', '.woff', '.woff2', '.ttf', '.otf'}:
                    paths.add(p)
    # Other directly authored root JS/CSS and caption files can affect pixels.
    paths.update(p for p in LONG.glob('*') if p.is_file() and p.suffix in {'.js', '.css'})
    for name in ('captions.json', 'render-config.json', 'render-config.js', 'render-data.js', 'action-cues.json'):
        p = LONG / 'content' / name
        if p.exists():
            paths.add(p)
    sources = {str(p.relative_to(ROOT)): sha256(p) for p in sorted(paths) if p.exists()}
    builder = LONG / 'scripts' / 'build_render_data.py'
    if builder.exists():
        sources[str(builder.relative_to(ROOT))] = sha256(builder)
    payload = {'sources': sources, 'options': options}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(), payload


def run_logged(cmd, logfile, *, events=False):
    """Write full output; show compact chapter/phase progress while rendering."""
    logfile.parent.mkdir(parents=True, exist_ok=True)
    result, last_progress, last_pct = None, 0.0, -10
    with logfile.open('w', encoding='utf-8') as log:
        log.write('$ ' + shlex.join(map(str, cmd)) + '\n')
        log.flush()
        process = subprocess.Popen(list(map(str, cmd)), cwd=ROOT, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, bufsize=1)
        try:
            for text in process.stdout:
                log.write(text)
                log.flush()
                if not events:
                    continue
                try:
                    event = json.loads(text)
                except ValueError:
                    continue
                if event.get('type') == 'result':
                    result = event
                if event.get('type') == 'warning':
                    print('  warning: ' + str(event.get('code') or event.get('message')), flush=True)
                if event.get('type') == 'progress':
                    now = time.monotonic()
                    total, done = event.get('total') or 0, event.get('done') or 0
                    pct = int(100 * done / total) if total else 0
                    if now - last_progress >= 20 or pct >= last_pct + 10:
                        print(f"  {event.get('phase', 'render')}: {done}/{total or '?'} ({pct}%)", flush=True)
                        last_progress, last_pct = now, pct
            code = process.wait()
        except BaseException:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            raise
    if code != 0:
        fail(f'Command failed ({code}); read {logfile}')
    if events and (not result or result.get('ok') is not True):
        fail(f'Multiplane did not report ok:true; read {logfile}')
    return result


def decode_probe(ffmpeg, path, logfile, expected_frames, width=WIDTH, height=HEIGHT, audio=False):
    """Decode every picture, verify contiguous timestamps and exact frame count.

    Uses FFmpeg's showinfo because this host need not have a separate ffprobe.
    -xerror makes a decoding error fail the pipeline, not just become a warning.
    """
    cmd = [ffmpeg, '-hide_banner', '-nostdin', '-nostats', '-xerror', '-i', str(path),
           '-map', '0:v:0', '-an', '-vf', 'showinfo=checksum=0', '-fps_mode', 'passthrough', '-f', 'null', '-']
    run_logged(cmd, logfile)
    text = logfile.read_text(encoding='utf-8')
    rate = re.search(r'config in time_base:\s*(\d+)/(\d+), frame_rate:\s*(\d+)/(\d+)', text)
    if not rate:
        fail(f'Could not read frame rate from {logfile}')
    tb = int(rate[1]) / int(rate[2])
    fps = int(rate[3]) / int(rate[4])
    if abs(fps - FPS) > 1e-6:
        fail(f'{path.name}: decoded rate is {fps}, expected {FPS}.')
    matches = list(re.finditer(r'\bn:\s*(\d+)\s+pts:\s*(-?\d+)\s+pts_time:.*?fmt:(\S+).*?\bs:(\d+)x(\d+)', text))
    if len(matches) != expected_frames:
        fail(f'{path.name}: decoded {len(matches)} frames, expected {expected_frames}.')
    base = int(matches[0][2]) * tb
    for i, m in enumerate(matches):
        if int(m[1]) != i or (int(m[4]), int(m[5])) != (width, height) or m[3] != 'yuv420p':
            fail(f'{path.name}: unexpected frame index, dimensions or pixel format at frame {i}.')
        if abs((int(m[2]) * tb - base) - i / FPS) > max(tb * .55, 1e-6):
            fail(f'{path.name}: non-contiguous frame timestamp at frame {i}.')
    input_header = text.split('Stream mapping:')[0]
    if not re.search(r'Video:\s*h264\b', input_header):
        fail(f'{path.name}: expected H.264 video.')
    packet_log = logfile.with_name(logfile.stem + '-packets.log')
    run_logged([ffmpeg, '-hide_banner', '-nostdin', '-nostats', '-i', str(path), '-map', '0:v:0',
                '-an', '-c', 'copy', '-loglevel', 'verbose', '-f', 'null', '-'], packet_log)
    packet_text = packet_log.read_text(encoding='utf-8')
    packet = re.search(r'Output stream #0:0 \(video\):\s*(\d+) packets muxed', packet_text)
    if not packet or int(packet[1]) != expected_frames:
        fail(f'{path.name}: copied packet count did not match the decoded frame count.')
    if audio:
        if not re.search(r'Audio:\s*aac\b', input_header):
            fail(f'{path.name}: missing AAC audio.')
        run_logged([ffmpeg, '-hide_banner', '-nostdin', '-v', 'error', '-xerror', '-i', str(path),
                    '-map', '0:a:0', '-vn', '-f', 'null', '-'], logfile.with_name(logfile.stem + '-audio.log'))
    return {'frames': expected_frames, 'packet_count': int(packet[1]), 'duration': expected_frames / FPS,
            'first_pts': base, 'fps': fps, 'width': width, 'height': height,
            'codec': 'h264', 'pixel_format': 'yuv420p', 'audio_decoded': audio}


def validate_mix(path, expected_seconds):
    if not path.is_file():
        fail(f'Final mix is missing: {path}')
    with wave.open(str(path), 'rb') as w:
        info = {'sample_rate': w.getframerate(), 'channels': w.getnchannels(),
                'samples': w.getnframes(), 'duration': w.getnframes() / w.getframerate()}
    if info['sample_rate'] != 48000 or info['channels'] != 2:
        fail('final-mix.wav must be stereo, 48 kHz.')
    # A sub-frame pad or trim is explicit in the final mux; anything larger may
    # conceal missing narration and is rejected rather than hidden by -shortest.
    if abs(info['duration'] - expected_seconds) > 1 / FPS + 1 / 48000:
        fail(f"Final mix lasts {info['duration']:.6f}s, picture lasts {expected_seconds:.6f}s.")
    return info


def receipt_valid(receipt, video, fingerprint, expected):
    if not receipt.exists() or not video.exists():
        return False
    try:
        d = read_json(receipt)
        return (d.get('complete') is True and d.get('fingerprint') == fingerprint
                and d.get('frames') == expected and d.get('file_sha256') == sha256(video))
    except (ValueError, OSError):
        return False


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--timeline', default='longform/content/timeline.json')
    parser.add_argument('--shot', default='longform/index.html')
    parser.add_argument('--audio', default='longform/assets/audio/final-mix.wav')
    parser.add_argument('--output-dir', default='longform/output')
    parser.add_argument('--chapter', action='append', help='Render selected chapter ID(s), comma-separated or repeated; no full-film mux.')
    parser.add_argument('--workers', type=int, choices=(1, 2), default=2, help='Chromium workers inside one chapter; chapters run sequentially.')
    parser.add_argument('--raster', choices=('software', 'gpu'), default='gpu')
    parser.add_argument('--quality', choices=('standard', 'fast', 'high'), default='standard')
    parser.add_argument('--ffmpeg')
    parser.add_argument('--resume', action='store_true', help='Reuse only successful chapter files with matching source fingerprints and SHA-256.')
    parser.add_argument('--prepare', action='store_true', help='Write frame plan and commands; do not launch a browser or render.')
    parser.add_argument('--allow-estimated', action='store_true', help='Only with --prepare, allow an explicitly estimated plan.')
    parser.add_argument('--verify-only', action='store_true', help='Inspect and verify the entire shot; do not render.')
    parser.add_argument('--delivery-1080', action='store_true', help='Also create master-landscape-1080p.mp4 with Lanczos downscaling.')
    parser.add_argument('--mux-only', action='store_true', help='Validate all existing chapter receipts and package without rendering.')
    args = parser.parse_args(argv)
    if args.allow_estimated and not args.prepare:
        parser.error('--allow-estimated is only allowed with --prepare.')
    timeline, shot, audio, out = map(resolve, (args.timeline, args.shot, args.audio, args.output_dir))
    # Even an explicit output override must stay inside the new longform project.
    if out != LONG and LONG not in out.parents:
        fail('--output-dir must be inside longform; old short-film output is protected.')
    if not timeline.exists():
        fail(f'Actual timeline is not ready: {timeline}')
    plan = make_plan(timeline, args.allow_estimated)
    chapters_dir, logs, jobs = out / 'chapters', out / 'logs', out / 'jobs'
    for folder in (chapters_dir, logs, jobs):
        folder.mkdir(parents=True, exist_ok=True)
    cli = ROOT / 'node_modules/.bin/multiplane'
    if not cli.exists():
        fail('Repository Multiplane CLI is missing. No installation was attempted.')
    ffmpeg = find_ffmpeg(args.ffmpeg)
    options = {'fps': FPS, 'width': WIDTH, 'height': HEIGHT, 'quality': args.quality,
               'raster': args.raster, 'encoder': 'x264', 'max_bitrate_mbps': 40, 'scale': 1}
    fingerprint, inputs = source_fingerprint(timeline, shot, options)
    common = ['--root', str(ROOT), '--job-dir', str(jobs), '--fps', str(FPS), '--json']
    visual = ['--scale', '1', '--render-scale', '1', '--quality', args.quality, '--raster', args.raster,
              '--workers', str(args.workers), '--no-hosted']
    render_extra = ['--encoder', 'x264', '--max-bitrate', '40', '--ffmpeg', ffmpeg]
    for ch in plan['chapters']:
        ch['command'] = [str(cli), 'render', str(shot), *common, *visual, *render_extra,
                         '--from', ch['from'], '--to', ch['to'], '--out', str(chapters_dir / ch['filename']), '--overwrite']
    plan.update({'fingerprint': fingerprint, 'render_options': options})
    write_json(out / 'render-plan.json', plan)
    write_json(out / 'render-inputs.json', inputs)
    print(f"Plan: {plan['frames']} frames, {plan['duration']:.3f}s, {len(plan['chapters'])} contiguous chapter ranges.", flush=True)
    for ch in plan['chapters']:
        print(f"  {ch['id']:9} [{ch['first_frame']}, {ch['end_frame']}) {ch['frames']:5} frames; transition included {ch['included_transition_frames']}", flush=True)
    if args.prepare:
        print(f'Prepared {out / "render-plan.json"}; no rendering started.')
        return 0
    if not shot.exists():
        fail(f'Master shot is not ready: {shot}')
    selected = {item for value in (args.chapter or []) for item in value.split(',') if item}
    unknown = selected - {ch['id'] for ch in plan['chapters']}
    if unknown:
        fail('Unknown chapter IDs: ' + ', '.join(sorted(unknown)))
    if selected and args.mux_only:
        parser.error('--chapter and --mux-only cannot be combined.')
    # Inspect is cheap and always runs, including on resume, to catch wrong stage
    # dimensions or a master still bound to the estimated timeline.
    inspection = run_logged([str(cli), 'inspect', str(shot), '--root', str(ROOT), '--fps', str(FPS), '--json'], logs / 'inspect.jsonl', events=True)['data']
    if (inspection['frames'], inspection['fps'], inspection['stage']['width'], inspection['stage']['height']) != (plan['frames'], FPS, WIDTH, HEIGHT):
        fail('Multiplane inspect does not match the actual timeline frame count, fps, or stage dimensions.')
    verify_receipt = out / 'verify-receipt.json'
    verified = args.resume and verify_receipt.exists() and read_json(verify_receipt).get('fingerprint') == fingerprint
    if not verified or args.verify_only:
        # All values originate in integer frame indices; zero, midpoint and final
        # frame of every chapter sample motion and chapter/transition boundaries.
        verify_frames = sorted({f for ch in plan['chapters'] for f in (ch['first_frame'], (ch['first_frame'] + ch['end_frame']) // 2, ch['end_frame'] - 1)})
        print(f'Verifying entire shot at {len(verify_frames)} frame-aligned times…', flush=True)
        result = run_logged([str(cli), 'verify', str(shot), *common, *visual,
                             '--at', ','.join(seconds(f) for f in verify_frames)], logs / 'verify.jsonl', events=True)
        write_json(verify_receipt, {'complete': True, 'fingerprint': fingerprint, 'frames_checked': verify_frames, 'result': result})
    else:
        print('Reusing whole-shot determinism verification for unchanged picture inputs.', flush=True)
    if args.verify_only:
        print('Whole-shot inspection and determinism verification passed; nothing rendered.')
        return 0
    if not selected:
        mix_info = validate_mix(audio, plan['duration'])
    for ch in plan['chapters']:
        if selected and ch['id'] not in selected:
            continue
        path = chapters_dir / ch['filename']
        receipt = path.with_suffix('.receipt.json')
        chapter_fingerprint = hashlib.sha256(f"{fingerprint}:{ch['first_frame']}:{ch['end_frame']}".encode()).hexdigest()
        if (args.resume or args.mux_only) and receipt_valid(receipt, path, chapter_fingerprint, ch['frames']):
            print(f"Reuse {ch['id']}: verified file and source hashes match.", flush=True)
            continue
        if args.mux_only:
            fail(f"Missing, changed, or invalid chapter receipt: {ch['id']}. Run --resume to render it.")
        print(f"Rendering {ch['id']}: frames [{ch['first_frame']}, {ch['end_frame']})…", flush=True)
        result = run_logged(ch['command'], logs / f"render-{ch['id']}.jsonl", events=True)
        data = result['data']
        if (data.get('frames'), data.get('width'), data.get('height'), data.get('fps')) != (ch['frames'], WIDTH, HEIGHT, FPS):
            fail(f"{ch['id']}: Multiplane result does not match the requested chapter range.")
        if data.get('draft'):
            fail('A draft render cannot be used as a final chapter.')
        probe = decode_probe(ffmpeg, path, logs / f"decode-{ch['id']}.log", ch['frames'])
        write_json(receipt, {'complete': True, 'fingerprint': chapter_fingerprint,
                            'file_sha256': sha256(path), 'frames': ch['frames'],
                            'first_frame': ch['first_frame'], 'end_frame': ch['end_frame'],
                            'probe': probe, 'multiplane_result': result})
        print(f"Verified {ch['id']}: {ch['frames']} decoded frames, H.264/yuv420p.", flush=True)
    if selected:
        print('Selected chapters finished. Run --resume without --chapter to finish and package the full film.')
        return 0
    # Revalidate every receipt before concatenation; a concurrent edit may not
    # silently put an old chapter into a new master.
    if source_fingerprint(timeline, shot, options)[0] != fingerprint:
        fail('Picture inputs changed while rendering. Rerun --resume after edits finish.')
    concat = out / 'chapters.ffconcat'
    lines = ['ffconcat version 1.0']
    for ch in plan['chapters']:
        path = chapters_dir / ch['filename']
        chapter_fingerprint = hashlib.sha256(f"{fingerprint}:{ch['first_frame']}:{ch['end_frame']}".encode()).hexdigest()
        if not receipt_valid(path.with_suffix('.receipt.json'), path, chapter_fingerprint, ch['frames']):
            fail(f"Chapter failed final receipt validation: {ch['id']}")
        # Controlled generated names, relative to the concat list; no shell quoting.
        lines.append(f"file chapters/{ch['filename']}")
        lines.append(f"duration {seconds(ch['frames'])}")
    concat.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    silent, silent_tmp = out / 'master-landscape-silent.mp4', out / 'master-landscape-silent.partial.mp4'
    run_logged([ffmpeg, '-hide_banner', '-nostdin', '-y', '-f', 'concat', '-safe', '1', '-i', str(concat),
                '-map', '0:v:0', '-an', '-c:v', 'copy', '-movflags', '+faststart', str(silent_tmp)], logs / 'concat.log')
    silent_probe = decode_probe(ffmpeg, silent_tmp, logs / 'decode-concat.log', plan['frames'])
    silent_tmp.replace(silent)
    # Explicit sample-exact trim/pad, never -shortest: the movie's final frame is
    # governed by the picture timeline rather than AAC packet rounding.
    master, master_tmp = out / 'master-landscape.mp4', out / 'master-landscape.partial.mp4'
    target_samples = plan['frames'] * 1600  # 48000 / 30 is exactly integral.
    run_logged([ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', str(silent), '-i', str(audio),
                '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k',
                '-ar', '48000', '-ac', '2', '-af', f'apad=whole_len={target_samples},atrim=end_sample={target_samples},asetpts=PTS-STARTPTS',
                '-movflags', '+faststart', '-metadata', 'title=压力上来，先让身体缓一缓',
                '-metadata', 'comment=Multiplane longform; frame-exact chapter assembly', str(master_tmp)], logs / 'mux.log')
    master_probe = decode_probe(ffmpeg, master_tmp, logs / 'decode-master.log', plan['frames'], audio=True)
    master_tmp.replace(master)
    delivery = None
    if args.delivery_1080:
        delivery, delivery_tmp = out / 'master-landscape-1080p.mp4', out / 'master-landscape-1080p.partial.mp4'
        run_logged([ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', str(master), '-map', '0:v:0', '-map', '0:a:0',
                    '-vf', 'scale=1920:1080:flags=lanczos', '-c:v', 'libx264', '-profile:v', 'high',
                    '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-c:a', 'copy',
                    '-movflags', '+faststart', str(delivery_tmp)], logs / 'delivery-1080.log')
        decode_probe(ffmpeg, delivery_tmp, logs / 'decode-delivery-1080.log', plan['frames'], 1920, 1080, audio=True)
        delivery_tmp.replace(delivery)
    report = {'complete': True, 'fingerprint': fingerprint, 'master': str(master), 'master_sha256': sha256(master),
              'frames': plan['frames'], 'duration': plan['duration'], 'picture': master_probe,
              'silent_picture': silent_probe, 'audio': {**mix_info, 'file': str(audio), 'sha256': sha256(audio), 'aac_bitrate': 320000},
              'delivery_1080': str(delivery) if delivery else None,
              'chapter_count': len(plan['chapters']), 'workers': args.workers}
    write_json(out / 'master-report.json', report)
    print(f"Complete: {master}\n{plan['frames']} frames / {plan['duration']:.3f}s / {WIDTH}x{HEIGHT} @ {FPS} fps / AAC 320 kbps", flush=True)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, ValueError, KeyError, wave.Error) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        raise SystemExit(1)
