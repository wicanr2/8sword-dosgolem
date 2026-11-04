package ownedworld

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"testing"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func TestOriginalGuardSessionWorld(t *testing.T) {
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
	parent := filepath.Join(work, "sessions-r1")
	must(os.MkdirAll(parent, 0700))
	name := os.Getenv("EIGHTSWORD_SESSION_CASE")
	if name == "" {
		name = "hd-native-go"
	}
	native := name == "hd-native-control"
	mixed := name == "hd-mixed-go"
	dir := filepath.Join(parent, name)
	must(os.Mkdir(dir, 0700))
	session := filepath.Join(dir, "session")
	must(importNativeProgress(root, root, session, filepath.Join(work, "inputs"), catalog, combat))
	store, snap, err := openProgressPair(session, catalog, combat)
	must(err)
	defer store.Close()
	player := [6]ArmyStack{{"native:01", 1000}, {"native:03", 200}}
	if mixed {
		player[2] = ArmyStack{"openkb:wolf", 20}
		player[3] = ArmyStack{"openkb:arcr", 20}
	}
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
	e.Oracle.WriteU16(oracle.Far(0x1e88, 0x8e12), 6)
	e.Oracle.WriteU16(oracle.Far(0x1e88, 0x8e44), 4)
	var owner *originalBattleGuard
	var lifecycle *originalBattleSession
	var checkpoint *nativeCheckpointPort
	if !native {
		owner, _ = originalGuardControllers(t, e, port, player)
		lifecycle, err = installOriginalBattleSession(owner)
		must(err)
		checkpoint, err = installNativeCheckpoint(e, port, filepath.Join(dir, "scratch"))
		must(err)
	} else {
		injected := false
		e.Oracle.OnCall(oracle.Far(0x110, 0x32e0), func(o *oracle.Oracle) {
			if injected {
				return
			}
			injected = true
			for i, row := range player {
				p := combat.Profiles[row.Unit]
				o.WriteU16(oracle.Far(0x1e88, 0x54a+uint16(i*4)), p.NativeKind)
				o.WriteU16(oracle.Far(0x1e88, 0x54c+uint16(i*4)), uint16(row.Count))
			}
		})
	}
	rows := []map[string]any{}
	for i, phase := range []string{"cancel", "retreat", "win"} {
		if i > 0 {
			setupPress(t, e, 0x4d)
		}
		before, er := store.Recover()
		must(er)
		err = originalGuardRun(t, e, phase == "retreat", owner, 300000000, phase == "cancel")
		if !errors.Is(err, errOriginalGuardMapHeld) {
			must(e.Oracle.SaveStateFile(filepath.Join(dir, phase+"-failed.state")))
			d := map[string]any{"error": fmt.Sprint(err), "regs": e.Oracle.Regs()}
			if owner != nil {
				d["events"] = owner.Events
				d["rounds"] = owner.Rounds.Rows
				d["session"] = lifecycle.Last
			}
			setupWrite(t, filepath.Join(dir, phase+"-failed.json"), d)
			t.Fatal("session", phase, err)
		}
		e.ReleaseAll()
		setupAdvance(t, e, 500)
		endingFrame(t, e, filepath.Join(dir, phase+".png"))
		resources := [6]uint16{}
		for i := range resources {
			resources[i] = e.Oracle.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))
		}
		saved, er := store.Recover()
		must(er)
		row := map[string]any{"phase": phase, "resources": resources, "NPC_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x365e), 1008)), "swords_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x275a), 16)), "seed": originalSeed(e.Oracle), "frame_rgba_sha256": contentSHA(e.Frame().Pix)}
		if !native {
			if lifecycle.Returns != uint64(i+1) || lifecycle.Cancels != 1 || lifecycle.Last.Cancelled != (phase == "cancel") {
				t.Fatal("session counter", lifecycle.Last)
			}
			if phase == "cancel" && saved.Token != before.Token {
				t.Fatal("cancel committed")
			}
			if phase != "cancel" && saved.World.Revision != before.World.Revision+1 {
				t.Fatal("battle commit count")
			}
			row["outcome"] = lifecycle.Last
			row["events"] = owner.Events
			row["actions"] = len(owner.Rounds.History)
			row["world_sha256"] = worldDigest(saved.World)
		} else {
			row["native_army_hex"] = fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24))
		}
		rows = append(rows, row)
		must(e.Oracle.SaveStateFile(filepath.Join(dir, phase+".state")))
	}
	if !native {
		// Revisit the cleared map tile through its original empty-guard message.
		beforeVisit, er := store.Recover()
		must(er)
		setupPress(t, e, 0x4d)
		err = originalGuardRun(t, e, false, owner, 30000000, true)
		if !errors.Is(err, errOriginalGuardMapHeld) {
			t.Fatal("cleared visit", err)
		}
		e.ReleaseAll()
		setupAdvance(t, e, 500)
		afterVisit, er := store.Recover()
		must(er)
		if lifecycle.Returns != 4 || lifecycle.Visits != 1 || lifecycle.Cancels != 1 || !lifecycle.Last.ClearedVisit || afterVisit.Token != beforeVisit.Token || len(owner.Rounds.History) != 0 {
			t.Fatal("cleared guard reopened")
		}
		setupPress(t, e, 0x41)
		setupPress(t, e, 0x1c)
		setupPress(t, e, 0x1c)
		setupAdvance(t, e, 700)
		e.ReleaseAll()
		if checkpoint.Saves != 1 {
			t.Fatal("session F7", checkpoint.Saves)
		}
		saved, er := store.Recover()
		must(er)
		setupWrite(t, filepath.Join(dir, "saved.json"), map[string]any{"world_sha256": worldDigest(saved.World), "token": saved.Token, "saves": checkpoint.Saves, "army": saved.World.Army.Slots, "resources": pairWorldResources(saved.World), "location": checkpointLocation(e.Oracle), "cleared_revisit_no_battle": true})
	}
	setupWrite(t, filepath.Join(dir, "receipt.json"), map[string]any{"case": name, "phases": rows, "player": player, "controlled_position": [2]uint16{6, 4}, "same_engine": true, "native_guard_unmodified": true, "actual_window": false})
}

