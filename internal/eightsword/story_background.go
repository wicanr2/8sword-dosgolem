package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/draw"
	"os"
	"path/filepath"
)

const approvedStoryArtSHA = "bd21a34613dabef939afc9b94c9f45473cef2cd5f0e42aeee660d3d02b6d5c04"

func loadStoryBackground(dir string) (*image.RGBA, error) {
	raw, err := os.ReadFile(filepath.Join(dir, "story-background.json"))
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	var m struct {
		Schema        int    `json:"schema"`
		SourceSHA     string `json:"source_sha256"`
		ApprovedSHA   string `json:"approved_sha256"`
		Image         string `json:"image"`
		ImageSHA      string `json:"image_sha256"`
		Width, Height int
	}
	if err = json.Unmarshal(raw, &m); err != nil {
		return nil, err
	}
	if m.Schema != 1 || m.SourceSHA != storyBackgroundSHA || m.ApprovedSHA != approvedStoryArtSHA || m.Image != "story-background.png" || m.Width != 1920 || m.Height != 1200 {
		return nil, fmt.Errorf("故事背景清單來源／形狀不符")
	}
	png, err := os.ReadFile(filepath.Join(dir, m.Image))
	if err != nil {
		return nil, err
	}
	if hash(png) != m.ImageSHA {
		return nil, fmt.Errorf("故事背景圖片 SHA-256 不符")
	}
	cfg, _, err := image.DecodeConfig(bytes.NewReader(png))
	if err != nil || cfg.Width != 1920 || cfg.Height != 1200 {
		return nil, fmt.Errorf("故事背景圖片尺寸不符")
	}
	im, _, err := image.Decode(bytes.NewReader(png))
	if err != nil {
		return nil, err
	}
	out := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	draw.Draw(out, out.Bounds(), im, im.Bounds().Min, draw.Src)
	for at := 3; at < len(out.Pix); at += 4 {
		if out.Pix[at] != 255 {
			return nil, fmt.Errorf("故事背景圖片必須不透明")
		}
	}
	return out, nil
}
