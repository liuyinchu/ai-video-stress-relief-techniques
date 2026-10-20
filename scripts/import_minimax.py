#!/usr/bin/env python3
"""Import actual MiniMax downloads without modifying originals or picture timing.

The raw directory must contain one file per timeline id. Each available file is
fingerprinted, decoded and measured. Only conservative edge silence is trimmed;
internal pauses are preserved. Playback may accelerate by at most 10 percent to
fit the existing slot with a 100 ms tail margin. Short files are never stretched.
The MiniMax timeline is published atomically only after all nine inputs pass.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import wave
import numpy as np
from mix_audio import decode, get_ffmpeg
from synth_audio import SR

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".aiff", ".aif", ".flac"}


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pcm_metadata(path: Path, ffmpeg: str) -> dict:
    metadata = {"container_extension": path.suffix.lower(), "bytes": path.stat().st_size}
    if path.suffix.lower() == ".wav":
        try:
            with wave.open(str(path), "rb") as source:
                metadata.update({"codec": "pcm", "sample_rate": source.getframerate(),
                                 "channels": source.getnchannels(),
                                 "bit_depth": source.getsampwidth() * 8,
                                 "frames": source.getnframes(),
                                 "duration_seconds": source.getnframes() / source.getframerate()})
            return metadata
        except (wave.Error, EOFError):
            pass
    # imageio-ffmpeg bundles FFmpeg but not ffprobe. Preserve its actual stream
    # description for compressed inputs; all fitting uses decoded PCM durations.
    probe = subprocess.run([ffmpeg, "-hide_banner", "-nostdin", "-i", str(path)],
                           capture_output=True, text=True)
    stream = next((line.strip() for line in probe.stderr.splitlines() if "Audio:" in line), None)
    metadata["source_stream"] = stream
    if stream:
        codec = re.search(r"Audio:\s*([^, ]+)", stream)
        rate = re.search(r"(\d+) Hz", stream)
        if codec:
            metadata["codec"] = codec.group(1)
        if rate:
            metadata["sample_rate"] = int(rate.group(1))
        if ", mono," in stream:
            metadata["channels"] = 1
        elif ", stereo," in stream:
            metadata["channels"] = 2
    return metadata


def signal_stats(audio: np.ndarray) -> dict:
    peak = float(np.max(np.abs(audio))) if len(audio) else 0
    rms = float(np.sqrt(np.mean(audio ** 2))) if len(audio) else 0
    return {"peak_dbfs": round(20 * math.log10(max(peak, 1e-12)), 3),
            "rms_dbfs": round(20 * math.log10(max(rms, 1e-12)), 3),
            "clipped_samples": int(np.count_nonzero(np.abs(audio) >= .999999)),
            "nonfinite_samples": int(np.count_nonzero(~np.isfinite(audio)))}


def conservative_edges(audio: np.ndarray) -> dict:
    """Use a low threshold plus generous guards to protect consonants and tails.

    Activity is detected in 5 ms blocks. Either RMS above -65 dBFS or any peak
    above -55 dBFS protects that block. Even quieter recordings use a lower
    relative threshold. Keep 120 ms before first activity and 180 ms after last.
    Do not remove an edge unless the removable duration is at least 80 ms.
    """
    block = 240
    count = len(audio)
    padded = np.pad(audio, ((0, (-count) % block), (0, 0)))
    grouped = padded.reshape(-1, block, 2)
    rms = np.sqrt(np.mean(grouped ** 2, axis=(1, 2)))
    peaks = np.max(np.abs(grouped), axis=(1, 2))
    peak = float(np.max(peaks))
    rms_threshold = min(10 ** (-65 / 20), peak * 10 ** (-40 / 20))
    peak_threshold = min(10 ** (-55 / 20), peak * 10 ** (-30 / 20))
    active = np.flatnonzero((rms > rms_threshold) | (peaks > peak_threshold))
    if len(active) == 0 or peak < 10 ** (-75 / 20):
        raise ValueError("Source is silent or below usable level")
    first = int(active[0]) * block
    last = min(count, (int(active[-1]) + 1) * block)
    head = max(0, first - round(.120 * SR))
    end = min(count, last + round(.180 * SR))
    if head < round(.080 * SR):
        head = 0
    if count - end < round(.080 * SR):
        end = count
    return {"head_trim_seconds": head / SR,
            "tail_trim_seconds": (count - end) / SR,
            "trim_start_seconds": head / SR, "trim_end_seconds": end / SR,
            "duration_after_trim_seconds": (end - head) / SR,
            "first_detected_activity_seconds": first / SR,
            "last_detected_activity_seconds": last / SR,
            "rms_activity_threshold_dbfs": round(20 * math.log10(rms_threshold), 3),
            "peak_activity_threshold_dbfs": round(20 * math.log10(peak_threshold), 3),
            "head_guard_seconds": .120, "tail_guard_seconds": .180,
            "minimum_edge_removal_seconds": .080,
            "internal_pauses_preserved": True}


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temp.replace(path)


def fit_file(source: Path, output: Path, info: dict, ffmpeg: str,
             target: float, slot: float, max_tempo: float) -> dict:
    trimmed = info["duration_after_trim_seconds"]
    tempo = max(1.0, trimmed / target)
    if tempo > max_tempo + 1e-9:
        return {"status": "needs_regeneration", "reason": "Required speed exceeds permitted 10 percent acceleration",
                "required_atempo": round(tempo, 7),
                "over_slot_percent": round(max(0, trimmed / slot - 1) * 100, 3)}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="minimax-import-") as work:
        temp = Path(work) / "fitted.wav"
        for attempt in range(3):
            filters = [f"atrim=start={info['trim_start_seconds']:.9f}:end={info['trim_end_seconds']:.9f}",
                       "asetpts=PTS-STARTPTS"]
            if tempo > 1.0000001:
                filters.append(f"atempo={tempo:.9f}")
            command = [ffmpeg, "-y", "-hide_banner", "-nostdin", "-loglevel", "error",
                       "-i", str(source), "-af", ",".join(filters),
                       "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s24le", str(temp)]
            run = subprocess.run(command, capture_output=True, text=True)
            if run.returncode:
                raise RuntimeError(run.stderr.strip())
            fitted = decode(temp, ffmpeg)
            actual = len(fitted) / SR
            # atempo duration can differ slightly due to its analysis window.
            # Correct the factor rather than truncating a word to force a fit.
            if actual <= target + .005:
                break
            tempo *= actual / target * 1.002
            if tempo > max_tempo:
                return {"status": "needs_regeneration", "reason": "Exact output fit would require speed above 1.10",
                        "required_atempo": round(tempo, 7)}
        if actual > target + .005 or actual > slot:
            return {"status": "needs_regeneration", "reason": "Output still exceeds reserved slot",
                    "actual_duration_seconds": actual, "attempted_atempo": round(tempo, 7)}
        # A same-directory temporary replacement prevents the mixer from seeing
        # a partially copied output. Original download is never opened for write.
        staging = output.with_suffix(".wav.tmp")
        staging.write_bytes(temp.read_bytes())
        staging.replace(output)
    return {"status": "ready", "path": relative(output), "sha256": sha256(output),
            "pcm": pcm_metadata(output, ffmpeg), "signal": signal_stats(fitted),
            "duration_seconds": actual, "atempo": round(tempo, 9),
            "accelerated": tempo > 1.0000001, "stretched_to_fill": False,
            "remaining_slot_seconds": round(slot - actual, 6)}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--timeline", type=Path, default=ROOT / "content/timeline.json")
    p.add_argument("--raw-dir", type=Path, default=ROOT / "assets/audio/minimax/raw")
    p.add_argument("--fitted-dir", type=Path, default=ROOT / "assets/audio/minimax/fitted")
    p.add_argument("--output-timeline", type=Path, default=ROOT / "content/timeline-minimax.json")
    p.add_argument("--report", type=Path, default=ROOT / "output/minimax/import-report.json")
    p.add_argument("--only", nargs="+", help="Process only specified ids while reporting the inventory of all nine")
    p.add_argument("--require-complete", action="store_true")
    p.add_argument("--tail-margin", type=float, default=.1)
    p.add_argument("--max-tempo", type=float, default=1.10)
    p.add_argument("--ffmpeg")
    args = p.parse_args()
    if not 1 <= args.max_tempo <= 1.10:
        p.error("--max-tempo must be in [1, 1.10]")
    if not 0 <= args.tail_margin <= .3:
        p.error("--tail-margin must be in [0, 0.3]")
    timeline = json.loads(args.timeline.read_text())
    ids = {item["id"] for item in timeline["segments"]}
    if args.only and set(args.only) - ids:
        p.error("Unknown id: " + ", ".join(sorted(set(args.only) - ids)))
    ffmpeg = get_ffmpeg(args.ffmpeg)
    report = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "source": {"provider": "MiniMax Audio", "model": "speech-2.8-hd", "voice_label": "温暖闺蜜",
                         "web_settings": {"speed": 1, "pitch": 0, "volume": 1},
                         "provenance": "Downloaded via user-authorized Chrome UI by main production thread"},
              "policy": {"max_atempo": args.max_tempo, "tail_margin_seconds": args.tail_margin,
                         "preserve_raw": True, "preserve_internal_pauses": True, "stretch_short_segments": False},
              "segments": [], "complete": False, "timeline_published": False}
    for seg in timeline["segments"]:
        ident = seg["id"]
        slot = float(seg["end"]) - float(seg["start"])
        target = slot - args.tail_margin
        item = {"id": ident, "start": seg["start"], "end": seg["end"],
                "maximum_duration_seconds": round(slot, 6), "target_duration_seconds": round(target, 6)}
        candidates = sorted(path for path in args.raw_dir.glob(f"{ident}.*")
                            if path.is_file() and path.suffix.lower() in EXTENSIONS)
        if not candidates:
            item["status"] = "missing"
        elif len(candidates) != 1:
            item.update({"status": "ambiguous", "paths": [relative(path) for path in candidates]})
        elif args.only and ident not in args.only:
            item.update({"status": "present_not_processed", "path": relative(candidates[0])})
        else:
            source = candidates[0]
            before_sha = sha256(source)
            try:
                audio = decode(source, ffmpeg)
                signal = signal_stats(audio)
                if signal["nonfinite_samples"]:
                    raise ValueError("Source contains NaN or infinite PCM samples")
                item["raw"] = {"path": relative(source), "sha256": before_sha,
                               "pcm": pcm_metadata(source, ffmpeg),
                               "decoded_duration_seconds": len(audio) / SR,
                               "analysis_pcm": {"sample_rate": SR, "channels": 2, "format": "float64"},
                               "signal": signal}
                edges = conservative_edges(audio)
                item["edges"] = edges
                fitted = fit_file(source, args.fitted_dir / f"{ident}.wav", edges,
                                  ffmpeg, target, slot, args.max_tempo)
                item["status"] = fitted["status"]
                item["fitted"] = fitted
                item["raw_unchanged"] = before_sha == sha256(source)
                if not item["raw_unchanged"]:
                    item["status"] = "source_changed_during_import"
            except Exception as exc:
                item.update({"status": "error", "error": str(exc)})
        report["segments"].append(item)
    report["complete"] = all(item["status"] == "ready" for item in report["segments"])
    report["ready_count"] = sum(item["status"] == "ready" for item in report["segments"])
    report["expected_count"] = len(timeline["segments"])
    report["needs_web_regeneration"] = [item["id"] for item in report["segments"]
                                         if item["status"] == "needs_regeneration"]
    if report["complete"]:
        by_id = {item["id"]: item for item in report["segments"]}
        for seg in timeline["segments"]:
            seg["audio"] = by_id[seg["id"]]["fitted"]["path"]
        timeline["voice"] = {**timeline.get("voice", {}), **report["source"],
                             "import_report": relative(args.report), "import_complete": True}
        atomic_json(args.output_timeline, timeline)
        report["timeline_published"] = True
        report["timeline_path"] = relative(args.output_timeline)
    elif args.output_timeline.exists():
        report["warning"] = "An older MiniMax timeline exists; it was not updated by this incomplete import. Do not mix until complete."
    atomic_json(args.report, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    selected = [item for item in report["segments"] if not args.only or item["id"] in args.only]
    failures = [item for item in selected if item["status"] not in ["ready", "missing"]]
    return 2 if failures or (args.require_complete and not report["complete"]) else 0


if __name__ == "__main__":
    sys.exit(main())