func TestOriginalEndingCheckpointModels(t *testing.T) {
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
	dir := filepath.Join(work, "session-ending-model-store")
	must(importNativeProgress(root, root, dir, filepath.Join(work, "inputs"), catalog, combat))
	store, base, err := openProgressPair(dir, catalog, combat)
	must(err)
	defer store.Close()
	base.Bytes.Native = bytes.Clone(base.Bytes.Native)
	for i := 0; i < 8; i++ {
		at := 1318 + i*4
		binary.LittleEndian.PutUint16(base.Bytes.Native[at:], uint16(at+4))
	}
	full, err := originalEndingCheckpoint(base.Bytes.Native)
	must(err)
	models := []map[string]any{}
	for n := 1; n <= 6; n++ {
		p := base
		p.Bytes.Native = bytes.Clone(base.Bytes.Native)
		want := full
		for i := n; i < 6; i++ {
			want[i] = ArmyStack{}
			for j := 0; j < 2; j++ {
				at := 1604 + i*4 + j*2
				binary.LittleEndian.PutUint16(p.Bytes.Native[at:], uint16(at+3))
			}
		}
		rows, er := originalEndingCheckpoint(p.Bytes.Native)
		must(er)
		if rows != want {
			t.Fatal("partial ending roster", n)
		}
		must(originalEndingRecord(p, WorldEncounter{Enemy: rows, Cleared: true}))
		models = append(models, map[string]any{"living_rows": n, "rows": rows})
	}
	refused := 0
	for _, name := range []string{"empty", "ghost-count", "ghost-kind", "unknown-kind", "wide", "gap", "history"} {
		p := base
		p.Bytes.Native = bytes.Clone(base.Bytes.Native)
		rec := WorldEncounter{Enemy: full, Cleared: true}
		set := func(row, part int, v uint16) {
			at := 1604 + row*4 + part*2
			binary.LittleEndian.PutUint16(p.Bytes.Native[at:], v+uint16(at+3))
		}
		switch name {
		case "empty":
			for i := 0; i < 6; i++ {
				set(i, 0, 0)
				set(i, 1, 0)
			}
		case "ghost-count":
			set(0, 0, 0)
		case "ghost-kind":
			set(0, 1, 0)
		case "unknown-kind":
			set(0, 0, 26)
		case "wide":
			set(0, 1, 32768)
		case "gap":
			set(0, 0, 0)
			set(0, 1, 0)
		case "history":
			rec.Enemy[0].Count--
		}
		if originalEndingRecord(p, rec) == nil {
			t.Fatal("unsafe ending checkpoint", name)
		}
		refused++
	}
	// A later victory without F7 must retain the earlier checkpoint roster,
	// rather than replacing replay history with the depleted current guard.
	scratch := filepath.Join(work, "session-ending-model-scratch")
	must(materializeNativeCheckpoint(root, filepath.Join(work, "inputs"), scratch, base))
	files, err := readNativeCheckpointMaps(scratch)
	must(err)
	base, err = store.CommitCheckpoint(base.Token, base.Bytes.Native, files)
	must(err)
	depleted := [6]ArmyStack{}
	copy(depleted[:], full[2:])
	w := cloneCampWorld(base.World)
	w.Revision++
	w.Encounters["guarded:00:04"] = WorldEncounter{Enemy: depleted}
	base, err = store.Commit(base.Token, w)
	must(err)
	g := &originalBattleGuard{Ending: true, Guard: &guardedBinding{Context: EncounterContext{Region: 0, Index: 4}, Rows: depleted}, Before: base, Port: &worldArmyPort{Store: store, Current: base}, Projection: &originalArmyProjection{Remaining: base.World.Army.Slots}, Rounds: &originalBattleRounds{Result: "win"}, Expected: pairWorldResources(base.World).words()}
	_, err = g.commitWorld()
	must(err)
	saved, err := store.Recover()
	must(err)
	rec := saved.World.Encounters["guarded:00:04"]
	if !rec.Cleared || rec.Enemy != full {
		t.Fatal("final victory replaced checkpoint history")
	}
	must(originalEndingRecord(saved, rec))
	setupWrite(t, filepath.Join(work, "session-ending-models.json"), map[string]any{"models": models, "refusals": refused, "no_F7_depleted_victory_retains_checkpoint": true, "schema_unchanged": true})
}

