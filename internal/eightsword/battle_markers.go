package eightsword

import (
	"encoding/json"
	"fmt"
	"image"
	"image/color"
	"os"
	"path/filepath"
)

const choiSourceSHA = "5504591888f306aee2fce04015a81fca30e4e6c8bd48897c5103abcece780bcb"

var choiSources = [4]battleActorSource{
	{"7ac7f294b86bac089f02e31da273582cb86eacdec72e72b16d2166a9101ab07b", "6ae3f0c429cc980799719d97891d1dced08127c8ea8912e3ed9c87c0960039da"},
	{"f54f2868e20dd013b3c875b8e7a8db9be2006cab6485d75992d730d77f8bf3e1", "1a3ec6e34fad3c23799e7efda393becedb11ba0aaf3edb320c19bc0adef35a75"},
	{"b42275f5d69c48e29833ecb52b3f77d6549d254b8aaab81c1e72cf76a4c09e4c", "94745eff702f3d979c8b254bb15ca9715fa2d0f6f516a06d0cdd63d1c7d22cbf"},
	{"19c56f10ab5bebcd9a7e2889cc5595be9e176251c00c2a3bc90683dbec61b362", "efec0c4fb555aa09ff3a8e92add92dc5c4256258edf781ade1a509e1dd20fa6d"},
}

func isChoiSource(id uint16) bool { return id >= 108 && id <= 111 }

// Spec 029: a rotated read-only view preserves the single original PNG.
type choiRotatedImage struct {
	image.Image
	quarter int
}

func (r choiRotatedImage) At(x, y int) color.Color {
	s := r.Image.Bounds().Dx()
	switch r.quarter {
	case 1:
		return r.Image.At(y, s-1-x)
	case 2:
		return r.Image.At(s-1-x, s-1-y)
	case 3:
		return r.Image.At(s-1-y, x)
	default:
		return r.Image.At(x, y)
	}
}

func loadBattleMarkers(dir, root string, assets *GraphicsAssets) error {
	raw, err := os.ReadFile(filepath.Join(dir, "battle-choi.json"))
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}
	var m struct {
		Schema    int        `json:"schema"`
		Source    string     `json:"source_file"`
		SourceSHA string     `json:"source_sha256"`
		Style     string     `json:"style"`
		StyleSHA  string     `json:"style_reference_sha256"`
		Image     graphicPNG `json:"image"`
		Frames    []struct {
			Record    int    `json:"record"`
			Offset    int    `json:"file_offset"`
			Quarter   int    `json:"clockwise_quarters"`
			Native    string `json:"native_sha256"`
			RecordSHA string `json:"record_sha256"`
			CacheSHA  string `json:"cache_sha256"`
		} `json:"frames"`
	}
	if err = json.Unmarshal(raw, &m); err != nil {
		return err
	}
	if m.Schema != 1 || m.Source != "CHOI.EGG" || m.SourceSHA != choiSourceSHA || m.Style != "B-bright-painted-r1" || m.StyleSHA != ApprovedStyleSHA || len(m.Frames) != 4 {
		return fmt.Errorf("陰陽圖案來源／樣式不符")
	}
	v := m.Image
	if v.Index != 107 || v.File != "battle-choi-r1.png" || v.Width != 1254 || v.Height != 1254 || v.Sampling != "bitmap" || len(v.SourceRect) != 4 {
		return fmt.Errorf("陰陽圖案原圖／尺寸不符")
	}
	for i, want := range [4]int{101, 110, 1056, 1042} {
		if v.SourceRect[i] != want {
			return fmt.Errorf("陰陽圖案裁幅不符")
		}
	}
	if assets.Materials[battleBackgroundID] == nil || assets.ByNative[battleBackgroundNativeSHA] != battleBackgroundID {
		return fmt.Errorf("陰陽圖案缺少已驗 GRO02 背景")
	}
	source, err := os.ReadFile(filepath.Join(root, "CHOI.EGG"))
	if err != nil {
		return err
	}
	if hash(source) != choiSourceSHA {
		return fmt.Errorf("CHOI.EGG 來源雜湊不符")
	}
	picture, err := loadGraphicPNG(dir, v)
	if err != nil {
		return err
	}
	var staged [4]*image.RGBA
	rect := image.Rect(101, 110, 1157, 1152)
	for i, frame := range m.Frames {
		id, expected := uint16(108+i), choiSources[i]
		if frame.Record != i || frame.Offset != i*3304 || frame.Quarter != i || frame.Native != expected.Native || frame.RecordSHA != expected.Record {
			return fmt.Errorf("陰陽圖案第 %d 筆來源／方向不符", i)
		}
		if assets.ByNative[expected.Native] != 0 || assets.Effects[id] != nil || assets.Actors[id] != nil || assets.Materials[id] != nil {
			return fmt.Errorf("陰陽圖案識別重複")
		}
		staged[i], err = sampleBattleActor(choiRotatedImage{picture, i}, rect, image.Rect(24, 36, 243, 258))
		if err != nil {
			return err
		}
		if hash(staged[i].Pix) != frame.CacheSHA {
			return fmt.Errorf("陰陽圖案第 %d 筆快取雜湊不符", i)
		}
		rect = image.Rect(1254-rect.Max.Y, rect.Min.X, 1254-rect.Min.Y, rect.Max.X)
	}
	// No public table changes until the fourth source and cache have passed.
	if assets.Effects == nil {
		assets.Effects = map[uint16]*graphicMaterial{}
	}
	if assets.EffectSHA == nil {
		assets.EffectSHA = map[uint16]string{}
	}
	for i, tile := range staged {
		id := uint16(108 + i)
		assets.Effects[id] = &graphicMaterial{88, 50, tile}
		assets.EffectSHA[id] = choiSources[i].Record
		assets.ByNative[choiSources[i].Native] = id
	}
	return nil
}

func (g *Graphics) recordEffectFallback(id uint16) {
	if isChoiSource(id) {
		g.Stats.BattleMarkerFallbackCalls++
	} else {
		g.Stats.BattleEffectFallbackCalls++
	}
}
