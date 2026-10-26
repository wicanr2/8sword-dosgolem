package eightsword

import (
	"bytes"
	"fmt"
	"image"
	"os"
	"path/filepath"
	"testing"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func TestResearchIntroMaskedOracle(t *testing.T) {
	project := os.Getenv("EIGHTSWORD_GLYPH_PROJECT")
	if project == "" {
		t.Skip("需唯讀專案")
	}
	entry := oracle.Far(0, 0x52c0)
	for _, dest := range []uint16{0xa000, 0xa400} {
		for _, w := range []int{1, 4} {
			for _, quota := range []uint64{100000, 100, 18} {
				t.Run(fmt.Sprintf("%x/w%d/quota%d", dest, w, quota), func(t *testing.T) {
					a, h := sourcePageFixture(t, project, "intro", sourcePageLayout{Entry: entry}, dest, 15), sourcePageFixture(t, project, "intro", sourcePageLayout{Entry: entry}, dest, 15)
					for _, m := range []*dg.Machine{a, h} {
						m.CPU.Cycles = 0
						m.Write16(0x60020, uint16(w))
						m.Write16(0x60022, 3)
						for i := 0; i < 6*w*3; i++ {
							m.Mem[0x60024+i] = byte(i*31 + 17)
						}
						for i, v := range []uint16{0x20, 0x6000, 0, 197} {
							m.Write16(0x9ff04+uint32(i*2), v)
						}
					}
					var ae, he []sourceGlyphEvent
					sourceGlyphWatch(a, &ae)
					sourceGlyphWatch(h, &he)
					calls, skipped := 0, uint64(0)
					for uint32(a.CPU.Seg[dg.CS])*16+uint32(a.CPU.IP) != 0x53f3 && a.Steps < 10000 {
						at := uint32(h.CPU.Seg[dg.CS])*16 + uint32(h.CPU.IP)
						if at == 0x52c0 || at == 0x533d {
							b := oracle.HostWorkLimits{Steps: quota, Cycles: quota}
							if p, _ := runtimePlanarPrepare(h, b); p != nil {
								stop := a.Steps + p.Steps
								for a.Steps < stop {
									if err := a.Step(); err != nil {
										t.Fatal(err)
									}
								}
								if err := p.commit(h, b); err != nil {
									t.Fatal(err)
								}
								sourceGlyphState(t, a, h, ae, he)
								calls++
								skipped += p.Steps
								continue
							}
						}
						if err := a.Step(); err != nil {
							t.Fatal(err)
						}
						if err := h.Step(); err != nil {
							t.Fatal(err)
						}
					}
					if calls == 0 || skipped == 0 {
						t.Fatal("opening native Go mask absent")
					}
					if err := a.Step(); err != nil {
						t.Fatal(err)
					}
					if err := h.Step(); err != nil {
						t.Fatal(err)
					}
					sourceGlyphState(t, a, h, ae, he)
				})
			}
		}
	}
}

func TestResearchIntroMaskedNormal(t *testing.T) {
	root, assets := os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if root == "" || assets == "" {
		t.Skip("需唯讀原版與正式素材")
	}
	var engines [2]*Engine
	for i := range engines {
		e, err := Open(Options{Root: root, Assets: assets, Saves: filepath.Join(t.TempDir(), fmt.Sprint(i)), HD: true})
		if err != nil {
			t.Fatal(err)
		}
		t.Cleanup(e.Close)
		e.Oracle.SetClock(12, 0, 0, 0)
		e.EnableLiveClock(3000)
		engines[i] = e
	}
	c := engines[0]
	pi, pf, pc := c.newSourcePAM()
	ii, iff, ic := c.newSourceIntro()
	c.sourceInstall = func() { ii(); pi() }
	c.sourceClose = func() { ic(); pc() }
	c.sourceRender = func() *image.RGBA {
		if im := pf(); im != nil {
			return im
		}
		return iff()
	}
	advance := func(ms int) {
		t.Helper()
		for elapsed := 0; elapsed < ms; elapsed += 10 {
			for _, e := range engines {
				if err := e.AdvanceCycles(30000); err != nil {
					t.Fatal(err)
				}
			}
			if !bytes.Equal(int16Bytes(c.RenderAudio()), int16Bytes(engines[1].RenderAudio())) {
				t.Fatal("opening PCM differs")
			}
		}
		if !bytes.Equal(observerGuestState(t, c), observerGuestState(t, engines[1])) {
			t.Fatal("opening full guest differs")
		}
		if !bytes.Equal(c.Frame().Pix, engines[1].Frame().Pix) {
			t.Fatal("opening source Frame differs")
		}
	}
	press := func(scan byte) {
		for _, e := range engines {
			if err := e.Key(scan, true); err != nil {
				t.Fatal(err)
			}
		}
		advance(100)
		for _, e := range engines {
			if err := e.Key(scan, false); err != nil {
				t.Fatal(err)
			}
		}
		advance(100)
	}
	advance(1000)
	press(2)
	press(2)
	for i := 0; i < 300 && engines[1].sourceIntroMaskCalls == 0; i++ {
		advance(100)
	}
	if engines[1].sourceIntroMaskCalls == 0 || c.sourceIntroMaskCalls != 0 {
		t.Fatal("ordinary opening six-plane Go work absent")
	}
	advance(1000)
	t.Logf("ordinary opening Go masked batches=%d at step%d", engines[1].sourceIntroMaskCalls, engines[1].Oracle.Steps())
}
