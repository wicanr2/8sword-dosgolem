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

// Spec 050: reviewed whole-image groups. No new guest addresses or rule values.
var battleBackgroundGroups = [...]struct{ Source, SourceSHA, NativeSHA, ManifestSHA string }{
	{"GRO03.EG", "aa86e444c75e3daad0a4591ca98fa9e68f871dbc5fbc0e632a1014936164a067", "e3361d72f32e0c5b4de129fc061dfc7b69fbf2df35692bd20abc2acdc66b7b4d", "ce5e0a0f70684f58c4c84182bf211a0e776b0a5778cd8fe994e5cab2a7af8767"},
	{"GRO04.EG", "f308fe3d711996673d0012daec158383ccf1a86cf9ed0d78779d551e1cd8c9d9", "c5499a5b60c3fae44a732faf771f84a8b1cb10018a0277e96e3b489a2bf76790", "dc653e132a4a2994b30f9c14e7ea14d3f729a63851b7597144683b2422fe5539"},
	{"GRO05.EG", "85a48e6b0a46d0b9f267634295982afca639828b09f6abb4fb13bb583c8f9626", "27d43c2e1aa3cbd08b9bfea555c5378d72ecb841566c81c97c73fe4a351e9d6e", "308f9e66fc3954086045c4ecc04de836168ba19311b354535f0f70d8ba0b911c"},
}

type battleBackgroundBatchManifest struct {
	battlePalaceManifest
	Prompt    string `json:"prompt_file"`
	PromptSHA string `json:"prompt_sha256"`
}

func isBattleBackgroundMaterial(id uint16) bool {
	return id == battleBackgroundID || id == battlePalaceID || id >= 844 && id <= 846
}

func loadBattleBackgroundBatch(dir, root string, assets *GraphicsAssets) error {
	var failures []string
	for i := range battleBackgroundGroups {
		if err := loadBattleBackgroundGroup(dir, root, assets, i); err != nil {
			failures = append(failures, battleBackgroundGroups[i].Source+": "+err.Error())
		}
	}
	if len(failures) > 0 {
		return fmt.Errorf("%s", strings.Join(failures, "；"))
	}
	return nil
}

func loadBattleBackgroundGroup(dir, root string, assets *GraphicsAssets, index int) error {
	if index < 0 || index >= len(battleBackgroundGroups) {
		return fmt.Errorf("戰場背景群組越界")
	}
	group := battleBackgroundGroups[index]
	raw, err := encounterRead(filepath.Join(dir, fmt.Sprintf("battle-gro%02d.json", index+3)), 16*1024)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	if hash(raw) != group.ManifestSHA {
		return fmt.Errorf("戰場背景批次清單雜湊不符")
	}
	var m battleBackgroundBatchManifest
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err := d.Decode(&m); err != nil {
		return err
	}
	if d.Decode(new(any)) != io.EOF {
		return fmt.Errorf("戰場背景批次清單有尾隨資料")
	}
	id := uint16(844 + index)
	if m.Schema != 1 || m.Source != group.Source || m.SourceSHA != group.SourceSHA || m.NativeSHA != group.NativeSHA || m.PAMSHA != PAMSHA || m.Style != "B-bright-painted-r1" || m.StyleSHA != ApprovedStyleSHA || m.Image.Index != int(id)-1 || m.Image.File != fmt.Sprintf("gro%02d-hd-r1.png", index+3) || m.Image.Width != 1586 || m.Image.Height != 992 || m.Image.Sampling != "bitmap" || len(m.Image.SourceRect) != 0 || m.Prompt != fmt.Sprintf("gro%02d-hd-r1.prompt.txt", index+3) {
		return fmt.Errorf("戰場背景批次來源／配置不符")
	}
	if assets == nil || assets.Materials == nil || assets.ByNative == nil {
		return fmt.Errorf("戰場背景批次缺少圖像目錄")
	}
	if assets.ByNative[group.NativeSHA] != 0 || assets.Materials[id] != nil || assets.Actors[id] != nil || assets.Effects[id] != nil || assets.ActorSHA[id] != "" || assets.EffectSHA[id] != "" || assets.BattleActors[id] || assets.BattleAliases[id] != 0 {
		return fmt.Errorf("戰場背景批次識別衝突")
	}
	for _, mapped := range assets.ByNative {
		if mapped == id {
			return fmt.Errorf("戰場背景識別已有來源")
		}
	}
	source, err := encounterRead(filepath.Join(root, group.Source), 1024*1024)
	if err != nil {
		return err
	}
	if hash(source) != group.SourceSHA {
		return fmt.Errorf("戰場背景批次原始資料不符")
	}
	prompt, err := encounterRead(filepath.Join(dir, m.Prompt), 64*1024)
	if err != nil || hash(prompt) != m.PromptSHA {
		return fmt.Errorf("戰場背景批次提示不符: %v", err)
	}
	if _, err := encounterRead(filepath.Join(dir, m.Image.File), 8*1024*1024); err != nil {
		return err
	}
	decoded, err := loadGraphicPNG(dir, m.Image)
	if err != nil {
		return err
	}
	tile, err := sampleMaterial(decoded, decoded.Bounds(), 1920, 1200, false)
	if err != nil {
		return err
	}
	if hash(tile.Pix) != m.CacheSHA {
		return fmt.Errorf("戰場背景批次快取不符")
	}
	// Commit only after source, image, prompt, cache and all ID checks pass.
	assets.Materials[id] = &graphicMaterial{640, 200, tile}
	assets.ByNative[group.NativeSHA] = id
	return nil
}
