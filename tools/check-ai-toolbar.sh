#!/usr/bin/env bash
# 030/032: normal GUI battle, live AI menu changes and input isolation.
set -euo pipefail
test -f /.dockerenv
test "$(id -u)" = 1000
ai_bin="${1:?candidate directory}"
ai_driver="${2:?XTEST helper}"
ai_original="${3:?read-only original}"
ai_assets="${4:?read-only assets}"
ai_output="${5:?new output directory}"
test -f "$ai_bin/8sword"
test -f "$ai_driver"
test -d "$ai_original"
test -f "$ai_assets/poster-toolbar.json"
test ! -e "$ai_output"
mkdir "$ai_output"
export DISPLAY=:98 LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS=1 MESA_GLTHREAD=false GOMAXPROCS=2
ai_gui_pid=""
Xvfb "$DISPLAY" -screen 0 1920x1200x24 -nolisten tcp > "$ai_output/xvfb.log" 2>&1 &
ai_xvfb_pid=$!
cleanup(){
 if [[ -n "$ai_gui_pid" ]]; then kill "$ai_gui_pid" 2>/dev/null || true; fi
 kill "$ai_xvfb_pid" 2>/dev/null || true
 wait 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT TERM
sleep .5
sha256sum "$ai_bin/8sword" "$ai_driver" "$0" > "$ai_output/executables.sha256"
"$ai_bin/8sword" -root "$ai_original" -assets "$ai_assets" -saves "$ai_output/scratch" \
 -settings "$ai_output/settings.json" -capture-dir "$ai_output" -mute -poster cover \
 -cycles 20000 -battle-ai native -max-updates 15000 > "$ai_output/player.log" 2>&1 &
ai_gui_pid=$!
"$ai_driver" -out "$ai_output" -flow save -saves "$ai_output/scratch" \
 -recruitment-hire-check -battle-check > "$ai_output/gui-check.log" 2>&1
wait "$ai_gui_pid"
ai_gui_pid=""
