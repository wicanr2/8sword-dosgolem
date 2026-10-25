package eightsword

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"
)

func storyEngine(t *testing.T, assets string) *Engine {
	t.Helper()
	root := os.Getenv("EIGHTSWORD_TEST_ORIG")
	if root == "" || assets == "" {
		t.Skip("requires original and real story font pack")
	}
	if _, err := os.Stat(filepath.Join(assets, "story.json")); err != nil {
		t.Skip("story assets not prepared")
	}
	e, err := openOverlayReference(Options{Root: root, Assets: assets, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(e.Close)
	if e.Story == nil || e.StoryError != "" {
		t.Fatal(e.StoryError)
	}
	e.EnableLiveClock(3000)
	return e
}

func storyAdvance(t *testing.T, e *Engine, ms int) {
	t.Helper()
	for i := 0; i < ms; i += 10 {
		if err := e.AdvanceCycles(30000); err != nil {
			t.Fatal(err)
		}
		e.RenderAudio()
	}
}
func storyPress(t *testing.T, e *Engine, scan byte) {
	t.Helper()
	if err := e.Key(scan, true); err != nil {
		t.Fatal(err)
	}
	storyAdvance(t, e, 100)
	if err := e.Key(scan, false); err != nil {
		t.Fatal(err)
	}
	storyAdvance(t, e, 100)
}
func storyBoot(t *testing.T, e *Engine) {
	t.Helper()
	storyAdvance(t, e, 1000)
	storyPress(t, e, 2)
	storyPress(t, e, 2)
	for i := 0; i < 1800 && e.Story.Stats.Glyphs < 5; i++ {
		storyAdvance(t, e, 10)
		e.Frame()
	}
	if e.Story.Stats.Glyphs < 5 || e.IntroStage() != "story-noto" {
		t.Fatalf("normal story missing: %+v", e.Status())
	}
}

func TestIntroStoryNaturalReadOnlyAndPages(t *testing.T) {
	e := storyEngine(t, os.Getenv("EIGHTSWORD_TEST_STORY_ASSETS"))
	storyBoot(t, e)
	state := func(name string) []byte {
		t.Helper()
		p := filepath.Join(t.TempDir(), name)
		if err := e.Oracle.SaveStateFile(p); err != nil {
			t.Fatal(err)
		}
		b, err := os.ReadFile(p)
		if err != nil {
			t.Fatal(err)
		}
		return b
	}
	before := state("before")
	hd := e.Frame()
	e.HD = false
	native := e.Frame()
	e.HD = true
	if bytes.Equal(hd.Pix, native.Pix) || e.IntroFrameStage(hd) != "story-noto" || e.IntroFrameStage(native) != "" {
		t.Fatal("story was not actually composed")
	}
	if !bytes.Equal(before, state("after")) {
		t.Fatal("Frame changed guest state")
	}
	broken := *e.Story
	broken.inText = true
	broken.start = e.Oracle.Cycles() - titleTransactionLimit - 1
	if broken.Compose(native) != native || broken.Stats.Timeouts != 1 || broken.Stage() != "" {
		t.Fatal("story transaction not bounded")
	}
	for i := 0; i < 1200 && e.Tracker.VisibleScene != "main-menu"; i++ {
		storyAdvance(t, e, 10)
		e.Frame()
	}
	s := e.Story.Stats
	if !s.Retired || s.Calls != 888 || s.Pages != 5 || s.Glyphs == 0 || s.Composed == 0 || s.Timeouts != 0 || len(s.Errors) != 0 ||
		e.IntroStage() != "" || !e.PAMLoaded || e.Tracker.VisibleScene != "main-menu" || e.Tracker.Stats.RenderedGlyphs == 0 {
		t.Fatalf("natural story/PAM path: %+v", e.Status())
	}
}

func TestIntroStoryEscape(t *testing.T) {
	e := storyEngine(t, os.Getenv("EIGHTSWORD_TEST_STORY_ASSETS"))
	storyBoot(t, e)
	storyPress(t, e, 1)
	for i := 0; i < 1000 && e.Tracker.VisibleScene != "main-menu"; i++ {
		storyAdvance(t, e, 10)
		e.Frame()
	}
	if !e.PAMLoaded || !e.Story.Stats.Retired || e.Story.Stats.Calls >= 888 || len(e.Story.Stats.Errors) != 0 || e.Tracker.VisibleScene != "main-menu" {
		t.Fatalf("normal story Esc: %+v", e.Status())
	}
}

func TestIntroStoryCorruptAtlasPreservesOtherHD(t *testing.T) {
	assets := os.Getenv("EIGHTSWORD_TEST_STORY_ASSETS")
	e := storyEngine(t, assets)
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
		if entry.Name() == "story-font.png" {
			b = append(b, 0)
		}
		if err = os.WriteFile(filepath.Join(bad, entry.Name()), b, 0600); err != nil {
			t.Fatal(err)
		}
	}
	fallback, err := openOverlayReference(Options{Root: os.Getenv("EIGHTSWORD_TEST_ORIG"), Assets: bad, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer fallback.Close()
	if fallback.Story != nil || fallback.StoryError != "故事字型圖片 SHA-256 不符" || !fallback.HD || fallback.Intro == nil || fallback.Tracker.graphics == nil || fallback.Music.LoadError != "" || len(fallback.Music.tracks) != len(e.Music.tracks) {
		t.Fatalf("story fault affected other HD: %+v", fallback.Status())
	}
}
