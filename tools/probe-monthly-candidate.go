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

func mcMust(e error) {
	if e != nil {
		panic(e)
	}
}
func mcWrite(path string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	mcMust(e)
	mcMust(os.WriteFile(path, append(b, '\n'), 0600))
}
func main() {
	root := flag.String("root", "", "original")
	input := flag.String("input", "", "input")
	out := flag.String("out", "", "new output")
	mode := flag.String("mode", "probe", "probe/init")
	scenario := flag.String("scenario", "mixed", "native/mixed/bankrupt/large")
	session := flag.String("session", "", "new session")
	flag.Parse()
	if os.Getuid() != 1000 {
		panic("UID1000")
	}
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	var seed OwnedWorld
	for _, v := range []struct {
		name string
		dst  any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}, {"world-normal.json", &seed}} {
		b, e := os.ReadFile(filepath.Join(*input, v.name))
		mcMust(e)
		mcMust(pairStrictJSON(b, v.dst))
	}
	mcMust(setMonthlySavePAM(filepath.Join(*input, "PAM.AY")))
	base, e := os.ReadFile(filepath.Join(*input, "original-save.ay"))
	mcMust(e)
	maps := map[string][]byte{}
	for i := 0; i < 9; i++ {
		n := fmt.Sprintf("map%02d.ay", i)
		maps[n], e = os.ReadFile(filepath.Join(*input, "maps", n))
		mcMust(e)
	}
	makeWorld := func(which string) (OwnedWorld, []byte) {
		w := cloneCampWorld(seed)
		w.Army.Gold = 500
		w.Army.Slots = [6]ArmyStack{}
		w.Army.Slots[0] = ArmyStack{"native:01", 30}
		if which != "native" {
			w.Army.Slots[1] = ArmyStack{"openkb:wolf", 5}
		}
		if which == "bankrupt" {
			w.Army.Gold = 0
		}
		if which == "large" {
			w.Army.Slots[1].Count = 2500
		}
		w.Army.Offers[campKey(0, 1)] = ArmyOffer{"native:01", 2900}
		b, e := projectCampStocks(base, w.Army)
		mcMust(e)
		return w, b
	}
	if *mode == "init" {
		w, b := makeWorld(*scenario)
		mcMust(initializeProgressPair(*session, b, c, cc, w))
		return
	}
	mcMust(os.Mkdir(*out, 0700))
	results := []map[string]any{}
	var faultBefore progressPairBytes
	var faultNative []byte
	var faultFiles map[string][]byte
	for _, which := range []string{"native", "mixed", "bankrupt"} {
		folder := filepath.Join(*out, which)
		mcMust(os.Mkdir(folder, 0700))
		w, b := makeWorld(which)
		dir := filepath.Join(folder, "session")
		mcMust(initializeProgressPair(dir, b, c, cc, w))
		store, before, e := openProgressPair(dir, c, cc)
		mcMust(e)
		scratch := filepath.Join(folder, "scratch")
		mcMust(materializeNativeCheckpoint(*root, *input, scratch, before))
		o, e := oracle.LoadWith(filepath.Join(*input, "PAM.AY"), *root, oracle.Options{Adlib: true})
		mcMust(e)
		mcMust(o.LoadStateFile(filepath.Join(*input, "before-commit.state")))
		o.SetScratch(scratch)
		bp := o.Regs().BP
		wrapper := o.Word(oracle.Far(0x1e88, bp))
		outer := o.Word(oracle.Far(0x1e88, wrapper))
		o.OnHostInstruction(oracle.Far(0x110, 0x56ec), func(m *dg.Machine) (bool, error) {
			m.CPU.R[dg.BP] = outer
			m.CPU.R[dg.SP] = outer - 18
			m.CPU.IP = 0x26d6
			m.Write16(0x1e880+uint32(outer)-2, 0)
			m.Write16(0x1e880+uint32(outer)-10, 0)
			m.CPU.Cycles++
			return true, nil
		})
		mcMust(o.RunUntil(oracle.At(oracle.Far(0x110, 0x26d6)), oracle.Budget(16)))
		for i, n := range pairWorldResources(w).words() {
			o.WriteU16(oracle.Far(0x1e88, 0x4f2+uint16(i*2)), uint16(n))
		}
		o.WriteU16(oracle.Far(0x1e88, 0x56da), 1)
		o.WriteU16(oracle.Far(0x1e88, campDS(0, 1)+8), 2900)
		writeOriginalSeed(o, 0x12345678)
		// The original fixed-table shadow stays thirty native militia.
		for i := 0; i < 12; i++ {
			at := 12 + i*2
			o.WriteU16(oracle.Far(0x1e88, 0x54a+uint16(i*2)), binary.LittleEndian.Uint16(before.Bytes.Native[at:])-uint16(at+3))
		}
		eng := &game.Engine{Oracle: o, PAM: monthlySavePAM, PAMLoaded: true, HD: true}
		army, e := installWorldArmyPort(eng, store, before)
		mcMust(e)
		port, e := installMonthlyPort(eng, army)
		mcMust(e)
		mcMust(o.SaveStateFile(filepath.Join(folder, "before.state")))
		e = catchWorldArmyFault(func() error { return o.Run(6000000) })
		if !errors.Is(e, errMonthlyYield) {
			panic(fmt.Sprintf("monthly yield: %v", e))
		}
		mcMust(o.SaveStateFile(filepath.Join(folder, "held.state")))
		evidence := filepath.Join(folder, "evidence")
		mcMust(os.Mkdir(evidence, 0700))
		mcMust(port.Complete(*root, *input, scratch, evidence))
		after, e := store.Recover()
		mcMust(e)
		if port.Complete(*root, *input, scratch, evidence) == nil {
			panic("duplicate completion")
		}
		if !bytes.Equal(before.Bytes.Native[12:36], after.Bytes.Native[12:36]) {
			panic("shadow army changed")
		}
		if which == "mixed" {
			faultBefore = before.Bytes
			faultNative = bytes.Clone(after.Bytes.Native)
			faultFiles = maps
		}
		mcWrite(filepath.Join(folder, "before-pair.json"), before)
		mcWrite(filepath.Join(folder, "after-pair.json"), after)
		mcMust(os.WriteFile(filepath.Join(folder, "after-native.ay"), after.Bytes.Native, 0600))
		saved := after
		store.Close()
		store, after, e = openProgressPair(dir, c, cc)
		mcMust(e)
		if after.Token != saved.Token {
			panic("monthly cold changed")
		}
		store.Close()
		results = append(results, map[string]any{"name": which, "before": before, "after": after, "budget": port.Budget, "saves": port.Saves, "native_sha256": after.NativeSHA, "stock": after.World.Army.Offers[campKey(0, 1)].Stock, "seed": originalSeed(o), "counter": o.Word(oracle.Far(0x1e88, 0x56da))})
	}
	faults := []map[string]any{}
	for i, phase := range []string{"before-intent", "intent-durable", "native-durable", "world-durable"} {
		dir := filepath.Join(*out, fmt.Sprintf("fault-%d", i))
		mcMust(os.Mkdir(dir, 0700))
		mcMust(os.WriteFile(filepath.Join(dir, "gamedata.ay"), faultBefore.Native, 0600))
		mcMust(os.WriteFile(filepath.Join(dir, "gamedata.ay.army.json"), faultBefore.World, 0600))
		s, start, e := openProgressPair(dir, c, cc)
		mcMust(e)
		s.Fault = func(p string) error {
			if p == phase {
				return errors.New("injected month interruption")
			}
			return nil
		}
		_, e = s.CommitMonthly(start.Token, faultNative, faultFiles)
		if e == nil {
			panic("missing fault")
		}
		s.Close()
		s, got, e := openProgressPair(dir, c, cc)
		mcMust(e)
		gold := uint64(370)
		stock := uint32(3000)
		if phase == "before-intent" {
			gold = 500
			stock = 2900
		}
		if got.World.Army.Gold != gold || got.World.Army.Offers[campKey(0, 1)].Stock != stock {
			panic("partial monthly recovery")
		}
		again, e := s.Recover()
		mcMust(e)
		if again.Token != got.Token {
			panic("month billed twice")
		}
		s.Close()
		faults = append(faults, map[string]any{"phase": phase, "gold": gold, "stock": stock, "token": got.Token})
	}
	// A budget beyond the existing source UI is rejected before any guest/Go
	// projection. Every army count still remains in a Go uint32 slot.
	large, _ := makeWorld("large")
	_, largeErr := planMonthlyBudget(c, large.Army, large.Progress.Legacy04F6)
	if largeErr == nil {
		panic("large UI budget accepted")
	}
	mcWrite(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-go-monthly-candidate", "cases": results, "faults": faults, "wide_budget_rejected": true, "controlled_entry": true, "seed": uint32(0x12345678), "formal_changed": false})
	fmt.Println("Go monthly native/mixed/disband, cold reopen and four fault points passed")
}
