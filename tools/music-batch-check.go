//go:build ignore

// Spec 008 research candidate: ordinary cold boot and all ten appreciation
// entries. No RAM injection, direct entry, snapshot load or production switch.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"image/png"
	"os"
	"path/filepath"
	"reflect"
	"runtime"

	"github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

func must(err error) {
	if err != nil {
		panic(err)
	}
}
func digest(data []byte) string { h := sha256.Sum256(data); return hex.EncodeToString(h[:]) }
func writeJSON(path string, value any) {
	b, err := json.MarshalIndent(value, "", "  ")
	must(err)
	must(os.WriteFile(path, append(b, '\n'), 0644))
}
func stereoBytes(samples []int16) []byte {
	b := make([]byte, len(samples)*2)
	for i, v := range samples {
		binary.LittleEndian.PutUint16(b[i*2:], uint16(v))
	}
	return b
}

func main() {
	root := flag.String("root", "", "read-only fixed original")
	base := flag.String("base", "", "approved current assets")
	assets := flag.String("assets", "", "unapproved candidate assets")
	out := flag.String("out", "", "new research output")
	flag.Parse()
	if *root == "" || *base == "" || *assets == "" || *out == "" {
		panic("missing paths")
	}
	if _, err := os.Stat(*out); !os.IsNotExist(err) {
		panic("output already exists")
	}
	must(os.Mkdir(*out, 0755))
	var engines [2]*eightsword.Engine
	var files [2]*os.File
	for i, path := range []string{*base, *assets} {
		name := []string{"control", "candidate"}[i]
		must(os.Mkdir(filepath.Join(*out, name), 0755))
		e, err := eightsword.Open(eightsword.Options{Root: *root, Assets: path, Saves: filepath.Join(*out, name, "scratch"), HD: true})
		must(err)
		engines[i] = e
		defer e.Close()
		e.Oracle.SetClock(12, 0, 0, 0)
		e.EnableLiveClock(3000)
		if !e.HD || e.AssetError != "" || e.GraphicsError != "" || e.Music.LoadError != "" {
			panic(e.Status())
		}
		files[i], err = os.Create(filepath.Join(*out, name, "output-s16le-stereo.pcm"))
		must(err)
		defer files[i].Close()
	}
	if engines[0].Music.Status()["loaded_cues"] != 1 || engines[1].Music.Status()["loaded_cues"] != 10 {
		panic("wrong loaded cue counts")
	}
	var audioFrames int64
	verifyNativePCM := false
	advance := func(ms int) {
		for elapsed := 0; elapsed < ms; elapsed += 10 {
			var pcm [2][]byte
			for i, e := range engines {
				must(e.AdvanceCycles(30000))
				if e.Exited {
					panic("unexpected guest exit")
				}
				pcm[i] = stereoBytes(e.RenderAudio())
				_, err := files[i].Write(pcm[i])
				must(err)
				if elapsed%100 == 0 {
					e.Frame()
				}
			}
			if len(pcm[0]) != len(pcm[1]) {
				panic("audio clock lengths differ")
			}
			if verifyNativePCM && !bytes.Equal(pcm[0], pcm[1]) {
				panic("native output after Esc differs")
			}
			audioFrames += int64(len(pcm[0]) / 4)
		}
	}
	press := func(scan byte) {
		for _, e := range engines {
			must(e.Key(scan, true))
		}
		advance(100)
		for _, e := range engines {
			must(e.Key(scan, false))
		}
		advance(150)
	}
	var checkpoints []map[string]any
	state := func(e *eightsword.Engine, index int) []byte {
		path := filepath.Join(*out, fmt.Sprintf("current-%d.state", index))
		must(e.Oracle.SaveStateFile(path))
		data, err := os.ReadFile(path)
		must(err)
		return data
	}
	checkpoint := func(name string) {
		before := [2][]byte{state(engines[0], 0), state(engines[1], 1)}
		if !bytes.Equal(before[0], before[1]) {
			panic("full native state differs at " + name)
		}
		var frames [2][]byte
		for i, e := range engines {
			im := e.Frame()
			frames[i] = im.Pix
			if !bytes.Equal(before[i], state(e, i)) {
				panic("Frame changed guest at " + name)
			}
			f, err := os.Create(filepath.Join(*out, []string{"control", "candidate"}[i], name+".png"))
			must(err)
			must(png.Encode(f, im))
			must(f.Close())
		}
		if !bytes.Equal(frames[0], frames[1]) {
			panic("Frame pixels differ at " + name)
		}
		if !reflect.DeepEqual(engines[0].Oracle.FileOps(), engines[1].Oracle.FileOps()) || !reflect.DeepEqual(engines[0].InputEvents, engines[1].InputEvents) {
			panic("native inputs or I/O differ")
		}
		checkpoints = append(checkpoints, map[string]any{"name": name, "step": engines[0].Oracle.Steps(), "cycles": engines[0].Oracle.Cycles(), "audio_frame": audioFrames,
			"state_sha256": digest(before[0]), "frame_sha256": digest(frames[0]), "control_music": engines[0].Music.Status(), "candidate_music": engines[1].Music.Status()})
		fmt.Println(name, "passed")
	}
	advance(200)
	press(2)
	press(2)
	advance(500)
	if !engines[0].PAMLoaded {
		press(1)
	}
	for i := 0; i < 300; i++ {
		advance(100)
		if engines[0].PAMLoaded && engines[0].Tracker.VisibleScene == "main-menu" {
			break
		}
	}
	if engines[0].Tracker.VisibleScene != "main-menu" {
		panic("ordinary main menu not reached")
	}
	press(0x50)
	press(0x50)
	press(0x1c)
	advance(500)
	checkpoint("00-music-menu")
	for cue := 1; cue <= 10; cue++ {
		if cue > 1 {
			before := engines[1].Music.Starts
			oldCue := engines[1].Music.CurrentCue
			press(0x50)
			if engines[1].Music.Starts != before || engines[1].Music.CurrentCue != oldCue {
				panic("highlight restarted music")
			}
		}
		before := engines[1].Music.Starts
		press(0x1c)
		advance(2000)
		if engines[1].Music.Starts != before+1 || engines[1].Music.CurrentCue != cue || engines[1].Music.Status()["mode"] != "hd" {
			panic("candidate cue did not start")
		}
		checkpoint(fmt.Sprintf("%02d-cue-first", cue))
		if cue == 6 {
			loops := engines[1].Music.Loops
			advance(33000)
			if engines[1].Music.Loops <= loops {
				panic("full candidate loop absent")
			}
			checkpoint("06-cue-full-loop")
			before = engines[1].Music.Starts
			press(0x1c)
			advance(500)
			if engines[1].Music.Starts != before+1 {
				panic("same cue did not restart")
			}
			checkpoint("06-cue-restart")
		}
	}
	press(1)
	advance(1000)
	if engines[1].Music.Status()["mode"] != "native" || engines[1].Tracker.VisibleScene != "main-menu" {
		panic("Esc did not stop HD")
	}
	verifyNativePCM = true
	advance(1000)
	checkpoint("11-exit-native")
	for i, e := range engines {
		name := []string{"control", "candidate"}[i]
		writeJSON(filepath.Join(*out, name, "final-receipt.json"), e.Status())
		must(e.Oracle.SaveStateFile(filepath.Join(*out, name, "final.state")))
		must(os.Remove(filepath.Join(*out, fmt.Sprintf("current-%d.state", i))))
		must(files[i].Close())
	}
	writeJSON(filepath.Join(*out, "receipt.json"), map[string]any{"schema": 1, "status": "PASS-candidate-only-normal-ten-music-entries", "production": false,
		"normal_inputs": true, "ram_injection": false, "snapshot_loaded": false, "cycles_per_ms": 3000, "clock": "12:00:00 fixed before execution",
		"go_version": runtime.Version(), "audio_frames": audioFrames, "sample_rate": 48000, "channels": 2, "checkpoints": checkpoints,
		"native_pcm_equal_after_escape": true, "scope": "Ten ordinary music-appreciation entries, one complete loop, same-cue restart and Esc; not approval or save/load."})
}
