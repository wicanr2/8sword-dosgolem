package ownedworld

import (
	"bytes"
	"encoding/json"
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

func originalBattleInputs(t *testing.T) (string, string, game.OwnedCombatCatalog) {
	t.Helper()
	work, root := os.Getenv("EIGHTSWORD_ORIGINAL_BATTLE_WORK"), os.Getenv("EIGHTSWORD_TEST_ORIG")
	if work == "" || root == "" {
		t.Skip("fixed original battle inputs required")
	}
	var c game.OwnedCombatCatalog
	b, err := os.ReadFile(filepath.Join(work, "inputs/combat-catalog.json"))
	if err != nil {
		t.Fatal(err)
	}
	if err = pairStrictJSON(b, &c); err != nil {
		t.Fatal(err)
	}
	return work, root, c
}

func TestOriginalBattleArithmeticControls(t *testing.T) {
	work, root, catalog := originalBattleInputs(t)
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	folder := filepath.Join(work, "helper-controls-r1")
	must(os.Mkdir(folder, 0700))
	rows := []map[string]any{}
	for _, ip := range []uint16{0x1532, 0x1592} {
		for _, count := range []uint16{1, 7, 30, 49} {
			var controlAX, controlHP uint16
			for mode := 0; mode < 2; mode++ {
				dir := filepath.Join(folder, fmt.Sprintf("%04x-%d-%d", ip, count, mode))
				must(os.Mkdir(dir, 0700))
				e, err := game.Open(game.Options{Root: root, Saves: filepath.Join(dir, "scratch")})
				must(err)
				must(e.Oracle.LoadStateFile(filepath.Join(work, "inputs/start.state")))
				writeOriginalSeed(e.Oracle, 0x12345678)
				var bridge *originalBattleArithmetic
				if mode == 1 {
					bridge, err = installOriginalBattleArithmetic(e, catalog)
					must(err)
				}
				ret, hpBase := uint16(0x4658), uint16(0x8ca4)
				if ip == 0x1592 {
					ret, hpBase = 0x32d9, 0x8e60
				}
				initialIP := e.Oracle.IP()
				setup := false
				swordOnHostInstruction(e.Oracle, initialIP, func(m *dg.Machine) (bool, error) {
					if setup {
						return false, errors.New("repeated fixture entry")
					}
					setup = true
					c := m.CPU
					c.Seg[dg.CS] = 0xf67
					c.Seg[dg.DS] = 0x1e88
					c.Seg[dg.SS] = 0x1e88
					c.R[dg.SP] = 0xef00
					c.IP = ip
					base := uint32(0x1e880)
					for i, v := range []uint16{ret, 0xf67, 0, 0} {
						m.Write16(base+0xef00+uint32(i*2), v)
					}
					sBase, tBase := uint32(0x5700), uint32(0x56e8)
					if ip == 0x1592 {
						sBase, tBase = tBase, sBase
					}
					m.Write16(base+sBase, 6)
					m.Write16(base+sBase+2, count)
					m.Write16(base+tBase, 1)
					m.Write16(base+tBase+2, 30)
					m.Write16(base+0x26ac, 0)
					m.Write16(base+0x26b2, 0)
					m.Write16(base+0x26b8, 0)
					m.Write16(base+uint32(hpBase), 1000)
					c.Cycles++
					return true, nil
				})
				must(e.Oracle.RunUntil(oracle.NewCond("original helper far return", func(o *oracle.Oracle) bool {
					r := o.Regs()
					return setup && r.CS == 0xf67 && r.IP == ret && r.SP == 0xef04
				}), oracle.Budget(10000)))
				ax, hp := e.Oracle.Regs().AX, e.Oracle.Word(oracle.Far(0x1e88, hpBase))
				if originalSeed(e.Oracle) != 0x12345678 {
					t.Fatal("ordinary helper changed RNG")
				}
				must(e.Oracle.SaveStateFile(filepath.Join(dir, "after.state")))
				if mode == 0 {
					controlAX, controlHP = ax, hp
				} else {
					if ax != controlAX || hp != controlHP || len(bridge.Calls) != 1 {
						t.Fatal("Go/native helper differs", ip, count, ax, hp, controlAX, controlHP, bridge.Calls)
					}
					rows = append(rows, map[string]any{"ip": ip, "count": count, "native_ax": controlAX, "native_hp": controlHP, "go": bridge.Calls[0]})
				}
				e.Close()
			}
		}
	}
	amount, encoded, err := originalBattleAmountFor(100, 3000, 20, 5, 1)
	must(err)
	if amount != 60000 || encoded != 3001 {
		t.Fatal("wide model", amount, encoded)
	}
	if _, _, err = originalBattleAmountFor(100, 4000, 20, 5, 1); err == nil {
		t.Fatal("word projection overflow admitted")
	}
	write := func(name string, v any) {
		b, er := json.MarshalIndent(v, "", "  ")
		must(er)
		must(os.WriteFile(filepath.Join(folder, name), append(b, '\n'), 0600))
	}
	write("receipt.json", map[string]any{"status": "passed-original-battle-helper-controls", "cases": rows, "seed": uint32(0x12345678), "method": "same fixed snapshot; controlled original far-call stack; no RNG in helper; semantic return/HP comparison, not whole-state parity"})
}

func TestOriginalBattleArithmeticAction(t *testing.T) {
	work, root, catalog := originalBattleInputs(t)
	assets := os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if assets == "" {
		t.Skip("HD assets required")
	}
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	folder := filepath.Join(work, "action-r1")
	must(os.Mkdir(folder, 0700))
	reports := []map[string]any{}
	for _, hd := range []bool{false, true} {
		var referenceUnits, referenceHP, referenceFrame []byte
		var referenceCalls []map[string]uint16
		for mode := 0; mode < 2; mode++ {
			dir := filepath.Join(folder, fmt.Sprintf("hd-%v-mode-%d", hd, mode))
			must(os.Mkdir(dir, 0700))
			e, err := game.Open(game.Options{Root: root, Assets: assets, Saves: filepath.Join(dir, "scratch"), HD: hd})
			must(err)
			e.Oracle.SetClock(12, 0, 0, 0)
			e.EnableLiveClock(3000)
			ready, mapReady, prompt := false, false, false
			e.Oracle.OnCall(oracle.Far(0x110, 0x55a), func(*oracle.Oracle) { ready = e.PAMLoaded })
			e.Oracle.OnCall(oracle.Far(0x110, 0xb62), func(*oracle.Oracle) { mapReady = e.PAMLoaded })
			e.Oracle.OnCall(oracle.Far(0x110, 0x16e0), func(*oracle.Oracle) {
				if e.PAMLoaded {
					prompt = true
				}
			})
			advance := func(ms int) {
				t.Helper()
				for n := 0; n < ms; n += 10 {
					must(e.AdvanceCycles(30000))
					e.RenderAudio()
				}
			}
			press := func(scan byte) {
				t.Helper()
				must(e.Key(scan, true))
				advance(100)
				must(e.Key(scan, false))
				advance(300)
			}
			advance(1000)
			press(2)
			press(2)
			advance(1000)
			press(1)
			for n := 0; !ready && n < 2000; n++ {
				advance(10)
			}
			if !ready {
				t.Fatal("cold main menu")
			}
			press(0x1c)
			for n := 0; !mapReady && n < 2000; n++ {
				advance(10)
			}
			if !mapReady {
				t.Fatal("cold Continue")
			}
			writeOriginalSeed(e.Oracle, 0x12345678)
			var bridge *originalBattleArithmetic
			if mode == 1 {
				bridge, err = installOriginalBattleArithmetic(e, catalog)
				must(err)
			}
			var nativeCalls []map[string]uint16
			pending := false
			if mode == 0 {
				for _, ip := range []uint16{0x1532, 0x1592} {
					ip := ip
					e.Oracle.OnCall(oracle.Far(0xf67, ip), func(o *oracle.Oracle) {
						if pending {
							return
						}
						r := o.Regs()
						src, target := o.Word(oracle.Far(r.SS, r.SP+4)), o.Word(oracle.Far(r.SS, r.SP+6))
						if src >= 6 || target >= 6 {
							t.Fatal("native observer index")
						}
						base := uint16(0x8ca4)
						if ip == 0x1592 {
							base = 0x8e60
						}
						nativeCalls = append(nativeCalls, map[string]uint16{"ip": ip, "source": src, "target": target, "before_hp": o.Word(oracle.Far(r.DS, base+target*2)), "hp_base": base, "sp": r.SP, "return": o.Word(oracle.Far(r.SS, r.SP))})
						pending = true
					})
				}
				for _, ip := range []uint16{0x4658, 0x48b2, 0x32d9} {
					ip := ip
					e.Oracle.OnCall(oracle.Far(0xf67, ip), func(o *oracle.Oracle) {
						if !pending {
							return
						}
						last := nativeCalls[len(nativeCalls)-1]
						r := o.Regs()
						if last["return"] != ip || r.SP != last["sp"]+4 {
							return
						}
						last["encoded"] = r.AX
						last["after_hp"] = o.Word(oracle.Far(r.DS, last["hp_base"]+last["target"]*2))
						pending = false
					})
				}
			}
			entered := false
			var ret oracle.Regs
			e.Oracle.OnCall(oracle.Far(0xf67, 0x4626), func(o *oracle.Oracle) {
				if entered {
					return
				}
				entered = true
				r := o.Regs()
				ret = r
				ret.IP = o.Word(oracle.Far(r.SS, r.SP))
				ret.CS = o.Word(oracle.Far(r.SS, r.SP+2))
				ret.SP += 4
				must(o.SaveStateFile(filepath.Join(dir, "before-action.state")))
			})
			moves := []byte{0x50, 0x50}
			press(0x50)
			press(0x50)
			for n := 0; !prompt && n < 128; n++ {
				scan := byte(0x4d)
				if n%2 != 0 {
					scan = 0x4b
				}
				moves = append(moves, scan)
				press(scan)
			}
			if !prompt {
				t.Fatal("normal encounter prompt")
			}
			advance(500)
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
				press(0x4b)
			}
			stop := errors.New("complete ordinary action")
			start := e.Oracle.Steps()
			key := 0
			released := false
			e.Oracle.SetStepGuard(func(o *oracle.Oracle) error {
				r := o.Regs()
				if entered && r.CS == ret.CS && r.IP == ret.IP && r.SS == ret.SS && r.SP == ret.SP {
					return stop
				}
				if !released && o.Steps() >= start+100000 {
					must(e.Key(0x1c, false))
					released = true
				}
				if key < 6 && o.Steps() >= start+uint64(key+1)*2000000 {
					o.PressScan(" ")
					key++
				}
				if o.Steps() > start+60000000 {
					return errors.New("cold action budget")
				}
				return nil
			})
			must(e.Key(0x1c, true))
			for {
				err = e.AdvanceCycles(100000)
				e.RenderAudio()
				if err != nil {
					break
				}
			}
			if !errors.Is(err, stop) {
				t.Fatal("cold original action", hd, mode, err, e.Oracle.Regs())
			}
			units := e.Oracle.Bytes(oracle.Far(0x1e88, 0x56e8), 48)
			hp := append(e.Oracle.Bytes(oracle.Far(0x1e88, 0x8ca4), 12), e.Oracle.Bytes(oracle.Far(0x1e88, 0x8e60), 12)...)
			im = e.Frame()
			f, er := os.Create(filepath.Join(dir, "frame.png"))
			must(er)
			must(png.Encode(f, im))
			must(f.Close())
			must(e.Oracle.SaveStateFile(filepath.Join(dir, "after-action.state")))
			if mode == 0 {
				referenceUnits, referenceHP, referenceFrame = bytes.Clone(units), bytes.Clone(hp), bytes.Clone(im.Pix)
				referenceCalls = nativeCalls
			} else {
				if !bytes.Equal(referenceUnits, units) || !bytes.Equal(referenceHP, hp) || !bytes.Equal(referenceFrame, im.Pix) || len(bridge.Calls) != len(referenceCalls) || len(referenceCalls) == 0 {
					t.Fatal("cold original action differs", hd, bridge.Calls, referenceCalls)
				}
				for i, call := range bridge.Calls {
					ref := referenceCalls[i]
					if call.IP != ref["ip"] || call.Source != ref["source"] || call.Target != ref["target"] || call.BeforeHP != ref["before_hp"] || call.AfterHP != ref["after_hp"] || call.Encoded != ref["encoded"] {
						t.Fatal("native helper event differs", i, ref, call)
					}
				}
			}
			record := map[string]any{"hd": hd, "mode": mode, "units": fmt.Sprintf("%x", units), "pending_hp": fmt.Sprintf("%x", hp), "frame_sha256": contentSHA(im.Pix), "seed_before": uint32(0x12345678), "seed_after": originalSeed(e.Oracle), "input_keys": key, "moves": moves, "controlled_snapshot": false, "normal_cold_start": true}
			if bridge != nil {
				record["calls"] = bridge.Calls
			} else {
				record["native_calls"] = nativeCalls
			}
			reports = append(reports, record)
			e.Close()
		}
	}
	b, err := json.MarshalIndent(map[string]any{"status": "passed-original-battle-action", "rows": reports, "scope": "Cold Continue, normal map movement and confirmation, through first complete ordinary enemy action; no snapshot load or world-state mutation except fixed RNG seed; no GUI or owned world-save acceptance"}, "", "  ")
	must(err)
	must(os.WriteFile(filepath.Join(folder, "receipt.json"), append(b, '\n'), 0600))
}

