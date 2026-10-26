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

func TestResearchSourceRevealTileOracle(t *testing.T) {
	project := os.Getenv("EIGHTSWORD_GLYPH_PROJECT")
	if project == "" {
		t.Skip("需唯讀專案")
	}
	raw, err := os.ReadFile(filepath.Join(project, "workplace/probe-20261023/graphics-first/intro-r1/cold-trace/decoded-06-TIT6V.AY.bin"))
	if err != nil {
		t.Fatal(err)
	}
	if hash(raw) != preludeSourceSHA {
		t.Fatal("original decoded source identity")
	}
	for _, count := range []uint16{1600, 1599, 801, 1} {
		for _, flags := range []uint16{0x202, 0x603} {
			t.Run(fmt.Sprintf("tile%d/flags%x", count, flags), func(t *testing.T) {
				makeMachine := func() *dg.Machine {
					m := sourcePageFixture(t, project, "intro", sourcePageLayout{Entry: oracle.Far(0, 0xa400)}, 0xa000, 15)
					m.SetVideoMode(0x13)
					m.VGAFrameEvery = 0
					m.CPU.Cycles = 0
					copy(m.Mem[0x60000:], raw)
					m.Write16(0xa49f, 0x6000)
					m.Write16(0xa4a1, 768)
					m.CPU.Seg[dg.CS] = 0xa3d
					m.CPU.IP = 0x30
					m.CPU.R[dg.CX] = count
					m.CPU.R[dg.BP] = m.CPU.R[dg.SP] + 16
					m.CPU.Flags = flags
					return m
				}
				a, h := makeMachine(), makeMachine()
				var events []dg.VideoWrite
				a.ObserveVideoWrites(func(w dg.VideoWrite) { events = append(events, w) })
				var before, after bytes.Buffer
				h.SaveState(&before)
				if p, _ := prepareSourceRevealTile(h, oracle.HostWorkLimits{Steps: 1, Cycles: 1}); p != nil {
					t.Fatal("short tile quota accepted")
				}
				h.SaveState(&after)
				if !bytes.Equal(before.Bytes(), after.Bytes()) {
					t.Fatal("rejection mutated guest")
				}
				b := oracle.HostWorkLimits{Steps: 100000, Cycles: 100000}
				p, why := prepareSourceRevealTile(h, b)
				if p == nil {
					t.Fatal(why)
				}
				for a.Steps < p.Steps {
					if err := a.Step(); err != nil {
						t.Fatal(err)
					}
				}
				if err := p.commit(h, b); err != nil {
					t.Fatal(err)
				}
				sourceGlyphState(t, a, h, nil, nil)
				if len(events) != 40 {
					t.Fatal("native reveal write count", len(events))
				}
				for i, pixel := range p.Pixels {
					if events[i].Offset != uint32(pixel.At) || events[i].Value != pixel.Color {
						t.Fatalf("ordered source point %d differs", i)
					}
				}
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

func TestResearchSourceRevealNormal(t *testing.T) {
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
	var nativeWrites [2]uint64
	for i, e := range engines {
		i := i
		t.Cleanup(e.ObservePresentation(PresentationObserver{Write: func(w PresentationWrite) {
			if uint32(w.CS)*16+uint32(w.IP) == 0xa486 {
				nativeWrites[i]++
			}
		}}))
	}
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
				t.Fatal("reveal PCM differs")
			}
		}
		if !bytes.Equal(observerGuestState(t, c), observerGuestState(t, engines[1])) {
			t.Fatal("reveal full guest differs")
		}
		if !bytes.Equal(c.Frame().Pix, engines[1].Frame().Pix) {
			t.Fatal("reveal source Frame differs")
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
	complete := false
	for i := 0; i < 1200; i++ {
		advance(100)
		if engines[1].sourceMetadata.PreludeInfo["written"] == 64000 {
			complete = true
			break
		}
	}
	if !complete || engines[1].sourceRevealTiles == 0 || c.sourceRevealTiles != 0 || engines[1].sourceRevealPixels != 64000 || nativeWrites[0] != 64000 || nativeWrites[1] != 0 {
		t.Fatal("ordinary Go reveal incomplete", nativeWrites, engines[1].sourceRevealPixels)
	}
	t.Logf("ordinary complete reveal Go tiles=%d point batches=%d atomic stores=%d pixels=%d native writes=%v at step%d", engines[1].sourceRevealTiles, engines[1].sourceRevealPoints, engines[1].sourceRevealAtomic, engines[1].sourceRevealPixels, nativeWrites, engines[1].Oracle.Steps())
}

func TestResearchSourceRevealPointOracle(t *testing.T) {
	project := os.Getenv("EIGHTSWORD_GLYPH_PROJECT")
	if project == "" {
		t.Skip("需唯讀專案")
	}
	raw, err := os.ReadFile(filepath.Join(project, "workplace/probe-20261023/graphics-first/intro-r1/cold-trace/decoded-06-TIT6V.AY.bin"))
	if err != nil {
		t.Fatal(err)
	}
	for _, pos := range [][2]uint16{{0, 0}, {319, 199}, {123, 87}} {
		for _, atomic := range []bool{false, true} {
			t.Run(fmt.Sprintf("%v/atomic%t", pos, atomic), func(t *testing.T) {
				makeMachine := func() *dg.Machine {
					m := sourcePageFixture(t, project, "intro", sourcePageLayout{Entry: oracle.Far(0, 0xa451)}, 0xa000, 15)
					m.SetVideoMode(0x13)
					m.VGAFrameEvery = 0
					m.CPU.Cycles = 0
					copy(m.Mem[0x60000:], raw)
					m.Write16(0xa49f, 0x6000)
					m.Write16(0xa4a1, 768)
					m.CPU.Seg[dg.CS] = 0xa3d
					m.CPU.IP = 0x81
					for i, v := range []uint16{0x5f, 0xa3d, pos[0], pos[1], pos[0], pos[1]} {
						m.Write16(0x9ff00+uint32(i*2), v)
					}
					return m
				}
				a, h := makeMachine(), makeMachine()
				if atomic {
					calls := 0
					h.InstallHostInstruction(0xa486, func(m *dg.Machine) (bool, error) {
						_, done := sourceRevealPixelInstruction(m)
						if done {
							calls++
						}
						return done, nil
					})
					for a.CPU.IP != 0xce && a.Steps < 100 {
						if err := a.Step(); err != nil {
							t.Fatal(err)
						}
						if err := h.Step(); err != nil {
							t.Fatal(err)
						}
						sourceGlyphState(t, a, h, nil, nil)
					}
					if calls != 1 {
						t.Fatal("atomic Go store missing", calls)
					}
				} else {
					var before, after bytes.Buffer
					h.SaveState(&before)
					if p, _ := prepareSourceRevealPoint(h, oracle.HostWorkLimits{Steps: 39, Cycles: 39}); p != nil {
						t.Fatal("point short budget accepted")
					}
					h.SaveState(&after)
					if !bytes.Equal(before.Bytes(), after.Bytes()) {
						t.Fatal("point rejection mutates guest")
					}
					b := oracle.HostWorkLimits{Steps: 1000, Cycles: 1000}
					p, why := prepareSourceRevealPoint(h, b)
					if p == nil {
						t.Fatal(why)
					}
					for a.Steps < 40 {
						if err := a.Step(); err != nil {
							t.Fatal(err)
						}
					}
					if err := p.commit(h, b); err != nil {
						t.Fatal(err)
					}
					sourceGlyphState(t, a, h, nil, nil)
				}
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
