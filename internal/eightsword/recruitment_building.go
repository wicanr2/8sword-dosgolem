package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
)

const recruitmentSourceSHA = "b854b04f3b0d3620adc37e3adb498cbe3ae710f007766695f40f4065ebde32eb"
const recruitmentNativeSHA = "edf6a0cc7dc13fbd054049bcb9bec91e1386c0c8b141174da376499854cb5978"
const recruitmentImageSHA = "7aa67f8975843e91e0a393863ba08bb77582fd4ab62ee10fad059bebcd5b61ab"
const recruitmentBuildingID uint16 = 112

func recruitmentRead(path string, limit int64) ([]byte, error) {
	info, err := os.Lstat(path)
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() > limit {
		return nil, fmt.Errorf("募兵建築檔案類型／容量不符")
	}
	return os.ReadFile(path)
}

// Spec 034: optional group; register ownership only after complete validation.
// The existing four-plane observer supplies position, copies and invalidation.
func loadRecruitmentBuilding(dir, root string, assets *GraphicsAssets) error {
	raw, err := recruitmentRead(filepath.Join(dir, "recruitment-building.json"), 64*1024)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	var m struct {
		Schema    int        `json:"schema"`
		Source    string     `json:"source"`
		SourceSHA string     `json:"source_sha256"`
		NativeSHA string     `json:"native_sha256"`
		Style     string     `json:"style"`
		StyleSHA  string     `json:"style_reference_sha256"`
		Image     graphicPNG `json:"image"`
		Rights    string     `json:"rights"`
	}
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err = d.Decode(&m); err != nil {
		return err
	}
	if err = d.Decode(new(any)); err != io.EOF {
		return fmt.Errorf("募兵建築清單有尾隨資料")
	}
	if m.Schema != 1 || m.Source != "LIVE2.AY" || m.SourceSHA != recruitmentSourceSHA || m.NativeSHA != recruitmentNativeSHA || m.Style != "B-bright-painted-r1" || m.StyleSHA != ApprovedStyleSHA || m.Image.Index != 111 || m.Image.File != "recruitment-building-r1.png" || m.Image.SHA != recruitmentImageSHA || m.Image.Width != 1877 || m.Image.Height != 838 || m.Image.Sampling != "bitmap" || len(m.Image.SourceRect) != 0 {
		return fmt.Errorf("募兵建築來源／定稿不符")
	}
	source, err := recruitmentRead(filepath.Join(root, "LIVE2.AY"), 11480)
	if err != nil {
		return err
	}
	if hash(source) != recruitmentSourceSHA {
		return fmt.Errorf("LIVE2.AY 來源 SHA-256 不符")
	}
	if _, err = recruitmentRead(filepath.Join(dir, m.Image.File), 8*1024*1024); err != nil {
		return err
	}
	im, err := loadGraphicPNG(dir, m.Image)
	if err != nil {
		return err
	}
	tile, err := sampleMaterial(im, im.Bounds(), 1344, 600, false)
	if err != nil {
		return err
	}
	if assets.ByNative[recruitmentNativeSHA] != 0 || assets.Materials[recruitmentBuildingID] != nil || assets.Actors[recruitmentBuildingID] != nil || assets.Effects[recruitmentBuildingID] != nil {
		return fmt.Errorf("募兵建築來源識別重複")
	}
	assets.ByNative[recruitmentNativeSHA] = recruitmentBuildingID
	assets.Materials[recruitmentBuildingID] = &graphicMaterial{NativeWidth: 448, NativeHeight: 100, Tile: tile}
	return nil
}
