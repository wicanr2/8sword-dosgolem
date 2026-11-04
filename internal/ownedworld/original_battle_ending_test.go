package ownedworld

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"image/png"
	"os"
	"path/filepath"
	"testing"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func TestOriginalEndingGuards(t *testing.T) {
	work, _, catalog := setupInputs(t)
	pam, err := os.ReadFile(filepath.Join(work, "inputs/PAM.AY"))
	if err != nil {
		t.Fatal(err)
	}
	code, err := worldArmyCode(pam)
	if err != nil {
		t.Fatal(err)
	}
	names := []string{"source", "segment", "frame", "NPC", "shadow", "resources", "missing-sword", "inactive", "not-captured", "non-final", "awarded", "enemy-alive", "not-released", "not-win", "capture-count", "stack"}
	for _, name := range names {
		m, _ := actionFixture(t, code, catalog, [2][6]ArmyStack{{{"native:01", 30}}, {{"native:06", 30}}})
		m.CPU.Seg[dg.CS] = 0x110
		m.CPU.IP = 0x329b
		m.CPU.R[dg.BP] = 0xee00
		m.CPU.R[dg.SP] = 0xedd0
		m.Write16(0x1e880+0xee00, 0xeb00)
		m.Write16(0x1e880+0xee02, 0x25ee)
		m.Write16(0x1e880+0xee04, 0x110)
		m.Write16(0x1e880+0x56e2, 1)
		clear(m.Mem[0x1e880+0x36be : 0x1e880+0x36d6])
		for i := 0; i < 8; i++ {
			m.Write16(0x1e880+0x275a+uint32(i*2), 1)
		}
		g := &originalBattleGuard{Code: code, Ending: true, Active: true, Captured: true, EntrySP: 0xee02, EntryBP: 0xeb00, Guard: &guardedBinding{Context: EncounterContext{Region: 0, Index: 4}}, Rounds: &originalBattleRounds{Done: true, Released: true, Result: "win"}, Projection: &originalArmyProjection{EntrySP: 0xedcc, Captures: 1}}
		copy(g.NPC[:], m.Mem[0x1e880+0x365e:0x1e880+0x3a4e])
		copy(g.Flags[:], m.Mem[0x1e880+0x275a:0x1e880+0x276a])
		copy(g.Shadow[:], m.Mem[0x1e880+0x54a:0x1e880+0x562])
		for i := range g.Expected {
			g.Expected[i] = uint64(m.Read16(0x1e880 + 0x4f2 + uint32(i*2)))
		}
		switch name {
		case "source":
			m.Mem[0x1100+0x2dde] ^= 1
		case "segment":
			m.CPU.Seg[dg.DS]++
		case "frame":
			m.CPU.R[dg.BP]--
		case "NPC":
			m.Mem[0x1e880+0x365e] ^= 1
		case "shadow":
			m.Mem[0x1e880+0x54a] ^= 1
		case "resources":
			m.Mem[0x1e880+0x4f8] ^= 1
		case "missing-sword":
			m.Write16(0x1e880+0x275a, 0)
			g.Flags[0] = 0
		case "inactive":
			g.Active = false
		case "not-captured":
			g.Captured = false
		case "non-final":
			g.Guard.Context.Index = 0
		case "awarded":
			g.Monthly = true
		case "enemy-alive":
			g.Enemy[0] = ArmyStack{"native:19", 1}
		case "not-released":
			g.Rounds.Released = false
		case "not-win":
			g.Rounds.Result = "retreat"
		case "capture-count":
			g.Projection.Captures = 2
		case "stack":
			m.CPU.R[dg.SP]--
		}
		before := bytes.Clone(m.Mem)
		regs, flags, ip, cycles := m.CPU.R, m.CPU.Flags, m.CPU.IP, m.CPU.Cycles
		if _, err := g.endingPrepare(m); err == nil {
			t.Fatal("unsafe ending", name)
		}
		if !bytes.Equal(before, m.Mem) || regs != m.CPU.R || flags != m.CPU.Flags || ip != m.CPU.IP || cycles != m.CPU.Cycles || g.Committed || g.EndingPrepared || len(g.Events) != 0 {
			t.Fatal("ending refusal mutated", name)
		}
	}
	setupWrite(t, filepath.Join(work, "ending-guards.json"), map[string]any{"refusals": len(names), "state_unchanged": true})
}

