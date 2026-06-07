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

SCRIPTS_DIR="./scripts"
BLENDER="$(resolve_blender)" || {
    echo "Error: Blender executable not found. Set BLENDER_BIN or install Blender at /Applications/Blender.app/Contents/MacOS/Blender or /usr/local/blender/blender" >&2
    exit 1
}

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

