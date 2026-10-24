package eightsword

import "github.com/wicanr2/dosgolem/oracle"

// PresentationWrite is pre-write metadata. Guest bytes are deliberately omitted.
type PresentationWrite struct {
	Step      uint64
	CS, IP    uint16
	Offset    uint32
	WriteMode uint8
}

type PresentationModeChange struct {
	Step uint64
	Mode uint8
}

// PresentationObserver must not execute or modify the guest. A mode callback
// must not read the palette, which is not yet complete at that notification.
type PresentationObserver struct {
	Write      func(PresentationWrite)
	ModeChange func(PresentationModeChange)
}

type presentationSubscription struct {
	observer PresentationObserver
	active   bool
}

// ObservePresentation shares Engine's core callbacks without replacing existing
// presenters. Call on the emulation thread. Cancellation is idempotent and may
// happen during delivery; registration during delivery is not supported.
func (e *Engine) ObservePresentation(observer PresentationObserver) func() {
	if e.presentationDispatch != 0 {
		panic("presentation observer registration during delivery")
	}
	if observer.Write == nil && observer.ModeChange == nil {
		return func() {}
	}
	slot := &presentationSubscription{observer: observer, active: true}
	e.presentationObservers = append(e.presentationObservers, slot)
	e.syncPresentationObservers()
	return func() {
		if !slot.active {
			return
		}
		slot.active = false
		e.presentationSweep = true
		if e.presentationDispatch == 0 {
			e.sweepPresentationObservers()
		}
	}
}

func (e *Engine) syncPresentationObservers() {
	if e.Tracker == nil && len(e.presentationObservers) == 0 {
		e.Oracle.ObserveVideoWrites(nil)
		e.Oracle.ObserveVideoModeChanges(nil)
		return
	}
	e.Oracle.ObserveVideoWrites(e.observePresentationWrite)
	e.Oracle.ObserveVideoModeChanges(e.observePresentationMode)
}

func (e *Engine) sweepPresentationObservers() {
	alive := e.presentationObservers[:0]
	for _, slot := range e.presentationObservers {
		if slot.active {
			alive = append(alive, slot)
		}
	}
	clear(e.presentationObservers[len(alive):])
	e.presentationObservers = alive
	e.presentationSweep = false
	e.syncPresentationObservers()
}

func (e *Engine) finishPresentationDispatch() {
	e.presentationDispatch--
	if e.presentationDispatch == 0 && e.presentationSweep {
		e.sweepPresentationObservers()
	}
}

func (e *Engine) observePresentationWrite(v oracle.VideoWrite) {
	if e.Tracker != nil {
		e.Tracker.write(v)
	}
	if e.Publisher != nil {
		e.Publisher.observeWrite(v)
	}
	if e.Intro != nil {
		e.Intro.observeWrite(v)
	}
	if e.Story != nil {
		e.Story.observeWrite(v)
	}
	if e.Captions != nil {
		e.Captions.observeWrite(v)
	}
	if len(e.presentationObservers) == 0 {
		return
	}
	metadata := PresentationWrite{v.Step, v.CS, v.IP, v.Offset, v.WriteMode}
	e.presentationDispatch++
	defer e.finishPresentationDispatch()
	for _, slot := range e.presentationObservers {
		if slot.active && slot.observer.Write != nil {
			slot.observer.Write(metadata)
		}
	}
}

func (e *Engine) observePresentationMode(v oracle.VideoModeChange) {
	if e.Tracker != nil {
		e.Tracker.clear()
	}
	if e.Publisher != nil {
		e.Publisher.invalidate()
	}
	if e.Intro != nil {
		e.Intro.invalidate()
	}
	if e.Story != nil {
		if e.Story.prelude != nil {
			e.Story.prelude.mode(v)
		}
		e.Story.invalidate()
	}
	if e.Captions != nil {
		e.Captions.invalidate()
	}
	if len(e.presentationObservers) == 0 {
		return
	}
	metadata := PresentationModeChange{v.Step, v.Mode}
	e.presentationDispatch++
	defer e.finishPresentationDispatch()
	for _, slot := range e.presentationObservers {
		if slot.active && slot.observer.ModeChange != nil {
			slot.observer.ModeChange(metadata)
		}
	}
}

func (e *Engine) closePresentationObservers() {
	for _, slot := range e.presentationObservers {
		slot.active = false
	}
	e.presentationObservers = nil
	e.Oracle.ObserveVideoWrites(nil)
	e.Oracle.ObserveVideoModeChanges(nil)
}
