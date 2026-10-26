//go:build ignore

// 053 DRAFT. Native glyph call oracle for Go row batches.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func glyphMust(e error) {
	if e != nil {
		panic(e)
	}
}
func glyphRead(p string) []byte { b, e := os.ReadFile(p); glyphMust(e); return b }
func glyphSHA(b []byte) string  { return fmt.Sprintf("%x", sha256.Sum256(b)) }

type glyphFixtureCase struct {
	CJK  bool
	Code uint16
	Name string
}

func glyphFixture(ram []byte, c glyphFixtureCase, dest uint16, fg, bg byte) *dg.Machine {
	m := dg.New()
	m.SetVideoMode(0x0e)
	m.SetDOSBoxCycles(3000)
	m.VGAFrameEvery = 0
	copy(m.Mem, ram)
	m.Write16(0x7e40+0x177a, 1)
	m.Write16(0x7e40+0x1780, dest)
	m.Mem[0x7e40+0x1782] = fg
	m.Mem[0x7e40+0x1783] = bg
	m.CPU.R = [8]uint16{0x1234, 0x2345, 0x3456, 0x4567, 0xff00, 0x6789, 0x789a, 0x89ab}
	m.CPU.Seg = [4]uint16{0x7000, 0x393, 0x9000, 0x7e4}
	m.CPU.IP = 0xb80
	m.CPU.Flags = 0x202
	x, y := uint16(0), uint16(0)
	w := uint16(1)
	if c.CJK {
		m.CPU.Seg[dg.CS] = 0x28e
		m.CPU.IP = 0xef0
		w = 2
	}
	if dest == 0xa400 {
		x, y = 80-w, 185
	}
	for i := 0; i < 32; i++ {
		m.Mem[0x9fee0+i] = 0xc7 + byte(i)
	}
	for i, v := range []uint16{0xfff0, 0x110, c.Code, x, y} {
		m.Write16(0x9ff00+uint32(i*2), v)
	}
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

type glyphEvent struct {
	Kind  string
	Read  dg.VideoRead
	Write dg.VideoWrite
}

func glyphWatch(m *dg.Machine, out *[]glyphEvent) {
	m.ObserveVideoReads(func(v dg.VideoRead) { *out = append(*out, glyphEvent{Kind: "read", Read: v}) })
	m.ObserveVideoWrites(func(v dg.VideoWrite) { *out = append(*out, glyphEvent{Kind: "write", Write: v}) })
}
func glyphState(a, b *dg.Machine, ae, be []glyphEvent) {
	var x, y bytes.Buffer
	glyphMust(a.SaveState(&x))
	glyphMust(b.SaveState(&y))
	if !bytes.Equal(x.Bytes(), y.Bytes()) {
		panic(fmt.Sprintf("glyph state differs steps%d/%d cycles%d/%d IP%x/%x flags%x/%x regs%v/%v", a.Steps, b.Steps, a.CPU.Cycles, b.CPU.Cycles, a.CPU.IP, b.CPU.IP, a.CPU.Flags, b.CPU.Flags, a.CPU.R, b.CPU.R))
	}
	if len(ae) != len(be) {
		panic(fmt.Sprintf("glyph trace length%d/%d", len(ae), len(be)))
	}
	for i, e := range ae {
		if e != be[i] {
			panic(fmt.Sprintf("glyph event%d native%+v Go%+v", i, e, be[i]))
		}
	}
}
func main() {
	project := flag.String("project", "", "read-only project")
	out := flag.String("out", "", "new JSON")
	flag.Parse()
	if os.Getuid() != 1000 {
		panic("UID1000 required")
	}
	_, e := os.Stat("/.dockerenv")
	glyphMust(e)
	b := filepath.Join(*project, "workplace/probe-20261023/graphics-first/ending-hd-r1")
	ram := glyphRead(filepath.Join(b, "startup-r3/ram-00000-9ffff.bin"))
	if glyphSHA(ram) != "0ccfd6a0d14ca315dc42ca8e70961e83c076f2c857509df70840402faf00ee60" {
		panic("RAM identity")
	}
	var cases []map[string]any
	for _, c := range []glyphFixtureCase{{true, 0, "CJK-index0"}, {true, 90, "CJK-comma"}, {false, 32, "ASCII-space"}, {false, 65, "ASCII-A"}} {
		for _, dest := range []uint16{0xa000, 0xa400} {
			for variant, colors := range [][2]byte{{14, 255}, {0, 0}, {15, 4}} {
				a, host := glyphFixture(ram, c, dest, colors[0], colors[1]), glyphFixture(ram, c, dest, colors[0], colors[1])
				row, ret := uint16(0xc16), uint16(0xc7f)
				if c.CJK {
					row, ret = 0xf7f, 0x104f
				}
				var ae, he []glyphEvent
				glyphWatch(a, &ae)
				glyphWatch(host, &he)
				batches, rows, steps := 0, 0, uint64(0)
				for a.CPU.IP != ret && a.Steps < 10000 {
					if a.CPU.IP == row {
						var before, after bytes.Buffer
						glyphMust(host.SaveState(&before))
						if rejected, _ := prepareEndingGlyph(host, oracle.HostWorkLimits{Steps: 1, Cycles: 1}); rejected != nil {
							panic("short glyph quota accepted")
						}
						glyphMust(host.SaveState(&after))
						if !bytes.Equal(before.Bytes(), after.Bytes()) {
							panic("glyph quota rejection changed state")
						}
						quota := uint64(100000)
						if variant != 0 {
							per := uint64(39)
							if c.CJK {
								per = 85
							}
							quota = per * uint64(variant)
						}
						limit := oracle.HostWorkLimits{Steps: quota, Cycles: 100000}
						p, why := prepareEndingGlyph(host, limit)
						if p == nil {
							panic("glyph prepare " + why)
						}
						stop := a.Steps + p.Steps
						for a.Steps < stop {
							glyphMust(a.Step())
						}
						glyphMust(p.commit(host, limit))
						glyphState(a, host, ae, he)
						batches++
						rows += p.Rows
						steps += p.Steps
						continue
					}
					glyphMust(a.Step())
					glyphMust(host.Step())
				}
				if a.CPU.IP != ret || rows != 15 || batches == 0 {
					panic("glyph call return missing")
				}
				glyphMust(a.Step())
				glyphMust(host.Step())
				glyphState(a, host, ae, he)
				cases = append(cases, map[string]any{"source": c.Name, "cjk": c.CJK, "code": c.Code, "destination": dest, "fg": colors[0], "bg": colors[1], "batches": batches, "rows": rows, "skipped_x86": steps, "full_machine_equal": true, "ordered_events_equal": true, "short_quota_rejected": true, "events": len(ae), "replacement_x86_pixel_instructions": 0})
			}
		}
		fmt.Println("glyph passed", c.Name)
	}
	result := map[string]any{"schema": 1, "spec": "053", "production": false, "status": "research-native-Go-glyph-rows", "source_ram_sha256": glyphSHA(ram), "cases": cases, "limits": []string{"Controlled glyph calls only, not normal PAM handoff or natural completion.", "Mode1 foreground and transparent/opaque backgrounds; Go row batches preserve native complete state and ordered VGA reads/writes.", "No production, GUI, visual art approval or overall FPS claim."}}
	encoded, err := json.MarshalIndent(result, "", "  ")
	glyphMust(err)
	f, err := os.OpenFile(*out, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
	glyphMust(err)
	_, err = f.Write(append(encoded, '\n'))
	glyphMust(err)
	glyphMust(f.Close())
	fmt.Printf("Go glyph %d controlled call cases\n", len(cases))
}
