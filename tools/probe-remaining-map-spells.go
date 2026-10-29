//go:build ignore

// 030 DRAFT. Ordinary boot/new game/F4 and original menu inputs; explicit resources.
package main

import (
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"github.com/wicanr2/dosgolem/oracle"
	"os"
	"path/filepath"
	"strings"
)

func must(e error) {
	if e != nil {
		panic(e)
	}
}
func save(p string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	must(e)
	must(os.WriteFile(p, append(b, '\n'), 0644))
}
func main() {
	root := flag.String("root", "", "original")
	out := flag.String("out", "", "new research")
	flag.Parse()
	must(os.Mkdir(*out, 0755))
	o, e := oracle.LoadWith(filepath.Join(*root, "PREDELLA.EXE"), *root, oracle.Options{Adlib: true, ProgramPath: `C:\PREDELLA.EXE`})
	must(e)
	o.SetScratch(filepath.Join(*out, "boot-scratch"))
	o.SetClock(12, 0, 0, 0)
	o.SetDOSBoxCycles(3000)
	scene := ""
	load := uint16(0)
	bind := func() {
		if load != 0 {
			return
		}
		for _, ov := range o.Overlays() {
			if strings.EqualFold(ov.Name, "PAM.AY") {
				load = ov.Seg
				o.OnCall(oracle.Addr{Seg: load + 0x13c2, Off: 0xae3}, func(q *oracle.Oracle) {
					switch q.Arg(0) {
					case 158, 218, 278:
						scene = "menu"
					case 338, 398:
						scene = "confirm"
					case 990, 1010, 1030, 1050, 1070, 1090, 1110:
						scene = "map"
					}
				})
			}
		}
	}
	advance := func(ms int) {
		for ; ms > 0; ms -= 10 {
			must(o.RunCycles(30000))
			bind()
			if o.Steps() > 200000000 {
				panic("boot bound")
			}
		}
	}
	press := func(scan uint8) { o.KeyDown(scan); advance(100); o.KeyUp(scan); advance(150) }
	advance(200)
	for i := 0; i < 2; i++ {
		must(o.TypeKeys("1"))
		advance(250)
	}
	advance(500)
	if load == 0 {
		must(o.SendKeys("Esc"))
	}
	for i := 0; i < 300 && scene != "menu"; i++ {
		advance(100)
	}
	if scene != "menu" {
		panic("no menu")
	}
	press(0x50)
	press(0x1c)
	advance(500)
	press(0x1c)
	advance(3000)
	if scene != "map" {
		panic("no map")
	}
	must(o.SaveStateFile(filepath.Join(*out, "map.state")))
	o.Close()
	for spell := 0; spell < 8; spell++ {
		dir := filepath.Join(*out, fmt.Sprintf("map-%d", spell))
		must(os.Mkdir(dir, 0755))
		q, e := oracle.LoadWith(filepath.Join(*root, "PREDELLA.EXE"), *root, oracle.Options{Adlib: true})
		must(e)
		must(q.LoadStateFile(filepath.Join(*out, "map.state")))
		q.SetScratch(filepath.Join(dir, "scratch"))
		ds := load + 0x1d78
		mutations := []map[string]any{}
		change := func(off, val uint16) {
			at := oracle.Addr{Seg: ds, Off: off}
			old := q.Word(at)
			q.WriteU16(at, val)
			mutations = append(mutations, map[string]any{"offset": off, "old": old, "new": val})
		}
		change(0x26aa, 1)
		for i := 0; i < 8; i++ {
			change(0x2b28+uint16(i*2), 2)
		}
		events := []map[string]any{}
		started, done := false, false
		lastCursor := -1
		keys := []map[string]any{}
		key := func(scan uint8, why string) {
			q.PressKey(oracle.Key(scan))
			keys = append(keys, map[string]any{"step": q.Steps(), "scan": scan, "why": why})
		}
		word := func(off uint16) uint16 { return q.Word(oracle.Addr{Seg: ds, Off: off}) }
		fields := func() []uint16 {
			a := []uint16{}
			for _, off := range []uint16{0x2b28, 0x2b2a, 0x2b2c, 0x2b2e, 0x2b30, 0x2b32, 0x2b34, 0x2b36, 0x46e, 0x478, 0x54a, 0x54c, 0x56c2, 0x56c4, 0x1e3a, 0x1e3c, 0x1e2a, 0x1e2c, 0x1e2e} {
				a = append(a, word(off))
			}
			return a
		}
		before := fields()
		diagnostics := []map[string]any{}
		for _, site := range []oracle.Addr{{Seg: load, Off: 0x6720}, {Seg: load, Off: 0x3d74}, {Seg: load + 0x13c2, Off: 0xc86}} {
			q.OnCall(site, func(q *oracle.Oracle) {
				if len(diagnostics) < 40 {
					diagnostics = append(diagnostics, map[string]any{"ip": q.IP(), "step": q.Steps(), "regs": q.Regs(), "lastkey": word(0x8bca)})
				}
			})
		}
		q.OnCall(oracle.Addr{Seg: load, Off: 0x67ac}, func(q *oracle.Oracle) {
			r := q.Regs()
			node := int(q.Word(oracle.Addr{Seg: r.SS, Off: r.BP - 4}))
			if node != lastCursor {
				if node == spell {
					key(0x1c, "confirm original map spell")
				} else {
					key(0x50, "original cursor Down")
				}
				lastCursor = node
			}
		})
		q.OnCall(oracle.Addr{Seg: load, Off: 0x68ce}, func(q *oracle.Oracle) {
			if started {
				return
			}
			started = true
			must(q.SaveStateFile(filepath.Join(dir, "entry.state")))
			r := q.Regs()
			ret := oracle.Addr{Seg: q.Word(oracle.Addr{Seg: r.SS, Off: r.SP + 2}), Off: q.Word(oracle.Addr{Seg: r.SS, Off: r.SP})}
			ss, sp := r.SS, r.SP+4
			events = append(events, map[string]any{"name": "dispatch", "step": q.Steps(), "cycles": q.Cycles(), "registers": r, "arg": q.Arg(0), "fields": fields()})
			q.OnCall(ret, func(q *oracle.Oracle) {
				r := q.Regs()
				if r.SS == ss && r.SP == sp {
					done = true
					events = append(events, map[string]any{"name": "return", "step": q.Steps(), "fields": fields()})
				}
			})
		})
		q.OnCall(oracle.Addr{Seg: load, Off: 0x844c}, func(q *oracle.Oracle) {
			if started && !done {
				key(0x1c, "dismiss original Enter/Esc-only prompt")
			}
		})
		q.OnCall(oracle.Addr{Seg: load + 0x13c2, Off: 0xc86}, func(q *oracle.Oracle) {
			if !started || done || len(keys) > 60 {
				return
			}
			if spell == 0 {
				key(0x4d, "original bridge Right at read")
			} else if spell == 7 {
				key(0x1c, "original teleport confirm at read")
			} else {
				key(0x39, "original dismiss at read")
			}
		})
		birdKey := false
		q.OnCall(oracle.Addr{Seg: load, Off: 0x827f}, func(q *oracle.Oracle) {
			if started && !done && !birdKey {
				key(0x1c, "bird-view original key availability")
				birdKey = true
			}
		})
		key(0x3e, "F4 original map magic menu")
		start := q.Steps()
		limit := uint64(60000000)
		if spell == 5 {
			limit = 400000000
		}
		for !done && q.Steps()-start < limit {
			must(q.Run(10000))
		}
		must(q.SaveStateFile(filepath.Join(dir, "final.state")))
		b, e := os.ReadFile(filepath.Join(dir, "final.state"))
		must(e)
		save(filepath.Join(dir, "receipt.json"), map[string]any{"diagnostics": diagnostics, "final_regs": q.Regs(), "load": load, "spell": spell, "started": started, "done": done, "keys": keys, "mutations": mutations, "before": before, "after": fields(), "events": events, "steps": q.Steps(), "final_sha256": fmt.Sprintf("%x", sha256.Sum256(b)), "limits": "Original F4 and cursor; learned/charges fixture. No selection/RNG/effect writes."})
		fmt.Println("map", spell, "started", started, "done", done, "keys", len(keys))
		q.Close()
		if !done {
			panic("bounded map spell incomplete")
		}
	}
}
