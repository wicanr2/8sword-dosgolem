package eightsword

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"
)

func TestIntroCaptionsNormalPagesReadOnlyAndRetire(t *testing.T) {
	e := storyEngine(t, os.Getenv("EIGHTSWORD_TEST_STORY_ASSETS"))
	if e.Captions == nil {
		t.Fatal("missing caption presenter")
	}
	storyAdvance(t, e, 1000)
	storyPress(t, e, 2)
	storyPress(t, e, 2)
	for i := 0; i < 220 && e.Captions.Stats.Composed == 0; i++ {
		storyAdvance(t, e, 100)
		e.Frame()
	}
	if e.Captions.Stats.Composed == 0 || e.IntroStage() != "captions-noto" {
		t.Fatalf("normal visible caption missing: %+v", e.Status())
	}
	state := func() []byte {
		t.Helper()
		p := filepath.Join(t.TempDir(), "snapshot")
		if err := e.Oracle.SaveStateFile(p); err != nil {
			t.Fatal(err)
		}
		b, err := os.ReadFile(p)
		if err != nil {
			t.Fatal(err)
		}
		return b
	}
	before := state()
	hd := e.Frame()
	e.HD = false
	native := e.Frame()
	e.HD = true
	if bytes.Equal(hd.Pix, native.Pix) || e.IntroFrameStage(hd) != "captions-noto" || e.Captions.FrameSource(hd) != 0x42 || e.IntroFrameStage(native) != "" {
		t.Fatal("caption not actually composed")
	}
	if !bytes.Equal(before, state()) {
		t.Fatal("caption Frame changed guest state")
	}
	broken := *e.Captions
	broken.tx = []captionTransaction{{0x583d, e.Oracle.Cycles() - titleTransactionLimit - 1}}
	if broken.Compose(native) != native || broken.Stats.Timeouts != 1 || broken.Stage() != "" {
		t.Fatal("caption transaction not bounded")
	}
	for i := 0; i < 300 && e.Tracker.VisibleScene != "main-menu"; i++ {
		storyAdvance(t, e, 100)
		e.Frame()
	}
	s := e.Captions.Stats
	if !s.Retired || s.Requests != 5 || len(s.VisibleSources) != 4 || s.Timeouts != 0 || len(s.Errors) != 0 || e.Tracker.VisibleScene != "main-menu" || e.Tracker.Stats.RenderedGlyphs == 0 || e.Story.Stats.Calls != 888 || len(e.Story.Stats.Errors) != 0 {
		t.Fatalf("captions/story/PAM path: %+v", e.Status())
	}
}

func TestIntroCaptionsEscape(t *testing.T) {
	e := storyEngine(t, os.Getenv("EIGHTSWORD_TEST_STORY_ASSETS"))
	storyAdvance(t, e, 1000)
	storyPress(t, e, 2)
	storyPress(t, e, 2)
	for i := 0; i < 220 && e.Captions.Stats.Composed == 0; i++ {
		storyAdvance(t, e, 100)
		e.Frame()
	}
	if e.Captions.Stats.Composed == 0 {
		t.Fatal("no actual caption before Esc")
	}
	storyPress(t, e, 1)
	for i := 0; i < 150 && e.Tracker.VisibleScene != "main-menu"; i++ {
		storyAdvance(t, e, 100)
		e.Frame()
	}
	if !e.PAMLoaded || !e.Captions.Stats.Retired || e.Captions.Stats.Requests >= 5 || len(e.Captions.Stats.Errors) != 0 || e.Story.Stats.Started || e.Tracker.VisibleScene != "main-menu" {
		t.Fatalf("normal caption Esc failed: %+v", e.Status())
	}
}

func TestIntroCaptionsTitleEscapeBeforeMuseum(t *testing.T) {
	e := storyEngine(t, os.Getenv("EIGHTSWORD_TEST_STORY_ASSETS"))
	storyAdvance(t, e, 1000)
	storyPress(t, e, 2)
	storyPress(t, e, 2)
	for i := 0; i < 100 && e.IntroStage() != "title-noto"; i++ {
		storyAdvance(t, e, 100)
		e.Frame()
	}
	if e.IntroStage() != "title-noto" || e.Captions.Stats.Started {
		t.Fatal("not the normal title before museum")
	}
	storyPress(t, e, 1)
	for i := 0; i < 150 && e.Tracker.VisibleScene != "main-menu"; i++ {
		storyAdvance(t, e, 100)
		e.Frame()
	}
	if !e.PAMLoaded || !e.Captions.Stats.Retired || e.Captions.Stats.Started || e.Captions.Stats.Requests != 0 || len(e.Captions.Stats.Errors) != 0 || e.Tracker.VisibleScene != "main-menu" || e.Tracker.Stats.RenderedGlyphs == 0 {
		t.Fatalf("early title Esc left old caption hooks live: %+v", e.Status())
	}
}
