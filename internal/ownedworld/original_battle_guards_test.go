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

var errOriginalGuardMapHeld = errors.New("original guard map returned")

func originalGuardControllers(t *testing.T, e *game.Engine, p *worldArmyPort, player [6]ArmyStack) (*originalBattleGuard, *originalBattleEnemy) {
	return originalGuardControllersMode(t, e, p, player, false)
}
func originalGuardControllersMode(t *testing.T, e *game.Engine, p *worldArmyPort, player [6]ArmyStack, ending bool) (*originalBattleGuard, *originalBattleEnemy) {
	t.Helper()
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	x, err := installOriginalArmyProjectionMode(e, p.Store.Combat, player, true)
	must(err)
	s, err := installOriginalBattleSetup(e, p.Store.Combat, &player)
	must(err)
	a, err := installOriginalBattleActions(e, s, true)
	must(err)
	r, err := installOriginalBattleRounds(e, a)
	must(err)
	x.Rounds = r
	spells, err := installOriginalBattleSpells(e, r)
	must(err)
	_, err = installOriginalBattleSupport(e, spells)
	must(err)
	enemy, err := installOriginalBattleEnemy(e, r)
	must(err)
	g, err := installOriginalBattleGuardMode(e, p, x, r, ending)
	must(err)
	return g, enemy
}

func TestOriginalGuardCold(t *testing.T) {
	session, dir := os.Getenv("EIGHTSWORD_GUARD_COLD_SESSION"), os.Getenv("EIGHTSWORD_GUARD_COLD_OUT")
	if session == "" || dir == "" {
		t.Skip("explicit separate-process guard cold fixture")
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
	e := setupCold(t, root, os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS"), dir, os.Getenv("EIGHTSWORD_GUARD_COLD_HD") == "1")
	defer e.Close()
	port := &worldArmyPort{Store: store, Current: snap}
	originalGuardControllers(t, e, port, snap.World.Army.Slots)
	for i, v := range pairWorldResources(snap.World).words() {
		if uint64(e.Oracle.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != v {
			t.Fatal("guard cold resource", i)
		}
	}
	must(e.Oracle.SaveStateFile(filepath.Join(dir, "continued.state")))
	setupWrite(t, filepath.Join(dir, "receipt.json"), map[string]any{"status": "passed-original-guard-process-cold", "world_sha256": worldDigest(snap.World), "resources": pairWorldResources(snap.World), "NPC_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x365e), 1008)), "swords_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x275a), 16)), "location": checkpointLocation(e.Oracle), "separate_process": true, "snapshot_loaded": false})
}