func TestOriginalEndingRecords(t *testing.T) {
	work, root, combat := setupInputs(t)
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	var catalog ArmyCatalog
	raw, err := os.ReadFile(filepath.Join(work, "inputs/army-catalog.json"))
	must(err)
	must(pairStrictJSON(raw, &catalog))
	dir := filepath.Join(work, "ending-record-store")
	must(importNativeProgress(root, root, dir, filepath.Join(work, "inputs"), catalog, combat))
	store, base, err := openProgressPair(dir, catalog, combat)
	must(err)
	native := bytes.Clone(base.Bytes.Native)
	for i := 0; i < 8; i++ {
		at := 1318 + i*4
		binary.LittleEndian.PutUint16(native[at:], uint16(at+4))
	}
	scratch := filepath.Join(work, "ending-record-scratch")
	must(materializeNativeCheckpoint(root, filepath.Join(work, "inputs"), scratch, base))
	files, err := readNativeCheckpointMaps(scratch)
	must(err)
	base, err = store.CommitCheckpoint(base.Token, native, files)
	must(err)
	var rows [6]ArmyStack
	for i := range rows {
		k, err := guardSavedWord(base.Bytes.Native, guardNPCAt(0, 4)+i*4)
		must(err)
		n, err := guardSavedWord(base.Bytes.Native, guardNPCAt(0, 4)+i*4+2)
		must(err)
		rows[i] = ArmyStack{fmt.Sprintf("native:%02d", k), uint32(n)}
	}
	w := cloneCampWorld(base.World)
	w.Revision++
	w.Encounters["guarded:00:04"] = WorldEncounter{Enemy: rows, Cleared: true}
	store.Fault = func(phase string) error {
		if phase == "intent-durable" {
			return errors.New("controlled ending interruption")
		}
		return nil
	}
	_, err = store.Commit(base.Token, w)
	if !errors.Is(err, errPairPending) {
		t.Fatal("ending journal", err)
	}
	store.Close()
	store, recovered, err := openProgressPair(dir, catalog, combat)
	must(err)
	defer store.Close()
	if worldDigest(recovered.World) != worldDigest(w) {
		t.Fatal("ending journal recovery")
	}
	projected, err := originalGuardOverlayMode(recovered, true)
	must(err)
	if !bytes.Equal(projected, recovered.Bytes.Native) {
		t.Fatal("ending replay did not preserve opaque checkpoint")
	}
	if _, err = originalGuardOverlay(recovered); err == nil {
		t.Fatal("ordinary mode accepted final")
	}
	for i := 0; i < 8; i++ {
		p := recovered
		p.Bytes.Native = bytes.Clone(recovered.Bytes.Native)
		at := 1318 + i*4
		binary.LittleEndian.PutUint16(p.Bytes.Native[at:], uint16(at+3))
		if _, err = originalGuardOverlayMode(p, true); err == nil {
			t.Fatal("ending receipt missing sword", i)
		}
	}
	for i := range rows {
		p := recovered
		p.World = cloneCampWorld(recovered.World)
		rec := p.World.Encounters["guarded:00:04"]
		rec.Enemy[i].Count++
		p.World.Encounters["guarded:00:04"] = rec
		if _, err = originalGuardOverlayMode(p, true); err == nil {
			t.Fatal("ending receipt wrong roster", i)
		}
	}
	// Last-sword wins need not have reached F7 before the final battle.
	p := recovered
	p.World = cloneCampWorld(recovered.World)
	p.Bytes.Native = bytes.Clone(recovered.Bytes.Native)
	for region, index := range swordBossIndex {
		at := 1318 + region*4
		binary.LittleEndian.PutUint16(p.Bytes.Native[at:], uint16(at+3))
		var enemy [6]ArmyStack
		for i := range enemy {
			k, er := guardSavedWord(p.Bytes.Native, guardNPCAt(region, int(index))+i*4)
			must(er)
			n, er := guardSavedWord(p.Bytes.Native, guardNPCAt(region, int(index))+i*4+2)
			must(er)
			if k != 0 {
				enemy[i] = ArmyStack{fmt.Sprintf("native:%02d", k), uint32(n)}
			}
		}
		p.World.Encounters[fmt.Sprintf("guarded:%02d:%02d", region, index)] = WorldEncounter{Enemy: enemy, Cleared: true}
	}
	overlay, er := originalGuardOverlayMode(p, true)
	must(er)
	flags, er := savedSwords(overlay)
	must(er)
	for _, v := range flags {
		if !v {
			t.Fatal("Go boss-record sword not restored")
		}
	}
	again, err := store.Recover()
	must(err)
	if again.Token != recovered.Token {
		t.Fatal("ending recovery not idempotent")
	}
	setupWrite(t, filepath.Join(work, "ending-records.json"), map[string]any{"refusals": 15, "opaque_checkpoint_preserved": true, "boss_records_supply_swords": true, "interrupted_commit_recovered": true, "recovery_idempotent": true, "enemy": rows})
}

