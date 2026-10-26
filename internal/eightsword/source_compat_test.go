package eightsword

import (
	"bytes"
	"errors"
	"fmt"
	"image"
	"os"
	"path/filepath"
	"testing"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func compatFixture(t *testing.T, project string, l compatRasterLayout, dest uint16) *dg.Machine {
	t.Helper()
	m := sourcePageFixture(t, project, l.Stage, sourcePageLayout{Entry: l.Entry}, dest, 15)
	m.CPU.Cycles = 0
	m.VGAFrameEvery = 0
	cs := uint16(0x14d2)
	if l.Stage == "intro" {
		cs = 0x4dd
		if l.Entry.Linear() == 0x4c74 {
			cs = 0x231
		}
	}
	if l.Stage == "pam" && l.Entry.Seg == 0xaa8 {
		cs = 0xaa8
	}
	if l.Stage == "ending" {
		cs = l.Entry.Seg
	}
	m.CPU.Seg[dg.CS] = cs
	m.CPU.IP = uint16(l.Entry.Linear() - uint32(cs)*16)
	if l.Stage == "pam" {
		for row := 0; row < 200; row++ {
			m.Write16(0x14d20+6+uint32(row*2), uint16(row*80))
		}
	}
	return m
}

func compatCall(t *testing.T, a, h *dg.Machine, l compatRasterLayout) {
	t.Helper()
	accepted, hostWrites, nativeWrites, escapedWrites := 0, 0, 0, 0
	a.ObserveVideoWrites(func(dg.VideoWrite) { nativeWrites++ })
	h.ObserveVideoWrites(func(dg.VideoWrite) { escapedWrites++ })
	for _, site := range l.Sites {
		pc := l.Entry.Linear() + uint32(site.Offset)
		h.InstallHostInstruction(pc, func(m *dg.Machine) (bool, error) {
			done, why := compatRasterInstruction(m, l, site)
			if !done {
				gc, seq, _ := m.VGAState()
				t.Fatalf("native Go rejection %s pc%x regs%v seg%v gc%v seq%v", why, pc, m.CPU.R, m.CPU.Seg, gc, seq)
			}
			accepted++
			if site.Kind != compatLatchRead {
				hostWrites++
			}
			return true, nil
		})
	}
	ret := l.Entry.Linear() + l.Size - 1
	for uint32(a.CPU.Seg[dg.CS])*16+uint32(a.CPU.IP) != ret && a.Steps < 20000 {
		before := accepted
		if err := a.Step(); err != nil {
			t.Fatal(err)
		}
		if err := h.Step(); err != nil {
			t.Fatal(err)
		}
		if accepted != before {
			sourceGlyphState(t, a, h, nil, nil)
		}
	}
	if uint32(a.CPU.Seg[dg.CS])*16+uint32(a.CPU.IP) != ret || hostWrites == 0 || nativeWrites == 0 || escapedWrites != 0 {
		t.Fatal("call/Go write gate missing", accepted, hostWrites, nativeWrites, escapedWrites)
	}
	sourceGlyphState(t, a, h, nil, nil)
	for i := 0; i < 30; i++ {
		if err := a.Step(); err != nil {
			t.Fatal(err)
		}
		if err := h.Step(); err != nil {
			t.Fatal(err)
		}
	}
	sourceGlyphState(t, a, h, nil, nil)
}

func TestSourceCompatNativeGlyphs(t *testing.T) {
	project := os.Getenv("EIGHTSWORD_GLYPH_PROJECT")
	if project == "" {
		t.Skip("需唯讀專案")
	}
	sets := [][]compatRasterLayout{compatPAMLayouts(&Tracker{fontSeg: 0xaa8, stringSeg: 0x14d2})[:2], compatIntroLayouts()[:2], compatEndingLayouts()[:2]}
	for _, ls := range sets {
		for index, l := range ls {
			for _, dest := range []uint16{0xa000, 0xa400} {
				for _, colors := range [][2]byte{{14, 255}, {0, 0}, {15, 4}} {
					t.Run(fmt.Sprintf("%s/%d/%x/%v", l.Stage, index, dest, colors), func(t *testing.T) {
						makeMachine := func() *dg.Machine {
							m := compatFixture(t, project, l, dest)
							fg := uint32(0x748c)
							if l.Stage == "intro" {
								fg = 0x1efa
							}
							if l.Stage == "ending" {
								fg = 0x1782
							}
							ds := uint32(m.CPU.Seg[dg.DS]) * 16
							m.Mem[ds+fg] = colors[0]
							m.Mem[ds+fg+1] = colors[1]
							code := uint16(65)
							x := uint16(79)
							if index == 0 {
								code = 90
								x = 78
							}
							for i, v := range []uint16{code, x, 185} {
								m.Write16(0x9ff04+uint32(i*2), v)
							}
							return m
						}
						compatCall(t, makeMachine(), makeMachine(), l)
					})
				}
			}
		}
	}
}

func TestSourceCompatNativeMasked(t *testing.T) {
	project := os.Getenv("EIGHTSWORD_GLYPH_PROJECT")
	if project == "" {
		t.Skip("需唯讀專案")
	}
	ps := compatPAMLayouts(&Tracker{fontSeg: 0xaa8, stringSeg: 0x14d2})
	ls := []compatRasterLayout{ps[2], ps[3], compatIntroLayouts()[2], compatEndingLayouts()[2]}
	for _, l := range ls {
		for _, dest := range []uint16{0xa000, 0xa400} {
			for _, w := range []int{1, 4} {
				if l.Entry.Off == 0x626 && dest == 0xa400 {
					continue
				}
				t.Run(fmt.Sprintf("%s/%x/%x/w%d", l.Stage, l.Entry.Off, dest, w), func(t *testing.T) {
					makeMachine := func() *dg.Machine {
						m := compatFixture(t, project, l, dest)
						m.Write16(0x60020, uint16(w))
						m.Write16(0x60022, 3)
						for i := 0; i < 6*w*3; i++ {
							m.Mem[0x60024+i] = byte(i*31 + 17)
						}
						for i, v := range []uint16{0x20, 0x6000, 0, 197} {
							m.Write16(0x9ff04+uint32(i*2), v)
						}
						return m
					}
					compatCall(t, makeMachine(), makeMachine(), l)
				})
			}
		}
	}
}

func TestSourceCompatNativePlotAndRestore(t *testing.T) {
	project := os.Getenv("EIGHTSWORD_GLYPH_PROJECT")
	if project == "" {
		t.Skip("需唯讀專案")
	}
	ls := compatPAMLayouts(&Tracker{fontSeg: 0xaa8, stringSeg: 0x14d2})
	for _, dest := range []uint16{0xa000, 0xa400} {
		for _, x := range []uint16{0, 7, 8, 639} {
			for _, fg := range []byte{0, 5, 15} {
				l := ls[4]
				t.Run(fmt.Sprintf("plot/%x/x%d/fg%d", dest, x, fg), func(t *testing.T) {
					makeMachine := func() *dg.Machine {
						m := compatFixture(t, project, l, dest)
						m.Mem[0x1e880+0x748c] = fg
						m.Write16(0x9ff04, x)
						m.Write16(0x9ff06, 199)
						return m
					}
					compatCall(t, makeMachine(), makeMachine(), l)
				})
			}
		}
	}
	for _, dest := range []uint16{0xa000, 0xa400} {
		for _, w := range []int{1, 80} {
			l := ls[5]
			t.Run(fmt.Sprintf("restore/%x/w%d", dest, w), func(t *testing.T) {
				makeMachine := func() *dg.Machine {
					m := compatFixture(t, project, l, dest)
					m.Write16(0x14d20+0x196, 0xa400)
					m.Write16(0x60020, uint16(w))
					m.Write16(0x60022, 4)
					for i, v := range []uint16{0x20, 0x6000, 0, 196} {
						m.Write16(0x9ff04+uint32(i*2), v)
					}
					return m
				}
				compatCall(t, makeMachine(), makeMachine(), l)
			})
		}
	}
}

func TestSourceCompatNativeGuard(t *testing.T) {
	root, assets := os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if root == "" || assets == "" {
		t.Skip("需唯讀原版與素材")
	}
	e, err := Open(Options{Root: root, Assets: assets, Saves: filepath.Join(t.TempDir(), "scratch"), HD: true})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(e.Close)
	e.EnableLiveClock(3000)
	// Start the renderer lifecycle before injecting the unsupported writer.
	// Advance normally binds after a bounded guest run, not before CallNear.
	e.sourceInstall()
	held := image.NewRGBA(image.Rect(0, 0, 1920, 1200))
	held.Pix[0] = 123
	e.sourceHeldFrame = held
	entry := oracle.Addr{Seg: 0x8000, Off: 0}
	// Controlled RAM program: mode 0E, an unregistered video store, then wait.
	// This verifies the fence; it is not a natural player path.
	e.Oracle.WriteBytes(entry, []byte{0xb8, 0x0e, 0, 0xcd, 0x10, 0xb8, 0, 0xa0, 0x8e, 0xc0, 0x26, 0xc6, 0x06, 0, 0, 0x5a, 0xeb, 0xfe})
	e.Oracle.CallNear(entry, 0, oracle.CallRegs{})
	err = e.AdvanceCycles(100000)
	var fault *OwnedRenderFault
	if !errors.As(err, &fault) || fault.Phase != "compatibility" || fault.Reason != "native-video-write-leftover" {
		t.Fatal("native pixel fence absent", err, e.Oracle.VideoMode(), e.Oracle.Regs())
	}
	state := observerGuestState(t, e)
	if e.Frame() != held || e.AdvanceCycles(1000) != fault || !bytes.Equal(state, observerGuestState(t, e)) {
		t.Fatal("pixel fence loses complete frame or resumes guest")
	}
}

func TestSourceCompatNativeRejectsWithoutMutation(t *testing.T) {
	project := os.Getenv("EIGHTSWORD_GLYPH_PROJECT")
	if project == "" {
		t.Skip("需唯讀專案")
	}
	l := compatPAMLayouts(&Tracker{fontSeg: 0xaa8, stringSeg: 0x14d2})[4]
	site := l.Sites[1]
	cases := map[string]func(*dg.Machine){
		"changed-code":        func(m *dg.Machine) { m.Mem[l.Entry.Linear()] ^= 255 },
		"wrong-pc":            func(m *dg.Machine) { m.CPU.IP++ },
		"outside-page":        func(m *dg.Machine) { m.CPU.R[dg.DI] = 16000 },
		"wrong-segment":       func(m *dg.Machine) { m.CPU.Seg[dg.ES] = 0xb000 },
		"unsupported-rop":     func(m *dg.Machine) { m.Out8(0x3ce, 3); m.Out8(0x3cf, 8) },
		"unexpected-setreset": func(m *dg.Machine) { m.Out8(0x3ce, 1); m.Out8(0x3cf, 15) },
		"halted":              func(m *dg.Machine) { m.CPU.Halted = true },
	}
	for name, mutate := range cases {
		t.Run(name, func(t *testing.T) {
			m := compatFixture(t, project, l, 0xa000)
			m.Write16(0x9ff04, 639)
			m.Write16(0x9ff06, 199)
			for uint32(m.CPU.Seg[dg.CS])*16+uint32(m.CPU.IP) != l.Entry.Linear()+uint32(site.Offset) && m.Steps < 100 {
				if err := m.Step(); err != nil {
					t.Fatal(err)
				}
			}
			mutate(m)
			var before, after bytes.Buffer
			m.SaveState(&before)
			if ok, _ := compatRasterInstruction(m, l, site); ok {
				t.Fatal("invalid pixel accepted")
			}
			m.SaveState(&after)
			if !bytes.Equal(before.Bytes(), after.Bytes()) {
				t.Fatal("rejection changes guest")
			}
		})
	}
}
