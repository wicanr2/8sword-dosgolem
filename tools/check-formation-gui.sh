#!/usr/bin/env bash
# 030 READY: normal battle and two cold starts share original saves and rules marker.
set -euo pipefail
test -f /.dockerenv
test "$(id -u)" = 1000
rules_bin="${1:?candidate directory}"
rules_driver="${2:?isolated XTEST driver}"
rules_original="${3:?read-only original}"
rules_assets="${4:?read-only r67 assets}"
rules_output="${5:?new output}"
rules_first="${6:-save}"
test -f "$rules_bin/8sword"
test -f "$rules_driver"
test -d "$rules_original"
test -f "$rules_assets/poster-toolbar.json"
if [[ "$rules_first" == save ]]; then
 test ! -e "$rules_output"
 mkdir "$rules_output"
else
 test "$rules_first" == restore-formation
 test -f "$rules_output/save/gui-input-receipt.json"
 test -f "$rules_output/save/gui-final.state"
 cp "$rules_output/scratch/gamedata.ay" "$rules_output/save/saved-gamedata.ay"
 cp "$rules_output/scratch/gamedata.ay.rules.json" "$rules_output/save/saved-rules.json"
fi
export DISPLAY=:98 LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS=1 MESA_GLTHREAD=false GOMAXPROCS=2
rules_gui_pid=""
Xvfb "$DISPLAY" -screen 0 1920x1200x24 -nolisten tcp > "$rules_output/xvfb.log" 2>&1 &
rules_xvfb_pid=$!
cleanup(){
 if [[ -n "$rules_gui_pid" ]]; then kill "$rules_gui_pid" 2>/dev/null || true; fi
 kill "$rules_xvfb_pid" 2>/dev/null || true
 wait 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT TERM
sleep .5
sha256sum "$rules_bin/8sword" "$rules_driver" "$0" > "$rules_output/executables-$rules_first.sha256"
rules_phases=(save restore-formation restore-native)
if [[ "$rules_first" == restore-formation ]]; then rules_phases=(restore-formation restore-native); fi
for phase in "${rules_phases[@]}"; do
 mkdir "$rules_output/$phase"
 flow=reload
 expect=native
 helper=()
 if [[ "$phase" == save ]]; then flow=save; helper=(-recruitment-hire-check -battle-check); fi
 if [[ "$phase" == restore-formation ]]; then expect=formation; helper=(-rewrite-native); fi
 "$rules_bin/8sword" -root "$rules_original" -assets "$rules_assets" -saves "$rules_output/scratch" \
  -settings "$rules_output/settings.json" -capture-dir "$rules_output/$phase" -mute -poster cover \
  -cycles 20000 -battle-ai target -battle-rules auto -max-updates 16000 > "$rules_output/$phase/player.log" 2>&1 &
 rules_gui_pid=$!
 timeout -s QUIT 150 "$rules_driver" -out "$rules_output/$phase" -flow "$flow" -expect-rules "$expect" -saves "$rules_output/scratch" "${helper[@]}" > "$rules_output/$phase/gui-check.log" 2>&1
 wait "$rules_gui_pid"
 rules_gui_pid=""
 cp "$rules_output/scratch/gamedata.ay" "$rules_output/$phase/saved-gamedata.ay"
 cp "$rules_output/scratch/gamedata.ay.rules.json" "$rules_output/$phase/saved-rules.json"
done
