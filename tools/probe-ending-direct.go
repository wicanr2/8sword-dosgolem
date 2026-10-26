//go:build ignore

// 053 DRAFT. Paired native call effects and native Go-copy benchmark.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"time"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func endingFixture(ram, raw []byte, entry, dest uint16, x, y int, poison byte) *dg.Machine {
	m := dg.New()
	m.SetVideoMode(0x0e)
	m.SetDOSBoxCycles(3000)
	m.VGAFrameEvery = 0
	copy(m.Mem, ram)
	m.Write16(0x7e40+0x177a, 1)
	m.Write16(0x7e40+0x1780, dest)
	copy(m.Mem[0x60000:], raw)
	m.CPU.R = [8]uint16{0x1234, 0x2345, 0x3456, 0x4567, 0xff00, 0x6789, 0x789a, 0x89ab}
	m.CPU.Seg = [4]uint16{0x7000, 0x393, 0x9000, 0x7e4}
	m.CPU.IP, m.CPU.Flags = entry, 0x202
	for i := 0; i < 32; i++ {
		m.Mem[0x9fee0+i] = poison + byte(i)
	}
	for i, v := range []uint16{0xfff0, 0x110, 0, 0x6000, uint16(x), uint16(y)} {
		m.Write16(0x9ff00+uint32(i*2), v)
	}
	for plane := 0; plane < 4; plane++ {
		for off := range m.EGAPlane(plane) {
			m.EGAPlane(plane)[off] = byte(off*7 + plane*31)
		}
	}
	m.Read8(0xa0000 + 77)
	return m
}

func endingMust(err error) {
	if err != nil {
		panic(err)
	}
}
func endingSHA(raw []byte) string { return fmt.Sprintf("%x", sha256.Sum256(raw)) }
func endingRead(p string) []byte  { b, e := os.ReadFile(p); endingMust(e); return b }

