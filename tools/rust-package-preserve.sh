#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_action="${1:-verify}"
case "$task_action" in prepare|audit|archive|verify|restore) ;; *) exit 2 ;; esac
test -d "$task_root/preserved"; test -d "$task_root/tools"; test "$(id -u)" = 1000
exec timeout -k 10s 620s docker run --rm --init --network none --user "$(id -u):$(id -g)" --memory 3g --cpus 2 --pids-limit 128 \
 --label org.wicanr2.project=8sword-package-r1 --mount "type=bind,src=$task_root,dst=/r" \
 sc-cht-hdtools:pillow11.3.0-r2 timeout 600 python3 /r/tools/rust-package-delivery.py "$task_action" --project /r
