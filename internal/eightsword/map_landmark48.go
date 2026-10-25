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
	mapLandmark48ImageSHA  = "d5f29bde62da0724e2a486f0b5f61dfd676c26e6fcf3751a17d679bca412ffc1"
	mapLandmark48NativeSHA = "8faa16d2679f1bad38deefebd4615cb1491b7ae17f8cc472ee5e38562ac587a4"
	mapLandmark48RecordSHA = "e0b751a64138af9343d01b6831271bf328e854ac761491bb00000e1f1570d975"
	mapLandmark48CacheSHA  = "62d3072d49922f2a73f9cdce83f91f53e1f65b8f38aa51e5eacb9f1309102d49"
)

type mapLandmark48Manifest struct {
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
func loadMapLandmark48(dir string, pmap []byte, assets *GraphicsAssets) error {
	raw, err := encounterRead(filepath.Join(dir, "map-landmark-48.json"), 16*1024)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	var m mapLandmark48Manifest
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err = d.Decode(&m); err != nil {
		return err
	}
	if d.Decode(new(any)) != io.EOF {
		return fmt.Errorf("地圖物件48清單有尾隨資料")
	}
	if m.Schema != 1 || m.Source != "PMAP.AY" || m.SourceSHA != PMAPSHA || m.StyleSHA != ApprovedStyleSHA || m.Index != 48 || m.NativeSHA != mapLandmark48NativeSHA || m.RecordSHA != mapLandmark48RecordSHA || m.CacheSHA != mapLandmark48CacheSHA || m.Grass != 0 || m.Sampling != "bilinear-full-alpha-over-grass" {
		return fmt.Errorf("地圖物件48清單來源或配置不符")
	}
	if m.Image.File != "map-landmark-48-r2.png" || m.Image.SHA != mapLandmark48ImageSHA || m.Image.Width != 1419 || m.Image.Height != 1108 {
		return fmt.Errorf("地圖物件48圖片來源不符")
	}
	if hash(pmap) != PMAPSHA || assets == nil || len(assets.Native) < 49 || assets.Materials == nil {
		return fmt.Errorf("地圖物件48缺少完整 PMAP 來源")
	}
	entry := pmap[48*1004 : 49*1004]
	n := assets.Native[48]
	if hash(entry) != mapLandmark48RecordSHA || hash(entry[:804]) != mapLandmark48NativeSHA || n.Index != 48 || n.WidthBytes != 8 || n.Height != 25 || n.NativeSHA != mapLandmark48NativeSHA || assets.ByNative[mapLandmark48NativeSHA] != 49 {
		return fmt.Errorf("地圖物件48原始來源不符")
	}
	if assets.Materials[49] != nil || assets.Actors[49] != nil || assets.Effects[49] != nil {
		return fmt.Errorf("地圖物件48識別重複")
	}
	grass := assets.Materials[1]
	if grass == nil || grass.NativeWidth != 64 || grass.NativeHeight != 25 || grass.Tile == nil || grass.Tile.Bounds() != image.Rect(0, 0, 192, 150) || grass.Tile.Stride != 192*4 || len(grass.Tile.Pix) != 192*150*4 {
		return fmt.Errorf("地圖物件48缺少完整草地快取")
	}
	raw, err = encounterRead(filepath.Join(dir, m.Image.File), 8*1024*1024)
	if err != nil {
		return err
	}
	if hash(raw) != mapLandmark48ImageSHA {
		return fmt.Errorf("地圖物件48圖片 SHA-256 不符")
	}
	config, err := png.DecodeConfig(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	if config.Width != 1419 || config.Height != 1108 {
		return fmt.Errorf("地圖物件48圖片尺寸不符")
	}
	decoded, err := png.Decode(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	tile, err := compositeStaticObject(decoded, grass.Tile)
	if err != nil {
		return err
	}
	if hash(tile.Pix) != mapLandmark48CacheSHA {
		return fmt.Errorf("地圖物件48快取不符")
	}
	assets.Materials[49] = &graphicMaterial{64, 25, tile}
	return nil
}
