package eightsword

import (
	"bytes"
	"encoding/hex"
	"fmt"
	"image"
	"sort"

	"github.com/wicanr2/dosgolem/oracle"
)

type cell struct {
	ID    uint32
	Local uint16
	Ink   bool
}
type glyph struct {
	ID     uint32
	Rune   rune
	Source uint16
	Width  int
	FG, BG uint8
	Native [30]byte
	Before [240]uint8
	Rows   [15]uint32
	Refs   int
}
type TrackerStats struct {
	Full, Half, PixelWrites, CopiedBytes, InvalidatedBytes, ComposedFrames uint64
	ErasedInk, RenderedGlyphs, MissingGlyphs                               uint64
	CachedFrames                                                           uint64
	BoundLoadSegment                                                       uint16
	Errors                                                                 []string
}
type Tracker struct {
	o                               *oracle.Oracle
	assets                          *Assets
	pam                             []byte
	owners                          []cell
	glyphs                          map[uint32]*glyph
	next                            uint32
	active                          *glyph
	fontSeg, stringSeg, loadSegment uint16
	Stats                           TrackerStats
	Scene                           string
	VisibleScene                    string
	visibleSources                  map[uint16]bool
	stringSource                    uint16
	Strings                         []StringEvent
	revision, cachedRevision        uint64
	cachedDisplay                   oracle.PlanarDisplay
	cachedIndexed                   []uint8
	cachedFrame                     *image.RGBA
	graphics                        *Graphics
}
type StringEvent struct {
	Step   uint64
	Source uint16
	X, Y   int
	Text   string
}

func NewTracker(o *oracle.Oracle, a *Assets, pam []byte) *Tracker {
	t := &Tracker{o: o, assets: a, pam: pam, owners: make([]cell, 65536*8), glyphs: map[uint32]*glyph{}}
	o.ObserveVideoWrites(t.write)
	o.ObserveVideoModeChanges(func(oracle.VideoModeChange) { t.clear() })
	return t
}
func (t *Tracker) clear() {
	clear(t.owners)
	clear(t.glyphs)
	t.active = nil
	if t.graphics != nil {
		t.graphics.clear()
	}
	t.VisibleScene = ""
	t.visibleSources = nil
	t.stringSource = 0
	t.cachedFrame = nil
	t.revision++
}
func (t *Tracker) fail(s string) {
	if len(t.Stats.Errors) < 16 {
		t.Stats.Errors = append(t.Stats.Errors, s)
	}
}

// Bind runs between bounded emulation chunks, after the original overlay load.
func (t *Tracker) Bind() {
	if t.loadSegment != 0 {
		return
	}
	for _, e := range t.o.Overlays() {
		if e.Name != "pam.ay" && e.Name != "PAM.AY" {
			continue
		}
		if e.Seg != e.Reloc {
			t.fail("PAM 載入段與重定位段不一致")
			return
		}
		load := e.Seg
		t.fontSeg = load + 0x998
		t.stringSeg = load + 0x13c2
		table := oracle.Addr{Seg: load + 0x1d78, Off: 0x5a4e}
		if !bytes.Equal(t.o.Bytes(table, 1272), t.pam[0x2463e:0x24b36]) {
			t.fail(fmt.Sprintf("PAM 執行期字碼表不符 load=%04X dseg=%04X prefix=%x", load, table.Seg, t.o.Bytes(table, 8)))
			return
		}
		font := oracle.Addr{Seg: t.fontSeg, Off: 0x10}
		if !bytes.Equal(t.o.Bytes(font, 636*30), t.pam[0xae00:0xf888]) {
			t.fail("PAM 執行期字模不符")
			return
		}
		for _, site := range []struct {
			seg, off uint16
			source   int
		}{{t.fontSeg, 0x4a98, 0xf888}, {t.stringSeg, 0xb86, 0x15c16}} {
			if !bytes.Equal(t.o.Bytes(oracle.Addr{Seg: site.seg, Off: site.off}, 16), t.pam[site.source:site.source+16]) {
				t.fail("PAM 繪字入口不符")
				return
			}
		}
		t.loadSegment = load
		t.Stats.BoundLoadSegment = load
		t.o.OnCall(oracle.Addr{Seg: t.fontSeg, Off: 0x4a98}, func(*oracle.Oracle) { t.begin(true) })
		t.o.OnCall(oracle.Addr{Seg: t.stringSeg, Off: 0xb86}, func(*oracle.Oracle) { t.begin(false) })
		t.o.OnCall(oracle.Addr{Seg: t.stringSeg, Off: 0xae3}, func(*oracle.Oracle) { t.observeString() })
		if t.graphics != nil {
			t.graphics.bind()
		}
		return
	}
}