func main() {
	project := flag.String("project", "", "read-only project")
	out := flag.String("out", "", "new JSON receipt")
	flag.Parse()
	if os.Getuid() != 1000 {
		panic("UID1000 required")
	}
	endingMust(func() error { _, e := os.Stat("/.dockerenv"); return e }())
	b := filepath.Join(*project, "workplace/probe-20261023/graphics-first/ending-hd-r1")
	ram := endingRead(filepath.Join(b, "startup-r3/ram-00000-9ffff.bin"))
	if endingSHA(ram) != "0ccfd6a0d14ca315dc42ca8e70961e83c076f2c857509df70840402faf00ee60" {
		panic("RAM identity")
	}
	budget := oracle.HostWorkLimits{Steps: 1000000, Cycles: 1000000}
	var cases, rowCases, benchmarks []map[string]any
	for _, f := range []struct {
		File  string
		Entry uint16
	}{{"end1-ay-00.bin", 0x996}, {"end7-ay-00.bin", 0x996}, {"end5-ay-00.bin", 0x769}} {
		raw := endingRead(filepath.Join(b, f.File))
		w, h := int(raw[0])|int(raw[1])<<8, int(raw[2])|int(raw[3])<<8
		ret := uint16(0xa69)
		if f.Entry == 0x769 {
			ret = 0x84e
		}
		positions := [][2]int{{0, 0}}
		if w < 80 || h < 200 {
			positions = append(positions, [2]int{80 - w, 200 - h})
		}
		for _, pos := range positions {
			for _, dest := range []uint16{0xa000, 0xa400} {
				for _, poison := range []byte{0, 0xc7} {
					native := endingFixture(ram, raw, f.Entry, dest, pos[0], pos[1], poison)
					host := endingFixture(ram, raw, f.Entry, dest, pos[0], pos[1], poison)
					var nativeWrites, hostWrites []dg.VideoWrite
					native.ObserveVideoWrites(func(v dg.VideoWrite) { nativeWrites = append(nativeWrites, v) })
					host.ObserveVideoWrites(func(v dg.VideoWrite) { hostWrites = append(hostWrites, v) })
					for native.CPU.IP != ret && native.Steps < 20000 {
						endingMust(native.Step())
					}
					plan, reason := prepareEndingDirect(host, budget)
					if native.CPU.IP != ret || plan == nil {
						panic("native prefix / direct prepare " + reason)
					}
					endingMust(plan.commit(host, budget))
					if !bytes.Equal(native.Mem, host.Mem) || native.CPU.R != host.CPU.R || native.CPU.Seg != host.CPU.Seg || native.CPU.IP != host.CPU.IP || native.CPU.Flags != host.CPU.Flags || native.Steps != host.Steps || native.CPU.Cycles != host.CPU.Cycles {
						panic(fmt.Sprintf("ABI differs %s native=%d/%d host=%d/%d", f.File, native.Steps, native.CPU.Cycles, host.Steps, host.CPU.Cycles))
					}
					if len(nativeWrites) != len(hostWrites) {
						panic("write count")
					}
					for i, v := range nativeWrites {
						if v != hostWrites[i] {
							panic(fmt.Sprintf("write metadata differs %d native%+v host%+v", i, v, hostWrites[i]))
						}
					}
					for plane := 0; plane < 4; plane++ {
						if !bytes.Equal(native.EGAPlane(plane), host.EGAPlane(plane)) {
							panic("index planes")
						}
					}
					endingMust(native.Step())
					endingMust(host.Step())
					var na, ho bytes.Buffer
					endingMust(native.SaveState(&na))
					endingMust(host.SaveState(&ho))
					if !bytes.Equal(na.Bytes(), ho.Bytes()) {
						panic("complete machine state")
					}
					cases = append(cases, map[string]any{"source": f.File, "source_sha256": endingSHA(raw), "entry": f.Entry, "destination": dest, "position": pos, "poison": poison, "prefix_steps": plan.Steps, "prefix_cycles": plan.Cycles, "original_stores": len(nativeWrites), "complete_state_equal": true, "ordered_metadata_equal": true, "replacement_x86_pixel_instructions": 0})
				}
			}
		}
		row := uint16(0x9eb)
		if f.Entry == 0x769 {
			row = 0x7be
		}
		for _, dest := range []uint16{0xa000, 0xa400} {
			for _, plane := range []int{0, 3} {
				for _, rows := range []int{1, h} {
					fixture := func() *dg.Machine {
						m := endingFixture(ram, raw, f.Entry, dest, 0, 0, 0xc7)
						for i := 0; ; i++ {
							_, seq, _ := m.VGAState()
							if m.CPU.IP == row && seq[2] == 1<<uint(plane) {
								return m
							}
							if i > 20000 {
								panic("row entry not reached")
							}
							endingMust(m.Step())
						}
					}
					native, host := fixture(), fixture()
					var before, after bytes.Buffer
					endingMust(host.SaveState(&before))
					if rejected, _ := prepareEndingRow(host, oracle.HostWorkLimits{Steps: 7, Cycles: 1000000}); rejected != nil {
						panic("short quota accepted")
					}
					endingMust(host.SaveState(&after))
					if !bytes.Equal(before.Bytes(), after.Bytes()) {
						panic("rejected row changed state")
					}
					var nativeWrites, hostWrites []dg.VideoWrite
					native.ObserveVideoWrites(func(v dg.VideoWrite) { nativeWrites = append(nativeWrites, v) })
					host.ObserveVideoWrites(func(v dg.VideoWrite) { hostWrites = append(hostWrites, v) })
					for i := 0; i < rows*8; i++ {
						endingMust(native.Step())
					}
					limit := oracle.HostWorkLimits{Steps: uint64(rows * 8), Cycles: 1000000}
					plan, why := prepareEndingRow(host, limit)
					if plan == nil || plan.Rows != rows {
						panic("row prepare " + why)
					}
					endingMust(plan.commit(host, limit))
					var na, ho bytes.Buffer
					endingMust(native.SaveState(&na))
					endingMust(host.SaveState(&ho))
					if !bytes.Equal(na.Bytes(), ho.Bytes()) {
						panic(fmt.Sprintf("row machine state differs %s plane%d rows%d native=%d/%d host=%d/%d IP%x/%x flags%x/%x", f.File, plane, rows, native.Steps, native.CPU.Cycles, host.Steps, host.CPU.Cycles, native.CPU.IP, host.CPU.IP, native.CPU.Flags, host.CPU.Flags))
					}
					if len(nativeWrites) != len(hostWrites) {
						panic("row metadata length")
					}
					for i, v := range nativeWrites {
						if v != hostWrites[i] {
							panic(fmt.Sprintf("row metadata differs %d native%+v host%+v", i, v, hostWrites[i]))
						}
					}
					rowCases = append(rowCases, map[string]any{"source": f.File, "row_entry": row, "destination": dest, "plane": plane, "rows": rows, "complete_state_equal": true, "ordered_metadata_equal": true, "rejected_short_quota_without_effects": true, "replacement_x86_pixel_instructions": 0})
				}
			}
		}
		var ratios []float64
		for trial := 0; trial < 3; trial++ {
			var nt, ht time.Duration
			for i := 0; i < 16; i++ {
				native := endingFixture(ram, raw, f.Entry, 0xa400, 0, 0, 0xc7)
				host := endingFixture(ram, raw, f.Entry, 0xa400, 0, 0, 0xc7)
				nativeCall := func() {
					for native.CPU.IP != ret {
						endingMust(native.Step())
					}
				}
				hostCall := func() {
					plan, why := prepareEndingDirect(host, budget)
					if plan == nil {
						panic(why)
					}
					endingMust(plan.commit(host, budget))
				}
				if i%2 == 0 {
					t := time.Now()
					nativeCall()
					nt += time.Since(t)
					t = time.Now()
					hostCall()
					ht += time.Since(t)
				} else {
					t := time.Now()
					hostCall()
					ht += time.Since(t)
					t = time.Now()
					nativeCall()
					nt += time.Since(t)
				}
			}
			ratio := float64(nt) / float64(ht)
			ratios = append(ratios, ratio)
			benchmarks = append(benchmarks, map[string]any{"source": f.File, "trial": trial + 1, "calls": 16, "native_ns_per_call": nt.Nanoseconds() / 16, "go_ns_per_call": ht.Nanoseconds() / 16, "ratio": ratio})
		}
		sort.Float64s(ratios)
		fmt.Printf("%s median native/Go %.3fx\n", f.File, ratios[1])
	}
	report := map[string]any{"spec": "053", "production": false, "status": "research-native-go-planar-contract", "ram_sha256": endingSHA(ram), "cases": cases, "row_cases": rowCases, "benchmarks": benchmarks, "clock": "DOSBox-cost3000", "limits": []string{"Controlled single-call ABI and paired call cost only; no normal handoff, whole-game FPS or production promotion.", "Direct commit executes native Go bulk copy and compatibility effects; zero x86 opcode dispatches inside admitted pixel loops."}}
	raw, err := json.MarshalIndent(report, "", "  ")
	endingMust(err)
	file, err := os.OpenFile(*out, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
	endingMust(err)
	_, err = file.Write(append(raw, '\n'))
	endingMust(err)
	endingMust(file.Close())
	fmt.Printf("PAE direct contract: %d full-call / %d row cases\n", len(cases), len(rowCases))
}
