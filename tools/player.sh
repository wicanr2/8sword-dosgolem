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
    exec timeout -k 10s 420s docker run --rm --init --name "8sword-player-$task_action" --network none \
      --user "$task_uid:$task_gid" --memory 1800m --cpus 2 --pids-limit 128 \
      --mount "type=bind,src=$task_root,dst=/project,readonly" \
      --mount "type=bind,src=$task_work/dosgolem,dst=/dosgolem,readonly" \
      --mount "type=bind,src=$task_work/gocache,dst=/gocache" \
      --mount "type=bind,src=$task_work/gomodcache,dst=/gomodcache,readonly" \
      --mount "type=bind,src=$task_player,dst=/out" \
      -w /tmp -e GOCACHE=/gocache -e GOMODCACHE=/gomodcache -e GOMAXPROCS=2 \
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
          music_assets=""
          if [[ -f /out/assets-painted-r9/music.json ]]; then
            music_assets=/out/assets-painted-r9
          fi
          intro_assets=""
          if [[ -f /out/assets-painted-r10/intro.json ]]; then
            intro_assets=/out/assets-painted-r10
          fi
          EIGHTSWORD_TEST_ORIG=/project/workplace/intake-20261023/sources/game/8sword \
            EIGHTSWORD_TEST_ASSETS=/out/assets EIGHTSWORD_TEST_GRAPHICS_ASSETS="$art_assets" \
            EIGHTSWORD_TEST_MUSIC_ASSETS="$music_assets" \
            EIGHTSWORD_TEST_INTRO_ASSETS="$intro_assets" \
            EIGHTSWORD_TEST_STORY_ASSETS=/out/assets-painted-r11 \
            EIGHTSWORD_TEST_STORY_BACKGROUND_ASSETS=/out/assets-painted-r12 \
            EIGHTSWORD_TEST_FONT_CHOICES_ASSETS=/out/assets-painted-r14 \
            EIGHTSWORD_TEST_PUBLISHER_ASSETS=/out/assets-painted-r15 \
            EIGHTSWORD_TEST_ARMY_ASSETS=/out/assets-painted-r16 \
            EIGHTSWORD_TEST_BATTLE_ASSETS=/out/assets-painted-r17 \
            EIGHTSWORD_TEST_BATTLE_ACTOR_ASSETS=/out/assets-painted-r18 \
            EIGHTSWORD_TEST_BATTLE_ACTOR_CACHE=/project/workplace/probe-20261023/graphics-first/battle-r1/man16-art-r1 \
            EIGHTSWORD_TEST_MAN06_ASSETS=/out/assets-painted-r19 \
            EIGHTSWORD_TEST_MAN06_CACHE=/project/workplace/probe-20261023/graphics-first/battle-r1/man06-art-r1 \
            EIGHTSWORD_TEST_MAN11_ASSETS=/out/assets-painted-r20 \
            EIGHTSWORD_TEST_MAN11_CACHE=/project/workplace/probe-20261023/graphics-first/battle-r1/man11-art-r1 \
            EIGHTSWORD_TEST_MAN21_ASSETS=/out/assets-painted-r21 \
            EIGHTSWORD_TEST_MAN21_CACHE=/project/workplace/probe-20261023/graphics-first/battle-r1/man21-art-r1 \
            EIGHTSWORD_TEST_PON_ASSETS=/out/assets-painted-r22 \
            EIGHTSWORD_TEST_PON_CACHE=/project/workplace/probe-20261023/graphics-first/battle-r1/pon-art-r1 \
            EIGHTSWORD_TEST_BATTLE_MILITIA_ASSETS=/out/assets-painted-r23 \
            EIGHTSWORD_TEST_CHOI_ASSETS=/out/assets-painted-r25 \
            EIGHTSWORD_TEST_CHOI_CACHE=/project/workplace/probe-20261023/graphics-first/battle-r1/choi-art-r1 \
            EIGHTSWORD_TEST_PALETTE_ASSETS=/out/assets-painted-r26 \
            EIGHTSWORD_TEST_POSTER_ASSETS=/out/assets-painted-r28 \
            EIGHTSWORD_TEST_MOE_ASSETS=/out/assets-painted-r27 \
            EIGHTSWORD_TEST_HEROINE_ASSETS=/out/assets-painted-r29 \
            EIGHTSWORD_TEST_MUSEUM_ASSETS=/out/assets-painted-r30 \
            EIGHTSWORD_TEST_STORY_PRELUDE_ASSETS=/out/assets-painted-r31 \
            EIGHTSWORD_TEST_PUBLISHER_ICON_ASSETS=/out/assets-painted-r32 \
            go test -v -timeout=390s -p=2 -mod=readonly /project/internal/eightsword
          if [[ "$1" == test ]]; then
            cd /dosgolem
            go test -mod=readonly ./oracle ./internal/machine ./internal/dos ./internal/state
          fi
        else
          find /project/internal /project/cmd -type f -name "*.go" -print0 \
            | sort -z | xargs -0 sha256sum > /out/build-inputs.sha256
          sha256sum /project/go.mod /project/go.sum /project/tools/gui-check.go /project/tools/music-check.go /project/tools/heroine-check.go /project/tools/museum-check.go /project/tools/story-prelude-check.go >> /out/build-inputs.sha256
          go build -mod=readonly -o /out/8sword /project/cmd/8sword
          go build -mod=readonly -o /out/8sword-replay /project/cmd/8sword-replay
          go build -mod=readonly -o /out/gui-check /project/tools/gui-check.go
          go build -mod=readonly -o /out/music-check /project/tools/music-check.go
          go build -mod=readonly -o /out/heroine-check /project/tools/heroine-check.go
          go build -mod=readonly -o /out/museum-check /project/tools/museum-check.go
          go build -mod=readonly -o /out/story-prelude-check /project/tools/story-prelude-check.go
          sha256sum -c /out/build-inputs.sha256 > /out/build-source-checks.log
          go version > /out/build-go-version.txt
          sha256sum /out/8sword /out/8sword-replay /out/gui-check /out/music-check /out/heroine-check /out/museum-check /out/story-prelude-check > /out/build-outputs.sha256
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
  battle-assets)
    task_name="${2:?指定新的素材組名稱}"
    task_base="${3:-painted-r16}"
    valid_name "$task_name"; valid_name "$task_base"
    task_art="$task_work/probe-20261023/graphics-first/battle-r1"
    test -d "$task_player/assets-$task_base"; test -f "$task_orig/GRO02.EG"
    test -f "$task_art/gro02-painted-raw-r1.png"; test -f "$task_art/gro02-painted-r1.prompt.txt"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout 60s docker run --rm --name "8sword-battle-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 700m --cpus 1 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_art,dst=/art,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-hd-battle.py --base /base --source /orig/GRO02.EG \
      --art /art/gro02-painted-raw-r1.png --prompt /art/gro02-painted-r1.prompt.txt --out /out
    ;;
  battle-actor-assets|battle-man06-assets|battle-man11-assets|battle-man21-assets|battle-pon-assets)
    task_name="${2:?指定新的素材組名稱}"
    task_unit=MAN16; task_default_base=painted-r17
    if [[ "$1" == battle-man06-assets ]]; then task_unit=MAN06; task_default_base=painted-r18; fi
    if [[ "$1" == battle-man11-assets ]]; then task_unit=MAN11; task_default_base=painted-r19; fi
    if [[ "$1" == battle-man21-assets ]]; then task_unit=MAN21; task_default_base=painted-r20; fi
    if [[ "$1" == battle-pon-assets ]]; then task_unit=PON; task_default_base=painted-r21; fi
    task_base="${3:-$task_default_base}"
    valid_name "$task_name"; valid_name "$task_base"
    task_art="$task_work/probe-20261023/graphics-first/battle-r1/${task_unit,,}-art-r1"
    test -d "$task_player/assets-$task_base"; test -f "$task_orig/$task_unit.EGG"
    test -d "$task_art"; test -d "$task_root/tools"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout 60s docker run --rm --name "8sword-battle-actor-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 700m --cpus 1 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_art,dst=/art,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-hd-battle-actors.py --base /base --source "/orig/$task_unit.EGG" \
      --unit "$task_unit" --art-dir /art --out /out
    ;;
  battle-militia-assets)
    task_name="${2:?指定新的素材組名稱}"
    task_base="${3:-painted-r22}"
    valid_name "$task_name"; valid_name "$task_base"
    test -d "$task_player/assets-$task_base"; test -f "$task_orig/MAN01.EGG"
    test -d "$task_root/tools"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout 60s docker run --rm --name "8sword-battle-militia-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 700m --cpus 1 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-hd-battle-militia.py --base /base --source /orig/MAN01.EGG --out /out
    ;;
  battle-choi-assets)
    task_name="${2:?指定新的素材組名稱}"
    task_base="${3:-painted-r24}"
    valid_name "$task_name"; valid_name "$task_base"
    task_refs="$task_work/probe-20261023/graphics-first/battle-r1/choi-art-r1"
    test -d "$task_player/assets-$task_base"; test -f "$task_orig/CHOI.EGG"
    test -f "$task_refs/frame-0-painted-raw-r1.png"; test -d "$task_root/tools"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout -k 5s 60s docker run --rm --init --name "8sword-choi-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 700m --cpus 1 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_refs,dst=/refs,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-hd-battle-markers.py --base /base --source /orig/CHOI.EGG --refs /refs --out /out
    ;;
  palette-assets)
    task_name="${2:?指定新的素材組名稱}"
    task_base="${3:-painted-r25}"
    valid_name "$task_name"; valid_name "$task_base"
    test -d "$task_player/assets-$task_base"; test -f "$task_root/tools/prepare-hd-palette.py"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout -k 5s 60s docker run --rm --init --name "8sword-palette-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 512m --cpus 1 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-hd-palette.py --base /base --out /out
    ;;
  moe-lishu-assets|poster-toolbar-assets)
    task_name="${2:?指定新的素材組名稱}"
    valid_name "$task_name"
    task_default_base=painted-r26
    if [[ "$1" == poster-toolbar-assets ]]; then task_default_base=painted-r27; fi
    task_base="${3:-$task_default_base}"
    valid_name "$task_base"
    task_refs="$task_work/probe-20261023/graphics-first"
    test -d "$task_player/assets-$task_base"; test -d "$task_refs"; test -d "$task_orig"
    test -f "$task_refs/font-settings-r1/NotoSansCJK-Black.ttc"
    task_args=(python /tools/prepare-poster-toolbar.py --base /base --art /refs/poster-art-r1 --font /refs/font-settings-r1/NotoSansCJK-Black.ttc --out /out)
    if [[ "$1" == moe-lishu-assets ]]; then
      test -d "$task_player/assets-painted-r14"; test -f "$task_orig/TIT1.AY"
      test -f "$task_refs/font-settings-r1/TW-MOE-Li-3.00.ttf"
      task_args=(python /tools/prepare-moe-lishu.py --base /base --publisher-base /player/assets-painted-r14 --source /orig/TIT1.AY --fonts /refs/font-settings-r1 --out /out)
    fi
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout -k 5s 90s docker run --rm --init --name "8sword-ui-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 1200m --cpus 1 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_player,dst=/player,readonly" \
      --mount "type=bind,src=$task_refs,dst=/refs,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" "${task_args[@]}"
    ;;
  heroine-assets)
    task_name="${2:?指定新的素材組名稱}"
    task_base="${3:-painted-r28}"
    valid_name "$task_name"; valid_name "$task_base"
    task_refs="$task_work/probe-20261023/graphics-first/museum-art-r1"
    test -d "$task_player/assets-$task_base"; test -d "$task_orig"
    test -f "$task_refs/heroine-closeup-r1.png"; test -f "$task_refs/heroine-closeup-r1.prompt.txt"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout -k 5s 60s docker run --rm --init --name "8sword-heroine-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 700m --cpus 1 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_refs,dst=/refs,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-hd-heroine.py --base /base --orig /orig --art /refs/heroine-closeup-r1.png --prompt /refs/heroine-closeup-r1.prompt.txt --out /out
    ;;
  heroine-check)
    task_name="${2:?指定新的收據名稱}"
    task_set="${3:-painted-r29}"
    task_escape="${4:-0}"
    task_font="${5:-noto}"
    valid_name "$task_name"; valid_name "$task_set"
    [[ "$task_escape" =~ ^[0-9]+$ ]]
    [[ "$task_font" == noto || "$task_font" == lishu || "$task_font" == caoshu ]]
    test -f "$task_player/heroine-check"; test -d "$task_orig"; test -d "$task_player/assets-$task_set"
    task_out="$task_player/replays/$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout -k 5s 300s docker run --rm --init --name "8sword-heroine-check-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 1800m --cpus 2 --pids-limit 128 \
      --mount "type=bind,src=$task_player,dst=/player,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      --entrypoint /player/heroine-check "$task_go" \
      -root /orig -assets "/player/assets-$task_set" -out /out -escape-ms "$task_escape" -font "$task_font"
    ;;
  story-prelude-assets)
    task_name="${2:?指定新的素材組名稱}"
    task_base="${3:-painted-r30}"
    valid_name "$task_name"; valid_name "$task_base"
    task_refs="$task_work/probe-20261023/graphics-first/story-art-r1"
    test -d "$task_player/assets-$task_base"; test -d "$task_orig"; test -f "$task_refs/color-canvas.png"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout -k 5s 120s docker run --rm --init --name "8sword-prelude-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 900m --cpus 2 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_refs,dst=/refs,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-hd-story-prelude.py --base /base --orig /orig --candidate /refs --out /out
    ;;
  story-prelude-check)
    task_name="${2:?指定新的收據名稱}"
    task_set="${3:-painted-r31}"
    task_escape="${4:-0}"
    task_font="${5:-noto}"
    valid_name "$task_name"; valid_name "$task_set"
    [[ "$task_escape" =~ ^[0-9]+$ ]]
    [[ "$task_font" == noto || "$task_font" == lishu || "$task_font" == caoshu ]]
    test -f "$task_player/story-prelude-check"; test -d "$task_orig"; test -d "$task_player/assets-$task_set"
    task_out="$task_player/replays/$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout -k 5s 300s docker run --rm --init --name "8sword-prelude-check-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 1800m --cpus 2 --pids-limit 128 \
      --mount "type=bind,src=$task_player,dst=/player,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      --entrypoint /player/story-prelude-check "$task_go" \
      -root /orig -assets "/player/assets-$task_set" -out /out -escape-ms "$task_escape" -font "$task_font"
    ;;
  museum-assets)
    task_name="${2:?指定新的素材組名稱}"
    task_base="${3:-painted-r29}"
    valid_name "$task_name"; valid_name "$task_base"
    task_refs="$task_work/probe-20261023/graphics-first/museum-art-r1/formal-assets-a-purple-r8"
    test -d "$task_player/assets-$task_base"; test -d "$task_orig"; test -f "$task_refs/museum.json"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout -k 5s 120s docker run --rm --init --name "8sword-museum-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 900m --cpus 2 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_refs,dst=/refs,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-hd-museum.py --base /base --orig /orig --candidate /refs --out /out
    ;;
  museum-check)
    task_name="${2:?指定新的收據名稱}"
    task_set="${3:-painted-r30}"
    task_escape="${4:-0}"
    task_font="${5:-noto}"
    valid_name "$task_name"; valid_name "$task_set"
    [[ "$task_escape" =~ ^[0-9]+$ ]]
    [[ "$task_font" == noto || "$task_font" == lishu || "$task_font" == caoshu ]]
    test -f "$task_player/museum-check"; test -d "$task_orig"; test -d "$task_player/assets-$task_set"
    task_out="$task_player/replays/$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout -k 5s 300s docker run --rm --init --name "8sword-museum-check-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 1800m --cpus 2 --pids-limit 128 \
      --mount "type=bind,src=$task_player,dst=/player,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      --entrypoint /player/museum-check "$task_go" \
      -root /orig -assets "/player/assets-$task_set" -out /out -escape-ms "$task_escape" -font "$task_font"
    ;;
  hero-redesign-assets)
    task_name="${2:?指定新的素材組名稱}"
    task_base="${3:-painted-r23}"
    valid_name "$task_name"; valid_name "$task_base"
    task_refs="$task_work/probe-20261023/graphics-first"
    test -d "$task_player/assets-$task_base"; test -f "$task_orig/MAN.AY"
    test -f "$task_refs/hero-portrait-r3.png"; test -d "$task_root/tools"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout -k 5s 60s docker run --rm --init --name "8sword-hero-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 700m --cpus 1 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_refs,dst=/refs,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-hd-hero-redesign.py --base /base --source /orig/MAN.AY --refs /refs --out /out
    ;;
  music-assets)
    task_name="${2:?指定新的素材組名稱}"
    task_base="${3:-painted-r8}"
    valid_name "$task_name"; valid_name "$task_base"
    task_music="$task_work/probe-20261023/music-first/hd-audition-r1"
    test -f "$task_music/b-approved-full-loop-r2.ogg"
    test -d "$task_player/assets-$task_base"; test -d "$task_root/tools"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout 60s docker run --rm --name "8sword-music-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 700m --cpus 1 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_music,dst=/music,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-hd-music.py --base /base \
      --music /music/b-approved-full-loop-r2.ogg --out /out
    ;;
  music-check)
    task_name="${2:?指定新的收據名稱}"
    task_set="${3:-painted-r9}"
    task_ms="${4:-90000}"
    task_intro_ms="${5:-500}"
    valid_name "$task_name"; valid_name "$task_set"
    [[ "$task_ms" =~ ^[0-9]+$ ]]
    [[ "$task_intro_ms" =~ ^[0-9]+$ ]]
    test -f "$task_player/music-check"; test -d "$task_orig"
    test -d "$task_player/assets-$task_set"
    task_out="$task_player/replays/$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout 240s docker run --rm --name "8sword-music-check-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 1800m --cpus 2 --pids-limit 128 \
      --mount "type=bind,src=$task_player,dst=/player,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      --entrypoint /player/music-check "$task_go" \
      -root /orig -assets "/player/assets-$task_set" -out /out -first-ms "$task_ms" -intro-ms "$task_intro_ms"
    ;;
  story-assets)
    task_name="${2:?指定新的素材組名稱}"
    task_base="${3:-painted-r10}"
    valid_name "$task_name"; valid_name "$task_base"
    task_fonts=/usr/share/fonts/opentype/noto
    task_runtime="$task_work/probe-20261023/music-first/intro-events-r1/unpacked-trace"
    test -f "$task_runtime/runtime-0110.bin"; test -d "$task_fonts"
    test -f "$task_fonts/NotoSansCJK-Black.ttc"; test -f "$task_orig/PREDELLA.EXE"
    test -d "$task_player/assets-$task_base"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout 60s docker run --rm --name "8sword-story-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 700m --cpus 1 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_runtime,dst=/runtime,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_fonts,dst=/fonts,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-hd-story.py --base /base \
      --runtime /runtime/runtime-0110.bin --exe /orig/PREDELLA.EXE \
      --font /fonts/NotoSansCJK-Black.ttc --out /out
    ;;
  story-background-assets)
    task_name="${2:?指定新的素材組名稱}"
    task_base="${3:-painted-r11}"
    valid_name "$task_name"; valid_name "$task_base"
    task_art="$task_work/probe-20261023/graphics-first/story-art-r1"
    test -f "$task_art/blue-raw.png"; test -d "$task_player/assets-$task_base"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout 60s docker run --rm --name "8sword-story-background-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 700m --cpus 1 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_art,dst=/art,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-hd-story-background.py --base /base \
      --approved /art/blue-raw.png --out /out
    ;;
  font-choices-assets)
    task_name="${2:?指定新的素材組名稱}"
    task_base="${3:-painted-r12}"
    valid_name "$task_name"; valid_name "$task_base"
    task_font_sources="$task_work/probe-20261023/graphics-first/font-settings-r1"
    task_fonts="$task_font_sources"
    test -d "$task_fonts"; test -f "$task_fonts/NotoSansCJK-Black.ttc"
    test -f "$task_font_sources/UnYetgul.ttf"; test -f "$task_font_sources/LiuJianMaoCao-Regular.ttf"
    test -f "$task_fonts/NotoSerifCJK-Regular.ttc"
    test -f "$task_font_sources/COPYING"; test -f "$task_font_sources/OFL.txt"
    test -d "$task_player/assets-$task_base"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout 60s docker run --rm --name "8sword-font-choices-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 700m --cpus 1 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_font_sources,dst=/sources,readonly" \
      --mount "type=bind,src=$task_fonts,dst=/fonts,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-font-choices.py --base /base --sources /sources \
      --noto /fonts/NotoSansCJK-Black.ttc --cjk-fallback /fonts/NotoSerifCJK-Regular.ttc --out /out
    ;;
  black-panel-assets)
    task_name="${2:?指定新的素材組名稱}"
    task_base="${3:-painted-r32}"
    valid_name "$task_name"; valid_name "$task_base"
    test -d "$task_player/assets-$task_base"; test -d "$task_orig"; test -f "$task_orig/PMAP.AY"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout -k 5s 90s docker run --rm --init --name "8sword-black-panel-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 900m --cpus 2 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-hd-black-panel.py --base /base --source /orig/PMAP.AY --out /out
    ;;
  bamboo-assets)
    task_name="${2:?指定新的素材組名稱}"
    task_base="${3:-painted-r35}"
    valid_name "$task_name"; valid_name "$task_base"
    test -d "$task_player/assets-$task_base"; test -d "$task_orig"
    task_refs="$task_work/probe-20261023/graphics-first/map-interaction-r1"
    test -f "$task_refs/bamboo-painted-r1.png"; test -f "$task_refs/bamboo-painted-r1.prompt.txt"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout -k 5s 90s docker run --rm --init --name "8sword-bamboo-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 900m --cpus 2 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_refs,dst=/refs,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-hd-bamboo.py --base /base --orig /orig --refs /refs --out /out
    ;;
  recruitment-assets)
    task_name="${2:?指定新的素材組名稱}"
    task_base="${3:-painted-r33}"
    valid_name "$task_name"; valid_name "$task_base"
    test -d "$task_player/assets-$task_base"; test -d "$task_orig"
    test -f "$task_root/docs/images/recruitment-gate-approved-r1.png"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout -k 5s 90s docker run --rm --init --name "8sword-recruitment-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 900m --cpus 2 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_root/docs/images,dst=/approved,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-hd-recruitment.py --base /base --orig /orig --approved /approved --out /out
    ;;
  publisher-icon-assets)
    task_name="${2:?指定新的素材組名稱}"
    task_base="${3:-painted-r31}"
    valid_name "$task_name"; valid_name "$task_base"
    test -d "$task_player/assets-$task_base"; test -d "$task_orig"
    test -f "$task_root/docs/images/publisher-icon-gradient-approved-r1.png"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout -k 5s 90s docker run --rm --init --name "8sword-publisher-icon-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 900m --cpus 2 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_root/docs/images,dst=/approved,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-hd-publisher-icon.py --base /base --orig /orig \
        --approved /approved/publisher-icon-gradient-approved-r1.png --out /out
    ;;
  publisher-assets)
    task_name="${2:?指定新的素材組名稱}"
    task_base="${3:-painted-r14}"
    valid_name "$task_name"; valid_name "$task_base"
    task_fonts="$task_work/probe-20261023/graphics-first/font-settings-r1"
    test -d "$task_fonts"; test -d "$task_player/assets-$task_base"; test -f "$task_orig/TIT1.AY"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout 60s docker run --rm --name "8sword-publisher-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 900m --cpus 1 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_fonts,dst=/fonts,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-hd-publisher.py --base /base --source /orig/TIT1.AY --fonts /fonts --out /out
    ;;
  intro-assets)
    task_name="${2:?指定新的素材組名稱}"
    task_base="${3:-painted-r9}"
    valid_name "$task_name"; valid_name "$task_base"
    task_fonts=/usr/share/fonts/opentype/noto
    task_notice=/usr/share/doc/fonts-noto-cjk
    test -d "$task_fonts"; test -f "$task_fonts/NotoSansCJK-Black.ttc"
    test -d "$task_notice"; test -f "$task_notice/copyright"
    test -f "$task_orig/TIT2.AY"; test -d "$task_player/assets-$task_base"
    task_out="$task_player/assets-$task_name"
    test ! -e "$task_out"; mkdir -p "$task_out"
    exec timeout 60s docker run --rm --name "8sword-intro-assets-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 700m --cpus 1 --pids-limit 64 \
      --mount "type=bind,src=$task_player/assets-$task_base,dst=/base,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_fonts,dst=/fonts,readonly" \
      --mount "type=bind,src=$task_notice,dst=/notice,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "$task_py" python /tools/prepare-hd-intro.py --base /base --source /orig/TIT2.AY \
      --font /fonts/NotoSansCJK-Black.ttc --notice /notice/copyright --out /out
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
    if [[ "${EIGHTSWORD_GUI_FLOW:-inspect}" == captions ]]; then task_limit=360s; fi
    if [[ "${EIGHTSWORD_GUI_FLOW:-inspect}" == save-cycle ]]; then task_limit=420s; fi
    if [[ "${EIGHTSWORD_GUI_SHOW_HEROINE:-0}" == 1 ]]; then task_limit=600s; fi
    if [[ "${EIGHTSWORD_GUI_SHOW_MUSEUM:-0}" == 1 ]]; then task_limit=1000s; fi
    exec timeout "$task_limit" docker run --rm --init --name "8sword-gui-$task_name" --network none \
      --user "$task_uid:$task_gid" --memory 1800m --cpus 2 --pids-limit 128 \
      --mount "type=bind,src=$task_player,dst=/bin-player,readonly" \
      --mount "type=bind,src=$task_player/assets,dst=/assets,readonly" \
      --mount "type=bind,src=$task_orig,dst=/orig,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      -e EIGHTSWORD_GUI_CYCLES="${EIGHTSWORD_GUI_CYCLES:-20000}" \
      -e EIGHTSWORD_GUI_RECORD="${EIGHTSWORD_GUI_RECORD:-1}" \
      -e EIGHTSWORD_GUI_RECORD_AUDIO="${EIGHTSWORD_GUI_RECORD_AUDIO:-0}" \
      -e EIGHTSWORD_GUI_VSYNC="${EIGHTSWORD_GUI_VSYNC:-true}" \
      -e EIGHTSWORD_GUI_FLOW="${EIGHTSWORD_GUI_FLOW:-inspect}" \
      -e EIGHTSWORD_GUI_ACTOR_WALK="${EIGHTSWORD_GUI_ACTOR_WALK:-0}" \
      -e EIGHTSWORD_GUI_ARMY_CHECK="${EIGHTSWORD_GUI_ARMY_CHECK:-0}" \
      -e EIGHTSWORD_GUI_DISMISS_CHECK="${EIGHTSWORD_GUI_DISMISS_CHECK:-0}" \
      -e EIGHTSWORD_GUI_RECRUITMENT_CHECK="${EIGHTSWORD_GUI_RECRUITMENT_CHECK:-0}" \
      -e EIGHTSWORD_GUI_RECRUITMENT_HIRE_CHECK="${EIGHTSWORD_GUI_RECRUITMENT_HIRE_CHECK:-0}" \
      -e EIGHTSWORD_GUI_BATTLE_CHECK="${EIGHTSWORD_GUI_BATTLE_CHECK:-0}" \
      -e EIGHTSWORD_GUI_SHOW_INTRO="${EIGHTSWORD_GUI_SHOW_INTRO:-0}" \
      -e EIGHTSWORD_GUI_SHOW_PUBLISHER="${EIGHTSWORD_GUI_SHOW_PUBLISHER:-0}" \
      -e EIGHTSWORD_GUI_PUBLISHER_FONT_CYCLE="${EIGHTSWORD_GUI_PUBLISHER_FONT_CYCLE:-0}" \
      -e EIGHTSWORD_GUI_SHOW_STORY="${EIGHTSWORD_GUI_SHOW_STORY:-0}" \
      -e EIGHTSWORD_GUI_SHOW_CAPTIONS="${EIGHTSWORD_GUI_SHOW_CAPTIONS:-0}" \
      -e EIGHTSWORD_GUI_SHOW_HEROINE="${EIGHTSWORD_GUI_SHOW_HEROINE:-0}" \
      -e EIGHTSWORD_GUI_SHOW_MUSEUM="${EIGHTSWORD_GUI_SHOW_MUSEUM:-0}" \
      -e EIGHTSWORD_GUI_FONT_CYCLE="${EIGHTSWORD_GUI_FONT_CYCLE:-0}" \
      -e EIGHTSWORD_GUI_INITIAL_FONT="${EIGHTSWORD_GUI_INITIAL_FONT:-}" \
      -e EIGHTSWORD_GUI_ASSETS="${EIGHTSWORD_GUI_ASSETS:-/assets}" \
      -e EIGHTSWORD_GUI_NATIVE_FRAME="${EIGHTSWORD_GUI_NATIVE_FRAME:-}" \
      "$task_go" bash /tools/gui-check.sh
    ;;
  *) printf '%s\n' '用法：bash tools/player.sh dependencies|build|test|test-player|assets|graphics-assets <名稱>|battle-assets <名稱> [基底名稱]|battle-actor-assets <名稱> [基底名稱]|battle-man06-assets <名稱> [基底名稱]|battle-man11-assets <名稱> [基底名稱]|battle-man21-assets <名稱> [基底名稱]|battle-pon-assets <名稱> [基底名稱]|battle-militia-assets <名稱> [基底名稱]|battle-choi-assets <名稱> [基底名稱]|palette-assets <名稱> [基底名稱]|hero-redesign-assets <名稱> [基底名稱]|music-assets <名稱> [基底名稱]|intro-assets <名稱> [基底名稱]|story-assets <名稱> [基底名稱]|story-background-assets <名稱> [基底名稱]|font-choices-assets <名稱> [基底名稱]|recruitment-assets <名稱> [基底名稱]|bamboo-assets <名稱> [基底名稱]|publisher-assets <名稱> [基底名稱]|music-check <名稱> [素材組] [虛擬毫秒]|museum-assets <名稱> [基底名稱]|museum-check <名稱> [素材組] [普通Esc毫秒] [字型]|replay hd|native <名稱> [參數]|gui-check <名稱>' >&2; exit 2;;
esac
