// Spec030 diagnostic: original Oracle notifications after an actual GUI snapshot.
package main

import (
	"encoding/json"
	"flag"
	"os"
	"path/filepath"

	"github.com/wicanr2/dosgolem/oracle"
)

func main() {
	root := flag.String("root", "", "original")
	snapshot := flag.String("state", "", "actual GUI state")
	out := flag.String("out", "", "new output")
	flag.Parse()
	must := func(e error) {
		if e != nil {
			panic(e)
		}
	}
	must(os.Mkdir(*out, 0755))
	o, e := oracle.LoadWith(filepath.Join(*root, "PREDELLA.EXE"), *root, oracle.Options{Adlib: true, ProgramPath: `C:\PREDELLA.EXE`})
	must(e)
	must(o.LoadStateFile(*snapshot))
	var pon, duplicates int
	lastPon, lastPhase := -1, -1
	events := []map[string]any{}
	o.OnCall(oracle.Addr{Seg: 0x14d2, Off: 0x625}, func(*oracle.Oracle) { pon++ })
	for i, off := range []uint16{0xa05, 0xa6e, 0xad7, 0xb40, 0xba9} {
		o.OnCall(oracle.Addr{Seg: 0xf67, Off: off}, func(*oracle.Oracle) {
			r := o.Regs()
			word := func(off uint16) uint16 { return o.Word(oracle.Addr{Seg: r.SS, Off: off}) }
			dup := pon == lastPon && i == lastPhase
			if dup {
				duplicates++
				if duplicates == 1 {
					must(o.SaveStateFile(filepath.Join(*out, "duplicate.state")))
				}
			}
			events = append(events, map[string]any{"step": o.Steps(), "phase": i, "pon_returns": pon, "duplicate": dup, "ss": r.SS, "bp": r.BP, "sp": r.SP, "port": word(r.SP), "value": word(r.SP + 2)})
			lastPon, lastPhase = pon, i
			if len(events) > 600 {
				panic("event bound")
			}
		})
	}
	must(o.Run(12000000))
	must(o.SaveStateFile(filepath.Join(*out, "final.state")))
	raw, e := json.MarshalIndent(map[string]any{"events": events, "duplicate_notifications": duplicates, "method": "Unhooked original rendering; only read-only PC observers; no writes or key input."}, "", "  ")
	must(e)
	must(os.WriteFile(filepath.Join(*out, "receipt.json"), append(raw, '\n'), 0644))
}
