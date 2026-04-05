#!/usr/bin/env bash
set -euo pipefail

# ---- configuration ----
BLENDER="/usr/local/blender/blender"
SCRIPT="./scripts/map.py"
# -----------------------

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <shot-name-without-.json>  (e.g. shot_1)"
    exit 1
fi

SHOT_NAME="$1"

if [ ! -f "./config/${SHOT_NAME}.json" ]; then
    echo "Error: shot config not found: ./config/${SHOT_NAME}.json"
    exit 1
fi

"$BLENDER" --background --python "$SCRIPT" -- "$SHOT_NAME"
