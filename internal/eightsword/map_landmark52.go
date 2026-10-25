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
	mapLandmark52ImageSHA  = "bfa21fb69c92918d2a27380077153377dbba5d5d84f1a3d1dac6c7ab85fc7e83"
	mapLandmark52NativeSHA = "e6b6adc005119cfcdf87cfe55cfe601f967a22b4f8796232c33733a65cd3f146"
	mapLandmark52RecordSHA = "28988f39adf2e0b5835163e413b63fc1f550dcfdc3097538143e028f5424018d"
	mapLandmark52CacheSHA  = "8147efffe2e0f26f26295391bdd1b2a3e5db621539ee55cc65ed2b48c9e2a6c8"
)

type mapLandmark52Manifest struct {
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
func loadMapLandmark52(dir string, pmap []byte, assets *GraphicsAssets) error {
	raw, err := encounterRead(filepath.Join(dir, "map-landmark-52.json"), 16*1024)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	var m mapLandmark52Manifest
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err = d.Decode(&m); err != nil {
		return err
	}
	if d.Decode(new(any)) != io.EOF {
		return fmt.Errorf("地圖物件52清單有尾隨資料")
	}
	if m.Schema != 1 || m.Source != "PMAP.AY" || m.SourceSHA != PMAPSHA || m.StyleSHA != ApprovedStyleSHA || m.Index != 52 || m.NativeSHA != mapLandmark52NativeSHA || m.RecordSHA != mapLandmark52RecordSHA || m.CacheSHA != mapLandmark52CacheSHA || m.Grass != 0 || m.Sampling != "bilinear-full-alpha-over-grass" {
		return fmt.Errorf("地圖物件52清單來源或配置不符")
	}
	if m.Image.File != "map-landmark-52-r1.png" || m.Image.SHA != mapLandmark52ImageSHA || m.Image.Width != 1419 || m.Image.Height != 1108 {
		return fmt.Errorf("地圖物件52圖片來源不符")
	}
	if hash(pmap) != PMAPSHA || assets == nil || len(assets.Native) < 53 || assets.Materials == nil {
		return fmt.Errorf("地圖物件52缺少完整 PMAP 來源")
	}
	entry := pmap[52*1004 : 53*1004]
	n := assets.Native[52]
	if hash(entry) != mapLandmark52RecordSHA || hash(entry[:804]) != mapLandmark52NativeSHA || n.Index != 52 || n.WidthBytes != 8 || n.Height != 25 || n.NativeSHA != mapLandmark52NativeSHA || assets.ByNative[mapLandmark52NativeSHA] != 53 {
		return fmt.Errorf("地圖物件52原始來源不符")
	}
	if assets.Materials[53] != nil || assets.Actors[53] != nil || assets.Effects[53] != nil {
		return fmt.Errorf("地圖物件52識別重複")
	}
	grass := assets.Materials[1]
	if grass == nil || grass.NativeWidth != 64 || grass.NativeHeight != 25 || grass.Tile == nil || grass.Tile.Bounds() != image.Rect(0, 0, 192, 150) || grass.Tile.Stride != 192*4 || len(grass.Tile.Pix) != 192*150*4 {
		return fmt.Errorf("地圖物件52缺少完整草地快取")
	}
	raw, err = encounterRead(filepath.Join(dir, m.Image.File), 8*1024*1024)
	if err != nil {
		return err
	}
	if hash(raw) != mapLandmark52ImageSHA {
		return fmt.Errorf("地圖物件52圖片 SHA-256 不符")
	}
	config, err := png.DecodeConfig(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	if config.Width != 1419 || config.Height != 1108 {
		return fmt.Errorf("地圖物件52圖片尺寸不符")
	}
	decoded, err := png.Decode(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	tile, err := compositeStaticObject(decoded, grass.Tile)
	if err != nil {
		return err
	}
	if hash(tile.Pix) != mapLandmark52CacheSHA {
		return fmt.Errorf("地圖物件52快取不符")
	}
	assets.Materials[53] = &graphicMaterial{64, 25, tile}
	return nil
}
