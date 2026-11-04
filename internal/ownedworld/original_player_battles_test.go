package ownedworld

import (
	"errors"
	"fmt"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
	"os"
	"path/filepath"
	"testing"
)

func playerRandomRun(t *testing.T, e *game.Engine, session *originalPlayerBattles, retreat bool) error {
	t.Helper()
	active := true
	defer func() { active = false }()
	prompt := false
	e.Oracle.OnCall(oracle.Far(0x110, 0x16e0), func(*oracle.Oracle) {
		if e.PAMLoaded {
			prompt = true
		}
	})
	setupPress(t, e, 0x50)
	setupPress(t, e, 0x50)
	for n := 0; !prompt && n < 128; n++ {
		k := byte(0x4d)
		if n%2 != 0 {
			k = 0x4b
		}
		setupPress(t, e, k)
	}
	if !prompt {
		t.Fatal("round normal encounter prompt")
	}
	setupAdvance(t, e, 500)
	im := e.Frame()
	red := 0
	for y := 798; y < 888; y++ {
		for x := 624; x < 720; x++ {
			c := im.RGBAAt(x, y)
			if c.R > 180 && c.G < 120 && c.B < 130 {
				red++
			}
		}
	}
	if red > 1000 {
		setupPress(t, e, 0x4b)
	}
	pending := false
	var picker oracle.Regs
	e.Oracle.OnCall(oracle.Far(0xf67, 0x283e), func(o *oracle.Oracle) {
		if !active || pending {
			return
		}
		pending = true
		picker = o.Regs()
		picker.IP = o.Word(oracle.Far(picker.SS, picker.SP))
		picker.CS = o.Word(oracle.Far(picker.SS, picker.SP+2))
		start := o.Word(oracle.Far(picker.SS, picker.SP+4))
		picker.SP += 4
		if retreat {
			o.PressKey(oracle.KeyEscape)
			return
		}
		target := uint16(0)
		for slot := uint16(0); slot < 6; slot++ {
			raw := o.Word(oracle.Far(0x1e88, 0x6fc2+slot*2))
			if raw < 6 && o.Word(oracle.Far(0x1e88, 0x5702+raw*4)) > 0 {
				target = slot + 1
				break
			}
		}
		if target == 0 {
			t.Fatal("round picker has no native enemy")
		}
		if err := roundKeys(o, start, target); err != nil {
			t.Fatal(err)
		}
	})
	startSteps := e.Oracle.Steps()
	released := false
	e.Oracle.SetStepGuard(func(o *oracle.Oracle) error {
		r := o.Regs()
		if session.RandomReturned && session.World.Returned {
			return errOriginalGuardMapHeld
		}
		if pending && r.CS == picker.CS && r.IP == picker.IP && r.SP == picker.SP && r.SS == picker.SS {
			pending = false
		}
		if !released && o.Steps() > startSteps+100000 {
			if er := e.Key(0x1c, false); er != nil {
				return er
			}
			released = true
		}
		if o.Steps() > startSteps+150000000 {
			return errors.New("round encounter budget")
		}
		return nil
	})
	if er := e.Key(0x1c, true); er != nil {
		t.Fatal(er)
	}
	var err error
	for err == nil {
		err = catchWorldArmyFault(func() error { return e.AdvanceCycles(100000) })
		e.RenderAudio()
	}
	e.Oracle.SetStepGuard(nil)
	return err
}

