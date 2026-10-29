package eightsword

import (
	"bytes"
	"encoding/json"
	"github.com/wicanr2/dosgolem/oracle"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func vfxRuntimePaths(t *testing.T) (string, string, string) {
	t.Helper()
	root, project, out := os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_VFX_PROJECT"), os.Getenv("EIGHTSWORD_VFX_OUT")
	if root == "" || project == "" || out == "" {
		t.Skip("需要原版、VFX原版控制與新輸出")
	}
	return root, project, out
}
func TestBattleVFXOriginalExecutors(t *testing.T) {
	root, project, out := vfxRuntimePaths(t)
	batch := filepath.Join(project, "workplace/probe-20261023/graphics-first/battle-r1")
	for _, name := range []string{"special0-choice", "special2-choice", "special5-empty-original", "player-fireball", "player-thunder-mixed", "player-thunder-sparse"} {
		t.Run(name, func(t *testing.T) {
			dir := filepath.Join(out, name)
			if err := os.Mkdir(dir, 0755); err != nil {
				t.Fatal(err)
			}
			ref := filepath.Join(batch, "ai-policy-r1", name, "baseline")
			if name == "special5-empty-original" {
				ref = filepath.Join(batch, "ai-policy-extra-r2", name, "baseline")
			}
			initial, entry := "before-decision.state", uint16(0x36c6)
			expectedEffects := uint64(1)
			if name == "player-fireball" {
				ref = filepath.Join(batch, "player-spells-r1/cast-r5/observed")
				initial, entry = "player-effect.state", 0x345c
			}
			if strings.HasPrefix(name, "player-thunder-") {
				ref = filepath.Join(batch, "player-spells-r1/thunder-r1", strings.TrimPrefix(name, "player-thunder-"), "observed")
				if name == "player-thunder-sparse" {
					ref = filepath.Join(batch, "player-spells-r1/thunder-r1/sparse-resumed")
				}
				initial, entry = "player-effect.state", 0x345c
				if name == "player-thunder-mixed" {
					expectedEffects = 4
				}
			}
			raw, err := os.ReadFile(filepath.Join(ref, "trace.json"))
			if err != nil {
				t.Fatal(err)
			}
			var tr struct{ StartStep, DecisionStep, EndStep uint64 }
			if err = json.Unmarshal(raw, &tr); err != nil {
				t.Fatal(err)
			}
			if strings.HasPrefix(name, "player-") {
				var player struct{ Steps uint64 }
				if err = json.Unmarshal(raw, &player); err != nil {
					t.Fatal(err)
				}
				tr.EndStep = player.Steps
			}
			e, err := Open(Options{Root: root, Saves: filepath.Join(dir, "scratch")})
			if err != nil {
				t.Fatal(err)
			}
			defer e.Close()
			if e.BattleVFXStatus().Bound {
				t.Fatal("native installed VFX")
			}
			if err = e.Oracle.LoadStateFile(filepath.Join(ref, initial)); err != nil {
				t.Fatal(err)
			}
			// Explicit observer fixture: install only VFX hooks over the original executor.
			// This deliberately does not claim a warmed HD scene or production CPU takeover.
			if e.Tracker == nil {
				e.Tracker = &Tracker{}
			}
			e.Tracker.loadSegment = 0x110
			e.HD = true
			p := &sourceAdapter{e: e, cachedScene: &ownedScene{Pixels: make([]ownedPixel, 128000)}}
			p.bindBattleVFX()
			o := e.Oracle
			o.OnCall(oracle.Addr{Seg: 0xf67, Off: entry}, func(*oracle.Oracle) {
				if err := o.SaveStateFile(filepath.Join(dir, "effect-entry.state")); err != nil {
					t.Fatal(err)
				}
			})
			type pending struct {
				raw        []byte
				x, y, w, h int
				dest       uint16
			}
			calls := map[uint16]pending{}
			samples := map[string]bool{}
			base := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
			for _, site := range []struct{ entry, ret uint16 }{{0x626, 0x76e}, {0x4f2, 0x625}} {
				site := site
				o.OnCall(oracle.Addr{Seg: 0x14d2, Off: site.entry}, func(*oracle.Oracle) {
					ptr := oracle.Addr{Seg: o.Arg(1), Off: o.Arg(0)}
					w, h := int(o.Word(ptr)), int(o.Word(oracle.Addr{Seg: ptr.Seg, Off: ptr.Off + 2}))
					calls[site.entry] = pending{o.Bytes(ptr, 4+w*h*6), int(o.Arg(2)), int(o.Arg(3)), w, h, o.Word(oracle.Addr{Seg: o.Regs().DS, Off: 0x748a})}
				})
				o.OnCall(oracle.Addr{Seg: 0x14d2, Off: site.ret}, func(*oracle.Oracle) {
					c, ok := calls[site.entry]
					if !ok {
						return
					}
					delete(calls, site.entry)
					p.battleVFXBitmap(site.entry, c.raw, c.x, c.y, c.w, c.h, c.dest)
					v := e.battleVFX
					if v.Active && ((v.Phase == "flight" && v.poses == 2) || (v.Phase == "impact" && v.pon == 6)) && !samples[v.Phase] {
						phase := v.Phase
						before, after := filepath.Join(dir, phase+"-before.state"), filepath.Join(dir, phase+"-after.state")
						if err := o.SaveStateFile(before); err != nil {
							t.Fatal(err)
						}
						frame := p.composeBattleVFX(base)
						if p.composeBattleVFX(base) != frame {
							t.Fatal("unstable repeated frame")
						}
						if err := o.SaveStateFile(after); err != nil {
							t.Fatal(err)
						}
						a, _ := os.ReadFile(before)
						b, _ := os.ReadFile(after)
						if !bytes.Equal(a, b) {
							t.Fatal("render changed guest")
						}
						f, err := os.Create(filepath.Join(dir, phase+"-synthetic-base.png"))
						if err != nil {
							t.Fatal(err)
						}
						if err = png.Encode(f, frame); err != nil {
							t.Fatal(err)
						}
						f.Close()
						samples[phase] = true
					}
				})
			}
			next := tr.StartStep
			for next < tr.DecisionStep && next < tr.StartStep+12000000 {
				next += 2000000
			}
			if strings.HasPrefix(name, "player-") {
				next = tr.EndStep + 1
			}
			for o.Steps() < tr.EndStep {
				if next >= tr.StartStep+12000000 {
					next = tr.EndStep + 1
				}
				if o.Steps() >= next {
					o.PressScan(" ")
					next += 2000000
				}
				end := min(tr.EndStep, next)
				if err = o.Run(end - o.Steps()); err != nil {
					t.Fatal(err)
				}
			}
			if err = o.SaveStateFile(filepath.Join(dir, "final.state")); err != nil {
				t.Fatal(err)
			}
			actual, _ := os.ReadFile(filepath.Join(dir, "final.state"))
			expected, _ := os.ReadFile(filepath.Join(ref, "final.state"))
			if !bytes.Equal(actual, expected) {
				t.Fatal("VFX changed original final state")
			}
			info := e.BattleVFXStatus()
			if info.Started != expectedEffects || info.Completed != expectedEffects || info.PONCommits != expectedEffects*12 || info.SourceCommits != expectedEffects*4 || info.Active || !samples["flight"] || !samples["impact"] {
				t.Fatal(info, samples)
			}
			referenceBasis := "continuous-fixed-control"
			if name == "player-thunder-sparse" {
				referenceBasis = "unhooked-original-mStep-resume; continuous snapshot equivalence unknown"
			}
			raw, _ = json.MarshalIndent(map[string]any{"battle_vfx": info, "full_original_state_equal": true, "frame_guest_pure": true, "synthetic_test_base": true, "reference_basis": referenceBasis}, "", "  ")
			if err = os.WriteFile(filepath.Join(dir, "receipt.json"), append(raw, '\n'), 0644); err != nil {
				t.Fatal(err)
			}
		})
	}
}
func TestBattleVFXRejectBeforeGuestWrites(t *testing.T) {
	root, project, out := vfxRuntimePaths(t)
	for _, name := range []string{"code", "selector", "mapping", "geometry", "player-code", "player-selector", "player-caster", "player-geometry", "thunder-code", "thunder-caller", "thunder-selector", "thunder-geometry"} {
		t.Run(name, func(t *testing.T) {
			e, err := Open(Options{Root: root, Saves: t.TempDir()})
			if err != nil {
				t.Fatal(err)
			}
			defer e.Close()
			player := strings.HasPrefix(name, "player-") || strings.HasPrefix(name, "thunder-")
			initial, entry := "workplace/probe-20261023/graphics-first/battle-r1/ai-policy-r1/special0-choice/baseline/before-decision.state", uint16(0x36c6)
			if player {
				initial, entry = "workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1/cast-r5/observed/player-effect.state", 0x345c
			}
			if strings.HasPrefix(name, "thunder-") {
				initial = "workplace/probe-20261023/graphics-first/battle-r1/player-spells-r1/thunder-r1/mixed/observed/player-effect.state"
			}
			if err = e.Oracle.LoadStateFile(filepath.Join(project, initial)); err != nil {
				t.Fatal(err)
			}
			if !player {
				if err = e.Oracle.RunUntil(oracle.At(oracle.Addr{Seg: 0xf67, Off: entry}), oracle.Budget(100000)); err != nil {
					t.Fatal(err)
				}
			}
			if e.Tracker == nil {
				e.Tracker = &Tracker{}
			}
			e.Tracker.loadSegment = 0x110
			p := &sourceAdapter{e: e}
			p.bindBattleVFX()
			v := e.battleVFX
			r := e.Oracle.Regs()
			switch name {
			case "code":
				v.body[0] ^= 1
			case "selector":
				e.Oracle.WriteU16(oracle.Addr{Seg: r.SS, Off: r.BP - 4}, 4)
			case "mapping":
				e.Oracle.WriteU16(oracle.Addr{Seg: r.SS, Off: r.SP + 4}, 6)
			case "geometry":
				e.Oracle.WriteU16(oracle.Addr{Seg: r.DS, Off: 0x7024}, 65535)
			case "player-code":
				v.playerBody[0] ^= 1
			case "player-selector":
				e.Oracle.WriteU16(oracle.Addr{Seg: r.SS, Off: r.BP - 4}, 1)
			case "player-caster":
				e.Oracle.WriteU16(oracle.Addr{Seg: r.DS, Off: 0x56e8}, 1)
			case "player-geometry":
				e.Oracle.WriteU16(oracle.Addr{Seg: r.DS, Off: 0x7042}, 65535)
			case "thunder-code":
				v.playerBody[0] ^= 1
			case "thunder-caller":
				e.Oracle.WriteU16(oracle.Addr{Seg: r.SS, Off: r.SP}, 0x74a)
			case "thunder-selector":
				e.Oracle.WriteU16(oracle.Addr{Seg: r.SS, Off: r.BP - 4}, 0)
			case "thunder-geometry":
				e.Oracle.WriteU16(oracle.Addr{Seg: r.DS, Off: 0x701e}, 65535)
			}
			before, after := filepath.Join(out, "guard-"+name+"-before.state"), filepath.Join(out, "guard-"+name+"-after.state")
			if err = e.Oracle.SaveStateFile(before); err != nil {
				t.Fatal(err)
			}
			v.beginFrom(e.Oracle, player)
			if err = e.Oracle.SaveStateFile(after); err != nil {
				t.Fatal(err)
			}
			a, _ := os.ReadFile(before)
			b, _ := os.ReadFile(after)
			if !bytes.Equal(a, b) || v.Active || v.Skipped != 1 {
				t.Fatal("unsafe context", v.BattleVFXInfo)
			}
		})
	}
}
