#!/usr/bin/env bash
# 由乾淨工作區重錄本機開發預覽。所有工作負載都在容器內。
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_work="$task_root/workplace/probe-20261023/graphics-first/battle-r1/rust-promo-r1"
task_native="$task_root/workplace/probe-20261023/graphics-first/battle-r1/rust-player-path-r1/native"
task_version=v.0.1.0-20261112
task_runtime=mm45-rust-desktop:1.99.1-r3
task_tools=sc-cht-hdtools:pillow11.3.0-r2
task_voice=rich2-narration:edge-tts7.3.1-20261101-r1
[[ "$(id -u)" == 1000 ]]
test -d "$task_native/pack"; test -f "$task_native/8sword-remake"
test -d "$(dirname -- "$task_work")"
test ! -e "$task_work/timeline.json"
test ! -e "$task_root/dist-all/$task_version/promo"
test "$(docker image inspect --format '{{.Id}}' "$task_runtime")" = sha256:ac10129fb2667f9be114a19db5b7a3837ba1a4457627420aec3044792715b8e1
test "$(docker image inspect --format '{{.Id}}' "$task_tools")" = sha256:b050fc7c49003ea6eecbbe0fc93b465b6869daf550c3284d5039e5e87517e831
test "$(docker image inspect --format '{{.Id}}' "$task_voice")" = sha256:cfad34b2da56da721c42a93d9802d345a85e5b3de1e0d49befc209a37ec3ef63
task_limits=(--rm --init --user "$(id -u):$(id -g)" --memory 3g --cpus 2 --pids-limit 128)
timeout -k 10s 60s docker run "${task_limits[@]}" --network none \
 --mount "type=bind,src=$task_root,dst=/r" \
 --mount "type=bind,src=$task_native,dst=/r/workplace/probe-20261023/graphics-first/battle-r1/rust-player-path-r1/native,readonly" \
 "$task_tools" python /r/tools/rust-promo.py prepare --project /r
test -d "$task_work/voice"
timeout -k 10s 180s docker run "${task_limits[@]}" --network bridge \
 --mount "type=bind,src=$task_work/voice,dst=/out" \
 --mount "type=bind,src=$task_root/tools/rust-promo.py,dst=/script.py,readonly" \
 "$task_voice" python3 /script.py voice --work /out
timeout -k 10s 40s docker run "${task_limits[@]}" --network none \
 --mount "type=bind,src=$task_work,dst=/out" \
 --mount "type=bind,src=$task_root/tools/rust-promo.py,dst=/script.py,readonly" \
 "$task_runtime" python3 /script.py plan --work /out
timeout -k 10s 360s docker run "${task_limits[@]}" --network none \
 --mount "type=bind,src=$task_native,dst=/runtime,readonly" \
 --mount "type=bind,src=$task_work,dst=/out" \
 --mount "type=bind,src=$task_root/tools/rust-promo-capture.py,dst=/script.py,readonly" \
 "$task_runtime" python3 /script.py
timeout -k 10s 40s docker run "${task_limits[@]}" --network none \
 --mount "type=bind,src=$task_work,dst=/out" \
 --mount "type=bind,src=$task_root/tools/rust-promo.py,dst=/script.py,readonly" \
 "$task_tools" python /script.py cards --work /out
for task_action in compose audit; do
 timeout -k 10s 600s docker run "${task_limits[@]}" --network none \
  --mount "type=bind,src=$task_root,dst=/r" \
  "$task_runtime" python3 /r/tools/rust-promo.py "$task_action" --project /r --version "$task_version"
done
timeout -k 10s 40s docker run "${task_limits[@]}" --network none \
 --mount "type=bind,src=$task_root,dst=/r" \
 "$task_tools" python /r/tools/rust-promo.py contact --project /r --out /r/docs/images/rust-promo-contact-r1.jpg
printf '%s\n' '技術核對完成。請逐鏡檢視contact-sheet與片頭／片尾後，再使用archive動作保存；不自動上傳或發布。'
