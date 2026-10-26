package eightsword

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"
)

func TestEndingPortraitLoadAndAtomicFallback(t *testing.T) {
	root, assets, _ := endingTestPaths(t)
	if _, err := os.Stat(filepath.Join(assets, "ending-portrait.json")); err != nil {
		t.Skip("END5 candidate not supplied")
	}
	good, err := loadEndingAssets(assets, root)
	if err != nil || len(good.art.portraits) != 5 || good.portraitError != "" {
		t.Fatalf("END5 group unavailable: %v", err)
	}
	for _, name := range []string{"legacy", "manifest", "missing-base", "broken-eye", "linked-mouth", "wrong-source"} {
		t.Run(name, func(t *testing.T) {
			dir := t.TempDir()
			files := []string{"ending.json", "ending-portrait.json"}
			for filename := range good.manifest.Files {
				files = append(files, filename)
			}
			for i := 0; i < 5; i++ {
				files = append(files, fmt.Sprintf("ending-end5-%d.png", i))
			}
			for _, filename := range files {
				data, err := os.ReadFile(filepath.Join(assets, filename))
				if err != nil {
					t.Fatal(err)
				}
				if err = os.WriteFile(filepath.Join(dir, filename), data, 0644); err != nil {
					t.Fatal(err)
				}
			}
			remove := func(filename string) {
				t.Helper()
				if err := os.Remove(filepath.Join(dir, filename)); err != nil {
					t.Fatal(err)
				}
			}
			write := func(filename string) {
				t.Helper()
				if err := os.WriteFile(filepath.Join(dir, filename), []byte("damaged END5 fixture"), 0644); err != nil {
					t.Fatal(err)
				}
			}
			selectedRoot := root
			switch name {
			case "legacy":
				remove("ending-portrait.json")
			case "manifest":
				write("ending-portrait.json")
			case "missing-base":
				remove("ending-end5-0.png")
			case "broken-eye":
				write("ending-end5-2.png")
			case "linked-mouth":
				remove("ending-end5-4.png")
				if err := os.Symlink(filepath.Join(assets, "ending-end5-4.png"), filepath.Join(dir, "ending-end5-4.png")); err != nil {
					t.Fatal(err)
				}
			case "wrong-source":
				selectedRoot = t.TempDir()
				if err := os.WriteFile(filepath.Join(selectedRoot, "END5.AY"), []byte("wrong original END5"), 0644); err != nil {
					t.Fatal(err)
				}
			}
			textures, loadErr := loadEndingPortrait(dir, selectedRoot)
			if len(textures) != 0 || (name == "legacy") != (loadErr == nil) {
				t.Fatalf("partial END5 group leaked: %s %d %v", name, len(textures), loadErr)
			}
			if name != "wrong-source" {
				group, err := loadEndingAssets(dir, root)
				if err != nil {
					t.Fatal(err)
				}
				if len(group.art.portraits) != 0 || group.art.end7 == nil || group.profile("noto") == nil || group.art.titles["lishu"] == nil {
					t.Fatal("portrait fault damaged independent ending groups")
				}
				if (name == "legacy") != (group.portraitError == "") {
					t.Fatal("portrait failure diagnostic absent")
				}
			}
		})
	}
}
