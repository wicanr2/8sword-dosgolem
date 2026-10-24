//go:build ignore

// 017 正常冷啟動收據；沒有快照續跑、客體注入或直接進場。
package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"

	"github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

func mustMuseum(err error) {
	if err != nil {
		panic(err)
	}
}
func main() {
	root := flag.String("root", "", "original root")
	assets := flag.String("assets", "", "assets")
	out := flag.String("out", "", "new receipt")
	escape := flag.Int("escape-ms", 0, "ordinary Esc at fixed elapsed virtual ms")
	font := flag.String("font", "noto", "font ID")
	flag.Parse()
	if err := os.Mkdir(*out, 0755); err != nil {
		entries, readErr := os.ReadDir(*out)
		if !os.IsExist(err) || readErr != nil || len(entries) != 0 {
			panic("receipt output must be new or empty")
		}
	}
	e, err := eightsword.Open(eightsword.Options{Root: *root, Assets: *assets, Saves: filepath.Join(*out, "scratch"), HD: true})
	mustMuseum(err)
	defer e.Close()
	e.EnableLiveClock(3000)
	mustMuseum(e.SetFont(*font))
	rec, err := eightsword.NewFrameRecorder(filepath.Join(*out, "presentation.frames.gz"), 1920, 1200)
	mustMuseum(err)
	log, err := os.Create(filepath.Join(*out, "intro-draw.jsonl"))
	mustMuseum(err)
	defer log.Close()
	enc := json.NewEncoder(log)
	pcm, err := os.Create(filepath.Join(*out, "audio.pcm"))
	mustMuseum(err)
	defer pcm.Close()
	elapsed, pure, museumFrames := 0, 0, 0
	seen := map[string]bool{}
	var previous *image.RGBA
	frame := func() {
		before := filepath.Join(*out, "frame-before.state")
		after := filepath.Join(*out, "frame-after.state")
		mustMuseum(e.Oracle.SaveStateFile(before))
		a, err := os.ReadFile(before)
		mustMuseum(err)
		im := e.Frame()
		mustMuseum(e.Oracle.SaveStateFile(after))
		b, err := os.ReadFile(after)
		mustMuseum(err)
		if !bytes.Equal(a, b) {
			panic("Frame changed guest state")
		}
		pure++
		info := map[string]any{"variant": "off"}
		stage := ""
		if e.Museum != nil {
			info = e.Museum.Status()
			stage = e.Museum.FrameStage(im)
		}
		if stage != "" {
			museumFrames++
			if !seen[stage] {
				f, err := os.Create(filepath.Join(*out, "museum-"+stage+".png"))
				mustMuseum(err)
				mustMuseum(png.Encode(f, im))
				mustMuseum(f.Close())
				seen[stage] = true
			}
		}

		if im == previous {
			mustMuseum(rec.Repeat(e.Oracle.Steps()))
		} else {
			mustMuseum(rec.Write(im, e.Oracle.Steps()))
		}
		previous = im
		mustMuseum(enc.Encode(map[string]any{"draw": rec.Frames, "step": e.Oracle.Steps(), "elapsed_ms": elapsed, "serial": info["serial"], "museum": info, "museum_stage": stage, "stage": e.IntroFrameStage(im), "font_id": e.FontID()}))
	}
	advance := func(ms int) {
		for i := 0; i < ms; i += 10 {
			mustMuseum(e.AdvanceCycles(30000))
			mustMuseum(binary.Write(pcm, binary.LittleEndian, e.RenderAudio()))
			elapsed += 10
			if elapsed%50 == 0 {
				frame()
			}
		}
	}
	press := func(scan byte) {
		mustMuseum(e.Key(scan, true))
		advance(100)
		mustMuseum(e.Key(scan, false))
		advance(100)
	}
	advance(1000)
	press(2)
	press(2)
	if *escape > 0 {
		if *escape < elapsed || *escape%10 != 0 {
			panic("invalid escape time")
		}
		advance(*escape - elapsed)
		press(1)
	}
	advance(21400 - elapsed)
	mustMuseum(rec.Close())
	mustMuseum(e.Oracle.SaveStateFile(filepath.Join(*out, "final.state")))
	status := e.Status()
	status["closed"] = true
	status["recorded_frames"] = rec.Frames
	status["frame_pure_count"] = pure
	status["museum_frames"] = museumFrames
	if e.Museum != nil {
		events, err := json.MarshalIndent(e.Museum.Events, "", "  ")
		mustMuseum(err)
		mustMuseum(os.WriteFile(filepath.Join(*out, "museum-transactions.json"), events, 0644))
	}
	status["elapsed_ms"] = elapsed
	b, err := json.MarshalIndent(status, "", "  ")
	mustMuseum(err)
	mustMuseum(os.WriteFile(filepath.Join(*out, "gui-final.json"), append(b, '\n'), 0644))
	fmt.Println("frames", rec.Frames, "pure", pure, "museum frames", museumFrames, "load error", e.MuseumError)
}
