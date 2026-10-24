//go:build ignore

// 033 正常冷啟動收據；沒有快照續跑、客體注入或直接進場。
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

func mustHeroine(err error) {
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
	mustHeroine(err)
	defer e.Close()
	e.EnableLiveClock(3000)
	mustHeroine(e.SetFont(*font))
	rec, err := eightsword.NewFrameRecorder(filepath.Join(*out, "presentation.frames.gz"), 1920, 1200)
	mustHeroine(err)
	log, err := os.Create(filepath.Join(*out, "intro-draw.jsonl"))
	mustHeroine(err)
	defer log.Close()
	enc := json.NewEncoder(log)
	pcm, err := os.Create(filepath.Join(*out, "audio.pcm"))
	mustHeroine(err)
	defer pcm.Close()
	elapsed, pure, maxPixels := 0, 0, 0
	var previous *image.RGBA
	frame := func() {
		before := filepath.Join(*out, "frame-before.state")
		after := filepath.Join(*out, "frame-after.state")
		mustHeroine(e.Oracle.SaveStateFile(before))
		a, err := os.ReadFile(before)
		mustHeroine(err)
		im := e.Frame()
		mustHeroine(e.Oracle.SaveStateFile(after))
		b, err := os.ReadFile(after)
		mustHeroine(err)
		if !bytes.Equal(a, b) {
			panic("Frame changed guest state")
		}
		pure++
		pixels, serial := 0, any(uint64(0))
		if e.Heroine != nil {
			pixels = e.Heroine.FramePixels(im)
			serial = e.Heroine.Status()["serial"]
		}
		if pixels > maxPixels {
			maxPixels = pixels
			f, err := os.Create(filepath.Join(*out, "heroine.png"))
			mustHeroine(err)
			mustHeroine(png.Encode(f, im))
			mustHeroine(f.Close())
		}
		if im == previous {
			mustHeroine(rec.Repeat(e.Oracle.Steps()))
		} else {
			mustHeroine(rec.Write(im, e.Oracle.Steps()))
		}
		previous = im
		mustHeroine(enc.Encode(map[string]any{"draw": rec.Frames, "step": e.Oracle.Steps(), "elapsed_ms": elapsed, "serial": serial, "heroine_pixels": pixels, "stage": e.IntroFrameStage(im), "font_id": e.FontID()}))
	}
	advance := func(ms int) {
		for i := 0; i < ms; i += 10 {
			mustHeroine(e.AdvanceCycles(30000))
			mustHeroine(binary.Write(pcm, binary.LittleEndian, e.RenderAudio()))
			elapsed += 10
			if elapsed%50 == 0 {
				frame()
			}
		}
	}
	press := func(scan byte) {
		mustHeroine(e.Key(scan, true))
		advance(100)
		mustHeroine(e.Key(scan, false))
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
	mustHeroine(rec.Close())
	mustHeroine(e.Oracle.SaveStateFile(filepath.Join(*out, "final.state")))
	status := e.Status()
	status["closed"] = true
	status["recorded_frames"] = rec.Frames
	status["frame_pure_count"] = pure
	status["max_heroine_pixels"] = maxPixels
	status["elapsed_ms"] = elapsed
	b, err := json.MarshalIndent(status, "", "  ")
	mustHeroine(err)
	mustHeroine(os.WriteFile(filepath.Join(*out, "gui-final.json"), append(b, '\n'), 0644))
	fmt.Println("frames", rec.Frames, "pure", pure, "max heroine pixels", maxPixels, "load error", e.HeroineError)
}
