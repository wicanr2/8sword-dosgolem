// 053 READY. Pure source-command scene and native Go painter; no emulator input.
package eightsword

import (
	"fmt"
	"image"
	"image/color"
	"image/draw"
)

var endingPalette = [16][3]uint8{{0, 0, 0}, {0, 0, 170}, {0, 170, 0}, {0, 170, 170}, {170, 0, 0}, {170, 0, 170}, {170, 85, 0}, {170, 170, 170}, {85, 85, 85}, {85, 85, 255}, {85, 255, 85}, {85, 255, 255}, {255, 85, 85}, {255, 85, 255}, {255, 255, 85}, {255, 255, 255}}

type endingFontGlyph struct {
	Character string
	Ink       [4]int
}
type endingFontProfile struct {
	ID, Atlas string
	Glyphs    []endingFontGlyph
	glyphs    map[rune]endingFontGlyph
	image     image.Image
}
type endingCJKGlyph struct {
	Index                 int
	Character, Code, Bits string
}
type endingInputManifest struct {
	CJK      []endingCJKGlyph
	ASCII    []string
	Profiles []endingFontProfile
	Sources  map[string]string
	Files    map[string]string
}
type endingCommand struct {
	Kind                  string `json:"kind"`
	X, Y, W, H            int
	FG, BG                byte
	Code                  int
	Char                  rune
	SourceSHA, SourceFile string
	Pixels, Mask          []byte `json:"-"`
}
type endingPage struct {
	native   []byte
	ops      []*endingCommand
	stage    string
	glyphs   int
	revision uint64
}
type endingScene struct {
	pages  [4]*endingPage
	active int
	mode   bool
}
type endingArtSet struct {
	completion map[string]image.Image
	profiles   []endingFontProfile
	end7       image.Image
	titles     map[string]image.Image
	portraits  map[string]image.Image
	swords     image.Image
	duel       image.Image
	effects    map[string]image.Image
	pair       map[string]image.Image
	ring       image.Image
}

func newEndingScene() *endingScene {
	s := &endingScene{}
	for i := range s.pages {
		s.pages[i] = &endingPage{native: make([]byte, 0x4000*8)}
	}
	return s
}
func decodeEndingBitmap(raw []byte, kind, w, h int) ([]byte, []byte) {
	area := w / 8 * h
	pixels, mask := make([]byte, w*h), make([]byte, w*h)
	for at := range pixels {
		b, bit := at/8, uint(7-at%8)
		for plane := 0; plane < 4; plane++ {
			pixels[at] |= (raw[4+plane*area+b] >> bit & 1) << uint(plane)
		}
		if kind != 6 || raw[4+5*area+b]>>bit&1 != 0 {
			mask[at] = 1
		}
	}
	return pixels, mask
}
func (p *endingPage) apply(c *endingCommand) bool {
	if c.X < 0 || c.Y < 0 || c.X+c.W > 640 || c.Y+c.H > 200 {
		panic(fmt.Sprintf("source geometry %+v", c))
	}
	if c.Kind == "cjk" || c.Kind == "ascii" {
		if c.Char == ' ' && c.BG == 255 {
			empty := true
			for _, v := range c.Mask {
				if v != 0 {
					empty = false
					break
				}
			}
			if empty {
				return false
			}
		}
		r := image.Rect(c.X, c.Y, c.X+c.W, c.Y+c.H)
		for i := len(p.ops) - 1; i >= 0; i-- {
			prior := p.ops[i]
			if !r.Overlaps(image.Rect(prior.X, prior.Y, prior.X+prior.W, prior.Y+prior.H)) {
				continue
			}
			if prior.Kind == c.Kind && prior.Code == c.Code && prior.Char == c.Char && prior.X == c.X && prior.Y == c.Y && prior.W == c.W && prior.H == c.H && prior.FG == c.FG && prior.BG == c.BG {
				return false
			}
			break
		}
	}
	for y := 0; y < c.H; y++ {
		for x := 0; x < c.W; x++ {
			local, at := y*c.W+x, (c.Y+y)*640+c.X+x
			if c.Kind == "cjk" || c.Kind == "ascii" {
				if c.BG != 255 {
					p.native[at] = c.BG
				}
				if c.Mask[local] != 0 {
					p.native[at] = c.FG
				}
			} else if c.Mask[local] != 0 {
				p.native[at] = c.Pixels[local]
			}
		}
	}
	if c.X == 0 && c.Y == 0 && c.W == 640 && c.H == 200 && c.Kind != "cjk" && c.Kind != "ascii" {
		p.ops = nil
		p.glyphs = 0
	}
	p.ops = append(p.ops, c)
	p.revision++
	if c.SourceFile != "" {
		p.stage = c.SourceFile
	}
	if c.Kind == "cjk" || c.Kind == "ascii" {
		p.glyphs++
	}
	return true
}
func endingFill(out *image.RGBA, r image.Rectangle, c [3]uint8) {
	draw.Draw(out, r, image.NewUniform(color.RGBA{c[0], c[1], c[2], 255}), image.Point{}, draw.Src)
}

