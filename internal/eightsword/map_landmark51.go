package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image/png"
	"io"
	"os"
	"path/filepath"
)

const (
	mapLandmark51ManifestSHA = "336bcb02dc4dc859b00abe9655457d95e6bc45bbd6eabba02d1a0900408bbc72"
	mapLandmark51ImageSHA    = "5cf5e88a13f889f7d3c5d0f2b9e520da6f9de890e182a6aef8503fb3f660b185"
	mapLandmark51PromptSHA   = "9a7b73e602e0f72f8ab9d614a9aa39be645bd52a2cb449d05f4a12de1237e3a3"
	mapLandmark51NativeSHA   = "8c63efa0f99d6c3bdc7b6ddd681aab690ffec992f6493404604dfaaee6dd21c4"
	mapLandmark51RecordSHA   = "4220e310282bdb93b5e26bbe65e89c8709606afaad00abd9a8889889f45c79e1"
	mapLandmark51CacheSHA    = "a68863856899744c1078c5d80e85f80ea00f097c61e10622a41734fd70f03174"
)

type mapLandmark51Manifest struct {
	Schema    int    `json:"schema"`
	Source    string `json:"source_file"`
	SourceSHA string `json:"source_sha256"`
	StyleSHA  string `json:"style_reference_sha256"`
	Index     int    `json:"source_index"`
	NativeSHA string `json:"native_sha256"`
	RecordSHA string `json:"record_sha256"`
	CacheSHA  string `json:"cache_sha256"`
	Sampling  string `json:"sampling"`
	Prompt    string `json:"prompt_file"`
	PromptSHA string `json:"prompt_sha256"`
	Image     struct {
		File   string `json:"file"`
		SHA    string `json:"sha256"`
		Width  int    `json:"width"`
		Height int    `json:"height"`
	} `json:"image"`
}

// Spec045: opaque source pattern; gameplay meaning remains unknown.
func loadMapLandmark51(dir string, pmap []byte, assets *GraphicsAssets) error {
	raw, err := encounterRead(filepath.Join(dir, "map-landmark-51.json"), 16*1024)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	if hash(raw) != mapLandmark51ManifestSHA {
		return fmt.Errorf("地圖格紋51清單雜湊不符")
	}
	var m mapLandmark51Manifest
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err := d.Decode(&m); err != nil {
		return err
	}
	if d.Decode(new(any)) != io.EOF {
		return fmt.Errorf("地圖格紋51清單有尾隨資料")
	}
	if m.Schema != 1 || m.Source != "PMAP.AY" || m.SourceSHA != PMAPSHA || m.StyleSHA != ApprovedStyleSHA || m.Index != 51 || m.NativeSHA != mapLandmark51NativeSHA || m.RecordSHA != mapLandmark51RecordSHA || m.CacheSHA != mapLandmark51CacheSHA || m.Sampling != "bilinear-full-opaque" || m.Prompt != "map-landmark-51-r1.prompt.txt" || m.PromptSHA != mapLandmark51PromptSHA || m.Image.File != "map-landmark-51-r1.png" || m.Image.SHA != mapLandmark51ImageSHA || m.Image.Width != 1419 || m.Image.Height != 1109 {
		return fmt.Errorf("地圖格紋51配置不符")
	}
	if hash(pmap) != PMAPSHA || assets == nil || len(assets.Native) < 52 || assets.Materials == nil {
		return fmt.Errorf("地圖格紋51缺少完整來源")
	}
	entry, n := pmap[51*1004:52*1004], assets.Native[51]
	if hash(entry) != mapLandmark51RecordSHA || hash(entry[:804]) != mapLandmark51NativeSHA || n.Index != 51 || n.WidthBytes != 8 || n.Height != 25 || n.NativeSHA != mapLandmark51NativeSHA || assets.ByNative[mapLandmark51NativeSHA] != 52 {
		return fmt.Errorf("地圖格紋51原生來源不符")
	}
	if assets.Materials[52] != nil || assets.Actors[52] != nil || assets.Effects[52] != nil || assets.ActorSHA[52] != "" || assets.EffectSHA[52] != "" || assets.BattleActors[52] || assets.BattleAliases[52] != 0 {
		return fmt.Errorf("地圖格紋51識別衝突")
	}
	for key, id := range assets.ByNative {
		if id == 52 && key != mapLandmark51NativeSHA {
			return fmt.Errorf("地圖格紋51來源衝突")
		}
	}
	prompt, err := encounterRead(filepath.Join(dir, m.Prompt), 64*1024)
	if err != nil || hash(prompt) != mapLandmark51PromptSHA {
		return fmt.Errorf("地圖格紋51提示不符: %v", err)
	}
	raw, err = encounterRead(filepath.Join(dir, m.Image.File), 8*1024*1024)
	if err != nil {
		return err
	}
	if hash(raw) != mapLandmark51ImageSHA {
		return fmt.Errorf("地圖格紋51圖片不符")
	}
	config, err := png.DecodeConfig(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	if config.Width != 1419 || config.Height != 1109 {
		return fmt.Errorf("地圖格紋51尺寸不符")
	}
	decoded, err := png.Decode(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	tile, err := sampleMaterial(decoded, decoded.Bounds(), 192, 150, false)
	if err != nil {
		return err
	}
	if hash(tile.Pix) != mapLandmark51CacheSHA {
		return fmt.Errorf("地圖格紋51快取不符")
	}
	assets.Materials[52] = &graphicMaterial{64, 25, tile}
	return nil
}
