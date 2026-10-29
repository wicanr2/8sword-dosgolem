package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/wicanr2/dosgolem/oracle"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"testing"
)

func TestSpellCueRendering(t *testing.T) {
	base, pixels := quakeTestBase()
	before := append([]byte(nil), base.Pix...)
	seen := map[string]bool{}
	for kind := 0; kind < 10; kind++ {
		layer := drawSpellCue(kind, .35, [2]int{224, 92})
		out := compositeSpellCue(base, layer, pixels)
		if out == base || bytes.Equal(out.Pix, base.Pix) {
			t.Fatal("missing cue", kind)
		}
		h := hash(out.Pix)
		if seen[h] {
			t.Fatal("indistinct cue", kind)
		}
		seen[h] = true
		for y := 0; y < 1200; y++ {
			for x := 0; x < 1920; x++ {
				if x < 12 || x >= 1344 || y < 12 || y >= 1140 || pixels[y/6*640+x/3].Text.ID != 0 {
					at := base.PixOffset(x, y)
					if !bytes.Equal(base.Pix[at:at+4], out.Pix[at:at+4]) {
						t.Fatal("protected pixel", kind, x, y)
					}
				}
			}
		}
		if dir := os.Getenv("EIGHTSWORD_CUE_DRAW_OUT"); dir != "" {
			f, e := os.Create(filepath.Join(dir, fmt.Sprintf("cue-%02d.png", kind)))
			if e != nil {
				t.Fatal(e)
			}
			if e = png.Encode(f, out); e != nil {
				t.Fatal(e)
			}
			f.Close()
		}
	}
	if !bytes.Equal(base.Pix, before) || drawSpellCue(-1, .5, [2]int{}) != nil || drawSpellCue(0, 1, [2]int{}) != nil {
		t.Fatal("invalid/pure")
	}
}

func TestSpellCueMapProtectionAndBattleBaseline(t *testing.T) {
	_, project, _ := vfxRuntimePaths(t)
	base, pixels := quakeTestBase()
	for y := 70; y < 115; y++ {
		for x := 210; x < 240; x++ {
			pixels[y*640+x].Actor.ID = 1
		}
	}
	for kind := 0; kind < 8; kind++ {
		out := compositeProtectedSpellCue(base, drawSpellCue(kind, .35, [2]int{224, 92}), pixels, true)
		for y := 70 * 6; y < 115*6; y++ {
			for x := 210 * 3; x < 240*3; x++ {
				at := base.PixOffset(x, y)
				if !bytes.Equal(base.Pix[at:at+4], out.Pix[at:at+4]) {
					t.Fatal("map cue covered actor", kind, x, y)
				}
			}
		}
	}
	base, pixels = quakeTestBase()
	for _, kind := range []int{8, 9} {
		f, err := os.Open(filepath.Join(project, "workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1/remaining-r1/draw-r1", fmt.Sprintf("cue-%02d.png", kind)))
		if err != nil {
			t.Fatal(err)
		}
		prior, err := png.Decode(f)
		f.Close()
		if err != nil {
			t.Fatal(err)
		}
		out := compositeSpellCue(base, drawSpellCue(kind, .35, [2]int{224, 92}), pixels)
		for y := 0; y < 1200; y++ {
			for x := 0; x < 1920; x++ {
				r, g, b, a := prior.At(x, y).RGBA()
				at := out.PixOffset(x, y)
				if !bytes.Equal(out.Pix[at:at+4], []byte{byte(r >> 8), byte(g >> 8), byte(b >> 8), byte(a >> 8)}) {
					t.Fatal("battle cue changed", kind, x, y)
				}
			}
		}
	}
}

func TestSpellCueMapVisibilityWindow(t *testing.T) {
	root, project, _ := vfxRuntimePaths(t)
	e, err := Open(Options{Root: root, Saves: t.TempDir()})
	if err != nil {
		t.Fatal(err)
	}
	defer e.Close()
	if err = e.Oracle.LoadStateFile(filepath.Join(project, "workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1/remaining-r1/original-map-r8/map-3/entry.state")); err != nil {
		t.Fatal(err)
	}
	base, pixels := quakeTestBase()
	p := &sourceAdapter{e: e, cachedScene: &ownedScene{Pixels: pixels}}
	e.spellCues = &spellCues{}
	e.spellCues.activate(e.Oracle, 0, [2]int{224, 92}, 1, 0)
	if err = e.Oracle.RunCycles(2100000); err != nil {
		t.Fatal(err)
	}
	if p.composeSpellCues(base) == base || !e.spellCues.Active {
		t.Fatal("map cue disappeared at old cutoff")
	}
	if err = e.Oracle.RunCycles(1800000); err != nil {
		t.Fatal(err)
	}
	if p.composeSpellCues(base) != base || e.spellCues.Active || e.spellCues.Completed != 1 {
		t.Fatal("map cue did not restore base")
	}
}

