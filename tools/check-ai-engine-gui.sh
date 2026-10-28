#!/usr/bin/env bash
# 030 READY: normal XTEST battle/save followed by a native-AI cold load.
set -euo pipefail
test -f /.dockerenv
test "$(id -u)" = 1000
ai_bin="${1:?candidate directory}"
ai_driver="${2:?isolated XTEST driver}"
ai_original="${3:?read-only original}"
ai_assets="${4:?read-only r65 assets}"
ai_output="${5:?new output}"
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
for phase in save reload; do
 mkdir "$ai_output/$phase"
 mode=native
 helper=()
 if [[ "$phase" == save ]]; then mode=target; helper=(-recruitment-hire-check -battle-check); fi
 "$ai_bin/8sword" -root "$ai_original" -assets "$ai_assets" -saves "$ai_output/scratch" \
  -settings "$ai_output/settings.json" -capture-dir "$ai_output/$phase" -mute -poster cover \
  -cycles 20000 -battle-ai "$mode" -max-updates 15000 > "$ai_output/$phase/player.log" 2>&1 &
 ai_gui_pid=$!
 "$ai_driver" -out "$ai_output/$phase" -flow "$phase" -saves "$ai_output/scratch" "${helper[@]}" > "$ai_output/$phase/gui-check.log" 2>&1
 wait "$ai_gui_pid"
 ai_gui_pid=""
done
