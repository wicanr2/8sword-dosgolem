#!/usr/bin/env bash
# 030 READY: genuine toolbar, normal battle, F7 save and two cold restores.
set -euo pipefail
test -f /.dockerenv
test "$(id -u)" = 1000
tactics_bin="${1:?candidate}"
tactics_driver="${2:?XTEST helper}"
tactics_original="${3:?original}"
tactics_assets="${4:?r68 assets}"
tactics_out="${5:?new output}"
test -f "$tactics_bin/8sword"
test -f "$tactics_driver"
test -d "$tactics_original"
test -f "$tactics_assets/poster-toolbar.json"
test ! -e "$tactics_out"
mkdir "$tactics_out"
export DISPLAY=:98 LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS=1 MESA_GLTHREAD=false GOMAXPROCS=2
tactics_pid=""
Xvfb "$DISPLAY" -screen 0 1920x1200x24 -nolisten tcp > "$tactics_out/xvfb.log" 2>&1 &
tactics_xvfb=$!
cleanup(){
 if [[ -n "$tactics_pid" ]]; then kill "$tactics_pid" 2>/dev/null || true; fi
 kill "$tactics_xvfb" 2>/dev/null || true
 wait 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT TERM
sleep .5
sha256sum "$tactics_bin/8sword" "$tactics_driver" "$0" > "$tactics_out/executables.sha256"
for phase in save restore-tactics restore-native; do
 mkdir "$tactics_out/$phase"
 flow=reload
 expect=native
 helper=()
 if [[ "$phase" == save ]]; then flow=save; helper=(-recruitment-hire-check -battle-check); fi
 if [[ "$phase" == restore-tactics ]]; then expect=tactics; helper=(-rewrite-native); fi
 "$tactics_bin/8sword" -root "$tactics_original" -assets "$tactics_assets" -saves "$tactics_out/scratch" \
  -settings "$tactics_out/settings.json" -capture-dir "$tactics_out/$phase" -mute -poster cover \
  -cycles 20000 -battle-ai target -battle-rules auto -max-updates 16000 > "$tactics_out/$phase/player.log" 2>&1 &
 tactics_pid=$!
 timeout -s QUIT 240 "$tactics_driver" -out "$tactics_out/$phase" -flow "$flow" -expect-rules "$expect" \
  -saves "$tactics_out/scratch" "${helper[@]}" > "$tactics_out/$phase/gui-check.log" 2>&1
 for _ in {1..100}; do
  if ! kill -0 "$tactics_pid" 2>/dev/null; then break; fi
  sleep .1
 done
 if kill -0 "$tactics_pid" 2>/dev/null; then kill -QUIT "$tactics_pid"; wait "$tactics_pid"; exit 1; fi
 wait "$tactics_pid"
 tactics_pid=""
 cp "$tactics_out/scratch/gamedata.ay" "$tactics_out/$phase/saved-gamedata.ay"
 cp "$tactics_out/scratch/gamedata.ay.rules.json" "$tactics_out/$phase/saved-rules.json"
done
