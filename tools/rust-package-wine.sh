#!/bin/sh
# 056：只在 Wine image 執行，X11 socket 僅與同批控制容器共用。
set -eu
test -e /.dockerenv
test "$(id -u)" = 1000
export DISPLAY=:98 WINEDEBUG=-all WINEDLLOVERRIDES='mscoree,mshtml='
export LANG=C.UTF-8 LC_ALL=C.UTF-8
export WINEPREFIX=/q/smoke/windows-prefix HOME=/tmp/8sword-home
export SDL_AUDIODRIVER=dummy SDL_RENDER_DRIVER=software
mkdir -p "$HOME" /q/smoke/windows
task_package="/q/smoke/解壓 測試-windows-x86_64/8sword-${EIGHTSWORD_PACKAGE_VERSION}-windows-x86_64"
test -f "$task_package/8sword.exe"
export WINEPATH="$(winepath -w "$task_package")"
Xvfb :98 -screen 0 3100x1450x24 -nolisten tcp -ac >/q/smoke/windows/xvfb.log 2>&1 &
task_xvfb=$!
trap 'wineserver -k || true; kill "$task_xvfb" || true; wait "$task_xvfb" || true' EXIT INT TERM
sleep 1
wineboot -u >/q/smoke/windows/wineboot.log 2>&1
wine "$task_package/8sword.exe" --version >/q/smoke/windows/version.txt 2>&1
wine "$task_package/8sword.exe" --self-check >/q/smoke/windows/self-check.txt 2>&1
wine cmd /c 'echo %LOCALAPPDATA%' >/q/smoke/windows/default-save-root.txt 2>&1
for task_test in /q/build/cross/x86_64-pc-windows-gnu/debug/deps/eightsword_remake-*.exe; do
 test -f "$task_test"
 wine "$task_test" --test-threads=1 >"/q/smoke/windows/$(basename "$task_test").log" 2>&1
done
for task_phase in fresh cold; do
 task_elapsed=0
 while ! test -f "/q/smoke/windows/$task_phase.go"; do
  sleep 1; task_elapsed=$((task_elapsed + 1)); test "$task_elapsed" -lt 150
 done
 mkdir -p "/q/smoke/windows/$task_phase"
 set +e
 task_capture='Z:\q\smoke\windows\'"$task_phase"
 if [ "$task_phase" = cold ]; then set -- --skip-intro; else set --; fi
 wine "$task_package/8sword.exe" "$@" --scale 1 --seed 1 --capture-dir "$task_capture" >"/q/smoke/windows/$task_phase/player.log" 2>&1
 task_code=$?
 set -e
 printf '%s\n' "$task_code" >"/q/smoke/windows/$task_phase.exit"
 test "$task_code" = 0
done
