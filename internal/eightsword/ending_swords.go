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

const endingSwordsSource = "b13caa558e7e0d93aec2023eedd21fec0f3b6980178770444395c0913e9cc687"
const endingSwordsManifest = "3799c2ca8cc2ea6a5e6a6942d571263bc7a6323f0e9c92b6b7020e8d8b0d3ae8"

func loadEndingSwords(dir, root string) (image.Image, error) {
	read := func(name string, limit int64) ([]byte, error) {
		p := filepath.Join(dir, name)
		s, err := os.Lstat(p)
		if err != nil {
			return nil, err
		}
		if !s.Mode().IsRegular() || s.Size() <= 0 || s.Size() > limit {
			return nil, fmt.Errorf("八劍材質檔案類型／大小不符")
		}
		return os.ReadFile(p)
	}
	raw, err := read("ending-swords.json", 4096)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if hash(raw) != endingSwordsManifest {
		return nil, fmt.Errorf("八劍材質清單SHA不符")
	}
	original, err := os.ReadFile(filepath.Join(root, "END3.AY"))
	if err != nil {
		return nil, err
	}
	if hash(original) != "cb56acd3b5652223083b6c41036b4df821f2310a097224613ddaf56ca599f9ff" {
		return nil, fmt.Errorf("八劍原始來源SHA不符")
	}
	var m struct {
		SHA string `json:"image_sha256"`
	}
	if err := json.Unmarshal(raw, &m); err != nil {
		return nil, err
	}
	data, err := read("ending-swords.png", 4<<20)
	if err != nil {
		return nil, err
	}
	if hash(data) != m.SHA {
		return nil, fmt.Errorf("八劍圖片SHA不符")
	}
	cfg, err := png.DecodeConfig(bytes.NewReader(data))
	if err != nil || cfg.Width != 528 || cfg.Height != 420 {
		return nil, fmt.Errorf("八劍圖片形狀不符")
	}
	return png.Decode(bytes.NewReader(data))
}

// Only identical last overlapping writes are idempotent; other overlaps must paint again.
func endingSwordsRepeat(ops []*endingCommand, index int) bool {
	c := ops[index]
	r := image.Rect(c.X, c.Y, c.X+c.W, c.Y+c.H)
	for j := index - 1; j >= 0; j-- {
		prior := ops[j]
		if !r.Overlaps(image.Rect(prior.X, prior.Y, prior.X+prior.W, prior.Y+prior.H)) {
			continue
		}
		return prior.Kind == c.Kind && prior.SourceSHA == c.SourceSHA && prior.X == c.X && prior.Y == c.Y && prior.W == c.W && prior.H == c.H
	}
	return false
}
