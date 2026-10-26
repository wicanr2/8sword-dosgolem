//go:build ignore

// 053 READY. Installed only into the private core revision.
package oracle

// DiscardStalledKeyboardInput is an explicit frontend input-consumer handoff.
// It is rejected before any change if the guest still owns IRQ1.
func (o *Oracle) DiscardStalledKeyboardInput() (int, int, int, error) {
	queued, timed, err := o.m.DiscardStalledKeyboardInput()
	if err != nil {
		return 0, 0, 0, err
	}
	held := len(o.held)
	clear(o.held)
	return queued, timed, held, nil
}