func TestOriginalGuardRecordModels(t *testing.T) {
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
	dir := filepath.Join(work, "guard-model-store")
	must(importNativeProgress(root, root, dir, filepath.Join(work, "inputs"), catalog, combat))
	store, base, err := openProgressPair(dir, catalog, combat)
	must(err)
	npcRows := func(region, index int) [6]ArmyStack {
		var rows [6]ArmyStack
		for i := range rows {
			at := guardNPCAt(region, index) + i*4
			kind, er := guardSavedWord(base.Bytes.Native, at)
			must(er)
			count, er := guardSavedWord(base.Bytes.Native, at+2)
			must(er)
			if kind != 0 {
				rows[i] = ArmyStack{fmt.Sprintf("native:%02d", kind), uint32(count)}
			}
		}
		return rows
	}
	models := []map[string]any{}
	for region := 0; region < 8; region++ {
		for _, boss := range []bool{false, true} {
			index := 0
			if boss {
				index = int(swordBossIndex[region])
			}
			key := fmt.Sprintf("guarded:%02d:%02d", region, index)
			p := base
			p.World = cloneCampWorld(base.World)
			p.World.Encounters[key] = WorldEncounter{Enemy: npcRows(region, index), Cleared: true}
			before := worldDigest(base.World)
			native := bytes.Clone(base.Bytes.Native)
			overlay, er := originalGuardOverlay(p)
			must(er)
			at := guardedSaveBase + guardNPCAt(region, index) - 0x365e
			for i := 0; i < 12; i++ {
				if binary.LittleEndian.Uint16(overlay[at+i*2:])-uint16(at+i*2+3) != 0 {
					t.Fatal("cleared record did not clear raw NPC", region, index)
				}
			}
			flags, er := savedSwords(overlay)
			must(er)
			oldFlags, er := savedSwords(native)
			must(er)
			if boss {
				oldFlags[region] = true
			}
			if flags != oldFlags {
				t.Fatal("cleared record swords", region, index)
			}
			if before != worldDigest(base.World) || !bytes.Equal(native, base.Bytes.Native) {
				t.Fatal("overlay modified input")
			}
			models = append(models, map[string]any{"region": region, "index": index, "boss": boss, "npc_save_offset": at, "cleared": true, "flags": flags, "source_unchanged": true})
		}
	}
	for _, name := range []string{"region", "index", "noncanonical", "ending", "extension", "wide", "flag"} {
		p := base
		p.World = cloneCampWorld(base.World)
		p.Bytes.Native = bytes.Clone(base.Bytes.Native)
		key := "guarded:00:00"
		rec := WorldEncounter{Enemy: [6]ArmyStack{{"native:06", 30}}}
		switch name {
		case "region":
			key = "guarded:08:00"
		case "index":
			key = "guarded:00:99"
		case "noncanonical":
			key = "guarded:0:0"
		case "ending":
			key = "guarded:00:04"
		case "extension":
			rec.Enemy[0] = ArmyStack{"openkb:wolf", 2}
		case "wide":
			rec.Enemy[0].Count = 32768
		case "flag":
			binary.LittleEndian.PutUint16(p.Bytes.Native[1318:], uint16(1318+3+2))
		}
		p.World.Encounters[key] = rec
		native := bytes.Clone(p.Bytes.Native)
		digest := worldDigest(p.World)
		if _, er := originalGuardOverlay(p); er == nil {
			t.Fatal("unsafe guard record", name)
		}
		if !bytes.Equal(native, p.Bytes.Native) || digest != worldDigest(p.World) {
			t.Fatal("guard record refusal modified input", name)
		}
	}
	// The existing paired journal already makes the Go guard record durable.
	w := cloneCampWorld(base.World)
	w.Revision++
	w.Progress.Legacy04F6 += 20
	w.Encounters["guarded:00:01"] = WorldEncounter{Enemy: npcRows(0, 1), Cleared: true}
	store.Fault = func(phase string) error {
		if phase == "intent-durable" {
			return errors.New("controlled guard record interruption")
		}
		return nil
	}
	_, err = store.Commit(base.Token, w)
	if !errors.Is(err, errPairPending) {
		t.Fatal("guard record fault", err)
	}
	store.Close()
	store, recovered, err := openProgressPair(dir, catalog, combat)
	must(err)
	defer store.Close()
	if worldDigest(recovered.World) != worldDigest(w) {
		t.Fatal("guard record journal did not recover")
	}
	overlay, err := originalGuardOverlay(recovered)
	must(err)
	flags, err := savedSwords(overlay)
	must(err)
	if !flags[0] {
		t.Fatal("recovered boss record missing sword")
	}
	again, err := store.Recover()
	must(err)
	if again.Token != recovered.Token {
		t.Fatal("recovery applied guard twice")
	}
	setupWrite(t, filepath.Join(work, "guard-record-models.json"), map[string]any{"models": models, "record_refusals": 7, "interrupted_commit_recovered": true, "recovery_idempotent": true, "schema_unchanged": true, "NPC_and_swords_restored_from_Go_records": true})
}