func TestOriginalSessionRearmModels(t *testing.T) {
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
	pam, err := os.ReadFile(filepath.Join(work, "inputs/PAM.AY"))
	must(err)
	code, err := worldArmyCode(pam)
	must(err)
	dir := filepath.Join(work, "session-rearm-model-store")
	must(importNativeProgress(root, root, dir, filepath.Join(work, "inputs"), catalog, combat))
	store, base, err := openProgressPair(dir, catalog, combat)
	must(err)
	defer store.Close()
	w := cloneCampWorld(base.World)
	w.Revision++
	w.Army.Slots = [6]ArmyStack{{"native:01", 31}}
	base, err = store.Commit(base.Token, w)
	must(err)
	names := []string{"source", "caller", "not-returned", "round", "casualty", "spell", "enemy", "clone", "resource", "NPC", "swords", "shadow", "coordinates", "valid"}
	for _, name := range names {
		m, _ := actionFixture(t, code, combat, [2][6]ArmyStack{{{"native:01", 30}}, {{"native:06", 30}}})
		m.CPU.Seg[dg.CS] = 0x110
		m.CPU.IP = 0x2dde
		m.CPU.R[dg.SP] = 0xee10
		m.CPU.R[dg.BP] = 0xabcd
		m.Write16(0x1e880+0xee10, 0x25ee)
		m.Write16(0x1e880+0xee12, 0x110)
		npc, er := originalGuardNPC(base.Bytes.Native)
		must(er)
		flags, er := originalGuardFlags(base.Bytes.Native)
		must(er)
		copy(m.Mem[0x1e880+0x365e:], npc[:])
		copy(m.Mem[0x1e880+0x275a:], flags[:])
		for i, v := range pairWorldResources(base.World).words() {
			m.Write16(0x1e880+0x4f2+uint32(i*2), uint16(v))
		}
		for i := 0; i < 12; i++ {
			at := 12 + i*2
			m.Write16(0x1e880+0x54a+uint32(i*2), binary.LittleEndian.Uint16(base.Bytes.Native[at:])-uint16(at+3))
		}
		m.Write16(0x1e880+0x56d6, 0)
		m.Write16(0x1e880+0x8e12, 5)
		m.Write16(0x1e880+0x8e44, 4)
		for i, v := range guardedCoordinates[0] {
			m.Write16(0x1e880+0x8c30+uint32(i*4), v[0])
			m.Write16(0x1e880+0x8c32+uint32(i*4), v[1])
		}
		for i, v := range swordBossCoordinates {
			m.Write16(0x1e880+0x26bc+uint32(i*6), v[0])
			m.Write16(0x1e880+0x26be+uint32(i*6), v[1])
		}
		oldPlayer := [6]ArmyStack{{"native:01", 30}}
		setup := &originalBattleSetup{Code: code, Catalog: combat, Override: &oldPlayer, Phase: "ready"}
		a := &originalBattleActions{Setup: setup}
		c := &originalBattleCasualties{Actions: a}
		a.Casualties = c
		r := &originalBattleRounds{Actions: a, Done: true, Released: true, Sorting: -1}
		a.Rounds = r
		setup.Actions = a
		p := &originalBattleSpells{Rounds: r, Selector: 6, Consumed: true}
		u := &originalBattleSupport{Spells: p, Growth: [6]uint32{30}}
		p.Support = u
		e := &originalBattleEnemy{Rounds: r, Mask: 63}
		r.Spells = p
		r.EnemySpells = e
		x := &originalArmyProjection{Code: code, Catalog: combat, Rounds: r, HeldPreview: true, Phase: "captured", Captures: 1, Entries: 1}
		g := &originalBattleGuard{Port: &worldArmyPort{Store: store, Current: base}, Code: code, Projection: x, Rounds: r, Returned: true, Active: true, Captured: true, Committed: true, CommittedToken: base.Token}
		s := &originalBattleSession{Guard: g, Returns: 1}
		g.Session = s
		switch name {
		case "source":
			m.Mem[0x1100+0x2dde] ^= 1
		case "caller":
			m.Write16(0x1e880+0xee10, 0x171d)
		case "not-returned":
			g.Returned = false
		case "round":
			r.Active = true
		case "casualty":
			c.Started = true
		case "spell":
			p.Active = true
		case "enemy":
			e.Active = true
		case "clone":
			u.Clone = &originalCloneRecord{}
		case "resource":
			m.Mem[0x1e880+0x4f8] ^= 1
		case "NPC":
			m.Mem[0x1e880+0x365e] ^= 1
		case "swords":
			m.Mem[0x1e880+0x275a] ^= 1
		case "shadow":
			m.Mem[0x1e880+0x54a] ^= 1
		case "coordinates":
			m.Write16(0x1e880+0x8e12, 4)
		}
		before := bytes.Clone(m.Mem)
		regs, ip, cycles, cf := m.CPU.R, m.CPU.IP, m.CPU.Cycles, m.CPU.Flags
		state := fmt.Sprint(x.Phase, setup.Phase, r.Done, r.Released, r.Active, c.Started, p.Active, p.Consumed, e.Active, e.Mask, u.Growth, g.Returned)
		err = s.rearm(m)
		if (err == nil) != (name == "valid") {
			t.Fatal("rearm", name, err)
		}
		if !bytes.Equal(before, m.Mem) || regs != m.CPU.R || ip != m.CPU.IP || cycles != m.CPU.Cycles || cf != m.CPU.Flags {
			t.Fatal("rearm changed guest", name)
		}
		if name != "valid" {
			if state != fmt.Sprint(x.Phase, setup.Phase, r.Done, r.Released, r.Active, c.Started, p.Active, p.Consumed, e.Active, e.Mask, u.Growth, g.Returned) {
				t.Fatal("refusal changed controllers", name)
			}
		} else if x.Input != base.World.Army.Slots || *setup.Override != x.Input || x.Phase != "" || setup.Phase != "" || r.Done || r.Released || p.Consumed || p.Selector != -1 || e.Mask != 0 || u.Growth != [6]uint32{} || g.Returned || x.Rounds != r || r.Actions != a || a.Casualties != c || p.Support != u || g.Session != s {
			t.Fatal("rearm retained old state")
		}
	}
	setupWrite(t, filepath.Join(work, "session-rearm-models.json"), map[string]any{"refusals": 13, "refusals_preserve_controllers_and_guest": true, "valid_rearm_preserves_guest_and_hook_pointers": true, "latest_army_loaded": 31, "old_spell_growth_enemy_state_cleared": true})
}
