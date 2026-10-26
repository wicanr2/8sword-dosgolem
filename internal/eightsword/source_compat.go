// Spec 047 READY: native Go pixel operations at event boundaries.
// These operate on source bytes/planes. They never generate HD from VGA RGB.
package eightsword

import (
	"crypto/sha256"
	"fmt"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

type compatRasterKind uint8

const (
	compatLatchRead compatRasterKind = iota
	compatGlyphBackground
	compatClearMask
	compatSourceInk
	compatFillMask
	compatRestoreRow
)

type compatRasterSite struct {
	Offset uint16
	Kind   compatRasterKind
}

type compatRasterLayout struct {
	Stage   string
	Entry   oracle.Addr
	Size    uint32
	CodeSHA string
	Sites   []compatRasterSite
}

func compatGlyphLayout(stage string, g sourceGlyphLayout) compatRasterLayout {
	l := compatRasterLayout{Stage: stage, Entry: g.Entry, Size: 0x100, CodeSHA: g.CodeSHA}
	if g.CJK {
		l.Size = 0x160
		l.Sites = []compatRasterSite{{0xb3, compatLatchRead}, {0xb6, compatGlyphBackground}, {0xd9, compatLatchRead}, {0xdc, compatClearMask}, {0xe8, compatSourceInk},
			{0x10d, compatLatchRead}, {0x110, compatGlyphBackground}, {0x133, compatLatchRead}, {0x136, compatClearMask}, {0x142, compatSourceInk}}
	} else {
		l.Sites = []compatRasterSite{{0xba, compatLatchRead}, {0xbd, compatGlyphBackground}, {0xdf, compatLatchRead}, {0xe2, compatClearMask}, {0xeb, compatSourceInk}}
	}
	return l
}

func compatPAMLayouts(t *Tracker) []compatRasterLayout {
	var ls []compatRasterLayout
	for _, g := range pamGlyphLayouts(t) {
		ls = append(ls, compatGlyphLayout("pam", g))
	}
	seg := t.stringSeg
	return append(ls,
		compatRasterLayout{"pam", oracle.Addr{Seg: seg, Off: 0x4f2}, 0x134, "cc7f7579b3ace806dfb714752b00731f675c415f699ef7047648814eb95d6de4", []compatRasterSite{{0x88, compatLatchRead}, {0x8b, compatSourceInk}}},
		compatRasterLayout{"pam", oracle.Addr{Seg: seg, Off: 0x626}, 0x149, "c1cd7da0c0b84fd8e6ac44c073c6a9e653e5d2ab04a3bbd72f577c9324cec40e", []compatRasterSite{{0x8e, compatLatchRead}, {0x92, compatSourceInk}}},
		compatRasterLayout{"pam", oracle.Addr{Seg: seg, Off: 0x274}, 0xaf, "7fd8c6a08d78025b8aa67d84d4200723b6da097d85148d1133c6b09347d2b112", []compatRasterSite{{0x86, compatLatchRead}, {0x89, compatClearMask}, {0x97, compatLatchRead}, {0x9a, compatFillMask}}},
		compatRasterLayout{"pam", oracle.Addr{Seg: seg, Off: 0x423}, 0xcf, "59130f647d8ce03b190ce6f3b514a9d4f951a4d1851d4ceafc70dd5034887dec", []compatRasterSite{{0x5c, compatRestoreRow}}},
	)
}

func compatIntroLayouts() []compatRasterLayout {
	var ls []compatRasterLayout
	for _, g := range introGlyphLayouts() {
		ls = append(ls, compatGlyphLayout("intro", g))
	}
	return append(ls, compatRasterLayout{"intro", oracle.Far(0, 0x52c0), 0x134, introMaskedCodeSHA, []compatRasterSite{{0x88, compatLatchRead}, {0x8b, compatSourceInk}}})
}

func compatEndingLayouts() []compatRasterLayout {
	gs := []sourceGlyphLayout{
		{Entry: oracle.Addr{Seg: 0x28e, Off: 0xef0}, CJK: true, CodeSHA: "dc3197283e3434f6ca35e71592b0c604bc035efef450ed50afffff1309f01739"},
		{Entry: oracle.Addr{Seg: 0x393, Off: 0xb80}, CodeSHA: "5631f527e7a205f772c3c0f0b1c6521781a1264b669d487346dfa1671a5c1692"},
	}
	var ls []compatRasterLayout
	for _, g := range gs {
		ls = append(ls, compatGlyphLayout("ending", g))
	}
	return append(ls, compatRasterLayout{"ending", oracle.Addr{Seg: 0x393, Off: 0x4ec}, 0x134, endingMaskSHA, []compatRasterSite{{0x88, compatLatchRead}, {0x8b, compatSourceInk}}})
}

func compatRasterInstruction(m *dg.Machine, l compatRasterLayout, site compatRasterSite) (bool, string) {
	if m.CPU.Halted || !m.CycleClock || !m.CPU.DOSBoxCost || m.VideoMode() != 0x0e || m.CPU.Flags&0x100 != 0 {
		return false, "clock-or-mode"
	}
	if (site.Kind == compatSourceInk || site.Kind == compatRestoreRow) && m.CPU.Flags&dg.DF != 0 {
		return false, "direction"
	}
	pc := l.Entry.Linear() + uint32(site.Offset)
	if uint32(m.CPU.Seg[dg.CS])*16+uint32(m.CPU.IP) != pc {
		return false, "entry"
	}
	if l.Entry.Linear()+l.Size > 0xa0000 || fmt.Sprintf("%x", sha256.Sum256(m.Mem[l.Entry.Linear():l.Entry.Linear()+l.Size])) != l.CodeSHA {
		return false, "code"
	}
	gc, seq, latches := m.VGAState()
	es, di := m.CPU.Seg[dg.ES], m.CPU.R[dg.DI]
	if (es != 0xa000 && es != 0xa400) || di >= 16000 {
		return false, "destination"
	}
	at := uint32(es-0xa000)*16 + uint32(di)
	if site.Kind == compatRestoreRow {
		ds, n, si := m.CPU.Seg[dg.DS], m.CPU.R[dg.CX], m.CPU.R[dg.SI]
		if (ds != 0xa000 && ds != 0xa400) || n < 1 || n > 80 || si != di || uint32(di)+uint32(n) > 16000 || seq[2]&15 != 15 || gc[5] != 0x11 {
			return false, "restore-layout"
		}
		from := uint32(ds-0xa000)*16 + uint32(si)
		m.ReadHostPlanar(dg.VideoRead{Step: m.Steps, CS: m.CPU.Seg[dg.CS], IP: m.CPU.IP, Offset: from + uint32(n) - 1})
		for plane := 0; plane < 4; plane++ {
			copy(m.EGAPlane(plane)[at:at+uint32(n)], m.EGAPlane(plane)[from:from+uint32(n)])
		}
		m.CPU.R[dg.SI] += n
		m.CPU.R[dg.DI] += n
		m.CPU.R[dg.CX] = 0
		m.CPU.IP += 2
		m.CPU.Cycles += 1 + uint64(n)
		return true, ""
	}
	if site.Kind == compatLatchRead {
		if gc[5]&8 != 0 {
			return false, "read-mode"
		}
		value := m.ReadHostPlanar(dg.VideoRead{Step: m.Steps, CS: m.CPU.Seg[dg.CS], IP: m.CPU.IP, Offset: at})
		m.CPU.R[dg.AX] = m.CPU.R[dg.AX]&255 | uint16(value)<<8
		m.CPU.IP += 3
		m.CPU.Cycles++
		return true, ""
	}
	if gc[3]&31 != 0 || gc[5]&3 != 0 {
		return false, "blend-mode"
	}
	value, size, cycles := byte(0), uint16(4), uint64(1)
	switch site.Kind {
	case compatGlyphBackground:
		if gc[1]&15 != 15 {
			return false, "background-mode"
		}
		size = 3
	case compatClearMask:
		if gc[1]&15 != 0 {
			return false, "clear-mode"
		}
	case compatFillMask:
		if gc[1]&15 != 0 {
			return false, "fill-mode"
		}
		value = 255
	case compatSourceInk:
		if gc[1]&15 != 0 {
			return false, "ink-mode"
		}
		from := uint32(m.CPU.Seg[dg.DS])*16 + uint32(m.CPU.R[dg.SI])
		if from >= 0xa0000 {
			return false, "source-bounds"
		}
		value = m.Mem[from]
		size = 1
		cycles = 2
	default:
		return false, "unknown-kind"
	}
	mask := gc[8]
	for plane := 0; plane < 4; plane++ {
		if seq[2]&(1<<uint(plane)) == 0 {
			continue
		}
		ink := value
		if site.Kind == compatGlyphBackground {
			ink = 0
			if gc[0]&(1<<uint(plane)) != 0 {
				ink = 255
			}
		}
		m.EGAPlane(plane)[at] = latches[plane]&^mask | ink&mask
	}
	if site.Kind == compatSourceInk {
		m.CPU.R[dg.SI]++
		m.CPU.R[dg.DI]++
	}
	m.CPU.IP += size
	m.CPU.Cycles += cycles
	return true, ""
}

func (e *Engine) sourceCompatInstall() func() {
	intro, pam, ending := false, false, false
	guarded := false
	install := func(ls []compatRasterLayout) {
		for _, l := range ls {
			for _, site := range l.Sites {
				at := l.Entry.Linear() + uint32(site.Offset)
				e.Oracle.OnHostInstruction(oracle.Addr{Seg: uint16(at >> 4), Off: uint16(at & 15)}, func(m *dg.Machine) (bool, error) {
					if !e.sourceEnabled || !e.HD {
						return false, nil
					}
					if (l.Stage == "intro" && e.PAMLoaded) || (l.Stage == "pam" && e.inEndingPhase()) || (l.Stage == "ending" && !e.inEndingPhase()) {
						return false, nil
					}
					if e.renderFault != nil {
						return false, e.renderFault
					}
					done, why := compatRasterInstruction(m, l, site)
					if !done {
						e.sourceGuardCall(func() { e.sourceReject("compatibility", why) })
						return false, e.renderFault
					}
					if site.Kind == compatLatchRead {
						e.sourceCompatReads++
					} else if site.Kind == compatRestoreRow {
						e.sourceCompatRestores++
					} else {
						e.sourceCompatWrites++
					}
					return true, nil
				})
			}
		}
	}
	return func() {
		if !e.sourceEnabled || !e.HD || e.renderFault != nil {
			return
		}
		if !guarded {
			e.ObservePresentation(PresentationObserver{Write: func(w PresentationWrite) {
				if e.HD && e.sourceEnabled && e.Oracle.VideoMode() == 0x0e && w.Step == e.Oracle.Steps() {
					e.sourceGuardCall(func() {
						e.sourceRejectAt("compatibility", "native-video-write-leftover", w.Step, w.CS, w.IP, e.Oracle.VideoMode())
					})
				}
			}})
			guarded = true
		}
		if e.inEndingPhase() {
			if !ending {
				install(compatEndingLayouts())
				ending = true
			}
			return
		}
		if e.Tracker != nil && e.Tracker.loadSegment != 0 {
			if !pam {
				install(compatPAMLayouts(e.Tracker))
				pam = true
			}
			return
		}
		if !intro && fmt.Sprintf("%x", sha256.Sum256(e.Oracle.Bytes(oracle.Far(0, 0x576a), 212))) == "88d6cfe05ddb19b00bd42cb4857a95cbcf9bdf764320ea21e503b9f202a947d8" {
			install(compatIntroLayouts())
			intro = true
		}
	}
}
