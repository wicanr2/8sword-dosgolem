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
	mapChestImageSHA  = "cbdafc80d3bc9b137d2ba10f6f1d76d0e4cdb8cf8e5cf24abe4768af6ebaae85"
	mapChestNativeSHA = "fbc25f989bb092e80bd2970605e5e27e1639dc907e857c8a03f3c9a06a04c2f6"
	mapChestRecordSHA = "58a024b3400338bfc12ffba0f8bc5d49c53343ed73ada2a0c41e2a2b19bcb781"
	mapChestCacheSHA  = "549d61ae37b4cdf0c4e9f6b0fa70c29322a145621e408716fe91b10bfd422919"
)

type mapChestManifest struct {
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

// Spec 044: independent optional presentation material. Register only after all checks.
func loadMapChest(dir string, pmap []byte, assets *GraphicsAssets) error {
	raw, err := encounterRead(filepath.Join(dir, "map-chest.json"), 16*1024)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	var m mapChestManifest
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err = d.Decode(&m); err != nil {
		return err
	}
	if d.Decode(new(any)) != io.EOF {
		return fmt.Errorf("寶箱清單有尾隨資料")
	}
	if m.Schema != 1 || m.Source != "PMAP.AY" || m.SourceSHA != PMAPSHA || m.StyleSHA != ApprovedStyleSHA || m.Index != 58 || m.NativeSHA != mapChestNativeSHA || m.RecordSHA != mapChestRecordSHA || m.CacheSHA != mapChestCacheSHA || m.Grass != 0 || m.Sampling != "bilinear-full-alpha-over-grass" {
		return fmt.Errorf("寶箱清單來源或配置不符")
	}
	if m.Image.File != "map-chest-r2.png" || m.Image.SHA != mapChestImageSHA || m.Image.Width != 1419 || m.Image.Height != 1108 {
		return fmt.Errorf("寶箱圖片來源不符")
	}
	if hash(pmap) != PMAPSHA || assets == nil || len(assets.Native) < 59 || assets.Materials == nil {
		return fmt.Errorf("寶箱缺少完整 PMAP 來源")
	}
	entry := pmap[58*1004 : 59*1004]
	n := assets.Native[58]
	if hash(entry) != mapChestRecordSHA || hash(entry[:804]) != mapChestNativeSHA || n.Index != 58 || n.WidthBytes != 8 || n.Height != 25 || n.NativeSHA != mapChestNativeSHA || assets.ByNative[mapChestNativeSHA] != 59 {
		return fmt.Errorf("寶箱原始來源不符")
	}
	if assets.Materials[59] != nil || assets.Actors[59] != nil || assets.Effects[59] != nil {
		return fmt.Errorf("寶箱識別重複")
	}
	grass := assets.Materials[1]
	if grass == nil || grass.NativeWidth != 64 || grass.NativeHeight != 25 || grass.Tile == nil || grass.Tile.Bounds() != image.Rect(0, 0, 192, 150) || grass.Tile.Stride != 192*4 || len(grass.Tile.Pix) != 192*150*4 {
		return fmt.Errorf("寶箱缺少完整草地快取")
	}
	raw, err = encounterRead(filepath.Join(dir, m.Image.File), 8*1024*1024)
	if err != nil {
		return err
	}
	if hash(raw) != mapChestImageSHA {
		return fmt.Errorf("寶箱圖片 SHA-256 不符")
	}
	config, err := png.DecodeConfig(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	if config.Width != 1419 || config.Height != 1108 {
		return fmt.Errorf("寶箱圖片尺寸不符")
	}
	decoded, err := png.Decode(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	tile, err := compositeStaticObject(decoded, grass.Tile)
	if err != nil {
		return err
	}
	if hash(tile.Pix) != mapChestCacheSHA {
		return fmt.Errorf("寶箱快取不符")
	}
	assets.Materials[59] = &graphicMaterial{64, 25, tile}
	return nil
}
