package eightsword

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"image"
	"io"
	"math/bits"
	"os"
	"path/filepath"
	"strings"
)

// 049 reviewed immutable manifests. IDs derive from record/direction/height.
var encounterBatchManifests = [...]string{
	"411712ea8388b464e53f5bf323a61460e6ae3ba9654ba3e6fc138b45515d83bb",
	"631d75caa81200edde2dc0091badb72652f11059c567fe558fb92aa22c8c0f57",
	"22e3a2a35acd926bebab23b907fd0f822c99ce75390d7cdc4ad6ec3452122f88",
	"2a003a359455107046fcf8ce4c45ebb75527407873900718f8c4faabfb983509",
	"246e4b1da66eda3fadcfa7b26b2687c86ff9661fefe2b02809087e22ccd1d1da",
	"3d90da58b29ebec7104c76ba7f5fc6ea91435c2d3c6f3573fa92e686c1d3be77",
	"3cfb00a1cea67b7f3251673307d0c7e33638c91f5d2826201c44666abca6ad87",
	"f5afc029d4736d4cef7f0bada5a081adbcca661f29fa8d19bed2c2d66e44a95a",
	"8a350f0d0d620129e9e42c81570ae0cf9d1e2b1e04f34d261ed7a2f02ff9110d",
	"7d9194c4fc285c904dec42744da7a4706a2fac7f237c7e5d97f896bf5f48ed5f",
	"7c46d56608ea5b32b50f31a41b4e204e0550718a2213541486cc07f599006ae8",
	"3a4d5b3f63418919b9d6f2edef16a2bd9f0fc71845e32f867354d264e70b1c53",
	"b1ac3f54e8a3654f41c2ec28419237eaa523ebbbf75abd96e8322fb67ed9dae7",
	"2f14b11a01b431eb5560ffe604981a6b80ad73c6f7db68aed0c0266c116d04e4",
}

type encounterBatchAlias struct {
	Direction int    `json:"direction"`
	Height    int    `json:"height"`
	Native    string `json:"native_sha256"`
	Record    string `json:"record_sha256"`
	Cache     string `json:"cache_sha256"`
}

type encounterBatchManifest struct {
	Schema    int                   `json:"schema"`
	Source    string                `json:"source"`
	SHA       string                `json:"source_sha256"`
	PAM       string                `json:"pam_sha256"`
	Record    int                   `json:"record"`
	Style     string                `json:"style"`
	StyleSHA  string                `json:"style_reference_sha256"`
	Geometry  string                `json:"geometry"`
	Image     graphicPNG            `json:"image"`
	Target    []int                 `json:"target_rect"`
	Mirrored  bool                  `json:"sampled_mirrored"`
	Prompt    string                `json:"prompt_file"`
	PromptSHA string                `json:"prompt_sha256"`
	Caches    [2]string             `json:"cache_sha256"`
	Aliases   []encounterBatchAlias `json:"aliases"`
}

func encounterBatchPrefix(raw []byte, direction, height int) []byte {
	result := make([]byte, 4+48*height)
	binary.LittleEndian.PutUint16(result, 8)
	binary.LittleEndian.PutUint16(result[2:], uint16(height))
	for plane := 0; plane < 6; plane++ {
		for y := 0; y < height; y++ {
			for x := 0; x < 8; x++ {
				value := raw[4+plane*200+y*8+x]
				if direction == 1 {
					value = bits.Reverse8(raw[4+plane*200+y*8+7-x])
				}
				result[4+plane*height*8+y*8+x] = value
			}
		}
	}
	return result
}

func encounterBatchID(record, direction, height int) uint16 {
	return uint16(480 + record*26 + direction*13 + (height-1)/2)
}

func loadEncounterBatch(dir, root string, assets *GraphicsAssets) error {
	var failures []string
	for record := range encounterBatchManifests {
		if err := loadEncounterBatchGroup(dir, root, assets, record); err != nil {
			failures = append(failures, fmt.Sprintf("ENEMY %02d: %s", record, err))
		}
	}
	if len(failures) != 0 {
		return fmt.Errorf("%s", strings.Join(failures, "；"))
	}
	return nil
}

