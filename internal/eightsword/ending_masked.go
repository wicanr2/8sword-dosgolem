// 053 READY. Native Go masked blits with indexed readback and bounded effects.
package eightsword

import (
	"crypto/sha256"
	"fmt"
	"math/bits"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

const endingMaskSHA = "85467a42c1b56b7eb880128fe34417adbe74fdf1bf42d857758908d8bbd79549"

type endingMaskPlan struct {
	SourceOffset, Destination uint16
	X, Y, W, H                int
	Steps, Cycles             uint64
	Raw                       []byte
	registers                 [8]uint16
	segments                  [4]uint16
	flags                     uint16
	stack                     []uint16
}

func prepareEndingMask(m *dg.Machine, b oracle.HostWorkLimits) (*endingMaskPlan, string) {
	if !m.CycleClock || !m.CPU.DOSBoxCost || m.VideoMode() != 0x0e {
		return nil, "clock-or-mode"
	}
	r, s := m.CPU.R, m.CPU.Seg
	code := uint32(s[dg.CS]) * 16
	if s[dg.CS] != 0x393 || m.CPU.IP != 0x4ec || fmt.Sprintf("%x", sha256.Sum256(m.Mem[code+0x4ec:code+0x620])) != endingMaskSHA {
		return nil, "code"
	}
	gc, _, _ := m.VGAState()
	if gc[1]&15 != 0 || gc[3]&31 != 0 || gc[5]&3 != 0 || gc[8] != 255 {
		return nil, "vga-mode"
	}
	ss, sp := uint32(s[dg.SS])*16, uint32(r[dg.SP])
	if sp < 36 || sp+12 > 65536 || ss+sp+12 > 0xa0000 {
		return nil, "stack-bounds"
	}
	arg := func(i uint32) uint16 { return m.Read16(ss + sp + 4 + i*2) }
	ptr := uint32(arg(1))*16 + uint32(arg(0))
	if ptr+4 > 0xa0000 {
		return nil, "source-header"
	}
	w, h, x, y := int(m.Read16(ptr)), int(m.Read16(ptr+2)), int(arg(2)), int(arg(3))
	if w < 1 || h < 1 || x+w > 80 || y+h > 200 {
		return nil, "geometry"
	}
	area, size := w*h, 4+6*w*h
	if int(arg(0))+size > 65536 || ptr+uint32(size) > 0xa0000 {
		return nil, "source-bounds"
	}
	ds := uint32(s[dg.DS]) * 16
	if ds+0x1784 > 0xa0000 || m.Read16(ds+0x177a) != 1 {
		return nil, "source-mode"
	}
	dest := m.Read16(ds + 0x1780)
	if dest != 0xa000 && dest != 0xa400 {
		return nil, "destination"
	}
	lo, hi := ss+sp-36, ss+sp+12
	overlap := func(a, z uint32) bool { return a < hi && lo < z }
	if overlap(ptr, ptr+uint32(size)) || overlap(code, code+0x620) || overlap(ds+0x177a, ds+0x1784) {
		return nil, "stack-alias"
	}
	for row := 0; row < h; row++ {
		if m.Read16(code+uint32((y+row)*2)) != uint16((y+row)*80) {
			return nil, "row-table"
		}
	}
	steps := uint64(4*h*(9*w+7) + 111)
	cycles := steps + uint64(4*area)
	available := m.HostWorkBudget(b.Steps, b.Cycles)
	if steps > available.Steps || cycles > available.Cycles {
		return nil, "quota-or-event"
	}
	mask := arg(0) + uint16(4+5*area)
	planeSlot := m.Read16(ss+sp-8)&0xff00 | 0x10
	stack := []uint16{r[dg.BP], uint16(w), uint16(h), planeSlot, uint16(4 * area), mask,
		r[dg.AX], r[dg.BX], r[dg.CX], r[dg.DX], r[dg.SI], r[dg.DI], s[dg.DS], s[dg.ES], uint16(h), uint16(y * 2), mask, arg(0) + uint16(4+4*area-1)}
	return &endingMaskPlan{arg(0), dest, x, y, w, h, steps, cycles, append([]byte(nil), m.Mem[ptr:ptr+uint32(size)]...), r, s, m.CPU.Flags, stack}, ""
}

func (p *endingMaskPlan) commit(m *dg.Machine, b oracle.HostWorkLimits) error {
	ss, sp := uint32(p.segments[dg.SS])*16, uint32(p.registers[dg.SP])
	for i, value := range p.stack {
		m.Write16(ss+sp-uint32((i+1)*2), value)
	}
	start, base, area := m.Steps, uint32(p.Destination-0xa000)*16, p.W*p.H
	for plane := 0; plane < 4; plane++ {
		m.Out8(0x3c4, 2)
		m.Out8(0x3c5, 1<<uint(plane))
		m.Out8(0x3ce, 8)
		for row := 0; row < p.H; row++ {
			for col := 0; col < p.W; col++ {
				i := row*p.W + col
				off := base + uint32((p.Y+row)*80+p.X+col)
				mask, value := p.Raw[4+5*area+i], p.Raw[4+plane*area+i]
				m.Out8(0x3cf, mask)
				step := start + 57 + uint64(plane*(p.H*(9*p.W+7)+15)+row*(9*p.W+7)+col*9)
				m.ReadHostPlanar(dg.VideoRead{Step: step, CS: p.segments[dg.CS], IP: 0x574, Offset: off})
				m.EGAPlane(plane)[off] = m.EGAPlane(plane)[off]&^mask | value&mask
				m.NotifyHostVideoWrite(dg.VideoWrite{Step: step + 1, CS: p.segments[dg.CS], IP: 0x577, Offset: off, Value: value, WriteMode: 0})
			}
		}
	}
	m.Out8(0x3cf, 255)
	m.CPU.R, m.CPU.Seg, m.CPU.IP = p.registers, p.segments, 0x61f
	m.CPU.Flags = (p.flags &^ uint16(dg.CF|dg.PF|dg.AF|dg.ZF|dg.SF|dg.OF|dg.DF)) | dg.PF | dg.ZF
	return m.CommitHostWork(p.Steps, p.Cycles, b.Steps, b.Cycles)
}

type endingMaskRun struct {
	Count, Plane int
	Base, Offset uint32
	MaskOffset   uint16
	Data, Masks  []byte
	registers    [8]uint16
	segments     [4]uint16
	flags        uint16
}

func prepareEndingMaskRun(m *dg.Machine, b oracle.HostWorkLimits) (*endingMaskRun, string) {
	if !m.CycleClock || !m.CPU.DOSBoxCost || m.VideoMode() != 0x0e {
		return nil, "clock-or-mode"
	}
	r, s := m.CPU.R, m.CPU.Seg
	code := uint32(s[dg.CS]) * 16
	if s[dg.CS] != 0x393 || m.CPU.IP != 0x569 || fmt.Sprintf("%x", sha256.Sum256(m.Mem[code+0x4ec:code+0x620])) != endingMaskSHA {
		return nil, "code"
	}
	if m.CPU.Flags&dg.DF != 0 || r[dg.DX] != 0x3ce || byte(r[dg.AX]) != 8 {
		return nil, "registers"
	}
	gc, seq, _ := m.VGAState()
	if gc[1]&15 != 0 || gc[3]&31 != 0 || gc[5]&3 != 0 {
		return nil, "vga-mode"
	}
	ss, bp := uint32(s[dg.SS])*16, uint32(r[dg.BP])
	if bp < 34 || bp+14 > 65536 || ss+bp+14 > 0xa0000 || uint32(r[dg.SP]) != bp-32 {
		return nil, "stack-bounds"
	}
	word := func(off int32) uint16 { return m.Read16(ss + uint32(int32(bp)+off)) }
	sourceOffset, sourceSegment := word(6), word(8)
	ptr := uint32(sourceSegment)*16 + uint32(sourceOffset)
	if ptr+4 > 0xa0000 || s[dg.DS] != sourceSegment {
		return nil, "source-header"
	}
	w, h, x, y := int(m.Read16(ptr)), int(m.Read16(ptr+2)), int(word(10)), int(word(12))
	if w < 1 || h < 1 || x+w > 80 || y+h > 200 {
		return nil, "geometry"
	}
	area, size := w*h, 4+6*w*h
	if int(sourceOffset)+size > 65536 || ptr+uint32(size) > 0xa0000 {
		return nil, "source-bounds"
	}
	left, n := int(word(-4)), int(r[dg.CX])
	row, col := h-left, w-n
	if left < 1 || left > h || n < 1 || n > w || int(word(-2)) != w || int(word(-8)) != 4*area || r[dg.BX] != uint16(2*(y+row)) {
		return nil, "position"
	}
	mask := byte(word(-6))
	plane := -1
	for i := 0; i < 4; i++ {
		if mask == 1<<uint(i) {
			plane = i
		}
	}
	if plane < 0 || seq[2]&15 != mask {
		return nil, "plane-mask"
	}
	maskStart := int(sourceOffset) + 4 + 5*area
	maskOffset := word(-10)
	if int(word(-32)) != maskStart || word(-30) != uint16(y*2) || word(-28) != uint16(h) ||
		int(maskOffset) != maskStart+row*w+col || int(r[dg.SI]) != int(sourceOffset)+4+plane*area+row*w+col ||
		int(r[dg.DI]) != (y+row)*80+x+col || m.Read16(code+uint32((y+row)*2)) != uint16((y+row)*80) {
		return nil, "pointers"
	}
	control := uint32(word(-24)) * 16
	if control+0x1784 > 0xa0000 || m.Read16(control+0x177a) != 1 {
		return nil, "source-mode"
	}
	dest := m.Read16(control + 0x1780)
	if (dest != 0xa000 && dest != 0xa400) || s[dg.ES] != dest {
		return nil, "destination"
	}
	lo, hi := ss+bp-34, ss+bp+14
	overlap := func(a, z uint32) bool { return a < hi && lo < z }
	if overlap(ptr, ptr+uint32(size)) || overlap(code, code+0x620) || overlap(control+0x177a, control+0x1784) {
		return nil, "stack-alias"
	}
	available := m.HostWorkBudget(b.Steps, b.Cycles)
	n = min(n, int(min(available.Steps/9, available.Cycles/10)))
	if n < 1 {
		return nil, "quota-or-event"
	}
	dataStart := ptr + 4 + uint32(plane*area+row*w+col)
	maskPtr := ptr + 4 + uint32(5*area+row*w+col)
	return &endingMaskRun{n, plane, uint32(dest-0xa000) * 16, uint32(r[dg.DI]), maskOffset,
		append([]byte(nil), m.Mem[dataStart:dataStart+uint32(n)]...), append([]byte(nil), m.Mem[maskPtr:maskPtr+uint32(n)]...), r, s, m.CPU.Flags}, ""
}

func endingIncrementFlags(flags, old uint16) uint16 {
	value := old + 1
	flags &^= dg.PF | dg.AF | dg.ZF | dg.SF | dg.OF
	if bits.OnesCount8(byte(value))&1 == 0 {
		flags |= dg.PF
	}
	if old&15 == 15 {
		flags |= dg.AF
	}
	if value == 0 {
		flags |= dg.ZF
	}
	if value&0x8000 != 0 {
		flags |= dg.SF
	}
	if old == 0x7fff {
		flags |= dg.OF
	}
	return flags
}

func (p *endingMaskRun) commit(m *dg.Machine, b oracle.HostWorkLimits) error {
	start := m.Steps
	var last byte
	for i, value := range p.Data {
		off := p.Base + p.Offset + uint32(i)
		mask := p.Masks[i]
		m.Out8(0x3ce, 8)
		m.Out8(0x3cf, mask)
		step := start + 7 + uint64(i*9)
		last = m.ReadHostPlanar(dg.VideoRead{Step: step, CS: p.segments[dg.CS], IP: 0x574, Offset: off})
		m.EGAPlane(p.Plane)[off] = m.EGAPlane(p.Plane)[off]&^mask | value&mask
		m.NotifyHostVideoWrite(dg.VideoWrite{Step: step + 1, CS: p.segments[dg.CS], IP: 0x577, Offset: off, Value: value, WriteMode: 0})
	}
	ss := uint32(p.segments[dg.SS]) * 16
	m.Write16(ss+uint32(p.registers[dg.BP])-10, p.MaskOffset+uint16(p.Count))
	m.Write16(ss+uint32(p.registers[dg.SP])-2, p.registers[dg.SI]+uint16(p.Count)-1)
	m.CPU.R, m.CPU.Seg = p.registers, p.segments
	m.CPU.R[dg.AX] = uint16(last)<<8 | 8
	m.CPU.R[dg.CX] -= uint16(p.Count)
	m.CPU.R[dg.SI] += uint16(p.Count)
	m.CPU.R[dg.DI] += uint16(p.Count)
	m.CPU.Flags = endingIncrementFlags(p.flags, p.MaskOffset+uint16(p.Count)-1)
	m.CPU.IP = 0x569
	if m.CPU.R[dg.CX] == 0 {
		m.CPU.IP = 0x57a
	}
	return m.CommitHostWork(uint64(p.Count*9), uint64(p.Count*10), b.Steps, b.Cycles)
}

func installEndingMasked(o *oracle.Oracle, counts map[string]int) {
	o.OnHostCall(oracle.Addr{Seg: 0x393, Off: 0x4ec}, func(_ *oracle.Oracle, m *dg.Machine, b oracle.HostWorkLimits) (bool, error) {
		p, why := prepareEndingMask(m, b)
		if p == nil {
			counts["masked-full-fallback-"+why]++
			return false, nil
		}
		if err := p.commit(m, b); err != nil {
			return false, err
		}
		counts["masked-full-calls"]++
		counts["masked-skipped-x86"] += int(p.Steps)
		counts["masked-indexed-bytes"] += 4 * p.W * p.H
		return true, nil
	})
	o.OnHostCall(oracle.Addr{Seg: 0x393, Off: 0x569}, func(_ *oracle.Oracle, m *dg.Machine, b oracle.HostWorkLimits) (bool, error) {
		p, why := prepareEndingMaskRun(m, b)
		if p == nil {
			counts["masked-run-fallback-"+why]++
			return false, nil
		}
		if err := p.commit(m, b); err != nil {
			return false, err
		}
		counts["masked-run-batches"]++
		counts["masked-skipped-x86"] += p.Count * 9
		counts["masked-indexed-bytes"] += p.Count
		if p.registers[dg.CX] > uint16(p.Count) {
			counts["masked-partial-row-batches"]++
		}
		return true, nil
	})
}
