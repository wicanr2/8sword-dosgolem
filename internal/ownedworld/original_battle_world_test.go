package ownedworld

import (
	"bytes"
	"errors"
	"image/png"
	"os"
	"path/filepath"
	"testing"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func TestOriginalBattleWorldGuards(t *testing.T) {
	work, _, _ := setupInputs(t)
	pam, err := os.ReadFile(filepath.Join(work, "inputs/PAM.AY"))
	if err != nil {
		t.Fatal(err)
	}
	code, err := worldArmyCode(pam)
	if err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"source", "segment", "frame", "resource", "unfinished", "shadow", "duplicate", "wrong-result"} {
		m := dg.New()
		copy(m.Mem[0x1100:], code)
		c := m.CPU
		c.Seg[dg.CS], c.Seg[dg.DS], c.Seg[dg.SS] = 0x110, 0x1e88, 0x1e88
		c.IP = 0x1900
		c.R[dg.BP], c.R[dg.SP] = 0xeefe, 0xeefa
		m.Write16(0x1e880+0xeefe, 0xf100)
		m.Write16(0x1e880+0xef00, 0x172b)
		m.Write16(0x1e880+0xef02, 0x110)
		v := &originalBattleWorld{Code: code, Projection: &originalArmyProjection{Captures: 1, Shadow: make([]byte, 24)}, Rounds: &originalBattleRounds{Done: true, Released: true, Result: "loss"}, EntrySP: 0xef00, EntryBP: 0xf100, Active: true, Writes: map[uint16]bool{}}
		switch name {
		case "source":
			m.Mem[0x1100+0x1796] ^= 1
		case "segment":
			c.Seg[dg.DS]++
		case "frame":
			c.R[dg.SP]--
		case "resource":
			m.Write16(0x1e880+0x4f8, 1)
		case "unfinished":
			v.Rounds.Done = false
		case "shadow":
			m.Write16(0x1e880+0x54a, 1)
		case "duplicate":
			v.Writes[0x1900] = true
		case "wrong-result":
			v.Rounds.Result = "win"
		}
		before := bytes.Clone(m.Mem)
		regs, flags, cycles, ip := c.R, c.Flags, c.Cycles, c.IP
		expected := v.Expected
		if _, er := v.execute(m, 0x1900); er == nil {
			t.Fatal("unsafe world operation", name)
		}
		if !bytes.Equal(before, m.Mem) || regs != c.R || flags != c.Flags || cycles != c.Cycles || ip != c.IP || expected != v.Expected {
			t.Fatal("world refusal mutated state", name)
		}
	}
	setupWrite(t, filepath.Join(work, "world-controls.json"), map[string]any{"refusals": 8, "state_unchanged": true})
}

func TestOriginalRoundMotionModels(t *testing.T) {
	work, _, _ := setupInputs(t)
	slots := [6]uint16{0, 1, 2, 5, 5, 5}
	for _, sc := range []struct {
		From, To int
		Alive    [3]uint32
		Want     [3]uint16
	}{
		{2, 0, [3]uint32{0, 33, 29}, [3]uint16{2, 1, 0}},
		{0, 2, [3]uint32{29, 33, 0}, [3]uint16{2, 1, 0}},
		{2, 0, [3]uint32{11, 33, 29}, [3]uint16{2, 0, 1}},
		{0, 2, [3]uint32{29, 33, 11}, [3]uint16{1, 2, 0}},
		{1, 0, [3]uint32{0, 33, 29}, [3]uint16{1, 0, 2}},
		{1, 2, [3]uint32{29, 33, 0}, [3]uint16{0, 2, 1}},
	} {
		var rows [6]ArmyStack
		for i, n := range sc.Alive {
			rows[i].Count = n
		}
		got, err := roundMotionPlan(rows, slots, sc.From, sc.To)
		if err != nil || [3]uint16{got[0], got[1], got[2]} != sc.Want {
			t.Fatal(sc, got, err)
		}
	}
	if _, err := roundMotionPlan([6]ArmyStack{}, slots, 2, 0); err == nil {
		t.Fatal("dead source admitted")
	}
	setupWrite(t, filepath.Join(work, "motion-models.json"), map[string]any{"cases": 6, "dead_source_refused": true})
}

