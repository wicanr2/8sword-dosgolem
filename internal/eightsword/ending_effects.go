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

const endingEffectsManifest = "720b89a14f76b3c47d82c85d21a054f985c7a4900986256e4b78cf5b6887957d"

var endingEffectsSources = [...]string{
	"c851736914bdb3c1d2419855d62eb96325e1ed4b4f265dc8b77b10da05dc7445",
	"62c8e2c52e5e289ab3111b0d6eaf80387026c131e67a39905c430957b39c713f",
	"a16c291f6f4d5ac42f17ecf66d1a39891406040f67d2b56bca7423b43dc2e78e",
	"f605f46227cb14b0212b4b02c5b98d61c8aa67b0fd4e27f34034091e6db449d7",
	"68bb0605ac105a4bb306bdd363791055524a3c3e1ae5c546d6a5e355ee9a9c6c",
	"31e2b9e9eba33118e518b7f5c4aed2f61bf501baa48de633c426732f1b9075f2",
	"a888256ee23e810b2b01ed7b51e612cfd5caac46acdd4cd436fc81b3a7a59acd",
	"b630aca792071a3e8ffeec62e5a526e068338a94441ab1db8de9902e0a9a7397",
	"aec7a1dc1b41c4581f6598f4629127dd22a91315d93c5d1f694042499c0d2417",
	"7c3df1b265fce28b4c5b874995a6e62979f83aba5600a7d9ec079f4501f3bbf3",
	"8087faac315fbb8da657ef1fd22c7c2407fa841d0cceed18341ac0e27fe22f5e",
}

func loadEndingEffects(dir, root string) (map[string]image.Image, error) {
	read := func(name string, limit int64) ([]byte, error) {
		p := filepath.Join(dir, name)
		s, err := os.Lstat(p)
		if err != nil {
			return nil, err
		}
		if !s.Mode().IsRegular() || s.Size() <= 0 || s.Size() > limit {
			return nil, fmt.Errorf("結局效果檔案類型／大小不符")
		}
		return os.ReadFile(p)
	}
	raw, err := read("ending-effects.json", 16384)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if hash(raw) != endingEffectsManifest {
		return nil, fmt.Errorf("結局效果清單SHA不符")
	}
	original, err := os.ReadFile(filepath.Join(root, "END2.AY"))
	if err != nil {
		return nil, err
	}
	if hash(original) != "c079973aaf332f8a30a5b4c905049d826cb1031aa568a766f60cf051c2f78d8c" {
		return nil, fmt.Errorf("結局效果原始來源SHA不符")
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
	if len(manifest.Records) != len(endingEffectsSources) {
		return nil, fmt.Errorf("結局效果筆數不符")
	}
	textures := make(map[string]image.Image, 11)
	for i, record := range manifest.Records {
		w, h := 480, 198
		if i >= 6 {
			w, h = 288, 240
		} else if i >= 3 {
			w, h = 216, 336
		}
		if record.Record != i || record.Source != endingEffectsSources[i] || record.Image != fmt.Sprintf("ending-effect-%02d.png", i) || record.Width != w || record.Height != h {
			return nil, fmt.Errorf("結局效果來源／形狀不符")
		}
		data, err := read(record.Image, 4<<20)
		if err != nil {
			return nil, err
		}
		if hash(data) != record.SHA {
			return nil, fmt.Errorf("結局效果第%d筆圖片SHA不符", i)
		}
		cfg, err := png.DecodeConfig(bytes.NewReader(data))
		if err != nil || cfg.Width != w || cfg.Height != h {
			return nil, fmt.Errorf("結局效果PNG形狀不符")
		}
		im, err := png.Decode(bytes.NewReader(data))
		if err != nil {
			return nil, err
		}
		textures[record.Source] = im
	}
	return textures, nil
}
