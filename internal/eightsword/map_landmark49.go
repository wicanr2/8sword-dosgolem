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
	mapLandmark49ImageSHA  = "347e485c9450754b28bb5f1db743a8d6aea83d51836ae8a1298e7f45919cd303"
	mapLandmark49NativeSHA = "5af28dbd172be266d77a5d07af241ee6488b1f97d7e5d08ba29df2ae1f842667"
	mapLandmark49RecordSHA = "d8858e3a2f3006a4813c4ba4cc28b4c633b85f072adad416f2f4842f179f4e39"
	mapLandmark49CacheSHA  = "210fd08b77ac192c962a3e41e3bfd522e7f144f64b4ac4ecbbb6f85934375870"
)

type mapLandmark49Manifest struct {
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
func loadMapLandmark49(dir string, pmap []byte, assets *GraphicsAssets) error {
	raw, err := encounterRead(filepath.Join(dir, "map-landmark-49.json"), 16*1024)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	var m mapLandmark49Manifest
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err = d.Decode(&m); err != nil {
		return err
	}
	if d.Decode(new(any)) != io.EOF {
		return fmt.Errorf("地圖物件49清單有尾隨資料")
	}
	if m.Schema != 1 || m.Source != "PMAP.AY" || m.SourceSHA != PMAPSHA || m.StyleSHA != ApprovedStyleSHA || m.Index != 49 || m.NativeSHA != mapLandmark49NativeSHA || m.RecordSHA != mapLandmark49RecordSHA || m.CacheSHA != mapLandmark49CacheSHA || m.Grass != 0 || m.Sampling != "bilinear-full-alpha-over-grass" {
		return fmt.Errorf("地圖物件49清單來源或配置不符")
	}
	if m.Image.File != "map-landmark-49-r1.png" || m.Image.SHA != mapLandmark49ImageSHA || m.Image.Width != 1419 || m.Image.Height != 1108 {
		return fmt.Errorf("地圖物件49圖片來源不符")
	}
	if hash(pmap) != PMAPSHA || assets == nil || len(assets.Native) < 50 || assets.Materials == nil {
		return fmt.Errorf("地圖物件49缺少完整 PMAP 來源")
	}
	entry := pmap[49*1004 : 50*1004]
	n := assets.Native[49]
	if hash(entry) != mapLandmark49RecordSHA || hash(entry[:804]) != mapLandmark49NativeSHA || n.Index != 49 || n.WidthBytes != 8 || n.Height != 25 || n.NativeSHA != mapLandmark49NativeSHA || assets.ByNative[mapLandmark49NativeSHA] != 50 {
		return fmt.Errorf("地圖物件49原始來源不符")
	}
	if assets.Materials[50] != nil || assets.Actors[50] != nil || assets.Effects[50] != nil {
		return fmt.Errorf("地圖物件49識別重複")
	}
	grass := assets.Materials[1]
	if grass == nil || grass.NativeWidth != 64 || grass.NativeHeight != 25 || grass.Tile == nil || grass.Tile.Bounds() != image.Rect(0, 0, 192, 150) || grass.Tile.Stride != 192*4 || len(grass.Tile.Pix) != 192*150*4 {
		return fmt.Errorf("地圖物件49缺少完整草地快取")
	}
	raw, err = encounterRead(filepath.Join(dir, m.Image.File), 8*1024*1024)
	if err != nil {
		return err
	}
	if hash(raw) != mapLandmark49ImageSHA {
		return fmt.Errorf("地圖物件49圖片 SHA-256 不符")
	}
	config, err := png.DecodeConfig(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	if config.Width != 1419 || config.Height != 1108 {
		return fmt.Errorf("地圖物件49圖片尺寸不符")
	}
	decoded, err := png.Decode(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	tile, err := compositeStaticObject(decoded, grass.Tile)
	if err != nil {
		return err
	}
	if hash(tile.Pix) != mapLandmark49CacheSHA {
		return fmt.Errorf("地圖物件49快取不符")
	}
	assets.Materials[50] = &graphicMaterial{64, 25, tile}
	return nil
}
