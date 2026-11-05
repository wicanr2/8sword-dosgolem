package ownedworld

import (
	"fmt"
	dg "github.com/wicanr2/dosgolem"
	"os"
	"strings"
	"testing"
)

// Original generator only, entered after terrain/player shadow setup.
func TestRustJourneyReference(t *testing.T) {
	out, pam := os.Getenv("EIGHTSWORD_RUST_JOURNEY_REFERENCE"), os.Getenv("EIGHTSWORD_RUST_WORLD_PAM")
	if out == "" || pam == "" {
		t.Skip("explicit original generator oracle")
	}
	raw, err := os.ReadFile(pam)
	if err != nil {
		t.Fatal(err)
	}
	code, err := worldArmyCode(raw)
	if err != nil {
		t.Fatal(err)
	}
	var b strings.Builder
	b.WriteString("# PAM original 0110:3542..36B4 generator; controlled rank/area/seed\n")
	for area := 0; area < 8; area++ {
		for rank := 1; rank <= 5; rank++ {
			for _, seed := range []uint32{0, 1, 2, 0x12345678, 0x5578f641, 0xffffffff, 0x80000000, 187430} {
				m := dg.New()
				copy(m.Mem[0x1100:], code)
				m.CPU.Seg[dg.CS] = 0x110
				m.CPU.Seg[dg.DS] = 0x1e88
				m.CPU.Seg[dg.SS] = 0x1e88
				m.CPU.R[dg.BP] = 0xee00
				m.CPU.R[dg.SP] = 0xedec
				m.CPU.IP = 0x3542
				m.Write16(0x1e880+0x4f2, uint16(rank))
				m.Write16(0x1e880+0x56d6, uint16(area))
				m.Write16(0x1e880+0x81bc, uint16(seed))
				m.Write16(0x1e880+0x81be, uint16(seed>>16))
				clear(m.Mem[0x1e880+0x5700 : 0x1e880+0x5718])
				done := false
				for n := 0; n < 10000; n++ {
					if m.CPU.Seg[dg.CS] == 0x110 && m.CPU.IP == 0x36b4 {
						done = true
						break
					}
					if err = m.Step(); err != nil {
						t.Fatal(err)
					}
				}
				if !done {
					t.Fatal("generator budget")
				}
				after := uint32(m.Read16(0x1e880+0x81bc)) | uint32(m.Read16(0x1e880+0x81be))<<16
				fmt.Fprintf(&b, "GEN\t%d\t%d\t%d\t%d", area, rank, seed, after)
				for i := 0; i < 6; i++ {
					fmt.Fprintf(&b, "\t%d\t%d", m.Read16(0x1e880+0x5700+uint32(i*4)), m.Read16(0x1e880+0x5702+uint32(i*4)))
				}
				b.WriteByte('\n')
			}
		}
	}
	f, err := os.OpenFile(out, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()
	if _, err = f.WriteString(b.String()); err != nil {
		t.Fatal(err)
	}
}
