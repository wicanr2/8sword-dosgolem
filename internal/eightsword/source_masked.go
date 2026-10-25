// 047 READY. Six-block source plans, native latch reads and indexed compatibility.
package eightsword

import (
	"crypto/sha256"
	"fmt"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func init() {
	runtimeDirectEntries = append(runtimeDirectEntries, 0x4f2, 0x626)
	runtimePlanarExtra = runtimeMaskedPrepare
}

func runtimeMaskedPrepare(m *dg.Machine, b oracle.HostWorkLimits) (*runtimePlanarPlan, string) {
	// The shared dispatcher already checked clock and BIOS mode.
	r, s := m.CPU.R, m.CPU.Seg
	entry := m.CPU.IP
	ret, readSite, writeSite := uint16(0x625), uint16(0x57a), uint16(0x57d)
	want := "cc7f7579b3ace806dfb714752b00731f675c415f699ef7047648814eb95d6de4"
	background := entry == 0x626
	if background {
		ret, readSite, writeSite = 0x76e, 0x6b4, 0x6b8
		want = "c1cd7da0c0b84fd8e6ac44c073c6a9e653e5d2ab04a3bbd72f577c9324cec40e"
	} else if entry != 0x4f2 {
		if runtimePlanarRowExtra != nil {
			return runtimePlanarRowExtra(m, b)
		}
		return nil, "entry-mode"
	}
	code := uint32(s[dg.CS]) * 16
	if code+uint32(ret)+1 > 0xa0000 || fmt.Sprintf("%x", sha256.Sum256(m.Mem[code+uint32(entry):code+uint32(ret)+1])) != want {
		return nil, "code"
	}
	gc, _, _ := m.VGAState()
	if gc[1]&15 != 0 || gc[3]&31 != 0 || gc[5]&3 != 0 || gc[8] != 255 {
		return nil, "vga-mode"
	}
	sp, ss := r[dg.SP], uint32(s[dg.SS])*16
	if sp < 36 || uint32(sp)+12 > 65536 || ss+uint32(sp)+12 > 0xa0000 {
		return nil, "stack-bounds"
	}
	arg := func(i uint32) uint16 { return m.Read16(ss + uint32(sp) + 4 + i*2) }
	sourceOff := arg(0)
	ptr := uint32(arg(1))*16 + uint32(sourceOff)
	if ptr+4 > 0xa0000 {
		return nil, "source-header"
	}
	w, h := int(m.Read16(ptr)), int(m.Read16(ptr+2))
	x, y := int(arg(2)), int(arg(3))
	if w < 1 || h < 1 || w > 80 || h > 200 || x+w > 80 || y+h > 200 {
		return nil, "geometry"
	}
	area, size := w*h, 4+6*w*h
	if int(sourceOff)+size > 65536 || ptr+uint32(size) > 0xa0000 {
		return nil, "source-bounds"
	}
	ds := uint32(s[dg.DS]) * 16
	if ds+0x748c > 0xa0000 || m.Read16(ds+0x7484) != 1 {
		return nil, "display-mode"
	}
	dest := m.Read16(ds + 0x748a)
	if dest != 0xa000 && dest != 0xa400 {
		return nil, "destination"
	}
	if background && (dest != 0xa000 || m.Read16(code+0x196) != 0xa400) {
		return nil, "background-page"
	}
	lo, hi := ss+uint32(sp)-36, ss+uint32(sp)+12
	overlaps := func(a, z uint32) bool { return a < hi && lo < z }
	if overlaps(ptr, ptr+uint32(size)) || overlaps(code, code+uint32(ret)+1) || overlaps(ds+0x7484, ds+0x748c) {
		return nil, "stack-alias"
	}
	for row := 0; row < h; row++ {
		if m.Read16(code+6+uint32((y+row)*2)) != uint16((y+row)*80) {
			return nil, "row-table"
		}
	}
	// Mode 1: each plane has 15 control instructions; each row has 7,
	// plus 9 per byte, or 12 for the ES-switching background read.
	// Prelude + epilogue = 51, four plane controls = 60; RETF stays native.
	byteSteps, firstRead, writeDelay := 9, uint64(57), uint64(1)
	if background {
		byteSteps, firstRead, writeDelay = 12, 59, 2
	}
	rowSteps := byteSteps*w + 7
	steps := uint64(4*h*rowSteps + 111)
	cycles := steps + uint64(4*area) // each MOVSB also charges its one iteration
	if steps > b.Steps || cycles > b.Cycles {
		return nil, "quota"
	}
	available := m.HostWorkBudget(b.Steps, b.Cycles)
	if steps > available.Steps || cycles > available.Cycles {
		return nil, "machine-event"
	}
	raw := append([]byte(nil), m.Mem[ptr:ptr+uint32(size)]...)
	planeSlot := m.Read16(ss+uint32(sp)-8)&0xff00 | 0x10
	maskStart := sourceOff + uint16(4+5*area)
	lastPush := sourceOff + uint16(4+4*area-1)
	if background {
		lastPush = dest
	}
	stack := []uint16{r[dg.BP], uint16(w), uint16(h), planeSlot, uint16(4 * area), maskStart,
		r[dg.AX], r[dg.BX], r[dg.CX], r[dg.DX], r[dg.SI], r[dg.DI], s[dg.DS], s[dg.ES], uint16(h), uint16(y * 2), maskStart, lastPush}
	p := &runtimePlanarPlan{SourceSHA256: fmt.Sprintf("%x", sha256.Sum256(raw)), Entry: entry, ReturnBoundary: ret,
		WriteSite: writeSite, XByte: x, Y: y, WidthBytes: w, Height: h, Destination: dest,
		Steps: steps, Cycles: cycles, Raw: raw, registers: r, segments: s, flags: m.CPU.Flags, stack: stack}
	p.commitExtra = func(m *dg.Machine, b oracle.HostWorkLimits) error {
		start := m.Steps
		for i, v := range p.stack {
			m.Write16(ss+uint32(sp)-uint32((i+1)*2), v)
		}
		base := uint32(dest-0xa000) * 16
		readBase := base
		if background {
			readBase = 0x4000
		}
		for plane := 0; plane < 4; plane++ {
			m.Out8(0x3c4, 2)
			m.Out8(0x3c5, 1<<uint(plane))
			m.Out8(0x3ce, 8)
			for row := 0; row < h; row++ {
				for col := 0; col < w; col++ {
					index := row*w + col
					off := uint32((y+row)*80 + x + col)
					mask := raw[4+5*area+index]
					m.Out8(0x3cf, mask)
					step := start + firstRead + uint64(plane*(h*rowSteps+15)+row*rowSteps+col*byteSteps)
					m.ReadHostPlanar(dg.VideoRead{Step: step, CS: s[dg.CS], IP: readSite, Offset: readBase + off})
					value := raw[4+plane*area+index]
					m.EGAPlane(plane)[base+off] = m.EGAPlane(plane)[readBase+off]&^mask | value&mask
					m.NotifyHostVideoWrite(dg.VideoWrite{Step: step + writeDelay, CS: s[dg.CS], IP: writeSite, Offset: base + off, Value: value, WriteMode: 0})
				}
			}
		}
		m.Out8(0x3cf, 255)
		m.CPU.R, m.CPU.Seg, m.CPU.IP = p.registers, p.segments, p.ReturnBoundary
		m.CPU.Flags = (p.flags & ^uint16(dg.CF|dg.PF|dg.AF|dg.ZF|dg.SF|dg.OF|dg.DF)) | dg.PF | dg.ZF
		return m.CommitHostWork(p.Steps, p.Cycles, b.Steps, b.Cycles)
	}
	return p, ""
}
