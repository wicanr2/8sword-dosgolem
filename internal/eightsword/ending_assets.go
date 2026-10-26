// 053 READY. Independent ending fonts/art group, fixed source identities.
package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"os"
	"path/filepath"
)

const endingPAESHA = "8ae11b4c89f0361ed0a2d5b1859bbb4750047d37f0e26885e6903e4feb721a0c"
const endingManifestSHA = "f66ddeebfecd728ccca16e4c958e386046f2383ecf83a662b280582785ffbd7b"

type endingAssets struct {
	manifest      endingInputManifest
	art           endingArtSet
	fallbacks     []string
	portraitError string
	swordsError   string
}

func (a *endingAssets) profile(id string) *endingFontProfile {
	var fallback *endingFontProfile
	for i := range a.art.profiles {
		p := &a.art.profiles[i]
		if p.image != nil {
			if p.ID == id {
				return p
			}
			if p.ID == "noto" {
				fallback = p
			}
		}
	}
	return fallback
}

func loadEndingAssets(dir, root string) (*endingAssets, error) {
	raw, err := os.ReadFile(filepath.Join(dir, "ending.json"))
	if err != nil {
		return nil, fmt.Errorf("結局素材清單：%w", err)
	}
	if hash(raw) != endingManifestSHA {
		return nil, fmt.Errorf("結局素材清單SHA不符")
	}
	pae, err := os.ReadFile(filepath.Join(root, "PAE.AY"))
	if err != nil {
		return nil, err
	}
	if hash(pae) != endingPAESHA {
		return nil, fmt.Errorf("結局PAE來源不符")
	}
	a := &endingAssets{}
	if err = json.Unmarshal(raw, &a.manifest); err != nil {
		return nil, err
	}
	in := &a.manifest
	if len(in.CJK) != 127 || len(in.ASCII) != 256 || len(in.Profiles) != 3 || len(in.Files) != 7 || len(in.Sources) < 30 {
		return nil, fmt.Errorf("結局素材範圍不符")
	}
	load := func(name string, w, h int) (image.Image, error) {
		if filepath.Base(name) != name {
			return nil, fmt.Errorf("結局圖檔名稱不符")
		}
		data, er := os.ReadFile(filepath.Join(dir, name))
		if er != nil {
			return nil, er
		}
		if hash(data) != in.Files[name] {
			return nil, fmt.Errorf("結局圖片SHA不符：%s", name)
		}
		config, _, er := image.DecodeConfig(bytes.NewReader(data))
		if er != nil {
			return nil, er
		}
		if config.Width != w || config.Height != h {
			return nil, fmt.Errorf("結局圖片尺寸不符：%s", name)
		}
		im, _, er := image.Decode(bytes.NewReader(data))
		return im, er
	}
	a.art.profiles = in.Profiles
	a.art.titles = map[string]image.Image{}
	a.art.end7, err = load("ending-end7-r2.png", 1920, 1200)
	if err != nil {
		a.fallbacks = append(a.fallbacks, err.Error())
	}
	ids := []string{"noto", "lishu", "caoshu"}
	seen := map[string]bool{}
	for i := range a.art.profiles {
		profile := &a.art.profiles[i]
		valid := false
		for _, id := range ids {
			valid = valid || profile.ID == id
		}
		if !valid || seen[profile.ID] || len(profile.Glyphs) != 128 {
			return nil, fmt.Errorf("結局字型設定不符")
		}
		seen[profile.ID] = true
		profile.image, err = load(profile.Atlas, 1024, 512)
		if err != nil {
			if profile.ID == "noto" {
				return nil, err
			}
			a.fallbacks = append(a.fallbacks, err.Error())
			continue
		}
		profile.glyphs = map[rune]endingFontGlyph{}
		for _, g := range profile.Glyphs {
			r := []rune(g.Character)
			if len(r) != 1 || g.Ink[0] < 0 || g.Ink[1] < 0 || g.Ink[2] < 1 || g.Ink[3] < 1 || g.Ink[0]+g.Ink[2] > 1024 || g.Ink[1]+g.Ink[3] > 512 {
				return nil, fmt.Errorf("結局字墨範圍不符")
			}
			profile.glyphs[r[0]] = g
		}
		a.art.titles[profile.ID], err = load("ending-title-"+profile.ID+".png", 1776, 570)
		if err != nil {
			a.fallbacks = append(a.fallbacks, err.Error())
		}
	}
	a.art.portraits, err = loadEndingPortrait(dir, root)
	if err != nil {
		a.portraitError = err.Error()
		a.fallbacks = append(a.fallbacks, err.Error())
	}
	a.art.swords, err = loadEndingSwords(dir, root)
	if err != nil {
		a.swordsError = err.Error()
		a.fallbacks = append(a.fallbacks, err.Error())
	}
	return a, nil
}
