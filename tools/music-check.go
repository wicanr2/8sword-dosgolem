//go:build ignore

// Spec 008: deterministic cold boot and ordinary music/menu keys only.
package main

import (
	"encoding/binary"
	"encoding/json"
	"flag"
	"image/png"
	"os"
	"path/filepath"
	"runtime"

	"github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

func check(err error) {
	if err != nil {
		panic(err)
	}
}
func save(path string, value any) {
	b, err := json.MarshalIndent(value, "", "  ")
	check(err)
	check(os.WriteFile(path, append(b, '\n'), 0644))
}
func main() {
	root := flag.String("root", "", "read-only original game root")
	assets := flag.String("assets", "", "prepared image/font/music asset directory")
	out := flag.String("out", "", "new receipt directory")
	firstMS := flag.Int("first-ms", 90000, "first music-appreciation playback, virtual milliseconds")
	flag.Parse()
	if *root == "" || *assets == "" || *out == "" || *firstMS < 2000 || *firstMS > 180000 || *firstMS%10 != 0 {
		panic("invalid music-check arguments")
	}
	check(os.MkdirAll(*out, 0755))
	contents, err := os.ReadDir(*out)
	check(err)
	if len(contents) != 0 {
		panic("music-check output is not empty")
	}
	e, err := eightsword.Open(eightsword.Options{Root: *root, Assets: *assets, Saves: filepath.Join(*out, "scratch"), HD: true})
	check(err)
	defer e.Close()
	if e.AssetError != "" {
		panic(e.AssetError)
	}
	e.EnableLiveClock(3000)
	pcm, err := os.Create(filepath.Join(*out, "output-s16le-stereo.pcm"))
	check(err)
	defer pcm.Close()
	advance := func(ms int) {
		for ; ms > 0; ms -= 10 {
			check(e.AdvanceCycles(30000))
			check(binary.Write(pcm, binary.LittleEndian, e.RenderAudio()))
		}
	}
	press := func(scan uint8) { check(e.Key(scan, true)); advance(100); check(e.Key(scan, false)); advance(150) }
	shot := func(name string) {
		f, er := os.Create(filepath.Join(*out, name+".png"))
		check(er)
		check(png.Encode(f, e.Frame()))
		check(f.Close())
	}
	advance(200)
	press(2)
	press(2)
	advance(500)
	press(1)
	for i := 0; i < 300; i++ {
		advance(100)
		e.Frame()
		if e.PAMLoaded && e.Tracker.Scene == "main-menu" {
			break
		}
	}
	if !e.PAMLoaded || e.Tracker.Scene != "main-menu" {
		panic("cold boot did not reach main-menu")
	}
	var rows []map[string]any
	act := func(name string, scan uint8, wait int) {
		before := len(e.Oracle.FileOps())
		press(scan)
		advance(wait)
		shot(name)
		rows = append(rows, map[string]any{"action": name, "step": e.Oracle.Steps(), "cycles": e.Oracle.Cycles(), "scene": e.Tracker.Scene, "opened": e.Oracle.FileOps()[before:]})
		save(filepath.Join(*out, name+".json"), e.Status())
	}
	press(0x50)
	press(0x50)
	act("01-music-menu", 0x1c, 500)
	act("02-first-play", 0x1c, *firstMS)
	act("03-same-enter", 0x1c, 2000)
	act("04-highlight-second", 0x50, 2000)
	act("05-second-play", 0x1c, 2000)
	act("06-second-enter", 0x1c, 2000)
	act("07-exit-music", 1, 1000)
	press(0x50)
	act("08-new-game-confirm", 0x1c, 500)
	act("09-map", 0x1c, 3000)
	act("10-character", 0x3b, 1000)
	act("11-return", 1, 1000)
	act("12-save", 0x41, 1000)
	act("13-leave-save", 1, 1000)
	save(filepath.Join(*out, "catalog.json"), map[string]any{"normal_input_replay": true, "snapshot_loaded": false, "cycles_per_ms": 3000, "sample_rate": 48000, "channels": 2, "first_ms": *firstMS, "go_version": runtime.Version(), "entries": rows, "scope": "music appreciation, new game, F1 and F7; F7 canceled, no save/load claim"})
	save(filepath.Join(*out, "final-receipt.json"), e.Status())
	check(e.Oracle.SaveStateFile(filepath.Join(*out, "final.state")))
}
