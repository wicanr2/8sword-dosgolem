//go:build ignore

// 047 DRAFT. The machine owns the original instruction/event boundary.
package oracle

import "github.com/wicanr2/dosgolem/internal/machine"

func (o *Oracle) OnHostInstruction(a Addr,fn func(*machine.Machine)(bool,error)) {
	o.m.InstallHostInstruction(a.Linear(),fn)
}
