package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"os"
	"path/filepath"
)

type FontChoice struct {
	ID            string `json:"id"`
	Label         string `json:"label"`
	FallbackCount int    `json:"fallback_count"`
	font          *Assets
	title         image.Image
}
type fontChoices struct {
	choices    []FontChoice
	pam, story Assets
	title      image.Image
	current    string
}

func (e *Engine) loadFontChoices(dir string) {
	e.fonts = &fontChoices{current: "noto", choices: []FontChoice{{ID: "noto", Label: "Noto Black 900"}}}
	if e.Assets == nil {
		return
	}
	e.fonts.pam = *e.Assets
	if e.Story != nil {
		e.fonts.story = *e.Story.font
	}
	if e.Intro != nil {
		e.fonts.title = e.Intro.ink
	}
	raw, err := os.ReadFile(filepath.Join(dir, "font-choices.json"))
	if os.IsNotExist(err) {
		return
	}
	if err != nil {
		e.FontError = err.Error()
		return
	}
	var m struct {
		Schema   int `json:"schema"`
		Profiles []struct {
			ID, Label      string
			SourceSHA      string `json:"source_sha256"`
			Atlas          string
			AtlasSHA       string `json:"atlas_sha256"`
			Width, Height  int
			Glyphs         []FontGlyph
			Title          string
			TitleSHA       string `json:"title_sha256"`
			FallbackCount  int    `json:"fallback_count"`
			CJKFallbackSHA string `json:"cjk_fallback_sha256"`
		}
	}
	if err = json.Unmarshal(raw, &m); err != nil || m.Schema != 1 || len(m.Profiles) > 2 {
		e.FontError = "可選字型清單形狀不符"
		return
	}
	wanted := map[rune]bool{}
	for r := range e.Assets.Glyphs {
		wanted[r] = true
	}
	if e.Story != nil {
		for r := range e.Story.font.Glyphs {
			wanted[r] = true
		}
	}
	seen := map[string]bool{}
	for _, p := range m.Profiles {
		load := func() (FontChoice, error) {
			expected := map[string]string{"lishu": "c9d42eaac473b8ab0461cc6c2d1a1bac79b0babdf73974c7269ae17b81fd5d51", "caoshu": "cab396b91a5b7c0b4005a35891180d06e6751f5ac261fe680aec65c1ae209033"}
			if expected[p.ID] == "" || seen[p.ID] || p.SourceSHA != expected[p.ID] || len([]rune(p.Label)) > 40 || p.Label == "" || p.Atlas != "font-choice-"+p.ID+".png" || p.Title != "font-title-"+p.ID+".png" || p.Width != 1024 || p.Height != 3456 || len(p.Glyphs) != 853 || p.FallbackCount < 0 || p.FallbackCount > 853 {
				return FontChoice{}, fmt.Errorf("可選字型來源／形狀不符")
			}
			seen[p.ID] = true
			if p.CJKFallbackSHA != "" && p.CJKFallbackSHA != "93069d8e9e45d515cc421c971a79e6a5777704b348e36a9ef86578bf58adef77" {
				return FontChoice{}, fmt.Errorf("可選字型中文回退來源不符")
			}
			decode := func(name, sha string, w, h int) (image.Image, error) {
				b, err := os.ReadFile(filepath.Join(dir, name))
				if err != nil {
					return nil, err
				}
				if hash(b) != sha {
					return nil, fmt.Errorf("可選字型圖片 SHA-256 不符")
				}
				cfg, _, err := image.DecodeConfig(bytes.NewReader(b))
				if err != nil || cfg.Width != w || cfg.Height != h {
					return nil, fmt.Errorf("可選字型圖片尺寸不符")
				}
				im, _, err := image.Decode(bytes.NewReader(b))
				return im, err
			}
			atlas, err := decode(p.Atlas, p.AtlasSHA, 1024, 3456)
			if err != nil {
				return FontChoice{}, err
			}
			title, err := decode(p.Title, p.TitleSHA, 1776, 570)
			if err != nil {
				return FontChoice{}, err
			}
			bounds := image.Rectangle{}
			for y := 0; y < 570; y++ {
				for x := 0; x < 1776; x++ {
					_, _, _, alpha := title.At(x, y).RGBA()
					if alpha != 0 {
						bounds = bounds.Union(image.Rect(x, y, x+1, y+1))
					}
				}
			}
			if bounds.Empty() || !bounds.In(image.Rect(24, 24, 1752, 546)) {
				return FontChoice{}, fmt.Errorf("可選標題字墨越界")
			}
			f := &Assets{Atlas: atlas, Glyphs: map[rune]FontGlyph{}}
			for i, g := range p.Glyphs {
				runes := []rune(g.Character)
				if len(runes) != 1 {
					return FontChoice{}, fmt.Errorf("可選字型項目不是單字")
				}
				r := runes[0]
				if _, ok := f.Glyphs[r]; ok {
					return FontChoice{}, fmt.Errorf("可選字型重複字元")
				}
				cell := image.Rect(g.Cell[0], g.Cell[1], g.Cell[0]+g.Cell[2], g.Cell[1]+g.Cell[3])
				ink := image.Rect(g.Ink[0], g.Ink[1], g.Ink[0]+g.Ink[2], g.Ink[1]+g.Ink[3])
				if g.Cell != [4]int{i % 16 * 64, i / 16 * 64, 64, 64} || !cell.In(atlas.Bounds()) || g.Ink[2] < 0 || g.Ink[3] < 0 || !ink.In(cell) || (r != ' ' && (g.Ink[2] == 0 || g.Ink[3] == 0)) {
					return FontChoice{}, fmt.Errorf("可選字型字墨越界／空白")
				}
				f.Glyphs[r] = g
			}
			for r := range wanted {
				if _, ok := f.Glyphs[r]; !ok {
					return FontChoice{}, fmt.Errorf("可選字型缺字 %U", r)
				}
			}
			return FontChoice{ID: p.ID, Label: p.Label, FallbackCount: p.FallbackCount, font: f, title: title}, nil
		}
		choice, err := load()
		if err != nil {
			e.FontError += p.ID + ": " + err.Error() + "; "
			continue
		}
		e.fonts.choices = append(e.fonts.choices, choice)
	}
}

