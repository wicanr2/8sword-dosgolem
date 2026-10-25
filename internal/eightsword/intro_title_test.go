package eightsword

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"
)

func introAssets(t *testing.T) (string, string) {
	t.Helper()
	root, assets := os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_INTRO_ASSETS")
	if root == "" || assets == "" {
		t.Skip("requires original PREDELLA/TIT2 and real Noto intro pack")
	}
	return root, assets
}

func TestIntroTitleNormalSourceReadOnlyAndEscape(t *testing.T) {
	root, assets := introAssets(t)
	e, err := openOverlayReference(Options{Root: root, Assets: assets, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer e.Close()
	if e.Intro == nil || e.IntroError != "" {
		t.Fatal(e.IntroError)
	}
	e.EnableLiveClock(3000)
	advance := func(ms int) {
		t.Helper()
		for n := 0; n < ms; n += 10 {
			if err := e.AdvanceCycles(30000); err != nil {
				t.Fatal(err)
			}
			e.RenderAudio()
		}
	}
	press := func(scan byte) {
		t.Helper()
		if err := e.Key(scan, true); err != nil {
			t.Fatal(err)
		}
		advance(100)
		if err := e.Key(scan, false); err != nil {
			t.Fatal(err)
		}
		advance(100)
	}
	advance(1000)
	press(2)
	press(2)
	for i := 0; i < 800 && e.IntroStage() != "title-noto"; i++ {
		advance(10)
		e.Frame()
	}
	if e.IntroStage() != "title-noto" || e.Intro.Stats.Starts != 1 || !e.Intro.Stats.Bound {
		t.Fatalf("normal title source not observed: %+v", e.Status())
	}
	state := func(name string) []byte {
		t.Helper()
		p := filepath.Join(t.TempDir(), name)
		if err := e.Oracle.SaveStateFile(p); err != nil {
			t.Fatal(err)
		}
		raw, err := os.ReadFile(p)
		if err != nil {
			t.Fatal(err)
		}
		return raw
	}
	before := state("before")
	hd := e.Frame()
	if e.IntroFrameStage(hd) != "title-noto" || e.Intro.Stats.Composed == 0 {
		t.Fatal("frame marker was not derived from actual composition")
	}
	e.HD = false
	native := e.Frame()
	e.HD = true
	if e.IntroFrameStage(native) != "" {
		t.Fatal("native frame mislabeled as Noto")
	}
	if bytes.Equal(hd.Pix, native.Pix) {
		t.Fatalf("title replacement missing: %+v", e.Status())
	}
	after := state("after")
	if !bytes.Equal(before, after) {
		at := 0
		for at < min(len(before), len(after)) && before[at] == after[at] {
			at++
		}
		t.Fatalf("guest state changed: before=%s after=%s first-byte=%d lengths=%d/%d", hash(before), hash(after), at, len(before), len(after))
	}
	// A lost return is a host presentation fault, never an unbounded wait.
	broken := *e.Intro
	broken.inDraw, broken.start = true, e.Oracle.Cycles()-titleTransactionLimit-1
	if broken.Compose(native) != native || broken.Stats.Timeouts != 1 || broken.Stage() != "" {
		t.Fatal("stale title transaction did not return to native")
	}
	if !bytes.Equal(before, state("after-timeout")) {
		t.Fatal("timeout fallback changed guest state")
	}
	press(1)
	for i := 0; i < 800 && e.Tracker.VisibleScene != "main-menu"; i++ {
		advance(10)
		e.Frame()
	}
	if !e.PAMLoaded || !e.Intro.Stats.Retired || e.IntroStage() != "" || e.Intro.Stats.Timeouts != 0 {
		t.Fatalf("normal Esc/handoff left an intro hook active: %+v", e.Status())
	}
	if e.Tracker.VisibleScene != "main-menu" || e.Tracker.Stats.PixelWrites == 0 || e.Tracker.Stats.RenderedGlyphs == 0 {
		t.Fatalf("intro callback displaced PAM presentation: %+v", e.Status())
	}
}

func TestIntroTitleCorruptPNGPreservesOtherHD(t *testing.T) {
	root, assets := introAssets(t)
	bad := t.TempDir()
	entries, err := os.ReadDir(assets)
	if err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		if entry.IsDir() {
			t.Fatal("unexpected nested asset")
		}
		data, err := os.ReadFile(filepath.Join(assets, entry.Name()))
		if err != nil {
			t.Fatal(err)
		}
		if entry.Name() == "intro-title-noto-r1.png" {
			data = append(data, 0)
		}
		if err := os.WriteFile(filepath.Join(bad, entry.Name()), data, 0600); err != nil {
			t.Fatal(err)
		}
	}
	e, err := openOverlayReference(Options{Root: root, Assets: bad, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer e.Close()
	if e.Intro != nil || e.IntroError != "HD 片頭圖片 SHA-256 不符" || !e.HD || e.AssetError != "" || e.GraphicsError != "" ||
		e.Tracker == nil || e.Tracker.graphics == nil || e.Music.LoadError != "" || len(e.Music.tracks) != 1 {
		t.Fatalf("intro fault affected another HD group: %+v", e.Status())
	}
}
