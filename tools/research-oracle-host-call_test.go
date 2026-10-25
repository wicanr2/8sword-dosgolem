//go:build ignore

package oracle

import (
	"testing"

	"github.com/wicanr2/dosgolem/internal/dos"
	"github.com/wicanr2/dosgolem/internal/machine"
)

func hostTestOracle(t *testing.T) *Oracle {
	m := machine.New()
	m.IRQ0Every = 0
	m.VGAFrameEvery = 0
	m.CPU.Seg[1] = 0x9000
	m.CPU.IP = 0x100
	for i := 0; i < 256; i++ {
		m.Mem[0x90100+i] = 0x90
	}
	d := dos.New(m, t.TempDir())
	d.Install()
	return &Oracle{m: m, d: d, onCall: map[uint32][]func(*Oracle){}}
}

func TestResearchHostCallKeepsEntryAndReturnBoundary(t *testing.T) {
	o := hostTestOracle(t)
	entered, returned := 0, 0
	o.OnCall(Addr{0x9000, 0x100}, func(*Oracle) { entered++ })
	o.OnCall(Addr{0x9000, 0x10f}, func(*Oracle) { returned++ })
	o.OnHostCall(Addr{0x9000, 0x100}, func(o *Oracle, m *machine.Machine, b HostWorkLimits) (bool, error) {
		if b.Steps < 15 || b.Cycles < 30 {
			return false, nil
		}
		if err := m.CommitHostWork(15, 30, b.Steps, b.Cycles); err != nil {
			return false, err
		}
		m.CPU.IP += 15
		return true, nil
	})
	if err := o.Run(16); err != nil {
		t.Fatal(err)
	}
	if entered != 1 || returned != 1 || o.m.Steps != 16 || o.m.CPU.Cycles != 32 || o.m.CPU.IP != 0x110 {
		t.Fatal(entered, returned, o.m.Steps, o.m.CPU.Cycles, o.IP())
	}
}

func TestResearchHostCallRunCyclesAndUnknownConditions(t *testing.T) {
	for _, quota := range []uint64{4, 15, 16} {
		o := hostTestOracle(t)
		o.SetDOSBoxCycles(3000)
		calls := 0
		o.OnHostCall(Addr{0x9000, 0x100}, func(o *Oracle, m *machine.Machine, b HostWorkLimits) (bool, error) {
			if b.Steps < 15 || b.Cycles < 15 {
				return false, nil
			}
			calls++
			if err := m.CommitHostWork(15, 15, b.Steps, b.Cycles); err != nil {
				return false, err
			}
			m.CPU.IP += 15
			return true, nil
		})
		if err := o.RunCycles(quota); err != nil {
			t.Fatal(err)
		}
		want := 0
		if quota >= 15 {
			want = 1
		}
		if o.m.Steps != quota || o.m.CPU.Cycles != quota || calls != want {
			t.Fatal(quota, o.m.Steps, o.m.CPU.Cycles, calls)
		}
	}
	o := hostTestOracle(t)
	called := false
	o.OnHostCall(Addr{0x9000, 0x100}, func(*Oracle, *machine.Machine, HostWorkLimits) (bool, error) { called = true; return false, nil })
	if err := o.RunUntil(At(Addr{0x9000, 0x108}), Budget(9)); err != nil {
		t.Fatal(err)
	}
	if called || o.m.Steps != 8 {
		t.Fatal("arbitrary stopping condition was bypassed")
	}
}

func TestResearchHostCallPreservesDueEventAndGuard(t *testing.T) {
	for _, guard := range []bool{false, true} {
		o := hostTestOracle(t)
		calls := 0
		guards := 0
		o.OnHostCall(Addr{0x9000, 0x100}, func(*Oracle, *machine.Machine, HostWorkLimits) (bool, error) { calls++; return false, nil })
		if guard {
			o.SetStepGuard(func(*Oracle) error { guards++; return nil })
		} else {
			o.m.ScheduleKey(0, 0x1e, false)
		}
		if err := o.Run(1); err != nil {
			t.Fatal(err)
		}
		if calls != 0 || (guard && guards != 1) {
			t.Fatal("guard or pending input was bypassed", guard, calls, guards)
		}
	}
}
