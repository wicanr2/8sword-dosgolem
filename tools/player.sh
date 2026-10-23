#!/usr/bin/env bash
# 主機只編排 Docker／Git，工作負載均在有界非 root 容器內。
set -euo pipefail
task_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
task_work="$task_root/workplace"
task_player="$task_work/player"
task_uid="$(id -u)"
task_gid="$(id -g)"
task_go=dosgolem-go-ebiten:1.24-r1
task_py=sc-cht-hdtools:pillow11.3.0-r1
task_orig="$task_work/intake-20261023/sources/game/8sword"
test "$(docker image inspect "$task_go" --format '{{.Id}}')" = sha256:8ed6bdee2bce1f32f804e888f942b25bbf62f2165a43344bb4587f3371de0581
test "$(docker image inspect "$task_py" --format '{{.Id}}')" = sha256:44d0742ca1061bcd453440cdce925afa31c5324e115fca1334da0e364f0e2c48
valid_name(){ [[ "$1" =~ ^[a-zA-Z0-9_-]+$ ]]; }
case "${1:-}" in
  dependencies)
    test -f "$task_root/go.mod"; test -f "$task_root/go.sum"
    mkdir -p "$task_work/gomodcache" "$task_work/gocache"
    exec timeout 180s docker run --rm --name 8sword-player-dependencies --network bridge \
      --user "$task_uid:$task_gid" --memory 800m --cpus 1 --pids-limit 64 \
      --mount "type=bind,src=$task_root/go.mod,dst=/project/go.mod,readonly" \
      --mount "type=bind,src=$task_root/go.sum,dst=/project/go.sum" \
      --mount "type=bind,src=$task_work/gomodcache,dst=/gomodcache" \
      --mount "type=bind,src=$task_work/gocache,dst=/gocache" \
      -w /project -e GOMODCACHE=/gomodcache -e GOCACHE=/gocache \
      -e GOPROXY=https://proxy.golang.org -e GOSUMDB=sum.golang.org \
      "$task_go" go mod download all
    ;;
  build|test|test-player)
    task_action="$1"
    bash "$task_root/tools/research.sh" build-probe
    test -d "$task_work/gocache"; test -d "$task_work/gomodcache"
    mkdir -p "$task_player"
    exec timeout 180s docker run --rm --name "8sword-player-$task_action" --network none \
      --user "$task_uid:$task_gid" --memory 1800m --cpus 2 --pids-limit 128 \
      --mount "type=bind,src=$task_root,dst=/project,readonly" \
      --mount "type=bind,src=$task_work/dosgolem,dst=/dosgolem,readonly" \
      --mount "type=bind,src=$task_work/gocache,dst=/gocache" \
      --mount "type=bind,src=$task_work/gomodcache,dst=/gomodcache,readonly" \
      --mount "type=bind,src=$task_player,dst=/out" \
      -w /tmp -e GOCACHE=/gocache -e GOMODCACHE=/gomodcache \
      "$task_go" bash -c '
        set -e
        printf "go 1.24.0\nuse (\n /project\n /dosgolem\n)\n" > /tmp/go.work
        export GOWORK=/tmp/go.work
        if [[ "$1" == test || "$1" == test-player ]]; then
          art_assets=""
          if [[ -f /out/assets-painted-r8/terrain.json ]]; then
            art_assets=/out/assets-painted-r8
          else
            printf "%s\n" "未備本機 HD 圖像，僅執行字型測試；圖像測試會明示跳過。"
          fi
          EIGHTSWORD_TEST_ORIG=/project/workplace/intake-20261023/sources/game/8sword \
            EIGHTSWORD_TEST_ASSETS=/out/assets EIGHTSWORD_TEST_GRAPHICS_ASSETS="$art_assets" \
            go test -mod=readonly /project/internal/eightsword
          if [[ "$1" == test ]]; then
            cd /dosgolem
            go test -mod=readonly ./oracle ./internal/machine ./internal/dos ./internal/state
          fi
        else
          find /project/internal /project/cmd -type f -name "*.go" -print0 \
            | sort -z | xargs -0 sha256sum > /out/build-inputs.sha256
          sha256sum /project/go.mod /project/go.sum /project/tools/gui-check.go >> /out/build-inputs.sha256
          go build -mod=readonly -o /out/8sword /project/cmd/8sword
          go build -mod=readonly -o /out/8sword-replay /project/cmd/8sword-replay
          go build -mod=readonly -o /out/gui-check /project/tools/gui-check.go
          sha256sum -c /out/build-inputs.sha256 > /out/build-source-checks.log
          go version > /out/build-go-version.txt
          sha256sum /out/8sword /out/8sword-replay /out/gui-check > /out/build-outputs.sha256
        fi' build "$task_action"
    ;;
  assets)
    test -f "$task_orig/PAM.AY"
    task_fonts=/usr/share/fonts/opentype/noto
    test -d "$task_fonts"; test -f "$task_fonts/NotoSansCJK-Black.ttc"
    mkdir -p "$task_player/assets"
    exec timeout 40s docker run --rm --name 8sword-player-assets --network none \
      --user "$task_uid:$task_gid" --memory 512m --cpus 1 --pids-limit 64 \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_fonts,dst=/fonts,readonly" \
      --mount "type=bind,src=$task_player/assets,dst=/out" \
      "$task_py" python /tools/prepare-hd-assets.py --exe /orig/PAM.AY \
      --font /fonts/NotoSansCJK-Black.ttc --out /out
    ;;
  graphics-assets)
    task_name="${2:?指定新的素材組名稱}"
    valid_name "$task_name"
    task_set="${3:-current}"
    case "$task_set" in ground|landscape|portrait|interface|objects|current) ;; *) exit 2;; esac
    task_refs="$task_work/probe-20261023/graphics-first"
    test -f "$task_orig/PMAP.AY"; test -d "$task_refs"; test -f "$task_player/assets/font.json"
    test -d "$task_root/docs/images"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout 40s docker run --rm --name "8sword-graphics-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 512m --cpus 1 --pids-limit 64 \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_refs,dst=/refs,readonly" \
      --mount "type=bind,src=$task_player/assets,dst=/fonts,readonly" \
      --mount "type=bind,src=$task_root/docs/images,dst=/style,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-hd-graphics.py --source /orig/PMAP.AY --refs /refs \
      --font-assets /fonts --style-reference /style/hd-style-approved-r1.png --out /out --set "$task_set"
    ;;
  replay)
    task_mode="${2:?指定 hd 或 native}"
    task_name="${3:?指定新的收據名稱}"
    valid_name "$task_name"
    case "$task_mode" in hd) task_hd=true;; native) task_hd=false;; *) exit 2;; esac
    test -f "$task_player/8sword-replay"; test -d "$task_orig"; test -d "$task_player/assets"
    task_out="$task_player/replays/$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    shift 3
    exec timeout 180s docker run --rm --name "8sword-replay-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 1200m --cpus 1 --pids-limit 64 \
      --mount "type=bind,src=$task_player,dst=/player,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      --entrypoint /player/8sword-replay "$task_go" \
      -root /orig -assets /player/assets -out /out -hd="$task_hd" "$@"
    ;;
  gui-check)
    task_name="${2:?指定新的 GUI 收據名稱}"
    valid_name "$task_name"
    test -f "$task_player/8sword"; test -f "$task_player/gui-check"
    test -d "$task_player/assets"; test -d "$task_orig"
    task_out="$task_player/gui/$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    task_limit=220s
    if [[ "${EIGHTSWORD_GUI_FLOW:-inspect}" == save-cycle ]]; then task_limit=420s; fi
    exec timeout "$task_limit" docker run --rm --name "8sword-gui-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 1800m --cpus 2 --pids-limit 128 \
      --mount "type=bind,src=$task_player,dst=/bin-player,readonly" \
      --mount "type=bind,src=$task_player/assets,dst=/assets,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      -e EIGHTSWORD_GUI_CYCLES="${EIGHTSWORD_GUI_CYCLES:-20000}" \
      -e EIGHTSWORD_GUI_RECORD="${EIGHTSWORD_GUI_RECORD:-1}" \
      -e EIGHTSWORD_GUI_VSYNC="${EIGHTSWORD_GUI_VSYNC:-true}" \
      -e EIGHTSWORD_GUI_FLOW="${EIGHTSWORD_GUI_FLOW:-inspect}" \
      -e EIGHTSWORD_GUI_ACTOR_WALK="${EIGHTSWORD_GUI_ACTOR_WALK:-0}" \
      -e EIGHTSWORD_GUI_ASSETS="${EIGHTSWORD_GUI_ASSETS:-/assets}" \
      -e EIGHTSWORD_GUI_NATIVE_FRAME="${EIGHTSWORD_GUI_NATIVE_FRAME:-}" \
      "$task_go" bash /tools/gui-check.sh
    ;;
  *) printf '%s\n' '用法：bash tools/player.sh dependencies|build|test|test-player|assets|graphics-assets <名稱>|replay hd|native <名稱> [參數]|gui-check <名稱>' >&2; exit 2;;
esac