func TestSpellCueActorAlpha(t *testing.T) {
	base, pixels := quakeTestBase()
	pixels[92*640+224].Actor.ID = 1
	tile := image.NewRGBA(image.Rect(0, 0, 3, 6))
	tile.Pix[tile.PixOffset(1, 2)+3] = 255
	actors := map[uint16]*graphicMaterial{1: {NativeWidth: 1, NativeHeight: 1, Tile: tile}}
	layer := image.NewRGBA(image.Rect(672, 552, 675, 558))
	for at := 0; at < len(layer.Pix); at += 4 {
		copy(layer.Pix[at:at+4], []byte{200, 0, 100, 200})
	}
	out := compositeMaterialSpellCue(base, layer, pixels, actors)
	ink := base.PixOffset(673, 554)
	clear := base.PixOffset(672, 552)
	if !bytes.Equal(out.Pix[ink:ink+4], base.Pix[ink:ink+4]) || bytes.Equal(out.Pix[clear:clear+4], base.Pix[clear:clear+4]) {
		t.Fatal("actor alpha became a rectangular exclusion")
	}
	fallback := compositeMaterialSpellCue(base, layer, pixels, map[uint16]*graphicMaterial{})
	if !bytes.Equal(fallback.Pix[clear:clear+4], base.Pix[clear:clear+4]) {
		t.Fatal("missing actor material lost native protection")
	}
}

func TestSpellCueOriginal(t *testing.T) {
	root, project, out := vfxRuntimePaths(t)
	q := filepath.Join(project, "workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1/remaining-r1")
	for kind := 0; kind < 10; kind++ {
		t.Run(fmt.Sprint(kind), func(t *testing.T) {
			name, initial := "map-"+fmt.Sprint(kind), "entry.state"
			ref := filepath.Join(q, "original-map-r8", name)
			if kind >= 8 {
				name = []string{"freeze", "clone"}[kind-8]
				ref = filepath.Join(q, name, "observed")
				initial = "player-" + name + ".state"
			}
			raw, e := os.ReadFile(filepath.Join(ref, map[bool]string{true: "trace.json", false: "receipt.json"}[kind >= 8]))
			if e != nil {
				t.Fatal(e)
			}
			var d struct{ Steps uint64 }
			if e = json.Unmarshal(raw, &d); e != nil {
				t.Fatal(e)
			}
			dir := filepath.Join(out, "cue-"+name)
			if e = os.Mkdir(dir, 0755); e != nil {
				t.Fatal(e)
			}
			var final [2][]byte
			var pcm [2]string
			var info SpellCueInfo
			continuous := false
			for pass := 0; pass < 2; pass++ {
				eng, e := Open(Options{Root: root, Saves: t.TempDir()})
				if e != nil {
					t.Fatal(e)
				}
				o := eng.Oracle
				if eng.SpellCueStatus().Bound {
					t.Fatal("native cue bound")
				}
				if e = o.LoadStateFile(filepath.Join(ref, initial)); e != nil {
					t.Fatal(e)
				}
				if kind < 8 {
					done, bird := false, false
					r := o.Regs()
					ss, sp := r.SS, r.SP+4
					o.OnCall(oracle.Addr{Seg: 0x110, Off: 0x6896}, func(o *oracle.Oracle) {
						if o.Regs().SS == ss && o.Regs().SP == sp {
							done = true
						}
					})
					o.OnCall(oracle.Addr{Seg: 0x110, Off: 0x844c}, func(o *oracle.Oracle) {
						if !done {
							o.PressKey(oracle.KeyEnter)
						}
					})
					o.OnCall(oracle.Addr{Seg: 0x14d2, Off: 0xc86}, func(o *oracle.Oracle) {
						if done {
							return
						}
						scan := uint8(0x39)
						if kind == 0 {
							scan = 0x4d
						} else if kind == 7 {
							scan = 0x1c
						}
						o.PressKey(oracle.Key(scan))
					})
					o.OnCall(oracle.Addr{Seg: 0x110, Off: 0x827f}, func(o *oracle.Oracle) {
						if !done && !bird {
							o.PressKey(oracle.KeyEnter)
							bird = true
						}
					})
				}
				if pass == 1 {
					eng.Tracker = &Tracker{loadSegment: 0x110}
					eng.HD = true
					p := &sourceAdapter{e: eng}
					p.bindBattleVFX()
					v := eng.spellCues
					if kind >= 8 {
						v.battlePending = true
						v.battleSP = o.Regs().BP + 2
						v.battleSequence = 1
					}
					// Pure render probe after accepted original events, no guest modifications.
					base, pixels := quakeTestBase()
					p.cachedScene = &ownedScene{Pixels: pixels}
					target := d.Steps
					if target < o.Steps() {
						t.Fatal("bad reference steps")
					}
					captured := false
					for o.Steps() < target {
						count := min(uint64(10000), target-o.Steps())
						if e = o.Run(count); e != nil {
							t.Fatal(e)
						}
						if v.Active && !captured && o.Cycles() > v.start {
							before := filepath.Join(dir, "frame-before.state")
							after := filepath.Join(dir, "frame-after.state")
							if e = o.SaveStateFile(before); e != nil {
								t.Fatal(e)
							}
							frame := p.composeSpellCues(base)
							if p.composeSpellCues(base) != frame {
								t.Fatal("unstable cache")
							}
							if e = o.SaveStateFile(after); e != nil {
								t.Fatal(e)
							}
							a, _ := os.ReadFile(before)
							b, _ := os.ReadFile(after)
							if !bytes.Equal(a, b) {
								t.Fatal("frame mutated guest")
							}
							captured = true
						}
					}
					if v.Started == 0 {
						t.Fatal("no accepted cue", v.SpellCueInfo)
					}
					info = v.SpellCueInfo
				} else {
					if e = o.Run(d.Steps - o.Steps()); e != nil {
						t.Fatal(e)
					}
				}
				f := filepath.Join(dir, fmt.Sprintf("final-%d.state", pass))
				if e = o.SaveStateFile(f); e != nil {
					t.Fatal(e)
				}
				final[pass], e = os.ReadFile(f)
				if e != nil {
					t.Fatal(e)
				}
				if pass == 0 {
					b, _ := os.ReadFile(filepath.Join(ref, "final.state"))
					continuous = bytes.Equal(final[pass], b)
				}
				pcm[pass] = hash(int16Bytes(eng.RenderAudio()))
				eng.Close()
			}
			if !bytes.Equal(final[0], final[1]) {
				t.Fatal("cue changed original snapshot result")
			}
			if pcm[0] != pcm[1] {
				t.Fatal("cue changed PCM")
			}
			raw, _ = json.MarshalIndent(map[string]any{"kind": kind, "full_state_equal": true, "same_snapshot_control": true, "continuous_reference_equal": continuous, "cue": info}, "", "  ")
			if e = os.WriteFile(filepath.Join(dir, "receipt.json"), append(raw, '\n'), 0644); e != nil {
				t.Fatal(e)
			}
		})
	}
}

