#!/usr/bin/env bash
# 開發入口。沿原版 HD 操作；所有執行工作留在 Docker。
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_work="$task_root/workplace/probe-20261023/graphics-first/battle-r1/original-player-integration-r1"
task_game="$task_root/workplace/intake-20261023/sources/game/8sword"
task_assets="$task_root/workplace/player/assets-painted-r69"
task_core="$task_root/workplace/player/runtime-render-r1/src"
task_modules="$task_root/workplace/gomodcache"
task_uid="$(id -u)"; task_gid="$(id -g)"
[[ "$task_uid" == 1000 ]]
test -d "$task_work/source"; test -d "$task_game"; test -d "$task_assets"
test -d "$task_core"; test -d "$task_modules"
test "$(docker image inspect --format '{{.Id}}' dosgolem-go-ebiten:1.24-r1)" = sha256:8ed6bdee2bce1f32f804e888f942b25bbf62f2165a43344bb4587f3371de0581
case "${1:-}" in
 build)
  exec timeout -k 10s 420s docker run --rm --init --network none --user "$task_uid:$task_gid" --memory 3g --cpus 2 --pids-limit 192 \
   --mount "type=bind,src=$task_work,dst=/out" --mount "type=bind,src=$task_core,dst=/core,readonly" \
   --mount "type=bind,src=$task_modules,dst=/gomodcache,readonly" -w /out/source \
   -e GOMODCACHE=/gomodcache -e GOCACHE=/out/build-cache -e GOMAXPROCS=2 -e GOTOOLCHAIN=local \
   dosgolem-go-ebiten:1.24-r1 go build -mod=readonly -modfile=/out/probe.mod \
   -ldflags '-X github.com/wicanr2/8sword-dosgolem/internal/ownedworld.originalPlayerBuild=original-ui-r1' \
   -o /out/8sword-original-player ./cmd/8sword-owned
  ;;
 run)
  task_session="${2:?指定已匯入的 Go 世界進度目錄}"
  task_scratch="${3:?指定尚不存在的原版暫存目錄}"
  [[ "$task_session" = /* && "$task_scratch" = /* ]]
  test -d "$task_session"; test ! -L "$task_session"; test ! -e "$task_scratch"; test ! -L "$task_scratch"
  task_parent="$(dirname "$task_scratch")"; task_name="$(basename "$task_scratch")"
  test -d "$task_parent"; test -d /tmp/.X11-unix; test -n "${DISPLAY:-}"
  test -x "$task_work/8sword-original-player"
  exec timeout -k 10s 3600s docker run --rm --init --network none --read-only --user "$task_uid:$task_gid" --memory 3g --cpus 2 --pids-limit 192 \
   --tmpfs /tmp:rw,exec,size=256m -e "DISPLAY=$DISPLAY" \
   --mount type=bind,src=/tmp/.X11-unix,dst=/tmp/.X11-unix,readonly \
   --mount "type=bind,src=$task_work,dst=/pack,readonly" --mount "type=bind,src=$task_game,dst=/game,readonly" \
   --mount "type=bind,src=$task_assets,dst=/assets,readonly" --mount "type=bind,src=$task_session,dst=/session" \
   --mount "type=bind,src=$task_parent,dst=/scratch-parent" \
   dosgolem-go-ebiten:1.24-r1 /pack/8sword-original-player -root /game -assets /assets -input /pack/inputs \
   -ui-assets /pack/ui-assets -session /session -scratch "/scratch-parent/$task_name"
  ;;
 *) printf '%s\n' '用法：bash tools/original-player.sh build | run <Go世界進度> <新的暫存目錄>。開始畫面請選繼續；新遊戲建立與戰中重啟待 Rust 階段。' >&2; exit 2 ;;
esac
