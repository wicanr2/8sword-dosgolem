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
	mapLandmark54ImageSHA  = "328c5a99cf1758062778c7381742129f4a755af5bb0d35693084a78c7c35d7b5"
	mapLandmark54NativeSHA = "f57a3908342e7c2a8a5986374d745f749af596306e3d310b7633533b7909e602"
	mapLandmark54RecordSHA = "023ad63010f68e3cb8ea140b69c8870301a787ab739f2425a53d0fd7d10cb0fc"
	mapLandmark54CacheSHA  = "79b142d453644177050a596082bcbc2607e9e48b3dfebb07e9f7981e686e7706"
)

type mapLandmark54Manifest struct {
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
func loadMapLandmark54(dir string, pmap []byte, assets *GraphicsAssets) error {
	raw, err := encounterRead(filepath.Join(dir, "map-landmark-54.json"), 16*1024)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	var m mapLandmark54Manifest
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err = d.Decode(&m); err != nil {
		return err
	}
	if d.Decode(new(any)) != io.EOF {
		return fmt.Errorf("地圖物件54清單有尾隨資料")
	}
	if m.Schema != 1 || m.Source != "PMAP.AY" || m.SourceSHA != PMAPSHA || m.StyleSHA != ApprovedStyleSHA || m.Index != 54 || m.NativeSHA != mapLandmark54NativeSHA || m.RecordSHA != mapLandmark54RecordSHA || m.CacheSHA != mapLandmark54CacheSHA || m.Grass != 0 || m.Sampling != "bilinear-full-alpha-over-grass" {
		return fmt.Errorf("地圖物件54清單來源或配置不符")
	}
	if m.Image.File != "map-landmark-54-r1.png" || m.Image.SHA != mapLandmark54ImageSHA || m.Image.Width != 1419 || m.Image.Height != 1108 {
		return fmt.Errorf("地圖物件54圖片來源不符")
	}
	if hash(pmap) != PMAPSHA || assets == nil || len(assets.Native) < 55 || assets.Materials == nil {
		return fmt.Errorf("地圖物件54缺少完整 PMAP 來源")
	}
	entry := pmap[54*1004 : 55*1004]
	n := assets.Native[54]
	if hash(entry) != mapLandmark54RecordSHA || hash(entry[:804]) != mapLandmark54NativeSHA || n.Index != 54 || n.WidthBytes != 8 || n.Height != 25 || n.NativeSHA != mapLandmark54NativeSHA || assets.ByNative[mapLandmark54NativeSHA] != 55 {
		return fmt.Errorf("地圖物件54原始來源不符")
	}
	if assets.Materials[55] != nil || assets.Actors[55] != nil || assets.Effects[55] != nil {
		return fmt.Errorf("地圖物件54識別重複")
	}
	grass := assets.Materials[1]
	if grass == nil || grass.NativeWidth != 64 || grass.NativeHeight != 25 || grass.Tile == nil || grass.Tile.Bounds() != image.Rect(0, 0, 192, 150) || grass.Tile.Stride != 192*4 || len(grass.Tile.Pix) != 192*150*4 {
		return fmt.Errorf("地圖物件54缺少完整草地快取")
	}
	raw, err = encounterRead(filepath.Join(dir, m.Image.File), 8*1024*1024)
	if err != nil {
		return err
	}
	if hash(raw) != mapLandmark54ImageSHA {
		return fmt.Errorf("地圖物件54圖片 SHA-256 不符")
	}
	config, err := png.DecodeConfig(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	if config.Width != 1419 || config.Height != 1108 {
		return fmt.Errorf("地圖物件54圖片尺寸不符")
	}
	decoded, err := png.Decode(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	tile, err := compositeStaticObject(decoded, grass.Tile)
	if err != nil {
		return err
	}
	if hash(tile.Pix) != mapLandmark54CacheSHA {
		return fmt.Errorf("地圖物件54快取不符")
	}
	assets.Materials[55] = &graphicMaterial{64, 25, tile}
	return nil
}
