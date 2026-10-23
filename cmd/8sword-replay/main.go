package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"image/png"
	"os"
	"path/filepath"
	"sort"

	"github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

type action struct {
	Step uint64
	Scan uint8
	Down bool
}

func check(err error) {
	if err != nil {
		panic(err)
	}
}
func main() {
	root := flag.String("root", "", "read-only original game root")
	assets := flag.String("assets", "", "prepared HD assets")
	out := flag.String("out", "", "new receipt directory")
	hd := flag.Bool("hd", true, "enable the production Noto compositor")
	until := flag.Uint64("until", 250000000, "absolute final instruction")
	frameEvery := flag.Uint64("frame-every", 1000000, "continuous compositor sampling interval")
	flag.Parse()
	check(os.MkdirAll(*out, 0755))
	engine, err := eightsword.Open(eightsword.Options{Root: *root, Assets: *assets, Saves: filepath.Join(*out, "scratch"), HD: *hd})
	check(err)
	defer engine.Close()
	if engine.AssetError != "" {
		fmt.Fprintln(os.Stderr, "HD fallback:", engine.AssetError)
	}
	acts := []action{{1000000, 2, true}, {1500000, 2, false}, {3000000, 2, true}, {3500000, 2, false}}
	for _, a := range []struct {
		step uint64
		scan uint8
	}{{126000000, 0x50}, {127000000, 0x1c}, {151000000, 0x1c}, {181000000, 0x3b}, {191000000, 0x01}, {201000000, 0x41}, {211000000, 0x01}, {221000000, 0x4d}, {231000000, 0x3b}, {241000000, 0x01}} {
		acts = append(acts, action{a.step, a.scan, true}, action{a.step + 500000, a.scan, false})
	}
	sort.SliceStable(acts, func(i, j int) bool { return acts[i].Step < acts[j].Step })
	ai := 0
	nextFrame := *frameEvery
	frames := 0
	keep := map[uint64]bool{125000000: true, 150000000: true, 180000000: true, 190000000: true, 200000000: true, 210000000: true, 220000000: true, 230000000: true, 240000000: true, 250000000: true}
	for engine.Oracle.Steps() < *until && !engine.Exited {
		now := engine.Oracle.Steps()
		for ai < len(acts) && acts[ai].Step == now {
			check(engine.Key(acts[ai].Scan, acts[ai].Down))
			ai++
		}
		if now == nextFrame {
			im := engine.Frame()
			frames++
			if keep[now] {
				f, err := os.Create(filepath.Join(*out, fmt.Sprintf("frame-%d.png", now)))
				check(err)
				check(png.Encode(f, im))
				check(f.Close())
			}
			nextFrame += *frameEvery
		}
		target := now + 50000
		if target > *until {
			target = *until
		}
		if ai < len(acts) && acts[ai].Step < target {
			target = acts[ai].Step
		}
		if nextFrame < target {
			target = nextFrame
		}
		if target == now {
			panic("replay did not advance")
		}
		check(engine.Advance(target - now))
	}
	im := engine.Frame()
	f, err := os.Create(filepath.Join(*out, "final.png"))
	check(err)
	check(png.Encode(f, im))
	check(f.Close())
	check(engine.Oracle.SaveStateFile(filepath.Join(*out, "final.state")))
	report := engine.Status()
	report["sampled_frames"] = frames
	report["normal_input_replay"] = true
	report["snapshot_loaded"] = false
	b, err := json.MarshalIndent(report, "", "  ")
	check(err)
	check(os.WriteFile(filepath.Join(*out, "receipt.json"), append(b, '\n'), 0644))
	fmt.Printf("steps=%d frames=%d hd=%v\n", engine.Oracle.Steps(), frames, engine.HD)
}