// Only source commands, colors and immutable textures enter this painter.
// It has no Oracle, VGA pixels or previous original RGB frame input.
func renderEndingPage(p *endingPage, palette [16][3]uint8, art endingArtSet, profile *endingFontProfile) *image.RGBA {
	out := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	endingFill(out, out.Bounds(), palette[0])
	for i, c := range p.ops {
		r := image.Rect(c.X*3, c.Y*6, (c.X+c.W)*3, (c.Y+c.H)*6)
		if profile != nil && c.Kind == "bitmap" {
			if texture := art.completion[c.SourceSHA]; texture != nil {
				if palette != endingPalette || texture.Bounds().Size() != r.Size() {
					panic("unreviewed completion geometry or palette")
				}
				if !endingSwordsRepeat(p.ops, i) {
					if c.SourceFile == "END4.AY" && (c.W == 176) || c.SourceFile == "END9.AY" {
						draw.Draw(out, r, texture, texture.Bounds().Min, draw.Src)
					} else {
						endingPairBlackBase(out, c)
						draw.Draw(out, r, texture, texture.Bounds().Min, draw.Over)
					}
				}
				continue
			}
		}
		if profile != nil && c.Kind == "bitmap" {
			if texture := art.pair[c.SourceSHA]; texture != nil {
				if palette != endingPalette || c.W != 136 || c.H != 50 || texture.Bounds().Size() != r.Size() {
					panic("unreviewed END6 pair geometry or palette")
				}
				if !endingSwordsRepeat(p.ops, i) {
					endingPairBlackBase(out, c)
					draw.Draw(out, r, texture, texture.Bounds().Min, draw.Over)
				}
				continue
			}
			if texture := art.effects[c.SourceSHA]; texture != nil {
				if palette != endingPalette || texture.Bounds().Size() != r.Size() {
					panic("unreviewed END2 effect geometry or palette")
				}
				if !endingSwordsRepeat(p.ops, i) {
					draw.Draw(out, r, texture, texture.Bounds().Min, draw.Over)
				}
				continue
			}
		}
		if profile != nil && c.Kind == "bitmap" && c.SourceSHA == endingDuelSource && art.duel != nil {
			if palette != endingPalette || art.duel.Bounds().Size() != r.Size() {
				panic("unreviewed END1 duel geometry or palette")
			}
			draw.Draw(out, r, art.duel, art.duel.Bounds().Min, draw.Src)
			continue
		}
		if profile != nil && c.Kind == "bitmap" && c.SourceSHA == endingRingSource && art.ring != nil {
			if palette != endingPalette || c.W != 232 || c.H != 105 || art.ring.Bounds().Size() != r.Size() {
				panic("unreviewed END3 ring geometry or palette")
			}
			if !endingSwordsRepeat(p.ops, i) {
				draw.Draw(out, r, art.ring, art.ring.Bounds().Min, draw.Over)
			}
			continue
		}
		if profile != nil && c.Kind == "bitmap" && c.SourceSHA == endingSwordsSource && art.swords != nil {
			if palette != endingPalette || art.swords.Bounds().Size() != r.Size() {
				panic("unreviewed END3 sword geometry or palette")
			}
			if !endingSwordsRepeat(p.ops, i) {
				draw.Draw(out, r, art.swords, art.swords.Bounds().Min, draw.Over)
			}
			continue
		}
		if profile != nil && c.Kind == "bitmap" {
			if texture := art.portraits[c.SourceSHA]; texture != nil {
				if palette != endingPalette || texture.Bounds().Size() != r.Size() {
					panic("unreviewed END5 portrait geometry or palette")
				}
				draw.Draw(out, r, texture, texture.Bounds().Min, draw.Src)
				continue
			}
		}
		if profile != nil && c.SourceFile == "END7.AY" && art.end7 != nil {
			if palette != endingPalette {
				panic("unreviewed ending art palette")
			}
			draw.Draw(out, r, art.end7, image.Point{}, draw.Src)
			continue
		}
		if profile != nil && c.SourceFile == "END8.AY" && art.titles[profile.ID] != nil {
			if palette != endingPalette {
				panic("unreviewed ending title palette")
			}
			endingFill(out, r, palette[0])
			draw.Draw(out, r, art.titles[profile.ID], image.Point{}, draw.Over)
			continue
		}
		if c.Kind == "cjk" || c.Kind == "ascii" {
			if c.BG != 255 {
				endingFill(out, r, palette[c.BG])
			}
			if profile != nil {
				if c.Char == ' ' {
					continue
				}
				g, ok := profile.glyphs[c.Char]
				if !ok {
					panic(fmt.Sprintf("HD ending glyph missing %U", c.Char))
				}
				iw, ih := g.Ink[2], g.Ink[3]
				dw, dh := min(iw, r.Dx()), min(ih, r.Dy())
				left, top := r.Min.X+(r.Dx()-dw)/2, r.Min.Y+(r.Dy()-dh)/2
				fg := palette[c.FG]
				for y := 0; y < dh; y++ {
					for x := 0; x < dw; x++ {
						_, _, _, alpha := profile.image.At(g.Ink[0]+x*iw/dw, g.Ink[1]+y*ih/dh).RGBA()
						a := uint32(alpha >> 8)
						at := (top+y)*out.Stride + (left+x)*4
						for k := 0; k < 3; k++ {
							out.Pix[at+k] = byte((uint32(fg[k])*a + uint32(out.Pix[at+k])*(255-a) + 127) / 255)
						}
					}
				}
				continue
			}
		}
		for y := 0; y < c.H; y++ {
			for x := 0; x < c.W; {
				at := y*c.W + x
				if c.Mask[at] == 0 {
					x++
					continue
				}
				index := c.FG
				if c.Kind != "cjk" && c.Kind != "ascii" {
					index = c.Pixels[at]
				}
				run := 1
				for x+run < c.W && c.Mask[at+run] != 0 {
					if c.Kind != "cjk" && c.Kind != "ascii" && c.Pixels[at+run] != index {
						break
					}
					run++
				}
				endingFill(out, image.Rect((c.X+x)*3, (c.Y+y)*6, (c.X+x+run)*3, (c.Y+y+1)*6), palette[index])
				x += run
			}
		}
	}
	return out
}
