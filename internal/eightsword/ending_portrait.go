package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"os"
	"path/filepath"
)

// 053 READY: source identities and image geometry, not animation rules.
const endingPortraitManifestSHA = "384bc2ecb1e280dd487ce3ed6fb3981d2e28da0c98031cd132ccefce4519eb80"
const endingPortraitOriginalSHA = "30451ddf5c325e27b7905e89cd34dc563c89ad0f4cced3a04835e7563632e2c0"

var endingPortraitSources = [5]string{
	"59cd1728bdd6a31f8a323580a7b57bc34bf309dc342a4028a8aaa06b370824e3",
	"138e96aa4c707a7e6b8c0cad20957faa5f9bbdee0bc2918198a5830aa9c3d00d",
	"d985494d828cfc7d1fe20c420276137aa95ec107c2c2bda385539ea36fe0682f",
	"79c79de9c767a3f0bc4bcc65990da275bb97c1f220fd5bc0ce2ed9565facca85",
	"9ea6391a0b07fa1550989381acf0b295c7ef18e194978a6402cf09405948e685",
}

type endingPortraitRecord struct {
	Record     int    `json:"record"`
	SourceSHA  string `json:"source_sha256"`
	SourceFile string `json:"source_file"`
	File       string `json:"file"`
	SHA        string `json:"sha256"`
	Size       [2]int `json:"size"`
	Position   [2]int `json:"position"`
	NativeSize [2]int `json:"native_size"`
}

func readEndingPortraitFile(dir, name string, limit int64) ([]byte, error) {
	if filepath.Base(name) != name {
		return nil, fmt.Errorf("END5材質名稱不符")
	}
	path := filepath.Join(dir, name)
	info, err := os.Lstat(path)
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() <= 0 || info.Size() > limit {
		return nil, fmt.Errorf("END5材質不是一般檔案或大小不符：%s", name)
	}
	return os.ReadFile(path)
}

func loadEndingPortrait(dir, root string) (map[string]image.Image, error) {
	raw, err := readEndingPortraitFile(dir, "ending-portrait.json", 16384)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if hash(raw) != endingPortraitManifestSHA {
		return nil, fmt.Errorf("END5人物清單SHA不符")
	}
	var manifest struct {
		Schema      int                    `json:"schema"`
		Source      string                 `json:"source_file"`
		OriginalSHA string                 `json:"original_sha256"`
		Records     []endingPortraitRecord `json:"records"`
	}
	if err = json.Unmarshal(raw, &manifest); err != nil {
		return nil, err
	}
	if manifest.Schema != 1 || manifest.Source != "END5.AY" || manifest.OriginalSHA != endingPortraitOriginalSHA || len(manifest.Records) != 5 {
		return nil, fmt.Errorf("END5人物清單範圍不符")
	}
	original, err := os.ReadFile(filepath.Join(root, "END5.AY"))
	if err != nil {
		return nil, err
	}
	if hash(original) != endingPortraitOriginalSHA {
		return nil, fmt.Errorf("END5原始檔SHA不符")
	}
	want := [5][2]int{{1920, 600}, {192, 180}, {192, 180}, {120, 90}, {120, 90}}
	positions := [5][2]int{{0, 50}, {488, 68}, {488, 68}, {496, 115}, {496, 115}}
	textures := make(map[string]image.Image, 5)
	for i, record := range manifest.Records {
		if record.Record != i || record.SourceFile != "END5.AY" || record.SourceSHA != endingPortraitSources[i] || record.Size != want[i] || record.Position != positions[i] || record.NativeSize != [2]int{want[i][0] / 3, want[i][1] / 6} || record.File != fmt.Sprintf("ending-end5-%d.png", i) {
			return nil, fmt.Errorf("END5第%d筆來源或形狀不符", i)
		}
		data, err := readEndingPortraitFile(dir, record.File, 8<<20)
		if err != nil {
			return nil, err
		}
		if hash(data) != record.SHA {
			return nil, fmt.Errorf("END5第%d筆圖片SHA不符", i)
		}
		config, format, err := image.DecodeConfig(bytes.NewReader(data))
		if err != nil {
			return nil, err
		}
		if format != "png" || config.Width != want[i][0] || config.Height != want[i][1] {
			return nil, fmt.Errorf("END5第%d筆圖片尺寸不符", i)
		}
		im, _, err := image.Decode(bytes.NewReader(data))
		if err != nil {
			return nil, err
		}
		textures[record.SourceSHA] = im
	}
	return textures, nil
}
