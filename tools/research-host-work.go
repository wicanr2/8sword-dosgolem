//go:build ignore

// 047 DRAFT. Copied only into the private core by prepare-vga-read-probe.py.
// Method reference: MM3 docs/re/direct-render-methodology.md, RRSAL-1.0,
// Wang Chun-Yu / wicanr2, https://github.com/wicanr2/mm3-dosgolem.
// This version separately bounds step events and the 8sword cycle-clock IRQ.
package machine

import "fmt"

type HostWorkLimits struct{ Steps, Cycles uint64 }

// HostWorkBudget is read-only. Both external run quotas and internal events
// bound a batch. A complete call-effect contract is still the caller's duty.
func (m *Machine) HostWorkBudget(stepLimit, cycleLimit uint64) HostWorkLimits {
	if stepLimit == 0 || cycleLimit == 0 || m.CPU.Halted ||
		m.CPU.Flags&0x100 != 0 || m.irq0Pending || len(m.cbQueue) != 0 ||
		len(m.keyQueue) != 0 || len(m.timedKeys) != 0 || len(m.wordWatches) != 0 ||
		m.Coverage != nil || m.TraceSegs || m.WatchDSOn || m.onRead != nil || m.onWrite != nil {
		return HostWorkLimits{}
	}
	stepBound := func(enabled bool, next uint64) {
		if !enabled {
			return
		}
		if next <= m.Steps {
			stepLimit = 0
			return
		}
		if next-m.Steps < stepLimit {
			stepLimit = next - m.Steps
		}
	}
	stepBound(!m.CycleClock && m.IRQ0Every > 0, m.nextIRQ0)
	stepBound(m.VGAFrameEvery > 0, m.nextFrame)
	stepBound(m.periodic.on, m.periodic.next)
	if m.CycleClock && m.cycPerIRQ0 > 0 {
		if m.nextIRQ0Cyc <= m.CPU.Cycles {
			cycleLimit = 0
		} else if m.nextIRQ0Cyc-m.CPU.Cycles < cycleLimit {
			cycleLimit = m.nextIRQ0Cyc - m.CPU.Cycles
		}
	}
	if ^uint64(0)-m.Steps < stepLimit {
		stepLimit = ^uint64(0) - m.Steps
	}
	if ^uint64(0)-m.CPU.Cycles < cycleLimit {
		cycleLimit = ^uint64(0) - m.CPU.Cycles
	}
	return HostWorkLimits{stepLimit, cycleLimit}
}

// CommitHostWork only accounts an event-free, prevalidated operation. It does
// not run an ISR or modify CPU/RAM call effects. Due events execute next Step.
func (m *Machine) CommitHostWork(steps, cycles, stepQuota, cycleQuota uint64) error {
	budget := m.HostWorkBudget(stepQuota, cycleQuota)
	if steps == 0 || cycles == 0 || steps > budget.Steps || cycles > budget.Cycles {
		return fmt.Errorf("machine: host operation exceeds step, cycle or event budget")
	}
	m.Steps += steps
	m.CPU.Cycles += cycles
	return nil
}
