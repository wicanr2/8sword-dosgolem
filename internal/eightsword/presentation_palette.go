package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"

	"github.com/wicanr2/dosgolem/oracle"
)

const paletteStyle = "jade-gold-refined-r2"
const paletteSampleSHA = "a817d0b60b919f79f185efac72440880f7c28a211308db8de3e953f6337ea5d8"

type presentationPalette struct{}

func loadPresentationPalette(dir string, graphics *Graphics) (*presentationPalette, error) {
	path := filepath.Join(dir, "presentation-palette.json")
	info, err := os.Lstat(path)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() > 4096 {
		return nil, fmt.Errorf("HD 配色清單形態或大小不符")
	}
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	raw, err := io.ReadAll(io.LimitReader(f, 4097))
	if err != nil || len(raw) > 4096 {
		return nil, fmt.Errorf("HD 配色清單讀取或大小不符")
	}
	var m struct {
		Schema         int    `json:"schema"`
		SourceSHA      string `json:"source_sha256"`
		Style          string `json:"style"`
		ReferenceSHA   string `json:"style_reference_sha256"`
		ApprovedSample string `json:"approved_sample_sha256"`
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&m); err != nil {
		return nil, fmt.Errorf("HD 配色清單格式不符：%w", err)
	}
	if decoder.Decode(new(any)) != io.EOF || m.Schema != 1 || m.SourceSHA != PAMSHA || m.Style != paletteStyle || m.ReferenceSHA != ApprovedStyleSHA || m.ApprovedSample != paletteSampleSHA {
		return nil, fmt.Errorf("HD 配色來源、樣式或批准圖不符")
	}
	if graphics == nil || graphics.assets == nil {
		return nil, fmt.Errorf("HD 配色缺少已驗介面素材")
	}
	for _, id := range []uint16{47, 70, 71, 72} {
		if graphics.assets.Materials[id] == nil {
			return nil, fmt.Errorf("HD 配色缺少介面素材 %d", id)
		}
	}
	return &presentationPalette{}, nil
}

func (t *Tracker) paletteEnabled(p oracle.PlanarDisplay) bool {
	return t.palette != nil && t.loadSegment != 0 && t.graphics != nil && t.graphics.Stats.Bound &&
		p.Width == 640 && p.Height == 200 && p.Pitch == 80 && p.LineCompare >= 199 && p.Palette == canonicalEGA
}

// Inspect current-page ownership, rather than the previous frame's scene or
// historical string events. Source positions are fixed by spec 031.
func (t *Tracker) paletteSidebarVisible(p oracle.PlanarDisplay) bool {
	for row := 0; row < 7; row++ {
		found := false
		top := 12 + row*27
		for y := top; y < top+15 && !found; y++ {
			for x := 472; x < 624; x++ {
				off := (p.Start + uint32(y*p.Pitch+x/8)) & 65535
				c := t.owners[off*8+uint32(x%8)]
				g := t.glyphs[c.ID]
				if g == nil || g.Rune == ' ' || g.Width <= 0 || g.Source != uint16(990+row*20) {
					continue
				}
				left, first := x-int(c.Local)%g.Width, y-int(c.Local)/g.Width
				if left >= 472 && left < 624 && first == top {
					found = true
					break
				}
			}
		}
		if !found {
			return false
		}
	}
	return true
}

func (p *presentationPalette) ink(index uint8, original [3]uint8) [3]uint8 {
	if p != nil {
		switch index {
		case 10:
			return [3]uint8{223, 195, 121}
		case 12:
			return [3]uint8{215, 112, 89}
		}
	}
	return original
}

func (p *presentationPalette) backdrop(index uint8, x, y int, c cell, g *glyph, sidebar bool) ([3]uint8, bool) {
	if p == nil || !sidebar {
		return [3]uint8{}, false
	}
	if x >= 8 && x < 456 && y >= 192 && y < 198 {
		switch index {
		case 2:
			return [3]uint8{36, 91, 56}, true
		case 10:
			return [3]uint8{110, 167, 92}, true
		case 14:
			return [3]uint8{223, 190, 102}, true
		}
	}
	if index != 12 || x < 472 || x >= 624 || y < 12 || y >= 189 || (y-12)%27 >= 15 || g == nil || g.Width <= 0 || g.BG != 12 || c.ID != g.ID {
		return [3]uint8{}, false
	}
	row := (y - 12) / 27
	left, top := x-int(c.Local)%g.Width, y-int(c.Local)/g.Width
	if g.Source != uint16(990+row*20) || left < 472 || left >= 624 || top != 12+row*27 {
		return [3]uint8{}, false
	}
	return [3]uint8{128, 45, 39}, true
}
