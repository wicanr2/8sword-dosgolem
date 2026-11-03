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

func casualtyFixture(t *testing.T, code []byte, catalog game.OwnedCombatCatalog, id string, count uint32) (*dg.Machine, *originalBattleCasualties) {
	t.Helper()
	rows := [2][6]ArmyStack{{{id, count}}, {{"native:06", 44}}}
	m, a := actionFixture(t, code, catalog, rows)
	target := originalEnemyTarget{IP: 0x484c, Caller: 0x1818, SourceSlot: 0, TargetSlot: 0, SourceRaw: 0, TargetRaw: 0, Source: rows[1][0], Target: rows[0][0]}
	a.Target = &target
	x := &originalBattleCasualties{Actions: a}
	a.Casualties = x
	m.CPU.IP = 0x484c
	for i, v := range []uint16{0x1818, 0xf67, 0, 0} {
		m.Write16(0x1e880+0xef00+uint32(i*2), v)
	}
	for side, base := range []uint32{0x8ca4, 0x8e60} {
		for i, n := range a.Setup.Plan.NativeHP[side] {
			m.Write16(0x1e880+base+uint32(i*2), n)
		}
	}
	m.Write16(0x1e880+0x26ac, 0)
	return m, x
}

func casualtyCall(t *testing.T, m *dg.Machine, x *originalBattleCasualties, ret uint16) {
	t.Helper()
	m.CPU.IP = 0x1532
	m.CPU.R[dg.SP] = 0xeb00
	for i, v := range []uint16{ret, 0xf67, 0, 0} {
		m.Write16(0x1e880+0xeb00+uint32(i*2), v)
	}
	if _, err := x.helper(m); err != nil {
		t.Fatal(err)
	}
}

func casualtyImpactFrame(m *dg.Machine, x *originalBattleCasualties) {
	bp := x.ImpactSP - 2
	m.CPU.R[dg.BP] = bp
	m.CPU.R[dg.SP] = x.ImpactSP - 12
	for i, v := range []uint16{x.ImpactBP, x.ImpactReturn, 0xf67} {
		m.Write16(0x1e880+uint32(bp)+uint32(i*2), v)
	}
}

