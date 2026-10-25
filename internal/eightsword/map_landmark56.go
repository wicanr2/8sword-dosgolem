package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/png"
	"io"
	"os"
	"path/filepath"
)

const (
	mapLandmark56ImageSHA  = "7188d67ebf710df40d2adfcaa520d21c1f9781008748a214a497629c2b0a542d"
	mapLandmark56NativeSHA = "c94b51a07f43d19768b4bc6b0d6c1ef57154f1be4d0024470bc8dc3755e420b6"
	mapLandmark56RecordSHA = "74d93a7872784953e405930f6046b04e326939dc9e0b8be488936f82a7ea218d"
	mapLandmark56CacheSHA  = "412af4cb89b40adc1b0b56b2b5605fd016918b51712a081a4cea01938d0e9fd4"
)

type mapLandmark56Manifest struct {
	Schema    int    `json:"schema"`
	Source    string `json:"source_file"`
	SourceSHA string `json:"source_sha256"`
	StyleSHA  string `json:"style_reference_sha256"`
	Index     int    `json:"source_index"`
	NativeSHA string `json:"native_sha256"`
	RecordSHA string `json:"record_sha256"`
	CacheSHA  string `json:"cache_sha256"`
	Grass     int    `json:"grass_source"`
	Sampling  string `json:"sampling"`
	Image     struct {
		File   string `json:"file"`
		SHA    string `json:"sha256"`
		Width  int    `json:"width"`
		Height int    `json:"height"`
	} `json:"image"`
}

// Spec 045: independent optional presentation material. Register only after all checks.
func loadMapLandmark56(dir string, pmap []byte, assets *GraphicsAssets) error {
	raw, err := encounterRead(filepath.Join(dir, "map-landmark-56.json"), 16*1024)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	var m mapLandmark56Manifest
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err = d.Decode(&m); err != nil {
		return err
	}
	if d.Decode(new(any)) != io.EOF {
		return fmt.Errorf("地圖物件56清單有尾隨資料")
	}
	if m.Schema != 1 || m.Source != "PMAP.AY" || m.SourceSHA != PMAPSHA || m.StyleSHA != ApprovedStyleSHA || m.Index != 56 || m.NativeSHA != mapLandmark56NativeSHA || m.RecordSHA != mapLandmark56RecordSHA || m.CacheSHA != mapLandmark56CacheSHA || m.Grass != 0 || m.Sampling != "bilinear-full-alpha-over-grass" {
		return fmt.Errorf("地圖物件56清單來源或配置不符")
	}
	if m.Image.File != "map-landmark-56-r1.png" || m.Image.SHA != mapLandmark56ImageSHA || m.Image.Width != 1419 || m.Image.Height != 1108 {
		return fmt.Errorf("地圖物件56圖片來源不符")
	}
	if hash(pmap) != PMAPSHA || assets == nil || len(assets.Native) < 57 || assets.Materials == nil {
		return fmt.Errorf("地圖物件56缺少完整 PMAP 來源")
	}
	entry := pmap[56*1004 : 57*1004]
	n := assets.Native[56]
	if hash(entry) != mapLandmark56RecordSHA || hash(entry[:804]) != mapLandmark56NativeSHA || n.Index != 56 || n.WidthBytes != 8 || n.Height != 25 || n.NativeSHA != mapLandmark56NativeSHA || assets.ByNative[mapLandmark56NativeSHA] != 57 {
		return fmt.Errorf("地圖物件56原始來源不符")
	}
	if assets.Materials[57] != nil || assets.Actors[57] != nil || assets.Effects[57] != nil {
		return fmt.Errorf("地圖物件56識別重複")
	}
	grass := assets.Materials[1]
	if grass == nil || grass.NativeWidth != 64 || grass.NativeHeight != 25 || grass.Tile == nil || grass.Tile.Bounds() != image.Rect(0, 0, 192, 150) || grass.Tile.Stride != 192*4 || len(grass.Tile.Pix) != 192*150*4 {
		return fmt.Errorf("地圖物件56缺少完整草地快取")
	}
	raw, err = encounterRead(filepath.Join(dir, m.Image.File), 8*1024*1024)
	if err != nil {
		return err
	}
	if hash(raw) != mapLandmark56ImageSHA {
		return fmt.Errorf("地圖物件56圖片 SHA-256 不符")
	}
	config, err := png.DecodeConfig(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	if config.Width != 1419 || config.Height != 1108 {
		return fmt.Errorf("地圖物件56圖片尺寸不符")
	}
	decoded, err := png.Decode(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	tile, err := compositeStaticObject(decoded, grass.Tile)
	if err != nil {
		return err
	}
	if hash(tile.Pix) != mapLandmark56CacheSHA {
		return fmt.Errorf("地圖物件56快取不符")
	}
	assets.Materials[57] = &graphicMaterial{64, 25, tile}
	return nil
}
