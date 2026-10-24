package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/draw"
	"image/png"
	"io"
	"os"
	"path/filepath"
)

const preludeSourceSHA = "9aadec77cf59adb1f444d47891526af7da888bebecc648a3fa16a6f0adcd6dfe"
const preludeApprovedSHA = "12aed4841ed37026e91547dce49a4696fc3c20b511de5983dd4ed43c5a3340e8"
const preludeImageSHA = "93879b591e694968c7b777a0b89bdc60f2e3965718ddd520491ebdb2b198eb7c"

func preludeFile(dir, name string, limit int64) ([]byte, error) {
	f := filepath.Join(dir, name)
	s, err := os.Lstat(f)
	if err != nil {
		return nil, err
	}
	if !s.Mode().IsRegular() || s.Size() > limit {
		return nil, fmt.Errorf("前導檔案類型／容量不符")
	}
	return os.ReadFile(f)
}

func loadStoryPrelude(t *IntroStory, dir string) (*StoryPrelude, error) {
	raw, err := preludeFile(dir, "story-prelude.json", 65536)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	var m struct {
		Schema      int    `json:"schema"`
		SourceSHA   string `json:"source_sha256"`
		ApprovedSHA string `json:"approved_sha256"`
		Image       string `json:"image"`
		ImageSHA    string `json:"image_sha256"`
		Width       int    `json:"width"`
		Height      int    `json:"height"`
		Rights      string `json:"rights"`
	}
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err = d.Decode(&m); err != nil {
		return nil, err
	}
	if d.Decode(new(any)) != io.EOF {
		return nil, fmt.Errorf("前導清單包含尾隨資料")
	}
	if m.Schema != 1 || m.SourceSHA != preludeSourceSHA || m.ApprovedSHA != preludeApprovedSHA || m.Image != "story-prelude.png" || m.ImageSHA != preludeImageSHA || m.Width != 1920 || m.Height != 1200 || m.Rights == "" {
		return nil, fmt.Errorf("前導來源／形狀不符")
	}
	data, err := preludeFile(dir, m.Image, 8*1024*1024)
	if err != nil {
		return nil, err
	}
	if hash(data) != m.ImageSHA {
		return nil, fmt.Errorf("前導圖片 SHA-256 不符")
	}
	cfg, err := png.DecodeConfig(bytes.NewReader(data))
	if err != nil || cfg.Width != 1920 || cfg.Height != 1200 {
		return nil, fmt.Errorf("前導圖片尺寸不符")
	}
	im, err := png.Decode(bytes.NewReader(data))
	if err != nil {
		return nil, err
	}
	art := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	draw.Draw(art, art.Bounds(), im, im.Bounds().Min, draw.Src)
	for i := 3; i < len(art.Pix); i += 4 {
		if art.Pix[i] != 255 {
			return nil, fmt.Errorf("前導圖片必須不透明")
		}
	}
	p := &StoryPrelude{owner: t, art: art}
	p.bind()
	return p, nil
}
