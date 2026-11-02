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

func TestOriginalArmyProjectionModels(t *testing.T) {
	work, _, cc := originalBattleInputs(t)
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
	rows := [6]ArmyStack{{"native:01", 30}, {"native:03", 10}, {"native:06", 5}, {"native:10", 2}, {"native:12", 2}, {"native:24", 1}}
	raw, err := originalArmyProjectionBytes(rows, cc)
	must(err)
	makeFixture := func() (*dg.Machine, *originalArmyProjection) {
		m := dg.New()
		copy(m.Mem[0x1100:], code)
		c := m.CPU
		c.Seg[dg.CS] = 0x110
		c.Seg[dg.DS] = 0x1e88
		c.Seg[dg.SS] = 0x1e88
		c.IP = 0x32e0
		c.R[dg.SP] = 0xef00
		c.R[dg.BP] = 0xf100
		ds := uint32(0x1e880)
		m.Write16(ds+0xef00, 0x171d)
		m.Write16(ds+0xef02, 0x110)
		m.Write16(ds+0xf102, 0xbd3)
		m.Write16(ds+0xf104, 0x110)
		m.Write16(ds+0x54a, 1)
		m.Write16(ds+0x54c, 30)
		return m, &originalArmyProjection{Code: code, Catalog: cc, Input: rows, Encoded: raw}
	}
	prologue := func(m *dg.Machine) {
		m.CPU.IP = 0x3365
		m.CPU.R[dg.BP] = 0xeefe
		m.CPU.R[dg.SP] = 0xeeec
		m.Write16(0x1e880+0xeefe, 0xf100)
	}
	m, x := makeFixture()
	shadow := bytes.Clone(m.Mem[0x1edca:0x1ede2])
	_, err = x.execute(m, 0x32e0)
	must(err)
	prologue(m)
	_, err = x.execute(m, 0x3365)
	must(err)
	if !bytes.Equal(m.Mem[0x23f68:0x23f80], raw[:]) || bytes.Equal(shadow, raw[:]) || !bytes.Equal(shadow, m.Mem[0x1edca:0x1ede2]) {
		t.Fatal("Go six-slot projection/source isolation")
	}
	remaining := rows
	remaining[0].Count = 26
	remaining[5] = ArmyStack{}
	after, err := originalArmyProjectionBytes(remaining, cc)
	must(err)
	copy(m.Mem[0x23f68:0x23f80], after[:])
	m.CPU.IP = 0x3745
	m.Write16(0x1e880+0xeefe-0xe, 1)
	_, err = x.execute(m, 0x3745)
	must(err)
	if x.Remaining != remaining || x.Result != 1 || m.CPU.IP != 0x376a || !bytes.Equal(shadow, m.Mem[0x1edca:0x1ede2]) {
		t.Fatal("capture/writeback isolation")
	}
	refusals := []string{"source", "caller", "segment", "cycles", "entry-repeat", "frame", "shadow", "copy-repeat", "typed-change", "capture-increase", "capture-unknown", "capture-hole", "capture-repeat", "result"}
	for _, name := range refusals {
		m, x := makeFixture()
		ip := uint16(0x32e0)
		switch name {
		case "source":
			m.Mem[0x1100+0x3774] ^= 1
		case "caller":
			m.Write16(0x1e880+0xef00, 0x309e)
		case "segment":
			m.CPU.Seg[dg.SS]++
		case "cycles":
			m.CPU.Cycles = ^uint64(0)
		case "entry-repeat":
			x.Phase = "entered"
		default:
			_, err = x.execute(m, 0x32e0)
			must(err)
			prologue(m)
			ip = 0x3365
			switch name {
			case "frame":
				m.CPU.R[dg.SP]--
			case "shadow":
				m.Write16(0x1e880+0x54c, 31)
			case "copy-repeat":
				x.Phase = "projected"
				x.Copies = 1
			case "typed-change":
				x.Input[0].Count++
			default:
				_, err = x.execute(m, 0x3365)
				must(err)
				ip = 0x3745
				m.CPU.IP = ip
				m.Write16(0x1e880+0xeefe-0xe, 1)
				switch name {
				case "capture-increase":
					m.Write16(0x23f6a, 31)
				case "capture-unknown":
					m.Write16(0x23f68, 25)
				case "capture-hole":
					clear(m.Mem[0x23f68:0x23f6c])
				case "capture-repeat":
					x.Phase = "captured"
					x.Captures = 1
				case "result":
					m.Write16(0x1e880+0xeefe-0xe, 3)
				}
			}
		}
		before := bytes.Clone(m.Mem)
		regs, at, cycles := m.CPU.R, m.CPU.IP, m.CPU.Cycles
		phase := x.Phase
		if _, err = x.execute(m, ip); err == nil {
			t.Fatal("unsafe projection admitted", name)
		}
		if !bytes.Equal(before, m.Mem) || regs != m.CPU.R || at != m.CPU.IP || cycles != m.CPU.Cycles || x.Phase != phase {
			t.Fatal("refusal changed state", name)
		}
	}
	for _, name := range []string{"extension", "wide", "zero", "duplicate", "empty"} {
		r := rows
		switch name {
		case "extension":
			r[0] = ArmyStack{"openkb:wolf", 1}
		case "wide":
			r[0].Count = 32768
		case "zero":
			r[0].Count = 0
		case "duplicate":
			r[1] = r[0]
		case "empty":
			r = [6]ArmyStack{}
		}
		if _, err = originalArmyProjectionBytes(r, cc); err == nil {
			t.Fatal("invalid typed army admitted", name)
		}
		refusals = append(refusals, name)
	}
	b, err := json.MarshalIndent(map[string]any{"status": "passed-original-army-projection-models", "six_slots": true, "input": rows, "remaining": remaining, "encoded_hex": fmt.Sprintf("%x", raw), "shadow_hex": fmt.Sprintf("%x", shadow), "shadow_unchanged": true, "refusals": refusals, "controlled_machine": true}, "", "  ")
	must(err)
	must(os.WriteFile(filepath.Join(work, "models-r1.json"), append(b, '\n'), 0600))
}

