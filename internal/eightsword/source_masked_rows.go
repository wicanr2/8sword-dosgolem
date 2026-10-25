// 047 READY. Interruptible source-row prefixes; native row/plane control remains.
package eightsword

import (
	"crypto/sha256"
	"fmt"
	"math/bits"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func init() {
	runtimeDirectEntries = append(runtimeDirectEntries, 0x56f, 0x6a3)
	runtimePlanarRowExtra = runtimeMaskedRowPrepare
}

func runtimeMaskedRowPrepare(m *dg.Machine, b oracle.HostWorkLimits) (*runtimePlanarPlan, string) {
	// The common dispatcher checked the clock and BIOS video mode.
	r, s := m.CPU.R, m.CPU.Seg
	entry := m.CPU.IP
	sourceEntry, sourceEnd, end, readSite, writeSite := uint16(0x4f2), uint16(0x625), uint16(0x580), uint16(0x57a), uint16(0x57d)
	byteSteps, firstRead, writeDelay := uint64(9), uint64(7), uint64(1)
	want := "cc7f7579b3ace806dfb714752b00731f675c415f699ef7047648814eb95d6de4"
	background := entry == 0x6a3
	if background {
		sourceEntry, sourceEnd, end, readSite, writeSite = 0x626, 0x76e, 0x6bb, 0x6b4, 0x6b8
		byteSteps, firstRead, writeDelay = 12, 9, 2
		want = "c1cd7da0c0b84fd8e6ac44c073c6a9e653e5d2ab04a3bbd72f577c9324cec40e"
	} else if entry != 0x56f {
		return nil, "row-entry"
	}
	code := uint32(s[dg.CS]) * 16
	if code+uint32(sourceEnd)+1 > 0xa0000 || fmt.Sprintf("%x", sha256.Sum256(m.Mem[code+uint32(sourceEntry):code+uint32(sourceEnd)+1])) != want {
		return nil, "row-code"
	}
	if m.CPU.Flags&dg.DF != 0 || r[dg.DX] != 0x3ce || byte(r[dg.AX]) != 8 {
		return nil, "row-registers"
	}
	gc, seq, _ := m.VGAState()
	if gc[1]&15 != 0 || gc[3]&31 != 0 || gc[5]&3 != 0 {
		return nil, "row-vga-mode"
	}
	bp, ss := r[dg.BP], uint32(s[dg.SS])*16
	if bp < 34 || uint32(bp)+14 > 65536 || ss+uint32(bp)+14 > 0xa0000 || r[dg.SP] != bp-32 {
		return nil, "row-stack"
	}
	word := func(off int32) uint16 { return m.Read16(ss + uint32(int32(bp)+off)) }
	sourceOff, sourceSeg := word(6), word(8)
	ptr := uint32(sourceSeg)*16 + uint32(sourceOff)
	if ptr+4 > 0xa0000 || s[dg.DS] != sourceSeg {
		return nil, "row-source"
	}
	w, h := int(m.Read16(ptr)), int(m.Read16(ptr+2))
	x, y := int(word(10)), int(word(12))
	if w < 1 || w > 80 || h < 1 || h > 200 || x+w > 80 || y+h > 200 {
		return nil, "row-geometry"
	}
	area, size := w*h, 4+6*w*h
	if int(sourceOff)+size > 65536 || ptr+uint32(size) > 0xa0000 {
		return nil, "row-source-bounds"
	}
	remainingH, n := int(word(-4)), int(r[dg.CX])
	row, col := h-remainingH, w-n
	if remainingH < 1 || remainingH > h || n < 1 || n > w || int(word(-2)) != w || int(word(-8)) != 4*area || r[dg.BX] != uint16(2*(y+row)) {
		return nil, "row-position"
	}
	planeMask := byte(word(-6))
	plane := -1
	for i := 0; i < 4; i++ {
		if planeMask == 1<<uint(i) {
			plane = i
		}
	}
	if plane < 0 || seq[2]&15 != planeMask {
		return nil, "row-plane"
	}
	maskStart := uint16(int(sourceOff) + 4 + 5*area)
	maskOff := word(-10)
	if word(-32) != maskStart || word(-30) != uint16(y*2) || word(-28) != uint16(h) ||
		int(maskOff) != int(maskStart)+row*w+col ||
		int(r[dg.SI]) != int(sourceOff)+4+plane*area+row*w+col ||
		int(r[dg.DI]) != (y+row)*80+x+col ||
		m.Read16(code+6+uint32((y+row)*2)) != uint16((y+row)*80) {
		return nil, "row-pointers"
	}
	control := uint32(word(-24)) * 16
	if control+0x748c > 0xa0000 || m.Read16(control+0x7484) != 1 {
		return nil, "row-display-mode"
	}
	dest := m.Read16(control + 0x748a)
	if (dest != 0xa000 && dest != 0xa400) || s[dg.ES] != dest {
		return nil, "row-destination"
	}
	if background && (dest != 0xa000 || m.Read16(code+0x196) != 0xa400) {
		return nil, "row-background"
	}
	lo, hi := ss+uint32(bp)-34, ss+uint32(bp)+14
	overlaps := func(a, z uint32) bool { return a < hi && lo < z }
	if overlaps(ptr, ptr+uint32(size)) || overlaps(code, code+uint32(sourceEnd)+1) || overlaps(control+0x7484, control+0x748c) {
		return nil, "row-alias"
	}
	steps, cycles := byteSteps*uint64(n), (byteSteps+1)*uint64(n)
	if steps > b.Steps || cycles > b.Cycles {
		return nil, "row-quota"
	}
	available := m.HostWorkBudget(b.Steps, b.Cycles)
	if steps > available.Steps || cycles > available.Cycles {
		return nil, "row-event"
	}
	raw := append([]byte(nil), m.Mem[ptr:ptr+uint32(size)]...)
	p := &runtimePlanarPlan{Primitive: "masked-row", SourceEntry: sourceEntry, Plane: plane, Row: row, Column: col,
		CompatibilityBytes: uint64(n), SourceSHA256: fmt.Sprintf("%x", sha256.Sum256(raw)),
		Entry: entry, ReturnBoundary: end, WriteSite: writeSite, XByte: x + col, Y: y + row, WidthBytes: n, Height: 1,
		Destination: dest, Steps: steps, Cycles: cycles, Raw: raw, registers: r, segments: s, flags: m.CPU.Flags}
	p.commitExtra = func(m *dg.Machine, b oracle.HostWorkLimits) error {
		base := uint32(dest-0xa000) * 16
		readBase := base
		if background {
			readBase = 0x4000
		}
		start := m.Steps
		var lastRead byte
		for i := 0; i < n; i++ {
			index := row*w + col + i
			mask := raw[4+5*area+index]
			m.Out8(0x3ce, 8)
			m.Out8(0x3cf, mask)
			off := uint32(int(r[dg.DI]) + i)
			step := start + firstRead + uint64(i)*byteSteps
			lastRead = m.ReadHostPlanar(dg.VideoRead{Step: step, CS: s[dg.CS], IP: readSite, Offset: readBase + off})
			value := raw[4+plane*area+index]
			m.EGAPlane(plane)[base+off] = m.EGAPlane(plane)[readBase+off]&^mask | value&mask
			m.NotifyHostVideoWrite(dg.VideoWrite{Step: step + writeDelay, CS: s[dg.CS], IP: writeSite, Offset: base + off, Value: value, WriteMode: 0})
		}
		m.Write16(ss+uint32(bp)-10, maskOff+uint16(n))
		lastPush := r[dg.SI] + uint16(n) - 1
		if background {
			lastPush = dest
		}
		m.Write16(ss+uint32(r[dg.SP])-2, lastPush)
		m.CPU.R, m.CPU.Seg = p.registers, p.segments
		m.CPU.R[dg.AX] = uint16(lastRead)<<8 | 8
		m.CPU.R[dg.CX] = 0
		m.CPU.R[dg.SI] += uint16(n)
		m.CPU.R[dg.DI] += uint16(n)
		m.CPU.Flags = runtimeInc16Flags(p.flags, maskOff+uint16(n)-1)
		m.CPU.IP = end
		return m.CommitHostWork(steps, cycles, b.Steps, b.Cycles)
	}
	return p, ""
}

// INC changes arithmetic flags except CF. MOVSB and LOOP leave those flags.
func runtimeInc16Flags(flags, old uint16) uint16 {
	v := old + 1
	flags &^= dg.PF | dg.AF | dg.ZF | dg.SF | dg.OF
	if bits.OnesCount8(byte(v))&1 == 0 {
		flags |= dg.PF
	}
	if old&15 == 15 {
		flags |= dg.AF
	}
	if v == 0 {
		flags |= dg.ZF
	}
	if v&0x8000 != 0 {
		flags |= dg.SF
	}
	if old == 0x7fff {
		flags |= dg.OF
	}
	return flags
}
