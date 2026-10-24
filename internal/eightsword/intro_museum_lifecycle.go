package eightsword

import (
	"image"
	"image/draw"
)

// The five exact writer PCs/modes were measured through the shared observer;
// consumer code windows are pinned by the constructor. No guest bytes appear here.
func museumOwnsWrite(t museumTX, v PresentationWrite) bool {
	pc := uint32(v.CS)*16 + uint32(v.IP)
	if t.clear {
		return pc == 0x5b3b && v.WriteMode == 0 && v.Offset >= t.page && v.Offset < t.page+16384
	}
	if t.copy {
		writer := uint32(0x5132)
		if t.at == 0x5d9c {
			writer = 0x51a5
		}
		return pc == writer && v.WriteMode == 1 && v.Offset >= t.page && v.Offset < t.page+16000
	}
	writer := uint32(0x57ca)
	if t.at == 0x52c0 {
		writer = 0x534b
	}
	if pc != writer || v.WriteMode != 0 || t.record == nil || len(t.rows) == 0 || v.Offset < t.rows[0] {
		return false
	}
	delta := v.Offset - t.rows[0]
	return delta/80 < uint32(t.record.h) && delta%80 < uint32(t.record.w)
}

func (m *IntroMuseum) forgetMuseumPage(page uint32) {
	delete(m.pages, page)
	delete(m.last, page)
	delete(m.hold, page)
	delete(m.holdVersion, page)
	m.cachedBase = nil
	m.cachedFrame = nil
}

func (m *IntroMuseum) retireMuseum() {
	m.active = false
	m.retired = true
	m.drain = nil
	m.Stage = ""
	m.final = nil
	m.pages = map[uint32]*museumPage{}
	m.tx = nil
	m.last = map[uint32]*image.RGBA{}
	m.hold = map[uint32]*image.RGBA{}
	m.holdVersion = map[uint32]uint64{}
	m.cachedBase = nil
	m.cachedFrame = nil
	if m.stopObserving != nil {
		m.stopObserving()
		m.stopObserving = nil
	}
}

func (m *IntroMuseum) observeMuseumWrite(v PresentationWrite) {
	if m.retired {
		if m.drain != nil {
			d := m.drain
			if v.Offset >= d.page+1600 && v.Offset < d.page+12000 {
				m.finishMuseumDrain("owned-write", v.Step)
			}
		} else {
			m.ObserverAfterRetire++
		}
		return
	}
	if len(m.o.Overlays()) != 0 {
		m.retireMuseum()
		return
	}
	if !m.active || m.failed {
		m.ObserverBefore++
		return
	}
	m.ObserverWrites++
	page := v.Offset &^ uint32(0x3fff)
	row := (v.Offset - page) / 80
	if (page != 0 && page != 0x4000) || row < 20 || row >= 150 {
		return
	}
	for i := len(m.tx) - 1; i >= 0; i-- {
		if museumOwnsWrite(m.tx[i], v) {
			return
		}
	}
	m.UnknownWrites++
	if len(m.unknownSamples) < 8 {
		m.unknownSamples = append(m.unknownSamples, map[string]any{"step": v.Step, "cs": v.CS, "ip": v.IP, "offset": v.Offset, "write_mode": v.WriteMode})
	}
	changed := m.pages[page] != nil || m.hold[page] != nil
	m.forgetMuseumPage(page)
	for i := range m.tx {
		t := &m.tx[i]
		if t.page == page || (t.copy && t.sourcePage == page) {
			t.invalidated = true
			m.forgetMuseumPage(t.page)
			changed = true
		}
	}
	if changed {
		m.Invalidations++
	}
}

