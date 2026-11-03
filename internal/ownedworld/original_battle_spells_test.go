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

func TestOriginalSpellGuards(t *testing.T) {
	work, _, catalog := setupInputs(t)
	pam, err := os.ReadFile(filepath.Join(work, "inputs/PAM.AY"))
	if err != nil {
		t.Fatal(err)
	}
	code, err := worldArmyCode(pam)
	if err != nil {
		t.Fatal(err)
	}
	refusals := []string{"source", "segment", "frame", "projection", "index", "display", "committed", "inactive"}
	for _, name := range refusals {
		rows := [2][6]ArmyStack{{{"native:12", 2}}, {{"native:16", 35}}}
		m, a := actionFixture(t, code, catalog, rows)
		r := &originalBattleRounds{Actions: a, Active: true, Rows: rows, Slots: a.Setup.Plan.Slots}
		copy(r.Projected[:], m.Mem[0x1e880+0x56e8:0x1e880+0x5718])
		p := &originalBattleSpells{Rounds: r, Active: true, Rows: rows, Projected: r.Projected, EffectSP: 0xef00, EffectBP: 0xee00, EffectReturn: 0x74a, Current: &originalSpellEffect{Raw: 0, Before: 35, After: 30, Planned: []uint16{35, 34, 33, 32, 31, 30}}}
		r.Spells, a.Rounds = p, r
		c := m.CPU
		c.IP, c.R[dg.BP], c.R[dg.AX], c.R[dg.BX] = 0x3546, 0xeefe, 35, 0
		m.Write16(0x1e880+0xeefe, 0xee00)
		m.Write16(0x1e880+0xef00, 0x74a)
		m.Write16(0x1e880+0xef02, 0xf67)
		switch name {
		case "source":
			m.Mem[0xf670+0x345c] ^= 1
		case "segment":
			c.Seg[dg.DS]++
		case "frame":
			c.R[dg.BP]--
		case "projection":
			m.Write16(0x1e880+0x5702, 34)
		case "index":
			c.R[dg.BX] = 24
		case "display":
			c.R[dg.AX] = 34
		case "committed":
			p.Current.Updates = 1
		case "inactive":
			p.Active = false
		}
		before := bytes.Clone(m.Mem)
		regs, flags, cycles, ip := c.R, c.Flags, c.Cycles, c.IP
		if _, er := p.write(m, 0x3546); er == nil {
			t.Fatal("unsafe spell write", name)
		}
		if !bytes.Equal(before, m.Mem) || regs != c.R || flags != c.Flags || cycles != c.Cycles || ip != c.IP || len(p.Current.Display) != 0 {
			t.Fatal("spell refusal changed state", name)
		}
	}
	setupWrite(t, filepath.Join(work, "spell-guards.json"), map[string]any{"refusals": len(refusals), "state_unchanged": true})
}

func TestOriginalSpellEntryGuards(t *testing.T) {
	work, _, catalog := setupInputs(t)
	pam, err := os.ReadFile(filepath.Join(work, "inputs/PAM.AY"))
	if err != nil {
		t.Fatal(err)
	}
	code, err := worldArmyCode(pam)
	if err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"valid", "inactive", "done", "front", "caller", "ordinary"} {
		rows := [2][6]ArmyStack{{{"native:01", 30}, {"native:12", 2}}, {{"native:16", 35}}}
		m, a := actionFixture(t, code, catalog, rows)
		a.Casualties = &originalBattleCasualties{}
		r := &originalBattleRounds{Actions: a, Active: true, Rows: rows, Slots: a.Setup.Plan.Slots, Sorting: -1}
		copy(r.Projected[:], m.Mem[0x1e880+0x56e8:0x1e880+0x5718])
		p := &originalBattleSpells{Rounds: r}
		r.Spells = p
		a.Rounds = r
		m.CPU.IP = 0x334
		m.Write16(0x1e880+0xef00, 0x1cfe)
		m.Write16(0x1e880+0xef02, 0xf67)
		m.Write16(0x1e880+0xef04, 5)
		switch name {
		case "inactive":
			r.Active = false
		case "done":
			r.Done = true
		case "front":
			m.Write16(0x1e880+0xef04, 0)
		case "caller":
			m.Write16(0x1e880+0xef00, 0x1cff)
		case "ordinary":
			r.Rows[0][r.Slots[0][5]] = ArmyStack{"native:01", 2}
		}
		before := bytes.Clone(m.Mem)
		regs, flags, cycles, ip := m.CPU.R, m.CPU.Flags, m.CPU.Cycles, m.CPU.IP
		_, err = p.begin(m)
		if name == "valid" {
			if err != nil || !p.Active {
				t.Fatal("valid spell entry", err)
			}
		} else if err == nil || p.Active {
			t.Fatal("unsafe spell entry", name, err)
		}
		if !bytes.Equal(before, m.Mem) || regs != m.CPU.R || flags != m.CPU.Flags || cycles != m.CPU.Cycles || ip != m.CPU.IP {
			t.Fatal("entry changed guest state", name)
		}
	}
	setupWrite(t, filepath.Join(work, "spell-entry-guards.json"), map[string]any{"refusals": 5, "valid_entry": 1, "guest_unchanged": true})
}

