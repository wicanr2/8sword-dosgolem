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
	battlePalaceID        = uint16(151)
	battlePalaceSourceSHA = "4e5c5c6569cc6fc9f1e585b7048c099228f787da041d46ded685e034b7594103"
	battlePalaceNativeSHA = "79e2c0119edf4ca9f87fb14dbee47de49afca4eee8f8cc2711c4c58c275e7be9"
	battlePalaceImageSHA  = "521a7a99e37cd437b6cf54835002df42dde1ef29c9bc551af0a1bfaec10230f6"
	battlePalaceCacheSHA  = "ee95cca6642a98ed4bdcb14415e19553d6efbb558b4fbf375ca2ba119abd9955"
)

type battlePalaceManifest struct {
	Schema    int        `json:"schema"`
	Source    string     `json:"source_file"`
	SourceSHA string     `json:"source_sha256"`
	NativeSHA string     `json:"native_sha256"`
	PAMSHA    string     `json:"pam_sha256"`
	Style     string     `json:"style"`
	StyleSHA  string     `json:"style_reference_sha256"`
	CacheSHA  string     `json:"cache_sha256"`
	Image     graphicPNG `json:"image"`
}

// Spec 046: a separate optional group. A failure cannot remove GRO02 or actors.
func loadBattlePalaceBackground(dir, root string, assets *GraphicsAssets) error {
	raw, err := encounterRead(filepath.Join(dir, "battle-palace-background.json"), 16*1024)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	var m battlePalaceManifest
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err = d.Decode(&m); err != nil {
		return err
	}
	if d.Decode(new(any)) != io.EOF {
		return fmt.Errorf("攻城背景清單有尾隨資料")
	}
	if m.Schema != 1 || m.Source != "GRO01.EG" || m.SourceSHA != battlePalaceSourceSHA || m.NativeSHA != battlePalaceNativeSHA || m.PAMSHA != PAMSHA || m.Style != "B-bright-painted-r1" || m.StyleSHA != ApprovedStyleSHA || m.CacheSHA != battlePalaceCacheSHA {
		return fmt.Errorf("攻城背景來源或樣式不符")
	}
	v := m.Image
	if v.Index != 150 || v.File != "battle-palace-background-r1.png" || v.SHA != battlePalaceImageSHA || v.Width != 1586 || v.Height != 992 || v.Sampling != "bitmap" || len(v.SourceRect) != 0 {
		return fmt.Errorf("攻城背景圖片配置不符")
	}
	if assets == nil || assets.Materials == nil || assets.ByNative == nil {
		return fmt.Errorf("攻城背景缺少圖像目錄")
	}
	if assets.ByNative[battlePalaceNativeSHA] != 0 || assets.Materials[battlePalaceID] != nil || assets.Actors[battlePalaceID] != nil || assets.Effects[battlePalaceID] != nil || assets.ActorSHA[battlePalaceID] != "" || assets.EffectSHA[battlePalaceID] != "" || assets.BattleActors[battlePalaceID] {
		return fmt.Errorf("攻城背景識別重複")
	}
	for _, id := range assets.ByNative {
		if id == battlePalaceID {
			return fmt.Errorf("攻城背景已有其他原生來源")
		}
	}
	source, err := encounterRead(filepath.Join(root, "GRO01.EG"), 1024*1024)
	if err != nil {
		return err
	}
	if hash(source) != battlePalaceSourceSHA {
		return fmt.Errorf("GRO01.EG 來源雜湊不符")
	}
	raw, err = encounterRead(filepath.Join(dir, v.File), 8*1024*1024)
	if err != nil {
		return err
	}
	if hash(raw) != battlePalaceImageSHA {
		return fmt.Errorf("攻城背景圖片 SHA-256 不符")
	}
	config, err := png.DecodeConfig(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	if config.Width != 1586 || config.Height != 992 {
		return fmt.Errorf("攻城背景圖片尺寸不符")
	}
	decoded, err := png.Decode(bytes.NewReader(raw))
	if err != nil {
		return err
	}
	tile, err := sampleMaterial(decoded, decoded.Bounds(), 1920, 1200, false)
	if err != nil {
		return err
	}
	if hash(tile.Pix) != battlePalaceCacheSHA {
		return fmt.Errorf("攻城背景快取不符")
	}
	assets.Materials[battlePalaceID] = &graphicMaterial{640, 200, tile}
	assets.ByNative[battlePalaceNativeSHA] = battlePalaceID
	return nil
}

// The whole rectangle must belong to one validated background, including its
// transparent actor pixels. Page offsets are physical VGA byte offsets.
func (g *Graphics) battleBackgroundKnown(first uint32, width, height int) bool {
	if g == nil || g.assets == nil || width != 88 || height != 50 || uint64(first)+uint64((height-1)*80+11) > 65536 || len(g.owners) < 65536*8 {
		return false
	}
	id := g.owners[first*8].ID
	if id != battleBackgroundID && id != battlePalaceID {
		return false
	}
	m := g.assets.Materials[id]
	if m == nil || m.NativeWidth != 640 || m.NativeHeight != 200 || m.Tile == nil || m.Tile.Bounds() != image.Rect(0, 0, 1920, 1200) || m.Tile.Stride != 1920*4 || len(m.Tile.Pix) != 1920*1200*4 {
		return false
	}
	for y := 0; y < height; y++ {
		for x := 0; x < width; x++ {
			c := g.owners[(first+uint32(y*80+x/8))*8+uint32(x%8)]
			if c.ID != id || c.Local >= 640*200 {
				return false
			}
		}
	}
	return true
}
