//go:build ignore

// 030 DRAFT: controlled Go resource write in an otherwise ordinary original
// Continue -> F1 -> F7 -> cold Continue path; never submits expanded armies.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
	"image/png"
	"os"
	"path/filepath"
)

func nativeMust(e error) {
	if e != nil {
		panic(e)
	}
}
func nativeWrite(p string, v any) {
	raw, e := json.MarshalIndent(v, "", "  ")
	nativeMust(e)
	nativeMust(os.WriteFile(p, append(raw, '\n'), 0600))
}
func nativeCapture(e *game.Engine, dir, name string) {
	f, x := os.Create(filepath.Join(dir, name+".png"))
	nativeMust(x)
	nativeMust(png.Encode(f, e.Frame()))
	nativeMust(f.Close())
	nativeMust(e.Oracle.SaveStateFile(filepath.Join(dir, name+".state")))
}
func main() {
	root := flag.String("root", "", "read-only original")
	assets := flag.String("assets", "", "read-only HD assets")
	input := flag.String("input", "", "normal original save and map")
	target := flag.String("target", "", "Go world resource values")
	out := flag.String("out", "", "new output")
	apply := flag.Bool("apply", false, "explicit controlled Go write")
	flag.Parse()
	if os.Getuid() != 1000 || *out == "" {
		panic("UID1000 and paths required")
	}
	nativeMust(os.Mkdir(*out, 0755))
	program, e := os.ReadFile(filepath.Join(*root, "PAM.AY"))
	nativeMust(e)
	if nativeSHA(program) != nativeProgressSource {
		panic("unverified original source")
	}
	raw, e := os.ReadFile(filepath.Join(*input, "gamedata.ay"))
	nativeMust(e)
	before, e := decodeNativeResources(nativeProgressSource, raw)
	nativeMust(e)
	next := before
	if *apply {
		b, e := os.ReadFile(*target)
		nativeMust(e)
		nativeMust(json.Unmarshal(b, &next))
	}
	plan, e := planNativeResources(nativeProgressSource, raw, before, next)
	nativeMust(e)
	candidate, e := applyNativeResources(raw, plan)
	nativeMust(e)
	nativeMust(os.WriteFile(filepath.Join(*out, "go-candidate.ay"), candidate, 0600))
	saveDir := filepath.Join(*out, "scratch")
	nativeMust(os.Mkdir(saveDir, 0700))
	entries, e := os.ReadDir(*input)
	nativeMust(e)
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		b, e := os.ReadFile(filepath.Join(*input, entry.Name()))
		nativeMust(e)
		nativeMust(os.WriteFile(filepath.Join(saveDir, entry.Name()), b, 0600))
	}
	open := func() *game.Engine {
		e, x := game.Open(game.Options{Root: *root, Assets: *assets, Saves: saveDir, HD: true})
		nativeMust(x)
		e.Oracle.SetClock(12, 0, 0, 0)
		e.EnableLiveClock(3000)
		return e
	}
	var engine *game.Engine
	advance := func(ms int) {
		for n := 0; n < ms; n += 10 {
			nativeMust(engine.AdvanceCycles(30000))
			engine.RenderAudio()
			if n%100 == 0 {
				engine.Frame()
			}
		}
	}
	press := func(scan byte) {
		nativeMust(engine.Key(scan, true))
		advance(100)
		nativeMust(engine.Key(scan, false))
		advance(200)
	}
	boot := func() {
		advance(200)
		press(2)
		press(2)
		advance(500)
		if !engine.PAMLoaded {
			press(1)
		}
		for n := 0; n < 300 && engine.Tracker.VisibleScene != "main-menu"; n++ {
			advance(100)
		}
		if engine.Tracker.VisibleScene != "main-menu" {
			panic("no menu")
		}
		press(0x1c)
		advance(3000)
		if engine.Tracker.VisibleScene != "map" {
			panic("no continued map")
		}
	}
	resource := func() NativeResources {
		var n [6]uint64
		for i := range n {
			n[i] = uint64(engine.Oracle.Word(oracle.Addr{Seg: 0x1e88, Off: 0x4f2 + uint16(i*2)}))
		}
		return NativeResources{n[0], n[1], n[2], n[3], n[4], n[5]}
	}
	engine = open()
	defer func() {
		if engine != nil {
			engine.Close()
		}
	}()
	boot()
	if resource() != before {
		panic("native decoder differs from Go")
	}
	nativeCapture(engine, *out, "before-map")
	army := engine.Oracle.Bytes(oracle.Addr{Seg: 0x1e88, Off: 0x54a}, 24)
	if *apply {
		for i, n := range next.words() {
			engine.Oracle.WriteU16(oracle.Addr{Seg: 0x1e88, Off: 0x4f2 + uint16(i*2)}, uint16(n))
		}
	}
	if resource() != next {
		panic("Go memory write failed")
	}
	nativeMust(os.WriteFile(filepath.Join(*out, "native-army-before.bin"), army, 0600))
	nativeMust(os.WriteFile(filepath.Join(*out, "native-army-after.bin"), engine.Oracle.Bytes(oracle.Addr{Seg: 0x1e88, Off: 0x54a}, 24), 0600))
	press(0x3b)
	advance(500)
	if engine.Tracker.VisibleScene != "character" {
		nativeWrite(filepath.Join(*out, "character-status.json"), engine.Status())
	}
	nativeCapture(engine, *out, "character")
	press(1)
	advance(500)
	press(0x41)
	advance(500)
	if engine.Tracker.VisibleScene != "system-menu" {
		panic("no F7 menu")
	}
	press(0x1c)
	advance(500)
	press(0x1c)
	advance(1500)
	if engine.Tracker.VisibleScene != "map" {
		panic("save did not return to map")
	}
	saved, e := os.ReadFile(filepath.Join(saveDir, "gamedata.ay"))
	nativeMust(e)
	if len(saved) != 2987 {
		panic("native write size")
	}
	for i := 0; i < 12; i++ {
		if saved[i] != candidate[i] {
			panic("Go/native encoder prefix differs")
		}
	}
	nativeMust(os.WriteFile(filepath.Join(*out, "native-saved.ay"), saved, 0600))
	nativeCapture(engine, *out, "saved-map")
	engine.Close()
	engine = nil
	engine = open()
	boot()
	if resource() != next {
		panic("cold original resource mismatch")
	}
	nativeCapture(engine, *out, "cold-map")
	press(0x3b)
	advance(500)
	nativeCapture(engine, *out, "cold-character")
	nativeWrite(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-native-resource-transport", "controlled_resource_write": *apply, "before": before, "after": next, "plan": plan, "source_sha256": nativeProgressSource, "base_save_sha256": nativeSHA(raw), "saved_sha256": nativeSHA(saved), "cold_resources": resource(), "original_size": 2987, "guest_army_modified": false, "normal_extended_army_path": false, "native_prefix_equals_go": true, "snapshot_loaded": false, "cold_engine": true, "limits": []string{"Resource-only controlled transport; original army IDs/counts remain untouched.", "No expanded army sidecar is loaded or silently discarded; formal guard is unchanged.", "Not a completed world-map or expanded-army handoff."}})
	fmt.Println("Native F7 and cold Continue resource transport passed", *apply)
}
