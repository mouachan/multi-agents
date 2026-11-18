#!/usr/bin/env bash
# Demo video of the platform: recording (Playwright), voice-over (Kokoro TTS), montage (ffmpeg), all in podman.
# See README.md. Everything produced goes to scripts/demo-video/out/ (git-ignored).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
IMAGE="${DEMO_VIDEO_IMAGE:-localhost/multi-agents-demo-video:latest}"
OUT_DIR="${HERE}/out"
mkdir -p "${OUT_DIR}"

run() {
  podman run --rm -v "${OUT_DIR}:/work/out:Z" -v demo-video-hf:/root/.cache/huggingface -e PYTHONUNBUFFERED=1 "$@"
}

usage() {
  cat <<'EOF'
usage: demo-video.sh <command>
  build                      build the tools image (Playwright, Chromium, ffmpeg, Kokoro)
  record                     record the scenes on the cluster (env: see README.md)
  voice [voice] [speed]      generate the voice-over (default: af_sarah 1.0)
  merge <base> <retake>:<scene>,...   use the scenes of a retake (paths under /work/out)
  plan                       print the montage plan, its duration and the YouTube chapters
  montage                    build out/multi-agents-demo.mp4 (with the voice-over if out/voice exists)
  clean                      remove the tools image and the model cache volume
EOF
}

case "${1:-}" in
  build)
    podman build -t "${IMAGE}" -f "${HERE}/Containerfile" "${HERE}"
    ;;
  record)
    : "${APPS_DOMAIN:?APPS_DOMAIN is required}" "${FRONTEND_PASSWORD:?}" "${PLATFORM_USER:?}" "${PLATFORM_PASSWORD:?}"
    run -e APPS_DOMAIN -e IDP_NAME -e FRONTEND_USER -e FRONTEND_PASSWORD -e PLATFORM_USER -e PLATFORM_PASSWORD \
        -e KEEP_USERS -e SCENES -e OUT -e CASE_DOMAINS -e CLAIM -e TENDER -e POSTAL -e CHAT_PROMPT \
        -e RESULT_CASES -e REVIEW_DIRECT -e REVIEW_QUESTION -e REVIEW_CHOICE -e REVIEW_NOTE -e MLFLOW_URL \
        "${IMAGE}" python3 /opt/demo-video/record.py
    ;;
  voice)
    run "${IMAGE}" python3 -W ignore /opt/demo-video/narration.py "${2:-af_sarah}" "${3:-1.0}"
    ;;
  merge)
    shift
    run "${IMAGE}" python3 /opt/demo-video/merge_marks.py "$@"
    ;;
  plan|montage)
    voice=()
    if [ "${NO_VOICE:-}" != "1" ] && [ -f "${OUT_DIR}/voice/narration.json" ]; then
      voice=(-e VOICE_JSON=/work/out/voice/narration.json)
    fi
    if [ "$1" = "plan" ]; then
      run -e REC -e BUILD -e RUN_TIME ${voice[@]+"${voice[@]}"} "${IMAGE}" python3 /opt/demo-video/montage.py --plan
    else
      run -e REC -e BUILD -e RUN_TIME ${voice[@]+"${voice[@]}"} "${IMAGE}" sh -c \
        'python3 /opt/demo-video/montage.py && sh "${BUILD:-/work/out/build}/montage.sh" \
         && cp "${BUILD:-/work/out/build}/final.mp4" /work/out/multi-agents-demo.mp4'
      echo "video: ${OUT_DIR}/multi-agents-demo.mp4"
    fi
    ;;
  clean)
    podman rmi "${IMAGE}" || true
    podman volume rm demo-video-hf || true
    ;;
  *)
    usage
    exit 1
    ;;
esac
