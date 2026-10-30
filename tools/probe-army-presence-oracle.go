//go:build ignore

// Bounded original CPU experiments. No host implementation of either rule.
package main

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	dg "github.com/wicanr2/dosgolem"
)

func main() {
	input := flag.String("pam", "", "fixed PAM.AY")
	out := flag.String("out", "", "new JSON")
	flag.Parse()
	must := func(e error) {
		if e != nil {
			panic(e)
		}
	}
	raw, e := os.ReadFile(*input)
	must(e)
	const source = "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0"
	if fmt.Sprintf("%x", sha256.Sum256(raw)) != source {
		panic("PAM source")
	}
	u16 := func(at int) uint16 { return binary.LittleEndian.Uint16(raw[at:]) }
	code := append([]byte(nil), raw[int(u16(8))*16:]...)
	for i := 0; i < int(u16(6)); i++ {
		p := int(u16(24)) + i*4
		at := int(u16(p)) + int(u16(p+2))*16
		binary.LittleEndian.PutUint16(code[at:], binary.LittleEndian.Uint16(code[at:])+0x110)
	}
	newMachine := func(ip uint16) *dg.Machine {
		m := dg.New()
		copy(m.Mem[0x1100:], code)
		m.CPU.Seg[dg.CS] = 0x110
		m.CPU.Seg[dg.DS] = 0x1e88
		m.CPU.Seg[dg.SS] = 0x1e88
		m.CPU.R[dg.BP] = 0xff00
		m.CPU.R[dg.SP] = 0xfee0
		m.CPU.IP = ip
		return m
	}
	run := func(m *dg.Machine, end uint16) int {
		for i := 0; i < 128; i++ {
			if m.CPU.IP == end {
				return i
			}
			must(m.Step())
		}
		panic("bounded CPU slice")
	}
	presence := []map[string]any{}
	for _, slot := range []int{-1, 0, 5} {
		m := newMachine(0x1650)
		clear(m.Mem[0x1edca:0x1ede2])
		m.Write16(0x2e77e, 1)
		if slot >= 0 {
			m.Write16(0x1edca+uint32(slot*4), 25)
			m.Write16(0x1edcc+uint32(slot*4), 1)
		}
		steps := run(m, 0x1671)
		presence = append(presence, map[string]any{"slot": slot, "empty_flag": m.Read16(0x2e77e), "steps": steps})
	}
	losses := []map[string]any{}
	for _, gold := range []uint16{0, 1, 299, 30000} {
		for _, random := range []uint16{0, 1, 2729, 2730, 32767} {
			m := newMachine(0x1690)
			m.CPU.R[dg.AX] = random
			m.Write16(0x1ed78, gold)
			steps := run(m, 0x16a8)
			losses = append(losses, map[string]any{"gold_before": gold, "controlled_rand": random, "divisor": m.CPU.R[dg.CX], "loss": m.Read16(0x2e77a), "gold_after": m.Read16(0x1ed78), "steps": steps})
		}
	}
	d := map[string]any{"status": "original-cpu-slices-complete", "source_sha256": source, "runtime": "0110; DS/SS=1E88", "core": "fixed 923-source Go dosgolem", "method": "Original instructions at 1650..1671 and 1690..16A8; bounded direct entry and controlled post-RNG AX. Not normal player path or RNG parity.", "presence": presence, "losses": losses}
	b, e := json.MarshalIndent(d, "", "  ")
	must(e)
	f, e := os.OpenFile(filepath.Clean(*out), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	must(e)
	_, e = f.Write(append(b, '\n'))
	must(e)
	must(f.Close())
}
