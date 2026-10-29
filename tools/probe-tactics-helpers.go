// 030 DRAFT: original helper controls for the approved tactics mode.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"runtime"

	"github.com/wicanr2/dosgolem/internal/cpu"
	"github.com/wicanr2/dosgolem/internal/dos"
	"github.com/wicanr2/dosgolem/internal/machine"
	"github.com/wicanr2/dosgolem/internal/state"
)

type helperCase struct {
	Name                                                              string
	Kind, SourceSlot, SourceCount, TargetSlot, TargetCount, AllyCount uint16
}

var helperCases = []helperCase{
	{"front-opposed", 3, 0, 50, 0, 31, 0}, {"rear-archer", 3, 3, 50, 0, 31, 0},
	{"open-lane", 3, 1, 50, 0, 31, 0}, {"other-ranged", 24, 0, 50, 0, 31, 0},
	{"combined", 3, 0, 50, 0, 31, 69}, {"other-kind", 6, 0, 50, 0, 31, 0},
	{"rear-target", 3, 0, 50, 3, 31, 69}, {"threshold", 3, 0, 4, 0, 2, 0},
}

func must(e error) {
	if e != nil {
		panic(e)
	}
}
func sha(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func write(p string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	must(e)
	must(os.WriteFile(p, append(b, '\n'), 0644))
}
func main() {
	root := flag.String("root", "", "read-only original")
	input := flag.String("state", "", "fixed original state")
	out := flag.String("out", "", "new output")
	flag.Parse()
	if _, e := os.Stat(*out); !os.IsNotExist(e) {
		panic("output exists")
	}
	must(os.Mkdir(*out, 0755))
	raw, e := os.ReadFile(*input)
	must(e)
	if sha(raw) != "88f21ef185d597fee43972aec1d14e9a6811ea072a443aa6be04fe6de999b5bf" {
		panic("snapshot SHA")
	}
	pam, e := os.ReadFile(filepath.Join(*root, "PAM.AY"))
	must(e)
	if sha(pam) != "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0" {
		panic("PAM SHA")
	}
	word := func(at int) uint16 { return binary.LittleEndian.Uint16(pam[at:]) }
	header := int(word(8)) * 16
	code := append([]byte(nil), pam[header:]...)
	for i := 0; i < int(word(6)); i++ {
		at := int(word(24)) + i*4
		loc := int(word(at+2))*16 + int(word(at))
		binary.LittleEndian.PutUint16(code[loc:], binary.LittleEndian.Uint16(code[loc:])+0x110)
	}
	rows := []map[string]any{}
	for _, side := range []string{"player", "enemy"} {
		for _, sc := range helperCases {
			for _, mode := range []string{"native", "formation", "tactics"} {
				dest := filepath.Join(*out, side+"-"+sc.Name+"-"+mode)
				must(os.Mkdir(dest, 0755))
				m := machine.New()
				d := dos.New(m, *root)
				d.Install()
				must(state.Load(*input, m, d))
				ds := uint16(0x1e88)
				get := func(off uint16) uint16 { return m.Read16(uint32(ds)*16 + uint32(off)) }
				put := func(off, v uint16) { m.Write16(uint32(ds)*16+uint32(off), v) }
				for i := uint16(0); i < 6; i++ {
					put(0x56e8+i*4, 0)
					put(0x56ea+i*4, 0)
					put(0x5700+i*4, 0)
					put(0x5702+i*4, 0)
					put(0x6fb6+i*2, i)
					put(0x6fc2+i*2, i)
				}
				target, slots, total, source, sourceSlots := uint16(0x56e8), uint16(0x6fb6), uint16(0x8ca4), uint16(0x5700), uint16(0x6fc2)
				entry, hook := uint16(0x1532), uint16(0x1560)
				if side == "enemy" {
					target, slots, total, source, sourceSlots = 0x5700, 0x6fc2, 0x8e60, 0x56e8, 0x6fb6
					entry, hook = 0x1592, 0x15ca
				}
				put(target, 1)
				put(target+2, sc.TargetCount)
				put(target+4, 21)
				put(target+6, sc.AllyCount)
				put(source, sc.Kind)
				put(source+2, sc.SourceCount)
				if sc.SourceSlot != 0 {
					put(sourceSlots, sc.SourceSlot)
					put(sourceSlots+sc.SourceSlot*2, 0)
				}
				if sc.TargetSlot != 0 {
					put(slots, sc.TargetSlot)
					put(slots+sc.TargetSlot*2, 0)
					if sc.AllyCount > 0 {
						put(slots, 1)
						put(slots+2, 3)
					}
				}
				put(0x26ac, 0)
				put(0x26b2, 0)
				put(0x26b8, 0)
				hp := get(0x70d0 + 4)
				put(total, hp*sc.TargetCount)
				m.CPU.Seg[cpu.CS] = 0xf67
				m.CPU.Seg[cpu.DS] = ds
				m.CPU.Seg[cpu.SS] = ds
				m.CPU.IP = entry
				m.CPU.R[cpu.SP] = 0xe000
				put(0xe000, 0xfff0)
				put(0xe002, 0xf67)
				put(0xe004, 0)
				put(0xe006, 0)
				at := 0xe57*16 + int(hook)
				if !bytes.Equal(m.Mem[0xf67*16+int(hook):0xf67*16+int(hook)+24], code[at:at+24]) {
					panic("hook bytes")
				}
				must(state.Save(filepath.Join(dest, "start-call.state"), m, d))
				start := m.Steps
				seen := false
				var before, after uint16
				pressure, formation := false, false
				for m.Steps < start+10000 {
					c := m.CPU
					if c.Seg[cpu.CS] == 0xf67 && c.IP == hook {
						if seen {
							panic("duplicate hook")
						}
						seen = true
						if get(c.R[cpu.BP]+6) != 0 || get(c.R[cpu.BP]+8) != 0 {
							panic("helper indices")
						}
						before = c.R[cpu.AX]
						must(state.Save(filepath.Join(dest, "before-hook.state"), m, d))
						if sc.Kind == 3 && sc.SourceSlot < 3 {
							opposed := get(slots + sc.SourceSlot*2)
							pressure = get(target+opposed*4+2) > 0
						}
						if sc.TargetSlot < 3 {
							for i := uint16(0); i < 3; i++ {
								id := get(slots + i*2)
								if i != sc.TargetSlot && get(target+id*4+2) > 0 {
									formation = true
								}
							}
						}
						if mode == "tactics" && pressure {
							c.R[cpu.AX] = uint16(uint32(c.R[cpu.AX]) * 75 / 100)
						}
						if mode != "native" && formation {
							c.R[cpu.AX] = uint16(uint32(c.R[cpu.AX]) * 80 / 100)
						}
						after = c.R[cpu.AX]
						must(state.Save(filepath.Join(dest, "after-hook.state"), m, d))
					}
					if seen && c.Seg[cpu.CS] == 0xf67 && c.IP == 0xfff0 {
						break
					}
					must(m.Step())
				}
				if !seen || m.CPU.IP != 0xfff0 || m.CPU.R[cpu.AX] != after/hp+1 || get(total) != hp*sc.TargetCount-after {
					panic("original helper result")
				}
				must(state.Save(filepath.Join(dest, "final.state"), m, d))
				b, e := os.ReadFile(filepath.Join(dest, "final.state"))
				must(e)
				result := map[string]any{"side": side, "case": sc, "mode": mode, "pressure": pressure, "formation": formation, "raw": before, "amount": after, "hp": hp, "encoded_return": m.CPU.R[cpu.AX], "remaining_total_hp": get(total), "steps": m.Steps - start, "final_sha256": sha(b), "go_version": runtime.Version()}
				write(filepath.Join(dest, "trace.json"), result)
				rows = append(rows, result)
				d.Close()
			}
		}
	}
	write(filepath.Join(*out, "summary.json"), map[string]any{"status": "controlled-tactics-helpers", "calls": len(rows), "rows": rows, "pam_sha256": sha(pam), "input_sha256": sha(raw)})
	fmt.Printf("tactics original helpers: %d\n", len(rows))
}
