package ownedworld

import (
	"errors"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"strconv"
	"unicode/utf8"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

// Spec 030 READY. These fields occupy reserved, undrawn parts of the original
// row. The guest never selects a substitute native kind for an extended unit.
var originalDismissNameEnds = map[uint16]uint16{
	0x77cd: 0x7801, 0x7850: 0x7884, 0x78ad: 0x78e1,
	0x7930: 0x7964, 0x798d: 0x79c1, 0x7a10: 0x7a44,
	0x7a6d: 0x7aa1, 0x7af0: 0x7b24, 0x7baf: 0x7be3,
}

func originalOpenKBID(id string) bool {
	for _, known := range openKBArtIDs {
		if id == known {
			return true
		}
	}
	return false
}

type originalArmyFields struct {
	View                                    *originalArmyReview
	Art                                     *hdUnitArtwork
	Fallback                                map[string]*game.Assets
	Boxes                                   map[string]image.Rectangle
	Cached                                  *image.RGBA
	Key                                     string
	Texts                                   []armyUIText
	SkippedRows, SkippedNames, Frames, Held uint64
}

func newOriginalArmyFields(v *originalArmyReview, fonts *armyUIFonts, art *hdUnitArtwork) *originalArmyFields {
	f := &originalArmyFields{View: v, Art: art, Fallback: map[string]*game.Assets{}, Boxes: map[string]image.Rectangle{}}
	for id, atlas := range fonts.Atlases {
		a := &game.Assets{Atlas: atlas, Glyphs: map[rune]game.FontGlyph{}}
		for ch, cell := range fonts.Glyphs {
			ink := image.Rectangle{}
			for y := cell.Min.Y; y < cell.Max.Y; y++ {
				for x := cell.Min.X; x < cell.Max.X; x++ {
					_, _, _, alpha := atlas.At(x, y).RGBA()
					if alpha != 0 {
						ink = ink.Union(image.Rect(x, y, x+1, y+1))
					}
				}
			}
			a.Glyphs[ch] = game.FontGlyph{Character: string(ch), Ink: [4]int{ink.Min.X, ink.Min.Y, ink.Dx(), ink.Dy()}}
		}
		f.Fallback[id] = a
	}
	return f
}

func originalFieldGeometry(slot int) (image.Rectangle, [3]image.Rectangle, [3]image.Rectangle) {
	col, row := slot/3, slot%3
	x, y := 24+232*col, 13+60*row
	icon := image.Rect(x*3, y*6, (x+88)*3, (y+50)*6)
	var labels, values [3]image.Rectangle
	end := min((24+232*(col+1))*3-24, 456*3)
	for i := 0; i < 3; i++ {
		top := (y + 16*i) * 6
		labels[i] = image.Rect((112+232*col)*3, top, (152+232*col)*3, top+90)
		values[i] = image.Rect((152+232*col)*3, top, end, top+90)
	}
	return icon, labels, values
}

func (f *originalArmyFields) glyph(ch rune, font string) (*game.Assets, game.FontGlyph, bool) {
	a := f.View.Engine.Assets
	if a != nil {
		if g, ok := a.Glyphs[ch]; ok {
			return a, g, true
		}
	}
	a = f.Fallback[font]
	if a == nil {
		return nil, game.FontGlyph{}, false
	}
	g, ok := a.Glyphs[ch]
	return a, g, ok
}

func (f *originalArmyFields) validate(rows [6]originalReviewRow) error {
	for _, row := range rows {
		if !row.Host {
			continue
		}
		if !f.View.Engine.HD || f.Art == nil || f.Art.Images[row.Unit] == nil || utf8.RuneCountInString(row.Name) > 4 || row.Name == "" {
			return errors.New("original army host field image/name unavailable")
		}
		for _, font := range []string{"noto", "lishu", "caoshu"} {
			for _, ch := range row.Name + "種類:數量月薪0123456789" {
				// Check the fallback group as well: Engine.Assets changes on F10.
				a := f.Fallback[font]
				if a == nil {
					return errors.New("original army field font unavailable")
				}
				if _, ok := a.Glyphs[ch]; !ok {
					return fmt.Errorf("original army missing glyph %U", ch)
				}
			}
		}
		if f.Boxes[row.Unit].Empty() {
			im := f.Art.Images[row.Unit]
			box := image.Rectangle{}
			for y := im.Rect.Min.Y; y < im.Rect.Max.Y; y++ {
				for x := im.Rect.Min.X; x < im.Rect.Max.X; x++ {
					if im.RGBAAt(x, y).A != 0 {
						box = box.Union(image.Rect(x, y, x+1, y+1))
					}
				}
			}
			if box.Empty() {
				return errors.New("original army empty image")
			}
			f.Boxes[row.Unit] = box
		}
	}
	return nil
}

func (f *originalArmyFields) text(out *image.RGBA, role, text string, safe image.Rectangle, ink [3]uint8) {
	count := utf8.RuneCountInString(text)
	digitWidth := 24
	if count > 0 {
		digitWidth = min(digitWidth, safe.Dx()/count)
	}
	x := safe.Min.X
	bounds := image.Rectangle{}
	for _, ch := range text {
		advance := 48
		if ch < 128 {
			advance = digitWidth
		}
		cell := image.Rect(x, safe.Min.Y, x+advance, safe.Max.Y)
		if !cell.In(safe) {
			panic("original army field overflow")
		}
		a, g, ok := f.glyph(ch, f.View.Engine.FontID())
		if !ok {
			panic("original army missing admitted glyph")
		}
		iw, ih := min(g.Ink[2], cell.Dx()), min(g.Ink[3], cell.Dy())
		if iw > 0 && ih > 0 {
			left, top := cell.Min.X+(cell.Dx()-iw)/2, cell.Min.Y+(cell.Dy()-ih)/2
			bounds = bounds.Union(image.Rect(left, top, left+iw, top+ih))
		}
		a.DrawRune(out, ch, cell, ink)
		x += advance
	}
	f.Texts = append(f.Texts, armyUIText{Role: role, Text: text, Rect: uiBox(safe), Ink: uiBox(bounds), Size: 90})
}

func (f *originalArmyFields) icon(out *image.RGBA, id string, area image.Rectangle) {
	im, box := f.Art.Images[id], f.Boxes[id]
	w, h := area.Dx(), area.Dy()
	if w*box.Dy() > h*box.Dx() {
		w = h * box.Dx() / box.Dy()
	} else {
		h = w * box.Dy() / box.Dx()
	}
	left, top := area.Min.X+(area.Dx()-w)/2, area.Min.Y+(area.Dy()-h)/2
	for y := 0; y < h; y++ {
		for x := 0; x < w; x++ {
			c := im.RGBAAt(box.Min.X+x*box.Dx()/w, box.Min.Y+y*box.Dy()/h)
			at := out.PixOffset(left+x, top+y)
			a := uint32(c.A)
			for k, s := range []byte{c.R, c.G, c.B} {
				out.Pix[at+k] = uint8(uint32(s) + (uint32(out.Pix[at+k])*(255-a)+127)/255)
			}
		}
	}
}

// The source page has no native sprite/name/numeric drawing for Host rows.
// Fill all reserved fields before the frontend uploads one immutable frame.
func composeOriginalArmyFields(v *originalArmyReview, base *image.RGBA) (*image.RGBA, []armyUIText) {
	if v == nil || v.Fields == nil {
		return base, nil
	}
	f := v.Fields
	if !v.Active {
		if v.ReturnPending && f.Cached != nil {
			f.Held++
			return f.Cached, f.Texts
		}
		f.Cached = nil
		f.Key = ""
		f.Texts = nil
		return base, nil
	}
	if !v.Ready {
		if f.Cached != nil {
			f.Held++
			return f.Cached, f.Texts
		}
		return base, nil
	}
	used := false
	for _, r := range v.Rows {
		used = used || r.Host
	}
	if !used {
		f.Cached = nil
		f.Key = ""
		f.Texts = nil
		return base, nil
	}
	if err := v.checkSnapshot(); err != nil {
		panic(&worldArmyPortFault{err.Error()})
	}
	selected := -1
	if v.Mode == 2 && v.Port.OriginalDismiss != nil {
		selected = v.Port.OriginalDismiss.State()["original_dismiss_selected"].(int)
	}
	key := fmt.Sprintf("%p:%s:%d:%d:%s", base, v.Token, v.Opens, selected, v.Engine.FontID())
	if f.Cached != nil && f.Key == key {
		return f.Cached, f.Texts
	}
	if base == nil || base.Bounds() != image.Rect(0, 0, 1920, 1200) {
		panic("original army source frame shape")
	}
	out := image.NewRGBA(base.Bounds())
	draw.Draw(out, out.Bounds(), base, base.Rect.Min, draw.Src)
	f.Texts = nil
	gold, warm := [3]uint8{223, 195, 121}, [3]uint8{255, 241, 181}
	for slot, row := range v.Rows {
		if !row.Host {
			continue
		}
		icon, labels, values := originalFieldGeometry(slot)
		f.icon(out, row.Unit, icon)
		for i, label := range []string{"種類:", "數量:", "月薪:"} {
			f.text(out, fmt.Sprintf("original:%d:label:%d", slot, i), label, labels[i], gold)
		}
		if slot == selected {
			r := values[0]
			r.Max.X = r.Min.X + utf8.RuneCountInString(row.Name)*48
			draw.Draw(out, r, image.NewUniform(color.RGBA{255, 85, 85, 255}), image.Point{}, draw.Src)
		}
		for i, value := range []string{row.Name, strconv.FormatUint(uint64(row.Count), 10), strconv.FormatUint(row.Monthly, 10)} {
			f.text(out, fmt.Sprintf("original:%d:value:%d", slot, i), value, values[i], warm)
		}
	}
	f.Cached = out
	f.Key = key
	f.Frames++
	return out, f.Texts
}
