// 047 READY. Native Go clear/copy at the original atomic REP boundary.
package eightsword

import (
	"crypto/sha256"
	"fmt"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

type sourcePageLayout struct {
	Entry   oracle.Addr
	Clear   bool
	CodeSHA string
}

func pamPageLayouts(seg uint16) []sourcePageLayout {
	return []sourcePageLayout{
		{oracle.Addr{Seg: seg, Off: 0xd3e}, true, "6c3417e691a1dc0487dd32ab5a277d0dd15c008127babc1213861400738e0c01"},
		{oracle.Addr{Seg: seg, Off: 0x33d}, false, "faa92f6dfda7d9d587f9279dac67ec33897fe9cde2fa1c1a21d9aacc1c04fb2c"},
		{oracle.Addr{Seg: seg, Off: 0x3b0}, false, "9c6604f617ce1421dd00d7f46e665e37416b00e822338f86dba879b13785aa36"},
	}
}

func introPageLayouts() []sourcePageLayout {
	return []sourcePageLayout{
		{oracle.Far(0, 0x5b0c), true, "9b2e2e5b7c9b878690e526de6705910ee57066806e3a44c3b51fdf853176c76f"},
		{oracle.Far(0, 0x510b), false, "faa92f6dfda7d9d587f9279dac67ec33897fe9cde2fa1c1a21d9aacc1c04fb2c"},
		{oracle.Far(0, 0x517e), false, "9c6604f617ce1421dd00d7f46e665e37416b00e822338f86dba879b13785aa36"},
	}
}

func endingPageLayouts() []sourcePageLayout {
	return []sourcePageLayout{
		{oracle.Addr{Seg: 0x393, Off: 0xd38}, true, "f64a64cc8b397aa4b1202678a1fb57a2e98f2e9e742091aee26839486238fa33"},
		{oracle.Addr{Seg: 0x393, Off: 0x3aa}, false, "9c6604f617ce1421dd00d7f46e665e37416b00e822338f86dba879b13785aa36"},
	}
}

func (l sourcePageLayout) rep() oracle.Addr {
	n := uint16(0x27)
	if l.Clear {
		n = 0x2f
	}
	return oracle.Addr{Seg: l.Entry.Seg, Off: l.Entry.Off + n}
}

// The routine prologue and epilogue remain ordinary original instructions.
// The admitted REP performs native array clear/copy; no x86 Step is called.
// Source adapters apply their already typed page command at the original RETF.
func sourcePageInstruction(m *dg.Machine, l sourcePageLayout) (bool, error) {
	if m.CPU.Halted || !m.CycleClock || !m.CPU.DOSBoxCost || m.VideoMode() != 0x0e || m.CPU.Flags&(dg.DF|0x100) != 0 {
		return false, nil
	}
	if uint32(m.CPU.Seg[dg.CS])*16+uint32(m.CPU.IP) != l.rep().Linear() {
		return false, nil
	}
	size := uint32(0x35)
	if l.Clear {
		size = 0x37
	}
	if l.Entry.Linear()+size > 0xa0000 || fmt.Sprintf("%x", sha256.Sum256(m.Mem[l.Entry.Linear():l.Entry.Linear()+size])) != l.CodeSHA {
		return false, nil
	}
	gc, seq, _ := m.VGAState()
	if m.CPU.R[dg.DI] != 0 {
		return false, nil
	}
	es := m.CPU.Seg[dg.ES]
	if es != 0xa000 && es != 0xa400 {
		return false, nil
	}
	to := uint32(es-0xa000) * 16
	count := m.CPU.R[dg.CX]
	if l.Clear {
		if count != 0x4000 || m.CPU.R[dg.AX] != 0 || gc[1]&15 != 0 || gc[3]&31 != 0 || gc[5]&3 != 0 || gc[8] != 255 {
			return false, nil
		}
		for plane := 0; plane < 4; plane++ {
			if seq[2]&(1<<uint(plane)) != 0 {
				clear(m.EGAPlane(plane)[to : to+uint32(count)])
			}
		}
	} else {
		ds := m.CPU.Seg[dg.DS]
		if count != 16000 || m.CPU.R[dg.SI] != 0 || seq[2]&15 != 15 || gc[5] != 0x11 || (ds != 0xa000 && ds != 0xa400) || ds == es {
			return false, nil
		}
		from := uint32(ds-0xa000) * 16
		// The final source read retains all four VGA latches for subsequent code.
		m.ReadHostPlanar(dg.VideoRead{Step: m.Steps, CS: m.CPU.Seg[dg.CS], IP: m.CPU.IP, Offset: from + uint32(count) - 1})
		for plane := 0; plane < 4; plane++ {
			copy(m.EGAPlane(plane)[to:to+uint32(count)], m.EGAPlane(plane)[from:from+uint32(count)])
		}
		m.CPU.R[dg.SI] += count
	}
	m.CPU.R[dg.DI] += count
	m.CPU.R[dg.CX] = 0
	m.CPU.IP += 2
	m.CPU.Cycles += 1 + uint64(count)
	return true, nil
}

func (e *Engine) sourcePageInstall() func() {
	intro, pam, ending := false, false, false
	install := func(layouts []sourcePageLayout) {
		for _, l := range layouts {
			e.Oracle.OnHostInstruction(l.rep(), func(m *dg.Machine) (bool, error) {
				if !e.sourceEnabled || !e.HD || e.renderFault != nil {
					return false, nil
				}
				done, err := sourcePageInstruction(m, l)
				if done {
					if l.Clear {
						e.sourcePageClears++
					} else {
						e.sourcePageCopies++
					}
				}
				return done, err
			})
		}
	}
	return func() {
		if !e.sourceEnabled || !e.HD || e.renderFault != nil {
			return
		}
		if e.inEndingPhase() {
			if !ending {
				install(endingPageLayouts())
				e.installSourceBitmapRows(endingBitmapRows())
				ending = true
			}
			return
		}
		if e.Tracker != nil && e.Tracker.loadSegment != 0 {
			if !pam {
				install(pamPageLayouts(e.Tracker.stringSeg))
				e.installSourceBitmapRows(pamBitmapRows(e.Tracker.stringSeg))
				pam = true
			}
			return
		}
		if !intro && fmt.Sprintf("%x", sha256.Sum256(e.Oracle.Bytes(oracle.Far(0, 0x576a), 212))) == "88d6cfe05ddb19b00bd42cb4857a95cbcf9bdf764320ea21e503b9f202a947d8" {
			install(introPageLayouts())
			e.installSourceBitmapRows(introBitmapRows())
			intro = true
		}
	}
}
