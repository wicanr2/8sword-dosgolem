//go:build ignore

// Two controlled original map transitions and a typed Go plan from each input.
package main

import (
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"github.com/wicanr2/dosgolem/oracle"
	"os"
	"path/filepath"
)

func originMust(e error) {
	if e != nil {
		panic(e)
	}
}
func originSHA(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func originJSON(p string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	originMust(e)
	originMust(os.WriteFile(p, append(b, '\n'), 0600))
}
func main() {
	root := flag.String("root", "", "original root")
	input := flag.String("input", "", "fixed inputs")
	out := flag.String("out", "", "new output")
	flag.Parse()
	if os.Getuid() != 1000 || *root == "" || *input == "" || *out == "" {
		panic("fixed Docker inputs")
	}
	originMust(os.Mkdir(*out, 0700))
	state := filepath.Join(*input, "origin-source.state")
	raw, e := os.ReadFile(state)
	originMust(e)
	if originSHA(raw) != "e618d4343697fa00a50ab4b6021b169f6a5e21e4eaf86100c1fac9cd7a98777b" {
		panic("source state")
	}
	o, e := oracle.LoadWith(filepath.Join(*root, "PAM.AY"), *root, oracle.Options{Adlib: true})
	originMust(e)
	defer o.Close()
	originMust(o.LoadStateFile(state))
	base := o.Save()
	last := uint64(0)
	randomCalls := 0
	o.OnCall(oracle.Far(0x160a, 0x87), func(o *oracle.Oracle) {
		if o.Steps()-last < 50000 {
			return
		}
		last = o.Steps()
		o.KeyDown(0x1c)
		o.KeyUp(0x1c)
		originMust(o.SendKeys("Return"))
	})
	o.OnCall(oracle.Far(0x110, 0x1930), func(*oracle.Oracle) { randomCalls++ })
	packed, e := os.ReadFile(filepath.Join(*input, "origin-terrain-packed.ay"))
	originMust(e)

	totalRand := 0
	branchRand := 0
	callers := map[string]int{}
	branchDir := ""
	o.OnCall(oracle.Far(0x1797, 0x2cce), func(o *oracle.Oracle) {
		totalRand++
		r := o.Regs()
		key := fmt.Sprintf("%04X:%04X", o.Word(oracle.Far(r.SS, r.SP+2)), o.Word(oracle.Far(r.SS, r.SP)))
		callers[key]++
	})
	o.OnCall(oracle.Far(0x110, 0x1975), func(o *oracle.Oracle) {
		branchRand = totalRand
		originMust(os.WriteFile(filepath.Join(branchDir, "branch-before.ram"), o.Bytes(oracle.Far(0, 0), 1<<20), 0600))
	})
	rows := []map[string]any{}
	for _, region := range []uint16{0, 1} {
		o.Restore(base)
		totalRand = 0
		branchRand = 0
		callers = map[string]int{}
		last = 0
		randomCalls = 0
		dir := filepath.Join(*out, fmt.Sprintf("region-%d", region))
		originMust(os.Mkdir(dir, 0700))
		branchDir = dir
		scratch := filepath.Join(dir, "scratch")
		originMust(os.Mkdir(scratch, 0700))
		o.SetScratch(scratch)
		maps := map[string][]byte{}
		for i := 0; i < 9; i++ {
			name := fmt.Sprintf("map%02d.ay", i)
			b, e := os.ReadFile(filepath.Join(*input, "maps", name))
			originMust(e)
			maps[name] = b
			originMust(os.WriteFile(filepath.Join(scratch, name), b, 0600))
		}
		if region == 1 {
			_, e = o.CallBudget(2000000, oracle.Far(0x110, 0x4542), region)
			originMust(e)
			_, e = o.CallBudget(2000000, oracle.Far(0x110, 0x479a), region)
			originMust(e)
			o.WriteU16(oracle.Far(0x1e88, 0x56d6), region)
			o.WriteU16(oracle.Far(0x1e88, 0x8e12), 35)
			o.WriteU16(oracle.Far(0x1e88, 0x8e44), 35)
		}
		for i := 0; i < 12; i++ {
			o.WriteU16(oracle.Far(0x1e88, 0x54a+uint16(i*2)), 0)
		}
		// The last map byte also participates in the original 5761-byte reset.
		o.WriteU8(oracle.Far(0x9c00, 5760), 100)
		before := append([]byte(nil), o.Bytes(oracle.Far(0, 0), 1<<20)...)
		originMust(os.WriteFile(filepath.Join(dir, "before.ram"), before, 0600))
		originMust(o.SaveStateFile(filepath.Join(dir, "before.state")))
		_, e = o.CallBudget(20000000, oracle.Far(0x110, 0x1796), 1)
		originMust(e)
		branchInput, e := os.ReadFile(filepath.Join(dir, "branch-before.ram"))
		originMust(e)
		plan, e := planOriginMap(branchInput, maps, packed)
		originMust(e)
		originJSON(filepath.Join(dir, "go-plan.json"), plan)
		after := append([]byte(nil), o.Bytes(oracle.Far(0, 0), 1<<20)...)
		originMust(os.WriteFile(filepath.Join(dir, "after.ram"), after, 0600))
		originMust(o.SaveStateFile(filepath.Join(dir, "after.state")))
		originJSON(filepath.Join(dir, "before-maps.json"), maps)
		row := map[string]any{"region": region, "before_sha256": originSHA(before), "after_sha256": originSHA(after), "random_calls": randomCalls, "controlled_empty_army": true, "controlled_last_map_byte": true, "original_saved_map": plan.CurrentName}
		row["total_rand_calls"] = totalRand
		row["rand_calls_before_map"] = branchRand
		row["rand_calls_map"] = totalRand - branchRand
		row["rand_callers"] = callers
		rows = append(rows, row)
	}
	originJSON(filepath.Join(*out, "receipt.json"), map[string]any{"status": "captured-original-origin-and-go-plans", "rows": rows, "source_state_sha256": originSHA(raw), "player_path": false, "seed_method": "restore the same fixed VM before each case; no seed write or reroll"})
}
