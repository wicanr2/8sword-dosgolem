package eightsword

import (
	"fmt"
	"image"
	"image/color"
	"os"
	"path/filepath"
	"testing"
)

func TestEndingEffectsLoadAndFallback(t *testing.T) {
	root, assets, _ := endingTestPaths(t)
	if _, err := os.Stat(filepath.Join(assets, "ending-effects.json")); err != nil {
		t.Skip("需要結局效果候選")
	}
	good, err := loadEndingAssets(assets, root)
	if err != nil || len(good.art.effects) != 11 || good.effectsError != "" {
		t.Fatal("結局效果未載入", err)
	}
	for _, name := range []string{"legacy", "manifest", "missing", "corrupt", "link", "source"} {
		t.Run(name, func(t *testing.T) {
			dir := t.TempDir()
			files := []string{"ending-effects.json"}
			for i := 0; i < 11; i++ {
				files = append(files, fmt.Sprintf("ending-effect-%02d.png", i))
			}
			for _, f := range files {
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
				if err := os.Remove(filepath.Join(dir, "ending-effects.json")); err != nil {
					t.Fatal(err)
				}
			case "manifest":
				if err := os.WriteFile(filepath.Join(dir, "ending-effects.json"), []byte("broken"), 0644); err != nil {
					t.Fatal(err)
				}
			case "missing", "link":
				if err := os.Remove(filepath.Join(dir, "ending-effect-10.png")); err != nil {
					t.Fatal(err)
				}
				if name == "link" {
					if err := os.Symlink(filepath.Join(assets, "ending-effect-10.png"), filepath.Join(dir, "ending-effect-10.png")); err != nil {
						t.Fatal(err)
					}
				}
			case "corrupt":
				if err := os.WriteFile(filepath.Join(dir, "ending-effect-10.png"), []byte("broken"), 0644); err != nil {
					t.Fatal(err)
				}
			case "source":
				selected = t.TempDir()
				if err := os.WriteFile(filepath.Join(selected, "END2.AY"), []byte("wrong"), 0644); err != nil {
					t.Fatal(err)
				}
			}
			im, err := loadEndingEffects(dir, selected)
			if im != nil || (err == nil) != (name == "legacy") {
				t.Fatal("失效圖像未回退", name, err)
			}
		})
	}
	if len(good.art.portraits) != 5 || good.art.end7 == nil || good.art.swords == nil || good.art.duel == nil || good.profile("lishu") == nil {
		t.Fatal("其他結局素材失效")
	}
}

func TestEndingEffectsLayering(t *testing.T) {
	red := image.NewNRGBA(image.Rect(0, 0, 480, 198))
	green := image.NewNRGBA(red.Bounds())
	red.SetNRGBA(0, 0, color.NRGBA{200, 0, 0, 128})
	green.SetNRGBA(0, 0, color.NRGBA{0, 200, 0, 128})
	art := endingArtSet{effects: map[string]image.Image{endingEffectsSources[0]: red, endingEffectsSources[1]: green}}
	first := &endingCommand{Kind: "bitmap", SourceSHA: endingEffectsSources[0], X: 40, Y: 100, W: 160, H: 33}
	next := *first
	next.SourceSHA = endingEffectsSources[1]
	page := &endingPage{ops: []*endingCommand{first, &next}}
	combined := renderEndingPage(page, endingPalette, art, &endingFontProfile{})
	if got := combined.RGBAAt(120, 600); got != (color.RGBA{49, 100, 0, 255}) {
		t.Fatal("不同效果未照序累積", got)
	}
	page.ops = append(page.ops, &next)
	repeated := renderEndingPage(page, endingPalette, art, &endingFontProfile{})
	if repeated.RGBAAt(120, 600) != combined.RGBAAt(120, 600) {
		t.Fatal("相同效果加深邊緣")
	}
	if repeated.RGBAAt(121, 601) != (color.RGBA{0, 0, 0, 255}) {
		t.Fatal("透明間隙失效")
	}
}
