//go:build ignore

// 030 DRAFT: ordinary recruitment and explicitly isolated native helper calls.
package main

import (
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"image/png"
	"os"
	"path/filepath"
	"runtime"

	"github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

func must(err error) {
	if err != nil {
		panic(err)
	}
}
func save(path string, value any) {
	b, err := json.MarshalIndent(value, "", "  ")
	must(err)
	must(os.WriteFile(path, append(b, '\n'), 0644))
}
func main() {
	root := flag.String("root", "", "read-only original")
	assets := flag.String("assets", "", "read-only current assets")
	out := flag.String("out", "", "new output directory")
	saveCycle := flag.Bool("save-cycle", false, "ordinary F7 save and fresh-engine continue")
	flag.Parse()
	if *out == "" || os.Getuid() != 1000 {
		panic("explicit paths and UID1000 required")
	}
	if _, err := os.Stat(*out); !os.IsNotExist(err) {
		panic("output exists")
	}
	must(os.Mkdir(*out, 0755))
	e, err := eightsword.Open(eightsword.Options{Root: *root, Assets: *assets, Saves: filepath.Join(*out, "scratch"), HD: true})
	must(err)
	defer e.Close()
	e.Oracle.SetClock(12, 0, 0, 0)
	e.EnableLiveClock(3000)
	advance := func(ms int) {
		for n := 0; n < ms; n += 10 {
			must(e.AdvanceCycles(30000))
			e.RenderAudio()
			if e.Exited {
				panic("unexpected exit")
			}
			if n%100 == 0 {
				e.Frame()
			}
		}
	}
	press := func(scan byte) {
		must(e.Key(scan, true))
		advance(100)
		must(e.Key(scan, false))
		advance(200)
	}
	advance(200)
	press(2)
	press(2)
	advance(500)
	if !e.PAMLoaded {
		press(1)
	}
	for n := 0; n < 300 && e.Tracker.VisibleScene != "main-menu"; n++ {
		advance(100)
	}
	if e.Tracker.VisibleScene != "main-menu" {
		panic("ordinary main menu not reached")
	}
	press(0x1c)
	advance(500)
	press(0x1c)
	advance(3000)
	if e.Tracker.VisibleScene != "map" {
		panic("ordinary new game not reached")
	}
	var records []map[string]any
	var ds uint16
	var helperState *oracle.State
	readArmy := func() []uint16 {
		v := make([]uint16, 12)
		for i := range v {
			v[i] = e.Oracle.Word(oracle.Addr{Seg: ds, Off: 0x54a + uint16(i*2)})
		}
		return v
	}
	var before, after map[string]any
	for _, ip := range []uint16{0x54ea, 0x4e7e, 0x5683, 0x56ec, 0x576b} {
		ip := ip
		e.Oracle.OnCall(oracle.Addr{Seg: 0x110, Off: ip}, func(o *oracle.Oracle) {
			c := o.Regs()
			ds = c.DS
			v := map[string]any{"ip": ip, "step": o.Steps(), "registers": c, "runtime_bytes": fmt.Sprintf("%x", o.Bytes(oracle.Addr{Seg: c.CS, Off: ip}, 16)), "army": readArmy(), "gold": o.Word(oracle.Addr{Seg: ds, Off: 0x4f8}), "leadership": o.Word(oracle.Addr{Seg: ds, Off: 0x4fa})}
			if ip == 0x54ea {
				kind := o.Word(oracle.Addr{Seg: c.SS, Off: c.SP + 4})
				stock := o.Word(oracle.Addr{Seg: c.SS, Off: c.SP + 6})
				v["kind"] = kind
				v["stock"] = stock
				v["unit_price"] = o.Word(oracle.Addr{Seg: ds, Off: 0x2986 + kind*2})
			}
			if ip == 0x56ec {
				before = v
				must(o.SaveStateFile(filepath.Join(*out, "before-commit.state")))
			}
			if ip == 0x576b {
				after = v
				helperState = o.Save()
				must(o.SaveStateFile(filepath.Join(*out, "after-commit.state")))
			}
			records = append(records, v)
		})
	}
	for _, scan := range []byte{0x4b, 0x48} {
		press(scan)
		advance(500)
		press(0x3b)
		advance(400)
		press(1)
		advance(400)
	}
	press(0x48)
	advance(1000)
	if len(records) == 0 {
		panic("ordinary recruitment was not reached")
	}
	press(2)
	press(11)
	press(14)
	press(0x1c)
	advance(1500)
	if before == nil || after == nil || helperState == nil {
		save(filepath.Join(*out, "incomplete.json"), records)
		panic("recruitment commit not observed")
	}
	var saveResult map[string]any
	if *saveCycle {
		press(0x41)
		advance(500)
		if e.Tracker.VisibleScene != "system-menu" {
			panic("ordinary F7 menu missing")
		}
		press(0x1c)
		advance(500)
		press(0x1c)
		advance(1500)
		if e.Tracker.VisibleScene != "map" {
			panic("ordinary F7 save did not return to map")
		}
		path := filepath.Join(*out, "scratch/gamedata.ay")
		raw, err := os.ReadFile(path)
		must(err)
		if len(raw) != 2987 {
			panic("original save length")
		}
		must(os.WriteFile(filepath.Join(*out, "saved-gamedata.ay"), raw, 0600))
		reload, err := eightsword.Open(eightsword.Options{Root: *root, Assets: *assets, Saves: filepath.Join(*out, "scratch"), HD: true})
		must(err)
		defer reload.Close()
		reload.Oracle.SetClock(12, 0, 0, 0)
		reload.EnableLiveClock(3000)
		run := func(ms int) {
			for n := 0; n < ms; n += 10 {
				must(reload.AdvanceCycles(30000))
				reload.RenderAudio()
				if n%100 == 0 {
					reload.Frame()
				}
			}
		}
		key := func(scan byte) { must(reload.Key(scan, true)); run(100); must(reload.Key(scan, false)); run(200) }
		run(200)
		key(2)
		key(2)
		run(500)
		if !reload.PAMLoaded {
			key(1)
		}
		for i := 0; i < 300 && reload.Tracker.VisibleScene != "main-menu"; i++ {
			run(100)
		}
		if reload.Tracker.VisibleScene != "main-menu" {
			panic("fresh-engine menu missing")
		}
		key(0x1c)
		run(3000)
		if reload.Tracker.VisibleScene != "map" {
			panic("fresh-engine continue failed")
		}
		army := make([]uint16, 12)
		for i := range army {
			army[i] = reload.Oracle.Word(oracle.Addr{Seg: ds, Off: 0x54a + uint16(i*2)})
		}
		gold := reload.Oracle.Word(oracle.Addr{Seg: ds, Off: 0x4f8})
		if fmt.Sprint(army) != fmt.Sprint(readArmy()) || gold != e.Oracle.Word(oracle.Addr{Seg: ds, Off: 0x4f8}) {
			panic("fresh-engine army or gold differs")
		}
		buffer := reload.Oracle.Bytes(oracle.Phys(0x9e000), 2987)
		if content := fmt.Sprintf("%x", sha256.Sum256(buffer)); content != fmt.Sprintf("%x", sha256.Sum256(raw)) {
			panic("actual read buffer differs from save")
		}
		saveResult = map[string]any{"original_bytes": 2987, "original_sha256": fmt.Sprintf("%x", sha256.Sum256(raw)), "army": army, "gold": gold, "fresh_engine": true, "snapshot_loaded": false, "buffer_equal": true}
		save(filepath.Join(*out, "reload-engine.json"), reload.Status())
		must(reload.Oracle.SaveStateFile(filepath.Join(*out, "reload.state")))
	}
	final := e.Oracle.Save()
	normalData := readArmy()
	var cases []map[string]any
	for kind := uint16(1); kind <= 25; kind++ {
		for _, scenario := range []string{"empty", "matching-full", "different-full"} {
			e.Oracle.Restore(helperState)
			army := make([]uint16, 12)
			for slot := 0; slot < 6; slot++ {
				if scenario != "empty" {
					army[slot*2] = uint16(slot + 1)
					army[slot*2+1] = uint16(slot + 2)
				}
			}
			if scenario == "matching-full" {
				army[4] = kind
			}
			if scenario == "different-full" {
				for i := 0; i < 6; i++ {
					if army[i*2] == kind {
						army[i*2] = 25
						if kind == 25 {
							army[i*2] = 24
						}
					}
				}
			}
			for i, v := range army {
				e.Oracle.WriteU16(oracle.Addr{Seg: ds, Off: 0x54a + uint16(i*2)}, v)
			}
			weight, err := e.Oracle.Call(oracle.Addr{Seg: 0x110, Off: 0x593c}, kind)
			must(err)
			capacity, err := e.Oracle.Call(oracle.Addr{Seg: 0x110, Off: 0x5962}, kind)
			must(err)
			used, err := e.Oracle.Call(oracle.Addr{Seg: 0x110, Off: 0x58f0})
			must(err)
			cases = append(cases, map[string]any{"kind": kind, "scenario": scenario, "army": army, "leadership_per_unit": uint16(weight), "capacity": uint16(capacity), "used_leadership": uint16(used), "isolated_calls": true})
		}
	}
	e.Oracle.Restore(final)
	if fmt.Sprint(readArmy()) != fmt.Sprint(normalData) {
		panic("helper fixture leaked into normal state")
	}
	pam, err := os.ReadFile(filepath.Join(*root, "PAM.AY"))
	must(err)
	save(filepath.Join(*out, "receipt.json"), map[string]any{"schema": 1, "status": "passed-normal-recruitment-and-isolated-helpers", "normal_inputs": true, "normal_ram_injection": false, "normal_snapshot_loaded": false, "helper_cases": cases, "normal_records": records, "before": before, "after": after, "native_save_cycle": saveResult, "go_version": runtime.Version(), "source_sha256": fmt.Sprintf("%x", sha256.Sum256(pam)), "limits": []string{"Helpers use explicit original snapshot and RAM fixtures; not a new unit gameplay claim.", "Only the ordinary one-unit purchase is a normal recruitment transaction.", "Original cold save/reload is recorded only when native_save_cycle is non-null; no new unit GUI claim."}})
	f, err := os.Create(filepath.Join(*out, "normal-frame.png"))
	must(err)
	must(png.Encode(f, e.Frame()))
	must(f.Close())
	save(filepath.Join(*out, "final-engine.json"), e.Status())
	fmt.Println("Passed ordinary recruitment and", len(cases), "isolated helper cases")
}
