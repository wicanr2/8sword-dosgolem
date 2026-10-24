//go:build ignore

// Normal cold boot, dense first-page handoff sampling, no guest injection.
package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"os"
	"path/filepath"

	"github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

func mustPrelude(err error) {
	if err != nil {
		panic(err)
	}
}
func main() {
	root := flag.String("root", "", "original root")
	assets := flag.String("assets", "", "assets")
	out := flag.String("out", "", "new output")
	escape := flag.Int("escape-ms", 0, "ordinary Esc at fixed virtual ms")
	font := flag.String("font", "noto", "font")
	flag.Parse()
	if err := os.Mkdir(*out, 0755); err != nil {
		entries, e := os.ReadDir(*out)
		if !os.IsExist(err) || e != nil || len(entries) != 0 {
			panic("output must be new or empty")
		}
	}
	e, err := eightsword.Open(eightsword.Options{Root: *root, Assets: *assets, Saves: filepath.Join(*out, "scratch"), HD: true})
	mustPrelude(err)
	defer e.Close()
	e.EnableLiveClock(3000)
	mustPrelude(e.SetFont(*font))
	frames, err := eightsword.NewFrameRecorder(filepath.Join(*out, "presentation.frames.gz"), 1920, 1200)
	mustPrelude(err)
	f, err := os.Create(filepath.Join(*out, "intro-draw.jsonl"))
	mustPrelude(err)
	defer f.Close()
	enc := json.NewEncoder(f)
	pcm, err := os.Create(filepath.Join(*out, "audio.pcm"))
	mustPrelude(err)
	defer pcm.Close()
	elapsed, pure := 0, 0
	var previous *image.RGBA
	frame := func() {
		before, after := filepath.Join(*out, "before.state"), filepath.Join(*out, "after.state")
		mustPrelude(e.Oracle.SaveStateFile(before))
		a, err := os.ReadFile(before)
		mustPrelude(err)
		im := e.Frame()
		mustPrelude(e.Oracle.SaveStateFile(after))
		b, err := os.ReadFile(after)
		mustPrelude(err)
		if !bytes.Equal(a, b) {
			panic("Frame changed guest")
		}
		pure++
		if im == previous {
			mustPrelude(frames.Repeat(e.Oracle.Steps()))
		} else {
			mustPrelude(frames.Write(im, e.Oracle.Steps()))
		}
		previous = im
		prelude := map[string]any{"loaded": false}
		var calls, pages uint64
		if e.Story != nil {
			prelude = e.Story.PreludeStatus()
			calls, pages = e.Story.FrameInfo(im)
		}
		if e.Oracle.VideoMode() == 0x13 {
			_, _, idx := e.Oracle.Screen()
			mustPrelude(os.WriteFile(filepath.Join(*out, fmt.Sprintf("native-%04d.idx", frames.Frames)), idx, 0644))
		}
		mustPrelude(enc.Encode(map[string]any{"draw": frames.Frames, "step": e.Oracle.Steps(), "elapsed_ms": elapsed, "stage": e.IntroFrameStage(im), "font_id": e.FontID(), "prelude": prelude, "story_calls": calls, "story_pages": pages}))
	}
	advance := func(ms int) {
		for i := 0; i < ms; i += 10 {
			mustPrelude(e.AdvanceCycles(30000))
			mustPrelude(binary.Write(pcm, binary.LittleEndian, e.RenderAudio()))
			elapsed += 10
			if elapsed%50 == 0 || (elapsed >= 17450 && elapsed <= 17550) {
				frame()
			}
		}
	}
	press := func(scan byte) {
		mustPrelude(e.Key(scan, true))
		advance(100)
		mustPrelude(e.Key(scan, false))
		advance(100)
	}
	advance(1000)
	press(2)
	press(2)
	if *escape > 0 {
		if *escape < elapsed || *escape%10 != 0 {
			panic("invalid Esc time")
		}
		advance(*escape - elapsed)
		press(1)
	}
	advance(27000 - elapsed)
	mustPrelude(frames.Close())
	mustPrelude(e.Oracle.SaveStateFile(filepath.Join(*out, "final.state")))
	status := e.Status()
	status["recorded_frames"], status["frame_pure_count"], status["elapsed_ms"] = frames.Frames, pure, elapsed
	data, err := json.MarshalIndent(status, "", "  ")
	mustPrelude(err)
	mustPrelude(os.WriteFile(filepath.Join(*out, "gui-final.json"), append(data, '\n'), 0644))
	fmt.Println("frames", frames.Frames, "pure", pure, "PAM", e.PAMLoaded, "story", status["intro_story"])
}
