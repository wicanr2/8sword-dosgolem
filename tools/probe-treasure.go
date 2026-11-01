//go:build ignore

// Controlled original dispatcher frame; choose using real DOS keyboard input.
package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
	"os"
	"path/filepath"
)

func tpMust(e error) {
	if e != nil {
		panic(e)
	}
}
func tpWrite(p string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	tpMust(e)
	tpMust(os.WriteFile(p, append(b, '\n'), 0600))
}

func main() {
	root := flag.String("root", "", "original")
	input := flag.String("input", "", "frozen input")
	out := flag.String("out", "", "new output")
	mode := flag.String("mode", "original", "original/candidate/init")
	session := flag.String("session", "", "new session")
	flag.Parse()
	if os.Getuid() != 1000 {
		panic("UID1000")
	}
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	var seed OwnedWorld
	for _, v := range []struct {
		Name string
		Dst  any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}, {"world-normal.json", &seed}} {
		b, e := os.ReadFile(filepath.Join(*input, v.Name))
		tpMust(e)
		tpMust(pairStrictJSON(b, v.Dst))
	}
	tpMust(setMonthlySavePAM(filepath.Join(*input, "PAM.AY")))
	base, e := os.ReadFile(filepath.Join(*input, "original-save.ay"))
	tpMust(e)
	makeWorld := func(gold, lead uint64, amount uint16) (OwnedWorld, []byte) {
		w := cloneCampWorld(seed)
		w.Army.Gold = gold
		w.Army.Leadership = lead
		w.Army.Slots = [6]ArmyStack{{"native:01", 30}, {"openkb:wolf", 5}}
		b := bytes.Clone(base)
		tpMust(writeTreasureAmount(b, 0, 0, amount))
		return w, b
	}
	if *mode == "init" {
		amount, e := treasureAmount(base, 0, 0)
		tpMust(e)
		w, b := makeWorld(500, 1000, amount)
		tpMust(initializeProgressPair(*session, b, c, cc, w))
		return
	}
	tpMust(os.Mkdir(*out, 0700))
	rows := []map[string]any{}
	for _, tc := range []struct {
		Name       string
		Choice     int
		Gold, Lead uint64
		Amount     uint16
	}{{"gold", 1, 500, 1000, 500}, {"leadership", 2, 500, 1000, 509}, {"gold-cap", 1, 29990, 1000, 500}, {"leadership-cap", 2, 500, 29990, 509}, {"gold-wrap", 1, 30000, 1000, 5000}, {"cancel", 0, 500, 1000, 500}, {"empty", 1, 500, 1000, 0}} {
		folder := filepath.Join(*out, tc.Name)
		tpMust(os.Mkdir(folder, 0700))
		w, b := makeWorld(tc.Gold, tc.Lead, tc.Amount)
		storeDir := filepath.Join(folder, "session")
		tpMust(initializeProgressPair(storeDir, b, c, cc, w))
		store, before, e := openProgressPair(storeDir, c, cc)
		tpMust(e)
		scratch := filepath.Join(folder, "scratch")
		tpMust(materializeNativeCheckpoint(*root, *input, scratch, before))
		o, e := oracle.LoadWith(filepath.Join(*input, "PAM.AY"), *root, oracle.Options{Adlib: true})
		tpMust(e)
		tpMust(o.LoadStateFile(filepath.Join(*input, "before-commit.state")))
		o.SetScratch(scratch)
		r := o.Regs()
		wrapper := o.Word(oracle.Far(0x1e88, r.BP))
		outer := o.Word(oracle.Far(0x1e88, wrapper))
		if o.Word(oracle.Far(0x1e88, outer+2)) != 0xbc7 {
			panic("source dispatcher frame")
		}
		o.OnHostInstruction(oracle.Far(0x110, 0x56ec), func(m *dg.Machine) (bool, error) {
			m.CPU.R[dg.BP] = outer
			m.CPU.R[dg.SP] = outer - 18
			m.CPU.IP = 0x25e4
			m.Write16(0x1e880+uint32(outer)-2, 0)
			m.Write16(0x1e880+uint32(outer)-16, 59)
			m.CPU.Cycles++
			return true, nil
		})
		tpMust(o.RunUntil(oracle.At(oracle.Far(0x110, 0x25e4)), oracle.Budget(16)))
		for i, n := range pairWorldResources(w).words() {
			o.WriteU16(oracle.Far(0x1e88, 0x4f2+uint16(i*2)), uint16(n))
		}
		for i := 0; i < 12; i++ {
			at := 12 + i*2
			o.WriteU16(oracle.Far(0x1e88, 0x54a+uint16(i*2)), binary.LittleEndian.Uint16(before.Bytes.Native[at:])-uint16(at+3))
		}
		for g := 0; g < 8; g++ {
			for row := 0; row < 10; row++ {
				n, e := treasureAmount(before.Bytes.Native, g, row)
				tpMust(e)
				o.WriteU16(oracle.Far(0x1e88, uint16(0x4490+g*20+row*2)), n)
			}
		}
		o.WriteU16(oracle.Far(0x1e88, 0x56d6), 0)
		o.WriteU16(oracle.Far(0x1e88, 0x8e12), o.Word(oracle.Far(0x1e88, 0x8c60)))
		o.WriteU16(oracle.Far(0x1e88, 0x8e44), o.Word(oracle.Far(0x1e88, 0x8c62)))
		writeOriginalSeed(o, 0x12345678)
		keys := []uint8{}
		o.OnCall(oracle.Far(0x110, 0x20c7), func(q *oracle.Oracle) { q.WriteU16(oracle.Far(0x1e88, q.Regs().BP-4), 0) })
		o.OnCall(oracle.Far(0x110, 0x20d4), func(q *oracle.Oracle) {
			scan := uint8(0x1c)
			if tc.Choice == 0 {
				scan = 1
			} else if tc.Choice == 2 && len(keys) == 0 {
				scan = 0x50
			}
			if len(keys) > 3 {
				panic("extra source keyboard request")
			}
			q.PressKey(oracle.Key(scan))
			keys = append(keys, scan)
		})
		eng := &game.Engine{Oracle: o, PAM: monthlySavePAM, PAMLoaded: true, HD: true}
		var port *treasurePort
		if *mode == "candidate" {
			army, e := installWorldArmyPort(eng, store, before)
			tpMust(e)
			port, e = installTreasurePort(eng, army)
			tpMust(e)
		}
		tpMust(o.SaveStateFile(filepath.Join(folder, "before.state")))
		if *mode == "candidate" {
			e = catchWorldArmyFault(func() error { return o.RunUntil(oracle.At(oracle.Far(0x110, 0x2440)), oracle.Budget(6000000)) })
			tpMust(e)
			if port.Awarded {
				e = catchWorldArmyFault(func() error { return o.Run(1) })
			}
			if tc.Amount > 0 && tc.Choice != 0 {
				if !errors.Is(e, errTreasureYield) {
					panic(fmt.Sprintf("treasure yield %v", e))
				}
			} else if e != nil {
				panic(e)
			}
		} else {
			tpMust(o.RunUntil(oracle.At(oracle.Far(0x110, 0x2440)), oracle.Budget(6000000)))
		}
		state := filepath.Join(folder, "after.state")
		tpMust(o.SaveStateFile(state))
		var native []byte
		if *mode == "candidate" && port.Pending {
			tpMust(port.Complete(*root, *input, scratch, ""))
			native = port.Army.Current.Bytes.Native
		} else {
			maps, e := readNativeCheckpointMaps(scratch)
			tpMust(e)
			native, _, e = serializeTreasureNative(*root, filepath.Join(*input, "PAM.AY"), state, filepath.Join(folder, "serialized"), maps)
			tpMust(e)
		}
		tpMust(os.WriteFile(filepath.Join(folder, "after-native.ay"), native, 0600))
		got, e := decodeNativeResources(nativeProgressSource, native)
		tpMust(e)
		tpWrite(filepath.Join(folder, "before-pair.json"), before)
		row := map[string]any{"name": tc.Name, "choice": tc.Choice, "amount": tc.Amount, "before": pairWorldResources(w), "after": got, "keys": keys, "seed": originalSeed(o), "native_sha256": nativeSHA(native)}
		if *mode == "candidate" {
			after, e := store.Recover()
			tpMust(e)
			tpWrite(filepath.Join(folder, "after-pair.json"), after)
			if port.Committed && port.Complete(*root, *input, scratch, "") == nil {
				panic("duplicate treasure")
			}
			row["world"] = after.World
			row["token"] = after.Token
			row["awards"] = port.Awards
			store.Close()
			var cold progressPairSnapshot
			store, cold, e = openProgressPair(storeDir, c, cc)
			tpMust(e)
			if cold.Token != after.Token {
				panic("cold treasure changed")
			}
		}
		store.Close()
		rows = append(rows, row)
	}
	tpWrite(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-treasure-" + *mode, "cases": rows, "seed": uint32(0x12345678), "controlled_dispatcher": true, "controlled_position": true, "formal_changed": false})
}
