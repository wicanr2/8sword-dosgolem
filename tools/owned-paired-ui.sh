#!/usr/bin/env bash
# 030 DRAFT: run the Go paired-save battle UI in the pinned, isolated Docker runtime.
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_work="$task_root/workplace/probe-20261023/graphics-first/battle-r1/owned-paired-save-r1"
task_session="${EIGHTSWORD_PAIRED_UI_SESSION:-$task_work/session-preview-r1}"
task_uid="$(id -u)"
task_gid="$(id -g)"
[[ "$task_uid" == 1000 ]] || { printf '%s\n' '本機研究工具鏈要求 UID 1000。' >&2; exit 2; }
[[ "${DISPLAY:-}" =~ ^:[0-9]+(\.[0-9]+)?$ ]] || { printf '%s\n' '請從本機 X11 桌面執行，DISPLAY 必須是 :數字。' >&2; exit 2; }
task_display="${DISPLAY#:}"
task_display="${task_display%%.*}"
test -S "/tmp/.X11-unix/X$task_display"
test -x "$task_work/battle-ui"
test -d "$task_work/ui-assets"
for task_input in army-catalog.json combat-catalog.json seed-world.json; do test -f "$task_work/inputs/$task_input"; done
test -d "$task_session"
test -f "$task_session/gamedata.ay"
test "$(stat -c %u "$task_session")" = "$task_uid"
test "$(stat -c %u "$task_session/gamedata.ay")" = "$task_uid"
task_auth="${XAUTHORITY:-$HOME/.Xauthority}"
test -f "$task_auth" || { printf '%s\n' '找不到 X11 授權檔，請指定 XAUTHORITY。' >&2; exit 2; }
test "$(docker image inspect --format '{{.Id}}' dosgolem-go-ebiten:1.24-r1)" = sha256:8ed6bdee2bce1f32f804e888f942b25bbf62f2165a43344bb4587f3371de0581
exec timeout -k 10s 1800s docker run --rm --init --network none --read-only \
  --user "$task_uid:$task_gid" --memory 2g --cpus 2 --pids-limit 192 \
  --tmpfs /tmp:rw,exec,size=512m -e HOME=/tmp -e DISPLAY -e XAUTHORITY=/x11-auth \
  -e LIBGL_ALWAYS_SOFTWARE=1 -e LP_NUM_THREADS=1 -e GOMAXPROCS=2 \
  --mount "type=bind,src=/tmp/.X11-unix,dst=/tmp/.X11-unix,readonly" \
  --mount "type=bind,src=$task_auth,dst=/x11-auth,readonly" \
  --mount "type=bind,src=$task_work,dst=/prototype,readonly" \
  --mount "type=bind,src=$task_session,dst=/session" \
  dosgolem-go-ebiten:1.24-r1 /prototype/battle-ui \
  -catalog /prototype/inputs/army-catalog.json -combat /prototype/inputs/combat-catalog.json \
  -seed /prototype/inputs/seed-world.json -ui-assets /prototype/ui-assets -session /session
