#!/usr/bin/env bash
# 在 Go 工具容器內執行；背景程序有 trap，外層另設 timeout。
set -euo pipefail
test -f /bin-player/8sword
test -f /bin-player/gui-check
test -d /out
export DISPLAY=:98 LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS=1
export MESA_GLTHREAD=false
gui_pid=""
Xvfb "$DISPLAY" -screen 0 1920x1200x24 -nolisten tcp > /out/xvfb.log 2>&1 &
xvfb_pid=$!
cleanup(){
  if [[ -n "$gui_pid" ]]; then kill "$gui_pid" 2>/dev/null || true; fi
  kill "$xvfb_pid" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT TERM
sleep 0.5
/bin-player/8sword -root /orig -assets /assets -saves /out/scratch \
  -capture-dir /out -max-updates 4000 -mute -record -cycles "${EIGHTSWORD_GUI_CYCLES:-20000}" > /out/player.log 2>&1 &
gui_pid=$!
/bin-player/gui-check -out /out > /out/gui-check.log 2>&1
wait "$gui_pid"
printf '%s\n' 'GUI normal-input path finished; inspect image and state audits separately.'
