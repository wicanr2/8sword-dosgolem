package eightsword

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"
)

func publisherEngine(t *testing.T) *Engine {
	t.Helper()
	assets := os.Getenv("EIGHTSWORD_TEST_PUBLISHER_ASSETS")
	if assets == "" {
		t.Skip("requires local publisher pack")
	}
	e := storyEngine(t, assets)
	if e.Publisher == nil || e.PublisherError != "" {
		t.Fatal(e.PublisherError)
	}
	storyAdvance(t, e, 1000)
	storyPress(t, e, 2)
	storyPress(t, e, 2)
	for i := 0; i < 800 && e.IntroStage() != "publisher-noto"; i++ {
		storyAdvance(t, e, 10)
		e.Frame()
	}
	if e.IntroStage() != "publisher-noto" || e.Publisher.Stats.Composed == 0 {
		t.Fatalf("publisher not composed: %+v", e.Status())
	}
	return e
}

func TestPublisherNormalFontsReadOnlyAndNaturalHandoff(t *testing.T) {
	e := publisherEngine(t)
	p := filepath.Join(t.TempDir(), "state")
	save := func() []byte {
		t.Helper()
		if err := e.Oracle.SaveStateFile(p); err != nil {
			t.Fatal(err)
		}
		b, err := os.ReadFile(p)
		if err != nil {
			t.Fatal(err)
		}
		return b
	}
	before := save()
	inputs := len(e.InputEvents)
	first := append([]byte(nil), e.Frame().Pix...)
	for _, id := range []string{"noto", "lishu", "caoshu", "noto"} {
		if err := e.SetFont(id); err != nil {
			t.Fatal(err)
		}
		frame := e.Frame()
		if e.IntroFrameStage(frame) != "publisher-noto" {
			t.Fatal("publisher frame marker missing")
		}
		e.HD = false
		native := e.Frame()
		e.HD = true
		if bytes.Equal(frame.Pix, native.Pix) {
			t.Fatal("wordmarks not painted")
		}
		for y := 0; y < 1200; y++ {
			for x := 0; x < 1920; x++ {
				_, _, _, alpha := e.Publisher.ink.At(x, y).RGBA()
				iconPixel := false
				if icon := e.Publisher.publisher.icon; icon != nil {
					_, _, _, a := icon.art.At(x, y).RGBA()
					iconPixel = a != 0 || icon.erase.AlphaAt(x, y).A != 0
				}
				if !iconPixel && e.Publisher.publisher.erase.AlphaAt(x, y).A == 0 && alpha == 0 {
					at := y*frame.Stride + x*4
					if !bytes.Equal(frame.Pix[at:at+4], native.Pix[at:at+4]) {
						t.Fatal("non-text pixel changed", x, y)
					}
				}
			}
		}
	}
	if !bytes.Equal(first, e.Frame().Pix) || !bytes.Equal(before, save()) || len(e.InputEvents) != inputs {
		t.Fatal("font change altered Noto restore, guest or DOS input")
	}
	broken := *e.Publisher
	broken.inDraw = true
	broken.start = e.Oracle.Cycles() - titleTransactionLimit - 1
	e.HD = false
	native := e.Frame()
	e.HD = true
	if broken.Compose(native) != native || broken.Stats.Timeouts != 1 || broken.Stage() != "" {
		t.Fatal("unbounded publisher transaction")
	}
	for i := 0; i < 2500 && e.Tracker.VisibleScene != "main-menu"; i++ {
		storyAdvance(t, e, 10)
		e.Frame()
	}
	if !e.PAMLoaded || !e.Publisher.Stats.Retired || e.Publisher.Stats.Starts != 1 || e.Publisher.Stats.Timeouts != 0 || len(e.Publisher.Stats.Errors) != 0 || e.Tracker.VisibleScene != "main-menu" || e.Tracker.Stats.RenderedGlyphs == 0 {
		t.Fatalf("publisher natural handoff: %+v", e.Status())
	}
}

func TestPublisherEscape(t *testing.T) {
	e := publisherEngine(t)
	storyPress(t, e, 1)
	for i := 0; i < 1000 && e.Tracker.VisibleScene != "main-menu"; i++ {
		storyAdvance(t, e, 10)
		e.Frame()
	}
	if !e.Publisher.Stats.Retired || e.Publisher.Stage() != "" || !e.PAMLoaded || e.Tracker.VisibleScene != "main-menu" {
		t.Fatalf("publisher Esc: %+v", e.Status())
	}
}

func TestPublisherCorruptLastPNGRejectsWholeGroup(t *testing.T) {
	assets := os.Getenv("EIGHTSWORD_TEST_PUBLISHER_ASSETS")
	if assets == "" {
		t.Skip("requires publisher pack")
	}
	root := os.Getenv("EIGHTSWORD_TEST_ORIG")
	bad := t.TempDir()
	entries, err := os.ReadDir(assets)
	if err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		b, err := os.ReadFile(filepath.Join(assets, entry.Name()))
		if err != nil {
			t.Fatal(err)
		}
		if entry.Name() == "publisher-caoshu.png" {
			b = append(b, 0)
		}
		if err = os.WriteFile(filepath.Join(bad, entry.Name()), b, 0600); err != nil {
			t.Fatal(err)
		}
	}
	e, err := Open(Options{Root: root, Assets: bad, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer e.Close()
	if e.Publisher != nil || e.PublisherError != "發行商字圖 publisher-caoshu.png SHA-256 不符" || !e.HD || e.Intro == nil || e.Story == nil || e.Captions == nil || e.Tracker.graphics == nil || e.Music.LoadError != "" || len(e.FontChoices()) != 3 {
		t.Fatalf("publisher failure affected other HD: %+v", e.Status())
	}
}
