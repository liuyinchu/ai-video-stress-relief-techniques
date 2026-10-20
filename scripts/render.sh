#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .tool-env
format="${1:-landscape}"
quality="${2:-final}"
case "$format" in landscape|portrait) ;; *) echo "format must be landscape or portrait"; exit 2;; esac
mkdir -p output
if [[ "$quality" == "draft" ]]; then
  npx multiplane render "shots/$format.html" --workers 2 --draft --fps 15 --out "output/${format}-draft-silent.mp4" --overwrite --json
else
  npx multiplane render "shots/$format.html" --workers 2 --out "output/${format}-silent.mp4" --overwrite --json
fi
