package eightsword

import (
	"bytes"
	"encoding/binary"
	"image"
	"image/draw"

	"github.com/wicanr2/dosgolem/oracle"
)

const captionsSourceSHA = "2689f07c2dde43c039c216e1417276616c12bf824f50dfbd79590f5a88509a44"

type IntroCaptionsStats struct {
	Bound, Started, Retired                   bool
	Requests, Composed, Invalidated, Timeouts uint64
	VisibleSources                            []uint16
	Errors                                    []string
}
type captionGlyph struct {
	x, width int
	r        rune
}
type captionEntry struct {
	source uint16
	width  int
	glyphs []captionGlyph
}
type captionTransaction struct {
	end   uint16
	start uint64
}
type IntroCaptions struct {
	o              *oracle.Oracle
	font           *Assets
	codes          map[uint16]rune
	raw            []byte
	entries        map[uint32]captionEntry
	pending        map[uint32]bool
	tx             []captionTransaction
	inText, failed bool
	textStart      uint64
	last           *image.RGBA
	lastSource     uint16
	Stats          IntroCaptionsStats
}

func newIntroCaptions(o *oracle.Oracle, story *IntroStory) *IntroCaptions {
	if story == nil {
		return nil
	}
	return &IntroCaptions{o: o, font: story.font, codes: story.codes, entries: map[uint32]captionEntry{}, pending: map[uint32]bool{}}
}
func (t *IntroCaptions) invalidate() {
	t.entries = map[uint32]captionEntry{}
	t.pending = map[uint32]bool{}
	t.tx = nil
	t.inText = false
	t.last = nil
	t.lastSource = 0
}
func (t *IntroCaptions) retire() { t.Stats.Retired = true; t.invalidate() }
func (t *IntroCaptions) fail(message string) {
	if len(t.Stats.Errors) < 8 {
		t.Stats.Errors = append(t.Stats.Errors, message)
	}
	t.failed = true
	t.invalidate()
}
func (t *IntroCaptions) valid() bool {
	return t.Stats.Bound && t.Stats.Started && !t.Stats.Retired && !t.failed && len(t.o.Overlays()) == 0
}
func (t *IntroCaptions) checkTimeout() {
	if !t.valid() {
		return
	}
	if (t.inText && t.o.Cycles()-t.textStart > titleTransactionLimit) || (len(t.tx) > 0 && t.o.Cycles()-t.tx[0].start > titleTransactionLimit) {
		t.Stats.Timeouts++
		t.fail("製作名單呈現交易逾時，恢復原版")
	}
}
func (t *IntroCaptions) Bind() {
	if t.Stats.Retired {
		return
	}
	if len(t.o.Overlays()) != 0 {
		t.retire()
		return
	}
	if t.Stats.Bound {
		t.checkTimeout()
		return
	}
	for _, w := range []struct {
		at  uint16
		n   int
		sha string
	}{
		{0x1be2, 1116, "792fc06dec03852fa5c88844dc0c11321e263454b9ced40b62521d016d2713f2"},
		{0x58b1, 95, "c05428726639bb22cfaa28ed4078610189fbddb2fe093d4d2ba7830b8709aa10"},
		{0x4c74, 352, "1aff4e0dbdf1831e8ba94e960bc6a0730a2edb075ac4c961a31d4a9b169beb6b"},
		{0x576a, 212, "88d6cfe05ddb19b00bd42cb4857a95cbcf9bdf764320ea21e503b9f202a947d8"},
		{0x5b0c, 55, "9b2e2e5b7c9b878690e526de6705910ee57066806e3a44c3b51fdf853176c76f"},
		{0x5954, 256, "3080de8fc158b5e5ba19394153621a6ed5b0b01210df7bc7ad90b27f0c37c8e3"},
		{0x5d76, 38, "908543eeb25cf60eb9dac835d484d3dc38cc53ac6b62e150272e988b0a2f5f07"},
		{0x5d9c, 38, "2ce8b80f1c0f969c41e341d89d62eebdba356a5f66d5d8b843b9530eb449e281"},
		{0x5dc2, 68, "24f2b4709430373bfeb8b921f5a4ed0ceab6b549a6aeeb71f861d916890c64fb"},
	} {
		if hash(t.o.Bytes(oracle.Far(0, w.at), w.n)) != w.sha {
			return
		}
	}
	t.Stats.Bound = true
	t.o.OnCall(oracle.Far(0, 0x1be2), func(o *oracle.Oracle) {
		if t.Stats.Retired || t.failed || len(o.Overlays()) != 0 {
			return
		}
		ds := o.Regs().DS
		raw := o.Bytes(oracle.Far(ds, 0x42), 160)
		if ds != 0xb31 || hash(raw) != captionsSourceSHA || hash(o.Bytes(oracle.Far(ds, 0x9fc), 706)) != storyCodesSHA || hash(o.Bytes(oracle.Far(0x231, 6), 10590)) != storyInkSHA {
			t.fail("製作名單執行期來源不符")
			return
		}
		t.raw = append([]byte(nil), raw...)
		t.Stats.Started = true
	})
	t.o.OnCall(oracle.Far(0, 0x58b1), func(*oracle.Oracle) { t.beginText() })
	t.o.OnCall(oracle.Far(0, 0x590f), func(*oracle.Oracle) {
		if t.valid() {
			t.inText = false
		}
	})
	t.o.OnCall(oracle.Far(0, 0x1322), func(o *oracle.Oracle) {
		if !t.Stats.Retired && len(o.Overlays()) == 0 {
			t.retire()
		}
	})
	for _, at := range []uint16{0x203c, 0x203e} {
		at := at
		t.o.OnCall(oracle.Far(0, at), func(*oracle.Oracle) {
			if t.Stats.Started && !t.Stats.Retired {
				t.retire()
			}
		})
	}
	for _, pair := range [][2]uint16{{0x576a, 0x583d}, {0x5b0c, 0x5b42}, {0x5d76, 0x5d8f}, {0x5d9c, 0x5db5}} {
		end := pair[1]
		t.o.OnCall(oracle.Far(0, pair[0]), func(o *oracle.Oracle) {
			if !t.valid() {
				return
			}
			if len(t.tx) >= 4 {
				t.fail("製作名單交易巢狀越界")
				return
			}
			t.tx = append(t.tx, captionTransaction{end, o.Cycles()})
		})
		t.o.OnCall(oracle.Far(0, end), func(*oracle.Oracle) {
			if !t.valid() || len(t.tx) == 0 {
				return
			}
			if t.tx[len(t.tx)-1].end != end {
				t.fail("製作名單交易返回不符")
				return
			}
			t.tx = t.tx[:len(t.tx)-1]
			if len(t.tx) == 0 {
				for page := range t.pending {
					delete(t.entries, page)
					t.Stats.Invalidated++
				}
				t.pending = map[uint32]bool{}
			}
		})
	}
}