func TestOriginalPlayerBattleChain(t *testing.T) {
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
	dir := filepath.Join(work, "player-chain-r1")
	must(os.Mkdir(dir, 0700))
	sessionDir := filepath.Join(dir, "session")
	must(importNativeProgress(root, root, sessionDir, filepath.Join(work, "inputs"), catalog, combat))
	store, snap, err := openProgressPair(sessionDir, catalog, combat)
	must(err)
	defer store.Close()
	world := snap.World
	world.Revision++
	world.Army.Leadership = 30000
	world.Progress.Merit = 10000
	world.Army.Rules = "formation"
	world.Army.Slots = [6]ArmyStack{{"native:01", 1000}, {"native:03", 200}, {"openkb:wolf", 20}, {"openkb:arcr", 20}}
	snap, err = store.Commit(snap.Token, world)
	must(err)
	must(materializeNativeCheckpoint(root, filepath.Join(work, "inputs"), filepath.Join(dir, "scratch"), snap))
	e := setupCold(t, root, assets, dir, true)
	defer e.Close()
	port, err := installWorldArmyPort(e, store, snap)
	must(err)
	view, _, err := installOriginalPlayerServices(e, port, filepath.Join(dir, "scratch"), filepath.Join(work, "ui-assets"))
	must(err)
	fonts, err := loadArmyUIFonts(filepath.Join(work, "ui-assets"))
	must(err)
	pack := loadHDUnitArtwork(e, filepath.Join(work, "ui-assets"), contentSHA(raw))
	view.Fields = newOriginalArmyFields(view, fonts, pack)
	session := port.PlayerBattles
	checkpoint := port.OriginalCheckpoint
	// Original F2/F3 are opened and cancelled before the same controller chain.
	for _, key := range []byte{0x3c, 0x3d} {
		setupPress(t, e, key)
		setupAdvance(t, e, 700)
		if !view.Active || !view.Ready {
			t.Fatal("original management did not open", key)
		}
		setupPress(t, e, 1)
		setupAdvance(t, e, 500)
		if view.Active {
			t.Fatal("original management did not close", key)
		}
	}
	active := false
	last := uint64(0)
	e.Oracle.OnCall(oracle.Far(0x160a, 0x87), func(o *oracle.Oracle) {
		if active && session.World.Active && session.Guard.Rounds.Done && o.Steps()-last > 50000 {
			last = o.Steps()
			o.PressKey(oracle.KeyEnter)
		}
	})
	reports := []map[string]any{}
	for i, kind := range []string{"random", "guard", "random"} {
		if kind == "guard" {
			e.Oracle.WriteU16(oracle.Far(0x1e88, 0x8e12), 6)
			e.Oracle.WriteU16(oracle.Far(0x1e88, 0x8e44), 4)
		}
		if i == 2 {
			e.Oracle.WriteU16(oracle.Far(0x1e88, 0x8e12), 40)
			e.Oracle.WriteU16(oracle.Far(0x1e88, 0x8e44), 40)
		}
		if kind == "random" {
			active = true
			err = playerRandomRun(t, e, session, true)
			active = false
		} else {
			err = originalGuardRun(t, e, false, session.Guard, 300000000, false)
		}
		if !errors.Is(err, errOriginalGuardMapHeld) {
			must(e.Oracle.SaveStateFile(filepath.Join(dir, fmt.Sprintf("failed-%d.state", i))))
			setupWrite(t, filepath.Join(dir, "failed.json"), map[string]any{"error": fmt.Sprint(err), "regs": e.Oracle.Regs(), "events": session.Events, "guard": session.Guard.Events})
			t.Fatal(kind, err)
		}
		e.ReleaseAll()
		want := "retreat"
		if kind == "guard" {
			want = "win"
		}
		if session.Guard.Rounds.Result != want {
			t.Fatalf("%s result: got %q, want %q", kind, session.Guard.Rounds.Result, want)
		}
		setupAdvance(t, e, 500)
		saved, er := store.Recover()
		must(er)
		endingFrame(t, e, filepath.Join(dir, fmt.Sprintf("%d-%s.png", i, kind)))
		reports = append(reports, map[string]any{"mode": kind, "sequence": session.Sequence, "army": saved.World.Army.Slots, "resources": pairWorldResources(saved.World), "round_result": session.Guard.Rounds.Result, "world_sha256": worldDigest(saved.World)})
	}
	setupPress(t, e, 0x41)
	setupPress(t, e, 0x1c)
	setupPress(t, e, 0x1c)
	setupAdvance(t, e, 700)
	e.ReleaseAll()
	if checkpoint.Saves != 1 {
		t.Fatal("F7", checkpoint.Saves)
	}
	saved, err := store.Recover()
	must(err)
	setupWrite(t, filepath.Join(dir, "receipt.json"), map[string]any{"status": "passed-original-player-chain", "phases": reports, "events": session.Events, "world_sha256": worldDigest(saved.World), "resources": pairWorldResources(saved.World), "army": saved.World.Army.Slots, "location": checkpointLocation(e.Oracle), "F7": checkpoint.Saves, "same_process": true, "position_fixtures": true, "initial_seed": 0x12345678, "F2_F3_original": true, "legacy_card_controller": encounterCurrent != nil})
}

func TestOriginalPlayerCold(t *testing.T) {
	session, dir := os.Getenv("EIGHTSWORD_PLAYER_COLD_SESSION"), os.Getenv("EIGHTSWORD_PLAYER_COLD_OUT")
	if session == "" || dir == "" {
		t.Skip("explicit separate-process fixture")
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
	e := setupCold(t, root, os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS"), dir, true)
	defer e.Close()
	p, err := installWorldArmyPort(e, store, snap)
	must(err)
	_, _, err = installOriginalPlayerServices(e, p, filepath.Join(dir, "scratch"), filepath.Join(work, "ui-assets"))
	must(err)
	if encounterCurrent != nil || runtimeEnemyCurrent != nil {
		t.Fatal("legacy card controller installed")
	}
	for i, v := range pairWorldResources(snap.World).words() {
		if uint64(e.Oracle.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != v {
			t.Fatal("cold resources", i)
		}
	}
	endingFrame(t, e, filepath.Join(dir, "continued.png"))
	setupWrite(t, filepath.Join(dir, "receipt.json"), map[string]any{"status": "passed-original-player-process-cold", "world_sha256": worldDigest(snap.World), "army": snap.World.Army.Slots, "resources": pairWorldResources(snap.World), "location": checkpointLocation(e.Oracle), "separate_process": true, "snapshot_loaded": false, "legacy_card_controller": false})
}
