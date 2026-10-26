package eightsword

import (
	"fmt"
	"os"
	"testing"

	dg "github.com/wicanr2/dosgolem"
)

func TestResearchSourceBitmapRowsOracle(t *testing.T) {
	project := os.Getenv("EIGHTSWORD_GLYPH_PROJECT")
	if project == "" {
		t.Skip("需唯讀專案")
	}
	for _, phase := range []string{"pam", "intro", "ending"} {
		layouts := pamBitmapRows(0x14d2)
		if phase == "intro" {
			layouts = introBitmapRows()
		}
		if phase == "ending" {
			layouts = endingBitmapRows()
		}
		for _, l := range layouts {
			for _, dest := range []uint16{0xa000, 0xa400} {
				for _, w := range []int{1, 80} {
					t.Run(fmt.Sprintf("%s/planes%d/%x/width%d", phase, l.Planes, dest, w), func(t *testing.T) {
						a, h := sourcePageFixture(t, project, phase, sourcePageLayout{Entry: l.Entry}, dest, 15), sourcePageFixture(t, project, phase, sourcePageLayout{Entry: l.Entry}, dest, 15)
						for _, m := range []*dg.Machine{a, h} {
							for row := 0; row < 200; row++ {
								m.Write16(uint32(m.CPU.Seg[dg.CS])*16+uint32(l.Table)+uint32(row*2), uint16(row*80))
							}
							m.Write16(0x60020, uint16(w))
							m.Write16(0x60022, 4)
							for i := 0; i < l.Planes*w*4; i++ {
								m.Mem[0x60024+i] = byte(i*31 + 17)
							}
							for i, v := range []uint16{0x20, 0x6000, 0, 196} {
								m.Write16(0x9ff04+uint32(i*2), v)
							}
						}
						calls := 0
						h.InstallHostInstruction(l.rep().Linear(), func(m *dg.Machine) (bool, error) {
							done, err := sourceBitmapRowInstruction(m, l)
							if done {
								calls++
							}
							return done, err
						})
						ret := l.Entry.Linear() + 211
						if l.Planes == 5 {
							ret = l.Entry.Linear() + 229
						}
						for uint32(a.CPU.Seg[dg.CS])*16+uint32(a.CPU.IP) != ret && a.Steps < 10000 {
							before := calls
							if err := a.Step(); err != nil {
								t.Fatal(err)
							}
							if err := h.Step(); err != nil {
								t.Fatal(err)
							}
							if calls != before {
								sourceGlyphState(t, a, h, nil, nil)
							}
						}
						if calls != 16 {
							t.Fatal("four-plane native rows missing", calls)
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
					})
				}
			}
		}
	}
}
