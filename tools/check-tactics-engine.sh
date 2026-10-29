#!/usr/bin/env bash
# Run inside the pinned Go container with /project, /dosgolem, /candidate, /out.
set -euo pipefail
test -f /.dockerenv
test "$(id -u)" = 1000
printf 'go 1.24.0\nuse (\n /candidate/src\n /dosgolem\n)\n' > /tmp/go.work
export GOWORK=/tmp/go.work
cd /candidate/src
export EIGHTSWORD_TEST_ORIG=/project/workplace/intake-20261023/sources/game/8sword
export EIGHTSWORD_POLICY_TEST_BATCH=/project/workplace/probe-20261023/graphics-first/battle-r1
export EIGHTSWORD_AI_ENGINE_OUT=/out/engine-runtime-r3
export EIGHTSWORD_AI_FORMATION_BATCH=$EIGHTSWORD_POLICY_TEST_BATCH/ai-formation-r1/original-r2
export EIGHTSWORD_RULE_CALLS=$EIGHTSWORD_POLICY_TEST_BATCH/formation-hooks-r1/calls-r2
export EIGHTSWORD_RULE_OUT=/out/rules-runtime-r3
export EIGHTSWORD_TEST_POSTER_ASSETS=/project/workplace/player/assets-painted-r68
export EIGHTSWORD_TACTICS_HELPERS=$EIGHTSWORD_POLICY_TEST_BATCH/tactics-r1/helpers-r1-calls
export EIGHTSWORD_TACTICS_BATTLES=$EIGHTSWORD_POLICY_TEST_BATCH/tactics-r1/battles-r1-calls
mkdir "$EIGHTSWORD_AI_ENGINE_OUT" "$EIGHTSWORD_RULE_OUT"
go test -count=1 -v ./internal/eightsword -run '^(TestBattleAI|TestBattleRules|TestBattleTactics|TestRulesMarker|TestRuleSelection|TestPoster)' > /out/tests-r3.log 2>&1
EIGHTSWORD_TEST_POSTER_ASSETS=/project/workplace/player/assets-painted-r67 go test -count=1 -v ./internal/eightsword -run '^TestPoster' > /out/tests-r67-r3.log 2>&1
go vet ./internal/eightsword ./cmd/8sword ./cmd/8sword-replay > /out/vet-r3.log 2>&1
go build -mod=readonly -o /candidate/8sword ./cmd/8sword
go build -mod=readonly -o /candidate/8sword-replay ./cmd/8sword-replay
for tool in gui-check music-check heroine-check museum-check story-prelude-check; do go build -mod=readonly -o "/candidate/$tool" "./tools/$tool.go"; done
go build -mod=readonly -o /out/gui-driver-r1/tactics-gui-check /out/gui-driver-r1/tactics-gui-check.go
go version > /candidate/build-go-version.txt
sha256sum -c /candidate/build-inputs.sha256 > /candidate/build-source-checks.log
cd /candidate
sha256sum 8sword 8sword-replay gui-check music-check heroine-check museum-check story-prelude-check > build-outputs.sha256