func (t *Tracker) observeString() {
	off := t.o.Arg(0)
	t.stringSource = off
	ds := t.o.Regs().DS
	raw := []byte{}
	for i := 0; i < 1024; i++ {
		b := t.o.Byte(oracle.Addr{Seg: ds, Off: off + uint16(i)})
		if b == 0 {
			break
		}
		raw = append(raw, b)
	}
	text := []rune{}
	for i := 0; i < len(raw); {
		if raw[i] < 128 {
			text = append(text, rune(raw[i]))
			i++
			continue
		}
		found := false
		if i+1 < len(raw) {
			for index := 0; index < 636; index++ {
				at := 0x2463e + index*2
				if raw[i] == t.pam[at] && raw[i+1] == t.pam[at+1] {
					text = append(text, t.assets.CJK[index])
					i += 2
					found = true
					break
				}
			}
		}
		if !found {
			text = append(text, '\ufffd')
			i++
		}
	}
	ev := StringEvent{t.o.Steps(), off, int(t.o.Arg(1)) * 8, int(t.o.Arg(2)), string(text)}
	t.Strings = append(t.Strings, ev)
	if len(t.Strings) > 32 {
		t.Strings = append([]StringEvent(nil), t.Strings[len(t.Strings)-32:]...)
	}
	switch off {
	case 158, 218, 278:
		t.Scene = "main-menu"
	case 338, 398:
		t.Scene = "new-game-confirm"
	case 990, 1010, 1030, 1050, 1070, 1090, 1110:
		t.Scene = "map"
	case 1170, 1182, 1194, 1206, 1218, 1230, 1242:
		t.Scene = "character"
	case 18046:
		t.Scene = "battle-result"
	case 12742, 12762, 12782, 12802, 12822, 12842:
		t.Scene = "system-menu"
	}
}

func (t *Tracker) begin(full bool) {
	if t.loadSegment == 0 {
		return
	}
	r := t.o.Regs()
	arg := t.o.Arg(0)
	x, y := int(t.o.Arg(1)), int(t.o.Arg(2))
	if x < 0 || x >= 80 || y < 0 || y+15 > 200 {
		t.active = nil
		t.fail(fmt.Sprintf("字格越界：%d,%d", x, y))
		return
	}
	ds := r.DS
	dest := t.o.Word(oracle.Addr{Seg: ds, Off: 0x748a})
	fg := t.o.Byte(oracle.Addr{Seg: ds, Off: 0x748c})
	bg := t.o.Byte(oracle.Addr{Seg: ds, Off: 0x748d})
	if dest < 0xa000 || dest >= 0xb000 || fg > 15 || (bg > 15 && bg != 255) {
		t.active = nil
		t.fail("未知字模目的地或顏色")
		return
	}
	g := &glyph{Width: 8, FG: fg, BG: bg, Source: t.stringSource}
	stride := 1
	if full {
		if arg%30 != 0 || int(arg/30) >= len(t.assets.CJK) {
			t.active = nil
			t.fail("未知全形字模偏移")
			return
		}
		index := int(arg / 30)
		g.Rune = t.assets.CJK[index]
		g.Width = 16
		stride = 2
		copy(g.Native[:], t.pam[0xae00+index*30:0xae00+(index+1)*30])
		t.Stats.Full++
	} else {
		if arg < 32 || arg > 126 {
			t.active = nil
			t.Stats.MissingGlyphs++
			t.fail(fmt.Sprintf("未知半形字碼 %02X", arg))
			return
		}
		g.Rune = rune(arg)
		copy(g.Native[:], t.pam[0x24b38+int(arg)*15:0x24b38+(int(arg)+1)*15])
		t.Stats.Half++
	}
	if _, ok := t.assets.Glyphs[g.Rune]; !ok {
		t.active = nil
		t.Stats.MissingGlyphs++
		return
	}
	tableOff := uint16(6)
	tableSeg := t.stringSeg
	for row := 0; row < 15; row++ {
		rowOff := t.o.Word(oracle.Addr{Seg: tableSeg, Off: tableOff + uint16((y+row)*2)})
		off := uint32(dest-0xa000)*16 + uint32(rowOff) + uint32(x)
		if off+uint32(stride) > 65536 {
			t.active = nil
			t.fail("字模列超出 VGA 平面")
			return
		}
		g.Rows[row] = off
		for col := 0; col < stride; col++ {
			old, _ := t.o.PlanarBytePixels(off + uint32(col))
			for bit := 0; bit < 8; bit++ {
				at := (off+uint32(col))*8 + uint32(bit)
				value := old[bit]
				prior := t.owners[at]
				if prior.ID != 0 && prior.Ink {
					if p := t.glyphs[prior.ID]; p != nil {
						value = p.Before[prior.Local]
					}
				}
				g.Before[row*g.Width+col*8+bit] = value
			}
		}
	}
	t.next++
	g.ID = t.next
	t.glyphs[g.ID] = g
	t.active = g
}

