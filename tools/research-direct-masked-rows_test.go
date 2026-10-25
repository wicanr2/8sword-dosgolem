//go:build ignore

package eightsword

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func maskedRowFixture(t *testing.T, raw []byte, entry, dest uint16, poison byte, sourceEnd bool) *dg.Machine {
	t.Helper()
	m := maskedRuntimeFixture(t, raw, entry, dest, poison)
	if sourceEnd {
		copy(m.Mem[0x5fff6:], raw)
		m.Write16(0x9ff04, 0xfff6)
		m.Write16(0x9ff06, 0x5000)
	}
	if poison != 0 {
		m.Out8(0x3ce, 4)
		m.Out8(0x3cf, 2) // AH must use the actual read-map result.
	}
	return m
}

func assertMaskedRowState(t *testing.T, a, b *dg.Machine) {
	t.Helper()
	if a.CPU.R != b.CPU.R || a.CPU.Seg != b.CPU.Seg || a.CPU.Flags != b.CPU.Flags || a.CPU.IP != b.CPU.IP || a.CPU.Cycles != b.CPU.Cycles || a.Steps != b.Steps {
		t.Fatalf("row CPU differs native=%+v/%04x/%x/%d/%d host=%+v/%04x/%x/%d/%d", a.CPU.R, a.CPU.Flags, a.CPU.IP, a.Steps, a.CPU.Cycles, b.CPU.R, b.CPU.Flags, b.CPU.IP, b.Steps, b.CPU.Cycles)
	}
	if !bytes.Equal(a.Mem, b.Mem) {
		for at, v := range a.Mem {
			if v != b.Mem[at] {
				t.Fatalf("row RAM %x native=%02x host=%02x", at, v, b.Mem[at])
			}
		}
	}
	for plane := 0; plane < 4; plane++ {
		if !bytes.Equal(a.EGAPlane(plane), b.EGAPlane(plane)) {
			t.Fatal("row planes differ", plane)
		}
	}
	gc, seq, latch := a.VGAState()
	hgc, hseq, hlatch := b.VGAState()
	if gc != hgc || seq != hseq || latch != hlatch || a.SequencerIndex() != b.SequencerIndex() {
		t.Fatal("row VGA controls or latches differ", latch, hlatch)
	}
}