func (m *IntroMuseum) observeMuseumMode(event PresentationModeChange) {
	// The core mode callback must not read Palette or PlanarDisplay.
	if m.retired {
		if m.drain != nil {
			m.finishMuseumDrain("mode-change", event.Step)
		}
		return
	}
	if len(m.o.Overlays()) != 0 {
		m.retireMuseum()
		return
	}
	if !m.active {
		return
	}
	m.ModeInvalidations++
	m.pages = map[uint32]*museumPage{}
	m.last = map[uint32]*image.RGBA{}
	m.hold = map[uint32]*image.RGBA{}
	m.holdVersion = map[uint32]uint64{}
	m.cachedBase = nil
	m.cachedFrame = nil
	for i := range m.tx {
		m.tx[i].invalidated = true
	}
}

// The original ends the museum routine before decoding the next scene.
// Keep only the verified final visible overlay until the display really changes.
type museumDrain struct {
	page       uint32
	palette    [16][3]uint8
	startCycle uint64
	overlay    *image.RGBA
}

func (m *IntroMuseum) retireMuseumAt(at uint16) {
	if at == 0x203c && !m.retired && m.active && len(m.tx) == 0 && len(m.o.Overlays()) == 0 {
		s, ok := m.o.PlanarDisplay()
		if ok && s.Width == 640 && s.Height == 200 && s.Pitch == 80 && s.Palette == m.palette {
			if p := m.pages[s.Start]; m.sceneSupported(p) {
				m.drain = &museumDrain{page: s.Start, palette: s.Palette, startCycle: m.o.Cycles(), overlay: m.renderBand(p)}
				m.DrainStartStep = m.o.Steps()
				m.active = false
				m.retired = true
				return
			}
		}
	}
	m.retireMuseum() // Ordinary Esc never starts a presentation drain.
}
func (m *IntroMuseum) finishMuseumDrain(reason string, step uint64) {
	m.drain = nil
	m.DrainStopReason = reason
	m.DrainStopStep = step
	m.retireMuseum()
}
func (m *IntroMuseum) composeMuseumDrain(base *image.RGBA) *image.RGBA {
	d := m.drain
	if len(m.o.Overlays()) != 0 {
		m.finishMuseumDrain("overlay", m.o.Steps())
		return base
	}
	s, ok := m.o.PlanarDisplay()
	if !ok || s.Width != 640 || s.Height != 200 || s.Pitch != 80 || s.Start != d.page || s.Palette != d.palette {
		m.finishMuseumDrain("display-change", m.o.Steps())
		return base
	}
	// A safety cap, not a display delay. Normal mode handoff is observed after
	// 12,255,911 cycles; rendering never runs or waits for guest instructions.
	if m.o.Cycles()-d.startCycle > 60000000 {
		m.finishMuseumDrain("cycle-cap", m.o.Steps())
		return base
	}
	result := image.NewRGBA(base.Bounds())
	copy(result.Pix, base.Pix)
	draw.Draw(result, image.Rect(0, 120, 1920, 900), d.overlay, image.Point{}, draw.Over)
	m.Stage = "drain"
	m.DrainFrames++
	return result
}

// Tick handles lifetime even when the frontend is not drawing.
func (m *IntroMuseum) Tick() {
	if m == nil {
		return
	}
	if m.drain != nil {
		d := m.drain
		if len(m.o.Overlays()) != 0 {
			m.finishMuseumDrain("overlay", m.o.Steps())
			return
		}
		s, ok := m.o.PlanarDisplay()
		if !ok || s.Width != 640 || s.Height != 200 || s.Pitch != 80 || s.Start != d.page || s.Palette != d.palette {
			m.finishMuseumDrain("display-change", m.o.Steps())
			return
		}
		if m.o.Cycles()-d.startCycle > 60000000 {
			m.finishMuseumDrain("cycle-cap", m.o.Steps())
		}
		return
	}
	if !m.active || m.retired {
		return
	}
	if len(m.o.Overlays()) != 0 {
		m.retireMuseum()
		return
	}
	for _, t := range m.tx {
		if m.o.Cycles()-t.start > 2000000 {
			m.fail("museum transaction timeout")
			return
		}
	}
}
func (m *IntroMuseum) FrameStage(frame *image.RGBA) string {
	if m != nil && frame != nil && m.final == frame {
		return m.Stage
	}
	return ""
}
