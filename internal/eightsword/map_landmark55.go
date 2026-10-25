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
	mapLandmark55ImageSHA  = "55e20818bf365b1d892ecce5ec2bf7eadaffba952635f890cc94c0bf2a107cdc"
	mapLandmark55NativeSHA = "6f7b459688d11fa5249790a6802f677bc7e38a228d4c380d4b472c40b37e3f87"
	mapLandmark55RecordSHA = "18f01693acca18d6f4254c7f3a14bf1d7e9bff0fa4bca45d5c288a1432d94069"
	mapLandmark55CacheSHA  = "2a4f23af0710c6e95ed002000f79dc612d312d74346f00452d5c0e4c0b4f322a"
)

type mapLandmark55Manifest struct {
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
func loadMapLandmark55(dir string, pmap []byte, assets *GraphicsAssets) error {
	raw, err := encounterRead(filepath.Join(dir, "map-landmark-55.json"), 16*1024)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	var m mapLandmark55Manifest
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err = d.Decode(&m); err != nil {
		return err
	}
	if d.Decode(new(any)) != io.EOF {
		return fmt.Errorf("地圖物件55清單有尾隨資料")
	}
	if m.Schema != 1 || m.Source != "PMAP.AY" || m.SourceSHA != PMAPSHA || m.StyleSHA != ApprovedStyleSHA || m.Index != 55 || m.NativeSHA != mapLandmark55NativeSHA || m.RecordSHA != mapLandmark55RecordSHA || m.CacheSHA != mapLandmark55CacheSHA || m.Grass != 0 || m.Sampling != "bilinear-full-alpha-over-grass" {
		return fmt.Errorf("地圖物件55清單來源或配置不符")
	}
	if m.Image.File != "map-landmark-55-r1.png" || m.Image.SHA != mapLandmark55ImageSHA || m.Image.Width != 1419 || m.Image.Height != 1108 {
		return fmt.Errorf("地圖物件55圖片來源不符")
	}
	if hash(pmap) != PMAPSHA || assets == nil || len(assets.Native) < 56 || assets.Materials == nil {
		return fmt.Errorf("地圖物件55缺少完整 PMAP 來源")
	}
	entry := pmap[55*1004 : 56*1004]
	n := assets.Native[55]
	if hash(entry) != mapLandmark55RecordSHA || hash(entry[:804]) != mapLandmark55NativeSHA || n.Index != 55 || n.WidthBytes != 8 || n.Height != 25 || n.NativeSHA != mapLandmark55NativeSHA || assets.ByNative[mapLandmark55NativeSHA] != 56 {
		return fmt.Errorf("地圖物件55原始來源不符")
	}
	if assets.Materials[56] != nil || assets.Actors[56] != nil || assets.Effects[56] != nil {
		return fmt.Errorf("地圖物件55識別重複")
	}
	grass := assets.Materials[1]
	if grass == nil || grass.NativeWidth != 64 || grass.NativeHeight != 25 || grass.Tile == nil || grass.Tile.Bounds() != image.Rect(0, 0, 192, 150) || grass.Tile.Stride != 192*4 || len(grass.Tile.Pix) != 192*150*4 {
		return fmt.Errorf("地圖物件55缺少完整草地快取")
	}
	raw, err = encounterRead(filepath.Join(dir, m.Image.File), 8*1024*1024)
	if err != nil {
		return err
	}
	if hash(raw) != mapLandmark55ImageSHA {
		return fmt.Errorf("地圖物件55圖片 SHA-256 不符")
	}
	config, err := png.DecodeConfig(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	if config.Width != 1419 || config.Height != 1108 {
		return fmt.Errorf("地圖物件55圖片尺寸不符")
	}
	decoded, err := png.Decode(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	tile, err := compositeStaticObject(decoded, grass.Tile)
	if err != nil {
		return err
	}
	if hash(tile.Pix) != mapLandmark55CacheSHA {
		return fmt.Errorf("地圖物件55快取不符")
	}
	assets.Materials[56] = &graphicMaterial{64, 25, tile}
	return nil
}
