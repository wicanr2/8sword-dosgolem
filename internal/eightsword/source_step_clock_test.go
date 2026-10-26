// 047 READY. Same fixed ordinary input as the legacy step-clock CLI.
package eightsword

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"image"
	"os"
	"path/filepath"
	"testing"
)

func TestSourceStepClockReplay(t *testing.T) {
	root, assets, out := os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS"), os.Getenv("EIGHTSWORD_STEP_CLOCK_OUT")
	if root == "" || assets == "" || out == "" {
		t.Skip("需原版、正式素材及新收據目錄")
	}
	var engines [2]*Engine
	for i := range engines {
		e, err := Open(Options{Root: root, Assets: assets, Saves: filepath.Join(out, fmt.Sprint(i)), HD: true})
		if err != nil {
			t.Fatal(err)
		}
		t.Cleanup(e.Close)
		e.Oracle.SetClock(12, 0, 0, 0)
		engines[i] = e
	}
	c := engines[0]
	pi, pf, pc := c.newSourcePAM()
	ii, iff, ic := c.newSourceIntro()
	c.sourceInstall = func() { ii(); pi() }
	c.sourceRender = func() *image.RGBA {
		if im := pf(); im != nil {
			return im
		}
		return iff()
	}
	c.sourceClose = func() { ic(); pc() }
	var writes [2]uint64
	for i, e := range engines {
		t.Cleanup(e.ObservePresentation(PresentationObserver{Write: func(w PresentationWrite) {
			if w.Step == e.Oracle.Steps() {
				writes[i]++
			}
		}}))
	}
	type action struct {
		Step uint64
		Scan byte
		Down bool
	}
	acts := []action{{1000000, 2, true}, {1500000, 2, false}, {3000000, 2, true}, {3500000, 2, false}}
	for _, a := range []struct {
		step uint64
		scan byte
	}{{126000000, 0x50}, {127000000, 0x1c}, {151000000, 0x1c}, {181000000, 0x3b}, {191000000, 1}, {201000000, 0x41}, {211000000, 1}, {221000000, 0x4d}, {231000000, 0x3b}, {241000000, 1}} {
		acts = append(acts, action{a.step, a.scan, true}, action{a.step + 500000, a.scan, false})
	}
	var checkpoints []map[string]any
	pcm := sha256.New()
	ai := 0
	for now := uint64(0); now < 250000000; {
		for ai < len(acts) && acts[ai].Step == now {
			for _, e := range engines {
				if err := e.Key(acts[ai].Scan, acts[ai].Down); err != nil {
					t.Fatal(err)
				}
			}
			ai++
		}
		target := now + 50000
		if ai < len(acts) && acts[ai].Step < target {
			target = acts[ai].Step
		}
		for _, e := range engines {
			if err := e.Advance(target - now); err != nil {
				t.Fatal(err)
			}
		}
		now = target
		if now%1000000 == 0 {
			a, b := int16Bytes(c.RenderAudio()), int16Bytes(engines[1].RenderAudio())
			if !bytes.Equal(a, b) {
				t.Fatal("step-clock mixed PCM differs", now)
			}
			pcm.Write(a)
			if !bytes.Equal(engines[0].Frame().Pix, engines[1].Frame().Pix) {
				t.Fatal("step-clock source frame differs", now)
			}
			if engines[1].renderFault != nil {
				t.Fatal(engines[1].renderFault)
			}
		}
		if now%10000000 == 0 {
			a, b := observerGuestState(t, c), observerGuestState(t, engines[1])
			if !bytes.Equal(a, b) {
				t.Fatal("step-clock guest differs", now)
			}
			checkpoints = append(checkpoints, map[string]any{"step": now, "state_sha256": fmt.Sprintf("%x", sha256.Sum256(a))})
		}
	}
	h := engines[1]
	if writes[0] == 0 || writes[1] != 0 || h.sourceCompatWrites == 0 || h.sourcePageClears == 0 || h.sourceBitmapRows == 0 || h.Tracker.VisibleScene != "map" {
		t.Fatal("step-clock delegation incomplete", writes, h.Status())
	}
	result := map[string]any{"schema": 1, "spec": "047", "status": "passed-step-clock-original-control", "production": true, "steps": h.Oracle.Steps(), "native_writes": writes, "checkpoints": checkpoints, "mixed_pcm_sha256": fmt.Sprintf("%x", pcm.Sum(nil)), "engine": h.Status(), "control": c.Status()}
	raw, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(filepath.Join(out, "replay.json"), append(raw, '\n'), 0644); err != nil {
		t.Fatal(err)
	}
	t.Logf("step-clock native pixel writes=%v Go compatibility=%d pages=%d copies=%d rows=%d reveal=%d", writes, h.sourceCompatWrites, h.sourcePageClears, h.sourcePageCopies, h.sourceBitmapRows, h.sourceRevealPixels)
}
