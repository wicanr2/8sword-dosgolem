package ownedworld

import (
	"bytes"
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

func TestOriginalRoundControls(t *testing.T) {
	work, _, catalog := setupInputs(t)
	pam, err := os.ReadFile(filepath.Join(work, "inputs/PAM.AY"))
	if err != nil {
		t.Fatal(err)
	}
	code, err := worldArmyCode(pam)
	if err != nil {
		t.Fatal(err)
	}
	fixture := func(site originalRoundSite, count uint32) (*dg.Machine, *originalBattleRounds) {
		var rows [2][6]ArmyStack
		if count != 0 {
			rows[site.Side][0] = ArmyStack{"native:01", count}
		}
		m, a := actionFixture(t, code, catalog, rows)
		a.Casualties = &originalBattleCasualties{Actions: a}
		r := &originalBattleRounds{Actions: a, Sorting: -1}
		a.Rounds = r
		if _, er := r.begin(m); er != nil {
			t.Fatal(er)
		}
		m.CPU.IP = site.IP
		m.CPU.R[dg.AX] = 12
		m.CPU.R[site.Register] = 0
		return m, r
	}
	pairs := 0
	for _, site := range originalRoundSites {
		for _, count := range []uint32{0, 30} {
			m, _ := fixture(site, count)
			before := bytes.Clone(m.Mem)
			if er := m.Step(); er != nil {
				t.Fatal(er)
			}
			flags, ip := m.CPU.Flags, m.CPU.IP
			m, r := fixture(site, count)
			if handled, er := r.compare(m, site); er != nil || !handled {
				t.Fatal(site, er)
			}
			if m.CPU.Flags != flags || m.CPU.IP != ip || !bytes.Equal(before, m.Mem) {
				t.Fatal("round comparison differs", site, count)
			}
			pairs++
		}
	}
	refusals := []string{"source", "segment", "inactive", "done", "raw", "unaligned", "projection", "map"}
	for _, name := range refusals {
		site := originalRoundSites[0]
		m, r := fixture(site, 30)
		switch name {
		case "source":
			m.Mem[0x1100+site.Start-0x10000] ^= 1
		case "segment":
			m.CPU.Seg[dg.DS]++
		case "inactive":
			r.Active = false
		case "done":
			r.Done = true
		case "raw":
			m.CPU.R[site.Register] = 24
		case "unaligned":
			m.CPU.R[site.Register] = 1
		case "projection":
			m.Write16(0x1e880+0x56ea, 31)
		case "map":
			m.Write16(0x1e880+0x6fb6, 6)
		}
		before := bytes.Clone(m.Mem)
		regs, flags, cycles, ip := m.CPU.R, m.CPU.Flags, m.CPU.Cycles, m.CPU.IP
		if _, er := r.compare(m, site); er == nil {
			t.Fatal("unsafe round comparison", name)
		}
		if !bytes.Equal(before, m.Mem) || regs != m.CPU.R || flags != m.CPU.Flags || cycles != m.CPU.Cycles || ip != m.CPU.IP {
			t.Fatal("refusal mutated state", name)
		}
	}
	setupWrite(t, filepath.Join(work, "round-controls.json"), map[string]any{"native_pairs": pairs, "refusals": len(refusals)})
}

func roundKeys(o *oracle.Oracle, start, target uint16) error {
	type node struct {
		at   uint16
		keys []oracle.Key
	}
	queue := []node{{at: start}}
	seen := map[uint16]bool{start: true}
	keys := []oracle.Key{oracle.KeyUp, oracle.KeyDown, oracle.KeyLeft, oracle.KeyRight}
	for len(queue) > 0 {
		n := queue[0]
		queue = queue[1:]
		if n.at == target {
			for _, k := range n.keys {
				o.PressKey(k)
			}
			o.PressKey(oracle.KeyEnter)
			return nil
		}
		for i, k := range keys {
			next := uint16(o.Bytes(oracle.Far(0x1e88, 0x709a+n.at*4+uint16(i)), 1)[0])
			if next >= 1 && next <= 12 && !seen[next] {
				seen[next] = true
				path := append(append([]oracle.Key{}, n.keys...), k)
				queue = append(queue, node{next, path})
			}
		}
	}
	return fmt.Errorf("original cursor has no path %d to %d", start, target)
}

func roundEncounter(t *testing.T, e *game.Engine, skip bool, retreat ...bool) error {
	return roundEncounterObserved(t, e, skip, retreat, nil)
}

func roundEncounterObserved(t *testing.T, e *game.Engine, skip bool, retreat []bool, returned func(*oracle.Oracle)) error {
	t.Helper()
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
		if pending {
			return
		}
		pending = true
		picker = o.Regs()
		picker.IP = o.Word(oracle.Far(picker.SS, picker.SP))
		picker.CS = o.Word(oracle.Far(picker.SS, picker.SP+2))
		start := o.Word(oracle.Far(picker.SS, picker.SP+4))
		picker.SP += 4
		if len(retreat) > 0 && retreat[0] {
			o.PressKey(oracle.KeyEscape)
			return
		}
		if skip {
			o.PressScan(" ")
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
		if pending && r.CS == picker.CS && r.IP == picker.IP && r.SP == picker.SP && r.SS == picker.SS {
			if returned != nil {
				returned(o)
			}
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
		err = e.AdvanceCycles(100000)
		e.RenderAudio()
	}
	e.Oracle.SetStepGuard(nil)
	return err
}

func TestOriginalRoundsCold(t *testing.T) {
	work, root, catalog := setupInputs(t)
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
	folder := filepath.Join(work, "cold-r1")
	must(os.Mkdir(folder, 0700))
	reports := []map[string]any{}
	for _, hd := range []bool{false, true} {
		var refFrame, refUnits, refHP []byte
		var refAX uint16
		var refSeed uint32
		for mode := 0; mode < 2; mode++ {
			dir := filepath.Join(folder, fmt.Sprintf("hd-%v-mode-%d", hd, mode))
			must(os.Mkdir(dir, 0700))
			e := setupCold(t, root, assets, dir, hd)
			var rounds *originalBattleRounds
			if mode == 0 {
				swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x3c), func(*dg.Machine) (bool, error) { return false, errOriginalBattleRoundsHeld })
			} else {
				s, er := installOriginalBattleSetup(e, catalog, nil)
				must(er)
				a, er := installOriginalBattleActions(e, s, true)
				must(er)
				rounds, er = installOriginalBattleRounds(e, a)
				must(er)
			}
			err := roundEncounter(t, e, false)
			if !errors.Is(err, errOriginalBattleRoundsHeld) {
				t.Fatal("round full native battle", hd, mode, err, e.Oracle.Regs())
			}
			im := e.Frame()
			units := e.Oracle.Bytes(oracle.Far(0x1e88, 0x56e8), 48)
			hp := append(e.Oracle.Bytes(oracle.Far(0x1e88, 0x8ca4), 12), e.Oracle.Bytes(oracle.Far(0x1e88, 0x8e60), 12)...)
			ax := e.Oracle.Regs().AX
			seed := originalSeed(e.Oracle)
			if mode == 0 {
				refFrame, refUnits, refHP, refAX, refSeed = bytes.Clone(im.Pix), bytes.Clone(units), bytes.Clone(hp), ax, seed
			} else if !bytes.Equal(im.Pix, refFrame) || !bytes.Equal(units, refUnits) || !bytes.Equal(hp, refHP) || ax != refAX || seed != refSeed || !rounds.Done || len(rounds.History) < 2 {
				t.Fatal("full battle original/Go differs", hd, rounds.Result, rounds.History)
			}
			f, er := os.Create(filepath.Join(dir, "frame.png"))
			must(er)
			must(png.Encode(f, im))
			must(f.Close())
			must(e.Oracle.SaveStateFile(filepath.Join(dir, "held.state")))
			row := map[string]any{"hd": hd, "mode": mode, "units_hex": fmt.Sprintf("%x", units), "hp_hex": fmt.Sprintf("%x", hp), "AX": ax, "seed_after": seed, "frame_rgba_sha256": contentSHA(im.Pix)}
			if rounds != nil {
				row["history"] = rounds.History
				row["rows"] = rounds.Rows
				row["slots"] = rounds.Slots
				row["sort_calls"] = rounds.SortCalls
				row["result"] = rounds.Result
			}
			reports = append(reports, row)
			e.Close()
		}
	}
	setupWrite(t, filepath.Join(work, "cold-receipt.json"), map[string]any{"status": "passed-original-rounds-cold", "rows": reports, "normal_cold_start": true, "seed": uint32(0x12345678), "held_before_world_cleanup": true})
}