func TestOriginalSpellModels(t *testing.T) {
	work, _, _ := setupInputs(t)
	cases := []struct {
		Selector               int
		Kind                   uint16
		Source, Target         uint32
		HP                     uint64
		TargetKind, Stat, Want uint16
	}{
		{0, 12, 2, 35, 20, 16, 2, 5}, {1, 12, 2, 35, 20, 16, 2, 5},
		{0, 10, 2, 35, 20, 16, 2, 9}, {0, 10, 6, 35, 20, 16, 2, 24},
		{2, 12, 2, 35, 20, 11, 2, 23}, {2, 12, 2, 35, 20, 16, 2, 14},
		{3, 12, 2, 35, 20, 16, 2, 35}, {5, 12, 2, 35, 20, 16, 2, 18},
		{5, 12, 2, 34, 20, 16, 2, 18}, {7, 12, 2, 49, 20, 16, 2, 49},
		{7, 12, 2, 50, 20, 16, 2, 36}, {7, 12, 2, 69, 20, 16, 2, 41},
		{7, 10, 2, 69, 20, 16, 2, 62},
	}
	for _, c := range cases {
		got, err := originalSpellAmount(c.Selector, c.Kind, c.Source, c.Target, c.HP, c.TargetKind, c.Stat)
		if err != nil || got != c.Want {
			t.Fatal(c, got, err)
		}
	}
	refusals := [][7]uint64{{4, 12, 2, 35, 20, 16, 2}, {6, 12, 2, 35, 20, 16, 2}, {0, 0, 2, 35, 20, 16, 2}, {0, 12, 0, 35, 20, 16, 2}, {0, 12, 32768, 35, 20, 16, 2}, {0, 12, 2, 32768, 20, 16, 2}, {0, 12, 2, 35, 9, 16, 2}, {0, 10, 6, 35, 20, 16, 6000}, {7, 12, 2, 20000, 20, 16, 2}}
	for _, c := range refusals {
		if _, err := originalSpellAmount(int(c[0]), uint16(c[1]), uint32(c[2]), uint32(c[3]), c[4], uint16(c[5]), uint16(c[6])); err == nil {
			t.Fatal("unsafe spell amount", c)
		}
	}
	setupWrite(t, filepath.Join(work, "spell-models.json"), map[string]any{"cases": len(cases), "refusals": len(refusals)})
}

