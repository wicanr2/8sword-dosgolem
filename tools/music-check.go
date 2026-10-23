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
	introMS := flag.Int("intro-ms", 500, "normal intro wait before Esc, virtual milliseconds")
	flag.Parse()
	if *root == "" || *assets == "" || *out == "" || *firstMS < 2000 || *firstMS > 180000 || *firstMS%10 != 0 || *introMS < 500 || *introMS > 120000 || *introMS%10 != 0 {
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
			if e.Exited {
				save(filepath.Join(*out, "unexpected-exit.json"), e.Status())
				panic("original exited before the requested input path finished")
			}
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
	advance(*introMS)
	shot("intro-before-skip")
	save(filepath.Join(*out, "intro-before-skip.json"), e.Status())
	if !e.PAMLoaded {
		press(1)
	}
	for i := 0; i < 300; i++ {
		advance(100)
		e.Frame()
		if e.PAMLoaded && e.Tracker.VisibleScene == "main-menu" {
			break
		}
	}
	if e.Exited || !e.PAMLoaded || e.Tracker.VisibleScene != "main-menu" {
		panic("cold boot did not reach main-menu")
	}
	var rows []map[string]any
	act := func(name string, scan uint8, wait int) {
		before := len(e.Oracle.FileOps())
		beforeStep, beforeStarts := e.Oracle.Steps(), e.Music.Starts
		press(scan)
		advance(wait)
		shot(name)
		rows = append(rows, map[string]any{"action": name, "step": e.Oracle.Steps(), "cycles": e.Oracle.Cycles(), "scene": e.Tracker.Scene, "opened": e.Oracle.FileOps()[before:]})
		save(filepath.Join(*out, name+".json"), e.Status())
		wantScene, wantStart, wantText := "", 0, uint16(0)
		switch name {
		case "01-music-menu":
			wantText = 758
		case "02-first-play", "03-same-enter":
			wantStart = 1
		case "04-highlight-second":
			wantText = 778
			if e.Music.Starts != beforeStarts || e.Music.CurrentCue != 1 {
				panic("moving highlight restarted or changed the original music")
			}
		case "05-second-play", "06-second-enter":
			wantStart = 2
		case "07-exit-music":
			wantScene = "main-menu"
		case "08-new-game-confirm":
			wantScene = "new-game-confirm"
		case "09-map", "11-return", "13-leave-save":
			wantScene = "map"
		case "10-character":
			wantScene = "character"
		case "12-save":
			wantScene = "system-menu"
		}
		if wantScene != "" && e.Tracker.VisibleScene != wantScene {
			panic("normal action did not reach its visible page: " + name)
		}
		if wantStart != 0 {
			found := false
			for _, event := range e.Music.Events {
				found = found || (event.Step > beforeStep && event.Kind == "start" && event.Cue == wantStart && event.Valid && event.Reason == "")
			}
			if !found {
				panic("normal action did not start its original cue: " + name)
			}
		}
		if wantText != 0 {
			found := false
			for _, event := range e.Tracker.Strings {
				found = found || (event.Step > beforeStep && event.Source == wantText)
			}
			if !found {
				panic("normal action did not print its original selection: " + name)
			}
		}
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
	save(filepath.Join(*out, "catalog.json"), map[string]any{"normal_input_replay": true, "snapshot_loaded": false, "cycles_per_ms": 3000, "sample_rate": 48000, "channels": 2, "first_ms": *firstMS, "intro_ms": *introMS, "go_version": runtime.Version(), "entries": rows, "scope": "intro, music appreciation, new game, F1 and F7; F7 canceled, no save/load claim"})
	save(filepath.Join(*out, "final-receipt.json"), e.Status())
	check(e.Oracle.SaveStateFile(filepath.Join(*out, "final.state")))
}
