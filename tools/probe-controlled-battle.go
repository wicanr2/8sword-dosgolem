//go:build ignore

// Fixed matrix of user-authorized memory/register injections.
package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func controlledMust(e error) {
	if e != nil {
		panic(e)
	}
}
func controlledWrite(p string, v any) {
	raw, e := json.MarshalIndent(v, "", "  ")
	controlledMust(e)
	f, e := os.OpenFile(p, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	controlledMust(e)
	_, e = f.Write(append(raw, '\n'))
	controlledMust(e)
	controlledMust(f.Close())
}
func main() {
	root := flag.String("root", "", "read-only original")
	input := flag.String("input", "", "fixed fixtures")
	out := flag.String("out", "", "new output")
	reader := flag.String("reader", "", "independent paired reader")
	flag.Parse()
	if os.Getuid() != 1000 {
		panic("UID1000")
	}
	controlledMust(os.Mkdir(*out, 0755))
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	var seed OwnedWorld
	for _, v := range []struct {
		Name string
		Dst  any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}, {"seed-world.json", &seed}} {
		b, e := os.ReadFile(filepath.Join(*input, v.Name))
		controlledMust(e)
		controlledMust(pairStrictJSON(b, v.Dst))
	}
	base, e := os.ReadFile(filepath.Join(*input, "original-save.ay"))
	controlledMust(e)
	pam, e := os.ReadFile(filepath.Join(*input, "PAM.AY"))
	controlledMust(e)
	code, e := worldArmyCode(pam)
	controlledMust(e)
	for _, name := range []string{"win", "retreat", "loss", "six", "reject-caller", "reject-source", "reject-resource", "reject-stale", "reject-segments"} {
		dir := filepath.Join(*out, name)
		controlledMust(os.Mkdir(dir, 0755))
		w := seed
		w.Army.Slots = [6]ArmyStack{{Unit: "openkb:wolf", Count: 30}}
		w.Army.Gold = 5000
		w.Army.Leadership = 1000
		enemy := seed.Encounters["skeleton-patrol"]
		if enemy.Enemy[0].Count == 0 {
			panic("fixed enemy missing")
		}
		w.Encounters = map[string]WorldEncounter{"random:controlled-r1": enemy}
		w.Battle = nil
		if name == "loss" {
			w.Army.Slots[0].Count = 1
			enemy.Enemy[0].Count = 1000
			w.Encounters["random:controlled-r1"] = enemy
		}
		if name == "six" {
			ids := []string{}
			for _, p := range c.Profiles {
				if p.NativeKind == 0 {
					ids = append(ids, p.ID)
				}
			}
			sort.Strings(ids)
			if len(ids) < 5 {
				panic("five extension profiles")
			}
			for i := 0; i < 5; i++ {
				w.Army.Slots[i] = ArmyStack{ids[i], 1}
			}
			w.Army.Slots[5] = ArmyStack{"native:25", 1}
		}
		paired := filepath.Join(dir, "paired-save")
		controlledMust(initializeProgressPair(paired, base, c, cc, w))
		store, snap, e := openProgressPair(paired, c, cc)
		controlledMust(e)
		o, e := oracle.LoadWith(filepath.Join(*root, "PAM.AY"), *root, oracle.Options{Adlib: true})
		controlledMust(e)
		controlledMust(o.LoadStateFile(filepath.Join(*input, "battle-before.state")))
		bridge := installControlledBattle(o, store, snap, code)
		beforeWorld := snap.World
		var beforeMem, afterMem []byte
		patches := []map[string]any{{"linear": 0x1ed72, "bytes": 12}, {"linear": 0x1edca, "bytes": 24}, {"linear": 0x23f68, "bytes": 48}}
		// 3733 is a saved real far-battle CALL frame. Unwind only the fixed
		// 32E0 prologue; preserve the actual 151C caller and its return stack.
		o.OnHostInstruction(oracle.Far(0x110, 0x3733), func(m *dg.Machine) (bool, error) {
			cpu := m.CPU
			ds := uint32(0x1e880)
			bp := cpu.R[dg.BP]
			if cpu.Seg[dg.CS] != 0x110 || cpu.Seg[dg.DS] != 0x1e88 || cpu.Seg[dg.SS] != 0x1e88 || bp < 32 || m.Read16(ds+uint32(bp)+2) != 0x171d || m.Read16(ds+uint32(bp)+4) != 0x110 {
				return false, errors.New("source snapshot call frame")
			}
			controlledMust(o.SaveStateFile(filepath.Join(dir, "before-commit.state")))
			beforeMem = o.Bytes(oracle.Far(0, 0), 1<<20)
			cpu.R[dg.SI] = m.Read16(ds + uint32(bp) - 0x12)
			cpu.R[dg.DI] = m.Read16(ds + uint32(bp) - 0x10)
			cpu.R[dg.SP] = bp + 2
			cpu.R[dg.BP] = m.Read16(ds + uint32(bp))
			cpu.IP = 0x32e0
			for i, n := range pairWorldResources(snap.World).words() {
				m.Write16(ds+0x4f2+uint32(i*2), uint16(n))
			}
			for _, p := range [][2]uint32{{ds + 0x54a, 24}, {ds + 0x56e8, 48}} {
				for i := uint32(0); i < p[1]; i++ {
					m.Write8(p[0]+i, 255)
				}
			}
			switch name {
			case "reject-caller":
				m.Write16(ds+uint32(cpu.R[dg.SP]), 0x171e)
				patches = append(patches, map[string]any{"linear": ds + uint32(cpu.R[dg.SP]), "bytes": 2})
			case "reject-source":
				m.Mem[0x1100+0x32e0] ^= 1
				patches = append(patches, map[string]any{"linear": 0x1100 + 0x32e0, "bytes": 1})
			case "reject-resource":
				m.Write16(ds+0x4f8, 1)
			case "reject-segments":
				cpu.Seg[dg.ES] = 0x1234
				cpu.Seg[dg.DS] = 0x1234
			}
			cpu.Cycles++
			controlledMust(o.SaveStateFile(filepath.Join(dir, "after-commit.state")))
			afterMem = o.Bytes(oracle.Far(0, 0), 1<<20)
			return true, nil
		})
		controlledMust(o.RunUntil(oracle.At(oracle.Far(0x110, 0x32e0)), oracle.Budget(100000)))
		if name == "reject-stale" {
			v := snap.World
			v.Revision++
			_, e = store.Commit(snap.Token, v)
			controlledMust(e)
		}
		diskBefore, e := store.readBytes()
		controlledMust(e)
		expectedReject := len(name) > 7 && name[:7] == "reject-"
		runError := o.Run(100000)
		rejected := runError != nil && !errors.Is(runError, errControlledBattleYield)
		if expectedReject {
			if !rejected {
				panic("expected rejection missing")
			}
			diskAfter, e := store.readBytes()
			controlledMust(e)
			if !bytes.Equal(diskBefore.Native, diskAfter.Native) || !bytes.Equal(diskBefore.World, diskAfter.World) {
				panic("rejection changed pair")
			}
			controlledMust(o.SaveStateFile(filepath.Join(dir, "final-map.state")))
			changed := 0
			for i := range beforeMem {
				if beforeMem[i] != afterMem[i] {
					changed++
				}
			}
			controlledWrite(filepath.Join(dir, "receipt.json"), map[string]any{"name": name, "controlled_memory": true, "expected_rejection": true, "rejected": true, "error": runError.Error(), "disk_unchanged": true, "injected_ranges": patches, "injected_changed_bytes": changed, "native_calls": bridge.NativeCalls})
			o.Close()
			store.Close()
			continue
		}
		if !errors.Is(runError, errControlledBattleYield) {
			panic(fmt.Sprintf("missing Go yield: %v", runError))
		}
		controlledMust(o.SaveStateFile(filepath.Join(dir, "paused.state")))
		actions := []game.OwnedCombatOutcome{}
		coldIndex := 0
		cold := func(label string) progressPairSnapshot {
			store.Close()
			p := filepath.Join(dir, label+"-cold.json")
			cmd := exec.Command(*reader, "-input", *input, "-dir", paired, "-world", "seed-world.json", "-mode", "read", "-out", p)
			if raw, e := cmd.CombinedOutput(); e != nil {
				panic(fmt.Sprintf("cold: %v %s", e, raw))
			}
			var disk struct {
				Snapshot progressPairSnapshot `json:"snapshot"`
			}
			raw, e := os.ReadFile(p)
			controlledMust(e)
			controlledMust(json.Unmarshal(raw, &disk))
			var current progressPairSnapshot
			store, current, e = openProgressPair(paired, c, cc)
			controlledMust(e)
			if current.Token != bridge.Current.Token || disk.Snapshot.Token != current.Token {
				panic("cold world changed")
			}
			bridge.Store = store
			return current
		}
		cold("battle-start")
		apply := func(side int) {
			s := bridge.Current.World.Battle.State
			p, e := s.Choose(cc, side, 0, "normal", 0, -1)
			controlledMust(e)
			event, e := bridge.apply(p.Action)
			controlledMust(e)
			actions = append(actions, event)
		}
		if name == "win" {
			for round := 0; round < 100; round++ {
				apply(1)
				if bridge.Current.World.Battle.State.Result != "" {
					break
				}
				apply(0)
				if bridge.Current.World.Battle.State.Result != "" {
					break
				}
				v := bridge.Current.World
				state, e := v.Battle.State.NextRound(cc)
				controlledMust(e)
				b := *v.Battle
				b.State = state
				v.Battle = &b
				controlledMust(bridge.commit(v))
				if coldIndex == 0 {
					cold("mid-battle")
					coldIndex++
				}
			}
			if bridge.Current.World.Battle.State.Result != "win" {
				panic("controlled victory missing")
			}
			controlledMust(bridge.settle(DefeatInput{}))
		} else if name == "loss" {
			apply(1)
			if bridge.Current.World.Battle.State.Result != "loss" {
				panic("controlled loss missing")
			}
			controlledMust(bridge.settle(DefeatInput{Reason: "annihilation", Choice: "roam"}))
		} else {
			if name == "retreat" {
				apply(1)
			}
			random := uint32(2730)
			controlledMust(bridge.settle(DefeatInput{Reason: "retreat", Random: &random}))
		}
		coldFinal := cold("settled")
		if e := bridge.settle(DefeatInput{}); e == nil {
			panic("duplicate settlement")
		}
		controlledMust(o.RunUntil(oracle.At(oracle.Far(0x110, 0x0bd3)), oracle.Budget(20000000)))
		if !bridge.Returned || bridge.NativeCalls != 0 {
			panic("native battle escaped")
		}
		controlledMust(o.SaveStateFile(filepath.Join(dir, "final-map.state")))
		changed := 0
		for i := range beforeMem {
			if beforeMem[i] != afterMem[i] {
				changed++
			}
		}
		controlledWrite(filepath.Join(dir, "receipt.json"), map[string]any{"name": name, "controlled_memory": true, "expected_rejection": false, "rejected": rejected, "injected_ranges": patches, "injected_changed_bytes": changed, "native_calls": bridge.NativeCalls, "return_gate": o.Regs().IP, "world_before": beforeWorld, "world_after": bridge.Current.World, "actions": actions, "cold_final": coldFinal, "result": bridge.Result, "random_input": 2730, "normal_player_path": false})
		o.Close()
		store.Close()
	}
}
