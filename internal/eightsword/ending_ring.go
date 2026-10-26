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

const endingRingSource = "f63c6b90c58db6f1bdc596c0c6dc565ecd47b6e8540fcb99cf2d76cbbe2c6f4a"
const endingRingManifest = "40ade60742046cf04effb6153b7c6bc6c792386b5e2025a7e311965cbf6443db"

func loadEndingRing(dir, root string) (image.Image, error) {
	read := func(name string, limit int64) ([]byte, error) {
		p := filepath.Join(dir, name)
		s, err := os.Lstat(p)
		if err != nil {
			return nil, err
		}
		if !s.Mode().IsRegular() || s.Size() <= 0 || s.Size() > limit {
			return nil, fmt.Errorf("紅金光環材質檔案類型／大小不符")
		}
		return os.ReadFile(p)
	}
	raw, err := read("ending-ring.json", 4096)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if hash(raw) != endingRingManifest {
		return nil, fmt.Errorf("紅金光環材質清單SHA不符")
	}
	original, err := os.ReadFile(filepath.Join(root, "END3.AY"))
	if err != nil {
		return nil, err
	}
	if hash(original) != "cb56acd3b5652223083b6c41036b4df821f2310a097224613ddaf56ca599f9ff" {
		return nil, fmt.Errorf("紅金光環原始來源SHA不符")
	}
	var m struct {
		SHA string `json:"image_sha256"`
	}
	if err := json.Unmarshal(raw, &m); err != nil {
		return nil, err
	}
	data, err := read("ending-ring.png", 4<<20)
	if err != nil {
		return nil, err
	}
	if hash(data) != m.SHA {
		return nil, fmt.Errorf("紅金光環圖片SHA不符")
	}
	cfg, err := png.DecodeConfig(bytes.NewReader(data))
	if err != nil || cfg.Width != 696 || cfg.Height != 630 {
		return nil, fmt.Errorf("紅金光環圖片形狀不符")
	}
	return png.Decode(bytes.NewReader(data))
}