func TestOriginalRoundsExpanded(t *testing.T) {
	work, root, catalog := setupInputs(t)
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
	folder := filepath.Join(work, "expanded-r1")
	must(os.Mkdir(folder, 0700))
	reports := []map[string]any{}
	for i, player := range [][6]ArmyStack{{{"openkb:wolf", 1000}, {"openkb:arcr", 10}}, {{"openkb:wolf", 2}, {"native:01", 30}}, {{"openkb:wolf", 2}, {"native:01", 30}}} {
		dir := filepath.Join(folder, fmt.Sprint(i))
		must(os.Mkdir(dir, 0700))
		e := setupCold(t, root, assets, dir, true)
		shadow := e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)
		projection, err := installOriginalArmyProjectionMode(e, catalog, player, true)
		must(err)
		s, err := installOriginalBattleSetup(e, catalog, &player)
		must(err)
		a, err := installOriginalBattleActions(e, s, true)
		must(err)
		rounds, err := installOriginalBattleRounds(e, a)
		must(err)
		err = roundEncounter(t, e, i == 1, i == 2)
		if !errors.Is(err, errOriginalBattleRoundsHeld) {
			t.Fatal("expanded continuous battle", i, err, e.Oracle.Regs(), rounds.History)
		}
		if !rounds.Done || (i < 2 && len(rounds.History) < 3) || (i == 2 && rounds.Result != "retreat") || projection.Captures != 0 {
			t.Fatal("expanded battle incomplete", rounds)
		}
		before := e.Oracle.Bytes(oracle.Far(0, 0), 1<<20)
		cycles := e.Oracle.Cycles()
		seed := originalSeed(e.Oracle)
		n := len(rounds.History)
		for k := 0; k < 5; k++ {
			if er := e.AdvanceCycles(100000); !errors.Is(er, errOriginalBattleRoundsHeld) {
				t.Fatal(er)
			}
		}
		if !bytes.Equal(before, e.Oracle.Bytes(oracle.Far(0, 0), 1<<20)) || cycles != e.Oracle.Cycles() || seed != originalSeed(e.Oracle) || n != len(rounds.History) || !bytes.Equal(shadow, e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
			t.Fatal("round result hold changed state")
		}
		raw, err := os.ReadFile(filepath.Join(work, "inputs/army-catalog.json"))
		must(err)
		art := loadHDUnitArtwork(e, filepath.Join(work, "ui-assets"), contentSHA(raw))
		if len(art.Failures) > 0 {
			t.Fatal(art.Failures)
		}
		im, err := composeOriginalBattleSetup(e, s, art)
		must(err)
		f, er := os.Create(filepath.Join(dir, "frame.png"))
		must(er)
		must(png.Encode(f, im))
		must(f.Close())
		must(e.Oracle.SaveStateFile(filepath.Join(dir, "held.state")))
		finalNative := e.Oracle.Bytes(oracle.Far(0x1e88, 0x56e8), 48)
		rounds.AllowWorld = true
		projection.Rounds = rounds
		stop := errors.New("Go ordinary army result returned")
		steps := e.Oracle.Steps()
		e.Oracle.SetStepGuard(func(o *oracle.Oracle) error {
			r := o.Regs()
			if r.CS == 0x110 && r.IP == 0x171d {
				return stop
			}
			if o.Steps() > steps+10000000 {
				return errors.New("round world wrapper budget")
			}
			return nil
		})
		for {
			err = e.AdvanceCycles(100000)
			e.RenderAudio()
			if err != nil {
				break
			}
		}
		e.Oracle.SetStepGuard(nil)
		if !errors.Is(err, stop) || projection.Captures != 1 || !rounds.Released || !bytes.Equal(shadow, e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
			t.Fatal("Go army result handoff", err, projection)
		}
		var ac ArmyCatalog
		raw, err = os.ReadFile(filepath.Join(work, "inputs/army-catalog.json"))
		must(err)
		must(pairStrictJSON(raw, &ac))
		session := filepath.Join(dir, "session")
		must(importNativeProgress(root, root, session, filepath.Join(work, "inputs"), ac, catalog))
		store, snap, err := openProgressPair(session, ac, catalog)
		must(err)
		w := snap.World
		// This checks the already approved owned Store contract independently
		// of world rewards and the native F7 checkpoint. Establish an explicit
		// owned-rules/leadership fixture before comparing the army-only update.
		w.Army.Rules = "formation"
		w.Army.Leadership = 30000
		w.Revision++
		snap, err = store.Commit(snap.Token, w)
		must(err)
		nativeBefore := bytes.Clone(snap.Bytes.Native)
		w = snap.World
		w.Army.Slots = projection.Remaining
		w.Revision++
		snap, err = store.Commit(snap.Token, w)
		must(err)
		if !bytes.Equal(nativeBefore, snap.Bytes.Native) {
			t.Fatal("army-only result changed original native file")
		}
		store.Close()
		store, cold, err := openProgressPair(session, ac, catalog)
		must(err)
		if cold.World.Army.Slots != projection.Remaining {
			t.Fatal("Go result cold army mismatch")
		}
		store.Close()
		must(e.Oracle.SaveStateFile(filepath.Join(dir, "returned.state")))
		reports = append(reports, map[string]any{"case": i, "initial": player, "rows": rounds.Rows, "slots": rounds.Slots, "history": rounds.History, "sort_calls": rounds.SortCalls, "result": rounds.Result, "seed_after": seed, "held_retries": 5, "controlled_typed_override": true, "controlled_enemy_first_argument": false, "native_rows_hex": fmt.Sprintf("%x", finalNative), "frame_rgba_sha256": contentSHA(im.Pix), "remaining": projection.Remaining, "world_wrapper_returned": true, "army_store_cold_read": true, "controlled_store_rules": "formation", "controlled_store_leadership": 30000, "world_rewards_committed": false})
		e.Close()
	}
	setupWrite(t, filepath.Join(work, "expanded-receipt.json"), map[string]any{"status": "passed-original-rounds-expanded", "rows": reports, "playable": false, "scope": "Continuous ordinary battle to original return; world cleanup and unsupported classes held."})
}
