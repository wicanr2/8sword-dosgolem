package eightsword

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"image"
	_ "image/png"
	"os"
	"path/filepath"
)

const PAMSHA = "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"
const NotoSHA = "3cffb10242b4b7e6edd439ebf3bd7e392345525e093ea08149e0a0158a1b5151"

type FontGlyph struct {
	Character   string `json:"character"`
	Big5        string `json:"big5"`
	SourceIndex int    `json:"source_index"`
	Cell        [4]int `json:"cell"`
	Ink         [4]int `json:"ink"`
}
type fontManifest struct {
	Schema        int    `json:"schema"`
	SourceSHA     string `json:"source_sha256"`
	FontSHA       string `json:"font_sha256"`
	Family        string `json:"family"`
	Weight        int    `json:"weight"`
	Atlas         string `json:"atlas"`
	AtlasSHA      string `json:"atlas_sha256"`
	Width, Height int
	Glyphs        []FontGlyph `json:"glyphs"`
}
type Assets struct {
	Atlas  image.Image
	Glyphs map[rune]FontGlyph
	CJK    []rune
}

func (a *Assets) DrawRune(out *image.RGBA, r rune, rect image.Rectangle, color [3]uint8) {
	g, ok := a.Glyphs[r]
	if !ok || r == ' ' {
		return
	}
	iw, ih := g.Ink[2], g.Ink[3]
	if iw <= 0 || ih <= 0 {
		return
	}
	dw, dh := iw, ih
	if dw > rect.Dx() {
		dw = rect.Dx()
	}
	if dh > rect.Dy() {
		dh = rect.Dy()
	}
	left, top := rect.Min.X+(rect.Dx()-dw)/2, rect.Min.Y+(rect.Dy()-dh)/2
	for y := 0; y < dh; y++ {
		for x := 0; x < dw; x++ {
			ox, oy := left+x, top+y
			if !image.Pt(ox, oy).In(out.Bounds()) {
				continue
			}
			_, _, _, alpha := a.Atlas.At(g.Ink[0]+x*iw/dw, g.Ink[1]+y*ih/dh).RGBA()
			v := uint32(alpha >> 8)
			at := oy*out.Stride + ox*4
			for c := 0; c < 3; c++ {
				out.Pix[at+c] = uint8((uint32(color[c])*v + uint32(out.Pix[at+c])*(255-v) + 127) / 255)
			}
		}
	}
}

func hash(data []byte) string { s := sha256.Sum256(data); return hex.EncodeToString(s[:]) }

func LoadAssets(dir string, pam []byte) (*Assets, error) {
	if hash(pam) != PAMSHA {
		return nil, fmt.Errorf("PAM.AY 來源雜湊不符")
	}
	raw, err := os.ReadFile(filepath.Join(dir, "font.json"))
	if err != nil {
		return nil, err
	}
	var m fontManifest
	if err = json.Unmarshal(raw, &m); err != nil {
		return nil, err
	}
	if m.Schema != 1 || m.SourceSHA != PAMSHA || m.FontSHA != NotoSHA || m.Family != "Noto Sans CJK TC" || m.Weight != 900 {
		return nil, fmt.Errorf("字型清單來源／字重不符")
	}
	if m.Atlas != "font.png" || len(m.Glyphs) != 731 {
		return nil, fmt.Errorf("字型清單形狀不符")
	}
	png, err := os.ReadFile(filepath.Join(dir, m.Atlas))
	if err != nil {
		return nil, err
	}
	if hash(png) != m.AtlasSHA {
		return nil, fmt.Errorf("字型圖片 SHA-256 不符")
	}
	f, err := os.Open(filepath.Join(dir, m.Atlas))
	if err != nil {
		return nil, err
	}
	defer f.Close()
	atlas, _, err := image.Decode(f)
	if err != nil {
		return nil, err
	}
	if atlas.Bounds() != image.Rect(0, 0, m.Width, m.Height) {
		return nil, fmt.Errorf("字型圖片尺寸不符")
	}
	out := &Assets{Atlas: atlas, Glyphs: map[rune]FontGlyph{}, CJK: make([]rune, 636)}
	for i, g := range m.Glyphs {
		runes := []rune(g.Character)
		if len(runes) != 1 {
			return nil, fmt.Errorf("字型項目不是單字")
		}
		r := runes[0]
		if _, exists := out.Glyphs[r]; exists {
			return nil, fmt.Errorf("字型項目重複 %U", r)
		}
		cell := image.Rect(g.Cell[0], g.Cell[1], g.Cell[0]+g.Cell[2], g.Cell[1]+g.Cell[3])
		ink := image.Rect(g.Ink[0], g.Ink[1], g.Ink[0]+g.Ink[2], g.Ink[1]+g.Ink[3])
		if g.Cell[2] != 64 || g.Cell[3] != 64 || !cell.In(atlas.Bounds()) || !ink.In(cell) {
			return nil, fmt.Errorf("字框越界 %U", r)
		}
		if i < 636 {
			if g.SourceIndex != i || g.Big5 != hex.EncodeToString(pam[0x2463e+i*2:0x24640+i*2]) {
				return nil, fmt.Errorf("原始 Big5 字碼對應不符：%d", i)
			}
			out.CJK[i] = r
		} else if r != rune(32+i-636) {
			return nil, fmt.Errorf("ASCII 字集順序不符")
		}
		out.Glyphs[r] = g
	}
	return out, nil
}
