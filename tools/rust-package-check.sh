#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source "$task_root/tools/rust-package-defaults.env"
task_version="${EIGHTSWORD_PACKAGE_VERSION:-$EIGHTSWORD_DEFAULT_VERSION}"
task_batch="${EIGHTSWORD_PACKAGE_BATCH:-$EIGHTSWORD_DEFAULT_BATCH}"
[[ "$task_version" =~ ^v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}$ ]]
[[ "$task_batch" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]
task_q="$task_root/workplace/probe-20261023/graphics-first/battle-r1/$task_batch"
test -d "$task_q"; test -d "$task_root/tools"; test -d "$task_q/smoke/x11"
test "$(id -u)" = 1000
task_options=(--rm --init --network none --user "$(id -u):$(id -g)" --memory 3g --cpus 2 --pids-limit 256
 -e "EIGHTSWORD_PACKAGE_VERSION=$task_version" -e "EIGHTSWORD_PACKAGE_BATCH=$task_batch" --label "org.wicanr2.project=$task_batch" --mount "type=bind,src=$task_q,dst=/q"
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
