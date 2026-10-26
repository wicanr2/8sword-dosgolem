//go:build ignore

// 053 DRAFT. Independent native PAE calls versus Go masked blits.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"time"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func maskMust(err error) {
	if err != nil {
		panic(err)
	}
}
func maskRead(p string) []byte { b, e := os.ReadFile(p); maskMust(e); return b }
func maskSHA(b []byte) string  { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func maskFixture(ram, raw []byte, dest uint16, poison byte) *dg.Machine {
	m := dg.New()
	m.SetVideoMode(0x0e)
	m.SetDOSBoxCycles(3000)
	m.VGAFrameEvery = 0
	copy(m.Mem, ram)
	copy(m.Mem[0x60000:], raw)
	w, h := int(raw[0])|int(raw[1])<<8, int(raw[2])|int(raw[3])<<8
	x, y := 0, 0
	if dest == 0xa400 {
		x, y = 80-w, 200-h
	}
	m.Write16(0x7e40+0x177a, 1)
	m.Write16(0x7e40+0x1780, dest)
	m.CPU.R = [8]uint16{0x1234, 0x2345, 0x3456, 0x4567, 0xff00, 0x6789, 0x789a, 0x89ab}
	m.CPU.Seg = [4]uint16{0x7000, 0x393, 0x9000, 0x7e4}
	m.CPU.IP = 0x4ec
	m.CPU.Flags = 0x202
	for i := 0; i < 40; i++ {
		m.Mem[0x9fed8+i] = poison + byte(i)
	}
	for i, v := range []uint16{0xfff0, 0x110, 0, 0x6000, uint16(x), uint16(y)} {
		m.Write16(0x9ff00+uint32(i*2), v)
	}
	for plane := 0; plane < 4; plane++ {
		for off := range m.EGAPlane(plane) {
			m.EGAPlane(plane)[off] = byte(off*7 + plane*31)
		}
	}
	if poison != 0 {
		m.Out8(0x3ce, 4)
		m.Out8(0x3cf, 2)
	}
	m.Read8(0xa0000 + 77)
	return m
}

type maskEvent struct {
	Kind  string
	Read  dg.VideoRead
	Write dg.VideoWrite
}

func maskObserve(m *dg.Machine, out *[]maskEvent) {
	m.ObserveVideoReads(func(v dg.VideoRead) { *out = append(*out, maskEvent{Kind: "read", Read: v}) })
	m.ObserveVideoWrites(func(v dg.VideoWrite) { *out = append(*out, maskEvent{Kind: "write", Write: v}) })
}
func maskEqual(a, b *dg.Machine, ae, be []maskEvent) {
	var x, y bytes.Buffer
	maskMust(a.SaveState(&x))
	maskMust(b.SaveState(&y))
	if !bytes.Equal(x.Bytes(), y.Bytes()) {
		panic(fmt.Sprintf("mask state differs steps%d/%d cycles%d/%d IP%x/%x flags%x/%x regs%v/%v", a.Steps, b.Steps, a.CPU.Cycles, b.CPU.Cycles, a.CPU.IP, b.CPU.IP, a.CPU.Flags, b.CPU.Flags, a.CPU.R, b.CPU.R))
	}
	if len(ae) != len(be) {
		panic("mask event count differs")
	}
	for i, event := range ae {
		if event != be[i] {
			panic(fmt.Sprintf("mask event%d differs %+v/%+v", i, event, be[i]))
		}
	}
}
func main() {
	project := flag.String("project", "", "read-only project")
	out := flag.String("out", "", "new JSON receipt")
	flag.Parse()
	if os.Getuid() != 1000 {
		panic("UID1000 required")
	}
	_, e := os.Stat("/.dockerenv")
	maskMust(e)
	b := filepath.Join(*project, "workplace/probe-20261023/graphics-first/ending-hd-r1")
	ram := maskRead(filepath.Join(b, "startup-r3/ram-00000-9ffff.bin"))
	if maskSHA(ram) != "0ccfd6a0d14ca315dc42ca8e70961e83c076f2c857509df70840402faf00ee60" {
		panic("RAM identity")
	}
	budget := oracle.HostWorkLimits{Steps: 1000000, Cycles: 1000000}
	var whole, rows, bench []map[string]any
	for _, file := range []string{"end2-ay-00.bin", "end3-ay-01.bin", "end6-ay-01.bin"} {
		raw := maskRead(filepath.Join(b, file))
		w := int(raw[0]) | int(raw[1])<<8
		for _, dest := range []uint16{0xa000, 0xa400} {
			for _, poison := range []byte{0, 0xc7} {
				a, c := maskFixture(ram, raw, dest, poison), maskFixture(ram, raw, dest, poison)
				var ae, ce []maskEvent
				maskObserve(a, &ae)
				maskObserve(c, &ce)
				for a.CPU.IP != 0x61f && a.Steps < 250000 {
					maskMust(a.Step())
				}
				if a.CPU.IP != 0x61f {
					panic("original masked return missing")
				}
				plan, why := prepareEndingMask(c, budget)
				if plan == nil {
					panic(why)
				}
				maskMust(plan.commit(c, budget))
				maskEqual(a, c, ae, ce)
				maskMust(a.Step())
				maskMust(c.Step())
				maskEqual(a, c, ae, ce)
				whole = append(whole, map[string]any{"source": file, "source_sha256": maskSHA(raw), "destination": dest, "poison": poison, "prefix_steps": plan.Steps, "prefix_cycles": plan.Cycles, "events": len(ae), "full_state_equal": true, "ordered_events_equal": true, "replacement_x86_pixel_instructions": 0})
			}
			for _, plane := range []int{0, 3} {
				fixture := func() *dg.Machine {
					m := maskFixture(ram, raw, dest, 0xc7)
					for i := 0; ; i++ {
						_, seq, _ := m.VGAState()
						if m.CPU.IP == 0x569 && seq[2] == 1<<uint(plane) {
							break
						}
						if i > 250000 {
							panic("masked byte loop not reached")
						}
						maskMust(m.Step())
					}
					if plane == 3 {
						for i := 0; i < (w/2)*9; i++ {
							maskMust(m.Step())
						}
					}
					return m
				}
				a, c := fixture(), fixture()
				var before, after bytes.Buffer
				maskMust(c.SaveState(&before))
				if rejected, _ := prepareEndingMaskRun(c, oracle.HostWorkLimits{Steps: 8, Cycles: 1000000}); rejected != nil {
					panic("tiny quota accepted")
				}
				maskMust(c.SaveState(&after))
				if !bytes.Equal(before.Bytes(), after.Bytes()) {
					panic("rejected batch changed guest")
				}
				n := int(c.CPU.R[dg.CX])
				if plane == 3 {
					n = 1
				}
				var ae, ce []maskEvent
				maskObserve(a, &ae)
				maskObserve(c, &ce)
				for i := 0; i < n*9; i++ {
					maskMust(a.Step())
				}
				limit := oracle.HostWorkLimits{Steps: uint64(n * 9), Cycles: uint64(n * 10)}
				plan, why := prepareEndingMaskRun(c, limit)
				if plan == nil || plan.Count != n {
					panic("masked run prepare " + why)
				}
				maskMust(plan.commit(c, limit))
				maskEqual(a, c, ae, ce)
				rows = append(rows, map[string]any{"source": file, "destination": dest, "plane": plane, "column": w - int(plan.registers[dg.CX]), "bytes": n, "partial_row": c.CPU.R[dg.CX] > 0, "full_state_equal": true, "ordered_events_equal": true, "tiny_quota_rejected_without_effects": true, "replacement_x86_pixel_instructions": 0})
			}
		}
		for trial := 0; trial < 3; trial++ {
			var nativeTime, hostTime time.Duration
			for i := 0; i < 8; i++ {
				a, c := maskFixture(ram, raw, 0xa400, 0xc7), maskFixture(ram, raw, 0xa400, 0xc7)
				native := func() {
					for a.CPU.IP != 0x61f {
						maskMust(a.Step())
					}
				}
				host := func() {
					p, why := prepareEndingMask(c, budget)
					if p == nil {
						panic(why)
					}
					maskMust(p.commit(c, budget))
				}
				if i%2 == 0 {
					t := time.Now()
					native()
					nativeTime += time.Since(t)
					t = time.Now()
					host()
					hostTime += time.Since(t)
				} else {
					t := time.Now()
					host()
					hostTime += time.Since(t)
					t = time.Now()
					native()
					nativeTime += time.Since(t)
				}
			}
			bench = append(bench, map[string]any{"source": file, "trial": trial + 1, "calls": 8, "native_ns_per_call": nativeTime.Nanoseconds() / 8, "go_ns_per_call": hostTime.Nanoseconds() / 8, "ratio": float64(nativeTime) / float64(hostTime)})
		}
		fmt.Println("masked source passed", file)
	}
	result := map[string]any{"spec": "053", "production": false, "status": "research-native-Go-masked-contract", "source_ram_sha256": maskSHA(ram), "full_cases": whole, "run_cases": rows, "benchmarks": bench, "limits": []string{"Controlled native ABI and ordered-read/write comparisons, not normal handoff or natural completion.", "Native Go mask blending and readback; no x86 instructions execute within admitted masked batches.", "Benchmark covers calls only, not overall FPS."}}
	encoded, err := json.MarshalIndent(result, "", "  ")
	maskMust(err)
	f, err := os.OpenFile(*out, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
	maskMust(err)
	_, err = f.Write(append(encoded, '\n'))
	maskMust(err)
	maskMust(f.Close())
	fmt.Printf("masked Go %d full / %d batch cases\n", len(whole), len(rows))
}
