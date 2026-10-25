//go:build ignore

package eightsword

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func directRuntimeFixture(t *testing.T, raw []byte, dest uint16, poison byte) *dg.Machine {
	t.Helper()
	pam, err := os.ReadFile(filepath.Join(os.Getenv("EIGHTSWORD_TEST_ORIGINAL"), "PAM.AY"))
	if err != nil {
		t.Fatal(err)
	}
	m := dg.New()
	m.SetVideoMode(0x0e)
	m.IRQ0Every = 0
	m.VGAFrameEvery = 0
	m.SetDOSBoxCycles(3000)
	word := func(b []byte, at int) uint16 { return binary.LittleEndian.Uint16(b[at:]) }
	header := int(word(pam, 8)) * 16
	copy(m.Mem[0x1100:], pam[header:])
	for i := 0; i < int(word(pam, 6)); i++ {
		at := int(word(pam, 24)) + i*4
		a := 0x1100 + int(word(pam, at)) + int(word(pam, at+2))*16
		binary.LittleEndian.PutUint16(m.Mem[a:], word(m.Mem, a)+0x110)
	}
	for row := 0; row < 200; row++ {
		m.Write16(0x14d20+6+uint32(row*2), uint16(row*80))
	}
	m.Write16(0x1e880+0x7484, 1)
	m.Write16(0x1e880+0x748a, dest)
	copy(m.Mem[0x60000:], raw)
	m.CPU.R = [8]uint16{0x1234, 0x2345, 0x3456, 0x4567, 0xff00, 0x6789, 0x789a, 0x89ab}
	m.CPU.Seg = [4]uint16{0x7000, 0x14d2, 0x9000, 0x1e88}
	m.CPU.IP = 0x99c
	m.CPU.Flags = 0x202
	for i := 0; i < 32; i++ {
		m.Mem[0x9fee0+i] = poison + byte(i)
	}
	for i, v := range []uint16{0xfff0, 0x110, 0, 0x6000, 0, 0} {
		m.Write16(0x9ff00+uint32(i*2), v)
	}
	for p := 0; p < 4; p++ {
		for off := range m.EGAPlane(p) {
			m.EGAPlane(p)[off] = byte(off*7 + p*31)
		}
	}
	m.Read8(0xa0000 + 77) // Nonzero latch state must survive an opaque draw.
	return m
}

