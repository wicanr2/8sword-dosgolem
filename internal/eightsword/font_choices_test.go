package eightsword

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"
)

func TestFontChoicesReadOnlyStoryAndExactNotoRestore(t *testing.T) {
	assets := os.Getenv("EIGHTSWORD_TEST_FONT_CHOICES_ASSETS")
	if assets == "" {
		t.Skip("requires local font choices")
	}
	e := storyEngine(t, assets)
	if e.FontError != "" || len(e.FontChoices()) != 3 {
		t.Fatalf("choices: %+v", e.Status())
	}
	storyBoot(t, e)
	state := filepath.Join(t.TempDir(), "guest.state")
	if err := e.Oracle.SaveStateFile(state); err != nil {
		t.Fatal(err)
	}
	before, err := os.ReadFile(state)
	if err != nil {
		t.Fatal(err)
	}
	noto := append([]byte(nil), e.Frame().Pix...)
	inputs := len(e.InputEvents)
	for _, id := range []string{"lishu", "caoshu"} {
		if err = e.SetFont(id); err != nil {
			t.Fatal(err)
		}
		if e.FontID() != id || bytes.Equal(noto, e.Frame().Pix) {
			t.Fatal("font did not render", id)
		}
		if e.Story.font.Atlas != e.Assets.Atlas || e.Captions.font.Atlas != e.Assets.Atlas {
			t.Fatal("font selection split across presenters")
		}
	}
	if err = e.SetFont("unknown"); err == nil || e.FontID() != "caoshu" {
		t.Fatal("unknown choice was accepted")
	}
	if err = e.SetFont("noto"); err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(noto, e.Frame().Pix) {
		t.Fatal("Noto restore differs")
	}
	if err = e.Oracle.SaveStateFile(state); err != nil {
		t.Fatal(err)
	}
	after, err := os.ReadFile(state)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(before, after) || len(e.InputEvents) != inputs {
		t.Fatal("font switch changed guest or DOS input")
	}
	p := filepath.Join(t.TempDir(), "settings.json")
	if err = SaveFontPreference(p, "caoshu"); err != nil {
		t.Fatal(err)
	}
	if id, err := LoadFontPreference(p); err != nil || id != "caoshu" {
		t.Fatal("preference not restored", id, err)
	}
	if err = os.WriteFile(p, []byte(`{"schema":1,"font":"invalid"}`), 0600); err != nil {
		t.Fatal(err)
	}
	if id, err := LoadFontPreference(p); err == nil || id != "noto" {
		t.Fatal("invalid preference did not fall back")
	}
}

func TestFontChoiceCorruptOneKeepsNotoAndOtherChoice(t *testing.T) {
	assets := os.Getenv("EIGHTSWORD_TEST_FONT_CHOICES_ASSETS")
	if assets == "" {
		t.Skip("requires local font choices")
	}
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
		if entry.Name() == "font-choice-caoshu.png" {
			b = append(b, 0)
		}
		if err = os.WriteFile(filepath.Join(bad, entry.Name()), b, 0600); err != nil {
			t.Fatal(err)
		}
	}
	e := storyEngine(t, bad)
	if e.FontError == "" || len(e.FontChoices()) != 2 || e.FontID() != "noto" || e.Intro == nil || e.Captions == nil || e.Story.art == nil || e.Music.LoadError != "" || e.Tracker.graphics == nil {
		t.Fatalf("font failure affected HD: %+v", e.Status())
	}
	if e.SetFont("caoshu") == nil || e.FontID() != "noto" {
		t.Fatal("corrupt choice accepted")
	}
	if err = e.SetFont("lishu"); err != nil {
		t.Fatal(err)
	}
}