func endingFrame(t *testing.T, e *game.Engine, path string) {
	t.Helper()
	f, err := os.Create(path)
	if err != nil {
		t.Fatal(err)
	}
	if err = png.Encode(f, e.Frame()); err != nil {
		t.Fatal(err)
	}
	if err = f.Close(); err != nil {
		t.Fatal(err)
	}
}

func originalEndingFinish(t *testing.T, e *game.Engine, dir string) {
	t.Helper()
	seen := map[string]bool{}
	for i := 0; i < 50000 && !e.Exited; i++ {
		if err := catchWorldArmyFault(func() error { return e.AdvanceCycles(30000) }); err != nil {
			t.Fatal(err)
		}
		e.RenderAudio()
		s := e.EndingStatus()
		stage, _ := s["stage"].(string)
		if stage != "" && (!seen[stage] || i%100 == 0) {
			seen[stage] = true
			endingFrame(t, e, filepath.Join(dir, stage+".png"))
		}
	}
	if !e.Exited || e.ExitCode != 0 || !seen["END7.AY"] {
		t.Fatal("ending incomplete", e.Exited, e.ExitCode, e.EndingStatus(), seen)
	}
	setupWrite(t, filepath.Join(dir, "playback.json"), map[string]any{"exit_code": e.ExitCode, "ending": e.EndingStatus(), "stages": seen, "gameplay_hooks_disabled": swordGameplayEnded})
}

