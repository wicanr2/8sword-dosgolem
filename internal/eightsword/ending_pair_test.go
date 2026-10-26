package eightsword

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"testing"
)

func TestEndingPairLoadAndFallback(t *testing.T) {
	root, assets, _ := endingTestPaths(t)
	good, err := loadEndingAssets(assets, root)
	if err != nil || len(good.art.pair) != 4 || good.pairError != "" {
		t.Fatal("雙人材質未完整載入", err)
	}
	for _, name := range []string{"legacy", "manifest", "missing-first", "missing-last", "corrupt", "link", "source"} {
		t.Run(name, func(t *testing.T) {
			dir := t.TempDir()
			for _, file := range []string{"ending-pair.json", "ending-pair-01.png", "ending-pair-02.png", "ending-pair-03.png", "ending-pair-04.png"} {
				data, err := os.ReadFile(filepath.Join(assets, file))
				if err != nil {
					t.Fatal(err)
				}
				if err = os.WriteFile(filepath.Join(dir, file), data, 0644); err != nil {
					t.Fatal(err)
				}
			}
			selected := root
			file := "ending-pair-01.png"
			switch name {
			case "legacy":
				if err := os.Remove(filepath.Join(dir, "ending-pair.json")); err != nil {
					t.Fatal(err)
				}
			case "manifest":
				if err := os.WriteFile(filepath.Join(dir, "ending-pair.json"), []byte("broken"), 0644); err != nil {
					t.Fatal(err)
				}
			case "missing-first", "missing-last", "link":
				if name == "missing-last" {
					file = "ending-pair-04.png"
				}
				if err := os.Remove(filepath.Join(dir, file)); err != nil {
					t.Fatal(err)
				}
				if name == "link" {
					if err := os.Symlink(filepath.Join(assets, file), filepath.Join(dir, file)); err != nil {
						t.Fatal(err)
					}
				}
			case "corrupt":
				if err := os.WriteFile(filepath.Join(dir, file), []byte("broken"), 0644); err != nil {
					t.Fatal(err)
				}
			case "source":
				selected = t.TempDir()
				if err := os.WriteFile(filepath.Join(selected, "END6.AY"), []byte("wrong"), 0644); err != nil {
					t.Fatal(err)
				}
			}
			textures, err := loadEndingPair(dir, selected)
			if textures != nil || (err == nil) != (name == "legacy") {
				t.Fatal("雙人材質未整組回退", name, err)
			}
		})
	}
	if good.art.end7 == nil || len(good.art.portraits) != 5 || len(good.art.effects) != 11 || good.art.swords == nil || good.art.duel == nil {
		t.Fatal("其他結局素材失效")
	}
}

func TestEndingPairSourceMasksAndReplay(t *testing.T) {
	root, assets, _ := endingTestPaths(t)
	project := os.Getenv("EIGHTSWORD_GLYPH_PROJECT")
	if project == "" {
		t.Skip("需唯讀專案")
	}
	a, err := loadEndingAssets(assets, root)
	if err != nil || len(a.art.pair) != 4 {
		t.Fatal(err)
	}
	for i, source := range endingPairSources {
		t.Run(fmt.Sprint(i+1), func(t *testing.T) {
			raw, err := os.ReadFile(filepath.Join(project, "workplace/probe-20261023/graphics-first/ending-hd-r1", fmt.Sprintf("end6-ay-%02d.bin", i+1)))
			if err != nil || hash(raw) != source {
				t.Fatal("真實END6來源不符", err)
			}
			w, h := int(binary.LittleEndian.Uint16(raw))*8, int(binary.LittleEndian.Uint16(raw[2:]))
			pixels, mask := decodeEndingBitmap(raw, 6, w, h)
			p := newEndingScene().pages[0]
			base := &endingCommand{Kind: "bitmap", W: 640, H: 200, Pixels: make([]byte, 640*200), Mask: make([]byte, 640*200), SourceSHA: "fixture-red", SourceFile: "CONTROLLED"}
			for at := range base.Pixels {
				base.Pixels[at] = 12
				base.Mask[at] = 1
			}
			p.apply(base)
			c := &endingCommand{Kind: "bitmap", X: 16, Y: 24, W: w, H: h, Pixels: pixels, Mask: mask, SourceSHA: source, SourceFile: "END6.AY"}
			p.apply(c)
			before := append([]byte(nil), p.native...)
			oldArt := a.art
			oldArt.pair = nil
			original := renderEndingPage(p, endingPalette, oldArt, a.profile("noto"))
			hd := renderEndingPage(p, endingPalette, a.art, a.profile("noto"))
			if bytes.Equal(original.Pix, hd.Pix) || !bytes.Equal(before, p.native) {
				t.Fatal("雙人未替換或修改來源")
			}
			if !bytes.Equal(renderEndingPage(p, endingPalette, oldArt, nil).Pix, renderEndingPage(p, endingPalette, a.art, nil).Pix) {
				t.Fatal("原生核對混入HD")
			}
			transparentArt := a.art
			transparentArt.pair = map[string]image.Image{source: image.NewNRGBA(image.Rect(0, 0, 408, 300))}
			transparent := renderEndingPage(p, endingPalette, transparentArt, a.profile("noto"))
			black, untouched := 0, 0
			for at, v := range pixels {
				x, y := (c.X+at%w)*3, (c.Y+at/w)*6
				got := transparent.RGBAAt(x, y)
				if mask[at] != 0 && v == 0 {
					black++
					if got.R != 0 || got.G != 0 || got.B != 0 {
						t.Fatal("原黑色寫入被略過")
					}
				} else {
					untouched++
					if got.R != 255 || got.G != 85 || got.B != 85 {
						t.Fatal("透明材質改變底色")
					}
				}
			}
			if black != []int{7, 14, 10, 4}[i] || untouched == 0 {
				t.Fatal("來源遮罩範圍不符", black, untouched)
			}
			if out := os.Getenv("EIGHTSWORD_TEST_PAIR_OUT"); out != "" {
				for suffix, frame := range map[string]*image.RGBA{"hd": hd, "original": original} {
					f, err := os.Create(filepath.Join(out, fmt.Sprintf("pair-%02d-%s.png", i+1, suffix)))
					if err != nil {
						t.Fatal(err)
					}
					if err = png.Encode(f, frame); err != nil {
						t.Fatal(err)
					}
					if err = f.Close(); err != nil {
						t.Fatal(err)
					}
				}
				endingTestWrite(t, filepath.Join(out, fmt.Sprintf("pair-%02d.json", i+1)), map[string]any{"controlled": true, "font": "noto", "palette": endingPalette, "ops": p.ops, "record": i + 1, "source_sha256": source})
			}
			p.apply(c)
			if !bytes.Equal(hd.Pix, renderEndingPage(p, endingPalette, a.art, a.profile("noto")).Pix) {
				t.Fatal("重複雙人圖加深透明邊緣")
			}
		})
	}
}
