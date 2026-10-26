// 047 READY. Source glyph row batches; the HD painter consumes typed glyphs.
package eightsword

import (
	"crypto/sha256"
	"fmt"
	"math/bits"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

type sourceGlyphLayout struct {
	Entry                                        oracle.Addr
	CJK                                          bool
	Mode, Destination, Foreground, Source, Table uint16
	MaxIndex                                     int
	CodeSHA                                      string
}

func pamGlyphLayouts(t *Tracker) []sourceGlyphLayout {
	return []sourceGlyphLayout{
		{oracle.Addr{Seg: t.fontSeg, Off: 0x4a98}, true, 0x7484, 0x748a, 0x748c, 0x10, 0xa2a6, 636, "dfebc4b82af7f599021f8fdf9a6dd4fac73107cac673ca37f5a6adf9af8bdd29"},
		{oracle.Addr{Seg: t.stringSeg, Off: 0xb86}, false, 0x7484, 0x748a, 0x748c, 0x5f48, 6, 256, "17b3918b0f449a362621b70a1a0bf33d006ed3211867f5f34710a339af58fffc"},
	}
}

func introGlyphLayouts() []sourceGlyphLayout {
	return []sourceGlyphLayout{
		{oracle.Far(0, 0x4c74), true, 0x1ef2, 0x1ef8, 0x1efa, 6, 0x2ac4, 353, "1aff4e0dbdf1831e8ba94e960bc6a0730a2edb075ac4c961a31d4a9b169beb6b"},
		{oracle.Far(0, 0x5954), false, 0x1ef2, 0x1ef8, 0x1efa, 0xcc0, 4, 256, "3080de8fc158b5e5ba19394153621a6ed5b0b01210df7bc7ad90b27f0c37c8e3"},
	}
}

func (l sourceGlyphLayout) row() oracle.Addr {
	n := uint16(0x96)
	if l.CJK {
		n = 0x8f
	}
	return oracle.Addr{Seg: l.Entry.Seg, Off: l.Entry.Off + n}
}

type sourceGlyphPlan struct {
	endingGlyphPlan
	Entry uint16
}

func prepareSourceGlyph(m *dg.Machine, b oracle.HostWorkLimits, l sourceGlyphLayout) (*sourceGlyphPlan, string) {
	if !m.CycleClock || !m.CPU.DOSBoxCost || m.VideoMode() != 0x0e || m.CPU.Flags&dg.DF != 0 {
		return nil, "clock-or-mode"
	}
	r, s := m.CPU.R, m.CPU.Seg
	code := uint32(s[dg.CS]) * 16
	if code+uint32(m.CPU.IP) != l.row().Linear() || code > l.Entry.Linear() {
		return nil, "entry"
	}
	entry := uint16(l.Entry.Linear() - code)
	size := uint32(0x100)
	width, depth := 1, uint32(12)
	if l.CJK {
		size = 0x160
		width = 2
		depth = 14
	}
	if l.Entry.Linear()+size > 0xa0000 || fmt.Sprintf("%x", sha256.Sum256(m.Mem[l.Entry.Linear():l.Entry.Linear()+size])) != l.CodeSHA {
		return nil, "code"
	}
	gc, _, _ := m.VGAState()
	if gc[1]&15 != 0 || gc[3]&31 != 0 || gc[5]&3 != 0 || gc[8] != 255 {
		return nil, "vga-mode"
	}
	ss, bp := uint32(s[dg.SS])*16, uint32(r[dg.BP])
	if bp < 18 || bp+12 > 65536 || ss+bp+12 > 0xa0000 || uint32(r[dg.SP]) != bp-depth {
		return nil, "stack-bounds"
	}
	arg := func(off uint32) uint16 { return m.Read16(ss + bp + off) }
	x, y, left := int(arg(8)), int(arg(10)), int(r[dg.CX])
	if x+width > 80 || y+15 > 200 || left < 1 || left > 15 || r[dg.BX] != uint16(2*(y+15-left)) {
		return nil, "geometry"
	}
	ds := uint32(s[dg.DS]) * 16
	if ds+uint32(l.Foreground)+2 > 0xa0000 || m.Read16(ds+uint32(l.Mode)) != 1 || m.Read16(ds+uint32(l.Destination)) != s[dg.ES] {
		return nil, "source-mode"
	}
	if s[dg.ES] != 0xa000 && s[dg.ES] != 0xa400 {
		return nil, "destination"
	}
	fg, bg := m.Mem[ds+uint32(l.Foreground)], m.Mem[ds+uint32(l.Foreground)+1]
	if fg > 15 || (bg > 15 && bg != 255) {
		return nil, "colors"
	}
	index := int(arg(6))
	source := ds + uint32(l.Source) + uint32(index*15)
	expectedSI := int(l.Source) + index*15 + 15 - left
	if l.CJK {
		if index%30 != 0 || index/30 >= l.MaxIndex {
			return nil, "glyph-index"
		}
		source = code + uint32(l.Source) + uint32(index)
		expectedSI = int(l.Source) + index + (15-left)*2
	} else if index >= l.MaxIndex {
		return nil, "glyph-index"
	}
	if int(r[dg.SI]) != expectedSI || source+uint32(width*15) > 0xa0000 {
		return nil, "source-pointer"
	}
	per := 24
	if l.CJK {
		per = 55
	}
	if bg != 255 {
		per += 15 * width
	}
	available := m.HostWorkBudget(b.Steps, b.Cycles)
	n := 0
	var steps, cycles uint64
	for rows := 1; rows <= left; rows++ {
		st := uint64(rows * per)
		if l.CJK && rows == left {
			st--
		}
		cy := st + uint64(rows*width)
		if st > available.Steps || cy > available.Cycles {
			break
		}
		n, steps, cycles = rows, st, cy
	}
	if n == 0 {
		return nil, "quota-or-event"
	}
	lo, hi := ss+bp-18, ss+bp+12
	overlap := func(a, z uint32) bool { return a < hi && lo < z }
	if overlap(source, source+uint32(width*15)) || overlap(code, code+uint32(entry)+size) || overlap(ds+uint32(l.Mode), ds+uint32(l.Foreground)+2) {
		return nil, "stack-alias"
	}
	for i := 0; i < n; i++ {
		if m.Read16(code+uint32(l.Table)+uint32((y+15-left+i)*2)) != uint16((y+15-left+i)*80) {
			return nil, "row-table"
		}
	}
	start := source + uint32((15-left)*width)
	return &sourceGlyphPlan{endingGlyphPlan{l.CJK, n, width, per, x, y + 15 - left, fg, bg, steps, cycles, append([]byte(nil), m.Mem[start:start+uint32(n*width)]...), r, s, m.CPU.Flags}, entry}, ""
}

func (p *sourceGlyphPlan) commit(m *dg.Machine, b oracle.HostWorkLimits) error {
	start, base := m.Steps, uint32(p.segments[dg.ES]-0xa000)*16
	sites := func(a, b, c, d, e uint16) glyphByteSites {
		return glyphByteSites{p.Entry + a, p.Entry + b, p.Entry + c, p.Entry + d, p.Entry + e}
	}
	for row := 0; row < p.Rows; row++ {
		off := base + uint32((p.Y+row)*80+p.X)
		step := start + uint64(row*p.StepsPerRow) + 4
		if p.CJK {
			glyphByte(m, off, p.Data[row*2], p.FG, p.BG, step, p.segments[dg.CS], sites(0xb3, 0xb6, 0xd9, 0xdc, 0xe8), true)
			advance := uint64(24)
			if p.BG != 255 {
				advance += 15
			}
			glyphByte(m, off+1, p.Data[row*2+1], p.FG, p.BG, step+advance, p.segments[dg.CS], sites(0x10d, 0x110, 0x133, 0x136, 0x142), true)
		} else {
			glyphByte(m, off, p.Data[row], p.FG, p.BG, step, p.segments[dg.CS], sites(0xba, 0xbd, 0xdf, 0xe2, 0xeb), false)
		}
	}
	ss := uint32(p.segments[dg.SS]) * 16
	if p.CJK {
		m.Write16(ss+uint32(p.registers[dg.SP])-2, p.segments[dg.DS])
		m.Write16(ss+uint32(p.registers[dg.SP])-4, p.segments[dg.CS])
	}
	m.CPU.R, m.CPU.Seg = p.registers, p.segments
	m.CPU.R[dg.AX] = 0xff08
	m.CPU.R[dg.DX] = 0x3ce
	m.CPU.R[dg.SI] += uint16(p.Rows * p.Width)
	m.CPU.R[dg.DI] = uint16((p.Y+p.Rows-1)*80 + p.X + p.Width)
	m.CPU.R[dg.BX] += uint16(p.Rows * 2)
	m.CPU.R[dg.CX] -= uint16(p.Rows)
	if p.CJK {
		left := m.CPU.R[dg.CX]
		m.CPU.Flags = p.flags &^ uint16(dg.CF|dg.PF|dg.AF|dg.ZF|dg.SF|dg.OF)
		if bits.OnesCount8(byte(left))&1 == 0 {
			m.CPU.Flags |= dg.PF
		}
		if left == 0 {
			m.CPU.Flags |= dg.ZF
		}
		m.CPU.IP = p.Entry + 0x8f
		if left == 0 {
			m.CPU.IP = p.Entry + 0x157
		}
	} else {
		m.CPU.Flags = endingAddTwoFlags(p.flags, m.CPU.R[dg.BX]-2)
		m.CPU.IP = p.Entry + 0x96
		if m.CPU.R[dg.CX] == 0 {
			m.CPU.IP = p.Entry + 0xf8
		}
	}
	return m.CommitHostWork(p.Steps, p.Cycles, b.Steps, b.Cycles)
}

func (e *Engine) installSourceGlyphs(layouts []sourceGlyphLayout) {
	for _, l := range layouts {
		e.Oracle.OnHostCall(l.row(), func(_ *oracle.Oracle, m *dg.Machine, b oracle.HostWorkLimits) (bool, error) {
			if !e.sourceEnabled || !e.HD || e.renderFault != nil {
				return false, nil
			}
			p, _ := prepareSourceGlyph(m, b, l)
			if p == nil {
				return false, nil
			}
			if err := p.commit(m, b); err != nil {
				return false, err
			}
			e.sourceDirectCalls++
			e.sourceGlyphRows += uint64(p.Rows)
			e.sourceGlyphSteps += p.Steps
			return true, nil
		})
	}
}

// Bind only from the HD renderer lifecycle. In particular, constructing a
// source adapter for a native-CPU oracle does not install accelerators.
func (e *Engine) sourceGlyphInstall() func() {
	introBound, pamBound := false, false
	return func() {
		if !e.sourceEnabled || !e.HD || e.renderFault != nil {
			return
		}
		if !introBound && !e.PAMLoaded {
			code := e.Oracle.Bytes(oracle.Far(0, 0x576a), 212)
			if fmt.Sprintf("%x", sha256.Sum256(code)) == "88d6cfe05ddb19b00bd42cb4857a95cbcf9bdf764320ea21e503b9f202a947d8" {
				e.installSourceGlyphs(introGlyphLayouts())
				introBound = true
			}
		}
		if !pamBound && e.Tracker != nil && e.Tracker.loadSegment != 0 {
			e.installSourceGlyphs(pamGlyphLayouts(e.Tracker))
			pamBound = true
		}
	}
}
