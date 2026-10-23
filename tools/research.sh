#!/usr/bin/env bash
# 主機只作 Docker／Git 編排；分析與執行均留在容器。
set -euo pipefail

task_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
task_work="$task_root/workplace"
task_uid="$(id -u)"
task_gid="$(id -g)"
dosgolem_rev=f79eab6db8c64a524a06535e53e5d32b0bbcf7c8
research_image=mm3-research:20261015-r1
go_image=dosgolem-go-ebiten:1.24-r1
source_dir="$task_work/intake-20261023/sources/game/8sword"

require_image() {
  local actual
  actual="$(docker image inspect "$1" --format '{{.Id}}')"
  if [[ "$actual" != "$2" ]]; then
    printf '%s\n' "工具映像身分不符：$1。先核對 RESEARCH-LOG.md，不自動換版。" >&2
    exit 1
  fi
}

require_image "$research_image" sha256:5a3829d46aa9efde50c71f5a2c120d8cfd9e606965ca715f5dec8ef3b55865a1
require_image "$go_image" sha256:8ed6bdee2bce1f32f804e888f942b25bbf62f2165a43344bb4587f3371de0581

case "${1:-}" in
  intake)
    test -f "$task_root/8sword.zip"
    test -f "$task_root/珍092-神州八劍.rar"
    mkdir -p "$task_work"
    # 既有來源不覆寫；若已盤點，直接使用既有 manifest。
    exec timeout 120s docker run --rm --name 8sword-intake \
      --user "$task_uid:$task_gid" --memory 512m --cpus 1 --pids-limit 64 \
      --network none --read-only \
      --mount "type=bind,src=$task_root,dst=/input,readonly" \
      --mount "type=bind,src=$task_work,dst=/out" \
      --entrypoint python3 "$research_image" /input/tools/intake.py \
      --out /out/intake-20261023
    ;;
  build-probe)
    mkdir -p "$task_work"
    if [[ ! -d "$task_work/dosgolem/.git" ]]; then
      test -d /home/anr2/cht/dosgolem/.git
      git clone --no-hardlinks /home/anr2/cht/dosgolem "$task_work/dosgolem"
      git -C "$task_work/dosgolem" checkout --detach "$dosgolem_rev"
    fi
    test "$(git -C "$task_work/dosgolem" rev-parse HEAD)" = "$dosgolem_rev"
    if ! git -C "$task_work/dosgolem" diff --quiet HEAD -- . \
      ':(exclude)internal/machine/bda.go' ':(exclude)internal/machine/bios_page.go' \
      ':(exclude)internal/dos/bios.go' ':(exclude)internal/dos/planar_bios_page_test.go' \
      ':(exclude)oracle/presentation_observe.go' ':(exclude)oracle/presentation_observe_test.go' \
      ':(exclude)oracle/live.go' ':(exclude)oracle/audio_mix_test.go'; then
      printf '%s\n' 'dosgolem 副本有補丁範圍外的變更，先核對來源。' >&2
      exit 1
    fi
    task_patch="$task_root/tools/dosgolem-planar-pages.patch"
    if git -C "$task_work/dosgolem" apply --check "$task_patch" 2>/dev/null; then
      git -C "$task_work/dosgolem" apply "$task_patch"
    else
      git -C "$task_work/dosgolem" apply --reverse --check "$task_patch"
    fi
    task_patch="$task_root/tools/dosgolem-presentation-observe.patch"
    if git -C "$task_work/dosgolem" apply --check "$task_patch" 2>/dev/null; then
      git -C "$task_work/dosgolem" apply "$task_patch"
    else
      git -C "$task_work/dosgolem" apply --reverse --check "$task_patch"
    fi
    task_patch="$task_root/tools/dosgolem-audio-mix.patch"
    if git -C "$task_work/dosgolem" apply --check "$task_patch" 2>/dev/null; then
      git -C "$task_work/dosgolem" apply "$task_patch"
    else
      git -C "$task_work/dosgolem" apply --reverse --check "$task_patch"
    fi
    exec timeout 180s docker run --rm --name 8sword-probe-build \
      --user "$task_uid:$task_gid" --memory 1500m --cpus 2 --pids-limit 128 \
      --network none \
      --mount "type=bind,src=$task_work/dosgolem,dst=/source,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_work,dst=/work" \
      -w /source -e GOCACHE=/work/gocache -e GOMODCACHE=/work/gomodcache -e GOMAXPROCS=2 \
      "$go_image" bash -c 'set -e; sha256sum -c /tools/dosgolem-page-files.sha256; sha256sum -c /tools/dosgolem-presentation-files.sha256; sha256sum -c /tools/dosgolem-audio-files.sha256; go build -p=2 -mod=readonly -o /work/probe-pages ./cmd/probe'
    ;;
  probe)
    shift
    task_name="${1:?用法：bash tools/research.sh probe <新收據名稱> [probe 參數]}"
    shift
    if [[ ! "$task_name" =~ ^[a-zA-Z0-9_-]+$ ]]; then
      printf '%s\n' '收據名稱只能包含英數字、底線與連字號。' >&2
      exit 1
    fi
    test -f "$task_work/probe-pages"
    test -d "$source_dir"
    task_out="$task_work/probe-20261023/$task_name"
    test ! -e "$task_out"
    mkdir -p "$task_out/scratch"
    task_prior_mount=()
    if [[ -n "${EIGHTSWORD_SCRATCH_FROM:-}" ]]; then
      test -d "$EIGHTSWORD_SCRATCH_FROM"
      task_prior="$(cd "$EIGHTSWORD_SCRATCH_FROM" && pwd)"
      task_prior_mount+=(--mount "type=bind,src=$task_prior,dst=/prior-scratch,readonly")
    fi
    # 整個研究區唯讀；只有本次收據與 scratch 掛成可寫。
    exec timeout 150s docker run --rm --name "8sword-probe-$task_name" \
      --user "$task_uid:$task_gid" --memory 900m --cpus 1 --pids-limit 64 \
      --network none --read-only \
      --mount "type=bind,src=$task_work,dst=/work,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      "${task_prior_mount[@]}" \
      --entrypoint /bin/sh "$go_image" -c \
      'if test -d /prior-scratch; then cp -a /prior-scratch/. /out/scratch/ || exit 1; fi; /work/probe-pages -root /work/intake-20261023/sources/game/8sword -scratch /out/scratch "$@" > /out/probe.log 2>&1; code=$?; head -24 /out/probe.log; tail -8 /out/probe.log; exit "$code"' \
      probe "$@"
    ;;
  test)
    test -d "$task_work/dosgolem"
    mkdir -p "$task_work/probe-20261023/validation"
    exec timeout 120s docker run --rm --name 8sword-regression \
      --user "$task_uid:$task_gid" --memory 1500m --cpus 2 --pids-limit 128 \
      --network none \
      --mount "type=bind,src=$task_work/dosgolem,dst=/source,readonly" \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_work,dst=/work" \
      -w /source -e GOCACHE=/work/gocache -e GOMODCACHE=/work/gomodcache -e GOMAXPROCS=2 \
      "$go_image" bash -c 'set -e; bash -n /tools/research.sh; bash -n /tools/aux-dosbox.sh; sha256sum -c /tools/dosgolem-page-files.sha256; go version > /work/probe-20261023/validation/go-version.txt; go test -mod=readonly ./internal/dos ./internal/machine ./internal/state ./oracle -count=1 > /work/probe-20261023/validation/tests.log 2>&1; cat /work/probe-20261023/validation/tests.log'
    ;;
  font-source)
    task_fonts=/usr/share/fonts/opentype/noto
    task_out="$task_work/probe-20261023/text-first"
    test -d "$source_dir"
    test -f "$source_dir/PAM.AY"
    test -d "$task_fonts"
    test -f "$task_fonts/NotoSansCJK-Black.ttc"
    test -d "$task_out"
    test -f "$task_work/probe-20261023/new-game-confirm/screen.png"
    require_image sc-cht-hdtools:pillow11.3.0-r1 sha256:44d0742ca1061bcd453440cdce925afa31c5324e115fca1334da0e364f0e2c48
    exec timeout 40s docker run --rm --name 8sword-font-source \
      --user "$task_uid:$task_gid" --memory 512m --cpus 1 --pids-limit 64 \
      --network none --read-only \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_work,dst=/work,readonly" \
      --mount "type=bind,src=$task_fonts,dst=/fonts,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      --entrypoint python3 sc-cht-hdtools:pillow11.3.0-r1 \
      /tools/font-source.py --exe /work/intake-20261023/sources/game/8sword/PAM.AY \
      --reference /work/probe-20261023/new-game-confirm/screen.png \
      --font /fonts/NotoSansCJK-Black.ttc --out /out
    ;;
  font-preview)
    task_fonts=/usr/share/fonts/opentype/noto
    test -d "$task_fonts"
    test -f "$task_fonts/NotoSansCJK-Bold.ttc"
    test -f "$task_fonts/NotoSansCJK-Black.ttc"
    require_image sc-cht-hdtools:pillow11.3.0-r1 sha256:44d0742ca1061bcd453440cdce925afa31c5324e115fca1334da0e364f0e2c48
    task_out="$task_work/probe-20261023"
    test -d "$task_out"
    exec timeout 30s docker run --rm --name 8sword-font-preview \
      --user "$task_uid:$task_gid" --memory 512m --cpus 1 --pids-limit 64 \
      --network none --read-only \
      --mount "type=bind,src=$task_root/tools,dst=/tools,readonly" \
      --mount "type=bind,src=$task_fonts,dst=/fonts,readonly" \
      --mount "type=bind,src=$task_out,dst=/out" \
      --entrypoint python3 sc-cht-hdtools:pillow11.3.0-r1 \
      /tools/font-preview.py --fonts /fonts --out /out
    ;;
  audit)
    test -d "$task_work/probe-20261023/validation"
    require_image sc-cht-hdtools:pillow11.3.0-r1 sha256:44d0742ca1061bcd453440cdce925afa31c5324e115fca1334da0e364f0e2c48
    exec timeout 30s docker run --rm --name 8sword-bootstrap-audit \
      --user "$task_uid:$task_gid" --memory 256m --cpus 1 --pids-limit 64 \
      --network none --read-only \
      --mount "type=bind,src=$task_root,dst=/project,readonly" \
      --mount "type=bind,src=$task_work/probe-20261023/validation,dst=/out" \
      --entrypoint python3 sc-cht-hdtools:pillow11.3.0-r1 \
      /project/tools/audit.py --out /out/bootstrap-audit.json
    ;;
  *)
    printf '%s\n' '用法：bash tools/research.sh intake|build-probe|test|audit|font-preview|font-source|probe <新收據名稱> [probe 參數]' >&2
    exit 2
    ;;
esac
