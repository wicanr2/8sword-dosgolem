// 053 READY. Native Go glyph rows; compatibility effects and event quotas.
package eightsword

import (
	"crypto/sha256"
	"fmt"
	"math/bits"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

type endingGlyphPlan struct {
	CJK                      bool
	Rows, Width, StepsPerRow int
	X, Y                     int
	FG, BG                   byte
	Steps, Cycles            uint64
	Data                     []byte
	registers                [8]uint16
	segments                 [4]uint16
	flags                    uint16
}

func prepareEndingGlyph(m *dg.Machine, b oracle.HostWorkLimits) (*endingGlyphPlan, string) {
	if !m.CycleClock || !m.CPU.DOSBoxCost || m.VideoMode() != 0x0e || m.CPU.Flags&dg.DF != 0 {
		return nil, "clock-or-mode"
	}
	r, s := m.CPU.R, m.CPU.Seg
	cjk := s[dg.CS] == 0x28e && m.CPU.IP == 0xf7f
	entry, end, row, table, width := uint16(0xb80), uint16(0xc7f), uint16(0xc16), uint16(0), 1
	want := "5631f527e7a205f772c3c0f0b1c6521781a1264b669d487346dfa1671a5c1692"
	if cjk {
		entry, end, row, table, width = 0xef0, 0x104f, 0xf7f, 0x1050, 2
		want = "dc3197283e3434f6ca35e71592b0c604bc035efef450ed50afffff1309f01739"
	} else if s[dg.CS] != 0x393 || m.CPU.IP != row {
		return nil, "entry"
	}
	code := uint32(s[dg.CS]) * 16
	if fmt.Sprintf("%x", sha256.Sum256(m.Mem[code+uint32(entry):code+uint32(end)+1])) != want {
		return nil, "code"
	}
	gc, _, _ := m.VGAState()
	if gc[1]&15 != 0 || gc[3]&31 != 0 || gc[5]&3 != 0 || gc[8] != 255 {
		return nil, "vga-mode"
	}
	ss, bp := uint32(s[dg.SS])*16, uint32(r[dg.BP])
	depth := uint32(12)
	if cjk {
		depth = 14
	}
	if bp < 18 || bp+12 > 65536 || ss+bp+12 > 0xa0000 || uint32(r[dg.SP]) != bp-depth {
		return nil, "stack-bounds"
	}
	arg := func(off uint32) uint16 { return m.Read16(ss + bp + off) }
	x, y, left := int(arg(8)), int(arg(10)), int(r[dg.CX])
	if x+width > 80 || y+15 > 200 || left < 1 || left > 15 || r[dg.BX] != uint16(2*(y+15-left)) {
		return nil, "geometry"
	}
	ds := uint32(s[dg.DS]) * 16
	if ds+0x1784 > 0xa0000 || m.Read16(ds+0x177a) != 1 || m.Read16(ds+0x1780) != s[dg.ES] {
		return nil, "source-mode"
	}
	if s[dg.ES] != 0xa000 && s[dg.ES] != 0xa400 {
		return nil, "destination"
	}
	fg, bg := m.Mem[ds+0x1782], m.Mem[ds+0x1783]
	if fg > 15 || (bg > 15 && bg != 255) {
		return nil, "colors"
	}
	index := int(arg(6))
	source := ds + 0x548 + uint32(index*15)
	expectedSI := 0x548 + index*15 + (15 - left)
	if cjk {
		if index%30 != 0 || index/30 >= 127 {
			return nil, "glyph-index"
		}
		source = code + 14 + uint32(index)
		expectedSI = 14 + index + (15-left)*2
	} else if index > 255 {
		return nil, "glyph-index"
	}
	if int(r[dg.SI]) != expectedSI || source+uint32(width*15) > 0xa0000 {
		return nil, "source-pointer"
	}
	per := 24
	if cjk {
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
		if cjk && rows == left {
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
	if overlap(source, source+uint32(width*15)) || overlap(code, code+uint32(end)+1) || overlap(ds+0x177a, ds+0x1784) {
		return nil, "stack-alias"
	}
	for i := 0; i < n; i++ {
		if m.Read16(code+uint32(table)+uint32((y+15-left+i)*2)) != uint16((y+15-left+i)*80) {
			return nil, "row-table"
		}
	}
	start := source + uint32((15-left)*width)
	return &endingGlyphPlan{cjk, n, width, per, x, y + 15 - left, fg, bg, steps, cycles,
		append([]byte(nil), m.Mem[start:start+uint32(n*width)]...), r, s, m.CPU.Flags}, ""
}

type glyphByteSites struct{ BGRead, BGWrite, ClearRead, ClearWrite, InkWrite uint16 }

func glyphByte(m *dg.Machine, off uint32, mask, fg, bg byte, step uint64, cs uint16, sites glyphByteSites, cjk bool) {
	opaque := bg != 255
	if opaque {
		m.Out8(0x3c4, 2)
		m.Out8(0x3c5, 15)
		m.Out8(0x3ce, 1)
		m.Out8(0x3cf, 15)
		m.Out8(0x3ce, 0)
		m.Out8(0x3cf, bg)
		old := m.ReadHostPlanar(dg.VideoRead{Step: step + 10, CS: cs, IP: sites.BGRead, Offset: off})
		for plane := 0; plane < 4; plane++ {
			value := byte(0)
			if bg&(1<<uint(plane)) != 0 {
				value = 255
			}
			m.EGAPlane(plane)[off] = value
		}
		m.NotifyHostVideoWrite(dg.VideoWrite{Step: step + 11, CS: cs, IP: sites.BGWrite, Offset: off, Value: old, WriteMode: 0})
		m.Out8(0x3ce, 0)
		m.Out8(0x3cf, 0)
		m.Out8(0x3ce, 1)
		m.Out8(0x3cf, 0)
		step += 15
	}
	m.Out8(0x3ce, 8)
	m.Out8(0x3cf, mask)
	m.Out8(0x3c4, 2)
	m.Out8(0x3c5, ^fg&15)
	m.ReadHostPlanar(dg.VideoRead{Step: step + 11, CS: cs, IP: sites.ClearRead, Offset: off})
	for plane := 0; plane < 4; plane++ {
		if fg&(1<<uint(plane)) == 0 {
			m.EGAPlane(plane)[off] &= ^mask
		}
	}
	m.NotifyHostVideoWrite(dg.VideoWrite{Step: step + 12, CS: cs, IP: sites.ClearWrite, Offset: off, Value: 0, WriteMode: 0})
	m.Out8(0x3c4, 2)
	m.Out8(0x3c5, fg)
	for plane := 0; plane < 4; plane++ {
		if fg&(1<<uint(plane)) != 0 {
			m.EGAPlane(plane)[off] |= mask
		}
	}
	delay := uint64(15)
	if cjk {
		delay = 18
	}
	m.NotifyHostVideoWrite(dg.VideoWrite{Step: step + delay, CS: cs, IP: sites.InkWrite, Offset: off, Value: mask, WriteMode: 0})
	m.Out8(0x3ce, 8)
	m.Out8(0x3cf, 255)
}

func endingAddTwoFlags(flags, old uint16) uint16 {
	v := old + 2
	flags &^= dg.CF | dg.PF | dg.AF | dg.ZF | dg.SF | dg.OF
	if uint32(old)+2 > 65535 {
		flags |= dg.CF
	}
	if bits.OnesCount8(byte(v))&1 == 0 {
		flags |= dg.PF
	}
	if (old^2^v)&0x10 != 0 {
		flags |= dg.AF
	}
	if v == 0 {
		flags |= dg.ZF
	}
	if v&0x8000 != 0 {
		flags |= dg.SF
	}
	if ^(old^2)&(old^v)&0x8000 != 0 {
		flags |= dg.OF
	}
	return flags
}

func (p *endingGlyphPlan) commit(m *dg.Machine, b oracle.HostWorkLimits) error {
	start, base := m.Steps, uint32(p.segments[dg.ES]-0xa000)*16
	for row := 0; row < p.Rows; row++ {
		off := base + uint32((p.Y+row)*80+p.X)
		step := start + uint64(row*p.StepsPerRow) + 4
		if p.CJK {
			glyphByte(m, off, p.Data[row*2], p.FG, p.BG, step, p.segments[dg.CS], glyphByteSites{0xfa3, 0xfa6, 0xfc9, 0xfcc, 0xfd8}, true)
			advance := uint64(24)
			if p.BG != 255 {
				advance += 15
			}
			glyphByte(m, off+1, p.Data[row*2+1], p.FG, p.BG, step+advance, p.segments[dg.CS], glyphByteSites{0xffd, 0x1000, 0x1023, 0x1026, 0x1032}, true)
		} else {
			glyphByte(m, off, p.Data[row], p.FG, p.BG, step, p.segments[dg.CS], glyphByteSites{0xc3a, 0xc3d, 0xc5f, 0xc62, 0xc6b}, false)
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
		m.CPU.IP = 0xf7f
		if left == 0 {
			m.CPU.IP = 0x1047
		}
	} else {
		m.CPU.Flags = endingAddTwoFlags(p.flags, m.CPU.R[dg.BX]-2)
		m.CPU.IP = 0xc16
		if m.CPU.R[dg.CX] == 0 {
			m.CPU.IP = 0xc78
		}
	}
	return m.CommitHostWork(p.Steps, p.Cycles, b.Steps, b.Cycles)
}

func installEndingGlyphs(o *oracle.Oracle, counts map[string]int) {
	for _, at := range []oracle.Addr{{Seg: 0x28e, Off: 0xf7f}, {Seg: 0x393, Off: 0xc16}} {
		o.OnHostCall(at, func(_ *oracle.Oracle, m *dg.Machine, b oracle.HostWorkLimits) (bool, error) {
			p, why := prepareEndingGlyph(m, b)
			if p == nil {
				counts["glyph-fallback-"+why]++
				return false, nil
			}
			if err := p.commit(m, b); err != nil {
				return false, err
			}
			counts["glyph-go-batches"]++
			counts["glyph-go-rows"] += p.Rows
			counts["glyph-skipped-x86"] += int(p.Steps)
			if p.CJK {
				counts["glyph-cjk-rows"] += p.Rows
			} else {
				counts["glyph-ascii-rows"] += p.Rows
			}
			if p.BG != 255 {
				counts["glyph-opaque-rows"] += p.Rows
			}
			return true, nil
		})
	}
}
