#!/usr/bin/env bash
# 053：只在有外層逾時與資源配額的 Docker 內執行。
set -euo pipefail
test -f /.dockerenv
test "$(id -u)" = 1000
ending_bin="${1:?binary directory}"
ending_original="${2:?read-only original directory}"
ending_assets="${3:?read-only assets directory}"
ending_output="${4:?new output directory}"
ending_flow="${5:?ending-full, ending-escape or save-cycle}"
test -f "$ending_bin/8sword"
test -f "$ending_bin/gui-check"
test -d "$ending_original"
test -f "$ending_assets/ending.json"
test ! -e "$ending_output"
test "$(stat -c %u "$(dirname "$ending_output")")" = 1000
mkdir "$ending_output"
export DISPLAY=:98 LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS=1
export MESA_GLTHREAD=false GOMAXPROCS=2
ending_gui_pid=""
Xvfb "$DISPLAY" -screen 0 1920x1200x24 -nolisten tcp > "$ending_output/xvfb.log" 2>&1 &
ending_xvfb_pid=$!
cleanup(){
  if [[ -n "$ending_gui_pid" ]]; then kill "$ending_gui_pid" 2>/dev/null || true; fi
  kill "$ending_xvfb_pid" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT TERM
sleep 0.5
phases=("$ending_flow")
case "$ending_flow" in
  ending-full|ending-escape) export EIGHTSWORD_RESEARCH_ENDING_BRANCH=1; ending_cycles=3000;;
  save-cycle) phases=(save reload); unset EIGHTSWORD_RESEARCH_ENDING_BRANCH; ending_cycles=20000;;
  *) exit 2;;
esac
sha256sum "$ending_bin/8sword" "$ending_bin/gui-check" "$0" > "$ending_output/executables.sha256"
for phase in "${phases[@]}"; do
  phase_out="$ending_output/$phase"
  mkdir "$phase_out"
  flags=()
  if [[ "$phase" != reload ]]; then flags=(-font noto); fi
  "$ending_bin/8sword" -root "$ending_original" -assets "$ending_assets" \
    -saves "$ending_output/scratch" -settings "$ending_output/settings.json" \
    -capture-dir "$phase_out" -record -mute -poster cover -cycles "$ending_cycles" \
    -max-updates 9000 "${flags[@]}" > "$phase_out/player.log" 2>&1 &
  ending_gui_pid=$!
  flags=()
  if [[ "$ending_flow" == save-cycle ]]; then flags=(-font-cycle -army-check); fi
  "$ending_bin/gui-check" -out "$phase_out" -flow "$phase" -saves "$ending_output/scratch" \
    "${flags[@]}" > "$phase_out/gui-check.log" 2>&1
  wait "$ending_gui_pid"
  ending_gui_pid=""
done
printf '%s\n' '實際視窗輸入完成；畫面、來源、存讀與隔離另由核對器確認。'