func TestOriginalGuardRewardGuards(t *testing.T) {
	work, _, catalog := setupInputs(t)
	pam, err := os.ReadFile(filepath.Join(work, "inputs/PAM.AY"))
	if err != nil {
		t.Fatal(err)
	}
	code, err := worldArmyCode(pam)
	if err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"source", "segment", "frame", "NPC", "swords", "shadow", "resources", "result", "amount", "duplicate", "inactive", "committed"} {
		m, _ := actionFixture(t, code, catalog, [2][6]ArmyStack{{{"native:01", 30}}, {{"native:06", 30}}})
		m.CPU.Seg[dg.CS] = 0x110
		m.CPU.IP = 0x1b7b
		m.CPU.R[dg.BP] = 0xee00
		m.CPU.R[dg.SP] = 0xedfc
		m.CPU.R[dg.AX] = 20
		m.Write16(0x1e880+0xee00, 0xeb00)
		m.Write16(0x1e880+0xee02, 0x32aa)
		m.Write16(0x1e880+0xee04, 0x110)
		g := &originalBattleGuard{Code: code, Rounds: &originalBattleRounds{Result: "win"}, Guard: &guardedBinding{Context: EncounterContext{Kind: "guarded"}}, RewardSP: 0xee02, RewardBP: 0xeb00, Active: true, Captured: true, RewardActive: true}
		copy(g.NPC[:], m.Mem[0x1e880+0x365e:0x1e880+0x3a4e])
		copy(g.Flags[:], m.Mem[0x1e880+0x275a:0x1e880+0x276a])
		copy(g.Shadow[:], m.Mem[0x1e880+0x54a:0x1e880+0x562])
		for i := range g.Expected {
			g.Expected[i] = uint64(m.Read16(0x1e880 + 0x4f2 + uint32(i*2)))
		}
		switch name {
		case "source":
			m.Mem[0x1100+0x1abe] ^= 1
		case "segment":
			m.CPU.Seg[dg.DS]++
		case "frame":
			m.CPU.R[dg.BP]--
		case "NPC":
			m.Mem[0x1e880+0x365e] ^= 1
		case "swords":
			m.Mem[0x1e880+0x275a] ^= 1
		case "shadow":
			m.Mem[0x1e880+0x54a] ^= 1
		case "resources":
			m.Mem[0x1e880+0x4f8] ^= 1
		case "result":
			g.Rounds.Result = "retreat"
		case "amount":
			m.CPU.R[dg.AX]++
		case "duplicate":
			g.Monthly = true
		case "inactive":
			g.RewardActive = false
		case "committed":
			g.Committed = true
		}
		before := bytes.Clone(m.Mem)
		regs, flags, ip, cycles := m.CPU.R, m.CPU.Flags, m.CPU.IP, m.CPU.Cycles
		resources, monthly, power, sword := g.Expected, g.Monthly, g.Power, g.Sword
		if _, er := g.reward(m, 0x1b7b); er == nil {
			t.Fatal("unsafe guard award", name)
		}
		if !bytes.Equal(before, m.Mem) || regs != m.CPU.R || flags != m.CPU.Flags || ip != m.CPU.IP || cycles != m.CPU.Cycles || resources != g.Expected || monthly != g.Monthly || power != g.Power || sword != g.Sword || len(g.Events) != 0 {
			t.Fatal("guard award refusal changed state", name)
		}
	}
	setupWrite(t, filepath.Join(work, "guard-reward-guards.json"), map[string]any{"refusals": 12, "state_unchanged": true})
}

