//go:build ignore

// 047 DRAFT: direct source-command replacement of one verified planar routine.
// This isolated call probe does not install hooks into the production player.
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

	dg "github.com/wicanr2/dosgolem"
)

type directSource struct {
	Name, File, SHA256 string
	WidthBytes         int `json:"width_bytes"`
	Height             int
}
type directCommand struct {
	SourceSHA256                 string
	XByte, Y, WidthBytes, Height int
	Destination                  uint16
	Raw                          []byte `json:"-"`
}

func must(err error) {
	if err != nil {
		panic(err)
	}
}
func digest(b []byte) string       { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func word(b []byte, at int) uint16 { return binary.LittleEndian.Uint16(b[at:]) }

func machine(pam, raw []byte, x, y int, dest, flags uint16) *dg.Machine {
	m := dg.New()
	m.IRQ0Every = 0 // Single-call output contract; IRQ/cycle compensation is a separate gate.
	m.SetVideoMode(0x0e)
	header := int(word(pam, 8)) * 16
	copy(m.Mem[0x1100:], pam[header:])
	for i := 0; i < int(word(pam, 6)); i++ {
		at := int(word(pam, 24)) + i*4
		address := 0x1100 + int(word(pam, at)) + int(word(pam, at+2))*16
		binary.LittleEndian.PutUint16(m.Mem[address:], word(m.Mem, address)+0x110)
	}
	for row := 0; row < 200; row++ {
		m.Write16(0x14d20+6+uint32(row*2), uint16(row*80))
	}
	m.Write16(0x1e880+0x7484, 1)
	m.Write16(0x1e880+0x748a, dest)
	copy(m.Mem[0x60000:], raw)
	m.CPU.R = [8]uint16{0x1234, 0x2345, 0x3456, 0x4567, 0xff00, 0x6789, 0x789a, 0x89ab}
	m.CPU.Seg = [4]uint16{0x7000, 0x14d2, 0x9000, 0x1e88}
	m.CPU.IP, m.CPU.Flags = 0x99c, flags
	for i, v := range []uint16{0xfff0, 0x110, 0, 0x6000, uint16(x), uint16(y)} {
		m.Write16(0x9ff00+uint32(i*2), v)
	}
	return m
}

func emptyReturn(m *dg.Machine) {
	sp := m.CPU.R[dg.SP]
	ss := uint32(m.CPU.Seg[dg.SS]) * 16
	m.CPU.IP = m.Read16(ss + uint32(sp))
	m.CPU.Seg[dg.CS] = m.Read16(ss + uint32(sp+2))
	m.CPU.R[dg.SP] += 4
}

func replace(m *dg.Machine) directCommand {
	gc, _, _ := m.VGAState()
	if m.VideoMode() != 0x0e || gc[1]&15 != 0 || gc[3]&31 != 0 || gc[5]&3 != 0 || gc[8] != 255 {
		panic("unsupported direct planar VGA state")
	}
	r, seg := m.CPU.R, m.CPU.Seg
	sp, ss := r[dg.SP], uint32(seg[dg.SS])*16
	arg := func(n uint16) uint16 { return m.Read16(ss + uint32(sp+4+n*2)) }
	ptr := uint32(arg(1))*16 + uint32(arg(0))
	w, h := int(m.Read16(ptr)), int(m.Read16(ptr+2))
	x, y := int(arg(2)), int(arg(3))
	ds := uint32(seg[dg.DS]) * 16
	dest := m.Read16(ds + 0x748a)
	if m.Read16(ds+0x7484) != 1 || (dest != 0xa000 && dest != 0xa400) || w < 1 || h < 1 || w+x > 80 || h+y > 200 || ptr+uint32(4+4*w*h) > 0xa0000 {
		panic("unsupported direct planar command")
	}
	for row := 0; row < h; row++ {
		if m.Read16(uint32(seg[dg.CS])*16+6+uint32((y+row)*2)) != uint16((y+row)*80) {
			panic("direct planar row table differs")
		}
	}
	raw := append([]byte(nil), m.Mem[ptr:ptr+uint32(4+w*h*4)]...)
	command := directCommand{digest(raw), x, y, w, h, dest, raw}
	// Preserve the original dead-stack bytes as well as live registers/flags.
	stack := []uint16{r[dg.BP], uint16(w), uint16(h), 16, uint16(w * h), r[dg.AX], r[dg.BX], r[dg.CX], r[dg.DX], r[dg.SI], r[dg.DI], seg[dg.DS], seg[dg.ES], uint16(h), uint16(y * 2)}
	for i, v := range stack {
		m.Write16(ss+uint32(sp-uint16((i+1)*2)), v)
	}
	m.Out8(0x3c4, 2)
	m.Out8(0x3c5, 8)
	m.CPU.Flags = (m.CPU.Flags & ^uint16(dg.CF|dg.PF|dg.AF|dg.ZF|dg.SF|dg.OF|dg.DF)) | dg.PF | dg.ZF
	emptyReturn(m)
	return command
}

// The source command is also sufficient for a managed native fallback surface.
// It does not read the guest's VGA or the original rendered frame.
func commandPixels(c directCommand) []byte {
	pixels := make([]byte, 640*200)
	area := c.WidthBytes * c.Height
	for y := 0; y < c.Height; y++ {
		for x := 0; x < c.WidthBytes*8; x++ {
			local := y*c.WidthBytes*8 + x
			value := byte(0)
			for plane := 0; plane < 4; plane++ {
				value |= ((c.Raw[4+plane*area+local/8] >> uint(7-local%8)) & 1) << uint(plane)
			}
			pixels[(c.Y+y)*640+c.XByte*8+x] = value
		}
	}
	return pixels
}

func main() {
	root := flag.String("root", "", "read-only original game directory")
	fixtures := flag.String("fixtures", "", "prepared source fixtures")
	out := flag.String("out", "", "new JSON receipt")
	flag.Parse()
	if _, err := os.Stat("/.dockerenv"); err != nil || os.Getuid() != 1000 {
		panic("Docker UID 1000 required")
	}
	pam, err := os.ReadFile(filepath.Join(*root, "PAM.AY"))
	must(err)
	if digest(pam) != "83e32f132e808d70ac7e170aa1c0019eb4c579b9c785f2cbaf0d3e00af28d6c0" {
		panic("PAM identity differs")
	}
	if pam[0x15aff] != 0xcb || digest(pam[0x15a2c:0x15b00]) != "a2f457e4ad98813eb3b8e2d727e71074b612c52b473cc3153ce42f915c1b70c8" {
		panic("planar far-return byte differs")
	}
	raw, err := os.ReadFile(filepath.Join(*fixtures, "fixtures.json"))
	must(err)
	var manifest struct {
		Schema   int
		Fixtures []directSource
	}
	must(json.Unmarshal(raw, &manifest))
	if manifest.Schema != 1 || len(manifest.Fixtures) != 3 {
		panic("fixture schema differs")
	}
	var results []map[string]any
	for _, source := range manifest.Fixtures {
		raw, err := os.ReadFile(filepath.Join(*fixtures, source.File))
		must(err)
		if digest(raw) != source.SHA256 {
			panic("fixture digest differs")
		}
		w, h := int(word(raw, 0)), int(word(raw, 2))
		if w != source.WidthBytes || h != source.Height {
			panic("fixture geometry differs")
		}
		positions := [][2]int{{0, 0}}
		if w != 80 || h != 200 {
			positions = append(positions, [2]int{80 - w, 200 - h})
		}
		for _, position := range positions {
			for _, dest := range []uint16{0xa000, 0xa400} {
				for _, flags := range []uint16{2, 0xcd7, 0x202} {
					original := machine(pam, raw, position[0], position[1], dest, flags)
					direct := machine(pam, raw, position[0], position[1], dest, flags)
					negative := machine(pam, raw, position[0], position[1], dest, flags)
					beforePlanes := [4]string{}
					for plane := range beforePlanes {
						beforePlanes[plane] = digest(direct.EGAPlane(plane))
					}
					// Historical WatchReads does not see planar VGA. This count is
					// retained for receipt compatibility, not as evidence of no reads.
					// probe-vga-shadow.go uses the dedicated pre-read hook instead.
					reads := 0
					original.WatchReads(0xa0000, 0xaffff, func(uint32, uint8) { reads++ })
					original.RowWritesFrom = 1
					for original.CPU.IP != 0xfff0 && original.Steps < 2000000 {
						must(original.Step())
					}
					if original.CPU.IP != 0xfff0 || original.CPU.Seg[dg.CS] != 0x110 || original.Steps == 0 {
						panic("original call did not execute and return")
					}
					command := replace(direct)
					emptyReturn(negative)
					regs := original.CPU.R == direct.CPU.R && original.CPU.Seg == direct.CPU.Seg && original.CPU.IP == direct.CPU.IP
					flagsEqual := original.CPU.Flags == direct.CPU.Flags
					ram := bytes.Equal(original.Mem, direct.Mem)
					gc, seq, latch := original.VGAState()
					dgGC, dgSeq, dgLatch := direct.VGAState()
					io := gc == dgGC && seq == dgSeq && latch == dgLatch && original.SequencerIndex() == direct.SequencerIndex()
					stores := uint64(0)
					for _, n := range original.VideoRowWrites {
						stores += n
					}
					directStores := uint64(0)
					for _, n := range direct.WriteModeUse {
						directStores += n
					}
					start := int(dest-0xa000) * 16
					nativeSurface, managedSurface := original.IndexedEGAFrom(start, 640, 200), commandPixels(command)
					pixelsEqual := bytes.Equal(nativeSurface, managedSurface)
					planesUnchanged := true
					for plane, before := range beforePlanes {
						planesUnchanged = planesUnchanged && before == digest(direct.EGAPlane(plane))
					}
					negativeRejected := !bytes.Equal(original.Mem, negative.Mem) || original.CPU.Flags != negative.CPU.Flags
					if !regs || !flagsEqual || !ram || !io || !pixelsEqual || !negativeRejected || !planesUnchanged || reads != 0 || stores != uint64(w*h*4) || directStores != 0 || direct.Steps != 0 {
						panic(fmt.Sprintf("direct contract mismatch %s pos=%v dest=%x flags=%x: regs=%v flags=%v ram=%v io=%v pixels=%v negative=%v reads=%d writes=%d originalFlags=%x directFlags=%x", source.Name, position, dest, flags, regs, flagsEqual, ram, io, pixelsEqual, negativeRejected, reads, stores, original.CPU.Flags, direct.CPU.Flags))
					}
					results = append(results, map[string]any{"source": source.Name, "source_sha256": source.SHA256, "command": command, "input_flags": flags, "original_steps": original.Steps, "original_cycles": original.CPU.Cycles, "original_vga_stores": stores, "vga_reads_inside_original_call": reads, "replacement_emulated_steps": direct.Steps, "replacement_vga_stores": directStores, "live_registers_equal": regs, "flags_equal": flagsEqual, "conventional_ram_equal": ram, "vga_control_equal": io, "source_surface_equals_original": pixelsEqual, "empty_return_rejected": negativeRejected, "replacement_vga_planes_unchanged": planesUnchanged, "original_surface_sha256": digest(nativeSurface), "managed_surface_sha256": digest(managedSurface), "original_ram_sha256": digest(original.Mem), "replacement_ram_sha256": digest(direct.Mem)})
				}
			}
		}
	}
	report := map[string]any{"schema": 1, "status": "PASS-single-routine-direct-source-command-contract", "production": false, "normal_player_route": false, "timer_irq_enabled": false, "pam_sha256": digest(pam), "routine_sha256": digest(pam[0x15a2c:0x15b00]), "address_space": "IDA MZ linear sub_245BC; runtime 14D2:099C..0A6F, load 0110; original PAM file offset 0x15A2C..0x15AFF", "cases": results, "limits": []string{"Only the verified mode-1 four-plane routine is replaced in this isolated probe.", "The guest VGA planes intentionally remain untouched; later guest reads and managed shadow surfaces require validation.", "Cycle compensation, IRQ/audio scheduling, normal gameplay and production integration are not validated.", "This probe emits source commands; no claim of fixed FPS or whole-game replacement."}}
	b, err := json.MarshalIndent(report, "", "  ")
	must(err)
	f, err := os.OpenFile(*out, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
	must(err)
	_, err = f.Write(append(b, 10))
	must(err)
	must(f.Close())
	fmt.Printf("direct planar output contract: %d cases passed; zero guest renderer steps and VGA stores in replacement\n", len(results))
}