func spellEncounter(t *testing.T, e *game.Engine, selector int, cancel string, goMode bool, whole ...bool) error {
	t.Helper()
	prompt := false
	e.Oracle.OnCall(oracle.Far(0x110, 0x16e0), func(*oracle.Oracle) { prompt = e.PAMLoaded })
	setupPress(t, e, 0x50)
	setupPress(t, e, 0x50)
	for n := 0; !prompt && n < 128; n++ {
		key := byte(0x4d)
		if n%2 == 1 {
			key = 0x4b
		}
		setupPress(t, e, key)
	}
	if !prompt {
		t.Fatal("spell encounter prompt")
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
	cast, menu := false, false
	finished := false
	full := len(whole) > 0 && whole[0]
	node := -1
	pending := false
	entering := false
	e.Oracle.OnCall(oracle.Far(0xf67, 0x1cfe), func(*oracle.Oracle) { cast = false; pending = false; finished = true })
	e.Oracle.OnCall(oracle.Far(0xf67, 0x283f), func(*oracle.Oracle) { entering = false })
	var picker oracle.Regs
	pickerTarget := uint16(0)
	pickerNode := -1
	// Read the live cursor at the original BIOS poll. Queue one move per
	// acknowledged cursor transition, including repeated direction keys.
	e.Oracle.OnCall(oracle.Far(0xf67, 0x28a6), func(o *oracle.Oracle) {
		if !pending {
			return
		}
		r := o.Regs()
		at := o.Word(oracle.Far(r.SS, r.BP-10))
		if int(at) == pickerNode {
			return
		}
		pickerNode = int(at)
		if cast && (cancel == "target" || cancel == "target-space") {
			if cancel == "target-space" {
				o.PressScan(" ")
				return
			}
			o.PressKey(oracle.KeyEscape)
			return
		}
		if at == pickerTarget {
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
			n := queue[0]
			queue = queue[1:]
			for i, key := range []oracle.Key{oracle.KeyUp, oracle.KeyDown, oracle.KeyLeft, oracle.KeyRight} {
				next := uint16(o.Bytes(oracle.Far(0x1e88, 0x709a+n.at*4+uint16(i)), 1)[0])
				if next < 1 || next > 12 || seen[next] {
					continue
				}
				first := n.first
				if n.at == at {
					first = key
				}
				if next == pickerTarget {
					o.PressKey(first)
					return
				}
				seen[next] = true
				queue = append(queue, path{next, first})
			}
		}
		t.Fatal("live spell cursor has no path", at, pickerTarget)
	})
	e.Oracle.OnCall(oracle.Far(0xf67, 0x334), func(*oracle.Oracle) { cast = true; pending = false })
	e.Oracle.OnCall(oracle.Far(0xf67, 0x122), func(*oracle.Oracle) { menu = true; node = -1 })
	e.Oracle.OnCall(oracle.Far(0xf67, 0x2b4), func(o *oracle.Oracle) {
		if !menu {
			return
		}
		r := o.Regs()
		cursor := int(o.Word(oracle.Far(r.SS, r.BP-6)))
		if cursor == node {
			return
		}
		node = cursor
		if full && finished {
			o.PressScan(" ")
			menu = false
		} else if cancel == "menu" {
			o.PressKey(oracle.KeyEscape)
			menu = false
		} else if cursor == selector {
			o.PressKey(oracle.KeyEnter)
			menu = false
		} else {
			o.PressKey(oracle.KeyDown)
		}
	})
	e.Oracle.OnCall(oracle.Far(0xf67, 0x283e), func(o *oracle.Oracle) {
		if entering {
			return
		}
		entering = true
		pending = true
		picker = o.Regs()
		picker.IP = o.Word(oracle.Far(picker.SS, picker.SP))
		picker.CS = o.Word(oracle.Far(picker.SS, picker.SP+2))
		picker.SP += 4
		target := uint16(0)
		mapBase, unitBase, offset := uint16(0x6fc2), uint16(0x5700), uint16(1)
		if cast && selector == 6 {
			mapBase, unitBase, offset = 0x6fb6, 0x56e8, 7
		}
		for slot := uint16(0); slot < 6; slot++ {
			raw := o.Word(oracle.Far(0x1e88, mapBase+slot*2))
			if raw < 6 && o.Word(oracle.Far(0x1e88, unitBase+2+raw*4)) > 0 {
				target = slot + offset
				break
			}
		}
		if target == 0 {
			t.Fatal("spell input has no target")
		}
		pickerTarget = target
		pickerNode = -1
	})
	steps := e.Oracle.Steps()
	released := false
	e.Oracle.SetStepGuard(func(o *oracle.Oracle) error {
		r := o.Regs()
		if pending && r.CS == picker.CS && r.IP == picker.IP && r.SP == picker.SP {
			pending = false
		}
		if cast && !goMode && !full && r.CS == 0xf67 && r.IP == 0x1cfe {
			return errOriginalSpellHeld
		}
		if !released && o.Steps() > steps+100000 {
			if er := e.Key(0x1c, false); er != nil {
				return er
			}
			released = true
		}
		if o.Steps() > steps+160000000 {
			return errors.New("spell input budget")
		}
		return nil
	})
	if err := e.Key(0x1c, true); err != nil {
		t.Fatal(err)
	}
	var err error
	for {
		err = e.AdvanceCycles(100000)
		e.RenderAudio()
		if err != nil {
			break
		}
	}
	e.Oracle.SetStepGuard(nil)
	return err
}

func TestOriginalBattleSpells(t *testing.T) {
	work, root, catalog := setupInputs(t)
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
	parent := filepath.Join(work, "casts-r1")
	must(os.MkdirAll(parent, 0700))
	for _, sc := range []struct {
		Name     string
		HD       bool
		Selector int
		Cancel   string
	}{
		{"fireball-hd", true, 0, ""}, {"thunder-hd", true, 1, ""}, {"exorcism-hd", true, 2, ""}, {"assassination-hd", true, 3, ""}, {"assassination-fail-hd", true, 3, ""}, {"halve-hd", true, 5, ""}, {"quake-hd", true, 7, ""}, {"fireball-native", false, 0, ""}, {"cancel-menu", true, 0, "menu"}, {"cancel-target", true, 0, "target"}, {"cancel-target-space", true, 0, "target-space"},
	} {
		t.Run(sc.Name, func(t *testing.T) {
			must := func(err error) {
				t.Helper()
				if err != nil {
					t.Fatal(err)
				}
			}
			var reference map[string]any
			for mode := 0; mode < 2; mode++ {
				dir := filepath.Join(parent, fmt.Sprintf("%s-mode-%d", sc.Name, mode))
				must(os.Mkdir(dir, 0700))
				e := setupCold(t, root, assets, dir, sc.HD)
				events := []map[string]any{}
				for _, ip := range []uint16{0x1daa, 0x334, 0x122, 0x2b4, 0x31e, 0x283e, 0x28b4, 0x345c, 0x1cfe} {
					ip := ip
					e.Oracle.OnCall(oracle.Far(0xf67, ip), func(o *oracle.Oracle) {
						if len(events) < 40 {
							regs := o.Regs()
							events = append(events, map[string]any{"ip": ip, "regs": regs, "menu_node": o.Word(oracle.Far(regs.SS, regs.BP-6)), "picker_node": o.Word(oracle.Far(regs.SS, regs.BP-10)), "picker_arg": o.Word(oracle.Far(regs.SS, regs.SP+4)), "learned": o.Word(oracle.Far(0x1e88, 0x26aa)), "charges": fmt.Sprintf("%x", o.Bytes(oracle.Far(0x1e88, 0x2aa8), 16))})
						}
					})
				}
				player := [6]ArmyStack{{"native:01", 30}, {"native:12", 2}}
				// Explicit original-ABI fixture, applied before formation/HP setup.
				e.Oracle.OnCall(oracle.Far(0xf67, 0x1daa), func(o *oracle.Oracle) {
					o.WriteU16(oracle.Far(0x1e88, 0x26aa), 1)
					o.WriteU16(oracle.Far(0x1e88, 0x26b0), 2)
					o.WriteU16(oracle.Far(0x1e88, 0x26ae), 4)
					if sc.Name == "assassination-fail-hd" {
						o.WriteU16(oracle.Far(0x1e88, 0x26ae), 0)
					}
					for i := uint16(0); i < 8; i++ {
						o.WriteU16(oracle.Far(0x1e88, 0x2aa8+i*2), 3)
					}
				})
				var spells *originalBattleSpells
				var rounds *originalBattleRounds
				if mode == 0 {
					e.Oracle.OnCall(oracle.Far(0x110, 0x3365), func(o *oracle.Oracle) {
						for i, s := range player {
							p := catalog.Profiles[s.Unit]
							o.WriteU16(oracle.Far(0x1e88, 0x54a+uint16(i*4)), p.NativeKind)
							o.WriteU16(oracle.Far(0x1e88, 0x54c+uint16(i*4)), uint16(s.Count))
						}
					})
				} else {
					_, er := installOriginalArmyProjection(e, catalog, player)
					must(er)
					setup, er := installOriginalBattleSetup(e, catalog, nil)
					must(er)
					a, er := installOriginalBattleActions(e, setup, true)
					must(er)
					rounds, er = installOriginalBattleRounds(e, a)
					must(er)
					spells, er = installOriginalBattleSpells(e, rounds)
					must(er)
					spells.Hold = true
				}
				err := spellEncounter(t, e, sc.Selector, sc.Cancel, mode == 1)
				if !errors.Is(err, errOriginalSpellHeld) {
					must(e.Oracle.SaveStateFile(filepath.Join(dir, "failed.state")))
					f, er := os.Create(filepath.Join(dir, "failed.png"))
					must(er)
					must(png.Encode(f, e.Frame()))
					must(f.Close())
					setupWrite(t, filepath.Join(dir, "failed-events.json"), events)
					t.Fatal("cast", err, e.Oracle.Regs())
				}
				frame := e.Frame()
				f, er := os.Create(filepath.Join(dir, "frame.png"))
				must(er)
				must(png.Encode(f, frame))
				must(f.Close())
				must(e.Oracle.SaveStateFile(filepath.Join(dir, "held.state")))
				row := map[string]any{"name": sc.Name, "hd": sc.HD, "selector": sc.Selector, "cancel": sc.Cancel, "mode": mode, "units_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x56e8), 48)), "hp_hex": fmt.Sprintf("%x", append(e.Oracle.Bytes(oracle.Far(0x1e88, 0x8ca4), 12), e.Oracle.Bytes(oracle.Far(0x1e88, 0x8e60), 12)...)), "charges_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x2aa8), 16)), "seed": originalSeed(e.Oracle), "frame_sha256": contentSHA(frame.Pix), "controlled_abi_fixture": true}
				if mode == 0 {
					reference = row
				} else {
					for _, key := range []string{"units_hex", "hp_hex", "charges_hex", "seed", "frame_sha256"} {
						if reference[key] != row[key] {
							t.Fatal("original/Go spell differs", sc.Name, key, reference[key], row[key])
						}
					}
					if len(spells.Records) != 1 {
						t.Fatal("spell not recorded")
					}
					row["record"] = spells.Records[0]
					row["rows"] = rounds.Rows
					before := e.Oracle.Bytes(oracle.Far(0, 0), 1<<20)
					cycles := e.Oracle.Cycles()
					for k := 0; k < 5; k++ {
						if er := e.AdvanceCycles(100000); !errors.Is(er, errOriginalSpellHeld) {
							t.Fatal("spell hold", er)
						}
					}
					if !bytes.Equal(before, e.Oracle.Bytes(oracle.Far(0, 0), 1<<20)) || cycles != e.Oracle.Cycles() {
						t.Fatal("spell hold mutated state")
					}
				}
				setupWrite(t, filepath.Join(dir, "receipt.json"), row)
				e.Close()
			}
		})
		if t.Failed() {
			break
		}
	}
}

