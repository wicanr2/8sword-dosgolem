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

// Spec 042: exact six-plane mirrored records, not runtime pointer aliases.
var friendlyMan21Sources = [4]battleActorSource{
	{armyMan21NativeSHA, armyMan21RecordSHA},
	{"da1c2fb244ca0a7b5d63393c48f0a7a1ae7eeed0e176b85ac074b8e375cac69d", "d47ee736fa72a13fbc8946a7be8c5207cdd45ba98419b571c4d56685c1300905"},
	{"b0a35fc31719c01f5926e3bf94ae29b7ebb43ecd34f387063f5e76d75e05009f", "e24e8e88378e972239b075d818652bf8b288ef2c5000f8cb631d88ad9f4bb22a"},
	{"fdd487613a294ca7b0ec2f253d792c5f329fac2ac7ac5f49477b5dd6894a2315", "83f267fa78962beef351880accb8a8c39a03ebe7aed38e846fe5d5e6e4ff57e9"},
}

var friendlyMan21OriginalCaches = [4]string{
	armyMan21OriginalCacheSHA,
	"445a326ab52abba8fcd78426fde3ee2ef23e061b803169e2c680e59a843587f6",
	"fbf95dd4af01dfb54534d94b91d8558d6637ff10ff0ca8ed66c0aeee73485eaa",
	"5dfca14098b37bbc581ccc16ea2d76275d2bccda67089103485d35088210eb1c",
}

var friendlyMan21MirrorCaches = [4]string{
	armyMan21MirrorCacheSHA,
	"b831db71b4b04fcb3bd141fd8783327b5e3588c1c8856777b783097e6a73d817",
	"7db471d462815c66cc34060b40592e832e9cd0fce6f78f63d9a0098906feac62",
	"d53240c3c9aed41868fc194e45d34e918b7688238c8fdfeb7292af63ffa737f9",
}

type friendlyMan21Frame struct {
	Record        int    `json:"record"`
	SourceID      uint16 `json:"source_id"`
	TargetID      uint16 `json:"target_id"`
	NativeSHA     string `json:"native_sha256"`
	RecordSHA     string `json:"record_sha256"`
	OriginalCache string `json:"original_cache_sha256"`
	MirrorCache   string `json:"cache_sha256"`
}

type friendlyMan21Manifest struct {
	Schema    int                  `json:"schema"`
	Source    string               `json:"source_file"`
	SourceSHA string               `json:"source_sha256"`
	PAMSHA    string               `json:"pam_sha256"`
	Transform string               `json:"transform"`
	Style     string               `json:"style"`
	StyleSHA  string               `json:"style_reference_sha256"`
	Frames    []friendlyMan21Frame `json:"frames"`
}

func friendlyMan21Tile(m *graphicMaterial, digest string) bool {
	return m != nil && m.NativeWidth == 88 && m.NativeHeight == 50 && m.Tile != nil && m.Tile.Bounds() == image.Rect(0, 0, 264, 300) && m.Tile.Stride == 1056 && len(m.Tile.Pix) == 264*300*4 && hash(m.Tile.Pix) == digest
}

// All four records commit together. Source IDs 99–102 and F2's 150 stay intact.
func loadFriendlyMan21(dir, root string, assets *GraphicsAssets) error {
	raw, err := encounterRead(filepath.Join(dir, "battle-friendly-man21.json"), 16*1024)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	var m friendlyMan21Manifest
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err = d.Decode(&m); err != nil {
		return err
	}
	if d.Decode(new(any)) != io.EOF {
		return fmt.Errorf("友軍矮人清單有尾隨資料")
	}
	if m.Schema != 1 || m.Source != "MAN21.EGG" || m.SourceSHA != man21SourceSHA || m.PAMSHA != PAMSHA || m.Transform != "mirror-six-planes" || m.Style != "B-bright-painted-r1" || m.StyleSHA != ApprovedStyleSHA || len(m.Frames) != 4 {
		return fmt.Errorf("友軍矮人來源或樣式不符")
	}
	if assets == nil || assets.ByNative == nil || assets.Actors == nil || assets.ActorSHA == nil || assets.BattleActors == nil {
		return fmt.Errorf("友軍矮人缺少已驗圖像目錄")
	}
	if assets.ByNative[armyMan21NativeSHA] != 150 || assets.ActorSHA[150] != armyMan21RecordSHA || assets.BattleActors[150] || !friendlyMan21Tile(assets.Actors[150], armyMan21MirrorCacheSHA) {
		return fmt.Errorf("友軍矮人缺少已驗 F2 快取")
	}
	source, err := encounterRead(filepath.Join(root, "MAN21.EGG"), 13216)
	if err != nil {
		return err
	}
	if len(source) != 13216 || hash(source) != man21SourceSHA {
		return fmt.Errorf("友軍 MAN21.EGG 來源不符")
	}
	var tiles [4]*image.RGBA
	for i, frame := range m.Frames {
		id, baseID := uint16(152+i), uint16(99+i)
		fp := friendlyMan21Sources[i]
		if frame.Record != i || frame.SourceID != baseID || frame.TargetID != id || frame.NativeSHA != fp.Native || frame.RecordSHA != fp.Record || frame.OriginalCache != friendlyMan21OriginalCaches[i] || frame.MirrorCache != friendlyMan21MirrorCaches[i] {
			return fmt.Errorf("友軍矮人第%d筆配置不符", i)
		}
		base := assets.Actors[baseID]
		if !friendlyMan21Tile(base, frame.OriginalCache) || assets.ByNative[man21Sources[i].Native] != baseID || assets.ActorSHA[baseID] != man21Sources[i].Record || !assets.BattleActors[baseID] {
			return fmt.Errorf("友軍矮人第%d筆原向快取不符", i)
		}
		if assets.Materials[id] != nil || assets.Actors[id] != nil || assets.Effects[id] != nil || assets.ActorSHA[id] != "" || assets.EffectSHA[id] != "" || assets.BattleActors[id] || (i > 0 && assets.ByNative[fp.Native] != 0) {
			return fmt.Errorf("友軍矮人第%d筆識別重複", i)
		}
		for _, mapped := range assets.ByNative {
			if mapped == id {
				return fmt.Errorf("友軍矮人第%d筆已有其他原生來源", i)
			}
		}
		original := source[i*3304 : (i+1)*3304]
		mirrored := make([]byte, 3304)
		copy(mirrored, original[:4])
		for row := 4; row < 3304; row += 11 {
			for x := 0; x < 11; x++ {
				mirrored[row+x] = bits.Reverse8(original[row+10-x])
			}
		}
		if hash(mirrored) != fp.Record || hash(mirrored[:2204]) != fp.Native {
			return fmt.Errorf("友軍矮人第%d筆六平面不符", i)
		}
		tile := image.NewRGBA(image.Rect(0, 0, 264, 300))
		for y := 0; y < 300; y++ {
			for x := 0; x < 264; x++ {
				copy(tile.Pix[(y*264+x)*4:(y*264+x+1)*4], base.Tile.Pix[(y*264+263-x)*4:(y*264+264-x)*4])
			}
		}
		if hash(tile.Pix) != frame.MirrorCache {
			return fmt.Errorf("友軍矮人第%d筆鏡射快取不符", i)
		}
		tiles[i] = tile
	}
	for i, tile := range tiles {
		id := uint16(152 + i)
		assets.Actors[id] = &graphicMaterial{88, 50, tile}
		assets.ActorSHA[id] = friendlyMan21Sources[i].Record
		assets.BattleActors[id] = true
		if i > 0 {
			assets.ByNative[friendlyMan21Sources[i].Native] = id
		}
	}
	return nil
}
