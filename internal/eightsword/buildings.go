package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

// Spec 051 READY groups only. LIVE4 inscription and LIVE6 art remain deferred.
var buildingGroups = [...]struct {
	Number                            int
	ID                                uint16
	SourceSHA, NativeSHA, ManifestSHA string
}{
	{1, 847, "dcd4da950f5bc32455c3fefae00c18d258d38017b1c8685772af38cc01b9fda6", "5c5e549514cc287c747ad075ebd7572cc265a4529f7af26325d74fc891202a4b", "4908cc83a254ba5260d38d1b915cf1ef0278b0f4d59a5524e6d32a63cbcb2c5c"},
	{3, 848, "624763a2922ecf16f88790970d9f536f8fa97a5371d7193332c87aa2cf4eeb00", "abc3df024aae9f21f829a549fa383e8f7f32ceb7031de8c938786a51a76d807b", "a817f6258bbe6193ee917a358b1c6be13f88aa860aa31e39f77a9b2841da126b"},
	{5, 850, "d98c76c44e3baeb5bcc4dc7a501a54990893043bd239dcebf1bb9a96667916ca", "aaa7766defa4fa81aebeec4a50d6d9f34f40fdc89f21a88f22450c83bc195845", "c83d2043884ecc27f9bab5858685599c6ebc5f9b901ad11bcd22fabdc555006d"},
}

func loadBuildings(dir, root string, assets *GraphicsAssets) error {
	var failures []string
	for i, group := range buildingGroups {
		if err := loadBuildingGroup(dir, root, assets, i); err != nil {
			failures = append(failures, fmt.Sprintf("LIVE%d: %s", group.Number, err))
		}
	}
	if len(failures) > 0 {
		return fmt.Errorf("%s", strings.Join(failures, "；"))
	}
	return nil
}

func loadBuildingGroup(dir, root string, assets *GraphicsAssets, index int) error {
	if index < 0 || index >= len(buildingGroups) {
		return fmt.Errorf("建築群組越界")
	}
	group := buildingGroups[index]
	raw, err := encounterRead(filepath.Join(dir, fmt.Sprintf("building-live%d.json", group.Number)), 16*1024)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	if hash(raw) != group.ManifestSHA {
		return fmt.Errorf("建築批次清單雜湊不符")
	}
	// Same whole-image schema as050, with a distinct fixed448x100 material.
	var m battleBackgroundBatchManifest
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err := d.Decode(&m); err != nil {
		return err
	}
	if d.Decode(new(any)) != io.EOF {
		return fmt.Errorf("建築批次清單有尾隨資料")
	}
	if m.Schema != 1 || m.Source != fmt.Sprintf("LIVE%d.AY", group.Number) || m.SourceSHA != group.SourceSHA || m.NativeSHA != group.NativeSHA || m.PAMSHA != PAMSHA || m.Style != "B-bright-painted-r1" || m.StyleSHA != ApprovedStyleSHA || m.Image.Index != int(group.ID)-1 || m.Image.File != fmt.Sprintf("live%d-hd-r1.png", group.Number) || m.Image.Width < 512 || m.Image.Width > 4096 || m.Image.Height < 512 || m.Image.Height > 4096 || m.Image.Sampling != "bitmap" || len(m.Image.SourceRect) != 0 || m.Prompt != fmt.Sprintf("live%d-hd-r1.prompt.txt", group.Number) {
		return fmt.Errorf("建築批次來源／配置不符")
	}
	if assets == nil || assets.Materials == nil || assets.ByNative == nil {
		return fmt.Errorf("建築批次缺少圖像目錄")
	}
	id := group.ID
	if assets.ByNative[group.NativeSHA] != 0 || assets.Materials[id] != nil || assets.Actors[id] != nil || assets.Effects[id] != nil || assets.ActorSHA[id] != "" || assets.EffectSHA[id] != "" || assets.BattleActors[id] || assets.BattleAliases[id] != 0 {
		return fmt.Errorf("建築批次識別衝突")
	}
	for _, mapped := range assets.ByNative {
		if mapped == id {
			return fmt.Errorf("建築識別已有來源")
		}
	}
	source, err := encounterRead(filepath.Join(root, m.Source), 1024*1024)
	if err != nil {
		return err
	}
	if hash(source) != group.SourceSHA {
		return fmt.Errorf("建築批次原始資料不符")
	}
	prompt, err := encounterRead(filepath.Join(dir, m.Prompt), 64*1024)
	if err != nil || hash(prompt) != m.PromptSHA {
		return fmt.Errorf("建築批次提示不符: %v", err)
	}
	if _, err := encounterRead(filepath.Join(dir, m.Image.File), 8*1024*1024); err != nil {
		return err
	}
	decoded, err := loadGraphicPNG(dir, m.Image)
	if err != nil {
		return err
	}
	tile, err := sampleMaterial(decoded, decoded.Bounds(), 1344, 600, false)
	if err != nil {
		return err
	}
	if hash(tile.Pix) != m.CacheSHA {
		return fmt.Errorf("建築批次快取不符")
	}
	assets.Materials[id] = &graphicMaterial{448, 100, tile}
	assets.ByNative[group.NativeSHA] = id
	return nil
}