func loadEncounterBatchGroup(dir, root string, assets *GraphicsAssets, record int) error {
	if record < 0 || record >= len(encounterBatchManifests) {
		return fmt.Errorf("遭遇圖記錄越界")
	}
	raw, err := encounterRead(filepath.Join(dir, fmt.Sprintf("encounter-batch-%02d.json", record)), 32*1024)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	if hash(raw) != encounterBatchManifests[record] {
		return fmt.Errorf("遭遇圖批次清單雜湊不符")
	}
	var m encounterBatchManifest
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err := d.Decode(&m); err != nil {
		return err
	}
	if d.Decode(new(any)) != io.EOF {
		return fmt.Errorf("遭遇圖批次清單有尾隨資料")
	}
	if m.Schema != 1 || m.Source != "ENEMY.AY" || m.SHA != encounterSourceSHA || m.PAM != PAMSHA || m.Record != record || m.Style != "B-bright-painted-r1" || m.StyleSHA != ApprovedStyleSHA || m.Geometry != "native-alpha-bounds-r1" || m.Image.Index != 479+record*26 || m.Image.Sampling != "bitmap" || m.Mirrored != (record == 7 || record == 13) || m.Prompt != filepath.Base(m.Prompt) || len(m.Aliases) == 0 || len(m.Aliases) > 26 {
		return fmt.Errorf("遭遇圖批次來源／樣式不符")
	}
	if assets == nil || assets.ByNative == nil || assets.Actors == nil || assets.ActorSHA == nil {
		return fmt.Errorf("遭遇圖批次缺少基底")
	}
	source, err := encounterRead(filepath.Join(root, "ENEMY.AY"), 16856)
	if err != nil {
		return err
	}
	if len(source) != 16856 || hash(source) != encounterSourceSHA {
		return fmt.Errorf("遭遇圖批次原始資料不符")
	}
	prompt, err := encounterRead(filepath.Join(dir, m.Prompt), 64*1024)
	if err != nil || hash(prompt) != m.PromptSHA {
		return fmt.Errorf("遭遇圖批次提示不符: %v", err)
	}
	if _, err := encounterRead(filepath.Join(dir, m.Image.File), 8*1024*1024); err != nil {
		return err
	}
	im, err := loadGraphicPNG(dir, m.Image)
	if err != nil {
		return err
	}
	src, err := battleActorRect(m.Image.SourceRect, m.Image.Width, m.Image.Height)
	if err != nil {
		return err
	}
	dst, err := battleActorRect(m.Target, 192, 150)
	if err != nil {
		return err
	}
	sampled, err := sampleBattleActor(im, src, dst)
	if err != nil {
		return err
	}
	var tiles [2]*image.RGBA
	for direction := range tiles {
		tiles[direction] = image.NewRGBA(image.Rect(0, 0, 192, 150))
		for y := 0; y < 150; y++ {
			for x := 0; x < 192; x++ {
				sx := x
				if (direction == 1) != m.Mirrored {
					sx = 191 - x
				}
				copy(tiles[direction].Pix[y*768+x*4:y*768+x*4+4], sampled.Pix[y*sampled.Stride+sx*4:y*sampled.Stride+sx*4+4])
			}
		}
		if hash(tiles[direction].Pix) != m.Caches[direction] {
			return fmt.Errorf("遭遇圖批次快取不符")
		}
	}
	ids, natives := map[uint16]bool{}, map[string]bool{}
	for _, alias := range m.Aliases {
		if alias.Direction < 0 || alias.Direction > 1 || alias.Height < 1 || alias.Height > 25 || alias.Height%2 != 1 || m.Mirrored && alias.Direction == 1 {
			return fmt.Errorf("遭遇圖批次前綴範圍不符")
		}
		prefix := encounterBatchPrefix(source[record*1204:(record+1)*1204], alias.Direction, alias.Height)
		id := encounterBatchID(record, alias.Direction, alias.Height)
		if ids[id] || natives[alias.Native] || hash(prefix[:4+32*alias.Height]) != alias.Native || hash(prefix) != alias.Record || hash(tiles[alias.Direction].Pix[:alias.Height*6*768]) != alias.Cache {
			return fmt.Errorf("遭遇圖批次六平面／前綴不符")
		}
		if assets.ByNative[alias.Native] != 0 || assets.Actors[id] != nil || assets.Materials[id] != nil || assets.Effects[id] != nil || assets.ActorSHA[id] != "" || assets.EffectSHA[id] != "" || assets.BattleActors[id] || assets.BattleAliases[id] != 0 {
			return fmt.Errorf("遭遇圖批次識別衝突")
		}
		for _, mapped := range assets.ByNative {
			if mapped == id {
				return fmt.Errorf("遭遇圖批次識別已有來源")
			}
		}
		ids[id], natives[alias.Native] = true, true
	}
	// All checks precede this atomic group commit. Prefixes share immutable storage.
	for _, alias := range m.Aliases {
		id := encounterBatchID(record, alias.Direction, alias.Height)
		assets.ByNative[alias.Native] = id
		assets.ActorSHA[id] = alias.Record
		assets.Actors[id] = &graphicMaterial{64, alias.Height, tiles[alias.Direction].SubImage(image.Rect(0, 0, 192, alias.Height*6)).(*image.RGBA)}
	}
	return nil
}
