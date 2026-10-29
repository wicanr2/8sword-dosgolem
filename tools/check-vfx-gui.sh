#!/usr/bin/env bash
set -euo pipefail
test -f /.dockerenv
test "$(id -u)" = 1000
vfx_bin="${1:?binary directory}"
vfx_driver="${2:?XTEST helper}"
vfx_original="${3:?original}"
vfx_assets="${4:?r68}"
vfx_out="${5:?new output}"
vfx_mode="${6:?fixture or normal}"
test -f "$vfx_bin/8sword"
test -f "$vfx_driver"
test -d "$vfx_original"
test -f "$vfx_assets/poster-toolbar.json"
test ! -e "$vfx_out"
mkdir "$vfx_out" "$vfx_out/save"
export DISPLAY=:98 LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS=1 MESA_GLTHREAD=false GOMAXPROCS=2
vfx_cycles=20000
if [[ "$vfx_mode" == fixture ]]; then export EIGHTSWORD_VFX_FIXTURE=1; vfx_cycles=3000; else test "$vfx_mode" == normal; fi
vfx_pid=""
Xvfb "$DISPLAY" -screen 0 1920x1200x24 -nolisten tcp > "$vfx_out/xvfb.log" 2>&1 &
vfx_xvfb=$!
cleanup(){ if [[ -n "$vfx_pid" ]]; then kill "$vfx_pid" 2>/dev/null || true; fi; kill "$vfx_xvfb" 2>/dev/null || true; wait 2>/dev/null || true; }
trap cleanup EXIT
trap 'exit 130' INT TERM
sleep .5
sha256sum "$vfx_bin/8sword" "$vfx_driver" "$0" > "$vfx_out/executables.sha256"
"$vfx_bin/8sword" -root "$vfx_original" -assets "$vfx_assets" -saves "$vfx_out/scratch" -settings "$vfx_out/settings.json" -capture-dir "$vfx_out/save" -mute -poster cover -cycles "$vfx_cycles" -battle-ai target -battle-rules auto -max-updates 16000 > "$vfx_out/save/player.log" 2>&1 &
vfx_pid=$!
timeout -s QUIT 350 "$vfx_driver" -out "$vfx_out/save" -flow save -saves "$vfx_out/scratch" -recruitment-hire-check -battle-check > "$vfx_out/save/gui-check.log" 2>&1
for _ in {1..100}; do if ! kill -0 "$vfx_pid" 2>/dev/null; then break; fi; sleep .1; done
if kill -0 "$vfx_pid" 2>/dev/null; then kill -QUIT "$vfx_pid"; wait "$vfx_pid"; exit 1; fi
wait "$vfx_pid"
vfx_pid=""
cp "$vfx_out/scratch/gamedata.ay" "$vfx_out/save/saved-gamedata.ay"
if [[ -f "$vfx_out/scratch/gamedata.ay.rules.json" ]]; then cp "$vfx_out/scratch/gamedata.ay.rules.json" "$vfx_out/save/saved-rules.json"; fi