func TestSpellCueGuards(t *testing.T) {
	root, project, out := vfxRuntimePaths(t)
	for _, name := range []string{"code", "selector", "caller", "charge", "learned"} {
		t.Run(name, func(t *testing.T) {
			e, err := Open(Options{Root: root, Saves: t.TempDir()})
			if err != nil {
				t.Fatal(err)
			}
			defer e.Close()
			o := e.Oracle
			initial := filepath.Join(project, "workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1/remaining-r1/original-map-r8/map-3/entry.state")
			if err = o.LoadStateFile(initial); err != nil {
				t.Fatal(err)
			}
			e.Tracker = &Tracker{loadSegment: 0x110}
			e.HD = true
			p := &sourceAdapter{e: e}
			p.bindBattleVFX()
			checked := false
			o.OnCall(oracle.Addr{Seg: 0x110, Off: 0x68f0}, func(o *oracle.Oracle) {
				if checked {
					return
				}
				checked = true
				v := e.spellCues
				beforeDuplicates := v.Duplicates
				started := v.Started
				v.mapCue(o)
				if v.Started != started || v.Duplicates != beforeDuplicates+1 {
					t.Fatal("duplicate counted twice")
				}
				bad := *v
				bad.Active = false
				bad.Started = 0
				bad.Skipped = 0
				r := o.Regs()
				switch name {
				case "code":
					bad.mapBody = append([]byte(nil), bad.mapBody...)
					bad.mapBody[0] ^= 1
				case "selector":
					o.WriteU16(oracle.Addr{Seg: r.SS, Off: r.BP + 6}, 8)
				case "caller":
					o.WriteU16(oracle.Addr{Seg: r.SS, Off: r.BP + 2}, 0)
				case "charge":
					o.WriteU16(oracle.Addr{Seg: r.DS, Off: 0x2b2e}, 0)
				case "learned":
					o.WriteU16(oracle.Addr{Seg: r.DS, Off: 0x26aa}, 0)
				}
				before, after := filepath.Join(out, "guard-cue-"+name+"-before.state"), filepath.Join(out, "guard-cue-"+name+"-after.state")
				if err = o.SaveStateFile(before); err != nil {
					t.Fatal(err)
				}
				bad.mapCue(o)
				if err = o.SaveStateFile(after); err != nil {
					t.Fatal(err)
				}
				a, _ := os.ReadFile(before)
				b, _ := os.ReadFile(after)
				if !bytes.Equal(a, b) || bad.Active || bad.Started != 0 || bad.Skipped != 1 {
					t.Fatal("unsafe cue guard", bad.SpellCueInfo)
				}
			})
			if err = o.RunUntil(oracle.NewCond("cue-guard", func(*oracle.Oracle) bool { return checked }), oracle.Budget(5000)); err != nil {
				t.Fatal(err)
			}
			if !checked {
				t.Fatal("guard not reached")
			}
		})
	}
}