func (t *IntroCaptions) beginText() {
	if !t.valid() {
		return
	}
	o := t.o
	r := o.Regs()
	source := o.Arg(0)
	ret := o.Word(oracle.Far(r.SS, r.SP))
	caller := ((source == 0x42 && ret == 0xb81) || (source == 0x6a && ret == 0xb9a) || (source == 0x92 && ret == 0xcbb) || (source == 0xba && (ret == 0xd4e || ret == 0xdb0))) && o.Word(oracle.Far(r.SS, r.SP+2)) == 0x110
	if !caller || r.DS != 0xb31 || o.Arg(1) != 0 || o.Arg(2) != 160 || o.Byte(oracle.Far(r.DS, 0x1efa)) != 3 || o.Byte(oracle.Far(r.DS, 0x1efb)) != 255 {
		t.fail("製作名單呼叫來源／位置不符")
		return
	}
	data := o.Bytes(oracle.Far(r.DS, source), 40)
	if !bytes.Equal(data, t.raw[int(source)-0x42:int(source)-0x42+40]) {
		t.fail("製作名單原文不符")
		return
	}
	n := bytes.IndexByte(data, 0)
	if n <= 0 || n > 33 {
		t.fail("製作名單長度不符")
		return
	}
	seg := o.Word(oracle.Far(r.DS, 0x1ef8))
	if seg != 0xa000 && seg != 0xa400 {
		t.fail("製作名單繪圖頁不符")
		return
	}
	page := uint32(seg-0xa000) * 16
	for y := 0; y < 15; y++ {
		if o.Word(oracle.Far(0x231, 0x2ac4+uint16((160+y)*2))) != uint16((160+y)*80) {
			t.fail("製作名單列位址不符")
			return
		}
		for x := 0; x < n; x++ {
			px, ok := o.PlanarBytePixels(page + uint32((160+y)*80+x))
			if !ok || px != [8]uint8{} {
				t.fail("製作名單黑底不符")
				return
			}
		}
	}
	entry := captionEntry{source: source, width: n * 8}
	for i := 0; i < n; {
		if data[i] == 32 {
			i++
			continue
		}
		if i+1 >= n {
			t.fail("製作名單字碼遭截斷")
			return
		}
		c, ok := t.codes[binary.LittleEndian.Uint16(data[i:i+2])]
		if !ok {
			t.fail("製作名單缺字")
			return
		}
		entry.glyphs = append(entry.glyphs, captionGlyph{i * 8, 16, c})
		i += 2
	}
	t.entries[page] = entry
	t.Stats.Requests++
	t.inText = true
	t.textStart = o.Cycles()
}

