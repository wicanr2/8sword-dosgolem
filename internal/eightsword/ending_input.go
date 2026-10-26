package eightsword

import "fmt"

// The optional API lives in the isolated 053 core revision. Older compatible
// cores keep their conservative native path rather than bypassing event limits.
func (e *Engine) syncEndingInput() error {
	if !e.inEndingPhase() || e.endingInputRetired {
		return nil
	}
	e.endingInputRetired = true
	e.endingInputStep = e.Oracle.Steps()
	handoff, ok := any(e.Oracle).(interface{ DiscardStalledKeyboardInput() (int, int, int, error) })
	if !ok {
		return nil
	}
	queued, timed, held, err := handoff.DiscardStalledKeyboardInput()
	if err != nil {
		return fmt.Errorf("結局硬體輸入交接：%w", err)
	}
	e.endingInputSupported = true
	e.endingInputDropped = [3]int{queued, timed, held}
	return nil
}
