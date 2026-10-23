#!/usr/bin/env bash
# 僅在 psychicwar-dosboxx 容器中執行，產物是輔助基準。
set -euo pipefail
test -f /orig/PREDELLA.EXE
test -d /out
mkdir /out/drive
cp -R /orig/. /out/drive/
export DISPLAY=:98 SDL_AUDIODRIVER=dummy
box_pid=""
Xvfb "$DISPLAY" -screen 0 1280x900x24 -nolisten tcp > /out/xvfb.log 2>&1 &
xvfb_pid=$!
cleanup() {
  if [[ -n "$box_pid" ]]; then kill "$box_pid" 2>/dev/null || true; fi
  kill "$xvfb_pid" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT TERM
for ((i=0; i<50; i++)); do
  if xdotool getdisplaygeometry >/dev/null 2>&1; then break; fi
  sleep 0.1
done
cat > /out/dosbox.conf <<'EOF'
[sdl]
fullscreen=false
output=surface
[dosbox]
machine=svga_s3
memsize=16
[render]
aspect=false
scaler=normal2x
[cpu]
core=normal
cycles=fixed 20000
[mixer]
nosound=true
[autoexec]
mount c /out/drive
c:
predella
EOF
dosbox-x -fastlaunch -conf /out/dosbox.conf > /out/dosbox.log 2>&1 &
box_pid=$!
window=""
for ((i=0; i<60; i++)); do
  window="$(xdotool search --onlyvisible --name 'DOSBox' 2>/dev/null | head -1 || true)"
  if [[ -n "$window" ]]; then break; fi
  sleep 0.2
done
test -n "$window"
xdotool windowfocus --sync "$window"
sleep 2
import -window "$window" /out/display-selection.png
xdotool key --clearmodifiers 1
sleep 1
import -window "$window" /out/sound-selection.png
xdotool key --clearmodifiers 1
sleep 12
import -window "$window" /out/intro.png
sleep "${AUX_LATE_WAIT:-25}"
import -window "$window" /out/after-intro.png
printf '%s\n' 'DOSBox-X auxiliary captures complete; not a dosgolem receipt.'
