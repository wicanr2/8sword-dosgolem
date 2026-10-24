package eightsword

import (
	"fmt"
	"image"
	"image/draw"
	"os"
	"path/filepath"

	"github.com/wicanr2/dosgolem/oracle"
)

const heroineDecodedSHA = "1ad430667a6d06969e1e71e1fa0b1f57453e65865488bbaa3416f86027e8924b"
const heroineArtSHA = "f060f488db011379ec80e82e48f2112309baf639fe1179f81cd822e95310a186"
const heroinePNGSHA = "9a9775fcf7c58ac5c60e8b8e1774858c6527d580801d5d04920b4c419f0b09f8"

var heroineRect = image.Rect(336, 120, 1608, 720)
var heroinePacked = map[string]string{"TIT3.AY": "31b943254292a75df2ad9d0c54eaeff7eacae83fb0f411bae4cfa4e66dd1bdec", "TIT4.AY": "d12b77ead60f2a85033c89a99b8e444473f143413647735196f75685e24de14d", "TIT5.AY": "b4114a8c64d949cba71321adc9979270ce001250845eb685badea9ad77c06d9e"}

type heroineRecord struct {
	offset, w, h, blocks int
	sha                  string
}

// These fifteen complete records are indexed by spec 017's verified r7 catalog.
var heroineRecords = []heroineRecord{
	{0, 80, 100, 4, "1fe2232d9767b43e7765e13fda48a7dfe96611945acddc90f0ffb3f31285ae1b"},
	{32004, 80, 100, 4, "5e0d8510c1bd96647eec5f5791664c82293253c6e09f0c36f95859213007007d"},
	{0, 10, 46, 6, "ad11ca076ce75af8a691468f63501858fb6b452d787a6330384ae7f10f8fe3c2"},
	{2764, 10, 46, 6, "9eea36aaa5fcea57bc3c185bb71491c9617c85a38cea31419ba751bdbebc002a"},
	{5528, 10, 46, 6, "adee4da2a9880eac10327c8019a38b38936aecbd19ca1cf60f91c365c7f964e0"},
	{8292, 10, 46, 6, "9bd744e54f463871b60e99588212c182d5a4f7e2496c1bc0767ea9537fdf9f33"},
	{11056, 10, 46, 6, "66cea37693e74bf85450ba671a9ac37c9478b5e4e5a4145a72cee4c96d95a84e"},
	{13820, 10, 46, 6, "eb70dc0dd6dc09e2a1d8df230431bde41828dcf9a9e3faaf19923eba19130821"},
	{16584, 10, 46, 6, "38f5b857bbf8583189a30e4a7b3e0373496212093eeb9701ac2d7be9e96bbf50"},
	{19348, 10, 46, 6, "31aef832ce5d155e38977ab5c49251737c349b1322acdcc3e8e9180a3aa5cd0d"},
	{22112, 10, 46, 6, "4aba66d8f1cf9d85c78e8dfa45545e125eb83b55017cc14db8779d2a8e4d8e44"},
	{24876, 10, 46, 6, "222fb53822fa45e54ba2b22704dd79f3da698c8a09f5f1fdccfc9615cc1e25d5"},
	{27640, 24, 50, 6, "7871a2930026aaf862d4f8015dfb0a27eaac460b6a2866a905f14cdd6f07a1f2"},
	{34844, 24, 50, 6, "84d61875ab3630e8d6fdeb29f2efcc4e124c4c0fbdf2e195161e92187e6b1d3f"},
	{0, 53, 100, 4, heroineDecodedSHA},
}

type HeroineEvent struct {
	Serial, Step                        uint64
	At                                  uint16
	Page, SourcePage                    uint32
	Rows                                []uint32
	SourceSHA                           string
	RecordOffset, Width, Height, Blocks int
	Invalid                             bool
}
type HeroineStats struct {
	Bound, Started, Retired                                                                   bool
	Portraits, Composed, Held, Copies, Clears, Masked, Invalidations, UnknownWrites, Timeouts uint64
	Errors                                                                                    []string
}
type heroinePage struct {
	bits  []bool
	count int
}
type heroineTX struct {
	at, end          uint16
	page, sourcePage uint32
	start            uint64
	record           *heroineRecord
	raw              []byte
	rows             []uint32
	invalid          bool
	hold             *image.RGBA
}
type IntroHeroine struct {
	o                         *oracle.Oracle
	art                       image.Image
	pages                     map[uint32]*heroinePage
	tx                        []heroineTX
	palette                   [16][3]uint8
	paletteSet                bool
	stop                      func()
	version, cachedVersion    uint64
	cachedBase, cached, final *image.RGBA
	cachedPage                uint32
	used                      int
	Stats                     HeroineStats
	Events                    []HeroineEvent
}