func TestResearchDirectRuntimeNativePrefixAndPoisonedStack(t *testing.T) {
	dir := os.Getenv("EIGHTSWORD_TEST_DIRECT_FIXTURES")
	if dir == "" || os.Getenv("EIGHTSWORD_TEST_ORIGINAL") == "" {
		t.Fatal("explicit read-only real inputs required")
	}
	raw, err := os.ReadFile(filepath.Join(dir, "fixtures.json"))
	if err != nil {
		t.Fatal(err)
	}
	var manifest struct {
		Fixtures []struct {
			Name, File string
			Entry      uint16
		}
	}
	if err = json.Unmarshal(raw, &manifest); err != nil {
		t.Fatal(err)
	}
	for _, source := range manifest.Fixtures {
		for _, dest := range []uint16{0xa000, 0xa400} {
			for _, poison := range []byte{0, 0xc7} {
				t.Run(fmt.Sprintf("%s-%04x-%02x", source.Name, dest, poison), func(t *testing.T) {
					raw, err := os.ReadFile(filepath.Join(dir, source.File))
					if err != nil {
						t.Fatal(err)
					}
					native := directRuntimeFixture(t, raw, dest, poison)
					host := directRuntimeFixture(t, raw, dest, poison)
					ret := uint16(0xa6f)
					if source.Entry == 0x76f {
						native.CPU.IP = source.Entry
						host.CPU.IP = source.Entry
						ret = 0x854
					}
					var nativeWrites, hostWrites []dg.VideoWrite
					native.ObserveVideoWrites(func(w dg.VideoWrite) { nativeWrites = append(nativeWrites, w) })
					host.ObserveVideoWrites(func(w dg.VideoWrite) { hostWrites = append(hostWrites, w) })
					for native.CPU.IP != ret && native.Steps < 20000 {
						if err = native.Step(); err != nil {
							t.Fatal(err)
						}
					}
					if native.CPU.IP != ret {
						t.Fatal("original prefix failed to reach RETF")
					}
					budget := oracle.HostWorkLimits{Steps: 100000, Cycles: 100000}
					plan, reason := runtimePlanarPrepare(host, budget)
					if plan == nil {
						t.Fatal(reason)
					}
					if err = plan.commit(host, budget); err != nil {
						t.Fatal(err)
					}
					if native.Steps != host.Steps || native.CPU.Cycles != host.CPU.Cycles || native.CPU.R != host.CPU.R || native.CPU.Seg != host.CPU.Seg || native.CPU.Flags != host.CPU.Flags || native.CPU.IP != host.CPU.IP {
						t.Fatalf("CPU prefix mismatch native=%d/%d host=%d/%d", native.Steps, native.CPU.Cycles, host.Steps, host.CPU.Cycles)
					}
					if !bytes.Equal(native.Mem, host.Mem) {
						for at := range native.Mem {
							if native.Mem[at] != host.Mem[at] {
								t.Fatalf("RAM %x native=%02x host=%02x", at, native.Mem[at], host.Mem[at])
							}
						}
					}
					for p := 0; p < 4; p++ {
						if !bytes.Equal(native.EGAPlane(p), host.EGAPlane(p)) {
							t.Fatal("planar compatibility mismatch", p)
						}
					}
					gc, seq, latch := native.VGAState()
					hgc, hseq, hlatch := host.VGAState()
					if gc != hgc || seq != hseq || latch != hlatch || native.SequencerIndex() != host.SequencerIndex() {
						t.Fatal("VGA controls differ")
					}
					if len(nativeWrites) != len(hostWrites) {
						t.Fatal("write metadata count", len(nativeWrites), len(hostWrites))
					}
					for i, w := range nativeWrites {
						if w != hostWrites[i] {
							t.Fatalf("write metadata %d native=%+v host=%+v", i, w, hostWrites[i])
						}
					}
					if err = native.Step(); err != nil {
						t.Fatal(err)
					}
					if err = host.Step(); err != nil {
						t.Fatal(err)
					}
					if native.CPU.R != host.CPU.R || native.CPU.Seg != host.CPU.Seg || native.CPU.IP != host.CPU.IP || native.CPU.Cycles != host.CPU.Cycles || native.Steps != host.Steps {
						t.Fatal("native RETF mismatch")
					}
					var a, b bytes.Buffer
					if err = native.SaveState(&a); err != nil {
						t.Fatal(err)
					}
					if err = host.SaveState(&b); err != nil {
						t.Fatal(err)
					}
					if !bytes.Equal(a.Bytes(), b.Bytes()) {
						t.Fatal("complete machine state differs")
					}
				})
			}
		}
	}
}

func TestResearchDirectRuntimeRejectsWithoutWrites(t *testing.T) {
	dir := os.Getenv("EIGHTSWORD_TEST_DIRECT_FIXTURES")
	raw, err := os.ReadFile(filepath.Join(dir, "pmap-ay.bin"))
	if err != nil {
		t.Fatal(err)
	}
	changes := []func(*dg.Machine){
		func(m *dg.Machine) { m.CPU.IP++ }, func(m *dg.Machine) { m.CPU.DOSBoxCost = false },
		func(m *dg.Machine) { m.Mem[0x14d20+0x99c] ^= 1 },
		func(m *dg.Machine) { m.Out8(0x3ce, 8); m.Out8(0x3cf, 0xf0) },
		func(m *dg.Machine) { m.Write16(0x1e880+0x748a, 0xa800) },
		func(m *dg.Machine) { m.Write16(0x9ff08, 80) },
		func(m *dg.Machine) { m.CPU.R[dg.SP] = 10 },
	}
	for i, change := range changes {
		m := directRuntimeFixture(t, raw, 0xa000, 0xc7)
		change(m)
		var before, after bytes.Buffer
		if err = m.SaveState(&before); err != nil {
			t.Fatal(err)
		}
		plan, _ := runtimePlanarPrepare(m, oracle.HostWorkLimits{Steps: 100000, Cycles: 100000})
		if plan != nil {
			t.Fatal("invalid input accepted", i)
		}
		if err = m.SaveState(&after); err != nil {
			t.Fatal(err)
		}
		if !bytes.Equal(before.Bytes(), after.Bytes()) {
			t.Fatal("rejection changed state", i)
		}
	}
}
