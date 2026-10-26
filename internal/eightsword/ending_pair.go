// Spec 053 READY. Optional four-scale END6 pair, source masks remain authoritative.
package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"
)

const endingPairManifest = "c230dfefb876877f2a5f8430296c4e4e2644497acfbe74562a48de95a245670b"

var endingPairSources = [...]string{
	"442e361a3e824fe076b7c062ab6f7f0000203bb2cf491aa6822c6a7fe673c9d2",
	"32d0f1629f4f85fda6eb55a7db519b62bd9c7d0574cbb02a3df721eacb0f1aac",
	"a08f07085c14a655fb46eceb95d1ad3bcf2e4dc908881b4b2c09af61eb2a3b90",
	"f808d2a2f8a37439943908b538dc820667967deaba6209ebecb5de25d46682cd",
}

func loadEndingPair(dir, root string) (map[string]image.Image, error) {
	read := func(name string, limit int64) ([]byte, error) {
		p := filepath.Join(dir, name)
		s, err := os.Lstat(p)
		if err != nil {
			return nil, err
		}
		if !s.Mode().IsRegular() || s.Size() <= 0 || s.Size() > limit {
			return nil, fmt.Errorf("結局雙人檔案類型／大小不符")
		}
		return os.ReadFile(p)
	}
	raw, err := read("ending-pair.json", 8192)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if hash(raw) != endingPairManifest {
		return nil, fmt.Errorf("結局雙人清單SHA不符")
	}
	original, err := os.ReadFile(filepath.Join(root, "END6.AY"))
	if err != nil {
		return nil, err
	}
	if hash(original) != "b8112bbcfe9cd045015da16a06ce98a53622c0fcf5cea436069cdcb0eccc96cc" {
		return nil, fmt.Errorf("結局雙人原始來源SHA不符")
	}
	var manifest struct {
		Records []struct {
			Record int    `json:"record"`
			Source string `json:"source_sha256"`
			Image  string `json:"image"`
			SHA    string `json:"image_sha256"`
			Width  int    `json:"width"`
			Height int    `json:"height"`
		} `json:"records"`
	}
	if err := json.Unmarshal(raw, &manifest); err != nil {
		return nil, err
	}
	if len(manifest.Records) != 4 {
		return nil, fmt.Errorf("結局雙人筆數不符")
	}
	textures := make(map[string]image.Image, 4)
	for i, record := range manifest.Records {
		if record.Record != i+1 || record.Source != endingPairSources[i] || record.Image != fmt.Sprintf("ending-pair-%02d.png", i+1) || record.Width != 408 || record.Height != 300 {
			return nil, fmt.Errorf("結局雙人來源／形狀不符")
		}
		data, err := read(record.Image, 4<<20)
		if err != nil {
			return nil, err
		}
		if hash(data) != record.SHA {
			return nil, fmt.Errorf("結局雙人第%d筆圖片SHA不符", i+1)
		}
		cfg, err := png.DecodeConfig(bytes.NewReader(data))
		if err != nil || cfg.Width != 408 || cfg.Height != 300 {
			return nil, fmt.Errorf("結局雙人PNG形狀不符")
		}
		im, err := png.Decode(bytes.NewReader(data))
		if err != nil {
			return nil, err
		}
		textures[record.Source] = im
	}
	return textures, nil
}

// Retain only the original mask's explicit black writes before applying the HD
// figure. Transparent areas do not clear the earlier page or source commands.
func endingPairBlackBase(out *image.RGBA, c *endingCommand) {
	for local, value := range c.Pixels {
		if c.Mask[local] != 0 && value == 0 {
			x, y := (c.X+local%c.W)*3, (c.Y+local/c.W)*6
			endingFill(out, image.Rect(x, y, x+3, y+6), endingPalette[0])
		}
	}
}