func TestOriginalArmyProjectionAction(t *testing.T) {
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
	folder := filepath.Join(work, "projection-action-r1")
	must(os.Mkdir(folder, 0700))
	reports := []map[string]any{}
	for _, hd := range []bool{false, true} {
		var referenceUnits, referenceHP, referenceFrame []byte
		var referenceCalls []map[string]uint16
		var referenceRemaining [6]ArmyStack
		var referenceReturnSeed uint32
		var referenceResult uint16
		for mode := 0; mode < 2; mode++ {
			dir := filepath.Join(folder, fmt.Sprintf("hd-%v-mode-%d", hd, mode))
			must(os.Mkdir(dir, 0700))
			var armyCatalog ArmyCatalog
			b, err := os.ReadFile(filepath.Join(work, "inputs/army-catalog.json"))
			must(err)
			must(pairStrictJSON(b, &armyCatalog))
			session := filepath.Join(dir, "session")
			must(importNativeProgress(root, root, session, filepath.Join(work, "inputs"), armyCatalog, catalog))
			store, snap, err := openProgressPair(session, armyCatalog, catalog)
			must(err)
			initialNative := bytes.Clone(snap.Bytes.Native)
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
			var projection *originalArmyProjection
			shadowBefore := e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)
			if mode == 1 {
				projection, err = installOriginalArmyProjection(e, catalog, snap.World.Army.Slots)
				must(err)
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

			firstSeed := originalSeed(e.Oracle)
			returnStop := errors.New("original wrapper returned")
			escapeSent := false
			e.Oracle.OnCall(oracle.Far(0xf67, 0x28a6), func(o *oracle.Oracle) {
				if !escapeSent {
					must(e.Key(1, true))
					escapeSent = true
				}
			})
			returnStart := e.Oracle.Steps()
			e.Oracle.SetStepGuard(func(o *oracle.Oracle) error {
				r := o.Regs()
				if r.CS == 0x110 && r.IP == 0x171d {
					return returnStop
				}
				if o.Steps() > returnStart+60000000 {
					return errors.New("wrapper return budget")
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
			if !errors.Is(err, returnStop) {
				t.Fatal("normal Escape return", hd, mode, err, e.Oracle.Regs())
			}
			must(e.Key(1, false))
			e.Oracle.SetStepGuard(nil)
			if !escapeSent {
				t.Fatal("normal player input not reached")
			}
			result := e.Oracle.Regs().AX
			shadowAfter := e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)
			var remaining [6]ArmyStack
			if projection == nil {
				x := &originalArmyProjection{Input: snap.World.Army.Slots}
				remaining, err = x.capture(shadowAfter)
				must(err)
				referenceRemaining, referenceReturnSeed, referenceResult = remaining, originalSeed(e.Oracle), result
			} else {
				remaining = projection.Remaining
				if remaining != referenceRemaining || result != referenceResult || projection.Result != result || originalSeed(e.Oracle) != referenceReturnSeed || !bytes.Equal(shadowBefore, shadowAfter) {
					t.Fatal("typed remainder/seed/shadow differs", remaining, referenceRemaining, projection)
				}
				w := snap.World
				w.Army.Slots = remaining
				w.Revision++
				snap, err = store.Commit(snap.Token, w)
				must(err)
				if !bytes.Equal(initialNative, snap.Bytes.Native) {
					t.Fatal("capture save changed original file")
				}
				store.Close()
				store, snap, err = openProgressPair(session, armyCatalog, catalog)
				must(err)
				if snap.World.Army.Slots != remaining {
					t.Fatal("cold save army differs")
				}
			}
			must(e.Oracle.SaveStateFile(filepath.Join(dir, "returned.state")))
			record := map[string]any{"hd": hd, "mode": mode, "units": fmt.Sprintf("%x", units), "pending_hp": fmt.Sprintf("%x", hp), "frame_sha256": contentSHA(im.Pix), "seed_before": uint32(0x12345678), "seed_after": firstSeed, "return_seed": originalSeed(e.Oracle), "remaining": remaining, "battle_result": result, "escape_sent": escapeSent, "shadow_before": fmt.Sprintf("%x", shadowBefore), "shadow_after": fmt.Sprintf("%x", shadowAfter), "input_keys": key, "moves": moves, "controlled_snapshot": false, "normal_cold_start": true}
			if bridge != nil {
				record["calls"] = bridge.Calls
				record["copies"] = projection.Copies
				record["captures"] = projection.Captures
				record["store_cold_read"] = true
				record["native_file_unchanged"] = true
			} else {
				record["native_calls"] = nativeCalls
			}
			reports = append(reports, record)
			store.Close()
			e.Close()
		}
	}
	b, err := json.MarshalIndent(map[string]any{"status": "passed-original-army-projection-action", "rows": reports, "scope": "Cold Continue, normal map movement and confirmation, through first complete ordinary enemy action; no snapshot load or world-state mutation except fixed RNG seed; typed remainder paired-save cold read; no GUI or complete world settlement acceptance"}, "", "  ")
	must(err)
	must(os.WriteFile(filepath.Join(folder, "receipt.json"), append(b, '\n'), 0600))
}
