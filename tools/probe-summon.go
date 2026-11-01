//go:build ignore

package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
	"os"
	"path/filepath"
)

type summonProbeSession interface {
	Finish(string, string, string) error
	Report() map[string]any
}

var summonProbeInstall func(*game.Engine, *worldArmyPort) (summonProbeSession, error)
var summonProbeYield error

func acMust(e error) {
	if e != nil {
		panic(e)
	}
}
func acWrite(p string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	acMust(e)
	acMust(os.WriteFile(p, append(b, '\n'), 0600))
}
func main() {
	root := flag.String("root", "", "original")
	input := flag.String("input", "", "input")
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
		raw, e := os.ReadFile(filepath.Join(*input, v.Name))
		acMust(e)
		acMust(pairStrictJSON(raw, v.Dst))
	}
	acMust(setMonthlySavePAM(filepath.Join(*input, "PAM.AY")))
	base, e := os.ReadFile(filepath.Join(*input, "original-save.ay"))
	acMust(e)

	type summonCase struct {
		Name   string
		Rank   uint32
		Bonus  bool
		Uses   uint16
		Native [6]ArmyStack
	}
	makeWorld := func(tc summonCase) (OwnedWorld, []byte) {
		w := cloneCampWorld(seed)
		w.Army.Gold = 500
		w.Army.Leadership = 1000
		w.Progress.Rank = tc.Rank
		w.Army.RecruitRank = tc.Rank
		w.Army.Slots = tc.Native
		for i, st := range w.Army.Slots {
			if st.Unit == "" {
				w.Army.Slots[i] = ArmyStack{"openkb:wolf", 5}
				break
			}
		}
		b := bytes.Clone(base)
		acMust(setAlchemyWord(b, alchemyLearnedOffset, 1))
		acMust(setAlchemyWord(b, summonUsesOffset, tc.Uses))
		bonus := uint16(0)
		if tc.Bonus {
			bonus = 1
		}
		acMust(setAlchemyWord(b, summonBonusOffset, bonus))
		idx, x := c.index()
		acMust(x)
		for i, st := range tc.Native {
			k := uint16(0)
			if st.Unit != "" {
				k = idx[st.Unit].NativeKind
				if k == 0 {
					panic("native fixture")
				}
			}
			acMust(setAlchemyWord(b, 12+i*4, k))
			acMust(setAlchemyWord(b, 14+i*4, uint16(st.Count)))
		}
		return w, b
	}
	if *mode == "init" {
		w, b := makeWorld(summonCase{"initial", 1, false, 2, [6]ArmyStack{{"native:01", 30}}})
		acMust(initializeProgressPair(*session, b, c, cc, w))
		return
	}
	acMust(os.Mkdir(*out, 0700))
	rows := []map[string]any{}

	for _, tc := range []summonCase{
		{"merge", 1, false, 2, [6]ArmyStack{{"native:16", 30}}},
		{"new-bonus", 5, true, 2, [6]ArmyStack{{"native:01", 30}}},
		{"full", 1, false, 2, [6]ArmyStack{{"native:01", 10}, {"native:02", 10}, {"native:03", 10}, {"native:04", 10}, {"native:05", 10}, {"native:06", 10}}},
		{"unavailable", 1, false, 0, [6]ArmyStack{{"native:16", 30}}},
	} {
		if tc.Uses == 0 && *mode == "original" {
			continue
		}
		dir := filepath.Join(*out, tc.Name)
		acMust(os.Mkdir(dir, 0700))
		w, b := makeWorld(tc)
		storeDir := filepath.Join(dir, "session")
		acMust(initializeProgressPair(storeDir, b, c, cc, w))
		store, before, e := openProgressPair(storeDir, c, cc)
		acMust(e)
		scratch := filepath.Join(dir, "scratch")
		acMust(materializeNativeCheckpoint(*root, *input, scratch, before))
		o, e := oracle.LoadWith(filepath.Join(*input, "PAM.AY"), *root, oracle.Options{Adlib: true})
		acMust(e)
		acMust(o.LoadStateFile(filepath.Join(*input, "summon-entry.state")))
		o.SetScratch(scratch)
		r := o.Regs()
		if r.CS != 0x110 || r.IP != 0x68ce || o.Arg(0) != 2 || o.Word(oracle.Far(r.SS, r.SP)) != 0x6896 {
			panic("fixed F4 entry frame")
		}
		for i, n := range pairWorldResources(w).words() {
			o.WriteU16(oracle.Far(0x1e88, 0x4f2+uint16(i*2)), uint16(n))
		}
		for i := 0; i < 12; i++ {
			at := 12 + i*2
			o.WriteU16(oracle.Far(0x1e88, 0x54a+uint16(i*2)), binary.LittleEndian.Uint16(before.Bytes.Native[at:])-uint16(at+3))
		}
		o.WriteU16(oracle.Far(0x1e88, 0x26aa), 1)
		bonus := uint16(0)
		if tc.Bonus {
			bonus = 1
		}
		o.WriteU16(oracle.Far(0x1e88, 0x26b0), bonus)
		o.WriteU16(oracle.Far(0x1e88, 0x2b2c), tc.Uses)
		o.WriteU16(oracle.Far(0x1e88, 0x56e6), 0)
		writeOriginalSeed(o, 0x12345678)
		roll, kind, count := uint16(0), uint16(0), uint16(0)
		seenRoll, seenAmount, keyed := false, false, false
		o.OnCall(oracle.Far(0x110, 0x6c2b), func(q *oracle.Oracle) {
			if !seenRoll {
				roll = q.Regs().AX
				seenRoll = true
			}
		})
		o.OnCall(oracle.Far(0x110, 0x6c87), func(q *oracle.Oracle) {
			kind = q.Word(oracle.Far(0x1e88, q.Regs().BP-12))
			count = q.Word(oracle.Far(0x1e88, q.Regs().BP-2))
			seenAmount = true
		})
		o.OnCall(oracle.Far(0x110, 0x6e29), func(q *oracle.Oracle) {
			if !keyed {
				q.PressKey(oracle.Key(0x1c))
				keyed = true
			}
		})
		var port summonProbeSession
		if *mode == "candidate" {
			eng := &game.Engine{Oracle: o, PAM: monthlySavePAM, PAMLoaded: true, HD: true}
			army, e := installWorldArmyPort(eng, store, before)
			acMust(e)
			port, e = summonProbeInstall(eng, army)
			acMust(e)
		}
		acMust(o.SaveStateFile(filepath.Join(dir, "before.state")))
		stop := uint16(0x68f9)
		if *mode == "candidate" {
			stop = 0x6906
		}
		e = catchWorldArmyFault(func() error { return o.RunUntil(oracle.At(oracle.Far(0x110, stop)), oracle.Budget(8000000)) })
		if tc.Uses == 0 {
			if e == nil || seenRoll {
				panic("empty uses admitted")
			}
			after, x := store.Recover()
			acMust(x)
			if before.Token != after.Token {
				panic("rejection changed store")
			}
			acMust(o.SaveStateFile(filepath.Join(dir, "after.state")))
			rows = append(rows, map[string]any{"name": tc.Name, "rejected": true, "token": after.Token, "error": e.Error()})
			store.Close()
			continue
		}
		acMust(e)
		if !seenRoll || !seenAmount || !keyed {
			panic("missing original observations")
		}
		if *mode == "candidate" {
			e = catchWorldArmyFault(func() error { return o.Run(1) })
			if !errors.Is(e, summonProbeYield) {
				panic(fmt.Sprintf("summon yield %v", e))
			}
		}
		acMust(o.SaveStateFile(filepath.Join(dir, "after.state")))
		if *mode == "candidate" {
			acMust(port.Finish(*root, *input, scratch))
		}
		var n []byte
		if *mode == "original" {
			maps, e := readNativeCheckpointMaps(scratch)
			acMust(e)
			n, _, e = serializeSummonNative(*root, filepath.Join(*input, "PAM.AY"), filepath.Join(dir, "after.state"), filepath.Join(dir, "serialized"), maps)
			acMust(e)
		} else {
			after, e := store.Recover()
			acMust(e)
			n = after.Bytes.Native
			acWrite(filepath.Join(dir, "after-pair.json"), after)
		}
		acMust(os.WriteFile(filepath.Join(dir, "after-native.ay"), n, 0600))
		got, e := decodeNativeResources(nativeProgressSource, n)
		acMust(e)
		acWrite(filepath.Join(dir, "before-pair.json"), before)
		row := map[string]any{"name": tc.Name, "before": pairWorldResources(w), "after": got, "roll": roll, "kind": kind, "count": count, "bonus": tc.Bonus, "uses_before": tc.Uses, "uses_after": o.Word(oracle.Far(0x1e88, 0x2b2c)), "seed_after": originalSeed(o), "native_sha256": nativeSHA(n)}
		var nativeRows [12]uint16
		for i := range nativeRows {
			nativeRows[i], e = alchemyWord(n, 12+i*2)
			acMust(e)
		}
		row["native_army_after"] = nativeRows
		row["rank"] = tc.Rank
		if port != nil {
			row["go"] = port.Report()
		}
		store.Close()
		store, cold, e := openProgressPair(storeDir, c, cc)
		acMust(e)
		row["cold_world"] = cold.World
		store.Close()
		rows = append(rows, row)
	}
	acWrite(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-summon-" + *mode, "cases": rows, "seed": uint32(0x12345678), "controlled_f4_entry": true, "formal_changed": false})
}