func (t *IntroCaptions) observeWrite(w oracle.VideoWrite) {
	if !t.valid() || t.inText {
		return
	}
	for page, entry := range t.entries {
		if w.Offset < page+12800 || w.Offset >= page+14000 {
			continue
		}
		off := w.Offset - page - 12800
		if off/80 >= 15 || off%80 >= uint32(entry.width/8) {
			continue
		}
		if len(t.tx) > 0 {
			t.pending[page] = true
		} else {
			delete(t.entries, page)
			t.Stats.Invalidated++
		}
	}
}
func (t *IntroCaptions) visible() (captionEntry, bool) {
	if !t.valid() {
		return captionEntry{}, false
	}
	p, ok := t.o.PlanarDisplay()
	if !ok || p.Width != 640 || p.Height != 200 || p.Pitch != 80 || p.LineCompare < 199 || (p.Start != 0 && p.Start != 0x4000) {
		t.invalidate()
		return captionEntry{}, false
	}
	e, ok := t.entries[p.Start]
	return e, ok
}
func (t *IntroCaptions) Stage() string {
	if _, ok := t.visible(); ok {
		return "captions-noto"
	}
	return ""
}
func (t *IntroCaptions) Compose(native *image.RGBA) *image.RGBA {
	t.checkTimeout()
	entry, ok := t.visible()
	if !ok {
		return native
	}
	p, _ := t.o.PlanarDisplay()
	rect := image.Rect(0, 960, entry.width*3, 1050)
	draw.Draw(native, rect, image.Black, image.Point{}, draw.Src)
	for _, g := range entry.glyphs {
		t.font.DrawRune(native, g.r, image.Rect(g.x*3, 960, (g.x+g.width)*3, 1050), p.Palette[3])
	}
	t.last = native
	t.lastSource = entry.source
	t.Stats.Composed++
	seen := false
	for _, s := range t.Stats.VisibleSources {
		seen = seen || s == entry.source
	}
	if !seen {
		t.Stats.VisibleSources = append(t.Stats.VisibleSources, entry.source)
	}
	return native
}
func (t *IntroCaptions) FrameSource(frame *image.RGBA) uint16 {
	if frame != nil && frame == t.last {
		return t.lastSource
	}
	return 0
}
