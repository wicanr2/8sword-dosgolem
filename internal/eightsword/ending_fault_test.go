package eightsword

import (
	"bytes"
	"errors"
	"fmt"
	"image/png"
	"os"
	"path/filepath"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

// The original cleanup branch is selected once, as authorized for presentation
// tests. Input and overlay loading still run through the original program.
func endingFaultReach(t *testing.T, e *Engine) error {
	t.Helper()
	bound, changed := false, false
	advance := func(ms int) error {
		for n := 0; n < ms; n += 10 {
			if err := e.AdvanceCycles(30000); err != nil {
				return err
			}
			if !bound && e.PAMLoaded {
				bound = true
				e.Oracle.OnCall(oracle.Addr{Seg: 0x110, Off: 0x20e}, func(o *oracle.Oracle) {
					if !changed && !e.inEndingPhase() {
						o.WriteU16(oracle.Addr{Seg: o.Regs().DS, Off: 0x56e2}, 1)
						changed = true
					}
				})
			}
			_ = e.RenderAudio()
			if n%100 == 0 {
				_ = e.Frame()
			}
		}
		return nil
	}
	press := func(scan byte) error {
		if err := e.Key(scan, true); err != nil {
			return err
		}
		if err := advance(100); err != nil {
			return err
		}
		if err := e.Key(scan, false); err != nil {
			return err
		}
		return advance(150)
	}
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	must(advance(200))
	must(press(2))
	must(press(2))
	must(advance(500))
	if !e.PAMLoaded {
		must(press(1))
	}
	for n := 0; n < 300 && e.Tracker.VisibleScene != "main-menu"; n++ {
		must(advance(100))
	}
	if e.Tracker.VisibleScene != "main-menu" {
		t.Fatal("main menu not reached")
	}
	for _, scan := range []byte{0x50, 0x1c, 0x1c} {
		must(press(scan))
		must(advance(500))
	}
	must(advance(2000))
	for _, scan := range []byte{0x41, 0x4d, 0x1c, 0x1c} {
		if err := press(scan); err != nil {
			return err
		}
		if err := advance(500); err != nil {
			return err
		}
	}
	for n := 0; n < 15000 && !e.Exited; n++ {
		if p := e.ending; p != nil && p.bound && p.scene.mode && p.active == 0 {
			page := p.scene.pages[p.scene.active]
			if page.stage == "END5.AY" && page.glyphs > 0 {
				_ = e.Frame()
				if changed {
					return nil
				}
			}
		}
		if err := advance(10); err != nil {
			return err
		}
	}
	return fmt.Errorf("controlled ending did not reach END5")
}

func TestEndingSourceFaultStops(t *testing.T) {
	root, assets, out := endingTestPaths(t)
	for _, name := range []string{"display-mode", "unknown-source", "required-noto"} {
		t.Run(name, func(t *testing.T) {
			dir := filepath.Join(out, "fault-"+name)
			if err := os.Mkdir(dir, 0755); err != nil {
				t.Fatal(err)
			}
			selected := assets
			if name == "required-noto" {
				selected = filepath.Join(dir, "assets")
				if err := os.Mkdir(selected, 0755); err != nil {
					t.Fatal(err)
				}
				entries, err := os.ReadDir(assets)
				if err != nil {
					t.Fatal(err)
				}
				for _, entry := range entries {
					if entry.Name() == "ending-font-noto.png" {
						continue
					}
					data, err := os.ReadFile(filepath.Join(assets, entry.Name()))
					if err != nil {
						t.Fatal(err)
					}
					if err := os.WriteFile(filepath.Join(selected, entry.Name()), data, 0644); err != nil {
						t.Fatal(err)
					}
				}
				if err := os.WriteFile(filepath.Join(selected, "ending-font-noto.png"), []byte("actual damaged PNG"), 0644); err != nil {
					t.Fatal(err)
				}
			}
			e, err := Open(Options{Root: root, Assets: selected, Saves: filepath.Join(dir, "scratch"), HD: true})
			if err != nil {
				t.Fatal(err)
			}
			defer e.Close()
			e.Oracle.SetClock(12, 0, 0, 0)
			e.EnableLiveClock(3000)
			err = endingFaultReach(t, e)
			before := append([]byte(nil), e.sourceHeldFrame.Pix...)
			want := "missing-or-invalid-ending-assets"
			if name != "required-noto" {
				if err != nil {
					t.Fatal(err)
				}
				entry := oracle.Addr{Seg: 0x8000, Off: 0}
				if name == "display-mode" {
					// Test-only INT10 request; the production renderer contains no
					// executable guest code or forced display-mode transition.
					e.Oracle.WriteBytes(entry, []byte{0xb8, 0x13, 0, 0xcd, 0x10, 0xeb, 0xfe})
					want = "unhandled-display-mode"
				} else {
					// A valid 8x1 four-plane bitmap with unregistered source bytes.
					e.Oracle.WriteBytes(oracle.Addr{Seg: 0x8100}, []byte{1, 0, 1, 0, 0x13, 0x57, 0x9b, 0xdf})
					// push y,x,segment,offset; far call original bitmap entry.
					e.Oracle.WriteBytes(entry, []byte{0x6a, 0, 0x6a, 0, 0x68, 0, 0x81, 0x6a, 0, 0x9a, 0x96, 9, 0x93, 3, 0xeb, 0xfe})
					want = "unclassified-source-bitmap"
				}
				e.Oracle.CallNear(entry, 0, oracle.CallRegs{})
				err = e.AdvanceCycles(100000)
			}
			var fault *OwnedRenderFault
			if !errors.As(err, &fault) || fault.Phase != "ending" || fault.Reason != want {
				t.Fatalf("unexpected fault %v", err)
			}
			state := observerGuestState(t, e)
			step, cycles := e.Oracle.Steps(), e.Oracle.Cycles()
			for n := 0; n < 3; n++ {
				if e.Advance(100000) != fault || e.AdvanceCycles(100000) != fault || !bytes.Equal(state, observerGuestState(t, e)) {
					t.Fatal("fault resumed guest")
				}
				if !bytes.Equal(before, e.Frame().Pix) {
					t.Fatal("fault lost last complete source frame")
				}
			}
			f, err := os.Create(filepath.Join(dir, "held.png"))
			if err != nil {
				t.Fatal(err)
			}
			if err := png.Encode(f, e.Frame()); err != nil {
				t.Fatal(err)
			}
			if err := f.Close(); err != nil {
				t.Fatal(err)
			}
			endingTestWrite(t, filepath.Join(dir, "fault.json"), map[string]any{"fault": fault, "steps": step, "cycles": cycles, "stable_state": hash(state), "held_pixels": hash(before), "rejected_advances": 6, "ending": e.EndingStatus(), "production_forced_branch": false})
		})
	}
}
