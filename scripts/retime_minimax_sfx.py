#!/usr/bin/env python3
"""Retime only unpitched paper texture for the reviewed MiniMax v2 animation.

No voice or musical pitch is processed. The existing paper-noise window is
compressed onto the v2 squeeze action; all samples outside old/new paper windows
are retained exactly. Abstract breath air already falls within the long exhale.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from mix_audio import decode, get_ffmpeg
from synth_audio import SR, write_wav, stats

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=ROOT / 'assets/audio/sfx.wav')
    p.add_argument('--output', type=Path, default=ROOT / 'assets/audio/minimax-sfx.wav')
    p.add_argument('--sync', type=Path, default=ROOT / 'output/minimax/sync-report.json')
    p.add_argument('--timeline', type=Path, default=ROOT / 'content/timeline-minimax.json')
    p.add_argument('--report', type=Path, default=ROOT / 'output/minimax/sfx-sync-report.json')
    args = p.parse_args()
    if args.source.resolve() == args.output.resolve():
        p.error('Output must differ from the original SFX stem')
    sync = json.loads(args.sync.read_text())
    timeline = json.loads(args.timeline.read_text())
    stations = {x['id']: x for x in timeline['stations']}
    paper = sync['render_config']['retime']['paper']
    def new_time(old_time):
        match = [pair[0] for pair in paper if abs(pair[1] - old_time) < 1e-6]
        if len(match) != 1:
            raise ValueError(f'Expected one reviewed mapping for paper phase {old_time}')
        return stations['paper']['start'] + match[0]
    source_start = stations['paper']['start'] + 3.0
    # synth_audio emits nine tapered noise bursts with .11-second spacing,
    # <=.04-second jitter and <=.13-second duration: all fit in 1.05 seconds.
    source_end = source_start + 1.05
    target_start, target_end = new_time(.45), new_time(2.55)
    source_hash = digest(args.source)
    ffmpeg = get_ffmpeg(None)
    original = decode(args.source, ffmpeg)
    output = original.copy()
    a, b = round(source_start * SR), round(source_end * SR)
    c, d = round(target_start * SR), round(target_end * SR)
    if not 0 <= min(a, c) < max(b, d) <= len(original) or d <= c:
        raise ValueError('Invalid paper retiming bounds')
    texture = original[a:b].copy()
    # This is unpitched filtered paper noise, so time resampling is appropriate.
    # Its original spectrum is below 3 kHz, safely below Nyquist after compression.
    positions = np.linspace(0, len(texture) - 1, d - c)
    retimed = np.column_stack([np.interp(positions, np.arange(len(texture)), texture[:, ch])
                              for ch in range(2)])
    output[a:b] = 0
    output[c:d] += retimed
    write_wav(args.output, output)
    stored = decode(args.output, ffmpeg)
    mask = np.ones(len(original), dtype=bool)
    mask[a:b] = False
    mask[c:d] = False
    outside_difference = float(np.max(np.abs(original[mask] - stored[mask])))
    if outside_difference > 2 ** -23:
        raise RuntimeError('Unexpected change outside paper windows')
    if digest(args.source) != source_hash:
        raise RuntimeError('Source SFX changed during retiming')
    report = {'source': str(args.source.relative_to(ROOT)), 'source_sha256': source_hash,
              'source_unchanged': True, 'output': str(args.output.relative_to(ROOT)),
              'output_sha256': digest(args.output), 'duration_seconds': len(output) / SR,
              'sample_rate': SR, 'channels': 2, 'bit_depth': 24,
              'paper_source_window': [source_start, source_end],
              'paper_destination_window': [target_start, target_end],
              'method': 'Retime unpitched paper-noise samples only; do not normalize the whole stem',
              'outside_edited_windows_max_absolute_difference': outside_difference,
              'breath_air_unchanged_window': [10.8, 13.6],
              'reviewed_long_exhale_window': [8.5, 15.0],
              'paper_landing_sound': 'No separate landing sound exists; none added',
              'generic_transitions': 'Unchanged', 'output_signal': stats(stored)}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
