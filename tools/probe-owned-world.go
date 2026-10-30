//go:build ignore

// 030 DRAFT: normal world/battle boundaries, followed by explicit reward fixtures.
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
func write(path string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	must(e)
	must(os.WriteFile(path, append(b, '\n'), 0600))
}
func main() {
	root := flag.String("root", "", "read-only original")
	assets := flag.String("assets", "", "read-only assets")
	out := flag.String("out", "", "new output")
	observed := flag.Bool("observe", false, "read-only boundary capture")
	fixtures := flag.Bool("fixtures", false, "explicit original reward fixtures after normal path")
	flag.Parse()
	if os.Getuid() != 1000 || *root == "" || *out == "" {
		panic("explicit paths and UID1000")
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
	ds := uint16(0x1e88)
	events := []map[string]any{}
	keys := []map[string]any{}
	defer func() {
		write(filepath.Join(*out, "diagnostic-events.json"), events)
		write(filepath.Join(*out, "diagnostic-keys.json"), keys)
	}()
	word := func(off uint16) uint16 { return e.Oracle.Word(oracle.Addr{Seg: ds, Off: off}) }
	words := func(off uint16, n int) []uint16 {
		v := make([]uint16, n)
		for i := range v {
			v[i] = word(off + uint16(i*2))
		}
		return v
	}
	capture := func(name string) map[string]any {
		r := e.Oracle.Regs()
		return map[string]any{"name": name, "step": e.Oracle.Steps(), "registers": r, "progress_04f2": words(0x4f2, 6), "army_054a": words(0x54a, 12), "battle_56e8": words(0x56e8, 24), "reward_8e84": word(0x8e84), "reward_far_segment": word(0x8362), "rank_thresholds_05b2": words(0x5b2, 7), "stack": e.Oracle.Bytes(oracle.Addr{Seg: r.SS, Off: r.SP}, 16)}
	}
	if *observed {
		points := map[uint16]string{0x32e0: "world-battle-entry", 0x3365: "army-copy-before", 0x3396: "army-copy-after", 0x3733: "battle-call-before", 0x373b: "battle-return", 0x3745: "compact-after", 0x376a: "army-writeback-after", 0x1796: "world-reward-entry", 0x1892: "merit-add-before", 0x18a5: "gold-add-before", 0x19cc: "promotion-gate", 0x1ab8: "world-reward-return", 0x172b: "world-reward-caller-after", 0x309e: "guarded-encounter-return"}
		for ip, name := range points {
			ip, name := ip, name
			e.Oracle.OnCall(oracle.Addr{Seg: 0x110, Off: ip}, func(o *oracle.Oracle) {
				if len(events) > 200 {
					panic("boundary limit")
				}
				v := capture(name)
				events = append(events, v)
				if name == "battle-call-before" || name == "battle-return" || name == "army-writeback-after" || name == "world-reward-caller-after" {
					must(o.SaveStateFile(filepath.Join(*out, fmt.Sprintf("%02d-%s.state", len(events), name))))
				}
			})
		}
	}
	advance := func(ms int) {
		for n := 0; n < ms; n += 10 {
			must(e.AdvanceCycles(30000))
			e.RenderAudio()
			if n%100 == 0 {
				e.Frame()
			}
			if e.Exited {
				panic("unexpected exit")
			}
		}
	}
	press := func(scan byte) {
		keys = append(keys, map[string]any{"step": e.Oracle.Steps(), "scan": scan})
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
		panic("menu absent")
	}
	press(0x1c)
	advance(500)
	press(0x1c)
	advance(3000)
	if e.Tracker.VisibleScene != "map" {
		panic("map absent")
	}
	for n := 0; n < 128 && e.Tracker.VisibleScene != "encounter-confirm"; n++ {
		scan := byte(0x4d)
		if n%2 == 1 {
			scan = 0x4b
		}
		press(scan)
		advance(300)
	}
	if e.Tracker.VisibleScene != "encounter-confirm" {
		write(filepath.Join(*out, "incomplete.json"), e.Status())
		panic("encounter absent")
	}
	// The original confirmation defaults to No; inspect its current selection.
	press(0x4b)
	press(0x1c)
	advance(2000)
	// Original escape is a normal player action, with no enemy/RNG/result injection.
	for n := 0; n < 15 && e.Tracker.VisibleScene != "battle-result"; n++ {
		press(1)
		advance(1000)
	}
	if e.Tracker.VisibleScene != "battle-result" {
		write(filepath.Join(*out, "incomplete.json"), e.Status())
		panic("battle result absent")
	}
	result := capture("normal-result")
	f, err := os.Create(filepath.Join(*out, "normal-result.png"))
	must(err)
	must(png.Encode(f, e.Frame()))
	must(f.Close())
	press(0x1c)
	advance(1000)
	if e.Tracker.VisibleScene != "map" {
		write(filepath.Join(*out, "incomplete.json"), e.Status())
		panic("map return absent")
	}
	normal := capture("normal-world-return")
	must(e.Oracle.SaveStateFile(filepath.Join(*out, "normal-final.state")))
	raw, err := os.ReadFile(filepath.Join(*out, "normal-final.state"))
	must(err)
	normalSave := e.Oracle.Save()
	fixtureRows := []map[string]any{}
	if *fixtures {
		e.Oracle.OnCall(oracle.Addr{Seg: 0x110, Off: 0x844c}, func(o *oracle.Oracle) { must(o.SendKeys("Return")) })
		var lastInput uint64
		e.Oracle.OnCall(oracle.Addr{Seg: 0x160a, Off: 0x87}, func(o *oracle.Oracle) {
			if o.Steps()-lastInput > 50000 {
				lastInput = o.Steps()
				o.KeyDown(0x1c)
				o.KeyUp(0x1c)
				must(o.SendKeys("Return"))
			}
		})
		// These are isolated original calls. Only their numeric effects are compared.
		for _, sc := range []struct {
			Name                string
			Rank, Merit, Reward uint16
		}{{"below", 1, 99, 0}, {"equal", 1, 100, 0}, {"above", 1, 100, 1}, {"single-promotion", 1, 10000, 1}, {"rank-cap", 5, 30000, 1}, {"gold-cap", 1, 99, 0}, {"bonus-cap", 1, 100, 1}} {
			e.Oracle.Restore(normalSave)
			set := func(off, v uint16) { e.Oracle.WriteU16(oracle.Addr{Seg: ds, Off: off}, v) }
			set(0x4f2, sc.Rank)
			set(0x4f4, sc.Merit)
			set(0x4f6, 100)
			set(0x4f8, 500)
			set(0x4fa, 300)
			set(0x4fc, 10)
			set(0x5b2+sc.Rank*2, 100)
			set(0x8e84, sc.Reward)
			if sc.Name == "gold-cap" {
				set(0x4f8, 29999)
			}
			if sc.Name == "bonus-cap" {
				set(0x4f6, 29999)
				set(0x4fa, 29999)
				set(0x4fc, 29999)
			}
			// seg_35AE2 points to the separate original reward word at offset 0x003e.
			// The actual segment operand is read from the relocated instruction.
			operand := e.Oracle.Word(oracle.Addr{Seg: 0x110, Off: 0x189f})
			seg := word(operand)
			e.Oracle.WriteU16(oracle.Addr{Seg: seg, Off: 0x3e}, 7)
			before := capture(sc.Name + "-before")
			// Queue confirmations before the bounded helper; no guest result fields patched.
			for n := 0; n < 8; n++ {
				must(e.Oracle.SendKeys("Return"))
			}
			_, err = e.Oracle.CallBudget(12000000, oracle.Addr{Seg: 0x110, Off: 0x1796}, 0)
			fixtureRows = append(fixtureRows, map[string]any{"name": sc.Name, "before": before, "after": capture(sc.Name + "-after"), "reward_merit": sc.Reward, "reward_gold": 7, "error": fmt.Sprint(err)})
			if err != nil {
				write(filepath.Join(*out, "fixtures-incomplete.json"), fixtureRows)
				panic(err)
			}
		}
		e.Oracle.Restore(normalSave)
	}
	write(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-world-boundary-replay", "normal_inputs": true, "normal_ram_injection": false, "normal_snapshot_loaded": false, "normal_result": result, "normal_world": normal, "state_sha256": fmt.Sprintf("%x", sha256.Sum256(raw)), "events": events, "keys": keys, "fixtures": fixtureRows, "go_version": runtime.Version(), "observed": *observed, "limits": []string{"Escape is not a natural victory.", "Reward fixtures are direct calls, not normal-player outcomes.", "No extended army is submitted to DOS."}})
	fmt.Println("world boundary replay passed", len(events), "events", len(fixtureRows), "fixtures")
}
