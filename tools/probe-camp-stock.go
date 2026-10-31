//go:build ignore

package main

import (
	"bytes"
	"encoding/binary"
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

func campMust(e error) {
	if e != nil {
		panic(e)
	}
}
func campWrite(p string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	campMust(e)
	f, e := os.OpenFile(p, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	campMust(e)
	_, e = f.Write(append(b, '\n'))
	campMust(e)
	campMust(f.Close())
}
func main() {
	root := flag.String("root", "", "read-only original")
	input := flag.String("input", "", "fixed input")
	out := flag.String("out", "", "new output")
	scratch := flag.String("scratch", "", "native shadow")
	mode := flag.String("mode", "probe", "probe/init")
	session := flag.String("session", "", "new pair")
	flag.Parse()
	if os.Getuid() != 1000 {
		panic("UID1000")
	}
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	var w OwnedWorld
	for _, r := range []struct {
		name string
		dst  any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}, {"world-normal.json", &w}} {
		b, e := os.ReadFile(filepath.Join(*input, r.name))
		campMust(e)
		campMust(pairStrictJSON(b, r.dst))
	}
	base, e := os.ReadFile(filepath.Join(*input, "original-save.ay"))
	campMust(e)
	if *mode == "init" {
		campMust(initializeProgressPair(*session, base, c, cc, w))
		return
	}
	campMust(os.Mkdir(*out, 0700))
	maps := map[string][]byte{}
	for i := 0; i < 9; i++ {
		n := fmt.Sprintf("map%02d.ay", i)
		maps[n], e = os.ReadFile(filepath.Join(*input, "maps", n))
		campMust(e)
	}
	newStore := func(name string) (*progressPairStore, progressPairSnapshot) {
		dir := filepath.Join(*out, name)
		campMust(initializeProgressPair(dir, base, c, cc, w))
		s, b, e := openProgressPair(dir, c, cc)
		campMust(e)
		return s, b
	}
	purchase := func(s *progressPairStore, b progressPairSnapshot, key string) (progressPairSnapshot, error) {
		n := cloneCampWorld(b.World)
		var e error
		n.Army, _, e = n.Army.recruit(c, key, 1)
		if e != nil {
			return b, e
		}
		n.Revision++
		return s.Commit(b.Token, n)
	}
	s, b := newStore("session")
	initial := b
	b, e = s.BindCamp(b.Token, 0, 1, maps)
	campMust(e)
	bound := b
	again, e := s.BindCamp(b.Token, 0, 1, maps)
	campMust(e)
	if again.Token != b.Token {
		panic("rebind changed progress")
	}
	b, e = purchase(s, b, campKey(0, 1))
	campMust(e)
	bought := b
	if _, e = purchase(s, bound, campKey(0, 1)); e == nil {
		panic("stale token admitted")
	}
	changes := []int{}
	for i := range b.Bytes.Native {
		if b.Bytes.Native[i] != bound.Bytes.Native[i] {
			changes = append(changes, i)
			if i >= 12 && i != 126 && i != 127 {
				panic(fmt.Sprintf("opaque byte changed %d", i))
			}
		}
	}
	if b.World.Army.Offers[campKey(0, 1)].Stock != 2999 || b.World.Army.Gold != 4999 || b.World.Army.Slots[0].Unit != "openkb:wolf" || b.World.Army.Slots[0].Count != 2500 || b.World.Army.Slots[1] != (ArmyStack{"native:01", 1}) {
		panic("purchase result")
	}
	s.Close()
	s, b, e = openProgressPair(s.Dir, c, cc)
	campMust(e)
	if b.Token != bought.Token {
		panic("cold purchase changed")
	}
	// New store, no F7, same source must retain its reduced stock.
	again, e = s.BindCamp(b.Token, 0, 1, maps)
	campMust(e)
	if again.Token != b.Token {
		panic("cold rebind refilled stock")
	}
	cases := []string{}
	reject := func(name string, next OwnedWorld) {
		_, e := s.Commit(b.Token, next)
		if e == nil {
			panic("accepted " + name)
		}
		now, x := s.Recover()
		campMust(x)
		if now.Token != b.Token {
			panic("refusal mutated files")
		}
		cases = append(cases, name)
	}
	n := cloneCampWorld(b.World)
	v := n.Army.Offers[campKey(0, 1)]
	v.Stock++
	n.Army.Offers[campKey(0, 1)] = v
	n.Revision++
	reject("unproven refill", n)
	n = cloneCampWorld(b.World)
	delete(n.Army.Offers, campKey(0, 1))
	n.Revision++
	reject("remove source", n)
	n = cloneCampWorld(b.World)
	v = n.Army.Offers[campKey(0, 1)]
	v.Stock--
	n.Army.Offers[campKey(0, 1)] = v
	n.Revision++
	reject("stock-only charge omission", n)
	n = cloneCampWorld(b.World)
	n.Army.Offers["native-camp:0:1"] = ArmyOffer{"native:01", 3000}
	n.Revision++
	reject("noncanonical source key", n)
	n = cloneCampWorld(b.World)
	n.Army.Offers[campKey(4, 0)] = ArmyOffer{"native:01", 1200}
	n.Revision++
	reject("wrong source kind", n)
	changedMaps := map[string][]byte{}
	for k, v := range maps {
		changedMaps[k] = bytes.Clone(v)
	}
	changedMaps["map01.ay"][0] ^= 1
	b, e = s.CommitCheckpoint(b.Token, b.Bytes.Native, changedMaps)
	campMust(e)
	if checkpointIntentSchema(b.Bytes) != campIntent {
		panic("F7 downgraded")
	}
	s.Close()
	faults := []map[string]any{}
	for i, phase := range []string{"before-intent", "intent-durable", "native-durable", "world-durable"} {
		st, start := newStore(fmt.Sprintf("fault-%d", i))
		start, e = st.BindCamp(start.Token, 4, 0, maps)
		campMust(e)
		st.Fault = func(p string) error {
			if p == phase {
				return errors.New("injected stock interruption")
			}
			return nil
		}
		_, e = purchase(st, start, campKey(4, 0))
		if e == nil {
			panic("fault not reached")
		}
		dir := st.Dir
		st.Close()
		st, got, x := openProgressPair(dir, c, cc)
		campMust(x)
		expectedStock := uint32(1199)
		expectedGold := uint64(4999)
		if phase == "before-intent" {
			expectedStock = 1200
			expectedGold = 5000
		}
		if got.World.Army.Offers[campKey(4, 0)].Stock != expectedStock || got.World.Army.Gold != expectedGold {
			panic("fault mixed outcome")
		}
		again, x := st.Recover()
		campMust(x)
		if again.Token != got.Token {
			panic("recovery repeated charge")
		}
		st.Close()
		faults = append(faults, map[string]any{"phase": phase, "stock": expectedStock, "gold": expectedGold, "token": got.Token})
	}
	// Real wrapper execution, with a declared controlled entry/quantity. No
	// keyboard, natural encounter or new HD parity is claimed by this probe.
	pam, e := os.ReadFile(filepath.Join(*input, "PAM.AY"))
	campMust(e)
	routes := []map[string]any{}
	for _, scenario := range []struct {
		group, row int
		qty        uint16
	}{{0, 1, 1}, {0, 1, 1}, {4, 0, 1}, {4, 0, 0}} {
		st, start, e := openProgressPair(filepath.Join(*out, "session"), c, cc)
		campMust(e)
		o, e := oracle.LoadWith(filepath.Join(*input, "PAM.AY"), *root, oracle.Options{Adlib: true})
		campMust(e)
		campMust(o.LoadStateFile(filepath.Join(*input, "before-commit.state")))
		reg := o.Regs()
		oldBP, oldSP, oldSI := reg.BP, reg.SP, reg.SI
		o.OnHostInstruction(oracle.Far(0x110, 0x56ec), func(m *dg.Machine) (bool, error) {
			bp := m.CPU.R[dg.BP]
			m.CPU.R[dg.SP] = bp + 2
			m.CPU.R[dg.BP] = m.Read16(0x1e880 + uint32(bp))
			m.CPU.R[dg.SI] = m.Read16(0x1e880 + uint32(bp) - 14)
			m.CPU.IP = 0x54ea
			m.CPU.Cycles++
			return true, nil
		})
		campMust(o.RunUntil(oracle.At(oracle.Far(0x110, 0x54ea)), oracle.Budget(16)))
		parent := o.Regs().BP
		rec, e := decodeCampRecord(start.Bytes.Native, scenario.group, scenario.row)
		campMust(e)
		// Synchronize precisely the controlled source and Go resource projection.
		campMust(overlayCampStocks(o, start))
		o.WriteU16(oracle.Far(0x1e88, parent-6), uint16(scenario.row))
		o.WriteU16(oracle.Far(0x1e88, 0x56d6), uint16(scenario.row/3))
		o.WriteU16(oracle.Far(0x1e88, 0x8e12), rec.Words[1])
		o.WriteU16(oracle.Far(0x1e88, 0x8e44), rec.Words[2])
		o.WriteU16(oracle.Far(0x1e88, oldBP+2), uint16(0x5a21+scenario.group*0x90))
		o.WriteU16(oracle.Far(0x1e88, oldBP+6), rec.Words[3])
		o.WriteU16(oracle.Far(0x1e88, oldBP+8), rec.Words[4])
		o.WriteU16(oracle.Far(0x1e88, oldBP-2), scenario.qty)
		for i, v := range pairWorldResources(start.World).words() {
			o.WriteU16(oracle.Far(0x1e88, 0x4f2+uint16(i*2)), uint16(v))
		}
		if *scratch == "" {
			*scratch = filepath.Join(*out, "scratch")
			campMust(os.Mkdir(*scratch, 0700))
			for k, v := range maps {
				campMust(os.WriteFile(filepath.Join(*scratch, k), v, 0600))
			}
		}
		eng := &game.Engine{Oracle: o, PAM: pam, PAMLoaded: true, HD: true}
		port, e := installWorldArmyPort(eng, st, start)
		campMust(e)
		o.OnCall(oracle.Far(0x110, 0x54ea), func(o *oracle.Oracle) {
			before := port.Current.Token
			campMust(port.bindCamp(o))
			if before != port.Current.Token {
				panic("duplicate entry committed")
			}
		})
		o.OnHostInstruction(oracle.Far(0x110, 0x54ea), func(m *dg.Machine) (bool, error) {
			if scenario.qty == 0 {
				m.CPU.R[dg.AX] = 0
				m.CPU.IP = 0x5565
			} else {
				m.CPU.R[dg.SP] = oldSP
				m.CPU.R[dg.BP] = oldBP
				m.CPU.R[dg.SI] = oldSI
				m.CPU.IP = 0x56ec
			}
			m.CPU.Cycles++
			return true, nil
		})
		finished := false
		o.OnCall(oracle.Far(0x110, uint16(0x5a3b+scenario.group*0x90)), func(o *oracle.Oracle) { finished = true })
		campMust(catchWorldArmyFault(func() error {
			return o.RunUntil(oracle.NewCond("wrapper stock commit", func(*oracle.Oracle) bool { return finished }), oracle.Budget(2000000))
		}))
		got, e := st.Recover()
		campMust(e)
		expectedStock := rec.Words[4] - scenario.qty
		if o.Word(oracle.Far(0x1e88, campDS(scenario.group, scenario.row)+8)) != expectedStock || got.World.Army.Offers[campKey(scenario.group, scenario.row)].Stock != uint32(expectedStock) || !bytes.Equal(start.Bytes.Native[12:36], got.Bytes.Native[12:36]) {
			panic("wrapper or native army mismatch")
		}
		for i := 0; i < 12; i++ {
			at := 12 + i*2
			if o.Word(oracle.Far(0x1e88, 0x54a+uint16(i*2))) != binary.LittleEndian.Uint16(start.Bytes.Native[at:])-uint16(at+3) {
				panic("guest native army changed")
			}
		}
		name := fmt.Sprintf("wrapper-%d.state", len(routes))
		campMust(o.SaveStateFile(filepath.Join(*out, name)))
		campWrite(filepath.Join(*out, fmt.Sprintf("wrapper-%d-pair.json", len(routes))), got)
		campMust(os.WriteFile(filepath.Join(*out, fmt.Sprintf("wrapper-%d-native.ay", len(routes))), got.Bytes.Native, 0600))
		routes = append(routes, map[string]any{"group": scenario.group, "row": scenario.row, "kind": rec.Words[3], "qty": scenario.qty, "stock_before": rec.Words[4], "stock_after": expectedStock, "gold": got.World.Army.Gold, "purchases": port.Purchases, "records": port.Records, "state": name, "token": got.Token})
		st.Close()
	}
	// Exercise the new envelope's intersection with the existing battle anchor.
	// Reuse its original held object and initial enemy; do not rerun combat/RNG.
	resumeBase, e := os.ReadFile(filepath.Join(*input, "resume-native.ay"))
	campMust(e)
	held, e := os.ReadFile(filepath.Join(*input, "held.state"))
	campMust(e)
	var old struct {
		Begin OwnedWorld `json:"begin_world"`
	}
	raw, e := os.ReadFile(filepath.Join(*input, "old-resume-receipt.json"))
	campMust(e)
	campMust(json.Unmarshal(raw, &old))
	resumeDir := filepath.Join(*out, "resume-session")
	campMust(initializeProgressPair(resumeDir, resumeBase, c, cc, w))
	st, start, e := openProgressPair(resumeDir, c, cc)
	campMust(e)
	start, e = st.BindCamp(start.Token, 0, 1, maps)
	campMust(e)
	next := cloneCampWorld(start.World)
	next.Encounters = old.Begin.Encounters
	next, e = next.begin(c, cc, old.Begin.Battle.Encounter, old.Begin.Battle.State.Config)
	campMust(e)
	start, e = st.CommitSuspendedBattle(start.Token, next, held, maps)
	campMust(e)
	ref, e := savedResume(start.Bytes.World)
	campMust(e)
	plan := planOriginalRand(ref.Seed)
	random := uint32(plan.Value)
	settled, e := start.World.resolveEncounter(c, cc, EncounterContext{Kind: "random"}, DefeatInput{Reason: "retreat", Random: &random})
	campMust(e)
	start, e = st.Commit(start.Token, settled.After)
	campMust(e)
	returnBefore := start
	start, e = purchase(st, start, campKey(0, 1))
	campMust(e)
	returnBought := start
	st.Close()
	st, start, e = openProgressPair(resumeDir, c, cc)
	campMust(e)
	o, e := oracle.LoadWith(filepath.Join(*input, "PAM.AY"), *root, oracle.Options{Adlib: true})
	campMust(e)
	bridge := &controlledBattle{Store: st}
	ref, e = loadResumeInto(o, st, start, bridge)
	campMust(e)
	rec, e := decodeCampRecord(start.Bytes.Native, 0, 1)
	campMust(e)
	if ref == nil || ref.Phase != "return" || !bridge.Settled || o.Word(oracle.Far(0x1e88, campDS(0, 1)+8)) != rec.Words[4] {
		panic("return stock overlay")
	}
	// Bad identities cannot cause partial stock writes.
	beforeStock := o.Word(oracle.Far(0x1e88, campDS(0, 1)+8))
	o.WriteU16(oracle.Far(0x1e88, campDS(0, 1)+6), 25)
	if overlayCampStocks(o, start) == nil || o.Word(oracle.Far(0x1e88, campDS(0, 1)+8)) != beforeStock {
		panic("invalid overlay admitted")
	}
	cleared, e := st.CommitCheckpoint(start.Token, start.Bytes.Native, changedMaps)
	campMust(e)
	clearRef, e := savedResume(cleared.Bytes.World)
	campMust(e)
	if clearRef != nil || checkpointIntentSchema(cleared.Bytes) != campIntent {
		panic("return F7 failed")
	}
	st.Close()
	resumeResult := map[string]any{"phase": "return", "before_purchase": returnBefore, "after_purchase": returnBought, "stock_after_restore": beforeStock, "return_seed": ref.Seed, "f7_kept_v4": true, "identity_failure_preserved_stock": true}
	campWrite(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-camp-stock-probe", "initial": initial, "bound": bound, "bought": bought, "native_changed_offsets": changes, "refusals": cases, "faults": faults, "wrappers": routes, "resume": resumeResult, "controlled_entry": true, "formal_changed": false, "gui_tested": false})
	fmt.Println("camp stock purchase, cold reopen, four interruption points and source wrappers passed")
}