func TestOriginalEndingWorld(t *testing.T) {
	work, root, combat := setupInputs(t)
	assets := os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if assets == "" {
		t.Skip("assets")
	}
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	var catalog ArmyCatalog
	raw, err := os.ReadFile(filepath.Join(work, "inputs/army-catalog.json"))
	must(err)
	must(pairStrictJSON(raw, &catalog))
	parent := filepath.Join(work, "ending-r1")
	must(os.MkdirAll(parent, 0700))
	name := os.Getenv("EIGHTSWORD_ENDING_CASE")
	if name == "" {
		name = "hd-native-go"
	}
	dir := filepath.Join(parent, name)
	must(os.Mkdir(dir, 0700))
	swordGameplayEnded = false
	defer func() { swordGameplayEnded = false }()
	player := [6]ArmyStack{{"native:19", 1000}, {"native:20", 600}, {"native:25", 500}, {"native:03", 1000}, {"native:24", 600}, {"native:18", 20}}
	mixed := name == "hd-mixed-go"
	native := name == "hd-native-control"
	if mixed {
		player[5] = ArmyStack{"openkb:arcr", 20}
	}
	session := filepath.Join(dir, "session")
	must(importNativeProgress(root, root, session, filepath.Join(work, "inputs"), catalog, combat))
	store, snap, err := openProgressPair(session, catalog, combat)
	must(err)
	defer store.Close()
	w := snap.World
	w.Revision++
	w.Army.Slots = player
	w.Army.Leadership = 30000
	w.Progress.Merit = 10000
	if mixed {
		w.Army.Rules = "formation"
	}
	snap, err = store.Commit(snap.Token, w)
	must(err)
	port := &worldArmyPort{Store: store, Current: snap}
	must(materializeNativeCheckpoint(root, filepath.Join(work, "inputs"), filepath.Join(dir, "scratch"), snap))
	e := setupCold(t, root, assets, dir, true)
	defer e.Close()
	e.Oracle.WriteU16(oracle.Far(0x1e88, 0x8e12), 59)
	e.Oracle.WriteU16(oracle.Far(0x1e88, 0x8e44), 52)
	for i := 0; i < 8; i++ {
		e.Oracle.WriteU16(oracle.Far(0x1e88, 0x275a+uint16(i*2)), 1)
	}
	partial := name == "hd-partial-go"
	if partial {
		// Controlled checkpoint after a prior retreat: retain the original last
		// four native rows, compacted; do not inject a win or instruction pointer.
		raw := e.Oracle.Bytes(oracle.Far(0x1e88, 0x36be), 24)
		for i := 0; i < 6; i++ {
			kind, count := uint16(0), uint16(0)
			if i < 4 {
				kind = binary.LittleEndian.Uint16(raw[(i+2)*4:])
				count = binary.LittleEndian.Uint16(raw[(i+2)*4+2:])
			}
			e.Oracle.WriteU16(oracle.Far(0x1e88, 0x36be+uint16(i*4)), kind)
			e.Oracle.WriteU16(oracle.Far(0x1e88, 0x36c0+uint16(i*4)), count)
		}
	}
	cp, err := installNativeCheckpoint(e, port, filepath.Join(dir, "scratch"))
	must(err)
	setupPress(t, e, 0x41)
	setupPress(t, e, 0x1c)
	setupPress(t, e, 0x1c)
	setupAdvance(t, e, 700)
	e.ReleaseAll()
	if cp.Saves != 1 {
		t.Fatal("prebattle F7", cp.Saves)
	}
	before, err := store.Recover()
	must(err)
	var owner *originalBattleGuard
	var enemy *originalBattleEnemy
	if !native {
		owner, enemy = originalGuardControllersMode(t, e, port, player, true)
	} else {
		e.Oracle.OnCall(oracle.Far(0x110, 0x32e0), func(o *oracle.Oracle) {
			for i, row := range player {
				p := combat.Profiles[row.Unit]
				o.WriteU16(oracle.Far(0x1e88, 0x54a+uint16(i*4)), p.NativeKind)
				o.WriteU16(oracle.Far(0x1e88, 0x54c+uint16(i*4)), uint16(row.Count))
			}
		})
		swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0x020e), func(m *dg.Machine) (bool, error) {
			if m.Read16(0x1e880+uint32(m.CPU.R[dg.SP])) != 0x329f {
				return false, errors.New("native ending caller")
			}
			swordGameplayEnded = true
			return false, errOriginalGuardMapHeld
		})
	}
	opened := false
	e.Oracle.OnCall(oracle.Far(0xf67, 0x283e), func(*oracle.Oracle) {
		if !opened {
			opened = true
			endingFrame(t, e, filepath.Join(dir, "battle.png"))
		}
	})
	err = originalGuardFightLimit(t, e, false, owner, 1000000000)
	if !errors.Is(err, errOriginalGuardMapHeld) {
		must(e.Oracle.SaveStateFile(filepath.Join(dir, "failed.state")))
		d := map[string]any{"error": fmt.Sprint(err), "regs": e.Oracle.Regs()}
		if owner != nil {
			d["events"] = owner.Events
			d["rows"] = owner.Rounds.Rows
			d["history"] = owner.Rounds.History
			d["enemy"] = enemy.Records
		}
		setupWrite(t, filepath.Join(dir, "failed.json"), d)
		t.Fatal(err)
	}
	resources := [6]uint16{}
	for i := range resources {
		resources[i] = e.Oracle.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))
	}
	if resources != [6]uint16{1, 10000, 100, 500, 30000, 0} {
		t.Fatal("ending incorrectly awarded", resources)
	}
	receipt := map[string]any{"case": name, "player": player, "resources": resources, "NPC_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x365e), 1008)), "swords_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x275a), 16)), "seed": originalSeed(e.Oracle), "prebattle_F7_saves": cp.Saves, "controlled_position": [2]uint16{59, 52}, "native_guard_unmodified": !partial, "controlled_partial_checkpoint": partial, "controlled_swords": 8, "world_before": worldDigest(before.World)}
	receipt["native_returned_hex"] = fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x56e8), 24))
	if !native {
		if !owner.EndingHandoff || !owner.Committed || owner.Replay || owner.Rounds.Result != "win" {
			t.Fatal("handoff missing")
		}
		saved, er := store.Recover()
		must(er)
		if saved.World.Revision != before.World.Revision+1 {
			t.Fatal("ending commit count")
		}
		receipt["remaining"] = owner.Projection.Remaining
		receipt["enemy_initial"] = owner.Guard.Rows
		receipt["world_sha256"] = worldDigest(saved.World)
		receipt["token"] = saved.Token
		receipt["events"] = owner.Events
		receipt["actions"] = len(owner.Rounds.History)
		// This path deliberately stops before playback to exercise process cold replay.
	}
	must(e.Oracle.SaveStateFile(filepath.Join(dir, "handoff.state")))
	setupWrite(t, filepath.Join(dir, "receipt.json"), receipt)
}

