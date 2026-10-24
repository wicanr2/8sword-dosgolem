package eightsword

import (
	"encoding/json"
	"fmt"
	"image"
	"os"
	"path/filepath"
)

const battleMilitiaID uint16 = 107
const militiaImageSHA = "5173125ab4f02b170561b797d6ae043fc3c1c854f3ad61da791c3ba1e8aea620"
const militiaCacheSHA = "1c795ec9e8d67feca9a014d3b3511bc9ed9d9d115102e8042e4a16b3b4982fe5"
const militiaSourceSHA = "a7e02cf495800fac19c293688043f3af6eb6deaec1a61a581ed3f9d5b8b3e5f1"

type battleMilitiaManifest struct {
	Schema      int    `json:"schema"`
	Source      string `json:"source_file"`
	SourceSHA   string `json:"source_sha256"`
	Record      int    `json:"record"`
	Transform   string `json:"transform"`
	NativeSHA   string `json:"native_sha256"`
	RecordSHA   string `json:"record_sha256"`
	SourceIndex int    `json:"source_index"`
	BaseActor   uint16 `json:"base_actor_id"`
	BattleActor uint16 `json:"battle_actor_id"`
	Image       string `json:"image_file"`
	ImageSHA    string `json:"image_sha256"`
	CacheSHA    string `json:"cache_sha256"`
	Style       string `json:"style"`
	StyleSHA    string `json:"style_reference_sha256"`
}

// Spec 028: share the immutable 018 cache without reclassifying F2's source.
func loadBattleMilitia(dir, root string, assets *GraphicsAssets) error {
	raw, err := os.ReadFile(filepath.Join(dir, "battle-militia.json"))
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	var m battleMilitiaManifest
	if err = json.Unmarshal(raw, &m); err != nil {
		return err
	}
	if m.Schema != 1 || m.Source != "MAN01.EGG" || m.SourceSHA != militiaSourceSHA || m.Record != 0 || m.Transform != "mirror-six-planes" || m.NativeSHA != militiaNativeSHA || m.RecordSHA != militiaRecordSHA || m.SourceIndex != 84 || m.BaseActor != 85 || m.BattleActor != battleMilitiaID || m.Image != "militia-painted-r1.png" || m.ImageSHA != militiaImageSHA || m.CacheSHA != militiaCacheSHA || m.Style != "B-bright-painted-r1" || m.StyleSHA != ApprovedStyleSHA {
		return fmt.Errorf("戰場民兵清單來源／樣式不符")
	}
	if assets.Materials[battleBackgroundID] == nil || assets.ByNative[battleBackgroundNativeSHA] != battleBackgroundID {
		return fmt.Errorf("戰場民兵缺少已驗 GRO02 背景")
	}
	source, err := os.ReadFile(filepath.Join(root, m.Source))
	if err != nil {
		return err
	}
	if hash(source) != militiaSourceSHA {
		return fmt.Errorf("MAN01.EGG 來源雜湊不符")
	}
	png, err := os.ReadFile(filepath.Join(dir, m.Image))
	if err != nil {
		return err
	}
	if hash(png) != militiaImageSHA {
		return fmt.Errorf("共用民兵圖片 SHA-256 不符")
	}
	base := assets.Actors[85]
	if base == nil || base.NativeWidth != 88 || base.NativeHeight != 50 || base.Tile == nil || base.Tile.Bounds() != image.Rect(0, 0, 264, 300) || base.Tile.Stride != 264*4 || hash(base.Tile.Pix) != militiaCacheSHA || assets.ActorSHA[85] != militiaRecordSHA || assets.ByNative[militiaNativeSHA] != 85 || assets.BattleActors[85] {
		return fmt.Errorf("共用 F2 民兵快取／來源不符")
	}
	if assets.Materials[battleMilitiaID] != nil || assets.Actors[battleMilitiaID] != nil || assets.Effects[battleMilitiaID] != nil || assets.ActorSHA[battleMilitiaID] != "" || assets.BattleActors[battleMilitiaID] {
		return fmt.Errorf("戰場民兵識別重複")
	}
	if assets.BattleActors == nil {
		assets.BattleActors = map[uint16]bool{}
	}
	assets.Actors[battleMilitiaID] = base
	assets.ActorSHA[battleMilitiaID] = militiaRecordSHA
	assets.BattleActors[battleMilitiaID] = true
	return nil
}
