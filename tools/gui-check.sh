#!/usr/bin/env bash
# 在 Go 工具容器內執行；背景程序有 trap，外層另設 timeout。
set -euo pipefail
test -f /bin-player/8sword
test -f /bin-player/gui-check
test -d /out
export DISPLAY=:98 LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS=1
export MESA_GLTHREAD=false GOMAXPROCS=2
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
record_flags=()
audio_flags=()
actor_flags=()
intro_flags=()
if [[ "${EIGHTSWORD_GUI_ACTOR_WALK:-0}" == 1 ]]; then actor_flags=(-actor-walk); fi
if [[ "${EIGHTSWORD_GUI_SHOW_INTRO:-0}" == 1 ]]; then intro_flags=(-intro-title); fi
if [[ "${EIGHTSWORD_GUI_RECORD:-1}" == 1 ]]; then record_flags=(-record); fi
if [[ "${EIGHTSWORD_GUI_RECORD_AUDIO:-0}" == 1 ]]; then audio_flags=(-record-audio); fi
phases=(inspect)
if [[ "${EIGHTSWORD_GUI_FLOW:-inspect}" == save-cycle ]]; then phases=(save reload); fi
if [[ "${EIGHTSWORD_GUI_FLOW:-inspect}" == fallback ]]; then phases=(fallback); fi
if [[ "${EIGHTSWORD_GUI_FLOW:-inspect}" == art-fallback ]]; then phases=(art-fallback); fi
if [[ "${EIGHTSWORD_GUI_FLOW:-inspect}" == music ]]; then phases=(music); fi
if [[ "${EIGHTSWORD_GUI_FLOW:-inspect}" == menus ]]; then phases=(menus); fi
if [[ "${EIGHTSWORD_GUI_FLOW:-inspect}" == boot ]]; then phases=(boot); fi
if [[ "${EIGHTSWORD_GUI_FLOW:-inspect}" == boot-fallback ]]; then phases=(boot-fallback); fi
if [[ "${EIGHTSWORD_GUI_FLOW:-inspect}" == intro ]]; then phases=(intro); fi
if [[ "${EIGHTSWORD_GUI_FLOW:-inspect}" == intro-skip ]]; then phases=(intro-skip); fi
if [[ "${EIGHTSWORD_GUI_FLOW:-inspect}" == intro-fallback ]]; then phases=(intro-fallback); fi
for phase in "${phases[@]}"; do
  phase_out=/out
  if [[ "$phase" != inspect ]]; then phase_out="/out/$phase"; mkdir -p "$phase_out"; fi
  cp /bin-player/build-inputs.sha256 /bin-player/build-outputs.sha256 /bin-player/build-go-version.txt "$phase_out/"
  sha256sum /bin-player/8sword /bin-player/gui-check > "$phase_out/executables.sha256"
  cat /proc/loadavg > "$phase_out/load-start.txt"
  cat /sys/fs/cgroup/cpu.stat > "$phase_out/cpu-start.txt"
  cat "/proc/$xvfb_pid/stat" > "$phase_out/xvfb-start.txt"
  /bin-player/8sword -root /orig -assets "${EIGHTSWORD_GUI_ASSETS:-/assets}" -saves /out/scratch \
    -capture-dir "$phase_out" -max-updates 4000 -mute "${record_flags[@]}" "${audio_flags[@]}" \
    -cpu-profile "$phase_out/cpu.pprof" -vsync="${EIGHTSWORD_GUI_VSYNC:-true}" \
    -cycles "${EIGHTSWORD_GUI_CYCLES:-20000}" > "$phase_out/player.log" 2>&1 &
  gui_pid=$!
  /bin-player/gui-check -out "$phase_out" -flow "$phase" -saves /out/scratch \
    -native-frame "${EIGHTSWORD_GUI_NATIVE_FRAME:-}" "${actor_flags[@]}" "${intro_flags[@]}" > "$phase_out/gui-check.log" 2>&1
  wait "$gui_pid"
  gui_pid=""
  cat /proc/loadavg > "$phase_out/load-end.txt"
  cat /sys/fs/cgroup/cpu.stat > "$phase_out/cpu-end.txt"
  cat "/proc/$xvfb_pid/stat" > "$phase_out/xvfb-end.txt"
done
printf '%s\n' 'GUI normal-input path finished; inspect image and state audits separately.'