func TestOriginalEndingCold(t *testing.T) {
	session, dir := os.Getenv("EIGHTSWORD_ENDING_COLD_SESSION"), os.Getenv("EIGHTSWORD_ENDING_COLD_OUT")
	if session == "" || dir == "" {
		t.Skip("explicit cold fixture")
	}
	work, root, combat := setupInputs(t)
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	var catalog ArmyCatalog
	raw, err := os.ReadFile(filepath.Join(work, "inputs/army-catalog.json"))
	must(err)
	must(pairStrictJSON(raw, &catalog))
	store, snap, err := openProgressPair(session, catalog, combat)
	must(err)
	defer store.Close()
	must(os.Mkdir(dir, 0700))
	must(materializeNativeCheckpoint(root, filepath.Join(work, "inputs"), filepath.Join(dir, "scratch"), snap))
	swordGameplayEnded = false
	defer func() { swordGameplayEnded = false }()
	e := setupCold(t, root, os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS"), dir, true)
	defer e.Close()
	port := &worldArmyPort{Store: store, Current: snap}
	owner, _ := originalGuardControllersMode(t, e, port, snap.World.Army.Slots, true)
	if e.Oracle.Word(oracle.Far(0x1e88, 0x8e12)) != 59 || e.Oracle.Word(oracle.Far(0x1e88, 0x8e44)) != 52 {
		t.Fatal("cold position")
	}
	err = originalGuardFightLimit(t, e, false, owner, 1000000000)
	if !errors.Is(err, errOriginalGuardMapHeld) {
		t.Fatal("cold replay", err)
	}
	if !owner.Replay || !owner.EndingHandoff || len(owner.Rounds.History) != 0 || owner.Rounds.Active {
		t.Fatal("replay repeated battle")
	}
	e.ReleaseAll()
	originalEndingFinish(t, e, dir)
	after, err := store.Recover()
	must(err)
	if after.Token != snap.Token || worldDigest(after.World) != worldDigest(snap.World) {
		t.Fatal("ending repeated transaction")
	}
	setupWrite(t, filepath.Join(dir, "receipt.json"), map[string]any{"status": "passed-original-ending-process-cold", "world_sha256": worldDigest(after.World), "token": after.Token, "events": owner.Events, "battle_actions": len(owner.Rounds.History), "snapshot_loaded": false, "separate_process": true, "exit_code": e.ExitCode})
}

func TestOriginalEndingMissingSwords(t *testing.T) {
	work, root, combat := setupInputs(t)
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	var catalog ArmyCatalog
	raw, err := os.ReadFile(filepath.Join(work, "inputs/army-catalog.json"))
	must(err)
	must(pairStrictJSON(raw, &catalog))
	dir := filepath.Join(work, "ending-missing-swords")
	must(os.Mkdir(dir, 0700))
	session := filepath.Join(dir, "session")
	must(importNativeProgress(root, root, session, filepath.Join(work, "inputs"), catalog, combat))
	store, snap, err := openProgressPair(session, catalog, combat)
	must(err)
	defer store.Close()
	must(materializeNativeCheckpoint(root, filepath.Join(work, "inputs"), filepath.Join(dir, "scratch"), snap))
	swordGameplayEnded = false
	defer func() { swordGameplayEnded = false }()
	e := setupCold(t, root, os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS"), dir, true)
	defer e.Close()
	port := &worldArmyPort{Store: store, Current: snap}
	owner, _ := originalGuardControllersMode(t, e, port, snap.World.Army.Slots, true)
	e.Oracle.WriteU16(oracle.Far(0x1e88, 0x8e12), 59)
	e.Oracle.WriteU16(oracle.Far(0x1e88, 0x8e44), 52)
	missing, entered := 0, 0
	e.Oracle.OnCall(oracle.Far(0x110, 0x3009), func(*oracle.Oracle) { missing++ })
	e.Oracle.OnCall(oracle.Far(0x110, 0x3048), func(*oracle.Oracle) { entered++ })
	setupPress(t, e, 0x4b)
	setupPress(t, e, 0x1c)
	setupPress(t, e, 0x1c)
	setupAdvance(t, e, 1500)
	if missing == 0 || entered != 0 || owner.Projection.Entries != 0 || owner.Committed || owner.EndingHandoff {
		t.Fatal("missing swords bypassed", missing, entered)
	}
	after, err := store.Recover()
	must(err)
	if after.Token != snap.Token {
		t.Fatal("missing swords wrote progress")
	}
	endingFrame(t, e, filepath.Join(dir, "rejected.png"))
	setupWrite(t, filepath.Join(dir, "receipt.json"), map[string]any{"original_warning_branch": missing, "battle_gate_entries": entered, "progress_unchanged": true, "ending_handoff": false})
}