func (t *Tracker) set(at uint32, v cell) {
	old := t.owners[at]
	if old == v {
		return
	}
	t.revision++
	if old.ID != 0 {
		if g := t.glyphs[old.ID]; g != nil {
			g.Refs--
		}
	}
	t.owners[at] = v
	if v.ID != 0 {
		if g := t.glyphs[v.ID]; g != nil {
			g.Refs++
		}
	}
}

func (t *Tracker) copyByte(destination, source uint32) {
	if t.graphics != nil {
		t.graphics.copyByte(destination, source)
	}
	var saved [8]cell
	for bit := range saved {
		saved[bit] = t.owners[source*8+uint32(bit)]
	}
	for bit, v := range saved {
		t.set(destination*8+uint32(bit), v)
	}
}
func (t *Tracker) write(w oracle.VideoWrite) {
	if t.loadSegment == 0 || w.Offset >= 65536 {
		return
	}
	t.Stats.PixelWrites++
	// The source and destination registers still point to the current byte.
	if w.CS == t.stringSeg && (w.IP == 0x364 || w.IP == 0x3d7 || w.IP == 0x47f) && w.WriteMode == 1 {
		r := t.o.Regs()
		source := uint32(r.DS)*16 + uint32(r.SI)
		if source >= 0xa0000 && source < 0xb0000 {
			t.copyByte(w.Offset, source-0xa0000)
			t.Stats.CopiedBytes++
			return
		}
	}
	mask := uint8(255)
	if t.graphics != nil {
		if source, ok := t.graphics.backgroundSource(w); ok {
			t.copyByte(w.Offset, source)
		}
		mask = t.graphics.write(w)
	}
	isGlyph := (w.CS == t.fontSeg && (w.IP == 0x4b80 || w.IP == 0x4bda)) || (w.CS == t.stringSeg && w.IP == 0xc71)
	if isGlyph && t.active != nil {
		g := t.active
		stride := g.Width / 8
		for row, off := range g.Rows {
			if w.Offset < off || w.Offset >= off+uint32(stride) {
				continue
			}
			col := int(w.Offset - off)
			native := g.Native[row*stride+col]
			for bit := 0; bit < 8; bit++ {
				t.set(w.Offset*8+uint32(bit), cell{ID: g.ID, Local: uint16(row*g.Width + col*8 + bit), Ink: native&(0x80>>uint(bit)) != 0})
			}
			return
		}
	}
	for bit := 0; bit < 8; bit++ {
		if mask&(0x80>>uint(bit)) != 0 {
			t.set(w.Offset*8+uint32(bit), cell{})
		}
	}
	t.Stats.InvalidatedBytes++
}

type drawGroup struct {
	ID   uint32
	X, Y int
}

func sortedGroups(groups map[drawGroup]bool) []drawGroup {
	out := make([]drawGroup, 0, len(groups))
	for g := range groups {
		out = append(out, g)
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].ID != out[j].ID {
			return out[i].ID < out[j].ID
		}
		if out[i].Y != out[j].Y {
			return out[i].Y < out[j].Y
		}
		return out[i].X < out[j].X
	})
	return out
}

