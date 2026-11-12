#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_q="$task_root/workplace/probe-20261023/graphics-first/battle-r1/rust-package-r1"
task_native=mm45-rust-desktop:1.99.1-r3
task_cross=dosgolem-rust-cross:1.99.1-sdk15.5-r1
test "$(id -u)" = 1000
test -d "$task_q"; test -d "$task_root/internal/remake-rust"; test -d "$task_root/tools"
test "$(docker image inspect --format '{{.Id}}' "$task_native")" = sha256:ac10129fb2667f9be114a19db5b7a3837ba1a4457627420aec3044792715b8e1
test "$(docker image inspect --format '{{.Id}}' "$task_cross")" = sha256:213e81d7c2be2edd9dfbdb6bfb7a1a0bf882c3accd38799bc3da030ce7f876f5
task_action="${1:-test}"
task_image="$task_native"; task_script=rust-package.py; task_seconds=240; task_network=none; task_rw=readonly
case "$task_action" in
 fetch) task_image="$task_cross"; task_script=rust-package-deps.py; task_arg=--fetch; task_network=bridge ;;
 deps) task_image="$task_cross"; task_script=rust-package-deps.py; task_arg=; task_seconds=1200 ;;
 linux) task_script=rust-package-build.py; task_arg=linux ;;
 cross) task_image="$task_cross"; task_script=rust-package-build.py; task_arg=cross; task_seconds=600 ;;
 stage-linux) task_arg=stage-linux ;;
 stage-cross) task_image="$task_cross"; task_arg=stage-cross ;;
 pack) task_image="$task_cross"; task_arg=pack; task_rw=rw; task_seconds=600 ;;
 *) echo '用法：bash tools/rust-package.sh fetch|deps|linux|cross|stage-linux|stage-cross|pack' >&2; exit 2 ;;
esac
task_mount="type=bind,src=$task_root,dst=/r"
if [[ "$task_rw" = readonly ]]; then task_mount+=,readonly; fi
exec timeout -k 10s "$((task_seconds + 20))"s docker run --rm --init --network "$task_network" --user "$(id -u):$(id -g)" --memory 3g --cpus 2 --pids-limit 192 \
 --label org.wicanr2.project=8sword-package-r1 \
 --mount "$task_mount" --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
 --mount "type=bind,src=$task_root/internal/remake-rust,dst=/crate,readonly" \
 --mount "type=bind,src=$task_q,dst=/q" \
 -e PYTHONDONTWRITEBYTECODE=1 -e MACOSX_DEPLOYMENT_TARGET=11.0 "$task_image" \
 timeout "$task_seconds" python3 "/tools/$task_script" ${task_arg:+"$task_arg"}
