//go:build ignore

// Original CPU controls and fixed-state refusal handoffs, with seeds fixed first.
package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func rmust(e error) {
	if e != nil {
		panic(e)
	}
}
func rwrite(p string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	rmust(e)
	f, e := os.OpenFile(p, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	rmust(e)
	_, e = f.Write(append(b, '\n'))
	rmust(e)
	rmust(f.Close())
}
func main() {
	root := flag.String("root", "", "original")
	input := flag.String("input", "", "fixed inputs")
	out := flag.String("out", "", "new output")
	flag.Parse()
	if os.Getuid() != 1000 {
		panic("UID1000")
	}
	rmust(os.Mkdir(*out, 0755))
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	var world OwnedWorld
	for _, v := range []struct {
		Name string
		Dst  any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}, {"world-runtime.json", &world}} {
		b, e := os.ReadFile(filepath.Join(*input, v.Name))
		rmust(e)
		rmust(pairStrictJSON(b, v.Dst))
	}
	codeRaw, e := os.ReadFile(filepath.Join(*input, "PAM.AY"))
	rmust(e)
	code, e := worldArmyCode(codeRaw)
	rmust(e)
	base, e := os.ReadFile(filepath.Join(*input, "original-save.ay"))
	rmust(e)
	var plan struct {
		Boundaries []struct {
			Value uint16
			Seed  uint32
		}
		Seeds []uint32
	}
	b, e := os.ReadFile(filepath.Join(*input, "seeds.json"))
	rmust(e)
	rmust(json.Unmarshal(b, &plan))
	load := func() *oracle.Oracle {
		o, e := oracle.LoadWith(filepath.Join(*root, "PAM.AY"), *root, oracle.Options{Adlib: true})
		rmust(e)
		rmust(o.LoadStateFile(filepath.Join(*input, "battle-before.state")))
		return o
	}
	address, e := originalRandAddress(code)
	rmust(e)
	rngRows := []map[string]any{}
	for _, seed := range plan.Seeds {
		o := load()
		writeOriginalSeed(o, seed)
		expected := seed
		for i := 0; i < 16; i++ {
			p := planOriginalRand(expected)
			value, e := o.CallBudget(20000, address)
			rmust(e)
			if uint16(value) != p.Value || originalSeed(o) != p.After {
				panic("original rand mismatch")
			}
			rngRows = append(rngRows, map[string]any{"seed": expected, "next": p.After, "value": p.Value, "sequence_seed": seed, "index": i})
			expected = p.After
		}
		rmust(o.SaveStateFile(filepath.Join(*out, fmt.Sprintf("rng-%d.state", seed))))
		o.Close()
	}
	decisions := []map[string]any{}
	rejections := []map[string]any{}
	for _, fixture := range plan.Boundaries {
		for _, mode := range []string{"original", "go"} {
			dir := filepath.Join(*out, fmt.Sprintf("gate-%d-%s", fixture.Value, mode))
			rmust(os.Mkdir(dir, 0755))
			o := load()
			var bp, sp uint16
			o.OnHostInstruction(oracle.Far(0x110, 0x3733), func(m *dg.Machine) (bool, error) {
				c := m.CPU
				ds := uint32(0x1e880)
				old := c.R[dg.BP]
				if m.Read16(ds+uint32(old)+2) != 0x171d {
					return false, errors.New("snapshot frame")
				}
				rmust(o.SaveStateFile(filepath.Join(dir, "before-commit.state")))
				c.R[dg.SI] = m.Read16(ds + uint32(old) - 0x12)
				c.R[dg.DI] = m.Read16(ds + uint32(old) - 0x10)
				c.R[dg.SP] = old + 6
				c.R[dg.BP] = m.Read16(ds + uint32(old))
				c.IP = 0x173a
				c.R[dg.AX] = 2
				bp = c.R[dg.BP]
				sp = c.R[dg.SP]
				for i, n := range pairWorldResources(world).words() {
					m.Write16(ds+0x4f2+uint32(i*2), uint16(n))
				}
				m.Write16(ds+0x81bc, uint16(fixture.Seed))
				m.Write16(ds+0x81be, uint16(fixture.Seed>>16))
				if mode == "go" {
					for _, off := range []uint32{ds + 0x54a, ds + 0x56e8} {
						for i := uint32(0); i < 24; i++ {
							m.Write8(off+i, 255)
						}
					}
				}
				c.Cycles++
				rmust(o.SaveStateFile(filepath.Join(dir, "after-commit.state")))
				return true, nil
			})
			rmust(o.RunUntil(oracle.At(oracle.Far(0x110, 0x173a)), oracle.Budget(100000)))
			if mode == "go" {
				g := &refusalGate{Code: code, BP: bp, SP: sp, Guard: func(m *dg.Machine) error {
					for i, n := range pairWorldResources(world).words() {
						if uint64(m.Read16(0x1ed72+uint32(i*2))) != n {
							return errors.New("gate resources")
						}
					}
					return nil
				}}
				o.OnHostInstruction(oracle.Far(0x110, 0x173a), g.execute)
			}
			end := uint16(0x1782)
			if fixture.Value/8192 == 1 {
				end = 0x1752
			}
			rmust(o.RunUntil(oracle.At(oracle.Far(0x110, end)), oracle.Budget(100000)))
			if originalSeed(o) != planOriginalRand(fixture.Seed).After {
				panic("gate seed")
			}
			rmust(o.SaveStateFile(filepath.Join(dir, "gate.state")))
			decisions = append(decisions, map[string]any{"value": fixture.Value, "seed": fixture.Seed, "mode": mode, "next_seed": originalSeed(o), "gate": o.Regs().IP})
			o.Close()
		}
	}
	handoffs := []map[string]any{}
	for _, fixture := range plan.Boundaries {
		if fixture.Value != 0 && fixture.Value != 8192 {
			continue
		}
		name := fmt.Sprintf("handoff-%d", fixture.Value)
		dir := filepath.Join(*out, name)
		rmust(os.Mkdir(dir, 0755))
		paired := filepath.Join(dir, "paired-save")
		rmust(initializeProgressPair(paired, base, c, cc, world))
		store, snap, e := openProgressPair(paired, c, cc)
		rmust(e)
		o := load()
		bridge := installRuntimeEnemyBattle(o, store, snap, code)
		var bp, sp uint16
		o.OnHostInstruction(oracle.Far(0x110, 0x3733), func(m *dg.Machine) (bool, error) {
			cpu := m.CPU
			ds := uint32(0x1e880)
			old := cpu.R[dg.BP]
			rmust(o.SaveStateFile(filepath.Join(dir, "before-commit.state")))
			cpu.R[dg.SI] = m.Read16(ds + uint32(old) - 0x12)
			cpu.R[dg.DI] = m.Read16(ds + uint32(old) - 0x10)
			cpu.R[dg.SP] = old + 6
			cpu.R[dg.BP] = m.Read16(ds + uint32(old))
			cpu.IP = 0x173a
			cpu.R[dg.AX] = 2
			bp = cpu.R[dg.BP]
			sp = cpu.R[dg.SP]
			for i, n := range pairWorldResources(world).words() {
				m.Write16(ds+0x4f2+uint32(i*2), uint16(n))
			}
			m.Write16(ds+0x81bc, uint16(fixture.Seed))
			m.Write16(ds+0x81be, uint16(fixture.Seed>>16))
			for _, off := range []uint32{ds + 0x54a, ds + 0x56e8} {
				for i := uint32(0); i < 24; i++ {
					m.Write8(off+i, 255)
				}
			}
			cpu.Cycles++
			rmust(o.SaveStateFile(filepath.Join(dir, "after-commit.state")))
			return true, nil
		})
		rmust(o.RunUntil(oracle.At(oracle.Far(0x110, 0x173a)), oracle.Budget(100000)))
		g := &refusalGate{Code: code, BP: bp, SP: sp, Guard: func(m *dg.Machine) error {
			s, e := store.Recover()
			if e != nil {
				return e
			}
			if s.Token != bridge.Current.Token {
				return errors.New("gate stale")
			}
			return nil
		}, Decision: func(_ originalRandPlan, p bool) {
			if p {
				bridge.Modifier = 1
			}
		}}
		o.OnHostInstruction(oracle.Far(0x110, 0x173a), g.execute)
		rmust(o.SendKeys("Return"))
		events := []game.OwnedCombatOutcome{}
		var retreat *originalRandPlan
		returnRNG := []map[string]any{}
		if fixture.Value == 8192 {
			if e = o.Run(20000000); !errors.Is(e, errControlledBattleYield) {
				panic(fmt.Sprintf("pursuit missing Go yield: %v", e))
			}
			rmust(o.SaveStateFile(filepath.Join(dir, "held.state")))
			for _, name := range []string{"stale", "source", "frame", "resources"} {
				d := filepath.Join(dir, "reject-"+name)
				rmust(os.Mkdir(d, 0755))
				rmust(initializeProgressPair(filepath.Join(d, "paired-save"), bridge.Current.Bytes.Native, c, cc, bridge.Current.World))
				st, ss, e := openProgressPair(filepath.Join(d, "paired-save"), c, cc)
				rmust(e)
				v := load()
				rmust(v.LoadStateFile(filepath.Join(dir, "held.state")))
				test := &controlledBattle{Store: st, Current: ss, Code: code, Pending: true, SP: bridge.SP, BP: bridge.BP, BeforeResources: bridge.BeforeResources}
				switch name {
				case "stale":
					w := ss.World
					b := *w.Battle
					w.Battle = &b
					w.Revision++
					w.Progress.Merit++
					w.Battle.StartSHA = w.baseDigest()
					_, e = st.Commit(ss.Token, w)
					rmust(e)
				case "source":
					v.WriteU16(address, v.Word(address)^1)
				case "frame":
					r := v.Regs()
					v.WriteU16(oracle.Far(r.SS, r.SP), 0x171e)
				case "resources":
					v.WriteU16(oracle.Far(0x1e88, 0x4f8), 1)
				}
				rmust(v.SaveStateFile(filepath.Join(d, "before-reject.state")))
				mem := v.Bytes(oracle.Far(0, 0), 1<<20)
				regs := v.Regs()
				steps, cycles := v.Steps(), v.Cycles()
				disk, e := st.readBytes()
				rmust(e)
				err := settleRuntimeRetreat(test, v)
				if err == nil {
					panic("missing retreat rejection")
				}
				after, e := st.readBytes()
				rmust(e)
				if !bytes.Equal(mem, v.Bytes(oracle.Far(0, 0), 1<<20)) || regs != v.Regs() || steps != v.Steps() || cycles != v.Cycles() || !bytes.Equal(disk.Native, after.Native) || !bytes.Equal(disk.World, after.World) {
					panic("rejected retreat mutated state")
				}
				rmust(v.SaveStateFile(filepath.Join(d, "after-reject.state")))
				rejections = append(rejections, map[string]any{"name": name, "error": err.Error(), "memory_unchanged": true, "disk_unchanged": true})
				st.Close()
				v.Close()
			}
			if o.Word(oracle.Far(0x1e88, 0x8d6a)) != 1 {
				panic("pursuit flag")
			}
			for i := 0; i < 6; i++ {
				s := bridge.Current.World.Battle.State
				if s.Rows[1][i].Count == 0 || i >= 3 && !cc.Profiles[s.Rows[1][i].Unit].Ranged {
					continue
				}
				kind := "normal"
				if cc.Profiles[s.Rows[1][i].Unit].Ranged {
					kind = "ranged"
				}
				p, e := s.Choose(cc, 1, i, kind, 0, -1)
				rmust(e)
				v, e := bridge.apply(p.Action)
				rmust(e)
				events = append(events, v)
			}
			rmust(settleRuntimeRetreat(bridge.controlledBattle, o))
			retreat = lastRetreatRand
			rmust(o.SaveStateFile(filepath.Join(dir, "settled.state")))
			o.OnCall(address, func(o *oracle.Oracle) {
				r := o.Regs()
				returnRNG = append(returnRNG, map[string]any{"seed_before": originalSeed(o), "return_cs": o.Word(oracle.Far(r.SS, r.SP+2)), "return_ip": o.Word(oracle.Far(r.SS, r.SP))})
			})
			seedBefore := originalSeed(o)
			if e = settleRuntimeRetreat(bridge.controlledBattle, o); e == nil || originalSeed(o) != seedBefore {
				panic("duplicate retreat consumed RNG")
			}
		}
		rmust(o.RunUntil(oracle.At(oracle.Far(0x110, 0xbd3)), oracle.Budget(20000000)))
		rmust(o.SaveStateFile(filepath.Join(dir, "final-map.state")))
		if bridge.NativeCalls != 0 {
			panic("native battle escaped")
		}
		current, e := store.Recover()
		rmust(e)
		if fixture.Value == 0 && current.Token != snap.Token {
			panic("free refusal changed pair")
		}
		mem := o.Bytes(oracle.Far(0x1e88, 0x54a), 24)
		if !bytes.Equal(mem, bytes.Repeat([]byte{255}, 24)) {
			panic("native army changed")
		}
		handoffs = append(handoffs, map[string]any{"name": name, "decision": g.Plan, "pursued": g.Pursued, "world_before": world, "world_after": current.World, "opening": events, "retreat": retreat, "return_rng": returnRNG, "enemy": bridge.Rows, "return_ip": o.Regs().IP, "native_calls": bridge.NativeCalls, "modifier": bridge.Modifier})
		store.Close()
		o.Close()
	}
	rwrite(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-original-rng-and-refusal-handoffs", "rng": rngRows, "decisions": decisions, "handoffs": handoffs, "rejections": rejections, "controlled_memory": true, "normal_player_path": false})
}