func TestOriginalBattleCasualtyModels(t *testing.T) {
	work, _, catalog := setupInputs(t)
	pam, err := os.ReadFile(filepath.Join(work, "inputs/PAM.AY"))
	if err != nil {
		t.Fatal(err)
	}
	code, err := worldArmyCode(pam)
	if err != nil {
		t.Fatal(err)
	}
	reports := []map[string]any{}
	ids := append([]string{"native:01"}, openKBArtIDs...)
	for _, id := range ids {
		for _, count := range []uint32{1, 100} {
			m, x := casualtyFixture(t, code, catalog, id, count)
			if _, err = x.enter(m); err != nil {
				t.Fatal(err)
			}
			casualtyCall(t, m, x, 0x48b2)
			encoded := x.Record.Calls[0].Encoded
			if encoded > 1 {
				m.CPU.IP = 0x4626
				m.CPU.R[dg.SP] = 0xed00
				m.CPU.R[dg.BP] = 0xeefe
				for i, v := range []uint16{0x4b12, 0xf67, 0, 0} {
					m.Write16(0x1e880+0xed00+uint32(i*2), v)
				}
				if _, err = x.impactEnter(m); err != nil {
					t.Fatal(err)
				}
				casualtyCall(t, m, x, 0x4658)
				casualtyImpactFrame(m, x)
				m.CPU.IP = 0x46da
				m.CPU.R[dg.BX] = 0
				if _, err = x.readCount(m, 0x46da); err != nil || uint32(m.CPU.R[dg.SI]) != count {
					t.Fatal("Go count read", err)
				}
				ip := uint16(0x4730)
				if x.Record.After == 0 {
					ip = 0x47d0
				}
				for _, v := range x.Record.PlannedDisplay {
					m.CPU.IP = ip
					m.CPU.R[dg.AX] = v
					m.CPU.R[dg.BX] = 0
					if id == "native:01" {
						n := dg.New()
						copy(n.Mem, m.Mem)
						n.CPU.R = m.CPU.R
						n.CPU.Seg = m.CPU.Seg
						n.CPU.IP = m.CPU.IP
						n.CPU.Flags = m.CPU.Flags
						if er := n.Step(); er != nil {
							t.Fatal(er)
						}
						if _, err = x.writeCount(m, ip); err != nil {
							t.Fatal(err)
						}
						if !bytes.Equal(n.Mem, m.Mem) || n.CPU.R != m.CPU.R || n.CPU.IP != m.CPU.IP || n.CPU.Flags != m.CPU.Flags {
							t.Fatal("original/Go countdown write differs")
						}
					} else {
						if _, err = x.writeCount(m, ip); err != nil {
							t.Fatal(err)
						}
						if m.Read16(0x1e880+0x56ea) != 0 {
							t.Fatal("extension countdown escaped")
						}
					}
					if x.Rows[0][0].Count != count {
						t.Fatal("display changed authoritative count")
					}
				}
				if x.Record.After == 0 {
					for _, ip := range []uint16{0x4825, 0x4829} {
						m.CPU.IP = ip
						m.CPU.R[dg.AX] = 0
						m.CPU.R[dg.SI] = 0
						if _, err = x.writeCount(m, ip); err != nil {
							t.Fatal(err)
						}
					}
				}
				m.CPU.IP = 0x4847
				if _, err = x.commit(m); err != nil {
					t.Fatal(err)
				}
				if _, err = x.commit(m); err != nil || x.Record.Updates != 1 {
					t.Fatal("repeat commit", err)
				}
			}
			m.CPU.IP = 0x1818
			m.CPU.R[dg.SP] = x.EntrySP + 4
			m.CPU.R[dg.BP] = x.EntryBP
			if _, err = x.finish(m, 0x1818); !errors.Is(err, errOriginalBattleCasualtiesHeld) {
				t.Fatal(err)
			}
			if x.Record.Updates != 1 || x.Rows[0][0].Count != x.Record.After {
				t.Fatal("Go authoritative commit")
			}
			before := bytes.Clone(m.Mem)
			cycles := m.CPU.Cycles
			for n := 0; n < 5; n++ {
				if _, er := x.finish(m, 0x1818); !errors.Is(er, errOriginalBattleCasualtiesHeld) {
					t.Fatal(er)
				}
			}
			if !bytes.Equal(before, m.Mem) || cycles != m.CPU.Cycles || x.Record.Updates != 1 {
				t.Fatal("held return repeated damage")
			}
			reports = append(reports, map[string]any{"id": id, "count": count, "record": x.Record, "HP": x.HP[0][0], "native_hex": fmt.Sprintf("%x", x.Projected[:4]), "held_retries": 5})
		}
	}
	refusals := []string{"source", "caller", "projection", "HP-word", "helper-repeat", "wide-target", "display-value", "missing-display"}
	for _, name := range refusals {
		count := uint32(100)
		if name == "wide-target" {
			count = 4294967295
		}
		m, x := casualtyFixture(t, code, catalog, "openkb:wolf", count)
		var attempt func() (bool, error)
		if name == "wide-target" {
			attempt = func() (bool, error) { return x.enter(m) }
		} else {
			if _, err = x.enter(m); err != nil {
				t.Fatal(err)
			}
			m.CPU.IP = 0x1532
			m.CPU.R[dg.SP] = 0xeb00
			for i, v := range []uint16{0x48b2, 0xf67, 0, 0} {
				m.Write16(0x1e880+0xeb00+uint32(i*2), v)
			}
			attempt = func() (bool, error) { return x.helper(m) }
			switch name {
			case "source":
				m.Mem[0xf670+0x1532] ^= 1
			case "caller":
				m.Write16(0x1e880+0xeb00, 0x1234)
			case "projection":
				m.Write16(0x1e880+0x56ea, 1)
			case "HP-word":
				m.Write16(0x1e880+0x8ca4, 1)
			case "helper-repeat":
				x.Record.Calls = []originalCasualtyAmount{{Encoded: 2}}
			case "display-value", "missing-display":
				casualtyCall(t, m, x, 0x48b2)
				m.CPU.IP = 0x4626
				m.CPU.R[dg.SP] = 0xed00
				m.CPU.R[dg.BP] = 0xeefe
				for i, v := range []uint16{0x4b12, 0xf67, 0, 0} {
					m.Write16(0x1e880+0xed00+uint32(i*2), v)
				}
				if _, err = x.impactEnter(m); err != nil {
					t.Fatal(err)
				}
				casualtyCall(t, m, x, 0x4658)
				casualtyImpactFrame(m, x)
				if name == "display-value" {
					m.CPU.IP = 0x4730
					m.CPU.R[dg.BX] = 0
					m.CPU.R[dg.AX] = 123
					attempt = func() (bool, error) { return x.writeCount(m, 0x4730) }
				} else {
					m.CPU.IP = 0x4847
					attempt = func() (bool, error) { return x.commit(m) }
				}
			}
		}
		before := bytes.Clone(m.Mem)
		regs, flags, ip, cycles := m.CPU.R, m.CPU.Flags, m.CPU.IP, m.CPU.Cycles
		hp := x.HP
		updates := x.Record.Updates
		calls := len(x.Record.Calls)
		display := len(x.Record.Display)
		if _, er := attempt(); er == nil {
			t.Fatal("unsafe casualty admitted", name)
		}
		if !bytes.Equal(before, m.Mem) || regs != m.CPU.R || flags != m.CPU.Flags || ip != m.CPU.IP || cycles != m.CPU.Cycles || hp != x.HP || updates != x.Record.Updates || calls != len(x.Record.Calls) || display != len(x.Record.Display) {
			t.Fatal("refusal mutated casualty", name)
		}
	}
	setupWrite(t, filepath.Join(work, "casualty-models.json"), map[string]any{"status": "passed-original-battle-casualty-models", "rows": reports, "refusals": refusals})
}