func loadIntroHeroine(e *Engine, dir, root string) (*IntroHeroine, error) {
	var m struct {
		Schema     int    `json:"schema"`
		SourceSHA  string `json:"source_sha256"`
		DecodedSHA string `json:"decoded_sha256"`
		ArtSHA     string `json:"art_sha256"`
		File       string `json:"file"`
		SHA        string `json:"sha256"`
		Width      int    `json:"width"`
		Height     int    `json:"height"`
	}
	path := filepath.Join(dir, "intro-heroine.json")
	st, err := os.Lstat(path)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if !st.Mode().IsRegular() {
		return nil, fmt.Errorf("女主角清單不是一般檔案")
	}
	if err = readPosterJSON(path, &m); err != nil {
		return nil, err
	}
	if m.Schema != 1 || m.SourceSHA != heroinePacked["TIT5.AY"] || m.DecodedSHA != heroineDecodedSHA || m.ArtSHA != heroineArtSHA || m.SHA != heroinePNGSHA || m.File != "intro-heroine.png" || m.Width != 1272 || m.Height != 600 {
		return nil, fmt.Errorf("女主角清單來源／形狀不符")
	}
	for name, h := range heroinePacked {
		b, err := os.ReadFile(filepath.Join(root, name))
		if err != nil {
			return nil, err
		}
		if hash(b) != h {
			return nil, fmt.Errorf("女主角原版來源 %s 不符", name)
		}
	}
	art, err := readPosterImage(dir, m.File, m.SHA, 1272, 600)
	if err != nil {
		return nil, err
	}
	mhd := &IntroHeroine{o: e.Oracle, art: art, pages: map[uint32]*heroinePage{}}
	mhd.stop = e.ObservePresentation(PresentationObserver{Write: mhd.observeWrite, ModeChange: func(PresentationModeChange) {
		if mhd.Stats.Started {
			mhd.retire()
		}
	}})
	e.Oracle.OnCall(oracle.Far(0, 0x1be2), func(*oracle.Oracle) { mhd.start() })
	for _, at := range []uint16{0x1322, 0x203c} {
		e.Oracle.OnCall(oracle.Far(0, at), func(*oracle.Oracle) {
			if mhd.Stats.Started {
				mhd.retire()
			}
		})
	}
	for _, p := range [][2]uint16{{0x576a, 0x583d}, {0x52c0, 0x53f3}, {0x5b0c, 0x5b42}, {0x5d76, 0x5d8f}, {0x5d9c, 0x5db5}} {
		at, end := p[0], p[1]
		e.Oracle.OnCall(oracle.Far(0, at), func(*oracle.Oracle) { mhd.begin(at, end) })
		e.Oracle.OnCall(oracle.Far(0, end), func(*oracle.Oracle) { mhd.commit(end) })
	}
	return mhd, nil
}
func (m *IntroHeroine) start() {
	if m.Stats.Retired || m.Stats.Started || len(m.o.Overlays()) != 0 {
		return
	}
	for _, g := range []struct {
		at  uint16
		n   int
		sha string
	}{
		{0x1be2, 1116, "792fc06dec03852fa5c88844dc0c11321e263454b9ced40b62521d016d2713f2"},
		{0x576a, 212, "88d6cfe05ddb19b00bd42cb4857a95cbcf9bdf764320ea21e503b9f202a947d8"},
		{0x52c0, 308, "c7c0315ee13ef29e26ea2b35098c3cae6453e4f4e5fcd34da6cee81ae57c4dd3"},
		{0x510b, 53, "faa92f6dfda7d9d587f9279dac67ec33897fe9cde2fa1c1a21d9aacc1c04fb2c"},
		{0x517e, 53, "9c6604f617ce1421dd00d7f46e665e37416b00e822338f86dba879b13785aa36"},
		{0x5b0c, 55, "9b2e2e5b7c9b878690e526de6705910ee57066806e3a44c3b51fdf853176c76f"},
		{0x5d76, 38, "908543eeb25cf60eb9dac835d484d3dc38cc53ac6b62e150272e988b0a2f5f07"},
		{0x5d9c, 38, "2ce8b80f1c0f969c41e341d89d62eebdba356a5f66d5d8b843b9530eb449e281"},
	} {
		if hash(m.o.Bytes(oracle.Far(0, g.at), g.n)) != g.sha {
			return
		}
	}
	m.Stats.Bound, m.Stats.Started = true, true
}
func (m *IntroHeroine) retire() {
	m.Stats.Retired = true
	m.pages = map[uint32]*heroinePage{}
	m.tx = nil
	m.cachedBase = nil
	m.cached = nil
	m.final = nil
	m.used = 0
	if m.stop != nil {
		m.stop()
		m.stop = nil
	}
}
func (m *IntroHeroine) fail(s string) {
	if len(m.Stats.Errors) < 8 {
		m.Stats.Errors = append(m.Stats.Errors, s)
	}
	m.retire()
}
func (m *IntroHeroine) valid() bool {
	return m != nil && m.Stats.Started && !m.Stats.Retired && len(m.o.Overlays()) == 0
}
func heroineRAM(seg, off uint16, n int) bool {
	return n > 0 && uint64(off)+uint64(n) <= 65536 && uint64(seg)*16+uint64(off)+uint64(n) <= 0xa0000
}
func (m *IntroHeroine) Tick() {
	if m == nil || m.Stats.Retired {
		return
	}
	if len(m.o.Overlays()) != 0 {
		m.retire()
		return
	}
	for _, t := range m.tx {
		if m.o.Cycles()-t.start > titleTransactionLimit {
			m.Stats.Timeouts++
			m.fail("女主角呈現交易逾時")
			return
		}
	}
}
func (m *IntroHeroine) begin(at, end uint16) {
	if !m.valid() {
		return
	}
	s, ok := m.o.PlanarDisplay()
	if !ok || s.Width != 640 || s.Height != 200 || s.Pitch != 80 || s.LineCompare < 199 || m.o.Word(oracle.Far(0, 0xd202)) != 1 {
		m.fail("女主角顯示幾何不符")
		return
	}
	if !m.paletteSet {
		m.palette = s.Palette
		m.paletteSet = true
	}
	if s.Palette != m.palette {
		m.fail("女主角色盤改變")
		return
	}
	dest := m.o.Word(oracle.Far(0, 0xd208))
	if dest != 0xa000 && dest != 0xa400 {
		m.fail("女主角目的頁不符")
		return
	}
	t := heroineTX{at: at, end: end, page: uint32(dest-0xa000) * 16, start: m.o.Cycles()}
	if at == 0x5d76 {
		t.page, t.sourcePage = 0x4000, 0
	}
	if at == 0x5d9c {
		t.page, t.sourcePage = 0, 0x4000
	}
	if at == 0x576a || at == 0x52c0 {
		off, seg, x, y := m.o.Arg(0), m.o.Arg(1), m.o.Arg(2), m.o.Arg(3)
		if !heroineRAM(seg, off, 4) {
			m.fail("女主角來源表頭越界")
			return
		}
		w, h := int(m.o.Word(oracle.Far(seg, off))), int(m.o.Word(oracle.Far(seg, off+2)))
		blocks := 4
		if at == 0x52c0 {
			blocks = 6
		}
		n := 4 + w*h*blocks
		if w < 1 || w > 80 || h < 1 || h > 200 || int(y)+h > 200 || !heroineRAM(seg, off, n) {
			m.fail("女主角來源記錄越界")
			return
		}
		raw := m.o.Bytes(oracle.Far(seg, off), n)
		sha := hash(raw)
		for i := range heroineRecords {
			r := &heroineRecords[i]
			if r.sha == sha && r.offset == int(off) && r.w == w && r.h == h && r.blocks == blocks {
				t.record = r
				break
			}
		}
		if t.record == nil {
			m.fail("女主角繪製來源未確認")
			return
		}
		t.raw = raw
		t.rows = make([]uint32, h)
		for i := range t.rows {
			row := m.o.Word(oracle.Far(m.o.Regs().CS, 4+(y+uint16(i))*2))
			if int(row) != (int(y)+i)*80 {
				m.fail("女主角列索引不符")
				return
			}
			t.rows[i] = t.page + uint32(row) + uint32(x)
		}
		if sha == heroineDecodedSHA && (x != 14 || y != 20) {
			m.fail("女主角來源位置不符")
			return
		}
	}
	if len(m.tx) >= 4 {
		m.fail("女主角交易巢狀越界")
		return
	}
	if s.Start == t.page && (m.pages[t.page] != nil || (t.record != nil && t.record.sha == heroineDecodedSHA)) {
		t.hold = m.nativeRect()
		if t.hold != nil {
			m.paint(t.hold, m.pages[t.page], image.Point{})
		}
	}
	m.tx = append(m.tx, t)
}
func (m *IntroHeroine) owns(t heroineTX, v PresentationWrite) bool {
	pc := uint32(v.CS)*16 + uint32(v.IP)
	switch t.at {
	case 0x5b0c:
		return pc == 0x5b3b && v.WriteMode == 0 && v.Offset >= t.page && v.Offset < t.page+16384
	case 0x5d76:
		return pc == 0x5132 && v.WriteMode == 1 && v.Offset >= t.page && v.Offset < t.page+16000
	case 0x5d9c:
		return pc == 0x51a5 && v.WriteMode == 1 && v.Offset >= t.page && v.Offset < t.page+16000
	}
	writer := uint32(0x57ca)
	if t.at == 0x52c0 {
		writer = 0x534b
	}
	if pc != writer || v.WriteMode != 0 || t.record == nil || len(t.rows) == 0 || v.Offset < t.rows[0] {
		return false
	}
	d := v.Offset - t.rows[0]
	return d/80 < uint32(t.record.h) && d%80 < uint32(t.record.w)
}
func (m *IntroHeroine) observeWrite(v PresentationWrite) {
	if !m.valid() {
		return
	}
	page := v.Offset &^ uint32(0x3fff)
	if page != 0 && page != 0x4000 {
		return
	}
	local := v.Offset - page
	x, y := int(local%80), int(local/80)
	if x < 14 || x >= 67 || y < 20 || y >= 120 {
		return
	}
	for i := len(m.tx) - 1; i >= 0; i-- {
		if m.owns(m.tx[i], v) {
			return
		}
	}
	m.Stats.UnknownWrites++
	delete(m.pages, page)
	m.cachedBase = nil
	m.cached = nil
	m.Stats.Invalidations++
	for i := range m.tx {
		t := &m.tx[i]
		if t.page == page || ((t.at == 0x5d76 || t.at == 0x5d9c) && t.sourcePage == page) {
			t.invalid = true
			t.hold = nil
			delete(m.pages, t.page)
		}
	}
}
func cloneHeroinePage(p *heroinePage) *heroinePage {
	if p == nil {
		return nil
	}
	return &heroinePage{bits: append([]bool(nil), p.bits...), count: p.count}
}
func (m *IntroHeroine) commit(end uint16) {
	if !m.valid() || len(m.tx) == 0 {
		return
	}
	t := m.tx[len(m.tx)-1]
	if t.end != end {
		m.fail("女主角返回點不符")
		return
	}
	m.tx = m.tx[:len(m.tx)-1]
	if t.invalid {
		delete(m.pages, t.page)
	} else {
		switch t.at {
		case 0x5b0c:
			delete(m.pages, t.page)
			m.Stats.Clears++
		case 0x5d76, 0x5d9c:
			m.pages[t.page] = cloneHeroinePage(m.pages[t.sourcePage])
			m.Stats.Copies++
		default:
			if t.record.sha == heroineDecodedSHA {
				bits := make([]bool, 424*100)
				for i := range bits {
					bits[i] = true
				}
				m.pages[t.page] = &heroinePage{bits: bits, count: len(bits)}
				m.Stats.Portraits++
			} else if p := m.pages[t.page]; p != nil {
				n := t.record.w * t.record.h
				for yy, row := range t.rows {
					for xx := 0; xx < t.record.w; xx++ {
						mask := byte(255)
						if t.record.blocks == 6 {
							mask = t.raw[4+5*n+yy*t.record.w+xx]
						}
						local := row - t.page + uint32(xx)
						for bit := 0; bit < 8; bit++ {
							if mask&(128>>bit) == 0 {
								continue
							}
							x, y := int(local%80)*8+bit-112, int(local/80)-20
							if x >= 0 && x < 424 && y >= 0 && y < 100 {
								i := y*424 + x
								if p.bits[i] {
									p.bits[i] = false
									p.count--
								}
							}
						}
					}
				}
				if p.count == 0 {
					delete(m.pages, t.page)
				}
			}
			if t.record.blocks == 6 {
				m.Stats.Masked++
			}
		}
	}
	m.version++
	ev := HeroineEvent{Serial: m.version, Step: m.o.Steps(), At: t.at, Page: t.page, SourcePage: t.sourcePage, Rows: t.rows, Invalid: t.invalid}
	if t.record != nil {
		ev.SourceSHA = t.record.sha
		ev.RecordOffset = t.record.offset
		ev.Width = t.record.w
		ev.Height = t.record.h
		ev.Blocks = t.record.blocks
	}
	if len(m.Events) < 512 {
		m.Events = append(m.Events, ev)
	}
	m.cachedBase = nil
	m.cached = nil
}
func (m *IntroHeroine) nativeRect() *image.RGBA {
	w, h, rgb := m.o.ScreenRGB()
	if w != 640 || h != 200 {
		return nil
	}
	out := image.NewRGBA(image.Rect(0, 0, 1272, 600))
	for y := 0; y < 600; y++ {
		for x := 0; x < 1272; x++ {
			src := ((20+y/6)*640 + 112 + x/3) * 3
			at := y*out.Stride + x*4
			copy(out.Pix[at:at+3], rgb[src:src+3])
			out.Pix[at+3] = 255
		}
	}
	return out
}
func (m *IntroHeroine) paint(out *image.RGBA, p *heroinePage, origin image.Point) {
	if p == nil || p.count == 0 {
		return
	}
	for y := 0; y < 100; y++ {
		for x := 0; x < 424; {
			if !p.bits[y*424+x] {
				x++
				continue
			}
			start := x
			for x < 424 && p.bits[y*424+x] {
				x++
			}
			src := image.Pt(start*3, y*6)
			rect := image.Rect(origin.X+start*3, origin.Y+y*6, origin.X+x*3, origin.Y+(y+1)*6)
			draw.Draw(out, rect, m.art, src, draw.Src)
		}
	}
}
func (m *IntroHeroine) Compose(base *image.RGBA) *image.RGBA {
	if m == nil {
		return base
	}
	m.used = 0
	m.final = nil
	m.Tick()
	if !m.valid() {
		return base
	}
	s, ok := m.o.PlanarDisplay()
	if !ok || s.Width != 640 || s.Height != 200 || s.Pitch != 80 || s.LineCompare < 199 || s.Palette != m.palette {
		return base
	}
	for _, t := range m.tx {
		if t.page == s.Start && t.hold != nil && !t.invalid {
			out := image.NewRGBA(base.Bounds())
			copy(out.Pix, base.Pix)
			draw.Draw(out, heroineRect, t.hold, image.Point{}, draw.Src)
			m.used = -1
			m.Stats.Held++
			return out
		}
	}
	p := m.pages[s.Start]
	if p == nil || p.count == 0 {
		return base
	}
	m.used = p.count
	m.Stats.Composed++
	if m.cachedBase == base && m.cachedPage == s.Start && m.cachedVersion == m.version {
		return m.cached
	}
	out := image.NewRGBA(base.Bounds())
	copy(out.Pix, base.Pix)
	m.paint(out, p, heroineRect.Min)
	m.cachedBase, m.cached, m.cachedPage, m.cachedVersion = base, out, s.Start, m.version
	return out
}
func (m *IntroHeroine) FramePixels(frame *image.RGBA) int {
	if m != nil && m.final == frame {
		return m.used
	}
	return 0
}
func (m *IntroHeroine) Status() map[string]any {
	if m == nil {
		return nil
	}
	return map[string]any{"stats": m.Stats, "serial": m.version, "frame_pixels": m.used, "events": m.Events}
}
