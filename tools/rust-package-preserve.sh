#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source "$task_root/tools/rust-package-defaults.env"
task_version="${EIGHTSWORD_PACKAGE_VERSION:-$EIGHTSWORD_DEFAULT_VERSION}"
task_batch="${EIGHTSWORD_PACKAGE_BATCH:-$EIGHTSWORD_DEFAULT_BATCH}"
[[ "$task_version" =~ ^v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}$ ]]
[[ "$task_batch" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]
task_action="${1:-verify}"
case "$task_action" in prepare|audit|archive|verify|restore|restore-native) ;; *) exit 2 ;; esac
test -d "$task_root/preserved"; test -d "$task_root/tools"; test "$(id -u)" = 1000
exec timeout -k 10s 620s docker run --rm --init --network none --user "$(id -u):$(id -g)" --memory 3g --cpus 2 --pids-limit 128 \
 -e "EIGHTSWORD_PACKAGE_VERSION=$task_version" -e "EIGHTSWORD_PACKAGE_BATCH=$task_batch" --label "org.wicanr2.project=$task_batch" --mount "type=bind,src=$task_root,dst=/r" \
 sc-cht-hdtools:pillow11.3.0-r2 timeout 600 python3 /r/tools/rust-package-delivery.py "$task_action" --project /r