func casualtyOracleStop(e *game.Engine) (*originalEnemyTarget, *uint64) {
	target := &originalEnemyTarget{}
	seen := new(uint64)
	var sp, bp uint16
	e.Oracle.OnCall(oracle.Far(0xf67, 0x484c), func(o *oracle.Oracle) {
		if *seen != 0 {
			return
		}
		*seen++
		r := o.Regs()
		sp, bp = r.SP, r.BP
		ss := r.SS
		target.IP = 0x484c
		target.Caller = o.Word(oracle.Far(ss, sp))
		target.SourceSlot = o.Word(oracle.Far(ss, sp+4))
		target.TargetSlot = o.Word(oracle.Far(ss, sp+6))
	})
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x1818), func(m *dg.Machine) (bool, error) {
		if *seen == 0 {
			return false, nil
		}
		if m.CPU.R[dg.SP] != sp+4 || m.CPU.R[dg.BP] != bp {
			return false, errors.New("oracle melee return frame")
		}
		return false, errOriginalBattleCasualtiesHeld
	})
	return target, seen
}

func TestOriginalBattleCasualtyCold(t *testing.T) {
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
		var refSeed uint32
		for mode := 0; mode < 2; mode++ {
			dir := filepath.Join(folder, fmt.Sprintf("hd-%v-mode-%d", hd, mode))
			must(os.Mkdir(dir, 0700))
			e := setupCold(t, root, assets, dir, hd)
			var x *originalBattleCasualties
			var err error
			if mode == 0 {
				casualtyOracleStop(e)
			} else {
				s, er := installOriginalBattleSetup(e, catalog, nil)
				must(er)
				a, er := installOriginalBattleActions(e, s, true)
				must(er)
				x, err = installOriginalBattleCasualties(e, a)
				must(err)
			}
			err = setupEncounter(t, e, true)
			if !errors.Is(err, errOriginalBattleCasualtiesHeld) {
				t.Fatal("full melee did not complete", err)
			}
			im := e.Frame()
			units := e.Oracle.Bytes(oracle.Far(0x1e88, 0x56e8), 48)
			hp := append(e.Oracle.Bytes(oracle.Far(0x1e88, 0x8ca4), 12), e.Oracle.Bytes(oracle.Far(0x1e88, 0x8e60), 12)...)
			seed := originalSeed(e.Oracle)
			if mode == 0 {
				refFrame, refUnits, refHP, refSeed = bytes.Clone(im.Pix), bytes.Clone(units), bytes.Clone(hp), seed
			} else if !bytes.Equal(im.Pix, refFrame) || !bytes.Equal(units, refUnits) || !bytes.Equal(hp, refHP) || seed != refSeed || x.Record.Updates != 1 || !x.Complete {
				t.Fatal("native/Go full melee differs", hd, fmt.Sprintf("%x", units), fmt.Sprintf("%x", refUnits), x.Record)
			}
			f, er := os.Create(filepath.Join(dir, "frame.png"))
			must(er)
			must(png.Encode(f, im))
			must(f.Close())
			must(e.Oracle.SaveStateFile(filepath.Join(dir, "held.state")))
			row := map[string]any{"hd": hd, "mode": mode, "units_hex": fmt.Sprintf("%x", units), "pending_hp_hex": fmt.Sprintf("%x", hp), "seed_after": seed, "frame_rgba_sha256": contentSHA(im.Pix)}
			if x != nil {
				row["record"] = x.Record
			}
			reports = append(reports, row)
			e.Close()
		}
	}
	setupWrite(t, filepath.Join(work, "cold-receipt.json"), map[string]any{"status": "passed-original-battle-casualty-cold", "rows": reports, "normal_cold_start": true, "snapshot_loaded": false, "seed": uint32(0x12345678)})
}

