//go:build ignore

// 053 DRAFT. PAE native Go planar copy; no x86 opcode execution in commit.
package main

import (
	"crypto/sha256"
	"fmt"
	"math/bits"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

type endingDirectPlan struct {
	Entry, Return, Write, Destination uint16
	X, Y, W, H                        int
	Steps, Cycles                     uint64
	Raw                               []byte
	registers                         [8]uint16
	segments                          [4]uint16
	flags                             uint16
	stack                             []uint16
}

func prepareEndingDirect(m *dg.Machine, b oracle.HostWorkLimits) (*endingDirectPlan, string) {
	if !m.CycleClock || !m.CPU.DOSBoxCost || m.VideoMode() != 0x0e {
		return nil, "clock-or-mode"
	}
	r, s := m.CPU.R, m.CPU.Seg
	entry, ret, write, planes, want := m.CPU.IP, uint16(0), uint16(0), 0, ""
	switch entry {
	case 0x996:
		ret, write, planes = 0xa69, 0x9f6, 4
		want = "603833bfa266acbc8f7a3c8ecf3a30e9f15b5242211367534a7ca1145bb4cfad"
	case 0x769:
		ret, write, planes = 0x84e, 0x7c9, 5
		want = "285723c100da394f2c125b5a1a293c0b24d4f18a8cf2276937ef4a47db4124bc"
	default:
		return nil, "entry"
	}
	code := uint32(s[dg.CS]) * 16
	if s[dg.CS] != 0x393 || code+uint32(ret)+1 > 0xa0000 || fmt.Sprintf("%x", sha256.Sum256(m.Mem[code+uint32(entry):code+uint32(ret)+1])) != want {
		return nil, "code"
	}
	gc, _, _ := m.VGAState()
	if gc[1]&15 != 0 || gc[3]&31 != 0 || gc[5]&3 != 0 || gc[8] != 255 {
		return nil, "vga-mode"
	}
	sp, ss := r[dg.SP], uint32(s[dg.SS])*16
	if sp < 30 || uint32(sp)+12 > 65536 || ss+uint32(sp)+12 > 0xa0000 {
		return nil, "stack-bounds"
	}
	arg := func(i uint32) uint16 { return m.Read16(ss + uint32(sp) + 4 + i*2) }
	ptr := uint32(arg(1))*16 + uint32(arg(0))
	if ptr+4 > 0xa0000 {
		return nil, "header"
	}
	w, h, x, y := int(m.Read16(ptr)), int(m.Read16(ptr+2)), int(arg(2)), int(arg(3))
	if w < 1 || h < 1 || x+w > 80 || y+h > 200 {
		return nil, "geometry"
	}
	size := 4 + planes*w*h
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
	lo, hi := ss+uint32(sp)-30, ss+uint32(sp)+12
	overlaps := func(a, z uint32) bool { return a < hi && lo < z }
	if overlaps(ptr, ptr+uint32(size)) || overlaps(code, code+uint32(ret)+1) || overlaps(ds+0x177a, ds+0x1784) {
		return nil, "stack-alias"
	}
	for row := 0; row < h; row++ {
		// PAE uses CS:[row*2], unlike PAM's CS:[6+row*2].
		if m.Read16(code+uint32((y+row)*2)) != uint16((y+row)*80) {
			return nil, "row-table"
		}
	}
	steps := uint64(32*h + 81)
	cycles := steps + uint64(4*w*h)
	available := m.HostWorkBudget(b.Steps, b.Cycles)
	if steps > available.Steps || cycles > available.Cycles {
		return nil, "quota-or-event"
	}
	planeSlot := m.Read16(ss+uint32(sp)-8)&0xff00 | 0x10
	stack := []uint16{r[dg.BP], uint16(w), uint16(h), planeSlot, uint16(w * h), r[dg.AX], r[dg.BX], r[dg.CX], r[dg.DX], r[dg.SI], r[dg.DI], s[dg.DS], s[dg.ES], uint16(h), uint16(y * 2)}
	return &endingDirectPlan{entry, ret, write, dest, x, y, w, h, steps, cycles,
		append([]byte(nil), m.Mem[ptr:ptr+uint32(size)]...), r, s, m.CPU.Flags, stack}, ""
}

func (p *endingDirectPlan) commit(m *dg.Machine, b oracle.HostWorkLimits) error {
	start := m.Steps
	ss, sp := uint32(p.segments[dg.SS])*16, p.registers[dg.SP]
	// These are the call's ABI effects, not a translated instruction loop.
	for i, v := range p.stack {
		m.Write16(ss+uint32(sp)-uint32((i+1)*2), v)
	}
	area, base := p.W*p.H, uint32(p.Destination-0xa000)*16
	for plane := 0; plane < 4; plane++ {
		m.Out8(0x3c4, 2)
		m.Out8(0x3c5, 1<<uint(plane))
		for row := 0; row < p.H; row++ {
			off := base + uint32((p.Y+row)*80+p.X)
			src := p.Raw[4+plane*area+row*p.W : 4+plane*area+(row+1)*p.W]
			// Native Go bulk copy updates only the legacy indexed readback surface.
			copy(m.EGAPlane(plane)[off:off+uint32(p.W)], src)
			step := start + 42 + uint64(plane*(8*p.H+9)+row*8)
			for col, value := range src {
				m.NotifyHostVideoWrite(dg.VideoWrite{Step: step, CS: p.segments[dg.CS], IP: p.Write, Offset: off + uint32(col), Value: value, WriteMode: 0})
			}
		}
	}
	m.CPU.R, m.CPU.Seg, m.CPU.IP = p.registers, p.segments, p.Return
	m.CPU.Flags = (p.flags & ^uint16(dg.CF|dg.PF|dg.AF|dg.ZF|dg.SF|dg.OF|dg.DF)) | dg.PF | dg.ZF
	return m.CommitHostWork(p.Steps, p.Cycles, b.Steps, b.Cycles)
}

func installEndingDirect(o *oracle.Oracle, counts map[string]int) {
	for _, entry := range []uint16{0x996, 0x769} {
		o.OnHostCall(oracle.Addr{Seg: 0x393, Off: entry}, func(_ *oracle.Oracle, m *dg.Machine, b oracle.HostWorkLimits) (bool, error) {
			plan, reason := prepareEndingDirect(m, b)
			if plan == nil {
				counts["direct-fallback-"+reason]++
				return false, nil
			}
			if err := plan.commit(m, b); err != nil {
				return false, err
			}
			counts[fmt.Sprintf("direct-accepted-%04x", plan.Entry)]++
			counts["direct-skipped-x86-instructions"] += int(plan.Steps)
			counts["direct-indexed-readback-bytes"] += 4 * plan.W * plan.H
			return true, nil
		})
	}
	for _, row := range []uint16{0x9eb, 0x7be} {
		o.OnHostCall(oracle.Addr{Seg: 0x393, Off: row}, func(_ *oracle.Oracle, m *dg.Machine, b oracle.HostWorkLimits) (bool, error) {
			plan, reason := prepareEndingRow(m, b)
			if plan == nil {
				counts["direct-row-fallback-"+reason]++
				return false, nil
			}
			if err := plan.commit(m, b); err != nil {
				return false, err
			}
			counts["direct-row-batches"]++
			counts["direct-row-copies"] += plan.Rows
			counts["direct-skipped-x86-instructions"] += plan.Rows * 8
			counts["direct-indexed-readback-bytes"] += plan.Rows * plan.Width
			return true, nil
		})
	}
}

type endingRowPlan struct {
	Row, End, Write                uint16
	Width, Rows, Left, X, Y, Plane int
	Destination                    uint32
	Raw                            []byte
	registers                      [8]uint16
	segments                       [4]uint16
	flags                          uint16
}

func prepareEndingRow(m *dg.Machine, b oracle.HostWorkLimits) (*endingRowPlan, string) {
	if !m.CycleClock || !m.CPU.DOSBoxCost || m.VideoMode() != 0x0e || m.CPU.Flags&dg.DF != 0 {
		return nil, "clock-or-mode"
	}
	r, s := m.CPU.R, m.CPU.Seg
	row, entry, ret, end, write := m.CPU.IP, uint16(0), uint16(0), uint16(0), uint16(0)
	want := ""
	switch row {
	case 0x9eb:
		entry, ret, end, write = 0x996, 0xa69, 0xa04, 0x9f6
		want = "603833bfa266acbc8f7a3c8ecf3a30e9f15b5242211367534a7ca1145bb4cfad"
	case 0x7be:
		entry, ret, end, write = 0x769, 0x84e, 0x7d7, 0x7c9
		want = "285723c100da394f2c125b5a1a293c0b24d4f18a8cf2276937ef4a47db4124bc"
	default:
		return nil, "entry"
	}
	code := uint32(s[dg.CS]) * 16
	if s[dg.CS] != 0x393 || fmt.Sprintf("%x", sha256.Sum256(m.Mem[code+uint32(entry):code+uint32(ret)+1])) != want {
		return nil, "code"
	}
	gc, seq, _ := m.VGAState()
	if gc[1]&15 != 0 || gc[3]&31 != 0 || gc[5]&3 != 0 || gc[8] != 255 {
		return nil, "vga-mode"
	}
	plane := -1
	for i := 0; i < 4; i++ {
		if seq[2] == 1<<uint(i) {
			plane = i
		}
	}
	if plane < 0 {
		return nil, "plane-mask"
	}
	ss, bp := uint32(s[dg.SS])*16, uint32(r[dg.BP])
	if bp < 24 || bp+14 > 65536 || ss+bp+14 > 0xa0000 {
		return nil, "stack-bounds"
	}
	w, left := int(m.Read16(ss+bp-2)), int(m.Read16(ss+bp-4))
	x, y := int(m.Read16(ss+bp+10)), int(r[dg.BX])/2
	if w < 1 || left < 1 || r[dg.BX]&1 != 0 || x+w > 80 || y+left > 200 {
		return nil, "geometry"
	}
	if s[dg.ES] != 0xa000 && s[dg.ES] != 0xa400 {
		return nil, "destination"
	}
	if s[dg.DS] != m.Read16(ss+bp+8) {
		return nil, "source-segment"
	}
	originalDS := uint32(m.Read16(ss+bp-22)) * 16
	if originalDS+0x1784 > 0xa0000 || m.Read16(originalDS+0x177a) != 1 || m.Read16(originalDS+0x1780) != s[dg.ES] {
		return nil, "source-mode"
	}
	available := m.HostWorkBudget(b.Steps, b.Cycles)
	n := min(left, int(min(available.Steps/8, available.Cycles/uint64(8+w))))
	if n < 1 {
		return nil, "quota-or-event"
	}
	ptr := uint32(s[dg.DS])*16 + uint32(r[dg.SI])
	size := uint32(w * n)
	if uint32(r[dg.SI])+size > 65536 || ptr+size > 0xa0000 {
		return nil, "source-bounds"
	}
	lo, hi := ss+uint32(r[dg.SP]), ss+bp+14
	if lo > hi || (ptr < hi && lo < ptr+size) || (code < hi && lo < code+uint32(ret)+1) {
		return nil, "stack-alias"
	}
	for i := 0; i < n; i++ {
		if m.Read16(code+uint32((y+i)*2)) != uint16((y+i)*80) {
			return nil, "row-table"
		}
	}
	return &endingRowPlan{row, end, write, w, n, left, x, y, plane, uint32(s[dg.ES]-0xa000) * 16,
		append([]byte(nil), m.Mem[ptr:ptr+size]...), r, s, m.CPU.Flags}, ""
}

func (p *endingRowPlan) commit(m *dg.Machine, b oracle.HostWorkLimits) error {
	start := m.Steps
	for row := 0; row < p.Rows; row++ {
		off := p.Destination + uint32((p.Y+row)*80+p.X)
		src := p.Raw[row*p.Width : (row+1)*p.Width]
		copy(m.EGAPlane(p.Plane)[off:off+uint32(p.Width)], src)
		for col, value := range src {
			m.NotifyHostVideoWrite(dg.VideoWrite{Step: start + 4 + uint64(row*8), CS: p.segments[dg.CS], IP: p.Write, Offset: off + uint32(col), Value: value, WriteMode: 0})
		}
	}
	remaining := p.Left - p.Rows
	m.Write16(uint32(p.segments[dg.SS])*16+uint32(p.registers[dg.BP])-4, uint16(remaining))
	m.CPU.R[dg.BX] += uint16(p.Rows * 2)
	m.CPU.R[dg.SI] += uint16(p.Rows * p.Width)
	m.CPU.R[dg.DI] = uint16((p.Y+p.Rows-1)*80 + p.X + p.Width)
	m.CPU.R[dg.CX] = 0
	m.CPU.Flags = p.flags & ^uint16(dg.CF|dg.PF|dg.AF|dg.ZF|dg.SF|dg.OF)
	if bits.OnesCount8(byte(remaining))&1 == 0 {
		m.CPU.Flags |= dg.PF
	}
	if remaining == 0 {
		m.CPU.Flags |= dg.ZF
		m.CPU.IP = p.End
	} else {
		m.CPU.IP = p.Row
	}
	return m.CommitHostWork(uint64(p.Rows*8), uint64(p.Rows*(8+p.Width)), b.Steps, b.Cycles)
}
