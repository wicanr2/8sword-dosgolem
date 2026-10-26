// 047 READY. Source plans and compatibility data; no original RGB rendering.
package eightsword

import (
	"crypto/sha256"
	"fmt"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

type runtimePlanarPlan struct {
	Primitive                        string `json:",omitempty"`
	SourceEntry                      uint16 `json:",omitempty"`
	Plane, Row, Column               int    `json:",omitempty"`
	CompatibilityBytes               uint64 `json:",omitempty"`
	SourceSHA256                     string
	Entry, ReturnBoundary, WriteSite uint16
	XByte, Y, WidthBytes, Height     int
	Destination                      uint16
	Steps, Cycles                    uint64
	Raw                              []byte `json:"-"`
	registers                        [8]uint16
	segments                         [4]uint16
	flags                            uint16
	stack                            []uint16
	commitExtra                      func(*dg.Machine, oracle.HostWorkLimits) error
}

var runtimeDirectEntries = []uint16{0x99c, 0x76f}
var runtimePlanarExtra func(*dg.Machine, oracle.HostWorkLimits) (*runtimePlanarPlan, string)
var runtimePlanarRowExtra func(*dg.Machine, oracle.HostWorkLimits) (*runtimePlanarPlan, string)

func (p *runtimePlanarPlan) compatibilityBytes() uint64 {
	if p.CompatibilityBytes != 0 {
		return p.CompatibilityBytes
	}
	return uint64(p.WidthBytes * p.Height * 4)
}

func runtimePlanarPrepare(m *dg.Machine, b oracle.HostWorkLimits) (*runtimePlanarPlan, string) {
	if !m.CycleClock || !m.CPU.DOSBoxCost {
		return nil, "clock-mode"
	}
	r, s := m.CPU.R, m.CPU.Seg
	if m.VideoMode() != 0x0e {
		return nil, "entry-mode"
	}
	entry, ret, writeSite, planes := m.CPU.IP, uint16(0), uint16(0), 0
	want := ""
	switch entry {
	case 0x99c:
		ret, writeSite, planes = 0xa6f, 0x9fc, 4
		want = "a2f457e4ad98813eb3b8e2d727e71074b612c52b473cc3153ce42f915c1b70c8"
	case 0x76f:
		ret, writeSite, planes = 0x854, 0x7cf, 5
		want = "49285f927aa83c57fce4d990102e6fda59e61581d8b571bb8c8d9ebc5e255419"
	default:
		if runtimePlanarExtra != nil {
			return runtimePlanarExtra(m, b)
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
	if sp < 30 || uint32(sp)+12 > 65536 || ss+uint32(sp)+12 > 0xa0000 {
		return nil, "stack-bounds"
	}
	arg := func(i uint32) uint16 { return m.Read16(ss + uint32(sp) + 4 + i*2) }
	ptr := uint32(arg(1))*16 + uint32(arg(0))
	if ptr+4 > 0xa0000 {
		return nil, "source-header"
	}
	w, h := int(m.Read16(ptr)), int(m.Read16(ptr+2))
	x, y := int(arg(2)), int(arg(3))
	if w < 1 || h < 1 || w > 80 || h > 200 || x+w > 80 || y+h > 200 {
		return nil, "geometry"
	}
	size := 4 + planes*w*h
	if int(arg(0))+size > 65536 || ptr+uint32(size) > 0xa0000 {
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
	lo, hi := ss+uint32(sp)-30, ss+uint32(sp)+12
	overlaps := func(a, z uint32) bool { return a < hi && lo < z }
	if overlaps(ptr, ptr+uint32(size)) || overlaps(code, code+uint32(ret)+1) || overlaps(ds+0x7484, ds+0x748c) {
		return nil, "stack-alias"
	}
	for row := 0; row < h; row++ {
		if m.Read16(code+6+uint32((y+row)*2)) != uint16((y+row)*80) {
			return nil, "row-table"
		}
	}
	// The final RETF remains native, so its hooks, stack read and cycle cost
	// execute normally. DOSBox cost counts instructions plus REP iterations.
	steps := uint64(32*h + 81)
	cycles := steps + uint64(4*w*h)
	if steps > b.Steps || cycles > b.Cycles {
		return nil, "quota"
	}
	available := m.HostWorkBudget(b.Steps, b.Cycles)
	if steps > available.Steps || cycles > available.Cycles {
		return nil, "machine-event"
	}
	raw := append([]byte(nil), m.Mem[ptr:ptr+uint32(size)]...)
	// Only the low byte of [bp-6] is written by MOV/SHL byte instructions.
	planeSlot := m.Read16(ss+uint32(sp)-8)&0xff00 | 0x10
	stack := []uint16{r[dg.BP], uint16(w), uint16(h), planeSlot, uint16(w * h), r[dg.AX], r[dg.BX], r[dg.CX], r[dg.DX], r[dg.SI], r[dg.DI], s[dg.DS], s[dg.ES], uint16(h), uint16(y * 2)}
	return &runtimePlanarPlan{SourceSHA256: fmt.Sprintf("%x", sha256.Sum256(raw)), Entry: entry, ReturnBoundary: ret, WriteSite: writeSite, XByte: x, Y: y, WidthBytes: w, Height: h, Destination: dest, Steps: steps, Cycles: cycles, Raw: raw, registers: r, segments: s, flags: m.CPU.Flags, stack: stack}, ""
}

func (p *runtimePlanarPlan) commit(m *dg.Machine, b oracle.HostWorkLimits) error {
	if p.commitExtra != nil {
		return p.commitExtra(m, b)
	}
	start := m.Steps
	ss, sp := uint32(p.segments[dg.SS])*16, p.registers[dg.SP]
	for i, v := range p.stack {
		m.Write16(ss+uint32(sp)-uint32((i+1)*2), v)
	}
	area := p.WidthBytes * p.Height
	base := uint32(p.Destination-0xa000) * 16
	for plane := 0; plane < 4; plane++ {
		m.Out8(0x3c4, 2)
		m.Out8(0x3c5, 1<<uint(plane))
		for row := 0; row < p.Height; row++ {
			step := start + 42 + uint64(plane*(8*p.Height+9)+row*8)
			for col := 0; col < p.WidthBytes; col++ {
				off := base + uint32((p.Y+row)*80+p.XByte+col)
				value := p.Raw[4+plane*area+row*p.WidthBytes+col]
				m.EGAPlane(plane)[off] = value
				m.NotifyHostVideoWrite(dg.VideoWrite{Step: step, CS: p.segments[dg.CS], IP: p.WriteSite, Offset: off, Value: value, WriteMode: 0})
			}
		}
	}
	m.CPU.R = p.registers
	m.CPU.Seg = p.segments
	m.CPU.IP = p.ReturnBoundary
	m.CPU.Flags = (p.flags & ^uint16(dg.CF|dg.PF|dg.AF|dg.ZF|dg.SF|dg.OF|dg.DF)) | dg.PF | dg.ZF
	return m.CommitHostWork(p.Steps, p.Cycles, b.Steps, b.Cycles)
}

func (e *Engine) sourceDirectInstall() func() {
	bound := false
	return func() {
		t := e.Tracker
		if !e.sourceEnabled || !e.HD || bound || t == nil || t.loadSegment == 0 {
			return
		}
		bound = true
		for _, entry := range runtimeDirectEntries {
			e.Oracle.OnHostCall(oracle.Addr{Seg: t.stringSeg, Off: entry}, func(o *oracle.Oracle, m *dg.Machine, b oracle.HostWorkLimits) (bool, error) {
				if !e.sourceEnabled || !e.HD || e.renderFault != nil {
					return false, nil
				}
				plan, _ := runtimePlanarPrepare(m, b)
				if plan == nil {
					return false, nil
				}
				if err := plan.commit(m, b); err != nil {
					return false, err
				}
				e.sourceDirectCalls++
				return true, nil
			})
		}
	}
}
