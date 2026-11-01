//go:build ignore

// Original CPU controls at an explicitly recovered real dispatcher frame.
package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func monthMust(e error) {
	if e != nil {
		panic(e)
	}
}
func monthWrite(path string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	monthMust(e)
	monthMust(os.WriteFile(path, append(b, '\n'), 0600))
}
func main() {
	root := flag.String("root", "", "read-only original")
	input := flag.String("input", "", "frozen input")
	out := flag.String("out", "", "new output")
	flag.Parse()
	if os.Getuid() != 1000 {
		panic("UID1000")
	}
	monthMust(os.Mkdir(*out, 0700))
	var c ArmyCatalog
	raw, e := os.ReadFile(filepath.Join(*input, "army-catalog.json"))
	monthMust(e)
	monthMust(pairStrictJSON(raw, &c))
	pam, e := os.ReadFile(filepath.Join(*input, "PAM.AY"))
	monthMust(e)
	caps, e := monthlyCaps(pam)
	monthMust(e)
	base, e := os.ReadFile(filepath.Join(*input, "original-save.ay"))
	monthMust(e)
	maps := map[string][]byte{}
	for i := 0; i < 9; i++ {
		n := fmt.Sprintf("map%02d.ay", i)
		maps[n], e = os.ReadFile(filepath.Join(*input, "maps", n))
		monthMust(e)
	}
	cases := []struct {
		Name                 string
		Gold, Income         uint64
		Kind, Count, Counter uint16
	}{{"paid", 500, 100, 1, 30, 1}, {"exact", 29, 1, 1, 30, 1}, {"disband", 0, 1, 1, 30, 1}, {"cap", 30000, 100, 0, 0, 1}, {"no-month", 500, 100, 1, 30, 2}, {"word-expense-wrap", 500, 100, 1, 50000, 1}, {"word-income-wrap", 30000, 30000, 1, 30, 1}}
	receipts := []map[string]any{}
	for _, tc := range cases {
		dir := filepath.Join(*out, tc.Name)
		monthMust(os.Mkdir(dir, 0700))
		o, e := oracle.LoadWith(filepath.Join(*input, "PAM.AY"), *root, oracle.Options{Adlib: true})
		monthMust(e)
		monthMust(o.LoadStateFile(filepath.Join(*input, "before-commit.state")))
		o.SetScratch(dir)
		regs := o.Regs()
		commonBP := regs.BP
		wrapperBP := o.Word(oracle.Far(0x1e88, commonBP))
		outerBP := o.Word(oracle.Far(0x1e88, wrapperBP))
		if o.Word(oracle.Far(0x1e88, commonBP+2)) != 0x5a21 || o.Word(oracle.Far(0x1e88, wrapperBP+2)) != 0x25b1 || o.Word(oracle.Far(0x1e88, outerBP+2)) != 0xbc7 {
			panic("fixed real source frame")
		}
		o.OnHostInstruction(oracle.Far(0x110, 0x56ec), func(m *dg.Machine) (bool, error) {
			m.CPU.R[dg.BP] = outerBP
			m.CPU.R[dg.SP] = outerBP - 18
			m.CPU.IP = 0x26d6
			m.Write16(0x1e880+uint32(outerBP)-2, 0)
			m.Write16(0x1e880+uint32(outerBP)-10, 0)
			m.CPU.Cycles++
			return true, nil
		})
		monthMust(o.RunUntil(oracle.At(oracle.Far(0x110, 0x26d6)), oracle.Budget(16)))
		o.WriteU16(oracle.Far(0x1e88, 0x4f8), uint16(tc.Gold))
		o.WriteU16(oracle.Far(0x1e88, 0x4f6), uint16(tc.Income))
		o.WriteU16(oracle.Far(0x1e88, 0x56da), tc.Counter)
		o.WriteBytes(oracle.Far(0x1e88, 0x54a), make([]byte, 24))
		o.WriteU16(oracle.Far(0x1e88, 0x54a), tc.Kind)
		o.WriteU16(oracle.Far(0x1e88, 0x54c), tc.Count)
		// A depleted real camp proves the producer without waiting a whole month.
		o.WriteU16(oracle.Far(0x1e88, campDS(0, 1)+8), 2900)
		writeOriginalSeed(o, 0x12345678)
		monthMust(o.SaveStateFile(filepath.Join(dir, "before.state")))
		beforeNative := append([]byte{}, base...)
		for g := 0; g < 5; g++ {
			for row := 0; row < 24; row++ {
				for f := 0; f < 5; f++ {
					at := campOffset(g, row, f)
					binary.LittleEndian.PutUint16(beforeNative[at:], o.Word(oracle.Far(0x1e88, campDS(g, row)+uint16(f*2)))+uint16(at+3))
				}
			}
		}
		army := OwnedArmy{Gold: tc.Gold, Leadership: 30000, RecruitRank: 1, Rules: "native", Offers: map[string]ArmyOffer{}}
		if tc.Kind > 0 {
			army.Slots[0] = ArmyStack{fmt.Sprintf("native:%02d", tc.Kind), uint32(tc.Count)}
		}
		budget, modelErr := planMonthlyBudget(c, army, tc.Income)
		target := uint16(0x284d)
		if tc.Counter == 2 {
			target = 0x2851
		}
		monthMust(o.RunUntil(oracle.At(oracle.Far(0x110, target)), oracle.Budget(6000000)))
		monthMust(o.SaveStateFile(filepath.Join(dir, "after.state")))
		if tc.Counter == 1 {
			expected, e := refillMonthlyCamps(beforeNative, pam)
			monthMust(e)
			for g := 0; g < 5; g++ {
				for row := 0; row < 24; row++ {
					rec, e := decodeCampRecord(expected, g, row)
					monthMust(e)
					if o.Word(oracle.Far(0x1e88, campDS(g, row)+8)) != rec.Words[4] {
						panic("stock model mismatch")
					}
				}
			}
			if modelErr == nil {
				empty := o.Word(oracle.Far(0x1e88, 0x54c)) == 0
				if uint64(o.Word(oracle.Far(0x1e88, 0x4f8))) != budget.After || empty != (budget.Disbanded || tc.Count == 0) {
					panic("budget model mismatch")
				}
			}
			n, files, e := serializeMonthlyNative(*root, filepath.Join(*input, "PAM.AY"), filepath.Join(dir, "after.state"), filepath.Join(dir, "serialized"), maps)
			monthMust(e)
			monthMust(os.WriteFile(filepath.Join(dir, "serialized.ay"), n, 0600))
			monthWrite(filepath.Join(dir, "maps.json"), map[string]any{"count": len(files), "native_sha256": nativeSHA(n)})
		} else if o.Word(oracle.Far(0x1e88, 0x4f8)) != uint16(tc.Gold) || o.Word(oracle.Far(0x1e88, campDS(0, 1)+8)) != 2900 {
			panic("non-month changed resources")
		}
		rows := o.Bytes(oracle.Far(0x1e88, 0x54a), 24)
		receipts = append(receipts, map[string]any{"name": tc.Name, "budget": budget, "model_rejected": modelErr != nil, "gold": o.Word(oracle.Far(0x1e88, 0x4f8)), "army_hex": fmt.Sprintf("%x", rows), "stock": o.Word(oracle.Far(0x1e88, campDS(0, 1)+8)), "counter": o.Word(oracle.Far(0x1e88, 0x56da)), "seed": originalSeed(o), "original_before_state": "before.state", "original_after_state": "after.state"})
		if !bytes.Equal(pam, func() []byte { b, _ := os.ReadFile(filepath.Join(*input, "PAM.AY")); return b }()) {
			panic("source changed")
		}
	}
	monthWrite(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-original-monthly-model", "source_sha256": nativeSHA(pam), "caps": caps, "cases": receipts, "controlled_frame": true, "seed": uint32(0x12345678), "formal_changed": false})
	fmt.Println("Original month controls, camps and detached native serializer passed")
}
