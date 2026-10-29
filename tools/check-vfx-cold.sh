#!/usr/bin/env bash
# Reload the normal saved tactics game using the unmodified candidate.
set -euo pipefail
test -f /.dockerenv
test "$(id -u)" = 1000
vfx_bin="${1:?candidate}"
vfx_driver="${2:?normal XTEST helper}"
vfx_original="${3:?original}"
vfx_assets="${4:?r68}"
vfx_saved="${5:?completed normal GUI directory}"
test -f "$vfx_saved/save/gui-final.state"
test -f "$vfx_saved/scratch/gamedata.ay.rules.json"
test ! -e "$vfx_saved/reload"
mkdir "$vfx_saved/reload"
export DISPLAY=:98 LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS=1 MESA_GLTHREAD=false GOMAXPROCS=2
vfx_pid=""
Xvfb "$DISPLAY" -screen 0 1920x1200x24 -nolisten tcp > "$vfx_saved/reload/xvfb.log" 2>&1 &
vfx_xvfb=$!
cleanup(){ if [[ -n "$vfx_pid" ]]; then kill "$vfx_pid" 2>/dev/null || true; fi; kill "$vfx_xvfb" 2>/dev/null || true; wait 2>/dev/null || true; }
trap cleanup EXIT
trap 'exit 130' INT TERM
sleep .5
"$vfx_bin/8sword" -root "$vfx_original" -assets "$vfx_assets" -saves "$vfx_saved/scratch" -settings "$vfx_saved/settings.json" -capture-dir "$vfx_saved/reload" -mute -poster cover -cycles 20000 -battle-ai target -battle-rules auto -max-updates 8000 > "$vfx_saved/reload/player.log" 2>&1 &
vfx_pid=$!
timeout -s QUIT 180 "$vfx_driver" -out "$vfx_saved/reload" -flow reload -expect-rules tactics -saves "$vfx_saved/scratch" > "$vfx_saved/reload/gui-check.log" 2>&1
wait "$vfx_pid"
vfx_pid=""
cp "$vfx_saved/scratch/gamedata.ay" "$vfx_saved/reload/saved-gamedata.ay"
cp "$vfx_saved/scratch/gamedata.ay.rules.json" "$vfx_saved/reload/saved-rules.json"