func TestOriginalGuardCommittedRetry(t *testing.T) {
	work, _, catalog := setupInputs(t)
	pam, err := os.ReadFile(filepath.Join(work, "inputs/PAM.AY"))
	if err != nil {
		t.Fatal(err)
	}
	code, err := worldArmyCode(pam)
	if err != nil {
		t.Fatal(err)
	}
	m, _ := actionFixture(t, code, catalog, [2][6]ArmyStack{{{"native:01", 30}}, {{"native:06", 30}}})
	m.CPU.Seg[dg.CS] = 0x110
	m.CPU.IP = 0x32ad
	m.CPU.R[dg.BP] = 0xee00
	m.CPU.R[dg.SP] = 0xedee
	m.Write16(0x1e880+0xee00, 0xeb00)
	m.Write16(0x1e880+0xee02, 0x25ee)
	m.Write16(0x1e880+0xee04, 0x110)
	g := &originalBattleGuard{Code: code, Projection: &originalArmyProjection{EntrySP: 0xedea}, EntrySP: 0xee02, EntryBP: 0xeb00, Active: true, Captured: true, RewardActive: true, Committed: true, Hold: true}
	copy(g.NPC[:], m.Mem[0x1e880+0x365e:0x1e880+0x3a4e])
	copy(g.Flags[:], m.Mem[0x1e880+0x275a:0x1e880+0x276a])
	copy(g.Shadow[:], m.Mem[0x1e880+0x54a:0x1e880+0x562])
	for i := range g.Expected {
		g.Expected[i] = uint64(m.Read16(0x1e880 + 0x4f2 + uint32(i*2)))
	}
	before := bytes.Clone(m.Mem)
	regs, flags, ip, cycles := m.CPU.R, m.CPU.Flags, m.CPU.IP, m.CPU.Cycles
	resources := g.Expected
	for i := 0; i < 5; i++ {
		if _, er := g.finish(m); !errors.Is(er, errOriginalGuardHeld) {
			t.Fatal("committed guard retry", er)
		}
	}
	if !bytes.Equal(before, m.Mem) || regs != m.CPU.R || flags != m.CPU.Flags || ip != m.CPU.IP || cycles != m.CPU.Cycles || resources != g.Expected || len(g.Events) != 0 {
		t.Fatal("committed guard result repeated")
	}
	setupWrite(t, filepath.Join(work, "guard-committed-retries.json"), map[string]any{"retries": 5, "RAM_cycles_registers_flags_resources_unchanged": true, "no_second_store_required": true})
}

