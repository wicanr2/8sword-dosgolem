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

const endingDuelSource = "4a5df66d3efaef4610802b281a9a216116922c914ebe920ecec14af6e94936ae"
const endingDuelManifest = "53c709eb2d1f76d9b44aaf555e414c2e092e777fe629de9cdc9542b9af90b056"

func loadEndingDuel(dir, root string) (image.Image, error) {
	read := func(name string, limit int64) ([]byte, error) {
		p := filepath.Join(dir, name)
		s, err := os.Lstat(p)
		if err != nil {
			return nil, err
		}
		if !s.Mode().IsRegular() || s.Size() <= 0 || s.Size() > limit {
			return nil, fmt.Errorf("對峙人物材質檔案類型／大小不符")
		}
		return os.ReadFile(p)
	}
	raw, err := read("ending-duel.json", 4096)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if hash(raw) != endingDuelManifest {
		return nil, fmt.Errorf("對峙人物材質清單SHA不符")
	}
	original, err := os.ReadFile(filepath.Join(root, "END1.AY"))
	if err != nil {
		return nil, err
	}
	if hash(original) != "7c1c6f91f4369d95c95b2d1e0ac09670ae459883add506bfe67dbe16da22e2b8" {
		return nil, fmt.Errorf("對峙人物原始來源SHA不符")
	}
	var m struct {
		SHA string `json:"image_sha256"`
	}
	if err := json.Unmarshal(raw, &m); err != nil {
		return nil, err
	}
	data, err := read("ending-duel.png", 4<<20)
	if err != nil {
		return nil, err
	}
	if hash(data) != m.SHA {
		return nil, fmt.Errorf("對峙人物圖片SHA不符")
	}
	cfg, err := png.DecodeConfig(bytes.NewReader(data))
	if err != nil || cfg.Width != 1536 || cfg.Height != 450 {
		return nil, fmt.Errorf("對峙人物圖片形狀不符")
	}
	return png.Decode(bytes.NewReader(data))
}
