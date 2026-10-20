#!/usr/bin/env bash
# Source this script from any working directory to use the project runtime.
TASK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="/opt/homebrew/opt/node@24/bin:${TASK_ROOT}/.tools/venv/bin:$PATH"
export MULTIPLANE_FFMPEG="$("${TASK_ROOT}/.tools/venv/bin/python" -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"
