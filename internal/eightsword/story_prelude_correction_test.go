package eightsword

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestStoryPreludeCorrectionPairs(t *testing.T) {
	dir, base, root := os.Getenv("EIGHTSWORD_TEST_PRELUDE_CORRECTION_ASSETS"), os.Getenv("EIGHTSWORD_TEST_PRELUDE_CORRECTION_BASE"), os.Getenv("EIGHTSWORD_TEST_ORIG")
	if dir == "" || base == "" || root == "" {
		t.Skip("需要014修正候選、r54與原版")
	}
	open := func(assets string) *Engine {
		e, err := Open(Options{Root: root, Assets: assets, Saves: t.TempDir(), HD: true})
		if err != nil {
			t.Fatal(err)
		}
		t.Cleanup(e.Close)
		if !e.sourceEnabled || e.Story == nil || e.Story.PreludeError != "" || e.Story.prelude == nil {
			t.Fatal(e.Status())
		}
		return e
	}
	e, old := open(dir), open(base)
	if hash(e.Story.prelude.art.Pix) != "972297efc356d2c7e8f44f4261a554beb5e412cabae897753ea38fca47b3ac34" || bytes.Equal(e.Story.prelude.art.Pix, old.Story.prelude.art.Pix) {
		t.Fatal("新圖未載入")
	}
	before := observerGuestState(t, e)
	for _, pair := range []struct{ assets, wrong string }{{dir, preludeApprovedSHA}, {base, preludeCorrectedSHA}} {
		raw, err := os.ReadFile(filepath.Join(pair.assets, "story-prelude.json"))
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
		if err := os.WriteFile(filepath.Join(out, "story-prelude.json"), raw, 0644); err != nil {
			t.Fatal(err)
		}
		if art, err := loadStoryPrelude(e.Story, out); err == nil || art != nil {
			t.Fatal("新舊SHA交叉配對被接受")
		}
	}
	if !bytes.Equal(before, observerGuestState(t, e)) {
		t.Fatal("配對核對改變客體")
	}
}

func TestStoryPreludePosterPosePairs(t *testing.T) {
	dir, base, root := os.Getenv("EIGHTSWORD_TEST_POSTER_POSE_ASSETS"), os.Getenv("EIGHTSWORD_TEST_POSTER_POSE_BASE"), os.Getenv("EIGHTSWORD_TEST_ORIG")
	if dir == "" || base == "" || root == "" {
		t.Skip("需要014海報姿態候選、r58與原版")
	}
	e, err := Open(Options{Root: root, Assets: dir, Saves: t.TempDir(), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	defer e.Close()
	if e.Story == nil || e.Story.prelude == nil || e.Story.PreludeError != "" {
		t.Fatal(e.Status())
	}
	if hash(e.Story.prelude.art.Pix) != "5de42d546a5065646c2c28075d8bda2c06808d206b08a9df24fb3730f593f729" {
		t.Fatal("海報姿態圖未載入")
	}
	before := observerGuestState(t, e)
	old, err := loadStoryPrelude(e.Story, base)
	if err != nil || old == nil || hash(old.art.Pix) != "972297efc356d2c7e8f44f4261a554beb5e412cabae897753ea38fca47b3ac34" {
		t.Fatal("舊版配對失效", err)
	}
	for _, pair := range []struct{ assets, wrong string }{{dir, preludeCorrectedSHA}, {base, preludePosterPoseSHA}, {dir, preludePosterPoseSHA}} {
		raw, err := os.ReadFile(filepath.Join(pair.assets, "story-prelude.json"))
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
		if err := os.WriteFile(filepath.Join(out, "story-prelude.json"), raw, 0644); err != nil {
			t.Fatal(err)
		}
		if art, err := loadStoryPrelude(e.Story, out); err == nil || art != nil {
			t.Fatal("交叉配對或缺圖被接受")
		}
	}
	if !bytes.Equal(before, observerGuestState(t, e)) {
		t.Fatal("載入檢查改變客體")
	}
}
