#!/usr/bin/env bash
set -euo pipefail
test -f /.dockerenv
test "$(id -u)" = 1000
fire_bin="${1:?private binaries}"
fire_root="${2:?read-only original}"
fire_assets="${3:?r68}"
fire_out="${4:?new output}"
test -f "$fire_bin/8sword"
test -f "$fire_bin/driver"
test ! -e "$fire_out"
mkdir "$fire_out"
export DISPLAY=:98 LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS=1 MESA_GLTHREAD=false GOMAXPROCS=2 EIGHTSWORD_VFX_FIXTURE=1
fire_pid=""
Xvfb "$DISPLAY" -screen 0 1920x1200x24 -nolisten tcp > "$fire_out/xvfb.log" 2>&1 &
fire_xvfb=$!
cleanup(){ if [[ -n "$fire_pid" ]]; then kill "$fire_pid" 2>/dev/null || true; fi; kill "$fire_xvfb" 2>/dev/null || true; wait 2>/dev/null || true; }
trap cleanup EXIT
trap 'exit 130' INT TERM
sleep .5
"$fire_bin/8sword" -root "$fire_root" -assets "$fire_assets" -saves "$fire_out/scratch" -settings "$fire_out/settings.json" -capture-dir "$fire_out" -mute -poster cover -cycles 3000 -battle-ai native -battle-rules native -max-updates 16000 > "$fire_out/player.log" 2>&1 &
fire_pid=$!
timeout -s QUIT 350 "$fire_bin/driver" -out "$fire_out" -flow save -saves "$fire_out/scratch" -recruitment-hire-check -battle-check > "$fire_out/gui-check.log" 2>&1
wait "$fire_pid"
fire_pid=""
