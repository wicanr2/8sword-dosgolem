#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_crate="$task_root/internal/remake-rust"
task_work="$task_root/workplace/probe-20261023/graphics-first/battle-r1/original-player-integration-r1"
test -d "$task_crate"; test -d "$task_work"
[[ "$(id -u)" == 1000 ]]
test "$(docker image inspect --format '{{.Id}}' rust:1.99.1-slim-bookworm)" = sha256:24707e70a4f1e23d9a7b25202ec43126d28a52294b96aad5c670df1fd1f1d400
exec timeout -k 10s 120s docker run --rm --init --network none --user "$(id -u):$(id -g)" --memory 1g --cpus 2 --pids-limit 96 \
 --mount "type=bind,src=$task_crate,dst=/crate,readonly" --mount "type=bind,src=$task_work,dst=/out" \
 -e CARGO_TARGET_DIR=/out/rust-target -w /crate rust:1.99.1-slim-bookworm sh -c \
 'set -eu; cargo test --offline --locked; cargo run --offline --locked --bin 8sword-remake -- --self-check'
