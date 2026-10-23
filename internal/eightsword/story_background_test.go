package eightsword

import (
	"os"
	"path/filepath"
	"testing"
)

func TestStoryBackgroundNaturalReadOnlyAndPages(t *testing.T) {
	assets := os.Getenv("EIGHTSWORD_TEST_STORY_BACKGROUND_ASSETS")
	if assets == "" {
		t.Skip("requires approved local story background")
	}
	t.Setenv("EIGHTSWORD_TEST_STORY_ASSETS", assets)
	e := storyEngine(t, assets)
	if e.Story.art == nil || e.Story.BackgroundError != "" {
		t.Fatalf("background missing: %+v", e.Status())
	}
	TestIntroStoryNaturalReadOnlyAndPages(t)
}

func TestStoryBackgroundCorruptionPreservesTextAndOtherHD(t *testing.T) {
	assets := os.Getenv("EIGHTSWORD_TEST_STORY_BACKGROUND_ASSETS")
	if assets == "" {
		t.Skip("requires approved local story background")
	}
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
		if entry.Name() == "story-background.png" {
			b = append(b, 0)
		}
		if err = os.WriteFile(filepath.Join(bad, entry.Name()), b, 0600); err != nil {
			t.Fatal(err)
		}
	}
	fallback := storyEngine(t, bad)
	if fallback.Story.art != nil || fallback.Story.BackgroundError != "故事背景圖片 SHA-256 不符" || fallback.Intro == nil || fallback.Captions == nil || fallback.Tracker.graphics == nil || fallback.Music.LoadError != "" || len(fallback.Music.tracks) != len(e.Music.tracks) {
		t.Fatalf("background failure affected other HD: %+v", fallback.Status())
	}
	storyBoot(t, fallback)
	if fallback.IntroFrameStage(fallback.Frame()) != "story-noto" || fallback.Story.Stats.Glyphs == 0 {
		t.Fatal("Noto story lost on background failure")
	}
}
