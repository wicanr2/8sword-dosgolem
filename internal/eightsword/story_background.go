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
const approvedStoryCanvasSHA = "734df8241381d2d016bb6c7421d8ce38b3dec2f7f91bdb0f7589b7d45b58ecbf"
const correctedStoryArtSHA = "9c26111247a7bf3606798c6ffb0708312bd939ecbec29db351ce1fc828e760d2"
const correctedStoryCanvasSHA = "966f94298da5c51de51cbb4652e03a921ee2a7ffd28a144fd341eaaa8075ded3"

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
	imageSHA := approvedStoryCanvasSHA
	if m.ApprovedSHA == correctedStoryArtSHA {
		imageSHA = correctedStoryCanvasSHA
	} else if m.ApprovedSHA != approvedStoryArtSHA {
		return nil, fmt.Errorf("故事背景圖像版本不符")
	}
	if m.Schema != 1 || m.SourceSHA != storyBackgroundSHA || m.ImageSHA != imageSHA || m.Image != "story-background.png" || m.Width != 1920 || m.Height != 1200 {
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
