#!/usr/bin/env bash
# Normal XTEST battle; existing rules/AI toolbar and genuine F7 save.
set -euo pipefail
test -f /.dockerenv
test "$(id -u)" = 1000
formation_bin="${1:?candidate directory}"
formation_driver="${2:?previous accepted XTEST helper}"
formation_original="${3:?read-only original}"
formation_assets="${4:?read-only r67}"
formation_out="${5:?new output}"
test -f "$formation_bin/8sword"
test -f "$formation_driver"
test -d "$formation_original"
test -f "$formation_assets/poster-toolbar.json"
test ! -e "$formation_out"
mkdir "$formation_out"
mkdir "$formation_out/save"
export DISPLAY=:98 LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS=1 MESA_GLTHREAD=false GOMAXPROCS=2
formation_pid=""
Xvfb "$DISPLAY" -screen 0 1920x1200x24 -nolisten tcp > "$formation_out/xvfb.log" 2>&1 &
formation_xvfb=$!
cleanup(){
 if [[ -n "$formation_pid" ]]; then kill "$formation_pid" 2>/dev/null || true; fi
 kill "$formation_xvfb" 2>/dev/null || true
 wait 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT TERM
sleep .5
sha256sum "$formation_bin/8sword" "$formation_driver" "$0" > "$formation_out/executables.sha256"
"$formation_bin/8sword" -root "$formation_original" -assets "$formation_assets" -saves "$formation_out/scratch" \
 -settings "$formation_out/settings.json" -capture-dir "$formation_out/save" -mute -poster cover \
 -cycles 20000 -battle-ai target -battle-rules auto -max-updates 16000 > "$formation_out/save/player.log" 2>&1 &
formation_pid=$!
timeout -s QUIT 210 "$formation_driver" -out "$formation_out/save" -flow save -expect-rules native \
 -saves "$formation_out/scratch" -recruitment-hire-check -battle-check > "$formation_out/save/gui-check.log" 2>&1
for _ in {1..100}; do
 if ! kill -0 "$formation_pid" 2>/dev/null; then break; fi
 sleep .1
done
if kill -0 "$formation_pid" 2>/dev/null; then kill -QUIT "$formation_pid"; wait "$formation_pid"; exit 1; fi
wait "$formation_pid"
formation_pid=""
cp "$formation_out/scratch/gamedata.ay" "$formation_out/save/saved-gamedata.ay"
cp "$formation_out/scratch/gamedata.ay.rules.json" "$formation_out/save/saved-rules.json"
