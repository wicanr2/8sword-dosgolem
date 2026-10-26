package eightsword

import (
	"os"
	"path/filepath"
	"testing"
)

func TestEndingDuelLoadAndFallback(t *testing.T) {
	root, assets, _ := endingTestPaths(t)
	if _, err := os.Stat(filepath.Join(assets, "ending-duel.json")); err != nil {
		t.Skip("需要對峙人物候選")
	}
	good, err := loadEndingAssets(assets, root)
	if err != nil || good.art.duel == nil || good.duelError != "" {
		t.Fatal("對峙人物未載入", err)
	}
	for _, name := range []string{"legacy", "manifest", "missing", "corrupt", "link", "source"} {
		t.Run(name, func(t *testing.T) {
			dir := t.TempDir()
			for _, f := range []string{"ending-duel.json", "ending-duel.png"} {
				data, err := os.ReadFile(filepath.Join(assets, f))
				if err != nil {
					t.Fatal(err)
				}
				if err := os.WriteFile(filepath.Join(dir, f), data, 0644); err != nil {
					t.Fatal(err)
				}
			}
			selected := root
			switch name {
			case "legacy":
				if err := os.Remove(filepath.Join(dir, "ending-duel.json")); err != nil {
					t.Fatal(err)
				}
			case "manifest":
				if err := os.WriteFile(filepath.Join(dir, "ending-duel.json"), []byte("broken"), 0644); err != nil {
					t.Fatal(err)
				}
			case "missing", "link":
				if err := os.Remove(filepath.Join(dir, "ending-duel.png")); err != nil {
					t.Fatal(err)
				}
				if name == "link" {
					if err := os.Symlink(filepath.Join(assets, "ending-duel.png"), filepath.Join(dir, "ending-duel.png")); err != nil {
						t.Fatal(err)
					}
				}
			case "corrupt":
				if err := os.WriteFile(filepath.Join(dir, "ending-duel.png"), []byte("broken"), 0644); err != nil {
					t.Fatal(err)
				}
			case "source":
				selected = t.TempDir()
				if err := os.WriteFile(filepath.Join(selected, "END1.AY"), []byte("wrong"), 0644); err != nil {
					t.Fatal(err)
				}
			}
			im, err := loadEndingDuel(dir, selected)
			if im != nil || (err == nil) != (name == "legacy") {
				t.Fatal("失效圖像未回退", name, err)
			}
		})
	}
	if len(good.art.portraits) != 5 || good.art.end7 == nil || good.art.swords == nil || good.profile("lishu") == nil {
		t.Fatal("其他結局素材失效")
	}
}
