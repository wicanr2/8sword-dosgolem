//go:build ignore

// Diagnose normal function-key delivery from one unchanged GUI snapshot.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"github.com/wicanr2/dosgolem/oracle"
	"os"
	"path/filepath"
)

func main() {
	root := flag.String("root", "", "original root")
	state := flag.String("state", "", "fixed GUI state")
	out := flag.String("out", "", "new output directory")
	flag.Parse()
	must := func(e error) {
		if e != nil {
			panic(e)
		}
	}
	must(os.Mkdir(*out, 0755))
	for _, v := range []struct {
		Name string
		Hold uint64
	}{{"short", 3000}, {"five-frame", 500000}} {
		o, e := oracle.LoadWith(filepath.Join(*root, "PAM.AY"), *root, oracle.Options{Adlib: true})
		must(e)
		must(o.LoadStateFile(*state))
		events := []map[string]any{}
		histogram := map[string]uint64{}
		phase := "ctrl"
		for _, ip := range []uint16{0x0850, 0x0b6b, 0x3e92, 0x75c6} {
			ip := ip
			o.OnCall(oracle.Far(0x110, ip), func(o *oracle.Oracle) {
				r := o.Regs()
				if r.CS != 0x110 || r.DS != 0x1e88 {
					return
				}
				key := fmt.Sprintf("%s:%04x:AX=%04x", phase, ip, r.AX)
				histogram[key]++
				if ip < 0x3e92 {
					return
				}
				if len(events) >= 128 {
					panic("dispatch event bound")
				}
				events = append(events, map[string]any{"ip": ip, "step": o.Steps(), "registers": r, "ds_56bc": o.Word(oracle.Far(0x1e88, 0x56bc))})
			})
		}
		// GUI's Ctrl+Q may leave the modifier held in the captured machine.
		o.KeyDown(0x1d)
		must(o.RunCycles(3000))
		o.KeyUp(0x1d)
		must(o.RunCycles(30000))
		phase = "f2-down"
		o.KeyDown(0x3c)
		must(o.RunCycles(v.Hold))
		phase = "f2-up"
		o.KeyUp(0x3c)
		must(o.RunCycles(3000000))
		must(o.SaveStateFile(filepath.Join(*out, v.Name+".state")))
		report := map[string]any{"source_state": *state, "hold_cycles": v.Hold, "registers": o.Regs(), "events": events, "poll_histogram": histogram, "ds_56bc": o.Word(oracle.Far(0x1e88, 0x56bc)), "army_hex": fmt.Sprintf("%x", o.Bytes(oracle.Far(0x1e88, 0x54a), 24)), "bda_flags": o.Bytes(oracle.Far(0x40, 0x17), 1), "input": "normal Ctrl normalization then F2 make/break; no RAM, register, return or RNG edits"}
		b, e := json.MarshalIndent(report, "", "  ")
		must(e)
		must(os.WriteFile(filepath.Join(*out, v.Name+".json"), append(b, '\n'), 0600))
		o.Close()
		fmt.Println(v.Name, len(events), report["ds_56bc"])
	}
}
