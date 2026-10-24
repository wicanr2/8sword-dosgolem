package eightsword

import (
	"bytes"
	"encoding/json"
	"image"
	"image/color"
	"image/png"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestPublisherIconFaultIsolation(t *testing.T) {
	assets := os.Getenv("EIGHTSWORD_TEST_PUBLISHER_ICON_ASSETS")
	if assets == "" {
		t.Skip("requires approved publisher icon pack")
	}
	e := storyEngine(t, assets)
	if e.Publisher == nil || e.Publisher.publisher.icon == nil || e.Publisher.publisher.iconError != "" {
		t.Fatal(e.Status())
	}
	words := e.Publisher.publisher
	manifest, err := os.ReadFile(filepath.Join(assets, "publisher-icon.json"))
	if err != nil {
		t.Fatal(err)
	}
	var original map[string]any
	if err = json.Unmarshal(manifest, &original); err != nil {
		t.Fatal(err)
	}
	tests := []struct {
		name, want string
		mutate     func(string, map[string]any)
	}{
		{"missing-manifest", "", func(d string, m map[string]any) { os.Remove(filepath.Join(d, "publisher-icon.json")) }},
		{"image-hash", "SHA-256", func(d string, m map[string]any) {
			b, _ := os.ReadFile(filepath.Join(d, "publisher-icon.png"))
			os.WriteFile(filepath.Join(d, "publisher-icon.png"), append(b, 0), 0600)
		}},
		{"mask-hash", "SHA-256", func(d string, m map[string]any) {
			b, _ := os.ReadFile(filepath.Join(d, "publisher-icon-erase.png"))
			os.WriteFile(filepath.Join(d, "publisher-icon-erase.png"), append(b, 0), 0600)
		}},
		{"source", "來源／形狀", func(d string, m map[string]any) { m["source_sha256"] = "wrong" }},
		{"dimensions", "來源／形狀", func(d string, m map[string]any) { m["width"] = 640 }},
		{"unknown-field", "unknown field", func(d string, m map[string]any) { m["extra"] = true }},
		{"non-binary-mask", "不是二值", func(d string, m map[string]any) {
			im := image.NewGray(image.Rect(0, 0, 640, 200))
			im.SetGray(0, 0, color.Gray{Y: 128})
			var b bytes.Buffer
			png.Encode(&b, im)
			os.WriteFile(filepath.Join(d, "publisher-icon-erase.png"), b.Bytes(), 0600)
			m["mask_sha256"] = hash(b.Bytes())
		}},
		{"wrong-mask-origin", "遮罩來源", func(d string, m map[string]any) {
			im := image.NewGray(image.Rect(0, 0, 640, 200))
			var b bytes.Buffer
			png.Encode(&b, im)
			os.WriteFile(filepath.Join(d, "publisher-icon-erase.png"), b.Bytes(), 0600)
			m["mask_sha256"] = hash(b.Bytes())
		}},
		{"wrong-mask-shape", "尺寸不符", func(d string, m map[string]any) {
			im := image.NewGray(image.Rect(0, 0, 1, 1))
			var b bytes.Buffer
			png.Encode(&b, im)
			os.WriteFile(filepath.Join(d, "publisher-icon-erase.png"), b.Bytes(), 0600)
			m["mask_sha256"] = hash(b.Bytes())
		}},
		{"symlink", "檔案類型", func(d string, m map[string]any) {
			os.Remove(filepath.Join(d, "publisher-icon-erase.png"))
			os.Symlink(filepath.Join(assets, "publisher-icon-erase.png"), filepath.Join(d, "publisher-icon-erase.png"))
		}},
		{"oversize-image", "容量不符", func(d string, m map[string]any) {
			os.WriteFile(filepath.Join(d, "publisher-icon.png"), make([]byte, 8*1024*1024+1), 0600)
		}},
		{"oversize-mask", "容量不符", func(d string, m map[string]any) {
			os.WriteFile(filepath.Join(d, "publisher-icon-erase.png"), make([]byte, 1024*1024+1), 0600)
		}},
		{"trailing", "尾隨", nil},
		{"oversize-manifest", "容量不符", nil},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			d := t.TempDir()
			for _, name := range []string{"publisher-icon.json", "publisher-icon.png", "publisher-icon-erase.png"} {
				b, err := os.ReadFile(filepath.Join(assets, name))
				if err != nil {
					t.Fatal(err)
				}
				if err = os.WriteFile(filepath.Join(d, name), b, 0600); err != nil {
					t.Fatal(err)
				}
			}
			m := map[string]any{}
			for k, v := range original {
				m[k] = v
			}
			if tc.mutate != nil {
				tc.mutate(d, m)
			}
			if tc.name != "missing-manifest" {
				b, err := json.Marshal(m)
				if err != nil {
					t.Fatal(err)
				}
				if tc.name == "trailing" {
					b = append(b, []byte(" {}")...)
				}
				if tc.name == "oversize-manifest" {
					b = make([]byte, 65537)
				}
				if err = os.WriteFile(filepath.Join(d, "publisher-icon.json"), b, 0600); err != nil {
					t.Fatal(err)
				}
			}
			icon, err := loadPublisherIcon(d, words)
			if icon != nil || (tc.want == "" && err != nil) || (tc.want != "" && (err == nil || !strings.Contains(err.Error(), tc.want))) {
				t.Fatalf("icon=%v err=%v want=%s", icon != nil, err, tc.want)
			}
		})
	}
	// An independently supplied word pixel cannot paint through the approved icon.
	t.Run("word-overlap", func(t *testing.T) {
		im := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
		found := false
		for y := 114; y < 828 && !found; y++ {
			for x := 654; x < 1281; x++ {
				_, _, _, a := words.icon.art.At(x, y).RGBA()
				if a != 0 {
					im.SetRGBA(x, y, color.RGBA{255, 255, 255, 255})
					found = true
					break
				}
			}
		}
		if !found {
			t.Fatal("approved icon empty")
		}
		p := *words
		p.words = map[string]image.Image{"noto": im}
		if icon, err := loadPublisherIcon(assets, &p); icon != nil || err == nil || !strings.Contains(err.Error(), "重疊") {
			t.Fatal(icon, err)
		}
	})
	// A real corrupt optional PNG leaves words and all other HD groups available.
	t.Run("engine-fallback", func(t *testing.T) {
		d := t.TempDir()
		files, err := os.ReadDir(assets)
		if err != nil {
			t.Fatal(err)
		}
		for _, f := range files {
			b, err := os.ReadFile(filepath.Join(assets, f.Name()))
			if err != nil {
				t.Fatal(err)
			}
			if f.Name() == "publisher-icon.png" {
				b = append(b, 0)
			}
			if err = os.WriteFile(filepath.Join(d, f.Name()), b, 0600); err != nil {
				t.Fatal(err)
			}
		}
		bad := storyEngine(t, d)
		if bad.Publisher == nil || bad.PublisherError != "" || bad.Publisher.publisher.icon != nil || !strings.Contains(bad.Publisher.publisher.iconError, "SHA-256") || bad.Intro == nil || bad.Story == nil || bad.Captions == nil || bad.Tracker.graphics == nil || bad.Music.LoadError != "" || len(bad.FontChoices()) != 3 {
			t.Fatal(bad.Status())
		}
	})
}
