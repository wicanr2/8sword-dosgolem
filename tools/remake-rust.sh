#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_crate="$task_root/internal/remake-rust"
task_work="$task_root/workplace/probe-20261023/graphics-first/battle-r1/rust-battle-core-r1"
test -d "$task_crate"; test -d "$task_work"
test -d "$task_work/native"
[[ "$(id -u)" == 1000 ]]
test "$(docker image inspect --format '{{.Id}}' rust:1.99.1-slim-bookworm)" = sha256:24707e70a4f1e23d9a7b25202ec43126d28a52294b96aad5c670df1fd1f1d400
test "$(docker image inspect --format '{{.Id}}' mm45-rust-desktop:1.99.1-r3)" = sha256:ac10129fb2667f9be114a19db5b7a3837ba1a4457627420aec3044792715b8e1
timeout -k 5s 30s docker run --rm --init --network none --user "$(id -u):$(id -g)" --memory 512m --cpus 1 --pids-limit 64 \
 --mount "type=bind,src=$task_crate,dst=/crate,readonly" -w /crate mm45-rust-desktop:1.99.1-r3 cargo fmt --check
exec timeout -k 10s 120s docker run --rm --init --network none --user "$(id -u):$(id -g)" --memory 1g --cpus 2 --pids-limit 96 \
 --mount "type=bind,src=$task_crate,dst=/crate,readonly" --mount "type=bind,src=$task_work/native,dst=/out" \
 -e CARGO_TARGET_DIR=/out/rust-target -w /crate rust:1.99.1-slim-bookworm sh -c \
 'set -eu; test ! -e /game; test ! -e /core; test ! -e /gomodcache; cargo test --offline --locked > /out/tests-rust-r1.log 2>&1; cat /out/tests-rust-r1.log; cargo run --offline --locked --bin 8sword-remake -- --self-check > /out/cli-r1.log 2>&1; cat /out/cli-r1.log'
