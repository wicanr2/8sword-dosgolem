#!/usr/bin/env bash
# Isolated reinforcement candidate. The launcher never changes player memory.
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_work="$task_root/workplace/probe-20261023/graphics-first/battle-r1/reinforcement-camps-r1"
task_session="${EIGHTSWORD_REINFORCEMENT_SESSION:-$task_work/session-gui-r2}"
task_uid="$(id -u)"; task_gid="$(id -g)"
[[ "$task_uid" == 1000 ]]
[[ "${DISPLAY:-}" =~ ^:[0-9]+(\.[0-9]+)?$ ]]
task_display="${DISPLAY#:}"; task_display="${task_display%%.*}"
test -S "/tmp/.X11-unix/X$task_display"
test -x "$task_work/reinforcement-ui"
test -d "$task_work/inputs"
test -d "$task_work/ui-assets"
test -d "$task_session"
test -f "$task_session/gamedata.ay"
test -f "$task_session/gamedata.ay.army.json"
test "$(stat -c %u "$task_session")" = "$task_uid"
task_original="$task_root/workplace/intake-20261023/sources/game/8sword"
task_assets="$task_root/workplace/player/assets-painted-r69"
test -d "$task_original"
test -d "$task_assets"
task_auth="${XAUTHORITY:-$HOME/.Xauthority}"
test -f "$task_auth"
test "$(docker image inspect --format '{{.Id}}' dosgolem-go-ebiten:1.24-r1)" = sha256:8ed6bdee2bce1f32f804e888f942b25bbf62f2165a43344bb4587f3371de0581
exec timeout -k 10s 1800s docker run --rm --init --network none --read-only \
 --user "$task_uid:$task_gid" --memory 3g --cpus 2 --pids-limit 192 \
 --tmpfs /tmp:rw,exec,size=512m -e HOME=/tmp -e DISPLAY -e XAUTHORITY=/x11-auth \
 -e LIBGL_ALWAYS_SOFTWARE=1 -e LP_NUM_THREADS=1 -e GOMAXPROCS=2 \
 --mount "type=bind,src=/tmp/.X11-unix,dst=/tmp/.X11-unix,readonly" \
 --mount "type=bind,src=$task_auth,dst=/x11-auth,readonly" \
 --mount "type=bind,src=$task_work,dst=/prototype,readonly" \
 --mount "type=bind,src=$task_session,dst=/session" \
 --mount "type=bind,src=$task_original,dst=/game,readonly" \
 --mount "type=bind,src=$task_original,dst=/project/workplace/intake-20261023/sources/game/8sword,readonly" \
 --mount "type=bind,src=$task_assets,dst=/assets,readonly" \
 dosgolem-go-ebiten:1.24-r1 /prototype/reinforcement-ui -root /game -assets /assets \
 -input /prototype/inputs -ui-assets /prototype/ui-assets -session /session -scratch /tmp/native-shadow