func TestOriginalBattleArithmeticRefusals(t *testing.T) {
	work, _, catalog := originalBattleInputs(t)
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	pam, err := os.ReadFile(filepath.Join(work, "inputs/PAM.AY"))
	must(err)
	code, err := worldArmyCode(pam)
	must(err)
	names := []string{"disabled", "code", "caller", "source-slot", "kind", "count", "factors", "divisor", "wide", "segment"}
	for _, name := range names {
		m := dg.New()
		copy(m.Mem[0x1100:], code)
		c := m.CPU
		c.Seg[dg.CS] = 0xf67
		c.Seg[dg.DS] = 0x1e88
		c.Seg[dg.SS] = 0x1e88
		c.IP = 0x1592
		c.R[dg.SP] = 0xef00
		ds := uint32(0x1e880)
		for i, v := range []uint16{0x32d9, 0xf67, 0, 0} {
			m.Write16(ds+0xef00+uint32(i*2), v)
		}
		m.Write16(ds+0x56e8, 6)
		m.Write16(ds+0x56ea, 50)
		m.Write16(ds+0x5700, 1)
		m.Write16(ds+0x5702, 30)
		m.Write16(ds+0x8e60, 1000)
		m.Write16(ds+0x70ce+6*4, uint16(catalog.Profiles["native:06"].Attack))
		m.Write16(ds+0x70d0+4, uint16(catalog.Profiles["native:01"].HP))
		x := &originalBattleArithmetic{Code: code, Catalog: catalog, Enabled: true}
		switch name {
		case "disabled":
			x.Enabled = false
		case "code":
			m.Mem[0xf670+0x1592] ^= 1
		case "caller":
			m.Write16(ds+0xef00, 0xdead)
		case "source-slot":
			m.Write16(ds+0xef04, 6)
		case "kind":
			m.Write16(ds+0x56e8, 26)
		case "count":
			m.Write16(ds+0x56ea, 0)
		case "factors":
			m.Write16(ds+0x70ce+6*4, 1)
		case "divisor":
			m.Write16(ds+0x26b2, 5)
		case "wide":
			m.Write16(ds+0x56ea, 65535)
		case "segment":
			c.Seg[dg.DS] = 0x1e89
		}
		before := bytes.Clone(m.Mem)
		regs, ip, cycles := c.R, c.IP, c.Cycles
		if _, er := x.execute(m, 0x1592); er == nil {
			t.Fatal("unsafe battle input admitted", name)
		}
		if !bytes.Equal(before, m.Mem) || regs != c.R || ip != c.IP || cycles != c.Cycles || len(x.Calls) != 0 {
			t.Fatal("rejected bridge mutated state", name)
		}
	}
	e, err := game.Open(game.Options{Root: os.Getenv("EIGHTSWORD_TEST_ORIG"), Saves: t.TempDir(), BattleRules: "formation"})
	must(err)
	if _, er := installOriginalBattleArithmetic(e, catalog); er == nil {
		t.Fatal("formation bridge silently admitted")
	}
	e.Close()
	damage, encoded, err := originalBattleAmountFor(100, 3000, 20, 5, 1)
	must(err)
	b, err := json.MarshalIndent(map[string]any{"status": "passed-original-battle-refusals", "cases": names, "no_state_change": true, "formation_rejected": true, "wide_model": map[string]any{"attack": 100, "count": 3000, "hp": 20, "divisor": 5, "multiplier": 1, "damage": damage, "encoded": encoded}}, "", "  ")
	must(err)
	must(os.WriteFile(filepath.Join(work, "refusals-r1.json"), append(b, '\n'), 0600))
}
