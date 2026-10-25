//go:build ignore

// 047 DRAFT. Build alongside a frozen probe-direct-planar.go whose main is renamed.
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	dg "github.com/wicanr2/dosgolem"
)

type shadowByte struct {
	command *directCommand
	local   int
}
type lazyBacking struct {
	m                                    *dg.Machine
	pending                              [65536]shadowByte
	remaining, materialized              int
	reads, writes, readFills, writeFills int
}

func (s *lazyBacking) put(c *directCommand) {
	base := int(c.Destination-0xa000) * 16
	for row := 0; row < c.Height; row++ {
		for col := 0; col < c.WidthBytes; col++ {
			off := base + (c.Y+row)*80 + c.XByte + col
			if s.pending[off].command == nil {
				s.remaining++
			}
			s.pending[off] = shadowByte{c, row*c.WidthBytes + col}
		}
	}
}
func (s *lazyBacking) ensure(off uint32) bool {
	ref := s.pending[off]
	if ref.command == nil {
		return false
	}
	c := ref.command
	for plane := 0; plane < 4; plane++ {
		s.m.EGAPlane(plane)[off] = c.Raw[4+plane*c.WidthBytes*c.Height+ref.local]
	}
	s.pending[off] = shadowByte{}
	s.remaining--
	s.materialized++
	return true
}
func (s *lazyBacking) bind() {
	s.m.PreparePlanarAccess(func(offset uint32) {
		if s.ensure(offset) {
			s.readFills++
		}
	}, func(offset uint32) {
		if s.ensure(offset) {
			s.writeFills++
		}
	})
	s.m.ObserveVideoReads(func(v dg.VideoRead) {
		require(s.pending[v.Offset].command == nil, "read observer ran before backing preparation")
		s.reads++
	})
	s.m.ObserveVideoWrites(func(v dg.VideoWrite) {
		require(s.pending[v.Offset].command == nil, "write observer ran before backing preparation")
		s.writes++
	})
}
func planes(m *dg.Machine) [4]string {
	var result [4]string
	for p := range result {
		result[p] = digest(m.EGAPlane(p))
	}
	return result
}
func require(ok bool, message string) {
	if !ok {
		panic(message)
	}
}
func executeReturn(m *dg.Machine) {
	start := m.Steps
	for m.CPU.IP != 0xfff0 && m.Steps-start < 2000000 {
		must(m.Step())
	}
	require(m.CPU.IP == 0xfff0 && m.CPU.Seg[dg.CS] == 0x110, "native call failed to return")
}
func setupCopy(m *dg.Machine, entry uint16) {
	m.CPU.R = [8]uint16{0x1234, 0x2345, 0x3456, 0x4567, 0xfd00, 0x6789, 0x789a, 0x89ab}
	m.CPU.Seg = [4]uint16{0x7000, 0x14d2, 0x9000, 0x1e88}
	m.CPU.IP, m.CPU.Flags = entry, 2
	m.Write16(0x9fd00, 0xfff0)
	m.Write16(0x9fd02, 0x110)
}
func main() {
	root := flag.String("root", "", "read-only game root")
	fixtures := flag.String("fixtures", "", "source fixtures")
	out := flag.String("out", "", "new receipt")
	accountClock := flag.Bool("account-clock", false, "account verified call steps/cycles within both event budgets; private event-budget core required")
	flag.Parse()
	require(os.Getuid() == 1000, "UID 1000 required")
	_, err := os.Stat("/.dockerenv")
	must(err)
	pam, err := os.ReadFile(filepath.Join(*root, "PAM.AY"))
	must(err)
	require(digest(pam) == "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0", "PAM differs")
	raw, err := os.ReadFile(filepath.Join(*fixtures, "fixtures.json"))
	must(err)
	var manifest struct{ Fixtures []directSource }
	must(json.Unmarshal(raw, &manifest))
	var cases []map[string]any
	for _, source := range manifest.Fixtures {
		raw, err := os.ReadFile(filepath.Join(*fixtures, source.File))
		must(err)
		require(digest(raw) == source.SHA256, "fixture differs")
		w, h := int(word(raw, 0)), int(word(raw, 2))
		positions := [][2]int{{0, 0}}
		if w != 80 || h != 200 {
			positions = append(positions, [2]int{80 - w, 200 - h})
		}
		for _, pos := range positions {
			for _, dest := range []uint16{0xa000, 0xa400} {
				for _, cost := range []bool{false, true} {
					native := machine(pam, raw, pos[0], pos[1], dest, 2)
					direct := machine(pam, raw, pos[0], pos[1], dest, 2)
					native.CPU.DOSBoxCost = cost
					direct.CPU.DOSBoxCost = cost
					if *accountClock && cost {
						native.SetDOSBoxCycles(3000)
						direct.SetDOSBoxCycles(3000)
					}
					nativeReads := 0
					native.ObserveVideoReads(func(dg.VideoRead) { nativeReads++ })
					before := planes(direct)
					executeReturn(native)
					drawSteps, drawCycles := native.Steps, native.CPU.Cycles
					require(nativeReads == 0, "opaque routine unexpectedly reads VGA")
					command := replace(direct)
					backing := &lazyBacking{m: direct}
					backing.bind()
					backing.put(&command)
					require(planes(direct) == before && direct.Steps == 0 && backing.materialized == 0 && backing.writes == 0, "eager native drawing occurred")
					if *accountClock {
						must(direct.CommitHostWork(drawSteps, drawCycles, drawSteps, drawCycles))
						require(direct.Steps == native.Steps && direct.CPU.Cycles == native.CPU.Cycles, "accounted call clock differs")
					}
					require(bytes.Equal(native.Mem, direct.Mem), "initial non-VGA RAM differs")
					base := uint32(dest-0xa000)*16 + uint32(pos[1]*80+pos[0])
					// Positive control: a real CPU read must load identical four-plane latches.
					a, b := native.Read8(0xa0000+base), direct.Read8(0xa0000+base)
					gc, seq, latch := native.VGAState()
					dgc, dseq, dlatch := direct.VGAState()
					require(a == b && gc == dgc && seq == dseq && latch == dlatch && backing.materialized == 1 && nativeReads == 1, "pre-read positive control failed")
					// A masked write uses the OLD latches, not the destination byte's latches.
					// Materializing the destination must therefore not call VGA.Read.
					for _, m := range []*dg.Machine{native, direct} {
						m.Out8(0x3ce, 8)
						m.Out8(0x3cf, 0xf0)
						m.Out8(0x3c4, 2)
						m.Out8(0x3c5, 1)
						m.Write8(0xa0000+base+1, 0xa5)
					}
					_, _, latch = native.VGAState()
					_, _, dlatch = direct.VGAState()
					require(latch == dlatch && backing.materialized == 2 && backing.writeFills == 1 && backing.readFills == 1, "pre-write positive control failed")
					entry := uint16(0x33d)
					if dest == 0xa400 {
						entry = 0x3b0
					}
					for _, m := range []*dg.Machine{native, direct} {
						m.Out8(0x3ce, 8)
						m.Out8(0x3cf, 255)
						setupCopy(m, entry)
					}
					readsBefore := nativeReads
					directReadsBefore := backing.reads
					executeReturn(native)
					executeReturn(direct)
					gc, seq, latch = native.VGAState()
					dgc, dseq, dlatch = direct.VGAState()
					equal := planes(native) == planes(direct) && bytes.Equal(native.Mem, direct.Mem) && native.CPU.R == direct.CPU.R && native.CPU.Seg == direct.CPU.Seg && native.CPU.IP == direct.CPU.IP && native.CPU.Flags == direct.CPU.Flags && gc == dgc && seq == dseq && latch == dlatch && native.SequencerIndex() == direct.SequencerIndex()
					require(equal && backing.remaining == 0 && backing.materialized == w*h && nativeReads-readsBefore > 0 && nativeReads-readsBefore == backing.reads-directReadsBefore, "native page-copy consumer mismatch")
					if *accountClock {
						require(native.Steps == direct.Steps && native.CPU.Cycles == direct.CPU.Cycles && native.Ticks == direct.Ticks && native.Frames == direct.Frames, "accounted consumer time differs")
					}
					cases = append(cases, map[string]any{"source": source.Name, "source_sha256": source.SHA256, "x_byte": pos[0], "y": pos[1], "destination": dest, "dosbox_cost": cost, "width_bytes": w, "height": h, "native_draw_steps": drawSteps, "native_draw_cycles": drawCycles, "opaque_vga_reads": readsBefore - 1, "replacement_draw_steps": 0, "replacement_draw_vga_writes": 0, "pending_after_command": w * h, "materialized_before_read": 0, "positive_read_materialized": 1, "positive_write_materialized": 1, "copy_entry": entry, "copy_vga_reads": nativeReads - readsBefore, "copy_emulated_steps": direct.Steps, "materialized_total": backing.materialized, "read_fills": backing.readFills, "write_fills": backing.writeFills, "remaining": backing.remaining, "all_planes_cpu_ram_control_equal": equal, "native_planes_sha256": planes(native), "direct_planes_sha256": planes(direct), "native_ram_sha256": digest(native.Mem), "direct_ram_sha256": digest(direct.Mem)})
					last := cases[len(cases)-1]
					last["clock_accounting"] = *accountClock
					last["cycle_clock_enabled"] = direct.CycleClock
					last["native_final_steps"], last["direct_final_steps"] = native.Steps, direct.Steps
					last["native_final_cycles"], last["direct_final_cycles"] = native.CPU.Cycles, direct.CPU.Cycles
					last["native_ticks"], last["direct_ticks"] = native.Ticks, direct.Ticks
					last["native_frames"], last["direct_frames"] = native.Frames, direct.Frames
					if *accountClock {
						last["copy_emulated_steps"] = direct.Steps - drawSteps
					}
				}
			}
		}
	}
	report := map[string]any{"schema": 1, "production": false, "normal_player_route": false, "timer_irq_enabled": false, "status": "PASS-lazy-planar-backing-native-consumer", "pam_sha256": digest(pam), "cases": cases, "limits": []string{"Only one opaque source-command routine is replaced; page copy executes original code.", "The two CPU cost modes are measured with IRQs disabled. No cycle compensation is validated.", "Lazy materialization supplies guest read/write compatibility only; it is not an HD rendering input.", "Mode transitions, overlapping pending commands and masked-image consumers need separate validation."}}
	report["timer_irq_enabled"] = *accountClock
	report["clock_accounting"] = *accountClock
	if *accountClock {
		report["limits"] = []string{"Only one opaque source-command routine is replaced; page copy executes original code.", "Default cost uses the instruction clock with IRQ disabled; DOSBox-cost cases enable the normal 3000 cycles/ms clock. Calls fit strictly event-free intervals.", "Generic IRQ, frame and periodic-call boundary delivery is checked separately. Normal-player direct bypass is not validated.", "Lazy backing supplies guest compatibility only. Mode transitions, overlapping pending commands and masked-image consumers remain unvalidated."}
	}
	b, err := json.MarshalIndent(report, "", "  ")
	must(err)
	f, err := os.OpenFile(*out, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
	must(err)
	_, err = f.Write(append(b, 10))
	must(err)
	must(f.Close())
	fmt.Printf("lazy VGA backing: %d native-consumer cases passed\n", len(cases))
}