// Normal original confirmation and picker keys; only the initial position and
// army are fixtures. No IP injection, battle stub, forced result or reroll.
func originalGuardFight(t *testing.T, e *game.Engine, retreat bool, owner *originalBattleGuard) error {
	return originalGuardFightLimit(t, e, retreat, owner, 220000000)
}
func originalGuardFightLimit(t *testing.T, e *game.Engine, retreat bool, owner *originalBattleGuard, budget uint64) error {
	return originalGuardRun(t, e, retreat, owner, budget, false)
}
func originalGuardRun(t *testing.T, e *game.Engine, retreat bool, owner *originalBattleGuard, budget uint64, cancel bool) error {
	t.Helper()
	initialReturns := uint64(0)
	if owner != nil && owner.Session != nil {
		initialReturns = owner.Session.Returns
	}
	entered, started, pending, entering := false, false, false, false
	phase, finished := true, false
	e.Oracle.OnCall(oracle.Far(0x110, 0x2dde), func(*oracle.Oracle) { entered = true })
	e.Oracle.OnCall(oracle.Far(0xf67, 8), func(*oracle.Oracle) { started = true })
	e.Oracle.OnCall(oracle.Far(0xf67, 0x3c), func(*oracle.Oracle) { finished = true })
	last := uint64(0)
	e.Oracle.OnCall(oracle.Far(0x160a, 0x87), func(o *oracle.Oracle) {
		if phase && entered && (!started || finished) && o.Steps()-last > 50000 {
			last = o.Steps()
			if cancel {
				o.PressKey(oracle.KeyEscape)
			} else {
				o.PressKey(oracle.KeyEnter)
			}
		}
	})
	if owner == nil {
		swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0x25ee), func(*dg.Machine) (bool, error) {
			if phase && (started || cancel && entered) {
				return false, errOriginalGuardMapHeld
			}
			return false, nil
		})
	}
	node := -1
	target := uint16(0)
	picks := 0
	var picker oracle.Regs
	e.Oracle.OnCall(oracle.Far(0xf67, 0x283f), func(*oracle.Oracle) { entering = false })
	e.Oracle.OnCall(oracle.Far(0xf67, 0x283e), func(o *oracle.Oracle) {
		if !phase || entering {
			return
		}
		entering = true
		pending = true
		picks++
		picker = o.Regs()
		picker.IP = o.Word(oracle.Far(picker.SS, picker.SP))
		picker.CS = o.Word(oracle.Far(picker.SS, picker.SP+2))
		picker.SP += 4
		node = -1
		target = 0
		for slot := uint16(0); slot < 6; slot++ {
			raw := o.Word(oracle.Far(0x1e88, 0x6fc2+slot*2))
			if raw < 6 && o.Word(oracle.Far(0x1e88, 0x5702+raw*4)) > 0 {
				target = slot + 1
				break
			}
		}
		if target == 0 {
			t.Fatal("guard picker lacks original live enemy")
		}
	})
	e.Oracle.OnCall(oracle.Far(0xf67, 0x28a6), func(o *oracle.Oracle) {
		if !phase || !pending {
			return
		}
		r := o.Regs()
		at := o.Word(oracle.Far(r.SS, r.BP-10))
		if int(at) == node {
			return
		}
		node = int(at)
		if retreat && picks > 1 {
			o.PressKey(oracle.KeyEscape)
			return
		}
		if at == target {
			o.PressKey(oracle.KeyEnter)
			return
		}
		type path struct {
			at    uint16
			first oracle.Key
		}
		queue := []path{{at: at}}
		seen := map[uint16]bool{at: true}
		for len(queue) > 0 {
			current := queue[0]
			queue = queue[1:]
			for i, key := range []oracle.Key{oracle.KeyUp, oracle.KeyDown, oracle.KeyLeft, oracle.KeyRight} {
				next := uint16(o.Bytes(oracle.Far(0x1e88, 0x709a+current.at*4+uint16(i)), 1)[0])
				if next < 1 || next > 12 || seen[next] {
					continue
				}
				first := current.first
				if current.at == at {
					first = key
				}
				if next == target {
					o.PressKey(first)
					return
				}
				seen[next] = true
				queue = append(queue, path{next, first})
			}
		}
		t.Fatal("guard cursor path", at, target)
	})
	start := e.Oracle.Steps()
	e.Oracle.SetStepGuard(func(o *oracle.Oracle) error {
		r := o.Regs()
		if owner != nil && (owner.EndingHandoff || owner.Returned && (owner.Session == nil || owner.Session.Returns > initialReturns)) {
			return errOriginalGuardMapHeld
		}
		if pending && r.CS == picker.CS && r.IP == picker.IP && r.SP == picker.SP {
			pending = false
		}
		if o.Steps() > start+budget {
			return errors.New("original guard input budget")
		}
		return nil
	})
	var err error
	if err = e.Key(0x4b, true); err != nil {
		e.Oracle.SetStepGuard(nil)
		phase = false
		return err
	}
	// A completed final guard can reach the held playback entry during this
	// first key press. Return that sentinel instead of setupPress calling Fatal.
	for n := 0; n < 40; n++ {
		if n == 10 {
			_ = e.Key(0x4b, false)
		}
		err = catchWorldArmyFault(func() error { return e.AdvanceCycles(30000) })
		e.RenderAudio()
		if err != nil {
			break
		}
	}
	_ = e.Key(0x4b, false)
	for err == nil {
		err = catchWorldArmyFault(func() error { return e.AdvanceCycles(100000) })
		e.RenderAudio()
		if err != nil {
			break
		}
	}
	e.Oracle.SetStepGuard(nil)
	phase = false
	return err
}