func (e *Engine) FontChoices() []FontChoice {
	if e.fonts == nil {
		return nil
	}
	return append([]FontChoice(nil), e.fonts.choices...)
}
func (e *Engine) FontID() string {
	if e.fonts == nil {
		return "noto"
	}
	return e.fonts.current
}
func (e *Engine) FontName() string {
	for _, c := range e.FontChoices() {
		if c.ID == e.FontID() {
			return c.Label
		}
	}
	return "Noto Black 900"
}
func (e *Engine) SetFont(id string) error {
	if e.fonts == nil || e.Assets == nil {
		return fmt.Errorf("HD 字型尚未載入")
	}
	var selected *FontChoice
	for i := range e.fonts.choices {
		if e.fonts.choices[i].ID == id {
			selected = &e.fonts.choices[i]
			break
		}
	}
	if selected == nil {
		return fmt.Errorf("字型選項不可用：%s", id)
	}
	if id == e.fonts.current {
		return nil
	}
	pam, story, title := e.fonts.pam, e.fonts.story, e.fonts.title
	if selected.font != nil {
		pam.Atlas, pam.Glyphs = selected.font.Atlas, selected.font.Glyphs
		story.Atlas, story.Glyphs = selected.font.Atlas, selected.font.Glyphs
		title = selected.title
	}
	e.Assets.Atlas, e.Assets.Glyphs = pam.Atlas, pam.Glyphs
	if e.Story != nil {
		e.Story.font.Atlas, e.Story.font.Glyphs = story.Atlas, story.Glyphs
	}
	if e.Intro != nil {
		e.Intro.ink = title
	}
	if e.Tracker != nil {
		e.Tracker.cachedFrame = nil
	}
	e.fonts.current = id
	return nil
}
