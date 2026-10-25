//go:build ignore

package machine

import "testing"

func TestResearchHostWorkBothClockBoundaries(t *testing.T) {
	for _, cycleClock := range []bool{false, true} {
		for _, dosCost := range []bool{false, true} {
			m := New()
			m.Steps = 100
			m.CPU.Cycles = 200
			m.CycleClock = cycleClock
			m.CPU.DOSBoxCost = dosCost
			m.IRQ0Every = 50
			m.nextIRQ0 = 137
			m.VGAFrameEvery = 100
			m.nextFrame = 150
			m.cycPerIRQ0 = 100
			m.nextIRQ0Cyc = 223
			want := HostWorkLimits{37, 1000}
			if cycleClock {
				want = HostWorkLimits{50, 23}
			}
			if got := m.HostWorkBudget(1000, 1000); got != want {
				t.Fatalf("clock=%v cost=%v budget=%v want=%v", cycleClock, dosCost, got, want)
			}
			m.periodic.on = true
			m.periodic.next = 121
			want.Steps = 21
			if got := m.HostWorkBudget(1000, 1000); got != want {
				t.Fatal("periodic callback", got, want)
			}
			if err := m.CommitHostWork(22, 1, 1000, 1000); err == nil || m.Steps != 100 || m.CPU.Cycles != 200 {
				t.Fatal("step overrun changed counters")
			}
			if cycleClock && m.CommitHostWork(21, 24, 1000, 1000) == nil {
				t.Fatal("cycle overrun accepted")
			}
			if err := m.CommitHostWork(21, 23, 1000, 1000); err != nil {
				t.Fatal(err)
			}
			if m.HostWorkBudget(1, 1).Steps != 0 {
				t.Fatal("due callback hidden")
			}
		}
	}
}

func TestResearchHostWorkRejectsPendingEventsAndOverflows(t *testing.T) {
	changes := []func(*Machine){
		func(m *Machine) { m.CPU.Halted = true },
		func(m *Machine) { m.CPU.Flags |= 0x100 }, func(m *Machine) { m.irq0Pending = true },
		func(m *Machine) { m.cbQueue = []QueuedCall{{}} }, func(m *Machine) { m.keyQueue = []KeyEvent{{}} },
		func(m *Machine) { m.timedKeys = []timedKey{{}} }, func(m *Machine) { m.wordWatches = []wordWatch{{}} },
		func(m *Machine) { m.TraceSegs = true }, func(m *Machine) { m.WatchDSOn = true },
		func(m *Machine) { m.Coverage = make([]bool, 1) },
		func(m *Machine) { m.WatchReads(1, 2, func(uint32, uint8) {}) },
		func(m *Machine) { m.WatchWrites(1, 2, func(uint32, uint8, uint8) {}) },
	}
	for i, change := range changes {
		m := New()
		m.IRQ0Every = 0
		m.VGAFrameEvery = 0
		change(m)
		if got := m.HostWorkBudget(100, 100); got != (HostWorkLimits{}) {
			t.Fatal(i, got)
		}
		if m.CommitHostWork(1, 1, 100, 100) == nil || m.Steps != 0 || m.CPU.Cycles != 0 {
			t.Fatal("rejected operation changed counters", i)
		}
	}
	m := New()
	m.IRQ0Every = 0
	m.VGAFrameEvery = 0
	m.Steps = ^uint64(0) - 1
	m.CPU.Cycles = ^uint64(0) - 2
	if got := m.HostWorkBudget(10, 10); got != (HostWorkLimits{1, 2}) {
		t.Fatal("overflow", got)
	}
	if m.CommitHostWork(2, 1, 10, 10) == nil || m.CommitHostWork(1, 3, 10, 10) == nil {
		t.Fatal("overflow accepted")
	}
	if m.CommitHostWork(1, 1, 0, 10) == nil || m.CommitHostWork(1, 1, 10, 0) == nil {
		t.Fatal("external quota ignored")
	}
}

func TestResearchHostWorkNativeEventsAtExactBoundary(t *testing.T) {
	for _, cycleClock := range []bool{false, true} {
		for _, dosCost := range []bool{false, true} {
			for _, kind := range []string{"frame", "irq", "periodic"} {
				t.Run(kind+"-"+boolName(cycleClock)+"-"+boolName(dosCost), func(t *testing.T) {
					cost := uint64(2)
					if dosCost {
						cost = 1
					}
					newMachine := func() (*Machine, *uint64) {
						m := New()
						m.IRQ0Every = 0
						m.VGAFrameEvery = 0
						m.Steps = 100
						m.CPU.Cycles = 200
						m.CycleClock = cycleClock
						m.CPU.DOSBoxCost = dosCost
						m.cycPerIRQ0 = 0
						m.CPU.Seg[1] = 0x9000
						m.CPU.IP = 0x100
						m.CPU.Flags |= 0x200
						for i := 0; i < 64; i++ {
							m.Mem[0x90100+i] = 0x90
						}
						seen := new(uint64)
						switch kind {
						case "frame":
							m.VGAFrameEvery = 15
							m.nextFrame = 115
							m.SetOnFrame(func() { *seen = m.Steps })
						case "irq":
							if cycleClock {
								m.cycPerIRQ0 = 15 * cost
								m.nextIRQ0Cyc = 200 + 15*cost
							} else {
								m.IRQ0Every = 15
								m.nextIRQ0 = 115
							}
							m.SetOnTick(func() { *seen = m.Steps })
						case "periodic":
							m.periodic.on = true
							m.periodic.every = 15
							m.periodic.next = 115
							m.periodic.seg = 0x9000
							m.periodic.off = 0x120
						}
						return m, seen
					}
					native, nativeEvent := newMachine()
					host, hostEvent := newMachine()
					for i := 0; i < 15; i++ {
						if err := native.Step(); err != nil {
							t.Fatal(err)
						}
					}
					if err := host.CommitHostWork(15, 15*cost, 15, 15*cost); err != nil {
						t.Fatal(err)
					}
					host.CPU.IP += 15
					if *nativeEvent != 0 || *hostEvent != 0 {
						t.Fatal("event delivered inside batch")
					}
					if err := native.Step(); err != nil {
						t.Fatal(err)
					}
					if err := host.Step(); err != nil {
						t.Fatal(err)
					}
					if kind != "periodic" && (*nativeEvent != 115 || *hostEvent != 115) {
						t.Fatal("event delivery step", *nativeEvent, *hostEvent)
					}
					if native.Steps != host.Steps || native.CPU.Cycles != host.CPU.Cycles || native.CPU.IP != host.CPU.IP || native.CPU.R != host.CPU.R || native.CPU.Seg != host.CPU.Seg || native.CPU.Flags != host.CPU.Flags || native.Frames != host.Frames || native.Ticks != host.Ticks || native.periodic.Calls != host.periodic.Calls {
						t.Fatal("native event phase differs")
					}
				})
			}
		}
	}
}

func boolName(b bool) string {
	if b {
		return "on"
	}
	return "off"
}
