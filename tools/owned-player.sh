#!/usr/bin/env bash
# All build, import and player workloads remain inside bounded Docker.
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_work="$task_root/workplace/probe-20261023/graphics-first/battle-r1/owned-player-r1"
task_original="$task_root/workplace/intake-20261023/sources/game/8sword"
task_assets="$task_root/workplace/player/assets-painted-r69"
task_core="$task_root/workplace/player/runtime-render-r1/src"
task_modules="$task_root/workplace/gomodcache"
task_uid="$(id -u)"; task_gid="$(id -g)"
[[ "$task_uid" == 1000 ]]
test -d "$task_original"; test -d "$task_assets"; test -d "$task_core"; test -d "$task_modules"
test "$(docker image inspect --format '{{.Id}}' dosgolem-go-ebiten:1.24-r1)" = sha256:8ed6bdee2bce1f32f804e888f942b25bbf62f2165a43344bb4587f3371de0581
test "$(docker image inspect --format '{{.Id}}' sc-cht-hdtools:pillow11.3.0-r2)" = sha256:b050fc7c49003ea6eecbbe0fc93b465b6869daf550c3284d5039e5e87517e831
case "${1:-}" in
 prepare)
  test ! -e "$task_work"; test -d "$(dirname "$task_work")"
  exec timeout -k 5s 120s docker run --rm --network none --user "$task_uid:$task_gid" --memory 1g --cpus 2 --pids-limit 96 \
   -e PYTHONDONTWRITEBYTECODE=1 --mount "type=bind,src=$task_root,dst=/project,readonly" \
   --mount "type=bind,src=$(dirname "$task_work"),dst=/project/workplace/probe-20261023/graphics-first/battle-r1" \
   sc-cht-hdtools:pillow11.3.0-r2 python /project/tools/prepare-owned-player.py prepare --project /project
  ;;
 build)
  test -d "$task_work"
  timeout -k 5s 90s docker run --rm --network none --user "$task_uid:$task_gid" --memory 1g --cpus 2 --pids-limit 96 \
   -e PYTHONDONTWRITEBYTECODE=1 --mount "type=bind,src=$task_root,dst=/project,readonly" \
   --mount "type=bind,src=$task_work,dst=/project/workplace/probe-20261023/graphics-first/battle-r1/owned-player-r1" \
   sc-cht-hdtools:pillow11.3.0-r2 python /project/tools/prepare-owned-player.py freeze --project /project
  exec timeout -k 10s 420s docker run --rm --network none --user "$task_uid:$task_gid" --memory 3g --cpus 2 --pids-limit 192 \
   --mount "type=bind,src=$task_work,dst=/out" --mount "type=bind,src=$task_core,dst=/core,readonly" \
   --mount "type=bind,src=$task_modules,dst=/gomodcache,readonly" -w /out/source \
   -e GOMODCACHE=/gomodcache -e GOCACHE=/out/build-cache -e GOMAXPROCS=2 \
   dosgolem-go-ebiten:1.24-r1 go build -mod=readonly -modfile=/out/probe.mod -o /out/8sword-owned ./cmd/8sword-owned
  ;;
 import)
  task_source="${2:?指定已關閉遊戲的原版存檔目錄}"
  task_destination="${3:?指定尚不存在的新Go進度目錄}"
  [[ "$task_source" = /* && "$task_destination" = /* ]]
  test -d "$task_source"; test ! -L "$task_source"
  test ! -e "$task_destination"; test ! -L "$task_destination"
  task_parent="$(dirname "$task_destination")"; task_name="$(basename "$task_destination")"
  test -d "$task_parent"; test ! -L "$task_parent"
  test -x "$task_work/8sword-owned"; test -d "$task_work/inputs"
  exec timeout -k 5s 90s docker run --rm --init --network none --read-only --user "$task_uid:$task_gid" --memory 2g --cpus 2 --pids-limit 192 \
   --tmpfs /tmp:rw,exec,size=256m --mount "type=bind,src=$task_work,dst=/pack,readonly" \
   --mount "type=bind,src=$task_original,dst=/game,readonly" --mount "type=bind,src=$task_source,dst=/native,readonly" \
   --mount "type=bind,src=$task_parent,dst=/sessions" \
   dosgolem-go-ebiten:1.24-r1 xvfb-run -a /pack/8sword-owned -root /game -input /pack/inputs \
   -session "/sessions/$task_name" -import-native /native -import-only
  ;;
 run)
  task_session="${2:?指定Go進度目錄}"
  [[ "$task_session" = /* ]]; test -d "$task_session"; test ! -L "$task_session"
  test -f "$task_session/gamedata.ay"; test -f "$task_session/gamedata.ay.army.json"
  test -x "$task_work/8sword-owned"; test -d "$task_work/inputs"; test -d "$task_work/ui-assets"
  [[ "${DISPLAY:-}" =~ ^:[0-9]+(\.[0-9]+)?$ ]]
  task_display="${DISPLAY#:}"; task_display="${task_display%%.*}"
  test -S "/tmp/.X11-unix/X$task_display"
  task_auth="${XAUTHORITY:-$HOME/.Xauthority}"; test -f "$task_auth"
  exec timeout -k 10s 1800s docker run --rm --init --network none --read-only --user "$task_uid:$task_gid" --memory 3g --cpus 2 --pids-limit 192 \
   --tmpfs /tmp:rw,exec,size=512m -e HOME=/tmp -e DISPLAY -e XAUTHORITY=/x11-auth \
   -e LIBGL_ALWAYS_SOFTWARE=1 -e LP_NUM_THREADS=1 -e GOMAXPROCS=2 \
   --mount "type=bind,src=/tmp/.X11-unix,dst=/tmp/.X11-unix,readonly" --mount "type=bind,src=$task_auth,dst=/x11-auth,readonly" \
   --mount "type=bind,src=$task_work,dst=/pack,readonly" --mount "type=bind,src=$task_session,dst=/session" \
   --mount "type=bind,src=$task_original,dst=/game,readonly" \
   --mount "type=bind,src=$task_original,dst=/project/workplace/intake-20261023/sources/game/8sword,readonly" \
   --mount "type=bind,src=$task_assets,dst=/assets,readonly" \
   dosgolem-go-ebiten:1.24-r1 /pack/8sword-owned -root /game -assets /assets -input /pack/inputs \
   -ui-assets /pack/ui-assets -session /session -scratch /tmp/native-shadow
  ;;
 *) printf '%s\n' '用法：owned-player.sh prepare | build | import <原版存檔目錄> <新的Go進度目錄> | run <Go進度目錄>' >&2; exit 2 ;;
esac