func TestOriginalGuardWorld(t *testing.T) {
	work, root, combat := setupInputs(t)
	assets := os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if assets == "" {
		t.Skip("assets")
	}
	var catalog ArmyCatalog
	raw, err := os.ReadFile(filepath.Join(work, "inputs/army-catalog.json"))
	if err != nil {
		t.Fatal(err)
	}
	if err = pairStrictJSON(raw, &catalog); err != nil {
		t.Fatal(err)
	}
	parent := filepath.Join(work, "guards-r1")
	if err = os.MkdirAll(parent, 0700); err != nil {
		t.Fatal(err)
	}
	cases := []struct {
		Name                     string
		HD, Retreat, Boss, Mixed bool
		Pair                     bool
	}{{"native-win", false, false, false, false, true}, {"hd-retreat", true, true, false, false, true}, {"hd-mixed-win", true, false, false, true, false}, {"hd-boss-win", true, false, true, true, false}}
	for _, sc := range cases {
		t.Run(sc.Name, func(t *testing.T) {
			must := func(err error) {
				t.Helper()
				if err != nil {
					t.Fatal(err)
				}
			}
			var reference map[string]any
			first := 1
			if sc.Pair {
				first = 0
			}
			for mode := first; mode < 2; mode++ {
				dir := filepath.Join(parent, fmt.Sprintf("%s-mode-%d", sc.Name, mode))
				must(os.Mkdir(dir, 0700))
				player := [6]ArmyStack{{"native:01", 1000}, {"native:03", 200}}
				if sc.Mixed {
					player[2] = ArmyStack{"openkb:wolf", 20}
					player[3] = ArmyStack{"openkb:arcr", 20}
				}
				session := filepath.Join(dir, "session")
				must(importNativeProgress(root, root, session, filepath.Join(work, "inputs"), catalog, combat))
				store, snap, er := openProgressPair(session, catalog, combat)
				must(er)
				w := snap.World
				w.Army.Slots = player
				if sc.Mixed {
					w.Army.Rules = "formation" // Existing save contract; this battle still uses native rules.
				}
				w.Army.Leadership = 30000
				w.Progress.Merit = 10000
				w.Revision++
				snap, er = store.Commit(snap.Token, w)
				must(er)
				port := &worldArmyPort{Store: store, Current: snap}
				must(materializeNativeCheckpoint(root, filepath.Join(work, "inputs"), filepath.Join(dir, "scratch"), snap))
				e := setupCold(t, root, assets, dir, sc.HD)
				x, y := uint16(6), uint16(4)
				if sc.Boss {
					x, y = 49, 5
				}
				e.Oracle.WriteU16(oracle.Far(0x1e88, 0x8e12), x)
				e.Oracle.WriteU16(oracle.Far(0x1e88, 0x8e44), y)
				var owner *originalBattleGuard
				var enemy *originalBattleEnemy
				var checkpoint *nativeCheckpointPort
				if mode == 1 {
					owner, enemy = originalGuardControllers(t, e, port, player)
					checkpoint, er = installNativeCheckpoint(e, port, filepath.Join(dir, "scratch"))
					must(er)
				} else {
					e.Oracle.OnCall(oracle.Far(0x110, 0x32e0), func(o *oracle.Oracle) {
						for i, row := range player {
							p := combat.Profiles[row.Unit]
							o.WriteU16(oracle.Far(0x1e88, 0x54a+uint16(i*4)), p.NativeKind)
							o.WriteU16(oracle.Far(0x1e88, 0x54c+uint16(i*4)), uint16(row.Count))
						}
					})
				}
				err = originalGuardFight(t, e, sc.Retreat, owner)
				if !errors.Is(err, errOriginalGuardMapHeld) {
					must(e.Oracle.SaveStateFile(filepath.Join(dir, "failed.state")))
					diag := map[string]any{"error": fmt.Sprint(err), "regs": e.Oracle.Regs()}
					if owner != nil {
						diag["events"] = owner.Events
						diag["rows"] = owner.Rounds.Rows
						diag["history"] = owner.Rounds.History
						diag["maps"] = owner.Rounds.Slots
						diag["motion_after"] = owner.Rounds.MotionAfter
						diag["enemy"] = enemy.Records
					}
					setupWrite(t, filepath.Join(dir, "failed.json"), diag)
					t.Fatal("original guard fight", err)
				}
				e.ReleaseAll()
				setupAdvance(t, e, 500)
				frame := e.Frame()
				f, er := os.Create(filepath.Join(dir, "map.png"))
				must(er)
				must(png.Encode(f, frame))
				must(f.Close())
				must(e.Oracle.SaveStateFile(filepath.Join(dir, "returned.state")))
				resources := [6]uint16{}
				for i := range resources {
					resources[i] = e.Oracle.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))
				}
				row := map[string]any{"name": sc.Name, "mode": mode, "hd": sc.HD, "controlled_army": player, "controlled_position": [2]uint16{x, y}, "native_guard_unmodified": true, "resources": resources, "NPC_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x365e), 1008)), "swords_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x275a), 16)), "seed": originalSeed(e.Oracle), "frame_sha256": contentSHA(frame.Pix), "location": checkpointLocation(e.Oracle)}
				if mode == 0 {
					reference = row
				} else {
					if sc.Pair {
						for _, key := range []string{"resources", "NPC_hex", "swords_hex", "seed", "frame_sha256"} {
							if fmt.Sprint(reference[key]) != fmt.Sprint(row[key]) {
								t.Fatal("original/Go guard differs", key, reference[key], row[key])
							}
						}
					}
					expectedResult := "win"
					if sc.Retreat {
						expectedResult = "retreat"
					}
					if !owner.Committed || !owner.Returned || owner.Rounds.Result != expectedResult {
						t.Fatal("guard result", owner.Rounds.Result)
					}
					beforeF7, er := store.Recover()
					must(er)
					if beforeF7.World.Progress.Rank != 1 || beforeF7.World.Progress.Merit != 10000 || (!sc.Retreat && beforeF7.World.Army.Gold != 500) {
						t.Fatal("guard used random-encounter promotion/reward")
					}
					row["result"] = owner.Rounds.Result
					row["events"] = owner.Events
					row["remaining"] = owner.Projection.Remaining
					row["enemy_remaining"] = owner.Enemy
					row["context"] = owner.Guard.Context
					row["world_before_f7"] = worldDigest(beforeF7.World)
					row["ordinary_actions"] = len(owner.Rounds.History)
					row["enemy_specials"] = enemy.Records
					// Rebuild the Go-owned records without an F7 serializer update.
					coldDir := filepath.Join(dir, "before-f7-cold")
					must(os.Mkdir(coldDir, 0700))
					must(materializeNativeCheckpoint(root, filepath.Join(work, "inputs"), filepath.Join(coldDir, "scratch"), beforeF7))
					cold := setupCold(t, root, assets, coldDir, sc.HD)
					coldOwner, _ := originalGuardControllers(t, cold, port, beforeF7.World.Army.Slots)
					if !bytes.Equal(cold.Oracle.Bytes(oracle.Far(0x1e88, 0x365e), 1008), e.Oracle.Bytes(oracle.Far(0x1e88, 0x365e), 1008)) {
						t.Fatal("guard pre-F7 cold NPC")
					}
					_ = coldOwner
					if !bytes.Equal(cold.Oracle.Bytes(oracle.Far(0x1e88, 0x275a), 16), e.Oracle.Bytes(oracle.Far(0x1e88, 0x275a), 16)) {
						t.Fatal("guard pre-F7 cold swords")
					}
					must(cold.Oracle.SaveStateFile(filepath.Join(coldDir, "continued.state")))
					cold.Close()
					row["pre_F7_cold_records_restored"] = true
					setupPress(t, e, 0x41)
					setupPress(t, e, 0x1c)
					setupPress(t, e, 0x1c)
					setupAdvance(t, e, 700)
					e.ReleaseAll()
					if checkpoint.Saves != 1 {
						t.Fatal("guard F7", checkpoint.Saves)
					}
					saved, er := store.Recover()
					must(er)
					overlay, er := originalGuardOverlay(saved)
					must(er)
					npc, er := originalGuardNPC(overlay)
					must(er)
					nativeNPC, er := originalGuardNPC(saved.Bytes.Native)
					must(er)
					if npc != nativeNPC {
						t.Fatal("F7 did not capture Go NPC")
					}
					flags, er := savedSwords(saved.Bytes.Native)
					must(er)
					if sc.Boss && !flags[0] {
						t.Fatal("boss sword not saved")
					}
					row["checkpoint_saves"] = checkpoint.Saves
					row["world_sha256"] = worldDigest(saved.World)
					row["saved_resources"] = pairWorldResources(saved.World)
					must(e.Oracle.SaveStateFile(filepath.Join(dir, "saved.state")))
				}
				setupWrite(t, filepath.Join(dir, "receipt.json"), row)
				e.Close()
				store.Close()
			}
		})
		if t.Failed() {
			break
		}
	}
}
