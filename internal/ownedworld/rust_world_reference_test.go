package ownedworld

import (
	"encoding/binary"
	"fmt"
	dg "github.com/wicanr2/dosgolem"
	"os"
	"strings"
	"testing"
)

// Controlled original routines, not a normal player-path claim.
func TestRustWorldReference(t *testing.T) {
	out := os.Getenv("EIGHTSWORD_RUST_WORLD_REFERENCE")
	source := os.Getenv("EIGHTSWORD_RUST_WORLD_PAM")
	if out == "" || source == "" {
		t.Skip("explicit world oracle inputs")
	}
	pam, err := os.ReadFile(source)
	if err != nil {
		t.Fatal(err)
	}
	code, err := worldArmyCode(pam)
	if err != nil {
		t.Fatal(err)
	}
	makeMachine := func() *dg.Machine {
		m := dg.New()
		copy(m.Mem[0x1100:], code)
		m.CPU.Seg[dg.CS] = 0x110
		m.CPU.Seg[dg.DS] = 0x1e88
		m.CPU.Seg[dg.SS] = 0x1e88
		m.CPU.R[dg.SP] = 0xee00
		m.CPU.R[dg.BP] = 0xed00
		m.Write16(0x1e880+0xee00, 0xfff0)
		m.Write16(0x1e880+0xee02, 0x110)
		return m
	}
	run := func(m *dg.Machine, stop uint16) {
		t.Helper()
		for n := 0; n < 10000; n++ {
			if m.CPU.Seg[dg.CS] == 0x110 && m.CPU.IP == stop {
				return
			}
			if er := m.Step(); er != nil {
				t.Fatal(er)
			}
		}
		t.Fatal("world oracle budget")
	}
	word := func(m *dg.Machine, off uint32) uint16 { return m.Read16(0x1e880 + off) }
	var b strings.Builder
	b.WriteString("# Original PAM routines; controlled fields, not normal world GUI\n")
	for _, key := range []uint16{0x4700, 0x4800, 0x4900, 0x4b00, 0x4d00, 0x4f00, 0x5000, 0x5100, 0x3920, 0x1c0d} {
		for _, p := range [][2]uint16{{0, 0}, {69, 79}, {40, 40}, {0, 79}, {69, 0}} {
			m := makeMachine()
			m.Write16(0x1e880+0x8cba, key)
			m.Write16(0x1e880+0x8e12, p[0])
			m.Write16(0x1e880+0x8e44, p[1])
			m.Write16(0x1e880+0x56c4, 3)
			m.Write16(0x1e880+0x56cc, 0)
			m.CPU.IP = 0xc32
			run(m, 0xfff0)
			x, y, face := word(m, 0x8e12), word(m, 0x8e44), word(m, 0x56c4)
			fmt.Fprintf(&b, "MOVE\t%d\t%d\t%d\t%d\t%d\t%d\n", key, p[0], p[1], x, y, face)
			m.CPU.R[dg.SP] = 0xee00
			m.CPU.IP = 0xd72
			run(m, 0xfff0)
			fmt.Fprintf(&b, "ROLLBACK\t%d\t%d\t%d\t%d\t%d\t%d\n", key, x, y, word(m, 0x8e12), word(m, 0x8e44), word(m, 0x56c4))
		}
	}
	for tile := uint16(1); tile <= 65; tile++ {
		for boat := uint16(0); boat < 3; boat++ {
			for mask := uint16(0); mask < 4; mask++ {
				m := makeMachine()
				m.CPU.IP = 0x246b
				m.CPU.R[dg.BP] = 0xee00
				m.CPU.R[dg.SP] = 0xedec
				m.CPU.R[dg.AX] = tile
				m.Write16(0x1e880+0xedf0, tile)
				m.Write16(0x1e880+0xedfe, 0)
				m.Write16(0x1e880+0x56ce, boat)
				m.Write16(0x1e880+0x26b6, mask&1)
				m.Write16(0x1e880+0x26b4, (mask>>1)&1)
				m.Write16(0x1e880+0x8cba, 0x4d00)
				m.Write16(0x1e880+0x8e12, 41)
				m.Write16(0x1e880+0x8e44, 40)
				run(m, 0x24de)
				fmt.Fprintf(&b, "GUARD\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n", tile, boat, mask, word(m, 0x56ce), word(m, 0xedfe), word(m, 0x8e12), word(m, 0x8e44))
			}
		}
	}
	if binary.LittleEndian.Uint16(pam[:2]) != 0x5a4d {
		t.Fatal("MZ")
	}
	f, err := os.OpenFile(out, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = f.WriteString(b.String()); err != nil {
		t.Fatal(err)
	}
	if err = f.Close(); err != nil {
		t.Fatal(err)
	}
}
