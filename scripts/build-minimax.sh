#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .tool-env
mkdir -p output/minimax
python scripts/import_minimax.py --require-complete
python scripts/sync_minimax.py
python scripts/synth_audio.py --timeline content/timeline.json
python scripts/retime_minimax_sfx.py
python scripts/mix_audio.py --timeline content/timeline-minimax.json \
  --sfx assets/audio/minimax-sfx.wav --output assets/audio/minimax-narrated-mix.wav \
  --no-voice-output assets/audio/minimax-background-mix.wav --report output/minimax/mix-report.json
for format in landscape portrait; do
  npx multiplane verify "shots/$format-minimax.html" --at 5,7,8.5,37,61.6 --workers 2 --json > "output/minimax/verify-$format-final.log"
  npx multiplane render "shots/$format-minimax.html" --workers 2 --out "output/$format-minimax-silent.mp4" --overwrite --json > "output/minimax/render-$format.log"
  python scripts/package_video.py --format "$format" --video "output/$format-minimax-silent.mp4" \
    --audio assets/audio/minimax-narrated-mix.wav --name "review-$format-minimax-v2.mp4" \
    --voice-label 'MiniMax Audio / speech-2.8-hd / 温暖闺蜜' > "output/minimax/package-$format.json"
done
cp scripts/review-minimax-template.html output/review-minimax.html
cp scripts/review-minimax-template.html output/review.html
