//go:build ignore

// 053 READY. Installed only into the private core revision.
package machine

import "fmt"

// DiscardStalledKeyboardInput drops host hardware events belonging to a retired
// input consumer. It must never be used while a guest IRQ1 handler is installed.
// No CPU, memory, video, clock, BIOS queue or port state is changed.
func (m *Machine) DiscardStalledKeyboardInput() (int, int, error) {
	if m.Read16(0x24) != 0x24 || m.Read16(0x26) != StubSeg {
		return 0, 0, fmt.Errorf("keyboard IRQ1 consumer is not the default stub")
	}
	queued, timed := len(m.keyQueue), len(m.timedKeys)
	m.keyQueue = nil
	m.timedKeys = nil
	return queued, timed, nil
}
