//go:build ignore

// 047 DRAFT. Single-instruction replacements run inside normal Step timing.
package machine

import "fmt"

type HostInstruction func(*Machine) (bool,error)

// InstallHostInstruction preserves normal tick, input, step accounting and
// instruction identity. It replaces exactly one admitted instruction, not a
// multi-instruction batch. Rejected callbacks must leave the guest unchanged.
func (m *Machine) InstallHostInstruction(linear uint32,fn HostInstruction) {
	if m.hostInstructions==nil {
		m.hostInstructions=map[uint32]HostInstruction{}
		m.hostInstructionBits=make([]uint64,1<<14)
	}
	linear&=0xfffff
	if fn==nil {delete(m.hostInstructions,linear);m.hostInstructionBits[linear>>6]&^=1<<(linear&63);return}
	m.hostInstructions[linear]=fn
	m.hostInstructionBits[linear>>6]|=1<<(linear&63)
}

func (m *Machine) fireHostInstruction(linear uint32)(bool,error) {
	// Tracing/coverage and memory watches retain their native interpreter path.
	if m.Coverage!=nil || m.TraceSegs || m.WatchDSOn || m.onRead!=nil || m.onWrite!=nil || len(m.wordWatches)!=0 {return false,nil}
	fn:=m.hostInstructions[linear&0xfffff]
	if fn==nil {return false,nil}
	steps,cycles:=m.Steps,m.CPU.Cycles
	done,err:=fn(m)
	if err!=nil {return false,err}
	if m.Steps!=steps || (done && m.CPU.Cycles<=cycles) || (!done && m.CPU.Cycles!=cycles) {return false,fmt.Errorf("machine: atomic host instruction violated accounting")}
	return done,nil
}
