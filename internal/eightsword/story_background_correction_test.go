package eightsword

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestStoryBackgroundCorrectionPairs(t *testing.T) {
	dir, base, root := os.Getenv("EIGHTSWORD_TEST_BLUE_CORRECTION_ASSETS"), os.Getenv("EIGHTSWORD_TEST_BLUE_CORRECTION_BASE"), os.Getenv("EIGHTSWORD_TEST_ORIG")
	if dir == "" || base == "" || root == "" {
		t.Skip("需要深藍修正候選、r55及原版")
	}
	e, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(e.Close)
	if !e.sourceEnabled || e.Story == nil || e.Story.BackgroundError != "" || e.Story.art == nil || hash(e.Story.art.Pix) != "649c76eb7afbabae56bbcc58cf6687d81697abf1cff631316a8288b8c7f94733" {
		t.Fatal(e.Status())
	}
	old, err := loadStoryBackground(base)
	if err != nil || old == nil || bytes.Equal(old.Pix, e.Story.art.Pix) {
		t.Fatal("新舊背景配對不符", err)
	}
	before := observerGuestState(t, e)
	for _, pair := range []struct{ assets, wrong string }{{dir, approvedStoryArtSHA}, {base, correctedStoryArtSHA}} {
		raw, err := os.ReadFile(filepath.Join(pair.assets, "story-background.json"))
		if err != nil {
			t.Fatal(err)
		}
		var m map[string]any
		if err := json.Unmarshal(raw, &m); err != nil {
			t.Fatal(err)
		}
		m["approved_sha256"] = pair.wrong
		raw, err = json.Marshal(m)
		if err != nil {
			t.Fatal(err)
		}
		out := t.TempDir()
		if err := os.WriteFile(filepath.Join(out, "story-background.json"), raw, 0644); err != nil {
			t.Fatal(err)
		}
		if art, err := loadStoryBackground(out); err == nil || art != nil {
			t.Fatal("深藍新舊SHA交叉混用被接受")
		}
	}
	if !bytes.Equal(before, observerGuestState(t, e)) {
		t.Fatal("背景配對核對改變客體")
	}
}
