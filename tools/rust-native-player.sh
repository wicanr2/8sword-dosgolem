#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_crate="$task_root/internal/remake-rust"
task_native="$task_root/workplace/probe-20261023/graphics-first/battle-r1/rust-enemy-spells-r1/native"
task_image=mm45-rust-desktop:1.99.1-r3
test -d "$task_crate"; test -d "$task_native"
[[ "$(id -u)" == 1000 ]]
test "$(docker image inspect --format '{{.Id}}' "$task_image")" = sha256:ac10129fb2667f9be114a19db5b7a3837ba1a4457627420aec3044792715b8e1
task_action="${1:-test}"; if (($#)); then shift; fi
case "$task_action" in
 test|build)
  exec timeout -k 10s 180s docker run --rm --init --network none --user "$(id -u):$(id -g)" --memory 2g --cpus 2 --pids-limit 128 \
   --mount "type=bind,src=$task_crate,dst=/crate,readonly" --mount "type=bind,src=$task_native,dst=/out" \
   -e CARGO_TARGET_DIR=/out/rust-target -w /crate "$task_image" sh -c '
    set -eu; test ! -e /game; test ! -e /core; test ! -e /gomodcache
    cargo fmt --all --check
    if [ "$1" = test ]; then
      cargo test --offline --locked --features desktop
      cargo run --offline --locked --features desktop -- --self-check
    else
      cargo build --offline --locked --release --features desktop
      cp /out/rust-target/release/8sword-remake /out/8sword-remake
    fi' sh "$task_action"
  ;;
 run)
  test -f "$task_native/8sword-remake"; test -d "$task_native/pack"
  test -d /tmp/.X11-unix; test -n "${DISPLAY:-}"
  task_options=(-e "DISPLAY=$DISPLAY" --mount 'type=bind,src=/tmp/.X11-unix,dst=/tmp/.X11-unix,readonly')
  if [[ -n "${XAUTHORITY:-}" ]] && test -f "$XAUTHORITY"; then
   task_options+=(--mount "type=bind,src=$XAUTHORITY,dst=/run/xauthority,readonly" -e XAUTHORITY=/run/xauthority)
  fi
  task_runtime="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
  if test -S "$task_runtime/pulse/native"; then
   task_options+=(--mount "type=bind,src=$task_runtime/pulse,dst=/run/pulse,readonly" -e PULSE_SERVER=unix:/run/pulse/native -e SDL_AUDIODRIVER=pulseaudio)
  elif test -d /dev/snd; then
   task_options+=(--device /dev/snd)
  fi
  exec timeout -k 10s 2h docker run --rm --init --network none --user "$(id -u):$(id -g)" --memory 2g --cpus 2 --pids-limit 128 \
   "${task_options[@]}" --mount "type=bind,src=$task_native/8sword-remake,dst=/player,readonly" \
   --mount "type=bind,src=$task_native/pack,dst=/media,readonly" "$task_image" /player --battle --assets /media "$@"
  ;;
 *) echo '用法：bash tools/rust-native-player.sh test|build|run [--mute] [--weak|--spells|--taoist|--enemy-spells]' >&2; exit 2 ;;
esac
