package eightsword

import (
	"bytes"
	"image"
	"image/color"
	"os"
	"path/filepath"
	"testing"
)

func TestEndingRingLoadAndFallback(t *testing.T) {
	root, assets, _ := endingTestPaths(t)
	if _, err := os.Stat(filepath.Join(assets, "ending-ring.json")); err != nil {
		t.Skip("需要紅金光環候選")
	}
	good, err := loadEndingAssets(assets, root)
	if err != nil || good.art.ring == nil || good.ringError != "" {
		t.Fatal("紅金光環未載入", err)
	}
	for _, name := range []string{"legacy", "manifest", "missing", "corrupt", "link", "source"} {
		t.Run(name, func(t *testing.T) {
			dir := t.TempDir()
			for _, f := range []string{"ending-ring.json", "ending-ring.png"} {
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
				if err := os.Remove(filepath.Join(dir, "ending-ring.json")); err != nil {
					t.Fatal(err)
				}
			case "manifest":
				if err := os.WriteFile(filepath.Join(dir, "ending-ring.json"), []byte("broken"), 0644); err != nil {
					t.Fatal(err)
				}
			case "missing", "link":
				if err := os.Remove(filepath.Join(dir, "ending-ring.png")); err != nil {
					t.Fatal(err)
				}
				if name == "link" {
					if err := os.Symlink(filepath.Join(assets, "ending-ring.png"), filepath.Join(dir, "ending-ring.png")); err != nil {
						t.Fatal(err)
					}
				}
			case "corrupt":
				if err := os.WriteFile(filepath.Join(dir, "ending-ring.png"), []byte("broken"), 0644); err != nil {
					t.Fatal(err)
				}
			case "source":
				selected = t.TempDir()
				if err := os.WriteFile(filepath.Join(selected, "END3.AY"), []byte("wrong"), 0644); err != nil {
					t.Fatal(err)
				}
			}
			im, err := loadEndingRing(dir, selected)
			if im != nil || (err == nil) != (name == "legacy") {
				t.Fatal("失效圖像未回退", name, err)
			}
		})
	}
	if len(good.art.pair) != 4 || len(good.art.portraits) != 5 || good.art.end7 == nil || good.profile("lishu") == nil {
		t.Fatal("其他結局素材失效")
	}
}

func TestEndingRingTransparentReplay(t *testing.T) {
	texture := image.NewNRGBA(image.Rect(0, 0, 696, 630))
	texture.SetNRGBA(0, 0, color.NRGBA{200, 100, 40, 128})
	art := endingArtSet{ring: texture}
	c := &endingCommand{Kind: "bitmap", SourceSHA: endingRingSource, X: 40, Y: 20, W: 232, H: 105}
	other := &endingCommand{Kind: "bitmap", X: 300, Y: 20, W: 1, H: 1, Pixels: []byte{2}, Mask: []byte{1}}
	p := &endingPage{ops: []*endingCommand{c}}
	first := renderEndingPage(p, endingPalette, art, &endingFontProfile{})
	p.ops = []*endingCommand{c, other, c}
	repeated := renderEndingPage(p, endingPalette, art, &endingFontProfile{})
	if first.RGBAAt(120, 120) != repeated.RGBAAt(120, 120) {
		t.Fatal("重複來源加深半透明邊緣")
	}
	if repeated.RGBAAt(121, 121) != (color.RGBA{0, 0, 0, 255}) {
		t.Fatal("透明留白被填滿")
	}
	overlap := *other
	overlap.X = 40
	p.ops = []*endingCommand{c, &overlap, c}
	if endingSwordsRepeat(p.ops, 2) {
		t.Fatal("相交寫入後仍略過")
	}
	changed := renderEndingPage(p, endingPalette, art, &endingFontProfile{})
	if bytes.Equal(changed.Pix, repeated.Pix) || changed.RGBAAt(120, 120) == repeated.RGBAAt(120, 120) {
		t.Fatal("相交後未重繪")
	}
}
