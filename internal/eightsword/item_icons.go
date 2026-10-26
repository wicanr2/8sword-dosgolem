package eightsword

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
)

const itemIconsManifestSHA = "b2404cd42918fd36987554205eece12d55ff04d5365c5a1378c56645dc8d30b2"
const itemIconsSourceSHA = "9849714498718f6616644ad717906cc426c3f3f5f335cdb99dbcc8173c8dbe12"

type itemIconsManifest struct {
	Schema    int    `json:"schema"`
	Source    string `json:"source_file"`
	SourceSHA string `json:"source_sha256"`
	Style     string `json:"style"`
	StyleSHA  string `json:"style_reference_sha256"`
	Sampling  string `json:"sampling"`
	Entries   []struct {
		Index     int        `json:"source_index"`
		Offset    int        `json:"offset"`
		NativeSHA string     `json:"native_sha256"`
		RecordSHA string     `json:"record_sha256"`
		CacheSHA  string     `json:"cache_sha256"`
		Prompt    string     `json:"prompt_file"`
		PromptSHA string     `json:"prompt_sha256"`
		Image     graphicPNG `json:"image"`
	} `json:"entries"`
}

// Spec052: only fixed inventory icons may blend over owned source colors.
// Every caller still checks the complete six-plane source against ActorSHA.
func itemIconSource(id, entry uint16, widthBytes, height int) bool {
	return itemIconID(id) && entry == 0x4f2 && widthBytes == 4 && height == 16
}

func itemIconID(id uint16) bool { return id >= 852 && id <= 867 }

func loadItemIcons(dir, root string, assets *GraphicsAssets) error {
	raw, err := encounterRead(filepath.Join(dir, "man-items.json"), 32*1024)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	if hash(raw) != itemIconsManifestSHA {
		return fmt.Errorf("器物圖示清單雜湊不符")
	}
	var m itemIconsManifest
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err := d.Decode(&m); err != nil {
		return err
	}
	if d.Decode(new(any)) != io.EOF {
		return fmt.Errorf("器物圖示清單有尾隨資料")
	}
	if m.Schema != 1 || m.Source != "MAN.AY" || m.SourceSHA != itemIconsSourceSHA || m.Style != "B-bright-painted-r1" || m.StyleSHA != ApprovedStyleSHA || m.Sampling != "bilinear-full-premultiplied-alpha-lte3" || len(m.Entries) != 16 {
		return fmt.Errorf("器物圖示配置不符")
	}
	if assets == nil || assets.ByNative == nil || assets.Actors == nil || assets.ActorSHA == nil {
		return fmt.Errorf("器物圖示缺少目錄")
	}
	source, err := encounterRead(filepath.Join(root, "MAN.AY"), 1024*1024)
	if err != nil {
		return err
	}
	if len(source) != 22660 || hash(source) != itemIconsSourceSHA {
		return fmt.Errorf("器物原版來源不符")
	}
	staged := map[uint16]*graphicMaterial{}
	for slot, entry := range m.Entries {
		index, offset := 12+slot, 14448+slot*388
		if slot >= 8 {
			index = 21 + slot - 8
			offset = 19556 + (slot-8)*388
		}
		id := uint16(852 + slot)
		if entry.Index != index || entry.Offset != offset || entry.Image.Index != int(id)-1 || entry.Image.Width != 1254 || entry.Image.Height != 1254 || entry.Image.Sampling != "bitmap" || len(entry.Image.SourceRect) != 0 {
			return fmt.Errorf("器物圖示順序／尺寸不符")
		}
		variant := 1
		if index == 16 || index >= 21 {
			variant = 2
		}
		if entry.Image.File != fmt.Sprintf("man-%02d-r%d.png", index, variant) || entry.Prompt != fmt.Sprintf("man-%02d-r%d.prompt.txt", index, variant) {
			return fmt.Errorf("器物圖示檔名不符")
		}
		record := source[offset : offset+388]
		if binary.LittleEndian.Uint16(record) != 4 || binary.LittleEndian.Uint16(record[2:]) != 16 || hash(record) != entry.RecordSHA || hash(record[:260]) != entry.NativeSHA {
			return fmt.Errorf("器物記錄不符")
		}
		if assets.Materials[id] != nil || assets.Actors[id] != nil || assets.Effects[id] != nil || assets.ActorSHA[id] != "" || assets.EffectSHA[id] != "" || assets.BattleActors[id] || assets.BattleAliases[id] != 0 || assets.ByNative[entry.NativeSHA] != 0 {
			return fmt.Errorf("器物識別衝突")
		}
		for _, mapped := range assets.ByNative {
			if mapped == id {
				return fmt.Errorf("器物已有來源別名")
			}
		}
		prompt, err := encounterRead(filepath.Join(dir, entry.Prompt), 64*1024)
		if err != nil || hash(prompt) != entry.PromptSHA {
			return fmt.Errorf("器物提示不符: %v", err)
		}
		if _, err := encounterRead(filepath.Join(dir, entry.Image.File), 8*1024*1024); err != nil {
			return err
		}
		decoded, err := loadGraphicPNG(dir, entry.Image)
		if err != nil {
			return err
		}
		tile, err := sampleActorSize(decoded, 32, 16)
		if err != nil {
			return err
		}
		if hash(tile.Pix) != entry.CacheSHA {
			return fmt.Errorf("器物快取不符")
		}
		staged[id] = &graphicMaterial{32, 16, tile}
	}
	for slot, entry := range m.Entries {
		id := uint16(852 + slot)
		assets.Actors[id] = staged[id]
		assets.ActorSHA[id] = entry.RecordSHA
		assets.ByNative[entry.NativeSHA] = id
	}
	return nil
}