func TestResearchDirectMaskedRowsNativeState(t *testing.T) {
	root, out := os.Getenv("EIGHTSWORD_TEST_ORIGINAL"), os.Getenv("EIGHTSWORD_MASKED_ROWS_RECEIPT")
	if root == "" || out == "" {
		t.Fatal("explicit original and new row receipt required")
	}
	read := func(name string, n int) []byte {
		raw, err := os.ReadFile(filepath.Join(root, name))
		if err != nil {
			t.Fatal(err)
		}
		return raw[:n]
	}
	pattern := append([]byte{3, 0, 4, 0}, make([]byte, 72)...)
	for i := 4; i < len(pattern); i++ {
		pattern[i] = byte(i*43 + 11)
	}
	var results []map[string]any
	for _, source := range []struct {
		name      string
		raw       []byte
		sourceEnd bool
	}{
		{"MAN02", read("MAN02.EGG", 3304), false}, {"hero", read("MAN.AY", 1204), false},
		{"mask-pattern", pattern, false}, {"one", []byte{1, 0, 1, 0, 0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc}, false},
		{"source-end", []byte{1, 0, 1, 0, 0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc}, true},
	} {
		for _, mode := range []struct{ entry, dest uint16 }{{0x4f2, 0xa000}, {0x4f2, 0xa400}, {0x626, 0xa000}} {
			for _, poison := range []byte{0, 0xc7} {
				for _, tail := range []bool{false, true} {
					name := fmt.Sprintf("%s-%04x-%04x-%02x-tail-%t", source.name, mode.entry, mode.dest, poison, tail)
					t.Run(name, func(t *testing.T) {
						native := maskedRowFixture(t, source.raw, mode.entry, mode.dest, poison, source.sourceEnd)
						host := maskedRowFixture(t, source.raw, mode.entry, mode.dest, poison, source.sourceEnd)
						rowEntry, ret, byteSteps := uint16(0x56f), uint16(0x625), uint64(9)
						if mode.entry == 0x626 {
							rowEntry, ret, byteSteps = 0x6a3, 0x76e, 12
						}
						type event struct {
							Kind  string
							Read  dg.VideoRead
							Write dg.VideoWrite
						}
						var a, b []event
						observe := func(m *dg.Machine, out *[]event) {
							m.ObserveVideoReads(func(r dg.VideoRead) { *out = append(*out, event{Kind: "read", Read: r}) })
							m.ObserveVideoWrites(func(w dg.VideoWrite) { *out = append(*out, event{Kind: "write", Write: w}) })
						}
						observe(native, &a)
						observe(host, &b)
						batches, compat, tailBatches := 0, 0, 0
						for native.CPU.IP != ret && native.Steps < 150000 {
							if native.CPU.IP == rowEntry {
								w := uint16(source.raw[0]) | uint16(source.raw[1])<<8
								if tail && native.CPU.R[dg.CX] == w && w > 1 {
									// A budget refusal leaves the native first byte available.
									if plan, reason := runtimePlanarPrepare(host, oracle.HostWorkLimits{Steps: 1, Cycles: 1}); plan != nil || reason != "row-quota" {
										t.Fatal("tiny row quota accepted", reason)
									}
									for i := uint64(0); i < byteSteps; i++ {
										if err := native.Step(); err != nil {
											t.Fatal(err)
										}
										if err := host.Step(); err != nil {
											t.Fatal(err)
										}
									}
									continue
								}
								budget := oracle.HostWorkLimits{Steps: 100000, Cycles: 100000}
								plan, reason := runtimePlanarPrepare(host, budget)
								if plan == nil {
									t.Fatal(reason)
								}
								if plan.Primitive != "masked-row" {
									t.Fatal("not a row plan")
								}
								stop := native.Steps + plan.Steps
								for native.Steps < stop {
									if err := native.Step(); err != nil {
										t.Fatal(err)
									}
								}
								if native.CPU.IP != plan.ReturnBoundary {
									t.Fatal("original row did not end at boundary")
								}
								if err := plan.commit(host, budget); err != nil {
									t.Fatal(err)
								}
								assertMaskedRowState(t, native, host)
								batches++
								compat += int(plan.CompatibilityBytes)
								if plan.Column > 0 {
									tailBatches++
								}
								continue
							}
							if err := native.Step(); err != nil {
								t.Fatal(err)
							}
							if err := host.Step(); err != nil {
								t.Fatal(err)
							}
						}
						if native.CPU.IP != ret || batches == 0 {
							t.Fatal("original return or row work missing")
						}
						assertMaskedRowState(t, native, host)
						if len(a) != len(b) {
							t.Fatal("ordered row trace length", len(a), len(b))
						}
						for i, e := range a {
							if e != b[i] {
								t.Fatalf("ordered row trace %d native=%+v host=%+v", i, e, b[i])
							}
						}
						if err := native.Step(); err != nil {
							t.Fatal(err)
						}
						if err := host.Step(); err != nil {
							t.Fatal(err)
						}
						var ns, hs bytes.Buffer
						if err := native.SaveState(&ns); err != nil {
							t.Fatal(err)
						}
						if err := host.SaveState(&hs); err != nil {
							t.Fatal(err)
						}
						if !bytes.Equal(ns.Bytes(), hs.Bytes()) {
							t.Fatal("full state after native RETF differs")
						}
						results = append(results, map[string]any{"case": name, "batches": batches, "compatibility_bytes": compat, "tail_batches": tailBatches, "ordered_events": len(a), "same_cpu_ram_planes_each_batch": true, "same_final_serialized_state": true})
					})
				}
			}
		}
	}
	raw, err := json.MarshalIndent(map[string]any{"status": "PASS-controlled-row-prefix-not-natural-path", "cases": results}, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	f, err := os.OpenFile(out, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0644)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = f.Write(append(raw, 10)); err != nil {
		t.Fatal(err)
	}
	if err = f.Close(); err != nil {
		t.Fatal(err)
	}
}

func TestResearchDirectMaskedRowsRejectWithoutWrites(t *testing.T) {
	fixture := func() *dg.Machine {
		raw := append([]byte{3, 0, 2, 0}, make([]byte, 36)...)
		m := maskedRowFixture(t, raw, 0x626, 0xa000, 0xc7, false)
		for m.CPU.IP != 0x6a3 && m.Steps < 1000 {
			if err := m.Step(); err != nil {
				t.Fatal(err)
			}
		}
		if m.CPU.IP != 0x6a3 {
			t.Fatal("native row not reached")
		}
		return m
	}
	for _, c := range []struct {
		name   string
		change func(*dg.Machine)
		reason string
	}{
		{"code", func(m *dg.Machine) { m.Mem[0x14d20+0x626] ^= 1 }, "row-code"},
		{"direction", func(m *dg.Machine) { m.CPU.Flags |= dg.DF }, "row-registers"},
		{"port", func(m *dg.Machine) { m.CPU.R[dg.DX] = 0 }, "row-registers"},
		{"source", func(m *dg.Machine) { m.CPU.Seg[dg.DS]++ }, "row-source"},
		{"stack", func(m *dg.Machine) { m.CPU.R[dg.SP]++ }, "row-stack"},
		{"width", func(m *dg.Machine) { m.Write16(0x60000, 0) }, "row-geometry"},
		{"remaining", func(m *dg.Machine) { m.CPU.R[dg.CX] = 0 }, "row-position"},
		{"plane", func(m *dg.Machine) { m.Out8(0x3c4, 2); m.Out8(0x3c5, 3) }, "row-plane"},
		{"mask", func(m *dg.Machine) { m.Write16(0x90000+uint32(m.CPU.R[dg.BP])-10, 0) }, "row-pointers"},
		{"destination", func(m *dg.Machine) { m.CPU.Seg[dg.ES] = 0xa800 }, "row-destination"},
		{"background", func(m *dg.Machine) { m.Write16(0x14d20+0x196, 0xa000) }, "row-background"},
		{"gc", func(m *dg.Machine) { m.Out8(0x3ce, 3); m.Out8(0x3cf, 0x18) }, "row-vga-mode"},
		{"event", func(m *dg.Machine) { m.ScheduleKey(m.Steps, 0x1e, false) }, "row-event"},
		{"alias", func(m *dg.Machine) {
			frame := append([]byte(nil), m.Mem[0x90000+uint32(m.CPU.R[dg.BP])-34:0x90000+uint32(m.CPU.R[dg.BP])+14]...)
			copy(m.Mem[0x5ffe0+80-34:], frame)
			m.CPU.Seg[dg.SS] = 0x5ffe
			m.CPU.R[dg.BP] = 80
			m.CPU.R[dg.SP] = 48
		}, "row-alias"},
	} {
		t.Run(c.name, func(t *testing.T) {
			m := fixture()
			c.change(m)
			var a, b bytes.Buffer
			if err := m.SaveState(&a); err != nil {
				t.Fatal(err)
			}
			plan, reason := runtimePlanarPrepare(m, oracle.HostWorkLimits{Steps: 100000, Cycles: 100000})
			if plan != nil || reason != c.reason {
				t.Fatal("wrong rejection", plan != nil, reason, c.reason)
			}
			if err := m.SaveState(&b); err != nil {
				t.Fatal(err)
			}
			if !bytes.Equal(a.Bytes(), b.Bytes()) {
				t.Fatal("row rejection changed state")
			}
		})
	}
	for _, budget := range []oracle.HostWorkLimits{{Steps: 1, Cycles: 100000}, {Steps: 100000, Cycles: 1}} {
		m := fixture()
		plan, reason := runtimePlanarPrepare(m, budget)
		if plan != nil || reason != "row-quota" {
			t.Fatal("row quota accepted", reason)
		}
	}
}
