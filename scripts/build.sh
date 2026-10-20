#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .tool-env
mkdir -p output
python scripts/export_content.py
python scripts/synth_audio.py --timeline content/timeline.json
if [[ "${1:-}" == "--scratch-voice" ]]; then
  python scripts/temp_voice.py
  mix="assets/audio/temp-narrated-mix.wav"
else
  mix="assets/audio/narrated-mix.wav"
fi
python - <<'CHECK'
import json
from pathlib import Path
x=json.loads(Path('content/timeline.json').read_text())
missing=[s['audio'] for s in x['segments'] if not Path(s['audio']).is_file()]
if missing:raise SystemExit('Missing narration files: '+', '.join(missing))
CHECK
python scripts/mix_audio.py --timeline content/timeline.json --output "$mix" --report output/mix-report.json
for format in landscape portrait; do
  npx multiplane lint "shots/$format.html" --json
  npx multiplane verify "shots/$format.html" --at 2,5,8.7,18,28,43,61.6 --workers 2 --json > "output/verify-$format.log"
  bash scripts/render.sh "$format" > "output/render-$format.log"
  python scripts/package_video.py --format "$format" --audio "$mix"
  npx multiplane stills "shots/cover-$format.html" --at 0 --motion-blur 1 --out "output/cover-$format" --overwrite --json > "output/cover-$format.log"
  cp "output/cover-$format/t-0.00.png" "output/cover-$format.png"
done
cp scripts/review-template.html output/review.html
