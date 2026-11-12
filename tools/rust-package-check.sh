#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_q="$task_root/workplace/probe-20261023/graphics-first/battle-r1/rust-package-r1"
test -d "$task_q"; test -d "$task_root/tools"; test -d "$task_q/smoke/x11"
test "$(id -u)" = 1000
task_options=(--rm --init --network none --user "$(id -u):$(id -g)" --memory 3g --cpus 2 --pids-limit 256
 --label org.wicanr2.project=8sword-package-r1 --mount "type=bind,src=$task_q,dst=/q"
 --mount "type=bind,src=$task_root/tools,dst=/tools,readonly")
case "${1:-}" in
 linux)
  exec timeout -k 10s 240s docker run "${task_options[@]}" mm45-rust-desktop:1.99.1-r3 timeout 220 python3 /tools/rust-package-smoke.py linux ;;
 windows)
  task_name=8sword-package-wine-r1
  trap 'docker stop -t 2 "$task_name" >/dev/null 2>&1 || true' EXIT INT TERM
  timeout -k 10s 360s docker run "${task_options[@]}" --name "$task_name" \
   --mount "type=bind,src=$task_q/smoke/x11,dst=/tmp/.X11-unix" \
   sotn-hd-movie-vulkan:mesa25.2.8-r2 timeout 340 sh /tools/rust-package-wine.sh &
  task_worker=$!
  timeout -k 10s 300s docker run "${task_options[@]}" \
   --mount "type=bind,src=$task_q/smoke/x11,dst=/tmp/.X11-unix,readonly" \
   mm45-rust-desktop:1.99.1-r3 timeout 280 python3 /tools/rust-package-smoke.py windows
  wait "$task_worker" ;;
 *) echo '用法：bash tools/rust-package-check.sh linux|windows' >&2; exit 2 ;;
esac
