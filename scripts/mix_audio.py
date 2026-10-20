#!/usr/bin/env python3
"""Place narration, gently duck score, and mix to -16 LUFS / -1.5 dBTP.

Single narration: --voice assets/audio/voice.wav
Segmented narration: --timeline content/timeline.json, with segments containing
{id, start, audio}, or --voice-dir containing files named after segment ids.
Use --segments for a standalone [{start, path}] manifest. MP3, AAC, AIFF and WAV
are decoded through FFmpeg. A quiet -24 LUFS music/SFX mix is always retained.
No speech is synthesized or attributed to any TTS provider by this script.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import numpy as np
from synth_audio import SR, write_wav, stats


def get_ffmpeg(explicit: str | None) -> str:
    if explicit:
        return explicit
    if os.environ.get("FFMPEG_BINARY"):
        return os.environ["FFMPEG_BINARY"]
    installed = shutil.which("ffmpeg")
    if installed:
        return installed
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as exc:
        raise SystemExit("FFmpeg missing: pass --ffmpeg PATH or install imageio-ffmpeg") from exc


def decode(path: Path, ffmpeg: str) -> np.ndarray:
    if not path.is_file():
        raise SystemExit(f"Audio file does not exist: {path}")
    result = subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(path),
                             "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                            capture_output=True)
    if result.returncode:
        raise SystemExit(result.stderr.decode(errors="replace"))
    return np.frombuffer(result.stdout, dtype="<f4").reshape(-1, 2).astype(np.float64)


def resized(audio: np.ndarray, duration: float) -> np.ndarray:
    size = round(duration * SR)
    result = np.zeros((size, 2), dtype=np.float64)
    result[:min(size, len(audio))] = audio[:size]
    return result


def resolve_path(value: str, manifest: Path | None) -> Path:
    source = Path(value).expanduser()
    if source.is_absolute() or source.is_file():
        return source
    if manifest:
        for root in [manifest.parent, manifest.parent.parent]:
            candidate = root / source
            if candidate.is_file():
                return candidate
    return source


def get_segments(timeline: dict | list, manifest: Path | None,
                 voice_dir: Path | None) -> list[dict]:
    items = timeline if isinstance(timeline, list) else timeline.get("segments", [])
    found = []
    for item in items:
        value = item.get("audio", item.get("voice_file", item.get("narration_audio", item.get("path"))))
        if isinstance(value, dict):
            value = value.get("path", value.get("file"))
        if not value and voice_dir:
            ident = str(item.get("id", ""))
            matches = [voice_dir / f"{ident}{ext}" for ext in [".wav", ".mp3", ".m4a", ".aac", ".aiff"]]
            value = next((str(p) for p in matches if p.is_file()), None)
            if not value:
                raise SystemExit(f"Missing narration file for segment {ident!r} in {voice_dir}")
        if value:
            start = float(item.get("voice_start", item.get("start", 0)))
            found.append({"id": item.get("id", Path(value).stem), "start": start,
                          "path": resolve_path(value, manifest), "end": item.get("end")})
    return found


def prepare_voice(args, ffmpeg: str, duration: float, timeline: dict | list) -> tuple[np.ndarray, list]:
    voice = np.zeros((round(duration * SR), 2), dtype=np.float64)
    if args.voice:
        segments = [{"id": "narration", "start": args.voice_start, "path": args.voice, "end": None}]
    else:
        data = timeline
        manifest = args.timeline
        if args.segments:
            data = json.loads(args.segments.read_text())
            manifest = args.segments
        segments = get_segments(data, manifest, args.voice_dir)
    report = []
    for seg in segments:
        decoded = decode(seg["path"], ffmpeg)
        start = round(seg["start"] * SR)
        if start < 0:
            raise SystemExit(f"Negative start for narration {seg['id']}")
        actual_end = (start + len(decoded)) / SR
        # A few codec-padding samples may exceed the requested endpoint. Speech may not.
        if start + len(decoded) > len(voice) + round(.05 * SR):
            raise SystemExit(f"Narration {seg['id']} ends at {actual_end:.3f}s, after duration {duration}s")
        length = min(len(decoded), len(voice) - start)
        if length > 0:
            voice[start:start + length] += decoded[:length]
        item = {"id": seg["id"], "path": str(seg["path"]), "start": seg["start"],
                "duration": round(len(decoded) / SR, 3), "end": round(actual_end, 3)}
        if seg["end"] is not None and actual_end > float(seg["end"]) + .1:
            item["warning"] = "Audio extends past visual segment; inspect narration timing."
        report.append(item)
    if segments and np.max(np.abs(voice)) < 1e-7:
        raise SystemExit("The supplied narration is silent")
    if np.any(voice):
        # Normalize active speech, not the silence between narration segments.
        block = 960
        padded = np.pad(voice, ((0, (-len(voice)) % block), (0, 0)))
        rms = np.sqrt(np.mean(padded.reshape(-1, block, 2) ** 2, axis=(1, 2)))
        active = rms[rms > max(.003, float(np.max(rms)) * .045)]
        active_rms = np.sqrt(np.mean(active ** 2)) if len(active) else 1
        gain = min(10 ** (-20 / 20) / active_rms,
                   10 ** (-3 / 20) / np.max(np.abs(voice)))
        voice *= gain
    return voice, report


def duck_envelope(voice: np.ndarray, minimum_gain: float = .33) -> np.ndarray:
    # 20 ms RMS, 60 ms attack, 450 ms release. The envelope is interpolated to
    # samples, so voice entrances never pump or zipper the background score.
    block = 960
    padded = np.pad(voice, ((0, (-len(voice)) % block), (0, 0)))
    rms = np.sqrt(np.mean(padded.reshape(-1, block, 2) ** 2, axis=(1, 2)))
    activity = np.clip((rms - .004) / .018, 0, 1)
    activity = np.maximum(activity, np.roll(activity, -1))  # one block lookahead
    desired = 1 - activity * (1 - minimum_gain)
    smoothed = np.ones(len(desired))
    current = 1.0
    for i, target in enumerate(desired):
        tau = .06 if target < current else .45
        coefficient = np.exp(-.02 / tau)
        current = coefficient * current + (1 - coefficient) * target
        smoothed[i] = current
    centers = np.arange(len(smoothed)) * block + block / 2
    return np.interp(np.arange(len(voice)), centers, smoothed, left=smoothed[0], right=smoothed[-1])


def parse_loudness(stderr: str) -> dict:
    candidates = re.findall(r"\{\s*\"input_i\".*?\}", stderr, flags=re.S)
    if not candidates:
        raise RuntimeError(f"FFmpeg did not return loudnorm statistics: {stderr[-2000:]}")
    return json.loads(candidates[-1])


def loudnorm(source: Path, output: Path, ffmpeg: str, target: float,
             duration: float) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    first_filter = f"loudnorm=I={target}:TP=-1.5:LRA=7:print_format=json"
    first = subprocess.run([ffmpeg, "-hide_banner", "-nostdin", "-i", str(source),
                            "-af", first_filter, "-f", "null", "-"], capture_output=True, text=True)
    if first.returncode:
        raise RuntimeError(first.stderr)
    measured = parse_loudness(first.stderr)
    if measured["input_i"] in ["-inf", "inf"]:
        raise RuntimeError("Cannot normalize an empty or silent mix")
    second_filter = (f"loudnorm=I={target}:TP=-1.5:LRA=7:"
                     f"measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
                     f"measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:"
                     f"offset={measured['target_offset']}:linear=true:print_format=json")
    second = subprocess.run([ffmpeg, "-y", "-hide_banner", "-nostdin", "-i", str(source),
                             "-af", second_filter, "-ar", str(SR), "-ac", "2", "-t", str(duration),
                             "-c:a", "pcm_s24le", str(output)], capture_output=True, text=True)
    if second.returncode:
        raise RuntimeError(second.stderr)
    return parse_loudness(second.stderr)


def safe_write(path: Path, audio: np.ndarray) -> None:
    peak = np.max(np.abs(audio))
    if peak > .95:
        audio = audio * (.95 / peak)
    write_wav(path, audio)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=62.0)
    parser.add_argument("--timeline", type=Path)
    parser.add_argument("--music", type=Path, default=Path("assets/audio/music.wav"))
    parser.add_argument("--sfx", type=Path, default=Path("assets/audio/sfx.wav"))
    parser.add_argument("--voice", type=Path)
    parser.add_argument("--voice-start", type=float, default=0)
    parser.add_argument("--voice-dir", type=Path)
    parser.add_argument("--segments", type=Path)
    parser.add_argument("--music-gain", type=float, default=1.0)
    parser.add_argument("--sfx-gain", type=float, default=1.0)
    parser.add_argument("--output", type=Path, default=Path("assets/audio/final_mix.wav"))
    parser.add_argument("--no-voice-output", type=Path, default=Path("assets/audio/music_sfx_mix.wav"))
    parser.add_argument("--report", type=Path)
    parser.add_argument("--ffmpeg")
    args = parser.parse_args()
    if args.voice and (args.voice_dir or args.segments):
        parser.error("Use either --voice or segmented narration, not both")
    timeline = json.loads(args.timeline.read_text()) if args.timeline else {}
    duration = float(timeline.get("duration", args.duration)) if isinstance(timeline, dict) else args.duration
    if duration <= 0 or duration > 3600:
        parser.error("Duration must be between 0 and 3600 seconds")
    ffmpeg = get_ffmpeg(args.ffmpeg)
    music = resized(decode(args.music, ffmpeg), duration) * args.music_gain
    sfx = resized(decode(args.sfx, ffmpeg), duration) * args.sfx_gain
    voice, narration = prepare_voice(args, ffmpeg, duration, timeline)
    has_voice = bool(narration)
    duck = duck_envelope(voice)
    mix = voice + music * duck[:, None] + sfx * (.7 + .3 * duck[:, None])
    with tempfile.TemporaryDirectory(prefix="shortvideo-mix-") as temp:
        temp = Path(temp)
        safe_write(temp / "background.wav", music + sfx)
        bg_stats = loudnorm(temp / "background.wav", args.no_voice_output, ffmpeg, -24, duration)
        if has_voice:
            safe_write(temp / "mix.wav", mix)
            final_stats = loudnorm(temp / "mix.wav", args.output, ffmpeg, -16, duration)
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            if args.output.resolve() != args.no_voice_output.resolve():
                shutil.copyfile(args.no_voice_output, args.output)
            final_stats = bg_stats
    report = {"duration": duration, "sample_rate": SR, "channels": 2,
              "has_narration": has_voice, "narration": narration,
              "target_lufs": -16 if has_voice else -24, "target_true_peak_db": -1.5,
              "ducking_min_gain_db": round(20 * np.log10(max(np.min(duck), 1e-9)), 2),
              "final_mix": {"path": str(args.output), "loudnorm": final_stats},
              "background_mix": {"path": str(args.no_voice_output), "loudnorm": bg_stats},
              "voice_before_mix": stats(voice)}
    report_text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report_text + "\n")
    print(report_text)


if __name__ == "__main__":
    main()