func TestOriginalSpellWorld(t *testing.T) {
	originalSpellWorld(t, "spell-world-r1", 0, [6]ArmyStack{{"native:01", 74}, {"native:12", 2}, {"openkb:wolf", 1}, {"openkb:arcr", 1}}, false)
}

func originalSpellWorld(t *testing.T, name string, selector int, player [6]ArmyStack, withSupport bool) {
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
	dir := filepath.Join(work, name)
	must(os.Mkdir(dir, 0700))
	var catalog ArmyCatalog
	raw, err := os.ReadFile(filepath.Join(work, "inputs/army-catalog.json"))
	must(err)
	must(pairStrictJSON(raw, &catalog))
	session := filepath.Join(dir, "session")
	must(importNativeProgress(root, root, session, filepath.Join(work, "inputs"), catalog, combat))
	store, snap, err := openProgressPair(session, catalog, combat)
	must(err)
	defer store.Close()
	w := snap.World
	w.Army.Slots = player
	w.Army.Rules = "formation"
	w.Revision++
	snap, err = store.Commit(snap.Token, w)
	must(err)
	port := &worldArmyPort{Store: store, Current: snap}
	must(materializeNativeCheckpoint(root, filepath.Join(work, "inputs"), filepath.Join(dir, "scratch"), snap))
	e := setupCold(t, root, assets, dir, true)
	defer e.Close()
	e.Oracle.OnCall(oracle.Far(0xf67, 0x1daa), func(o *oracle.Oracle) {
		o.WriteU16(oracle.Far(0x1e88, 0x26aa), 1)
		o.WriteU16(oracle.Far(0x1e88, 0x26b0), 2)
		o.WriteU16(oracle.Far(0x1e88, 0x26ae), 4)
		for i := uint16(0); i < 8; i++ {
			o.WriteU16(oracle.Far(0x1e88, 0x2aa8+i*2), 3)
		}
	})
	projection, err := installOriginalArmyProjectionMode(e, combat, player, true)
	must(err)
	setup, err := installOriginalBattleSetup(e, combat, &player)
	must(err)
	actions, err := installOriginalBattleActions(e, setup, true)
	must(err)
	rounds, err := installOriginalBattleRounds(e, actions)
	must(err)
	projection.Rounds = rounds
	spells, err := installOriginalBattleSpells(e, rounds)
	must(err)
	var support *originalBattleSupport
	if withSupport {
		support, err = installOriginalBattleSupport(e, spells)
		must(err)
	}
	world, err := installOriginalBattleWorld(e, port, projection, rounds)
	must(err)
	checkpoint, err := installNativeCheckpoint(e, port, filepath.Join(dir, "scratch"))
	must(err)
	err = spellEncounter(t, e, selector, "", true, true)
	if !errors.Is(err, errOriginalBattleRoundsHeld) {
		must(e.Oracle.SaveStateFile(filepath.Join(dir, "failed-battle.state")))
		setupWrite(t, filepath.Join(dir, "failed-battle.json"), map[string]any{"error": fmt.Sprint(err), "regs": e.Oracle.Regs(), "spells": spells.Records, "rows": rounds.Rows, "history": rounds.History})
		t.Fatal("spell continuous battle", err)
	}
	applied := len(spells.Records) > 0 && len(spells.Records[0].Effects) > 0
	if support != nil {
		applied = len(support.Records) > 0 && support.Records[0].Selector == selector
	}
	if rounds.Result != "win" || !applied || len(rounds.History) < 2 {
		t.Fatal("spell/ordinary battle not completed", rounds.Result, len(spells.Records), len(rounds.History))
	}
	rounds.AllowWorld = true
	phase := true
	last := uint64(0)
	e.Oracle.OnCall(oracle.Far(0x160a, 0x87), func(o *oracle.Oracle) {
		if phase && o.Steps()-last > 50000 {
			last = o.Steps()
			o.PressKey(oracle.KeyEnter)
		}
	})
	stop := errors.New("spell world returned")
	start := e.Oracle.Steps()
	e.Oracle.SetStepGuard(func(o *oracle.Oracle) error {
		if world.Returned {
			return stop
		}
		if o.Steps() > start+50000000 {
			return errors.New("spell world budget")
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
	phase = false
	if !errors.Is(err, stop) || !world.Committed {
		t.Fatal("spell world return", err)
	}
	e.ReleaseAll()
	setupAdvance(t, e, 500)
	charges := fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x2aa8), 16))
	file, err := os.Create(filepath.Join(dir, "map.png"))
	must(err)
	must(png.Encode(file, e.Frame()))
	must(file.Close())
	location := checkpointLocation(e.Oracle)
	setupPress(t, e, 0x41)
	setupPress(t, e, 0x1c)
	setupPress(t, e, 0x1c)
	setupAdvance(t, e, 700)
	e.ReleaseAll()
	if checkpoint.Saves != 1 {
		t.Fatal("spell F7", checkpoint.Saves)
	}
	saved, err := store.Recover()
	must(err)
	if saved.World.Army.Slots != projection.Remaining {
		t.Fatal("spell survivors not saved")
	}
	must(e.Oracle.SaveStateFile(filepath.Join(dir, "saved.state")))
	if support != nil {
		setupWrite(t, filepath.Join(dir, "support.json"), map[string]any{"records": support.Records, "growth": support.Growth, "counters": support.Counters, "consumes": support.Consumes, "reads": support.Reads})
	}
	setupWrite(t, filepath.Join(dir, "receipt.json"), map[string]any{"status": "passed-original-spell-world", "initial": player, "remaining": saved.World.Army.Slots, "world_sha256": worldDigest(saved.World), "charges_hex": charges, "records": spells.Records, "ordinary_actions": len(rounds.History), "result": rounds.Result, "resources": pairWorldResources(saved.World), "location": location, "checkpoint_saves": checkpoint.Saves, "controlled_abi_fixture": true, "battle_rules_applied": "native", "stored_rules": saved.World.Army.Rules})
}
