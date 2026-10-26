package eightsword

import (
	"bytes"
	"errors"
	"image"
	"os"
	"path/filepath"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

// Native CPU execution is the control. Only the test removes host-call plans;
// both sides consume the same ordinary input and source rendering protocol.
func TestSourceRuntimeNormalAndControlledFault(t *testing.T) {
	root, assets := os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if root == "" || assets == "" {
		t.Skip("需設定原始資料與正式HD素材")
	}
	var engines [2]*Engine
	for i := range engines {
		e, err := Open(Options{Root: root, Assets: assets, Saves: filepath.Join(t.TempDir(), "scratch"), HD: true})
		if err != nil {
			t.Fatal(err)
		}
		t.Cleanup(e.Close)
		if !e.sourceEnabled || e.AssetError != "" || e.GraphicsError != "" {
			t.Fatal(e.Status())
		}
		e.Oracle.SetClock(12, 0, 0, 0)
		e.EnableLiveClock(3000)
		engines[i] = e
	}
	control := engines[0]
	pamInstall, pamFrame, pamClose := control.newSourcePAM()
	introInstall, introFrame, introClose := control.newSourceIntro()
	control.sourceInstall = func() { introInstall(); pamInstall() }
	control.sourceRender = func() *image.RGBA {
		if im := pamFrame(); im != nil {
			return im
		}
		return introFrame()
	}
	control.sourceClose = func() { introClose(); pamClose() }
	advance := func(ms int) {
		t.Helper()
		for elapsed := 0; elapsed < ms; elapsed += 10 {
			for _, e := range engines {
				if err := e.AdvanceCycles(30000); err != nil {
					t.Fatal(err)
				}
			}
			if !bytes.Equal(int16Bytes(control.RenderAudio()), int16Bytes(engines[1].RenderAudio())) {
				t.Fatal("native and direct PCM differ")
			}
			if elapsed%100 == 0 {
				for _, e := range engines {
					before := observerGuestState(t, e)
					e.Frame()
					if !bytes.Equal(before, observerGuestState(t, e)) {
						t.Fatal("Frame changed guest state")
					}
				}
			}
		}
		if !bytes.Equal(observerGuestState(t, control), observerGuestState(t, engines[1])) {
			t.Fatal("native and direct full guest state differ")
		}
		if !bytes.Equal(control.Frame().Pix, engines[1].Frame().Pix) {
			t.Fatal("native and direct source frames differ")
		}
	}
	press := func(scan byte, hold, gap int) {
		t.Helper()
		for _, e := range engines {
			if err := e.Key(scan, true); err != nil {
				t.Fatal(err)
			}
		}
		advance(hold)
		for _, e := range engines {
			if err := e.Key(scan, false); err != nil {
				t.Fatal(err)
			}
		}
		advance(gap)
	}
	ready := false
	control.Oracle.OnCall(oracle.Addr{Seg: 0x110, Off: 0x55a}, func(*oracle.Oracle) { ready = control.PAMLoaded })
	advance(1000)
	press(2, 100, 100)
	press(2, 100, 100)
	advance(1000)
	press(1, 100, 1000)
	for n := 0; !ready && n < 2000; n++ {
		advance(10)
	}
	if !ready {
		t.Fatal("ordinary main-menu input boundary not reached")
	}
	press(0x50, 100, 300)
	press(0x1c, 100, 500)
	press(0x1c, 100, 1400)
	press(0x3b, 100, 700)
	press(1, 100, 400)
	press(0x3c, 100, 700)
	press(1, 100, 400)
	e := engines[1]
	if e.Tracker.VisibleScene != "map" || e.sourceDirectCalls == 0 || control.sourceDirectCalls != 0 || e.sourceGlyphRows == 0 || e.sourceGlyphSteps == 0 || control.sourceGlyphRows != 0 {
		t.Fatal("representative route or direct plans absent", e.Status())
	}
	t.Logf("normal HD route Go glyph rows=%d skipped x86=%d", e.sourceGlyphRows, e.sourceGlyphSteps)
	if e.sourcePageClears == 0 || e.sourcePageCopies == 0 || control.sourcePageClears != 0 || control.sourcePageCopies != 0 {
		t.Fatal("normal Go clear/copy path absent", e.Status())
	}
	t.Logf("normal HD route Go page clears=%d copies=%d", e.sourcePageClears, e.sourcePageCopies)
	if e.sourceBitmapRows == 0 || e.sourceBitmapBytes == 0 || control.sourceBitmapRows != 0 {
		t.Fatal("normal Go planar row copies absent", e.Status())
	}
	t.Logf("normal HD route Go bitmap rows=%d plane bytes=%d", e.sourceBitmapRows, e.sourceBitmapBytes)
	// Controlled memory is authorized for presentation tests. This genuine INT10
	// changes to a mode unsupported by PAM; it is not a natural player route.
	before := append([]byte(nil), e.Frame().Pix...)
	entry := oracle.Addr{Seg: 0x8000, Off: 0}
	e.Oracle.WriteBytes(entry, []byte{0xb8, 0x13, 0x00, 0xcd, 0x10, 0xeb, 0xfe})
	e.Oracle.CallNear(entry, 0, oracle.CallRegs{})
	err := e.AdvanceCycles(100000)
	var fault *OwnedRenderFault
	if !errors.As(err, &fault) || fault.Reason != "unhandled-display-mode" {
		t.Fatal("missing typed fault", err)
	}
	state := observerGuestState(t, e)
	if !bytes.Equal(before, e.Frame().Pix) {
		t.Fatal("fault lost complete source frame")
	}
	if e.Advance(1) != fault || e.AdvanceCycles(1) != fault || !bytes.Equal(state, observerGuestState(t, e)) {
		t.Fatal("fault resumed guest")
	}
}

func int16Bytes(samples []int16) []byte {
	out := make([]byte, len(samples)*2)
	for i, sample := range samples {
		out[i*2], out[i*2+1] = byte(sample), byte(sample>>8)
	}
	return out
}
