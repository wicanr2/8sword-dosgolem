package eightsword

import (
	"bytes"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

// Raw original execution first: no replacement, no fitted expected values.
func TestSourceDirectMaskedNativeTrace(t *testing.T) {
	root, out := os.Getenv("EIGHTSWORD_TEST_ORIGINAL"), os.Getenv("EIGHTSWORD_MASKED_TRACE")
	if root == "" || out == "" {
		t.Skip("需設定原始資料與新收據路徑")
	}
	var rows []map[string]any
	for _, shape := range []struct {
		name string
		raw  []byte
	}{
		{"unit", func() []byte {
			b, e := os.ReadFile(filepath.Join(root, "MAN02.EGG"))
			if e != nil {
				t.Fatal(e)
			}
			return b[:3304]
		}()},
		{"hero", func() []byte {
			b, e := os.ReadFile(filepath.Join(root, "MAN.AY"))
			if e != nil {
				t.Fatal(e)
			}
			return b[:1204]
		}()},
		{"small", append([]byte{2, 0, 2, 0}, make([]byte, 24)...)},
		{"one", append([]byte{1, 0, 1, 0}, []byte{0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc}...)},
	} {
		for _, entry := range []uint16{0x4f2, 0x626} {
			m := directRuntimeFixture(t, shape.raw, 0xa000, 0xc7)
			for plane := 0; plane < 4; plane++ {
				for off := range m.EGAPlane(plane) {
					m.EGAPlane(plane)[off] = byte(off*7 + (off/0x4000)*53 + plane*31)
				}
			}
			m.CPU.IP = entry
			m.Write16(0x14d20+0x196, 0xa400)
			m.Write16(0x9ff08, 7)
			m.Write16(0x9ff0a, 13)
			for i := 0; i < 36; i++ {
				m.Mem[0x9fedc+i] = byte(i*7 + 0x5a)
			}
			var reads []dg.VideoRead
			var writes []dg.VideoWrite
			m.ObserveVideoReads(func(r dg.VideoRead) { reads = append(reads, r) })
			m.ObserveVideoWrites(func(w dg.VideoWrite) { writes = append(writes, w) })
			ret := uint16(0x625)
			if entry == 0x626 {
				ret = 0x76e
			}
			for m.CPU.IP != ret && m.Steps < 100000 {
				if err := m.Step(); err != nil {
					t.Fatal(err)
				}
			}
			if m.CPU.IP != ret {
				t.Fatal("original RETF not reached")
			}
			sampleReads := append([]dg.VideoRead(nil), reads[:min(14, len(reads))]...)
			sampleWrites := append([]dg.VideoWrite(nil), writes[:min(14, len(writes))]...)
			gc, seq, latch := m.VGAState()
			row := map[string]any{"source": shape.name, "entry": fmt.Sprintf("%04x", entry), "steps": m.Steps, "cycles": m.CPU.Cycles, "flags": m.CPU.Flags, "stack_hex": hex.EncodeToString(m.Mem[0x9fedc:0x9ff00]), "reads": len(reads), "writes": len(writes), "read_samples": sampleReads, "write_samples": sampleWrites, "gc": gc, "seq": seq, "latches": latch}
			if len(reads) > 0 {
				row["last_read"] = reads[len(reads)-1]
			}
			if len(writes) > 0 {
				row["last_write"] = writes[len(writes)-1]
			}
			rows = append(rows, row)
		}
	}
	raw, err := json.MarshalIndent(map[string]any{"status": "native-execution-trace-only", "cases": rows}, "", "  ")
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

func maskedRuntimeFixture(t *testing.T, raw []byte, entry, dest uint16, poison byte) *dg.Machine {
	m := directRuntimeFixture(t, raw, dest, poison)
	for plane := 0; plane < 4; plane++ {
		for off := range m.EGAPlane(plane) {
			m.EGAPlane(plane)[off] = byte(off*7 + (off/0x4000)*53 + plane*31)
		}
	}
	m.CPU.IP = entry
	m.CPU.Flags |= dg.DF | dg.CF | dg.SF | dg.OF
	m.Steps, m.CPU.Cycles = 123, 456
	m.Write16(0x14d20+0x196, 0xa400)
	// Same physical source, nonzero source offset exercises pointer stack slots.
	m.Write16(0x9ff04, 0x20)
	m.Write16(0x9ff06, 0x5ffe)
	m.Write16(0x9ff08, 7)
	m.Write16(0x9ff0a, 13)
	for i := 0; i < 36; i++ {
		m.Mem[0x9fedc+i] = poison + byte(i*7)
	}
	return m
}

func TestSourceDirectMaskedNativePrefix(t *testing.T) {
	root := os.Getenv("EIGHTSWORD_TEST_ORIGINAL")
	if root == "" {
		t.Skip("需設定唯讀原始資料")
	}
	read := func(name string, size int) []byte {
		raw, err := os.ReadFile(filepath.Join(root, name))
		if err != nil {
			t.Fatal(err)
		}
		return raw[:size]
	}
	pattern := append([]byte{3, 0, 4, 0}, make([]byte, 72)...)
	for i := 4; i < len(pattern); i++ {
		pattern[i] = byte(i*43 + 11)
	}
	for _, source := range []struct {
		name string
		raw  []byte
	}{
		{"MAN02", read("MAN02.EGG", 3304)}, {"hero", read("MAN.AY", 1204)},
		{"mask-pattern", pattern}, {"one", []byte{1, 0, 1, 0, 0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc}},
	} {
		for _, mode := range []struct{ entry, dest uint16 }{{0x4f2, 0xa000}, {0x4f2, 0xa400}, {0x626, 0xa000}} {
			for _, poison := range []byte{0, 0xc7} {
				t.Run(fmt.Sprintf("%s-%04x-%04x-%02x", source.name, mode.entry, mode.dest, poison), func(t *testing.T) {
					native := maskedRuntimeFixture(t, source.raw, mode.entry, mode.dest, poison)
					host := maskedRuntimeFixture(t, source.raw, mode.entry, mode.dest, poison)
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
					ret := uint16(0x625)
					if mode.entry == 0x626 {
						ret = 0x76e
					}
					for native.CPU.IP != ret && native.Steps < 100000 {
						if err := native.Step(); err != nil {
							t.Fatal(err)
						}
					}
					if native.CPU.IP != ret {
						t.Fatal("native RETF not reached")
					}
					budget := oracle.HostWorkLimits{Steps: 100000, Cycles: 100000}
					plan, reason := runtimePlanarPrepare(host, budget)
					if plan == nil {
						t.Fatal(reason)
					}
					if err := plan.commit(host, budget); err != nil {
						t.Fatal(err)
					}
					if native.Steps != host.Steps || native.CPU.Cycles != host.CPU.Cycles || native.CPU.R != host.CPU.R || native.CPU.Seg != host.CPU.Seg || native.CPU.Flags != host.CPU.Flags || native.CPU.IP != host.CPU.IP {
						t.Fatalf("CPU prefix mismatch native=%d/%d/%04x host=%d/%d/%04x", native.Steps, native.CPU.Cycles, native.CPU.Flags, host.Steps, host.CPU.Cycles, host.CPU.Flags)
					}
					if !bytes.Equal(native.Mem, host.Mem) {
						for at, v := range native.Mem {
							if v != host.Mem[at] {
								t.Fatalf("RAM %x native=%02x host=%02x", at, v, host.Mem[at])
							}
						}
					}
					for p := 0; p < 4; p++ {
						if !bytes.Equal(native.EGAPlane(p), host.EGAPlane(p)) {
							t.Fatal("planes differ", p)
						}
					}
					gc, seq, latch := native.VGAState()
					hgc, hseq, hlatch := host.VGAState()
					if gc != hgc || seq != hseq || latch != hlatch || native.SequencerIndex() != host.SequencerIndex() {
						t.Fatal("VGA controls/latches differ", gc, hgc, latch, hlatch)
					}
					if len(a) != len(b) {
						t.Fatal("ordered trace length", len(a), len(b))
					}
					for i, e := range a {
						if e != b[i] {
							t.Fatalf("ordered trace %d native=%+v host=%+v", i, e, b[i])
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
						t.Fatal("complete native RETF state differs")
					}
				})
			}
		}
	}
}

func TestSourceDirectMaskedRejectsWithoutWrites(t *testing.T) {
	raw := []byte{1, 0, 1, 0, 0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc}
	for _, c := range []struct {
		name   string
		change func(*dg.Machine)
		reason string
	}{
		{"code", func(m *dg.Machine) { m.Mem[0x14d20+0x626] ^= 1 }, "code"},
		{"zero-width", func(m *dg.Machine) { m.Write16(0x60000, 0) }, "geometry"},
		{"overflow", func(m *dg.Machine) { m.Write16(0x9ff08, 80) }, "geometry"},
		{"source-wrap", func(m *dg.Machine) {
			m.Write16(0x9ff04, 0xfffc)
			m.Write16(0x9ff06, 0x5000)
			m.Write16(0x5fffc, 1)
			m.Write16(0x5fffe, 1)
		}, "source-bounds"},
		{"stack-small", func(m *dg.Machine) { m.CPU.R[dg.SP] = 34 }, "stack-bounds"},
		{"background", func(m *dg.Machine) { m.Write16(0x14d20+0x196, 0xa000) }, "background-page"},
		{"destination", func(m *dg.Machine) { m.Write16(0x1e880+0x748a, 0xa800) }, "destination"},
		{"mode", func(m *dg.Machine) { m.Write16(0x1e880+0x7484, 2) }, "display-mode"},
		{"pitch", func(m *dg.Machine) { m.Write16(0x14d20+6+26, 7) }, "row-table"},
		{"gc", func(m *dg.Machine) { m.Out8(0x3ce, 3); m.Out8(0x3cf, 0x18) }, "vga-mode"},
	} {
		t.Run(c.name, func(t *testing.T) {
			m := maskedRuntimeFixture(t, raw, 0x626, 0xa000, 0xc7)
			c.change(m)
			var before, after bytes.Buffer
			if err := m.SaveState(&before); err != nil {
				t.Fatal(err)
			}
			plan, reason := runtimePlanarPrepare(m, oracle.HostWorkLimits{Steps: 100000, Cycles: 100000})
			if plan != nil || reason != c.reason {
				t.Fatalf("accepted or wrong rejection: %v %s", plan != nil, reason)
			}
			if err := m.SaveState(&after); err != nil {
				t.Fatal(err)
			}
			if !bytes.Equal(before.Bytes(), after.Bytes()) {
				t.Fatal("rejected input changed guest")
			}
		})
	}
	for _, budget := range []oracle.HostWorkLimits{{Steps: 1, Cycles: 100000}, {Steps: 100000, Cycles: 1}} {
		m := maskedRuntimeFixture(t, raw, 0x626, 0xa000, 0xc7)
		plan, reason := runtimePlanarPrepare(m, budget)
		if plan != nil || reason != "quota" {
			t.Fatal("quota accepted", reason)
		}
	}
}

func TestSourceHostPlanarReadPreparation(t *testing.T) {
	m := maskedRuntimeFixture(t, []byte{1, 0, 1, 0, 0, 0, 0, 0, 0, 0}, 0x626, 0xa000, 0)
	read := dg.VideoRead{Step: 777, CS: 0x14d2, IP: 0x6b4, Offset: 0x4012}
	prepared, observed := false, false
	m.PreparePlanarAccess(func(off uint32) {
		if off != read.Offset {
			t.Fatal("wrong preparation offset")
		}
		for p := 0; p < 4; p++ {
			m.EGAPlane(p)[off] = byte(0x42 + p)
		}
		prepared = true
	}, nil)
	m.ObserveVideoReads(func(r dg.VideoRead) {
		if !prepared || r != read {
			t.Fatal("wrong ordering/site")
		}
		observed = true
	})
	m.ReadHostPlanar(read)
	_, _, latch := m.VGAState()
	if !prepared || !observed || latch != [4]byte{0x42, 0x43, 0x44, 0x45} {
		t.Fatal("preparation/latch contract", latch)
	}
	if m.Steps != 123 || m.CPU.IP != 0x626 {
		t.Fatal("read executed an opcode")
	}
}