// Compose never writes to DOS. The baseline is scaled with the game's 2:1
// vertical pixel aspect; text is drawn from the checked Black 900 atlas.
func (t *Tracker) Compose() *image.RGBA {
	p, ok := t.o.PlanarDisplay()
	if !ok || p.Width != 640 || p.Height != 200 {
		return nil
	}
	_, _, indexed := t.o.Screen()
	if t.cachedFrame != nil && t.cachedRevision == t.revision && t.cachedDisplay == p && bytes.Equal(t.cachedIndexed, indexed) {
		t.Stats.CachedFrames++
		return t.cachedFrame
	}
	out := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	groups := map[drawGroup]bool{}
	for y := 0; y < 200; y++ {
		for x := 0; x < 640; x++ {
			at := y*640 + x
			color := p.Palette[indexed[at]&15]
			off := (p.Start + uint32(y*p.Pitch+x/8)) & 65535
			c := t.owners[off*8+uint32(x%8)]
			if c.ID != 0 {
				if g := t.glyphs[c.ID]; g != nil {
					lx, ly := int(c.Local)%g.Width, int(c.Local)/g.Width
					groups[drawGroup{g.ID, x - lx, y - ly}] = true
					if c.Ink && indexed[at] == g.FG {
						bg := g.Before[c.Local]
						if g.BG != 255 {
							bg = g.BG
						}
						color = p.Palette[bg&15]
						t.Stats.ErasedInk++
					}
				}
			}
			row := y*6*out.Stride + x*3*4
			for dx := 0; dx < 3; dx++ {
				o := row + dx*4
				out.Pix[o] = color[0]
				out.Pix[o+1] = color[1]
				out.Pix[o+2] = color[2]
				out.Pix[o+3] = 255
			}
		}
		start := y * 6 * out.Stride
		for dy := 1; dy < 6; dy++ {
			copy(out.Pix[start+dy*out.Stride:start+(dy+1)*out.Stride], out.Pix[start:start+out.Stride])
		}
	}
	// Stable order avoids map iteration changing overlapping alpha blends.
	if t.graphics != nil {
		t.graphics.paint(out, p)
	}
	ordered := sortedGroups(groups)
	sources := map[uint16]bool{}
	for _, key := range ordered {
		g := t.glyphs[key.ID]
		if g != nil {
			sources[g.Source] = true
		}
		if g == nil || g.Rune == ' ' {
			continue
		}
		fg, exists := t.assets.Glyphs[g.Rune]
		if !exists {
			continue
		}
		iw, ih := fg.Ink[2], fg.Ink[3]
		if iw <= 0 || ih <= 0 {
			continue
		}
		dw := iw
		if dw > g.Width*3 {
			dw = g.Width * 3
		}
		dh := ih
		if dh > 90 {
			dh = 90
		}
		left := key.X*3 + (g.Width*3-dw)/2
		top := key.Y*6 + (90-dh)/2
		color := p.Palette[g.FG]
		if g.FG == 14 {
			color = [3]uint8{255, 241, 181}
		}
		for yy := 0; yy < dh; yy++ {
			oy := top + yy
			if oy < 0 || oy >= 1200 {
				continue
			}
			sy := fg.Ink[1] + yy*ih/dh
			for xx := 0; xx < dw; xx++ {
				ox := left + xx
				if ox < 0 || ox >= 1920 {
					continue
				}
				nx, ny := ox/3, oy/6
				off := (p.Start + uint32(ny*p.Pitch+nx/8)) & 65535
				owner := t.owners[off*8+uint32(nx%8)]
				if owner.ID != g.ID || int(owner.Local)%g.Width != nx-key.X || int(owner.Local)/g.Width != ny-key.Y {
					continue
				}
				_, _, _, alpha := t.assets.Atlas.At(fg.Ink[0]+xx*iw/dw, sy).RGBA()
				a := uint32(alpha >> 8)
				if a == 0 {
					continue
				}
				at := oy*out.Stride + ox*4
				for channel := 0; channel < 3; channel++ {
					old := uint32(out.Pix[at+channel])
					out.Pix[at+channel] = uint8((uint32(color[channel])*a + old*(255-a) + 127) / 255)
				}
			}
		}
		t.Stats.RenderedGlyphs++
	}
	for id, g := range t.glyphs {
		if g.Refs == 0 && g != t.active {
			delete(t.glyphs, id)
		}
	}
	t.Stats.ComposedFrames++
	t.visibleSources = sources
	t.VisibleScene = visibleScene(sources)
	t.cachedFrame = out
	t.cachedDisplay = p
	t.cachedRevision = t.revision
	t.cachedIndexed = append(t.cachedIndexed[:0], indexed...)
	return out
}

// This is a read-only presentation observation. A string being drawn to an
// off-screen page is not proof that the player can already see that page.
func visibleScene(sources map[uint16]bool) string {
	all := func(values ...uint16) bool {
		for _, value := range values {
			if !sources[value] {
				return false
			}
		}
		return true
	}
	// The normal retreat result is drawn over the map. Its visible title
	// takes priority over the still-present side menu; see spec 020.
	if all(18046) {
		return "battle-result"
	}
	if all(17749, 17786) {
		return "encounter-confirm"
	}
	if all(12742, 12762, 12782, 12802, 12822) {
		return "system-menu"
	}
	if all(1170, 1182, 1194, 1206, 1218, 1230, 1242) {
		return "character"
	}
	if all(990, 1010, 1030, 1050, 1070, 1090, 1110) {
		return "map"
	}
	if all(338, 398) {
		return "new-game-confirm"
	}
	if all(158, 218, 278) {
		return "main-menu"
	}
	return ""
}

func (t *Tracker) EventSource() string { return hex.EncodeToString(t.pam[0x2463e:0x2464e]) }

func (t *Tracker) HasVisibleSource(source uint16) bool { return t.visibleSources[source] }

// A copy of the last composed display's source IDs. Historical string events
// and glyphs retained on another VGA page do not enter this list.
func (t *Tracker) VisibleSources() []uint16 {
	out := make([]uint16, 0, len(t.visibleSources))
	for source := range t.visibleSources {
		out = append(out, source)
	}
	sort.Slice(out, func(i, j int) bool { return out[i] < out[j] })
	return out
}
