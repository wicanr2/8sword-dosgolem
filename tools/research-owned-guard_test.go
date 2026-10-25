//go:build ignore

package eightsword

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

// Two actual guest instruction paths expose a stale source scene. The guarded
// renderer reports them while preserving native execution through the current
// 50,000-cycle slice. This is controlled fault injection, not a player route.
func TestResearchOwnedSourceGuard(t *testing.T) {
	root, assets, out := os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_OWNED_GUARD_ASSETS"), os.Getenv("EIGHTSWORD_TEST_OWNED_GUARD_OUT")
	if root == "" || assets == "" || out == "" {
		t.Fatal("explicit original/assets/new output required")
	}
	if err := os.Mkdir(out, 0755); err != nil {
		t.Fatal(err)
	}
	for _, kind := range []string{"unclassified-write", "unhandled-mode"} {
		for _, control := range []bool{true, false} {
			label := "guarded"
			if control {
				label = "control"
			}
			t.Run(kind+"/"+label, func(t *testing.T) {
				q := filepath.Join(out, kind, label)
				owned := filepath.Join(q, "owned")
				if err := os.MkdirAll(owned, 0755); err != nil {
					t.Fatal(err)
				}
				t.Setenv("EIGHTSWORD_RESEARCH_OWNED", owned)
				t.Setenv("EIGHTSWORD_RESEARCH_GUARD_CONTROL", "0")
				if control {
					t.Setenv("EIGHTSWORD_RESEARCH_GUARD_CONTROL", "1")
				}
				e, err := Open(Options{Root: root, Assets: assets, Saves: filepath.Join(q, "scratch"), HD: true})
				if err != nil {
					t.Fatal(err)
				}
				t.Cleanup(e.Close)
				if !e.HD || e.AssetError != "" || e.GraphicsError != "" {
					t.Fatal(e.Status())
				}
				e.Oracle.SetClock(12, 0, 0, 0)
				e.EnableLiveClock(3000)
				var pcm bytes.Buffer
				advance := func(ms int) {
					for i := 0; i < ms; i += 10 {
						if err := e.AdvanceCycles(30000); err != nil {
							t.Fatal(err)
						}
						if err := binary.Write(&pcm, binary.LittleEndian, e.RenderAudio()); err != nil {
							t.Fatal(err)
						}
						if i%100 == 0 {
							e.Frame()
						}
					}
				}
				press := func(scan byte, hold, gap int) {
					if err := e.Key(scan, true); err != nil {
						t.Fatal(err)
					}
					advance(hold)
					if err := e.Key(scan, false); err != nil {
						t.Fatal(err)
					}
					advance(gap)
				}
				ready := false
				e.Oracle.OnCall(oracle.Addr{Seg: 0x110, Off: 0x55a}, func(*oracle.Oracle) {
					if e.PAMLoaded && e.Tracker.loadSegment == 0x110 {
						ready = true
					}
				})
				advance(1000)
				press(2, 100, 100)
				press(2, 100, 100)
				advance(1000)
				press(1, 100, 1000)
				for n := 0; !ready && n < 2000; n++ {
					advance(10)
				}
				if !ready {
					t.Fatal("original main-menu marker absent")
				}
				press(0x50, 100, 300)
				press(0x1c, 100, 500)
				press(0x1c, 100, 1400)
				press(0x3b, 100, 700)
				e.Frame()
				press(1, 100, 400)
				press(0x3c, 100, 700)
				e.Frame()
				press(1, 100, 400)
				before := e.Frame()
				if e.researchRenderFault != nil || e.Tracker.VisibleScene != "map" {
					t.Fatal("ordinary prefix failed", e.Status())
				}
				beforePixels := append([]byte(nil), before.Pix...)
				nw, nh, nativeBefore := e.Oracle.Screen()
				nativeBefore = append([]byte(nil), nativeBefore...)
				code := []byte{0xb8, 0x13, 0x00, 0xcd, 0x10, 0xeb, 0xfe} // AX=0013; INT10; JMP $
				if kind == "unclassified-write" {
					// SEQ plane mask=0F; GC enable-set/reset=0, rotate=0,
					// write-mode=2, bit-mask=FF; write a distinct color to ES:0.
					code = []byte{0xba, 0xc4, 0x03, 0xb8, 0x02, 0x0f, 0xef,
						0xba, 0xce, 0x03, 0xb8, 0x01, 0x00, 0xef, 0xb8, 0x03, 0x00, 0xef,
						0xb8, 0x05, 0x02, 0xef, 0xb8, 0x08, 0xff, 0xef, 0xb8, 0x00, 0xa0, 0x8e, 0xc0,
						0x26, 0xc6, 0x06, 0x00, 0x00, (nativeBefore[0] + 1) & 15, 0xeb, 0xfe}
				}
				buffer := oracle.Addr{Seg: 0x8000, Off: 0}
				e.Oracle.WriteBytes(buffer, code)
				// The injected program loops instead of returning. CallNear's
				// synthetic stack word is recorded as controlled CPU preparation.
				e.Oracle.CallNear(buffer, 0, oracle.CallRegs{})
				start := e.Oracle.Steps()
				budget := uint64(100000)
				if control {
					budget = 50000
				}
				err = e.AdvanceCycles(budget)
				steps := e.Oracle.Steps() - start
				if steps == 0 || steps > 50000 {
					t.Fatal("did not stop at first bounded slice", steps)
				}
				if control {
					if err != nil || e.researchRenderFault != nil {
						t.Fatal("control unexpectedly rejected", err)
					}
				} else {
					var fault *OwnedRenderFault
					if !errors.As(err, &fault) || fault != e.researchRenderFault || fault.Phase != "pam" {
						t.Fatal("typed source failure absent", err)
					}
					want := "unclassified-video-write"
					if kind == "unhandled-mode" {
						want = "unhandled-display-mode"
					}
					if fault.Reason != want || fault.Step < start || fault.Step > e.Oracle.Steps() {
						t.Fatal("wrong fault metadata", fault)
					}
				}
				aw, ah, nativeAfter := e.Oracle.Screen()
				if nw == aw && nh == ah && bytes.Equal(nativeBefore, nativeAfter) {
					t.Fatal("injected guest operation did not alter native video")
				}
				state := observerGuestState(t, e)
				after := e.Frame()
				if !bytes.Equal(beforePixels, after.Pix) || !bytes.Equal(state, observerGuestState(t, e)) {
					t.Fatal("fault Frame lost complete scene or changed guest")
				}
				if !control {
					for _, run := range []func(uint64) error{e.Advance, e.AdvanceCycles} {
						if run(1) != e.researchRenderFault || !bytes.Equal(state, observerGuestState(t, e)) {
							t.Fatal("latched failure resumed guest")
						}
					}
				}
				if err := binary.Write(&pcm, binary.LittleEndian, e.RenderAudio()); err != nil {
					t.Fatal(err)
				}
				if err := os.WriteFile(filepath.Join(q, "audio.pcm"), pcm.Bytes(), 0644); err != nil {
					t.Fatal(err)
				}
				for name, im := range map[string]*image.RGBA{"before": before, "after": after} {
					f, err := os.OpenFile(filepath.Join(q, name+".png"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
					if err != nil {
						t.Fatal(err)
					}
					if err := png.Encode(f, im); err != nil {
						t.Fatal(err)
					}
					if err := f.Close(); err != nil {
						t.Fatal(err)
					}
				}
				if err := e.Oracle.SaveStateFile(filepath.Join(q, "final.state")); err != nil {
					t.Fatal(err)
				}
				report := map[string]any{"case": kind, "control": control, "fault": e.researchRenderFault, "injection_step": start, "final_step": e.Oracle.Steps(), "slice_steps": steps,
					"requested_cycles": budget, "first_slice_cycles": 50000, "controlled_code_hex": fmt.Sprintf("%x", code), "controlled_code_sha256": hash(code),
					"controlled_entry":   "8000:0000 via CallNear; synthetic near-return stack word; infinite guest loop",
					"native_before_size": []int{nw, nh}, "native_after_size": []int{aw, ah}, "native_before_sha256": hash(nativeBefore), "native_after_sha256": hash(nativeAfter),
					"frame_sha256": hash(after.Pix), "frame_pure": true, "method": "ordinary boot/new game/F1/F2 prefix, then controlled fault; not a natural player-path claim"}
				data, err := json.MarshalIndent(report, "", "  ")
				if err != nil {
					t.Fatal(err)
				}
				if err := os.WriteFile(filepath.Join(q, "receipt.json"), append(data, 10), 0644); err != nil {
					t.Fatal(err)
				}
			})
		}
	}
}

func TestResearchOwnedGuardDoesNotSwallowRuntimePanic(t *testing.T) {
	e := &Engine{}
	defer func() {
		if recover() != "unexpected defect" {
			t.Fatal("guard swallowed or replaced runtime panic")
		}
	}()
	e.researchGuardCall(func() { panic("unexpected defect") })
}
