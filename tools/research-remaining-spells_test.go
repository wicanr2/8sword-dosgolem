//go:build ignore

// Private normal cold boot/F4 sample, resources fixture; no original rule overrides.
package eightsword

import (
	"bytes"
	"compress/gzip"
	"encoding/json"
	"fmt"
	"github.com/wicanr2/dosgolem/oracle"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"testing"
)

var researchCueScene *ownedScene

func TestResearchRemainingMap(t *testing.T) {
	root, assets, out := os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS"), os.Getenv("EIGHTSWORD_CUE_NORMAL_OUT")
	if out == "" {
		t.Fatal("missing research output")
	}
	if err := os.Mkdir(out, 0755); err != nil {
		t.Fatal(err)
	}
	e, err := Open(Options{Root: root, Assets: assets, Saves: filepath.Join(out, "scratch"), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer e.Close()
	e.Oracle.SetClock(12, 0, 0, 0)
	e.EnableLiveClock(3000)
	advance := func(ms int) {
		for i := 0; i < ms; i += 10 {
			if err := e.AdvanceCycles(30000); err != nil {
				t.Fatal(err)
			}
		}
	}
	press := func(scan byte, ms int) {
		if err := e.Key(scan, true); err != nil {
			t.Fatal(err)
		}
		advance(100)
		if err := e.Key(scan, false); err != nil {
			t.Fatal(err)
		}
		advance(ms)
	}
	ready := false
	e.Oracle.OnCall(oracle.Addr{Seg: 0x110, Off: 0x55a}, func(*oracle.Oracle) { ready = e.PAMLoaded })
	advance(1000)
	press(2, 100)
	press(2, 100)
	advance(1000)
	press(1, 1000)
	for i := 0; i < 2000 && !ready; i++ {
		advance(10)
	}
	if !ready {
		t.Fatal("normal menu")
	}
	press(0x50, 300)
	press(0x1c, 500)
	press(0x1c, 1800)
	e.Frame()
	if e.Tracker.VisibleScene != "map" {
		t.Fatal(e.Status())
	}
	q := e.Oracle
	ds := uint16(0x1e88)
	mutations := []map[string]any{}
	change := func(off, val uint16) {
		at := oracle.Addr{Seg: ds, Off: off}
		old := q.Word(at)
		q.WriteU16(at, val)
		mutations = append(mutations, map[string]any{"offset": off, "old": old, "new": val})
	}
	change(0x26aa, 1)
	for i := 0; i < 8; i++ {
		change(0x2b28+uint16(i*2), 2)
	}
	selected, cursor := 0, -1
	dispatch, returned, bird := false, false, false
	q.OnCall(oracle.Addr{Seg: 0x110, Off: 0x67ac}, func(o *oracle.Oracle) {
		r := o.Regs()
		node := int(o.Word(oracle.Addr{Seg: r.SS, Off: r.BP - 4}))
		if node != cursor {
			if node == selected {
				o.PressKey(oracle.KeyEnter)
			} else {
				o.PressKey(oracle.KeyDown)
			}
			cursor = node
		}
	})
	q.OnCall(oracle.Addr{Seg: 0x110, Off: 0x68ce}, func(*oracle.Oracle) { dispatch = true })
	q.OnCall(oracle.Addr{Seg: 0x110, Off: 0x6896}, func(*oracle.Oracle) {
		if dispatch {
			returned = true
		}
	})
	q.OnCall(oracle.Addr{Seg: 0x110, Off: 0x844c}, func(o *oracle.Oracle) {
		if dispatch && !returned {
			o.PressKey(oracle.KeyEnter)
		}
	})
	q.OnCall(oracle.Addr{Seg: 0x14d2, Off: 0xc86}, func(o *oracle.Oracle) {
		if !dispatch || returned {
			return
		}
		scan := oracle.Key(0x39)
		if selected == 0 {
			scan = oracle.KeyRight
		} else if selected == 7 {
			scan = oracle.KeyEnter
		}
		o.PressKey(scan)
	})
	q.OnCall(oracle.Addr{Seg: 0x110, Off: 0x827f}, func(o *oracle.Oracle) {
		if dispatch && !returned && !bird {
			o.PressKey(oracle.KeyEnter)
			bird = true
		}
	})
	results := []map[string]any{}
	for kind := 0; kind < 8; kind++ {
		selected, cursor = kind, -1
		dispatch, returned, bird = false, false, false
		captured := false
		q.PressKey(oracle.Key(0x3e))
		dir := filepath.Join(out, fmt.Sprint(kind))
		if err = os.Mkdir(dir, 0755); err != nil {
			t.Fatal(err)
		}
		for tick := 0; tick < 20000; tick++ {
			advance(10)
			v := e.spellCues
			if v != nil && v.Active && v.Kind == kind && q.Cycles() > v.start+360000 && !captured {
				before, after := filepath.Join(dir, "before.state"), filepath.Join(dir, "after.state")
				if err = q.SaveStateFile(before); err != nil {
					t.Fatal(err)
				}
				frame := e.Frame()
				if researchCueScene == nil {
					t.Fatal("no source scene")
				}
				e.spellCues = nil
				base := e.sourceRender()
				e.spellCues = v
				layer := drawSpellCue(kind, float64(v.sample)/120, v.Anchor)
				if err = q.SaveStateFile(after); err != nil {
					t.Fatal(err)
				}
				a, _ := os.ReadFile(before)
				b, _ := os.ReadFile(after)
				if !bytes.Equal(a, b) {
					t.Fatal("Frame changed guest")
				}
				for name, im := range map[string]*image.RGBA{"frame": frame, "base": base, "layer": layer} {
					f, e := os.Create(filepath.Join(dir, name+".png"))
					if e != nil {
						t.Fatal(e)
					}
					if e = png.Encode(f, im); e != nil {
						t.Fatal(e)
					}
					f.Close()
				}
				lf, le := os.Create(filepath.Join(dir, "layer-rgba.gz"))
				if le != nil {
					t.Fatal(le)
				}
				lg := gzip.NewWriter(lf)
				lg.Write(layer.Pix)
				lg.Close()
				lf.Close()
				mask := make([]byte, 128000)
				for i, p := range researchCueScene.Pixels[researchCueScene.Start : researchCueScene.Start+128000] {
					if p.Text.ID != 0 {
						mask[i] = 1
					}
				}
				f, er := os.Create(filepath.Join(dir, "mask.gz"))
				if er != nil {
					t.Fatal(er)
				}
				gz := gzip.NewWriter(f)
				gz.Write(mask)
				gz.Close()
				f.Close()
				m := map[string]any{"layer_rect": []int{layer.Rect.Min.X, layer.Rect.Min.Y, layer.Rect.Dx(), layer.Rect.Dy()}, "kind": kind, "sample": v.sample, "step": q.Steps(), "cycles": q.Cycles(), "cue": v.SpellCueInfo, "frame_guest_pure": true, "original_f4_menu": true, "resources_fixture": true, "source_status": e.Status()}
				raw, _ := json.MarshalIndent(m, "", "  ")
				os.WriteFile(filepath.Join(dir, "receipt.json"), append(raw, '\n'), 0644)
				results = append(results, m)
				captured = true
			}
			if returned && captured {
				advance(900)
				e.Frame()
				break
			}
			if tick == 19999 {
				t.Fatal("bounded normal map cast", kind, e.Status())
			}
		}
	}
	if len(results) != 8 {
		t.Fatal("missing map samples")
	}
	raw, _ := json.MarshalIndent(map[string]any{"status": "passed-normal-f4-eight-map-cues", "mutations": mutations, "cases": results, "limits": "Resources/learning fixture, original menu and outcomes; actual Engine Frames, not Ebiten Draw or natural learning."}, "", "  ")
	os.WriteFile(filepath.Join(out, "receipt.json"), append(raw, '\n'), 0644)
}
