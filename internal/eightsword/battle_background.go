package eightsword

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

const battleBackgroundNativeSHA = "b2262e970d5525826db47e9507787f9f3daddb2e00394934c728dc5d0ee8f763"
const battleBackgroundSourceSHA = "9e0182e0a576d62564ffcdccc6b9484bd0ff94e4f545ca43045f9aa1c1c45e4a"
const battleBackgroundID = uint16(86)

// This optional group commits only after every input has passed validation.
// A failure leaves the existing terrain, actors and Noto groups untouched.
func loadBattleBackground(dir, root string, assets *GraphicsAssets) error {
	raw, err := os.ReadFile(filepath.Join(dir, "battle-background.json"))
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	var m struct {
		Schema    int        `json:"schema"`
		SourceSHA string     `json:"source_sha256"`
		NativeSHA string     `json:"native_sha256"`
		Style     string     `json:"style"`
		StyleSHA  string     `json:"style_reference_sha256"`
		Image     graphicPNG `json:"image"`
	}
	if err = json.Unmarshal(raw, &m); err != nil {
		return err
	}
	if m.Schema != 1 || m.SourceSHA != battleBackgroundSourceSHA || m.NativeSHA != battleBackgroundNativeSHA || m.Style != "B-bright-painted-r1" || m.StyleSHA != ApprovedStyleSHA || m.Image.Index != 85 || m.Image.File != "battle-background-r1.png" || m.Image.Sampling != "bitmap" || len(m.Image.SourceRect) != 0 {
		return fmt.Errorf("戰場背景清單來源／樣式不符")
	}
	source, err := os.ReadFile(filepath.Join(root, "GRO02.EG"))
	if err != nil {
		return err
	}
	if hash(source) != battleBackgroundSourceSHA {
		return fmt.Errorf("GRO02.EG 來源雜湊不符")
	}
	decoded, err := loadGraphicPNG(dir, m.Image)
	if err != nil {
		return err
	}
	tile, err := sampleMaterial(decoded, decoded.Bounds(), 1920, 1200, false)
	if err != nil {
		return err
	}
	if assets.ByNative[battleBackgroundNativeSHA] != 0 || assets.Materials[battleBackgroundID] != nil || assets.Actors[battleBackgroundID] != nil {
		return fmt.Errorf("戰場背景來源識別重複")
	}
	assets.ByNative[battleBackgroundNativeSHA] = battleBackgroundID
	assets.Materials[battleBackgroundID] = &graphicMaterial{NativeWidth: 640, NativeHeight: 200, Tile: tile}
	return nil
}
