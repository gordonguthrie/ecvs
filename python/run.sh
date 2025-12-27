#!/usr/bin/env bash
set -euo pipefail

# ---- configuration ----
BLENDER="../../blender-5.0.1-linux-x64/blender"
SCRIPTS_DIR="./scripts"
# -----------------------

# Check argument
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <script-name-without-.py>"
    exit 1
fi

SCRIPT_NAME="$1"
SCRIPT_PATH="${SCRIPTS_DIR}/${SCRIPT_NAME}.py"

# Check script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: script not found: $SCRIPT_PATH"
    exit 1
fi

# Run Blender
"$BLENDER" --background --python "$SCRIPT_PATH"

