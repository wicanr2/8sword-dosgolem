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