func TestOriginalBattleCasualtyExpanded(t *testing.T) {
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
	for i, count := range []uint32{2, 100} {
		dir := filepath.Join(folder, fmt.Sprint(i))
		must(os.Mkdir(dir, 0700))
		e := setupCold(t, root, assets, dir, true)
		player := [6]ArmyStack{{"openkb:wolf", count}, {"native:01", 30}}
		shadow := e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)
		projection, err := installOriginalArmyProjectionMode(e, catalog, player, true)
		must(err)
		s, err := installOriginalBattleSetup(e, catalog, &player)
		must(err)
		a, err := installOriginalBattleActions(e, s, true)
		must(err)
		x, err := installOriginalBattleCasualties(e, a)
		must(err)
		firstSideSet := false
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x2076), func(m *dg.Machine) (bool, error) {
			if er := a.check(m, 0x2076, 0x205e6, 0x20689); er != nil {
				return false, er
			}
			sp := uint32(m.CPU.R[dg.SP])
			if sp > 65529 || m.Read16(0x1e880+sp) != 0x3c || m.Read16(0x1e880+sp+2) != 0xf67 {
				return false, errors.New("controlled enemy-first caller")
			}
			if !firstSideSet {
				if m.Read16(0x1e880+sp+4) != 0 {
					return false, errors.New("controlled first side")
				}
				m.Write16(0x1e880+sp+4, 1)
				firstSideSet = true
			}
			return false, nil
		})
		err = setupEncounter(t, e, true)
		if !errors.Is(err, errOriginalBattleCasualtiesHeld) || !firstSideSet || !x.Complete || x.Record.Updates != 1 || len(x.Record.Calls) != 2 || projection.Captures != 0 {
			t.Fatal("expanded melee not complete", err, x.Record)
		}
		if (i == 0 && x.Record.After != 0) || (i == 1 && x.Record.After == 0) {
			t.Fatal("expanded boundary outcome", x.Record)
		}
		mem := e.Oracle.Bytes(oracle.Far(0, 0), 1<<20)
		cycles := e.Oracle.Cycles()
		seed := originalSeed(e.Oracle)
		for n := 0; n < 5; n++ {
			if er := e.AdvanceCycles(100000); !errors.Is(er, errOriginalBattleCasualtiesHeld) {
				t.Fatal(er)
			}
		}
		if !bytes.Equal(mem, e.Oracle.Bytes(oracle.Far(0, 0), 1<<20)) || cycles != e.Oracle.Cycles() || seed != originalSeed(e.Oracle) || x.Record.Updates != 1 || !bytes.Equal(shadow, e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)) || !bytes.Equal(e.Oracle.Bytes(oracle.Far(0x1e88, 0x56e8), 4), make([]byte, 4)) || e.Oracle.Word(oracle.Far(0x1e88, 0x8ca4)) != 0 {
			t.Fatal("expanded result isolation")
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
		reports = append(reports, map[string]any{"case": i, "record": x.Record, "rows": x.Rows, "pending_HP": x.HP, "native_rows_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x56e8), 48)), "seed_after": seed, "held_retries": 5, "frame_rgba_sha256": contentSHA(im.Pix), "controlled_typed_override": true, "controlled_enemy_first_argument": true})
		e.Close()
	}
	setupWrite(t, filepath.Join(work, "expanded-receipt.json"), map[string]any{"status": "passed-original-battle-casualty-expanded", "rows": reports, "playable": false, "actual_window_verified": false, "scope": "First enemy ordinary melee and authoritative Go casualties only; held before next action. New unit hit/death poses remain unimplemented."})
}
