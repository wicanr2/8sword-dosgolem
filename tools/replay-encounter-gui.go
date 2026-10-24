//go:build ignore

// Replay recorded ordinary GUI inputs at their exact cycle boundaries.
// Docker only. No snapshot loading, guest memory writes or scene injection.
// Spec 039 records the fixed clock/update contract and verification limits.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"

	"github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

func must(err error) {
	if err != nil {
		panic(err)
	}
}
func main() {
	root := flag.String("root", "", "original root")
	assets := flag.String("assets", "", "assets")
	out := flag.String("out", "", "new output")
	witness := flag.String("gui-source", "", "recorded ordinary GUI state")
	trace := flag.Bool("trace-units", false, "read-only known ENEMY full/prefix capture")
	checkpoint := flag.String("checkpoint", "", "optional recorded GUI checkpoint after the encounter")
	complete := flag.Bool("complete", false, "after checkpoint, ordinary F1/F2 and F7 save/exit")
	capture := flag.Bool("capture-samples", false, "require research-only read-only layer capture")
	flag.Parse()
	must(os.Mkdir(*out, 0755))
	e, err := eightsword.Open(eightsword.Options{Root: *root, Assets: *assets, Saves: filepath.Join(*out, "scratch"), HD: true})
	must(err)
	defer e.Close()
	e.Oracle.SetClock(12, 0, 0, 0)
	e.EnableLiveClock(3000)

	installed := false
	known := map[string][]string{}
	source, err := os.ReadFile(filepath.Join(*root, "ENEMY.AY"))
	must(err)
	if fmt.Sprintf("%x", sha256.Sum256(source)) != "0d18b068e177b54f7b8a2b30072e9ae3ebc984fbed9fd6a8706f71d3140a5ffd" || len(source) != 16856 {
		panic("ENEMY source differs")
	}
	for record := 0; record < 14; record++ {
		raw := source[record*1204 : (record+1)*1204]
		if binary.LittleEndian.Uint16(raw) != 8 || binary.LittleEndian.Uint16(raw[2:]) != 25 {
			panic("record shape")
		}
		mirrored := append([]byte(nil), raw...)
		for row := 4; row < 1204; row += 8 {
			for x := 0; x < 8; x++ {
				v := raw[row+7-x]
				var r byte
				for bit := 0; bit < 8; bit++ {
					r = (r << 1) | (v & 1)
					v >>= 1
				}
				mirrored[row+x] = r
			}
		}
		for height := 1; height <= 25; height += 2 {
			prefix := make([]byte, 4+48*height)
			binary.LittleEndian.PutUint16(prefix, 8)
			binary.LittleEndian.PutUint16(prefix[2:], uint16(height))
			for plane := 0; plane < 6; plane++ {
				copy(prefix[4+plane*8*height:], mirrored[4+plane*200:4+plane*200+8*height])
			}
			h := fmt.Sprintf("%x", sha256.Sum256(prefix))
			known[h] = append(known[h], fmt.Sprintf("ENEMY.AY/%d/mirror/height-%02d", record, height))
		}
	}
	callsFile, err := os.Create(filepath.Join(*out, "encounter-calls.jsonl"))
	must(err)
	defer callsFile.Close()
	calls := json.NewEncoder(callsFile)
	totalCalls := 0
	captured := map[string]bool{}
	var pending map[string]any
	pendingCapture := ""
	var first uint32
	captureHeight := 0
	pixels := func(at uint32, height int) []byte {
		out := make([]byte, 64*height)
		for y := 0; y < height; y++ {
			for x := 0; x < 8; x++ {
				v, ok := e.Oracle.PlanarBytePixels(at + uint32(y*80+x))
				if !ok {
					panic("invalid planar read")
				}
				copy(out[y*64+x*8:], v[:])
			}
		}
		return out
	}
	install := func() {
		if installed || !*trace || e.Tracker.Stats.BoundLoadSegment == 0 {
			return
		}
		installed = true
		seg := e.Tracker.Stats.BoundLoadSegment + 0x13c2
		if !bytes.Equal(e.Oracle.Bytes(oracle.Addr{Seg: seg, Off: 0x4f2}, 308), e.PAM[0x15582:0x15582+308]) || e.Oracle.Byte(oracle.Addr{Seg: seg, Off: 0x625}) != 0xcb {
			panic("known normal source ABI differs")
		}
		e.Oracle.OnCall(oracle.Addr{Seg: seg, Off: 0x4f2}, func(o *oracle.Oracle) {
			if pending != nil {
				panic("encounter return missing")
			}
			ptr := oracle.Addr{Seg: o.Arg(1), Off: o.Arg(0)}
			if ptr.Linear() >= 0xa0000 || uint32(ptr.Off)+1204 > 65536 || ptr.Linear()+1204 > 0xa0000 {
				return
			}
			head := o.Bytes(ptr, 4)
			w, h := int(binary.LittleEndian.Uint16(head)), int(binary.LittleEndian.Uint16(head[2:]))
			if w != 8 || h < 1 || h > 25 || h%2 != 1 {
				return
			}
			raw := o.Bytes(ptr, 4+48*h)
			sha := fmt.Sprintf("%x", sha256.Sum256(raw))
			matches := known[sha]
			if len(matches) == 0 {
				return
			}
			totalCalls++
			if totalCalls > 256 {
				panic("source count bound")
			}
			ds := o.Regs().DS
			dest := o.Word(oracle.Addr{Seg: ds, Off: 0x748a})
			mode := o.Word(oracle.Addr{Seg: ds, Off: 0x7484})
			x, y := o.Arg(2), o.Arg(3)
			if (dest != 0xa000 && dest != 0xa400) || x > 72 || y+uint16(h) > 200 {
				panic(fmt.Sprintf("unexpected encounter geometry: dest=%04x mode=%d x=%d y=%d h=%d", dest, mode, x, y, h))
			}
			first = uint32(dest-0xa000)*16 + uint32(o.Word(oracle.Addr{Seg: seg, Off: 6 + y*2})) + uint32(x)
			for row := 0; row < h; row++ {
				if uint32(dest-0xa000)*16+uint32(o.Word(oracle.Addr{Seg: seg, Off: 6 + (y+uint16(row))*2}))+uint32(x) != first+uint32(row*80) {
					panic("row table differs")
				}
			}
			pending = map[string]any{"serial": totalCalls, "entry_step": o.Steps(), "segment": seg, "entry": 0x4f2, "return": 0x625, "source": ptr, "sha256": sha, "catalog": matches, "height": h, "width_bytes": w, "x_byte": x, "y": y, "first_physical_byte": first, "destination_segment": dest, "mode": mode}
			if !captured[sha] {
				captured[sha] = true
				pendingCapture = fmt.Sprintf("encounter-first-%02d-h%02d", totalCalls, h)
				captureHeight = h
				must(os.WriteFile(filepath.Join(*out, pendingCapture+"-source.bin"), raw, 0644))
				must(os.WriteFile(filepath.Join(*out, pendingCapture+"-before.idx"), pixels(first, h), 0644))
			}
		})
		e.Oracle.OnCall(oracle.Addr{Seg: seg, Off: 0x625}, func(o *oracle.Oracle) {
			if pending == nil {
				return
			}
			pending["return_step"] = o.Steps()
			if pendingCapture != "" {
				must(os.WriteFile(filepath.Join(*out, pendingCapture+"-after.idx"), pixels(first, captureHeight), 0644))
				b, err := json.MarshalIndent(pending, "", "  ")
				must(err)
				must(os.WriteFile(filepath.Join(*out, pendingCapture+"-call.json"), append(b, '\n'), 0644))
				pendingCapture = ""
			}
			must(calls.Encode(pending))
			pending = nil
		})
	}

	rawWitness, err := os.ReadFile(*witness)
	must(err)
	var recorded struct {
		InputEvents []eightsword.InputEvent `json:"input_events"`
		Updates     uint64                  `json:"updates"`
	}
	must(json.Unmarshal(rawWitness, &recorded))
	sourceWitness, err := os.ReadFile(filepath.Join(filepath.Dir(*witness), "research-encounter-sources.json"))
	must(err)
	var sourceCalls struct {
		Calls []struct {
			Records []int  `json:"records"`
			Height  int    `json:"height"`
			Return  uint64 `json:"return_step"`
		} `json:"calls"`
	}
	must(json.Unmarshal(sourceWitness, &sourceCalls))
	firstFull := uint64(0)
	for _, c := range sourceCalls.Calls {
		if len(c.Records) == 1 && c.Records[0] == 7 && c.Height == 25 {
			firstFull = c.Return
			break
		}
	}
	if firstFull == 0 || len(recorded.InputEvents) > 1024 {
		panic("bounded target witness missing")
	}
	stopStep := uint64(0)
	for _, event := range recorded.InputEvents {
		if event.Step > firstFull {
			stopStep = event.Step
			break
		}
	}
	if stopStep == 0 {
		panic("next ordinary input boundary missing")
	}
	firstBoundary := stopStep
	var expected map[string]json.RawMessage
	checkpointSHA := ""
	if *checkpoint != "" {
		raw, err := os.ReadFile(*checkpoint)
		must(err)
		must(json.Unmarshal(raw, &expected))
		must(json.Unmarshal(expected["steps"], &stopStep))
		checkpointSHA = fmt.Sprintf("%x", sha256.Sum256(raw))
		if stopStep < firstBoundary {
			panic("checkpoint precedes target")
		}
	}
	pcm, err := os.Create(filepath.Join(*out, "audio.pcm"))
	must(err)
	defer pcm.Close()
	frames, err := eightsword.NewFrameRecorder(filepath.Join(*out, "presentation.frames.gz"), 1920, 1200)
	must(err)
	e.Frame()
	at, updates := 0, 0
	writePNG := func(name string, im image.Image) {
		f, err := os.Create(filepath.Join(*out, name+".png"))
		must(err)
		must(png.Encode(f, im))
		must(f.Close())
	}
	sample := func(im *image.RGBA) {
		if !*capture {
			return
		}
		cap, ok := any(e).(interface {
			ResearchCaptureEncounterSample(string, *image.RGBA, uint64) error
		})
		if !ok {
			panic("research layer capture was not compiled")
		}
		must(cap.ResearchCaptureEncounterSample(filepath.Join(*out, "research-encounter-draws"), im, uint64(frames.Frames)))
	}
	frame := func() { im := e.Frame(); must(frames.Write(im, e.Oracle.Steps())); sample(im) }
	advance := func(count int) {
		for i := 0; i < count; i++ {
			install()
			must(e.AdvanceCycles(100000))
			must(binary.Write(pcm, binary.LittleEndian, e.RenderAudio()))
			frame()
			updates++
			if updates > 6000 {
				panic("GUI update replay bound")
			}
		}
	}
	encounterSampled := false
	for {
		current := e.Oracle.Steps()
		if current == firstBoundary && !encounterSampled {
			encounterSampled = true
			must(e.Oracle.SaveStateFile(filepath.Join(*out, "encounter-before.state")))
			for _, font := range []string{"noto", "lishu", "caoshu", "noto"} {
				must(e.SetFont(font))
				frame()
				if font != "noto" || len(e.InputEvents) > 0 {
					writePNG("encounter-"+font, e.Frame())
				}
			}
			must(e.Oracle.SaveStateFile(filepath.Join(*out, "encounter-after.state")))
		}
		if current >= stopStep {
			if current != stopStep {
				panic(fmt.Sprintf("stop boundary differs: got %d want %d", current, stopStep))
			}
			break
		}
		if at < len(recorded.InputEvents) && recorded.InputEvents[at].Step < current {
			panic(fmt.Sprintf("input boundary differs: got %d want %d", current, recorded.InputEvents[at].Step))
		}
		for at < len(recorded.InputEvents) && recorded.InputEvents[at].Step == current {
			event := recorded.InputEvents[at]
			must(e.Key(event.Scan, event.Down))
			at++
		}
		advance(1)
	}
	if *checkpoint != "" {
		status := e.Status()
		for _, key := range []string{"steps", "input_events", "file_ops", "exec_log", "strings", "visible_scene"} {
			a, err := json.Marshal(status[key])
			must(err)
			var want, got any
			must(json.Unmarshal(expected[key], &want))
			must(json.Unmarshal(a, &got))
			aa, _ := json.Marshal(want)
			bb, _ := json.Marshal(got)
			if !bytes.Equal(aa, bb) {
				panic("recorded GUI checkpoint differs: " + key)
			}
		}
	}
	recordedUpdates := updates
	if *complete {
		if e.Tracker.VisibleScene != "map" {
			panic("normal map checkpoint required for completion path")
		}
		press := func(scan byte, hold, gap int) {
			must(e.Key(scan, true))
			advance(hold)
			must(e.Key(scan, false))
			advance(gap)
		}
		press(0x3b, 3, 21)
		writePNG("character-after-encounter", e.Frame())
		if e.Tracker.VisibleScene != "character" {
			panic("F1 not reached")
		}
		press(0x01, 3, 9)
		press(0x3c, 3, 21)
		writePNG("army-after-encounter", e.Frame())
		press(0x01, 3, 9)
		writePNG("returned-map", e.Frame())
		press(0x41, 3, 15)
		press(0x1c, 3, 15)
		press(0x1c, 3, 15)
		writePNG("saved-map", e.Frame())
		press(0x41, 3, 15)
		press(0x4d, 3, 9)
		press(0x1c, 3, 9)
		press(0x1c, 3, 18)
		if !e.Exited || e.ExitCode != 0 {
			panic("normal DOS exit not reached")
		}
	}
	must(frames.Close())
	must(e.Oracle.SaveStateFile(filepath.Join(*out, "final-before.state")))
	im := e.Frame()
	must(e.Oracle.SaveStateFile(filepath.Join(*out, "final-after.state")))
	f, err := os.Create(filepath.Join(*out, "final-hd.png"))
	must(err)
	must(png.Encode(f, im))
	must(f.Close())
	width, height, rgb := e.Oracle.ScreenRGB()
	native := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	for y := 0; y < 1200; y++ {
		for x := 0; x < 1920; x++ {
			from := ((y*height/1200)*width + x*width/1920) * 3
			to := y*native.Stride + x*4
			copy(native.Pix[to:to+3], rgb[from:from+3])
			native.Pix[to+3] = 255
		}
	}
	f, err = os.Create(filepath.Join(*out, "final-native.png"))
	must(err)
	must(png.Encode(f, native))
	must(f.Close())
	status := e.Status()
	status["recorded_frames"] = frames.Frames
	status["replayed_updates"] = recordedUpdates
	status["total_update_calls"] = updates
	status["replayed_inputs"] = at
	status["normal_input_replay"] = true
	status["snapshot_loaded"] = false
	status["guest_memory_injection"] = false
	status["clock_baseline"] = "12:00:00.00 before execution; normal PIT progression; 3000 cycles/ms"
	status["update_cycles"] = 100000
	status["gui_witness_sha256"] = fmt.Sprintf("%x", sha256.Sum256(rawWitness))
	status["normal_source_calls"] = totalCalls
	status["checkpoint_sha256"] = checkpointSHA
	status["ordinary_completion_path"] = *complete
	status["recorded_boundary_before_extra_keys"] = stopStep
	status["source_witness_sha256"] = fmt.Sprintf("%x", sha256.Sum256(sourceWitness))
	status["internal_rng_seed"] = "unknown; this is a recorded normal-input replay, not RNG parity"
	if !*complete && *checkpoint == "" && e.Tracker.VisibleScene != "encounter-confirm" {
		panic("original encounter not reached")
	}
	data, err := json.MarshalIndent(status, "", "  ")
	must(err)
	must(os.WriteFile(filepath.Join(*out, "final.json"), append(data, '\n'), 0644))
	fmt.Printf("ran %d fixed-cycle updates, replayed %d GUI inputs; complete=%t, sources=%d, step=%d\n", updates, at, *complete, totalCalls, e.Oracle.Steps())
}
