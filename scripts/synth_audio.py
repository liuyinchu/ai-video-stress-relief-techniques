#!/usr/bin/env python3
"""Deterministic original ambient score and quiet Foley, 48 kHz stereo.

No recordings, loops, or externally generated music are used. The two stems
are deliberately quiet and are intended to sit underneath spoken narration.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import wave
import numpy as np

SR = 48000
SEED = 1020
BPM = 78.0
CUES = {"intro": 0.0, "breath": 5.0, "cool": 17.0, "ear": 23.0,
        "shake": 28.0, "paper": 34.0, "nature": 42.0, "order": 49.0,
        "outro": 55.0}


def write_wav(path: Path, audio: np.ndarray) -> None:
    """24-bit PCM avoids throwing away resolution in these quiet stems."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.rint(np.clip(audio, -1, 1 - 2**-23) * (2**23 - 1)).astype(np.int32)
    packed = np.empty((pcm.size, 3), dtype=np.uint8)
    flat = pcm.reshape(-1)
    for byte in range(3):
        packed[:, byte] = (flat >> (8 * byte)) & 255
    with wave.open(str(path), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(3)
        f.setframerate(SR)
        f.writeframes(packed.tobytes())


def add(dst: np.ndarray, source: np.ndarray, start: float,
        gain: float = 1.0, pan: float = 0.0) -> None:
    offset = round(start * SR)
    trim = max(0, -offset)
    offset = max(0, offset)
    size = min(len(source) - trim, len(dst) - offset)
    if size <= 0:
        return
    source = source[trim:trim + size]
    if source.ndim == 1:
        angle = (np.clip(pan, -1, 1) + 1) * math.pi / 4
        dst[offset:offset + size, 0] += source * gain * math.cos(angle)
        dst[offset:offset + size, 1] += source * gain * math.sin(angle)
    else:
        dst[offset:offset + size] += source * gain


def soft_envelope(t: np.ndarray, duration: float,
                  attack: float = 1.5, release: float = 2.5) -> np.ndarray:
    a = np.sin(np.minimum(t / max(attack, .001), 1) * math.pi / 2) ** 2
    r = np.sin(np.minimum(np.maximum(duration - t, 0) / max(release, .001), 1) * math.pi / 2) ** 2
    return a * r


def midi(note: float) -> float:
    return 440 * 2 ** ((note - 69) / 12)


def pad(notes: list[int], duration: float, rng: np.random.Generator) -> np.ndarray:
    t = np.arange(round(duration * SR), dtype=np.float64) / SR
    result = np.zeros((len(t), 2), dtype=np.float64)
    env = soft_envelope(t, duration, attack=2.7, release=3.2)
    for index, note in enumerate(notes):
        freq = midi(note)
        phase = rng.uniform(0, 2 * math.pi)
        # A low-harmonic sine/tine body: no bright sawtooth energy under speech.
        drift = .006 * np.sin(2 * math.pi * (.07 + index * .011) * t)
        wave_a = np.sin(2 * math.pi * freq * t + phase + drift)
        wave_b = np.sin(2 * math.pi * freq * 1.00013 * t + phase + drift)
        harmonic = .055 * np.sin(4 * math.pi * freq * t + phase)
        gain = [.53, .35, .24, .18, .13][index]
        pan = [-.18, .22, -.5, .48, 0][index]
        result[:, 0] += gain * (wave_a + harmonic) * (1 - pan * .3)
        result[:, 1] += gain * (wave_b + harmonic) * (1 + pan * .3)
    return result * env[:, None] * .026


def wood(note: int, duration: float = 1.8) -> np.ndarray:
    t = np.arange(round(duration * SR)) / SR
    f = midi(note)
    # Inharmonic resonant modes with rounded attack, akin to felted wood.
    env = (1 - np.exp(-t / .004))
    x = (.78 * np.sin(2 * math.pi * f * t) * np.exp(-t / .29)
         + .18 * np.sin(2 * math.pi * f * 2.73 * t) * np.exp(-t / .065)
         + .035 * np.sin(2 * math.pi * f * 4.92 * t) * np.exp(-t / .025))
    return x * env


def filtered_noise(duration: float, rng: np.random.Generator,
                   low: float = 100, high: float = 1800) -> np.ndarray:
    n = round(duration * SR)
    # FFT filtering is offline and deterministic. Its result is tapered before use.
    noise = rng.standard_normal(n)
    spectrum = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(n, 1 / SR)
    filt = (1 - np.exp(-(freqs / low) ** 2)) * np.exp(-(freqs / high) ** 4)
    filtered = np.fft.irfft(spectrum * filt, n=n)
    filtered /= max(np.std(filtered), 1e-9)
    return filtered


def airy(duration: float, rng: np.random.Generator, high: float = 1400) -> np.ndarray:
    t = np.arange(round(duration * SR)) / SR
    env = np.sin(math.pi * t / duration) ** 2
    return filtered_noise(duration, rng, low=180, high=high) * env


def control_stem(audio: np.ndarray, rms_db: float, max_peak_db: float) -> np.ndarray:
    audio -= np.mean(audio, axis=0)
    rms = np.sqrt(np.mean(audio ** 2))
    peak = np.max(np.abs(audio))
    gain = min(10 ** (rms_db / 20) / max(rms, 1e-12),
               10 ** (max_peak_db / 20) / max(peak, 1e-12))
    audio *= gain
    # All stems land exactly at zero at both edges.
    fade = min(round(.025 * SR), len(audio) // 2)
    audio[:fade] *= np.linspace(0, 1, fade)[:, None]
    audio[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return audio


def score(duration: float, rng: np.random.Generator) -> np.ndarray:
    result = np.zeros((round(duration * SR), 2), dtype=np.float64)
    beat = 60 / BPM
    phrase = beat * 16
    chords = [
        [38, 57, 61, 64, 69],    # Dmaj9, spacious inversion
        [43, 54, 59, 62, 69],    # Gmaj9
        [47, 54, 57, 61, 66],    # Bm9
        [45, 52, 57, 59, 64],    # Asus2
        [38, 57, 62, 64, 66],    # Dadd9 home, open and unforced
    ]
    for i in range(math.ceil(duration / phrase)):
        start = i * phrase - 1.8
        add(result, pad(chords[i % len(chords)], phrase + 4.6, rng), start)
    # Opening only: gentle beating, resolving at two seconds, never a pulse/alarm.
    t = np.arange(round(2.7 * SR)) / SR
    tension = .0035 * (np.sin(2 * math.pi * 220 * t)
                      + np.sin(2 * math.pi * 222.2 * t))
    tension *= soft_envelope(t, 2.7, .2, 1.5)
    add(result, tension, 0)
    # A memorable four-note phrase, with enough empty air for the narrator.
    motif = [(2, 74, .022), (5.5, 69, .015), (10, 76, .019), (14, 73, .014)]
    for bar in range(math.ceil(duration / phrase)):
        for j, (pos, note, gain) in enumerate(motif):
            start = 3.5 + bar * phrase + pos * beat
            if start > duration - 4:
                continue
            note += [0, -2, -2, -5, 0][bar % 5]
            sound = wood(note)
            pan = [-.32, .25, -.12, .38][j]
            add(result, sound, start, gain, pan)
            add(result, sound, start + .31, gain * .12, -pan)
            add(result, sound, start + .61, gain * .045, pan)
    # A very restrained air floor softens the otherwise pure synthesis.
    air = filtered_noise(duration, rng, low=90, high=650)
    tt = np.arange(len(air)) / SR
    air *= .0007 * (.7 + .3 * np.sin(2 * math.pi * .04 * tt))
    add(result, air, 0)
    # Give the ending a real cadence and space for the closing sentence.
    tail_start = max(0, duration - 5.2)
    add(result, wood(74, 2.8), tail_start, .014, -.15)
    add(result, wood(81, 2.8), tail_start + .18, .006, .15)
    fade_in = min(round(.7 * SR), len(result))
    result[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
    fade_out = min(round(3.5 * SR), len(result))
    result[-fade_out:] *= (np.cos(np.linspace(0, math.pi / 2, fade_out)) ** 2)[:, None]
    return control_stem(result, rms_db=-30.0, max_peak_db=-17.0)


def effects(duration: float, cues: dict, rng: np.random.Generator) -> np.ndarray:
    result = np.zeros((round(duration * SR), 2), dtype=np.float64)
    # Soft transitions follow camera landings, not every word or animation.
    for key, length, gain, pan in [
        ("breath", .75, .007, -.16), ("cool", .65, .007, .15),
        ("ear", .45, .004, -.1), ("shake", .55, .005, .1),
        ("paper", .45, .005, -.15), ("nature", 1.1, .006, .22),
        ("order", .55, .005, -.12), ("outro", .9, .006, 0)]:
        add(result, airy(length, rng), cues[key] - length * .65, gain, pan)
    # Breath cue is abstract air, deliberately not a fake human inhalation.
    add(result, airy(2.8, rng, 700), cues["breath"] + 5.8, .0022, 0)
    # Cool cloth: a single muted glass-like sine/tine with no ice-crash effect.
    add(result, wood(81), cues["cool"] + .18, .011, .18)
    # Shoulder/hand motion: two tiny rustles.
    for offset, pan in [(1.1, -.2), (2.1, .2)]:
        add(result, airy(.32, rng, 950), cues["shake"] + offset, .0028, pan)
    # Tactile paper crumple, all synthesized filtered noise.
    paper_start = cues["paper"] + 3.0
    for i in range(9):
        length = float(rng.uniform(.045, .13))
        x = airy(length, rng, float(rng.uniform(1600, 2800)))
        add(result, x, paper_start + i * .11 + float(rng.uniform(0, .04)),
            float(rng.uniform(.002, .005)), float(rng.uniform(-.2, .2)))
    # Tidying clicks land sparsely, each one warmer and softer than the previous.
    for i in range(3):
        add(result, wood(62 + i * 2, .5), cues["order"] + .9 + i * .62,
            .009 - i * .0015, -.2 + i * .2)
    # Leave four seconds of clean ending, no UI "success" sound.
    return control_stem(result, rms_db=-42.0, max_peak_db=-23.0)


def stats(audio: np.ndarray) -> dict:
    return {"peak_dbfs": round(20 * np.log10(max(np.max(np.abs(audio)), 1e-12)), 2),
            "rms_dbfs": round(20 * np.log10(max(np.sqrt(np.mean(audio**2)), 1e-12)), 2)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=62.0)
    parser.add_argument("--out-dir", type=Path, default=Path("assets/audio"))
    parser.add_argument("--timeline", type=Path)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    duration = args.duration
    cues = dict(CUES)
    if args.timeline:
        timeline = json.loads(args.timeline.read_text())
        duration = float(timeline.get("duration", duration))
        for item in timeline.get("stations", timeline.get("segments", [])):
            key = item.get("audio_cue", item.get("id"))
            if key in cues and "start" in item:
                cues[key] = float(item["start"])
    if duration <= 0 or duration > 3600:
        raise SystemExit("Duration must be between 0 and 3600 seconds")
    rng = np.random.default_rng(args.seed)
    music = score(duration, rng)
    sfx = effects(duration, cues, rng)
    write_wav(args.out_dir / "music.wav", music)
    write_wav(args.out_dir / "sfx.wav", sfx)
    print(json.dumps({"duration": duration, "sample_rate": SR,
                      "channels": 2, "bit_depth": 24, "seed": args.seed,
                      "bpm": BPM, "music": stats(music), "sfx": stats(sfx)}, indent=2))


if __name__ == "__main__":
    main()
