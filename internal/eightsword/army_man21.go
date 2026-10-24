package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"io"
	"math/bits"
	"os"
	"path/filepath"
)

const armyMan21NativeSHA = "7e443adef3f02593c629d9c5d28c928c684b8664c2062ed320eb00c1d6c49b11"
const armyMan21RecordSHA = "5168810f892b3d4723a990d7c231f1a14801568166030fd9eef661140d937f30"
const armyMan21OriginalCacheSHA = "90f3e7d4039f3aca90f5921f79e04e1155c699fe923482a42c588f9a61148f4c"
const armyMan21MirrorCacheSHA = "0d2155399bd208382cc623fd4087ebf274bdc497f82d807b5d56b551f22f58ee"

// Spec 041: the exact F2/F3 source reuses an immutable copy of spec 026's cache.
func loadArmyMan21(dir, root string, assets *GraphicsAssets) error {
	raw, err := encounterRead(filepath.Join(dir, "army-man21.json"), 16*1024)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	var m struct {
		Schema    int    `json:"schema"`
		Source    string `json:"source_file"`
		SourceSHA string `json:"source_sha256"`
		Record    int    `json:"record"`
		Transform string `json:"transform"`
		SourceID  int    `json:"source_id"`
		TargetID  int    `json:"target_id"`
		StyleSHA  string `json:"style_reference_sha256"`
		CacheSHA  string `json:"cache_sha256"`
	}
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err = d.Decode(&m); err != nil {
		return err
	}
	if d.Decode(new(any)) != io.EOF {
		return fmt.Errorf("軍隊 MAN21 清單有尾隨資料")
	}
	if m.Schema != 1 || m.Source != "MAN21.EGG" || m.SourceSHA != man21SourceSHA || m.Record != 0 || m.Transform != "mirror-six-planes" || m.SourceID != 99 || m.TargetID != 150 || m.StyleSHA != ApprovedStyleSHA || m.CacheSHA != armyMan21MirrorCacheSHA {
		return fmt.Errorf("軍隊 MAN21 清單來源不符")
	}
	source, err := encounterRead(filepath.Join(root, m.Source), 13216)
	if err != nil {
		return err
	}
	if len(source) != 13216 || hash(source) != man21SourceSHA {
		return fmt.Errorf("軍隊 MAN21 原始來源 SHA-256 不符")
	}
	mirrored := make([]byte, 3304)
	copy(mirrored, source[:4])
	for row := 4; row < 3304; row += 11 {
		for x := 0; x < 11; x++ {
			mirrored[row+x] = bits.Reverse8(source[row+10-x])
		}
	}
	if hash(mirrored) != armyMan21RecordSHA || hash(mirrored[:2204]) != armyMan21NativeSHA {
		return fmt.Errorf("軍隊 MAN21 六塊來源不符")
	}
	original := assets.Actors[99]
	if original == nil || original.NativeWidth != 88 || original.NativeHeight != 50 || original.Tile == nil || original.Tile.Bounds() != image.Rect(0, 0, 264, 300) || original.Tile.Stride != 264*4 || hash(original.Tile.Pix) != armyMan21OriginalCacheSHA || assets.ByNative[man21Sources[0].Native] != 99 || assets.ActorSHA[99] != man21Sources[0].Record || !assets.BattleActors[99] {
		return fmt.Errorf("軍隊 MAN21 缺少已驗原向快取")
	}
	if assets.ByNative[armyMan21NativeSHA] != 0 || assets.Materials[150] != nil || assets.Actors[150] != nil || assets.Effects[150] != nil || assets.ActorSHA[150] != "" || assets.BattleActors[150] {
		return fmt.Errorf("軍隊 MAN21 識別重複")
	}
	tile := image.NewRGBA(original.Tile.Bounds())
	for y := 0; y < 300; y++ {
		for x := 0; x < 264; x++ {
			copy(tile.Pix[(y*264+x)*4:(y*264+x+1)*4], original.Tile.Pix[(y*264+263-x)*4:(y*264+264-x)*4])
		}
	}
	if hash(tile.Pix) != armyMan21MirrorCacheSHA {
		return fmt.Errorf("軍隊 MAN21 鏡射快取不符")
	}
	// Commit only after all source and cache checks. Never mutate source ID 99.
	assets.ByNative[armyMan21NativeSHA] = 150
	assets.ActorSHA[150] = armyMan21RecordSHA
	assets.Actors[150] = &graphicMaterial{88, 50, tile}
	return nil
}