// Run in a separate test process after the functional cohort closes its Store.
// This cold gate never loads a VM snapshot or resumes an in-memory controller.
func TestOriginalBattleWorldCold(t *testing.T) {
	session, dir := os.Getenv("EIGHTSWORD_WORLD_COLD_SESSION"), os.Getenv("EIGHTSWORD_WORLD_COLD_OUT")
	if session == "" || dir == "" {
		t.Skip("explicit cold process fixture required")
	}
	work, root, combat := setupInputs(t)
	var catalog ArmyCatalog
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	raw, err := os.ReadFile(filepath.Join(work, "inputs/army-catalog.json"))
	must(err)
	must(pairStrictJSON(raw, &catalog))
	store, snap, err := openProgressPair(session, catalog, combat)
	must(err)
	defer store.Close()
	must(os.Mkdir(dir, 0700))
	must(materializeNativeCheckpoint(root, filepath.Join(work, "inputs"), filepath.Join(dir, "scratch"), snap))
	e := setupCold(t, root, os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS"), dir, os.Getenv("EIGHTSWORD_WORLD_COLD_HD") == "1")
	defer e.Close()
	for i, n := range pairWorldResources(snap.World).words() {
		if uint64(e.Oracle.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != n {
			t.Fatal("process cold resource", i)
		}
	}
	must(e.Oracle.SaveStateFile(filepath.Join(dir, "continued.state")))
	setupWrite(t, filepath.Join(dir, "receipt.json"), map[string]any{"status": "passed-original-battle-world-process-cold", "world_sha256": worldDigest(snap.World), "resources": pairWorldResources(snap.World), "location": checkpointLocation(e.Oracle), "snapshot_loaded": false, "separate_process": true})
}

func TestOriginalBattleWorld(t *testing.T) {
	work, root, combat := setupInputs(t)
	assets := os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if assets == "" {
		t.Skip("HD assets")
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
	parent := filepath.Join(work, "world-r1")
	must(os.MkdirAll(parent, 0700))
	reports := []map[string]any{}
	for _, sc := range []struct {
		Name                              string
		HD, Go, Expanded, Retreat, Origin bool
	}{
		{"native-retreat-oracle", false, false, false, true, false}, {"native-retreat-go", false, true, false, true, false},
		{"hd-loss-oracle", true, false, false, false, false}, {"hd-loss-go", true, true, false, false, false},
		{"expanded-win", true, true, true, false, false}, {"expanded-loss-origin", true, true, true, false, true},
		{"expanded-win-promotion", true, true, true, false, false},
	} {
		t.Run(sc.Name, func(t *testing.T) {
			must := func(err error) {
				t.Helper()
				if err != nil {
					t.Fatal(err)
				}
			}
			dir := filepath.Join(parent, sc.Name)
			must(os.Mkdir(dir, 0700))
			player := [6]ArmyStack{{"native:01", 30}}
			if sc.Expanded {
				player = [6]ArmyStack{{"native:01", 74}, {"openkb:wolf", 2}, {"openkb:arcr", 2}}
				if sc.Origin {
					player = [6]ArmyStack{{"openkb:wolf", 2}, {"native:01", 30}}
				}
			}
			var port *worldArmyPort
			var store *progressPairStore
			if sc.Go {
				session := filepath.Join(dir, "session")
				must(importNativeProgress(root, root, session, filepath.Join(work, "inputs"), catalog, combat))
				var snap progressPairSnapshot
				store, snap, err = openProgressPair(session, catalog, combat)
				must(err)
				w := snap.World
				w.Army.Slots = player
				if sc.Expanded {
					w.Army.Rules = "formation"
				}
				if sc.Name == "expanded-win-promotion" {
					w.Progress.Merit = 1999
					w.Army.Gold = 29950
					w.Progress.Legacy04F6 = 29950
					w.Progress.Legacy04FC = 29999
				}
				w.Revision++
				snap, err = store.Commit(snap.Token, w)
				must(err)
				port = &worldArmyPort{Store: store, Current: snap}
				must(materializeNativeCheckpoint(root, filepath.Join(work, "inputs"), filepath.Join(dir, "scratch"), snap))
			}
			e := setupCold(t, root, assets, dir, sc.HD)
			defer e.Close()
			shadow := e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)
			var world *originalBattleWorld
			var rounds *originalBattleRounds
			var checkpoint *nativeCheckpointPort
			allow := false
			if sc.Go {
				projection, er := installOriginalArmyProjectionMode(e, combat, player, sc.Expanded)
				must(er)
				var override *[6]ArmyStack
				if sc.Expanded {
					override = &player
				}
				setup, er := installOriginalBattleSetup(e, combat, override)
				must(er)
				actions, er := installOriginalBattleActions(e, setup, true)
				must(er)
				rounds, er = installOriginalBattleRounds(e, actions)
				must(er)
				projection.Rounds = rounds
				world, er = installOriginalBattleWorld(e, port, projection, rounds)
				must(er)
				checkpoint, er = installNativeCheckpoint(e, port, filepath.Join(dir, "scratch"))
				must(er)
			} else {
				swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x3c), func(*dg.Machine) (bool, error) {
					if !allow {
						return false, errOriginalBattleRoundsHeld
					}
					return false, nil
				})
			}
			err = roundEncounter(t, e, !sc.Expanded && !sc.Retreat || sc.Origin, sc.Retreat)
			if !errors.Is(err, errOriginalBattleRoundsHeld) {
				must(e.Oracle.SaveStateFile(filepath.Join(dir, "failed-battle.state")))
				if rounds != nil {
					setupWrite(t, filepath.Join(dir, "failed-battle.json"), map[string]any{"regs": e.Oracle.Regs(), "rows": rounds.Rows, "slots": rounds.Slots, "motion_after": rounds.MotionAfter, "target": rounds.Actions.Target, "history": rounds.History})
				}
				t.Fatal("world battle", err)
			}
			allow = true
			if rounds != nil {
				rounds.AllowWorld = true
			}
			worldPhase := true
			choiceShown, downSent := false, false
			lastKey := uint64(0)
			resultPanels := 0
			e.Oracle.OnCall(oracle.Far(0x110, 0x1daa), func(o *oracle.Oracle) { choiceShown = true })
			e.Oracle.OnCall(oracle.Far(0x110, 0x1ecf), func(o *oracle.Oracle) { choiceShown = false })
			e.Oracle.OnCall(oracle.Far(0x110, 0x716c), func(o *oracle.Oracle) {
				if worldPhase {
					resultPanels++
				}
			})
			e.Oracle.OnCall(oracle.Far(0x160a, 0x87), func(o *oracle.Oracle) {
				if !worldPhase || o.Steps()-lastKey < 50000 {
					return
				}
				lastKey = o.Steps()
				if choiceShown && !sc.Origin && !downSent {
					o.PressKey(oracle.KeyDown)
					downSent = true
				} else {
					o.PressKey(oracle.KeyEnter)
				}
			})
			stop := errors.New("ordinary world map returned")
			start := e.Oracle.Steps()
			e.Oracle.SetStepGuard(func(o *oracle.Oracle) error {
				r := o.Regs()
				if world != nil && world.Returned || world == nil && r.CS == 0x110 && r.IP == 0xbd3 {
					return stop
				}
				if o.Steps() > start+50000000 {
					return errors.New("world result budget")
				}
				return nil
			})
			for {
				err = catchWorldArmyFault(func() error { return e.AdvanceCycles(100000) })
				e.RenderAudio()

				if err != nil {
					break
				}
			}
			e.Oracle.SetStepGuard(nil)
			worldPhase = false
			if !errors.Is(err, stop) {
				t.Fatal("world return", err, e.Oracle.Regs())
			}
			if world != nil && (!world.Committed || !world.Returned || !bytes.Equal(shadow, e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24))) {
				t.Fatal("Go world not returned", world)
			}
			e.ReleaseAll()
			setupAdvance(t, e, 500)
			frame := e.Frame()
			file, er := os.Create(filepath.Join(dir, "map.png"))
			must(er)
			must(png.Encode(file, frame))
			must(file.Close())
			resources := [6]uint16{}
			for i := range resources {
				resources[i] = e.Oracle.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))
			}
			location := checkpointLocation(e.Oracle)
			seed := originalSeed(e.Oracle)
			must(e.Oracle.SaveStateFile(filepath.Join(dir, "returned.state")))
			// F7 still executes the original save UI and DOS writes. The existing
			// checkpoint adapter atomically binds the Go army to those bytes/maps.
			setupPress(t, e, 0x41)
			setupPress(t, e, 0x1c)
			setupPress(t, e, 0x1c)
			setupAdvance(t, e, 700)
			worldPhase = false
			e.ReleaseAll()
			native, er := os.ReadFile(filepath.Join(dir, "scratch/gamedata.ay"))
			must(er)
			nr, er := decodeNativeResources(nativeProgressSource, native)
			must(er)
			row := map[string]any{"name": sc.Name, "hd": sc.HD, "go": sc.Go, "controlled_army_override": sc.Expanded, "initial": player, "resources": resources, "location": location, "seed_after": seed, "frame_sha256": contentSHA(frame.Pix), "result_panels": resultPanels, "choice_menu": choiceShown || downSent || sc.Origin, "saved_resources": nr}
			if sc.Go {
				if checkpoint.Saves != 1 {
					must(e.Oracle.SaveStateFile(filepath.Join(dir, "failed-f7.state")))
					f, er := os.Create(filepath.Join(dir, "failed-f7.png"))
					must(er)
					must(png.Encode(f, e.Frame()))
					must(f.Close())
					t.Fatal("F7 not committed", checkpoint.Saves, checkpoint.Active)
				}
				snap, er := store.Recover()
				must(er)
				if pairWorldResources(snap.World) != nr {
					t.Fatal("F7 Go resources differ")
				}
				row["result"] = rounds.Result
				row["before_resources"] = pairWorldResources(world.Before)
				row["reward_gold"], row["reward_merit"] = world.RewardGold, world.RewardMerit
				row["enemy_initial"] = rounds.Actions.Setup.Plan.Rows[1]
				row["remaining"] = snap.World.Army.Slots
				row["events"] = world.Events
				row["random"] = world.Random
				row["choice"] = world.Choice
				row["actions"] = len(rounds.History)
				row["checkpoint_saves"] = checkpoint.Saves
				if sc.Expanded && !sc.Origin && rounds.Result != "win" {
					t.Fatal("expected expanded ordinary victory", rounds.Result)
				}
				if sc.Name == "expanded-win-promotion" && (resources[0] != 2 || resources[2] != 30000 || resources[3] != 30000 || resources[4] != 200 || resources[5] != 30000) {
					t.Fatal("promotion/cap fixture", resources)
				}
				store.Close()
				store, cold, er := openProgressPair(filepath.Join(dir, "session"), catalog, combat)
				must(er)
				if worldDigest(cold.World) != worldDigest(snap.World) || !bytes.Equal(cold.Bytes.Native, native) {
					t.Fatal("cold Store changed battle/checkpoint")
				}
				coldDir := filepath.Join(dir, "cold")
				must(os.Mkdir(coldDir, 0700))
				must(materializeNativeCheckpoint(root, filepath.Join(work, "inputs"), filepath.Join(coldDir, "scratch"), cold))
				coldEngine := setupCold(t, root, assets, coldDir, sc.HD)
				for i, n := range nr.words() {
					if uint64(coldEngine.Oracle.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != n {
						t.Fatal("cold Continue world resource", i)
					}
				}
				row["cold_location"] = checkpointLocation(coldEngine.Oracle)
				row["cold_store_world_sha256"] = worldDigest(cold.World)
				row["cold_continue"] = true
				must(coldEngine.Oracle.SaveStateFile(filepath.Join(coldDir, "continued.state")))
				coldEngine.Close()
				store.Close()
			}
			setupWrite(t, filepath.Join(dir, "receipt.json"), row)
			reports = append(reports, row)
		})
		if t.Failed() {
			break
		}
	}
	if !t.Failed() {
		setupWrite(t, filepath.Join(work, "world-receipt.json"), map[string]any{"status": "passed-original-battle-world", "rows": reports, "seed": uint32(0x12345678), "general_player_entry": false})
	}
}
