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

CONFIG_DIR="./config"
OUTPUTS_DIR="./outputs"
RENDERS_DIR="./renders"
RUN_MAP_SCRIPT="./run_map.sh"
BLENDER="$(resolve_blender)" || {
	echo "Error: Blender executable not found. Set BLENDER_BIN or install Blender at /Applications/Blender.app/Contents/MacOS/Blender or /usr/local/blender/blender" >&2
	exit 1
}

if [ ! -x "$RUN_MAP_SCRIPT" ]; then
	echo "Error: run script is missing or not executable: $RUN_MAP_SCRIPT" >&2
	exit 1
fi

mkdir -p "$RENDERS_DIR"

SHOTS=()
while IFS= read -r shot_name; do
	SHOTS+=("$shot_name")
done < <(
	find "$CONFIG_DIR" -maxdepth 1 -type f -name 'shot_[0-9]*.json' \
		-exec basename {} .json \; | sort -V
)

if [ "${#SHOTS[@]}" -eq 0 ]; then
	echo "Error: no shot configs found in $CONFIG_DIR" >&2
	exit 1
fi

for shot_name in "${SHOTS[@]}"; do
	blend_file="$OUTPUTS_DIR/map_${shot_name}_2.blend"
	render_output="$RENDERS_DIR/${shot_name}"

	echo "Generating $blend_file"
	"$RUN_MAP_SCRIPT" "$shot_name"
	if [ ! -f "$blend_file" ]; then
		echo "Error: expected blend file not found: $blend_file" >&2
		exit 1
	fi

	echo "Rendering $blend_file -> $render_output"
	"$BLENDER" --background "$blend_file" --render-output "$render_output" --render-anim
done

echo "Finished generating and rendering ${#SHOTS[@]} shot(s)."
