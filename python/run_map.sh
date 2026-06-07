#!/usr/bin/env bash
set -euo pipefail

resolve_blender() {
    if [ -n "${BLENDER_BIN:-}" ]; then
        printf '%s\n' "$BLENDER_BIN"
        return 0
    fi

    local candidates=(
        "/Applications/Blender.app/Contents/MacOS/Blender"
        "/usr/local/blender/blender"
    )
    local candidate
    for candidate in "${candidates[@]}"; do
        if [ -x "$candidate" ]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done

    return 1
}

SCRIPT="./scripts/map.py"
BLENDER="$(resolve_blender)" || {
    echo "Error: Blender executable not found. Set BLENDER_BIN or install Blender at /Applications/Blender.app/Contents/MacOS/Blender or /usr/local/blender/blender" >&2
    exit 1
}

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <shot-name-without-.json>  (e.g. shot_1)"
    exit 1
fi

SHOT_NAME="$1"

if [ ! -f "./config/${SHOT_NAME}.json" ]; then
    echo "Error: shot config not found: ./config/${SHOT_NAME}.json"
    exit 1
fi

"$BLENDER" --background --python-exit-code 1 --python "$SCRIPT" -- "$SHOT_NAME"
