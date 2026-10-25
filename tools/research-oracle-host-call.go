//go:build ignore

// 047 DRAFT. Installed only into the isolated research core.
package oracle

import (
	"fmt"

	"github.com/wicanr2/dosgolem/internal/machine"
)

type HostWorkLimits = machine.HostWorkLimits
type HostCall func(*Oracle, *machine.Machine, HostWorkLimits) (bool, error)

// OnHostCall runs after ordinary entry observations. A rejected plan must
// leave guest state unchanged. Accepted plans must account their full work.
func (o *Oracle) OnHostCall(a Addr, fn HostCall) {
	if o.hostCalls == nil {
		o.hostCalls = map[uint32]HostCall{}
	}
	if fn == nil {
		delete(o.hostCalls, a.Linear())
		return
	}
	o.hostCalls[a.Linear()] = fn
	// Reuse the existing sparse hook index; this observation has no effects.
	o.OnCall(a, func(*Oracle) {})
}

func (o *Oracle) fireHostCall(key uint32, c Cond, deadline uint64) (bool, error) {
	if o.stepGuard != nil || c.hostLimits == nil || o.IP().Linear() != key {
		return false, nil
	}
	fn := o.hostCalls[key]
	if fn == nil {
		return false, nil
	}
	limits := c.hostLimits(o)
	if deadline-o.m.Steps < limits.Steps {
		limits.Steps = deadline - o.m.Steps
	}
	limits = o.m.HostWorkBudget(limits.Steps, limits.Cycles)
	if limits.Steps == 0 || limits.Cycles == 0 {
		return false, nil
	}
	steps, cycles := o.m.Steps, o.m.CPU.Cycles
	done, err := fn(o, o.m, limits)
	if err != nil {
		return false, err
	}
	if done && (o.m.Steps <= steps || o.m.Steps-steps > limits.Steps || o.m.CPU.Cycles < cycles || o.m.CPU.Cycles-cycles > limits.Cycles) {
		return false, fmt.Errorf("oracle: host call violated its work budget")
	}
	return done, nil
}
