package eightsword

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestMOELishuPublisherSourceGuard(t *testing.T) {
	assets := os.Getenv("EIGHTSWORD_TEST_MOE_ASSETS")
	if assets == "" {
		t.Skip("需要教育部隸書素材")
	}
	e := storyEngine(t, assets)
	if e.FontError != "" || e.PublisherError != "" || len(e.FontChoices()) != 3 {
		t.Fatal(e.FontError, e.PublisherError)
	}
	if err := e.SetFont("lishu"); err != nil || e.FontName() != "教育部隸書" {
		t.Fatal(e.FontName(), err)
	}
	c := e.FontChoices()[1]
	if c.SourceSHA != moeLishuSHA || c.FallbackCount != 135 {
		t.Fatal(c)
	}
	e.Close()
	tmp := t.TempDir()
	for _, entry := range mustReadDir(t, assets) {
		b, err := os.ReadFile(filepath.Join(assets, entry.Name()))
		if err != nil {
			t.Fatal(err)
		}
		if entry.Name() == "publisher.json" {
			var m map[string]any
			if err = json.Unmarshal(b, &m); err != nil {
				t.Fatal(err)
			}
			for _, row := range m["words"].([]any) {
				p := row.(map[string]any)
				if p["id"] == "lishu" {
					delete(p, "font_source_sha256")
				}
			}
			b, _ = json.Marshal(m)
		}
		if err = os.WriteFile(filepath.Join(tmp, entry.Name()), b, 0600); err != nil {
			t.Fatal(err)
		}
	}
	mixed := storyEngine(t, tmp)
	if !strings.Contains(mixed.FontError, "來源不一致") || len(mixed.FontChoices()) != 2 || mixed.SetFont("lishu") == nil || mixed.PublisherError != "" {
		t.Fatal("混用舊發行商來源未拒用", mixed.FontError, mixed.PublisherError)
	}
	if validChoiceSource("noto", moeLishuSHA) || validChoiceSource("unknown", "") || validChoiceSource("caoshu", moeLishuSHA) {
		t.Fatal("字型 ID 衛式擴大")
	}
}
func mustReadDir(t *testing.T, p string) []os.DirEntry {
	t.Helper()
	entries, err := os.ReadDir(p)
	if err != nil {
		t.Fatal(err)
	}
	return entries
}
