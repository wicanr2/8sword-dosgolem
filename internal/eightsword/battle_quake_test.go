package eightsword

import (
	"bytes"
	"encoding/json"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

func quakeTestBase() (*image.RGBA, []ownedPixel) {
	base := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	for y := 0; y < 1200; y++ {
		for x := 0; x < 1920; x++ {
			at := base.PixOffset(x, y)
			copy(base.Pix[at:at+4], []byte{byte(x), byte(y), byte(x + y), 255})
		}
	}
	pixels := make([]ownedPixel, 128000)
	for y := 90; y < 100; y++ {
		for x := 180; x < 200; x++ {
			pixels[y*640+x].Text = cell{ID: 1}
		}
	}
	pixels[199*640+4].Text = cell{ID: 2}
	pixels[10*640+10].Text = cell{ID: 3}
	return base, pixels
}

func TestBattleQuakeRows(t *testing.T) {
	base, pixels := quakeTestBase()
	before := append([]byte(nil), base.Pix...)
	for _, shift := range []int{6, 12, 18} {
		out := renderQuakeShift(base, pixels, shift)
		for y := 0; y < 1200; y++ {
			for x := 0; x < 1920; x++ {
				sy := min(y+shift, 1199)
				if pixels[y/6*640+x/3].Text.ID != 0 || pixels[sy/6*640+x/3].Text.ID != 0 {
					sy = y
				}
				at := out.PixOffset(x, y)
				src := base.PixOffset(x, sy)
				if !bytes.Equal(out.Pix[at:at+4], base.Pix[src:src+4]) {
					t.Fatalf("shift%d pixel%d,%d", shift, x, y)
				}
			}
		}
	}
	if !bytes.Equal(base.Pix, before) || renderQuakeShift(base, pixels, 0) != base || renderQuakeShift(base, nil, 6) != base {
		t.Fatal("base/invalid canvas")
	}
}

func TestBattleQuakeOriginal(t *testing.T) {
	root, project, out := vfxRuntimePaths(t)
	for _, name := range []string{"mixed", "sparse"} {
		t.Run(name, func(t *testing.T) {
			ref := filepath.Join(project, "workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1/quake-r1/original-r2", name, "observed")
			if name == "sparse" {
				ref = filepath.Join(project, "workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1/quake-r1/sparse-resumed")
			}
			dir := filepath.Join(out, "quake-"+name)
			if err := os.Mkdir(dir, 0755); err != nil {
				t.Fatal(err)
			}
			raw, err := os.ReadFile(filepath.Join(ref, "trace.json"))
			if err != nil {
				t.Fatal(err)
			}
			var trace struct{ Steps uint64 }
			if err = json.Unmarshal(raw, &trace); err != nil {
				t.Fatal(err)
			}
			e, err := Open(Options{Root: root, Saves: t.TempDir()})
			if err != nil {
				t.Fatal(err)
			}
			defer e.Close()
			if e.BattleVFXStatus().Bound {
				t.Fatal("native installed VFX")
			}
			if err = e.Oracle.LoadStateFile(filepath.Join(ref, "player-quake.state")); err != nil {
				t.Fatal(err)
			}
			e.Tracker = &Tracker{loadSegment: 0x110}
			e.HD = true
			base, pixels := quakeTestBase()
			p := &sourceAdapter{e: e, cachedScene: &ownedScene{Pixels: pixels}}
			p.bindBattleVFX()
			o := e.Oracle
			o.OnCall(oracle.Addr{Seg: 0xf67, Off: 0x960}, func(*oracle.Oracle) { e.battleVFX.beginQuake(o) })
			var source []byte
			var x, y, w, h int
			var dest uint16
			o.OnCall(oracle.Addr{Seg: 0x14d2, Off: 0x4f2}, func(*oracle.Oracle) {
				ptr := oracle.Addr{Seg: o.Arg(1), Off: o.Arg(0)}
				w = int(o.Word(ptr))
				h = int(o.Word(oracle.Addr{Seg: ptr.Seg, Off: ptr.Off + 2}))
				source = o.Bytes(ptr, 4+w*h*6)
				x, y = int(o.Arg(2)), int(o.Arg(3))
				dest = o.Word(oracle.Addr{Seg: o.Regs().DS, Off: 0x748a})
			})
			o.OnCall(oracle.Addr{Seg: 0x14d2, Off: 0x625}, func(*oracle.Oracle) {
				if source != nil {
					p.battleVFXBitmap(0x4f2, source, x, y, w, h, dest)
					source = nil
				}
			})
			seen := map[string]bool{}
			for i, off := range []uint16{0xa05, 0xa6e} {
				key := []string{"quake-low", "quake-high"}[i]
				o.OnCall(oracle.Addr{Seg: 0xf67, Off: off}, func(*oracle.Oracle) {
					v := e.battleVFX
					if !v.Active || seen[key] {
						return
					}
					// OnCall precedes Machine.Step; IRQ return can notify this PC again.
					v.quakePan(o, i)
					rejected := *v
					rejected.quakePan(o, (i+1)%5)
					if rejected.Cancelled != v.Cancelled+1 || rejected.Active {
						t.Fatal("wrong phase accepted")
					}
					before, after := filepath.Join(dir, key+"-before.state"), filepath.Join(dir, key+"-after.state")
					if err := o.SaveStateFile(before); err != nil {
						t.Fatal(err)
					}
					frame := p.composeBattleVFX(base)
					if p.composeBattleVFX(base) != frame {
						t.Fatal("unstable quake cache")
					}
					if err := o.SaveStateFile(after); err != nil {
						t.Fatal(err)
					}
					a, _ := os.ReadFile(before)
					b, _ := os.ReadFile(after)
					if !bytes.Equal(a, b) {
						t.Fatal("quake Frame changed guest")
					}
					f, err := os.Create(filepath.Join(dir, key+"-synthetic-base.png"))
					if err != nil {
						t.Fatal(err)
					}
					if err = png.Encode(f, frame); err != nil {
						t.Fatal(err)
					}
					f.Close()
					seen[key] = true
				})
			}
			if err = o.Run(trace.Steps - o.Steps()); err != nil {
				t.Fatal(err)
			}
			if err = o.SaveStateFile(filepath.Join(dir, "final.state")); err != nil {
				t.Fatal(err)
			}
			a, _ := os.ReadFile(filepath.Join(dir, "final.state"))
			b, _ := os.ReadFile(filepath.Join(ref, "final.state"))
			if !bytes.Equal(a, b) {
				t.Fatal("quake changed original final state")
			}
			v := e.BattleVFXStatus()
			if v.Started != 1 || v.Completed != 1 || v.Cancelled != 0 || v.QuakePans != 250 || v.QuakeDuplicates < 2 || v.PONCommits != 250 || v.Active || v.Shift != [2]int{} || !seen["quake-low"] || !seen["quake-high"] {
				t.Fatal(v, seen)
			}
			raw, _ = json.MarshalIndent(map[string]any{"battle_vfx": v, "full_original_state_equal": true, "frame_guest_pure": true, "synthetic_test_base": true, "reference_basis": map[bool]string{true: "unhooked-original-mStep-resume; continuous snapshot equivalence unknown", false: "continuous-fixed-control"}[name == "sparse"]}, "", "  ")
			if err = os.WriteFile(filepath.Join(dir, "receipt.json"), append(raw, '\n'), 0644); err != nil {
				t.Fatal(err)
			}
		})
	}
}

func TestBattleQuakeReject(t *testing.T) {
	root, project, out := vfxRuntimePaths(t)
	for _, name := range []string{"code", "selector", "caller", "caster", "geometry"} {
		t.Run(name, func(t *testing.T) {
			e, err := Open(Options{Root: root, Saves: t.TempDir()})
			if err != nil {
				t.Fatal(err)
			}
			defer e.Close()
			if err = e.Oracle.LoadStateFile(filepath.Join(project, "workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1/quake-r1/original-r2/mixed/observed/player-quake.state")); err != nil {
				t.Fatal(err)
			}
			e.Tracker = &Tracker{loadSegment: 0x110}
			e.HD = true
			p := &sourceAdapter{e: e}
			p.bindBattleVFX()
			o := e.Oracle
			r := o.Regs()
			v := e.battleVFX
			switch name {
			case "code":
				v.quakeBody[0] ^= 1
			case "selector":
				o.WriteU16(oracle.Addr{Seg: r.SS, Off: r.BP - 4}, 6)
			case "caller":
				o.WriteU16(oracle.Addr{Seg: r.SS, Off: r.BP + 2}, 0)
			case "caster":
				o.WriteU16(oracle.Addr{Seg: r.DS, Off: 0x56e8}, 1)
			case "geometry":
				o.WriteU16(oracle.Addr{Seg: r.DS, Off: 0x701e}, 65535)
			}
			before, after := filepath.Join(out, "guard-quake-"+name+"-before.state"), filepath.Join(out, "guard-quake-"+name+"-after.state")
			if err = o.SaveStateFile(before); err != nil {
				t.Fatal(err)
			}
			v.beginQuake(o)
			if err = o.SaveStateFile(after); err != nil {
				t.Fatal(err)
			}
			a, _ := os.ReadFile(before)
			b, _ := os.ReadFile(after)
			if !bytes.Equal(a, b) || v.Active || v.Started != 0 || v.Skipped != 1 {
				t.Fatal("unsafe quake context", v.BattleVFXInfo)
			}
		})
	}
}
