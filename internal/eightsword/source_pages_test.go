package eightsword

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"os"
	"path/filepath"
	"testing"

	dg "github.com/wicanr2/dosgolem"
)

func sourcePageFixture(t *testing.T, project, phase string, l sourcePageLayout, dest uint16, mask byte) *dg.Machine {
	t.Helper()
	m := dg.New()
	m.SetVideoMode(0x0e)
	m.SetDOSBoxCycles(3000)
	if os.Getenv("EIGHTSWORD_TEST_STEP_CLOCK") == "1" {
		m.SetDOSBoxCycles(0)
		m.IRQ0Base = 128
		m.SetDOSBoxCycles(0)
	}
	m.CPU.Cycles = 164000 // REP crosses the first cycle-clock IRQ deadline.
	m.VGAFrameEvery = 3
	cs, ds := uint16(0x14d2), uint16(0x1e88)
	mode, target, fg := uint32(0x7484), uint32(0x748a), uint32(0x748c)
	path := "workplace/intake-20261023/sources/game/8sword/PAM.AY"
	if phase == "intro" {
		path = "workplace/probe-20261023/music-first/intro-events-r1/PREDELLA-runtime-analysis.exe"
		cs = 0x4dd
		ds = 0xb31
		mode, target, fg = 0x1ef2, 0x1ef8, 0x1efa
	}
	if phase == "ending" {
		path = "workplace/probe-20261023/graphics-first/ending-hd-r1/startup-r3/ram-00000-9ffff.bin"
		cs = 0x393
		ds = 0x7e4
		mode, target, fg = 0x177a, 0x1780, 0x1782
	}
	raw, err := os.ReadFile(filepath.Join(project, path))
	if err != nil {
		t.Fatal(err)
	}
	if phase == "ending" {
		copy(m.Mem, raw)
	} else {
		hdr := int(binary.LittleEndian.Uint16(raw[8:])) * 16
		copy(m.Mem[0x1100:], raw[hdr:])
		for i := 0; i < int(binary.LittleEndian.Uint16(raw[6:])); i++ {
			p := int(binary.LittleEndian.Uint16(raw[24:])) + i*4
			at := uint32(0x1100) + uint32(binary.LittleEndian.Uint16(raw[p:])) + uint32(binary.LittleEndian.Uint16(raw[p+2:]))*16
			m.Write16(at, m.Read16(at)+0x110)
		}
	}
	// Machine-only fixtures need a real IRET, not Oracle's BIOS stub dispatch.
	m.Write16(0x20, 0)
	m.Write16(0x22, 0x7000)
	m.Mem[0x70000] = 0xcf
	m.Write16(uint32(ds)*16+mode, 1)
	m.Write16(uint32(ds)*16+target, dest)
	m.Mem[uint32(ds)*16+fg] = mask
	m.CPU.R = [8]uint16{0x1234, 0x2345, 0x3456, 0x4567, 0xff00, 0x6789, 0x789a, 0x89ab}
	m.CPU.Seg = [4]uint16{0x7000, cs, 0x9000, ds}
	m.CPU.IP = uint16(l.Entry.Linear() - uint32(cs)*16)
	m.CPU.Flags = 0x602
	for i := 0; i < 32; i++ {
		m.Mem[0x9fee0+i] = 0xc7 + byte(i)
	}
	m.Write16(0x9ff00, 0xfff0)
	m.Write16(0x9ff02, 0x110)
	for p := 0; p < 4; p++ {
		for off := range m.EGAPlane(p) {
			m.EGAPlane(p)[off] = byte(off*7 + p*31)
		}
	}
	m.Out8(0x3ce, 4)
	m.Out8(0x3cf, 2)
	m.Read8(0xa0000 + 77)
	return m
}

func TestResearchSourcePageOracle(t *testing.T) {
	project := os.Getenv("EIGHTSWORD_GLYPH_PROJECT")
	if project == "" {
		t.Skip("需唯讀專案")
	}
	for _, phase := range []string{"pam", "intro", "ending"} {
		layouts := pamPageLayouts(0x14d2)
		if phase == "intro" {
			layouts = introPageLayouts()
		}
		if phase == "ending" {
			layouts = endingPageLayouts()
		}
		for index, l := range layouts {
			for _, dest := range []uint16{0xa000, 0xa400} {
				for _, mask := range []byte{0, 1, 5, 15} {
					t.Run(fmt.Sprintf("%s/%d/%x/mask%d", phase, index, dest, mask), func(t *testing.T) {
						a, h := sourcePageFixture(t, project, phase, l, dest, mask), sourcePageFixture(t, project, phase, l, dest, mask)
						calls := 0
						h.InstallHostInstruction(l.rep().Linear(), func(m *dg.Machine) (bool, error) {
							done, err := sourcePageInstruction(m, l)
							if done {
								calls++
							} else {
								gc, seq, _ := m.VGAState()
								t.Logf("REP rejected IP%x seg%v regs%v flags%x gc%v seq%v", m.CPU.IP, m.CPU.Seg, m.CPU.R, m.CPU.Flags, gc, seq)
							}
							return done, err
						})
						ret := l.Entry.Linear() + 0x34
						if l.Clear {
							ret = l.Entry.Linear() + 0x36
						}
						for uint32(a.CPU.Seg[dg.CS])*16+uint32(a.CPU.IP) != ret && a.Steps < 10000 {
							if err := a.Step(); err != nil {
								t.Fatal(err)
							}
							if err := h.Step(); err != nil {
								t.Fatal(err)
							}
							var x, y bytes.Buffer
							a.SaveState(&x)
							h.SaveState(&y)
							if !bytes.Equal(x.Bytes(), y.Bytes()) {
								t.Fatalf("atomic state differs step%d/%d cycles%d/%d IP%x/%x flags%x/%x regs%v/%v", a.Steps, h.Steps, a.CPU.Cycles, h.CPU.Cycles, a.CPU.IP, h.CPU.IP, a.CPU.Flags, h.CPU.Flags, a.CPU.R, h.CPU.R)
							}
						}
						if calls != 1 {
							t.Fatal("native Go REP absent", calls)
						}
						// Include the original RETF and a due IRQ following an atomic REP.
						for i := 0; i < 30; i++ {
							if err := a.Step(); err != nil {
								t.Fatal(err)
							}
							if err := h.Step(); err != nil {
								t.Fatal(err)
							}
						}
						sourceGlyphState(t, a, h, nil, nil)
					})
				}
			}
		}
	}
}
